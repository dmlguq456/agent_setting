"""manifest.py — hash-manifest 기록·drift 감지·reapply (PRD "hash-manifest + reapply").

대상은 installer 가 runtime home 에 **복사**한 파일만 (settings.json·keybindings·Windows
copy 분기) — symlink 는 그 자체가 canonical 이라 제외, plugin cache 는 런타임 소유라 제외.
스키마는 harness-layer-sync(HLS) 와 공유(PRD §1 interlock) — `tools/build-manifest.py` 증분
포맷을 재사용할지는 구현 단계에서 확정한다.

⚠️ 구현 선행 게이트 (PRD "hash-manifest + reapply" 절, HLS §3.2 공유): GSD `bin/install.js`
실코드를 line 단위로 정독하기 전에는 아래 함수들의 실 hash/merge 로직을 채우지 않는다.
research 카드 서술을 그대로 이식 금지 — 지금은 시그니처와 반환 shape 만 확정한 stub.
"""


def record(runtime, files):
    """설치 직후 각 복사 파일의 hash 를 등재한다 (scaffold — 미구현)."""
    raise NotImplementedError("manifest.record: GSD bin/install.js 정독 게이트(HLS §3.2) 후 구현")


def check_drift(runtimes):
    """등재된 hash 와 현재 파일을 비교해 사용자 수정(drift) 목록을 돌려준다.

    반환 shape: [{"runtime": str, "path": str, "detail": str}, ...]. scaffold 단계 —
    항상 빈 리스트(감지 로직 미구현).
    """
    return []


def reapply(runtimes):
    """`update --reapply` — local-patches 백업 위에 새 파일을 재적용한다 (scaffold — 미구현).

    3-way 충돌은 자동 머지 강행 금지, 명시 report 로 그친다 (PRD 원칙).
    """
    raise NotImplementedError("manifest.reapply: GSD bin/install.js 정독 게이트(HLS §3.2) 후 구현")
