# 실제 토큰 파일 템플릿

스택에 따라 둘 중 하나 또는 둘 다 작성.

## Option A: tokens.css (CSS variables)

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

## Option B: tailwind.config.ts

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
