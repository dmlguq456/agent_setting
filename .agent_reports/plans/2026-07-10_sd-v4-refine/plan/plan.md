---
slug: 2026-07-10_sd-v4-refine
mode: dev
intensity: standard
qa: standard
status: done
spec: .agent_reports/spec/stage-dispatch/prd.md §8.6 (v4)
---

# stage-dispatch v4 정련 — SD-15b · SD-16e · SD-11b

도그푸딩 실측 3건을 정련한다. 셋 다 분사 launch/liveness/gate 경로를 손대는 자기수정 — inline opt-out 부여됨(metrics.md).

## SD-15b — 로그-패턴 DEAD 판정 앵커링 (§8.6.1)

**문제**: 정상 완주 conductor 의 최종 보고문이 limit 을 _주제로_ 서술 → `LIMIT_RE` 가 로그 tail 본문에 매치해 DEAD 오탐.

**개정 (dispatch-liveness.sh + codex/opencode dispatch-liveness.py 3종 동형)**:
- (a) 로그-패턴 매치를 **말미 소수 라인의 짧은 단독 라인**으로 앵커링 — 실제 CLI 종료 에러 라인(예: 단독 "You've hit
  your session limit · resets 3pm")만 매치, 긴 보고문 산문은 배제.
- (b) **정상 완주 신호와 결합** — transcript 가 신선(≤ STALE_MIN)하면 완주/활성으로 보고 로그-패턴 매치가 있어도 DEAD
  배제. 로그-death 스캔은 transcript 가 stale/부재일 때만 사유 판정에 쓴다. (완주 세션은 종료 시점 transcript 가
  신선 → ALIVE 로 오탐 제거.)
- 회귀 fixture: "limit 를 논하는 보고문" 로그 + 신선 transcript → ALIVE/done 유지.

## SD-16e — usage-check reset 의미론 (§8.6.2)

**문제**: `reset=` 없는 dead 마커가 300분 창 내내 `limited(-)` — 실제 리셋 경과 후에도 해제 안 됨.

**개정 (usage-check.sh)**:
- (a) `reset=` 있는 마커 — reset 시각 파싱(3pm/noon/15:45) 후 경과했으면 `ok`(expired).
- (b) `reset=` 없는 마커 — **보수 창 단축(`UNKNOWN_WINDOW_MIN`=60) + `limited(unknown-reset)` 구분 표기 둘 다**.
  근거: reset 을 모르면 해제 시점을 확정 못 하므로 (1) 라벨로 "확인 필요"를 표면화하고 (2) 60분 뒤에는 근거 없는 차단을
  풀어 reset-less 마커가 5h 내내 하네스를 봉쇄하지 않게 한다. 스펙은 "택일" 이나 둘 다가 안전한 상위집합이라 채택.
- (c) 수동 row 마감 시 `reset=` 기입 의무를 core/OPERATIONS.md §5.10 jobs.log 하드 계약(96행)에 한 줄 명문화.
- 테스트: reset 경과 expired, reset 부재 구분(짧은 창 내 limited(unknown-reset)·창 밖 ok). 기존 3pm 케이스는
  실행 시각 비의존이 되도록 reset 을 now 상대(±N h)로 동적 산출하게 갱신.

## SD-11b — reminder → deny 상향 (§8.6.3)

**문제**: soft reminder(SD-11)가 문서-효력 2연속 실패 — 자기 발명 예외로 inline. 결정론 강제 필요.

**개정**:
- (a) wrapper env 주입 — `AGENT_DISPATCH_INTENSITY` 는 이미 3어댑터 dispatch-headless.py 에 존재(SD-15 이식분).
  추가 작업 없음(확인만). ADAPTATION 불필요.
- (b) `hooks/stage-dispatch-reminder.sh` deny 상향: [CHILD_SESSION=1 && depth==1 && intensity∈standard+ &&
  code-* Skill 직접 호출] → hard deny + "dispatch-headless.py 로 depth-2 분사하라" 피드백.
- (c) opt-out: `STAGE_DISPATCH_INLINE_OK=1`(orchestrator 명시 부여) 이면 deny 대신 기존 soft reminder.
  env 부재·intensity 불명(구 wrapper) 이면 deny 안 함 → reminder 유지(하위호환, false-positive 금지).
- deny 기전 = worktree-path-guard 선례: hook 모드 JSON `permissionDecision:deny`, CLI 모드 stderr `⛔`+exit 2.
- 테스트(portable-guards.test.sh): deny 조건·opt-out·intensity 불명 3분기 + 기존 soft 케이스 재정렬.

## 검증

- `utilities/dispatch-liveness.test.sh` · `utilities/usage-check.test.sh` · `hooks/portable-guards.test.sh` 전부 PASS.
- `tools/check-adaptation-boundary.sh` 신규 FAIL 0 (잔존 2 = fleet baseline, 범위 외).
- 테스트 __pycache__ 커밋 전 정리.

## 제외
`loops/**` · `tools/fleet/**` 수정 금지.
