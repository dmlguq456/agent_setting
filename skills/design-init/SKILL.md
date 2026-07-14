---
# GENERATED METADATA — edit harness-manifest.json, then run tools/generate.py.
name: design-init
description: "Use when invoking the portable design-init capability. 디자인 환경과 state를 bootstrap한다."
argument-hint: "<design task description> [--scope ui|slide|icon|diagram|mixed]"
metadata:
  group: sub
  fam: sub
  modes: []
  blurb: "디자인 환경과 state를 bootstrap한다."
---

## Language Rule
- Korean output, English tool/path identifiers.

## Pre-Check

`<artifact-root>/designs/<name>/` 또는 `<artifact-root>/spec/design/` 에 이미 `design_state.yaml` 있는지 확인.
- 있음 → "이미 init 완료. 새 사이클 시작하려면 폴더 정리." 안내 후 중단
- 부재 → 계속

## Procedure

### Step 1: Design name 결정

사용자 입력 또는 호출자 (autopilot-spec) 가 준 app name 사용. 모호 시 한 줄 확인.

### Step 2: Design MCP 부트스트랩 & 자가 프로비저닝 (시각 검증의 본체 — 최우선)

시각 자가검증 루프 (components·review·tokens phase 가 전제) 는 **Design MCP** (`~/.claude/tools/design-mcp/`) 로 돈다. 스펙 §0.5 의 _"필요하면 알아서 깔고 띄워 검증까지 끝낸 뒤 일한다"_ 원칙을 따른다. 환경 부재로 작업을 중단하지 않는다 (가드레일·권한 차단 제외).

자가 점검 → 부재분만 프로비저닝 (프로젝트-로컬·MCP 등록은 알릴 필요 없이 진행; OS 전역 패키지 설치만 한 줄 알리고):

```bash
# 1) Node 18+
node -v

# 2) Design MCP 설치 상태
test -d "$HOME/.claude/tools/design-mcp/node_modules" && echo 'design-mcp:installed' || echo 'design-mcp:needs-install'

# 3) MCP 등록 상태 (Claude Code 가 인식하는가)
claude mcp list 2>/dev/null | grep -q '^design:' && echo 'design-mcp:registered' || echo 'design-mcp:unregistered'
```

부재분 처리:
- `needs-install` → `(cd ~/.claude/tools/design-mcp && npm install)` (Playwright·sharp·pptxgenjs 포함, lockfile 고정). 브라우저 누락 시 `npx playwright install chromium` (없을 때만; 보통 `~/.cache/ms-playwright` 에 이미 있음).
- `unregistered` → `claude mcp add design --scope user -- node ~/.claude/tools/design-mcp/server.js` (user scope = 전 프로젝트 공유). **등록 직후 새 세션에서야 도구가 붙는다** — 같은 세션에서 막 등록했다면 사용자에 "다음 세션부터 `mcp__design__*` 사용 가능, 이번 사이클은 fallback (`sharp`/`rsvg`/`mmdc` 정적 렌더)" 안내.
- **스모크 테스트** — `(cd ~/.claude/tools/design-mcp && npm run smoke)` 가 7/7 통과해야 프로비저닝 완료 (preview→screenshot→view_image, 콘솔 에러 캡처, eval_js computed-style, steps 다중 캡처).

scope 별 _부가_ 도구 (있으면 좋음, 없어도 Design MCP 로 진행):

| 도구 | 용도 | 부재 시 |
|---|---|---|
| Figma MCP | Figma 파일 참조 (ui/slide/icon) | 참조 안 하면 skip |
| shadcn/ui CLI (`components.json`) | 컴포넌트 install (`--artifact project` 시) | `pnpm dlx shadcn@latest init` 안내 |
| Tailwind config / tokens.css | 디자인 토큰 (`project` 시) | tokens phase 가 생성 |
| 이미지 생성 MCP | 로고·일러스트·썸네일 | placeholder (`image_slot` scaffold) 로 진행 |
| SVG 래스터라이저 (sharp/rsvg/cairosvg/inkscape) | SVG·다이어그램 _단품_ PNG (브라우저 불필요) | sharp 는 design-mcp 에 이미 포함; 단품 빠른 렌더용 |
| mermaid-cli (`mmdc`) | mermaid → PNG | `npm i -g @mermaid-js/mermaid-cli` (mermaid 쓸 때만) |

> OS 전역 패키지 (`apt install librsvg2-bin` 등) 설치는 _실행 전 한 줄 알리고_ 진행. 프로젝트-로컬 (`npm install` in tools dir) 은 바로. 네트워크·권한 차단 시 추측 말고 정확한 차단 지점 보고.

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
- 이전 사이클의 design 자산 (`<artifact-root>/designs/*` 또는 `design/`)

결과를 `00_init/asset_inventory.md` 에 정리.

### Step 5: design_state.yaml 생성

```yaml
design_name: <name>
scope: <ui|slide|icon|diagram|mixed>
created: <YYYY-MM-DD>
output_dir: <full path>
environment:
  design_mcp: <registered|installed-unregistered|needs-install>  # 시각 검증 본체
  design_mcp_smoke: <pass|fail|skipped>                            # npm run smoke 결과
  figma_mcp: <OK|MISSING|N/A>
  shadcn: <OK|MISSING|N/A>
  tailwind: <OK|MISSING|N/A>
  image_gen_mcp: <OK|MISSING|N/A>
  svg_renderer: <sharp|rsvg|cairosvg|inkscape|bundled>            # 단품 SVG/diagram 빠른 렌더
  mermaid_cli: <OK|MISSING|N/A>
  visual_verify_ready: <true|false>                               # design_mcp registered+smoke pass OR fallback 렌더 확보
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
