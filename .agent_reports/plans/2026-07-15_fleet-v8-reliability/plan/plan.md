---
status: done
created: 2026-07-15
qa: standard
intensity: standard
mode: dev
spec_significance: within-spec
---

# fleet v8 — 관제 신뢰성·세션 제어 (PRD v8 §4.8: F-25 · F-26 · F-22 minor · F-27)

- **사이클**: 2026-07-15 fleet-v8-reliability
- **worktree**: `/home/Uihyeop/agent_setting-wt/fleet-v8-reliability` (branch `fleet-v8-reliability`)
- **근거 계약**: `.agent_reports/spec/agent-fleet-dashboard/prd.md` **§4.8**(prd.md:234–260) — F-25=238–244, F-26=245–249, F-27=250–255. **F-28(256–260)은 범위 밖**. v8 minor 2건 = prd.md:217, 218. 지원 맥락 = §0.5(prd.md:18), §4.7 F-22 원본(214–219), F-24(227–230), §7(280–285), §9(294–313), Non-goals(360–365), **확정 결정 v8 승격(410–413)**, 구현 순서(419).
- **잠긴 결정 재논의 금지**: prd.md:410–413의 F-25/F-26/F-27 lock은 본 계획의 입력이지 논의 대상이 아니다. 계획은 그것을 코드로 실현할 뿐이다.
- **선례 사이클**: `plans/2026-07-10_fleet-f15-dispatch-rows/`(디자인팀 critic plan-review 계약), `plans/2026-07-10_fleet-ui-v2/`(v2 UI 기준선).

## 0. 목표와 스코프

한 줄: **상태 판정을 `model.py` 단일 분류기로 통합(F-25)하고, 그 위에 레지스트리 1급화(F-26)·wide name zone 고정 상한(F-22 minor)·사용자 개시 kill(F-27)을 얹는다.**

구현 순서는 spec prd.md:419가 고정한다 — **F-25가 기반이고 F-26/F-27이 그 위에 선다.** F-22 minor는 독립이라 Step 3에 배치(렌더 회귀 되돌리기, 다른 Step과 파일 충돌 없음).

**스코프 안**
- `tools/fleet/model.py` — 상태 분류기 신설(F-25 소유), 스키마 additive 확장.
- `tools/fleet/collectors/{liveness,claude,dispatch,procscan}.py` — 기존 휴리스틱을 분류기 **입력 계층으로 재배치**.
- `tools/fleet/render.py` — `unused` 표시, name zone 상한, 선택 커서·kill 프롬프트.
- `tools/fleet/control.py` — **신설**(F-27 kill 안전·action log·registry 마감).
- `tools/fleet/tests/` — 신규 픽스처 + 회귀 테스트.
- **canonical `tools/fleet/` ↔ mirror `adapters/claude/tools/fleet/` 양쪽 동기 필수**.

**스코프 밖**
- **F-28 전량**(route record 소비·resource-runner·governor lease) — stage-dispatch v9 착륙 후 별도 phase.
- attach/resume(Non-goal 유지, prd.md:363) · 자동 제어(prd.md:412) · sparkline/herdr 소켓.
- 하네스 원본 transcript/DB write — 불변(prd.md:16). **유일 예외 = F-27 registry 마감 1건**(prd.md:255).

**소스는 읽기 전용이 아니다 — 본 계획은 위 파일들을 실제로 수정한다.** (계획 문서 자체는 소스를 수정하지 않았다.)

---

## 1. 현재 상태 분석 (실측)

### 1.1 상태 판정이 분산된 실태 (F-25의 문제 표면)

| 판정 조각 | 위치 | 현재 동작 |
|---|---|---|
| 세션 4-상태 | `collectors/liveness.py:47 classify()` | `_alive(pid)` → orphan → mtime 48h 창 → claude status → `age<1min` 이면 working |
| 프로세스 생존 | `liveness.py:17 _alive()` | `os.kill(pid,0)`만 — **start-time 재검증 없음**(PID 재사용 무방비) |
| 잡 liveness | `collectors/dispatch.py:304 _dispatch_liveness()` | loop=무조건 working · codex/opencode 별도 함수 · claude=`_job_liveness` 15min 창 |
| queued 유도 | `dispatch.py:299 _QUEUED_GRACE_MIN=15` + `:312` | `dead + source=jobs + status=open + elapsed≤15min` → queued |
| drill dedup | `dispatch.py:882 _reconcile_drill_rows()` | proc row의 liveness를 registry row에 흡수(F-18a) |
| env 마커 | `procscan.py:242,246` | `AGENT_SESSION_ROLE=worker`→is_child, `MEM_DISTILL/FLEET_TITLE_REFRESH`→mem_worker |
| fd 소유권 | `collectors/__init__.py:84 prepare_tick()` | Codex rollout fd 선점 예약(F-24) |
| registry status | `collectors/claude.py:205` | `sess.status = sj.get("status")` — liveness가 소비 |

→ 우선순위·충돌 규칙이 **코드 암묵**. `liveness.classify()`가 사실상 유일 분류기지만 dispatch 잡은 완전히 별도 경로. 같은 세션이 tick마다 다른 기준으로 분류될 수 있고 근거를 검증할 수단이 없다. **이것이 사용자 관찰 "판정 기준 자체가 불안정"의 실체.**

### 1.2 유령 세션 pid 1168514 (F-26의 acceptance 대상, 실측)

`~/.claude/sessions/1168514.json`:
```json
{"pid":1168514,"sessionId":"37abe594-b164-4924-9b2c-15997701e0c2","cwd":"/home/Uihyeop/agent_setting",
 "startedAt":1784083189482,"procStart":"3918896","version":"2.1.210","peerProtocol":1,
 "kind":"interactive","entrypoint":"cli","name":"agent-setting-17","nameSource":"derived",
 "status":"idle","updatedAt":1784083189601,"statusUpdatedAt":1784083189601}
```
- `updatedAt - startedAt = 119ms` — 프롬프트 한 번도 제출 안 됨. proc: `claude --teammate-mode tmux --dangerously-skip-permissions`, 시작 Wed Jul 15 11:39:47 2026. 레지스트리 총 7행.
- 현재 코드 경로: `claude.py:207` 이 `name`을 **`sess.slug`에 덮어씀** → 이름은 있으나, `claude.py:226-229` 가 transcript 부재 시 mtime을 `statusUpdatedAt`(=시작 시각)으로 채움 → `liveness.classify()`가 48h 창 안 + status=`idle` → **평범한 `idle` 행**. 유령임을 알리는 신호가 0.
- **핵심 상호작용(계획이 규범으로 해소)**: 이 행은 registry `status:"idle"`을 **가지고 있다**. F-25 우선순위대로면 1순위 registry가 `idle`을 주장한다. 그런데 F-26은 `unused` 렌더를 요구한다. → **§2.2 축 분리 논거로 해소**.
- **fresh 행은 `status`/`updatedAt`이 아예 없을 수 있음 — tolerate 필수.**

### 1.3 F-22 wide name zone 회귀 (실측)

`render.py:542-555 _wide_name_width(term_width)`:
```python
fixed_row = _NAME_COL + _BRW + _MW + 4 + _CTX_W + 5     # = 20+14+23+4+16+5 = 82
framing   = ... (tint 경로 = 9)
return max(_NW_S, int(term_width) - fixed_row - framing)
```
남는 slack을 **전부** name에 준다. 실측 = 60→28, 120→29, **168→77**, 200→109. (`_NW_S`=28 하한 render.py:488, `_TITLE_MAX`=24 레거시/dispatch 상한 render.py:491.)

→ **40 상한은 60/120을 바꾸지 않는다**(28·29 < 40). **168만 77→40, 200은 109→40으로 되돌린다.** `_session_row`(render.py:680-722)의 `name_width is None` → `_TITLE_MAX` 24 클립 경로는 그대로 유지.

### 1.4 F-27 키 충돌 (실측 — 중요)

`render.py:2071-2073`:
```python
if ch in (curses.KEY_UP, ord("k")):     _OFFSET -= 1
elif ch in (curses.KEY_DOWN, ord("j")): _OFFSET += 1
```
**`↑↓`는 이미 스크롤에 바인딩**되어 `k`/`j`와 공유한다. spec F-27(prd.md:252)의 "`↑↓` 선택 모드 진입/이동"과 **직접 충돌**. → §5.2에서 설계로 해소.

### 1.5 테스트·런타임 실측

- 러너: `python3 -m unittest discover -s tools/fleet/tests -t . -q` → **현재 247 tests OK, 14.0s**. pytest 없음.
- python3 = **3.8.10** → **match문·`X|Y` 타입 문법 금지**. `from typing import Optional` 유지.
- `tests/` = `test_dispatch/test_f14_title/test_f15_rows/test_f17_title_refresh/test_f18_attribution/test_f19_memory/test_f21_cross_harness_titles/test_runtime_currentness/test_token_budget/test_token_experiment/test_mirror_parity`. 픽스처 디렉토리 선례 = `tests/fixtures/token_experiment/*.json`.
- `tests/test_mirror_parity.py:10` 이 재동기 명령을 명시: `rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/`.
- `render_once`(render.py:1806-1816)는 `shutil.get_terminal_size().columns`를 씀 → **`COLUMNS` env가 그대로 먹는다**(검증 명령 근거). stdout 비-TTY여도 plain 출력.
- `close_job_row` = `adapters/claude/bin/dispatch-headless.py:358`(opencode 동형 `adapters/opencode/bin/dispatch-headless.py:355`). `jobs_lock`(`:320`)의 `fcntl.flock(LOCK_EX)` + `<jobs>.lock` 규율. 매치 키 = `(status=="open", slug, worktree)`, 6-필드 행 재작성.
- XDG state 선례 = `titles.py:30 state_root()` → `${XDG_STATE_HOME:-~/.local/state}/agent-fleet/titles`.

---

## 2. F-25 규범 표 (본 계획이 확정 — 코드 상수로 encode)

### 2.1 소스 우선순위 표 (prd.md:240 규범화)

| 순위 | 소스 | 구체 신호 | 신뢰 근거 |
|---|---|---|---|
| **1** | **명시 registry 상태** | jobs.log `status` 필드(`open/running/done/killed/cancelled`) · `~/.claude/sessions/<pid>.json`의 `status`(`idle/shell/busy`) + `startedAt`/`updatedAt`/`procStart` | 런타임 자신이 자기 상태를 직접 선언 |
| **2** | **강한 프로세스 증거** | exact pid + `/proc/<pid>/stat` field 22 start-time 일치 · Codex rollout **fd 소유권**(F-24) · env 마커(`AGENT_SESSION_ROLE=worker`, `AGENT_DISPATCH_DEPTH`, `MEM_DISTILL`, `FLEET_TITLE_REFRESH`) · `/proc/<pid>/cwd` `(deleted)` orphan | OS 커널 사실 — 위조 불가하나 "무엇을 하는 중인지"는 모름 |
| **3** | **mtime 휴리스틱** | transcript/rollout mtime 창 · opencode DB `MAX(time_updated)` · worktree 산출물 mtime(F-15 queued 유도) | 최후 수단 — 공유 worktree aliasing·이웃 파일 오염에 취약. **표시 시 `~` 접두 유지** |

**불변식**: 하위 소스는 상위 소스와 **모순될 때 절대 이기지 못한다**. 하위는 상위가 **침묵할 때만** 판정하거나, 상위가 판정한 상태를 **같은 축 안에서 정제(refine)**할 수 있다(§2.2).

### 2.2 `unused` 축 분리 논거 (pid 1168514 상호작용 해소 — 규범)

registry `status`와 `unused`는 **다른 축**이다:

- **활동성 축** (registry `status`가 소유): `busy` ↔ `idle`. "지금 모델이 돌고 있나?"
- **무활동 이력 축** (registry `startedAt`/`updatedAt` + transcript 부재가 소유): "시작 이후 **한 번이라도** 프롬프트가 제출됐나?"

→ **`unused`는 registry status와 모순이 아니라 `idle`의 하위 정제(refinement)다.** 1순위 registry가 `idle`을 주장할 때, **레지스트리 자신의 `updatedAt≈startedAt` 증거(동일 1순위 소스)**가 그 `idle`을 `unused`로 좁힌다. 소스 계층이 바뀌지 않으므로 **"하위가 상위를 이기지 못한다" 불변식이 깨지지 않는다.**

**정제 규칙 (코드 상수)**: `state == "idle"` AND `transcript 부재` AND `registry updatedAt - startedAt <= UNUSED_ACTIVITY_MS(=2000)` → `unused`. 셋 중 하나라도 불충족·부재면 `idle` 유지(tolerate).

**금지**: `busy`를 `unused`로 좁히지 않는다(축 위반). 3순위 mtime만으로 `unused`를 만들지 않는다(registry 증거 필수).

### 2.3 어휘 매핑 표 (prd.md:241 규범화 — 표시층 재해석 금지)

**세션 어휘** = `working / idle / unused / stale / dead`

| registry `status` (1순위) | 추가 증거 | fleet 세션 상태 |
|---|---|---|
| `busy` | — | `working` |
| `idle` / `shell` | transcript 있음 or 활동 이력 있음 | `idle` |
| `idle` / `shell` | transcript 부재 + `updatedAt≈startedAt` | **`unused`** (§2.2 정제) |
| (부재) | 2순위: pid 죽음 | `dead` |
| (부재) | 2순위: orphan cwd `(deleted)` | `stale` |
| (부재) | 3순위: mtime age > `SESSION_STALE_MIN` | `stale` (`~` 유도값) |
| (부재) | 3순위: mtime age < `SESSION_WORK_SEC` | `working` (`~` 유도값) |
| (부재) | 3순위: 그 외 | `idle` (`~` 유도값) |
| (임의) | 2순위: pid 죽음 | `dead` — **registry를 이긴다** (프로세스 부재는 registry status와 같은 축의 상위 사실이 아니라 존재 축의 종결) |

> `blocked`/`done`은 세션에 emit하지 않는다(liveness.py:6-7 기존 계약 유지 — `blocked`는 herdr 소켓 필요, `done`은 잡 전용).

**잡 어휘** = `queued / working / done / stale / dead / killed`

| jobs.log 원어휘 (`core/OPERATIONS.md §5.10`) | 추가 증거 | fleet 잡 상태 |
|---|---|---|
| `open` | transcript 부재 + `elapsed ≤ JOB_QUEUED_GRACE_MIN` | `queued` (진짜 미기동) |
| `open` | transcript 부재 + `elapsed > JOB_QUEUED_GRACE_MIN` | `dead` |
| `open` | transcript age ≤ `JOB_STALE_MIN` | `working` (F-15 유도) |
| `open` | transcript age > `JOB_STALE_MIN` | `stale` |
| `running` | transcript age ≤ `JOB_STALE_MIN` | `working` |
| `running` | transcript age > `JOB_STALE_MIN` | `stale` |
| `running` | transcript 부재 | `dead` |
| `done` | — | `done` (터미널 — 현행처럼 live 목록에서 제외) |
| `killed` | — | `killed` |
| `cancelled` | — | `killed` (**매핑 결정**: fleet 잡 어휘에 `cancelled`가 없다. `killed`가 "외부 개입으로 종결"이라는 같은 의미축 — 구분은 `state_evidence.raw_status`에 보존) |

> **★ 터미널 행(`done`/`killed`/`cancelled`)은 live 행을 신설하지 않는다 (의도 명시)**: `dispatch.py:814-815`가 **분류 이전에** 터미널 행을 버린다(`if status not in ("open","running"): continue`). **이 필터는 불변** — 위 3행은 **분류기 수준의 어휘 계약**(표시층이 원어휘를 임의 재해석하지 못하게 고정)이지 새 렌더 행이 아니다. 따라서 오늘 `collect()` 경로에서는 **도달 불가**이며, 픽스처 `job_cancelled.json`은 `classify_job()` **직접 호출**로만 검증한다. F-27 착륙 후에도 도달 불가는 유지된다 — kill 성공 시 registry 행이 `done`으로 마감되면 **다음 tick에 행이 사라지는 것이 의도된 동작**(§6.6 검증 6). (부수: `_LIVE_GLYPH`(render.py:294)에 `killed` 엔트리가 없어 만약 노출된다면 `.get(state,"·")` 폴백으로 stale과 동일한 `·`로 찍힌다 — 도달 불가를 유지해야 할 또 하나의 이유.)
| (proc-scan, registry 행 없음) | key ∈ `_LOOP_KEYS` | `working` (현행 dispatch.py:305 계약 유지) |

### 2.4 hysteresis 상수 (구체값 — `model.py` 한 블록에 집결)

```python
# --- F-25 state model constants (single block; PRD v8 §4.8) ---
SESSION_WORK_SEC       = 60      # 흡수: liveness.py:66 `age_min < 1.0`
SESSION_STALE_MIN      = 48 * 60 # 흡수: liveness.py:14 STALE_MIN
JOB_STALE_MIN          = 15      # 흡수: dispatch.py:432 _job_liveness(stale_min=15)
JOB_QUEUED_GRACE_MIN   = 15      # 흡수: dispatch.py:299 _QUEUED_GRACE_MIN
UNUSED_ACTIVITY_MS     = 2000    # §2.2: updatedAt-startedAt 이 이 이하면 무활동(실측 119ms)

# 하향 전이 dwell — 임계 조건이 이 시간 이상 "연속" 유지돼야 상태가 내려간다.
# 상향(활동 재개)·강한 증거(dead/killed)는 즉시(0).
# ★ tier-3(mtime 유도) 하향 전이에만 적용된다 — 아래 HYST_APPLIES_TO_TIER 참조.
HYST_DOWNGRADE_DWELL_SEC = {
    ("working", "idle"):   90,   # tick=2s → 45 tick. mtime 60s 경계 진동 흡수
    ("working", "stale"):  300,
    ("idle",    "stale"):  300,
    ("working", "queued"): 300,
    ("idle",    "unused"):  0,   # unused는 registry 증거 기반(시간 감쇠 아님) → 즉시
    ("queued",  "dead"):    0,   # 강한 증거
}
HYST_IMMEDIATE_STATES = ("dead", "killed", "done")   # 절대 지연 없음
HYST_APPLIES_TO_TIER  = (3,)     # ★ dwell 은 tier-3 유도 전이에만. tier-1/2 = 즉시(dwell 0)
```

**상태 서열(하향 판정용)**: `working > idle ≈ unused > queued > stale > dead/killed`. 전이쌍이 표에 없으면 dwell=0(즉시).

**★ tier 게이트 (§2.1 불변식과의 정합 — 필수)**: dwell은 **새 상태의 판정 tier가 3일 때만** 적용한다.
- **근거**: `("working","idle"): 90`의 정당화는 애초에 **"mtime 60s 경계 진동 흡수"** — 즉 **tier-3 유도값의 노이즈 문제**다. 그런데 Claude 세션의 `working→idle`은 registry `status: busy→idle`, 즉 **tier-1 명시 선언**이다(실측: pid 1168514 행이 `status:"idle"`을 직접 들고 있음). tier-3 노이즈용 처방을 tier-1 진실에 무차별 적용하면 **런타임이 스스로 idle을 선언해도 90초간 working으로 표시**된다 — §2.1 불변식("상위 소스가 이긴다")과 정면 충돌이고, 해소하려던 "판정 기준 불안정"을 오히려 재생산한다(R6의 증상 그대로).
- **규칙**: tier-1(registry 명시 선언) / tier-2(강한 프로세스 증거) 하향 전이 = **즉시**. tier-3(mtime 휴리스틱) 하향 전이 = 표의 dwell 적용. 상향 = tier 무관 즉시.
- prd.md:242의 hysteresis 요구는 그대로 충족된다 — 플래핑은 tier-3에서만 발생하므로 처방이 원인에 정확히 대응한다.
- 픽스처 `flap_60s_boundary.json`(tier-3)은 dwell 적용을, 신규 `flap_registry_tier1.json`은 **tier-1 busy→idle이 즉시 반영**됨을 각각 고정한다.

**tick 간 직전 상태 참조 메커니즘** — 명시 설계:
- 소유자 = **`model.py`의 모듈 레벨 싱글턴 `_TRACKER` (`StateTracker` 클래스)**. 렌더 루프가 아니다 — `--json`/`--once`/live 3경로가 전부 `collect_all()`을 지나므로 분류기 옆에 두는 것이 유일하게 균질하다.
- 키: 세션 = `("s", harness, pid, proc_start)` — **`proc_start` 포함이 PID 재사용 방지의 핵심**(없으면 `("s", harness, pid, None)`). 잡 = `("j", slug)`.
- 값: `{"state": str, "since": float, "pending": (state, first_seen_ts) or None}`.
- GC: 매 tick 끝에 이번 tick에 안 보인 키를 제거(unbounded 성장 방지).
- **`--once`/`--json`은 단일 tick** → 직전 상태 없음 → dwell 미충족 → **최초 관측은 항상 즉시 확정**(pending 없이 그대로 emit). 즉 스냅샷 경로에서 hysteresis는 no-op. 이 규칙을 테스트로 고정.
- 테스트용 `reset_state_tracker()` 공개 — 테스트 간 상태 누수 차단(**hermetic 필수**).

### 2.5 `state_evidence` shape (additive only)

`Session`·`DispatchJob`에 `state_evidence: Optional[dict] = None` **필드 추가**. `asdict()`가 자동으로 `--json`에 실어준다(model.py:158,192). **기존 필드 삭제·개명 0.**

```json
{"state":"unused","tier":1,"source":"claude-registry",
 "rule":"idle refined to unused (no transcript, updatedAt≈startedAt)",
 "derived":false,
 "inputs":{"registry_status":"idle","started_at":1784083189.482,"updated_at":1784083189.601,
           "activity_ms":119,"transcript":false,"pid_alive":true,"proc_start_match":true},
 "raw_status":null,"hysteresis":null}
```
- `tier` ∈ {1,2,3} = §2.1 순위. `derived=true` ⇔ tier 3(표시층 `~` 접두 조건과 동일 소스).
- `hysteresis`: 하향 보류 중이면 `{"pending":"idle","dwell_sec":90,"elapsed_sec":31}`, 아니면 `null`.
- `raw_status`: 잡의 jobs.log 원어휘 보존(`cancelled` 구분 등).

---

## 3. Step 1 — F-25 단일 상태 분류기 (기반 · 최우선)

> 의존: 없음. **Step 2/3/4 전부가 이 Step에 의존**(3은 파일이 분리돼 병렬 가능, 아래 §7 참조).

### 편집 표면

| 파일 | 영역 | 변경 |
|---|---|---|
| `tools/fleet/model.py` | 신규 블록(파일 하단, `Session`/`DispatchJob` 뒤) | §2.4 상수 블록 + `StateTracker` + `classify_session()` / `classify_job()` / `reset_state_tracker()` |
| `tools/fleet/model.py:63` | `LIVENESS_STATES` | `"unused"` 추가 (additive) |
| `tools/fleet/model.py:117-160` | `Session` | `state_evidence`, `proc_start`, `started_at`, `updated_at`, `registry_name`, `kind`, `provenance` 필드 추가 (전부 `Optional`, default `None`) |
| `tools/fleet/model.py:162-194` | `DispatchJob` | `state_evidence` 필드 추가 |
| `tools/fleet/collectors/liveness.py` | 전체 | `classify()`를 **얇은 입력 수집기**로 강등 — `_alive()` 를 `_proc_evidence(pid, proc_start)`(start-time 재검증 포함)로 확장하고 `model.classify_session()`에 위임. **`classify(sess, now, stale_min=...)` 시그니처·리턴 계약은 유지**(collectors/__init__.py:149 호출자 무회귀) |
| `tools/fleet/collectors/dispatch.py:304` | `_dispatch_liveness()` | 하네스별 mtime 조회는 **증거 수집만** 하고 판정은 `model.classify_job()`에 위임. `_QUEUED_GRACE_MIN`(:299)은 `model.JOB_QUEUED_GRACE_MIN`을 참조하도록 교체(상수 이중화 제거) |
| `tools/fleet/collectors/dispatch.py:882` | `_reconcile_drill_rows()` | liveness 흡수(:923)를 **입력 증거 병합**으로 재배치 — proc row의 pid/proc_start를 registry row의 tier-2 증거로 넘기고, 최종 판정은 병합 후 `classify_job()` 1회 |
| `tools/fleet/collectors/__init__.py:144-151` | liveness 블록 | 세션 분류 후 tick 종료 시 `model.tracker_sweep()` 호출(GC) |
| `tools/fleet/collectors/procscan.py:242-246` | env 마커 | 변경 없음 — 이미 tier-2 증거 생산자. `Session.proc_start` 채우기만 추가(`/proc/<pid>/stat` field 22) |

### 재배치 매핑 (폐기 아님 — prd.md:244)

| 기존 휴리스틱 | 재배치 후 위치 |
|---|---|
| `liveness.classify()` 판정 로직 | `model.classify_session()` tier-1/2/3 분기 |
| F-15 queued 유도 (`dispatch.py:312`) | `classify_job()` tier-1(`open`) × tier-3(transcript) 교차 규칙 (§2.3 표) |
| F-18a drill 상관 dedup (`dispatch.py:882`) | `classify_job()` **입력 증거 병합**(판정 전) |
| F-24 fd 소유권 (`collectors/__init__.py:84`) | tier-2 증거 — `prepare_tick()` 유지, 결과를 `state_evidence.inputs.fd_owner`로 전달 |
| F-18b env 마커 (`procscan.py:246`) | tier-2 증거 — 분류 입력 |

**독립 패치 층으로 남기지 않는다**: 위 5건 중 어느 것도 `classify_*()` **바깥에서 최종 liveness 문자열을 쓰지 않는다.** 검증 = §3 검증 4번(grep 가드).

### 픽스처 목록 (`tools/fleet/tests/fixtures/state_model/`)

관측된 불안정 사례를 고정한다. 선례 = `tests/fixtures/token_experiment/`.

| 픽스처 | 재현 사례 | 기대 |
|---|---|---|
| `ghost_unused.json` | §1.2 pid 1168514 원본 그대로(status=idle, activity 119ms, transcript 부재) | `unused`, tier 1, `derived=false` |
| `registry_fresh_no_status.json` | 방금 뜬 세션 — `status`/`updatedAt` 키 **부재** | 크래시 0, tier-2/3으로 degrade, `idle` |
| `registry_busy_no_transcript.json` | status=busy + transcript 부재 | `working` (**`unused`로 좁히지 않음** — 축 위반 가드) |
| `flap_60s_boundary.json` | mtime이 `SESSION_WORK_SEC` 경계에서 진동하는 3-tick 시퀀스 (**tier-3**) | working 유지(dwell 90s 미충족) → 90s 후 idle |
| `flap_registry_tier1.json` | registry `status: busy → idle` (**tier-1** 명시 선언) | **즉시** idle — dwell 미적용(§2.4 tier 게이트) |
| `flap_recovery.json` | idle 상태에서 mtime 갱신 | **즉시** working(상향 무지연) |
| `pid_reuse.json` | registry `procStart:"3918896"` ≠ `/proc/<pid>/stat` start-time | tier-2 불일치 → registry 증거 폐기, `dead` |
| `job_queued_vs_working.json` | registry-only `open` 행 × (transcript 있음/없음) | 각각 `working` / `queued` |
| `job_cancelled.json` | jobs.log `cancelled` 행 | `killed` + `state_evidence.raw_status=="cancelled"` |
| `drill_dedup_pair.json` | F-18a proc + registry 쌍(slug 불일치) | 1행 병합, registry 정본, proc는 증거로 흡수 |
| `codex_fd_owner_pair.json` | F-24 same-cwd fd-owner + fd-less | owner만 sid/title, 둘 다 살아 있음 |
| `snapshot_single_tick.json` | 단일 tick(`--json` 경로) | hysteresis no-op — 최초 관측 즉시 확정 |

테스트 파일 = `tools/fleet/tests/test_f25_state_model.py` (신규). **모든 케이스 hermetic** — `reset_state_tracker()` 를 `setUp`에서 호출, `/proc`·`~/.claude` 실제 접근 금지(주입/monkeypatch).

### 검증 (Step 1 종료 시 — 끝이 아니라 여기서)

```bash
cd /home/Uihyeop/agent_setting-wt/fleet-v8-reliability

# 1) 신규 F-25 스위트
python3 -m unittest tools.fleet.tests.test_f25_state_model -v

# 2) 전체 회귀 — 247+ tests, 회귀 0
python3 -m unittest discover -s tools/fleet/tests -t . -q

# 3) --json smoke + state_evidence additive 확인 (기존 키 삭제 0 검증 포함)
python3 tools/fleet/fleet.py --json > /tmp/v8_step1.json
python3 - <<'PY'
import json
d = json.load(open("/tmp/v8_step1.json"))
rows = d["sessions"] + d["jobs"]
assert rows, "no rows collected"
assert all("state_evidence" in r for r in rows), "state_evidence missing"
for r in d["sessions"]:
    ev = r["state_evidence"]
    assert ev["tier"] in (1, 2, 3), ev
    assert ev["state"] == r["liveness"], ("evidence/liveness 불일치", r["pid"], ev)
    assert ev["derived"] == (ev["tier"] == 3), ("derived⇔tier3 불변식 위반", ev)
print("sessions:", len(d["sessions"]), "jobs:", len(d["jobs"]))
print("tier 분포:", {t: sum(1 for r in d["sessions"] if r["state_evidence"]["tier"] == t) for t in (1,2,3)})
PY

# 4) ★ 재배치 가드 (자동 단언 — 실패 시 비영 종료)
#    현재 `.liveness = ` 대입 지점 3곳 → 재배치 후 2곳이어야 한다:
#      · collectors/__init__.py:149  s.liveness = liveness.classify(s, now)      (위임 — 유지)
#      · collectors/dispatch.py:982  j.liveness = _dispatch_liveness(j, now)     (위임 — 유지)
#      · collectors/dispatch.py:924  r.liveness = p.liveness  (F-18a 흡수 → 증거 병합으로 재배치되며 소멸)
grep -rn "\.liveness = " tools/fleet/ --include=*.py | grep -v tests/     # 육안 확인용
N=$(grep -rn "\.liveness = " tools/fleet/ --include=*.py | grep -v tests/ | wc -l)
test "$N" -eq 2 || { echo "★ FAIL: liveness 대입 $N곳 (기대 2) — 재배치 누락 또는 신규 패치층"; exit 1; }
echo "재배치 가드 OK — liveness 대입 2곳(전부 classify_* 위임)"

# 5) 3.8 문법 가드 (match문/X|Y 타입 금지)
python3 -c "import ast,sys; [ast.parse(open(f).read()) for f in sys.argv[1:]]" \
  tools/fleet/model.py tools/fleet/collectors/liveness.py tools/fleet/collectors/dispatch.py
python3 --version   # 기대: Python 3.8.10

# 6) 실제 렌더 출력 — 눈으로 리뷰 (상태 문자열이 §2.3 어휘 밖으로 새지 않는지)
COLUMNS=120 python3 tools/fleet/fleet.py --once

# 7) mirror parity
rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/
python3 -m unittest tools.fleet.tests.test_mirror_parity -v
```

---

## 4. Step 2 — F-26 레지스트리 1급화 (유령 세션 가시성)

> 의존: **Step 1 완료 필수**(`unused`는 `classify_session()`이 만든다).

### 편집 표면

| 파일 | 영역 | 변경 |
|---|---|---|
| `tools/fleet/collectors/claude.py:193-209` | `enrich()` 1) 블록 | registry 파싱을 **1급 계약**으로 승격 — `read_registry(pid)` 헬퍼 추출, `sessionId/status/name/startedAt/updatedAt/procStart/kind` 전부 `Session`에 적재. **`status`/`updatedAt` 부재 tolerate**(`.get()` + isinstance 가드) |
| `tools/fleet/collectors/claude.py:207-208` | `sess.slug = name` | **유지**(회귀 방지) + `sess.registry_name = name` **추가**(이름 사슬 명시화) |
| `tools/fleet/collectors/claude.py:221-240` | 3) 블록 | `sess._has_transcript = bool(path)` 를 tier-1 정제 입력으로 전달(§2.2). mtime의 `statusUpdatedAt` fallback(:226-229)은 **tier-3 표식**으로 evidence에 기록 |
| `tools/fleet/collectors/procscan.py` | 신규 헬퍼 | `read_proc_start(pid)` — `/proc/<pid>/stat` field 22. Windows/실패 = `None`(tolerate) |
| `tools/fleet/collectors/procscan.py` | 신규 헬퍼 | `provenance(pid)` — ppid 계보 best-effort |
| `tools/fleet/collectors/{codex,opencode}.py` | enrich | **실측 후 tolerant 추가만.** 동형 레지스트리 부재 = **no-op, 무회귀**(신규 파일 탐색 실패는 조용히 통과) |
| `tools/fleet/render.py:294-298` | `_LIVE_GLYPH` / `_GLYPH_KEY` | `"unused"` 엔트리 추가 — 글리프 **`◌`**(점선 고리 = "한 번도 채워진 적 없음"), 색 `g_stale`가 아닌 **전용 dim-yellow 키**(idle과 구분, dead와도 구분) |
| `tools/fleet/render.py:680-722` | `_session_row()` | 이름 사슬을 명시 함수로: `_session_name(s)` = `s.title or s.registry_name or slug`. `unused` 행은 name zone 뒤에 `unused <경과>` 배지 |
| `tools/fleet/render.py:995` | `_session_row_2line()` | 동일 사슬·배지 적용(narrow/stack parity) |
| `tools/fleet/render.py:1060` | `_session_row_stack()` | 동일 |
| `tools/fleet/render.py:1377-1387` | pulse 요약 | `unused` 카운트 추가(`· K unused`, K>0일 때만 — healthy 무음 원칙) |
| `tools/fleet/render.py:1755-1765` | legend | `unused` 글리프는 **등장 시만**(F-12 계약) |
| `tools/fleet/render.py:1291-1292` | `_build_lines` 필터 | **`unused`는 기본 노출**(`--all` 무관). stale/dead만 기본 숨김 — F-26의 목적 자체가 "어디서도 인지 불가" 해소이므로 숨기면 계약 위반 |

### `unused` 글리프 — 충돌 회피 (실측)

render.py:294-296의 **점유 현황**: `working`/`idle`=`●` · `blocked`=`◑` · `done`=`✓` · `stale`/`unknown`=`·` · `dead`=`✕` · `queued`=`◦` · **`_DETACHED_GLYPH`=`○`**.

→ **`○`는 이미 detached가 점유**하므로 unused에 쓸 수 없다. render.py:291-293이 이 표의 계약을 **"Readable without color"**로 못박았으므로, 색으로만 갈리는 `○` 재사용은 계약 위반이다. detached(attach 축)와 unused(활동 이력 축)는 의미가 전혀 달라 흑백 구분 불가는 F-26의 목적("idle과 구분되는 1급 신호", prd.md:248)도 직접 약화시킨다.

- **채택: `◌`**(U+25CC, 미점유) — shape gradient상 `●`(채움) > `○`(고리) > **`◌`(점선 고리 = 한 번도 채워진 적 없음)** 로 읽혀 "무활동 이력" 의미와 정합.
- **최종 확정은 Step 2 디자인팀 critic에 위임**(§4 검증 4) — 계획이 critic 이전에 글리프를 확정할 이유가 없다. `⊘`도 후보. critic verdict를 반영해 상수 1곳(`_LIVE_GLYPH["unused"]`)만 교체한다.
- **폭 가드**: 신규 글리프는 `_cw`(render.py:1844) 기준 **1셀**이어야 한다(`◦`/`◑`와 동류). 정렬 깨짐 시 §4 검증 4의 폭 가드가 잡는다.

### provenance 태깅 (best-effort — prd.md:249)

`/proc/<pid>/stat` field 4(ppid) 를 따라 최대 6단계 위로 오르며 `/proc/<ppid>/comm` 매칭:
- `herdr` → `herdr` · `tmux`/`sshd`/`login`/`bash`/`zsh` → `terminal` · `code`/`node`(vscode-server 경로) → `vscode` · env `AGENT_SESSION_ROLE=worker` → `worker`.
- **판별 실패 = 조용히 생략**(`provenance=None` → 태그 미표시). **오귀속보다 결손**(prd.md:249 명시).
- dim 태그로 name zone 뒤 suffix에 배치 — `_session_row`의 suffix 예약 예산(render.py:704-718)에 **gate 태그와 같은 방식으로 편입**(폭 부족 시 드롭).

### 검증 (Step 2)

```bash
cd /home/Uihyeop/agent_setting-wt/fleet-v8-reliability

# 1) 신규 F-26 스위트
python3 -m unittest tools.fleet.tests.test_f26_registry -v

# 2) F-26 live acceptance — 유령 세션 pid 1168514 이 "이름 있는 unused 행"으로 렌더돼야 함
cat ~/.claude/sessions/1168514.json          # 전제 확인: 살아있나?
ps -o pid=,lstart=,args= -p 1168514
COLUMNS=168 python3 tools/fleet/fleet.py --once | grep -i "agent-setting-17"
#    기대: 익명 아님(이름 `agent-setting-17` 표시) + `unused <경과>` 배지 + idle 과 구분되는 글리프
# ※ heredoc 은 stdin 을 점유하므로 앞단 파이프를 절대 붙이지 않는다(round_1 B1 실증:
#   `--json | python3 - <<'PY'` 는 구현과 무관하게 항상 실패). Step 1 #3 과 동일 패턴 사용.
python3 tools/fleet/fleet.py --json > /tmp/v8_step2.json
python3 - <<'PY'
import json
d = json.load(open("/tmp/v8_step2.json"))
row = [s for s in d["sessions"] if s["pid"] == 1168514]
assert row, "pid 1168514 세션 부재 — 아래 재현 절차로 동형 케이스 생성"
r = row[0]
assert r["liveness"] == "unused", r["liveness"]
assert r["registry_name"] == "agent-setting-17", r
assert r["state_evidence"]["tier"] == 1 and r["state_evidence"]["inputs"]["activity_ms"] < 2000
print("F-26 live acceptance OK:", r["registry_name"], r["liveness"], r["state_evidence"]["rule"])
PY

#    [⛔ 철회된 재현 절차 — 2026-07-15 harvest 시 안전 정정, 따라하지 말 것]
#    원문은 pid 1168514 사망 시 "실제 claude 세션을 새로 스폰해 재현 후 kill로 정리"를
#    안내했고, execute 워커가 이를 따라 실세션 1개를 스폰·SIGTERM하는 안전 경계 위반이
#    발생했다(step_04 dev log 자진 보고, final_report §4.5). 이 절차는 규범이 아니다.
#    올바른 재현 = 프로세스 생성 없이 픽스처 주입: `classify_session()`에 registry shape
#    (updatedAt-startedAt ≤ 2000ms, transcript 부재)를 직접 주입해 동일 검증 가능함을
#    code-test가 실증했다(tests/fixtures/state_model/*.json 참조). 실 세션 스폰·signal 금지.

# 3) 3폭 실제 렌더 출력 — 출력 자체를 눈으로 리뷰
for w in 60 120 168; do echo "=== COLUMNS=$w ==="; COLUMNS=$w python3 tools/fleet/fleet.py --once; done

# 4) 디자인팀 critic 렌더 비평 (read-only) — F-15 critic 계약 재사용
#    입력 = 위 3폭 출력 캡처, 비평 산출물 경로:
for w in 60 120 168; do COLUMNS=$w python3 tools/fleet/fleet.py --once > /tmp/v8_step2_${w}.txt; done
#    → `디자인팀` critic 모드로 /tmp/v8_step2_{60,120,168}.txt 비평 요청 (read-only, 코드 수정 금지).
#    → verdict 를 plan 디렉토리 `_internal/plan_reviews/design_critic_step2.md` 에 embed.
#    비평 범위: unused 배지가 idle/stale/dead 와 시각적으로 구분되는가 · provenance dim 태그가
#              name zone 을 잡아먹지 않는가 · 3폭 전부에서 행이 터미널 경계를 넘지 않는가.

# 5) 전체 회귀 + mirror
python3 -m unittest discover -s tools/fleet/tests -t . -q
rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/
python3 -m unittest tools.fleet.tests.test_mirror_parity -v
```

---

## 5. Step 3 — F-22 minor (wide name zone 고정 상한)

> 의존: 없음(파일·함수가 Step 1/2와 분리). **Step 1과 병렬 가능** — 단 Step 2도 `_session_row`를 만지므로 **Step 2와는 순차**(같은 함수 충돌).

### 편집 표면

| 파일 | 영역 | 변경 |
|---|---|---|
| `render.py:489-491` 인접 | 상수 | `_NAME_WIDE_MAX = 40` **신설**(상수 한 곳 — prd.md:218 "고정 상한(기본 40 display cols, 상수 한곳에서 조정)") |
| `render.py:542-555` | `_wide_name_width()` | `return max(_NW_S, min(_NAME_WIDE_MAX, int(term_width) - fixed_row - framing))` — **남는 slack 재배분 금지**(다른 컬럼으로 흘려보내지도 않음: 기존처럼 행 끝 padding으로 남는다) |
| `render.py:542-548` | docstring | "give all remaining horizontal slack to the session column" → v8 minor 계약으로 개정 |

**보존 불변식 (건드리지 않는다)**
- `_session_row`(:719-722)의 `name_width is None` → `_TITLE_MAX`(24) 클립 경로 — hermetic/레거시 호출자.
- narrow/stack의 suffix-예약 예산 계산(`_session_row_2line` :995, `_session_row_stack` :1060) — prd.md:218 "narrow/stack의 suffix-예약 예산 계산 … 그대로 유지".
- `_clip_w`(:1861) display-cell/CJK 안전 tail-cut.
- F-15 dispatch compact 24열 상한(`_DISPATCH_NAME_MAX` / `_compact_dispatch_name` :785).

### acceptance 교체 (prd.md:218 → 219 대체)

| term width | 현재(실측) | 변경 후 | 비고 |
|---|---|---|---|
| 60 | 28 | **28** | 불변 (`_NW_S` 하한) |
| 120 | 29 | **29** | 불변 (29 < 40) |
| 168 | **77** | **40** | ★ 회귀 되돌림 |
| 200 | 109 | **40** | ★ 회귀 되돌림 |

→ 구 acceptance "168열에서 24열보다 커진다" → **"40열 상한까지만 커진다"**.

### 검증 (Step 3)

```bash
cd /home/Uihyeop/agent_setting-wt/fleet-v8-reliability

# 1) 상한 단위 검증 — 실측 표 그대로 고정
python3 - <<'PY'
import sys; sys.path.insert(0, "tools")
from fleet import render
got = {w: render._wide_name_width(w) for w in (60, 120, 168, 200)}
exp = {60: 28, 120: 29, 168: 40, 200: 40}
assert got == exp, ("F-22 minor 상한 불일치", got, exp)
assert render._wide_name_width(None) == render._NW_S
print("F-22 minor OK:", got, "| cap =", render._NAME_WIDE_MAX)
PY

# 2) 신규 스위트 (위 표 + dispatch 24열 상한 무회귀 + CJK tail-cut 무회귀)
python3 -m unittest tools.fleet.tests.test_f22_name_cap -v

# 3) 실제 렌더 출력 3폭 — 출력 자체를 눈으로 리뷰
for w in 60 120 168; do echo "=== COLUMNS=$w ==="; COLUMNS=$w python3 tools/fleet/fleet.py --once; done
#    확인: 168 에서 세션 제목이 40열에서 멈추고 branch/model/context/time 정렬 유지,
#         행이 168 경계를 넘지 않음, dispatch 이름은 24열 compact 유지.

# 4) 행 길이 하드 가드 (경계 초과 0)
for w in 60 120 168; do
  COLUMNS=$w python3 tools/fleet/fleet.py --once | python3 -c "
import sys, unicodedata
w = int(sys.argv[1]); bad = 0
for i, ln in enumerate(sys.stdin.read().splitlines()):
    dw = sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in ln)
    if dw > w: bad += 1; print('OVER', i, dw, repr(ln[:60]))
print('width', w, 'over-limit lines:', bad); sys.exit(1 if bad else 0)
" $w || echo "FAIL at $w"
done

# 5) 디자인팀 critic 렌더 비평 (read-only) — 40열이 실제 제목에 충분한지, 잘림이 정보를 죽이는지
for w in 60 120 168; do COLUMNS=$w python3 tools/fleet/fleet.py --once > /tmp/v8_step3_${w}.txt; done
#    → `디자인팀` critic 모드, verdict → `_internal/plan_reviews/design_critic_step3.md`

# 6) 전체 회귀 + mirror
python3 -m unittest discover -s tools/fleet/tests -t . -q
rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/
python3 -m unittest tools.fleet.tests.test_mirror_parity -v
```

---

## 6. Step 4 — F-27 제한적 세션 제어 (kill + 정리만)

> 의존: **Step 1 + Step 2 완료 필수**(허용 대상 판정이 `unused`/`stale`/`dead` 상태에 의존).

### 6.1 신규 모듈 결정

**`tools/fleet/control.py` 신설** — kill 안전 재검증 + action log + registry 마감. render.py(2124줄)에 넣지 않는 이유 = **curses 없이 hermetic 테스트가 가능해야 함**(F-27 안전 acceptance가 단위 테스트 대상).

> **[decision: significant — spec §9 모듈 트리 sync 의무]** prd.md:294-313의 §9 모듈 트리는 v3에서 현행화된 확정 목록이고 `control.py`가 없다. F-19가 `collectors/memory.py`를 추가할 때 spec에 명시 등재한 선례(prd.md:202)를 따라, **구현 착륙 후 §9 트리에 `control.py` 1줄 추가하는 minor spec sync가 의무로 남는다.** 본 계획은 spec을 수정하지 않는다 — 후속 obligation으로 §8에 기록.

### 6.2 키 충돌 해소 — 모드 있는 커서 (설계 결정)

**실측 충돌**(§1.4): `↑↓`는 이미 `_OFFSET` 스크롤. spec(prd.md:252)은 "`↑↓` = 선택 모드 진입/이동".

검토한 2안:

| 안 | spec 문구 | 스크롤 회귀 |
|---|---|---|
| A. `j/k`=스크롤 유지, `↑↓`=선택 모드 진입/이동으로 분리 | 문구 그대로 충족 | **회귀 발생** — 화살표로 스크롤하던 사용자가 갑자기 선택 모드에 진입 |
| **B. 모드 있는 커서 (채택)** | "이동"은 충족, "진입"만 별도 키 | **회귀 0** |

**채택 = B.** 근거: spec F-27의 목적은 "행 선택 커서"라는 **조작 모델**이지 특정 키코드가 아니다(prd.md:252는 조작 모델 절 안의 예시 표기). 반면 스크롤은 v2가 "핵심 버그 수정"으로 세운 계약(prd.md:155 "항상 맨 아래까지 도달")이고 `↑↓`는 §3 키 표(prd.md:80)에 **명시된 계약**이다. 두 계약이 충돌하면 **기존 명시 계약을 깨지 않는 쪽**이 옳다. B는 spec 문구 중 "진입" 한 단어만 양보하고 나머지(선택 커서·`↑↓` 이동·`x` kill·확인 프롬프트)를 전부 지킨다.

**최종 키 계약**:

| 모드 | 키 | 동작 |
|---|---|---|
| 기본(스크롤) | `↑↓`, `j/k`, `PgUp/PgDn`, `g/G` | **현행 그대로** (회귀 0) |
| 기본 | `s` | **선택 모드 진입** (커서 = 첫 selectable 행) |
| 기본 | `x` | 선택 모드 진입 + 첫 selectable 행 선택 (진입 단축 — spec "↑↓ 진입" 의도 보존) |
| 선택 | `↑↓`, `j/k` | **커서 이동** (뷰포트 밖으로 나가면 `_OFFSET` 자동 추종) |
| 선택 | `x` | 현재 커서 행 **kill 요청** → 확인 프롬프트 |
| 선택 | `Esc`, `s` | 선택 모드 해제 → **스크롤 복귀** |
| 선택 | `q` | 종료(현행 유지) |

footer 키 바(render.py:2030-2038)는 모드별로 갈린다 — 기본은 현행 + `s select`, 선택 모드는 `↑↓ move · x kill · Esc cancel`.

### 6.3 편집 표면

| 파일 | 영역 | 변경 |
|---|---|---|
| `tools/fleet/control.py` | **신규** | 공개 표면 **전량**(§6.6 검증이 호출하는 이름과 1:1 일치해야 함): `read_proc_start(pid)` — **`procscan.read_proc_start`의 재수출**(구현 1곳, 호출 편의상 control에서도 노출) · `verify_target(pid, proc_start) -> bool` · `is_excluded(pid) -> bool` (§6.4-3 제외 규칙) · `kill_target(pid, proc_start, sid, state, approval) -> str` · `log_action(**kw)` · `close_registry_row(jobs, slug, worktree) -> bool` · `actions_root()` |
| `render.py:2044-2106` | `_loop()` | 모드 상태(`_SELECT_MODE`, `_CURSOR`), 키 분기(§6.2 표), 확인 프롬프트 렌더 |
| `render.py:2001-2041` | `_draw()` | 커서 행 하이라이트(reverse), 커서 뷰포트 추종 clamp |
| `render.py:2030-2038` | footer | 모드별 키 바 |
| `render.py:1266` | `_build_lines()` | **selectable row index 맵 반환**(현재는 segment-line 리스트만) — 커서가 "몇 번째 화면 줄"이 아니라 "어느 세션/잡"인지 알아야 한다. **additive 반환**(모듈 레벨 `_SELECTABLE` 맵에 stash — `_TOGGLE_ROWS`(render.py:2092) 선례와 동형)이라 기존 호출자(`render_once`) 무영향 |

### 6.4 안전 계약 (prd.md:253 — 전부 필수)

1. **exact pid + start-time 재검증** (`control.verify_target`): 시그널 **직전에** `/proc/<pid>/stat` field 22를 다시 읽어 수집 시점 `proc_start`와 **일치할 때만** 진행. 불일치 = **PID 재사용** → 거부 + `action=refused,reason=start_time_mismatch` 로그. registry의 `procStart:"3918896"`(clock ticks 문자열)이 대조 기준으로 이미 존재(§1.2).
2. **SIGTERM 우선 → SIGKILL 에스컬레이션**: SIGTERM 후 `KILL_GRACE_SEC=5` 대기(비블로킹 폴링 — curses 루프를 막지 않음). 미종료 시 **명시 재확인 프롬프트**를 다시 띄우고, 승인 시에만 SIGKILL. **자동 에스컬레이션 금지.**
3. **대상 제외** (하드 가드, 프롬프트 이전 단계에서 selectable에서 제거):
   - `pid == os.getpid()` 및 `os.getppid()` — fleet 자신.
   - 현재 조작 중인 메인 세션 — `CLAUDE_CODE_SESSION_ID` env / fleet 자신의 프로세스 계보 상의 harness pid.
4. **허용 대상 등급**:
   - **기본 허용**(단일 확인): `unused` / `stale` / `dead` 세션 + `is_child`(worker) idle 세션 + registry 잡의 exact pid.
   - **경고 + 이중 확인**: `working` 세션 / registry `busy` — 프롬프트에 경고 문구 + **두 번째 확인**(첫 확인과 다른 키 요구, 예: 대상 pid 마지막 2자리 입력 대신 `y` → `YES` 2단).
5. **자동 제어 0**: `control.py`의 어떤 함수도 사용자 키 입력 경로 밖에서 호출되지 않는다. `--json`/`--once`/collector/scheduler는 `control`을 **import조차 하지 않는다**(검증 = §6.6 grep 가드).

### 6.5 action log + registry 마감

**action log** — 제목 sidecar 동형(`titles.py:30` 선례):
- 경로: `${FLEET_ACTION_STATE_DIR:-${XDG_STATE_HOME:-~/.local/state}/agent-fleet/actions}/actions.jsonl` (env override는 **테스트 hermetic용**).
- 행: `{"ts":<epoch>,"action":"sigterm|sigkill|refused|close_row","pid":<n>,"sid":<str|null>,"state":"<판정상태>","approval":"single|double|escalated","result":"ok|refused|error","reason":<str|null>}`.
- **bounded rotation**: 쓰기 전 크기 확인 → `ACTION_LOG_MAX_BYTES = 1<<20`(1 MiB) 초과 시 `actions.jsonl` → `actions.jsonl.1`(기존 `.1` 덮어씀, **총 2파일 상한**). append는 `O_APPEND` + 같은 디렉토리 `.lock` flock.

**registry 마감** (prd.md:255 — 무write 불변식의 **명시적 단일 예외**):
- 조건: **kill 성공** AND 대상이 **registry 잡 행**(`source=="jobs"`) AND 그 행이 `status=="open"`. 세션 kill은 registry를 **건드리지 않는다**.
- 동작: 해당 행을 `done` + pipe에 `,note=fleet-kill` 추가. 매치 키 = `(status=="open", slug, worktree)` — `close_job_row`와 **동일**.
- **계층 문제 해소 (결정)**: canonical `tools/fleet/`가 `adapters/claude/bin/dispatch-headless.py`를 **import하면 계층 위반**(canonical → adapter 역방향 의존)이고, mirror 사본(`adapters/claude/tools/fleet/`)에서는 상대 경로가 달라져 **양쪽이 다르게 동작**한다. subprocess 호출은 dispatch-headless.py에 신규 CLI 서브명령을 추가해야 해서 **adapter 2개 + mirror까지 편집 표면이 번진다**.
  → **채택: `control.close_registry_row()`를 fleet 안에 구현하되 `close_job_row`와 규율 동형**. **임의 write가 아니다** — 동일 lock으로 직렬화되므로 concurrent conductor와 안전.

#### "동형"의 규범적 범위 (prd.md:255 해석 — 확정)

**실측 충돌**: `adapters/claude/bin/dispatch-headless.py:380`은 note 토큰을 **하드코딩**한다 — `pipe += f",note=dead-{reason}"`. `reason="fleet-kill"`을 넣어도 산출은 `note=dead-fleet-kill`이다. 따라서 prd.md:255가 요구하는 `done,note=fleet-kill`과는 **정의상 1바이트도 같아질 수 없다.** 초안의 "byte-identical 교차 구현 계약"은 **통과 불가능한 단언이었고 철회한다.**

**해소**: prd.md:255의 "SD-15 `close_job_row` **동형 경로** 재사용, 임의 write 아님"에서 **"동형"의 규범적 범위 = 동시성·정합성 규율**이지 note 토큰 문자열이 아니다. 동형의 정의 = 다음 5개 전부:

| # | 동형 항목 | 원본 위치 |
|---|---|---|
| ⑴ | 동일 `jobs_lock` flock 규율 — `<jobs>.lock` 경로 + `fcntl.flock(LOCK_EX)` | `dispatch-headless.py:320-327` |
| ⑵ | 동일 매치 키 — `status=="open"` && `slug` && `worktree` 3중 일치 | `:378` |
| ⑶ | **첫 매치에서 `break`** — 중복 행이 있어도 1건만 마감 | `:385` |
| ⑷ | `done` flip + **idempotent**(무매치 시 `False` 리턴, 파일 무변경) | `:388`, `:364` |
| ⑸ | 동일 6-필드 재조립 규칙 — `f"{ts}\tdone\t{repo}\t{wt}\t{row_slug}\t{pipe}\n"` | `:383` |

**note 토큰은 의도적으로 다르다 (계약상 달라야 한다)**: `note=dead-<reason>`은 "**dispatch가 스스로 죽었다**"는 의미축이고, `note=fleet-kill`은 "**외부 관제 도구가 사용자 승인 하에 종료시켰다**"는 **다른 행위**다. 두 행위를 같은 note로 뭉개면 사후 감사에서 구분 불가 — prd.md:255가 굳이 `fleet-kill`을 명시한 이유다. → **`note=fleet-kill`이 우선**하며, note 축은 동형 범위에서 **명시적으로 면제**된다.

**adapter 파라미터화(리뷰 수정방향 ②)는 기각**: (a) 계획이 이미 근거로 든 "adapter 2개(`claude`/`opencode`) + mirror까지 편집 표면이 번짐"이 여전히 유효하고, (b) 더 중요하게 — note 축은 **의미상 달라야 하는 것**이므로 `close_job_row(reason=...)`로 파라미터화하는 것은 서로 다른 두 행위(자기 사망 vs 외부 관제 종료)를 **하나의 생성 경로로 잘못 통합**하는 설계다. 면제해야 할 것을 통합하는 방향이라 기각.

**미명시 3건 해소 (리뷰 지적)**:
- **⑴ `reset` 필수 인자**: 원본 시그니처는 `close_job_row(jobs, slug, worktree, reason, reset)`으로 `reset`이 **필수**이고, truthy일 때만 `,reset={reset}`을 덧붙인다(`:381-382`). **fleet kill에는 reset(세션 한도 리셋 시각) 개념이 자체가 없다** — 사용자가 죽인 것이지 rate-limit으로 죽은 게 아니다. → `close_registry_row(jobs, slug, worktree)`는 `reset` 파라미터를 **갖지 않으며**, `reset` 토큰을 **절대 쓰지 않는다**(원본에 `reset=""`(falsy)를 넘긴 것과 동일 산출). 교차 검증은 원본을 `reset=""`로 호출해 이 축을 정렬한다.
- **⑵ 첫 매치 `break`**: **동형 범위에 포함**(위 표 ⑶). 중복 open 행은 registry 이상 상태이고, 원본과 다르게 전부 마감하면 fleet이 원본보다 **더 넓게 write**하게 된다 — 예외를 최소로 유지하는 원칙에 반한다.
- **⑶ 6필드 초과 행의 초과 필드 손실**: 원본은 `parts[0..5]`만 재조립하므로 7번째 이후 필드를 **버린다**(`:377`, `:383`). → **이 손실 동작도 동형 범위에 포함**한다. 근거: (a) jobs.log는 `core/OPERATIONS.md §5.10`상 **6필드가 하드 계약**이라 초과 필드는 정의상 존재하지 않아야 하고, (b) 만약 wild에 존재한다면 fleet만 보존하고 dispatch는 버리는 **비대칭이 더 나쁜 드리프트**다. 단 이 손실은 `state_evidence`가 아니라 **action log의 `reason` 필드에 원행을 남겨** 감사 가능하게 한다.

**드리프트 방어 = 교차 구현 계약 테스트 (재설계 — 약화 아님)**: `tests/test_f27_control.py::TestRegistryCloseParity`가 동일 jobs.log 픽스처에 대해 (a) `control.close_registry_row(jobs, slug, worktree)` 와 (b) `dispatch-headless.py`의 `close_job_row(jobs, slug, worktree, reason="fleet-kill", reset="")`(**테스트에서만** 파일 경로 import — 테스트는 계층을 넘어도 된다)를 각각 돌려, 산출 파일에서 **note 토큰만 정규화**(`note=dead-fleet-kill` → `note=fleet-kill`)한 뒤 **완전 일치**를 단언한다.
→ 이러면 **flock 규율·매치 키·필드 재조립·`break` 시맨틱·idempotency 드리프트는 그대로 잡히고**, 계약상 달라야 하는 **단 한 토큰만 면제**된다. 무매치 케이스(둘 다 `False` + 파일 무변경)와 6필드 초과 행 케이스도 같은 방식으로 단언한다.

### 6.6 검증 (Step 4)

```bash
cd /home/Uihyeop/agent_setting-wt/fleet-v8-reliability

# 1) 신규 F-27 스위트 (hermetic — 실제 kill 없음, 가짜 pid + 주입 signal)
python3 -m unittest tools.fleet.tests.test_f27_control -v

# 2) ★ 안전 acceptance A — start-time 불일치 거부 실측 (실제 프로세스, 실제 거부)
python3 - <<'PY'
import os, sys, subprocess, time
sys.path.insert(0, "tools")
from fleet import control
os.environ["FLEET_ACTION_STATE_DIR"] = "/tmp/v8_actions"
p = subprocess.Popen(["sleep", "300"])
time.sleep(0.3)
real = control.read_proc_start(p.pid)
assert real, "proc_start 미취득"
# (a) 정확한 start-time → 통과
assert control.verify_target(p.pid, real) is True, "정상 대상이 거부됨"
# (b) 위조된 start-time (PID 재사용 시뮬레이션) → 반드시 거부
assert control.verify_target(p.pid, str(int(real) + 1)) is False, "★ start-time 불일치를 거부하지 못함"
# (c) 거부가 action log 에 남아야 함
control.kill_target(p.pid, proc_start=str(int(real) + 1), sid=None, state="unused", approval="single")
assert p.poll() is None, "★ 거부됐어야 할 대상이 실제로 죽었다 — 치명적"
p.kill(); p.wait()
log = open("/tmp/v8_actions/actions.jsonl").read()
assert '"refused"' in log and 'start_time_mismatch' in log, log
print("safety acceptance A OK — start-time 불일치 거부 + 로그 기록 확인")
PY

# 3) ★ 안전 acceptance B — 자동 제어 횟수 0 실측
rm -rf /tmp/v8_auto && mkdir -p /tmp/v8_auto
FLEET_ACTION_STATE_DIR=/tmp/v8_auto python3 tools/fleet/fleet.py --json > /dev/null
FLEET_ACTION_STATE_DIR=/tmp/v8_auto COLUMNS=120 python3 tools/fleet/fleet.py --once > /dev/null
test ! -e /tmp/v8_auto/actions.jsonl && echo "자동 제어 0 OK — action log 생성조차 안 됨" || \
  { echo "★ FAIL: 사용자 입력 없이 제어 행위 발생"; cat /tmp/v8_auto/actions.jsonl; }
#    정적 가드 — collector/스냅샷 경로는 control 을 import 조차 하지 않는다
grep -rn "import control\|from .* import control\|from fleet import control" \
  tools/fleet/ --include=*.py | grep -v tests/ | grep -v "render.py"
#    기대: 출력 0줄 (render.py 만 control 을 알고, 그것도 키 입력 경로에서만)

# 4) registry 마감 교차 구현 동형 검증 (close_job_row 와 note-정규화 후 완전 일치 — §6.5)
#    note 토큰만 정규화(note=dead-fleet-kill → note=fleet-kill)하고 나머지 전 바이트 등가를 단언.
#    무매치 idempotency(둘 다 False + 파일 무변경)·6필드 초과 행 케이스도 같은 방식으로 단언.
python3 -m unittest tools.fleet.tests.test_f27_control.TestRegistryCloseParity -v

# 5) 대상 제외 가드 (fleet 자신 / 메인 세션)
python3 - <<'PY'
import os, sys; sys.path.insert(0, "tools")
from fleet import control
assert control.is_excluded(os.getpid()), "★ fleet 자신이 kill 대상"
assert control.is_excluded(os.getppid()), "★ fleet 부모가 kill 대상"
print("대상 제외 가드 OK")
PY

# 6) 라이브 TUI 수동 검증 (UI 관점 — 실제 눈으로)
#    tmux 안에서: python3 tools/fleet/fleet.py
#      · 기본 모드에서 ↑↓ 가 여전히 스크롤인지 (회귀 0 확인) ★
#      · `s` → 선택 모드, ↑↓ 로 커서 이동, 뷰포트 자동 추종
#      · working 행에 `x` → 경고 + 이중 확인 프롬프트
#      · unused 행(pid 1168514)에 `x` → 단일 확인 → SIGTERM → 행 소멸
#      · Esc → 스크롤 복귀
#    → 그 후 action log 확인:
cat "${XDG_STATE_HOME:-$HOME/.local/state}/agent-fleet/actions/actions.jsonl"

# 7) 디자인팀 critic 렌더 비평 (read-only) — 선택 커서·확인 프롬프트의 시각 설계
#    입력 = 위 6)의 화면 캡처 + 프롬프트 목업. verdict → `_internal/plan_reviews/design_critic_step4.md`

# 8) 전체 회귀 + mirror (최종)
python3 -m unittest discover -s tools/fleet/tests -t . -q     # 기대: 247+ tests, 회귀 0
rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/
python3 -m unittest tools.fleet.tests.test_mirror_parity -v
```

---

## 7. 의존 순서 / 병렬성

```
Step 1 (F-25 model.py 분류기)  ← 기반. 단독 선행.
    ├── Step 2 (F-26 registry 1급) ── unused 상태에 의존
    │        └── Step 4 (F-27 제어) ── 허용 대상 판정이 unused/stale/dead 에 의존
    └── Step 3 (F-22 name cap)  ── 상태 모델과 무관
```

- **Step 3은 Step 1과 병렬 가능**(`_wide_name_width` vs `model.py` — 파일 무충돌).
- **Step 3 ↔ Step 2는 순차**: 둘 다 `_session_row`/`_session_row_2line`/`_session_row_stack`을 만진다. **Step 2 → Step 3 순서 권장**(Step 2가 suffix 예약에 provenance 태그를 추가하고, Step 3의 상한이 그 위에 얹혀야 예산 계산이 한 번만 검증된다).
- **Step 4는 최후** — 유일하게 파괴적 행위를 도입하므로, 상태 판정이 안정된 뒤에 얹는다.
- **mirror rsync는 매 Step 끝**(드리프트 조기 발견 — 사이클 끝에 몰면 diff가 커진다).

---

## 8. 리스크 / 롤백

| # | 리스크 | 영향 | 완화 | 롤백 |
|---|---|---|---|---|
| R1 | **키 충돌 해소가 spec 문구와 불일치** — B안이 "`↑↓` 진입"을 별도 키(`s`)로 양보 | spec 문구 vs 구현 드리프트 | §6.2에 근거 명문화. **spec §4.8 F-27 조작 모델 문구를 구현 확정 후 minor sync**(prd.md:252 "`↑↓` 선택 모드 진입/이동" → "`s`/`x` 진입, `↑↓`/`jk` 이동") — **[decision: significant — 사용자 확인 자리]** | `s` 진입키 제거 후 A안(↑↓ 분리)으로 전환. `_loop` 키 분기 1곳 |
| R2 | **registry write 예외가 넓어짐** — `close_registry_row`가 잘못된 행을 마감 | 무write 불변식 훼손, 타 세션 잡 오염 | 매치 키 3중(`status==open` × `slug` × `worktree`) + flock + 첫 매치 `break` + idempotent. 세션 kill은 registry 무접촉. 교차 구현 동형 테스트(note 정규화 후 완전 일치, §6.5) | `control.close_registry_row` 호출 1줄 제거 → kill은 되고 마감만 안 됨(안전한 degrade) |
| R3 | **`close_job_row` 드리프트** — adapter 원본이 바뀌면 fleet 사본이 조용히 갈라짐 | registry 포맷 불일치 | §6.5 교차 구현 계약 테스트(**note 토큰만 정규화 후 완전 일치**)가 flock·매치키·`break`·필드 재조립·idempotency 드리프트를 **즉시 실패**로 잡는다. adapters/opencode 동형(`:355`)도 같은 테스트에 편입 | fleet 사본을 adapter 원본에 재정렬 |
| R3b | **note 축 면제가 과도하게 넓어짐** — 정규화가 note 외 차이까지 삼킴 | 드리프트 방어 무력화 | 정규화는 **`note=dead-fleet-kill` → `note=fleet-kill` 단일 치환**으로 한정(정규식 광역 치환 금지). 그 외 1바이트 차이 = 실패 | 정규화 제거 후 note 축까지 수동 대조 |
| R4 | **mirror drift** — canonical만 고치고 `adapters/claude/tools/fleet/` 미동기 (2026-07-11 F-16~F-19 구간 실사고) | 배포 표면이 stale | **매 Step 끝 rsync + `test_mirror_parity`** (사이클 끝 1회 아님) | rsync 재실행 |
| R5 | **python 3.8 문법 위반** — match문·`X\|Y` 타입·`dict\|dict` | 런타임 SyntaxError | 각 Step 검증에 `ast.parse` 가드 + `python3 --version`. `typing.Optional`/`typing.Dict` 사용 | 문법 되돌림 |
| R6 | **hysteresis 상수 오튜닝** — dwell 90s가 너무 길면 "일 끝났는데 계속 working" | 신뢰성 개선이 새 부정확으로 | 상수 **한 블록**(§2.4)에 집결 → 1곳 수정. `state_evidence.hysteresis`가 보류 중임을 노출해 진단 가능. 라이브 관찰 후 조정 | 전 dwell을 0으로 → 현행(hysteresis 없음) 동작과 동일 |
| R7 | **`StateTracker` 싱글턴 상태 누수** — 테스트 간 오염, 장기 실행 시 메모리 성장 | flaky 테스트 / 누수 | `reset_state_tracker()` 를 `setUp` 필수 + 매 tick GC(§2.4) | 싱글턴 제거 → dwell 전부 0(현행 동작) |
| R8 | **PID 재사용** — 수집~시그널 사이 pid 재활용 | **엉뚱한 프로세스 kill** | 시그널 **직전** start-time 재검증(§6.4-1) + acceptance A가 실증 | — (가드가 실패하면 kill 자체를 막는 fail-closed) |
| R9 | **`unused` 오탐** — 활동 중인데 registry `updatedAt`이 안 갱신되는 하네스 버전 | 살아있는 세션이 정리 후보로 | 3중 조건(transcript 부재 ∧ activity≤2s ∧ status=idle). busy 제외(축 가드). **fresh 행 tolerate**. kill은 항상 사용자 확인 뒤 | `UNUSED_ACTIVITY_MS=0` → unused 사실상 비활성 |
| R10 | **Codex/OpenCode 레지스트리 부재** | 무의미한 탐색 비용 | **실측 후 tolerant 추가만, 부재=no-op 무회귀**(prd.md:246) | 해당 enrich 블록 제거 |
| R11 | **`_build_lines` selectable 맵 추가가 `render_once` 회귀** | 스냅샷 경로 파손 | 모듈 레벨 stash(`_TOGGLE_ROWS` 선례) — 반환 시그니처 불변 | stash 제거 |
| R12 | **spec §9 모듈 트리에 `control.py` 미등재** | spec/구현 드리프트 | **후속 obligation**(§6.1) — 착륙 후 prd.md §9 트리에 1줄 추가 minor sync. F-19 `collectors/memory.py` 선례 | `control.py` 내용을 render.py로 흡수 |

**전체 롤백**: 본 사이클은 worktree `fleet-v8-reliability` 브랜치 단독. Step 단위 커밋 → 문제 Step만 `git revert`. Step 1이 기반이므로 Step 1 revert = Step 2/4 동반 revert(Step 3은 독립 revert 가능).

---

## 9. 완료 기준 (사이클 종료 게이트)

- [ ] `python3 -m unittest discover -s tools/fleet/tests -t . -q` → **247+ tests, 회귀 0**
- [ ] `test_mirror_parity` 통과 — canonical/adapter 동기
- [ ] `--json` smoke — 모든 row에 `state_evidence`, 기존 필드 삭제/개명 0
- [ ] **F-26 live acceptance** — pid 1168514(또는 동형 재현)가 **이름 있는 `unused` 행**으로 렌더
- [ ] **F-22 minor acceptance** — `_wide_name_width` = {60:28, 120:29, 168:40, 200:40}
- [ ] **F-27 safety acceptance** — start-time 불일치 **거부 실측** + **자동 제어 0 실측**
- [ ] **registry 마감 동형 검증** — `close_job_row` 대비 **note 토큰 정규화 후 완전 일치** + 무매치 idempotency (§6.5)
- [ ] **F-25 재배치 가드** — `.liveness = ` 대입 **정확히 2곳**(자동 단언, Step 1 검증 #4)
- [ ] 60/120/168열 `--once` 출력 **눈 리뷰** 완료 + **디자인팀 critic verdict 3건** embed
- [ ] python 3.8 문법 가드 통과
- [ ] 후속 obligation 기록: spec §9 `control.py` 등재 + §4.8 F-27 키 문구 sync

---

## 10. 변경 이력

### 2026-07-15 — plan-check round 1 (BLOCK) 교정

리뷰: `_internal/plan_reviews/round_1.md`. blocking 2건 + non-blocking 5건 전량 반영. 실측 기반·재배치 설계·범위 준수는 유지(국소 교정만). 소스 무수정.

| # | 지적 | 반영 |
|---|---|---|
| **B1** | Step 2 F-26 live acceptance가 `--json \| python3 - <<'PY'` — heredoc이 파이프 stdin을 덮어써 **구현과 무관하게 항상 실패** | §4 검증 #2를 Step 1 #3과 동일 패턴(`--json > /tmp/v8_step2.json` 후 `json.load(open(...))`)으로 통일 + 안티패턴 경고 주석. 계획 전체 grep 결과 **이 1건이 유일**(Step 3 #4는 `python3 -c`라 stdin 파이프 정상, Step 4 #2/#5는 파이프 없음) |
| **B2** | "byte-identical 교차 구현 계약" 성립 불가 — 원본(`dispatch-headless.py:380`)이 `note=dead-{reason}` 하드코딩이라 prd.md:255의 `note=fleet-kill`과 정의상 1바이트도 같을 수 없음 | §6.5 전면 개정: **"byte-identical" 문구 철회**. "동형"의 규범적 범위 = **동시성·정합성 규율 5항**(flock·매치키·`break`·idempotent·6필드 재조립)으로 확정하고 **note 축은 명시적 면제**(`dead-<reason>`="자기 사망" vs `fleet-kill`="외부 관제 종료" — 다른 행위축, 뭉개면 사후 감사 불가). 드리프트 방어는 **note 토큰만 정규화 후 완전 일치**로 재설계(약화 아님 — 나머지 전 바이트 검사 유지). adapter 파라미터화(②)는 **기각**(편집 표면 번짐 + 면제해야 할 축을 잘못 통합). 미명시 3건(`reset` 필수 인자 → fleet엔 개념 부재라 파라미터 미보유·원본은 `reset=""`로 호출해 정렬 / 첫 매치 `break` → 동형 포함 / 6필드 초과 손실 → 동형 포함, 근거 명시) 해소 |
| **N1** | hysteresis dwell가 tier 무시 — tier-1 `busy→idle` 명시 선언에도 90초 working 유지 → §2.1 불변식과 충돌 | §2.4에 **`HYST_APPLIES_TO_TIER = (3,)` 게이트** 신설 — dwell은 **tier-3 유도 전이에만**, tier-1/2 하향은 즉시. 근거 명문화 + 픽스처 `flap_registry_tier1.json` 추가 |
| **N2** | `unused` 글리프 `○`가 `_DETACHED_GLYPH`(render.py:296)와 충돌 → "Readable without color" 계약 위반 | §4에 글리프 점유 현황 실측표 + **`◌`(U+25CC, 미점유)** 채택. **최종 확정은 Step 2 디자인팀 critic에 위임**(계획이 critic 이전에 확정할 이유 없음) + 1셀 폭 가드 |
| **N3** | §2.3 `killed`/`cancelled` 행이 live 경로 도달 불가 — 의도 미명시 | §2.3에 **"터미널 행은 live 행을 신설하지 않는다"** 명시 — `dispatch.py:814-815` 필터 불변, 분류기 수준 어휘 계약일 뿐이며 `classify_job()` 직접 호출로만 검증. F-27 착륙 후에도 도달 불가 유지(kill 성공 → 다음 tick 행 소멸이 의도) |
| **N4** | §6.3 `control.py` 표면과 §6.6 검증 호출 불일치(`read_proc_start`/`is_excluded` 미선언) → 복사-실행 시 AttributeError | §6.3에 공개 표면 **전량 등재** — `read_proc_start`(procscan 재수출)·`is_excluded` 포함, 검증 호출과 1:1 시그니처 일치 |
| **N5** | Step 1 검증 #4 grep 가드가 주석 기대값일 뿐 게이트 아님 | **자동 단언으로 승격** — `test $(...\| wc -l) -eq 2` + 실패 시 비영 종료. 3곳→2곳 전이(`dispatch.py:924` 소멸)를 주석에 명시. §9 완료 기준에도 게이트 추가 |

**유지(리뷰 I1~I11 확인 사항)**: 실측 인용 전량 일치, F-28 범위 침범 0, prd.md:410-413 잠긴 결정 재논의 0, `state_evidence` additive-only, `StateTracker` ↔ `--once`/`--json` no-op 정합, 상수 흡수 정합, `COLUMNS` 폭 주입 동작 확인.
