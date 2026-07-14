---
name: design-handoff
description: "디자인 → 개발 핸드오프 자산·스펙 정리 sub-skill"
argument-hint: "<design path or app path>"
metadata:
  group: sub
  fam: sub
  modes: []
  blurb: "디자인 → 개발 핸드오프 자산·스펙 정리 sub-skill"
---

## Language Rule
- User-facing output follows the user's communication language; preserve code and path identifiers.

## Design Resolution

`design_state.yaml` 발견.

## Pre-Check

- `phases.review: done` (또는 `--intensity quick` 으로 review skip 됐을 시 components: done)
- 검토 결과 review 가 `failed` 면 handoff 거부, 사용자에 fix 권장

## Procedure

### Step 1: 산출물 inventory

design phase 의 모든 자산 모음:
- `02_tokens/tokens.md` + 실제 토큰 파일 경로
- `03_components/` 컴포넌트 목록 + **standalone preview (필수) + 검증 screenshot** — scope 별 단일 self-contained 파일이 보장됨 (`ui`/`webapp`/`icon`/`diagram` → `03_components/preview.html`, `slide` → `03_components/slides/slides.html`). 브라우저로 바로 열어볼 산출물로 handoff **상단에 필수 명시**. _유일한 예외_: paper architecture figure (디자인팀이 생성하지 않고 사용자 pptx 인계 — render/standalone 대상 아님)
- `04_review/critique.md` 의 _accepted issue_ (사용자가 의도적으로 두기로 한 것)

### Step 1.5: Output exports (converters, 요청·scope 적합 시)

브라우저 미리보기 외 배포 포맷이 필요하면 `~/.claude/tools/design-mcp/convert.mjs` 로 생성 (별도 도구 불필요 — Playwright/pptxgenjs 내장):

```bash
node ~/.claude/tools/design-mcp/convert.mjs pdf    <preview/slides>.html [out.pdf]     # 인쇄·배포 (덱: 1슬라이드=1페이지)
node ~/.claude/tools/design-mcp/convert.mjs bundle <preview>.html        [out.html]    # 모든 에셋 inline → 오프라인 단일 파일
node ~/.claude/tools/design-mcp/convert.mjs pptx   <slides>.html         [out.pptx]    # slide scope — 슬라이드별 full-bleed PNG + 스피커노트
```

- `slide` scope → PDF + PPTX 기본 제안. `webapp`/`ui` → bundle (오프라인 공유). `icon`/`diagram` → 보통 PNG/SVG 그대로.
- 생성물은 `05_handoff/exports/` 에 두고 handoff.md 에 경로 명시.

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

프로젝트 stack 없이 브라우저로 바로 열림 = Claude Design artifact 패리티. 시각 자가검증 (Design MCP 렌더 → view_image) + verifier 게이트 통과한 산출물.

## Exports (배포 포맷, 있으면)

| 포맷 | 파일 | 생성 |
|---|---|---|
| PDF | `05_handoff/exports/<name>.pdf` | `convert.mjs pdf` (덱: 1슬라이드=1페이지) |
| PPTX | `05_handoff/exports/<name>.pptx` | `convert.mjs pptx` (slide scope) |
| 단일 HTML 번들 (inline) | `05_handoff/exports/<name>.bundle.html` | `convert.mjs bundle` (기존 preview 오프라인화) |
| production 번들 (ui/webapp) | `05_handoff/exports/<name>.bundle.html` | real Tailwind/shadcn 빌드 → 단일파일 — 레시피 [`tools/web-bundle`](../../tools/web-bundle/README.md) (Vite+singlefile). 배포 후보·design-system 정합 시 |

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
