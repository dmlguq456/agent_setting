# Depth-1 surface terminology remediation — execution checklist

Final status: **REJECTED / NOT MERGED** (2026-07-20). The single bounded
remediation round ended with an independent `verdict: FAIL`: same-digest
standard+ retries can retain stale completion-attempt/surface axes, and current
qualified-terminology coverage remains incomplete. The registered review
attempt was reconciled terminal with `note=dead-worker-fail`; the global
registry is `open 0 / orphan 0`. See
`test_logs/final-independent-review.md`.

Status legend: `[x]` complete in plan stage; `[ ]` required downstream.

## Plan-stage handoff

- [x] Immutable route, PRD v20 §13.12 / SD-73–75, audit, and approved/rejected commit boundaries read.
- [x] Worktree confirmed at clean `d7e5ad35865b77cfa5c05ddf4b3c4dccd87e9c72` / `origin/main`.
- [x] Standard/code QA policy recorded as `plan-check:selected-independent-pass:final-verify` with one deep and up to two fast reviewers.
- [x] No independent-review claim made for this plan stage; no separate reviewer ran.
- [x] Source left unmodified; only canonical `plan.md` and `checklist.md` written.
- [x] Spec-read marker failure (`.spec-grounding` read-only) recorded; upstream immutable route gate remains the authoritative satisfied evidence.

## Safety and candidate application

- [x] Reconfirmed clean worktree and expected `d7e5ad35865b77cfa5c05ddf4b3c4dccd87e9c72` / `origin/main` before attempting source mutation; no cherry-pick state remains after the failed command (evidence: `dev_logs/execute-blocked.md`).
- [x] Read assigned PRD/audit inputs; the PRD read-marker hook failed only because `.spec-grounding` is a read-only mount (evidence: `dev_logs/execute-blocked.md`).
- [x] Enumerated files touched by `7094c92b` and `c95ed391`; ran `preflight.sh write <file> codex-headless` for each before the required application attempt (evidence: `dev_logs/execute-blocked.md`).
- [x] UNBLOCKED: `git cherry-pick --no-commit 7094c92b c95ed391` succeeded in this run (both commits' 25 files staged, no cherry-pick state remaining) (evidence: `dev_logs/execute-partial.md`).
- [x] Resolved against current main; candidate prose already matches plan intent, no Claude teammate/subagent conflation found in either diff (evidence: `dev_logs/execute-partial.md`).
- [x] Confirmed `6b3a34bc` is not an ancestor and its co-primary/multi-capability composition contract is absent from the diff.
- [x] Changes kept uncommitted (partial implementation only; not ready for commit).

## SD-74 qualified dispatch topology

- [x] Replaced `owner_depth`, `max_depth`, node `depth` with `owner_dispatch_depth`, `max_dispatch_depth`, `dispatch_depth` in `capabilities/topologies.json`, `tools/capability_topology.py`, `utilities/capability-route.py`, `utilities/dispatch-node.py` (evidence: `dev_logs/execute-partial.md`).
- [ ] Public wrapper/output/registry/Fleet bare depth fields NOT yet renamed — adapter wrappers' `--depth` CLI flag, Fleet model/collectors, and dispatch-registry/completion row fields are unchanged.
- [x] Direct route is dispatch depth 0, `execution_surface=inline`, `registered_worker=false`, no worker registry row (compiler-level; not yet propagated through the real wrapper path).
- [x] Quick route has one dispatch-depth-1 owner node, max dispatch depth 1, no child node (compiler-level).
- [x] Standard+ owner/stage topology remains dispatch depth 1/2 (topologies.json + compiler).
- [ ] Node dispatch depth surviving native/inline standard+ fallback without implying registration — NOT verified end-to-end (wrapper/registry layer untouched).
- [x] Codex `agents.max_depth` left untouched and not referenced by the new `max_dispatch_depth`/eligibility logic.

## SD-75 namespace closure and four surfaces

- [x] Transport vocabulary is exactly `headless|interactive` (`capabilities/topologies.json`).
- [x] Execution-surface vocabulary is exactly `registered-headless|codex-native-subagent|claude-subagent|claude-agent-team-teammate|inline` (registry + `capability-route.py`).
- [x] Fallback-hop vocabulary is exactly `same-harness-headless|cross-harness-headless|native-subagent|inline` (already correct in `capability-route.py`'s `FALLBACK_ORDER`; now also declared in the registry and enforced by the topology validator).
- [x] `detached-process` represented only as `resource_transport` on resource-runner nodes, outside the transport/execution-surface/fallback-hop vocabularies.
- [x] Global vocabulary validation precedes recipe allowlist validation in `capability_topology.py` (`unknown fallback hops` check runs before per-recipe scope checks).
- [x] Unknown strings fail before route write for the compiler paths touched (topology validation, quick transport/eligibility). NOT verified for registry claim/spawn (untouched layer).
- [ ] New attempts record both `execution_surface` and boolean `registered_worker` evidence — done for compiled route *nodes*; NOT done for runtime *attempt* rows in `dispatch-registry.py`/`dispatch_contract.py` (untouched).
- [ ] Only registered wrapper headless attempts may set `registered_worker=true` — NOT enforced at the wrapper/registry layer (untouched).
- [x] Four-surface prose distinction (Codex native subagent, Claude subagent, Claude agent-team teammate session, registered headless worker session) added to `core/OPERATIONS.md` §5.10 "Delegation surfaces are distinct"; corrected the candidate's "team agent — a runtime-native subagent" mislabel to "Claude agent-team teammate session, not a runtime-native subagent" (evidence: `dev_logs/execute-partial-2.md`). `core/CONVENTIONS.md`/`WORKFLOW.md` prose beyond the two candidate commits, role/capability/Skill-owner prose, and the terminology conformance check are still NOT done.

## SD-73 strict quick behavior

- [x] Omitted quick transport derives to `headless` (`compile_route`).
- [x] Structured registered-headless eligibility (`--registered-headless-evidence`) checked during compilation.
- [x] Missing/unknown/unsupported eligibility returns exactly `quick-headless-unavailable` (tested).
- [x] Empty/interactive/native-subagent/inline-fallback/arbitrary quick transports fail (`invalid quick transport: ...`, tested for one case; full negative matrix not enumerated).
- [x] Invalid quick compiles raise before `write_once`/registry/claim/spawn are reachable (no code path between the raise and any of those calls).
- [ ] Quick single-live-attempt-under-lock, terminal-retry-history, and `quick-registered-headless-exhausted` — NOT implemented; this is runtime registry/wrapper behavior (`dispatch-registry.py`, `stage-dispatch-fallback.py`) which was not touched in this round.
- [ ] Quick native/inline attempt/child-row zero-emission proof at the registry/Fleet layer — NOT verified (untouched layer).
- [x] No automatic intensity/transport/execution-surface mutation exists in the compiler (any change is a new `compile_route` call).

## Direct and standard+ preservation

- [x] Direct retains main-inline behavior with no registry worker row, at the compiler level.
- [x] Standard+ retains `same-harness-headless -> cross-harness-headless -> native-subagent -> inline` ordering (`FALLBACK_ORDER`, unchanged and already correctly named).
- [x] Standard+ checked tuple binding, stable attempts, completion markers pass their existing focused tests unmodified (`dispatch_contract`, `dispatch_registry`, `stage_dispatch_fallback`, `worker_route_guard`, `dispatch_completion_marker` all green against the new field names).
- [ ] Standard+ headless attempts registered vs. native/inline fallbacks explicitly unregistered — NOT verified as *attempt*-level evidence (only the static route's `dispatch_fallback` chain was checked; the wrapper/registry layer that would stamp `registered_worker` on live attempts is untouched).

## Versioning, legacy, and self-hosting exception

Remaining unchecked items below this point were NOT attempted in this round
(see `dev_logs/execute-partial.md` "Not implemented" for the full breakdown);
they require a follow-up execute round against `utilities/dispatch-registry.py`,
`utilities/stage-dispatch-fallback.py`, the three adapter wrappers,
`tools/fleet/`, canonical prose/generators, and the Step 5/6 acceptance and
verification matrix.

- [x] `capabilities/topologies.json` and route `schema_version` bumped (1 -> 2); `verify_route` rejects any non-current `schema_version`.
- [x] `legacy_route_diagnostic()` added in `capability-route.py` for read-only Fleet labeling of pre-v20 routes (not yet wired into Fleet, which doesn't call it).
- [x] `verify_route`/mutating compile paths reject legacy `schema_version`; node/start/resume/complete at the registry/wrapper layer NOT audited for the same rejection (untouched).
- [ ] Fleet may display legacy history without promoting it to current/resumable state.
- [ ] `_internal/code-route.json` remains immutable.
- [ ] Depth-1 owner creates `_internal/metrics.md` with the exact self-hosting legacy bootstrap stanza from `plan.md`.
- [ ] Exception is scoped to `rt-4ddceb3e346c0941` and this remediation cycle only.

## Canonical sources and generated propagation

- [ ] Portable topology/compiler/wrapper/registry/completion/liveness/Fleet sources updated first.
- [ ] Core, capability, role, and canonical Skill prose updated to qualified/four-surface terminology.
- [ ] Generator templates updated before generated outputs.
- [ ] Write preflight run for every generator/mirror output that will change.
- [ ] `python3 tools/generate.py` run after canonical edits.
- [ ] `tools/fleet/` mechanically mirrored to `adapters/claude/tools/fleet/`.
- [ ] No generated output hand-edited after regeneration.

## Deterministic test additions

- [ ] Every capability/mode quick recipe has a supported-evidence positive fixture.
- [ ] Quick invalid transport/evidence matrix asserts exact enums and zero emissions.
- [ ] Quick one-live-attempt, terminal-history, exhaustion, no-child, and no-native/inline fixtures added.
- [ ] Direct depth-0/no-row preservation fixture added.
- [ ] Standard+ full fallback-order and registration-status preservation fixture added.
- [ ] Namespace unknown-value negative fixtures added.
- [ ] Qualified-depth conformance rejects current bare schema/prose/projection fields.
- [ ] Four-surface terminology conformance rejects Claude teammate/subagent conflation.
- [ ] Legacy read-only plus resume/re-emit refusal fixtures added.
- [ ] Codex native `agents.max_depth` variation is proven irrelevant to headless maximum/eligibility.
- [ ] Composition/co-primary non-introduction regression added.

## Fresh post-change route acceptance evidence

- [ ] Fresh `test_logs/route-acceptance/direct.json` generated and assertions pass.
- [ ] Fresh `test_logs/route-acceptance/quick.json` generated and assertions pass.
- [ ] Fresh `test_logs/route-acceptance/standard-plus.json` generated and assertions pass.
- [ ] `summary.md` records changed-worktree HEAD, commands, route IDs/hashes, expected fields, and negative zero-emission results.
- [ ] No acceptance artifact is copied from the legacy `_internal/code-route.json`.

## Required verification

- [ ] `python3 tools/capability_topology.test.py`
- [ ] `python3 utilities/capability_route.test.py`
- [ ] `python3 utilities/dispatch_contract.test.py`
- [ ] `python3 utilities/dispatch_node.test.py`
- [ ] `python3 utilities/dispatch_registry.test.py`
- [ ] `python3 utilities/dispatch_completion_marker.test.py`
- [ ] `python3 utilities/dispatch_progress.test.py`
- [ ] `python3 utilities/worker_route_guard.test.py`
- [ ] `python3 utilities/stage_dispatch_fallback.test.py`
- [ ] `python3 utilities/stage_dispatch_capacity.test.py`
- [ ] `python3 utilities/worker_bootstrap.test.py`
- [ ] `python3 utilities/worker_dispatch_prompt.test.py`
- [ ] Claude/Codex/OpenCode `dispatch-headless.sd45.test.py`
- [ ] Claude/Codex/OpenCode `dispatch-headless.sd15.test.sh`
- [ ] `python3 -m unittest discover -s tools/fleet/tests -p 'test_*.py'`
- [ ] New v20 acceptance/conformance suite.
- [ ] `sh tools/routing-contract.test.sh`
- [ ] `python3 tools/generate.py --check`
- [ ] `python3 tools/sync-entry-skill-layer.py --check`
- [ ] `sh tools/check-adaptation-boundary.sh`
- [ ] `git diff --check`
- [ ] Aggregate run completed through bounded `preflight.sh verification-runner`; logs retained under `test_logs/`.

## QA review, bounded fix loop, and commit gate

- [ ] A separate deep reviewer performs the risk-focused diff/final-verification pass and writes a durable artifact.
- [ ] Up to two separate fast reviewers are used only if selected; only reviewers that actually ran are named.
- [ ] Review covers quick zero emission, namespace closure, migration fence, direct/standard+ preservation, generated ownership, and rejected-commit exclusion.
- [ ] If findings require changes, at most one execute-fix round is run and every verification/review gate is repeated.
- [ ] No independent-pass claim is made without a separate worker artifact.
- [ ] Final verdict is PASS; otherwise stop without commit.
- [ ] Final diff contains only approved scope and no merge/cherry-pick residue.
- [ ] One task commit created only after PASS.
- [ ] Stage workers do not push, merge, clean worktrees, or modify the original source branches.
