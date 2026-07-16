# Deep plan review 2 — direct headless resilience

verdict: **FAIL**

scope: read-only review of the amended `plan.md` and
`_internal/plan_refinement.md` against the concrete blockers recorded by
`plan_review_deep1.md`, `plan_review_fast1.md`, and `plan_review_fast2.md`.
No source files were edited.

## Resolved items

- The immutable route metadata now explicitly records `qa: thorough`, standard
  intensity, the depth-1 owner, and the full durable stage graph.
- The no-broker boundary remains explicit and complete.
- The plan assigns the synchronous watchdog/continuation responsibility to
  `utilities/stage-dispatch-fallback.py --start --progress-window-seconds N`,
  keys state by exact route/node/attempt, requires immediate PID/start
  revalidation before signal, and resumes the checked SD-50 iterator.
- Capacity selection is kept out of wrappers; the amendment defines
  adapter-paired CLI inputs, a canonical per-node retry authority, persisted
  cooldown/prior-attempt evidence, and the exactly-one retry rule.
- Reconciliation now requires locked re-read/reclassification, SD-49 row
  identity, reused SD-29 gates, explicit dry-run/apply behavior, and selected
  current-work filters.
- The nonexistent Claude preflight projection was removed. Live nested smoke
  and the final commit are explicitly depth-1-owner-only, and the exact
  canonical artifact set is named.

## Remaining blocking gaps

1. **The watchdog lifetime/terminal contract is still not closed.** Lines
   59–67 say the synchronous command remains in the foreground for “at most
   two bounded windows,” while lines 66–72 allow deterministic progress to
   reset the consecutive quiet-window count. Those statements cannot enforce
   a later stall: one progress-bearing observation can consume one of the two
   total windows, after which the command may exit before two later consecutive
   quiet windows occur. The plan also still omits the requested terminal
   success/failure conditions and structured exit/output contract. Define the
   loop as bounded per observation but continuing until an exact terminal
   result, two consecutive quiet windows, or an explicit owner cancellation;
   define how successful child completion returns without fallback and which
   exit/result makes preflight continue or stop. The public-command fixture
   must cover progress reset followed by a later two-window stall, not only an
   initially silent child.

2. **The model allow/role authority remains abstract.** Lines 111–114 name an
   “adapter role/profile resolver” and “configured allowed model set,” but do
   not identify the existing command/module/config key that is authoritative
   for each of Codex, Claude, and OpenCode. This was an explicit prior blocker:
   code-execute still has to invent where concrete model/profile resolution and
   allow-list proof come from. Name the actual resolver surfaces and the
   comparable concrete identity they return, including how explicit
   inheritance is recorded and validated. Keep the already-defined paired CLI
   and canonical retry fields.

3. **`dead-stale` still lacks positive terminal evidence and class separation.**
   Lines 154–161 require a newest exact attempt, no live exact PID, and two
   quiet windows, but “terminal-not-updated” is not defined by a positive
   terminal source. “No newer ... completion-marker update” is an absence test,
   not terminal proof. As written, an exact-dead row can fall into both the
   preceding `dead-*` class and `dead-stale`, and a missing completion marker
   plus elapsed quiet windows can still authorize closure despite the prior
   review requiring that missing markers never do so. Define a mutually
   exclusive truth table: the exact terminal evidence source/version required
   for `dead-stale`, completion-marker semantics, the selected note when PID
   death already proves `dead-*`, and explicit veto behavior when terminal
   evidence is absent or ambiguous.

These are implementation-shaping safety decisions, not details that should be
invented during code-execute. Execution should not proceed until they are
durably amended.

## Non-blocking precision corrections

- Harmonize line 51 (“reject ... repeated phase refreshes”) with line 66
  (permit a repeated phase when its deterministic digest changes) by stating
  once that sequence/generation is monotonic and only identical/replayed
  evidence is rejected.
- Replace the remaining vague targets at lines 91, 139, and 175 with the
  concrete prompt and liveness consumers identified by the first fast review.
  This will make the single-classifier import boundary mechanically reviewable.

## Guard and assurance evidence

- `preflight.sh qa-policy thorough code`: passed; required assurance is
  `plan-check:selected-independent-pass:final-verify` with up to two deep and
  two fast reviewers.
- `preflight.sh mode-info dev/backend`: portable Codex mode projection resolved.
- `preflight.sh write .../_internal/plan_review_deep2.md codex-headless`: passed
  before this artifact write.
- `preflight.sh worker-route --check`: returned usage exit 2 because this
  native review assignment did not supply a route file/node/digest tuple to the
  worker-route guard. The parent owner route was already wrapper-validated;
  this did not prevent the read-only review and no route was reselected.
