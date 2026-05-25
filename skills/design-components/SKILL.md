---
name: design-components
description: Component / visual asset creation — invokes 디자인팀 maker mode. Produces shadcn/Tailwind components (ui), slide visual guides (slide), SVG icons (icon), or mermaid/excalidraw diagrams (diagram).
argument-hint: "<design path or app path>"
---

## Language Rule
- Korean output, English code identifiers.

## Design Resolution

`design_state.yaml` 발견 (`.claude_reports/designs/<name>/` 또는 `02_design/`).

## Pre-Check

- `phases.tokens: done` 검증 (scope != icon|diagram 인 경우)
- `01_refs/brief.md` Read 가능 여부

## Procedure

### Step 1: brief + tokens Read

- `01_refs/brief.md` — 의도·톤
- `02_tokens/tokens.md` — 디자인 토큰 (단일 source)

### Step 2: scope 별 dispatch

#### scope=ui (가장 흔함)

PRD (autopilot-spec 에서 위임된 경우) 또는 사용자 명시에서 _필요한 컴포넌트 목록_ 추출:

```
Agent(디자인팀, mode=maker):
  "UI 컴포넌트 작성.
   Brief: 01_refs/brief.md
   Tokens: 02_tokens/tokens.css (또는 tailwind config)
   필요 컴포넌트: [TaskRow, TaskForm, EmptyState, ...]
   각 컴포넌트:
     - shadcn/ui base + Tailwind customization
     - Props 명세
     - 한 page 의 사용 예시
     - 접근성 (a11y) 신경
   산출 위치: 03_components/<component>.tsx + 03_components/<component>.md (spec)"
```

산출물:
- `03_components/<name>.tsx` — 실제 React 컴포넌트
- `03_components/<name>.md` — props · 사용 예시 · 접근성 노트

#### scope=slide

```
Agent(디자인팀, mode=maker):
  "발표 슬라이드 비주얼 가이드.
   각 슬라이드:
     - 레이아웃 (text-left, image-right 등)
     - 색 사용 가이드 (brand-500 강조, neutral 본문)
     - 타이포 hierarchy (h1 / body / caption)
     - 강조 패턴 (bold / highlight / accent stripe)
   산출 위치: 03_components/slides/slide_<N>.md (마크다운 가이드)"
```

#### scope=icon

```
Agent(디자인팀, mode=maker):
  "아이콘·로고 만들기.
   - Lucide / Iconify 매칭 우선
   - 매칭 없으면 SVG 직접 작성
   - 이미지 생성 MCP 활용 가능 (logo 등 복잡)
   산출 위치: 03_components/icons/<name>.svg + 03_components/icons/index.md"
```

#### scope=diagram

```
Agent(디자인팀, mode=maker):
  "다이어그램 작성.
   - mermaid syntax (architecture, flow, sequence)
   - 또는 excalidraw (자유 형식)
   산출 위치: 03_components/diagrams/<name>.mmd 또는 .excalidraw"
```

### Step 3: 실제 코드 통합 (scope=ui 만)

shadcn/ui 컴포넌트 install:
```bash
pnpm dlx shadcn@latest add button card dialog
```

(사용자 confirm 후)

생성된 코드는 프로젝트 루트의 `components/ui/` 에. 03_components/ 에는 customization · 사용 가이드만.

### Step 4: preview 검증 (옵션)

dev server 켜고 `preview_screenshot` 으로 결과 확인. 사용자에 보여줌.

### Step 5: design_state.yaml 업데이트

`phases.components: done` + `components_dir: 03_components/`.

## Output

- `03_components/` — 컴포넌트 spec + 코드 (scope 별)
- 프로젝트 루트의 실제 컴포넌트 파일 (사용자 confirm 후)

## Return Format

```
<design_path>/03_components/ -- ✅ components ready (N components / K assets)
```

## Update agent memory

- 자주 만든 컴포넌트 (TaskRow, EmptyState 등) 의 패턴
- shadcn 사용 빈도 vs 직접 작성 빈도
- 사용자 선호 컴포넌트 구조 (props 명명, hooks 분리 정도)
