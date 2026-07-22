No asynchronous Monitor/wakeup/scheduling waits. This is an atomic read-oriented
code-execute gate finalizer, not another implementation or correction pass. Do
not edit source, tests, plan, checklist, artifacts, or mirrors; do not
commit/push/merge/clean and do not call a live provider.

Read the approved plan/checklist and the complete fresh execute evidence at:

/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/dev_logs/execute_fix2_stage.md

The fresh registered correction attempt reported all mandatory execute gates
green: focused correction regressions 37/37; Fleet 773/773; compose 9/9;
capability-route 30/30; sealed arbitrary-DAG fixture verification;
provider-disabled group/process/JSON smoke; compileall; mirror parity and
diff-rq; git diff --check; adaptation guard; and then adaptation boundary,
sequentially. Its exact attempt was
att-aae6de402638cfed0535adb06d383b1af8eb8d37ab0612a2 and its terminal verdict
was PASS.

Revalidate read-only:

1. The evidence artifact is internally complete and names the exact attempt,
   route, assurance, corrections, commands/results, and warnings.
2. Canonical-to-Claude Fleet mirror parity and git diff --check pass.
3. The focused WorkProjection/context tests pass.
4. The exact correction attempt is terminal PASS in the inherited registry.

If any revalidation is red, emit FAIL and do not mark complete. On PASS, before
the final handoff while this registered finalizer attempt is open, resolve its
attempt_id from the unique open jobs row matching AGENT_DISPATCH_SELF_SLUG,
AGENT_ROUTE_ID, and AGENT_ROUTE_NODE=execute. Run:

python3 utilities/capability-route.py complete \
  --route /tmp/fleet-unified-stage-ui.ammXPV/route.json \
  --node execute \
  --evidence /home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui/dev_logs/execute_fix2_stage.md \
  --jobs /home/Uihyeop/agent_setting/.dispatch/jobs.log \
  --attempt-id <this-finalizer-attempt-id> \
  --dispatch-depth 2 \
  --transport headless \
  --execution-surface registered-headless \
  --registered-worker 1 \
  --fallback-hop same-harness-headless

Confirm the attempt-bound marker exists and names this finalizer attempt, then
finish with the exact three-line kernel handoff using the execute evidence path.
