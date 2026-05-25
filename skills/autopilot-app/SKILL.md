---
name: autopilot-app
description: "Unified app development pipeline — orchestrates app-init → app-spec → autopilot-design → app-build → app-qa → app-ship → app-iterate. For building user-facing web/mobile apps where the user is a general consumer (not a developer). Distinct from autopilot-code (library/research code, user = developer)."
argument-hint: "<app or feature description> [--from <phase>] [--qa quick|light|standard|thorough] [--user-refine]"
---

> 산출물 폴더: `.claude_reports/apps/<app-name>/` (CONVENTIONS.md §5 3-tier — T1: root + pipeline_state.yaml / T2: `00_init/`, `01_spec/`, … / T3: `_internal/` per phase).

## Default Invocation Rule (메인 Claude 자동 라우팅)

본 skill 은 글로벌 [`CLAUDE.md`](../../CLAUDE.md) §6 "autopilot-* 호출 패턴" 의 _컨펌 의무_ 적용 대상.

### Trigger 신호 (자연어 발화 예시)

- "X 앱 만들어줘" / "Y 서비스 만들어줘" / "Z 웹사이트 짜줘"
- "이 앱에 X 기능 추가" / "사용자가 X 할 수 있는 페이지"
- 기존 `.claude_reports/apps/<name>/` + 재개 신호 ("이어서 진행", "다음 phase 부터")

### Default 옵션 권장값 (컨펌 시 메인 Claude 가 제안)

- `--from`: auto-detect — `pipeline_state.yaml` 발견 시 마지막 성공 phase 다음부터, 부재 시 `init` 부터
- `--qa`: `standard` (global §6 high-stakes 신호 시 thorough 자동 상향)
- `--user-refine`: **off** (사용자 명시 시만 on)

### Override 1순위 — autopilot 우회

- 작은 작업 (한 파일 수정·rename·cleanup) — `Agent(개발팀)` 직접 호출
- 디자인만 — `/autopilot-design` 직접 호출
- 라이브러리·연구코드 — `/autopilot-code` 사용 (autopilot-app 은 사용자 앱 전용)
- `/autopilot-app <args>` slash 직접 입력 — 컨펌 skip

## Language Rule
- Think and reason in English internally. Write all user-facing output in Korean.
- Code identifiers, file paths, technical terms stay in English.

## Argument Parsing

### --from (optional, auto-detect default)
- `init` / `spec` / `design` / `build` / `qa` / `ship` / `iterate`
- Auto-detect from `pipeline_state.yaml`: 마지막 `done` phase 다음부터

### --qa
- `quick` (skip Visual QA, 기본 functional 만)
- `light` (single reviewer)
- `standard` (default — code-review + test + critic)
- `thorough` (다축 axis-decomposed review)

### --user-refine
- On 시: spec phase 끝에서 사용자 메모 받고 refine loop

## Pipeline Overview

```
Phase 0: app-init        (cold start — pipeline_state.yaml 부재 시만)
Phase 1: app-spec        (PRD 작성·refine)
Phase 2: autopilot-design (UI 있는 경우만 — 자동 위임)
Phase 3: app-build       (백엔드 + 프론트엔드 구현)
Phase 4: app-qa          (기능 + 시각 검증)
Phase 5: app-ship        (배포·CI/CD)
Phase 6: app-iterate     (피드백 → spec 갱신, loop back to Phase 1)
```

각 phase 끝에 **[CONFIRM Gate]** — 사용자 OK 받은 후 다음 phase.

## Pipeline Execution

You (메인 Claude) orchestrate by invoking each skill directly via the Skill tool.

### Phase 0: app-init

If `pipeline_state.yaml` 부재 (신규 앱) OR `--from init` 명시:

Invoke Skill: `app-init` with the app description as args.

결과: `.claude_reports/apps/<app-name>/00_init/` + `pipeline_state.yaml` 생성

**[CONFIRM Gate 0]** — "Phase 0 init 완료. 환경/스택 결정 보고서 검토 후 spec 으로 진행할까요?"

### Phase 1: app-spec

Invoke Skill: `app-spec` with the task/feature description + `--app <name>` as args.

결과: `.claude_reports/apps/<app-name>/01_spec/PRD.md` + `scenarios.md`

If `--user-refine`: 사용자 메모 받은 후 refine. `_internal/refine_v{N}.md` 에 버전.

**[CONFIRM Gate 1]** — "PRD 작성 완료. design 으로 진행할까요?"

### Phase 2: autopilot-design (UI 있는 경우만)

PRD 의 시나리오에 UI 요소가 있는지 확인:
- 사용자가 _화면_ 으로 상호작용 → autopilot-design 자동 위임
- CLI tool / pure API → skip

Invoke Skill: `autopilot-design` with the app path as args.

결과: `.claude_reports/apps/<app-name>/02_design/` (디자인 토큰, 컴포넌트 mockup, 시각 결정)

**[CONFIRM Gate 2]** — "디자인 완료. build 로 진행할까요?"

### Phase 3: app-build

Invoke Skill: `app-build` with the app path as args.

내부적으로 개발팀 backend / frontend 모드 병렬 호출.

결과: `.claude_reports/apps/<app-name>/03_build/build_log.md` + `_internal/step_logs/`

**[CONFIRM Gate 3]** — "구현 완료. QA 로 진행할까요?"

### Phase 4: app-qa

Invoke Skill: `app-qa` with the app path as args.

내부: 품질관리팀 code-review + test + (UI 있으면) 디자인팀 critic.

결과: `.claude_reports/apps/<app-name>/04_qa/`

If 🔴 발견:
- `pipeline_state.yaml` 의 `phases.qa: failed` 기록
- 사용자에 보고 후 fix plan:
  - Invoke Skill: `app-build` 다시 (fix scope 명시)
  - 또는 `Agent(개발팀, mode=<backend|frontend>)` 직접 호출

**[CONFIRM Gate 4]** — "QA 통과. 배포할까요?"

### Phase 5: app-ship

Invoke Skill: `app-ship` with the app path as args.

호스팅·CI/CD·환경변수 셋업 _안내_. 실제 배포 명령은 사용자 confirm 후.

결과: `.claude_reports/apps/<app-name>/05_ship/deploy_record.md`

**[CONFIRM Gate 5]** — "배포 완료. 사용 후 피드백 있을 때 iterate phase 호출하세요."

### Phase 6: app-iterate

사용자가 _실제 사용 후 피드백_ 있을 때:

Invoke Skill: `app-iterate` with feedback + app path as args.

결과: `06_iterate/feedback_log.md` + 다음 사이클 spec 으로 인계 안내.

**[Loop back to Phase 1]** — 새 사이클 시작. `pipeline_state.yaml` 의 `current_cycle` 증가.

## Pipeline state 관리

`.claude_reports/apps/<app-name>/pipeline_state.yaml`:

```yaml
app_name: <name>
created: <YYYY-MM-DD>
current_cycle: 1
stack:
  framework: Next.js
  db: Prisma + Turso
  ...
phases:
  init: done
  spec: done
  design: done
  build: done
  qa: done
  ship: pending
  iterate: pending
last_updated: <timestamp>
```

각 sub-skill 이 자기 phase 완료 시 `phases.<name>: done` 으로 갱신.

## Return Format

마지막 phase 완료 시:
```
.claude_reports/apps/<app-name>/ -- ✅ Phase {N} ({phase_name}) completed
```

전체 사이클 완료 시:
```
.claude_reports/apps/<app-name>/ -- ✅ Cycle {N} completed (ship done)
```

## Update memory

- 자주 만난 phase 게이트 보강 사항
- 사용자 선호 (스택, QA 강도, refine 자주 vs 적게)
- 프로젝트별 특수 흐름 (예: "home-os 는 Phase 2 design skip — 기존 토큰 재사용")
- design phase 위임 vs skip 판단 기준
