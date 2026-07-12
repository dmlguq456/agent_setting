"""projector.py — symlink projection plan (INSTALL_LAYOUT.md 레시피의 기계화).

SoT 는 언제나 `capabilities/`·`roles/`·core (PRD §0.5 원칙 3). 이 모듈은 그 SoT 로부터
런타임 home 아래 심어야 할 (source, dest) 링크 목록을 계산만 한다 — 실제 `os.symlink()`
적용은 이 스킬(scaffold)의 범위 밖, autopilot-code 구현 사이클에서 채운다.

TODO(autopilot-code): INSTALL_LAYOUT.md 의 런타임별 ln -sfn 나열(Claude ~17줄·Codex ~30줄·
OpenCode ~25줄)을 여기로 옮겨 온다. OpenCode 는 구현 Step 0 에서 로컬 버전 실측 후
migration 포함 여부 결정(INST-OPEN-4) — 그 전엔 legacy 배선(단수형 `agent/`·`command/`,
`skills.paths`)을 그대로 베끼지 않는다.
"""

# 런타임별 projection 대상 디렉토리 — capabilities/roles SoT → adapters/<runtime>/ 미러
# 자리를 가리키는 placeholder. 실제 항목은 미확정(scaffold).
_PROJECTION_STUB = {
    "claude": [],
    "codex": [],
    "opencode": [],
}


def plan(runtimes, scope="global"):
    """runtime 별 (source, dest) 링크 계획을 돌려준다. scaffold 단계 — 항상 빈 리스트.

    반환 shape: {runtime: [{"source": str, "dest": str}, ...]}
    """
    return {rt: list(_PROJECTION_STUB.get(rt, [])) for rt in runtimes}
