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
| `standard` | (`frame` + `frame-alternative`) → code-plan → plan-check → code-execute → impl-review → code-test → code-report | Required | Run the route-declared 2-way framing exploration with `balanced-deep` + `light` profiles and distinct perspectives |
| `strong` | 3-way frame → 2-way plan → plan-check arbitration → execute → 2-way implementation review → test → report | Required | Spend cheap asymmetric breadth early, then converge through the declared arbiters; every group remains cross-harness-first |
| `thorough`/`adversarial` | strong graph + 3-way plan and 3-way implementation review + deeper rigor | Required | Use the registry-declared third implementation-risk/failure-mode legs; never invent or widen a group outside the sealed route |

**`standard+` dispatch**: Run every durable compiled node as dispatch depth 2. Start each sealed `parallel_group` of 2–4 legs with one `dispatch-batch --parallel-group` transaction, never member-by-member. The dispatch-depth-1 conductor passes artifact paths, reads only verdict/status, and yields while the adapter supervisor joins the exact child batch. Cross-harness means at least two harness families across the group; model-profile and perspective asymmetry are independently sealed and reported. Use `dispatch-wait` only for an explicit `poll-fallback`. Only `direct` and `quick` keep micro-stages inline.

## Mode Routing

- `dev`: add features, refactor, or implement. `direct|quick` shorten the full pipeline; `standard+` uses framing, `code-plan`, durable `plan-check`, optional `code-refine`, `code-execute`, `impl-review`, `code-test`, and `code-report`.
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
