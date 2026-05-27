---
name: design-init
description: Design environment check and initial setup — verifies Figma MCP, shadcn/ui, Tailwind tokens, Playwright (preview tools), optional image generation MCP. Creates design_state.yaml.
argument-hint: "<design task description> [--scope ui|slide|icon|diagram|mixed]"
---

## Language Rule
- Korean output, English tool/path identifiers.

## Pre-Check

`.claude_reports/designs/<name>/` 또는 `.claude_reports/specs/<name>/02_design/` 에 이미 `design_state.yaml` 있는지 확인.
- 있음 → "이미 init 완료. 새 사이클 시작하려면 폴더 정리." 안내 후 중단
- 부재 → 계속

## Procedure

### Step 1: Design name 결정

사용자 입력 또는 호출자 (autopilot-spec) 가 준 app name 사용. 모호 시 한 줄 확인.

### Step 2: 환경 점검 (`00_init/environment_check.md`)

scope 별 필요 도구 다름:

| 도구 | UI/webapp | slide | icon | diagram |
|---|---|---|---|---|
| Figma MCP (figma-developer-mcp 등) | 권장 | 옵션 | 옵션 | X |
| shadcn/ui CLI | 권장 (`--artifact project` 시 필수) | X | X | X |
| Tailwind config (tokens.css / tailwind.config.ts) | 권장 (`project` 시 필수) | X | X | X |
| 이미지 생성 MCP (Replicate, BFL 등) | 옵션 | 옵션 | 권장 | X |
| **Playwright / preview_screenshot** (HTML·React 렌더) | **필수** (시각 검증) | 권장 | X | 옵션 |
| **SVG 래스터라이저** (sharp / rsvg-convert / cairosvg / inkscape) | 권장 | 옵션 | **필수** | **필수** |
| **mermaid-cli (`mmdc`)** (mermaid → PNG 렌더) | X | X | X | 권장 (mermaid 쓸 때) |
| excalidraw | X | X | X | 옵션 |

> **시각 검증 도구는 선택이 아님** — components·review phase 가 _렌더해서 본다_ 를 전제로 한다. scope 에 맞는 렌더 도구 (HTML→Playwright, SVG→래스터라이저, mermaid→mmdc) 중 최소 하나가 없으면 시각 자가검증 루프가 불가하니, 부재 시 우선 설치 안내.

각 도구 확인 명령:

```bash
# shadcn/ui 초기화 여부
test -f components.json && echo 'shadcn:OK' || echo 'shadcn:MISSING'

# Tailwind config
test -f tailwind.config.ts -o -f tailwind.config.js && echo 'tailwind:OK' || echo 'tailwind:MISSING'

# tokens.css
find . -name "tokens.css" -not -path "./node_modules/*" 2>/dev/null | head -1

# 시각 검증 렌더 도구 (최소 하나 필요)
node -e "require('sharp')" 2>/dev/null && echo 'sharp:OK' || echo 'sharp:MISSING'
command -v rsvg-convert >/dev/null && echo 'rsvg:OK'
command -v mmdc >/dev/null && echo 'mermaid-cli:OK'
command -v cairosvg inkscape >/dev/null 2>&1 && echo 'svg-alt:OK'
```

렌더 도구가 모두 부재하면 안내 (시각 자가검증 루프 필수):
```
시각 검증 렌더 도구 부재. 하나 설치 필요:
  SVG/다이어그램  → $ npm i sharp   또는  $ apt install librsvg2-bin
  mermaid         → $ npm i -g @mermaid-js/mermaid-cli
  HTML/React      → Playwright preview_screenshot (이미 있으면 OK)
설치할까요? (components/review phase 가 이 도구로 렌더해서 결과를 눈으로 확인합니다.)
```

부재 도구 발견 시:
- **자동 설치 X**
- 사용자에 안내: "이 도구가 부재합니다. 다음 명령으로 설치할 수 있어요:" + 명령 제시

예시:
```
shadcn/ui 초기화 안 됨. 다음 명령으로 설치 가능:
  $ pnpm dlx shadcn@latest init

진행할까요? (이 디자인 사이클이 컴포넌트 만들기를 포함한다면 필수입니다.)
```

### Step 3: Figma MCP 검증 (옵션, scope=ui|slide|icon 시)

```bash
# MCP 서버 목록 확인
claude mcp list 2>/dev/null | grep -i figma
```

부재 시 안내. 사용자가 Figma 파일 _참조하지 않는_ 디자인이면 skip 가능.

### Step 4: 기존 디자인 자산 inventory

- `tokens.css` 또는 `tailwind.config.ts` 경로 (있으면 _다음 phase 에서 확장_, 없으면 _신규 생성_)
- `components/ui/` 또는 비슷한 컴포넌트 디렉토리
- `public/icons/` 또는 SVG 자산 폴더
- 이전 사이클의 design 자산 (`.claude_reports/designs/*` 또는 `02_design/`)

결과를 `00_init/asset_inventory.md` 에 정리.

### Step 5: design_state.yaml 생성

```yaml
design_name: <name>
scope: <ui|slide|icon|diagram|mixed>
created: <YYYY-MM-DD>
output_dir: <full path>
environment:
  figma_mcp: <OK|MISSING|N/A>
  shadcn: <OK|MISSING|N/A>
  tailwind: <OK|MISSING|N/A>
  image_gen_mcp: <OK|MISSING|N/A>
  playwright: <OK|MISSING|N/A>
  svg_renderer: <sharp|rsvg|cairosvg|inkscape|MISSING>   # 시각 검증 필수 (scope=icon/diagram)
  mermaid_cli: <OK|MISSING|N/A>
  visual_verify_ready: <true|false>                       # 렌더 도구 최소 하나 확보 여부
existing_assets:
  tokens_file: <path or null>
  components_dir: <path or null>
  icons_dir: <path or null>
phases:
  init: done
  refs: pending
  tokens: pending
  components: pending
  review: pending
  handoff: pending
last_updated: <timestamp>
```

## Output

- `00_init/environment_check.md` — 도구 점검 결과
- `00_init/asset_inventory.md` — 기존 자산 목록
- `design_state.yaml`

## Return Format

```
<output_dir>/00_init/ -- ✅ init completed (scope: <scope>, K tools OK, M missing)
```

부재 도구가 _필수_ 인 경우:
```
<output_dir>/00_init/ -- ⚠️ init completed but K required tools missing — install before next phase
```

## Update agent memory

- 사용자 환경에 자주 부재한 도구
- scope 별 도구 필요성 누적
- 기존 자산 발견 패턴
