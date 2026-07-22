# autopilot-code

Code-work entrypoint. Detect spec context and close the `plan → execute → test → report` loop at the selected intensity. This file defines routing and stage contracts; load the relevant reference only when its detailed policy is needed.

## Quick Contract

- Default output: `<artifact-root>/plans/<date>_<slug>/`. `direct` creates no durable plan; `quick` uses a micro-plan; `standard+` writes the plan, checklist, `pipeline_summary`, development logs, and test logs.
- When a spec exists, emit a one-line `spec-significance` judgment before editing code. Route spec-significant changes through an `autopilot-spec` update first.
- Recheck git and worktree state at entry and immediately before durable write-back or commit. Stop on an active merge/rebase, detached HEAD, or an unexpected HEAD change.
- Do not parallelize QA at every stage. Scale `plan-check` and final `code-test` from the rigor derived from intensity (CONVENTIONS §1.1).
- Follow an explicit artifact or audience language for user-facing reports. Otherwise, use the conversation language.

## Reference Index

| File | When to load (mandatory) | Content |
|---|---|---|
| `context-and-guards.md` | Every invocation (required) | Artifact, spec, and git guards; spec-mode detection; design/app/library/API/CLI/research boundaries; experiment-ready input; invocation routing |
| `arguments-and-decisions.md` | When interpreting arguments, `--from`, pause/resume, or active-plan conflicts | Argument parsing, defaults, active/partial/complete plan handling, and plan-path resolution |
| `dev-pipeline.md` | When running `--mode dev` | Stage orchestration, plan check, retry behavior, and `analyze-project` update |
| `debug-audit.md` | When running `--mode debug` or `audit` | Debug diagnosis and fix flow; audit fan-out and autofix workflow |
| `pipeline-summary-safety.md` | At terminal, failed, partial, rollback, or summary states | Summary template, terminal-state reporting, and common safety rules |

## Argument Shape

`--mode dev|debug|audit <task/plan/error description> [--from <step>] [--intensity direct|quick|standard|strong|thorough|adversarial] [--user-refine]`

Defaults:

- `--mode`: default to `dev`; infer `debug` when the request is centered on an error log or traceback.
- `--intensity`: choose from scope and risk. Use `direct` for a one-line task, `quick` for a small scoped change, and `standard+` for multi-stage or multi-file work. Verification rigor is derived from intensity rather than selected separately (CONVENTIONS §1.1).
- `--user-refine`: enable only when the user explicitly requests a review or note-taking pause.

## Stage Graph

| Intensity | Graph | Durable artifact | Review policy |
|---|---|---|---|
| `direct` | intake → produce → sanity/report | None | No independent QA |
| `quick` | intake → orient-lite → micro-plan → plan-check-lite → produce → verify-lite → report | None by default | Inline check with 3-4 questions |
| `standard` | code-plan → plan-check → bounded dispatch-depth-2 verifier/planner when separable → synthesize → code-execute → code-test → code-report | Required | Use bounded dispatch-depth-2 planning or verification for separable work |
| `strong` | standard + cross-harness 2-way replicate-and-merge at the riskiest review (route adds `impl-review-replica`) | Required | Dispatch both legs on different harness/model families; merge verdicts, stricter wins |
| `thorough`/`adversarial` | strong + multi-axis dispatch-depth-2 planner/verifier/adversary synthesis | Required | Synthesize dispatch-depth-2 reports concisely |

**`standard+` dispatch**: Run each durable stage (`code-plan`, `code-execute`, `code-test`, and `code-report`) in its own dispatch-depth-2 headless session. The dispatch-depth-1 conductor passes artifact paths, reads only verdict and status, and uses deterministic one-shot `dispatch-wait` polling for wait and harvest (dev-pipeline Steps 1-7; OPERATIONS §5.10 and SD-14). Keep `direct`, `quick`, and plan-check micro-stages inline.

## Mode Routing

- `dev`: add features, refactor, or implement. `direct|quick` shorten the full pipeline; `standard+` uses `code-plan`, optional `code-refine`, `code-execute`, `code-test`, and `code-report`.
- `debug`: diagnose the root cause before planning a fix. Proceed when the cause is clear; ask for a choice only when materially different causes remain plausible.
- `audit`: inspect a codebase or app comprehensively and apply low-risk fixes. Keep review fan-out read-only; make and verify changes in a worktree based on current HEAD before harvest.

## Critical Gates

1. Resolve the artifact root by preferring `.agent_reports` and falling back to legacy `.claude_reports`.
2. Run git-state preflight and remember starting `HEAD`.
3. If `spec/` exists, read `spec/prd.md` and emit `spec-significance`.
4. Choose stage graph from intensity before QA.
5. Before source write-back or commit, re-run git-state preflight.
6. On any terminal state, write `pipeline_summary.md` before reporting to the user.

> Treat the [Reference Index](#reference-index) as the single source for reference files, load points, and contents.
