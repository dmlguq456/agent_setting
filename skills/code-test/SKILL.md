---
# GENERATED METADATA — edit harness-manifest.json, then run tools/generate.py.
name: code-test
description: "Use when invoking the portable code-test capability. Verify implementation results in stages and record evidence."
argument-hint: "<plan name, path, or test scope> [--intensity direct|quick|standard|strong|thorough|adversarial]"
metadata:
  group: sub
  fam: sub
  modes: []
  blurb: "Verify implementation results in stages and record evidence."
---

# code-test

> **Stage-session entry (`standard+` dispatch, spec/stage-dispatch SD-2)**: Run in-session or as an isolated depth-2 stage worker dispatched by the `autopilot-code` conductor. Read the verification section in `plan/plan.md` and marks in `plan/checklist.md` from disk; never depend on prior-stage conversation. Source is read-only in this stage. The write class is `test_logs/` and `_internal/test_reviews/`. Any `qa-team` delegation remains inside this stage session.

> **Plan resolution**: Treat [arguments-and-decisions.md#plan-resolution](../autopilot-code/references/arguments-and-decisions.md) as the single authority for resolving `$ARG`. If no plan matches, interpret the argument as the file or directory test target instead of returning a plan-resolution error.

> **Language rule**: Follow the audience and artifact language contract in [arguments-and-decisions.md#language-rule](../autopilot-code/references/arguments-and-decisions.md). Preserve commands, paths, test names, identifiers, and raw output.

## Run Graduated Tests

Invoke `qa-team` in test mode. Select one prompt form:

- Plan path:

  ```text
  Run graduated tests for plan: {$ARG}
  Read the plan verification sections and plan/checklist.md in the task root to identify targets.
  Execute Level 1 → 2 → 3 → 4 → 5 in order, stopping on the first failure.
  ```

- File or directory path:

  ```text
  Run graduated tests on: {$ARG}
  Execute Level 1 → 2 → 3 → 4 → 5 in order, stopping on the first failure.
  Skip levels that do not apply, such as Level 4 when no plan exists.
  ```

- Empty argument:

  ```text
  Run graduated tests on recently changed files.
  Use git diff --name-only HEAD~1 to find targets.
  Execute Level 1 → 2 → 3 → 4 → 5 in order, stopping on the first failure.
  Skip levels that do not apply, such as Level 4 when no plan exists.
  ```

## Test Log Contract

Always include this requirement in the `qa-team` test prompt. Record the exact command, full stdout/stderr or the last 50 lines when long, and a PASS/FAIL verdict with the error reason.

```text
Write a detailed test log to: {log_dir}/test_logs/test_report.md

Format:
## Level N: [Level Name]
### Test N.1: [description]
**Command:** [exact command]
**Output:** [stdout/stderr]
**Verdict:** PASS / FAIL — [reason]
```

Run test commands through the active adapter's bounded verification runner when its contract requires one. Preserve the actual exit status in the log.

## Verification Assurance

This is the concrete final verify stage. Derive rigor from plan frontmatter or caller intensity; do not hardcode Thorough or automatically open a parallel QA loop.

| Rigor | Concrete verification | Optional adequacy review |
|---|---|---|
| `quick` | Run the narrowest applicable command or check and record skip reasons | None by default |
| `light` | Run focused syntax, import, smoke, or caller-specified checks | One fast review only when risk selects it |
| `standard` | Run applicable graduated levels and capture command evidence | One focused adequacy review for a nontrivial change surface |
| `thorough` | Broaden target coverage and add behavioral runtime observation for changed user-facing surfaces | Parallel or depth-2 review only when selected by `intensity=thorough` |
| `adversarial` | Thorough verification plus applicable security, failure-mode, and external-adversary evidence | Prove every claimed adversary or security pass ran |

After `qa-team` returns, read `test_logs/test_report.md`. Run a separate adequacy review only when the selected assurance budget requires it, and append its findings to the report. Otherwise return the concrete verification verdict directly.

Do not modify source or invoke a hotfix worker from this stage. Any repair belongs to the caller's bounded retry/fix path.

## Report Results

Return the report path, executed commands, skipped levels and reasons, blockers, and the first actionable failure when present.

- Success requires every selected level and selected adequacy review to pass.
- Failure must include enough evidence for the caller to open a bounded retry/fix stage.
- Do not commit or merge; ownership remains with the caller or orchestrator.
- Record verdict and blockers for the pipeline decision record.

## Log Directory

- Plan path: use the task root above `plan/`; for example, `<artifact-root>/plans/2026-03-18_refactor/plan/plan.md` → `<artifact-root>/plans/2026-03-18_refactor/`.
- No plan: use a date-stamped directory under `<artifact-root>/tests/`.

## Task

Test: $ARG
