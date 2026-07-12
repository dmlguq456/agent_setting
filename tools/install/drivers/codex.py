"""drivers/codex.py — Codex channel driver (PRD "plugin 채널 — Codex (승격)").

호출 대상(재구현 금지): `adapters/codex/bin/sync-native-*.py`(agents/skills/modes/plugin),
`adapters/codex/bin/preflight.sh`. plugin 채널은 기존 `adapters/codex/plugin-marketplace/`
(`.agents/plugins/marketplace.json`)를 재사용 — installer 는 `codex plugin marketplace add`
+ `codex plugin add <name>@<marketplace>` 를 wrapping 한다 (Phase 7, 이 사이클 범위 밖).

⚠️ plugin 이 못 싣는 것(공식 확인, PRD 표): custom agents(`.codex/agents/*.toml`)·prompts·
config.toml fragment·AGENTS.md — 이들은 plugin 채널과 무관하게 symlink projection 이 계속
담당한다. 즉 Codex 는 plugin 채널만으로 완결 불가 — `plugin=True` 여도 symlink projection 은
항상 병행 적용한다("plugin 이면 symlink 생략"은 명시적 anti-pattern, INST-D-5).
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import paths
import projector
import manifest
import verifier

RUNTIME = "codex"


def install(scope="global", plugin=False, dry_run=False):
    """symlink projection(agents .toml 등 plugin 미탑재분) + plugin add wrapping(stub).

    Codex 는 copy_once 파일이 없다 — 순수 symlink projection (fixed symlinks + agents/skills
    glob fan-out, projector.plan() 이 이미 펼쳐서 준다). `plugin=True` 여도 symlink projection
    은 항상 적용된다(INST-D-5) — plugin 채널 자체는 Phase 7 에서 real wrapping 으로 채워질
    자리표시(SKIP)만 낸다.
    """
    entries = projector.plan(["codex"], scope=scope)["codex"]

    actions = []

    for entry in entries:
        action = entry["action"]

        if action == "skip":
            actions.append(
                {
                    "action": "skip",
                    "dest": entry["dest"],
                    "status": "skipped",
                    "detail": entry["reason"],
                }
            )
            continue

        if action == "symlink":
            source = Path(entry["source"])
            dest = Path(entry["dest"])

            if dry_run:
                actions.append(
                    {
                        "action": "symlink",
                        "source": str(source),
                        "dest": str(dest),
                        "status": "planned",
                        "detail": "dry-run",
                    }
                )
                continue

            dest.parent.mkdir(parents=True, exist_ok=True)

            already_linked = False
            if dest.is_symlink():
                try:
                    already_linked = Path(os.readlink(dest)) == source
                except OSError:
                    already_linked = False

            if already_linked:
                actions.append(
                    {
                        "action": "symlink",
                        "source": str(source),
                        "dest": str(dest),
                        "status": "unchanged",
                        "detail": "already linked",
                    }
                )
                continue

            if dest.exists() and not dest.is_symlink():
                actions.append(
                    {
                        "action": "symlink",
                        "source": str(source),
                        "dest": str(dest),
                        "status": "blocked",
                        "detail": (
                            f"dest is a real file/dir, refusing to overwrite: {dest} "
                            "(e.g. a pre-existing vanilla codex AGENTS.md — surface, don't clobber)"
                        ),
                    }
                )
                continue

            if dest.is_symlink():
                dest.unlink()

            dest.symlink_to(source, target_is_directory=source.is_dir())
            actions.append(
                {
                    "action": "symlink",
                    "source": str(source),
                    "dest": str(dest),
                    "status": "created",
                    "detail": "symlink created",
                }
            )
            continue

    if plugin:
        actions.append(
            {
                "action": "plugin",
                "status": "skipped",
                "detail": (
                    "codex plugin marketplace/add wrapping — Phase 7 (not yet implemented "
                    "in this dispatch), symlink projection still applied above (INST-D-5)"
                ),
            }
        )

    manifest_result = None
    if not dry_run:
        manifest_result = manifest.record("codex", [], scope=scope)

    return {
        "runtime": "codex",
        "actions": actions,
        "blocked": any(a.get("status") == "blocked" for a in actions),
        "manifest": manifest_result,
    }


def checks(scope="global"):
    """verify 가 실행할 check 함수 목록 (Phase 4.3 — sync-native + preflight + bootstrap)."""
    entries = projector.plan(["codex"], scope=scope)["codex"]
    agent_home = str(paths.agent_home())

    check_list = []

    for entry in entries:
        if entry["action"] != "symlink":
            continue
        dest = entry["dest"]
        dest_path = Path(dest)
        check_id = f"codex.symlink.{dest_path.parent.name}.{dest_path.name}"
        check_list.append(verifier.check_symlink(check_id, dest, entry["source"]))

    for name in ("skills", "agents", "modes", "plugin"):
        check_list.append(
            verifier.check_cmd(
                f"codex.sync-native-{name}",
                ["python3", f"adapters/codex/bin/sync-native-{name}.py", "--check"],
                cwd=agent_home,
            )
        )

    check_list.append(
        verifier.check_cmd(
            "codex.preflight.capability-info",
            ["adapters/codex/bin/preflight.sh", "capability-info", "autopilot-code"],
            must_match=[r"^native_skill_path="],
            cwd=agent_home,
        )
    )
    check_list.append(
        verifier.check_cmd(
            "codex.preflight.role",
            ["adapters/codex/bin/preflight.sh", "role", "fast", "reviewer"],
            must_match=[r"^adapter=codex$"],
            cwd=agent_home,
        )
    )

    def _bootstrap_smoke():
        if shutil.which("codex") is None:
            return {
                "id": "codex.bootstrap-smoke",
                "ok": True,
                "detail": "SKIP(codex): bootstrap smoke — codex CLI absent",
            }

        tmp_home = tempfile.mkdtemp(prefix="codex-bootstrap-smoke-")
        try:
            source = paths.resolve_source("codex_setting/AGENTS.md")
            dest = Path(tmp_home) / "AGENTS.md"
            dest.symlink_to(source)

            try:
                result = subprocess.run(
                    ["codex", "debug", "prompt-input", "bootstrap check"],
                    capture_output=True,
                    text=True,
                    env={**os.environ, "CODEX_HOME": tmp_home},
                    timeout=60,
                )
            except subprocess.TimeoutExpired:
                return {
                    "id": "codex.bootstrap-smoke",
                    "ok": False,
                    "detail": "timeout: codex debug prompt-input",
                }

            if result.returncode != 0:
                return {
                    "id": "codex.bootstrap-smoke",
                    "ok": False,
                    "detail": f"exit={result.returncode} stderr={result.stderr[:300]!r}",
                }

            marker = "AGENTS.md — Codex Adapter Bootstrap"
            if marker not in result.stdout:
                return {
                    "id": "codex.bootstrap-smoke",
                    "ok": False,
                    "detail": f"마커 미발견: {marker!r} (stdout 일부: {result.stdout[:300]!r})",
                }

            return {
                "id": "codex.bootstrap-smoke",
                "ok": True,
                "detail": "OK: AGENTS.md bootstrap marker found via codex debug prompt-input",
            }
        finally:
            shutil.rmtree(tmp_home, ignore_errors=True)

    check_list.append(_bootstrap_smoke)

    return check_list


def status(scope="global"):
    """channel·version·drift·pointer·plugin-marketplace 요약."""
    manifest_data = manifest._load_manifest(manifest._manifest_path("codex", scope))
    drift = manifest.check_drift(["codex"], scope=scope)

    if manifest_data is None:
        version = "not-installed"
    else:
        version = manifest_data.get("version", "none")

    pointer_present = (paths.runtime_home("codex", scope) / "agent-harness").is_symlink()
    plugin_marketplace_source_present = paths.resolve_source(
        "adapters/codex/plugin-marketplace"
    ).exists()

    return {
        "channel": "dev",
        "version": version,
        "drift_count": len(drift),
        "pointer_present": pointer_present,
        "plugin_marketplace_source_present": plugin_marketplace_source_present,
        "plugin_registered": None,  # Phase 7 TODO — needs `codex plugin marketplace list`
    }
