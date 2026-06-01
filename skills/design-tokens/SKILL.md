---
name: design-tokens
description: Design tokens decision — color palette, typography scale, spacing scale, radius, shadow, motion. Writes tokens.css / tailwind.config.ts. Extends existing tokens (never silently overwrites). Versions every change — snapshots prior tokens to _internal/versions/v{N}/ + logs reason to design_summary.md (mirrors spec versioning), so later token edits stay traceable.
argument-hint: "<design path or app path>"
---

## Language Rule
- Korean output, English token names (color hex, font family names, spacing units).

## Design Resolution

`design_state.yaml` 발견:
- `.claude_reports/designs/<name>/` 또는 `.claude_reports/spec/<name>/design/`

## Pre-Check

- `phases.refs: done` 검증 → brief 없이는 token 결정 불가
- `00_init/asset_inventory.md` Read — 기존 `tokens.css` 또는 `tailwind.config.ts` 발견 여부

기존 토큰 발견 시:
- 기본 mode: **확장** (기존 보존 + 새 토큰 추가)
- 명시 요청 시: **재설계** (기존 백업 후 신규)

## Procedure

### Step 1: brief Read

`01_refs/brief.md` 의 _색감 방향 / 폰트 방향 / 톤·무드_ 추출.

### Step 2: 디자인 결정 (`02_tokens/tokens.md`)

```markdown
# Design Tokens — <name>

## Color Palette

### Brand
- `--color-brand-50`: #FFF8F3
- `--color-brand-500`: #F97316  (primary)
- `--color-brand-700`: #C2410C
- ...

**결정 사유**: 사용자 brief 의 "warm, minimal" — orange-coral 계열로 단일 brand axis. neutral 은 zinc 계열로 대비.

### Neutral
- `--color-neutral-50`: ...
- ...

### Semantic
- `--color-success-500`: green-500
- `--color-warning-500`: amber-500
- `--color-danger-500`: red-500

## Typography

### Font Family
- `--font-sans`: 'Inter', system-ui, sans-serif
- `--font-serif`: 'Iowan Old Style', serif  (paper figure 만)
- `--font-mono`: 'JetBrains Mono', monospace

### Scale
- `--text-xs`: 12px / 16px
- `--text-sm`: 14px / 20px
- `--text-base`: 16px / 24px
- `--text-lg`: 18px / 28px
- `--text-xl`: 20px / 28px
- `--text-2xl`: 24px / 32px

**결정 사유**: 본문 16px / 1.5 — 가독성 표준. heading scale 은 1.25 modular (minor 3rd).

## Spacing

- `--space-1`: 4px
- `--space-2`: 8px
- `--space-3`: 12px
- `--space-4`: 16px
- `--space-6`: 24px
- `--space-8`: 32px

8-point grid + 4-point sub-unit. Tailwind default 와 호환.

## Radius

- `--radius-sm`: 4px
- `--radius-md`: 8px
- `--radius-lg`: 12px
- `--radius-full`: 9999px

shadcn default 보다 살짝 작게 — 사용자 선호 (memory 참조 시).

## Shadow

- `--shadow-sm`: 0 1px 2px rgb(0 0 0 / 0.05)
- `--shadow-md`: 0 4px 6px -1px rgb(0 0 0 / 0.1)

## Motion

- `--ease-out`: cubic-bezier(0.16, 1, 0.3, 1)
- `--duration-fast`: 150ms
- `--duration-base`: 250ms
```

### Step 3: specimen 시각 자가검증 (필수 — 토큰을 component 가 소비하기 _전_)

토큰은 그 자체로 시각 시스템 (palette / type / spacing) 이라, 값만 정하고 넘기지 않는다. **렌더해서 본 것** 으로만 완료.

`02_tokens/specimen.html` — 자체 완결 단일 파일 (inline `<style>`, 외부 빌드 의존 0):
- **color swatch** — 각 색 칩에 hex 표기 + 주요 foreground/background 쌍의 **WCAG contrast ratio** 명시 (본문 ≥4.5:1, large ≥3:1 통과 여부 라벨)
- **type scale 전체** — xs~2xl 까지 실제 글자로 렌더 (line-height 포함)
- **spacing / radius / shadow ruler** — 각 단계를 시각 막대·박스로

루프: specimen.html 렌더 (Playwright `preview_screenshot`) → **Read 로 이미지 직접 보기** → 대비·조화 자가 비평 (대비 미달 쌍 / 색 충돌 / scale 점프 불균일) → 토큰 조정 → 재렌더. 깨끗할 때까지. **이 검증을 통과해야 component 가 토큰을 소비**.

### Step 4: 실제 토큰 파일 작성

#### Option A: tokens.css (CSS variables)

`<project_root>/styles/tokens.css` 또는 `<project_root>/app/tokens.css`:

```css
:root {
  --color-brand-500: #F97316;
  --color-neutral-50: #FAFAFA;
  /* ... */
}

@media (prefers-color-scheme: dark) {
  :root {
    --color-neutral-50: #18181B;
    /* dark mode 적응 */
  }
}
```

#### Option B: tailwind.config.ts

`<project_root>/tailwind.config.ts`:

```ts
import type { Config } from 'tailwindcss'

const config: Config = {
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#FFF8F3',
          500: '#F97316',
          // ...
        },
      },
      fontFamily: { /* ... */ },
      spacing: { /* ... */ },
    },
  },
}
export default config
```

스택에 따라 둘 중 하나 또는 둘 다.

### Step 5: 기존 토큰 호환 + 버전 스냅샷

토큰 변경은 spec 의 `_internal/versions/v{N}/` 와 같은 방식으로 추적한다. 기존 `tokens.css`/`tailwind.config.ts` 또는 `02_tokens/tokens.md` 발견 시 **덮어쓰기·확장 _전_**:

1. 직전 `02_tokens/tokens.md` + 실제 토큰 파일(`tokens.css`/`tailwind.config.ts`)을 `_internal/versions/v{N}/` 로 자동 snapshot (N = `_internal/versions/` 의 기존 최대 +1).
2. 새 토큰 추가 (확장 mode — 기존 키 보존) 또는 신규 작성 (재설계 mode — 명시 요청 시).
3. 변경 narrative 를 `design_summary.md` 에 통합 기록 — _바뀐 토큰 / old→new 값 / 사유 / 날짜_. design cycle 의 **단일 변경 이력 source** (spec 의 `pipeline_summary.md` 미러). 별도 CHANGELOG 두지 않음.
4. 충돌 시 사용자 confirm.

> **minor/major 판정** (DESIGN_PRINCIPLES §4 동일 원리): minor (1~2 토큰 미세조정) → snapshot 생략 + `design_summary.md` minor-log 만. major (palette/scale 재설계·신규 axis) → `v{N}` snapshot. 누적 minor 5+ 시 `/audit` alert.

### Step 6: design_state.yaml 업데이트

`phases.tokens: done` + `tokens_path: <실제 파일 경로>` + `tokens_version: v{N}` (현재 토큰 버전) + `tokens_updated: <date>` + `specimen: 02_tokens/specimen.html` + `tokens_verified_visually: true`.

> `tokens_version` / `tokens_updated` 는 autopilot-code 의 _역방향 drift 체크_ 가 읽는 필드 — 토큰이 직전 코드 작업 이후 갱신됐는지 판정하는 anchor.

## Output

- `02_tokens/tokens.md` — 결정 사유 + 토큰 값
- `02_tokens/specimen.html` — swatch·type·spacing 시각 검증 산출 (렌더 → Read 자가검증 완료)
- 프로젝트 루트의 `tokens.css` 또는 `tailwind.config.ts` (사용자 confirm 후 작성·확장)
- `_internal/versions/v{N}/` — 직전 토큰 snapshot (major 변경 시; `tokens.md` + 토큰 파일)
- `design_summary.md` — 토큰 변경 이력 narrative (단일 변경 이력 source; spec `pipeline_summary.md` 미러)

## Return Format

```
<design_path>/02_tokens/ -- ✅ tokens decided (N colors, K type scale, M spacing)
```

기존 확장:
```
<design_path>/02_tokens/ -- ✅ tokens extended (+K new tokens, existing preserved)
```

## Update agent memory

- 사용자 자주 선택하는 색감 방향
- 폰트 선호 (Inter / system / serif 자주 선택)
- shadcn default 에서 자주 바꾸는 토큰
- 다크 모드 적응 패턴
