#!/usr/bin/env python3
"""Runtime-neutral ``harness`` installer CLI.

Subcommand tree:
  install [claude|codex|opencode|all]
  verify  [runtime]
  update  [--reapply]
  status
  uninstall [runtime]

The installer PRD is the source of truth. This module owns command parsing,
exit codes, and JSON output while helper modules own projection and drift logic.
It depends only on the Python standard library.
"""
import sys
import os
import json
import argparse
import shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

import paths
import projector
import manifest
import verifier
import bootstrap
import runtime_activation
import extensions
from drivers import get_driver, RUNTIMES

# Exit codes map one-to-one to the PRD CLI table.
EXIT_OK = 0
EXIT_FAIL = 1
EXIT_VERIFY_FAIL = 2
EXIT_BLOCKED = 3
EXIT_DRIFT = 4
EXIT_USAGE = 64


class _UsageExitParser(argparse.ArgumentParser):
    """Use the PRD usage exit code 64 instead of argparse's default 2."""

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, f"{self.prog}: error: {message}\n")


def build_parser():
    p = _UsageExitParser(
        prog="harness",
        description="agent-harness installer — install/verify/update/status/uninstall (hybrid two-channel model).",
    )
    # Common options inherited by all subcommands.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--runtime", action="append", choices=RUNTIMES, dest="runtimes",
        help="Target runtime (repeatable); defaults to the positional target or all runtimes.",
    )
    common.add_argument("--scope", choices=["global", "project"], default="global")
    common.add_argument("--dry-run", action="store_true", help="Print the plan without applying it")
    common.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    common.add_argument("--yes", action="store_true", help="Skip interactive confirmation")
    common.add_argument("--plugin", action="store_true", help="Use the plugin-channel marketplace wrapper")

    sub = p.add_subparsers(dest="command", required=True, parser_class=_UsageExitParser)

    p_install = sub.add_parser("install", parents=[common], help="Install projections, runtime-owned surfaces, and manifests")
    p_install.add_argument("target", nargs="?", choices=[*RUNTIMES, "all"], default="all")
    p_install.add_argument(
        "--profile",
        choices=runtime_activation.PROFILES,
        help="linked product profile; explicit use routes install through runtime activation",
    )

    p_verify = sub.add_parser("verify", parents=[common], help="Run the automated Migration Order checks")
    p_verify.add_argument("target", nargs="?", choices=RUNTIMES, default=None)

    p_update = sub.add_parser("update", parents=[common], help="Pull and reproject, optionally updating plugins")
    p_update.add_argument("--reapply", action="store_true", help="Reapply local patches to new files")

    sub.add_parser("status", parents=[common], help="Summarize installation channels, versions, and drift")

    p_uninstall = sub.add_parser("uninstall", parents=[common], help="Remove only manifest-owned files")
    p_uninstall.add_argument("target", nargs="?", choices=RUNTIMES, default=None)

    # Source → active runtime truth.  These parsers intentionally do not inherit
    # the legacy install channel's --plugin option: linked/packaged are mutually
    # exclusive and both are fully local/offline.
    p_runtime = sub.add_parser("runtime", help="Manage the active source, revision, and projection")
    runtime_sub = p_runtime.add_subparsers(
        dest="runtime_command", required=True, parser_class=_UsageExitParser
    )

    def runtime_common(parser, *, require_runtime=False):
        parser.add_argument(
            "--runtime",
            action="append" if require_runtime else "store",
            choices=[*RUNTIMES, "all"],
            required=require_runtime,
            default=None if require_runtime else "all",
        )
        parser.add_argument("--scope", choices=["global", "project"], default="global")
        parser.add_argument("--json", action="store_true")

    p_runtime_status = runtime_sub.add_parser("status", help="Show the active source and freshness")
    runtime_common(p_runtime_status)

    p_runtime_activate = runtime_sub.add_parser("activate", help="Activate a linked or packaged source")
    runtime_common(p_runtime_activate, require_runtime=True)
    p_runtime_activate.add_argument("--mode", choices=runtime_activation.MODES, required=True)
    p_runtime_activate.add_argument("--source", help="local canonical repo (default: AGENT_HOME)")
    p_runtime_activate.add_argument("--profile", choices=runtime_activation.PROFILES)

    p_runtime_refresh = runtime_sub.add_parser("refresh", help="Refresh the current mode from its local source")
    runtime_common(p_runtime_refresh, require_runtime=True)
    p_runtime_refresh.add_argument("--profile", choices=runtime_activation.PROFILES)

    p_runtime_doctor = runtime_sub.add_parser("doctor", help="Diagnose projections, duplicates, and freshness")
    runtime_common(p_runtime_doctor)
    p_runtime_doctor.add_argument("--strict", action="store_true")

    p_extension = sub.add_parser(
        "extension", help="offline instruction-only external extension lifecycle"
    )
    extension_sub = p_extension.add_subparsers(
        dest="extension_command", required=True, parser_class=_UsageExitParser
    )
    p_extension_inspect = extension_sub.add_parser(
        "inspect", help="inspect a local extension source without mutation"
    )
    p_extension_inspect.add_argument("source")
    p_extension_inspect.add_argument("--json", action="store_true")

    p_extension_add = extension_sub.add_parser(
        "add", help="inspect, snapshot, and project a local extension"
    )
    p_extension_add.add_argument("source")
    p_extension_add.add_argument(
        "--runtime",
        action="append",
        choices=[*RUNTIMES, "all"],
        dest="extension_runtimes",
    )
    p_extension_add.add_argument("--json", action="store_true")

    p_extension_update = extension_sub.add_parser(
        "update", help="refresh an installed extension from a local source"
    )
    p_extension_update.add_argument("canonical_id")
    p_extension_update.add_argument("--source")
    p_extension_update.add_argument("--json", action="store_true")

    p_extension_remove = extension_sub.add_parser(
        "remove", help="remove only registry-owned extension projections"
    )
    p_extension_remove.add_argument("canonical_id")
    p_extension_remove.add_argument("--json", action="store_true")

    return p


def resolve_runtimes(args):
    """Combine a positional target and repeated ``--runtime`` options."""
    if args.runtimes:
        return list(args.runtimes)
    target = getattr(args, "target", None)
    if target in (None, "all"):
        return list(RUNTIMES)
    return [target]


def emit(result, as_json):
    if as_json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        for line in result.get("lines", []):
            print(line)
    return result["exit"]


def cmd_install(args):
    runtimes = resolve_runtimes(args)
    if args.profile:
        if args.plugin:
            return {
                "runtime": runtimes,
                "channel": "linked",
                "checks": [],
                "drift": [],
                "exit": EXIT_BLOCKED,
                "lines": ["install --profile cannot be combined with the external plugin channel"],
            }
        try:
            for runtime in runtimes:
                runtime_activation.validate_scope(runtime, args.scope)
        except runtime_activation.ActivationError as exc:
            return {
                "runtime": runtimes,
                "channel": "linked",
                "profile": args.profile,
                "checks": [],
                "drift": [],
                "exit": EXIT_BLOCKED,
                "lines": [f"install --profile: blocked: {exc}"],
            }
        if args.dry_run:
            return {
                "runtime": runtimes,
                "channel": "linked",
                "profile": args.profile,
                "checks": [],
                "drift": [],
                "exit": EXIT_OK,
                "lines": [
                    f"install(dry-run): runtime={runtime} mode=linked profile={args.profile}"
                    for runtime in runtimes
                ],
            }
        runtime_args = argparse.Namespace(
            runtime=runtimes,
            runtime_command="activate",
            source=str(paths.agent_home()),
            scope=args.scope,
            json=args.json,
            mode="linked",
            profile=args.profile,
        )
        result = cmd_runtime(runtime_args)
        result["channel"] = "linked"
        result["profile"] = args.profile
        result["lines"].insert(0, f"install: linked profile={args.profile}")
        return result

    lines = [f"install: runtime={r} scope={args.scope} plugin={args.plugin} dry_run={args.dry_run}" for r in runtimes]
    checks = []
    results = []

    for rt in runtimes:
        driver = get_driver(rt)
        result = driver.install(scope=args.scope, plugin=args.plugin, dry_run=args.dry_run)
        results.append(result)

        for a in result["actions"]:
            dest = a.get("dest", "")
            detail = a.get("detail")
            line = f"{rt}: {a['action']} {dest} -> {a['status']}"
            if detail and a["status"] not in ("created", "unchanged"):
                line += f" ({detail})"
            lines.append(line)

            check_name = Path(dest).name if dest else "x"
            checks.append(
                {
                    "id": f"{rt}.{a['action']}.{check_name}",
                    "ok": a["status"] != "blocked",
                    "detail": detail if detail else a["status"],
                }
            )

    any_blocked = any(result["blocked"] for result in results)

    if not any_blocked:
        if args.dry_run:
            launcher_results = bootstrap.install_launchers(dry_run=True)
            lines.append("bootstrap: mem-import skipped (dry-run — no dry-run mode for restore_memory)")
            for lr in launcher_results:
                lines.append(f"bootstrap: launcher {lr['name']} -> {lr['status']} (dry-run)")
                checks.append(
                    {
                        "id": f"bootstrap.launcher.{lr['name']}",
                        "ok": lr["status"] != "skipped-collision",
                        "detail": lr.get("detail", lr["status"]),
                    }
                )
        else:
            mem_result = bootstrap.restore_memory()
            lines.append(f"bootstrap: mem-import -> {mem_result['action']} ({mem_result['detail']})")
            checks.append(
                {
                    "id": "bootstrap.mem-import",
                    "ok": mem_result["action"] != "failed",
                    "detail": mem_result["detail"],
                }
            )

            launcher_results = bootstrap.install_launchers(dry_run=False)
            for lr in launcher_results:
                lines.append(f"bootstrap: launcher {lr['name']} -> {lr['status']}")
                checks.append(
                    {
                        "id": f"bootstrap.launcher.{lr['name']}",
                        "ok": lr["status"] != "skipped-collision",
                        "detail": lr.get("detail", lr["status"]),
                    }
                )

    exit_code = EXIT_BLOCKED if any_blocked else EXIT_OK
    return {"runtime": runtimes, "channel": "plugin" if args.plugin else "dev", "checks": checks,
            "drift": [], "exit": exit_code, "lines": lines}


def cmd_verify(args):
    runtimes = resolve_runtimes(args)
    all_checks = []
    ok = True
    for rt in runtimes:
        activation_state = paths.harness_state_dir(rt, args.scope) / "activation.json"
        if activation_state.exists() or activation_state.is_symlink():
            try:
                report = runtime_activation.doctor(rt, strict=True, scope=args.scope)
                status = report["status"]
                rt_checks = [
                    {
                        "id": f"{rt}.runtime-activation",
                        "ok": report["ok"],
                        "detail": (
                            f"profile={status.get('profile')} "
                            f"freshness={report['freshness']} "
                            f"next={report['next_action']}"
                        ),
                    }
                ]
            except (runtime_activation.ActivationError, OSError, ValueError) as exc:
                rt_checks = [
                    {
                        "id": f"{rt}.runtime-activation",
                        "ok": False,
                        "detail": f"activation state invalid: {exc}",
                    }
                ]
        else:
            driver = get_driver(rt)
            rt_checks = verifier.run(rt, driver)
        all_checks.extend(rt_checks)
        if any(not c["ok"] for c in rt_checks):
            ok = False
    lines = [("✓" if c["ok"] else "✗") + f" {c['id']} {c['detail']}" for c in all_checks]
    return {"runtime": runtimes, "channel": "plugin" if args.plugin else "dev", "checks": all_checks,
            "drift": [], "exit": EXIT_OK if ok else EXIT_VERIFY_FAIL, "lines": lines}


def cmd_update(args):
    runtimes = resolve_runtimes(args)
    drift = manifest.check_drift(runtimes, scope=args.scope)
    lines = [f"update: runtime={r} reapply={args.reapply}" for r in runtimes]
    checks = []

    if not args.reapply:
        if drift:
            for d in drift:
                lines.append(f"drift: {d['runtime']}/{d['path']} ({d['detail']})")
            checks.append(
                {
                    "id": "update.drift",
                    "ok": False,
                    "detail": f"found {len(drift)} drift item(s); use --reapply or inspect manually",
                }
            )
            exit_code = EXIT_DRIFT
        else:
            checks.append({"id": "update.drift", "ok": True, "detail": "no drift"})
            exit_code = EXIT_OK
        return {"runtime": runtimes, "channel": "plugin" if args.plugin else "dev", "checks": checks,
                "drift": drift, "exit": exit_code, "lines": lines}

    # --reapply: build sources dict from current projector plan's copy_once entries.
    sources = {rt: {} for rt in runtimes}
    for rt in runtimes:
        entries = projector.plan([rt], scope=args.scope)[rt]
        for entry in entries:
            if entry["action"] == "copy_once":
                relpath = Path(entry["dest"]).name
                sources[rt][relpath] = entry["source"]

    result = manifest.reapply(runtimes, scope=args.scope, sources=sources)

    for r in result["reapplied"]:
        lines.append(f"reapplied: {r['runtime']}/{r['path']}")
    for c in result["conflicts"]:
        lines.append(f"conflict: {c['runtime']}/{c['path']} ({c.get('status')})")
    for v in result["verify_failed"]:
        lines.append(f"verify_failed: {v['runtime']}/{v['path']} ({v.get('status')})")
    for m in result["missing"]:
        lines.append(f"missing: {m['runtime']}/{m['path']}")

    checks.append({"id": "update.reapplied", "ok": True, "detail": f"reapplied {len(result['reapplied'])} file(s)"})
    checks.append(
        {
            "id": "update.conflicts",
            "ok": not result["conflicts"],
            "detail": f"{len(result['conflicts'])} conflict(s)",
        }
    )
    checks.append(
        {
            "id": "update.verify_failed",
            "ok": not result["verify_failed"],
            "detail": f"{len(result['verify_failed'])} verification failure(s)",
        }
    )
    checks.append({"id": "update.missing", "ok": True, "detail": f"{len(result['missing'])} missing file(s)"})

    exit_code = EXIT_DRIFT if (result["conflicts"] or result["verify_failed"]) else EXIT_OK
    return {"runtime": runtimes, "channel": "plugin" if args.plugin else "dev", "checks": checks,
            "drift": drift, "exit": exit_code, "lines": lines}


def cmd_status(args):
    runtimes = resolve_runtimes(args)
    lines = []
    checks = []
    for rt in runtimes:
        driver = get_driver(rt)
        s = driver.status(scope=args.scope)
        detail = f"channel={s['channel']} version={s['version']} drift={s['drift_count']}"
        checks.append({"id": f"{rt}.status", "ok": True, "detail": detail})
        lines.append(f"{rt}: {detail}")
    return {"runtime": runtimes, "channel": "dev", "checks": checks, "drift": [], "exit": EXIT_OK, "lines": lines}


def cmd_uninstall(args):
    runtimes = resolve_runtimes(args)
    lines = []
    checks = []

    for rt in runtimes:
        manifest_path = manifest._manifest_path(rt, args.scope)
        manifest_data = manifest._load_manifest(manifest_path)

        if manifest_data is None:
            lines.append(f"uninstall: {rt} — no manifest; nothing to remove")
            checks.append({"id": f"{rt}.uninstall", "ok": True, "detail": "no manifest, nothing to uninstall"})
            continue

        runtime_home = paths.runtime_home(rt, args.scope)

        copy_once_dests = [runtime_home / relpath for relpath in manifest_data.get("files", {})]

        entries = projector.plan([rt], scope=args.scope)[rt]
        symlink_dests = [Path(e["dest"]) for e in entries if e["action"] == "symlink"]

        if args.dry_run:
            for d in copy_once_dests:
                lines.append(f"uninstall(dry-run): {rt} — remove copy-once file {d}")
            for d in symlink_dests:
                lines.append(f"uninstall(dry-run): {rt} — remove symlink {d}")
            lines.append(f"uninstall(dry-run): {rt} — remove manifest {manifest_path}")
            checks.append(
                {
                    "id": f"{rt}.uninstall",
                    "ok": True,
                    "detail": f"dry-run: would remove {len(copy_once_dests)} copy-once file(s) and {len(symlink_dests)} symlink(s)",
                }
            )
            continue

        # 1) Remove symlinks idempotently.
        for d in symlink_dests:
            if d.is_symlink():
                d.unlink()
                lines.append(f"uninstall: {rt} — removed symlink {d}")

        # 2) Back up and remove copy-once files.
        for relpath, d in zip(manifest_data.get("files", {}), copy_once_dests):
            if d.exists():
                backup_path = paths.harness_state_dir(rt, args.scope) / "local-patches" / relpath
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(d, backup_path)
                d.unlink()
                lines.append(f"uninstall: {rt} — removed copy-once file {d} (backed up to {backup_path})")

        # 3) Remove manifest.json last.
        if manifest_path.exists():
            manifest_path.unlink()
            lines.append(f"uninstall: {rt} — removed manifest {manifest_path}")

        checks.append(
            {
                "id": f"{rt}.uninstall",
                "ok": True,
                "detail": f"removed {len(copy_once_dests)} copy-once file(s) and {len(symlink_dests)} symlink(s)",
            }
        )

    return {"runtime": runtimes, "channel": "dev", "checks": checks, "drift": [], "exit": EXIT_OK, "lines": lines}


def _runtime_targets(value):
    values = value if isinstance(value, list) else [value]
    if not values or "all" in values:
        return list(runtime_activation.RUNTIMES)
    result = []
    for runtime in values:
        if runtime not in result:
            result.append(runtime)
    return result


def _runtime_emit_shape(command, reports, exit_code, lines):
    if len(reports) == 1:
        result = dict(reports[0])
        result.update({"command": command, "exit": exit_code, "lines": lines})
        return result
    return {
        "command": command,
        "runtimes": reports,
        "exit": exit_code,
        "lines": lines,
    }


def cmd_runtime(args):
    targets = _runtime_targets(args.runtime)
    reports = []
    lines = []
    exit_code = EXIT_OK
    snapshots = []

    try:
        if args.runtime_command in {"activate", "refresh"} and len(targets) > 1:
            source = args.source if args.runtime_command == "activate" else None
            for runtime in targets:
                snapshots.append(
                    runtime_activation.capture_runtime_state(runtime, source, args.scope)
                )
        for runtime in targets:
            if args.runtime_command == "status":
                report = runtime_activation.status(runtime, args.scope)
                if report["freshness"] in {
                    "missing", "cache-stale", "duplicate", "unsupported"
                }:
                    exit_code = EXIT_VERIFY_FAIL
            elif args.runtime_command == "activate":
                report = runtime_activation.activate(
                    runtime,
                    args.mode,
                    args.source,
                    args.scope,
                    getattr(args, "profile", None),
                )
            elif args.runtime_command == "refresh":
                report = runtime_activation.refresh(
                    runtime, args.scope, getattr(args, "profile", None)
                )
            elif args.runtime_command == "doctor":
                report = runtime_activation.doctor(runtime, args.strict, args.scope)
                if not report["ok"]:
                    exit_code = EXIT_VERIFY_FAIL
            else:
                raise runtime_activation.ActivationError(
                    f"unknown runtime command: {args.runtime_command}"
                )
            reports.append(report)
            freshness = report.get("freshness")
            if freshness is None and isinstance(report.get("status"), dict):
                freshness = report["status"].get("freshness")
            lines.append(
                f"{runtime}: {args.runtime_command} profile="
                f"{report.get('profile') or report.get('status', {}).get('profile')} "
                f"freshness={freshness} "
                f"next={report.get('next_action', 'none')}"
            )
    except runtime_activation.ActivationError as exc:
        rollback_errors = []
        for snapshot in reversed(snapshots):
            try:
                runtime_activation.restore_runtime_state(snapshot)
            except Exception as rollback_exc:
                rollback_errors.append(str(rollback_exc))
        for report in reports:
            report["rolled_back"] = True
        if snapshots:
            lines.append("runtime invocation rolled back across all selected runtimes")
        if rollback_errors:
            lines.append("rollback errors: " + "; ".join(rollback_errors))
        lines.append(f"runtime {args.runtime_command}: blocked: {exc}")
        for snapshot in snapshots:
            runtime_activation.discard_runtime_state(snapshot)
        return _runtime_emit_shape(
            args.runtime_command,
            reports + [{"error": str(exc)}],
            EXIT_BLOCKED,
            lines,
        )
    except Exception:
        for snapshot in reversed(snapshots):
            runtime_activation.restore_runtime_state(snapshot)
        for snapshot in snapshots:
            runtime_activation.discard_runtime_state(snapshot)
        raise

    for snapshot in snapshots:
        runtime_activation.discard_runtime_state(snapshot)

    return _runtime_emit_shape(args.runtime_command, reports, exit_code, lines)


def cmd_extension(args):
    operation = args.extension_command
    try:
        if operation == "inspect":
            report = extensions.inspect_source(args.source)
            blocked = report["status"] == "blocked"
            return {
                "operation": operation,
                "extension": report,
                "checks": report["findings"],
                "drift": [],
                "exit": EXIT_VERIFY_FAIL if blocked else EXIT_OK,
                "lines": [
                    f"extension inspect: {report['status']}: {report['canonical_id']}",
                    f"checksum: {report['source_checksum']}",
                    (
                        "parity: "
                        + ", ".join(
                            f"{runtime}={value['status']}"
                            for runtime, value in report["parity"].items()
                        )
                    ),
                    (
                        "inactive: "
                        + (",".join(report["inactive_surfaces"]) or "none")
                    ),
                    f"findings: {len(report['findings'])}",
                    (
                        f"next: extension add {report['source']}"
                        if not blocked
                        else "next: resolve blocking findings and inspect again"
                    ),
                ],
            }
        if operation == "add":
            result = extensions.add(args.source, args.extension_runtimes)
        elif operation == "update":
            result = extensions.update(args.canonical_id, args.source)
        elif operation == "remove":
            result = extensions.remove(args.canonical_id)
        else:
            raise extensions.ExtensionError(
                "unsupported-operation", f"unsupported extension operation: {operation}"
            )
        changed = "changed" if result["changed"] else "unchanged"
        return {
            "operation": operation,
            "extension": result,
            "checks": [],
            "drift": [],
            "exit": EXIT_OK,
            "lines": [
                f"extension {operation}: {changed}: {result['canonical_id']}",
                f"checksum: {result['snapshot_key']}",
                (
                    "projection: "
                    + ", ".join(
                        f"{runtime}={destination}"
                        for runtime, destination in result["runtime_projection"].items()
                    )
                ),
                f"inactive: {','.join(result['inactive_surfaces']) or 'none'}",
                f"snapshot: {result['snapshot'] or 'removed'}",
                (
                    "next-session: "
                    + ", ".join(
                        f"{runtime}={action}"
                        for runtime, action in result["next_session_action"].items()
                    )
                ),
            ],
        }
    except extensions.ExtensionError as exc:
        exit_code = EXIT_VERIFY_FAIL if operation == "inspect" else EXIT_BLOCKED
        return {
            "operation": operation,
            "extension": None,
            "checks": [{"id": exc.reason, "ok": False, "detail": str(exc)}],
            "drift": [],
            "exit": exit_code,
            "reason": exc.reason,
            "lines": [f"extension {operation}: blocked ({exc.reason}): {exc}"],
        }


COMMANDS = {
    "install": cmd_install,
    "verify": cmd_verify,
    "update": cmd_update,
    "status": cmd_status,
    "uninstall": cmd_uninstall,
    "runtime": cmd_runtime,
    "extension": cmd_extension,
}


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = COMMANDS.get(args.command)
    if handler is None:
        parser.print_usage(sys.stderr)
        return EXIT_USAGE
    result = handler(args)
    return emit(result, args.json)


if __name__ == "__main__":
    sys.exit(main())
