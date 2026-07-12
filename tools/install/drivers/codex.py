"""drivers/codex.py — Codex channel driver (PRD "plugin 채널 — Codex (승격)").

호출 대상(재구현 금지): `adapters/codex/bin/sync-native-*.py`(agents/skills/modes/plugin),
`adapters/codex/bin/preflight.sh`. plugin 채널은 기존 `adapters/codex/plugin-marketplace/`
(`.agents/plugins/marketplace.json`)를 재사용 — installer 는 `codex plugin marketplace add`
+ `codex plugin add <name>@<marketplace>` 를 wrapping 한다.

⚠️ plugin 이 못 싣는 것(공식 확인, PRD 표): custom agents(`.codex/agents/*.toml`)·prompts·
config.toml fragment·AGENTS.md — 이들은 plugin 채널과 무관하게 symlink projection 이 계속
담당한다. 즉 Codex 는 plugin 채널만으로 완결 불가(install() 은 두 경로를 항상 병행 고려).
"""

RUNTIME = "codex"


def install(scope="global", plugin=False, dry_run=False):
    """symlink projection(agents .toml 등 plugin 미탑재분) + plugin add wrapping.

    TODO(autopilot-code): plugin=True 여도 custom agents/prompts/config.toml fragment 는
    symlink 경로가 여전히 필요 — "plugin 이면 symlink 생략" 단순화 금지.
    """
    raise NotImplementedError("drivers.codex.install: scaffold — 구현 사이클에서 채움")


def checks():
    """verify 가 실행할 check 함수 목록. scaffold — 아직 비어 있음(verifier.run 이 fallback)."""
    return []


def status():
    """channel·commit·drift 요약. TODO(autopilot-code)."""
    raise NotImplementedError("drivers.codex.status: scaffold — 구현 사이클에서 채움")
