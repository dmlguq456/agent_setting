"""drivers/opencode.py — OpenCode channel driver (PRD "plugin 채널 — OpenCode").

호출 대상(재구현 금지): `adapters/opencode/bin/sync-native-*.py`(agents/skills/commands),
`adapters/opencode/bin/preflight.sh`. marketplace·번들 포맷 **부재 확인** — plugin 채널
없음, installer 가 유일 경로. `opencode.json` 은 `instructions[]`·`plugin[]` 을
non-destructive merge(기존 사용자 config 보존, 충돌 시 보고·중단 — 자동 해석 시도 없음).

⚠️ drift(PRD currentness 검증): 현행 공식 문서는 복수형 디렉토리(`.opencode/skills|commands|
agents|plugins/`, global `~/.config/opencode/…`)이고 `skills.paths` config key 는 문서에
없음 — 기존 `INSTALL_LAYOUT.md`·`opencode_setting` 배선(단수형 `agent/`·`command/`,
`skills.paths`)은 legacy 일 가능성(INST-OPEN-4). 구현 Step 0 에서 로컬 opencode 버전 대상
실측 후 migration 포함 여부를 결정한다 — 그 전엔 이 legacy 배선을 그대로 베끼지 않는다.
"""

RUNTIME = "opencode"


def install(scope="global", plugin=False, dry_run=False):
    """symlink projection + opencode.json non-destructive merge.

    TODO(autopilot-code): merge 충돌(같은 key 다른 값)은 자동 해석 없이 report·중단
    (PRD "의미↔규칙 경계 체크" — 유일 경계 후보, 규칙으로 처리).
    """
    raise NotImplementedError("drivers.opencode.install: scaffold — 구현 사이클에서 채움")


def checks():
    """verify 가 실행할 check 함수 목록. scaffold — 아직 비어 있음(verifier.run 이 fallback)."""
    return []


def status():
    """channel·commit·drift 요약. TODO(autopilot-code)."""
    raise NotImplementedError("drivers.opencode.status: scaffold — 구현 사이클에서 채움")
