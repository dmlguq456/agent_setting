---
name: autopilot-code
description: "Use when starting or routing any code task (library/research/app). 코드 작업 일반 entry — 라이브러리·연구·앱 모두 커버, spec 컨텍스트 자동 감지"
argument-hint: "--mode dev|debug <task/plan/error description> [--from <step>] [--intensity direct|quick|standard|strong|thorough|adversarial] [--user-refine]"
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
- QA는 stage마다 무조건 병렬화하지 않는다. `plan-check`와 최종 `code-test`는 intensity에서 파생된 rigor(CONVENTIONS §1.1)에 맞춰 커진다.
- User-facing reports follow the user's communication language unless an explicit audience, publication, or artifact-language requirement overrides it.

## Reference Index

| 파일 | 언제 로드 (의무) | 내용 |
|---|---|---|
| `references/context-and-guards.md` | 모든 호출 (필수) | artifact/spec/git guard 요약, spec mode 감지, design/app/library/api/cli/research guard, experiment-ready input, invocation triggers |
| `references/arguments-and-decisions.md` | 인자 해석·`--from`·pause/resume·active plan 충돌 자리 | argument parsing, default decisions, active/partial/done plan handling, plan path resolution |
| `references/dev-pipeline.md` | `--mode dev` 실행 시 | dev mode stage-by-stage orchestration, plan-check, retry, analyze-project update |
| `references/debug-audit.md` | `--mode debug`\|`audit` 실행 시 | debug diagnosis/fix flow, audit fan-out/autofix workflow |
| `references/pipeline-summary-safety.md` | terminal state·실패/부분성공/rollback·summary 작성 자리 | summary template, terminal-state reporting, common safety rules |

## Argument Shape

`--mode dev|debug|audit <task/plan/error description> [--from <step>] [--intensity direct|quick|standard|strong|thorough|adversarial] [--user-refine]`

Defaults:

- `--mode`: 생략 시 dev. 에러 로그/traceback이면 debug로 추론 가능.
- `--intensity`: 범위와 위험으로 선택한다. 단발 1줄급은 direct, 작은 scoped change는 quick, 다단계/다파일은 standard+. 검증 rigor는 별도 축이 아니라 이 intensity에서 파생된다 (CONVENTIONS §1.1).
- `--user-refine`: 사용자가 검토/메모 pause를 명시한 경우만 켠다.

## Stage Graph

| Intensity | Graph | Durable artifact | Review policy |
|---|---|---|---|
| `direct` | intake -> produce -> sanity/report | 없음 | 독립 QA 없음 |
| `quick` | intake -> orient-lite -> micro-plan -> plan-check-lite -> produce -> verify-lite -> report | 기본 없음 | 3-4문항 inline check |
| `standard` | code-plan -> plan-check -> bounded depth2 verifier/planner? -> synth -> code-execute -> code-test -> code-report | 필수 | separable work는 depth2 verifier/planner 기본 |
| `strong` | standard + one risk-focused depth2 review | 필수 | 가장 위험한 지점 1회 |
| `thorough`/`adversarial` | standard + multi-axis depth2 planner/verifier/adversary synthesis | 필수 | depth2 worker report를 짧게 합성 |

**`standard+` dispatch**: 각 durable 스테이지(code-plan/execute/test/report)는 depth-2 headless 세션으로 분사된다 — depth-1 conductor 는 산출물 경로만 넘기고 verdict/status 만 읽으며, 대기·수확은 one-shot wait(dispatch-wait) 폴링으로 결정론화한다 (dev-pipeline Step 1~7, OPERATIONS §5.10 ③④·SD-14). `direct/quick` 과 plan-check 마이크로-스테이지는 inline.

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

> reference 파일 목록·로드 시점·내용은 위 [Reference Index](#reference-index) 표 참조 (단일 표).
