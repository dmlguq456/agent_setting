# Phase A (F-25) code-review — correctness

- **사이클**: 2026-07-15 fleet-v8-reliability · mode=code-review (read-only)
- **대상**: `git diff 8dd0c062` @ `/home/Uihyeop/agent_setting-wt/fleet-v8-reliability`
- **판정**: **PASS-with-minor**
- **CRITICAL: 0건.** tier 모델 자체는 정확하다. 아래 F1은 코드 결함이 아니라 **트리 상태(mirror 미동기)** 문제이며, 커밋 전 반드시 해소해야 한다.

---

## 요약

계획 §2.1/§2.2/§2.3 대비 `classify_session()`은 **비-`unused` 입력 전 구간에서 구 `liveness.classify()`와 완전 동치**임을 차분 퍼즈로 실증했다(280조합, divergence 0). D1·D3 주장은 **코드로 참**이다. D2는 약화가 아니다. 재배치 가드(`.liveness =` 정확히 2곳)도 실측 통과.

다만 **현재 워크트리에서 전체 스위트는 RED**이며(F1), 스텝로그의 "272 tests OK, 회귀 0" 및 브리프의 전제는 지금 재현되지 않는다.

---

## F1 — `test_mirror_parity` 실패 · 트리 dirty (MINOR, 커밋 전 필수)

브리프/스텝로그 전제 "272 tests OK, 0 regressions"는 **현재 재현되지 않는다**:

```
Ran 272 tests in 14.335s
FAILED (failures=1)
FAIL: test_mirror_matches_canonical (tools.fleet.tests.test_mirror_parity)
AssertionError: 내용 상이: ['collectors/claude.py', 'render.py']
```

원인은 F-25 로직이 아니다. canonical `tools/fleet/render.py`·`collectors/claude.py`에 **Step 2(F-26) 내용이 이미 들어와 있고 mirror에는 rsync되지 않았다**:

- `tools/fleet/render.py:99` `"g_unused": ("y", _A_D)` / `:161-163` `_COLOR["g_unused"]` / `:290-291` `_GLYPH_KEY`에 `unused` / `:297-302` `◌` 글리프 — mirror에 전부 부재.
- `tools/fleet/collectors/claude.py:279-292` provenance 해석 블록(`procscan.provenance(sess.pid)`) — mirror에 부재.

부수 사실 2건:

1. `git status`상 **Phase A는 아직 하나도 커밋되지 않았다**(Step 1 파일 전부 `M`/`??`). 브리프의 "changed files" 목록에 `render.py`가 없는데 실제로는 `M tools/fleet/render.py`다 — 즉 **선언된 Phase A 표면 밖의 Step 2 작업이 같은 트리에 섞여 있다**.
2. 스텝로그 검증 7("mirror parity OK")은 Step 1 시점엔 참이었을 것이나, 이후 F-26 편집이 rsync 없이 얹히며 무효화됐다.

→ **처분**: 커밋 전 `rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/` 재실행. Phase A만 분리 커밋할 생각이라면 render.py/claude.py의 F-26 부분을 어느 스텝에 귀속시킬지 먼저 정해야 한다(현 상태로는 Step 1/2 경계가 트리에 없다).

---

## F2 — D1 검증 결과: **주장은 참** (지적 없음 · 근거 기록)

`git show 8dd0c062:tools/fleet/collectors/liveness.py`의 구 `classify()`와 신 경로를 차분 퍼즈로 대조했다 — `age ∈ {None,0,30,59.9,60,60.1,120,48h-1s,48h+1s,100h} × status ∈ {None,busy,idle,shell,compacting,"",BUSY} × orphan ∈ {F,T} × transcript ∈ {T,F}` = **280조합, divergence 0**.

브리프가 지목한 잠재 발산점 전부 무결로 확인:

| 의심 지점 | 결과 |
|---|---|
| stale-before-status (D1) | **참**. `model.py:389` `age_min > stale_min` 이 `:393` status 분기보다 앞 — 구 `:58-63` 순서 그대로. status=idle + 48h 침묵 → 신·구 모두 `stale`. |
| `_from_status` 미지 status 단어 | 동치. `_session_status_state("compacting")`/`""`/`"BUSY"` → `None` → mtime 휴리스틱 폴백(구 `_from_status`와 동일). |
| `mtime=None` + status 존재 | 동치. `model.py:379-386` = 구 `_from_status(status) or "idle"`. |
| orphan 순서 | 동치. `model.py:372` orphan → `stale`, dead 다음·status 앞. |
| `stale_min` 파라미터 전달 | 정상. `liveness.classify(sess, now, stale_min=)` → `classify_session(..., stale_min=stale_min)` → `:389`에서 실제 사용. |
| `SESSION_WORK_SEC` 경계 | 동치. 구 `age_min < 1.0` ≡ 신 `age_min*60 < 60`. 60.0s에서 양쪽 `idle`. |

유일한 발산은 **의도된 `unused` 정제뿐**이며(`status ∈ {idle,shell}` + `transcript=False` + `activity_ms ≤ 2000`), 축 가드도 실측 확인: `busy`+무transcript+0ms → `working`(좁히지 않음), status 부재+무transcript → tier-3 `working`(mtime만으로 `unused` 불가). 계획 §2.2 준수.

---

## F3 — D3 PID-reuse 가드: **정확** (지적 없음 · 근거 기록)

`procscan.read_proc_start()`의 field 22 인덱스 산술은 **옳다**. `data.rindex(")")` 이후 split → `rest[0]`=field 3(state), 따라서 field 22 = `rest[19]` — 코드 주석과 일치. comm에 공백/괄호가 있어도 `rindex`가 마지막 `)`를 잡으므로 안전. 실측 교차검증:

```
read_proc_start(self) = 5301359   |   cut -d' ' -f22 /proc/<pid>/stat = 5301359
```

`None`(증거 없음) vs `False`(양성 불일치) 구분도 정상 — 실측:

```
claimed=5301359    actual=5301359  -> idle   match=True
claimed=999999999  actual=5301359  -> dead   match=False     # fail CLOSED ✓
claimed=None       actual=5301359  -> idle   match=None      # 증거 부재 → 침묵 ✓
```

`model.py:368` 이 `is False`로 명시 비교하므로 `None`이 fail-open으로 새지 않는다. **fail-open 경로는 "증거 부재"뿐이고 이는 문서화된 의도**(`_proc_evidence` docstring: "absence of evidence is not evidence of mismatch"). 타당하다.

**D3 자체를 호평한다**: 계획이 `Session.proc_start` 1필드만 명시한 것은 실제로 결함이었고(자기 자신과 비교 → 가드 무의미), `registry_proc_start` 분리는 실측으로만 발견 가능한 필연적 교정이다.

---

## F4 — dwell 보류 중 `state_evidence`가 자기모순 (MINOR)

`model.py:353-362` `out()`은 hysteresis가 상태를 보류하면 `ev["state"]`만 덮어쓰고 `tier`/`rule`/`source`/`derived`는 **억제된 쪽(새 상태)** 을 계속 서술한다. 실측:

```
tick2 (dwell 보류):
   ev['state']     : working
   ev['rule']      : 'no activity within 60s'   <-- working 인데 "활동 없음"
   ev['tier']      : 3
   ev['derived']   : True
   ev['hysteresis']: {'pending': 'idle', 'dwell_sec': 90, 'elapsed_sec': 0.0}
```

F-25의 존재 이유가 "**근거를 검증할 수단**"(계획 §1.1)인데, 그 근거 dict가 스스로 모순된다. `hysteresis.pending`으로 해독은 가능하므로 오분류는 아니고 감사성 결함이다.

- 계획 §3 검증 3의 단언(`ev["state"] == r["liveness"]`, `derived ⇔ tier==3`)은 **통과한다** — 그래서 이 결함이 검증을 빠져나갔다.
- 제안: 보류 시 `rule`에 보류 사실을 반영하거나(`"held: <old rule> (pending idle)"`), 억제된 판정을 `hysteresis.suppressed_rule`에 넣고 `rule`/`tier`는 실제 emit 상태의 것으로 맞춘다. 후자가 §2.5 shape 확장으로 자연스럽다.

---

## F5 — D4 reconcile 재배치의 **신규 경로가 무테스트** (MINOR)

D4의 실질 신규 코드는 `dispatch.py:951-953`의 유도 분기 하나다:

```python
pl = p.liveness
if pl in (None, "unknown"):
    pl = _dispatch_liveness(p, time.time() if now is None else now)
```

이 분기는 **프로덕션에서 항상 실행된다**(`collect()`가 분류 루프 앞에서 reconcile을 부르므로 `p.liveness`는 항상 기본값 `"unknown"`). 그런데 **어떤 테스트도 이 분기를 밟지 않는다**:

- `test_f18_attribution.py:201,217,228` — proc row에 `liveness="working"`을 **핀으로 박아** 넣어 유도 분기를 건너뛴다.
- `test_f25_state_model.py:188 test_drill_dedup_pair` — `_reconcile_drill_rows`를 거치지 않고 `classify_job()`을 직접 호출한다.

실측 확인(핀 있을 때 tracker 키 0개 = 유도 미실행 / 핀 없을 때 키 생성 = 유도 실행):

```
proc.liveness 핀 O -> tracker keys = []            <- 유도 분기 미실행
proc.liveness 핀 X -> tracker keys = [('j','drill')]  <- 프로덕션과 동일 경로
```

→ **처분**: `proc.liveness`를 핀하지 않는(=`"unknown"` 기본값) reconcile 테스트 1건 추가. D4가 계획에 없던 자작 결정인 만큼 회귀 가드가 있어야 한다.

**부수(now=None)**: `now=None` → `time.time()` 폴백 자체는 무회귀이나, 레거시 1-arg 호출자는 reconcile 내부에서 **실시간 클럭**으로 분류하고 직후 테스트가 `now=0`으로 재분류하는 혼합 시계가 된다. 현재 무해(키가 갈림)하나 F5의 테스트를 추가할 땐 `now`를 명시 주입할 것.

---

## F6 — reconcile이 **드롭될 행**의 tracker 키를 만든다 (ADVISORY)

`dispatch.py:953`의 `_dispatch_liveness(p, now)`는 `model.classify_job(..., key=("j", p.slug))`를 타므로, 곧 `drop`될 proc row에 대해 tracker 엔트리를 생성한다. 실측:

```
reconcile 후: tracker keys = [('j','drill')]              <- 드롭된 행의 키
classify 루프 후: [('j','drill'), ('j','drill-claude-CASE-...-12345')]
sweep 후: 둘 다 생존 (이번 tick에 'seen' 이므로)
```

**브리프의 우려(GC 오염/무한 성장)는 실현되지 않는다**: 유령 키는 drill proc row가 존재하는 동안 매 tick 재생성·재-seen 되고, drill이 끝나면 seen에서 빠져 `sweep()`이 제거한다. **경계 있음, 오판정 없음**(registry row는 다른 키를 쓴다 — proc slug=`drill` vs registry slug=`drill-claude-CASE-…`).

다만 존재하지 않는 행의 상태를 tracker가 들고 있는 것은 설계상 잡음이다. `classify_job`에 `key=None`을 넘길 수 있는 내부 경로(증거 유도 전용 호출)를 두면 깨끗해진다 — `classify_job(ev_in, now, key=None)`은 이미 hysteresis를 건너뛰도록 되어 있어 시그니처 변경도 불필요하다.

---

## F7 — 동일 tick 이중 settle이 dwell을 **날조**할 수 있다 (ADVISORY · 현재 도달 불가)

`StateTracker.settle()`은 "prev = 직전 **tick**"을 가정하지만 실제로는 "직전 **호출**"이다. 같은 tick에 같은 키로 두 번 settle하면 없는 이력이 생긴다. 실측:

```
settle(('j','same'), "working", 3, t=1000) 
settle(('j','same'), "queued",  3, t=1000)  -> ('working', {'pending':'queued','dwell_sec':300,'elapsed_sec':0.0})
```

즉 **최초 관측인데 dwell 보류가 걸린다** — 계획 §2.4의 "`--once`/`--json`은 단일 tick → 최초 관측은 항상 즉시 확정" 불변식 위반.

**현재는 도달 불가**로 판단한다: 키가 `("j", slug)`이고, `dispatch.py:967,973` `_scan_jobs_log(path, seen, seen_keys)`가 proc slug와 겹치는 log row를 드롭하며(`:839 if slug in seen_slugs: continue`), `_scan_processes`도 `dkey` dedup(`:740`)을 건다. reconcile의 proc/registry도 slug가 다르다(F6). 따라서 한 tick에 같은 slug 2행이 서지 않는다.

→ 계획이 고정한 키 스킴(`("j", slug)`)에 딸린 잠재 취약성이다. 방어가 필요하면 `settle()`에 "이미 이번 tick에 seen이면 첫 판정을 유지" 가드 1줄이 근본적이다.

---

## F8 — 잡다 (ADVISORY)

1. **죽은 설정** — `model.py:235-236`의 `("idle","unused"): 0`, `("queued","dead"): 0`은 **도달 불가**다. 전자는 `_STATE_RANK` 동률(idle=unused=4)이라 `:274`의 `>=` 즉시 분기가 먼저 먹고, 후자는 `dead ∈ HYST_IMMEDIATE_STATES`(`:273`)가 먼저 먹는다. 무해하나 표가 "여기서 0을 준다"고 읽히므로 문서로서 오도한다 — 주석으로 "중복 방어(rank/immediate가 이미 처리)"임을 명시할 것.
2. **죽은 import** — `liveness.py:16`의 `UNUSED_ACTIVITY_MS`는 어디서도 쓰이지 않는다(`_is_unused`는 model.py 내부에서 판정). 제거 대상.
3. **`inputs` 참조 공유** — `model.py:318`의 `_evidence(...)`가 `inputs`에 호출자 dict를 **복사 없이** 담는다. 실측: `ev["inputs"] is ev_in` → `True`이고, 이후 `ev_in` 변형이 evidence에 비친다. 현 두 호출부(`collect_evidence`, `_dispatch_liveness`)가 매번 새 dict를 만들어 실버그는 없으나, evidence를 "그 시점의 불변 스냅샷"으로 부르는 계약이므로 `dict(inputs)`가 옳다.

---

## 무결 확인 (지적 없음)

- **hysteresis off-by-one**: `:287` `elapsed >= dwell` — dwell=90이면 정확히 90.0s에 확정. 경계 정상.
- **`pending` 리셋 조건**: `:271`(동일 상태 복귀), `:276`/`:280`/`:288`(확정) 모두 `pending=None`. `:283`의 `pending[0] != state`로 **다른 상태로 목표가 바뀌면 dwell 재시작** — 옳다(A→B 보류 중 A→C면 C 기준으로 새로 세야 한다).
- **`_STATE_RANK` 완전성**: 분류기가 emit하는 전 상태 커버 — `working/idle/unused/stale/dead` (세션) + `queued/killed/done/unknown` (잡) + `blocked`(미emit이나 등재). 누락 0.
- **lateral(idle↔unused, rank 동률 4)**: 양방향 모두 tier-1이라 `:273`의 tier 게이트에서 즉시 확정. 정상.
- **`tracker_sweep()` try/except 성장 위험**(`__init__.py:168-172`): `sweep()`은 dict 순회/삭제뿐이라 실질 throw 경로가 없다. 예외 시에도 `_store`는 tick당 행 수로 경계된다.
- **python 3.8**: `ast.parse` 5파일 통과, 3.8.10에서 전 경로 실행 확인. match문·`X|Y` 없음. `Optional` 유지.
- **재배치 가드**: `.liveness = ` 정확히 **2곳**(`collectors/__init__.py:149`, `dispatch.py:1017`) — 둘 다 `classify_*` 위임. `dispatch.py:924`의 구 `r.liveness = p.liveness` 소멸 확인. 계획 §3 검증 4 통과.
- **additive 스키마**: `Session`/`DispatchJob` 기존 필드 삭제·개명 0.

---

## D2 판정 — **정당하다 (약화 아님)**

구 단언 `jobs[0].liveness == "working"`은 reconcile의 자체 override 가드(`p.liveness in ("working","idle") and r.liveness in ("queued","stale","dead","unknown")`)를 검사했다. 그 가드의 후반 조건은 **소멸하지 않고** `classify_job`의 `state in ("queued","stale","dead","unknown")`(`model.py:456`)으로 이동했으며, 신 단언 경로가 이를 실제로 통과한다 — registry row가 없는 cwd에서 tier-3 `dead`를 유도한 뒤 `_proc_liveness` tier-2 override로 `working`이 된다.

신 단언은 흡수(`_proc_liveness`) · 판정(`_dispatch_liveness`) · 근거(`tier == 2`) 3축을 본다. 스텝로그의 "옛 단언보다 강하다"는 **동의**한다. 테스트 수 불변(247 baseline)도 사실.

단, **D2가 강해진 것과 별개로 D4의 재배치 자체는 커버리지를 잃었다** — F5 참조. D2 갱신은 정당하나 D4용 테스트가 그 자리를 메워야 했다.

---

## 잘한 결정 (명시)

- **tier 게이트(`HYST_APPLIES_TO_TIER=(3,)`)**: dwell의 정당화가 "mtime 60s 경계 노이즈"였음을 근거로 tier-1 선언에 적용하지 않은 것은 §2.1 불변식과 정확히 정합한다. 이게 없었으면 "런타임이 idle을 선언해도 90초간 working" 이라는 R6 재생산이 일어났다.
- **`proc_start_match`의 3-값(None/True/False)**: 증거 부재와 양성 불일치를 타입으로 가른 것 — bool 2-값이었으면 조용한 fail-open이 됐다.
- **`is_loop`일 때 mtime 프로브 생략**(`dispatch.py:318`): tier-2가 이미 결정한 행에 tier-3 I/O를 태우지 않는다. 프리-F-25 동작과도 동일.
- **tracker 키에 `proc_start` 포함**: PID 재사용 세션이 죽은 프로세스의 dwell 이력을 상속하지 못한다. `test_proc_start_in_key_prevents_pid_reuse_confusion`이 이를 고정한다.
- **`_reconcile_drill_rows`를 분류 앞으로(D4)**: "대입 2곳" 제약을 우회하지 않고 **구조로** 만족시킨 선택. 판정점 단일화라는 F-25의 목적에 부합한다(테스트만 붙이면 된다).

---

## 처분 요약

| # | 심각도 | 처분 |
|---|---|---|
| F1 | MINOR (커밋 전 필수) | mirror rsync 재실행 → 스위트 GREEN 회복. Step 1/2 경계를 트리에서 정리 |
| F4 | MINOR | dwell 보류 시 `rule`/`tier`/`derived`를 emit 상태와 정합화 |
| F5 | MINOR | `proc.liveness` 핀 없는 reconcile 테스트 1건 추가(D4 신규 경로) |
| F6 | ADVISORY | 증거 유도용 `_dispatch_liveness` 호출에 `key=None` |
| F7 | ADVISORY | `settle()`에 tick 내 재진입 가드(또는 현 도달-불가를 주석으로 고정) |
| F8 | ADVISORY | 죽은 dwell 엔트리 주석 · `UNUSED_ACTIVITY_MS` import 제거 · `inputs` 복사 |
