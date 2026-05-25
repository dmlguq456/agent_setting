---
name: design-review
description: Visual review (디자인팀 critic mode) — 6-axis critique covering hierarchy, alignment, accessibility, responsiveness, UX flow, tone consistency. Read-only — no auto-fix.
argument-hint: "<design path or app path>"
---

## Language Rule
- Korean output.

## Design Resolution

`design_state.yaml` 발견.

## Pre-Check

- `phases.components: done` 검증
- 검토 대상 식별:
  - 코드: `03_components/*.tsx`
  - 스크린샷 (있으면)
  - 또는 사용자 제공 mockup

## Procedure

### Step 1: 검토 대상 확보

scope 별:

| scope | 대상 |
|---|---|
| ui | `03_components/*.tsx` + `preview_screenshot` (dev server 켜져있을 시) |
| slide | `03_components/slides/*.md` (가이드 평가) |
| icon | `03_components/icons/*.svg` |
| diagram | `03_components/diagrams/*` |

preview_screenshot 활용 가능하면 시각 직접 점검.

### Step 2: 디자인팀 critic 호출

```
Agent(디자인팀, mode=critic):
  "Visual review for <design_name>.
   대상: 03_components/ 또는 위 식별된 자료
   Brief: 01_refs/brief.md
   Tokens: 02_tokens/tokens.md

   6축 점검:
   1. 시각 위계 (hierarchy) — 시선 흐름 자연스러운가, 강조점이 맞는가
   2. 정렬·여백 (alignment, spacing) — 일관성, breathing room
   3. 접근성 (a11y) — WCAG AA contrast, keyboard nav, focus indicator, alt text
   4. 반응형 — breakpoint 깨짐 (모바일/태블릿/데스크탑)
   5. UX 흐름 — 로딩/에러/빈 상태, undo/취소
   6. 톤 일관성 — 토큰 일치, 다른 컴포넌트와 어울림

   산출: 04_review/critique.md
   우선순위 (🔴/🟡/🟢) 별 정리, 5-7개 핵심 발견만, 칭찬할 부분 별도"
```

### Step 3: critique 검증

🔴 발견 시 사용자에 보고:
- 어떤 axis 에서 문제
- 어떤 컴포넌트·파일
- 수정 방향 (코드 수정은 components phase 재호출 또는 maker mode 위임)

🟡 만 있으면 _다음 phase 진행 가능_, 단 사용자에 안내.

🟢 만 — 통과.

### Step 4: design_state.yaml 업데이트

- `🔴 0`: `phases.review: done`
- `🔴 ≥ 1`: `phases.review: failed`

## Output

- `04_review/critique.md` — 6축 별 발견 사항
- `04_review/summary.md` — 종합 판정 + 다음 액션

## Return Format

```
<design_path>/04_review/ -- ✅ review passed (M minor, K praise)
```

```
<design_path>/04_review/ -- 🔴 N major issues found — see critique.md
```

## Update agent memory

- 자주 발견하는 UX 함정 (예: "이 프로젝트는 빈 상태 누락이 흔함")
- 사용자가 자주 받아들이는/거부하는 비평 패턴
- 6축 중 자주 fail 하는 축
