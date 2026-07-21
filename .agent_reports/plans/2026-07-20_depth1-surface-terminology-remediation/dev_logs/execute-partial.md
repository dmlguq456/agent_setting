# Execute stage — partial implementation, unblocked candidate application

## Unblock of the prior BLOCKED state

The previous `execute-blocked.md` reported `git cherry-pick --no-commit
7094c92b c95ed391` failing because the linked worktree's `.git/worktrees/...`
sequencer directory was read-only. In this run the same command succeeded:
both commits are applied and staged (`git status` shows the 25 doc files from
both commits as `Changes to be committed`, nothing left in a cherry-pick
state). `6b3a34bc` confirmed not an ancestor of the starting HEAD
(`d7e5ad35865b77cfa5c05ddf4b3c4dccd87e9c72`); no co-primary/composition text
is present in the diff.

The prose from `7094c92b`/`c95ed391` already matches plan intent (quick
depth-1 one-shot labeled "a registered dispatch session, not a runtime-native
subagent") and needed no further correction against the Claude
teammate/subagent conflation called out in the plan — that conflation does
not appear in either candidate's diff.

## What was implemented (unstaged, on top of the staged candidates)

1. `capabilities/topologies.json` (schema_version 1 -> 2):
   - Added closed `execution_surfaces` (5 values) and `fallback_hops` (4
     values) vocabularies; narrowed `transports` to `headless|interactive`.
   - Renamed every recipe's `quick.owner_depth`/`quick.max_depth` ->
     `owner_dispatch_depth`/`max_dispatch_depth`, `standard_plus.owner_depth`
     -> `owner_dispatch_depth`, and every node's `depth` -> `dispatch_depth`.
   - Replaced each node's `transport` allowlist with `fallback_hops` mapped
     onto the new vocabulary (`headless` -> `same-harness-headless` +
     `cross-harness-headless`, `native-subagent` -> `native-subagent`,
     `inline-fallback` -> `inline`). `resource-runner` nodes keep
     `detached-process` under a new `resource_transport` key, explicitly
     separated from the fallback/transport/execution-surface namespaces.
2. `tools/capability_topology.py` / `tools/capability_topology.test.py`:
   validator updated to the renamed fields, plus a new unknown-fallback-hop
   negative test. `python3 tools/capability_topology.test.py` passes (9/9).
3. `utilities/capability-route.py` / `utilities/capability_route.test.py`:
   - `ROUTE_SCHEMA_VERSION = 2`; `verify_route` now rejects any route whose
     `schema_version` is not current (legacy routes fail mutating/resume
     verify) and a new `legacy_route_diagnostic()` gives Fleet a read-only,
     non-resumable label for pre-v20 records.
   - `compile_route` direct nodes now emit `dispatch_depth=0`,
     `execution_surface="inline"`, `registered_worker=False` (no `transport`
     literal).
   - `compile_route` quick path implements SD-73: an omitted/`"headless"`
     transport is required (any other value raises
     `invalid quick transport: ...`); a new
     `_validate_registered_headless_evidence()` requires a structured
     `--registered-headless-evidence` fixture (`harness`, `transport`,
     `surface`, `status`, `probe_source`, `probe_time`) with at least one
     `supported` candidate, else raises exactly `quick-headless-unavailable`.
     Quick nodes emit `dispatch_depth=1`,
     `execution_surface="registered-headless"`, `registered_worker=True`, and
     the route carries `registered_headless_candidates` +
     `registered_headless_policy="serial-attempt"`.
   - `owner_dispatch_depth`/`max_dispatch_depth` added to the route payload;
     all internal `node.get("depth")==2` checks renamed to `dispatch_depth`.
   - `inline_reason` is now accepted only when `effective_intensity=="direct"`
     (previously it was accepted for any `transport=="inline-fallback"`,
     which no longer exists as a transport value).
   - Test file updated: fixed three tests that previously passed
     `inline_reason` into non-direct routes (now `None`), added a
     `registered_headless()` fixture helper, and added
     `test_quick_missing_eligibility_fails_closed` /
     `test_quick_invalid_transport_fails_closed`. `python3
     utilities/capability_route.test.py` passes (20/20).
4. `utilities/dispatch-node.py` / `utilities/dispatch_node.test.py`: fixed the
   two `node.get("depth")` reads (CLI `--depth` value and the depth-2
   `--parent` gate) to `node.get("dispatch_depth")` so the wrapper-argument
   binding does not silently stop enforcing the depth-2 parent requirement
   against the renamed schema. `python3 utilities/dispatch_node.test.py`
   passes (23/23). The wrapper-facing CLI flag name is still `--depth` (see
   "Not implemented" below).

Regression check on adjacent suites that were not intentionally touched (all
green, confirming no field-rename fallout elsewhere yet):
`dispatch_contract.test.py`, `dispatch_registry.test.py`,
`stage_dispatch_fallback.test.py`, `worker_route_guard.test.py`,
`worker_bootstrap.test.py`, `dispatch_progress.test.py`,
`dispatch_completion_marker.test.py`, `dispatch_adapters_v11.test.py`,
`worker_dispatch_prompt.test.py` (pre-existing flake, reproduced identically
against the untouched worktree state — see below), and the full
`tools/fleet/tests` suite (721 tests).

`worker_dispatch_prompt.test.py`'s 3 failures
(`noncanonical-nested-jobs` / inherited `AGENT_HOME` jobs path) are
environmental (this session's `AGENT_HOME` points at the primary checkout,
not this worktree) and reproduce identically with none of this stage's edits
present; not attributable to this change.

## Not implemented — scope remaining for a follow-up execute round

The full plan spans ~40 files; only the foundational schema/compiler layer
(topology registry + route compiler) and one immediate consumer
(`dispatch-node.py`) were completed and verified in this round. Explicitly
NOT done, and required before `code-test` can pass the plan's completion
gate:

- **Wrapper/registry/fallback/liveness (Step 2 primary files):**
  `utilities/dispatch_contract.py`, `utilities/dispatch-registry.py`,
  `utilities/stage-dispatch-fallback.py`, `utilities/worker-route-guard.py`,
  `utilities/worker_bootstrap.py`, `utilities/dispatch-progress.py`,
  `utilities/dispatch-liveness.sh` were not audited/edited for the renamed
  fields, the new `execution_surface`/`registered_worker` attempt evidence,
  or quick's single-live-attempt/`quick-registered-headless-exhausted`
  runtime gate. They currently do not construct routes with the new quick
  eligibility shape, so quick dispatch through the real wrapper path is
  untested against the new contract.
- **Adapter wrappers:** `adapters/{claude,codex,opencode}/bin/dispatch-headless.py`
  still expose `--depth` (not renamed to a qualified flag) and do not accept
  or record `execution_surface`/`registered_worker`. `dispatch-node.py` still
  emits `--depth` on the wrapper CLI for this reason (an intentional,
  documented compromise, not an oversight).
  `adapters/{claude,codex,opencode}/bin/dispatch-headless.sd15.test.sh` /
  `.sd45.test.py` not run against any of the above.
  `utilities/dispatch-broker.py`'s unrelated `depth`/`--depth` fields (broker
  request schema, distinct namespace, retired component per
  memory `no-broker-revival`) were intentionally left untouched.
- **Fleet (Step 3):** `tools/fleet/model.py`,
  `tools/fleet/collectors/dispatch.py`, render/control code, and fixtures do
  not yet expose `dispatch_depth`/`execution_surface`/`registered_worker` as
  model attributes, and the `adapters/claude/tools/fleet/` mirror was not
  resynced (no source-of-truth change was made there yet, so the mirror is
  still byte-identical to the old `tools/fleet/`, which is itself unchanged).
- **Canonical prose/generators (Step 4):** `core/CONVENTIONS.md`,
  `core/OPERATIONS.md`, `core/WORKFLOW.md`, capability/role/Skill prose beyond
  the two applied candidate commits, and the terminology conformance check
  were not added/updated. `tools/generate.py`, `tools/sync-entry-skill-layer.py`
  were not re-run (no canonical template changed beyond the two candidates).
- **Fresh acceptance evidence + full test matrix (Steps 5–6):**
  `test_logs/route-acceptance/{direct,quick,standard-plus}.json` +
  `summary.md` were not produced; the negative zero-emission matrix was not
  run end-to-end through the real wrapper/registry path (only the compiler
  unit tests above were exercised); the full command list in plan Step 6 was
  not run.
- `_internal/metrics.md` already carries the required self-hosting stanza
  from the plan stage; not modified further.

## State handed to code-test

Worktree is uncommitted, matches `d7e5ad35865b77cfa5c05ddf4b3c4dccd87e9c72`
plus: the two staged candidate commits' content (unstaged-vs-HEAD but
staged-vs-index), and the unstaged compiler-layer changes listed above. No
merge/cherry-pick state remains (`git status` clean of any in-progress
operation markers). This is not commit-ready: the plan's SD-73/74/75
acceptance items for Steps 2-5 are not met, so the code-execute completion
gate for the *full* plan is not satisfied, even though the parts implemented
are internally consistent and pass their focused tests.
