---
name: design-components
description: Component / visual asset creation — invokes 디자인팀 maker mode. Produces shadcn/Tailwind components (ui), composed full-screen pages (webapp), slide visual guides (slide), SVG icons (icon), or mermaid/direct-SVG/excalidraw diagrams (diagram). Every output is rendered and visually self-verified (render → Read → fix loop), and can be emitted as a self-contained single-file HTML preview artifact (--artifact standalone).
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
   - 단순 flow/sequence/architecture → mermaid syntax
   - 정밀 레이아웃·커스텀 비주얼 (관계 그래프·매트릭스·논문 figure 류) → 직접 SVG
     (many-to-many 는 화살표 대신 매트릭스/레인/거터 직각 라우팅 — 교차 회피)
   - 자유 스케치 → excalidraw
   **산출 후 반드시 PNG 렌더 → Read 로 보고 관통/overlap 수정** (Step 4)
   산출 위치: 03_components/diagrams/<name>.svg|.mmd|.excalidraw + 검증용 .png"
```

### Step 3: 실제 코드 통합 (scope=ui 만)

shadcn/ui 컴포넌트 install:
```bash
pnpm dlx shadcn@latest add button card dialog
```

(사용자 confirm 후)

생성된 코드는 프로젝트 루트의 `components/ui/` 에. 03_components/ 에는 customization · 사용 가이드만.

### Step 4: 시각 자가검증 (필수 — "valid/코드 작성됨" 으로 끝내지 말 것)

maker 가 산출 직후 **반드시 렌더해서 본다**. 좌표·코드만으로 완료 보고 금지. 상세 루프는 `agent-modes/design/maker.md` "시각 자가검증 루프".

scope 별 렌더 경로:

| scope | 렌더 → 본다 |
|---|---|
| `ui` / `webapp` | `preview.html` 또는 dev server 를 Playwright `preview_screenshot` → Read. 컴포넌트 단품 + **페이지 합성 전체 화면** 둘 다 |
| `slide` | 대표 슬라이드 1-2 장을 HTML/이미지로 렌더 → Read (가이드만으로 끝내지 않음) |
| `icon` | SVG → `sharp`/`rsvg-convert` PNG → Read (작은 자산은 확대 렌더) |
| `diagram` | SVG → PNG / mermaid → `mmdc` PNG → Read. 관통·overlap·label 겹침 확인, 의심 영역 crop 확대 |

루프: 렌더 → Read → 자가 비평 (관통·overlap·정렬·위계·잘림·색 역할) → 수정 → 재렌더. 시각적으로 깨끗할 때까지 (최대 3-5 회전). **렌더 이미지를 사용자에 제시** (live-preview 패리티).

### Step 4b: standalone preview artifact (`--artifact standalone` 또는 stack 부재 시)

프로젝트 stack 없이도 브라우저로 바로 열리는 **자체 완결 단일 파일** 산출:
- `03_components/preview.html` — inline `<style>` + (필요 시) CDN Tailwind/React (`https://cdn.tailwindcss.com`, esm.sh) + 모든 컴포넌트·페이지를 한 파일에. 외부 빌드 의존 0.
- diagram/icon 은 SVG 를 inline 한 `preview.html` 또는 SVG 자체.
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
