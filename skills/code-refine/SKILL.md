---
name: code-refine
description: "사용자 메모·QA 피드백 반영해 기존 plan 정정 — sub-skill"
argument-hint: "<plan name or path>"
metadata:
  group: sub
  fam: sub
  modes: []
  blurb: "사용자 메모·QA 피드백 반영해 기존 plan 정정 — sub-skill"
---

> **Plan Resolution**: `$ARGUMENTS`→plan 경로 해석은 [autopilot-code/references/arguments-and-decisions.md#plan-resolution](../autopilot-code/references/arguments-and-decisions.md) 단일 authority — 로드해 그 절차대로 해석한다. **단, code-refine 은 `plan.md` 와 `plan_ko.md` 를 _둘 다_ 해석한다** (path swap `plan.md`↔`plan_ko.md`; refine 고유).

> **Language Rule**: 사용자-facing 출력은 자연스러운 한국어. 단일 SoT = [arguments-and-decisions.md#language-rule](../autopilot-code/references/arguments-and-decisions.md).

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
The verification rigor tier is derived from the plan's selected `--intensity` context (per [`CONVENTIONS.md §1.1`](../../core/CONVENTIONS.md#11-verification-rigor-tiers-intensity-derived-canonical-sot)). `code-refine` is optional correction of an existing durable plan; it is not an automatic stage in `direct` or `quick`.

| Rigor tier | Review action after refine | Fix behavior |
|---|---|---|
| `quick` | Direct invocation only: one fast sanity review or self-check. | Record remaining concerns; no repeated fix-round. |
| `light` | One focused fast review when the changed plan steps could affect execution. | One bounded correction if blocking. |
| `standard` | One lightweight plan-review pass for changed steps. | At most one correction pass. |
| `thorough` | Multi-axis review only when selected by `intensity=thorough`. | Up to two corrections with synthesis. |
| `adversarial` | Thorough plus explicit adversary/failure-mode/security critique when available and selected. | Fail loudly only for explicit unavailable adversarial; otherwise fall back to thorough and report. |

After 기획팀 returns, run only the review action selected by the caller's graph. Do not open a repeated QA loop merely because the rigor tier is high. If unresolved concerns remain after the selected budget, add them to the plan's risk/unresolved section and report them to the caller.

## Task
Refine the plan at: $ARGUMENTS
