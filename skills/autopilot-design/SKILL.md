---
name: autopilot-design
description: "Unified design pipeline — orchestrates design-init → design-refs → design-tokens → design-components → design-review → design-handoff. For visual artifacts across UI/UX, slides, diagrams, icons, logos. Can be invoked standalone or auto-delegated from autopilot-spec Phase 2. Distinct from autopilot-draft (text-only documents) — autopilot-design handles visual deliverables."
argument-hint: "<design task or app path> [--scope ui|slide|icon|diagram|mixed] [--from <phase>] [--qa quick|standard|thorough]"
---

> 산출물 폴더:
> - 사용자 직접 호출: `.claude_reports/designs/<name>/`
> - autopilot-spec 에서 위임: `.claude_reports/specs/<name>/02_design/`
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
- `ui` — 프론트 UI (컴포넌트, 페이지, 레이아웃)
- `slide` — 발표 슬라이드 비주얼
- `icon` — 아이콘·로고 단일 자산
- `diagram` — mermaid, excalidraw 아키텍처 도식
- `mixed` — 위 여러 영역 통합

scope 에 따라 일부 phase auto-skip:
- `icon`: tokens skip 가능 (단일 자산), components skip
- `diagram`: tokens·components skip, refs + handoff 중심

### --from (auto-detect default)
- `init` / `refs` / `tokens` / `components` / `review` / `handoff`
- design_state.yaml 발견 시 마지막 `done` phase 다음부터

### --qa
- `quick` (review phase skip)
- `standard` (default)
- `thorough` (디자인팀 critic + 외부 레퍼런스 cross-check)

## Pipeline Overview

```
Phase 0: design-init        (환경 점검 — Figma MCP, shadcn, tokens.css 부재 안내)
Phase 1: design-refs        (레퍼런스 수집 — 사용자 image, 외부 검색, 기존 디자인)
Phase 2: design-tokens      (color / typography / spacing / radius / shadow — single source)
Phase 3: design-components  (컴포넌트·시각 자산 만들기 — 디자인팀 maker)
Phase 4: design-review      (비평 — 디자인팀 critic, 6축 점검)
Phase 5: design-handoff     (코드 위치·import path·재현 가이드)
```

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

결과: `00_init/environment_check.md` + `design_state.yaml` 생성

**[CONFIRM Gate 0]** — "환경 점검 완료. refs 로 진행할까요? (진행 / 수정 / 중단)"

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
- `02_tokens/tokens.css` 또는 `tailwind.config.ts` — 실제 토큰 파일

기존 토큰 파일 발견 시 _확장_ (덮어쓰기 X).

**[CONFIRM Gate 2]** — "토큰 결정. components 로 진행할까요? (진행 / 수정 — 토큰 조정 / back-jump — refs 로 / 중단)"

### Phase 3: design-components

Invoke Skill: `design-components` with the design path as args.

내부: `Agent(디자인팀, mode=maker)` 호출.

결과:
- `03_components/` — 컴포넌트 spec / mockup / 실제 코드
- scope 따라:
  - `ui`: shadcn/ui 컴포넌트 + custom
  - `slide`: 슬라이드 비주얼 가이드 (마크다운)
  - `icon`: SVG 또는 이미지
  - `diagram`: mermaid / excalidraw

**[CONFIRM Gate 3]** — "컴포넌트 완료. review 로 진행할까요? (진행 / 수정 — 컴포넌트 보강 / back-jump — tokens / refs 로 / 중단)"

### Phase 4: design-review

`--qa quick` 시 skip. 그 외:

Invoke Skill: `design-review` with the design path as args.

내부: `Agent(디자인팀, mode=critic)` 호출.

결과: `04_review/critique.md` — 6축 (위계 / 정렬 / 접근성 / 반응형 / 흐름 / 톤) 별 발견 사항.

🔴 발견 시:
- `design_state.yaml` 의 `phases.review: failed`
- 사용자에 보고 후 components phase 재호출 권장

**[CONFIRM Gate 4]** — "review 통과. handoff 로 진행할까요? (진행 / 수정 — 비평 반영 / back-jump — tokens·components / 중단)"

### Phase 5: design-handoff

Invoke Skill: `design-handoff` with the design path as args.

결과:
- `05_handoff/handoff.md` — 사용된 컴포넌트·토큰 위치, frontend 개발자가 import 할 path, 재현 가이드
- autopilot-spec 에서 위임된 경우: 호출자에 결과 path 반환

**[Final Confirm]** — "디자인 사이클 완료. (확인 / back-jump — 어느 phase 든 / 중단)"

## Design state 관리

`design_state.yaml`:

```yaml
design_name: <name>
scope: ui  # or slide/icon/diagram/mixed
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
- 산출물 위치를 `.claude_reports/specs/<name>/02_design/` 로 자동 설정
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
