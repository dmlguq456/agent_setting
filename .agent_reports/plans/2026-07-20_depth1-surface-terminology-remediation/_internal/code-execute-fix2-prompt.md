# Code-execute bounded continuation 2

Finish the existing partially implemented `execute` node. Read `plan.md`,
`checklist.md`, `dev_logs/execute-partial.md`, and
`dev_logs/execute-partial-2.md`; inspect the actual staged and unstaged diff.
Preserve valid work. Approved candidate content is already applied, so do not
run cherry-pick again.

This round must implement—not merely enumerate—the remaining machine layer:

1. Update wrapper/registry/fallback/liveness and all three adapter wrappers to
   use public/serialized `dispatch_depth`, validate/record the closed
   `execution_surface`, `registered_worker`, and `fallback_hop` namespaces,
   and reject unknowns before registry claim or spawn.
2. Implement quick's at-most-one-live registered-headless attempt, serial
   registered-headless retries, exact unavailable/exhaustion reasons, and no
   native/inline fallback or child rows.
3. Propagate the fields and legacy-read-only behavior through completion and
   Fleet canonical model/collectors/render/control/fixtures; sync the Claude
   Fleet mirror from the canonical tree.
4. Add deterministic negative/preservation/conformance tests and generate
   fresh direct/quick/standard+ acceptance evidence under the canonical test
   logs. Preserve direct main-inline and the standard+ four-hop chain.
5. Update remaining canonical/generated terminology through the repository
   generators and run focused tests sufficient for a complete execute handoff.

Run preflight write before every edit. `agents.max_depth` remains unchanged.
Do not touch explicit versioned legacy fixtures or rejected `6b3a34bc`
composition. Update `checklist.md` and write `dev_logs/execute-fix2.md` with
commands/results. Do not commit. PASS only when the full execute gate is met;
otherwise list exact failures. End with the exact three-line handoff.
