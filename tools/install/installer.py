#!/usr/bin/env python3
"""installer.py — harness-installer CLI skeleton (`harness` 진입 명령, INST-OPEN-2 확정).

runtime-neutral core (tools/install/, fleet 과 같은 자리 컨벤션). 서브명령 트리:
  install [claude|codex|opencode|all]
  verify  [runtime]
  update  [--reapply]
  status
  uninstall [runtime]

SoT = .agent_reports/spec/harness-installer/prd.md ([cli] 섹션). 본 파일은 Step 4 scaffold —
서브명령 파싱·exit code·--json shape 만 확정하고, 실 동작(symlink 실행·hash 기록·drift 판정·
채널 driver 호출)은 각 모듈 stub 에 TODO 로 위임한다. 구현은 이후 autopilot-code 사이클(plans/).

의존성: python3 stdlib only (zero-pip, fleet 선례). git·각 런타임 CLI 는 verify 단계 한정.
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
from drivers import get_driver, RUNTIMES

# exit code 상수 — PRD [cli] "### Exit code" 표와 1:1
EXIT_OK = 0
EXIT_FAIL = 1
EXIT_VERIFY_FAIL = 2
EXIT_BLOCKED = 3
EXIT_DRIFT = 4
EXIT_USAGE = 64


class _UsageExitParser(argparse.ArgumentParser):
    """argparse 기본 usage-error exit(2) 대신 PRD exit code 표의 64(usage)로 통일."""

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, f"{self.prog}: error: {message}\n")


def build_parser():
    p = _UsageExitParser(
        prog="harness",
        description="agent-harness installer — install/verify/update/status/uninstall (2-채널 하이브리드).",
    )
    # 공통 옵션 (PRD [cli] "공통 옵션") — 모든 서브명령에 상속
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--runtime", action="append", choices=RUNTIMES, dest="runtimes",
        help="대상 런타임 (반복 가능). 생략 시 서브명령 positional 또는 전체.",
    )
    common.add_argument("--scope", choices=["global", "project"], default="global")
    common.add_argument("--dry-run", action="store_true", help="실행 없이 계획만 출력")
    common.add_argument("--json", action="store_true", help="기계 출력 (--json shape, fleet 스타일)")
    common.add_argument("--yes", action="store_true", help="비대화 확인 생략")
    common.add_argument("--plugin", action="store_true", help="plugin 채널 경로 (marketplace/plugin add wrapping)")

    sub = p.add_subparsers(dest="command", required=True, parser_class=_UsageExitParser)

    p_install = sub.add_parser("install", parents=[common], help="dev 머신 projection + runtime-owned 표면 + manifest 기록")
    p_install.add_argument("target", nargs="?", choices=[*RUNTIMES, "all"], default="all")

    p_verify = sub.add_parser("verify", parents=[common], help="Migration Order 기계화 — check 목록 실행")
    p_verify.add_argument("target", nargs="?", choices=RUNTIMES, default=None)

    p_update = sub.add_parser("update", parents=[common], help="repo pull 후 재-projection (+ plugin update wrapping)")
    p_update.add_argument("--reapply", action="store_true", help="local-patches 를 새 파일에 재적용")

    sub.add_parser("status", parents=[common], help="설치 상태 요약 — 채널·버전·drift")

    p_uninstall = sub.add_parser("uninstall", parents=[common], help="manifest 등재분만 제거 (소유 경계)")
    p_uninstall.add_argument("target", nargs="?", choices=RUNTIMES, default=None)

    # Source → active runtime truth.  These parsers intentionally do not inherit
    # the legacy install channel's --plugin option: linked/packaged are mutually
    # exclusive and both are fully local/offline.
    p_runtime = sub.add_parser("runtime", help="active source/revision/projection 관리")
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

    p_runtime_status = runtime_sub.add_parser("status", help="active source와 freshness 조회")
    runtime_common(p_runtime_status)

    p_runtime_activate = runtime_sub.add_parser("activate", help="linked/packaged source 활성화")
    runtime_common(p_runtime_activate, require_runtime=True)
    p_runtime_activate.add_argument("--mode", choices=runtime_activation.MODES, required=True)
    p_runtime_activate.add_argument("--source", help="local canonical repo (default: AGENT_HOME)")

    p_runtime_refresh = runtime_sub.add_parser("refresh", help="현재 mode를 local source에서 갱신")
    runtime_common(p_runtime_refresh, require_runtime=True)

    p_runtime_doctor = runtime_sub.add_parser("doctor", help="projection/duplicate/freshness 진단")
    runtime_common(p_runtime_doctor)
    p_runtime_doctor.add_argument("--strict", action="store_true")

    return p


def resolve_runtimes(args):
    """positional target 과 --runtime 반복 옵션을 하나의 대상 목록으로 합친다."""
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
                    "detail": f"{len(drift)}개 drift 발견 — --reapply 로 재적용하거나 직접 확인",
                }
            )
            exit_code = EXIT_DRIFT
        else:
            checks.append({"id": "update.drift", "ok": True, "detail": "drift 없음"})
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

    checks.append({"id": "update.reapplied", "ok": True, "detail": f"{len(result['reapplied'])}개 재적용"})
    checks.append(
        {
            "id": "update.conflicts",
            "ok": not result["conflicts"],
            "detail": f"{len(result['conflicts'])}개 충돌",
        }
    )
    checks.append(
        {
            "id": "update.verify_failed",
            "ok": not result["verify_failed"],
            "detail": f"{len(result['verify_failed'])}개 verify 실패",
        }
    )
    checks.append({"id": "update.missing", "ok": True, "detail": f"{len(result['missing'])}개 누락 파일"})

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
            lines.append(f"uninstall: {rt} — manifest 없음, 제거할 것 없음")
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
                    "detail": f"dry-run: {len(copy_once_dests)}개 copy-once + {len(symlink_dests)}개 symlink 제거 예정",
                }
            )
            continue

        # 1) 심볼릭 링크 제거 (idempotent — 이미 없으면 조용히 skip).
        for d in symlink_dests:
            if d.is_symlink():
                d.unlink()
                lines.append(f"uninstall: {rt} — removed symlink {d}")

        # 2) copy-once 파일 — 백업 후 제거.
        for relpath, d in zip(manifest_data.get("files", {}), copy_once_dests):
            if d.exists():
                backup_path = paths.harness_state_dir(rt, args.scope) / "local-patches" / relpath
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(d, backup_path)
                d.unlink()
                lines.append(f"uninstall: {rt} — removed copy-once file {d} (backed up to {backup_path})")

        # 3) manifest.json 마지막 제거.
        if manifest_path.exists():
            manifest_path.unlink()
            lines.append(f"uninstall: {rt} — removed manifest {manifest_path}")

        checks.append(
            {
                "id": f"{rt}.uninstall",
                "ok": True,
                "detail": f"{len(copy_once_dests)}개 copy-once + {len(symlink_dests)}개 symlink 제거됨",
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
                    runtime, args.mode, args.source, args.scope
                )
            elif args.runtime_command == "refresh":
                report = runtime_activation.refresh(runtime, args.scope)
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
                f"{runtime}: {args.runtime_command} freshness={freshness} "
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


COMMANDS = {
    "install": cmd_install,
    "verify": cmd_verify,
    "update": cmd_update,
    "status": cmd_status,
    "uninstall": cmd_uninstall,
    "runtime": cmd_runtime,
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
