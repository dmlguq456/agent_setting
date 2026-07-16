# Deep plan review 3 — direct headless resilience

verdict: **FAIL**

scope: read-only re-review of the plan amended at
`2026-07-16 17:36:49 +0900`, focused on the blockers from
`plan_review_deep2.md`. No source files were edited.

## Resolved since review 2

- **Watchdog lifetime:** the synchronous public command now has an explicit
  maximum observation budget, continues observing after deterministic progress
  resets the quiet counter, and terminates on child terminal state, two
  consecutive quiet windows, or budget exhaustion. This removes the prior
  two-total-window contradiction and preserves detection of a later stall.
- **Heartbeat repetition:** the amendment now permits a repeated phase only
  when its deterministic evidence digest changes and otherwise leaves time and
  window state untouched.
- **Capacity authority:** model/profile validation is pinned to checked adapter
  role/model-map output and tracked profiles, with pre-launch concrete
  resolution. Local inspection confirms every adapter has a `model-map.sh` and
  Codex/OpenCode also have `role-map.sh`; Claude's stated alternative authority
  is its existing `model-map.sh`.
- **Named consumers:** the plan now names the Codex liveness reader, portable
  liveness utility, wrapper `dispatch_prompt()` producers, and exact
  `stage-heartbeat` projection instead of leaving the single-classifier
  boundary abstract.

## Remaining blocker

**The `dead-stale` safety predicate is unchanged and still not mutually
exclusive or positively terminal.** Lines 161–168 still authorize
`dead-stale` from newest exact identity, no matching live PID/start, no newer
transition/marker update, and two quiet windows. They do not require a specific
shared-classifier terminal verdict or a completion/terminal evidence record;
“no newer completion-marker update” remains an absence test. The preceding
exact-PID-missing/reused class already covers confirmed exact process death, so
the plan also does not define when that row receives its corresponding
`dead-*` note versus `dead-stale`.

Before execution, replace these overlapping bullets with an ordered truth
table or equivalent rule:

1. confirmed exact PID missing/reused closes only under the corresponding
   exact-death note after the shared classifier and safety gates pass;
2. `dead-stale` additionally requires a named, positive terminal evidence
   source/version that is not already the exact-death class, plus the existing
   newest-attempt/two-window/artifact/clock checks;
3. missing, absent, ambiguous, or mismatched terminal/completion evidence is a
   veto, not authorization from elapsed quiet windows.

This remains a safety-critical reconciliation decision that code-execute
should not invent. The other previously reported blockers are sufficiently
resolved for planning purposes.

## Guard evidence

- `preflight.sh qa-policy thorough code`: passed; assurance remains
  `plan-check:selected-independent-pass:final-verify`.
- `preflight.sh write .../_internal/plan_review_deep3.md codex-headless`:
  passed before artifact creation.
