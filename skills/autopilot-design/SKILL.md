---
name: autopilot-design
description: "시각 산출물 디자인 파이프 entry — 토큰·컴포넌트·레퍼런스·핸드오프 통합"
argument-hint: "<design task or app path> [--scope ui|webapp|slide|icon|diagram|mixed] [--artifact standalone|project] [--from <phase>] [--intensity direct|quick|standard|strong|thorough|adversarial]"
metadata:
  group: entry
  fam: design
  modes: []
  blurb: "시각 산출물 디자인 파이프 entry — 토큰·컴포넌트·레퍼런스·핸드오프 통합"
---

> 산출물 폴더:
> - 사용자 직접 호출: `<artifact-root>/designs/<name>/`
> - autopilot-spec 에서 위임: `<artifact-root>/spec/design/`
>
> CONVENTIONS.md §5 3-tier — T1: root + design_state.yaml / T2: `00_init/`, `01_refs/`, … / T3: `_internal/` per phase.

> **역할·소유 (DESIGN_PRINCIPLES §9).** design 이 시각을 _먼저_ 잡고 code 는 _적용만_ 한다 (design = 시각 spec). **토큰은 단일 계약 — design 소유**: 디자인 토큰은 _앱이 실제 import 하는 파일_(globals.css `@theme` / tokens.css) 에만 산다. `designs/`(또는 `spec/design/`) 는 토큰 _사본이 아니라_ refs·mockup·결정 근거·specimen(=decision record, spec/prd 의 "왜" 자리). **빌트앱도 design-first** — mockup 이 아니라 _실제 돌아가는 앱 화면을 Design MCP 로 렌더_ 해서 시각 결정 (롱테일도 design 이 리드). **경계**: 방향·토큰·새 레이아웃·구조 변경=substantial → 본 skill (design-first). 한 요소 색 한 끗=trivial tweak 만 autopilot-code 직접.

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
- 검증 강도: `--intensity` 에서 파생 (별도 `--qa` 축 없음 — [CONVENTIONS §1.1](../../core/CONVENTIONS.md#11-verification-rigor-tiers-intensity-derived-canonical-sot)). default 는 standard-tier

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

### 검증 강도 (intensity 파생)
검증 rigor 는 별도 `--qa` 축이 아니라 `--intensity` 에서 파생된다 — tier 정의·매핑은 [CONVENTIONS §1.1](../../core/CONVENTIONS.md#11-verification-rigor-tiers-intensity-derived-canonical-sot) 단일 source. 본 skill 적용:
- quick-tier (`--intensity quick`) — review phase skip
- standard-tier (default) — 표준 review phase
- thorough-tier (`--intensity thorough`) — 디자인팀 critic + 외부 레퍼런스 cross-check

## Context Auto-Detection (신규 vs 재호출 자동 분기)

본 skill 은 호출 자리에서 _발화 + cwd_ 검사로 자동 분기 — `--from` 명시 없이도 동작:

### 1단계 — design_state.yaml 자동 검사

| 감지 조건 | 처리 |
|---|---|
| `<artifact-root>/designs/<name>/design_state.yaml` 또는 `<artifact-root>/spec/design/design_state.yaml` 부재 | **신규 cycle** — Phase 0 (design-init) 부터 처음 |
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

> **Intake 게이트**: 비주얼 방향성·톤·타깃 디바이스·디자인시스템 유무·브랜드 제약·산출형태가 미명세면 [CONVENTIONS.md §6.6](../../core/CONVENTIONS.md#66-autopilot-intake-gate) 1라운드 질문 먼저 (질문 뱅크는 _design_rules.md 비주얼 기본값·conceptual altitude 재사용). Phase 0 design-init 앞. 명시·재개(--from) 시 skip (별도 flag 불요).

## Pipeline Overview & Stage-worker mapping

> **Stage-dispatch (`standard+`, OPERATIONS §5.10 ③④·SD-1·SD-2)**: for `standard+`, each durable design phase below is dispatched as its own **depth-2 headless session**; the 디자인팀 mode (또는 orchestrator step) named in each phase runs *inside* that stage session. The depth-1 conductor passes only artifact paths and reads verdict/status — never phase bodies or prior-phase conversation (**file-only handoff**: each phase reads its inputs from files — `design_state.yaml` + prior-phase artifacts — never from the conductor's memory of earlier phases). Design phases carry `[CONFIRM Gate]`s — the conductor holds the gate verdict *between* dispatched phases via `design_state.yaml` phase status (다음 phase 는 진행 응답이 기록된 뒤에만 dispatch). `direct/quick` and micro-stages (산출물 없는 확인 스텝) stay inline; stage sessions never re-dispatch (depth 3+ forbidden). Per-pipe body rewrite to imperative dispatch commands is follow-up work — this block only adds the contract + the mapping below.

| stage | in-session team | input artifacts | output artifacts | write class |
|---|---|---|---|---|
| Phase 0: design-init (환경 점검 — Figma MCP·shadcn·tokens.css 부재 안내) | orchestrator (환경 프로비저닝, no sub-agent) | design 발화 + cwd | `00_init/environment_check.md`, `design_state.yaml` | init |
| Phase 1: design-refs (레퍼런스 수집) | orchestrator + `Agent(자료팀, mode=web-image-search)` (외부 검색 시) | 사용자 image / 기존 디자인 자산 / 발화 | `01_refs/brief.md`, `_internal/references/` | refs |
| Phase 2: design-tokens (color/typography/spacing/radius/shadow — single source) | orchestrator (직접, Design MCP specimen 자가검증 — sub-agent 미위임) | `01_refs/brief.md` + 기존 토큰 파일(있으면) | `02_tokens/tokens.md`, `02_tokens/specimen.html`, `tokens.css`/`tailwind.config.ts` | tokens |
| Phase 3: design-components (컴포넌트·시각 자산 만들기) | `Agent(디자인팀, mode=maker)` | `02_tokens/tokens.*`, `01_refs/brief.md` | `03_components/` (spec/mockup/code, scope 별 `preview.html`/`slides.html` 등) | components |
| Phase 4: design-review (비평 — 6축 점검) | `Agent(디자인팀, mode=verifier)` → `Agent(디자인팀, mode=critic)` | `03_components/` 렌더 산출 | `04_review/verifier.md`, `04_review/critique.md` | review (read-only critique — 03_components 산출물 미수정) |
| Phase 5: design-handoff (코드 위치·import path·재현 가이드) | orchestrator (직접, no sub-agent) | `03_components/`, `04_review/*`, `02_tokens/tokens.*` | `05_handoff/handoff.md`, `05_handoff/exports/` | handoff |

No two stages mutate the same shared file without a lock (mirrors the autopilot-code `pipeline_summary.md` lock exception) — `design_state.yaml` in particular is written by a single phase at a time in sequence (각 phase 는 CONFIRM Gate 통과 후 자기 `phases.<phase>` 항목만 갱신, 동시 쓰기 없음).

## Paper architecture figure 정책

Paper architecture diagram 은 LLM 시각 craft 한계 영역 — 디자인팀은 layout 가이드까지만 산출, 그림 자체는 생성하지 않는다. 상세·범위(2026-05-28 정책) = [references/paper-figure-policy.md](references/paper-figure-policy.md). 다른 scope(ui·webapp·slide·icon·diagram)는 대상 아님 — 아래 시각 검증 루프로 완결.

## 하네스

시각 피드백 루프(Design MCP·verifier·디자인 규칙·scaffolds·converters·post-write hook) 구성 요소 표 = [references/harness.md](references/harness.md). design-init 이 Design MCP 를 자가 프로비저닝(부재로 멈추지 않음, 스펙 §0.5).

## 시각 검증 (전 visual phase 공통 — Claude Design parity, 필수)

components·tokens·review phase 는 **Design MCP 로 렌더해서 본 것** 으로만 완료한다. 좌표·코드·XML valid 는 시각 검증이 아니다 (maker/critic 이 _눈 감고_ 좌표 부르는 실패가 반복됐음).

- **렌더 경로·scope 표·자가비평 루프**(HTML/React·SVG/diagram, 관통·overlap·정렬·위계·잘림, 최대 3-5 회전)는 [_design_rules.md §시각 자가검증 루프](../../roles/modes/design/_design_rules.md) 단일 SoT (maker/critic/verifier 공유) — 로드해 그대로 돈다.
- **사용자에 렌더 이미지를 보여준다** — 텍스트 보고만으로 완료 X (live-preview 패리티). Design MCP 미부착이면 `sharp`/`rsvg`/`mmdc` 정적 렌더 fallback.

각 phase 끝에 **[CONFIRM Gate]** — autopilot-spec 의 4 갈래 응답 패턴 그대로 (발화가 모호하면 메인 에이전트가 옵션 다시 물음, 임의 추측 X): **진행**(다음 phase) / **수정**(현 phase `--user-refine`, v2 작성) / **back-jump**(`--from <phase>`, 하위 phase reset) / **중단**(pipeline 멈춤, `design_state.yaml` 상태 보존).

## Pipeline Execution

메인 에이전트가 Skill tool 로 각 phase 를 직접 호출한다. invoke 인자·산출 파일 목록 등 실행 상세는 [references/pipeline-execution.md](references/pipeline-execution.md) — 아래는 phase 별 checkable completion criterion([CONFIRM Gate])만 잔류.

| phase | invoke | [CONFIRM Gate] |
|---|---|---|
| 0 design-init | `design-init` | "환경 점검 + Design MCP 프로비저닝 완료. refs 로 진행할까요? (진행 / 수정 / 중단)" |
| 1 design-refs | `design-refs` | "레퍼런스 정리 완료. tokens 로 진행할까요? (진행 / 수정 — 레퍼런스 추가·교체 / 중단)" |
| 2 design-tokens | `design-tokens` | "토큰 결정. components 로 진행할까요? (진행 / 수정 — 토큰 조정 / back-jump — refs 로 / 중단)" |
| 3 design-components | `design-components` | "컴포넌트 완료 (렌더 확인함). review 로 진행할까요? (진행 / 수정 — 컴포넌트 보강 / back-jump — tokens / refs 로 / 중단)" |
| 4 design-review | `design-review` | "review 통과. handoff 로 진행할까요? (진행 / 수정 — 비평 반영 / back-jump — tokens·components / 중단)" — 🔴/verifier `needs_work` 시 `phases.review: failed` + components 재호출 권장 |
| 5 design-handoff | `design-handoff` | **[Final Confirm]** "디자인 사이클 완료. (확인 / back-jump — 어느 phase 든 / 중단)" |

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
- 산출물 위치를 `<artifact-root>/spec/design/` 로 자동 설정
- `--intensity` 옵션은 autopilot-spec 의 그것 상속 (검증 rigor 는 거기서 파생)
- 완료 후 `phases.design: done` 을 autopilot-spec 의 `pipeline_state.yaml` 에 갱신

## Return Format

```
<output_path> -- ✅ Phase {N} ({phase_name}) completed
```
전체 사이클 완료 시: `<output_path> -- ✅ Design cycle completed (handoff ready)`

## Update memory

- 사용자 디자인 선호 (minimal / dense / playful, 색감, 폰트)
- 자주 만든 컴포넌트 패턴
- scope 별 phase auto-skip 판단 기준
- 외부 레퍼런스 vs 자체 디자인 비중
