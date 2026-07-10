# final_report — stage-dispatch v4 정련 (SD-15b·SD-16e·SD-11b)

> 사이클 `2026-07-10_sd-v4-refine` · 브랜치 `sd-v4-refine` · inline opt-out 실행(자기수정 사이클, metrics.md)

## 요약

도그푸딩 실측 3건을 정련. SD-15b 로그-패턴 DEAD 오탐 앵커링(3어댑터), SD-16e usage-check reset 의미론,
SD-11b reminder→deny 상향. 신규·기존 스위트 신규 FAIL 0.

## 변경 파일

| 파일 | 결정 | 내용 |
|---|---|---|
| `utilities/dispatch-liveness.sh` | SD-15b | 로그-death 스캔을 `scan_log_death()`로 앵커링(말미 3줄·≤200자 단독 라인). 루프 재정렬 — transcript 먼저, 신선하면 ALIVE(로그 미조회), stale/부재일 때만 로그로 limit 사유 판정. |
| `adapters/codex/bin/dispatch-liveness.py` | SD-15b | `log_shows_limit` 앵커링(비어있지 않은 말미 3줄·≤200자). main 루프 재정렬(transcript 우선, 신선=ALIVE). |
| `adapters/opencode/bin/dispatch-liveness.py` | SD-15b | 동형. 신선 SQLite/heartbeat 신호가 로그를 이김. stale·no-fresh 시에만 앵커링 로그 스캔. |
| `core/OPERATIONS.md` §5.10 ⑨ | SD-15b | 로그-패턴 판정 앵커링(짧은 말미 CLI 에러 라인 한정 + 신선 transcript 완주 신호면 DEAD 배제) 명문화. |
| `utilities/usage-check.sh` | SD-16e | `reset_to_epoch()` 추가(3pm/noon/15:45 파싱, 마커 이후 첫 도래). reset 경과→`ok`, reset 부재→`UNKNOWN_WINDOW_MIN`(60m) 안 `limited(unknown-reset)`·밖 `ok`. 헤더 판정표 갱신. |
| `core/OPERATIONS.md` §5.10 jobs.log 하드 계약 | SD-16e(c) | 수동 row 마감 시 `reset=<시각>` 기입 의무 명문화. |
| `hooks/stage-dispatch-reminder.sh` | SD-11b | reminder→deny 상향. [child·depth1·standard+·code-* Skill]→hard deny(hook JSON permissionDecision / CLI stderr+exit2). `STAGE_DISPATCH_INLINE_OK=1`→soft reminder. intensity 불명(구 wrapper)→reminder(deny 금지, 하위호환). |
| `utilities/dispatch-liveness.test.sh` | SD-15b | 신규 3케이스(fresh-transcript 배제·terse-line DEAD·prose 앵커링 미매치). |
| `utilities/usage-check.test.sh` | SD-16e | reset 시각 동적 산출(실행시각 비의존) + 신규 4케이스. |
| `hooks/portable-guards.test.sh` | SD-11b | SDR 섹션 재작성 — deny·opt-out·intensity 불명 3분기(7케이스). |

### SD-11b(a) 확인 사항
`AGENT_DISPATCH_INTENSITY` 자식 env 주입은 이미 3어댑터 dispatch-headless.py 에 존재(SD-15 이식분: claude:524·codex:571·opencode:463).
**추가 편집 불필요, ADAPTATION 불필요** — deny 결정론 조건이 이미 확보돼 있었다.

## 검증

- `dispatch-liveness.test.sh` PASS · `usage-check.test.sh` PASS.
- `portable-guards.test.sh` PASS=313 FAIL=12 (baseline HEAD=311/12 stash 대조 → **신규 FAIL 0**, +2 통과).
  잔존 12 = baseline: liveness.sh state-transition 4(테스트 환경 PROJ 전제, HEAD 동일 출력) + codex/opencode 런타임 프로젝션 8.
- `check-adaptation-boundary.sh` FAIL=2 (fleet 소유 baseline, 범위 외).
- adapter .py py_compile OK. `__pycache__` 정리 완료.

## 산출물 경로
- plan: `.agent_reports/plans/2026-07-10_sd-v4-refine/plan/plan.md`
- metrics: `.agent_reports/plans/2026-07-10_sd-v4-refine/_internal/metrics.md`
- dev_log: `.agent_reports/plans/2026-07-10_sd-v4-refine/dev_logs/step_impl.md`

## 제외 준수
`loops/**` · `tools/fleet/**` 무수정. main 머지·worktree 정리는 오케스트레이터(메인) 몫.
