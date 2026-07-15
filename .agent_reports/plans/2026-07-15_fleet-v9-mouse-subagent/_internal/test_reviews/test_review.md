# code-test 독립 검증 verdict — fleet v9 (마우스 1급 · 서브에이전트 관측 · 잔여 후속)

- **스테이지**: `code-test` (depth 2, 독립 검증자) · 2026-07-15
- **입장**: execute의 주장은 **검증 대상 입력**이지 증거가 아니다. 모든 수치는 본 스테이지가 직접 실행해 재측정했다.
- **소스 무수정**: `tools/fleet/**`·`adapters/claude/tools/fleet/**`·plan·dev_logs 전부 read-only 유지. 발견된 결함은 **보고만** 하고 고치지 않았다.
- **⛔ 안전**: 실 `claude`/`codex`/`opencode` 세션 **스폰 0 · 시그널 0**. 검증 전후 harness 프로세스 8개 전부 생존. 프로브는 `sleep` 프로세스 + `mock.patch("os.kill")`만 사용(plan §0 허용 수단 표 준수).

---

## 0. 종합 verdict

## **PASS (조건부)** — 계약 이행 확인, 병합 가능. 단 🟡 사양 divergence 1건은 병합 전/직후 닫아야 한다.

전 acceptance 기준이 PRD 절로 추적되어 충족됐다. execute의 주장(468 OK / 52 신규 / 변경 파일 8종)은 **전부 독립 재현으로 확인**됐으며 과장·누락이 없었다. 핵심 안전 계약 6종은 execute의 테스트를 신뢰하지 않고 **자체 작성 프로브로 재검증**해 전부 통과했다.

블로킹 결함 **0건**. 잔여는 사양 정합성 1건(🟡) + 정보성 3건(🟢).

---

## 1. 검증 수치 (독립 재측정)

| 항목 | execute 주장 | 실측 | 일치 |
|---|---|---|---|
| 전체 테스트 | 468 OK | **468 OK** (16.956s) | ✅ |
| 베이스라인 | 416 | 416 (HEAD 실행 확인) | ✅ |
| 신규 테스트 | 52 | **52** (21+15+6+10) | ✅ |
| 변경 파일 | render/model/collectors×2 + 미러 | 8 파일, +954/−88 | ✅ |
| 미러 parity | 동기됨 | **바이트 일치, 드리프트 0** | ✅ |

**과장 없음** — 검증한 모든 주장이 사실이었다.

---

## 2. acceptance 기준별 판정 (PRD 절 추적)

| ID | 기준 | PRD 근거 | 판정 | 증거 |
|---|---|---|---|---|
| **A1-1** | 추출 후 회귀 0 | plan §3 | **PASS** | 468 OK, 신규 실패 0 |
| **A1-2** | `_handle_base_key` curses-free | plan §3 | **PASS** | `test_scroll_regression` 10건 hermetic 통과 |
| **A2-1** | 행 클릭 6동작(선택/재클릭/확정/취소/이동/해제) | prd.md:279 | **PASS** | `test_f27_mouse` 21건 + 자체 프로브 C |
| **A2-2** | 키보드 폴백 회귀 0 | prd.md:280 | **PASS** | `test_f27_control` 82건 무변경 OK |
| **A2-3** | 새 mousemask 0, 토글 회귀 0, HERDR 스킵 불변 | prd.md:279 | **PASS** | 마스크 diff 0, rung 2 토글 유지 |
| **A2-4** | working 이중 확인 + 히트박스 비겹침 | prd.md:281 | **PASS** | 자체 프로브 F — 6폭 × 3단계 전조합 비겹침, 동일좌표 연타 kill 도달 불가 |
| **A2-5** | 안전 계약 5종 재검증 | prd.md:282-284 | **PASS** | 자체 프로브 A~E (§3 상세) |
| **A2-6** | 스크롤 회귀 0 (base 모드 한정) | plan §7.1 | **PASS** | `test_arrow_keys_still_scroll_in_base_mode` OK |
| **A3-1** | 서브에이전트 실패가 세션 목록에 영향 0 | prd.md:291 | **PASS** | 자체 프로브 — 예외 주입해도 행 생존 |
| **A3-2** | 소스 순서 OpenCode→Claude→Codex, Codex 미확정=결손 | prd.md:292 | **PASS** | codex 코드 추가 0 (정직한 결손) |
| **A3-3** | `└⚡` 서브 행 + `⚡N` 배지 + pulse 혼입 0 | prd.md:293 | **PASS (글리프 이탈)** | pulse 불변 실증. **글리프는 `🔬` — §4 divergence** |
| **A3-4** | zero-injection · `--json` additive · 부재 시 생략 | prd.md:294 | **PASS** | read-only I/O 전수 확인, `subagents`만 신규, 제거 0 |
| **A4-1** | `_STAGE_ZONE_MAX` 단일 상수 | v8 D3 | **PASS** | `test_cap_lives_in_exactly_one_constant` |
| **A4-2** | 168 무오버플로 **구조적** | v8 D3 | **PASS** | `_dw()` 정본 0건 + fixture 테스트 |
| **A4-3** | 성분 드롭, 활성 스테이지 보존 | F-9(c)/SD-F2 | **PASS** | 전용 테스트 2건 |
| **A4-4** | 짧은 행 회귀 0 | v8 D3 | **PASS** | `test_short_rows_are_unaffected` |
| **A4-5** | 60폭 잔존 정직 명시 | v8 정직성 조건 | **PASS (문구 정정 조건)** | §4 🟢-2 참조 |
| **A5-1/2** | base 6키 고정 + 격리 4건 | plan §7 | **PASS** | 10건 OK |
| **C2b** | §4.4.1 재그리기 + §4.2.1 클릭 맵 기준 | plan-check 🔴 2건 | **PASS** | **코드 실물 확인 — §3.1** |
| **C8** | 미러 parity | plan §2.1 | **PASS** | `diff -r` 무출력 |
| **C9** | 실세션 스폰·시그널 0 | plan §0 | **PASS** | 본 스테이지도 준수 |

---

## 3. plan-check 규범 2건 — 코드 실물 준수 확인 ★

태스크가 특별히 요구한 항목. **산문 약속이 아니라 코드가 그렇게 쓰였는지** 확인했다.

### 3.1 §4.4.1 — `_handle_mouse`가 `_PROMPT` 블록 **내부**에 (render.py:2884-2895)

```python
if _PROMPT is not None:
    # §4.4.1 — _handle_mouse MUST be called from inside this block (not before it with
    # its own `continue`): the _draw two lines below is what repopulates _PROMPT_HITS ...
    if ch == curses.KEY_MOUSE:
        mx, my = _getmouse_xy()
        if mx is not None:
            _handle_mouse(mx, my)
    else:
        _handle_prompt_key(ch)
    _draw(...)      # ← 불변식 충족
    continue
```

**준수 ✅** — 블록 내부, `_draw`가 `continue` 앞에 위치. 배치 이유가 주석으로 코드에 결박돼 후속 리팩터가 무심코 깨기 어렵다. `_getmouse_xy()`가 실패 시 `(None, None)`을 반환하고 호출부가 `if mx is not None`으로 가드 → 🟡5(NameError 크래시) 해소 확인.

### 3.2 §4.2.1 — `_CLICK_ROWS`가 `_SELECTABLE` 기준 (render.py:2821)

```
2821  _CLICK_ROWS[row] = entry                            ← _SELECTABLE 순회
2794  targets = _live_targets() if _SELECT_MODE else []   ← 기존 게이트 무변경
2340  return control.is_excluded(pid)                     ← 클릭 시점 1회
2342  return True                                         ← 해석 불가 = fail closed
```

**준수 ✅** — base 모드에서 `_draw`가 `is_excluded`를 호출하지 않아 틱당 비용 0(10fps `/proc`+JSON 폭풍 회피). 제외 판정은 rung 3 클릭 시점으로 지연됐고 **fail-closed**임을 자체 프로브로 확인.

> 두 규범 모두 **의도까지 이해하고 구현**됐다 — plan-check가 "어기면 조용히 안전이 깨진다"고 인계한 항목인데, 코드가 그 이유를 스스로 설명한다. 이 사이클의 품질 하이라이트.

---

## 4. 발견 사항 (심각도 순)

### 🟡-1 [사양 divergence] F-29 글리프 `⚡` → `🔬` 무단 대체 — **거짓 전제**

- **위치**: `tools/fleet/render.py:1476-1482` (+미러)
- **PRD**: prd.md:293이 `└⚡<agent-type>` / `⚡N` 배지를 **명시**
- **구현**: `_ICON_SUBAGENT = "🔬"`
- **execute 근거**: *"`⚡` is already load-bearing for the spec-gate `⚡untracked` badge (:613/:1925)"*

**판정: 근거가 실측으로 반증된다.**

1. fleet은 `⚡`를 **렌더하지 않는다** — 60/120/168 + `--demo` 전부 **0회**.
2. `_gate_word`(render.py:618-621)는 **단어만** 반환(`"untracked"`), 글리프 없음. `:613`의 `⚡untracked`는 *statusline 어휘를 설명하는 산문*.
3. 인용된 `:1925`는 **무관한 dispatch 라벨 코드**.
4. `⚡untracked`의 실거주지는 `statusline.sh`/`hooks/*` — **다른 표면**.
5. `🔬`가 `_WIDE`에 pre-registered라는 건 참이나, **`⚡`도 동일하게 pre-registered**(HEAD `_WIDE` 무변경 확인) → 구분 논거 아님.
6. **plan.md:347이 이미 "`⚡`는 신규 — 기존 글리프와 충돌 없음"으로 판정**했고 execute는 이를 인용·반박 없이 뒤집었다.

**권고**: `_ICON_SUBAGENT = "⚡"` 복귀(1줄) + 주석 삭제. **또는** 사용자 확인 후 PRD prd.md:293 개정. **어느 쪽이든 PRD minor-log 항목 필수** — 현 상태는 v9가 방금 해소한 spec drift를 되도입하며 다음 audit의 🔴 후보다.

**심각도 근거**: 안전·기능 무영향(🟡)이나, 단순 취향이 아니라 **실측으로 반증되는 주장 위에 세워진 이탈**이라 단순 divergence보다 무겁다. 수정 비용 1줄.

> 상세 판정: `test_logs/06_glyph_divergence_adjudication.md`

### 🟡-2 [정직성] OpenCode 서브에이전트 영구 `active=True`

- **위치**: `collectors/opencode.py::_child_sessions`
- OpenCode 스키마에 완료 신호가 없어 모든 자식 행이 `active=True`로 보고된다. 독스트링이 *"absence of evidence to the contrary"*로 정직하게 문서화했고 `done`을 날조하지 않는 방향은 옳다.
- **그러나**: prd.md:293의 *"완료분은 기본 숨김, 활성만 표시"* 가 OpenCode 소스에 대해 **달성 불가**하며, 배지 카운트가 단조 증가할 수 있다. `time_updated`를 이미 SELECT하면서 활성 판정에 쓰지 않는다 — staleness 유도 여지가 남는다.
- **심각도 🟡 낮음** — Claude 경로는 짝짓기로 정확. 후속 사이클 개선 권고, 본 사이클 블로킹 아님.

### 🟢-1 [사전 존재] 미러 트리 직접 실행 시 3건 실패

- `adapters/claude/tools/fleet/tests` 직접 실행 → `test_token_budget.AccountingTest` 3건 `FileNotFoundError`.
- **회귀 아님, 3중 확증**: (a) HEAD(416)에서 **동일 3건 동일 원인** 실패 (b) `test_token_budget.py`는 본 사이클 무수정 (c) 원인은 테스트의 repo-루트 walk-up이 미러 사본 위치에서 오착지 — 미러를 직접 실행할 때만 발생.
- parity 계약이 요구하는 **바이트 일치는 통과**했고 정본 스위트는 468 OK. **별도 이슈 분리 권고.**

### 🟢-2 [문구] 60폭 "5건 중 2건 개선" 주장은 근거 없음

- `--once`는 **라이브 데이터**를 렌더한다. 현 세션 집합은 v8 계측 시점과 다르다(본 사이클의 depth-2 워커 행이 새로 존재).
- 실측 60폭 오버플로 = 7건(`_dw()` 정본): **4건 = D4**(usage/mem/alert/legend — plan §9 스코프 밖 명시), **3건 = dispatch 행**.
- "5건 → 7건"은 **회귀 증거가 아니고**, "2건 개선"도 **이 실행으로 증명 불가**. 입력 고정 없이는 비교 불가.
- **결과 보고 문구 권고**: *"168 무오버플로 = 구조적 보장(fixture 단위 테스트 실증)"* + *"60폭 잔존 = D4 4건 + dispatch 3건, 스코프 밖"*. **수치 대비 주장은 삭제.** A4-2의 168 한정 주장은 정당하게 성립한다.

### 🟢-3 [정보] 60폭에서 마우스 kill 경로 부재 · plan 예시 불일치

- `w=60`의 `confirm`/`confirm2`는 히트박스 `{}` — 폭 사다리가 클릭 타깃을 떨어뜨리고 키보드 안내를 보존한다. plan §4.5 우선순위 규칙을 정확히 따른 **안전한 방향**(마우스 kill 불가 = 더 보수적).
- 다만 plan §4.5:234의 산출 예시(*"≈33셀 → 60에 여유"*)는 실측과 불일치. 계약 위반 아님(prd.md:280 키보드 폴백이 커버). **기록만.**

### 🟢-4 [개선] `├`/`└` 접두 — PRD는 `└`만 명시

- render.py:1503이 비말단에 `├`를 쓴다(design critic step3 §2 근거: 다중 서브에이전트를 연결된 그룹으로). **개선이며 반대 없음.** 🟡-1의 minor-log에 같이 기록하면 충분.

---

## 5. 결론

**병합 권고 — 단 🟡-1을 닫을 것.**

구현 품질은 높다. 특히 plan-check가 "어기면 조용히 안전이 깨진다"고 경고한 규범 2건(§4.4.1 재그리기 불변식 · §4.2.1 클릭 맵 기준)이 **의도까지 이해된 채로** 구현됐고, 코드가 그 이유를 스스로 설명한다. 마우스 고유의 신규 위험(더블클릭이 이중 확인을 무력화)은 좌표 반전으로 **구조적으로** 차단됐으며 내 독립 프로브가 6폭 × 3단계 전조합에서 이를 확인했다. `kill_target`이 `_handle_prompt_key` 단일 경로로만 도달 가능하고 마우스는 키스트로크를 재생할 뿐이라는 설계는 "kill 결정 경로는 하나" 계약을 정확히 지킨다.

안전 규칙(⛔ 실세션 0)은 execute·code-test 양쪽에서 준수됐다 — v8 위반의 재발 없음.

**조치 필요**:
1. **🟡-1 글리프** — `⚡` 복귀(권고) 또는 사용자 확인 후 PRD 개정. **어느 쪽이든 minor-log 항목 필수.**
2. **🟢-2 보고 문구** — code-report는 "60폭 5건 중 2건 개선"류 수치 대비를 쓰지 말 것(근거 없음). 168 구조적 보장은 정당.
3. 🟡-2 / 🟢-1은 후속 사이클·별도 이슈로 분리.
