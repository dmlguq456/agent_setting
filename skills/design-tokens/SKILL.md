---
name: design-tokens
description: Design tokens decision — color palette, typography scale, spacing scale, radius, shadow, motion. Writes tokens.css / tailwind.config.ts. Extends existing tokens (never silently overwrites).
argument-hint: "<design path or app path>"
---

## Language Rule
- Korean output, English token names (color hex, font family names, spacing units).

## Design Resolution

`design_state.yaml` 발견:
- `.claude_reports/designs/<name>/` 또는 `.claude_reports/specs/<name>/02_design/`

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

### Step 3: 실제 토큰 파일 작성

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

### Step 4: 기존 토큰 호환

기존 `tokens.css` 또는 `tailwind.config.ts` 있으면:
- 기존 백업: `_internal/tokens_backup_<date>.css`
- 새 토큰 추가 (기존 키 보존)
- 충돌 시 사용자 confirm

### Step 5: design_state.yaml 업데이트

`phases.tokens: done` + `tokens_path: <실제 파일 경로>`.

## Output

- `02_tokens/tokens.md` — 결정 사유 + 토큰 값
- 프로젝트 루트의 `tokens.css` 또는 `tailwind.config.ts` (사용자 confirm 후 작성·확장)
- `_internal/tokens_backup_<date>.css` (기존 덮어쓰기 시)

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
