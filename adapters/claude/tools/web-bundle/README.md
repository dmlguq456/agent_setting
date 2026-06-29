# web-bundle — production급 단일 HTML 번들 레시피

> **무엇**: 멀티파일로 _제대로 빌드_(Vite + TS + Tailwind + shadcn/ui)한 webapp/ui 를 **self-contained 단일 `index.html`** 로 inline. 공개 `web-artifacts-builder` 계열 레시피의 온프레미스 재구현.
> **왜 별도 경로**: 디자인팀에는 이미 단일파일 산출 2 경로가 있다 — (a) `design-components` Step 4b 의 **CDN standalone**(`https://cdn.tailwindcss.com` + esm.sh, 0-build, _dev-grade_), (b) `convert.mjs bundle`(기존 HTML 의 에셋 inline). 본 레시피는 _세 번째_ — **production-grade 빌드**(실제 Tailwind purge + 진짜 shadcn 컴포넌트 + Radix, CDN 의존 0). 진지한 앱 UI·배포 후보 산출에만.

## 언제 무엇

| 경로 | 충실도 | 빌드 | 자리 |
|---|---|---|---|
| CDN standalone (Step 4b) | dev-grade (CDN Tailwind) | 0 | 빠른 미리보기·mockup·diagram·slide |
| `convert.mjs bundle` | 기존 산출물 inline | 0 | 이미 만든 preview.html 오프라인화 |
| **web-bundle (본 레시피)** | **production** (real Tailwind/shadcn) | Vite | 배포 후보 webapp·ui, design-system 정합 필요 |

## 스택 (web-artifacts-builder parity)

React 18 + TypeScript · Vite · Tailwind CSS 3.4.1 · shadcn/ui(40+) · Radix UI · path alias `@/`.

## 절차

```bash
# 1. 프로젝트 (없으면 생성). spec/design 의 tokens.css·tailwind.config.ts 를 그대로 주입.
npm create vite@latest <name> -- --template react-ts
cd <name> && npm i && npm i -D tailwindcss@3.4.1 postcss autoprefixer && npx tailwindcss init -p
#  shadcn/ui: npx shadcn@latest init  → 필요한 컴포넌트만 add
#  디자인 토큰: design 폴더의 tokens.css / tailwind.config.ts 복사 (design-system 정합)

# 2. 단일파일 번들 — vite-plugin-singlefile (모든 JS/CSS inline → dist/index.html 한 파일)
npm i -D vite-plugin-singlefile
#  vite.config.ts 에 plugin 추가 (아래 snippet)
npx vite build
#  → dist/index.html = self-contained 단일 파일 (외부 의존 0, 브라우저로 바로 열림)

# 3. 디자인 폴더로 산출
cp dist/index.html <design_dir>/05_handoff/exports/<name>.bundle.html
```

`vite.config.ts` snippet:
```ts
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import { viteSingleFile } from "vite-plugin-singlefile"
export default defineConfig({ plugins: [react(), viteSingleFile()], build: { cssCodeSplit: false, assetsInlineLimit: 100000000 } })
```

> 대안(web-artifacts-builder 원본): Parcel + `parcel-resolver-tspaths` + `html-inline`(`.parcelrc` 로 `@/` alias) — 동일 결과. vite-plugin-singlefile 이 더 단순해 본 레시피의 default.

## 검증 (필수 — `_design_rules.md` 시각 자가검증 루프)

번들 후 **반드시** adapter visual harness 로 `preview(dist/index.html)` → `getConsoleLogs`(에러 0) → `screenshot` → `view_image` 또는 동등 검증을 실행한다. 빌드가 통과해도 _렌더가 깨질 수 있다_ — 본 것으로만 완료.
