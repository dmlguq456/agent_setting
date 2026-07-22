No asynchronous Monitor/wakeup/scheduling waits. This is the fresh corrective
cycle's one authorized implementation-correction allowance after the mandatory
independent review returned FAIL. You own canonical `tools/fleet/**`, v16 tests,
the checklist/dev log, and the final prescribed rsync to
`adapters/claude/tools/fleet/**`. Do not hand-edit the mirror in parallel. Do
not commit/push/merge/clean and do not call a live provider. Preserve all
unrelated/concurrent changes in the dirty worktree.

Read completely:

- /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/_internal/dev_reviews/phase_review_followup.md
- /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/_internal/dev_reviews/orchestrator_repro.md
- /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/_internal/dev_reviews/root_post_execute_findings.md
- /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/dev_logs/execute_fix2_stage.md
- /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/plan/plan.md
- /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/plan/checklist.md

Fix every red/yellow item in `phase_review_followup.md`, without narrowing:

1. Remove the remaining first-child selection from owner/conductor aggregation
   in `resolve_work_projection`. For two or more same-route active children, a
   main Session's attached WorkProjection and rendered stage text must visibly
   represent every agreeing active sibling in sealed route record order at
   wide 168/120, narrow 100, and stack 60. It must not depend on collector/jobs
   iteration order. Retain full `active_nodes`, progress, route identity, and
   fail-closed owner-route-conflict/multiple-route behavior.
2. Add a regression that passes a multi-child-agreement Session owner through
   the real `_build_lines`/Session row path and asserts every sibling id is
   visible at all required widths, including reversed job input order. Preserve
   explicit-invalid/ambiguous no-first-route behavior.
3. Wire the sealed `synth_composed_survey.json` fixture into
   `test_f28_route.py`, `test_f28_breadcrumb.py`, and
   `test_f30_process_view.py` so group/process/plain/public-route JSON prove
   `survey -> {claim-a, claim-b} -> synth`, sibling record order, fan-in,
   metadata, and no fixed-pipeline text.
4. Extend `demo.py` with a deterministic provider-disabled composed-DAG,
   multi-sibling-owner entity. `--once --view group` must visibly exercise the
   main Session's complete parallel stage/progress; process output must exercise
   the route/degrade chunk contract. Do not add live provider calls.
5. Add a dedicated populated old-key-only `_snapshot_json()` consumer test. A
   consumer reading only the pre-v16 keys/meanings must remain unchanged while
   additive WorkProjection/context data is present; assert private evidence is
   absent and node `model`, `harness`, `effort`, `elapsed_min`, and `note`
   retain their meanings.
6. Preserve every previously green acceptance group: exact identity/cwd
   adoption and refusal; attempt-only traversal; owner/child conflict; process
   job->context/NOW->subagent order; PRD-compatible `ambiguity[]`; context truth
   table/orthogonality/exact association; F-39 quotas/debounce/provider
   boundaries; OpenCode mode=ro DB/WAL/SHM immutability; sealed schema-v2
   compiler untouched; concurrency 3/hard 4 and four starts per 60s.

Also fix every open item in `root_post_execute_findings.md`; these are
independently reproduced integration blockers, not optional follow-up work:

7. Make `test_f39_title_quota.py` hermetic with no inherited
   `AGENT_ARTIFACT_ROOT`: isolate `AGENT_MODEL_GOVERNOR_ROOT` under its temp
   directory, save/restore all governor limit/kill-switch variables, and remove
   the contradictory set-then-pop concurrency setup. The provider-call test
   must observe exactly one real provider invocation.
8. Align the central `utilities/model-worker-governor.py` title class ceiling
   with Fleet's hard ceiling `4` while retaining the separate global total and
   rolling-start protections. Add a central test that admits four live title
   leases and rejects the fifth, plus a cross-file parity assertion against
   `refresh_title.MAX_CONCURRENCY`.
9. Owner/main stage labels must be derived from all active route nodes in
   sealed record order even when a child carries the generic
   `assigned_contract=autopilot-code`: one active node displays its node ID;
   parallel nodes display the complete ordered set. A leaf may retain its
   validated micro-contract label. Add both single-generic-child and parallel
   owner regressions.
10. Replace direct live OpenCode SQLite reads in `refresh_title.py` with a
    fail-closed, consistency-checked ephemeral private snapshot of the database
    plus any existing WAL; never copy or open the source SHM. Capture source
    DB/WAL/SHM (and journal) signatures before/after copy using device, inode,
    size, mode, mtime_ns, and ctime_ns, and reject any change. Prefer Linux
    reflink when available with a streaming-copy fallback, open only the private
    snapshot using `mode=ro&cache=private`, and reuse one snapshot/connection for
    table selection plus delta reading in the worker. Add a live WAL regression
    that keeps the writer open, sees an uncheckpointed exact-session row, and
    proves source DB/WAL/SHM bytes and write metadata remain identical. Do not
    expand the hot-path OpenCode collector and never restore/rewrite source
    files.
11. Correct the plan/checklist/dev-log wording that currently forbids any DB
    copy: a private consistency-checked ephemeral DB+WAL snapshot is allowed;
    persistent copies and source DB/WAL/SHM writes remain forbidden.

Run focused new regressions first, then the complete required matrix after the
last source/test edit: Fleet discovery; compose-on-demand; capability-route;
sealed fixture verify; provider-disabled group/process once and public JSON;
compileall; canonical/mirror diff and mirror parity; git diff --check;
adaptation guard; then adaptation boundary sequentially. Run an actual
provider-disabled live command and record the exact main Session primary row
showing every parallel sibling and progress. Do not claim completion from a
test count alone.

Update checklist/dev logs truthfully and write a distinct durable stage artifact:

/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/dev_logs/execute_fix2_review_correction.md

On PASS only, while this registered attempt remains open, bind a new exact
execute marker to that evidence with:

python3 utilities/capability-route.py complete \
  --route /tmp/fleet-unified-stage-ui.ammXPV/route.json \
  --node execute \
  --evidence /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/dev_logs/execute_fix2_review_correction.md \
  --jobs /home/Uihyeop/agent_setting/.dispatch/jobs.log \
  --attempt-id <this-correction-attempt-id> \
  --dispatch-depth 2 \
  --transport headless \
  --execution-surface registered-headless \
  --registered-worker 1 \
  --fallback-hop same-harness-headless

Confirm the marker names this exact correction attempt, then finish with the
exact three-line kernel handoff. If any required gate is red, emit FAIL and do
not bind the marker.
