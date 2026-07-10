---
name: code-test
description: "구현 결과 단계별 검증 — 품질관리팀 test 모드 sub-skill"
argument-hint: "<plan name, path, or test scope>"
metadata:
  group: sub
  fam: sub
  modes: []
  blurb: "구현 결과 단계별 검증 — 품질관리팀 test 모드 sub-skill"
---

> **Stage-session entry (`standard+` dispatch, spec/stage-dispatch SD-2)**: runs either in-session (Skill tool) or as its own depth-2 headless session dispatched by the autopilot-code conductor. Input = `plan/plan.md` verification section + `plan/checklist.md` (resolved below), read from files — never prior-stage conversation. Source is **read-only** here; write class = `test_logs/`·`_internal/test_reviews/` only. 품질관리팀 delegation stays **inside** this session.

## Plan Resolution (canonical — keep in sync with code-execute, code-test, code-report, code-refine, autopilot-code)
Resolve `$ARG` to a plan file path:
1. If it ends with `.md` → use as-is
2. If it's a directory path → append `/plan/plan.md`
3. Otherwise, fuzzy search: `ls -d <artifact-root>/plans/*$ARG* 2>/dev/null`
   - **1 match** → use `{match}/plan/plan.md`
   - **Multiple matches** → prefer folder without `_audit`/`_fix_` suffix; if still multiple, ask user
   - **No match** → fallback: treat argument as a file/directory path for direct testing

Example: `/code-test inference-refactor` → `<artifact-root>/plans/2026-03-18_inference-refactor/plan/plan.md`

## Language Rule
- All user-facing output in natural Korean (no translationese — write Korean natively, don't translate from an English draft).

## Delegate to 품질관리팀 (test 모드)
Invoke the **품질관리팀** agent in **test mode** (the agent absorbed the former 테스트팀 in 2026-05-22; specify "test 모드" in the prompt so mode dispatch is unambiguous) with the following prompt:

- If $ARG points to a plan file:
  ```
  Run graduated tests for plan: {$ARG}
  Read the plan's verification sections and the log directory's plan/checklist.md to identify targets.
  Execute Level 1 → 2 → 3 → 4 → 5 in order, stopping on first failure.
  ```

- If $ARG is a file/directory path:
  ```
  Run graduated tests on: {$ARG}
  Execute Level 1 → 2 → 3 → 4 → 5 in order, stopping on first failure.
  Skip levels that don't apply (e.g., Level 4 if no plan file).
  ```

- If $ARG is empty:
  ```
  Run graduated tests on recently changed files.
  Use git diff --name-only HEAD~1 to find targets.
  Execute Level 1 → 2 → 3 → 4 → 5 in order, stopping on first failure.
  Skip levels that don't apply (e.g., Level 4 if no plan file).
  ```

### Test Log Requirement (CRITICAL)
**Always** include this in the 품질관리팀 (test 모드) prompt. Every test must record: exact command, full stdout/stderr (last 50 lines if long), and PASS/FAIL verdict with error message.

```
Write a detailed test log to: {log_dir}/test_logs/test_report.md

Format:
## Level N: [Level Name]
### Test N.1: [description]
**Command:** [exact command]
**Output:** [stdout/stderr]
**Verdict:** PASS / FAIL — [reason]
```

## Verification Assurance
`code-test` is the concrete final `verify` stage. It is not hardcoded to thorough and does not automatically launch a parallel QA loop. Read the selected QA/intensity context from the plan frontmatter or caller prompt.

| QA level | Verification behavior | Optional adequacy review |
|---|---|---|
| `quick` | Run the narrowest applicable concrete command/check and record skip reasons. | none by default |
| `light` | Run focused syntax/import/smoke or the caller's explicit command. | fast review only if risk-selected |
| `standard` | Run applicable graduated levels and capture command evidence. | one focused test-adequacy review when changed surface is nontrivial |
| `thorough` | Broader target coverage plus behavioral runtime observation where user-facing surfaces changed. | selected parallel/depth2 review only if `intensity=thorough` selected it |
| `adversarial` | Thorough verification plus security/failure-mode/external adversary evidence where the track supports it. | must prove the adversary/security pass ran before claiming it |

After the 품질관리팀 (test mode) agent returns, read the test log and decide whether the selected assurance budget requires a separate adequacy review. If yes, run the focused reviewer(s) and append issues to the test report. If no, report the concrete verification verdict directly. Do not mutate source files while acting in `code-test`; any hotfix belongs to the caller's retry/fix stage.

## Report Results
1. Relay the verification results to the caller with the report path, executed commands, skipped levels, blockers, and first actionable failure if any.
2. If all selected levels passed and any selected adequacy review passed, return success. Do not commit; commit/merge ownership belongs to the caller or `code-report`/orchestrator.
3. If any level failed, return failure with enough context for the caller's retry/fix stage. Do not invoke a hotfix agent from `code-test`; this keeps final verification read-only and prevents hidden mutation inside QA.

> Record the verdict and blocker context so the pipeline skill can decide whether to open its bounded retry/fix stage.

## Log Directory Resolution
- If $ARG points to a plan file: log directory is the task root (grandparent of `plan/plan.md`).
  Example: `<artifact-root>/plans/2026-03-18_refactor/plan/plan.md` → `<artifact-root>/plans/2026-03-18_refactor/`
- If no plan file: use `<artifact-root>/tests/` with a date-stamped subdirectory.

## Task
Test: $ARG
