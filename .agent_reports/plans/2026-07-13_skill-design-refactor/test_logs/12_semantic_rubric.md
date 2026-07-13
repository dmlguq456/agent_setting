# SD-10 semantic rubric reapplication

## Scope

- Canonical rubric: `.agent_reports/analysis_project/code/_internal/skill_design_audit/RUBRIC_BRIEF.md` 전체.
- Baseline: 28-skill per-skill audit and its zero-count strengths.
- Reapplication target: current `skills/*/SKILL.md`, all current one-depth `references/*.md`, and the refactor delta through `9d1abb2`.
- `skills/` and `adapters/claude/skills/` are byte-identical except `skills/.sync_state.json`; therefore semantic judgment is performed once and applies to both trees.

## Explicit counts

| requested failure mode | count | verdict |
|---|---:|---|
| `no-op` | 0 | PASS — extracted text is replaced by actionable authority pointers or stage-specific instructions; the new autopilot-ship pointers alter routing/ownership and are not default-behavior filler. |
| `sediment` | 0 | PASS — old Plan Resolution/Language Rule/artifact-root/Required Reads·Reference Map remnants are absent in both trees; no stale duplicate route table remains around autopilot-ship. |
| `premature-completion` | 0 | PASS — checkable completion and CONFIRM/Final Confirm boundaries remain in the router SKILL files; extraction did not hide terminal gates behind post-completion prose. |
| `variance-bug` | 0 | PASS — must-have references name the file and the load stage, with mandatory wording where unconditional; examples/exemplars left behind simple pointers are optional support material, not must-have execution assets. |

## Autopilot-ship Step 4 semantic preservation

Both trees preserve all three unique re-entry rows:

1. env: `.env.example` update + dashboard handoff + env/changelog update.
2. domain: DNS guidance + Domain/changelog update.
3. migration: destructive warning + user-run command boundary + rollback guidance + Notes/changelog update.

The shared utterance routing and deploy-command boundary now live in Step 2. Step 4 remains the single authority for re-entry mutation semantics, so the dedupe does not erase unique behavior.

## Non-rubric residuals

- Invocation classification remains on the safe fallback: the newly appended C1 gate evidence reports slash PASS, Skill-tool FAIL, pipeline FAIL, so all 13 candidates remain model-invoked.
- `g7_skill_conformance` currently verifies `disable_model` parsing only; its TODO does not enforce the aspirational sub-skill=true rule. This does not change the four requested counts, but it is unresolved invocation-contract debt.
- Capability contract drift and sync-state drift are recorded separately in `11_capability_contracts.log` and `08_sync_skills_check.log`.
