---
# GENERATED METADATA — edit harness-manifest.json, then run tools/generate.py.
name: code-plan
description: "Use when invoking the portable code-plan capability. Analyze code, write a detailed implementation plan, and run the plan-check gate at the rigor derived from intensity."
argument-hint: "<task description> [--intensity direct|quick|standard|strong|thorough|adversarial]"
metadata:
  group: sub
  fam: sub
  modes: []
  blurb: "Analyze code, write a detailed implementation plan, and run the plan-check gate at the rigor derived from intensity."
---

# code-plan

Use the deepest eligible planning profile selected by the active adapter when cross-file reasoning or call-site analysis would benefit from it.

> **Stage-session entry (`standard+` dispatch, spec/stage-dispatch SD-2)**: Run in-session or as an isolated depth-2 stage worker dispatched by the `autopilot-code` conductor. Inputs are the task description and `<artifact-root>/plans/`; never depend on prior-stage conversation. The write class is `plan/plan.md`, an existing or explicitly requested audience-language companion such as legacy `plan/plan_ko.md`, and `_internal/plan_reviews/`. Any `plan-team` delegation remains inside this stage session.

> **Language rule**: Follow the audience and artifact language contract in [arguments-and-decisions.md#language-rule](../autopilot-code/references/arguments-and-decisions.md). Write the canonical plan in the selected artifact language; do not generate a language mirror merely because the skill source is English or the conversation uses a particular language.

## Pre-Check

Search `<artifact-root>/plans/` for a similar plan and branch on its frontmatter status:

- `active`: Ask whether to continue the active plan or create a new one. Do not proceed until that genuine choice is resolved.
- `done` or `failed`: Note it as a reference and create a new plan without pausing.
- `partial`: Read `failed_steps` and create a new plan covering only those failed or dependent steps without pausing.

Record any user-facing pause for `pipeline_summary.md` Decision Points.

## Delegate Planning

Invoke `plan-team` as a subagent with this task, adapted only for the selected artifact language and known prior-plan state:

```text
Plan mode. Create a new implementation plan.

Task: {$ARGUMENTS}
Save canonical plan to: <artifact-root>/plans/{YYYY-MM-DD}_{short-task-name}/plan/plan.md
Artifact language: {selected audience or conversation language}
Date: {YYYY-MM-DD}
{If a done/failed/partial plan exists: "Reference previous plan: [path], status: [status]"}
{If partial: "Failed steps from previous execution: [list from plan frontmatter failed_steps]"}

Read all relevant source files, analyze the current state, and create the plan.
Write the plan file directly. Return ONLY the file path and a 3-5 line summary. Do NOT return the plan content itself.
```

The stage orchestrator receives only paths and a compact summary.

## Plan-Check Assurance

Derive verification rigor from the caller's `--intensity` and plan risk under [CONVENTIONS §1.1](../../core/CONVENTIONS.md#11-verification-rigor-tiers). Rigor does not select this stage: `code-plan` runs only after the caller chooses a durable `standard+` graph. `direct` skips it; `quick` uses a one-shot worker with an inline micro-plan and plan-check-lite.

Set `{log_dir}` to the task root above `plan/`; for example, `<artifact-root>/plans/2026-03-18_task/plan/plan.md` resolves to `<artifact-root>/plans/2026-03-18_task/`. Run `mkdir -p {log_dir}/_internal/plan_reviews` before independent review.

| Rigor | Plan-check action | Correction budget |
|---|---|---|
| `quick` | Normally unreachable; if invoked directly, run one fast sanity review or self-check | Record residual concerns; no repeated loop |
| `light` | One focused fast review or equivalent self-check | One pass only when an issue blocks execution |
| `standard` | One independent review for feasibility, missing steps, and concrete verification commands | At most one correction |
| `thorough` | Deeper or multi-axis review when explicitly selected by the graph | Up to two corrections after synthesizing reviews |
| `adversarial` | Thorough review plus failure-mode, security, and adversarial critique when the adapter proves availability | Explicit unavailable requests fail loudly; automatic escalation falls back to thorough |

After `plan-team` returns:

1. Check whether the selected graph requires independent review. Otherwise run an inline plan-check.
2. When independent review is required, invoke `qa-team` in plan-review mode and write `{log_dir}/_internal/plan_reviews/round_{N}.md`. Use bounded separate reviewers only when the owner-worker graph and rigor select them.
3. If blocking issues exist, re-invoke `plan-team` for at most one correction at standard or the selected thorough/adversarial budget. Do not loop solely because rigor is high.
4. If concerns remain after the budget, add them to the plan's risk or unresolved section and continue only when the caller can safely own the risk.

Record any user-facing pause, including active-plan ambiguity, for the pipeline summary.

## Optional Audience-Language Companion

The canonical `plan.md` should normally be sufficient because its prose already follows the selected artifact language while code identifiers and paths remain unchanged. Create or update a companion only when the user explicitly requests a second language, an external audience contract requires it, or an existing workflow depends on a legacy companion such as `plan_ko.md`.

When a companion is required, have `editorial-team` translate from canonical `plan.md` while preserving code identifiers, file paths, library names, step numbering, and semantics. Use the existing project naming convention for the output. Consult memory for writing preferences only when the acting agent judges the retrieved preference relevant; project and explicit audience requirements take precedence.

Report the canonical plan path, any requested companion path, a compact summary, and the QA verdict in the conversation language.

## Task

$ARGUMENTS
