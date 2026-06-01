---
name: design-handoff
description: Final handoff — consolidates design artifacts into a single handoff.md that frontend devs (or autopilot-spec build phase) can use directly. Lists components, token paths, import paths, reproduction guide.
argument-hint: "<design path or app path>"
---

## Language Rule
- Korean output, English code/path identifiers.

## Design Resolution

`design_state.yaml` 발견.

## Pre-Check

- `phases.review: done` (또는 `--qa quick` 으로 review skip 됐을 시 components: done)
- 검토 결과 review 가 `failed` 면 handoff 거부, 사용자에 fix 권장

## Procedure

### Step 1: 산출물 inventory

design phase 의 모든 자산 모음:
- `02_tokens/tokens.md` + 실제 토큰 파일 경로
- `03_components/` 컴포넌트 목록 + **standalone preview (필수) + 검증 screenshot** — scope 별 단일 self-contained 파일이 보장됨 (`ui`/`webapp`/`icon`/`diagram` → `03_components/preview.html`, `slide` → `03_components/slides/slides.html`). 브라우저로 바로 열어볼 산출물로 handoff **상단에 필수 명시**. _유일한 예외_: paper architecture figure (디자인팀이 생성하지 않고 사용자 pptx 인계 — render/standalone 대상 아님)
- `04_review/critique.md` 의 _accepted issue_ (사용자가 의도적으로 두기로 한 것)

### Step 2: handoff.md 작성

`05_handoff/handoff.md`:

```markdown
# Design Handoff — <name>

**완성**: <date>
**Scope**: <ui|slide|icon|diagram|mixed>
**Cycle**: <N>

---

## Preview (브라우저로 바로 열기)

> **필수 산출물** — paper architecture figure scope 외 모든 scope 에 보장됨.

| 파일 | 위치 | 검증 screenshot |
|---|---|---|
| `preview.html` (또는 slide 면 `slides.html`) | `03_components/preview.html` / `03_components/slides/slides.html` | `<렌더 검증 png 경로>` |

프로젝트 stack 없이 브라우저로 바로 열림 = Claude Design artifact 패리티. 시각 자가검증 (렌더 → Read) 통과한 산출물.

---

## Tokens

| 파일 | 위치 | 사용법 |
|---|---|---|
| `tokens.css` | `<project>/styles/tokens.css` | `@import` in `app/globals.css` |
| `tailwind.config.ts` | `<project>/tailwind.config.ts` | 자동 적용 |

**토큰 버전**: `v{N}` (`design_state.yaml` 의 `tokens_version`, `<date>` 갱신) — autopilot-code 가 _역방향 drift 체크_ 시 이 버전을 코드 반영분과 대조. 변경 이력은 `design_summary.md`.

핵심 토큰:
- Brand color: `--color-brand-500` (#F97316)
- Sans font: Inter
- Spacing scale: 4-point grid

자세한 결정 사유는 `02_tokens/tokens.md` 참조.

---

## Components

| 이름 | 위치 | Props | 사용 예시 |
|---|---|---|---|
| `TaskRow` | `components/ui/task-row.tsx` | `{ task, onComplete }` | `03_components/task-row.md` 참조 |
| ...|

각 컴포넌트의 자세한 spec 은 `03_components/<name>.md`.

---

## Frontend 개발자 가이드 (frontend-eng / autopilot-spec 의 build phase 가 import)

```tsx
// 토큰
import '@/styles/tokens.css'

// 컴포넌트
import { TaskRow } from '@/components/ui/task-row'

export default function TasksPage() {
  return <TaskRow task={...} onComplete={...} />
}
```

---

## 알아둘 점

- 다크 모드: `tokens.css` 에 `prefers-color-scheme: dark` 적용 — 자동
- 반응형: 컴포넌트가 모바일 우선. `md:` breakpoint 부터 데스크탑 변형
- 접근성: 모든 interactive 요소에 `aria-label` 또는 visible label
- Accepted issues (review 에서 의도적으로 둔 것): N건 — 04_review/critique.md 참조

---

## 다음 사이클

이 design 을 사용해 build 진행:
- autopilot-spec 에서 호출됐다면: 자동으로 Phase 3 (build) 로 인계
- 직접 호출이었다면: `/autopilot-code` 호출 권장 (앱 mode 자동 — 디자인 자산 위 컴포넌트 구현)

피드백 있으면:
- 토큰 변경 → `/design-tokens <design>` 재실행
- 컴포넌트 추가 → `/design-components <design>` 재실행
- 새 사이클 → `/autopilot-design <design> --from refs`
```

### Step 3: 호출자별 인계

#### autopilot-spec 에서 위임된 경우

- 산출 path 를 autopilot-spec 에 반환
- autopilot-spec 의 `pipeline_state.yaml` 의 `phases.design: done` 갱신

#### 사용자 직접 호출

- 위 handoff.md 사용자에 보여줌
- 다음 액션 (build 또는 새 사이클) 안내

### Step 4: design_state.yaml 업데이트

`phases.handoff: done` — 사이클 완료.

## Output

- `05_handoff/handoff.md` — 단일 통합 문서
- 호출자 (autopilot-spec 또는 사용자) 에 path 반환

## Return Format

```
<design_path>/05_handoff/handoff.md -- ✅ design cycle completed (cycle <N>)
```

autopilot-spec 위임:
```
<app_path>/design/05_handoff/handoff.md -- ✅ handed off to autopilot-spec build phase
```

## Update agent memory

- handoff 후 frontend 가 자주 막히는 부분 (다음 cycle 에 보강)
- 사용자가 자주 review 에서 accepted 로 두는 issue 패턴
- 사이클 간 변동률 (토큰 안정 vs 자주 바뀜)
