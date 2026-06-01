---
name: design-components
description: Component / visual asset creation — invokes 디자인팀 maker mode. Produces shadcn/Tailwind components (ui), composed full-screen pages (webapp), slide visual guides (slide), SVG icons (icon), or mermaid/direct-SVG/excalidraw diagrams (diagram). Every output is rendered and visually self-verified (render → Read → fix loop), and can be emitted as a self-contained single-file HTML preview artifact (--artifact standalone).
argument-hint: "<design path or app path>"
---

## Language Rule
- Korean output, English code identifiers.

## Design Resolution

`design_state.yaml` 발견 (`.claude_reports/designs/<name>/` 또는 `design/`).

## Pre-Check

- `phases.tokens: done` 검증 (scope != icon|diagram 인 경우)
- `01_refs/brief.md` Read 가능 여부

## Procedure

### Step 1: brief + tokens + scaffold Read

- `01_refs/brief.md` — 의도·톤
- `02_tokens/tokens.md` — 디자인 토큰 (단일 source)
- **scaffold 매칭** — 바퀴 재발명 금지. `~/.claude/scaffolds/` 에서 골라 design 폴더로 복사 후 채운다:
  - `slide` → `deck_stage/deck_stage.html` (자동 스케일·키보드 내비·PDF). **덱은 손으로 만들지 말 것.**
  - variant 요청 → `tweaks_panel/` (파일 늘리지 말고 트윅). 목업 → `device_frames/`. 옵션 비교 → `design_canvas/`. 이미지 자리 → `image_slot/`.

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
  "발표 슬라이드 비주얼.
   각 슬라이드:
     - 레이아웃 (text-left, image-right 등)
     - 색 사용 (brand-500 강조, neutral 본문)
     - 타이포 hierarchy (h1 / body / caption)
     - 강조 패턴 (bold / highlight / accent stripe)
   **`deck_stage` scaffold 를 베이스로** — `~/.claude/scaffolds/deck_stage/deck_stage.html` 복사 →
   각 슬라이드를 `<section class=\"slide\">` 로 채운다 (자동 스케일·키보드 내비·PDF·스피커노트 슬롯 내장).
   본문 ≥ 24px (1920×1080 기준). **모든 슬라이드가 렌더 대상** (마크다운 가이드만으로 끝내지 않음).
   산출 위치:
     - 03_components/slides/slide_<N>.md (마크다운 가이드, 의도 기록용)
     - 03_components/slides/slides.html (deck_stage 기반 단일 self-contained 덱)
   산출 후 Step 4 의 시각 자가검증 루프로 **전 슬라이드** 렌더 → view_image → 수정."
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
   - 단순 flow/sequence/architecture → mermaid syntax
   - 관계 그래프·매트릭스·워크플로우 (LLM 가능 영역) → 직접 SVG
     (many-to-many 는 화살표 대신 매트릭스/레인/거터 직각 라우팅 — 교차 회피)
   - 자유 스케치 → excalidraw
   - **논문용 architecture figure (사용자 deck 양식) → layout 가이드만**:
     블록 list(라벨·역할색·위치) + 흐름 + 강조 자리 markdown sketch.
     본 그림은 사용자가 pptx 에서 직접 (assets/figure/svg/ + figure_ppt/ 안내).
     LLM 시각 craft 한계 — autopilot-design 정책 참조.
   **산출 후 반드시 PNG 렌더 → Read 로 보고 관통/overlap 수정** (Step 4) — paper architecture 는 wireframe 만이라 검증 가벼움.
   산출 위치: 03_components/diagrams/<name>.svg|.mmd|.excalidraw|.md + 검증용 .png"
```

### Step 3: 실제 코드 통합 (scope=ui 만)

shadcn/ui 컴포넌트 install:
```bash
pnpm dlx shadcn@latest add button card dialog
```

(사용자 confirm 후)

생성된 코드는 프로젝트 루트의 `components/ui/` 에. 03_components/ 에는 customization · 사용 가이드만.

### Step 4: 시각 자가검증 (필수 — "valid/코드 작성됨" 으로 끝내지 말 것)

maker 가 산출 직후 **반드시 렌더해서 본다** (Design MCP 경유). 좌표·코드만으로 완료 보고 금지. 상세 루프는 `agent-modes/design/maker.md` + `_design_rules.md` "시각 자가검증 루프".

공통 흐름: `mcp__design__preview({ path })` → `mcp__design__getConsoleLogs()` (에러 먼저) → `mcp__design__screenshot({ savePath, steps })` → `mcp__design__view_image({ path })`. scope 별:

| scope | 렌더 → 본다 |
|---|---|
| `ui` / `webapp` | `preview.html` 을 `preview` → screenshot → view_image. 컴포넌트 단품 + **페이지 합성 전체 화면** 둘 다. hover/active/empty/loading 은 `steps[]` 로. 반응형은 `preview` viewport 변경 |
| `slide` | `slides.html` (deck_stage) 을 `preview` → `screenshot({ steps })` 로 **전 슬라이드** 캡처 (각 step: 다음 슬라이드로 이동) → view_image. _un-rendered 가이드로 남는 슬라이드 없음_ |
| `icon` | SVG → `sharp`/`rsvg-convert` PNG → view_image (작은 자산은 `clip`/density 확대). 또는 preview.html gallery 로 |
| `diagram` | SVG → PNG / mermaid → `mmdc` PNG → view_image. 관통·overlap·label 겹침 확인, 의심 영역 `clip` crop 확대 |

루프: 렌더 → view_image → 자가 비평 (관통·overlap·정렬·위계·잘림·색 역할) → 수정 → 재렌더. 시각적으로 깨끗할 때까지 (최대 3-5 회전). **렌더 이미지를 사용자에 제시** (live-preview 패리티). _Design MCP 미부착 세션_ (막 등록함) 이면 `sharp`/`rsvg`/`mmdc` 정적 렌더로 fallback.

### Step 4b: standalone preview artifact (`--artifact standalone` 또는 stack 부재 시)

프로젝트 stack 없이도 브라우저로 바로 열리는 **자체 완결 단일 파일** 산출 (scope 별 1개 보장):
- `ui` / `webapp` → `03_components/preview.html` — inline `<style>` + (필요 시) CDN Tailwind/React (`https://cdn.tailwindcss.com`, esm.sh) + 모든 컴포넌트·페이지를 한 파일에. 외부 빌드 의존 0.
- `slide` → `03_components/slides/slides.html` — **단일 self-contained 덱**. 한 슬라이드 = 한 `<section>` (inline CSS, reveal/section 스타일), 모든 슬라이드를 한 파일에. 프로젝트 stack 불필요, 브라우저로 바로 열림.
- `icon` / `diagram` → `03_components/preview.html` — 모든 SVG 를 inline 한 라벨링 grid (icon gallery / diagram + legend). ui/webapp 단일 파일 경로와 일관 (SVG 파일 자체만 흩뿌리지 않음).
- 이 파일을 렌더·screenshot 해 검증하고 사용자에 경로 + 이미지 제시 = Claude Design artifact 패리티.

### Step 4c: 완성도 체크 (polish — generic flowchart/와이어프레임 탈피)

렌더 본 뒤 다음을 _시각적으로_ 확인: ① focal point 1 개가 시선을 먼저 잡는가 (위계 평평 X) ② 정렬선·spacing 리듬 일관 ③ 여백이 답답하지 않은가 ④ 상태 (hover/active/empty/loading) 표현 ⑤ 색이 역할대로 (token 일치) ⑥ 타이포 위계 (heading/body/caption 명확). 미달 시 Step 4 루프로 회귀.

### Step 5: design_state.yaml 업데이트

`phases.components: done` + `components_dir: 03_components/` + `preview: <preview.html 경로 또는 screenshot>` + `verified_visually: true`.

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
