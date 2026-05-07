---
name: refine-plan
description: Reflect user memos/comments in a plan and update it (do NOT implement)
argument-hint: "<plan name or path> [--qa quick|light|standard|thorough|adversarial]"
---

## Plan Resolution (canonical — keep in sync with execute-plan, run-test, final-report, refine-plan, autopilot-code)
Resolve `$ARGUMENTS` to plan file paths. Always resolve BOTH `plan.md` and `plan_ko.md`:
1. If it ends with `.md` → use as-is; derive the other file by path swap (`plan.md` ↔ `plan_ko.md`)
2. If it's a directory path → append `/plan/plan.md` (English) and `/plan/plan_ko.md` (Korean)
3. Otherwise, fuzzy search: `ls -d .claude_reports/plans/*$ARGUMENTS* 2>/dev/null`
   - **1 match** → use `{match}/plan/plan.md` and `{match}/plan/plan_ko.md`
   - **Multiple matches** → prefer folder without `_audit`/`_fix_` suffix; if still multiple, ask user
   - **No match** → report error

Example: `/refine-plan inference-refactor` → English: `.../plan/plan.md`, Korean: `.../plan/plan_ko.md`

## Language Rule
- Think and reason in English internally.
- Write all user-facing output in Korean.

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

## QA Scaling
If `$ARGUMENTS` contains `--qa light|standard|thorough|adversarial`, use that level and strip the flag.

> Note: refine-plan delegates to 기획팀 and runs a QA review loop. The "3 rounds with 🔴 remaining" outcome is handled at the init-plan level and does not need separate gating here.

Otherwise, auto-detect from the refinement scope:

| Level | Auto-detect condition | Action |
|---|---|---|
| **Quick** | (manual via `--qa quick` only — autopilot skips refine entirely in quick mode, so this only matters on direct invocation) | 1× 품질관리팀 (`model: "sonnet"`), single pass, **max 1 round** (no fix-round on 🔴 — record as 미해결 이슈 and exit) |
| **Light** | ≤3 steps changed, mechanical | 1× 품질관리팀 (`model: "sonnet"`) |
| **Standard** | 4-10 steps changed, logic changes | 1× 품질관리팀 (default opus) |
| **Thorough** | >10 steps changed, architectural | 2× 품질관리팀 in parallel: A correctness (opus), B completeness (sonnet) |
| **Adversarial** | Cross-variant (SE+SS+CSS), shared modules (utils/, network.py), or >20 steps changed — **AND Codex available** | Thorough-level 품질관리팀 (A/B) + 1× codex-review-team (`adversarial-review`) in parallel; Codex writes `refine_round_{N}_codex.md` |

> See `--qa` flag for manual override. When `qa_level` is set in plan frontmatter, it overrides auto-detect.

**Codex availability check**: Before selecting Adversarial, run `codex --version` (suppress stderr). If the command fails or Codex is not authenticated, fall back to Thorough silently. This check is skipped if `--qa adversarial` is explicitly specified (fail loudly instead).

**Thorough mode** — launch 2 QA agents in parallel:
- Agent A: "Focus on **correctness**: Do the revised steps reference correct files/functions? Are dependencies updated?"
- Agent B: "Focus on **completeness**: Are downstream impacts of the changes reflected? Any missing steps?"
- Each writes to a separate review file. All 🔴 issues from ANY agent must be addressed.

## Post-Refine Review Loop (max 3 rounds; quick = 1 round)
Log dir = task root folder (parent of `plan/`). Run `mkdir -p {log_dir}/plan_reviews` before invoking QA.

After 기획팀 returns, assess QA level (changed step count, nature) per the table above, then:
- **Light/Standard**: 1 agent — "Review changed steps. Plan: [path], Changed: [list]. Write to: {log_dir}/plan_reviews/refine_round_{N}.md. Return file path + one-line verdict." (Light: pass `model: 'sonnet'`)
- **Thorough**: 2 agents in parallel (A/B), each with different focus suffix and output file. Pass `model: 'sonnet'` for the B (completeness) agent; A (correctness) uses default opus.

**Check verdict:**
- **No 🔴**: Loop ends. Report changed steps and review results to user.
- **qa_level == quick AND 🔴 found**: Loop ends after round 1. Add 🔴 issues to plan's **리스크** section under `## 미해결 이슈` (no fix-round). Report to user.
- **🔴 found**: Re-invoke 기획팀 — "Refine mode. Fix QA issues. Plan: {plan_path}, QA review: {log_dir}/plan_reviews/refine_round_{N}.md. Re-read sources if needed. Return changed steps + summary." Then re-invoke QA. Repeat until clear or max rounds.
- **After 3 rounds with 🔴 remaining**: Add to plan's **리스크** section under `## 미해결 이슈`. Report to user: changed steps, resolved issues, unresolved issues and why.

## Task
Refine the plan at: $ARGUMENTS
