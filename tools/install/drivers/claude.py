"""drivers/claude.py — Claude Code channel driver (PRD "plugin 채널 — Claude Code (신설)").

Claude 는 **native runtime** — root 디렉터리(`core/`·`capabilities/`·`roles/`·`skills/`·...)
자체가 SoT 이고, 별도 생성기(`adapters/claude/bin/sync-native-*.py`)나
`claude_setting/bin/preflight.sh` 는 존재하지 않는다. projection 은 순수 symlink +
`copy_once`(settings.json, keybindings.json) 뿐이며 Windows 분기만
`adapters/claude/bin/install-windows.sh` 로 위임한다(재구현 금지).

plugin 채널(marketplace 콘텐츠 실물화)은 cycle-1 범위 밖 — Phase 7 에서 별도 사이클로
미뤄졌다. 여기서는 `plugin=True` 를 받아도 SKIP 만 보고한다.

싣기 가능(공식 확인, PRD 표): skills·agents·`hooks/hooks.json`·`.mcp.json`·`bin/`.
불가: settings.json 일반 키(`agent`·`subagentStatusLine` 만)·env·permissions·statusline·
plugin 내 CLAUDE.md. 이 경계는 install()/checks() 구현 시 그대로 반영한다(INST-OPEN-1).
"""

import os
import shutil
import subprocess
from pathlib import Path

import paths
import projector
import manifest
import verifier

RUNTIME = "claude"


def install(scope="global", plugin=False, dry_run=False):
    """symlink projection + copy-once runtime-owned 표면 적용.

    Claude 에는 생성기가 없다 — 순수 symlink + copy_once. Windows 호스트에서만
    `install-windows.sh` 위임 분기가 실행된다. `plugin=True` 는 Phase 7 로 미뤄진
    marketplace 실물화에 대응하는 SKIP 보고만 내보낸다(파일 시스템 접촉 없음).
    """
    entries = projector.plan(["claude"], scope=scope)["claude"]

    actions = []

    if plugin:
        actions.append(
            {
                "action": "plugin",
                "status": "skipped",
                "detail": "SKIP(claude): plugin channel — deferred to next cycle (Phase 7 boundary)",
            }
        )

    copy_once_files = []

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

        if action == "copy_once":
            source = Path(entry["source"])
            dest = Path(entry["dest"])

            if dry_run:
                actions.append(
                    {
                        "action": "copy_once",
                        "source": str(source),
                        "dest": str(dest),
                        "status": "planned",
                        "detail": "dry-run",
                    }
                )
                continue

            dest.parent.mkdir(parents=True, exist_ok=True)

            if dest.exists():
                status = "unchanged"
            else:
                shutil.copyfile(source, dest)
                status = "created"

            actions.append(
                {
                    "action": "copy_once",
                    "source": str(source),
                    "dest": str(dest),
                    "status": status,
                    "detail": "never re-copy over an existing runtime-owned copy",
                }
            )
            copy_once_files.append(
                {"relpath": dest.name, "source_abs": str(source), "dest_abs": str(dest)}
            )
            continue

        if action == "delegate":
            is_windows = os.name == "nt"
            if not is_windows or dry_run:
                reason = "not Windows" if not is_windows else "dry-run"
                actions.append(
                    {
                        "action": "delegate",
                        "cmd": entry["cmd"],
                        "status": "planned" if dry_run and is_windows else "skipped",
                        "detail": f"install-windows.sh delegate skipped ({reason})",
                    }
                )
                continue

            subprocess.run(entry["cmd"], cwd=str(paths.agent_home()))
            actions.append(
                {
                    "action": "delegate",
                    "cmd": entry["cmd"],
                    "status": "delegated",
                    "detail": "install-windows.sh executed",
                }
            )
            continue

    blocked = any(a.get("status") == "blocked" for a in actions)

    manifest_result = None
    if not dry_run and not blocked and copy_once_files:
        manifest_result = manifest.record("claude", copy_once_files, scope=scope)

    return {
        "runtime": "claude",
        "actions": actions,
        "blocked": blocked,
        "manifest": manifest_result,
    }


def checks(scope="global"):
    """verify 가 실행할 check 함수 목록 (Phase 4.2 — no sync-native, no preflight)."""
    entries = projector.plan(["claude"], scope=scope)["claude"]

    check_list = []

    for entry in entries:
        action = entry["action"]
        if action == "symlink":
            dest = entry["dest"]
            name = Path(dest).name
            check_list.append(
                verifier.check_symlink(f"claude.symlink.{name}", dest, entry["source"])
            )
        elif action == "copy_once":
            dest = entry["dest"]
            name = Path(dest).name
            check_list.append(verifier.check_file_exists(f"claude.file.{name}", dest))
        # "skip"/"delegate" 항목은 read-only check 대상이 아님 — 건너뜀.

    agent_home = str(paths.agent_home())

    check_list.append(
        verifier.check_cmd(
            "claude.build-manifest-check",
            ["python3", "tools/build-manifest.py", "--check"],
            cwd=agent_home,
        )
    )

    check_list.append(
        verifier.check_cmd(
            "claude.compile-smoke",
            [
                "python3",
                "-c",
                "import sys; [compile(open(f,encoding='utf-8').read(), f, 'exec') for f in sys.argv[1:]]",
                "tools/build-manifest.py",
                "tools/memory/mem.py",
            ],
            cwd=agent_home,
        )
    )

    def _bootstrap_smoke():
        if shutil.which("claude") is None:
            return {
                "id": "claude.bootstrap-smoke",
                "ok": True,
                "detail": "SKIP(claude): bootstrap smoke — claude CLI absent",
            }
        return {
            "id": "claude.bootstrap-smoke",
            "ok": True,
            "detail": "claude CLI present (no scripted bootstrap-smoke contract yet)",
        }

    check_list.append(_bootstrap_smoke)

    return check_list


def status(scope="global"):
    """channel·version·drift 요약."""
    manifest_data = manifest._load_manifest(manifest._manifest_path("claude", scope))
    drift = manifest.check_drift(["claude"], scope=scope)

    if manifest_data is None:
        return {"channel": "dev", "version": "not-installed", "file_count": 0, "drift_count": len(drift)}

    return {
        "channel": "dev",
        "version": manifest_data.get("version", "none"),
        "file_count": len(manifest_data.get("files", {})),
        "drift_count": len(drift),
    }
