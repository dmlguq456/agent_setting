# test log 06 — ★ 글리프 divergence 판정 (`⚡` → `🔬`)

## 사안

PRD §4.8 F-29(prd.md:293)는 서브에이전트 글리프를 **명시**한다:

> *"세션 행 아래 `└⚡<agent-type> ⏳<경과>` 서브 행 — 분사 잡 `└▸🚀`와 글리프로 구분. … 세션 행에 `⚡N` 카운트 배지"*

execute는 `🔬`로 **대체**하고 근거를 코드 주석에 남겼다(render.py:1476-1482):

> *"`⚡` was PRD's proposed glyph but it is already load-bearing for the spec-gate `⚡untracked` badge (:613/:1925 area) — reusing it would recreate the exact dual-meaning problem prd.md:232 warns `🧠` already has. `🔬` is pre-registered in `_WIDE` (double-width) and otherwise unused…"*

## (a) 충돌 주장은 사실인가 → **아니다 (거짓)**

### 증거 1 — fleet은 `⚡`를 **한 번도 렌더하지 않는다**

```bash
for w in 60 120 168; do grep -c "⚡" /tmp/v9_test_${w}.txt; done
# → 0, 0, 0
COLUMNS=168 python3 tools/fleet/fleet.py --demo --once | grep -c "⚡"
# → 0
```

라이브·데모 전 폭에서 **0회**. 

### 증거 2 — 게이트 배지는 **글리프 없는 단어**다

`render.py:612-622` 실물:

```python
def _gate_word(gate, pipe):
    """Binary spec-gate vocabulary — EXACTLY the statusline's 📌tracked / ⚡untracked, nothing
    else … Returns (word, color_key); ('', None) when there is no artifact root at all."""
    if gate == "untracked":
        return "untracked", "gate_u"      # ← 단어만. 글리프 없음
    if gate == "tracked":
        return "tracked", "gate_t"
```

실렌더 확인: `● agent-note/ 🚧 1  tracked` — `📌`도 `⚡`도 없다. `:613`의 `⚡untracked`는 **statusline의 어휘를 설명하는 산문**이지 fleet이 그리는 글리프가 아니다. execute는 **주석 속 글자를 렌더 표면으로 오독**했다.

### 증거 3 — 인용된 `:1925`는 무관한 코드다

```bash
sed -n '1918,1935p' tools/fleet/render.py
# → dispatch 자식/스테이지 라벨 계산 (kids/active/job.stage). 게이트 배지 아님.
```

주석의 근거 인용 자체가 부정확하다.

### 증거 4 — `⚡`가 실제로 사는 곳은 **다른 표면**이다

```bash
grep -rln "⚡untracked" --include='*.sh' --include='*.py' .
# adapters/claude/statusline.sh
# utilities/workflow-guard-hook.sh
# hooks/artifact-guard.sh · hooks/worktree-path-guard.sh · hooks/portable-guards.test.sh
# tools/fleet/render.py  ← 주석에서만
```

`⚡untracked`는 **statusline/hook 표면**의 어휘다(본 세션 프롬프트 상단의 `🧭 📌tracked`가 그 예). fleet TUI 내부 어휘가 아니다.

### 증거 5 — `_WIDE` 논거는 두 글리프를 구분하지 못한다

```bash
git show HEAD:tools/fleet/render.py | grep "^_WIDE"
# _WIDE = set("🧠✨⏳📁🚀🛰📌⚡📋⚙📊🐛📈🔬💻⏱↻")
grep "^_WIDE" tools/fleet/render.py          # 동일 (무변경)
```

`🔬`가 "pre-registered in `_WIDE`"라는 주장은 **참**이다 — 그러나 **`⚡`도 똑같이 pre-registered**다. 이 논거는 `🔬`를 `⚡`보다 선호할 이유가 되지 못한다(둘 다 폭 테이블에 이미 있음).

### 증거 6 — plan이 **이미 정반대로 판정했다**

plan.md:347 (§5.3 "글리프 위계 확인"):

> *"`🧠`는 두 의미(mem-worker 수 / mem 이벤트)로 이미 포화. **`⚡`는 신규 — 기존 글리프와 충돌 없음**을 legend에서 확인하고…"*

plan 스테이지는 이 질문을 **명시적으로 검토하고 "충돌 없음"으로 결론**냈다. execute는 이 판정을 뒤집으면서 plan을 인용하거나 반박하지 않았다.

**(a) 결론: 충돌 주장은 fleet 렌더 표면 기준으로 사실이 아니다.** `⚡`는 fleet 안에서 load-bearing이 아니며, `prd.md:232`가 경고하는 `🧠`류 dual-meaning은 **동일 표면 내 중복**을 말하는데 `⚡`는 애초에 그 표면에 없다.

## (b) 대체는 옳은 판단인가 → **부분적으로만. 기각 우세**

### 대체를 지지하는 유일한 잔존 논거 (cross-surface)

사용자는 statusline/hook에서 `⚡untracked`를 **상시** 본다. fleet이 `⚡<agent-type>`을 도입하면 두 도구를 나란히 읽는 사용자가 혼동할 수 있다 — **도구 간(cross-surface) dual meaning**. 이는 실재하는 논거이나:

- `prd.md:232`의 위계 규칙은 **fleet 내부 글리프 어휘**를 다룬다 — cross-surface 충돌은 그 규칙이 말하는 바가 아니다.
- fleet은 이미 `📌`를 `_WIDE`에 두고도 게이트를 단어로만 그린다 — 즉 **statusline 어휘와 fleet 어휘는 이미 의도적으로 분리**돼 있다. 이 분리가 존재하는 이상 cross-surface 충돌 우려는 약하다.
- PRD 작성자는 `⚡untracked`의 존재를 알면서(같은 문서 §0.5·§4가 tracked/untracked를 다룸) `⚡`를 골랐다.

### `🔬`의 실질 품질

`🔬`(현미경)가 "서브에이전트"를 은유하는가? `⚡`(빠른 병렬 실행)보다 명백히 낫다고 보기 어렵다. `🚀`(dispatch)와의 시각적 구분은 둘 다 충족한다. **미학적으로 무승부에 가깝고, 계약 준수 측면에서는 `⚡`가 우세**하다.

**(b) 결론: PRD의 `⚡`가 이겨야 한다.** 대체의 근거로 제시된 명제(충돌 실재)가 **거짓**이고, plan이 반대로 판정했으며, 대체안이 품질상 뚜렷이 우월하지도 않다. 거짓 전제 위에 세워진 사양 이탈은 유지할 근거가 없다.

> 단, 이는 **사용자 결정 사항**이다. cross-surface 논거를 사용자가 받아들인다면 `🔬`(또는 제3의 글리프) 유지도 정당해진다 — 그 경우 **PRD 본문을 고쳐야지 코드가 조용히 이탈해선 안 된다**.

## (c) PRD minor-log 항목이 필요한가 → **어느 쪽이든 필요하다 (예)**

이것은 **사양 대 구현 divergence**이며, 두 경로 중 하나로 반드시 닫혀야 한다:

| 경로 | 조치 |
|---|---|
| **A (권고)** — PRD 우선 | `_ICON_SUBAGENT = "⚡"`로 되돌리고 render.py:1476-1481 주석 삭제. 코드 1줄 + 주석. `_WIDE`에 `⚡` 이미 존재하므로 폭 처리 무변경. minor-log에 *"F-29 글리프 = PRD 원안 `⚡` 확정, execute의 충돌 주장은 실측으로 반증됨"* 기록 |
| **B** — 구현 우선 | PRD prd.md:293의 `└⚡`/`⚡N`을 `└🔬`/`🔬N`으로 개정 + minor-log에 근거(cross-surface 어휘 분리) 기록. **사용자 확인 필요** — F-29는 "사용자 확정 2026-07-15" 항목이므로 글리프 변경도 같은 격의 확인을 받는 것이 일관됨 |

**어느 경로든 minor-log 항목이 필요하다.** 현재 상태(코드가 PRD와 다르고 그 근거가 코드 주석에만 존재)는 v9가 방금 해소한 "spec drift"를 되도입하는 것이며, 다음 audit이 🔴로 잡을 유형이다(v9 자체가 minor 6건 흡수 + audit 🟡 2건 해소 사이클이었다는 점에서 특히).

## 부수 divergence — `├` 접두 (🟢 정보성)

PRD는 `└⚡`만 명시하나 구현은 `├`(비말단)/`└`(말단)을 쓴다(render.py:1503). 근거는 design critic step3 §2 — *"2+ stacked sub-agents를 하나의 연결된 그룹으로 읽히게"*. **개선이며 반대하지 않는다.** minor-log 항목을 쓸 때 같이 기록하면 충분하다(별도 결정 불요).

## 종합 판정

| 질문 | 답 |
|---|---|
| (a) 충돌 주장이 사실인가 | **아니오** — `⚡`는 fleet이 렌더하지 않으며, 인용된 `:1925`는 무관 코드. plan.md:347이 이미 "충돌 없음" 판정 |
| (b) 대체가 옳은가 | **아니오 (기각 우세)** — 거짓 전제 + plan 판정 역행 + 품질 우위 없음. `⚡` 복귀 권고 |
| (c) minor-log 필요한가 | **예 — 어느 경로든 필수** |

**심각도: 🟡 중간** — 안전·기능 무영향, 순수 사양 정합성 문제. 그러나 근거가 **실측으로 반증되는 주장**이라는 점에서 단순 취향 차이보다 무겁다. 수정 비용은 1줄.
