"""drivers/opencode.py — OpenCode channel driver (PRD "plugin 채널 — OpenCode").

호출 대상(재구현 금지): `adapters/opencode/bin/sync-native-*.py`(agents/skills/commands),
`adapters/opencode/bin/preflight.sh`. marketplace·번들 포맷 **부재 확인** — plugin 채널
없음, installer 가 유일 경로. `opencode.json` 은 `instructions[]`·`skills.paths` 를
non-destructive merge(기존 사용자 config 보존, 충돌 시 보고·중단 — 자동 해석 시도 없음).

⚠️ drift(PRD currentness 검증): 현행 공식 문서는 복수형 디렉토리(`.opencode/skills|commands|
agents|plugins/`, global `~/.config/opencode/…`)이고 `skills.paths` config key 는 문서에
없을 수 있음 — 기존 `INSTALL_LAYOUT.md`·`opencode_setting` 배선(단수형 `agent/`·`command/`,
`skills.paths`)은 legacy 일 가능성(INST-OPEN-4, 로컬 실측 버전 1.17.13 기준). impl-inputs §B
에 따라 이번 사이클은 그 단수형 배선을 그대로 유지하고(임의 전환 금지), Phase 4.4(d) 의
drift-watch sentinel 로 미래 버전업 시 복수형 등장 여부만 관측한다.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import paths
import projector
import manifest
import verifier

RUNTIME = "opencode"


def _config_path(scope):
    """이번 사이클 단순화: global/project 모두 `runtime_home / opencode.json` 을 쓴다.

    INSTALL_LAYOUT.md 의 project 예시는 실제로는 프로젝트 루트에 `opencode.json`을 두는
    쪽을 보여주지만(`paths.runtime_home('opencode','project')` 는 `<cwd>/.opencode`),
    이 사이클에서는 두 scope 모두 `runtime_home / opencode.json` 으로 일관되게 둔다 —
    project-root 배치는 이후 사이클 과제로 남긴다(step log Decision 참조).
    """
    return paths.runtime_home("opencode", scope) / "opencode.json"


def _instructions_path():
    return str(paths.resolve_source("opencode_setting/AGENTS.md"))


def _skills_path():
    return str(paths.resolve_source("opencode_setting/opencode-skills"))


def _merge_config(existing, our_instructions, our_skills_path):
    """existing(dict) 에 our_instructions/our_skills_path 를 non-destructive 로 병합한다.

    반환: (merged_dict, changed: bool, blocked: bool, detail: str)
    - key 부재 → 새로 만든다.
    - key 가 list(또는 skills.paths 의 경우 skills dict + paths list) 이고 우리 값이
      없으면 append, 있으면 그대로(no-op).
    - key 가 있지만 기대 타입이 아니면(conflict) blocked=True, existing 은 변경하지 않는다.
    """
    merged = dict(existing)
    changed = False

    # instructions[]
    if "instructions" not in merged:
        merged["instructions"] = [our_instructions]
        changed = True
    else:
        instructions = merged["instructions"]
        if not isinstance(instructions, list):
            return (
                existing,
                False,
                True,
                "opencode.json 'instructions' key exists with a non-list value — "
                "refusing to merge, manual resolution required",
            )
        if our_instructions not in instructions:
            merged["instructions"] = instructions + [our_instructions]
            changed = True

    # skills.paths
    if "skills" not in merged:
        merged["skills"] = {"paths": [our_skills_path]}
        changed = True
    else:
        skills = merged["skills"]
        if not isinstance(skills, dict):
            return (
                existing,
                False,
                True,
                "opencode.json 'skills' key exists with a non-dict value — "
                "refusing to merge, manual resolution required",
            )
        skills = dict(skills)
        if "paths" not in skills:
            skills["paths"] = [our_skills_path]
            merged["skills"] = skills
            changed = True
        else:
            skills_paths = skills["paths"]
            if not isinstance(skills_paths, list):
                return (
                    existing,
                    False,
                    True,
                    "opencode.json 'skills.paths' key exists with a non-list value — "
                    "refusing to merge, manual resolution required",
                )
            if our_skills_path not in skills_paths:
                skills = dict(skills)
                skills["paths"] = skills_paths + [our_skills_path]
                merged["skills"] = skills
                changed = True

    return (merged, changed, False, "merged" if changed else "unchanged")


def install(scope="global", plugin=False, dry_run=False):
    """symlink projection 적용 + opencode.json non-destructive merge.

    같은 key 다른 semantic(conflict) 은 자동 해석 없이 report·중단 — 이 install() 호출
    전체의 opencode 컴포넌트를 blocked=True 로 보고한다. 이전에 처리된 symlink 액션은
    롤백하지 않는다(BLOCKED = stop+report, undo 아님).
    """
    entries = projector.plan(["opencode"], scope=scope)["opencode"]

    actions = []
    blocked = False

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
                    already_linked = dest.resolve() == source.resolve()
                except OSError:
                    already_linked = os.readlink(dest) == str(source)

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
                        "detail": f"dest is a real file/directory, refusing to overwrite: {dest}",
                    }
                )
                continue

            if dest.is_symlink() or dest.exists():
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

        if action == "merge":
            cfg_path = _config_path(scope)
            our_instructions = _instructions_path()
            our_skills_path = _skills_path()

            if dry_run:
                actions.append(
                    {
                        "action": "merge",
                        "status": "planned",
                        "detail": "would add instructions[]/skills.paths entries if missing",
                    }
                )
                continue

            existing = {}
            if cfg_path.exists():
                with open(cfg_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)

            merged, changed, conflict, detail = _merge_config(
                existing, our_instructions, our_skills_path
            )

            if conflict:
                actions.append(
                    {"action": "merge", "status": "blocked", "detail": detail}
                )
                blocked = True
                continue

            if changed:
                cfg_path.parent.mkdir(parents=True, exist_ok=True)
                with open(cfg_path, "w", encoding="utf-8") as f:
                    json.dump(merged, f, indent=2, ensure_ascii=False)
                actions.append(
                    {"action": "merge", "status": "merged", "detail": detail}
                )
            else:
                actions.append(
                    {"action": "merge", "status": "unchanged", "detail": detail}
                )
            continue

    blocked = blocked or any(a.get("status") == "blocked" for a in actions)

    manifest_result = None
    if not dry_run and not blocked:
        manifest_result = manifest.record("opencode", [], scope=scope)

    return {
        "runtime": "opencode",
        "actions": actions,
        "blocked": blocked,
        "manifest": manifest_result,
    }


def checks(scope="global"):
    """verify 가 실행할 check 함수 목록 (Phase 4.4)."""
    entries = projector.plan(["opencode"], scope=scope)["opencode"]

    check_list = []

    for entry in entries:
        action = entry["action"]
        if action == "symlink":
            dest = entry["dest"]
            dest_path = Path(dest)
            check_id = f"opencode.symlink.{dest_path.parent.name}.{dest_path.name}"
            check_list.append(
                verifier.check_symlink(check_id, dest, entry["source"])
            )
        # "skip"/"merge" 항목은 read-only check 대상이 아님.

    agent_home = str(paths.agent_home())

    for name in ("skills", "agents", "commands"):
        check_list.append(
            verifier.check_cmd(
                f"opencode.sync-native-{name}",
                ["python3", f"adapters/opencode/bin/sync-native-{name}.py", "--check"],
                cwd=agent_home,
            )
        )

    check_list.append(
        verifier.check_cmd(
            "opencode.preflight.capability-info",
            ["adapters/opencode/bin/preflight.sh", "capability-info", "autopilot-code"],
            must_match=[r"^native_skill_path="],
            cwd=agent_home,
        )
    )
    check_list.append(
        verifier.check_cmd(
            "opencode.preflight.role",
            ["adapters/opencode/bin/preflight.sh", "role", "fast", "reviewer"],
            must_match=[r"^adapter=opencode$"],
            cwd=agent_home,
        )
    )

    def _drift_watch_sentinel():
        """INST-OPEN-4 — doc-vs-wiring drift-watch (Phase 4.4d). 항상 ok=True (informational)."""
        version_detail = "opencode CLI absent, version unknown"
        oc_bin = shutil.which("opencode")
        if oc_bin:
            try:
                result = subprocess.run(
                    [oc_bin, "--version"], capture_output=True, text=True, timeout=10
                )
                version_detail = f"opencode --version: {result.stdout.strip() or result.stderr.strip()}"
            except Exception as exc:
                version_detail = f"opencode --version 실행 실패: {exc}"

        # "plugins" 는 후보에서 제외 — 우리 자신이 항상 만드는 정당한 디렉터리
        # (agent-harness-guards.js dest) 라 마이그레이션 신호가 아니라 상시 오탐이 된다.
        plural_candidates = [
            Path.home() / ".config" / "opencode" / "skills",
            Path.home() / ".config" / "opencode" / "commands",
            Path.home() / ".config" / "opencode" / "agents",
        ]
        found_plural = [str(p) for p in plural_candidates if p.is_dir()]

        if found_plural:
            detail = (
                f"{version_detail}; plural dirs (.config/opencode/skills etc) DETECTED "
                f"alongside singular wiring — review INST-OPEN-4, local opencode may have "
                f"migrated: {found_plural}"
            )
        else:
            detail = (
                f"{version_detail}; singular wiring in use (agent/, command/); plural dirs "
                f"not detected — INST-OPEN-4 still open, no action needed"
            )

        return {"id": "opencode.drift-watch", "ok": True, "detail": detail}

    check_list.append(_drift_watch_sentinel)

    def _bootstrap_smoke():
        oc_bin = shutil.which("opencode")
        if oc_bin is None:
            return {
                "id": "opencode.bootstrap-smoke",
                "ok": True,
                "detail": "SKIP(opencode): bootstrap smoke — opencode CLI absent",
            }

        import tempfile

        with tempfile.TemporaryDirectory() as tmp_home:
            config_content = json.dumps(
                {
                    "instructions": [_instructions_path()],
                    "skills": {"paths": [_skills_path()]},
                }
            )
            env = dict(os.environ)
            env["HOME"] = tmp_home
            env["XDG_CONFIG_HOME"] = str(Path(tmp_home) / ".config")
            env["XDG_DATA_HOME"] = str(Path(tmp_home) / ".local" / "share")
            env["OPENCODE_CONFIG_CONTENT"] = config_content

            try:
                result = subprocess.run(
                    [oc_bin, "debug", "config", "--pure"],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=30,
                )
            except Exception as exc:
                return {
                    "id": "opencode.bootstrap-smoke",
                    "ok": False,
                    "detail": f"opencode debug config 실행 실패: {exc}",
                }

            if "opencode_setting/AGENTS.md" in result.stdout:
                return {
                    "id": "opencode.bootstrap-smoke",
                    "ok": True,
                    "detail": "opencode debug config --pure 출력에 opencode_setting/AGENTS.md 확인",
                }
            return {
                "id": "opencode.bootstrap-smoke",
                "ok": False,
                "detail": f"opencode_setting/AGENTS.md 미발견 (stdout 일부: {result.stdout[:300]!r})",
            }

    check_list.append(_bootstrap_smoke)

    return check_list


def status(scope="global"):
    """channel·version·drift·pointer·config-merge 요약."""
    manifest_data = manifest._load_manifest(manifest._manifest_path("opencode", scope))
    drift = manifest.check_drift(["opencode"], scope=scope)

    pointer_path = paths.runtime_home("opencode", scope) / "agent-harness"
    pointer_present = pointer_path.is_symlink() or pointer_path.exists()

    config_merged = False
    cfg_path = _config_path(scope)
    if cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            instructions = cfg.get("instructions", [])
            skills_paths = cfg.get("skills", {}).get("paths", [])
            config_merged = (
                isinstance(instructions, list)
                and _instructions_path() in instructions
                and isinstance(skills_paths, list)
                and _skills_path() in skills_paths
            )
        except (json.JSONDecodeError, OSError):
            config_merged = False

    if manifest_data is None:
        return {
            "channel": "dev",
            "version": "not-installed",
            "drift_count": len(drift),
            "pointer_present": pointer_present,
            "config_merged": config_merged,
        }

    return {
        "channel": "dev",
        "version": manifest_data.get("version", "none"),
        "drift_count": len(drift),
        "pointer_present": pointer_present,
        "config_merged": config_merged,
    }
