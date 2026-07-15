# test log 04 — F-27 안전 계약 **독립** 재검증 (마우스 경로 포함)

> execute의 테스트 주장은 **입력**이지 증거가 아니다. 본 로그는 code-test가 **직접 작성한** 프로브(`/tmp/v9_indep_probe.py`, `/tmp/v9_indep_probe2.py`)의 결과다. 소스 트리에 테스트를 쓰지 않았다(write scope 밖).

## ⛔ 안전 준수 선언

- 실 `claude`/`codex`/`opencode` 세션 **스폰 0 · 시그널 0**.
- 실 시그널 경로는 `subprocess.Popen(["sleep","600"])` + `mock.patch("os.kill")`로만 검증(plan §0 허용 수단 표).
- 검증 후 harness 프로세스 8개 전부 생존 확인(etimes 5039~36089s, 무영향).
- 프로브 sleep 프로세스 전부 회수(leftover 0).

## 1. 규범 구현 규칙 2건 — 코드 실물 확인

### §4.4.1 — `_handle_mouse`가 `_PROMPT` 블록 **내부**에 있는가

`render.py:2884-2895` 실물:

```python
        if _PROMPT is not None:
            # §4.4.1 — _handle_mouse MUST be called from inside this block (not before it with
            # its own `continue`): the _draw two lines below is what repopulates _PROMPT_HITS
            # for the CURRENT stage before the next getch can land a click.
            if ch == curses.KEY_MOUSE:
                mx, my = _getmouse_xy()
                if mx is not None:
                    _handle_mouse(mx, my)
            else:
                _handle_prompt_key(ch)
            _draw(stdscr, sessions, jobs, section, malformed, memory=mem_snapshot)
            continue
```

**준수 ✅** — 블록 내부, `_draw`가 뒤따르고 `continue` 앞. 불변식("모든 반환 경로는 다음 `getch` 이전에 `_draw`를 거친다") 성립. 배치 의도가 주석으로 코드에 박혀 있어 후속 리팩터가 무심코 깨기 어렵다.

### §4.2.1 — `_CLICK_ROWS`가 `_SELECTABLE` 기준인가 (`_live_targets()` 아님)

```
render.py:2821   _CLICK_ROWS[row] = entry        ← _SELECTABLE 순회 중
render.py:2794   targets = _live_targets() if _SELECT_MODE else []   ← 기존 게이트, 무변경
render.py:2340   return control.is_excluded(pid)  ← _click_target_excluded, 클릭 시점 1회
render.py:2342   return True                      ← 해석 불가 pid = fail closed
```

**준수 ✅** — base 모드(`_SELECT_MODE=False`)에서 `_draw`는 `is_excluded`를 호출하지 않으므로 틱당 추가 비용 0. `is_excluded`는 rung 3 클릭 시점에만 적용되고, **해석 불가 시 fail-closed**(내가 직접 검증, 아래 D-3).

## 2. 독립 프로브 결과 — 안전 계약 6종

```bash
python3 /tmp/v9_indep_probe.py    # A~D
python3 /tmp/v9_indep_probe2.py   # E~F (권위 빌더 사용)
```

```
A_StartTimeGuard.test_start_time_mismatch_refuses_kill ................ ok
A_StartTimeGuard.test_correct_start_time_is_accepted .................. ok
B_DoubleConfirm.test_single_approval_on_working_is_refused_by_control .. ok
C_AutoControlZero.test_mouse_reclick_raises_prompt_but_never_kills ..... ok
C_AutoControlZero.test_stray_click_while_prompted_neither_kills_nor_cancels ok
D_Exclusion.test_excluded_row_click_does_not_select ................... ok
D_Exclusion.test_fleet_self_pid_is_excluded_for_real .................. ok
D_Exclusion.test_unresolvable_pid_fails_closed ........................ ok
E_ActionLog.test_refusal_and_success_both_append ...................... ok
F_CoordInversion.test_kill_hitboxes_never_overlap_across_stages ....... ok
F_CoordInversion.test_same_spot_doubleclick_cannot_walk_confirm_to_confirm2 ok
```

### A — start-time 불일치 → kill 거부 (PID 재사용 가드, prd.md:282)

```python
r = control.kill_target(p.pid, "999999999", "sid1", "stale", "single")
# → "refused";  killer.assert_not_called()   ← 시그널이 프로세스를 떠나지 않음
r = control.kill_target(p.pid, _start_of(p.pid), "sid1", "stale", "single")
# → "ok";       killer.call_count == 1       ← 정확히 하나의 시그널
```

**PASS** — 위조 start-time은 거부되고 `os.kill`이 아예 호출되지 않는다. 올바른 start-time에서만 정확히 1회 시그널.

### B — `working`/`busy` 이중 확인 (prd.md:281)

```python
control.kill_target(pid, <correct start>, "s", "working", "single")  # → "refused"
```

`control.single_confirm_allowed`는 **화이트리스트 default-deny**:

```python
SINGLE_CONFIRM_STATES = ("unused", "stale", "dead")
# control.py:206 — return state in DOUBLE_CONFIRM_STATES or registry_status == "busy"
```

**PASS** — `busy`는 `registry_status`로 처리됨(PRD의 "working/busy" 양쪽 커버). 미등록/신규 상태는 자동으로 "더 많은 확인 필요"로 떨어진다 — 새 상태가 한 키로 통과할 수 없는 구조.

### C — 자동 제어 0 (prd.md:278·452) ★ 마우스 경로

`kill_target` 전 호출 지점 grep:

```
control.py:233  def kill_target(...)          ← 정의
render.py:2679  r = control.kill_target(...)  ← _handle_prompt_key 안
render.py:2692  r = control.kill_target(...)  ← _handle_prompt_key 안
```

**마우스 핸들러는 `kill_target`을 직접 호출하지 않는다.** 히트박스는 키스트로크를 재생한다:

```python
if action == "kill":
    _handle_prompt_key(ord("y") if _PROMPT["stage"] == "confirm" else ord("Y"))
else:
    _handle_prompt_key(_ESC)
```

→ 마우스와 키보드가 **동일한 단일 결정 경로**를 공유. 내 프로브가 직접 확인:
- 선택 행 재클릭 → `_PROMPT["stage"]=="confirm"` 이 뜨고 `kill_target` **미호출** ✅
- 프롬프트 중 히트박스 밖 클릭(40,3) → `kill_target` 미호출 **AND** `_PROMPT`가 여전히 살아있음(취소도 아님) ✅ — 빗나간 클릭이 어느 방향으로도 kill 프롬프트를 해소하지 않는다.

**PASS** — 명시적 사용자 확인 없이 시그널이 나가는 코드 경로 없음.

### D — fleet 자신 / 현재 세션 제외 (prd.md:282)

- 제외 대상 행 클릭 → `_CURSOR_ID` 여전히 `None`, `_PROMPT` `None` — **선택 자체가 안 됨** ✅
- `control.is_excluded(os.getpid())` → `True` (실측, fleet 자신) ✅
- `is_excluded`가 예외를 던지면 `_click_target_excluded` → `True` (**fail-closed**) ✅

**PASS.**

### E — action log append (prd.md:283)

```bash
FLEET_ACTION_STATE_DIR=<tmp>   # hermetic override (control.py:42 actions_root)
```

실제 기록된 2행:

```json
{"ts":1784110437.302099,"action":"refused","pid":3303390,"sid":"s","state":"stale",
 "approval":"single","result":"refused","reason":"start_time_mismatch"}
{"ts":1784110437.3029468,"action":"sigterm","pid":3303390,"sid":"s","state":"stale",
 "approval":"single","result":"ok","reason":null}
```

**PASS** — 성공뿐 아니라 **거부도** 기록된다. prd.md:283 요구 필드(`ts/action/pid/sid/state/승인 방식`) 전부 존재. 관제 도구가 자기 행위를 스스로 관측 대상으로 남긴다는 계약 충족.

### F — 좌표 반전 비겹침 (§4.4, 마우스 고유 위험)

**권위 빌더**(`render._prompt_hit_boxes`)로 측정 — 내 1차 프로브는 `"kill" in text`로 경고 **산문**까지 잡는 오류가 있었고, 정정 후 재측정:

```
w=60   confirm={}                      confirm2={}                       escalate={kill:(44,50), cancel:(51,59)}
w=80   confirm={}                      confirm2={kill:(55,61), cancel:(62,70)}  escalate={kill:(44,50), ...}
w=100  confirm={cancel:(80,88), kill:(89,95)}  confirm2={}               escalate={}
w=120  confirm={cancel:(80,88), kill:(89,95)}  confirm2={kill:(100,106), cancel:(107,115)}  escalate={kill:(98,104), ...}
w=168  confirm={cancel:(80,88), kill:(89,95)}  confirm2={kill:(100,106), cancel:(107,115)}  escalate={kill:(98,104), ...}
w=200  (= w=168)
```

실제 공격 시나리오 재현 — *confirm에서 `[kill]`을 클릭한 그 x를 그대로 재클릭*:

```
w=120  re-click x=89 at confirm2 lands on: nothing  (kill avoided)
w=168  re-click x=89 at confirm2 lands on: nothing  (kill avoided)
```

**PASS** — 두 단계의 `kill` 히트박스가 x범위에서 겹치지 않으며, 같은 자리 연타가 `confirm`→`confirm2`를 통과하지 못한다. 60/80/100폭은 한쪽 단계에 버튼이 없어 공격 자체가 성립 불가.

`_prompt_hit_boxes`는 `pw == _dw(text)` 조건으로 **통째로 그려진 버튼만** 등록 — 부분 클리핑된 버튼의 히트박스가 살아남지 않는다(§4.5 요구 충족, 코드 실물 확인).

### 부수 관찰 — 60폭에서 마우스 kill 경로 부재 (🟢 정보성)

`w=60`의 `confirm`/`confirm2`는 히트박스 `{}` — 폭 사다리가 클릭 타깃을 떨어뜨리고 **키보드 안내를 보존**한다. 이는 plan §4.5의 우선순위 규칙(*"폭이 부족해 클릭 타깃이 잘리면 키보드 키 안내를 우선 보존"*)을 정확히 따른 것이며 **안전한 방향**(마우스로 kill 불가 = 더 보수적).

다만 plan §4.5:234의 산출 예시(*"60폭 최소 rung 예: … ≈ 33셀 → 60에 여유"*)는 **실측과 불일치** — 실제로는 60폭에서 버튼이 등록되지 않는다. 계약 위반이 아니라 plan의 워크된 예시가 낙관적이었던 것. 60폭 사용자는 키보드 `s`/`x`/`y` 폴백이 유일 경로이며, 이는 prd.md:280의 폴백 계약이 이미 보장한다.

## 3. 기존 F-27 스위트 회귀 — 키보드 폴백 무결

```bash
python3 -m unittest tools.fleet.tests.test_f27_control
```

```
Ran 82 tests — OK
```

**무변경 스위트 82건 전량 통과** → 키보드 `s`/`x`/`↑↓`/`jk`/`Esc`/`y`/`n` 경로 회귀 0 (A2-2 ✅). registry 마감(`TestRegistryCloseParity`)·action log(`ActionLogTest`)·start-time(`VerifyTargetTest`) 포함.

### registry 마감 `done,note=fleet-kill` (prd.md:284)

`control.close_registry_row` 실물 — F-18 "registry 무write" 불변식의 명시적 단일 예외로 문서화되어 있고, upstream `close_job_row`와 동형(같은 flock, 같은 3-part 매치 키, first-match-wins, 멱등)이며 `note=fleet-kill` 토큰만 의도적으로 상이. 기존 스위트가 커버하며 통과.
