---
slug: 2026-07-10_stage-dispatch-phase3
capability: autopilot-code
mode: dev
qa: standard
intensity: strong
status: done
spec: .agent_reports/spec/stage-dispatch/prd.md
scope: SD-15 (limit-death detect) · SD-16 (usage-aware cross-harness) · SD-16(d) concurrency verification
---

# stage-dispatch Phase 3 — 구현 plan

SoT = `spec/stage-dispatch/prd.md` v3. 범위 = SD-15 + SD-16 + thorough+ 다축 동시성 실측.
core-first: 계약은 core/OPERATIONS §5.10 먼저 → adapter(wrapper)/utility/skill 파생.

## Phase A — core 계약 (core-first 선행)
- [x] `core/OPERATIONS.md §5.10`: ⑧ 사용량-인지 상호보완 크로스 하네스 라우팅(failover·강점 배치·검증 교차·조회 표면 한계) + ⑨ limit-사망 즉시 감지·마감 계약 추가.

## Phase B — SD-15 wrapper limit-death 즉시 감지 (realization)
- [x] `adapters/claude/bin/dispatch-headless.py`: `DEATH_PATTERNS`/`scan_death`(사유+reset 추출), `--early-exit-watch`(기본 8s), `watch_early_death`(launch 후 조기 exit 폴), `close_job_row`(row → done,note=dead-<사유>,reset=<x> under flock), `write_reset_cache`. `main` 배선 + 출력에 `early_death`/`row_closed` 표면화.
- [x] `utilities/dispatch-liveness.sh`: open row 의 dispatch 로그 `LIMIT_RE` 스캔 → transcript-mtime 무관 DEAD 판정.
- [x] `utilities/dispatch-wait.sh`: liveness 재사용이라 로그-limit DEAD 근거 자동 상속(헤더 명문화).

## Phase C — SD-16 사용량-인지 크로스 하네스
- [x] runtime-currentness 조사(WebSearch): Claude `/usage`·Codex `/status` 대화형뿐, 스크립트 표면 부재 확정.
- [x] `utilities/usage-check.sh`: harness 별 `{ok|limited(reset)|unknown}` — 보수 조회(jobs.log dead-limit 마커 + reset 캐시). 한계 헤더 명시.
- [x] `skills/autopilot-code/references/dev-pipeline.md`: cross-harness failover·강점 배치·검증 교차 + SD-15 self-close 절 추가(core 파생).
- [x] SD-16(c): row 연속성(harness/owner_harness/parent_sid) 유지 확인(append_job 불변, 테스트로 실측).

## Phase D — SD-16(d) thorough+ 다축 동시성 실측
- [x] `utilities/dispatch-concurrency.test.sh`: 실제 depth-2 워커 3대 동시 분사 → 동시 open row·liveness 3-ALIVE·dispatch-wait 다중자식·Σ상한 비강제 실측. **결과 PASS — 병렬 성립**(계약 vs 실측 drift 없음).

## Phase E — 테스트·projection·drift
- [x] `dispatch-headless.sd15.test.sh`·`usage-check.test.sh`·`dispatch-concurrency.test.sh` 신설, 전부 PASS.
- [x] projection: 신규 3 utility 를 `adapters/claude/utilities/` 심링크 + codex/opencode UTILITY_DEFERRED 등재. dev-pipeline 미러 byte-sync.
- [x] `check-adaptation-boundary.sh`: 신규 FAIL 0(잔존 1건 = 기존 fleet baseline, 범위 외). `build-manifest.py --check` up-to-date.

## 제외 (범위 밖)
- `loops/**`·`tools/fleet/**` (타 세션 소유). SD-15 codex/opencode wrapper 동형은 미착수(ADAPTATION disclosure 로 이월).
