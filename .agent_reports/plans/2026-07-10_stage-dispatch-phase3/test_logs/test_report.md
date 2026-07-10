# stage-dispatch Phase 3 — 검증 보고 (code-test)

Level 4 (functional) — 신규 동작 실측 + 회귀 무결.

## 결과 요약

| 스위트 | 결과 | 커버 |
|---|---|---|
| `dispatch-headless.sd15.test.sh` | **PASS** | scan_death 패턴/reset 추출, limit-death → row done,note=dead-<사유>,reset, reset 캐시, clean-exit 는 row 불변 |
| `usage-check.test.sh` | **PASS** | limited(reset)/ok/unknown/만료/harness 스코프 5케이스 |
| `dispatch-concurrency.test.sh` (SD-16d) | **PASS — 병렬 성립** | 3워커 동시 open row·liveness 3-ALIVE·dispatch-wait 다중자식·Σ상한 비강제 |
| `dispatch-liveness.test.sh` (회귀) | PASS | runtime-root 판정 불변 |
| `dispatch-wait.test.sh` (회귀) | PASS | 6 conformance |
| `check-adaptation-boundary.sh` | 신규 FAIL 0 | 잔존 1건 = `adapters/claude/tools/fleet/tests/test_f14_title.py`(기존 baseline, HEAD 에도 부재, fleet 타 세션 소유) |
| `build-manifest.py --check` | up-to-date | delta baselines bound |

전체 로그: `full_suite.txt`, `sd16d_concurrency.txt`.

## SD-16(d) 다축 동시성 — 계약 vs 실측

계약(WORKFLOW §1.1·OPERATIONS §5.10 ④)이 명시한 "thorough/adversarial 에서 다축 depth-2 perspective/verifier/adversary 워커 병렬"이 실제 성립하는지 소형 fixture(fake `claude` sleep, 실제 wrapper 분사)로 검증:

1. **병렬 분사 성립** — 같은 parent 로 3워커 분사 시 jobs.log 에 3개 open row 동시 존재.
2. **병렬 실행 성립** — dispatch-liveness 가 3워커 동시 ALIVE 판정(각 transcript 독립 갱신).
3. **다중-자식 대기 의미론** — dispatch-wait `--parent` 가 실행 중 "자식 3개" 보고(exit 2), 종료 후 exit 0(수확).
4. **Σ 상한 비강제(drift 아님)** — wrapper 는 동시 분사 수를 게이트하지 않음. Σ≤5 강제는 계약상 conductor 큐잉 책임(§5.10 ⑤)이며 wrapper 층 아님 → 설계대로. **병렬 drift 없음.**

⇒ 계약의 병렬 전제는 실측 성립. 고칠 것 없음.

## 재검증 (conductor)
- SD-15 end-to-end: fake session-limit `claude` 분사 → `early_death=session-limit`·row `done,note=dead-session-limit,reset=3pm`·`usage-check` → `claude limited(3pm)` 실측.
- negative: clean 조기 exit 는 row `open` 유지(정상 harvest 소유) — 오탐 없음.
