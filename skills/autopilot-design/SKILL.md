---
name: autopilot-design
description: "Unified design pipeline — orchestrates design-init → design-refs → design-tokens → design-components → design-review → design-handoff. For visual artifacts across UI/UX, slides, diagrams, icons, logos. Can be invoked standalone or auto-delegated from autopilot-spec Phase 2. Distinct from autopilot-draft (text-only documents) — autopilot-design handles visual deliverables. **Claude-Design parity via a design harness** (claude-design-harness-spec.md): a Design MCP server (~/.claude/tools/design-mcp — preview/screenshot/console/eval_js/view_image) renders every output so it is visually self-verified (render → view_image → fix loop); a separate-context verifier subagent gates console/layout breakage; shared design rules (slop avoidance, scale, HTML conventions) and reusable scaffolds (deck_stage, tweaks_panel, device_frames) standardize craft; converters export PDF/PPTX/single-HTML bundle; a post-write hook auto-checks console on design HTML saves. Outputs can be a self-contained single-file HTML preview viewable without any project stack."
argument-hint: "<design task or app path> [--scope ui|webapp|slide|icon|diagram|mixed] [--artifact standalone|project] [--from <phase>] [--qa quick|standard|thorough]"
---

> 산출물 폴더:
> - 사용자 직접 호출: `.claude_reports/designs/<name>/`
> - autopilot-spec 에서 위임: `.claude_reports/spec/design/`
>
> CONVENTIONS.md §5 3-tier — T1: root + design_state.yaml / T2: `00_init/`, `01_refs/`, … / T3: `_internal/` per phase.

## Default Invocation Rule (메인 Claude 자동 라우팅)

### Trigger 신호 (자연어 발화 예시)

- "디자인 해줘" / "UI 만들어줘" / "컴포넌트 디자인"
- "이 슬라이드 디자인 정리해줘" / "발표 자료 디자인"
- "로고 / 아이콘 / 일러스트 만들어줘"
- "디자인 토큰 정해줘" / "색 팔레트 짜줘"
- "이 화면 비평해줘" — design-review 만 직접 호출 권장
- autopilot-spec Phase 2 자동 위임

### Default 옵션

- `--scope`: `mixed` (auto-detect — UI 면 `ui`, 슬라이드면 `slide`, 단일 자산이면 `icon` 등)
- `--from`: auto-detect (design_state.yaml 있으면 다음 phase 부터)
- `--qa`: `standard`

### Override

- 단일 컴포넌트 — `Agent(디자인팀, mode=maker)` 직접 호출
- 비평만 — `Agent(디자인팀, mode=critic)` 직접 호출
- 외부 레퍼런스만 — `Agent(자료팀, mode=web-image-search)` 직접 호출
- `/autopilot-design <args>` slash 직접 입력 — 컨펌 skip

## Language Rule
- Korean output, English code identifiers, English design tokens (color names, font families).

## Argument Parsing

### --scope (auto-detect default)
- `ui` — 프론트 UI 컴포넌트 단위 (버튼·카드·폼 등)
- `webapp` — _전체 화면·페이지·랜딩_ 합성 (컴포넌트 조합 + 페이지 레이아웃 + 인터랙션 상태). Claude Design 의 "한 장짜리 완성 화면" 자리
- `slide` — 발표 슬라이드 비주얼
- `icon` — 아이콘·로고 단일 자산
- `diagram` — 아키텍처·flow·관계 도식 (mermaid / 직접 SVG / excalidraw)
- `mixed` — 위 여러 영역 통합

scope 에 따라 일부 phase auto-skip:
- `icon`: tokens skip 가능 (단일 자산), components skip
- `diagram`: tokens·components skip, refs + handoff 중심

### --artifact (산출 형태)
- `project` (default when a stack exists) — 프로젝트의 `components/ui/` + tokens 파일에 통합 (shadcn/Tailwind/Next 전제)
- `standalone` (default when no stack, or quick 시각 요청) — **자체 완결 단일 HTML preview** (`preview.html`, inline CSS/JS, 필요 시 CDN React·Tailwind). 프로젝트 없이 브라우저로 바로 열림 = Claude Design artifact 패리티. diagram·slide·icon·webapp 빠른 미리보기에 기본 적합
- auto-detect: cwd 에 `package.json`/`components.json`/`tailwind.config.*` 있으면 `project`, 없으면 `standalone`

### --from (auto-detect default)
- `init` / `refs` / `tokens` / `components` / `review` / `handoff`
- design_state.yaml 발견 시 마지막 `done` phase 다음부터

### --qa
- `quick` (review phase skip)
- `standard` (default)
- `thorough` (디자인팀 critic + 외부 레퍼런스 cross-check)

## Context Auto-Detection (신규 vs 재호출 자동 분기)

본 skill 은 호출 자리에서 _발화 + cwd_ 검사로 자동 분기 — `--from` 명시 없이도 동작:

### 1단계 — design_state.yaml 자동 검사

| 감지 조건 | 처리 |
|---|---|
| `.claude_reports/designs/<name>/design_state.yaml` 또는 `.claude_reports/spec/design/design_state.yaml` 부재 | **신규 cycle** — Phase 0 (design-init) 부터 처음 |
| 위 path 존재 | **재호출** — `phases:` read + 발화 의도 분류 후 해당 phase 부터. _토큰 보존 + 새 컴포넌트만 확장_ 자리 자연 |

`<name>` 추출 — 발화·cwd. autopilot-spec 의 app mode 자리면 `spec/design/` 우선.

### 2단계 — 발화 → phase 자동 분류 (재호출 자리)

| 발화 신호 | 추론 phase | 흐름 |
|---|---|---|
| "환경 다시 점검" / "Figma 연결 다시" | `--from init` (Phase 0) | 환경 점검만 |
| "레퍼런스 추가" / "이 image 도 참고" | `--from refs` (Phase 1) | refs 보강 |
| "색 / 폰트 / 간격 토큰 바꾸자" | `--from tokens` (Phase 2) | tokens.css 갱신 + 이후 phase 재 |
| "새 컴포넌트 X 추가" / "버튼 variant 추가" | `--from components` (Phase 3) | 토큰 보존 + 컴포넌트 확장 (가장 흔한 재호출) |
| "디자인 비평 다시 받자" / "review 다시" | `--from review` (Phase 4) | critic 만 |
| "handoff 정리" / "import path 갱신" | `--from handoff` (Phase 5) | handoff.md 갱신 |

### 3단계 — 자동 컨펌 한 화면

```
=== autopilot-design 호출 자리 ===
대상: <name> (designs/<name>/ 또는 spec/design/)
산출물: 발견 (last_completed_phase: <phase>) / 부재 (신규 cycle)
발화: "<사용자 한 줄>"
→ 추론: <신규 / --from <phase>> 자리

진행? (진행 / 다른 phase 로 / 새 cycle 로 / 중단)
```

신규 vs 재호출 분류는 _명시 옵션 없이도_ 동작 — 발화 + cwd 자동 판단. 사용자가 명시적 `--from <phase>` 입력하면 그대로.

## Pipeline Overview

```
Phase 0: design-init        (환경 점검 — Figma MCP, shadcn, tokens.css 부재 안내)
Phase 1: design-refs        (레퍼런스 수집 — 사용자 image, 외부 검색, 기존 디자인)
Phase 2: design-tokens      (color / typography / spacing / radius / shadow — single source)
Phase 3: design-components  (컴포넌트·시각 자산 만들기 — 디자인팀 maker)
Phase 4: design-review      (비평 — 디자인팀 critic, 6축 점검)
Phase 5: design-handoff     (코드 위치·import path·재현 가이드)
```

## Paper architecture figure 는 _layout 가이드_ 까지만 (2026-05-28 정책)

논문용 architecture diagram (사용자 deck 양식의 그림) 은 **LLM 시각 craft 의 한계 영역** — 디자인팀은 본 그림을 생성하지 않는다. 다음 자리에서만 개입:
- **composition/layout 가이드 산출** — 블록 list(라벨·역할색·위치) · 흐름 · 위계 · 강조 자리. markdown sketch 또는 wireframe-grade SVG.
- **참조 자료 안내** — `~/.claude/user_profile/assets/figure/svg/`(pptx 추출 개체) · `figure_ppt/*.pptx`(편집 가능 원본) · `01_paper_figure_style.md` Part B 거시 감각.
- **사용자가 pptx 에서 직접 완성** — 슬라이드 도형 복제 후 라벨·색 교체.

본 정책은 **paper architecture figure 한정**. 다른 scope (ui · webapp · slide HTML · icon · mermaid/excalidraw diagram) 는 LLM 손그림으로 충분 → 아래 시각 검증 루프로 완결.

## 하네스 (claude-design-harness-spec.md 기반 구성)

본 pipeline 은 _"자기가 만든 결과물을 픽셀로 보고 고치는 피드백 루프"_ 를 본체로 한다. 구성 요소·위치:

| # | 컴포넌트 | 위치 | 역할 |
|---|---|---|---|
| ① | **Design MCP Server** | `~/.claude/tools/design-mcp/` (`mcp__design__*`) | preview·screenshot·getConsoleLogs·eval_js·view_image·image_metadata. 시각 피드백 루프의 본체 |
| ② | **Verifier subagent** | `Agent(디자인팀, mode=verifier)` | 별도 컨텍스트 독립 검수 — 콘솔·레이아웃·의도 _깨짐_ 게이트 |
| ③ | **디자인 규칙** | `agent-modes/design/_design_rules.md` | 슬롭 회피·비주얼 기본값·스케일·HTML 규약·변형 처리 (프롬프트) |
| ④ | **Scaffolds** | `~/.claude/scaffolds/` | deck_stage·tweaks_panel·device_frames·design_canvas·image_slot |
| ⑤ | **Converters** | `~/.claude/tools/design-mcp/convert.mjs` | PDF · 단일 HTML 번들 · PPTX |
| ⑥ | **Post-write hook** | `~/.claude/hooks/design-postwrite.sh` | design HTML 저장 시 콘솔 자동 체크 (`DESIGN_POSTWRITE_HOOK=0` 으로 opt-out) |

design-init 이 ① 를 자가 프로비저닝 (설치·등록·스모크). 부재로 멈추지 않는다 (스펙 §0.5).

## 시각 검증 (전 visual phase 공통 — Claude Design parity, 필수)

components·tokens·review phase 는 **Design MCP 로 렌더해서 본 것** 으로만 완료한다. 좌표·코드·XML valid 는 시각 검증이 아니다 (maker/critic 이 _눈 감고_ 좌표 부르는 실패가 반복됐음).

- **렌더 경로**: HTML/React → `mcp__design__preview` → `getConsoleLogs` → `screenshot` → `view_image`. SVG/diagram 단품 → `sharp`/`rsvg-convert`/`mmdc` PNG → `view_image` (브라우저 불필요).
- **루프**: 산출 → 렌더 → **이미지 직접 보기** → 자가 비평 (관통·overlap·정렬·위계·잘림) → 수정 → 재렌더. 시각적으로 깨끗할 때까지 (최대 3-5 회전). 큰 화면은 `clip` crop 확대. 대비·box 의심은 `eval_js` 로 수치 확인.
- **사용자에 렌더 이미지를 보여준다** — 텍스트 보고만으로 완료 X. live-preview 패리티.
- 상세 루프는 `_design_rules.md` §시각 자가검증 루프 (maker/critic/verifier 공유).
- **Design MCP 미부착 세션** (막 등록한 직후) 이면 `sharp`/`rsvg`/`mmdc` 정적 렌더로 fallback, 다음 세션부터 `mcp__design__*` 사용.

각 phase 끝에 **[CONFIRM Gate]** — autopilot-spec 의 4 갈래 응답 (진행 / 수정 / back-jump / 중단) 패턴 그대로. 발화가 모호하면 메인 Claude 가 옵션 다시 물음 (임의 추측 X).

| 응답 | 동작 |
|---|---|
| **진행** | 다음 phase |
| **수정** | 현 phase `--user-refine` 진입 (산출물 v2 작성) |
| **back-jump** | `--from <phase>` (refs / tokens / components 자리 선택, 하위 phase reset) |
| **중단** | pipeline 멈춤, `design_state.yaml` 상태 보존 |

## Pipeline Execution

You (메인 Claude) orchestrate by invoking each skill directly via the Skill tool.

### Phase 0: design-init

If `design_state.yaml` 부재 OR `--from init` 명시:

Invoke Skill: `design-init` with the design task as args.

design-init 이 **Design MCP (①) 를 자가 프로비저닝** — 설치(`npm install`)·등록(`claude mcp add design --scope user`)·스모크(`npm run smoke`). 부재 도구는 깔고 진행 (스펙 §0.5), OS 전역 설치만 한 줄 알림.

결과: `00_init/environment_check.md` + `design_state.yaml` 생성

**[CONFIRM Gate 0]** — "환경 점검 + Design MCP 프로비저닝 완료. refs 로 진행할까요? (진행 / 수정 / 중단)"

### Phase 1: design-refs

Invoke Skill: `design-refs` with task description + (옵션) image paths as args.

레퍼런스 수집:
- 사용자 제공 이미지 (drag-drop 또는 path)
- 외부 검색 (autopilot-design 이 자체로 `Agent(자료팀, mode=web-image-search)` 호출 가능)
- 기존 디자인 system / paper figure / 이전 cycle 자산

결과: `01_refs/brief.md` + `_internal/references/` 폴더 (이미지·URL·메모)

**[CONFIRM Gate 1]** — "레퍼런스 정리 완료. tokens 로 진행할까요? (진행 / 수정 — 레퍼런스 추가·교체 / 중단)"

### Phase 2: design-tokens

scope 가 `icon` 이면 skip 가능. 그 외엔:

Invoke Skill: `design-tokens` with the design path as args.

결과:
- `02_tokens/tokens.md` — 디자인 결정 사유
- `02_tokens/specimen.html` — palette/type/spacing specimen. **렌더 → Read 자가검증 필수** (대비·조화 확인 후에야 토큰을 component 가 소비). 토큰도 시각 시스템이라 값만 정하고 넘기지 않음
- `02_tokens/tokens.css` 또는 `tailwind.config.ts` — 실제 토큰 파일

기존 토큰 파일 발견 시 _확장_ (덮어쓰기 X).

**[CONFIRM Gate 2]** — "토큰 결정. components 로 진행할까요? (진행 / 수정 — 토큰 조정 / back-jump — refs 로 / 중단)"

### Phase 3: design-components

Invoke Skill: `design-components` with the design path as args.

내부: `Agent(디자인팀, mode=maker)` 호출 — maker 는 **시각 자가검증 루프** 를 거쳐 산출 (렌더→Read→수정).

결과:
- `03_components/` — 컴포넌트 spec / mockup / 실제 코드
- scope 따라:
  - `ui`: shadcn/ui 컴포넌트 + custom
  - `webapp`: 페이지 합성 + 전체 화면 `preview.html` (인터랙션 상태 포함)
  - `slide`: 슬라이드 비주얼 가이드 (마크다운) + **전 슬라이드 렌더** (장수 많으면 contact-sheet montage 한 장) + self-contained `slides.html` (한 슬라이드=한 section)
  - `icon`: SVG 또는 이미지
  - `diagram`: mermaid / 직접 SVG / excalidraw + **렌더 PNG**
- `--artifact standalone` 면 위 산출을 자체 완결 `preview.html` 로도 emit (브라우저 바로 열림)
- **렌더 이미지 첨부** — 컴포넌트/화면을 렌더해 본 결과를 산출과 함께 제시 (live-preview 패리티)

**[CONFIRM Gate 3]** — "컴포넌트 완료 (렌더 확인함). review 로 진행할까요? (진행 / 수정 — 컴포넌트 보강 / back-jump — tokens / refs 로 / 중단)"

### Phase 4: design-review

`--qa quick` 시 skip. 그 외:

Invoke Skill: `design-review` with the design path as args.

내부 **두 게이트**: ① `Agent(디자인팀, mode=verifier)` — 별도 컨텍스트에서 Design MCP 로 _깨졌는가_ (콘솔 에러·레이아웃 붕괴·의도 불일치) 기계 판정. ② `Agent(디자인팀, mode=critic)` — 렌더 이미지를 직접 보고 6축 _품질_ 비평.

결과: `04_review/verifier.md` (verdict + issues) + `04_review/critique.md` (6축).

🔴 / verifier `needs_work` 발견 시:
- `design_state.yaml` 의 `phases.review: failed`
- 사용자에 보고 후 components phase 재호출 권장 (깨짐은 critic 전에 verifier 가 차단)

**[CONFIRM Gate 4]** — "review 통과. handoff 로 진행할까요? (진행 / 수정 — 비평 반영 / back-jump — tokens·components / 중단)"

### Phase 5: design-handoff

Invoke Skill: `design-handoff` with the design path as args.

결과:
- `05_handoff/handoff.md` — 사용된 컴포넌트·토큰 위치, frontend 개발자가 import 할 path, 재현 가이드
- `05_handoff/exports/` — 요청·scope 적합 시 converters (⑤) 산출: PDF / 단일 HTML 번들 / PPTX (`convert.mjs`)
- autopilot-spec 에서 위임된 경우: 호출자에 결과 path 반환

**[Final Confirm]** — "디자인 사이클 완료. (확인 / back-jump — 어느 phase 든 / 중단)"

## Design state 관리

`design_state.yaml`:

```yaml
design_name: <name>
scope: ui  # or webapp/slide/icon/diagram/mixed
artifact: standalone  # or project (stack 유무로 auto-detect)
created: <date>
phases:
  init: done
  refs: done
  tokens: done
  components: done
  review: done
  handoff: pending
last_updated: <timestamp>
```

## Auto-delegation from autopilot-spec

autopilot-spec Phase 2 가 `Invoke Skill: autopilot-design --app <name>` 호출 시:
- 산출물 위치를 `.claude_reports/spec/design/` 로 자동 설정
- `--qa` 옵션은 autopilot-spec 의 그것 상속
- 완료 후 `phases.design: done` 을 autopilot-spec 의 `pipeline_state.yaml` 에 갱신

## Return Format

```
<output_path> -- ✅ Phase {N} ({phase_name}) completed
```

전체 사이클 완료 시:
```
<output_path> -- ✅ Design cycle completed (handoff ready)
```

## Update memory

- 사용자 디자인 선호 (minimal / dense / playful, 색감, 폰트)
- 자주 만든 컴포넌트 패턴
- scope 별 phase auto-skip 판단 기준
- 외부 레퍼런스 vs 자체 디자인 비중
