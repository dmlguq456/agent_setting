"""drivers/claude.py — Claude Code channel driver (PRD "plugin 채널 — Claude Code (신설)").

Claude 는 **native runtime** — root 디렉터리(`core/`·`capabilities/`·`roles/`·`skills/`·...)
자체가 SoT 이고, symlink projection 은 `adapters/claude/bin/sync-native-*.py` 없이도
성립한다. 단 plugin 채널만은 예외 — Claude plugin cache 는 self-contained 모델이라
콘텐츠 실물 포함이 필요, 그래서 `adapters/claude/bin/sync-native-plugin.py`(cycle 2 신설,
Claude 첫 sync-native 생성기)가 `adapters/claude/plugin-marketplace/plugins/
agent-harness-claude/` 를 채운다. projection 자체는 여전히 순수 symlink +
`copy_once`(settings.json, keybindings.json) 이며 Windows 분기만
`adapters/claude/bin/install-windows.sh` 로 위임한다(재구현 금지).

plugin 채널(marketplace 콘텐츠 실물화 + `claude plugin marketplace add`/`plugin install`
wrapping, `_plugin_action`)은 cycle 2 에서 `drivers/codex.py._plugin_action` 을 미러해
채운다 — CLI 부재 시 SKIP, dry-run 시 두 명령 문자열만 보고, 성공 시 registered.

싣기 가능(공식 확인, PRD 표 + `_internal/hooks_inventory.md`): skills(28)·agents(9)·
`hooks/hooks.json`(채택 2 개, git-state-guard/artifact-guard). `.mcp.json`/`bin/` 은
탑재 대상 없음(부재/비-self-contained, hooks_inventory 조사 결론).
불가: settings.json 일반 키(`agent`·`subagentStatusLine` 만)·env·permissions·statusline·
plugin 내 CLAUDE.md — **plugin=True 여도 symlink+copy_once projection 은 항상 병행**
(INST-D-5, "plugin 이면 symlink 생략"은 명시적 anti-pattern, codex 와 동일 원칙).
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

_MARKETPLACE_SOURCE_RELPATH = "adapters/claude/plugin-marketplace"
_MARKETPLACE_NAME = "agent-harness"
_PLUGIN_SPEC = f"agent-harness-claude@{_MARKETPLACE_NAME}"


def _plugin_action(dry_run):
    """Phase 2 Step 2.1 — `claude plugin marketplace add`/`plugin install` wrapping.

    `drivers/codex.py._plugin_action` 의 미러. 차이점(로컬 `claude` CLI `--help` +
    실측으로 확인, runtime-currentness — dev_logs/step_01 참조): `claude plugin
    marketplace add`/`plugin install` 어느 쪽도 `--json` 플래그가 없다(codex 와 달리) —
    비대화성은 두 명령 모두 기본 동작으로 이미 보장된다(대화형 프롬프트 없음, 실측
    `marketplace add` 는 mktemp `CLAUDE_CONFIG_DIR` 하에서 exit 0 로 즉시 완료 확인).
    marketplace source 는 codex 처럼 별도 `*_setting/` 미러가 아니라 adapters 경로 직접
    (`resolve_source("adapters/claude/plugin-marketplace")`) — Claude 는 native 라
    plugin-marketplace 스켈레톤이 이미 adapters 아래 있다.
    """
    marketplace_source = str(paths.resolve_source(_MARKETPLACE_SOURCE_RELPATH))
    marketplace_cmd = ["claude", "plugin", "marketplace", "add", marketplace_source]
    plugin_cmd = ["claude", "plugin", "install", _PLUGIN_SPEC]

    if dry_run:
        return {
            "action": "plugin",
            "status": "planned",
            "detail": f"dry-run: {' '.join(marketplace_cmd)} ; {' '.join(plugin_cmd)}",
        }

    if shutil.which("claude") is None:
        return {
            "action": "plugin",
            "status": "skipped",
            "detail": "SKIP(claude): plugin channel wrapping — claude CLI absent",
        }

    try:
        mp_result = subprocess.run(marketplace_cmd, capture_output=True, text=True, timeout=60)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"action": "plugin", "status": "blocked", "detail": f"marketplace add 실행 실패: {exc}"}

    if mp_result.returncode != 0:
        return {
            "action": "plugin",
            "status": "blocked",
            "detail": f"marketplace add exit={mp_result.returncode} stderr={mp_result.stderr[:300]!r}",
        }

    try:
        plugin_result = subprocess.run(plugin_cmd, capture_output=True, text=True, timeout=60)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"action": "plugin", "status": "blocked", "detail": f"plugin install 실행 실패: {exc}"}

    if plugin_result.returncode != 0:
        return {
            "action": "plugin",
            "status": "blocked",
            "detail": f"plugin install exit={plugin_result.returncode} stderr={plugin_result.stderr[:300]!r}",
        }

    return {
        "action": "plugin",
        "status": "registered",
        "detail": f"marketplace + plugin install OK: {_PLUGIN_SPEC}",
    }


def install(scope="global", plugin=False, dry_run=False):
    """symlink projection + copy-once runtime-owned 표면 적용 + plugin wrapping.

    Claude 에는 symlink projection 생성기가 없다 — 순수 symlink + copy_once. Windows
    호스트에서만 `install-windows.sh` 위임 분기가 실행된다. `plugin=True` 는
    `_plugin_action(dry_run)` 을 호출한다 — symlink+copy_once projection 은 plugin
    콘텐츠가 못 싣는 표면(settings.json 복사·statusline·mem 복원·CLAUDE.md·launcher)을
    담당하므로 plugin=True 여도 항상 병행 실행된다(INST-D-5).
    """
    entries = projector.plan(["claude"], scope=scope)["claude"]

    actions = []

    if plugin:
        actions.append(_plugin_action(dry_run))

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
    """verify 가 실행할 check 함수 목록 (Phase 4.2 no-sync-native/no-preflight 기반 +
    cycle-2 Phase 3 plugin 채널 3 종 check 추가: sync-native-plugin drift,
    marketplace source 존재, CLI-gated registration — 모두 read-only)."""
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

    # Phase 3 Step 3.1 — generator drift: adapters/claude/plugin-marketplace/
    # plugins/agent-harness-claude/ must not be stale vs SoT (skills/agents/
    # hooks/hooks.json all covered by sync-native-plugin.py's own --check).
    check_list.append(
        verifier.check_cmd(
            "claude.sync-native-plugin",
            ["python3", "adapters/claude/bin/sync-native-plugin.py", "--check"],
            cwd=agent_home,
        )
    )

    # Step 3.2 — marketplace source presence (mirrors codex.plugin-marketplace-source).
    check_list.append(
        verifier.check_file_exists(
            "claude.plugin-marketplace-source",
            str(
                paths.resolve_source(_MARKETPLACE_SOURCE_RELPATH)
                / ".claude-plugin"
                / "marketplace.json"
            ),
        )
    )

    # Step 3.3 — CLI-gated, read-only registration check. Never installs during
    # verify; queries `claude plugin marketplace list --json` / `claude plugin
    # list --json` (verified live via --help: both support --json, unlike the
    # mutating `marketplace add`/`install` commands — see dev_logs/step_01).
    def _plugin_registered():
        if shutil.which("claude") is None:
            return {
                "id": "claude.plugin-registered",
                "ok": True,
                "detail": "SKIP(claude): plugin registration — claude CLI absent",
            }

        import json as _json

        try:
            mp_result = subprocess.run(
                ["claude", "plugin", "marketplace", "list", "--json"],
                capture_output=True,
                text=True,
                timeout=60,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            return {"id": "claude.plugin-registered", "ok": False, "detail": f"marketplace list 실행 실패: {exc}"}
        if mp_result.returncode != 0:
            return {
                "id": "claude.plugin-registered",
                "ok": False,
                "detail": f"marketplace list exit={mp_result.returncode} stderr={mp_result.stderr[:300]!r}",
            }
        try:
            marketplaces = _json.loads(mp_result.stdout)
        except ValueError:
            return {"id": "claude.plugin-registered", "ok": False, "detail": f"marketplace list JSON 파싱 실패: {mp_result.stdout[:300]!r}"}
        marketplace_present = any(m.get("name") == _MARKETPLACE_NAME for m in marketplaces)
        if not marketplace_present:
            return {
                "id": "claude.plugin-registered",
                "ok": False,
                "detail": f"marketplace {_MARKETPLACE_NAME!r} 미등록 (claude plugin marketplace add 필요)",
            }

        try:
            pl_result = subprocess.run(
                ["claude", "plugin", "list", "--json"],
                capture_output=True,
                text=True,
                timeout=60,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            return {"id": "claude.plugin-registered", "ok": False, "detail": f"plugin list 실행 실패: {exc}"}
        if pl_result.returncode != 0:
            return {
                "id": "claude.plugin-registered",
                "ok": False,
                "detail": f"plugin list exit={pl_result.returncode} stderr={pl_result.stderr[:300]!r}",
            }
        try:
            plugins = _json.loads(pl_result.stdout)
        except ValueError:
            return {"id": "claude.plugin-registered", "ok": False, "detail": f"plugin list JSON 파싱 실패: {pl_result.stdout[:300]!r}"}
        plugin_present = any(p.get("id") == _PLUGIN_SPEC for p in plugins)
        if not plugin_present:
            return {
                "id": "claude.plugin-registered",
                "ok": False,
                "detail": f"plugin {_PLUGIN_SPEC!r} 미설치 (claude plugin install 필요)",
            }

        return {
            "id": "claude.plugin-registered",
            "ok": True,
            "detail": f"OK: marketplace {_MARKETPLACE_NAME!r} + plugin {_PLUGIN_SPEC!r} 등록 확인",
        }

    check_list.append(_plugin_registered)

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
