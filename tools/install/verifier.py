"""verifier.py — Migration Order 수동 검증(~260줄)의 기계화 (PRD "verify" 명령).

check 목록을 실행해 pass/fail 을 돌려준다. 실제 check 항목(projection 링크 존재·생성기
`--check` drift·preflight 계약·bootstrap 로드 스모크)은 각 channel driver 가 정의하고,
여기서는 공통 실행기(runner)만 둔다 — 항목 자체는 구현 사이클(plans/)에서 채운다.
"""


def run(runtime, driver):
    """runtime 하나에 대해 driver 가 등록한 check 들을 순서대로 돌린다.

    반환 shape: [{"id": str, "ok": bool, "detail": str}, ...]
    """
    checks = driver.checks()
    if not checks:
        # TODO(autopilot-code): driver.checks() 가 실 항목(symlink 존재·`--check` drift·
        # preflight 계약·bootstrap 스모크)을 채우기 전까지는 "미구현" 자리표시만 낸다.
        return [{"id": f"{runtime}.no-checks", "ok": True, "detail": "check 목록 미구현 (scaffold)"}]
    results = []
    for check in checks:
        results.append(check())
    return results
