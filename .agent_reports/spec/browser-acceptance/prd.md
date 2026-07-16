# browser-acceptance — Spec (PRD)

> mode: **library** (하네스 인프라 — 실행 중인 앱의 브라우저 acceptance 검증 공통 primitive) · 작성 2026-07-16 · v1
> 컴포넌트: `agent_setting` repo의 **browser acceptance harness library** (`tools/browser-acceptance/`). QA/verification worker가 실행 중인 앱을 브라우저로 검수할 때 사용하는 공통 도구 계약. `spec/prd.md`(Unified Memory System)·`spec/stage-dispatch/`·`spec/agent-fleet-dashboard/`와 무관한 독립 청사진 — 이 폴더(`spec/browser-acceptance/`)가 자체 SoT.
> 입력(1순위 근거):
> - **운영 진단 (2026-07-16, 사용자 보고 항목 6)**: v94-reading-face 사이클 D3 브라우저 검증에서 도구-급 실수 4계열이 순차 재현 — ① CJS 환경 top-level await 사용, ② 접힌 Hubs 그룹을 열지 않고 검사, ③ whole-page selector로 read-only 판정, ④ URL 변경 뒤 reader mount를 기다리지 않음. (중복 `<main>`·scoped Axe contrast 실패 2건은 실제 제품 결함으로 별개.) 수용 기준 원문: "CJS-safe entry, URL+root mount wait, scoped selectors, disclosure open helper, Axe/console/screenshot/result JSON을 공통화해야 합니다."
> - **현행 도구 census (2026-07-16, 본 세션)**: `tools/design-mcp/console-check.mjs`는 로컬 HTML 파일 전용 post-write hook(디자인 산출물 console 오류 감지)이며 실행 중 앱 URL acceptance와 용도가 다름. playwright 의존성(`tools/design-mcp/package.json` ^1.49.0)은 해석 fallback으로 재사용 가능. 중복 재발명 없음 확인.
> 본 문서는 청사진(PRD). 구현은 autopilot-code (산출물 `plans/`).

## 0. 한 줄

**QA worker가 매번 즉석 브라우저 스크립트를 짜다 반복하는 도구-실수를, 주입식(dependency-injected) CJS primitive 라이브러리로 제거한다.** 라이브러리는 판정하지 않는다 — 증거(콘솔·Axe·스크린샷·결과 JSON)를 결정론적으로 수집하고, 판정은 worker/conductor의 의미 구간에 남는다.

## 1. 설계 결정 (locked) — BA-1~6

- **BA-1 (CJS-safe entry)**: 라이브러리는 CommonJS(`.cjs`)로 작성하고 top-level await를 금지한다. 모든 async는 export된 함수 내부에만 존재한다. `require()` 즉시 사용 가능 — 진단 ①의 실패 계급을 원천 차단.
- **BA-2 (0-dependency, 주입식)**: 라이브러리 자체는 외부 의존성 0. Playwright `page`와 axe-core 소스는 호출자가 주입한다. 해석 헬퍼 `resolvePlaywright()`/`resolveAxeSource()`는 제공하되(호출 cwd `node_modules` → `tools/design-mcp/node_modules` 순) 실패 시 명시 오류로 닫는다 — 하네스 repo에 node 의존성 트리를 추가하지 않는다.
- **BA-3 (primitive 집합)**: ① `gotoAndWaitMount(page, url, rootSelector, opts)` — URL 이동 후 root mount 요소의 attach+visible을 명시 대기(진단 ④). ② `scoped(page, scopeSelector)` — 이후 모든 질의가 scope 하위로 강제되는 locator 래퍼; whole-page 질의 API를 노출하지 않음(진단 ③). ③ `openDisclosure(page, triggerSelector, opts)` — 접힌 그룹(aria-expanded=false)을 멱등하게 열고 expand 완료를 대기(진단 ②). ④ `captureConsole(page)` — pageerror/console error 수집기(시작·중지·수확). ⑤ `runScopedAxe(page, {scope, axeSource})` — 주입된 axe-core를 scope 한정으로 실행. ⑥ `writeEvidence(dir, result)` — 스크린샷 경로·결과 JSON을 고정 스키마로 기록.
- **BA-4 (결과 계약)**: 단일 `result.json` 스키마 — `{schema_version, url, scope, started_at, finished_at, checks: [{id, verdict, detail}], console_errors: [], axe: {violations: []}, screenshots: [], verdict}`. `verdict ∈ {PASS, FAIL}`은 checks/console/axe의 결정론 집계(오류 0 = PASS)이며, 의미 판정(개별 check의 구성)은 호출자 소유. code-test/code-report가 이 파일을 증거로 소비한다.
- **BA-5 (검증 2단)**: fake-page 단위 테스트(node `--test`, 브라우저 불요)가 필수 게이트 — 각 primitive의 대기·scope·멱등·수집·스키마 계약을 검증. 실브라우저 통합 acceptance(실제 앱 URL 대상 6 primitive 완주)는 라이브러리를 처음 소비하는 앱 사이클에서 실행하고 그 결과를 본 spec의 v1 완료 증거로 회수한다(명시 이월).
- **BA-6 (경계)**: 이 라이브러리는 검증 실행 도구이지 dispatch/stage 계약이 아니다 — stage-dispatch spec과 표면을 공유하지 않는다. 디자인 산출물(로컬 HTML) 검사는 계속 design-mcp 소관.

## 2. acceptance criteria (진단 6 수용 기준 매핑)

1. CJS-safe entry: `node -e "require('./tools/browser-acceptance')"`가 부작용·top-level await 없이 성공.
2. URL+root mount wait: mount 지연 fixture에서 `gotoAndWaitMount`가 mount 전 반환하지 않고, timeout 시 구조화 오류.
3. scoped selectors: `scoped()` 밖의 whole-page 질의 경로가 API에 없음; scope 밖 요소는 검사에 잡히지 않음(fake-page 검증).
4. disclosure open helper: 접힘 상태에서 1회 열고, 이미 열린 상태에서 no-op(멱등).
5. 공통화: console 수집·scoped Axe·screenshot·result JSON이 BA-4 스키마로 한 경로에서 출력; 스키마 필드 결손 시 fail-closed.
6. 단위 테스트(node --test) 전부 통과 + 실브라우저 통합은 첫 소비 사이클 회수 조건으로 기록.

## 3. 의미↔규칙 경계 (DESIGN_PRINCIPLES §0.7)

- **규칙 구간(코드)**: mount 대기·scope 강제·멱등 open·수집·스키마 검증·결정론 verdict 집계.
- **의미 구간(worker/사람)**: 어떤 check를 구성할지, FAIL의 제품-결함 여부 해석, 접근성 위반의 심각도 판정.
