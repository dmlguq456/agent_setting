# Stage-dispatch v11 implementation plan

## Goal

Implement PRD v11 SD-48~50 after the v10 merge, without modifying the v10
worktree or its cycle artifacts.

## Baseline

- Base: `f5f3949f` (`stage-dispatch-v10` merged into `main`).
- Worktree: `/home/Uihyeop/agent_setting-wt/stage-dispatch-v11`.
- Spec significance: `within-spec`.
- Intensity: `standard`; execution is inline in the isolated worktree because
  this change repairs the dispatch surface itself and native/subagent
  delegation is not authorized for this turn.

## Implementation

1. Update `core/OPERATIONS.md` first with nested tuple eligibility, immutable
   global registry authority, attempt identity, and ordered fallback semantics.
2. Extend the route compiler with checked nested evidence and a fail-closed
   ordered fallback plan for depth-2 nodes.
3. Add shared registry/fallback utilities, then adapt the Claude, Codex, and
   OpenCode headless wrappers independently:
   - inherit and enforce the canonical global registry;
   - reject noncanonical nested `--jobs`;
   - write `attempt_id`, launch authority, fallback ordinal, and tuple evidence
     before spawn;
   - close rows on immediate launch failure and propagate the registry path.
4. Expose nested eligibility and fallback planning through adapter preflight
   surfaces where present, with Codex's observed nested tuple remaining
   `unsupported(network-operation-not-permitted)` until a new probe supersedes it.
5. Add portable and sibling-adapter fixtures for route selection, registry
   authority/unwritable handling, attempt identity, and fallback order.
6. Absorb diagnosis O1 within SD-15: record Codex child PID/start ticks and
   make shared liveness fallback harness-aware (`codex.jsonl`, OpenCode
   heartbeat/log, Claude transcript). Keep O2/O3 out of implementation and
   list them only as v12 spec-decision candidates after v11 verification.
7. Run focused tests, parity/adaptation checks, integrated regression, then
   update cycle evidence and the stage-dispatch pipeline state.

## Non-goals

- Do not edit or clean `/home/Uihyeop/agent_setting-wt/stage-dispatch-v10`.
- Do not mutate v10 plan/checklist/dev/test artifacts.
- Do not claim native-subagent execution as registered headless parity.
- Do not implement O2 worker commit authority or O3 self-modifying route
  completion overrides in v11.

## Verification

- Route compiler unit/property tests.
- Shared fallback/registry unit tests.
- Three adapter wrapper fixtures, each independently asserting depth-2 rules.
- Existing SD-15/SD-45 dispatch regression suites.
- `tools/check-adaptation-boundary.sh` and relevant portable guard checks.
- Integrated dry-run showing Codex conductor-local same-harness is skipped and
  an eligible ancestor-broker/cross-harness hop is selected before inline.
