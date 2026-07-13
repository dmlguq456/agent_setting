# code-plan stage — skill-design-refactor

You are a depth-2 stage worker (code-plan) inside worktree `/home/Uihyeop/agent_setting-wt/skill-design-refactor`. Write ONLY to files; no chat-only output — the conductor reads your artifact from disk, not your final message.

## Read first (in order)
1. `.agent_reports/spec/skill-design-refactor/prd.md` — full PRD, this cycle's blueprint (SD-1~10 locked, D1/D3 resolved).
2. `.agent_reports/spec/skill-design-refactor/pipeline_state.yaml` — decisions_locked/resolved.
3. `.agent_reports/analysis_project/code/skill_design_audit.md` and `skill_design_audit_per_skill.md` — file:line evidence for every cluster.
4. Baseline scan already run: `.agent_reports/plans/2026-07-13_skill-design-refactor/_internal/scan_baseline.tsv` (quantitative norms, per skill).

## Task
Write a concrete implementation plan to `.agent_reports/plans/2026-07-13_skill-design-refactor/plan.md` covering, in this fixed order, three clusters:

**Cluster 2 (SoT consolidation, P2+P5)** — PRD §3.1:
- Plan Resolution: designate `autopilot-code/references/arguments-and-decisions.md` as sole authority; replace the duplicated "Plan Resolution (canonical — keep in sync with …)" blocks in code-execute/code-refine/code-report/code-test (SKILL.md + README.md, 4 skills × 2 files = up to 8 files) with a 1-line pointer. List exact files/line ranges from the audit per-skill doc.
- 시각검증 loop: designate a single SoT (`_design_rules.md` or equivalent shared reference) for design-components/design-review/design-tokens (and autopilot-design's inline copy); replace duplicates with pointers.
- Language Rule: consolidate the repeated code-* Language Rule text into one shared reference or `CONVENTIONS.md §5`.
- `<artifact-root>` snippet: point analyze-project/analyze-user/audit/autopilot-code/autopilot-draft (and any others found) at `CONVENTIONS.md §5` instead of re-defining it.
- P5: merge each router skill's duplicated "Required Reads" ↔ "Reference Map" listing (~13 routers, 4 references each) into a single reference-index section.
- Completion criteria to verify: `grep -rln "keep in sync" skills/*/SKILL.md skills/*/README.md` must return 0 lines.

**Cluster 3 (sprawl extraction, P3+P6)** — PRD §3.2:
- autopilot-design (315 lines, only double-🔴): extract Phase 0-5 execution body, the harness table, and the visual-verification loop text into `skills/autopilot-design/references/`, leaving only the stage-worker mapping table in SKILL.md body. Target <200 lines.
- Then draft-refine (278, delegate prompt), autopilot-ship (241), design-tokens (212, 70-line exemplar), autopilot-apply (190): extract worked examples / delegate prompts / templates into each skill's `references/`.
- Completion criteria: re-run scan.sh — body line count drops for each target (autopilot-design especially), and `references/` stays 1-depth (no subdirectories) for every skill.

**Cluster 1 (invocation reclassification, P1+P4+P7)** — PRD §3.3, gated:
- Identify the 13 pure sub-skill candidates for `disable-model-invocation: true`: code-execute/code-plan/code-refine/code-report/code-test, design-components/design-handoff/design-init/design-refs/design-review/design-tokens, draft-refine, draft-strategy.
- Plan the exact trial-flip gate procedure per PRD §3.3 (a)(b)(c) — this is a GATE that a later stage (code-execute or a dedicated verification step) must run BEFORE flipping all 13:
  (a) flip draft-strategy only → verify `claude -p "/draft-strategy <args>"` slash invocation still works
  (b) flip code-test only → verify autopilot-code conductor's depth-2 Skill-tool dispatch of code-test still works
  (c) if (a)+(b) PASS, run one full standard-intensity autopilot-code pipeline (code-plan→execute→test→report) to confirm the ecosystem survives
  Fallback: if gate fails, narrow scope per PRD's fallback rule (keep Skill-tool-dispatched code-* model-invoked if (b) fails; flip only skills with no Skill-tool dispatch path).
- P7: `post-it/SKILL.md:14` wording fix to match actual model-invoked+proactive-nudge behavior (either soften wording or use disable flag consistently with the gate outcome).
- P4: entry-router English "Use when…" trigger — per D3 (resolved), add an English trigger sentence to the description's first sentence for entry-router skills (autopilot-*, analyze-*, audit) ONLY, alongside (not replacing) the existing Korean blurb.

**Also plan** (PRD §2, core-first):
- `core/CONVENTIONS.md` new `§skill-design` section: quantitative norms table (<500 lines / references 1-depth / invocation frontmatter requirements).
- `core/DESIGN_PRINCIPLES.md` new tenet section: the 4-axis + Predictability root-virtue tenets, with a 1-line pointer to CONVENTIONS §skill-design (no duplication — Cluster 2's own SoT rule applies to this PRD's own output).
- scan.sh promotion to a standing lint (decide location: sync-skills pipe vs a hooks/ conformance guard) + a drill regression case referencing PRD SD-4.
- `core/*` must be edited BEFORE any adapter-derived mirror (core-first convention already established elsewhere in this harness).

## Plan document requirements
- Break into checkable steps per cluster with exact file paths.
- Note SD-6: each cluster's completion requires running `sync-skills` and verifying adapter doctor/parity-mirror checks pass.
- Note SD-10: regression check against audit §5's four strengths (variance-bug/premature-completion/no-op/sediment = 0) must stay true — call out what to re-verify.
- End with a checklist file at `.agent_reports/plans/2026-07-13_skill-design-refactor/checklist.md` (one line per checkable item, unchecked).

Do not execute any edits in this stage — plan only. When done, write the plan.md + checklist.md files and stop.
