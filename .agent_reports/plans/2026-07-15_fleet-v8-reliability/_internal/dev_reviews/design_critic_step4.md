# F-27 제한적 세션 제어 UI — 디자인팀 critic (Step 4)

- **사이클**: 2026-07-15 fleet-v8-reliability · mode=design/critic (read-only, **소스 무수정**)
- **대상**: 실측 아티팩트 `/tmp/v8_step4_ui.txt` (168·60폭) + `render._prompt_segs` / `_footer_segs` / `_highlight_row` / `_addline` / `_handle_*_key` / `_poll_pending_kill` · `control.py`
- **근거 계약**: `prd.md` §4.8 F-27 (prd.md:250-255) · plan §6.2 (키 계약, plan.md:510-535) · §6.4 (안전 계약, plan.md:547-557)
- **종합 판정**: **BLOCK** — CRITICAL 1건 (경고 프롬프트의 시각 위계 **역전**, 실측 확인)

> 이 표면은 실제 프로세스에 SIGTERM/SIGKILL을 보낸다. 그래서 "예쁜가"가 아니라 **"사용자가 오독할 수 있는가"** 만 봤다. 텍스트로 읽고 판단하지 않고 **실제 curses 화면에 그린 뒤 셀 단위로 attribute를 되읽고 래스터로 눈으로 확인**했다(방법·한계 §검증 방법).

---

## 스코프 5문 직답 (결론 먼저)

| # | 질문 | 답 |
|---|---|---|
| 1 | 확인 프롬프트를 오독할 수 있나? | **168폭: 아니오** (대상·키 모두 명확). **60폭: 부분적으로 예** — 이름이 사라진다. 단 그 트레이드오프는 **거짓 양자택일**이었다 → §2 |
| 2 | `working` 경로가 `unused`보다 **눈에 더 무섭나**? | **아니오 — 측정상 더 약하다.** 경고 프롬프트 2종만 풋터 바를 잃고 검은 파편으로 렌더된다 → **§1 CRITICAL** |
| 3 | escalate가 "더 세고 못 막는 kill"임을 전달하나? | **텍스트는 정확·충분**("SIGTERM ignored for 5s" + "SIGKILL"). **하지만 4개 프롬프트 중 가장 차분하게** 렌더되고, 60폭에서 대상 state를 잃는다 → §4 |
| 4 | 모드 상태가 발견 가능한가? | **선택 모드 안은 명확** (풋터 전면 교체, 60폭에 넉넉히 맞음 — 잘 됨). **진입로는 60폭에서 안 보임** → §7 |
| 5 | A_REVERSE가 이미 색 있는 행 위에서 읽히나? | **읽힌다 — "위에 덧칠"이 아니라 행을 흑백으로 납작하게 만들기 때문.** docstring의 주장은 **사실이 아니다** → §8 |

---

## 요약

키 계약(§6.2)·안전 계약(§6.4)의 **논리**는 견고하다. `control.kill_target`은 UI를 신뢰하지 않고 자체 거부 게이트를 갖고 있고(§9 잘 된 부분 1), `_poll_pending_kill`은 자동 에스컬레이션을 하지 않으며 pid+start-time으로 identity를 재결속한다. **자동 제어 0 원칙도 지켜졌다.** prd.md:253이 요구한 것들은 대체로 코드에 실재한다.

문제는 **그 논리가 화면에 도달하지 못한다**는 것이다. 이중 확인 사다리 전체가 "사용자가 경고를 보고 놀란다"는 전제 위에 서 있는데, **경고 프롬프트 2종이 정확히 그 자리에서 시각적으로 무너진다.** 원인은 미학이 아니라 `_addline:2128` 한 줄이고, 수정도 한 줄 수준이다.

CRITICAL 1건 · MINOR 4건 · ADVISORY 5건.

---

## 1. 🔴 CRITICAL — 경고 프롬프트만 **풋터 바를 잃는다** (시각 위계 역전)

### 원인 (file:line)

`_addline:2128` 은 행이 "바"인지를 **첫 세그먼트의 role** 로 판정한다:

```python
bar = bool(segs) and segs[0][1] == "hdr_bar"      # render.py:2128
band = bar or tint is not None                     # :2129
...
elif band and endcol < band_lim:                   # :2145
    _draw([(" " * (band_lim - endcol), fill_key)], endcol, lim=band_lim)
```

그런데 `_prompt_segs` 의 **경고 프롬프트 2종만 첫 세그먼트가 `g_dead`** 다:

- `render.py:2256` — `head = (" ⚠ this session is WORKING — kill ", "g_dead") if warn else (" kill ", "hdr_bar")`
- `render.py:2245` — `(" ⚠ LIVE session — confirm again: ", "g_dead")`

→ 이 두 행은 `bar=False` → `band=False` → **채움 분기에 진입조차 못 한다.** 행은 텍스트 길이만큼만 그려지고 **나머지는 기본(검정) 배경으로 남는다.** 반면 `hdr_bar`로 시작하는 `kill unused?` 와 `send SIGKILL?` 은 전폭 시안 바로 정상 렌더된다.

### 실측 (실제 curses 화면 → `inch()` attribute 되읽기)

| 프롬프트 | 첫 role | 168폭 바 채움 | 60폭 바 채움 |
|---|---|---|---|
| `kill unused?` (양성) | `hdr_bar` | **168/168** ✅ | **60/60** ✅ |
| `⚠ WORKING kill?` (경고 1/2) | `g_dead` | **78/168** (검은 꼬리 56) ❌ | **28/60** (검은 꼬리 24) ❌ |
| `⚠ LIVE confirm again` (경고 2/2) | `g_dead` | **98/168** (검은 꼬리 36) ❌ | **16/60** ❌ |
| `send SIGKILL?` (최대 파괴) | `hdr_bar` | **167/168** ✅ | **60/60** ✅ |
| 선택 모드 풋터 | `hdr_bar` | 165/168 ✅ | 57/60 ✅ |

래스터 확인(`/tmp/v8_prompt_168.png`, `/tmp/v8_prompt_60.png` — 실제 셀의 fg/bg/attr로 그림): 경고 2종은 **빨간 글자 + 시안 섬 + 검은 꼬리** 의 3배경 누더기로, 경고가 아니라 **렌더 버그처럼** 보인다. 특히 60폭에서 `⚠ LIVE` 이중 확인은 **전 프롬프트 중 가장 적게 칠해진 16/60 파편**이다.

### 왜 CRITICAL인가

- 이 기능의 **유일한 시각적 안전 주장**이 "live 경로가 더 무섭게 보인다"인데, **측정 결과 정확히 반대**다. 양성 프롬프트와 SIGKILL 프롬프트는 단정한 전폭 바(= 시스템이 통제 중이라는 신호)로, 경고 2종은 깨진 파편으로 렌더된다.
- 4개 프롬프트의 시각적 무게 순서가 **비단조**다: `SIGKILL(차분·권위)` ≈ `unused(차분·권위)` vs `WORKING(빨강·깨짐)`. 사다리가 성립하지 않는다.
- **완화 요인은 인정한다**: 텍스트는 정확하고 빨간 `⚠ ... WORKING` 헤드 자체는 눈에 띈다. 아무도 잘못 죽지 않는다 — **기능 결함이 아니라 시각 위계 결함**이다. 그럼에도 CRITICAL로 두는 이유는, 이 결함이 훼손하는 대상이 **바로 이 스텝이 존재하는 이유(§6.4-4 경고+이중확인)** 이고, §5의 커서 드리프트가 "프롬프트를 읽는다"를 load-bearing으로 만들기 때문이다. 읽어야 할 그 프롬프트가 깨져 있다.

### 수정 (구체)

`g_dead`(본문 글리프 role)를 풋터 바에 재사용한 것이 근인이다. **풋터 전용 경고 role을 신설**한다:

```python
# _init_colors() — hdr_bar(:232-235) 옆에 추가
_COLOR["hdr_warn"] = curses.color_pair(<white-on-RED pair>) | curses.A_BOLD
# _addline:2128
_BAR_ROLES = ("hdr_bar", "hdr_warn")
bar = bool(segs) and segs[0][1] in _BAR_ROLES
fill_key = segs[0][1] if bar else None      # :2131 — 바 색을 첫 role에서 승계
```
그리고 `_prompt_segs` 의 두 경고 헤드 role을 `g_dead` → `hdr_warn` 으로 교체.

결과: `unused` = 전폭 **시안** 바 < `WORKING` = 전폭 **빨강** 바 — 구조는 일관되고 위계는 단조가 된다. 이것이 §6.4-4가 원래 요구한 그림이다.

**추가 (같은 수정 안에서)**: 이렇게 고치면 stage1과 stage2가 **둘 다 빨간 바로 똑같아진다.** 현재도 두 단계는 `⚠`·`g_dead`·구조가 전부 동일해 **시각적 에스컬레이션이 0이고 차이는 순전히 어휘**다. stage2에서 요구 키를 튀게 하라 — 예: `("Y", "hdr_key")` → `("Y", "hdr_warn_key")` 로 `A_REVERSE|A_BOLD` 를 얹어 빨간 바에서 키캡만 반전시킨다. 사용자가 읽어야 할 단 하나(=`Y`)가 광고된다.

---

## 2. 🟡 MINOR — 60폭 이름 손실은 **불필요했다** (`unused`는 3셀 차이로 탈락, 27셀을 놀린다)

지시받은 질문: *"이름이 잘리면 모호한데, 맨 pid가 정말 더 나은가?"* — **질문 자체가 거짓 양자택일이다.** 코드는 제3안을 시도하지 않는다.

`_prompt_segs` 는 `fits(full)` 실패 시 곧바로 pid-only로 **절벽 낙하**한다(`render.py:2260-2265`). 실측 폭:

| 프롬프트 | full | 60폭 산출 | **유휴 셀** |
|---|---|---|---|
| confirm/unused | **63** (60을 **3셀** 초과) | 33 | **27** |
| confirm/WORKING | 112 | 36 | 24 |
| confirm2/LIVE | 132 | 38 | 22 |
| escalate | 93 | 27 | **33** |

`unused` 확인은 **3셀 때문에** 이름 전체를 버리고 **27셀을 비운 채** 끝난다. 장식(`" yes · "`, `" cancel"`)만 줄인 중간 단계면 이름이 산다 — 실측 검증:

```
 kill agent-setting-17 [pid 1168514] unused? y/Esc     → 50셀, 60폭에 맞음 ✓
```
현재:
```
| kill pid 1168514 (unused)? y/Esc|                     → 33셀 (이름 없음)
```

`unused`는 **F-27 정리의 기본 대상**(prd.md:248)이다. 즉 **가장 자주 뜨는 프롬프트가 가장 불필요하게 이름을 잃는다.**

- **정직한 반대편**: `WORKING`(제목 36자)은 full 112라 중간 단계(83셀)도 60에 안 맞는다. **거기서는 pid-only가 옳다** — 잘린 제목보다 온전한 pid가 낫다는 코드 주석(`render.py:2222-2224`)의 판단은 그 케이스에 한해 타당하다.
- **핵심 지적**: 코드는 **하나의 절벽을 두 케이스에 똑같이** 적용한다. 3단 예산(full → 이름유지·장식제거 → pid-only)으로 나누면 `unused`는 이름을 지키고 `WORKING`은 지금처럼 pid로 떨어진다. 케이스별 최적이 자동으로 나온다.
- **수정**: `fits(full)` 실패 시 `mid`(장식 축약)를 한 번 더 `fits` 검사 후 채택, 실패 시에만 현행 fallback.

---

## 3. 🟡 MINOR — 60폭 `confirm2`가 `(capital)`을 잃는다 + **틀린 키는 무피드백 무시**

168폭:
```
| ⚠ LIVE session — confirm again: … — press Y (capital) to kill · Esc cancel|
```
60폭 (`render.py:2252-2254`):
```
| ⚠ LIVE pid 2119125 — Y kills · Esc no|              38셀 / 22셀 유휴
```

`(capital)` 이 사라진다. 그런데 `_handle_prompt_key:2326` 은 `if ch != ord("Y"): return` — **소문자 `y`는 조용히 무시되고 아무 피드백도 없다**(`_set_action` 호출 없음). 즉 60폭 사용자가 `Y`를 소문자로 읽고 `y`를 누르면 **아무 일도 안 일어나고 이유도 알 수 없다.**

Caps Lock 사용자는 대칭적 막다른 길에 빠진다: stage1은 `y`를 요구하는데 키보드는 `Y`를 내보내므로 **stage1에 영원히 진입 못 하고**, 역시 무피드백이다. (다만 이 방향은 **fail-safe** 다 — stage2 도달 경로가 stage1뿐이라 조합해도 kill로 이어지지 않는다. 안전하지만 불친절.)

- **수정**: 60폭 형을 `Y (capital) kills` 로 — 실측 **48셀, 60폭에 맞음 ✓**. 그리고 프롬프트에서 인식 못 한 키는 조용히 삼키지 말고 `_set_action("press Y (capital)")` 로 되받아친다. **안전에 반하지 않는다** — 거부를 알리는 것은 동의가 아니다.

---

## 4. 🟡 MINOR — escalate가 **대상 state를 잃고**(60폭), live/ghost 구분 없이 **가장 차분하다**

`_prompt_segs` 의 `escalate` 분기(`render.py:2234-2243`)는 **`requires_double_confirm` 을 한 번도 조회하지 않는다.** 실측 결과:

| 대상 | escalate 헤드 role | 60폭 산출 |
|---|---|---|
| `unused` ghost | `hdr_bar` (차분) | `SIGKILL pid 1168514? y/Esc` (27셀) |
| `working` LIVE | **`hdr_bar` (동일하게 차분)** | `SIGKILL pid 2119125? y/Esc` (27셀) |

**60폭에서 두 프롬프트는 pid 말고 구별 불가능하다.** 유령을 SIGKILL하는지 동료의 진행 중 작업을 SIGKILL하는지 화면이 말하지 않는다 — **33셀을 놀리면서**. 168폭에서는 `who` 안에 state가 실려 살아있다(`render.py:2229`).

- **수정**: 60폭 형에 state를 넣는다 — `SIGKILL pid 2119125 (working)? y/Esc` = 실측 **37셀, 맞음 ✓**. 그리고 live 대상이면 헤드를 §1의 `hdr_warn` 으로.
- **`y` 한 방인 것 자체는 방어 가능하다 (정직하게)**: escalate 시점엔 사용자가 **이미 이 대상을 죽이기로 동의**했고(working이면 2회), 남은 결정은 *대상*이 아니라 *방법*이다. 이미 사형선고된 프로세스에 정리 기회를 줄지의 한계적 판단이므로 최초 확인보다 의식이 가벼운 것은 합리적이다. **여기서 심각도를 만들지 않겠다** — 지적은 "state를 안 보여준다"에 한정한다.

---

## 5. 🟡 MINOR — 커서가 **세션이 아니라 인덱스에 묶여 있다** (2초마다 재조준 가능)

`_CURSOR` 는 `_live_targets()` 리스트의 **맨 정수 인덱스**다(`render.py:2158`). 그런데 그 리스트는 `_draw` 가 매 wake(10fps)마다 `_build_lines` 로 재구축하고, 내용은 **`--interval` 기본 2.0초**(`fleet.py:34`)마다 `collect_all` 로 갈린다. 커서에 **identity 결속이 없다.**

실측(hermetic 프로브, 소스 무수정):

```
user aims at                 : ghost-d
refresh inserts a row above; prompt now targets: ghost-c
same session the user aimed at? False
```

사용자가 `ghost-d` 에 커서를 놓고 → 2초 tick이 위에 행 하나를 삽입 → `x` → **프롬프트는 `ghost-c` 를 겨눈다.**

동시에 **plan.md:529 이탈**도 실측된다. 계획은 `x` = "선택 모드 진입 + **첫 selectable 행** 선택"인데, `_exit_select`(`render.py:2199-2202`)가 `_CURSOR`를 리셋하지 않고 `_enter_select`(`:2195`)는 옛 값을 clamp만 한다:

```
cursor after 2x j            : 2 -> ghost-c
cursor survives Esc          : 2
re-enter via x selects       : ghost-c   (plan.md:529 requires 'ghost-a')
```

- **왜 CRITICAL이 아닌가 (정직하게)**: 프롬프트가 대상을 **이름으로 재진술**하고, 드리프트가 `working` 행으로 향하면 프롬프트가 빨개지며 `y`→`Y` 를 요구한다. **즉 위험한 방향은 상태 의존 프롬프트가 이미 막고 있고**, 안 막히는 방향(`unused`→`unused`)은 손실이 유령 세션 하나다. 이 비대칭은 설계의 좋은 부수 효과다.
- **그러나 §1과 곱해진다**: 이 완화는 전적으로 "사용자가 프롬프트를 읽는다"에 의존하는데, 하필 그 경고 프롬프트가 §1에서 깨져 있다. 두 결함은 서로를 악화시킨다.
- **수정**: 커서를 identity로 결속한다. `_CURSOR` 옆에 `_CURSOR_KEY = (pid, proc_start)` 를 두고, 이동 시 갱신 · 재구축 시 `_CURSOR_KEY` 로 인덱스를 **재해석**(사라졌으면 clamp + `_set_action("target gone")`). `_exit_select` 는 `_CURSOR`/`_CURSOR_KEY` 를 리셋해 plan.md:529("첫 selectable 행")를 실제로 만족시킨다.

---

## 6. 🟢 ADVISORY — fallback 자신은 `fits` 검사를 받지 않는다

`_prompt_segs` 의 docstring은 스스로 원칙을 선언한다(`render.py:2218-2224`): *"the footer is clipped at the terminal edge … the tail is where the keys are."* 그런데 **compact fallback 4종 중 어느 것도 `fits()` 를 다시 통과하지 않는다** — 무조건 `return`. 폭 < 33이면 `_addline` 이 잘라내고 **꼬리(=키)가 사라진다.** 자기 원칙이 자기 fallback에는 적용되지 않았다.

- 40셀 미만 터미널은 비현실적이라 ADVISORY. 수정은 `_addline` 이 이미 자르므로 **최소한 키를 앞으로** 보내거나(`y/Esc — kill pid N?`) 3단 예산(§2)에 마지막 티어를 하나 더 두는 것.

## 7. 🟢 ADVISORY — 진입로 `s select` 가 하필 **잘려나가는 꼬리**에 놓였다

> (기지 사실인 "base 풋터 90셀 오버플로"는 재보고하지 않는다. 여기서 지적하는 것은 **신규 세그먼트의 배치 결정**이다.)

`_footer_segs`(`render.py:2402-2410`) 에서 `s select` 는 13개 중 **11번째**, 약 64번째 셀에서 시작한다. 60폭에서는 **통째로 잘려 보이지 않는다.** 즉 60폭 사용자에게 **파괴적 기능의 유일한 발견 경로가 화면에 없다**(`x` 는 base 풋터에 아예 광고되지 않는다). 60폭 compact 프롬프트를 정성껏 설계해놓고 정작 그 폭의 사용자는 기능에 도달할 단서가 없다.

- fail-safe(못 찾으면 못 죽인다)라 ADVISORY. **수정**: `s select` 를 21셀짜리 `w wide/narrow/stack` **앞으로** 옮긴다 — 비용 0, 60폭에서 살아남는다.

## 8. 🟢 ADVISORY — `A_REVERSE` 는 행의 색을 **보존하지 않는다** (docstring 사실오류)

`_highlight_row`(`render.py:2469-2475`) docstring 주장:
> *"Painted over the already-drawn line so the row keeps its own colors"*

**실측(실제 curses, ASCII 셀 되읽기 — 신뢰 가능):**

```
== BEFORE _highlight_row ==
  pair=0   fg=-1 bg=-1  bold=True   ' claude code  agent-setting-17'
  pair=2   fg=3  bg=-1  dim=True    ' unused 3h55m'
  pair=1   fg=2  bg=-1  dim=True    ' tracked'
== AFTER  _highlight_row (cursor) ==
  pair=0   fg=-1 bg=-1  rev=True  bold=False  dim=False
            ' claude code  agent-setting-17 unused 3h55m tracked  main'
```

`chgat(y, 0, w, curses.A_REVERSE)` 는 attr을 **덮어쓴다** — color pair {0,1,2} → 0 으로 **붕괴**하고 **`A_BOLD`·`A_DIM` 도 소거**된다. 커서 행은 `unused` 노랑도, `tracked` 초록도, 이름/메타를 가르는 bold/dim 위계도 **전부 잃고** 균일한 흑백 반전이 된다.

- **질문에 대한 답**: **읽힌다.** 대비는 오히려 최고다. 색 위에 덧칠해 탁해지는 문제는 **발생하지 않는다** — 색을 아예 없애기 때문이다.
- **동작 자체는 방어 가능하다 (정직하게)**: 이 대시보드는 명시적으로 htop을 모델로 삼고(`render.py:2459` "htop F-key bar"), **htop의 선택 행도 색을 납작하게 덮는 바**다. 관례에 부합하고 가장 읽히는 선택지다. 그래서 MINOR가 아니라 ADVISORY.
- **다만 의식적 결정이어야 한다**: 커서 행은 **사용자가 `x` 전에 상태를 판단해야 할 유일한 행**인데, 화면에서 상태 색을 잃은 유일한 행이 된다. (배지 **텍스트** `unused 3h55m` 는 살아남고 프롬프트가 상태를 재진술하므로 오살 위험은 아니다.)
- **수정**: 최소한 **docstring을 사실로 고친다**. 색을 지키고 싶다면 셀별로 기존 attr을 승계한다:
  ```python
  for x in range(w):
      a = stdscr.inch(y, x) & curses.A_ATTRIBUTES
      stdscr.chgat(y, x, 1, a | curses.A_REVERSE)
  ```

## 9. 🟢 ADVISORY — `kill_target` 의 백스톱이 UI보다 **약하다** (`registry_status` 누락)

(시각 범위 밖이나 §6.4 사다리를 판정하며 발견 — 기록만.)

`requires_double_confirm(state, registry_status=None)`(`control.py:189-191`)은 `registry_status == "busy"` 도 이중 확인 대상으로 친다. UI는 두 인자를 모두 넘긴다(`render.py:2255`, `:2318` — `e.get("state"), e.get("status")`). 그런데 **방어 게이트는 인자를 하나만 넘긴다**:

```python
if requires_double_confirm(state) and approval == "single":   # control.py:212 — status 누락
```

→ `status=="busy"` 인 registry 잡은 **`control` 층에서 single 승인으로도 거부되지 않는다.** UI가 이미 막으므로 현재 도달 불가하지만, `kill_target` docstring은 *"refuse anything that is not provably safe"* 를 표방한다. UI를 불신하는 것이 이 함수의 존재 이유인데 그 축 하나가 UI에만 의존한다.
- **수정**: `kill_target` 시그니처에 `registry_status` 를 받아 `requires_double_confirm(state, registry_status)` 로 호출. 계약 테스트 1건 추가.

## 10. 🟢 ADVISORY — `y`→`Y` 판정: **최소 기준으로 타당**, 다만 이해 확인은 아니다

위임받은 질문에 정면으로 답한다.

**타당한 부분 (인정)**: 코드 주석(`render.py:2325`)이 내건 위협 — *"holding `y` cannot walk through both"* — 은 **실제로 무력화된다.** `y` 오토리피트는 결코 `Y`를 내보내지 않고, `:2326`이 정확히 `ord("Y")` 만 받는다. **plan.md:556의 "첫 확인과 다른 키" 문구도 충족한다.** 근거 있는 설계다.

**한계 (정직하게)**: `y` → shift+`y` 는 **같은 손가락, 같은 물리 키, 0.3초 간격**이다. 이것은 **과속방지턱이지 이해 확인(read-back)이 아니다.** 막는 것은 *키 반복*이고, 못 막는 것은 *반사적 확인 습관*이다.

**그래서 pid 뒷 2자리가 더 나은가?** — plan.md:556이 대안으로 제시했던 그 안은 **두 문제를 동시에 닫는다**: (a) 자릿수를 입력하려면 **프롬프트를 읽어야** 하므로 진짜 이해 확인이 되고, (b) **§5의 커서 드리프트를 구조적으로 무해화한다** — 엉뚱한 행으로 재조준돼도 사용자가 입력하는 자릿수는 **화면에 표시된 대상의 것**이라, 겨냥이 어긋나면 kill이 성립하지 않는다. 미학적 선호가 아니라 **실제 결함 하나를 함께 닫는** 근거다.

- **그럼에도 ADVISORY로 둔다**: 현행이 계획의 문자를 지키고 명시된 위협을 막으므로 **결함이 아니다**. 격상 여부는 사용자 결정 사항. **§1을 먼저 고치는 것이 우선순위상 훨씬 중요하다** — 사다리가 눈에 보이지 않으면 몇 번째 계단이든 의미가 없다.

---

## 11. 🟢 잘 된 부분 (구체적으로)

1. **`control.kill_target` 이 UI를 신뢰하지 않는다.** `:212` 는 live 대상 + `single` 승인을 **거부하고 로그를 남긴다.** UI가 잘못 호출해도 live 세션은 한 키로 죽지 않는다. 프롬프트가 유일 방어선이 아니다 — 이것이 §5를 MINOR에 머물게 하는 이유 중 하나다.
2. **escalate 경로만은 identity에 결속돼 있다.** `_PENDING_KILL` 은 `entry`(pid+proc_start)를 잡고, `_poll_pending_kill:2386` 이 `verify_target` 으로 **재검증 후** 프롬프트를 띄운다. §5의 인덱스 드리프트가 **여기엔 닿지 않는다.** 가장 위험한 프롬프트가 가장 단단히 묶여 있다 — 옳은 배분이다.
3. **자동 에스컬레이션이 정말로 없다.** `_poll_pending_kill:2373-2390` 은 유예 만료 시 SIGKILL을 보내지 않고 **프롬프트를 세운다.** `_handle_prompt_key:2312` 의 `if ch == -1: return` 은 **타임아웃 tick을 동의로 세지 않는다.** prd.md:253의 "명시 재확인 후"가 문자 그대로 지켜졌다.
4. **`_live_targets` 가 프롬프트 이전에 fail-closed로 거른다.** `:2181-2185` — `is_excluded` 가 예외를 던져도 `continue`(대상 제외). **판정 불가 = 비대상.** fleet 자신은 프롬프트에 도달조차 못 한다(prd.md:253).
5. **프롬프트가 풋터를 독점한다.** `_draw:2463` 이 `_PROMPT` 존재 시 풋터를 통째로 교체하고, `_loop:2507-2510` 이 **모든 키를 삼킨다.** 결정 중에는 다른 어떤 것도 일어나지 않는다 — 안전 표면의 올바른 모달리티.
6. **선택 모드 풋터는 60폭에 실측 57/60으로 맞는다.** 바를 부분 수정하지 않고 **전면 교체**해 모드 혼동이 없다. base(90셀 오버플로)와 대조적으로 신규 풋터는 예산 안에 있다 — 스코프 4의 "어느 모드인지 명확한가"는 **모드 안에서는 명확히 통과**다.
7. **`(capital)` 이라는 단어**(168폭). *무엇* 이 아니라 *어떻게* 를 알려준다. `Y` 만 보여주고 사용자가 shift를 유추하게 두지 않았다 — §3은 이 좋은 판단이 60폭에서 탈락하는 것에 대한 지적일 뿐이다.
8. **`n`/`N` 도 취소로 받는다**(`:2306`). 광고되진 않지만 관대하고 **fail-safe 방향**이다.

---

## 판정

| 항목 | 결과 |
|---|---|
| **CRITICAL** | **1건** — §1 경고 프롬프트만 풋터 바 상실 → 시각 위계 역전 (`_addline:2128` + `_prompt_segs:2245,2256`) |
| MINOR | 4건 — §2 60폭 이름 불필요 손실 / §3 `(capital)` 손실 + 무피드백 / §4 escalate state 손실 / §5 커서 identity 미결속 + plan.md:529 이탈 |
| ADVISORY | 5건 — §6 fallback 무검사 / §7 `s select` 배치 / §8 A_REVERSE docstring 오류 / §9 백스톱 `registry_status` 누락 / §10 `y`→`Y` 격상 검토 |
| **종합** | **BLOCK** |

**BLOCK 사유**: prd.md:252-253이 요구한 "**경고** + 이중 확인"에서 **이중 확인은 착륙했고 경고는 착륙하지 못했다.** 경고 프롬프트 2종이 양성 프롬프트·SIGKILL 프롬프트보다 시각적으로 약하게 렌더되는 것은, 파괴적 표면에서 방향이 **반대**인 결함이다. 원인은 한 줄(`_addline:2128`)이고 수정도 한 줄 수준이라 **재작업 비용은 작다** — 그래서 지금 막는 것이 싸다.

**착륙 조건**: §1 수정 + §1 재렌더로 4개 프롬프트의 바 채움이 **단조**임을 실측 확인. §2·§3·§4는 같은 `_prompt_segs` 편집에서 함께 처리하는 것이 자연스럽다(제안 폭 전부 60폭 적합 실측 완료). §5는 별건으로 분리 가능.

### 검증 방법 (재현 가능)

- `/tmp/v8_step4_ui.txt` 전문 판독 + `render._dw` 로 **프롬프트 5종 × 2폭 표시폭 실측** 및 제안 대안 3종의 60폭 적합 검증.
- **실제 curses(pty, `TERM=xterm-256color`, 24×{168,60})에 `_addline` 으로 프롬프트를 그린 뒤 `inch()` 로 셀별 pair/fg/bg/bold/dim/reverse 되읽기** → 바 채움 셀 수 측정(§1 표) · 하이라이트 전후 attr 비교(§8).
- 되읽은 실제 셀을 **DejaVu Sans Mono로 1:1 래스터** → `/tmp/v8_prompt_168.png` · `/tmp/v8_prompt_60.png` 육안 확인(§1).
- `_enter_select`/`_handle_select_key` **hermetic 행위 프로브**로 커서 드리프트·`x` 재진입 실측(§5). `control.is_excluded` 는 프로브 프로세스 내에서만 스텁 — **소스 파일 무수정**.
- **한계 명시**: ① `inch()` 는 비-wide API라 **U+0100 이상 문자를 되읽지 못한다**(`⚠`·`—`·`↑↓`·`◌` 가 래스터에서 두부로 보이는 것은 **프로브 아티팩트이며 제품 결함이 아니다** — 글리프 형상에 대한 판단은 이 보고서에서 일절 하지 않았다). 배경·attr 데이터는 셀별로 독립이라 영향받지 않으며 §1·§8은 전적으로 그 축에 근거한다. ② 실제 터미널 에뮬레이터에 붙여 확인한 것은 아니다(pty + curses 되읽기가 상한). ③ `◌` 글리프는 Step 2에서 KEEP 확정 — 재론하지 않았다. ④ base 풋터 90셀 오버플로는 기지·범위 밖으로 재보고하지 않았고, §7은 **신규 세그먼트의 배치**만 다룬다.
