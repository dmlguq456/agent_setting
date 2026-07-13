# tokens.md worked exemplar

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
