# code-test

> This README summarizes the portable capability for users and maintainers. The model-neutral contract lives under `<agent-home>/capabilities/`; `SKILL.md` in this directory provides shared guidance for runtime-specific projections.

## Overview

Record concrete verification evidence after code-execute or on demand. code-test is a read-only final verification stage: it does not open its own hotfix, commit, or parallel QA fan-out. The selected `intensity` and `qa_level` determine test breadth and whether test-adequacy review is required.

## Invocation

```text
/code-test <plan name, path, or test scope>
```

## Plan resolution

The single authority for resolving `$ARG` is [autopilot-code plan resolution](../autopilot-code/references/arguments-and-decisions.md#plan-resolution). When no plan matches, code-test may interpret the argument as a file or directory to test.

## Verification — `qa/test` unit

Run the applicable graduated verification levels from 1 through 5 and stop at the first failure. For a user-facing surface change, add Level 5b behavioral runtime observation when the selected assurance permits it.

### Test-log requirement

Record every command in `{log_dir}/test_logs/test_report.md`, including the exact command, relevant stdout or stderr excerpt, and a `PASS`, `FAIL`, `SKIP`, or `BLOCKED` reason.

## Assurance

- `quick`: one narrow concrete check with reasons for anything skipped.
- `light`: focused syntax, import, smoke, or caller-specified command.
- `standard`: every applicable graduated level with command evidence.
- `thorough`: broader target coverage, runtime observation for surface changes, and test-adequacy review when needed.
- `adversarial`: security, failure-mode, or external-adversary evidence when required by the selected graph and risk.

## Result

Return a success or failure verdict and the report path in the user's communication language. On failure, the caller or orchestrator decides whether to open a bounded retry or fix stage. code-test does not modify source, invoke a hotfix agent, or commit automatically.

---

*Portable capability contract: `<agent-home>/capabilities/code-test.md`; shared skill guidance: `<agent-home>/skills/code-test/SKILL.md`.*
