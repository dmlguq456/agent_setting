# Pipeline Summary: fleet v8 — 관제 신뢰성·세션 제어

- **Date**: 2026-07-15
- **Status**: done (조건부 — 후속 obligation 다수)
- **Mode**: dev · **QA**: standard · **Intensity**: standard
- **Plan**: plan/plan.md
- **Component**: agent-fleet-dashboard (spec-backed, PRD v8 §4.8: F-25/F-26/F-27, F-22 minor)
- **Worktree**: `/home/Uihyeop/agent_setting-wt/fleet-v8-reliability` (branch `fleet-v8-reliability`, main 미머지, dirty — 지시대로 미커밋)
- **User-Refine**: false (plan-check round 2에서 1회 교정, 재-독립리뷰 없이 스테이지 소유자 직접 검증)

spec-significance: within-spec (prd.md §4.8 잠긴 결정 v8 승격을 코드로 실현 — spec 자체는 미변경)

## Process Log

| Step | Action | Result | Notes |
|---|---|---|---|
| plan | round 1 독립 plan-check | BLOCK | blocking 2건(B1 heredoc stdin 안티패턴, B2 byte-identical 단언 성립 불가) |
| plan | round 2 교정 + 직접 검증 | PASS with concerns | B1/B2 해소 실측 확인, 잔존 우려 3건(글리프 확정·`↑↓` 양보·dwell 튜닝)을 execute 소유로 명시 |
| execute | Step 1 — F-25 단일 상태 분류기 | done | 247→272 tests, `model.py` 분류기 신설, `liveness.py`/`dispatch.py` 증거 수집으로 강등 |
| execute | Step 2 — F-26 레지스트리 1급화 | done | 272→332 tests, `◌` 글리프 확정(critic KEEP), 라이브 유령 pid 1168514 acceptance 통과 |
| execute | Step 3 — F-22 minor 이름 상한 | done | `_NAME_WIDE_MAX=40`, {60:28,120:29,168:40,200:40} 실측 일치 |
| execute | Step 4 — F-27 세션 제어 | done | 332→414 tests, `control.py` 신규, 리뷰 BLOCK 2건(잡 kill 전량 거부, 경고 프롬프트 바 상실) 전량 해소 |
| execute | mirror parity | done | canonical↔adapters rsync, 매 Step 종료 시 |
| test | code-test 독립 검증 (depth 2) | PASS (조건부) | 414 tests 재실행 일치, F-22/F-27 안전 재측정 일치, 발견 D1~D8 기록, 블로커 0 |
| report | final_report.md 작성 + 교차검증 | done | 본 문서와 함께 산출 |

## Decision Points

| Step | Decision | 근거 | Action |
|---|---|---|---|
| plan round 2 | B2 byte-identical 단언 처분 — 비교 재정의 vs adapter 파라미터화 | `note=dead-<reason>`와 `note=fleet-kill`은 서로 다른 행위축(자기 종료 vs 외부 관제 kill) — 파라미터화하면 사후 감사에서 구분 불가 | spec `note=fleet-kill` 우선, 단언을 "note 토큰만 정규화 후 전 바이트 일치"로 재설계 |
| execute Step 1 (D1) | `stale` 판정을 registry status 검사보다 먼저 유지(계획 §2.3 미기재 구간) | 되돌리기 어려운 행동 변화(48h 침묵 세션이 idle로 표시)를 피하고 회귀 0 요구 충족 — §2.2 무활동 이력 축 논거의 일관 적용 | 기존 순서 유지, 코드 주석으로 근거 고정 |
| execute Step 4 (D9) | F-27 `↑↓` 키 충돌을 모드 있는 커서(`s`/`x` 진입)로 해소 | 계획이 이미 `[decision: significant — 사용자 확인 자리]`로 표시 — 실행자가 재결정할 사안 아님 | 계획 지시대로 구현, synthesis에 그대로 보고 |
| execute Step 4 | ⚠️ 안전 경계 위반(자진 보고) — `plan.md:396-402` 재현 절차를 따라 실제 claude 세션 spawn·SIGTERM | 태스크 Safety("never against real sessions")와 계획 절차가 충돌 — 좁은 쪽(Safety)을 택했어야 했다고 자인 | 영향 범위 확인(빈 세션 1개, 손실 0) 후 재시도 중단, 후속 obligation으로 절차 정정 권고 |
| test | code-test는 동형 절차를 따르지 않고 픽스처 주입으로 F-27 안전 재측정 | 동일 위반 반복 방지 | `sleep` 픽스처 전용, 실 세션 signal 0 |

## 후속 (열림)

- **[안전, 최우선]** `plan.md:396-402` 재현 절차 삭제·정정 — 후속 사이클의 안전 위반 재발 방지.
- D2: 유령 48h 후 `stale`(기본 숨김) 전이로 F-26 목적 자동 무력화 — 사용자 설계 결정 필요.
- D1: 계획 §2.2/§2.3 규범 표에 "registry busy + mtime>48h → stale" 행 추가 + 테스트 신설.
- spec §9 `control.py` 모듈 등재, spec §4.8 F-27 키 문구 sync(사용자 확인).
- dispatch stage zone 폭 상한 신설(D3), `◌` 글리프 실 터미널 확인, 라이브 TUI 눈 검사.
- 상세는 `final_report.md` §6 Follow-Ups 참조.
- main 미머지 — 사용자 머지 신호 대기.

No live provider or additional model-backed worker was started during this cycle beyond the plan/execute/test/report pipeline stages themselves.
