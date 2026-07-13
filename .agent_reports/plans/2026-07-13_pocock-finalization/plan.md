# Pocock skill-design finalization plan

> intensity: `standard` (headless unavailable: installed Codex `hooks.json` projection mismatch; documented fallback = current-session execution in isolated worktree)
> spec-significance: `within-spec` — resumes `spec/skill-design-refactor/prd.md` P4/P8/SD-4/SD-6 closure.

## Scope

Finish only the remaining Matt Pocock skill-design work. Ponytail and the Codex depth-2/liveness runtime gap are explicitly out of scope.

## Ordered work

1. Confirm the already-merged 14-file capability `--qa` cleanup and treat it as closed baseline evidence.
2. Complete Invocation P4 by adding `autopilot-ship` to the entry-router trigger contract, updating both Claude skill trees and the deterministic registry/g7 expectations.
3. Complete Steering P8 by rewriting only the two non-safety negations in `design-components` as positive executable instructions; retain all load-bearing safety negations.
4. Close SD-4/SD-6 projection debt for `tools/skill-conformance`: project it into Claude's concrete tool tree, classify it deferred for Codex/OpenCode selective tool projections, and record the decision in the portable adaptation inventory.
5. Run sync outputs (Claude plugin, manifest, sync state), focused conformance/projection checks, and final semantic regression.
6. Update the original skill-design artifacts from RED/partial to the verified final state, commit, push, and hand back for main-session harvest.

## Verification

- `tools/skill-conformance/check.sh skills adapters/claude/skills`
- scanner: 13 entry routers are `use_when=Y`; both trees remain identical except `.sync_state.json`
- g7 static regression passes, including parent/user-only controls
- Claude plugin, root manifest, Codex/OpenCode native generated projections remain current
- adaptation boundary no longer reports `skill-conformance`; unrelated pre-existing `INSTALL_LAYOUT.md` and fleet projection failures are explicitly filtered as out of scope
- semantic review: P8 changed only non-safety anti-pattern wording; `no-op=0`, `sediment=0`, `premature-completion=0`, `variance-bug=0`
