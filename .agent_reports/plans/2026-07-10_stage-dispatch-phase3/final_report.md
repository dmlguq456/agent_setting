# stage-dispatch Phase 3 — 최종 보고

브랜치 `stage-dispatch-phase3`. SoT = `spec/stage-dispatch/prd.md` v3(SD-15·SD-16). core-first 준수(OPERATIONS §5.10 먼저 → adapter/utility/skill 파생).

## 무엇을 했나

**SD-15 — wrapper limit-사망 즉시 감지**: `dispatch-headless.py` 가 launch 직후 짧은 워치(`--early-exit-watch`, 기본 8s)에서 자식 조기 exit + 로그의 limit/auth 패턴을 감지하면 jobs.log row 를 `done,note=dead-<사유>`(+`reset=<시각>`)로 즉시 마감하고 사유·reset 을 stdout 에 표면화, reset 캐시 기록. `dispatch-liveness`/`dispatch-wait` 도 open row 로그의 limit 패턴을 transcript-mtime 무관 DEAD 근거에 추가. **재시도 없음**(orchestrator 판단 구간).

**SD-16 — 사용량-인지 상호보완 크로스 하네스 분사**:
- (a) `utilities/usage-check.sh` — harness 별 `{ok|limited(reset)|unknown}`. runtime-currentness 조사 결과 공식 스크립트 표면 부재(Claude `/usage`·Codex `/status` 대화형뿐, Codex 는 openai/codex#15281 open) → jobs.log dead-limit 마커 + reset 캐시 기반 **보수 조회**, 한계 명시.
- (b) 상호보완 라우팅 계약 명문화 — OPERATIONS §5.10 ⑧(core) + dev-pipeline dispatch 절(파생): 사용량 failover(막힌 하네스 회피·codex preflight 우회) + 특성 강점 배치 + 검증 자리 타 모델 계열 교차(codex-review-team 선례). 초기 가중 = limit 회피 > 적합 > 분산(SD-OPEN-3).
- (c) cross-harness row 연속성(`harness=`/`owner_harness=`/`parent_sid`) 유지 실측 확인.
- (d) **thorough+ 다축 동시성 실측 검증 — PASS(병렬 성립)**: 실제 depth-2 워커 3대 동시 분사 fixture 로 동시 open row·3-ALIVE·dispatch-wait 다중자식·Σ상한 비강제 확인. 계약 vs 실측 drift 없음.

## 변경 파일

**소스**
- `adapters/claude/bin/dispatch-headless.py` — SD-15 감지·마감·표면화 + `--early-exit-watch`.
- `utilities/dispatch-liveness.sh` — 로그 limit 패턴 DEAD 근거.
- `utilities/dispatch-wait.sh` — 로그-limit DEAD 상속 명문화.
- `utilities/usage-check.sh` (신규) — SD-16(a) 보수 조회 헬퍼.
- `core/OPERATIONS.md` §5.10 — ⑧ 크로스 하네스 라우팅 + ⑨ limit-감지 계약(core-first).
- `skills/autopilot-code/references/dev-pipeline.md`(+adapter 미러) — cross-harness·self-close 절.
- `tools/check-adaptation-boundary.sh` — 신규 utility 3종 projection 분류.
- `adapters/claude/utilities/{usage-check.sh,usage-check.test.sh,dispatch-concurrency.test.sh}` (신규 심링크 projection).

**테스트(신규)**
- `adapters/claude/bin/dispatch-headless.sd15.test.sh`, `utilities/usage-check.test.sh`, `utilities/dispatch-concurrency.test.sh`.

**산출물**: `plans/2026-07-10_stage-dispatch-phase3/{plan/plan.md, _internal/metrics.md, test_logs/}`.

## 검증

- 신규 3 스위트 + 회귀 2 스위트 전부 PASS. `check-adaptation-boundary.sh` 신규 FAIL 0(잔존 1 = fleet baseline, 범위 외). `build-manifest.py --check` up-to-date.
- 재현: `bash adapters/claude/bin/dispatch-headless.sd15.test.sh` · `bash utilities/usage-check.test.sh` · `bash utilities/dispatch-concurrency.test.sh` · `bash tools/check-adaptation-boundary.sh`.

## 한계·이월

- **오케스트레이션 방식**: 이 사이클은 분사 인프라 자기수정이라 스테이지 분사 대신 inline 실행(SD-16d 검증만 실제 병렬 분사). 계약과의 예외 판단을 `_internal/metrics.md` 에 명시(은폐 안 함). 다음 일반 사이클은 스테이지 분사 복귀.
- **SD-15 codex/opencode wrapper 동형** 미착수 — ADAPTATION disclosure 로 이월(claude wrapper 만 구현).
- **usage-check 한계**: 공식 표면 부재로 `ok`=가용 보장 아님(알려진 차단 없음). 공식 headless 사용량 API 등장 시 승격.
- **SD-OPEN-1/2/3** 미결 유지 — 계측 누적만.

merge·worktree 정리는 main orchestrator 소관(이 turn 자체 머지 안 함).
