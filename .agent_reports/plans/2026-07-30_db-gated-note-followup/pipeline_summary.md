# DB-gated note follow-up — Pipeline Summary

## 결과

`autopilot-note`를 결과 파이프라인의 조건부 최종 postcondition으로 봉인했다.
원격 note DB에 대한 bounded `SELECT 1` probe가 `connected`일 때만 실행이
필수이고, DB가 없거나 접근할 수 없으면 `skipped/db-unavailable`로 끝나며
원 산출물 성공에는 영향을 주지 않는다.

## 적용 범위

- topology schema v6에 code, draft, lab setup/eval, refine, research의
  `conditional_follow_ups`를 선언했다.
- direct/quick/standard+ 경로 컴파일러가 각각 실제 terminal anchor를 봉인하고
  변조된 follow-up metadata를 거부한다.
- lab setup/eval은 동일 `experiment-artifact`, research는 단일
  `research-artifact`를 canonical source로 사용한다.
- 피드백으로 같은 보고서를 다시 처리하면 note id와 사용자/DB 소유 필드를
  보존한 채 agent-derived 본문과 revision evidence만 갱신한다.
- readiness probe는 dotenv를 실행하지 않고 필요한 DB 키만 읽으며 URL, token,
  exception 본문을 출력하지 않는다.

## 검증

- topology tests: 25 passed
- route compiler tests: 40 passed
- readiness fixture suite: passed (성공, 미설정, 로컬 fallback, timeout,
  실패, 비밀값 비노출, dotenv 비실행)
- generated projection check: passed
- generated projection regression suite: passed
- adaptation boundary: passed (기존 portable-area warning 170건 유지)
- utility census, manifest check, shell syntax, `git diff --check`: passed

## Follow-up note cycle

현재 실행 환경의 live probe 결과는 `unavailable / worklog-board-app-unset`이다.
따라서 이 결과에 대한 automatic note publication은
`skipped/db-unavailable`이며 사용자 DB나 runtime 설정은 변경하지 않았다.
