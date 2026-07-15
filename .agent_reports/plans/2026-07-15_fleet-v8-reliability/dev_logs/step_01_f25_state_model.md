# Step 1 — F-25 단일 상태 분류기 (dev log)

- **사이클**: 2026-07-15 fleet-v8-reliability · stage=code-execute (depth 2)
- **safety commit**: `8dd0c062a58fd61827cc9c3f1d7c7be63b8a7aa8` (진입 시 worktree clean)
- **기준선**: 247 tests OK (14.4s) · python 3.8.10
- **종료 상태**: **272 tests OK** (247 + 신규 25) · 회귀 0

## 변경 파일

| 파일 | 변경 |
|---|---|
| `tools/fleet/model.py` | §2.4 상수 블록 + `StateTracker` + `classify_session()`/`classify_job()`/`reset_state_tracker()`/`tracker_sweep()` 신설. `LIVENESS_STATES`에 `unused` additive. `Session`에 `proc_start`/`registry_proc_start`/`started_at`/`updated_at`/`registry_name`/`kind`/`provenance`/`state_evidence` 추가, `DispatchJob`에 `state_evidence` 추가 (전부 Optional=None) |
| `collectors/liveness.py` | `classify()`를 증거 수집기로 강등 — `collect_evidence()` + `_proc_evidence()`(start-time 재검증) 신설, 판정은 `model.classify_session()` 위임. **시그니처·리턴 계약 유지** |
| `collectors/dispatch.py` | `_dispatch_liveness()` 위임 + `_job_transcript_signal()` 분리(증거 수집만). `_QUEUED_GRACE_MIN` → `model.JOB_QUEUED_GRACE_MIN` 참조(이중화 제거). `_reconcile_drill_rows()` 흡수 → 증거 병합. `collect()` 순서 재배치 |
| `collectors/procscan.py` | `read_proc_start()`/`provenance()` 신설, `Session.proc_start` 적재 |
| `collectors/claude.py` | `read_registry()`/`_apply_registry()` 추출(Step 2 선착륙 — `unused` 증거가 여기 의존), `_has_transcript`/`_mtime_from_registry` 표식 |
| `collectors/__init__.py` | tick 종료 시 `model.tracker_sweep()` GC |
| `tests/test_f25_state_model.py` | **신규** 25 tests |
| `tests/fixtures/state_model/*.json` | **신규** 9 픽스처 |
| `tests/test_f18_attribution.py` | 단언 2건 갱신 (아래 D2) |

## Decision

### D1 — `stale` 판정을 registry status보다 먼저 유지 (계획 §2.3 표의 미명시 구간 해소)

계획 §2.3 표는 tier-1 registry status가 이긴다고 규범화했지만, **status가 있으면서 mtime이 48h 초과인 행**은 표에 없다. 기존 `liveness.classify()`(원본 :58-63)는 `age_min > stale_min` 을 status **이전에** 검사했다 — 즉 status=idle 이어도 48h 침묵이면 `stale`.

- **선택**: 기존 순서 유지 (`stale` 검사 → status).
- **근거**: §2.2가 세운 논거를 그대로 적용하면 정합적이다. `stale`은 **무활동 이력 축**의 판정이고, 이는 `unused`가 `idle`을 좁히는 것과 **같은 축의 정제**다 (`unused` = "한 번도 활동 없음", `stale` = "48h간 활동 없음"). 활동성 축(`busy`/`idle`)을 뒤집는 것이 아니므로 §2.1 불변식을 깨지 않는다.
- **대안(status 우선)을 기각한 이유**: 되돌리기 어려운 행동 변화(48h 침묵 세션이 `idle`로 표시)를 낳고, 회귀 0 요구와 충돌한다. 기존 순서 유지 = 가역적·무회귀.
- 코드에 근거 주석으로 고정(`model.py` classify_session 내 stale 분기).

### D2 — `test_f18_attribution` 단언 2건 갱신 (아키텍처 이동에 따른 필연)

계획은 `dispatch.py:924`의 `r.liveness = p.liveness` **소멸**을 요구하고(재배치 가드: 대입 정확히 2곳), 최종 판정을 병합 후 `classify_job()` 1회로 옮긴다. 그런데 기존 테스트는 `_reconcile_drill_rows()` **직후** `registry.liveness == "working"`을 단언했다 — 이 단언은 "reconcile이 곧 판정자"라는 옛 구조에 묶여 있다.

- **처분**: 같은 **행동**(live proc = ground truth)을 **종단으로** 단언하도록 갱신 — `jobs[0]._proc_liveness == "working"`(증거 흡수 확인) + `dispatch._dispatch_liveness(jobs[0], now=0) == "working"`(분류기 판정) + `state_evidence["tier"] == 2`.
- **약화 아님**: 옛 단언보다 강하다 — 흡수·판정·tier 근거 3축을 검사한다. 테스트 수 불변(247→247 baseline 유지).

### D3 — `registry_proc_start` 필드 신설 (계획 미명시, 실측으로 발견)

계획 §3 편집 표면은 `Session.proc_start` 하나만 명시했으나, PID 재사용 가드는 **두 값의 대조**를 요구한다 — registry의 `procStart` **주장**과 `/proc/<pid>/stat` field 22 **실측**. 하나의 필드로는 자기 자신과 비교하게 되어 가드가 항상 통과한다(무의미).

- **처분**: `proc_start`(실측) + `registry_proc_start`(주장) 2필드로 분리. 둘 다 additive Optional.
- **실측 확인**: 유령 pid 1168514 → 주장 `3918896` == 실측 `3918896` → `proc_start_match=true` → 가드 통과 → `unused` 도달. (불일치했다면 `dead`로 오분류될 뻔했고, 이 실측 없이는 발견 불가했다.)

### D4 — `_reconcile_drill_rows`를 분류 루프 **앞**으로 이동

대입 2곳 제약상 reconcile 후 재분류가 불가능하므로, reconcile을 분류 **이전**에 두고 그 안에서 proc 행의 상태를 `_dispatch_liveness(p, now)` **지역 계산**으로 얻어 registry 행에 `_proc_liveness` 증거로 stash한다. 기존 호출자(`_reconcile_drill_rows(jobs)` 1-arg, 테스트)는 `now=None` 기본값으로 무회귀.

## 검증 결과 (계획 §3 검증 1–7 전량)

| # | 명령 | 결과 |
|---|---|---|
| 1 | `python3 -m unittest tools.fleet.tests.test_f25_state_model` | **Ran 25 tests — OK** |
| 2 | `python3 -m unittest discover -s tools/fleet/tests -t . -q` | **Ran 272 tests — OK** (기준선 247 + 25, 회귀 0) |
| 3 | `--json` smoke + additive 단언 | **OK** — sessions 10 / jobs 3, 전 행 `state_evidence` 보유, `ev.state == liveness` 전행 일치, `derived ⇔ tier==3` 전행 성립. tier 분포 `{1: 5, 2: 0, 3: 5}` |
| 4 | ★ 재배치 가드 `.liveness = ` 대입 수 | **정확히 2곳** — `dispatch.py:1017`(위임), `__init__.py:149`(위임). `dispatch.py:924` 소멸 확인 |
| 5 | 3.8 문법 가드 (`ast.parse` + `--version`) | **OK** — 6파일 파싱 통과, Python 3.8.10 |
| 6 | `COLUMNS={60,120,168} --once` 실제 렌더 | **OK** — 아래 §관측 참조. 상태 문자열이 §2.3 어휘 밖으로 새지 않음 |
| 7 | mirror parity | **OK** — rsync 후 `test_mirror_parity` 통과 |

### 검증 3 — `--json` 실측 (유령 세션)

```json
"pid": 1168514, "liveness": "unused", "registry_name": "agent-setting-17",
"proc_start": "3918896", "registry_proc_start": "3918896",
"started_at": 1784083189.482, "updated_at": 1784083189.601,
"state_evidence": {
  "state": "unused", "tier": 1, "source": "claude-registry",
  "rule": "idle refined to unused (no transcript, updatedAt≈startedAt)",
  "derived": false,
  "inputs": {"pid_alive": true, "proc_start_match": true, "status": "idle",
             "transcript": false, "activity_ms": 118.99995803833008},
  "raw_status": "idle", "hysteresis": null}
```

→ **F-25 층에서 F-26 acceptance의 판정 절반이 이미 성립.** `raw_status:"idle"`이 보존된 채 `unused`로 좁혀졌다 = §2.2 축 분리가 코드로 실현됨(모순이 아니라 정제).

### 검증 6 — 실제 렌더 관측 (눈 리뷰)

전 세션 tier 분포와 rule (실측):
```
pid=113926   claude    idle     tier=1  registry status=idle
pid=224511   codex     idle     tier=3  no activity within 60s
pid=1168514  claude    unused   tier=1  idle refined to unused (no transcript, updatedAt≈startedAt)
pid=1680590  claude    idle     tier=1  registry status=shell
pid=2157581  codex     idle     tier=3  no mtime and no registry status
pid=2222224  claude    working  tier=3  activity within 60s
```

**관측된 중간 상태 (Step 2가 해소 — 의도된 것)**: 168열 렌더에서 유령 행이
```
▍ · claude code     agent-setting-17 tracked    main   Fable 5 (xhigh)   ────────────  —   3h45m
```
글리프 **`·`** 로 찍힌다 — `_LIVE_GLYPH`에 `unused` 엔트리가 없어 `.get(state,"·")` 폴백이 stale과 **동일 글리프**를 준다. 계획 §2.3 각주가 예고한 바로 그 현상이며, Step 2의 `_LIVE_GLYPH["unused"]` 신설이 해소한다. Step 1 종료 시점에 이는 **회귀가 아니라 미완**이다(직전에는 `●` idle로 유령임이 아예 안 보였고, 지금은 최소한 idle과 구분은 된다).

**F-22 회귀 실측 확인 (Step 3 대상)**: 168열에서 `trackedmain` — name zone 77열이 branch 컬럼을 잡아먹어 gate 배지와 branch 사이 공백이 사라졌다. 계획 §1.3 실측(`168→77`)과 정확히 일치하며 Step 3의 40 상한이 해소한다.
`_wide_name_width` 실측 = `{60: 28, 120: 29, 168: 77, 200: 109}` — 계획 §1.3 표와 1:1 일치.

## 잔존 우려 처분

- **우려 3 (dwell 90/300s 제안값)**: Step 1 시점에서 **변경 없이 유지**. 근거 — 픽스처가 경계를 고정했고(`flap_60s_boundary` tier-3 dwell 적용 / `flap_registry_tier1` tier-1 즉시), plan-check N1의 **tier 게이트**(`HYST_APPLIES_TO_TIER=(3,)`)가 R6의 실제 위험(“일 끝났는데 계속 working”)을 원인 층에서 제거한다. 실측: 현재 라이브 10세션 중 tier-3은 5개이고 dwell 보류(`hysteresis != null`)는 **0건** — 90s가 체감을 해치는 증거가 아직 없다. 라이브 관찰은 Step 4 TUI 검증에서 재평가.
