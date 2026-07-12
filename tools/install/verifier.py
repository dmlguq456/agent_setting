"""verifier.py — Migration Order 수동 검증(~260줄)의 기계화 (PRD "verify" 명령).

check 목록을 실행해 pass/fail 을 돌려준다. 실제 check 항목(projection 링크 존재·생성기
`--check` drift·preflight 계약·bootstrap 로드 스모크)은 각 channel driver 가 정의한다
(drivers/*.py `checks()`). 이 모듈은 공통 실행기(runner)와, driver 들이 재사용할 공통
check 빌더(`check_symlink`/`check_cmd`/`check_file_exists`)를 둔다 — 모두 read-only.
"""

import subprocess
from pathlib import Path


def check_symlink(check_id, dest, expected_source):
    """dest 가 symlink 이고 expected_source 로 resolve 되는지 확인하는 0-인자 콜러블을 만든다."""

    def _check():
        dest_path = Path(dest)
        expected = Path(expected_source)
        if not dest_path.is_symlink():
            return {"id": check_id, "ok": False, "detail": f"symlink 아님 또는 부재: {dest_path}"}
        try:
            resolved = dest_path.resolve()
        except OSError as exc:
            return {"id": check_id, "ok": False, "detail": f"resolve 실패: {exc}"}
        expected_resolved = expected.resolve() if expected.exists() else expected
        if resolved != expected_resolved:
            return {
                "id": check_id, "ok": False,
                "detail": f"symlink target 불일치: {dest_path} -> {resolved} (기대: {expected_resolved})",
            }
        return {"id": check_id, "ok": True, "detail": f"symlink OK: {dest_path} -> {resolved}"}

    return _check


def check_cmd(check_id, argv, must_match=None, cwd=None):
    """argv 를 read-only subprocess 로 실행하고, exit 0 + (있다면) stdout 정규식 매칭을 확인한다."""
    must_match = must_match or []

    def _check():
        try:
            result = subprocess.run(
                argv, capture_output=True, text=True, cwd=cwd, timeout=60,
            )
        except FileNotFoundError as exc:
            return {"id": check_id, "ok": False, "detail": f"실행 불가: {exc}"}
        except subprocess.TimeoutExpired:
            return {"id": check_id, "ok": False, "detail": f"timeout: {' '.join(argv)}"}
        if result.returncode != 0:
            return {
                "id": check_id, "ok": False,
                "detail": f"exit={result.returncode} stderr={result.stderr[:300]!r}",
            }
        import re
        for pattern in must_match:
            if not re.search(pattern, result.stdout, re.MULTILINE):
                return {
                    "id": check_id, "ok": False,
                    "detail": f"패턴 불일치: {pattern!r} (stdout 일부: {result.stdout[:300]!r})",
                }
        return {"id": check_id, "ok": True, "detail": f"OK: {' '.join(argv)}"}

    return _check


def check_file_exists(check_id, path):
    """path 파일 존재 여부만 확인하는 0-인자 콜러블을 만든다."""

    def _check():
        exists = Path(path).exists()
        return {
            "id": check_id, "ok": exists,
            "detail": f"{'존재' if exists else '부재'}: {path}",
        }

    return _check


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
