# code-execute stage 1 — CORE + Cluster 2 (SoT consolidation)

You are a depth-2 stage worker (code-execute) inside worktree `/home/Uihyeop/agent_setting-wt/skill-design-refactor`. This worktree IS the git branch — edit files directly, no further sub-dispatch (depth 3 is forbidden).

## Read first
1. `.agent_reports/plans/2026-07-13_skill-design-refactor/plan.md` — full plan. Execute **§1 (Step CORE, CORE-1~4)** and **§2 (Cluster 2, C2-1~5)** ONLY in this stage. Do NOT touch Cluster 3 or Cluster 1 (later stages).
2. `.agent_reports/plans/2026-07-13_skill-design-refactor/checklist.md` — tick items as you complete them (edit the file in place, `[ ]`→`[x]`).
3. `.agent_reports/spec/skill-design-refactor/prd.md` for context if the plan references something ambiguous.

## Execute exactly
- **CORE-1**: `core/CONVENTIONS.md` — new `§5.6a Skill-Design 정량 규범` section right after `§5.6` (around line 357), per plan §1 CORE-1 table content.
- **CORE-2**: `core/DESIGN_PRINCIPLES.md` — new `## §10 Skill-Design Tenets (Pocock 4축 + Predictability)` after `## 9. Design ownership` (around line 230), plus the 부록 history line, per plan CORE-2.
- **CORE-3**: `roles/modes/design/_design_rules.md` — add the 4-scope (ui/webapp·slide·icon·diagram) render table to `§시각 자가검증 루프`, merging design-components:120-125 + design-review:65-70 content. This is core-first — edit ONLY the `roles/` copy, not the `adapters/claude/agent-modes/design/` or `adapters/codex/modes/design/` copies (those get synced later by sync-skills).
- **CORE-4**: move `.agent_reports/analysis_project/code/_internal/skill_design_audit/scan.sh` to new `tools/skill-conformance/scan.sh` (git mv, keep executable). Update `skills/sync-skills/references/finalize-and-hooks.md` to add a "scan.sh 정량 규범 lint" step, and add a row to sync-skills SKILL.md's step table (~line 60-65). Create drill case `loops/drill/cases/g7_skill_conformance/{config,fixture.sh,assert.sh}` per plan CORE-4 detail (assert.sh calls `bash tools/skill-conformance/scan.sh skills` and checks line_ok/ref_depth_ok/disable_model columns — for THIS stage, since Cluster 1 flip hasn't happened yet, the disable_model check should just verify the column parses, not assert true yet; leave a TODO comment noting Cluster 1 will make it meaningful, or write the assertion so it naturally passes today and will also correctly pass post-flip).

- **C2-1 (Plan Resolution)**: edit `skills/autopilot-code/references/arguments-and-decisions.md` header per plan (remove "keep in sync" wording — designate single authority). Replace the duplicated "## Plan Resolution (canonical — keep in sync with …)" blocks with a 1-line pointer in: `skills/code-execute/SKILL.md`, `skills/code-test/SKILL.md`, `skills/code-report/SKILL.md`, `skills/code-refine/SKILL.md` (SKILL.md files) AND their `README.md` compat mirrors (`code-execute/README.md`, `code-test/README.md`, `code-report/README.md`, `code-refine/README.md`). code-plan is excluded (no such block). Use exact grep to find current block boundaries — do not rely solely on plan's line numbers, verify live.
- **C2-2 (Language Rule)**: pointer-ize `## Language Rule` blocks in code-execute/code-refine/code-report/code-plan/code-test SKILL.md files to point at `arguments-and-decisions.md#language-rule`, after enriching the SoT text per plan wording.
- **C2-3 (시각검증 loop)**: pointer-ize the visual-verification loop prose in `design-components/SKILL.md`, `design-review/SKILL.md`, `design-tokens/SKILL.md`, `autopilot-design/SKILL.md` to point at `_design_rules.md §시각 자가검증 루프`, keeping each skill's unique gate language (specimen-consume gate, verifier/critic 2-gate, etc.) per plan table.
- **C2-4 (`<artifact-root>` snippet)**: pointer-ize the verbatim artifact-root resolution snippet in `analyze-project/SKILL.md`, `audit/SKILL.md`, `autopilot-research/SKILL.md`, `autopilot-draft/SKILL.md`, `autopilot-spec/SKILL.md`, `autopilot-refine/SKILL.md` to point at `core/CONVENTIONS.md §5.1`.
- **C2-5 (P5 Reference Index merge)**: for the 13 router skills (analyze-project, analyze-user, audit, autopilot-code, autopilot-draft, autopilot-lab, autopilot-note, autopilot-refine, autopilot-research, autopilot-spec, draft-strategy, post-it, sync-skills), merge duplicated "Required Reads" + "Reference Map" sections into one `## Reference Index` table (file + when-to-load + obligation columns — do not weaken the pointer, per SD-10 variance-bug guard). Also add the 1-line convention to `core/CONVENTIONS.md §5.6`.

## Verification before stopping
- `grep -rln "keep in sync" skills/*/SKILL.md skills/*/README.md` must return 0 lines.
- `grep -rln "## Language Rule" skills/code-*/SKILL.md` must return 0 lines.
- `bash tools/skill-conformance/scan.sh skills` runs without error and produces the same TSV shape as before.
- No unintended content loss: every pointer replacement must preserve the semantic obligation (file name + when-to-load + why) — re-read each edited file after editing.
- Write a short `_internal/execute1_log.md` listing every file touched with a one-line note per file.

## Stop condition
When CORE + Cluster 2 are complete and verified, update the checklist, write the execute1 log, and stop. Do not run sync-skills yourself unless it's a lightweight dry check — a later test stage will run it. If sync-skills is trivial to invoke directly (it's a skill under skills/sync-skills), you MAY run it via its documented CLI/script path if one exists without needing the Skill tool (you have no Skill tool at depth 2) — otherwise just note in execute1_log.md that sync-skills needs to run next stage.
