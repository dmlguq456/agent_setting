# 축 4 — 정의→manifest 허브 & 디자인 taste/검증 레이어

> 조사일 2026-06-23 · 메타데이터 실측 (GitHub API; rate-limit 시 WebFetch/WebSearch 교차).
> 렌즈: local-first · BYOK · 기존 하네스 재사용 · 디스크=상태 · 앱 임베드(통째 채택 X) · 라이선스 MIT/Apache · **검증=결정론(boolean) 게이트**.
> 기준선(중복 서술 금지): nexu-io/open-design(agents.ts 정의→어댑터 + sandboxed iframe) · opencoworkai/open-codesign(boolean parity 검증 = 결정론 게이트 선례). 각 카드에 **"OD/OCD 대비 새로 얻는 것"** 1줄.

베이스라인 메모: (a)군은 내 기존 `sync-skills` 스킬(skills/agents 정의 변경 감지 → README 대시보드 동기화)이 이미 절반을 한다. 후보는 "그 위에 lift할 인덱싱 스키마·렌더 카탈로그"로만 평가. (b)군은 내 디자인 하네스가 이미 console-error gate(`tools/design-mcp/console-check.mjs` exit 2)와 verifier subagent를 가진다 — 후보는 "그 루프에 박을 결정론 boolean 부품(스샷 diff·layout 안깨짐)"으로만 평가.

---

## (a) 정의 → manifest / 카탈로그

### 1. Storybook
- **레포**: storybookjs/storybook (https://github.com/storybookjs/storybook) — ⭐90,414 · MIT · push 2026-06-23 · archived=False
- **한 줄 정체**: 컴포넌트 워크벤치 — `*.stories.*` 파일을 인덱싱해 `index.json`(구 stories.json) manifest로 방출, UI가 그 manifest로 카탈로그 렌더.
- **manifest 방출 방식**: 빌드 시 stories indexer가 모든 story 파일을 스캔 → `index.json`(엔트리별 id·title·importPath·tags) 생성. 이게 정확히 "파일 기반 정의 → 구조화 manifest → UI 렌더" 패턴의 레퍼런스 구현.
- **CI/headless**: storybook build는 정적 산출물(헤드리스). 인덱싱 자체는 브라우저 불필요.
- **에이전트 루프 결합 사례**: 직접 LLM 루프 선례는 약함(워크벤치 본체). 단 test-runner(아래 8)가 게이트 역할.
- **lift할 구체 모듈/파일**: `code/core/src/core-server/utils/StoryIndexGenerator` 류 인덱서의 **스키마 모양**(id/title/importPath/tags 평탄 엔트리 + `v` 버전 필드)을 sync-skills가 방출할 `manifest.json` 스키마로 모사. 코드가 아니라 **JSON shape**만 lift.
- **적합도**: 중 — 패턴은 정확히 맞지만 엔진 통째는 과대. 스키마만 차용.
- **채택 리스크**: 통째 임베드는 무겁다(monorepo·빌더 의존). lift는 스키마 카피라 리스크 0.
- **OD/OCD 대비 새로 얻는 것**: 정의 인덱싱의 **검증된 manifest 스키마 형태**(평탄 엔트리 + 버전 필드 + tags) — OD의 agents.ts는 어댑터지 카탈로그 인덱스 스키마는 아님.

### 2. Style Dictionary
- **레포**: style-dictionary/style-dictionary (https://github.com/style-dictionary/style-dictionary) — ⭐4,705 · Apache-2.0 · push 2026-06-21 · archived=False  (구 `amzn/style-dictionary`는 이 org로 redirect)
- **한 줄 정체**: 토큰 정의(JSON/JSON5) → 다중 포맷(css·scss·ts·iOS·android…) manifest를 build로 방출하는 build system.
- **manifest 방출 방식**: source 토큰 트리(category/type/item 계층) → transform → format → platform별 산출. "단일 정의를 여러 타깃 manifest로 fan-out"의 정석.
- **CI/headless**: 순수 node CLI, 헤드리스 완전.
- **에이전트 루프 결합 사례**: 직접 LLM 루프 X. 단 디자인 토큰을 코드로 떨구는 단계라 maker→handoff 자리에 잘 붙음.
- **lift할 구체 모듈/파일**: 내 산출물이 토큰 트리가 아니라 skill/agent 정의라 본체는 부적합. 차용할 건 **transform→format→platform fan-out 아키텍처 개념**(하나의 정의 → N개 렌더 타깃) 정도.
- **적합도**: 하 — 토큰 도메인 특화라 skills/agents 허브엔 의미 매핑이 약함. (디자인 토큰을 따로 다룰 때만 중.)
- **채택 리스크**: 임베드 가벼움(node lib)이나 use-case 불일치.
- **OD/OCD 대비 새로 얻는 것**: 단일 정의 → 다중 포맷 fan-out 개념(다만 내 허브엔 약한 매치).

### 3. anthropic frontend-design plugin (claude-plugins-official)
- **레포(실재 확인)**: anthropics/claude-code → `plugins/frontend-design/` (https://github.com/anthropics/claude-code/tree/main/plugins/frontend-design) · claude-plugins-official 마켓플레이스 등재. (plugin 단독 stars 무의미 — 모노레포 동거.)
- **한 줄 정체**: distinctive 프런트엔드 생성용 **skill-only 플러그인** — `.claude-plugin/plugin.json`(메타) + `skills/frontend-design/`(SKILL.md) 구조, commands·agents·hooks 없음.
- **manifest 방출 방식**: 자기가 manifest를 *방출*하진 않음. 대신 **플러그인 manifest 규격 자체**가 레퍼런스 — `.claude-plugin/plugin.json`(name·version·source) + marketplace `marketplace.json`(plugin 목록). 즉 "정의 폴더 → 표준 manifest"의 *스키마 표준*.
- **CI/headless**: 해당 없음(정의 패키지).
- **에이전트 루프 결합 사례**: 본질이 에이전트(Claude Code)용 정의 — 루프 결합이 기본값.
- **lift할 구체 모듈/파일**: `.claude-plugin/plugin.json` + `marketplace.json`의 **필드 스키마**(name/version/description/source/components). sync-skills가 방출할 manifest를 *이 공식 규격에 맞추면* 내 허브가 Claude Code 플러그인 카탈로그와 호환 — 무료 상호운용.
- **적합도**: 상 — 내 도메인(skills/agents 정의)과 1:1. 공식 규격이라 표준 안착.
- **채택 리스크**: 매우 낮음(규격 차용). 단 규격은 진화 중 — 버전 고정 필요.
- **OD/OCD 대비 새로 얻는 것**: **공식 Claude 플러그인 manifest 규격** — 내 sync-skills manifest를 anthropic 표준에 정렬시켜 외부 카탈로그 호환. OD/OCD엔 없는 표준화 레이어.

### 4. VoltAgent/awesome-design-md (+ Google Stitch DESIGN.md spec)
- **레포**: VoltAgent/awesome-design-md (https://github.com/VoltAgent/awesome-design-md) — ⭐92,362 · MIT · push 2026-06-16 · archived=False
- **한 줄 정체**: 브랜드별 `DESIGN.md`(Google Stitch DESIGN.md v2 규격) 모음 — **frontmatter YAML 토큰 + markdown prose** 2층 구조, 에이전트가 읽어 일관 UI 생성.
- **manifest 방출 방식(canonical 확정)**: v2 = Google Stitch DESIGN.md 규격. frontmatter 스키마 = `version·name·description·colors·typography·rounded·spacing·components` + `{path.to.token}` 교차참조 syntax. "frontmatter 정의 = machine-readable manifest, prose = human rationale"의 **표준화된 frontmatter 인제스트 패턴**. (canonical spec: google-labs-code/design.md)
- **CI/headless**: 정의 파일 — lint/diff/Tailwind export 가능(헤드리스).
- **에이전트 루프 결합 사례**: 설계 목적이 코딩 에이전트 입력 — 직접 결합.
- **lift할 구체 모듈/파일**: `design-md/*/DESIGN.md`의 **frontmatter 토큰 스키마 + `{path.to.token}` 참조 규약**을 내 정의 frontmatter 인제스트 규약으로 차용. 인제스트 라이브러리는 **gray-matter**(jonschlinkert/gray-matter, ⭐4,459·MIT·push 2025-06-14)로 markdown frontmatter→JSON.
- **적합도**: 상 — 내 skills/agents가 이미 frontmatter 정의라 패턴 그대로 적용. gray-matter는 sync-skills 파서를 정규화.
- **채택 리스크**: 낮음. awesome-design-md는 데이터 모음(임베드 대상 아님, 규격만); gray-matter는 안정 성숙 lib.
- **OD/OCD 대비 새로 얻는 것**: **frontmatter 2층 규격(machine 토큰 + human prose) + 검증된 인제스트 lib(gray-matter)** — OD/OCD엔 정의→어댑터(코드)는 있으나 frontmatter 표준 스키마·prose 분리는 없음.

---

## (b) 디자인 자동 검증

### 5. Playwright (toHaveScreenshot)
- **레포**: microsoft/playwright (https://github.com/microsoft/playwright) — ⭐91,442 · Apache-2.0 · push 2026-06-22 · archived=False
- **한 줄 정체**: headless 브라우저 자동화 + 비주얼 회귀(`expect(page).toHaveScreenshot()`).
- **검증 방식**: 골든 baseline 자동 생성 → 이후 실행마다 현재 스샷과 비교. **내부적으로 pixelmatch 사용**. 첫 실행 시 baseline write, 이후 diff.
- **검증이 결정론적인가**: **예 — 명백한 boolean**. `maxDiffPixels`·`maxDiffPixelRatio`·`threshold` 임계 초과 시 fail, 이내면 pass. 점수/주관 아님. (volatile 요소는 `stylePath`로 마스킹해 결정론 강화.)
- **CI/headless**: 정석 — `--update-snapshots`로 baseline 갱신, CI에서 머신 실행.
- **에이전트 루프 결합 사례**: agent가 머신 검증 도구로 부르는 사례 다수(자동 비주얼 regression). maker→render→verify에 직결.
- **lift할 구체 모듈/파일**: 나는 **이미 playwright를 design-mcp가 의존**(console-check.mjs가 `import("playwright")`). 따라서 추가 종속 0 — `toHaveScreenshot` 비교 로직(또는 그냥 `page.screenshot()` + 아래 odiff)을 verifier 루프의 boolean 게이트로 추가만 하면 됨.
- **적합도**: 상 — 이미 설치돼 있고 결정론, BYOK·local-first 부합.
- **채택 리스크**: 매우 낮음(이미 의존). full test-runner 채택은 과하니 비교 함수만.
- **OD/OCD 대비 새로 얻는 것**: OCD의 boolean *parity*(구조 동등) 검증 대비 — **픽셀 레벨 비주얼 회귀 게이트**(렌더 결과가 baseline에서 시각적으로 어긋났는가). parity는 구조, 이건 픽셀.

### 6. 비주얼 diff 엔진 — pixelmatch / odiff / reg-suit
- **레포들**:
  - mapbox/pixelmatch (https://github.com/mapbox/pixelmatch) — ⭐6,854 · ISC · push 2026-06-18 · archived=False
  - dmtrKovalenko/odiff (https://github.com/dmtrKovalenko/odiff) — ⭐3,067 · MIT · push 2026-06-11 · archived=False
  - reg-viz/reg-suit (https://github.com/reg-viz/reg-suit) — ⭐1,277 · MIT · push 2026-06-16 · archived=False
- **한 줄 정체**: pixelmatch=경량 픽셀 diff lib(playwright 내부 엔진) / odiff=SIMD 네이티브 바이너리 픽셀 diff(node·브라우저 불필요) / reg-suit=비주얼 회귀 *오케스트레이터*(baseline 저장·비교·리포트).
- **검증 방식 / 결정론**: **셋 다 결정론 boolean**. 핵심은 **odiff의 CLI exit code** — `0=match · 21=layout diff(차원 불일치) · 22=pixel diff`. → **그대로 hook이 소비할 수 있는 결정론 게이트**(내 console-check.mjs `exit 2`와 동일 패턴). threshold(0~1)·antialiasing 무시 옵션. odiff는 pixelmatch 대비 ~6.6배 빠름(SIMD).
- **CI/headless**: odiff=단일 바이너리(node·브라우저 불필요)라 CI 최경량. reg-suit=CI 오케스트레이션 전용.
- **에이전트 루프 결합 사례**: reg-suit는 CI 비주얼 회귀 파이프 표준. odiff는 그 백엔드로 자주 채택.
- **lift할 구체 모듈/파일**: **odiff-bin CLI를 verifier 게이트로 직접 호출** — `odiff base.png cur.png diff.png; case $? in 0) pass;; 21|22) needs_work;; esac`. exit code가 곧 boolean 판정이라 래퍼 거의 불필요. baseline은 디스크에 둠(디스크=상태 부합).
- **적합도**: **상(odiff) / 중(pixelmatch, playwright에 이미 내장) / 중(reg-suit, 오케스트레이션은 sync-skills로 self-host 가능해 과대)**.
- **채택 리스크**: odiff=낮음(작은 단일 바이너리, MIT). reg-suit=내 디스크-상태 패턴과 일부 중복(과대 채택 위험).
- **OD/OCD 대비 새로 얻는 것**: OCD boolean parity 대비 — **exit-code 기반 픽셀/레이아웃 게이트**(0/21/22). parity는 "구조 같나", odiff는 "픽셀·차원 깨졌나"를 *서로 다른 두 exit code*로 분리해 줌(레이아웃 붕괴 vs 미세 픽셀차 구분 = 내 verifier가 지금 사람 눈으로 하는 판정의 결정론화).

### 7. BackstopJS
- **레포**: garris/BackstopJS (https://github.com/garris/BackstopJS) — ⭐7,154 · MIT · **push 2024-09-07(정체)** · archived=False
- **한 줄 정체**: 시나리오 기반 비주얼 회귀 프레임워크(headless Chrome + resemble.js diff + HTML 리포트).
- **검증 방식 / 결정론**: 결정론 boolean(scenario별 mismatch threshold 초과 시 fail). 다만 무겁고 설정 장황(`backstop.json` 시나리오 DSL).
- **CI/headless**: 지원. 단 puppeteer·리포트 UI 등 의존 다발.
- **에이전트 루프 결합**: CI 회귀 도구로의 선례는 있으나 LLM 루프 결합 선례는 약함.
- **lift할 구체 모듈/파일**: scenario 정의 스키마(referenceUrl·selectors·misMatchThreshold) 개념 정도. 본체 임베드는 비권장.
- **적합도**: 하 — 내가 이미 가진 design-mcp(preview/screenshot) + odiff 조합이 같은 일을 더 가볍게 함. 중복.
- **채택 리스크**: **유지보수 정체(20개월 무 push)** + 무거운 종속. 신뢰·성숙 모두 마이너스.
- **OD/OCD 대비 새로 얻는 것**: 사실상 없음(playwright+odiff가 상위호환). 시나리오 DSL 아이디어만.

### 8. Storybook test-runner / Chromatic OSS
- **레포들**:
  - storybookjs/test-runner (https://github.com/storybookjs/test-runner) — ⭐274 · MIT · push 2026-05-14 · archived=False
  - chromaui/chromatic-cli (https://github.com/chromaui/chromatic-cli) — ⭐337 · MIT · push 2026-06-22 · archived=False
- **한 줄 정체**: test-runner=story를 playwright로 자동 smoke/play-fn 실행(렌더·인터랙션 깨짐 검출) / chromatic-cli=Chromatic SaaS 업로드 클라이언트(비주얼 diff 본체는 클라우드, 클로즈드).
- **검증 방식 / 결정론**: test-runner=story render 에러/play assertion boolean(결정론). chromatic-cli=**diff 판정이 클라우드 SaaS**라 local-first·BYOK 위반(OSS는 업로드 클라만).
- **CI/headless**: test-runner=헤드리스 CI. chromatic=클라우드 의존.
- **에이전트 루프 결합**: test-runner의 "render→play→assert" 게이트는 내 verifier "preview→getConsoleLogs→needs_work"와 사상 동일.
- **lift할 구체 모듈/파일**: test-runner의 **play-function smoke 게이트 패턴**(렌더 후 인터랙션 시퀀스 → assert → boolean). 내 verifier `steps[]` 전/후 캡처를 assert까지 확장하는 청사진.
- **적합도**: 중(test-runner 패턴) / **하(chromatic — 클라우드라 렌즈 위반)**.
- **채택 리스크**: test-runner=storybook 종속(내가 storybook 안 쓰면 부적합 — 패턴만). chromatic=local-first 탈락.
- **OD/OCD 대비 새로 얻는 것**: test-runner의 인터랙션 후 assert 게이트(정적 스샷 너머의 상태 검증) 아이디어. chromatic은 얻을 것 없음(렌즈 위반).

---

## 축 4 비교표

### (a) 정의 → manifest / 카탈로그
| 후보 | ⭐ | license | 핵심 속성 | 적합도 |
|---|---|---|---|---|
| Storybook (index.json) | 90.4k | MIT | 정의 파일 인덱싱 → 평탄 엔트리 manifest 스키마 | 중 |
| Style Dictionary | 4.7k | Apache-2.0 | 토큰 → 다중포맷 fan-out(도메인 특화) | 하 |
| **frontend-design plugin** | (모노레포) | (Anthropic) | `.claude-plugin/plugin.json`+marketplace 공식 manifest 규격 | **상** |
| awesome-design-md (+gray-matter) | 92.4k / 4.5k | MIT / MIT | frontmatter 2층(machine 토큰+prose) + 인제스트 lib | 상 |

### (b) 디자인 자동 검증
| 후보 | ⭐ | license | 핵심 속성 | 결정론? | 적합도 |
|---|---|---|---|---|---|
| Playwright toHaveScreenshot | 91.4k | Apache-2.0 | baseline 픽셀 diff(내부 pixelmatch), maxDiffPixels 임계 | ✅ boolean | 상(이미 의존) |
| **odiff** | 3.1k | MIT | SIMD CLI, **exit 0/21/22**(match/layout/pixel) | ✅ exit-code boolean | **상** |
| pixelmatch | 6.9k | ISC | 경량 픽셀 diff lib(playwright 내장 엔진) | ✅ boolean | 중 |
| reg-suit | 1.3k | MIT | 비주얼 회귀 오케스트레이터 | ✅ boolean | 중(과대) |
| BackstopJS | 7.2k | MIT | 시나리오 회귀, 유지정체(2024) | ✅ boolean | 하 |
| Storybook test-runner | 0.3k | MIT | render→play→assert smoke | ✅ boolean | 중(패턴) |
| Chromatic OSS(cli) | 0.3k | MIT | diff는 **클라우드 SaaS** | ✅이나 클라우드 | 하(렌즈 위반) |

---

## 축 4 단독 1픽 (둘 다 필요)

- **(a) manifest용 1픽 — awesome-design-md DESIGN.md 규격 + gray-matter**.
  근거: 내 skills/agents가 이미 frontmatter 정의라 "frontmatter 2층(machine 토큰 + human prose) + `{path.to.token}` 참조"를 그대로 적용 가능. gray-matter(MIT·성숙)로 sync-skills 파서를 정규화해 `manifest.json` 방출. **차순위 = frontend-design plugin 규격** — 방출 manifest를 anthropic 공식 plugin.json/marketplace.json 필드에 정렬하면 외부 카탈로그 호환(무료 상호운용). 둘은 보완: awesome-design-md=*frontmatter 인제스트 규약*, frontend-design=*방출 manifest 표준*. (Storybook은 스키마 shape만 참고.)

- **(b) 검증용 1픽 — odiff (exit-code 게이트), Playwright screenshot을 캡처원으로**.
  근거: odiff CLI exit `0/21/22`가 곧 boolean 판정이라 내 `console-check.mjs exit 2` 패턴에 *래퍼 거의 없이* 박힌다 — `layout diff(21)`와 `pixel diff(22)`를 분리 코드로 줘서 "레이아웃 붕괴"와 "미세 픽셀차"를 결정론으로 구분(지금 verifier가 사람 눈으로 하는 판정의 자동화). 캡처는 이미 의존 중인 playwright `page.screenshot()`로 떠서 추가 종속 0, baseline은 디스크 보관(디스크=상태). SIMD라 CI 최경량.

---

## 축 4 핵심 takeaway

**(a)는 신규 OSS 채택이 아니라 "내 sync-skills를 awesome-design-md frontmatter 규격(+gray-matter)으로 정규화해 anthropic 공식 plugin manifest 형태로 방출"하는 *규격 정렬* 문제이고, (b)는 내 디자인 하네스가 이미 가진 console-error 게이트 옆에 odiff exit-code(0=ok/21=layout/22=pixel)를 박아 OCD의 구조 parity 검증을 *픽셀·레이아웃 비주얼 회귀*로 확장하는 *부품 1개 추가* 문제다 — 둘 다 통째 채택이 아닌 "스키마 차용 + 단일 바이너리 게이트"라 종속 무게 사실상 0.**
