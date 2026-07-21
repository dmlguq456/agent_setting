# Execute stage — bounded continuation 1 (partial)

## Starting state

Resumed the dirty worktree exactly as left by `execute-partial.md`: both approved
candidates (`7094c92b`, `c95ed391`) staged, the Step 1 topology/compiler layer
(`capabilities/topologies.json`, `tools/capability_topology.py` + test,
`utilities/capability-route.py` + test, `utilities/dispatch-node.py` + test)
unstaged on top, no merge/cherry-pick state, worktree matching
`d7e5ad35865b77cfa5c05ddf4b3c4dccd87e9c72` plus those changes. Verified this by
`git status`/`git diff --stat` before making any edit; no candidate content was
altered and no in-progress operation markers were present.

## What was implemented this round

Only a narrow, low-risk slice of Step 4 (canonical prose): the plan's
four-surface terminology, in `core/OPERATIONS.md` §5.10:

1. Rewrote the "Delegation surfaces are distinct" paragraph to name the four
   exact runtime nouns from the plan — Codex native subagent, Claude subagent,
   Claude agent-team teammate session, registered headless worker session —
   and to state explicitly that only the first two compose the cross-runtime
   "runtime-native subagent" category, and that Claude agent-team teammates
   are separate peer sessions carrying no depth and no registered-worker
   status.
2. Corrected the "Light team delegation" bullet's `team agent — a
   runtime-native subagent` wording (this is exactly the mislabel the plan's
   §6 calls out as needing correction) to `Claude agent-team teammate
   session, not a runtime-native subagent`.

No other file was touched this round. `tools/generate.py --check`'s
pre-existing `manifest-and-catalogs` drift was checked and confirmed
unrelated to this edit (`build-manifest.py` derives `manifest.json` from
`harness-manifest.json` metadata, not from `core/*.md` prose; the drift
message is unchanged regardless of this file's content). Re-ran
`tools/capability_topology.test.py` (9/9), `utilities/capability_route.test.py`
(20/20), and `utilities/dispatch_node.test.py` (23/23) to confirm the prior
round's foundational layer is still green and untouched by this prose-only
edit.

## Why the round stopped here

The remaining scope named in the assignment is very large and touches
concurrency-sensitive dispatch code (registry claim/lock semantics in
`utilities/dispatch-registry.py`, `utilities/stage-dispatch-fallback.py`,
`utilities/dispatch_contract.py`, `utilities/worker-route-guard.py`,
`utilities/worker_bootstrap.py`, three adapter wrappers) plus Fleet model
propagation and a full fresh acceptance/conformance test matrix. I read these
files (`dispatch-registry.py` in full, greps over the others) and confirmed
the plan's assumption: outside `stage-dispatch-fallback.py`'s literal
`"--depth", "2"` CLI argument (intentionally still bare per
`execute-partial.md`), none of these files currently reference the renamed
`dispatch_depth`/`owner_dispatch_depth`/`max_dispatch_depth` fields at all —
the `depth` parameters present in `dispatch_contract.py`/`worker_bootstrap.py`
are the unrelated `AGENT_DISPATCH_DEPTH` worker-nesting counter, which the
plan says stays as-is. What Step 2 actually requires here is new logic (quick
single-live-attempt-under-lock, terminal retry history preservation,
`quick-registered-headless-exhausted`, and `execution_surface`/
`registered_worker` attempt-evidence stamping), not a mechanical rename —
implementing it correctly against this registry's existing lock/claim/
classify contract needs a dedicated pass with its own focused tests, not a
rushed addition inside an already time-boxed continuation. Rather than make
partial, undertested edits to concurrency-critical dispatch code, I limited
this round to the verified-safe prose fix above and left the rest for the
next round with an accurate, itemized state.

## Remaining scope (unchanged in shape from `execute-partial.md`, updated status)

- **Step 2 (wrapper/registry/fallback/liveness):** entirely not started.
  `utilities/dispatch_contract.py`, `utilities/dispatch-registry.py`,
  `utilities/stage-dispatch-fallback.py`, `utilities/worker-route-guard.py`,
  `utilities/worker_bootstrap.py`, `utilities/dispatch-progress.py`,
  `utilities/dispatch-liveness.sh`, and the three adapter
  `dispatch-headless.py` wrappers need: qualified `dispatch_depth` fields
  where genuinely topology-related (not `AGENT_DISPATCH_DEPTH`), closed
  `execution_surface`/boolean `registered_worker` attempt evidence, quick
  single-live-attempt-under-lock + terminal retry history +
  `quick-registered-headless-exhausted`, and legacy `schema_version` rejection
  at node/start/resume/complete/registry-claim.
- **Step 3 (Fleet):** `tools/fleet/model.py`,
  `tools/fleet/collectors/dispatch.py`, render/control code, and fixtures;
  mirror to `adapters/claude/tools/fleet/`. Not started.
- **Step 4 (canonical prose, remainder):** `core/CONVENTIONS.md` and
  `core/WORKFLOW.md` four-surface language beyond the depth-vocabulary
  sentence already in the two candidate commits; capability/role/canonical
  Skill owner-reference prose; the deterministic terminology conformance
  check (reject bare route fields, conflated transport/surface/fallback
  values, Claude teammate-as-subagent wording, unqualified
  `agents.max_depth` comparisons). Not started beyond the two edits in this
  log.
- **Step 5 (fresh acceptance evidence):**
  `test_logs/route-acceptance/{direct,quick,standard-plus}.json` +
  `summary.md`, and the full negative zero-emission matrix through the real
  wrapper/registry path. Not started.
- **Step 6 (full verification matrix):** the complete command list in
  `plan.md` Step 6 has not been run end-to-end; only the three Step 1 unit
  suites were re-confirmed green this round.
- `_internal/metrics.md` self-hosting stanza: unchanged from the prior round
  (already present, not touched further).

## State handed to the next round

Worktree is uncommitted, matches `d7e5ad35865b77cfa5c05ddf4b3c4dccd87e9c72`
plus: the two staged candidate commits, the prior round's unstaged Step 1
compiler-layer changes, and this round's two-paragraph edit to
`core/OPERATIONS.md`. No merge/cherry-pick state remains. This is not
commit-ready: Steps 2, 3, 5, and 6 are entirely outstanding and most of Step 4
remains outstanding, so the code-execute completion gate for the full plan is
not satisfied.
