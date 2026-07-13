# 디자인 공통 규칙 (maker · critic · verifier 공유)

> 스펙 `claude-design-harness-spec.md` §1·§4 를 디자인팀 운영 규칙으로 인코딩. **도구가 아니라 프롬프트** — 이게 빠른 코더와 디자이너를 가른다. maker/critic/verifier 는 작업 시작 자리에서 이 파일을 Read 하고 따른다.

## 설계 원칙 (먼저 내면화)

1. **시각 피드백이 본체다.** HTML/SVG 를 "코드"로만 다루면 그럴듯하지만 틀린다. 매 빌드 후 _반드시_ 렌더 → 캡처 → 비전으로 되읽어 비평한다 (아래 §시각 자가검증 루프).
2. **검수는 분리한다.** 만든 에이전트가 자기 작업을 검수하면 관대해진다. 별도 컨텍스트의 verifier 가 콘솔·스크린샷·DOM 을 독립 점검한다.
3. **컨텍스트 없이 시작하지 않는다.** 브랜드·디자인 시스템·레퍼런스가 없으면 _먼저 질문_ 해 확보한다. 컨텍스트 결핍 = 슬롭의 근원.
4. **시스템을 말로 먼저 선언한다.** 색·타입·간격·레이아웃 규칙을 빌드 전에 명시. 매 화면 새 색을 즉흥 발명하지 않는다.
5. **적게가 많다.** 더미 콘텐츠·불필요한 통계·아이콘 남발 금지. 모든 요소는 존재 이유가 있어야 한다.
6. **고정 크기 산출물은 스스로 스케일링한다.** 슬라이드·영상은 고정 캔버스를 뷰포트에 맞춰 `transform: scale()` 로 레터박싱.

## 시각 자가검증 루프 (필수 — Design MCP 경유)

렌더 가능한 모든 산출물 (HTML·React·SVG·다이어그램) 은 **텍스트로 짜고 끝내지 않는다.** 좌표 계산·XML 유효성 (`valid`/`교차 0`) 은 _시각 검증이 아님_ — 눈 감고 좌표 부르는 것과 같다.

도구는 **Design MCP** (`mcp__design__*`, 설치는 design-init 이 보장):

1. **공통 플로어 (모든 어댑터가 실현)** — `mcp__design__preview` 로 HTML 을 렌더하고, 같은 렌더 세션에서 스크린샷과 콘솔 에러를 얻는다. 콘솔 에러가 있으면 먼저 고친다 (깨진 화면을 비평해봐야 무의미) — 캡처한 이미지는 직접 본다.
2. **확장 기능 (지원 런타임 한정)** — 여러 상태(슬라이드·hover·scroll)의 연속 캡처·영역 확대(crop)·DOM 수치(대비·box 위치) 확인·in-loop 이미지 재조회를 제공하는 렌더 런타임에서는 이 루프 안에서 활용해 더 깊이 검증한다. 제공하지 않는 런타임(단일 스냅샷 harness 등)에서는 공통 플로어가 상한이며, 그 한계를 명시해 보고한다.
3. **자가 비평 → 수정 → 재렌더** — 관통·overlap·정렬 어긋남·spacing 불균형·위계 불명확(focal point 없음)·색 역할 혼선·잘림. 의심 지점은 위 확장 기능의 DOM 수치 확인으로 교차확인 (지원 런타임 한정 — 미지원이면 육안 판단). 시각적으로 깨끗할 때까지 (최대 3-5 회전).
4. **보고는 본 것으로** — "valid/교차 0" 대신 "렌더해 확인: X 영역 관통 수정, label overlap 없음, 콘솔 에러 0" 식 _관찰_ 보고. **렌더 이미지를 사용자에 제시** (live-preview 패리티).

### scope 별 렌더 (ui/webapp · slide · icon · diagram)

공통 흐름: `mcp__design__preview({ path })` → `mcp__design__getConsoleLogs()` (에러 먼저) → `mcp__design__screenshot({ savePath, steps })` → `mcp__design__view_image({ path })`. scope 별 구체:

| scope | 렌더 → 본다 |
|---|---|
| `ui` / `webapp` | `preview.html` 을 `preview` → screenshot → view_image. 컴포넌트 단품 + **페이지 합성 전체 화면** 둘 다. hover/active/empty/loading 은 `steps[]` 로. 반응형은 `preview` viewport 변경 (mobile/desktop 각각) |
| `slide` | `slides.html` (deck_stage) 을 `preview` → `screenshot({ steps })` 로 **전 슬라이드** 캡처 (각 step: 다음 슬라이드로 이동) → view_image. _un-rendered 가이드로 남는 슬라이드 없음_ |
| `icon` | SVG → `sharp`/`rsvg-convert` PNG → view_image (작은 자산은 `clip`/density 확대). 또는 preview.html gallery 로 |
| `diagram` | SVG → PNG / mermaid → `mmdc` PNG → view_image. 관통·overlap·label 겹침 확인, 의심 영역 `clip` crop 확대 |

> 렌더 불가 환경(Design MCP 미부착·단일 스냅샷 harness 등)이면 그 사실을 명시하고 `sharp`/`rsvg`/`mmdc` 정적 렌더로 fallback + _본 범위만_ 비평한다 (못 본 것을 본 척 X).

> SVG/diagram 단품은 `sharp`/`rsvg-convert`/`mmdc` 로 PNG 렌더 후 이미지로 직접 확인도 가능 (브라우저 불필요한 정적 자산). HTML·React·인터랙션·콘솔 점검이 필요하면 반드시 Design MCP.

## 슬롭 회피 (그대로 지킬 것)

- **금지 (AI slop blocklist — 공개 DESIGN.md 그대로)**: 흰 배경 위 purple gradient / 공격적 그라데이션 배경 / 둥근 모서리+좌측 액센트 보더 컨테이너 / _균일한_ rounded corner 도배 / _과도한_ centered layout / evenly-distributed timid(겁먹은 균등 채도) 팔레트 / 이모지 남발(브랜드 아니면) / 무지성 default 폰트 (**Inter · Roboto · Arial · Open Sans · Lato · system-ui** + 남용된 Fraunces).
- 더미·플레이스홀더 콘텐츠로 공간 채우지 않기 — 모든 요소는 존재 이유가 있어야.
- 불필요한 숫자·통계·아이콘(데이터 슬롭) 금지. 미니멀 지향.
- 이미지를 SVG 손그림으로 위조하지 말 것 — 줄무늬 placeholder + 모노스페이스 설명("product shot")으로 자리만.
- 섹션·콘텐츠가 더 필요해 보이면 임의로 넣지 말고 _먼저 물어본다_.

## 비주얼 기본값 (디자인 시스템·레퍼런스가 _없을 때만_)

- 컨텍스트도 레퍼런스도 없으면 미감을 임의로 고르지 말고 **사용자에 질문**한다.
- 타입: 웹세이프 또는 Google Fonts 1–3 개. 가독성 우선.
- 전경/배경: 톤(웜/쿨/뉴트럴) 하나. 흰/검정은 subtle 하게(채도 ≤ 0.02).
- 액센트: 0–2 개, `oklch` 로. 같은 chroma·lightness, hue 만 다르게.
- 색은 브랜드·디자인 시스템에서. 부족하면 `oklch` 로 조화롭게 확장.

## conceptual altitude — 4 dimension (Claude Design 공개 frontend-design skill 흡수)

> 핵심 철학: **low-level hex 가 아니라 _올바른 conceptual altitude_ 의 targeted language** 로 디자인을 지시한다. "균형 잡힌 모던" 같은 generic default 는 명시적으로 _금지_ — 모델은 그쪽으로 수렴한다.

빌드 전 4축을 _말로 선언_ (없으면 사용자에 질문):
1. **Typography** — 폰트는 _altitude 리스트_ 에서 (generic 회피):
   - code/tech: JetBrains Mono · Fira Code · Space Grotesk
   - editorial: Playfair Display · Crimson Pro · Fraunces
   - startup/brand: Clash Display · Satoshi · Cabinet Grotesk
   - **페어링 = high contrast** (display+mono, serif+geometric sans). **weight 극단** (100/200 vs 800/900, 어중간 400/500 회피). **size jump 3x+** (위계 또렷이).
   - **anti-convergence**: Space Grotesk 처럼 _대체 default_ 로도 수렴하니 그것마저 의식적으로 피한다.
2. **Color & Theme** — 톤 하나 + oklch 액센트 (위 비주얼 기본값). timid 균등 팔레트 금지.
3. **Motion** — 의미 있는 전환만 (등장·강조·상태변화). 장식적 애니메이션 남발 금지. 고정 캔버스는 scale 레터박싱.
4. **Backgrounds / Spatial composition** — 평면 단색이 default 보다 낫다 (그라데이션 슬롭 회피). 여백·grid 로 위계, 균등 분산 회피.

inspiration 참조 전략: 막연하면 _IDE 테마 / 문화적 미감 / 특정 브랜드_ 를 anchor 로 지정해 generic 탈출.

## 스택·번들 parity (Claude Design / artifacts 흡수)

- **default 스택**: React 18 + Tailwind + shadcn/ui + Radix + Recharts(차트) + Lucide(아이콘) + Three.js(3D) + Motion(React 애니메이션). webapp/component 산출 시 이 셋을 1순위 보장 (artifact 가 보장하는 라이브러리 셋과 parity).
- **단일파일 번들**: 멀티파일로 개발(Vite+TS+Tailwind)하되 최종은 _self-contained 단일 `bundle.html`_ 로 inline (Parcel + html-inline). 참조 구현 = 공개 `anthropics/skills` 의 `web-artifacts-builder` (init/bundle 2 스크립트). 우리 standalone preview.html 목표와 동일 — 프로젝트 스택 없이 열림.

## 스케일 / 단위

- 1920×1080 슬라이드: 본문 ≥ 24px (가능하면 더 큼).
- 인쇄 문서: 최소 12pt.
- 모바일 목업 히트 타깃: ≥ 44px.
- 고정 크기 콘텐츠(덱·영상)는 fixed 캔버스를 full-viewport stage 로 감싸 `transform: scale()` 레터박싱. 컨트롤은 scale 밖에 둔다. (→ `<agent-home>/scaffolds/deck_stage` 사용)

## HTML 작성 규약 (직접 편집 친화 + SPA 안전)

- 모든 비-void 요소는 명시적으로 닫는다 (`<div></div>`). 속성값은 큰따옴표. 비-void self-close 금지.
- UI 요소 그룹은 flex/grid + `gap`. 인라인 흐름 + `margin` 의존 금지.
- `scrollIntoView` 사용 금지 (SPA·덱 깨짐). 다른 scroll 메서드 사용.
- 1000 줄 넘는 단일 파일 금지. 작은 컴포넌트로 분할 후 메인에서 import.

## 변형(variant) 처리

사용자가 새 버전·변경을 요청하면 **파일을 늘리지 말고** 원본에 **트윅**으로 추가한다 (단일 메인 파일 버전 토글, → `<agent-home>/scaffolds/tweaks_panel`). 색 트윅은 자유 피커 대신 3–4 개 큐레이션 스와치.
