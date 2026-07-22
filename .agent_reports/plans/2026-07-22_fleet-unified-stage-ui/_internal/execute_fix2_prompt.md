# Fleet v16 fresh corrective execute — fix2

You are the registered dispatch-depth-2 `code-execute` stage for the sealed route
`rt-dfec3aabe921b37f`, node `execute`. This is a fresh corrective cycle authorized
after the prior independent review failed. You are not alone in the repository:
preserve every concurrent/user change, do not revert unrelated edits, and adapt to
the dirty worktree. Do not commit, push, merge, clean the worktree, or edit git
metadata.

## Immutable scope and ownership

- Worktree: `/home/Uihyeop/agent_setting-wt/fleet-unified-stage-ui`
- Canonical artifact root: `/home/Uihyeop/agent_setting/.agent_reports`
- Plan cycle: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_fleet-unified-stage-ui`
- Route file: `/tmp/fleet-unified-stage-ui.ammXPV/route.json`
- Route identity/hash: `rt-dfec3aabe921b37f` / `sha256:dfec3aabe921b37fa9da8973c530b48ea92b7a9cd8fa9cdff7a7dd950512d404`
- Source ownership: canonical `tools/fleet/**`, its v16 tests/fixtures, `plan/checklist.md`, and `dev_logs/execute.md`.
- Mirror ownership is final-only: after canonical verification passes, run the prescribed `rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/`. Never hand-edit canonical and mirror in parallel.
- Do not modify or reimplement the compose-on-demand schema-v2 route compiler.

Read completely before editing:

1. `/home/Uihyeop/agent_setting/.agent_reports/spec/agent-fleet-dashboard/prd.md`
2. `plan/plan.md` and `plan/checklist.md`
3. `dev_logs/execute.md`
4. `final_report.md`
5. `_internal/dev_reviews/phase_review.md`
6. `_internal/dev_reviews/orchestrator_repro.md`

Inspect the complete current source/test diff. The prior 766/766 result is not
acceptance evidence for behaviors its tests omitted.

## Mandatory correction groups

Fix every finding in both review files and prove all nine groups below. Do not
narrow this pass to the prior review's two red items.

1. A main `Session` carrying a route-exact `WorkProjection` must visibly render
   its stage/progress in wide 168 and 120, narrow 100, stack 60, plain/group, and
   live provider-disabled output. The root reproduction must show active
   `impl-review`, progress `3/6` (or the truthful current route state at run time)
   on the primary Session row.
2. Projection association must adopt one unique exact `(pid, proc_start)`
   registered route candidate. Only when exact identity evidence is absent may it
   adopt one same-harness `realpath(cwd)` candidate. Refuse PID reuse and multiple
   cwd candidates. Test both positive and refusal paths.
3. `attempt_id` by itself is not an explicit route tuple. An attempt-only owner
   must still traverse `session_id/parent_sid` or `slug/parent_slug` children.
4. A direct owner route A versus child route B must fail closed as
   `owner-route-conflict`; multiple children from the same validated route remain
   all visible active siblings.
5. Retire render-local `_conductor_stage_override()` /
   `_conductor_route_seq()` first-child or first-route selection. Every row must
   consume only its attached `WorkProjection`. Explicit-invalid or ambiguous
   evidence must never revive `_PIPE_STAGES` or a first child.
6. In process view, emit every active route and degrade chunk in exact order:
   job row -> context/NOW detail -> exact-session sub-agent strip. Never batch
   detail rows at card tail.
7. Preserve the old top-level route JSON keys and meanings, including node
   `model`, `harness`, `effort`, `elapsed_min`, and `note`, while adding v16
   fields. Serialize from attached backing views without reopening route files.
   Pin an old-key-only consumer.
8. Preserve sealed record order within every arbitrary DAG topological level,
   visibly retain parallel siblings and fan-in, and infer no semantics from
   opaque node IDs. Prove the sealed `survey -> {claim-a, claim-b} -> synth`
   fixture and the existing lab fork/fan-in.
9. Close every remaining yellow/unchecked plan obligation: deterministic
   projection-aware demo; truthful per-harness sequence/head evidence (or a
   clearly bounded contract that does not overclaim unavailable production
   evidence); old-key JSON test; and the PRD `ambiguity[]` public shape. Do not
   silently retain the current scalar schema deviation.

Update all affected constructors/serialization/rendering/tests coherently.
Preserve the following locked boundaries:

- F-39 is exactly concurrency default 3/hard 4, 4 starts per rolling 60s,
  debounce main 600s/child 150s, default Haiku with tool denial, and shell-free
  custom argv/model replacement.
- `--json`, `--once`, demo, width/projection/storm tests make zero live/default/
  custom provider calls.
- OpenCode SQLite remains URI `mode=ro`; prove DB/WAL/SHM bytes and write
  metadata unchanged.
- Context/NOW association is atomic; parent context is never inherited.
- Context pressure changes display only and remains orthogonal to route graph,
  node state, intensity, model/effort, QA/reviewer/test/retry/gate/guard/DoD.
- Artifact inference is legal only for route-tuple-absent exact-cardinality
  legacy evidence and provides stage label only.

## Required named evidence

Add or extend hermetic regressions for:

- exact identity positive, unique cwd positive, PID-reuse refusal, duplicate cwd
  refusal;
- Session `session_id/parent_sid`, DispatchJob `slug/parent_slug`, attempt-only
  owner, same-route siblings, multiple route/hash, direct owner/child conflict;
- main Session stage/progress at 168/120/100/60 and explicit-invalid
  no-first-route;
- process route and degrade job/detail/sub-agent order;
- old route JSON key/meaning compatibility plus additive WorkProjection/context
  and absence of private evidence;
- sealed composed DAG order/branch/fan-in/metadata/no fixed-pipeline text;
- context truth table, exact child association and orthogonality;
- title quotas, default/custom provider boundaries, and OpenCode zero-write.

After focused regressions, run every final gate truthfully:

```text
preflight verification-runner: complete tools/fleet/tests discovery
utilities/compose_route.test.py
utilities/capability_route.test.py
sealed fixture capability-route verify
provider-disabled group --once
provider-disabled process --once
provider-disabled public --json | json.tool
compileall canonical and mirror
mirror parity
git diff --check
tools/adaptation-guard.test.sh
tools/check-adaptation-boundary.sh
```

Run adaptation guard and adaptation boundary sequentially because the guard uses
temporary sentinel mutations. Do not mark a pre-existing/unrelated failure green;
record exact evidence. Update `plan/checklist.md` only for truly evidenced rows and
append/replace `dev_logs/execute.md` with this fresh attempt's commands, counts,
changed paths, warnings, zero-provider proof, and the assurance string
`plan-check:selected-independent-pass:final-verify`.

Return PASS only if all task-owned execute gates are green and the final canonical
rsync/parity state is truthful. The owner will bind the exact completion marker
after harvesting your PASS artifact.
