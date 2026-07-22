# Orchestrator live-reproduction addendum

Date: 2026-07-22 19:17 KST  
Scope: read-only checks against the implementation snapshot reviewed in
`phase_review.md`. This addendum does not alter the independent reviewer verdict.

## Must-fix findings beyond the independent review

1. **The main Session row does not render its attached WorkProjection.** Live
   `--json` gave the current root Session `source=route-exact`, active node
   `impl-review`, and progress `3/6`, but `--once --view group` rendered only:

   ```text
   codex (...)  Session stage display rendering ▾2  main  5h17m
       ctx 42% normal · ...
   ```

   The primary row had no stage/progress zone. This misses the user's central
   requirement and PRD F-36/F-33. Add projection-driven Session stage/progress
   rendering in wide, narrow, and stack/plain paths, with an explicit live-output
   regression test.

2. **Exact leaf association is checked only for conflicts, never adopted.** In
   `projection.py`, a unique job with matching `(pid, proc_start)` is not used to
   project a Session; only the `>1` conflict case is handled. Likewise, the unique
   same-harness `realpath(cwd)` fallback is absent. Add positive exact-identity and
   unique-cwd joins plus two-candidate ambiguity tests.

3. **`attempt_id` alone incorrectly counts as an explicit route tuple.** A live
   depth-1 owner with an attempt but no route fields currently becomes
   `registry-exact/route-record-mismatch` and never traverses its children. The
   explicit-route barrier must comprise route fields, not attempt identity alone.

4. **Direct owner/child disagreement is not detected.** This independently
   confirms the review's major finding: an owner route A and child route B must
   return `owner-route-conflict`, never early-return route A.

5. **Group rendering still chooses the first child/route.** Remove
   `_conductor_stage_override()` and `_conductor_route_seq()` first-child logic.
   Every Session/DispatchJob row must render only `entity.work_projection`, and an
   ambiguous projection must not fall back to a fabricated fixed/first route.

6. **Process detail order is wrong.** This independently confirms the review's
   other major finding. Build each chunk as job row -> context/NOW detail -> exact
   Session sub-agent strip inside `_route_card()` and `_degrade_card()`; do not
   append all detail rows after the completed card.

7. **Top-level route JSON is not additive-compatible.** Current v16 output removes
   legacy node keys `model`, `harness`, `effort`, `elapsed_min`, and `note`, and
   changes the legacy route `source` meaning. Preserve the existing
   `route.summary()` key set and meanings from the already attached validated
   backing view, then add only v16 fields. Pin an old-key-only consumer test.

8. **Arbitrary DAG display order/parallelism is not fully preserved.** Active
   nodes are sorted by `(level, id)` instead of record order, and a flat route
   breadcrumb can erase parallel siblings. Preserve record order within each
   topological level and render a branch set/fan-in without semantic stage-name
   inference. Test the sealed `survey -> {claim-a, claim-b} -> synth` fixture.

## Required correction evidence

- Positive Session/DispatchJob exact-identity parity and unique-cwd association.
- Owner `session_id/parent_sid`, owner `slug/parent_slug`, attempt-only owner, and
  direct owner/child conflict cases.
- Wide/narrow/stack main Session stage/progress rendering and explicit-invalid
  no-first-route rendering.
- Process job/detail/sub-agent ordering for route and degrade cards.
- Old route JSON keys and meanings retained.
- Sealed composed-DAG record order, parallel siblings, and fan-in retained.
- Actual live `FLEET_TITLE_DISABLE=1 --once --view group` output showing the root
  Session's attached route stage/progress before integration.
