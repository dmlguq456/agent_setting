# 병합 검증 보고서

## 대상

- 계획: `.agent_reports/plans/2026-07-20_memory-oncall-promotion-merge/plan/plan.md`
- 병합 커밋: `eaaa89225d19fa9e4a8691a2abba65625cd1fc42`
- 깨끗한 검증 작업 트리:
  `/home/Uihyeop/agent_setting-wt/memory-oncall-promotion-merge`
- 검증 기준: 병합 커밋과 `origin/main`의 동기화 전후

## 병합 후 재검증

1. 기능·회귀 테스트

   ```text
   adapters/codex/bin/preflight.sh verification-runner --timeout 180 -- \
     python3 -m unittest tools.improvement.test_proposals
   ```

   결과: `24/24 PASS` (`Ran 24 tests in 1.428s`, `status=ok`).

2. 생성물·diff 검사

   ```text
   python3 tools/build-manifest.py --check
   python3 tools/generate.py --check
   git diff --check
   ```

   결과: manifest 최신, delta baseline 결속, 12개 core projection group
   일치, whitespace 오류 없음.

3. 어댑터 경계

   ```text
   bash tools/check-adaptation-boundary.sh
   ```

   결과: `PASS`. portable 영역의 기존 concrete Claude/model reference
   108개 경고는 허용된 mapping/compat 경계이며 이번 변경의 실패가 아니다.

## 병합 전 확장 검증

- generated projection semantic verifier: `29/29 PASS`
- portable guard suite: `355/355 PASS`
- Skill conformance: `PASS`
- runtime activation: `PASS`
- extension lifecycle: `PASS`
- managed release: `PASS`
- Python 및 shell 구문 검사: `PASS`

첫 adaptation 검사는 generated-projection 테스트가 의도적으로 파일을
변형·복구하는 구간과 겹쳐 stale 경고를 냈다. 두 검사를 분리한 재실행에서
생성물 diff 없이 통과했으므로 실제 drift로 판정하지 않았다.

## 범위·안전성 확인

- 병합 인덱스는 선택한 소스 16개와 승인된 스펙 8개만 포함했다.
- `35a0c75d`의 `daily-curator`, 자동 memory lifecycle, hard-coded 사용자
  경로는 병합하지 않았다.
- 당시 별도 작업 중이던 `dispatch-headless.py` 수정 2개와 drill 케이스
  2개는 이 병합 인덱스에 스테이징하거나 수정하지 않았다. 병합 이후 해당
  작업은 동시 workflow에서 별도 커밋 `d04ee778`로 완료됐다.
- 실제 on-call/drill 실행, runtime config·credential·session·cache 직접
  수정은 수행하지 않았다.

## 최종 판정

`PASS` — 선택 병합 결과는 계획의 기능·경계·회귀 게이트를 충족한다.
