---
name: code-refine
description: "사용자 메모·QA 피드백 반영해 기존 plan 정정 — sub-skill"
argument-hint: "<plan name or path> [--qa quick|light|standard|thorough|adversarial]"
metadata:
  group: sub
  fam: sub
  modes: []
  blurb: "사용자 메모·QA 피드백 반영해 기존 plan 정정 — sub-skill"
---

## Plan Resolution (canonical — keep in sync with code-execute, code-test, code-report, code-refine, autopilot-code)
Resolve `$ARGUMENTS` to plan file paths. Always resolve BOTH `plan.md` and `plan_ko.md`:
1. If it ends with `.md` → use as-is; derive the other file by path swap (`plan.md` ↔ `plan_ko.md`)
2. If it's a directory path → append `/plan/plan.md` (English) and `/plan/plan_ko.md` (Korean)
3. Otherwise, fuzzy search: `ls -d <artifact-root>/plans/*$ARGUMENTS* 2>/dev/null`
   - **1 match** → use `{match}/plan/plan.md` and `{match}/plan/plan_ko.md`
   - **Multiple matches** → prefer folder without `_audit`/`_fix_` suffix; if still multiple, ask user
   - **No match** → report error

Example: `/code-refine inference-refactor` → English: `.../plan/plan.md`, Korean: `.../plan/plan_ko.md`

## Language Rule
- All user-facing output in natural Korean (no translationese — write Korean natively, don't translate from an English draft).

## Delegate to 기획팀
Invoke the **plan-team** (기획팀) agent as a subagent with the following prompt:

```
Refine mode. Update an existing plan based on user memos.

Korean plan file: {$ARGUMENTS}
English plan file: {$ARGUMENTS with plan_ko.md replaced by plan.md}

Read the Korean plan and find all user memos. Memos can appear in any of these formats:
- `<!-- memo: ... -->` (standard memo tag)
- `<!-- ... -->` (HTML comment — treat any HTML comment as a user memo)
- `// ...` (inline comment)
- `[memo] ...` (bracketed annotation)
- `(**...**)` (parenthetical note)
- Any other text marked as a user annotation (e.g., a distinct block inserted between plan steps, or an inline sentence addressed to the planner). Do NOT treat the plan's original author-written prose as a memo.

Re-read source files if needed, update the Korean plan in-place, and sync changes to the English plan. Remove the memo comments after incorporating them.
Return which steps were changed and a brief summary.
```

## Refine Assurance
If `$ARGUMENTS` contains `--qa quick|light|standard|thorough|adversarial`, use that level and strip the flag. Otherwise inherit the plan's selected assurance context. `code-refine` is optional correction of an existing durable plan; it is not an automatic stage in `direct` or `quick`.

| QA level | Review action after refine | Fix behavior |
|---|---|---|
| `quick` | Direct invocation only: one fast sanity review or self-check. | Record remaining concerns; no repeated fix-round. |
| `light` | One focused fast review when the changed plan steps could affect execution. | One bounded correction if blocking. |
| `standard` | One lightweight plan-review pass for changed steps. | At most one correction pass. |
| `thorough` | Multi-axis review only when selected by `intensity=thorough`. | Up to two corrections with synthesis. |
| `adversarial` | Thorough plus explicit adversary/failure-mode/security critique when available and selected. | Fail loudly only for explicit unavailable adversarial; otherwise fall back to thorough and report. |

After 기획팀 returns, run only the review action selected by the caller's graph. Do not open a repeated QA loop merely because `--qa` is high. If unresolved concerns remain after the selected budget, add them to the plan's risk/unresolved section and report them to the caller.

## Task
Refine the plan at: $ARGUMENTS
