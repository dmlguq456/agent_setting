---
name: autopilot-code
description: "코드 작업 일반 entry — 라이브러리·연구·앱 모두 커버, spec 컨텍스트 자동 감지"
argument-hint: "--mode dev|debug <task/plan/error description> [--from <step>] [--intensity direct|quick|standard|strong|thorough|adversarial] [--qa quick|light|standard|thorough|adversarial] [--user-refine]"
metadata:
  group: entry
  fam: code
  modes: [dev, debug, audit]
  blurb: "코드 작업 일반 entry — 라이브러리·연구·앱 모두 커버, spec 컨텍스트 자동 감지"
---

# autopilot-code

코드 작업 entry. spec 컨텍스트를 감지하고 선택된 intensity에 맞춰 `plan -> execute -> test -> report` 흐름을 닫는다. 이 파일은 라우터와 stage contract만 담고, 세부 정책은 필요할 때 아래 reference를 읽는다.

## Quick Contract

- 산출물: 기본 `<artifact-root>/plans/<date>_<slug>/`; `direct`는 durable plan 없음, `quick`은 micro-plan, `standard+`는 plan/checklist/pipeline_summary/dev_logs/test_logs.
- spec이 있으면 코드 편집 전 `spec-significance`를 한 줄로 판정한다. spec-significant 변경은 `autopilot-spec` update를 먼저 거친다.
- git/worktree 상태는 진입 시와 durable write-back/commit 직전에 재확인한다. merge/rebase/detached/head 변경은 중단한다.
- QA는 stage마다 무조건 병렬화하지 않는다. `plan-check`와 최종 `code-test`가 선택된 intensity/QA에 맞춰 커진다.
- 보고는 한국어로 한다.

## Required Reads

- 모든 호출: `references/context-and-guards.md`의 artifact/spec/git guard 요약을 확인한다.
- 인자 해석, `--from`, pause/resume, active plan 충돌: `references/arguments-and-decisions.md`.
- `--mode dev`: `references/dev-pipeline.md`.
- `--mode debug` 또는 `--mode audit`: `references/debug-audit.md`.
- terminal state, 실패/부분성공/rollback, 사용자 보고 전 summary 작성: `references/pipeline-summary-safety.md`.

## Argument Shape

`--mode dev|debug|audit <task/plan/error description> [--from <step>] [--intensity direct|quick|standard|strong|thorough|adversarial] [--qa quick|light|standard|thorough|adversarial] [--user-refine]`

Defaults:

- `--mode`: 생략 시 dev. 에러 로그/traceback이면 debug로 추론 가능.
- `--intensity`: 범위와 위험으로 선택한다. 단발 1줄급은 direct, 작은 scoped change는 quick, 다단계/다파일은 standard+.
- `--qa`: 기본은 intensity와 함께 간다. 명시 QA는 assurance override이지 full pipeline 강제 스위치가 아니다.
- `--user-refine`: 사용자가 검토/메모 pause를 명시한 경우만 켠다.

## Stage Graph

| Intensity | Graph | Durable artifact | Review policy |
|---|---|---|---|
| `direct` | intake -> produce -> sanity/report | 없음 | 독립 QA 없음 |
| `quick` | intake -> orient-lite -> micro-plan -> plan-check-lite -> produce -> verify-lite -> report | 기본 없음 | 3-4문항 inline check |
| `standard` | code-plan -> plan-check -> bounded depth2 verifier/planner? -> synth -> code-execute -> code-test -> code-report | 필수 | separable work는 depth2 verifier/planner 기본 |
| `strong` | standard + one risk-focused depth2 review | 필수 | 가장 위험한 지점 1회 |
| `thorough`/`adversarial` | standard + multi-axis depth2 planner/verifier/adversary synthesis | 필수 | depth2 worker report를 짧게 합성 |

## Mode Routing

- `dev`: 기능 추가, 리팩터, 구현 작업. `direct|quick`은 full sub-skill pipeline을 줄이고, `standard+`는 `code-plan`, optional `code-refine`, `code-execute`, `code-test`, `code-report`를 사용한다.
- `debug`: root cause를 먼저 직접 진단한다. 원인이 명확하면 fix plan으로 진행하고, 원인이 복수 후보면 그때만 사용자 선택이 필요하다.
- `audit`: 코드베이스/앱 전수 점검 + 저위험 autofix. 리뷰 fan-out은 read-only, 수정은 current HEAD 기반 worktree에서 검증 후 harvest한다.

## Critical Gates

1. Resolve artifact root (`.agent_reports` 우선, legacy `.claude_reports` fallback).
2. Run git-state preflight and remember starting `HEAD`.
3. If `spec/` exists, read `spec/prd.md` and emit `spec-significance`.
4. Choose stage graph from intensity before QA.
5. Before source write-back or commit, re-run git-state preflight.
6. On any terminal state, write `pipeline_summary.md` before reporting to the user.

## Reference Map

- `references/context-and-guards.md`: spec mode 감지, design/app/library/api/cli/research guard, experiment-ready input, invocation triggers.
- `references/arguments-and-decisions.md`: argument parsing, default decisions, active/partial/done plan handling, plan path resolution.
- `references/dev-pipeline.md`: dev mode stage-by-stage orchestration, plan-check, retry, analyze-project update.
- `references/debug-audit.md`: debug diagnosis/fix flow and audit fan-out/autofix workflow.
- `references/pipeline-summary-safety.md`: summary template, terminal-state reporting, common safety rules.
