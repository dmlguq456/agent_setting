---
name: design-review
description: Visual review — two gates. (1) verifier (디자인팀 verifier mode, separate context, Design MCP) screens for breakage — console errors, layout collapse, intent mismatch — and must pass before critique. (2) critic (디자인팀 critic mode) gives a 6-axis quality critique (hierarchy, alignment, accessibility, responsiveness, UX flow, tone). Both render via the Design MCP and view the image. Read-only — no auto-fix.
argument-hint: "<design path or app path>"
metadata:
  group: sub
  fam: sub
  modes: []
  blurb: "디자인 결과물 6축 비평·토큰 계약 점검 sub-skill"
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

review 는 **두 게이트**다 — verifier 가 _깨졌는가_ (콘솔·레이아웃·의도) 를 먼저 걸러내고, critic 이 _얼마나 좋은가_ (6축 품질) 를 본다.

### Step 1: verifier 게이트 (독립 검수 — `Agent(디자인팀, mode=verifier)`)

별도 컨텍스트에서 산출물을 기계적으로 점검 (만든 사람 관대함 제거):

```
Agent(디자인팀, mode=verifier):
  "검수 대상: 03_components/preview.html (또는 slides.html)
   풀 스윕 — Design MCP 로 preview → getConsoleLogs → screenshot → view_image.
   콘솔 에러 / 레이아웃 붕괴(관통·overlap·잘림·빈 영역) / brief 의도 불일치 / a11y 하드 실패만.
   verdict: done | needs_work + issues[]."
```

`needs_work` 면 — `design_state.yaml` `phases.review: failed`, 사용자 보고 후 **critic 까지 가지 않고** components phase 재호출 권장.

### Step 2: 검토 대상을 **렌더해서 본다** (critic 입력 — 렌더한 이미지로 본다)

critic 은 렌더한 _이미지_ 를 직접 본다. **Design MCP** 로: `mcp__design__preview` → `screenshot` → `view_image`. 반응형은 `preview` viewport 를 바꿔 mobile/desktop 각각.

| scope | 렌더 → 본다 |
|---|---|
| ui / webapp | `preview.html` → preview/screenshot/view_image. 컴포넌트 + 페이지 전체. mobile/desktop viewport 각각 |
| slide | `slides.html` (deck_stage) → `screenshot({ steps })` 전 슬라이드 |
| icon | SVG → `sharp`/`rsvg-convert` PNG → view_image (확대) |
| diagram | SVG/mermaid → PNG → view_image. 관통·overlap·label 겹침 확인 |

렌더 불가 환경이면 그 사실을 critique 에 명시하고 _본 범위만_ 비평 (못 본 것을 본 척 X).

### Step 3: 디자인팀 critic 호출

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

### Step 4: critique 검증

🔴 발견 시 사용자에 보고:
- 어떤 axis 에서 문제
- 어떤 컴포넌트·파일
- 수정 방향 (코드 수정은 components phase 재호출 또는 maker mode 위임)

🟡 만 있으면 _다음 phase 진행 가능_, 단 사용자에 안내.

🟢 만 — 통과.

### Step 5: design_state.yaml 업데이트

- verifier `needs_work` OR critic `🔴 ≥ 1`: `phases.review: failed`
- verifier `done` AND critic `🔴 0`: `phases.review: done` (+ `verifier: passed`)

## Output

- `04_review/verifier.md` — verifier 판정 (verdict + issues, 콘솔·레이아웃·의도)
- `04_review/critique.md` — critic 6축 별 발견 사항
- `04_review/summary.md` — 종합 판정 (verifier + critic) + 다음 액션

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
