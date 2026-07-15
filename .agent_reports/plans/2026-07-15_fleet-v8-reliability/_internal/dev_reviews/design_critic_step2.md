# F-26 `unused` 세션 행 — 디자인팀 critic (Step 2)

- **사이클**: 2026-07-15 fleet-v8-reliability · mode=design/critic (read-only, 소스 무수정)
- **대상**: 실측 캡처 `/tmp/v8_step2_60.txt` · `/tmp/v8_step2_120.txt` · `/tmp/v8_step2_168.txt` (3폭 전부 판독)
- **관심 행**: 실제 유령 세션 `agent-setting-17` (pid 1168514) — registry `updatedAt - startedAt` = 119ms
- **근거 계약**: `prd.md` §4.8 F-26 (prd.md:245-249) · plan §4 (plan.md:343-358)
- **글리프 판정**: **KEEP `◌`** (U+25CC DOTTED CIRCLE) — 4개 제약 전부 자체 검증 통과
- **종합 판정**: **PASS-with-minor** · CRITICAL 0건

---

## 요약

F-26의 핵심 주장 — "unused를 idle과 구분되는 1급 신호로"(prd.md:248) — 은 **3폭 전부에서 실제로 성립한다.** 문제의 행은 이제 `◌ … unused 3h55m`로 자기를 설명하며, 그 옆 6개 idle 행과 혼동될 여지가 없다.

`◌`는 유지한다. 텍스트로 읽고 판단하지 않고 **실제 monospace 폰트에 1:1 래스터라이즈 후 확대해 눈으로 확인**했다(방법·증거 아래 §1). 대안 `⊘`는 **렌더 증거로 기각**한다 — Liberation Mono에서 두부(tofu)처럼 보이고, DejaVu에서는 테이블 전체에서 가장 무거운 글리프가 되어 shape-size gradient를 거꾸로 뒤집는다.

MINOR 1건(배지 age 중복), ADVISORY 3건. 모두 1급 신호 자체를 훼손하지 않는다.

---

## 1. 글리프 판정 — **KEEP `◌`** (위임받은 결정)

계획이 critic에 위임한 유일한 결정(plan.md:358). 4개 제약을 각각 직접 검증했다.

### 제약 1 — 충돌 없음 ✅

`render.py:302-304` 실측 + 코드포인트 대조:

| state | glyph | codepoint |
|---|---|---|
| working/idle | `●` | U+25CF |
| blocked | `◑` | U+25D1 |
| done | `✓` | U+2713 |
| stale/unknown | `·` | U+00B7 |
| dead | `✕` | U+2715 |
| queued | `◦` | U+25E6 |
| `_DETACHED_GLYPH` | `○` | U+25CB |
| **unused (제안)** | **`◌`** | **U+25CC** |

**`◌`는 어느 것과도 충돌하지 않는다.** 계획의 주장은 참.

> 부수 관찰(F-26 범위 밖, 보고만): `○`는 `_DETACHED_GLYPH`(render.py:304)와 `_COOL_RING`(render.py:316)이 **이미 공유**한다. 단 전자는 세션 글리프 열, 후자는 디렉토리 헤더로 zone이 달라 실사용 충돌은 아니다. F-26이 만든 문제가 아니며 조치 불요.

### 제약 2 — "Readable without color" ⚠️→✅ (조건부, 아래 근거)

**이게 핵심이므로 회의적으로, 실물로 검증했다.** PIL로 실제 mono 폰트에 12/14/16/20px 렌더 → 1:1 픽셀을 nearest-neighbour 확대해 육안 판독 (`/tmp/glyph_mono.png`, `/tmp/glyph_zoom.png`).

**관찰 결과:**

- **DejaVu Sans Mono (12–20px)** — `◌`는 **끊어진 옅은 고리**, `○`는 **연속된 진한 고리**. 12px에서도 잉크 무게 차이가 뚜렷해 확실히 구분된다. 16px 이상에서는 점선 자체가 또렷이 읽힌다. **명확 통과.**
- **Liberation Mono 12px — 가장 약한 경우.** 점들이 거의 병합되어 `◌`가 "점선 고리"가 아니라 **"○보다 옅고 약간 큰 고리"** 로 읽힌다. 즉 이 조합에서 구분 근거는 *shape*가 아니라 **ink weight** 하나로 축소된다. 14px부터는 점선기가 회복된다.
- **Ubuntu Mono** — `●` `○` `◌` `⊘` `◦` **전부 두부**. 단 이는 `◌` 고유 리스크가 **아니다**: Ubuntu Mono cmap은 이미 쓰이고 있는 `●`/`○`도 똑같이 결여한다. 즉 폰트 폴백 없는 환경이면 **기존 글리프 테이블 전체가 이미 두부**다. 차등 리스크 0.

**판정 근거 — 왜 그럼에도 통과인가:** Liberation 12px의 약한 구분은 **글리프가 의미의 단독 운반체가 아니기 때문에** 계약을 깨지 않는다. 같은 행이 `unused 3h55m` 텍스트 배지를 **항상** 함께 싣고(render.py:738-742, 배지는 suffix 예산에서 마지막에 떨어지는 최우선 항목), pulse·legend도 글리프 뒤에 `unused` 단어를 즉시 붙인다(render.py:1446, 1825). 색이 없어도 **행 수준에서** unused는 언제나 판독 가능하다. 색 없이 글리프 단독으로 `○`/`◌`를 분간해야 하는 자리는 코드 어디에도 없다.

### 제약 3 — 의미 정합 ✅

확대 렌더에서 잉크 무게 gradient가 **실제로 관찰된다**: `●`(꽉 참) → `○`(연속 고리) → `◌`(끊어진 고리). `◌`는 테이블에서 **가장 가벼운 자국**이고, 이는 "less active = 더 작고 옅게"라는 render.py:294-296이 선언한 축과 정확히 일치한다. "한 번도 채워진 적 없음"은 억지 해석이 아니라 **보이는 대로**다. 정합.

### 제약 4 — 1 display cell ✅ + 반전된 발견

`unicodedata.east_asian_width('◌')` = **`N`(Neutral)** → 항상 1셀. 확인.

**주목**: `●`/`○`/`◑`/`·`는 전부 **`A`(Ambiguous)** 다. 즉 CJK 로케일에서 ambiguous-width=wide로 잡는 터미널이면 **기존 글리프들이 2셀이 되고 `◌`는 1셀로 남아** 열이 어긋난다. 다만 이는 `◌`가 만든 문제가 아니다 — `✓`(done)/`✕`(dead)/`◦`(queued)가 **이미 `N`** 이라 같은 성질을 갖는다. 현재 환경 `LANG=en_US.UTF-8` / `TERM=xterm-256color`에서는 비발현. **기존 조건이며 F-26 델타 0.** 조치 불요, 인지만.

### 대안 `⊘` — **기각** (렌더 증거)

- **Liberation Mono 12/14px에서 `⊘`는 두꺼운 검은 사각형**으로 렌더된다 — 사실상 두부와 구분 불가. 흔한 기본 mono 폰트에서 두부처럼 보이는 글리프는 상태 표시에 실격.
- **DejaVu에서 `⊘`는 테이블 전체에서 가장 무겁고 어두운 글리프**다. `unused`는 물러나야 할 상태인데 `working`보다 시선을 더 끈다 — shape-size gradient를 **정면으로 역행**한다.

`◌`가 `⊘`보다 모든 축에서 낫다. **최종: `_LIVE_GLYPH["unused"] = "◌"` 유지. 변경 불요.**

---

## 2. 🟡 MINOR — 배지의 age가 time 열과 **완전 중복** (데이터 슬롭)

**같은 값이 같은 행에 두 번 찍힌다.** 추정이 아니라 동일 표현식이다:

- 배지: `render.py:702` → `" unused %s" % fmt_min(s.elapsed_min)`
- time 열(wide): `render.py:792` → `("%6s" % fmt_min(s.elapsed_min), "dim")`
- time 열(stack l2): `render.py:1094` → `(_pad(fmt_min(s.elapsed_min), _HW), "dim")`

**3폭 전부에서 실측 확인:**

```
60  L32: ▍ ◌ claude code     agent-… unused 3h55m tracked  main
    L33: ▍   3h55m           Fable 5 (xhigh)
```
```
168 L18: ▍ ◌ claude code     agent-setting-17 unused 3h55m tracked terminal  main  …  —    3h55m
```

60폭에선 두 `3h55m`이 **바로 윗줄/아랫줄**로 인접해 중복이 가장 눈에 띄고, **동시에 공간이 가장 비싼 자리**다. 배지가 13셀을 가져가 이름이 `agent-…`(7셀)로 굶는다 — 어느 세션인지 식별 불가한 수준.

- **왜 문제인가**: `_design_rules.md` §슬롭 회피 — "불필요한 숫자·통계 금지(데이터 슬롭)". 같은 숫자를 두 번 보여주면서 그 대가로 식별자를 죽이고 있다.
- **수정 방향**: 60폭(stack)에서 배지를 `unused`로 축약(age 생략) → 6셀 회수 → 이름이 `agent-setti…`까지 확보. age는 바로 아랫줄 time 열이 이미 말하고 있다. 120/168은 슬랙이 충분(w=72/168)하니 현행 `unused 3h55m` 유지해도 무방.
- **반대 논거도 기록**(maker 판단용): 168폭에선 time 열이 ~160칸 우측에 있어 이름 zone을 훑는 시선과 멀다. 그 폭에선 배지 내 age가 행을 자족적으로 만드는 실익이 있다. **즉 이 지적은 60폭에 한정해 받는 것이 옳다.**
- F-27 kill 타겟팅 관점에선 `agent-…`도 치명적이진 않다(행 커서 `↑↓`+`x`로 선택, prd.md:252). 그래서 CRITICAL이 아니라 MINOR.

---

## 3. 🟢 ADVISORY — `terminal` provenance 값이 프로젝트 **자체 어휘와 충돌**

`procscan.py:90-91` 어휘 = `herdr | terminal | vscode | worker`. 그런데 이 프로젝트에서 **"터미널"은 이미 다른 뜻으로 쓰인다** — plan.md:163: *"**터미널 행**(`done`/`killed`/`cancelled`)은 live 행을 신설하지 않는다"*. 즉 terminal = **종료 상태**.

실측 행:
```
▍ ◌ claude code     agent-setting-17 unused 3h55m tracked terminal  main
```

`unused`(상태) 옆에 `terminal`(출처)이 붙어 **"이 세션은 terminated 되었다"** 로 오독될 여지가 있다. 상태 어휘와 출처 어휘가 같은 dim 태그 열에서 섞인다.

- **다만 조치 신중**: `terminal`은 **prd.md:249가 명시한 스펙 어휘**다. maker가 단독 변경할 사안이 아니라 **스펙 개정이 선행**해야 한다. 그래서 MINOR가 아니라 ADVISORY.
- **제안(스펙 개정 시)**: `terminal` → `tty` 또는 `shell`. 오독이 사라지고 **3–5셀로 짧아져** §2의 이름 굶주림도 함께 완화된다.

---

## 4. 🟢 ADVISORY — 캡처가 `◌`/`○` **인접 상황을 한 번도 실증하지 못했다**

`◌`의 유일한 실질 리스크는 `○`와 나란히 놓일 때인데, **3폭 캡처 전부 그 상황을 만들지 못했다** — detached 세션이 0이라 pulse·legend의 조건부 분기가 죽어 있다:

- pulse: `render.py:1446` `◌ N unused` + `render.py:1448` `○ N detached` → **같은 줄에 인접 가능**
- legend: `render.py:1825` + `render.py:1827` → `● idle   ◌ unused   ○ detached` **동시 노출 가능**

실측 pulse는 `fleet ⠹ 1 working   ● 6 idle   ◌ 1 unused   ↳ 3 jobs`로 detached가 없다. 즉 **가장 위험한 시각적 순간이 미검증 상태**로 남았다.

- **완화 요인**: 두 자리 모두 글리프 직후에 `unused` / `detached` 단어가 즉시 붙어 텍스트가 항상 동반한다(§1 제약2 논거와 동일). 그래서 실패 가능성은 낮다고 본다 — 그러나 **본 적 없다고 말하는 게 정확하다.**
- **수정 방향**: verifier/QA에 detached+unused 동시 존재 픽스처 1개 추가해 pulse 줄과 legend 줄을 캡처. 코드 변경 불요, **커버리지 요청**.

---

## 5. 🟢 ADVISORY — `g_unused`와 `gate_u`가 **동일 색** (dim yellow)

`render.py:99` `"g_unused": ("y", _A_D)` / `render.py:101` `"gate_u": ("y", _A_D)` — 완전히 같다.

현재 캡처의 행은 `tracked`(=`gate_t`, dim **green**)라 분리돼 보이지만, **untracked인 unused 세션**이면 `unused 3h55m untracked`가 **끊김 없는 하나의 dim-yellow 덩어리**로 렌더된다. 상태 배지와 gate 태그의 경계가 색으로 사라진다.

- 발생 조건이 좁고(untracked ∧ unused) 텍스트로는 여전히 읽히므로 ADVISORY.
- **수정 방향**: 확정 전 해당 조합을 한 번 렌더해 보고, 뭉쳐 보이면 `g_unused`를 `("y", 0)`(비-dim)로 올려 배지를 gate보다 한 단계 세우는 것을 검토. 단 `g_idle`이 이미 `("y", 0)`이라 그쪽과의 분리도 함께 봐야 한다.

---

## 6. 🟢 잘 된 부분 (구체적으로)

1. **행 폭이 그리드에 정확히 들어맞는다.** 168폭 main 세션 행 8개 전부 실측 `w=168` — unused 행(L18)도 **정확히 168**로 동일. 이례가 아니라 **규범 준수**다. 60폭 `w=54`(≤60), 120폭 `w=72`(≤120). **unused 행 자체는 3폭 어디서도 경계를 넘지 않는다.** (60의 장문 행들과 168의 dispatch 3행 overflow는 기존 baseline이며 F-26 델타 0 — 재보고하지 않음. 168 dispatch overflow는 F-22 40셀 캡이 처리.)

2. **suffix 우선순위가 의미론적으로 옳다.** `render.py:736-737`의 주석 그대로 배지 > gate > provenance. 60폭에서 실제로 provenance가 먼저 죽고 배지가 살아남았다 — **행이 노출된 이유(=unused)가 마지막까지 남는다**는 원칙이 코드와 렌더 양쪽에서 지켜졌다.

3. **provenance 게이팅이 자기제한적으로 우아하다.** `collectors/claude.py:287` — `if sess.provenance is None and not sess.title`. **제목 없는 행에만** 붙으므로, provenance가 나타나는 자리는 정의상 이름 zone에 여유가 있는 자리다. "provenance가 이름 zone을 먹는가?"에 대한 답: **구조적으로 먹을 수 없다.** 60폭 드롭도 별도 특례가 아니라 예산 규칙(`render.py:756`)의 자연스러운 귀결 — 특수 케이스가 없다는 점이 좋다. 그리고 판별 실패 시 무표시(`claude.py:290-292`)로 prd.md:249 "오귀속보다 결손"을 정확히 지킨다.

4. **F-12 "healthy board stays quiet" 계약이 pulse·legend 양쪽에서 지켜진다.** pulse는 `if n_un:`(render.py:1445), legend는 `if "unused" in _seen_glyphs:`(render.py:1824)로 **실제 행이 있을 때만** 노출. `_seen_glyphs`가 렌더 중 실측 수집(render.py:1745-1746)이라 legend가 거짓말하지 않는다. **네, 이 설계가 옳다** — 범례는 화면에 실재하는 기호만 설명해야 하고, 건강한 보드는 unused 어휘를 아예 모른다.

5. **census의 색·순서가 시선을 옳은 곳으로 보낸다.** `⠹ 1 working`(bright green) → `● 6 idle`(dim green) → `◌ 1 unused`(**dim yellow**). 활동성 내림차순 배치인데 **유일한 yellow가 unused**라 6개 idle을 제치고 1개 이상치가 눈에 먼저 들어온다. 관제 도구로서 정확한 위계.

6. **`unused <age>`가 `stale`/`dead` 어휘와 안 겹친다.** stale/dead는 `last seen <age>`(render.py:1007, F-13)를 쓴다. `unused 3h55m`("한 번도 안 씀") vs `last seen 2h`("전엔 썼는데 끊김") — **문구가 두 상태의 의미 차이를 그대로 담는다.** idle은 배지 자체가 없어 3자 구분이 텍스트만으로 성립한다.

---

## 판정

| 항목 | 결과 |
|---|---|
| **글리프** | **KEEP `◌`** — 4제약 전부 통과, `⊘`는 렌더 증거로 기각. `render.py:302` 변경 불요 |
| CRITICAL | **0건** |
| MINOR | 1건 (§2 배지 age 중복 — 60폭 한정 축약 권고) |
| ADVISORY | 3건 (§3 `terminal` 어휘 / §4 `◌`+`○` 커버리지 / §5 dim-yellow 중복) |
| **종합** | **PASS-with-minor** |

prd.md:248 "idle과 구분되는 1급 신호"는 **달성됐다.** F-26 착륙 승인.

### 검증 방법 (재현 가능)

- 3폭 캡처 전문 판독 + `east_asian_width` 기반 표시폭 실측(행별 overflow 스캔)
- `◌`/`○`/`●`/`⊘` × {DejaVu Sans Mono, Ubuntu Mono, Liberation Mono} × {12,14,16,20}px **실제 래스터 렌더 후 육안 판독** → `/tmp/glyph_mono.png`
- 1:1 픽셀 nearest-neighbour 14× 확대로 monochrome 판별력 검증 → `/tmp/glyph_zoom.png`
- 글리프 충돌은 코드포인트 대조로 기계 확인, 색 충돌은 `_HUE_OF` 테이블 대조로 확인
- **한계 명시**: 실제 터미널 에뮬레이터에 붙여 폰트 폴백 동작을 본 것은 아니다(정적 캡처 + 폰트 직접 렌더가 상한). Ubuntu Mono 두부는 PIL 무폴백 아티팩트이며 실터미널에선 폴백된다 — 그래서 차등 리스크 판단에만 사용했다.
