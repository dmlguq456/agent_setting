No asynchronous Monitor/wakeup/scheduling waits. You are the mandatory
independent cross-harness implementation reviewer for the fresh Fleet v16
corrective cycle. This is a read/test/review stage. Do not edit source, tests,
checklist, mirrors, or prior reports; do not commit/push/merge/clean and do not
call any live provider. You may write only the required review artifact under
the canonical artifact root.

Read completely before judging:

- /home/Uihyeop/agent_setting/.agent_reports/spec/agent-fleet-dashboard/prd.md
- /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/plan/plan.md
- /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/plan/checklist.md
- /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/dev_logs/execute.md
- /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/dev_logs/execute_fix2_stage.md
- /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/final_report.md
- /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/_internal/dev_reviews/phase_review.md
- /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/_internal/dev_reviews/orchestrator_repro.md

Inspect the complete current source/test diff, including untracked files. The
prior test count is supporting evidence only; reproduce every correction group
below and independently inspect the implementation.

1. A main Session with an attached route-exact WorkProjection visibly renders
   stage/progress in wide 168 and 120, narrow 100, stack 60, plain, and group
   surfaces. Reproduce the root Session case from orchestrator_repro.md. Run an
   actual provider-disabled live command whose primary root Session row contains
   its attached route stage/progress; JSON-only projection presence is not
   sufficient. Explicit-invalid/ambiguous evidence must show no first-route or
   fixed-pipeline revival.
2. A unique exact `(pid, proc_start)` registered route candidate is adopted;
   only when exact identity evidence is absent may one same-harness
   `realpath(cwd)` candidate be adopted. Reproduce exact positive, unique cwd
   positive, PID-reuse refusal, and duplicate-cwd refusal.
3. `attempt_id` alone is not an explicit route tuple and does not block
   owner/child traversal. Check Session `session_id/parent_sid` and DispatchJob
   `slug/parent_slug` traversal.
4. Direct owner route A versus child route B yields `owner-route-conflict`,
   while all active same-route siblings remain visible. Reproduce attempt-only
   owner, siblings, multiple route/hash, and direct conflict cases.
5. Confirm render-local first-child/first-route selection is retired and every
   row consumes only its attached WorkProjection. Search for retired helpers as
   well as exercising invalid/ambiguous evidence.
6. In process view, both route and degrade cards emit each chunk as job row ->
   context/NOW detail -> exact-session sub-agent strip.
7. Public route JSON preserves old top-level keys and meanings, including node
   `model`, `harness`, `effort`, `elapsed_min`, and `note`, while additively
   exposing WorkProjection/context. It must serialize from the attached backing
   view without reopening route files. Confirm the old-key-only consumer and
   absence of private evidence.
8. The sealed arbitrary DAG `survey -> {claim-a, claim-b} -> synth` preserves
   record order within topological levels, visibly retains both parallel
   siblings and fan-in, preserves metadata, and emits no fixed-pipeline text or
   semantics inferred from opaque node IDs. Do not modify or reimplement the
   schema-v2 compiler.
9. Resolve the prior yellow obligations: deterministic projection-aware demo;
   meaningful sequence/head evidence or the explicitly truthful bounded
   same-sample contract; pinned old-key JSON consumer; and PRD-compatible public
   `ambiguity[]` array shape.

Also verify the context/NOW truth table, exact child association, context
orthogonality, F-39 default concurrency 3/hard 4, four rolling starts per 60s,
600s main/150s child debounce, Haiku default with tool denial, shell-free custom
argv/model replacement, zero provider calls in JSON/once/demo/tests, and
OpenCode SQLite `mode=ro` plus DB/WAL/SHM immutability.

Run the focused regressions and the full required matrix: complete Fleet suite,
compose-on-demand, capability-route, sealed fixture, group/process once, public
JSON, compile, mirror parity, git diff --check, adaptation guard, and adaptation
boundary. Run adaptation guard and boundary sequentially. Record exact commands,
counts, outputs, source findings, warnings, and any unsupported runtime contract
in:

/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/_internal/dev_reviews/phase_review_followup.md

Use PASS only if every one of the nine correction groups and every v16
acceptance row is met with no major or yellow obligation remaining. Otherwise
write a precise FAIL report and do not bind the route marker.

On PASS only, while this registered attempt remains open, resolve its exact
attempt_id from AGENT_DISPATCH_ATTEMPT_ID (or the unique current registry row)
and run:

python3 utilities/capability-route.py complete \
  --route /tmp/fleet-unified-stage-ui.ammXPV/route.json \
  --node impl-review \
  --evidence /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/_internal/dev_reviews/phase_review_followup.md \
  --jobs /home/Uihyeop/agent_setting/.dispatch/jobs.log \
  --attempt-id <this-review-attempt-id> \
  --dispatch-depth 2 \
  --transport headless \
  --execution-surface registered-headless \
  --registered-worker 1 \
  --fallback-hop cross-harness-headless

Confirm the attempt-bound marker names this review attempt, then finish with the
exact three-line kernel handoff.
