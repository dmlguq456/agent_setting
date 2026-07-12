"""drivers/claude.py — Claude Code channel driver (PRD "plugin 채널 — Claude Code (신설)").

호출 대상(재구현 금지): `adapters/claude/bin/sync-native-*.py`(생성 projection),
`adapters/claude/bin/preflight.sh`(부트스트랩 계약). plugin 채널은
`adapters/claude/plugin-marketplace/`(marketplace.json + agent-harness-claude) 신설분.

싣기 가능(공식 확인, PRD 표): skills·agents·`hooks/hooks.json`·`.mcp.json`·`bin/`.
불가: settings.json 일반 키(`agent`·`subagentStatusLine` 만)·env·permissions·statusline·
plugin 내 CLAUDE.md. 이 경계는 install()/checks() 구현 시 그대로 반영한다(INST-OPEN-1).
"""

RUNTIME = "claude"


def install(scope="global", plugin=False, dry_run=False):
    """symlink projection + runtime-owned 표면 적용, 또는 --plugin 시 marketplace add wrapping.

    TODO(autopilot-code): dry_run=False 일 때 실제 sync-native-*.py 호출 + settings.json
    copy-once + manifest.record(). plugin=True 면 `claude plugin marketplace add` +
    `claude plugin install` 비대화 wrapping(PRD "CLI wrapping" 절 확인됨).
    """
    raise NotImplementedError("drivers.claude.install: scaffold — 구현 사이클에서 채움")


def checks():
    """verify 가 실행할 check 함수 목록. scaffold — 아직 비어 있음(verifier.run 이 fallback)."""
    return []


def status():
    """channel·commit·drift 요약. TODO(autopilot-code)."""
    raise NotImplementedError("drivers.claude.status: scaffold — 구현 사이클에서 채움")
