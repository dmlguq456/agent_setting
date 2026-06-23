# 축 2 — 생성 산출물의 sandboxed 라이브 프리뷰 (OSS 선행조사)

> 목표: LLM 이 생성한 HTML/JSX 를 안전하게 iframe 에 스트리밍 렌더 + 핫리로드 하는 패턴. ("프롬프트→라이브 캔버스"의 프리뷰 면)
> 렌즈: local-first · BYOK · 기존 하네스 재사용 · 디스크=상태 · Next.js 임베드 · 라이선스 명확(MIT/Apache 선호).
> 모든 메타데이터는 GitHub API 실측 (조사일 2026-06-23). 못 본 경로는 지어내지 않음.
> 기준선(중복 서술 금지): **OD** = nexu-io/open-design (srcdoc sandboxed iframe), **OCD** = opencoworkai/open-codesign (Electron 렌더 + boolean parity).

---

## 후보 카드

### 1. vercel/chatbot (구 vercel/ai-chatbot)
- **레포**: [vercel/chatbot](https://github.com/vercel/chatbot) — ⭐20,517 · License NOASSERTION(커스텀 license 파일) · push 2026-05-18 · archived=false
- **한 줄 정체**: Vercel 공식 Next.js AI 챗봇 템플릿. AI SDK 기반 "artifacts" UI 의 레퍼런스 구현.
- **격리 방식**: ⚠️ **HTML iframe 프리뷰 없음**. `artifacts/` 4종(code/text/image/sheet) 중 code 는 iframe 이 아니라 **Pyodide(브라우저 Python WASM)** 로 직접 실행, text 는 ProseMirror 에디터. 즉 "생성 HTML 을 sandbox iframe 에 렌더"하는 면은 이 레포에 _구현돼 있지 않다_.
- **JSX 트랜스파일 경로**: 없음 — JSX/HTML 캔버스가 아니라 Python 코드 실행기.
- **스트리밍 중 부분 렌더**: ✅ 강력. `artifacts/code/client.tsx` 의 `onStreamPart` 가 `data-codeDelta` 스트림 파트를 받아 토큰 흐름 중 콘텐츠를 점진 갱신(300자 넘으면 아티팩트 패널 자동 노출). 이 **스트리밍 델타 → artifact state → 부분 렌더 배선**이 핵심 lift 대상.
- **핫리로드 메커니즘**: 버전드 콘텐츠 교체(에디터/Pyodide 재실행). iframe HMR 아님.
- **로컬 동작 여부**: ✅ 완전 로컬 (Pyodide CDN 만 외부). 클라우드 sandbox 불필요.
- **lift할 구체 모듈/파일**: `artifacts/code/client.tsx` 의 `onStreamPart` 스트리밍 델타 패턴 · `artifacts/actions.ts` · artifact kind 추상화(`code/text/image/sheet` 폴더 구조 = "kind 별 client/server 핸들러" 패턴). **HTML/JSX 프리뷰 자체는 여기서 못 가져옴.**
- **적합도**: **중** — 스트리밍 부분 렌더 배선·artifact 추상화는 가져올 가치 큼. 단 우리 축의 본질인 "sandboxed HTML/JSX iframe"은 부재.
- **채택 리스크**: license NOASSERTION(LICENSE 파일 직접 확인 필요) · Next.js/AI SDK 강결합 · 우리가 원하는 프리뷰 면은 직접 구현해야 함.
- **OD/OCD 대비 새로 얻는 것**: OD/OCD 의 정적 프리뷰에 없는 **"토큰 스트리밍 → 부분 렌더" 배선**(onStreamPart 델타 패턴)을 프로덕션급으로 제공.

### 2. e2b-dev/E2B (+ e2b-dev/fragments)
- **레포**: [e2b-dev/E2B](https://github.com/e2b-dev/E2B) — ⭐12,685 · Apache-2.0 · push 2026-06-23 · archived=false / [e2b-dev/fragments](https://github.com/e2b-dev/fragments) — ⭐6,326 · Apache-2.0 · push 2026-06-11
- **한 줄 정체**: AI 생성 코드를 격리 실행하는 sandbox 인프라(SDK) + fragments = 그 위에서 "프롬프트→앱" 전체를 보여주는 Next.js 데모.
- **격리 방식**: **서버사이드 Firecracker microVM**(하드웨어 가상화, ~150ms 부팅, 3-5MB 오버헤드). 브라우저 sandbox 가 아니라 _원격 컨테이너_. fragments 는 그 sandbox 의 결과 URL 을 UI 에 표시.
- **JSX 트랜스파일 경로**: sandbox 안에서 실제 `npm`/Vite 빌드 실행 (진짜 dev 서버). 브라우저 트랜스파일 아님.
- **스트리밍 중 부분 렌더**: ✗ — 코드를 전부 받아 sandbox 에 쓰고 빌드/실행하는 모델. 토큰 흐름 중 점진 렌더 아님.
- **핫리로드 메커니즘**: sandbox 안 실제 dev 서버의 HMR (full fidelity).
- **로컬 동작 여부**: ⚠️ **클라우드 의존 강함**. 공식 경로는 `E2B_API_KEY`(e2b.dev 가입) 필수. self-host 는 `e2b-dev/infra`(self-host.md) 로 가능하나 Nomad/Consul/KVM 등 무거운 인프라 구축 필요. local-first 렌즈에 **크게 감점**.
- **lift할 구체 모듈/파일**: fragments 의 sandbox 호출 흐름(`lib/templates.json` 기반 템플릿 선택) · E2B SDK 의 sandbox lifecycle API. (단 우리 모델엔 과한 무게.)
- **적합도**: **하** — 풀 fidelity·진짜 보안 격리는 최강이나 클라우드 microVM 의존이 local-first·디스크=상태 철학과 정면 충돌.
- **채택 리스크**: API key/과금 또는 self-host 인프라 무게 · 종속성 매우 큼 · "디자인 캔버스 프리뷰"엔 오버킬.
- **OD/OCD 대비 새로 얻는 것**: 진짜 격리(Firecracker)와 실제 빌드 fidelity — 그러나 그 대가가 클라우드 의존이라 우리 축엔 부적합 (참고용 상한선).

### 3. codesandbox/sandpack
- **레포**: [codesandbox/sandpack](https://github.com/codesandbox/sandpack) — ⭐6,167 · Apache-2.0 · push 2025-04-24 · archived=false
- **한 줄 정체**: 브라우저 내 라이브 코드 편집·실행 컴포넌트 툴킷(CodeSandbox 번들러 기반).
- **격리 방식**: ✅ **별도 origin 의 bundler iframe**. `sandpack-client` 가 부모 컨텍스트와 bundler iframe 간 postMessage 핸드셰이크 중재. bundler URL 기본 `${version}-sandpack.codesandbox.io` 인데 **`bundlerURL` 옵션으로 self-host 가능**(보안 origin 분리 유지하며 우리 인프라에 배치). 이 축의 정석.
- **JSX 트랜스파일 경로**: **브라우저 내 번들링**(CodeSandbox 번들러, multi-file). 서버 불필요. (Nodebox 도 별도 제공하나 핵심 프리뷰는 in-browser 번들러.)
- **스트리밍 중 부분 렌더**: △ 직접 토큰 스트리밍 API 는 없음. 단 `updateSandbox()` 를 델타마다 호출하면 점진 갱신 효과 가능(파일 단위). vercel/chatbot 의 onStreamPart 와 조합하면 됨.
- **핫리로드 메커니즘**: ✅ `updateSandbox()` 가 변경 파일 자동 감지 후 HMR — 라이브러리가 기본 제공.
- **로컬 동작 여부**: ✅ 번들링은 완전 in-browser. bundler iframe 만 별도 origin(self-host 가능) — 클라우드 불필요. local-first 호환.
- **lift할 구체 모듈/파일**: `@codesandbox/sandpack-react`(UI·`SandpackPreview`) · `@codesandbox/sandpack-client`(`loadSandpackClient`, `updateSandbox`, `bundlerURL`) · self-host bundler(`sandpack-bundler`).
- **적합도**: **상** — multi-file 번들 + 핫리로드 + origin 분리 격리를 라이브러리로 제공. self-host 가능해 local-first 와 양립. 우리 캔버스에 가장 곧장 임베드.
- **채택 리스크**: push 2025-04(다소 정체) · 번들러가 무겁고(MB 급) origin 분리 self-host 운영 부담 · React/Vue 등 SPA 프리뷰엔 강하나 단순 HTML 1장엔 과함.
- **OD/OCD 대비 새로 얻는 것**: OD 의 단순 srcdoc 대비 **multi-file 번들·의존성 resolve·HMR 을 라이브러리로** + **별도 origin 격리**(srcdoc 보다 강한 보안 경계).

### 4. WebContainers (@webcontainer/api, stackblitz)
- **레포**: [stackblitz/webcontainer-core](https://github.com/stackblitz/webcontainer-core) — ⭐4,610 · MIT(레포) · push 2025-04-22 · archived=false. ⚠️ 단 **런타임 자체는 프로퍼티어리**(레포는 docs/래퍼; 실제 WASM Node 런타임 비공개).
- **한 줄 정체**: 브라우저 안에서 Node.js 를 통째로 돌리는 WASM 런타임(실제 npm install·dev 서버).
- **격리 방식**: 브라우저 WASM 가상 파일시스템 + service worker. 프리뷰는 service worker URL 을 iframe 으로. **COOP/COEP cross-origin isolation 헤더 필수**(임베드 제약 큼).
- **JSX 트랜스파일 경로**: sandbox 안 실제 Vite/번들러 실행 — full fidelity, 브라우저 내.
- **스트리밍 중 부분 렌더**: ✗ — 파일 mount 후 빌드 모델.
- **핫리로드 메커니즘**: ✅ 안에서 실제 dev 서버 HMR.
- **로컬 동작 여부**: 브라우저에서 돌지만 **런타임 비공개 + 상용 프로덕션 유료 라이선스 필요**(POC 만 면제). "always free for OSS"라도 우리가 _상용 앱_ 이면 StackBlitz 라이선스 계약 필요.
- **lift할 구체 모듈/파일**: `@webcontainer/api`(`WebContainer.boot`, `mount`, `spawn`, `on('server-ready')`). 코드는 lift 불가(런타임 클로즈드) — API 사용만.
- **적합도**: **하** — 기술은 최강이나 (a) 런타임 프로퍼티어리 (b) 상용 유료 라이선스 (c) COOP/COEP 헤더 강제. 라이선스 명확·local-first·재사용 렌즈에서 탈락.
- **채택 리스크**: 라이선스 비용·벤더 락인(런타임 비공개)·헤더 제약. 신뢰는 높으나 BYOK/오픈 철학과 충돌.
- **OD/OCD 대비 새로 얻는 것**: 브라우저 내 _진짜 Node 런타임_(SSR·서버 프레임워크까지) — 단 클로즈드+유료라 우리 축에선 채택 불가, 상한선 참고만.

### 5. LLM artifacts/canvas 오픈 구현군
- **레포들**:
  - [langchain-ai/open-canvas](https://github.com/langchain-ai/open-canvas) — ⭐5,471 · MIT · **archived=true** · push 2026-02
  - [assistant-ui/assistant-ui](https://github.com/assistant-ui/assistant-ui) — ⭐10,748 · MIT · push 2026-06-23(활발)
  - [13point5/open-artifacts](https://github.com/13point5/open-artifacts) — ⭐305 · MIT · **archived=true** + 별도 [open-artifacts-renderer](https://github.com/13point5/open-artifacts-renderer)
  - [CopilotKit/OpenGenerativeUI](https://github.com/CopilotKit/OpenGenerativeUI) — ⭐1,417 · MIT · push 2026-06
- **한 줄 정체**: Claude artifacts/canvas 의 오픈 클론·생성 UI 프레임워크군.
- **격리 방식**: 갈림.
  - **open-artifacts(-renderer)**: 별도 Next.js 앱을 **iframe 으로 임베드**(다른 origin), 부모-자식 **postMessage** 통신 — 우리 축에 직접 부합한 sandbox 패턴. (`NEXT_PUBLIC_ARTIFACT_RENDERER_URL` 로 렌더러 origin 분리.)
  - **assistant-ui**: iframe 이 아니라 **JSON spec + 컴포넌트 allowlist**(`MessagePrimitive.GenerativeUI`) — 임의 HTML/JSX 를 실행하지 않고 _허용된 컴포넌트만_ 트리로 렌더. 격리 모델이 근본적으로 다름(코드 실행 X = 가장 안전하나 자유도 낮음).
  - **CopilotKit/OpenGenerativeUI**: 일부 시각화를 sandboxed iframe 으로.
- **JSX 트랜스파일 경로**: open-artifacts-renderer = **babel(브라우저)** 로 문자열 코드 → React 컴포넌트(`getReactComponentFromCode`). assistant-ui = 트랜스파일 없음(allowlist 매핑).
- **스트리밍 중 부분 렌더**: open-artifacts-renderer = 새 컴포넌트 코드 수신 시 재평가·재렌더(델타 단위). assistant-ui = 스트리밍 친화(메시지 파트).
- **핫리로드 메커니즘**: 코드 문자열 교체 → 재evaluate(babel). 번들러 HMR 아님.
- **로컬 동작 여부**: ✅ 모두 로컬 가능. open-artifacts/open-canvas 는 **archived**(유지보수 정지) 주의.
- **lift할 구체 모듈/파일**: open-artifacts-renderer 의 **iframe + postMessage + `getReactComponentFromCode`(babel) 렌더 루프**(우리 캔버스 프리뷰의 직접 청사진) · assistant-ui 의 `MessagePrimitive.GenerativeUI`(allowlist 보안 모델 — 옵션 B).
- **적합도**: **중상** — open-artifacts-renderer 의 "iframe+postMessage+babel 평가"는 우리 축의 _정확한_ 미니멀 패턴. 단 archived(305⭐)라 코드 흡수 후 fork/유지 전제. assistant-ui 는 활발하나 allowlist 모델이라 자유 HTML/JSX 캔버스엔 부분 적합.
- **채택 리스크**: open-artifacts archived(직접 의존 X, 패턴만 흡수) · assistant-ui 는 라이브러리 무게·allowlist 제약 · babel 평가 = XSS 경계를 iframe origin 분리로 반드시 봉인해야.
- **OD/OCD 대비 새로 얻는 것**: OD 의 srcdoc 정적 프리뷰 대비 **JSX(React 컴포넌트) 동적 평가 + 델타 재렌더 루프**(open-artifacts-renderer) — 즉 "정적 HTML"을 넘어 "인터랙티브 컴포넌트 캔버스".

### 6. val.town / townie (오픈 부분)
- **레포**: [val-town (org)](https://github.com/val-town) — 24 repos(CodeMirror-TS·docs·blog 등 컴포넌트 오픈). Townie 본체는 val.town 플랫폼 위(`valdottown/Townie`, remix 가능)에 존재 — **독립 self-host GitHub 레포·라이선스 미확인**(플랫폼 종속). 커뮤니티: [404wolf/valfs](https://github.com/404wolf/valfs), [pomdtr/vt](https://github.com/pomdtr/vt).
- **한 줄 정체**: TypeScript 조각을 즉시 배포하는 클라우드 + Townie(Claude 기반 AI 에디터).
- **격리 방식**: 프리뷰 = **val.town 인프라에 즉시 배포된 라이브 URL**(branch-preview-URL, ~100ms) 를 임베드. 즉 _플랫폼 서버사이드 배포_ 모델.
- **JSX 트랜스파일 경로**: val.town 서버 런타임(Deno 기반) — 플랫폼 종속.
- **스트리밍 중 부분 렌더**: ✗(배포 단위).
- **핫리로드 메커니즘**: 매 edit 즉시 재배포(라이브 URL 갱신).
- **로컬 동작 여부**: ✗ — 프리뷰가 **val.town 클라우드 배포에 종속**. local-first 불가.
- **lift할 구체 모듈/파일**: 오픈된 주변부(CodeMirror-TS 통합)만 부분 참고. 프리뷰 메커니즘은 플랫폼 종속이라 lift 불가.
- **적합도**: **하** — 프리뷰의 본질이 클라우드 배포라 local-first·디스크=상태 렌즈에 부적합.
- **채택 리스크**: 플랫폼 락인 · 핵심 lift 불가 · 라이선스 불명.
- **OD/OCD 대비 새로 얻는 것**: 사실상 없음(클라우드 배포 모델은 우리가 피하는 방향). 참고 가치 낮음.

### 7. (보너스) babel-standalone + srcdoc iframe 직접 패턴
- **레포**: [webllm/renderify](https://github.com/webllm/renderify) — ⭐23 · MIT · push 2026-06-17 · archived=false (이 패턴의 _가장 발전된_ OSS 예시). 보조: [babel/babel-standalone](https://github.com/babel/babel-standalone) — archived(Babel monorepo 로 이전, npm `@babel/standalone` 가 현행).
- **한 줄 정체**: Renderify = "LLM 생성 JSX/TSX 를 빌드·서버 없이 브라우저에서 즉시 트랜스파일·sandbox·렌더"하는 런타임 엔진.
- **격리 방식**: ✅ **3종 sandbox 모드 — Web Worker / sandboxed iframe / ShadowRealm** 자동 폴백. (sandbox 끄면 host DOM 직접 렌더도 가능.) iframe sandbox 가 기본 경계.
- **JSX 트랜스파일 경로**: ✅ **Babel Standalone(브라우저)** + `es-module-lexer` 로 import 추출 → **JSPM CDN** 으로 bare specifier resolve → **blob URL 로 import 재작성** 후 in-browser 실행. (esbuild-wasm 아님, babel 기반.)
- **스트리밍 중 부분 렌더**: ✅ **명시 지원** — "LLM 이 코드 생성 중에도 progressive preview 갱신", FNV-1a 해시로 변경 감지(불필요 재렌더 억제). 우리 축의 _부분 렌더_ 요구에 정확히 부합.
- **핫리로드 메커니즘**: 해시 기반 변경 감지 → 변경분만 재평가·재렌더.
- **로컬 동작 여부**: ✅ **완전 로컬·zero build·zero server**(CDN 의존만). local-first 최적합.
- **lift할 구체 모듈/파일**: Renderify 핵심 — babel-standalone 트랜스파일 + es-module-lexer import 추출 + JSPM blob URL 재작성 + 3-mode sandbox + FNV-1a 스트리밍 델타. (코드 lift 또는 패턴 모사.)
- **적합도**: **상(개념) / 중(성숙도)** — 우리 축의 모든 요구(브라우저 트랜스파일·iframe sandbox·스트리밍 부분 렌더·zero server)를 _한 곳에서_ 충족. 다만 ⭐23 로 신생.
- **채택 리스크**: 성숙도 낮음(⭐23, 1인 프로젝트 추정·테스트/프로덕션 검증 불명) · JSPM CDN 의존(오프라인·BYOK 환경서 import resolve 끊김 가능 → 로컬 import map 으로 대체 필요) · babel 평가 보안은 sandbox origin 봉인 전제. **코드 직접 의존보다 패턴 흡수 + 자체 구현 권장.**
- **OD/OCD 대비 새로 얻는 것**: OD 의 정적 srcdoc 대비 **JSX 트랜스파일 + 의존성 CDN resolve + 스트리밍 progressive preview** 를 한 경량 엔진에 결합 — "프롬프트→라이브 JSX 캔버스"의 정확한 미니멀 레시피.

---

## 축 2 비교표

| 후보 | ⭐stars | license | 격리 방식 | JSX 트랜스파일 | 스트리밍 부분렌더 | 로컬가능 | 적합도 |
|---|---|---|---|---|---|---|---|
| vercel/chatbot | 20,517 | NOASSERTION | (HTML iframe 없음; Pyodide·ProseMirror) | 없음 | ✅ onStreamPart 델타 | ✅ | 중 |
| e2b E2B/fragments | 12,685/6,326 | Apache-2.0 | 서버 Firecracker microVM | sandbox 내 실제 빌드 | ✗ | ✗(클라우드 의존) | 하 |
| codesandbox/sandpack | 6,167 | Apache-2.0 | 별도 origin bundler iframe(self-host 가능) | 브라우저 번들러(multi-file) | △(updateSandbox 조합) | ✅ | 상 |
| WebContainers | 4,610(런타임 클로즈드) | MIT(래퍼)/상용유료 | WASM Node + SW iframe(COOP/COEP) | sandbox 내 실제 빌드 | ✗ | △(유료·헤더 제약) | 하 |
| open-artifacts-renderer | 305(archived) | MIT | iframe + postMessage(별 origin) | babel(브라우저) | ✅ 컴포넌트 델타 재평가 | ✅ | 중상 |
| assistant-ui | 10,748 | MIT | JSON spec + 컴포넌트 allowlist(코드 실행 X) | 없음(매핑) | ✅ 메시지 파트 | ✅ | 중 |
| val.town/townie | (org 24 repos) | 불명/플랫폼종속 | 클라우드 라이브 URL 배포 | 플랫폼 서버 | ✗ | ✗ | 하 |
| **webllm/renderify** | 23 | MIT | Worker/iframe/ShadowRealm 3-mode | **babel-standalone(브라우저)** + JSPM blob | **✅ progressive(FNV-1a)** | ✅ | 상(개념)/중(성숙도) |

---

## 축 2 단독 1픽 + 이유

**1픽: `codesandbox/sandpack` 을 기반 라이브러리로, `webllm/renderify` 의 패턴(+vercel/chatbot 의 onStreamPart 배선)을 흡수.**

- 우리 축의 본질("sandboxed iframe + 핫리로드 + 로컬")을 **검증된 라이브러리로** 충족하는 건 Sandpack 뿐: 별도 origin bundler iframe(srcdoc 보다 강한 격리) + multi-file 번들 + `updateSandbox()` HMR + **`bundlerURL` self-host 로 local-first 양립**. Apache-2.0 으로 라이선스도 명확.
- 다만 Sandpack 은 _스트리밍 부분 렌더_ 가 약하다. 그 한 조각은 **vercel/chatbot `onStreamPart` 델타 패턴**(토큰 흐름 → artifact state → updateSandbox 호출)으로 메운다.
- 단순 HTML 1장·경량 캔버스 또는 Sandpack 번들러가 과하다고 느껴지면, **webllm/renderify 패턴**(babel-standalone + iframe sandbox + progressive preview)을 자체 구현해 경량 경로를 둔다 — renderify 코드 직접 의존은 ⭐23 성숙도 때문에 비권장(패턴만 흡수).
- e2b/WebContainers/val.town 은 fidelity 는 높아도 클라우드 의존·프로퍼티어리·유료 라이선스로 local-first·BYOK·오픈 렌즈에서 탈락(상한선 참고용).

**축 2 핵심 takeaway: "Sandpack(별 origin iframe·번들·HMR·self-host 가능)을 골격으로, 스트리밍 부분 렌더는 vercel/chatbot onStreamPart 델타 패턴으로, 경량 HTML/JSX 경로는 renderify식 babel-standalone+sandboxed iframe 으로 — 클라우드 sandbox(e2b/WebContainer/val.town)는 local-first·라이선스 렌즈에서 전원 탈락."**
