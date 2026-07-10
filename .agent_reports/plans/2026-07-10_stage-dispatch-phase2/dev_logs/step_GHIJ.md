# dev_log — Phase G (adapter parity) + H (diffusion) + I (drill) + J (instrumentation)

## Phase G — adapter bootstrap parity
- `adapters/claude/CLAUDE.md §0(C)`: appended conductor one-shot pointer (dispatch-wait, core OPERATIONS §5.10 is SoT). `grep -c one-shot` = 1.
- `adapters/codex/AGENTS.md` + `adapters/opencode/AGENTS.md`: one-shot-process parity sentence (poll `preflight.sh liveness`, harvest, re-dispatch on SUSPECT/DEAD; SD-14 parity). `grep -c "one-shot process"` = 1 each.

## Phase H — diffusion (5 pipes, via 5 parallel in-session 개발팀 agents)
- Each pipe reference doc gained a **stage-dispatch contract block** + a **§6-homolog stage-worker table** (`stage | in-session team | input artifacts | output artifacts | write class`) + a "file-only handoff" clause. Scope = contract + mapping only (per-pipe imperative body rewrite is follow-up, §12-1).
  - autopilot-draft: `pipeline-steps.md` (draft-strategy/Step4.1 연구팀/Step5.5 편집팀; Step4b detector inline).
  - autopilot-research: `pipeline-search-analysis.md` (2/2e/3b/3c/3e/4a/4b; 자료팀 as in-stage sub-delegation; 2e/3c conditional) + `report-generation.md` (4a/4b back-ref).
  - autopilot-spec: `scaffolding.md` (asymmetry: PRD authoring = conductor-inline, scaffold = 개발팀 new-lib dispatch) + `prd-authoring.md` (conductor-inline note).
  - autopilot-design: `SKILL.md` (design phases dispatch; [CONFIRM Gate] verdict held via design_state.yaml).
  - autopilot-lab: `setup-procedure.md` + `eval-procedure.md` (S1/S2 scaffold + E2/E3-2/E3-3 dispatch; **experiment run = human-gated RUNLOG ⏳, NOT dispatched**, uses lab-runner profile).
- **Verify**: all 5 pipe dirs matched by `grep -rl "stage-worker|스테이지-워커"`; every added table uses the exact 5 columns; each pipe carries a "file-only handoff" clause (prd-authoring.md intentionally carries only the conductor-inline note pointing to scaffolding.md's table). No two stages write the same shared file without a lock (RUNLOG append-only, pipeline_summary lock noted).

## Phase I — drill regression case (HANDOFF artifact, NOT written into loops/)
- Authored under `drill_case_stage_dispatch/`: `README.md` (install instructions → `loops/drill/cases_growing/g_stage_dispatch/`, growing tier, AXIS=git, expensive), `prompt.md` (standard+ multi-file dev, spec-backed fixture, no dispatch spoon-feeding — §8.5.5 doc-efficacy), `config` (MAX_TURNS=120 TIMEOUT=2400 AXIS=git), `fixture.sh` (spec-backed repo: .agent_reports/spec/prd.md + pipeline_state.yaml + app.py/version.py; .pre/main_sha), `assert.sh` (HARD = main unchanged + no depth=3 + no non-execute source write; SOFT = depth-2 stage rows / doc-efficacy dispatch trace / stage artifacts).
- **Verify**: `bash -n` clean on both scripts; fixture builds a spec-backed repo in a temp dir; assert HARD passes (exit 0) with no work done. Modeled on `g6_worktree_dispatch` (read-only). **loops/ untouched.**

## Phase J — instrumentation (measurement only, no thresholds)
- `instrumentation.md`: per-stage record format (stage/profile/model_role/wall_clock/conductor_ctx_proxy) seeded with the Phase-1 pilot row (plan 218s/execute 255s/test 46s/report 28s, full-bootstrap). SD-OPEN-2 curator observation table (curator fired? / duplicate mem add?) — observation only; reminder/Stop hooks already guard MEM_DISTILL=1 recursion. Micro-stage inline threshold (SD-OPEN-1) deliberately unset.
