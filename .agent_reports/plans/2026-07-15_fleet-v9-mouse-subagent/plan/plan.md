# fleet v9 구현 플랜 — F-27 마우스 1급 · F-29 서브에이전트 관측 · 잔여 후속

> 계약: `spec/agent-fleet-dashboard/prd.md` **v9** (§4.8 F-27 v9 개정 prd.md:278-284 · F-29 prd.md:290-295 · 확정 결정 v9 prd.md:455-461 · Next v9 prd.md:468)
> 워크트리: `/home/Uihyeop/agent_setting-wt/fleet-v9-mouse-subagent` (브랜치 `fleet-v9-mouse-subagent`)
> intensity: standard · qa: standard · execute = **단일 depth-2 워커** → 스텝 순서가 계약이다
> 베이스라인 (2026-07-15 실측): `python3 -m unittest discover -s tools/fleet/tests -q` → **Ran 416 tests, OK**

---

## ⛔ 0. 절대 안전 규칙 (모든 스텝에 선행 — 비협상)

**실제 `claude`/`codex`/`opencode` 세션을 스폰하거나 시그널하지 않는다.**

v8 사이클에서 execute 워커가 이 경계를 위반했다 — 실세션 1개를 스폰하고 SIGTERM했다(자진 보고: `plans/2026-07-15_fleet-v8-reliability/dev_logs/step_04_f27_control.md`, 철회 기록: 같은 사이클 `plan/plan.md:396-402`의 ⛔ 블록). 철회된 절차는 **규범이 아니다**.

**본 사이클의 유일한 검증 수단**:

| 검증 대상 | 허용 수단 | 금지 |
|---|---|---|
| 상태 분류·kill 게이트 | `classify_session()`/`control.*`에 fixture dict 직접 주입 (`tests/fixtures/state_model/*.json` 선례) | 실세션 스폰 |
| 실 시그널 경로 | `subprocess.Popen(["sleep", "600"])` 프로세스 + monkeypatched `os.kill` (기존 `tests/test_f27_control.py::RealSignalTest` 패턴) | 하네스 프로세스 시그널 |
| 마우스 이벤트 | `curses.getmouse`를 `mock.patch`로 스텁 — **hermetic 단위 테스트만** | 라이브 TUI에서 실제 클릭으로 kill 검증 |
| 렌더 | `--once` / `--json` / `_build_lines` 직접 호출 | — |

`--once`·`--json`은 curses에 진입하지 않고 kill 경로에 도달할 수 없다(`control.py` 어느 함수도 collector/`--json`/scheduler에서 도달 불가 — control.py:13-15). 라이브 TUI 실행은 **눈 검사 전용**이며 그 세션에서 kill 키/클릭을 누르지 않는다.

---

## 1. 스텝 요약 · 분리 가능성

| # | 스텝 | 표면 | 선행 | 분리 가능? |
|---|---|---|---|---|
| 1 | 베이스 키 핸들러 추출 (구조 선행) | `render.py` `_loop` | — | **불가 — Step 5의 전제** |
| 2 | F-27 마우스 1급 | `render.py` (+`control.py` 무변경) | — (Step 1 불요 — §1.1) | 병렬 가능 |
| 3 | F-29 서브에이전트 관측 | `model.py`·`collectors/{opencode,claude,codex}.py`·`render.py`·`fleet.py` | — (Step 2와 **파일은 겹치나 함수는 분리**) | **원리상 병렬 가능 · 단일 워커라 순차 배치** |
| 4 | D3 stage zone 폭 상한 | `render.py` `_dispatch_stage_segs` | — | 병렬 가능 (Step 2/3과 함수 분리) |
| 5 | 스크롤 회귀 테스트 신설 | `tests/` only | **1** | 1 이후 언제든 |
| 6 | 통합 검증 · 미러 동기 | 전역 | 1-5 | 불가 (마감) |

**순서 근거**: Step 3·4는 서로도, Step 2와도 함수 단위로 겹치지 않지만 — Step 3이 `_session_row`를, Step 2가 `_draw`/`_loop`를 만지므로 **같은 파일**이다. 단일 워커라 충돌 위험은 없고, 순차 실행이 각 스텝의 테스트 회귀를 독립 관측 가능하게 한다.

### 1.1 실제 의존 사슬 (선행 주장 정정)

Step 1 → Step 2 선행은 **성립하지 않는다**. §4.1이 밝히듯 `KEY_MOUSE` 분기는 Step 1에 넣지 않으므로(마우스는 base/select/prompt 세 모드에 걸쳐 `_handle_base_key`의 책임이 아니다), Step 2는 `_handle_base_key` 없이 진행 가능하다.

**실제 사슬**: `Step 1 → Step 5 → (Step 2의 A2-6 증명)`

즉 Step 1은 **Step 5의 전제**이고, Step 5가 **Step 2의 acceptance A2-6을 증명**한다. A2-6이 Step 2에 있으면서 Step 5에서만 증명되는 순서 뒤틀림은 남으며 — 단일 워커라 무해하다. **A2-6은 Step 5 완료 시점에 판정한다**(§4.6 acceptance 참조).

Step 1을 여전히 맨 앞에 두는 이유: 회귀 예산 0을 **증명 가능한 상태로 먼저 만들어 두고** 마우스를 넣는 것이, 넣고 나서 증명 수단을 만드는 것보다 안전하다.

**중단 지점**: Step 2 완료 후, Step 3 완료 후가 각각 자연스러운 중단선이다(각각 독립적으로 PRD 절을 만족하고 테스트가 통과함).

---

## 2. 조사에서 확인된 태스크 전제 정정 (2건 — execute 워커는 이것을 전제로 시작할 것)

### 2.1 미러는 `fleet.py`/`fleet.sh`만이 아니다 ★

태스크 지시문은 미러가 "currently `fleet.py`/`fleet.sh` only"라고 했으나 **실측은 전체 트리**다:

```
adapters/claude/tools/fleet/ = collectors/ control.py demo.py fleet.py fleet.sh __init__.py
                               model.py refresh_title.py render.py tests/ titles.py
                               token_{accounting,budget,experiment}.py
```

`tests/test_mirror_parity.py`는 `rglob("*")` 전수 **바이트 매치**를 요구한다(`__pycache__`만 제외). 즉 **본 사이클이 건드리는 모든 파일 + 신규 테스트 파일까지** 미러에 동기돼야 하며, 동기 누락 시 Step 6에서 반드시 실패한다. 동기 명령은 parity 테스트 docstring이 직접 명시:

```bash
rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/
```

### 2.2 스크롤 로직은 현재 테스트 불가능하다 ★ (Step 1의 존재 이유)

Step 3(b) 요구 = `test_arrow_keys_still_scroll_in_base_mode`. 그런데 스크롤 키 처리는 `_loop`(render.py:2610-2635) **안에 인라인**이고, `_loop`는 `curses.wrapper` 아래에서만 실행된다. 현재 구조로는 이 테스트를 hermetic하게 쓸 수 없다 — `_handle_select_key`/`_handle_prompt_key`가 이미 "curses 없이 테스트 가능하게" 밖으로 빼진 것과 같은 이유(render.py:2203 주석: *"Kept out of _loop so they are testable without curses"*)로, 베이스 키도 추출해야 한다.

이 추출은 **Step 5의 전제**다. (Step 2의 전제는 **아니다** — §1.1에서 그 주장을 철회했다: `KEY_MOUSE` 분기는 `_handle_base_key`가 소유하지 않으므로 Step 2는 추출 없이도 진행 가능하다. 다만 Step 2의 acceptance A2-6(회귀 0)은 Step 5의 테스트로만 증명되므로, 증명 수단을 먼저 세워두는 순서를 택한다.) **테스트를 위한 리팩터가 아니라, 회귀 0을 증명 가능하게 만드는 구조 변경**이다.

---

## 3. Step 1 — 베이스 키 핸들러 추출 (구조 선행, 행위 변경 0)

> **행위 변경이 0이어야 한다.** 이 스텝의 성공 기준은 "416 테스트가 그대로 통과 + `_loop`의 관측 가능한 동작이 동일"이다.

### 편집 표면

| 파일 | 영역 | 변경 |
|---|---|---|
| `render.py` :2610-2635 | `_loop` base-mode 키 블록 | `_handle_base_key(ch, body_h)` 로 **추출** — 함수 본문은 현재 분기를 그대로 옮긴다 |
| `render.py` :2203 인접 | 신설 | `_handle_base_key` 를 `_handle_select_key` 옆에 배치(같은 "curses-free 핸들러" 구역) |

### 계약

```python
def _handle_base_key(ch, body_h):
    """Base-mode keys (scroll/a/w). True = handled. Kept out of _loop so scroll can be
    tested without curses — the F-27 regression budget is 0 and an untestable budget is
    not a budget."""
    global _OFFSET
    # KEY_UP/k, KEY_DOWN/j, PPAGE, NPAGE, HOME/g, END/G, a, w — 현재 분기 그대로
```

- `curses.KEY_MOUSE` 분기는 **여기 넣지 않는다** — Step 2가 별도 `_handle_mouse`로 소유한다(마우스는 base/select/prompt 세 모드 전부에 걸치므로 base 핸들러의 책임이 아니다).
- `_loop`는 `if _handle_base_key(ch, body_h): pass` 형태로 호출하되, **`r`(force refresh) 판정과 tick 로직은 `_loop`에 남긴다**(수집 소유는 루프의 몫).
- `_OFFSET = 1 << 30` (END) 의 clamp-in-`_draw` 계약(render.py:2622 주석) 불변.

### 검증

```bash
cd /home/Uihyeop/agent_setting-wt/fleet-v9-mouse-subagent
python3 -m unittest discover -s tools/fleet/tests -q      # 416 OK 유지 (행위 변경 0)
python3 tools/fleet/fleet.py --once | head -5              # 스모크
```

### acceptance
- **A1-1**: 전체 테스트 416 유지, OK. 신규 실패 0.
- **A1-2**: `_handle_base_key`가 `curses` 모듈 없이 import·호출 가능(단, `curses.KEY_UP` 등 상수 참조는 기존 모듈 import 경로를 그대로 사용 — 상수 접근 자체는 headless에서도 안전함을 Step 5 테스트가 실증).

### 리스크
- **R1-1 (낮음)**: 추출 중 분기 누락 → 조용한 스크롤 회귀. **완화**: Step 5의 테스트가 6개 스크롤 키를 전부 고정하며, 이 스텝에서는 diff를 "이동만, 수정 없음"으로 제한한다.

---

## 4. Step 2 — F-27 마우스 1급 재설계 (prd.md:278-284) ★ 본 사이클 핵심

> 계약 원문(prd.md:279): *"행 클릭 = 해당 행 선택(하이라이트, 선택 모드 진입과 동일 상태) → 선택된 행 재클릭 = kill 요청 → 확인 프롬프트의 `[kill]`/`[cancel]` 클릭 타깃으로 확정/취소. 다른 행 클릭 = 선택 이동, 행 밖 클릭 = 해제. 기존 `+N hidden` 클릭 토글과 같은 `_TOGGLE_ROWS`/mouse mask 기제 재사용"*

### 4.1 재사용하는 기존 기제 (신설 금지)

| 기제 | 위치 | 재사용 방식 |
|---|---|---|
| `_TOGGLE_ROWS` 리셋 패턴 | render.py:2504 (`_draw` 최상단, early-return 전) | `_CLICK_ROWS`/`_PROMPT_HITS`도 **같은 지점에서 리셋** — stale 맵이 클릭을 먹는 것을 막는 유일한 이유 |
| `curses.mousemask(BUTTON1_CLICKED)` | render.py:2574 | **그대로** — 새 마스크 비트 추가 없음 |
| `curses.getmouse()` | render.py:2629 | 그대로. **`mx`를 이제 실제로 쓴다** — 현재도 바인딩은 되나(버려지는 건 `_mz`/`_bstate`) 히트 테스트에 쓰이지 않는다. **`except` 경로의 `mx` unbound 결함은 §4.2에서 함께 고친다** |
| `HERDR_ENV` 마우스 스킵 | render.py:2572 | **불변** — herdr에서 마우스 리포팅은 페인을 얼린다(2026-07-01 실관찰). herdr 아래에서는 키보드 폴백이 유일 경로 |
| `_SELECTABLE` / `_entry_id()` | render.py:1383·2224 | 마우스도 **같은 행 집합**을 쓴다 — 클릭 맵은 `_SELECTABLE` 기준(**§4.2.1**) |
| `control.is_excluded()` | render.py:2216 경유 (control.py:143) | 제외 규칙(fleet 자신·조상·구동 세션)은 **자동 적용이 아니라 rung 3의 명시 호출**이다 — `_live_targets()`를 `_draw`에서 쓰지 않기 때문(§4.2.1의 성능 근거). 적용 **시점**만 다르고 효력은 동일: 제외 대상은 선택되지 않으므로 프롬프트에 도달 불가 |
| `_PROMPT` 상태 기계 + `_do_kill` | render.py:2193·2422 | **무변경** — 마우스는 새 입력 경로일 뿐, kill 결정 경로는 하나 |
| `control.py` 전체 | — | **무변경** — 안전 게이트는 이미 UI를 불신하도록 설계됨(control.py:243) |

### 4.2 편집 표면

| 파일 | 영역 | 변경 |
|---|---|---|
| `render.py` :2179 인접 | 상태 | `_CLICK_ROWS = {}` 신설 — `screen_y -> entry` (선택 가능 행의 클릭 맵) |
| `render.py` :2179 인접 | 상태 | `_PROMPT_HITS = []` 신설 — `[(x0, x1, "kill"|"cancel")]` (푸터 프롬프트 클릭 타깃) |
| `render.py` :2504 | `_draw` | `global` 에 둘 추가 + **`_TOGGLE_ROWS`와 같은 줄에서 리셋** |
| `render.py` :2528-2537 | `_draw` 본문 루프 | 가시 행 순회 중 `line_idx = _OFFSET + row` 가 **`_SELECTABLE`** 엔트리의 `line`과 일치하면 `_CLICK_ROWS[row] = entry` (**★ `_live_targets()` 아님 — §4.2.1**) |
| `render.py` :2550 | `_draw` 푸터 | `_prompt_segs` 결과에서 `[kill]`/`[cancel]` 세그먼트의 x 범위를 계산해 `_PROMPT_HITS` 채움. **히트박스는 `[0, w)`와 교집합하고, 부분 클리핑된 버튼은 등록하지 않는다** (§4.5) |
| `render.py` :2264-2333 | `_prompt_segs` | 클릭 타깃 세그먼트 추가 (§4.4) |
| `render.py` :2203 구역 | 신설 | `_handle_mouse(mx, my)` — **curses-free 순수 함수** |
| `render.py` :2627-2633 | `_loop` | `KEY_MOUSE` 분기를 `_handle_mouse` 호출로 교체 + **`_PROMPT` 분기(:2594-2597) 안에 삽입**(§4.4.1) + `except`에서 **`mx = my = None`** 설정 후 조기 반환 (**★ 현재 `except`는 `my`만 설정 → `mx` unbound → `_handle_mouse(mx, my)` 호출 시 `NameError`로 TUI 크래시**) |
| `render.py` :2477-2494 | `_footer_segs` | 마우스 힌트 1개 추가(폭 여유 있을 때만) |

#### 4.2.1 ★ `_CLICK_ROWS`는 `_SELECTABLE` 기준이다 (`_live_targets()` 아님)

`_draw`의 기존 `targets`(:2515)는 **`_live_targets() if _SELECT_MODE else []`** 로 게이트돼 있다. base 모드 — 즉 **첫 클릭 시점** — 에는 항상 `[]`다. 이 변수를 재사용해 클릭 맵을 채우면 **rung 3이 영원히 안 걸리고 rung 4(해제)로 떨어져 마우스 1급 경로 진입 자체가 불가능**하다.

게이트를 푸는 순진한 수정은 더 나쁘다. `_live_targets()`는 엔트리마다 `control.is_excluded()`를 호출하고(:2216), 그 안의 `_ancestors()`가 최대 16회 `/proc/<pid>/stat`을 읽으며 `_current_session_pid()`가 **`~/.claude/sessions/` 전체를 listdir + 매 파일 `json.load`** 한다(control.py:118-140, 캐시 없음). `_draw`는 **매 wake(~10fps** — render.py:2585·2647**)** 돈다 → base 모드에서 현재 비용 0인 경로가 초당 수백~수천 회 JSON 파싱으로 바뀐다.

**결정**:
- `_CLICK_ROWS`는 **`_SELECTABLE`** 기준으로 채운다 → 틱당 추가 비용 **0**.
- `control.is_excluded()` 판정은 **rung 3 클릭 시점에 1회**만 적용한다.
- `_live_targets()` 독스트링의 계약 — *"프롬프트 이전에 걸러진다"*(:2207-2209) — 은 그대로 지켜진다: 클릭이 곧 선택 시도이고, 제외 대상은 선택되지 않으므로 프롬프트에 도달할 수 없다.

### 4.3 `_handle_mouse` 계약 (우선순위 순 — 이 순서가 규범)

```python
def _handle_mouse(mx, my):
    """Mouse is the FIRST-CLASS F-27 path (prd.md:279). Returns True = handled.

    Precedence, in order — each rung is a different mode, and a click means a different
    thing in each:
      1. _PROMPT up  → only the [kill]/[cancel] hit-boxes act. A click anywhere ELSE on
         screen is swallowed (NOT a cancel): a stray click must never resolve a kill
         prompt in either direction. This mirrors _handle_prompt_key's "any other key is
         NOT consent" (render.py:2393).
      2. my in _TOGGLE_ROWS → the existing `+N hidden`/`folded` toggle. Checked before the
         row map because a toggle row is not a selectable row; the two maps never overlap.
      3. my in _CLICK_ROWS  → row click:
           · same identity as _CURSOR_ID → kill REQUEST → _PROMPT = {"stage": "confirm"}
           · different row              → move selection (_CURSOR_ID = id, _SELECT_MODE = True)
      4. otherwise → click outside any row → _exit_select()  (deselect, prd.md:279)
    """
```

**안전 불변식 (이 스텝에서 절대 깨지 않는다)**:
- 재클릭은 **kill 요청**이지 kill이 아니다 — `control.kill_target`에 도달하는 유일한 경로는 여전히 `_do_kill`이며 그 앞에 프롬프트가 있다.
- `working`/`busy` 세션의 이중 확인(`confirm` → `confirm2`)은 마우스에도 **그대로** 적용된다(`requires_double_confirm` 분기가 `_handle_prompt_key`에 이미 있고, 마우스는 그 상태 기계에 진입할 뿐이다).
- fleet 자신·조상·구동 세션은 **클릭으로도 선택 불가** — rung 3이 `control.is_excluded()`를 **클릭 시점에 명시 호출**해 거른다(§4.2.1). `_live_targets()`가 자동으로 걸러주는 것이 **아니다**: 클릭 맵은 `_SELECTABLE` 기준이므로 제외 대상 행도 맵에는 존재하고, **선택 단계에서 거부**된다. render.py:2207-2209의 계약("프롬프트 이전에 걸러진다")은 그대로 지켜진다 — 걸러지는 시점이 draw가 아니라 click일 뿐이다.

### 4.4 ★ 더블클릭 안전 설계 (설계 결정 — 리뷰 필수 포인트)

키보드 경로는 `confirm`=`y`, `confirm2`/`escalate`=`Y`(대문자)로 **의도적으로 다른 키**를 요구한다 — *"holding `y` cannot walk through both"* (render.py:2401·2408).

마우스에는 이 보호가 자동으로 오지 않는다: `[kill]` 버튼이 두 단계에서 **같은 좌표**에 있으면 더블클릭 한 번이 `confirm`과 `confirm2`를 모두 통과한다 — 즉 **working 세션의 이중 확인이 마우스에서 무력화**된다. 이는 prd.md:281의 "working/busy 세션은 경고 + 이중 확인"을 마우스 경로에서 깨는 것이다.

**결정 — 좌표 비겹침 규칙**:
- `confirm` 단계: `[cancel]` 왼쪽, `[kill]` 오른쪽
- `confirm2`/`escalate` 단계: **순서 반전** — `[KILL]` 왼쪽, `[cancel]` 오른쪽

두 단계의 `kill` 히트박스가 **x 범위에서 겹치지 않음**을 단위 테스트로 고정한다. 겹치지 않으면 같은 자리 연타가 2단계를 통과할 수 없다.

반전이 fail-safe 방향으로 접히는 것도 확인했다: `confirm`의 `[kill]`(우)은 `confirm2`에서 `[cancel]`(우) 자리가 되므로, 같은 자리 연타는 kill이 아니라 **취소**로 끝난다.

- 대안(기각): 시간 기반 디바운스 — 임의 상수가 늘고, 느린 더블클릭은 여전히 통과한다. 좌표 규칙이 구조적이다.
- `escalate`(SIGKILL) 단계도 같은 반전 규칙을 적용한다. 방어적 잉여임을 인지한다 — `escalate`는 `_poll_pending_kill`이 `KILL_GRACE_SEC` 경과 후에만 띄우므로(render.py:2468-2474) 더블클릭이 `confirm`에서 도달할 수 없다. 그래도 유지: SIGKILL은 가장 파괴적이므로 SIGTERM을 시작한 그 좌표로 도달 가능해선 안 된다(render.py:2408의 키보드 논리와 동형).

#### 4.4.1 ★★ 반전을 떠받치는 불변식 — `_PROMPT_HITS` 신선도 (명문화 필수)

**좌표 반전은 그 자체로 안전을 보장하지 않는다.** 반전은 "click 2 시점의 `_PROMPT_HITS`가 `confirm2` 단계의 맵"이라는 전제 위에서만 성립한다. `_PROMPT_HITS`는 `_draw` 최상단에서만 리셋·재구축되므로(§4.1이 채택한 `_TOGGLE_ROWS` 패턴, :2504), **재그리기 없이 click 2가 들어오면 `_handle_mouse`는 `confirm` 단계의 낡은 맵을 읽는다** → 그 맵은 우측 x를 `"kill"`로 보고한다 → `confirm2`에서 kill 확정 → **반전이 무력화되고 prd.md:281의 이중 확인이 마우스 경로에서 깨진다.**

**규범 불변식**: `_handle_mouse`의 **모든 반환 경로는 다음 `getch` 이전에 `_draw`를 거친다.**

**구현 규범 (배치가 곧 안전)**: 현행 `_loop`는 이미 이 형태다 —

```python
if _PROMPT is not None:
    _handle_prompt_key(ch)
    _draw(...)          # ← 이 _draw 가 불변식을 만족시킨다
    continue
```

→ `_handle_mouse` 호출은 **반드시 이 블록 안**(`_handle_prompt_key`와 나란히)에 들어간다. 블록 **앞에 자체 `continue`와 함께** 넣으면 `_draw`를 건너뛰어 불변식이 깨진다. R2-2의 "한 줄만 선행 삽입"은 **이 블록 내부 삽입을 의미**하며, 그 밖의 배치는 금지다.

**고정 테스트**: `test_confirm_to_confirm2_transition_repopulates_hits` — 재그리기 없이 같은 좌표를 2회 클릭해도 kill에 도달하지 않음을 직접 고정한다. (`test_hits_are_only_populated_for_the_drawn_rung`는 rung만 볼 뿐 **단계 전이 staleness를 보지 않는다** — 별개 테스트가 필요하다.)

### 4.5 `_prompt_segs` 폭 사다리 통합

`_prompt_segs`는 `pick(*variants)` 폭 사다리를 가진다 — 마지막 rung은 어떤 터미널에도 들어가는 pid-only 형태(render.py:2280-2286). 클릭 타깃 추가는 이 사다리를 **깨면 안 된다**:

- `[kill]`/`[cancel]` 세그먼트는 각 rung에 포함하되, **60폭에서도 마지막 rung이 들어가야 한다**.
- 60폭 최소 rung 예: `" ⚠ kill pid 12345? "` + `[kill]` + `[cancel]` ≈ 19 + 6 + 8 = 33셀 → 60에 여유.
- 폭이 부족해 클릭 타깃이 잘리면 **키보드 키 안내를 우선 보존**한다(prd.md의 폴백 계약 — 마우스는 opt-in, 키보드가 primary: prd.md:88·280). 즉 클릭 타깃이 없는 rung에서도 프롬프트는 여전히 유효하다.
- `_PROMPT_HITS`는 **실제로 그려진 rung** 기준으로만 채운다 — 그리지 않은 버튼의 히트박스가 살아있으면 빈 공간 클릭이 kill이 된다(치명적).
- ★ **`pick()`은 안 맞는 마지막 rung도 반환한다** (:2286 `return variants[-1]`) — 사다리 전부가 `width`를 넘으면 마지막 rung이 그대로 나가고 `_addline`이 잘라낸다. 따라서 "그린 rung만 채운다"만으로는 부족하다: **히트박스를 `[0, w)`와 교집합하고, 부분 클리핑된 버튼은 등록하지 않는다.** 화면 밖으로 밀린 `[kill]`의 히트박스가 살아있으면 안 된다.
- ★ **버튼 x는 rung 조합에 따라 이동한다** — 단계마다 문구 길이가 다르므로 비겹침(§4.4)은 **한 폭에서 검증하면 불충분**하다. 60/120/168 × rung 전조합으로 파라미터화해 고정한다.

### 4.6 검증 (hermetic — 실세션 0)

신규 `tools/fleet/tests/test_f27_mouse.py`:

```python
# 전부 curses.getmouse 스텁 + fixture Session/DispatchJob. 실 프로세스 0, 실 시그널 0.
class MouseSelectionTest:
    test_row_click_selects_and_highlights            # prd.md:279 행 클릭 = 선택
    test_first_click_works_from_base_mode            # ★ §4.2.1 — _SELECTABLE 기준 (게이트 함정)
    test_second_click_same_row_raises_kill_prompt    # 재클릭 = kill 요청 (kill 아님!)
    test_second_click_does_not_reach_kill_target     # ★ control.kill_target 미호출 (mock 스파이)
    test_click_other_row_moves_selection             # 다른 행 = 선택 이동
    test_click_outside_any_row_deselects             # 행 밖 = 해제
    test_toggle_row_click_still_toggles_show_all     # 기존 `+N hidden` 회귀 0
    test_excluded_pid_click_does_not_select          # ★ is_excluded 를 클릭 시점에 1회 적용(§4.2.1)
    test_click_map_costs_nothing_per_tick            # ★ _draw 가 is_excluded 를 호출하지 않음(스파이)
    test_getmouse_exception_does_not_crash           # ★ mx/my unbound → NameError 방지

class MousePromptTest:
    test_kill_hitbox_confirms                        # [kill] 클릭 = 확정
    test_cancel_hitbox_cancels                       # [cancel] 클릭 = 취소
    test_click_elsewhere_while_prompt_is_swallowed   # ★ 빗나간 클릭은 확정도 취소도 아님
    test_working_session_click_needs_second_confirm  # ★ working = confirm → confirm2 (마우스에서도)
    test_confirm_to_confirm2_transition_repopulates_hits  # ★★ §4.4.1 staleness — 같은 좌표 2연타 ≠ kill
    test_kill_hitboxes_do_not_overlap_across_stages  # ★★ §4.4 비겹침 — 60/120/168 × rung 전조합
    test_escalate_hitbox_does_not_overlap_confirm    # ★★ SIGKILL 좌표 분리
    test_hits_are_only_populated_for_the_drawn_rung  # 안 그린 버튼의 히트박스 없음
    test_clipped_button_registers_no_hitbox          # ★ pick() 최종 rung 초과 시 [0,w) 교집합
    test_prompt_fits_at_60_columns                   # 폭 사다리 불변
```

**안전 acceptance 재검증 (prd.md:282-284 — v8에서 이미 통과했으나 마우스 경로로 재확인)**:

```bash
# 기존 F-27 스위트 전량 재실행 — 마우스 추가가 안전 게이트를 우회하지 않음을 실증
python3 -m unittest tools.fleet.tests.test_f27_control -v
python3 -m unittest tools.fleet.tests.test_f27_mouse -v
```

| 안전 계약 | 근거 | 재검증 수단 |
|---|---|---|
| exact pid + `/proc` start-time 재검증 | prd.md:282 | `test_f27_control::VerifyTargetTest` (기존, 무변경) + 마우스 경로가 같은 `_do_kill`을 통과함을 `test_second_click_does_not_reach_kill_target`이 고정 |
| `working`/`busy` 이중 확인 | prd.md:281 | `test_working_session_click_needs_second_confirm` (신규) |
| 자동 제어 0 | prd.md:278·452 | 마우스 핸들러 어디에도 `kill_target` 직접 호출 없음 — grep 가드 테스트 |
| action log append | prd.md:283 | `test_f27_control::ActionLogTest` (기존) |
| registry `done,note=fleet-kill` 마감 | prd.md:284 | `test_f27_control::TestRegistryCloseParity` (기존) |

**렌더 검증**:
```bash
for w in 60 120 168; do echo "=== COLUMNS=$w ==="; COLUMNS=$w python3 tools/fleet/fleet.py --once; done
python3 tools/fleet/fleet.py --json > /tmp/v9_step2.json && python3 -c "import json;d=json.load(open('/tmp/v9_step2.json'));print('json ok', len(d['sessions']))"
```
> ※ heredoc은 stdin을 점유하므로 `--json | python3 - <<'PY'` 형태를 **절대 쓰지 않는다**(v8 round_1 B1 실증: 구현과 무관하게 항상 실패). 파일 경유가 규범이다.

**디자인팀 critic (read-only, F-15 critic 계약 재사용)**:
```bash
for w in 60 120 168; do COLUMNS=$w python3 tools/fleet/fleet.py --once > /tmp/v9_step2_${w}.txt; done
```
→ `디자인팀` critic 모드로 `/tmp/v9_step2_{60,120,168}.txt` 비평 요청 (**read-only, 코드 수정 금지**).
→ verdict를 `_internal/dev_reviews/design_critic_step2.md`에 embed.
→ **비평 범위**: 선택 하이라이트(`A_REVERSE`)가 hot/cooling/cold 틴트 위에서 판독 가능한가 · `[kill]`/`[cancel]` 클릭 타깃이 버튼으로 읽히는가(밑줄/괄호 어느 쪽이 터미널에서 클릭 가능해 보이는가) · 확정 단계 반전 배치가 사용자를 혼란시키지 않고 "다른 결정"으로 읽히는가 · 3폭 전부 경계 미초과.

### acceptance
- **A2-1** (prd.md:279): 행 클릭 → 선택 하이라이트, 재클릭 → kill **요청**(프롬프트), `[kill]` 클릭 → 확정, `[cancel]` 클릭 → 취소, 다른 행 → 이동, 행 밖 → 해제. 6개 전부 단위 테스트로 고정.
- **A2-2** (prd.md:280): 키보드 `s`/`x`/`↑↓`/`jk`/`Esc`/`y`/`n` 경로 **전부 무변경 통과** — 기존 `test_f27_control` 스위트 회귀 0.
- **A2-3** (prd.md:279): 새 mousemask 비트 0, `_TOGGLE_ROWS` 토글 회귀 0, `HERDR_ENV` 스킵 불변.
- **A2-4** (prd.md:281): working/busy 이중 확인이 마우스 경로에서도 성립하며, 두 단계의 kill 히트박스가 x범위에서 겹치지 않는다.
- **A2-5** (prd.md:282-284): 안전 계약 5종 전부 재검증 통과 (위 표).
- **A2-6**: 스크롤 회귀 0 — **base 모드 한정**(§7.1: 선택 모드의 방향키 커서는 v8부터의 기존 계약이며 회귀 아님). **증명은 Step 5**가 소유한다 — 이 acceptance는 Step 5 완료 시점에 판정된다.

### 리스크
- **R2-1 (중)**: `_CLICK_ROWS`가 `_draw`에서 채워지므로 **그린 직후의 화면 좌표에만 유효**하다. tick이 재수집하면 행이 이동한다 — 사용자가 클릭한 순간과 맵이 만들어진 순간 사이에 board가 바뀌면 **엉뚱한 행이 선택**될 수 있다. **완화**: 선택은 `_CURSOR_ID`(identity — `(pid, proc_start)`)로 저장되므로 **선택 자체는 안전**하다(render.py:2187-2191의 설계가 그대로 보호). 위험 구간은 "클릭 → 선택" 1틱뿐이고, 잘못 선택돼도 kill에는 프롬프트가 한 번 더 있으며 프롬프트는 **대상 이름과 pid를 명시**한다(render.py:2278). 즉 오선택은 오kill로 이어지지 않는다.
- **R2-2 (중)**: `_PROMPT` 중 마우스가 도달하려면 `_loop`의 "프롬프트가 모든 키를 삼킨다"(render.py:2592-2597) 분기를 수정해야 한다. **부주의하면 프롬프트 중 다른 키가 새어나간다**. **완화**: 분기를 넓히지 않고 `if ch == curses.KEY_MOUSE: _handle_mouse(...)` **단 한 줄만** 선행 삽입하며, `_handle_mouse`의 rung 1이 "히트박스 외 클릭은 삼킨다"를 보장. `test_click_elsewhere_while_prompt_is_swallowed`가 고정.
- **R2-3 (낮음)**: tmux `set -g mouse on`이 꺼져 있으면 마우스가 아예 동작하지 않는다 — 이는 **결함이 아니라 opt-in 전제**(prd.md:279·88). 키보드 폴백이 전 경로를 커버하므로 회귀 없음. 사용자 혼란 완화로 footer에 마우스 힌트를 1개 노출(폭 여유 시).
- **R2-4 (낮음)**: `BUTTON1_CLICKED`는 터미널에 따라 리포트되지 않고 `BUTTON1_PRESSED`만 오는 경우가 있다. **본 사이클은 마스크를 넓히지 않는다**(기존 `+N hidden` 토글이 이 마스크로 실동작 중이라는 것이 근거). 실기에서 클릭이 안 잡히면 별도 이슈로 분리.

---

## 5. Step 3 — F-29 서브에이전트 관측 (prd.md:290-295)

> 계약: **enrichment 전용 — 세션 존재 판정에 절대 관여하지 않는다**(prd.md:291). 프로세스 백본은 무관.

### 5.1 소스 순서 (prd.md:292 — 완전성 순)

| 순위 | 하네스 | 소스 | 실측 상태 |
|---|---|---|---|
| 1 | OpenCode | DB `session.parent_id` + `agent` 컬럼 | ★ **이미 SELECT 중** — `collectors/opencode.py:19-20`의 `_COLS`에 `agent`, `parent_id`가 있으나 현재 `_query`는 `parent_id IS NULL` 최상위만 취하고 자식을 **버린다**(:63-72). 자식 조회만 추가하면 됨 — 가장 완전(토큰·비용 포함) |
| 2 | Claude | transcript `isSidechain: true` + Agent `tool_use`↔`tool_result` 짝짓기 | `_tail_ai_title`(claude.py:75)의 **역방향 성장 스캔 + `(mtime,size)` 캐시** 패턴 재사용. 같은 파일을 이미 tail 중 |
| 3 | Codex | state DB threads 표면 probe | **확정 전에는 구현하지 않는다** — probe 결과 확정 불가면 정직한 결손(`—`), 추측 표시 금지(prd.md:292) |

### 5.2 편집 표면

| 파일 | 변경 | 계약 |
|---|---|---|
| `model.py` | `SubAgent` dataclass 신설 + `Session.subagents: Optional[list] = None` | **additive only** — 기존 필드 무변경. `None` = 소스 부재/미확인(결손), `[]` = 확인했으나 없음 |
| `collectors/opencode.py` | `_child_sessions(con, sid)` 신설 → `enrich`에서 `sess.subagents` 채움 | 기존 `_query`/ctx% 경로 **무변경**. 예외는 기존처럼 삼켜 `subagents=None` |
| `collectors/claude.py` | `_tail_subagents(path)` 신설 + `_SUBAGENT_CACHE` | `_TITLE_CACHE`와 **별도 캐시**(같은 `(mtime,size)` 키 패턴). `enrich`의 title 경로와 독립 |
| `collectors/codex.py` | probe만 — 확정 못 하면 **코드 추가 없음** | 정직한 결손 |
| `render.py` | `└⚡<agent-type> ⏳<경과>` 서브 행 + 세션 행 `⚡N` 배지 + `a` 토글 완료분 dim | pulse 카운트 **혼입 금지** |
| `fleet.py` / `--json` | `subagents` 키 additive | 기존 키 무변경 |

### 5.3 표시 계약 (prd.md:293)

- 서브 행: `└⚡<agent-type> ⏳<경과>` — 분사 잡 `└▸🚀`와 **글리프로 구분**(`⚡` vs `🚀`).
- 기본 = **활성만**. 완료분은 숨김 → `a` 토글 시 dim 노출(F-18b dim row 계열).
- 세션 행에 `⚡N` 카운트 배지.
- **pulse 혼입 금지** (prd.md:293): `fleet <spinner> N working · M idle · ↳ J jobs` 의 어느 카운트에도 서브에이전트가 들어가지 않는다 — F-18b의 mem-worker 제외와 **같은 계열**. 별도 집계.
- **글리프 위계 확인** (prd.md:232): `🧠`는 두 의미(mem-worker 수 / mem 이벤트)로 이미 포화. `⚡`는 신규 — 기존 글리프와 충돌 없음을 legend에서 확인하고, legend는 **등장 시만** 노출(F-12).
- `_NAME_WIDE_MAX`(40) 캡과 `⚡N` 배지: 배지는 **child-count/gate 태그와 같은 suffix 예약 계열**(prd.md:215) — name zone을 잡아먹지 않도록 suffix 예산에 먼저 예약.

### 5.4 검증

신규 `tools/fleet/tests/test_f29_subagents.py`:

```python
class OpenCodeSubagentTest:      # 임시 sqlite DB fixture — 실 opencode 무관
    test_child_rows_become_subagents
    test_agent_column_maps_to_type
    test_absent_parent_id_yields_no_subagents
    test_db_without_agent_column_degrades_to_none    # tolerant (F-3 동형)

class ClaudeSidechainTest:       # 임시 jsonl transcript fixture
    test_sidechain_lines_pair_tool_use_and_tool_result
    test_unpaired_tool_use_counts_as_active
    test_malformed_lines_are_skipped                 # tolerant
    test_cache_keyed_on_mtime_and_size               # 재읽기 없음

class NoRegressionTest:          # ★ 회귀 없음 원칙 (prd.md:294)
    test_source_absent_omits_subrow_entirely
    test_parse_failure_omits_subrow_entirely
    test_subagents_never_enter_pulse_counts          # ★★ prd.md:293
    test_session_existence_unaffected_by_subagents   # ★★ prd.md:291 백본 불가침
    test_json_key_is_additive                        # 기존 키 무변경
```

```bash
python3 -m unittest tools.fleet.tests.test_f29_subagents -v
for w in 60 120 168; do echo "=== COLUMNS=$w ==="; COLUMNS=$w python3 tools/fleet/fleet.py --once; done
python3 tools/fleet/fleet.py --json > /tmp/v9_step3.json
python3 -c "import json;d=json.load(open('/tmp/v9_step3.json'));print('subagents key present:', any('subagents' in s for s in d['sessions']))"
```

**디자인팀 critic** (read-only): `/tmp/v9_step3_{60,120,168}.txt` → `_internal/dev_reviews/design_critic_step3.md`.
**비평 범위**: `└⚡` 서브 행이 `└▸🚀` 분사 행과 시각적으로 구분되는가 · `⚡N` 배지가 name zone/40열 캡을 침범하지 않는가 · 서브에이전트 다수 세션에서 세로 폭증이 없는가(F-15의 "done 접기" 계열 문제) · 3폭 경계 미초과.

### acceptance
- **A3-1** (prd.md:291): 서브에이전트 수집 실패·부재가 **세션 목록에 영향 0** — 백본 불가침을 테스트로 고정.
- **A3-2** (prd.md:292): 소스 순서 OpenCode → Claude → Codex. Codex 미확정 시 `—`(추측 표시 0).
- **A3-3** (prd.md:293): `└⚡` 서브 행 + `⚡N` 배지 + `a` 토글 완료분 dim. **pulse 카운트 혼입 0**.
- **A3-4** (prd.md:294): zero-injection 유지(read-only), `--json` additive `subagents`, 소스 부재 → 서브 행 생략(회귀 0).

### 리스크
- **R3-1 (낮음 — 재평가됨)**: Claude sidechain 짝짓기(`tool_use`↔`tool_result`)를 역방향 tail(`_tail_ai_title` 계열)로 수행한다. **역방향 tail의 성질이 오히려 유리하다**: `tool_use`가 스캔 창 안이면 그 뒤에 오는 `tool_result`도 **필연적으로 창 안**이다(append-only 로그이므로). 따라서 "짝 없는 `tool_use` = 아직 미완 = **활성**"은 추측이 아니라 **구조적으로 정확**하다. 실제 결손은 짝 없는 `tool_result`(= `tool_use`가 창 밖) 쪽뿐이고, 그것은 **완료분이라 어차피 기본 숨김**이다(prd.md:293). **완화**: 짝 없는 `tool_result`는 무시. 스캔 창은 `_tail_ai_title`의 성장 스캔(×8)을 재사용. → prd.md:292의 "추측 표시 금지"와 완전 정합.
- **R3-2 (낮음)**: OpenCode `_query`가 `parent_id IS NULL` 실패 시 아무 세션이나 fallback한다(:64). 그 fallback이 **자식 세션**이면 자식의 자식을 찾게 된다. **완화**: 서브에이전트 조회는 `_query`가 고른 sid 기준이며, fallback 경로였는지를 구분해 자식 조회를 건너뛴다.
- **R3-3 (낮음)**: 틱당 DB/transcript 추가 읽기 비용. **완화**: opencode는 **이미 열린 커넥션 재사용**(추가 connect 0), claude는 `(mtime,size)` 캐시 → 변화 없는 파일 재읽기 0.
- **R3-4 (낮음)**: `⚡` 글리프가 double-width로 정렬을 깨뜨릴 수 있다. **완화**: `_ICON_PARENT`/`_ICON_CHILD`의 ASCII degrade 선례(prd.md:142)를 따라 한 곳에서 교체 가능하게 상수화.

---

## 6. Step 4 — D3: dispatch stage zone 대칭 폭 상한 (v8 사이클 발견)

> 근거: v8 `_internal/test_reviews/test_review.md:89-110` (독립 design critic 발견 → code-test 재측정 확인) + `final_report.md:51`.

### 문제 (실측)

```
168열 최장 행: line=15  width=163  slack=5    ← dispatch conductor 행
상한 상수: _NAME_WIDE_MAX=40 (name) · _DISPATCH_NAME_MAX=18 (dispatch 이름)
         → stage/meta suffix(`dev·std/conductor/qa:~std  code: plan✓ › exec✓ › test`)를 묶는 상수 없음
```

**168열 무오버플로는 구조적 보장이 아니라 5열 여유에 의존하는 부수적 상태다.** conductor/qa 라벨이 6열 길어지거나 stage가 `test✓ › report`로 진행하면 다시 터진다. 60폭 오버플로 5건 중 2건도 **같은 뿌리**다.

### 편집 표면

| 파일 | 영역 | 변경 |
|---|---|---|
| `render.py` :523 인접 | 상수 | `_STAGE_ZONE_MAX` **신설** — `_NAME_WIDE_MAX`(:523)/`_DISPATCH_NAME_MAX`(:878)/`_PROFILE_MAX`(:941) 와 **같은 idiom**: 한 상수, 한 곳 |
| `render.py` :704 | `_dispatch_stage_segs` | 반환 세그먼트의 총 display 폭을 `_STAGE_ZONE_MAX`로 상한 |

**드롭 우선순위** — 새 어휘를 만들지 않고 F-9(c)의 기존 규칙(`_dispatch_role_suffix`:958-967의 `qa → intensity → role` 순 **성분 통째 드롭**, 중간 tail-cut 금지)을 **그대로 미러**한다. breadcrumb은 과거 스테이지(`plan✓ › exec✓`)를 먼저 접고 **활성 스테이지를 마지막까지 보존**한다 — SD-F2(prd.md:164)에서 conductor breadcrumb의 정보 가치는 "지금 어디"이지 "어디를 지났나"가 아니다.

**초기값 근거**: 168열에서 최장 행이 163 → slack 5. 대칭 상한을 두어 **최장 행이 상한으로 결정되게** 한다. 실측 기반으로 값을 고르되 — 현재 stage zone 실폭을 먼저 계측(`_build_lines` 출력에서 해당 세그먼트 폭)하고, **현행 렌더를 깎지 않는 최소값**을 택한다(회귀 0 우선). 상한 도입 자체가 목적이고 값 튜닝은 부차다.

### 검증

`tools/fleet/tests/test_f22_name_cap.py`의 **폭 테스트 패턴을 그대로 미러**해 `test_d3_stage_zone.py` 신설:

```python
test_cap_lives_in_exactly_one_constant       # test_f22_name_cap.py:44 미러
test_stage_zone_never_exceeds_the_cap
test_long_conductor_label_is_dropped_not_tail_cut   # F-9(c) 성분 드롭
test_active_stage_survives_when_past_stages_drop    # SD-F2 우선순위
test_168_no_overflow_is_structural_not_incidental   # ★ D3의 본론
test_short_rows_are_unaffected               # 회귀 0
```

```bash
python3 -m unittest tools.fleet.tests.test_d3_stage_zone -v
# 3폭 오버플로 실측 (D3 재측정 — v8 베이스라인: 60→5건, 120→0, 168→0[slack 5])
for w in 60 120 168; do
  echo -n "width=$w over: "
  COLUMNS=$w python3 tools/fleet/fleet.py --once | awk -v w=$w '{ if (length($0) > w) c++ } END { print c+0 }'
done
```
> ※ `awk length`는 바이트가 아닌 문자 기준이나 CJK/이모지 display-cell과는 다르다 — **참고 지표**이며 정본은 `_dw()` 기반 단위 테스트다.

### acceptance
- **A4-1**: `_STAGE_ZONE_MAX` 상수 1개, 한 곳(`test_cap_lives_in_exactly_one_constant`).
- **A4-2**: 168열 무오버플로가 **구조적** — stage 라벨을 인위적으로 늘린 fixture에서도 경계 미초과.
- **A4-3**: 드롭은 성분 단위(중간 tail-cut 0), 활성 스테이지 보존.
- **A4-4**: 회귀 0 — 현행 짧은 행 렌더 무변경.
- **A4-5** (정직성 조건, v8 test_review.md:210): 결과 보고에서 "168 오버플로 0"을 **이제는 구조적 보장으로 말할 수 있다** — 단 60폭은 여전히 legend/mem/usage 요약 행 원인으로 미충족이며(**D4, 본 스텝 스코프 밖**) 이를 보고에 명시한다.

### 리스크
- **R4-1 (낮음)**: 상한이 너무 낮으면 현행 정보가 사라진다(회귀). **완화**: 실폭 계측 후 "현행을 깎지 않는 최소값" 채택 + `test_short_rows_are_unaffected`.
- **R4-2 (낮음)**: 60폭은 이 스텝으로 해결되지 않는다(D4의 legend/mem/usage 원인이 별개). **스코프 밖임을 명시** — 60폭 5건 중 stage zone 원인 2건만 개선되면 성공.

---

## 7. Step 5 — 스크롤 회귀 테스트 신설 (F-27 회귀 예산 0의 증명)

> 전제: **Step 1**(`_handle_base_key` 추출). 그 전에는 hermetic하게 쓸 수 없다(§2.2).

신규 `tools/fleet/tests/test_scroll_regression.py`:

```python
class BaseModeScrollTest:
    test_arrow_keys_still_scroll_in_base_mode    # ★ 태스크 명시 요구
    test_jk_still_scroll_in_base_mode
    test_pgup_pgdn_page_scroll
    test_home_end_jump_to_top_and_bottom
    test_a_still_toggles_show_all
    test_w_still_cycles_layout

class ScrollIsolationTest:
    test_base_mode_keeps_arrow_keys_when_nothing_is_selected  # ★ 회귀 예산 0의 실제 범위
    test_select_mode_intentionally_takes_arrow_keys           # ★ §7.1 — 명시된 동작을 고정
    test_mouse_click_does_not_disturb_scroll_offset           # ★ Step 2 회귀 0
    test_prompt_does_not_leak_keys_to_scroll                  # render.py:2592
```

### 7.1 ★ 결정 — 클릭 한 번이 방향키를 가져간다 (의도된 동작)

rung 3이 `_SELECT_MODE = True`로 만들면 `_handle_select_key`가 `↑↓`/`jk`를 가로챈다(render.py:2598-2601·2363-2368). prd.md:279가 마우스 행 클릭을 *"선택 모드 진입과 동일 상태"* 로 규정하므로 이는 **PRD 위반이 아니라 요구된 동작**이다.

그러나 실질 변화는 인정해야 한다: v8에서는 `s` 키로 **의도적 opt-in** 해야 방향키를 잃었지만, v9에서는 **빗나간 클릭 한 번**으로 발생한다. 이는 §3 스크롤 계약(prd.md:80-81)과의 실질적 긴장이다.

**결정**: PRD 요구를 그대로 따른다(선택 모드 진입 = 동일 상태). 이탈 경로가 이미 넓어 비용이 낮다 — `Esc`/`s` 키, **행 밖 클릭**(rung 4) 어느 쪽이든 즉시 해제되고 방향키가 돌아온다.

**따라서 "스크롤 회귀 0"의 범위를 명확히 한다**: **base 모드 한정**이다 — 아무것도 선택하지 않은 사용자(=kill을 쓰지 않는 전 사용자, render.py:2182-2183이 보호하려는 바로 그 집단)의 스크롤은 100% 불변. 선택 모드에서 방향키가 커서로 가는 것은 v8부터의 기존 계약이며 회귀가 아니다. A2-6·C3에 이 범위를 못박는다.

**설계 근거**: `↑↓`는 v2 스크롤 계약(spec §3 키 표)이고 F-27은 **모드 커서**로 이를 보호한다 — *"↑↓ is already bound to scroll … so taking it would regress scrolling for everyone who never kills anything"*(render.py:2182-2183). 이 테스트는 그 계약을 **실행 가능한 형태로 고정**한다. 마우스 1급이 들어온 지금 더 중요하다: 클릭이 선택 모드를 켜므로, base 스크롤이 조용히 뺏길 경로가 하나 늘었다.

```bash
python3 -m unittest tools.fleet.tests.test_scroll_regression -v
```

### acceptance
- **A5-1**: 6개 base 키 전부 고정, curses 없이 실행(hermetic).
- **A5-2**: `ScrollIsolationTest` 4개가 **§7.1의 결정된 경계**를 고정한다 — (a) 아무것도 선택되지 않은 base 모드는 방향키를 100% 유지 (b) 선택 모드는 방향키를 **의도적으로 커서에 쓴다**(침범이 아니라 v8부터의 기존 계약 — prd.md:279) (c) 마우스 클릭이 `_OFFSET`을 흔들지 않음 (d) 프롬프트가 스크롤로 키를 흘리지 않음.

### 리스크
- **R5-1 (낮음)**: `curses.KEY_UP` 등 상수는 curses import를 요구한다. **완화**: render.py가 이미 조건부 import(`curses is None` 가드, :2651)를 가지므로 테스트는 실제 상수를 그대로 쓴다. curses 부재 환경이면 `skipTest`.

---

## 8. Step 6 — 통합 검증 · 미러 동기 (마감)

```bash
cd /home/Uihyeop/agent_setting-wt/fleet-v9-mouse-subagent

# 1) 전체 회귀 — 베이스라인 416, 신규 4스위트(f27_mouse/f29_subagents/d3_stage_zone/scroll_regression) 추가 → ≥416 + OK
python3 -m unittest discover -s tools/fleet/tests -q

# 2) 3폭 렌더 눈 검사
for w in 60 120 168; do echo "=== COLUMNS=$w ==="; COLUMNS=$w python3 tools/fleet/fleet.py --once; done

# 3) --json 스모크 (heredoc·파이프 금지 — 파일 경유)
python3 tools/fleet/fleet.py --json > /tmp/v9_final.json
python3 -c "import json;d=json.load(open('/tmp/v9_final.json'));print('sessions',len(d['sessions']),'jobs',len(d.get('jobs',[])))"

# 4) 미러 동기 (§2.1 — tests/ 신규 파일 포함 전체 트리)
rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/
python3 -m unittest tools.fleet.tests.test_mirror_parity -v

# 5) 미러 동기 후 전체 재실행 (rsync가 무언가를 깨지 않았음을 확인)
python3 -m unittest discover -s tools/fleet/tests -q
```

### 완료 기준 (전부 충족해야 사이클 종료)

| # | 기준 | 근거 |
|---|---|---|
| C1 | 전체 테스트 **≥416, OK**, 신규 실패 0 | 베이스라인 |
| C2 | F-27 마우스 6동작 + 안전 5계약 전부 통과 | prd.md:279-284 |
| C2b | **§4.4.1 재그리기 불변식 + §4.2.1 클릭 맵 기준**이 코드·테스트로 고정 | plan-check 🔴 2건 |
| C3 | 키보드 폴백 회귀 0 · 스크롤 회귀 0 (**base 모드 한정** — §7.1) | prd.md:280, A2-6/A5-1 |
| C4 | F-29 백본 불가침 + pulse 혼입 0 + `--json` additive | prd.md:291·293·294 |
| C5 | stage zone 상한 상수 1개, 168 무오버플로 **구조적** | v8 D3 |
| C6 | 3폭 `--once` 렌더 + `--json` 스모크 통과 | Next v9 (prd.md:468) |
| C7 | 디자인 critic 비평 2건 수령·기록 | F-15 critic 계약 |
| C8 | 미러 parity 통과 | §2.1 |
| C9 | **실세션 스폰·시그널 0** — dev log에 명시 | §0 |

---

## 9. 스코프 밖 (계획하지 않는다 — 명시)

- **F-28** (분사 정책 연동 관제) · **F-30** (처리 과정 시각화 뷰): stage-dispatch v9 topology registry / route record **착륙 대기**(prd.md:289·296). v9는 F-30의 *방향만* 등재하며 조기 설계를 고정하지 않는다.
- **D4** (60폭 legend/mem/usage 요약 행 미축약, 5건 중 3건): Step 4의 stage zone과 **원인이 다르다**. 기존 결함이며 본 사이클 스코프 밖 — 결과 보고에 잔존 명시.
- `BUTTON1_PRESSED` 등 마우스 마스크 확장 (R2-4).

---

## 10. 리스크 총괄 (심각도 순)

| # | 리스크 | 심각도 | 완화 |
|---|---|---|---|
| **§4.4.1** | **`_PROMPT_HITS` staleness — 재그리기 없이 click 2가 들어오면 좌표 반전이 무력화되고 working 이중 확인이 마우스에서 깨진다** | **높음 (설계로 해소)** | `_handle_mouse`의 모든 반환 경로가 `_draw`를 거친다를 **규범 불변식**으로 승격 + `_PROMPT` 분기 **안** 삽입 강제 + `test_confirm_to_confirm2_transition_repopulates_hits` |
| **§4.2.1** | **`_CLICK_ROWS`를 `_live_targets()` 기준으로 채우면 base 모드 첫 클릭이 죽고, 게이트를 풀면 10fps `/proc`+JSON 폭풍** | **높음 (설계로 해소)** | `_SELECTABLE` 기준으로 채우고 `is_excluded`는 **클릭 시점 1회** 지연 적용 → 틱당 비용 0 + `test_click_map_costs_nothing_per_tick` |
| R2-2 | 프롬프트 중 마우스 도달을 위해 "모든 키 삼킴" 분기를 수정 → 다른 키 누출 | **중** | `_PROMPT` 블록 **내부**에 한 줄 삽입(§4.4.1) + rung 1이 히트박스 외 클릭 삼킴 + 전용 테스트 |
| R2-1 | 클릭 좌표 맵이 tick 재수집으로 낡음 → 오선택 | **중** | 선택은 identity 기반이라 안전; 오선택→오kill 경로는 프롬프트가 pid·이름 명시로 차단 |
| §4.4 | 마우스 더블클릭이 working 세션 이중 확인을 무력화 | **중 (설계로 해소)** | 확정 단계 히트박스 **좌표 반전**(fail-safe 방향으로 접힘) + 60/120/168 × rung 전조합 비겹침 테스트 |
| 🟡5 | `getmouse()` 예외 시 `mx` unbound → `NameError`로 TUI 크래시 | **중** | `except`에서 `mx = my = None` 설정 + 조기 반환 + `test_getmouse_exception_does_not_crash` |
| 🟡4 | `pick()` 최종 rung이 폭을 넘어 클리핑 → 화면 밖 `[kill]` 히트박스 생존 | **중** | 히트박스 `[0, w)` 교집합 + 부분 클리핑 버튼 미등록 |
| §7.1 | 빗나간 클릭 한 번이 방향키를 커서로 가져감 | 낮 (의도된 동작) | PRD 요구(prd.md:279) 그대로 · 이탈 경로 3종(`Esc`/`s`/행 밖 클릭) · 회귀 0은 **base 모드 한정**으로 범위 명시 |
| R1-1 | 추출 중 스크롤 분기 누락 | 낮 | "이동만, 수정 없음" diff + Step 5 테스트 |
| R4-1 | stage zone 상한이 낮아 현행 정보 삭제 | 낮 | 실폭 계측 후 최소값 + 회귀 테스트 |
| R3-1 | Claude sidechain 짝짓기 | 낮 (재평가) | 역방향 tail 성질상 "짝 없는 `tool_use` = 활성"이 구조적으로 정확 |
| R3-2/3/4 | opencode fallback 오조회 · 틱 비용 · `⚡` double-width | 낮 | fallback 구분 · 커넥션/캐시 재사용 · ASCII degrade 상수화 |
| R2-3/R5-1 | tmux mouse off · curses 부재 | 낮 | opt-in 전제(회귀 0) · skipTest |
