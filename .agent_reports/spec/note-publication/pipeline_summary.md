# note-publication — Spec Pipeline Summary

## v1 — DB-gated final note topology (2026-07-30)

`autopilot-note` 후속 단계를 결과 파이프라인의 마지막 postcondition으로 봉인하되,
사용자의 원격 note DB에 대한 bounded read-only live probe가 성공한 경우에만 필수로
실행한다. 미설정·로컬 fallback·인증/네트워크 실패는 `db-unavailable` skip이며 원
산출물의 성공을 무효화하지 않는다.

초기 적용 대상은 code, draft, lab setup/eval, refine, research다. direct/quick은
각각 `inline`/`one-shot`, standard+는 선언된 terminal node 뒤에 follow-up을 실현한다.
이는 owner postcondition이므로 dispatch depth를 추가하지 않는다.

피드백에 따른 보고서 수정은 canonical source 경로를 유지해 같은 note를 upsert한다.
note identity와 사용자/DB 소유 routing 필드는 보존하고 agent-derived 본문과 run/source
revision 정보만 갱신한다. snapshot이나 diff-preview는 새 note identity가 아니다.

## 구현 결과

portable contract, topology schema v6, route sealing, Codex/OpenCode preflight,
공유 readiness probe와 projection을 구현했다. topology 25개, route 40개 테스트,
readiness fixture, generated projection 회귀 및 adaptation boundary가 통과했다.
현재 runtime은 `WORKLOG_BOARD_APP` 미설정으로 `skipped/db-unavailable`이며,
이 상태가 spec대로 원 결과를 실패시키지 않음을 확인했다.
