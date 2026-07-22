## Pipeline: Mode dev

Select the stage graph from `--intensity` before QA. `direct` performs produce plus sanity/report without this durable pipeline. `quick` uses one registered-headless dispatch-depth-1 one-shot owner with an inline micro-plan, plan-check-lite, and focused verification. standard+ follows the durable pipeline below.

The compiled standard+ route always carries the `plan-check` review node; select its unit by risk axis: UI or visual risk → the `design/critic` unit; research or domain risk → the `research/plan-review` unit; construction quality (the compiled default) → the `qa/plan-review` unit. Each runs as a sibling review node dispatched by the owner per the compiled route.

### Standard+ Stage Dispatch

The dispatch-depth-1 owner is a thin conductor. The approved pre-execution gate must already
have compiled an immutable standard+ route file with checked headless evidence. If that route
file or the canonical jobs path is unavailable, stop instead of launching an unbound row.
Dispatch every durable node through `utilities/dispatch-node.py`; it binds the route identity,
node, write scope, completion gate, exact fallback tuple, and current attempt axes to the
selected adapter wrapper:

```bash
STAGE_OUTPUT=$(python3 "$AGENT_HOME/utilities/dispatch-node.py" \
  --route "$ROUTE_FILE" --node "$NODE_ID" --adapter "$STAGE_ADAPTER" \
  --action start --slug "$STAGE_SLUG" --qa "$QA" \
  --parent "$CONDUCTOR_SLUG" --prompt-text "$STAGE_PROMPT" \
  -- --jobs "$CANONICAL_JOBS")
printf '%s\n' "$STAGE_OUTPUT"
ATTEMPT_ID=$(printf '%s\n' "$STAGE_OUTPUT" | sed -n 's/^attempt_id=//p' | tail -1)
test -n "$ATTEMPT_ID"
```

Keep `ROUTE_FILE`, `CANONICAL_JOBS`, `NODE_ID`, and the captured `ATTEMPT_ID` together until
that node's completion transaction succeeds. Never dispatch standard+ with a raw wrapper
command that omits the route record.

The prompt carries only subskill name, absolute input paths, output contract, intensity, and slug. It never carries plan bodies or prior-stage conversation. Each stage reads files; the conductor reads only verdict and gate state. Register every stage in `.dispatch/jobs.log`, monitor liveness, and keep conductor plus active stages at or below five processes. One-line or no-artifact micro-stages stay inline.

#### One-Shot Wait

A conductor process ends when its turn ends. After dispatch, poll in the same turn:

```bash
sh <agent-home>/utilities/dispatch-wait.sh --parent <conductor-slug>
# exit 0 = done and harvest
# exit 2 = still alive; call again
# exit 3 = suspect or dead; diagnose and redispatch
```

After judging a stage's artifact contract complete, publish its captured exact-attempt completion before
dispatching the next stage. The completion transaction writes the immutable marker/link and
closes only that attempt row; never mark a routed row `done` first:

```bash
python3 <agent-home>/utilities/capability-route.py complete \
  --route <route-file> --node <node-id> --evidence <stage terminal artifact> \
  --jobs <canonical-jobs.log> --attempt-id <exact-attempt-id>
```

The marker lands at `<agent-home>/.dispatch/completion/<route_id>/<node_id>.json`. Evidence is
the stage's contractual terminal artifact (`plan/plan.md`, the final dev log, the test verdict,
`final_report.md`). The pass judgement stays semantic and belongs to the conductor; the marker
only makes its *result* deterministic. A record-bound `--start` for a node whose `depends_on`
markers are absent fails closed with `completion-marker-missing` and spawns nothing. Marker
absence is *no claim*, never a failure.

#### Closed Inline Fallback

Run standard+ stages in-session only when:

1. intensity is direct or quick;
2. the runtime reports headless dispatch unavailable; or
3. the conductor judges the edit nonseparable because file artifacts cannot carry a boundary-coupled semantic contract.

For case 3, record reasoning in `plans/<slug>/_internal/metrics.md`; an unrecorded inline standard+ run violates the contract. Still parallelize separable census or disjoint file groups. Dispatch-infrastructure self-modification requires the explicit `STAGE_DISPATCH_INLINE_OK` opt-out.

#### Usage-Aware Cross-Harness Routing

Before dispatch, run `sh <agent-home>/utilities/usage-check.sh`. It reports per-harness `ok`, `limited(<reset>)`, or `unknown`; `ok` means no known block, not guaranteed capacity. Avoid limited runtimes, honor explicit `HARNESS_CAPACITY_BIAS`, otherwise balance limit avoidance, task fit, and spread. Prefer a different model family for test or review than for implementation when feasible. Preserve `dispatch_depth`, `parent`, `worker_type`, `assigned_contract`, `model_role`, `harness`, `owner_harness`, and `parent_sid` metadata across runtimes.

If a stage dies immediately from usage, session, or authentication limits, the wrapper closes its row as `done,note=dead-<reason>` and records reset time when known. The wrapper does not retry; the conductor decides redispatch or cross-harness failover.

### Optional Material Delegation

When implementation or reporting requires result plots, experiment-log visualization, or result tables, the code-execute or code-report worker records the need in its artifact. The enumerated autopilot-code recipe compiles no `material/*` node, so the owner satisfies the need per the WORKFLOW compose-on-demand doctrine: a composed route extension node bound to the matching `material/*` unit (e.g. `material/figure-gen`, `material/data-script`) that passes the same validator and hash-seal as a recipe route — or, for narrow throwaway scaffolding only, an ephemeral native helper with no unit semantics. Training and experiment execution remain in autopilot-code; the material units own postprocessing. Record generated asset paths in the relevant dev log.

### Step 1: code-plan

Skip for direct. quick uses an inline micro-plan. For standard+, first verify the SD-13 precondition: the repository has an artifact root and `spec/`. Then dispatch:

```bash
AGENT_HOME=$(utilities/agent-home.sh)
NODE_ID=plan
STAGE_ADAPTER=claude # choose claude, codex, or opencode from checked route evidence
STAGE_SLUG="${CONDUCTOR_SLUG}-plan"
STAGE_PROMPT="<sub-skill contract + absolute input paths + output contract + slug>"
# Run the route-bound dispatch transaction from "Standard+ Stage Dispatch",
# capture ATTEMPT_ID, then use that same value for `capability-route.py complete`.
```

Poll in the same turn:

```bash
sh "$AGENT_HOME/utilities/dispatch-wait.sh" --parent <cycle-slug>
```

Loop until exit 0. Then read only plan status and paths. On exit 3, inspect liveness and transcript tail, then redispatch using existing artifacts. For direct, quick, or unavailable headless runtime, invoke `code-plan` in-session.

### Step 2: plan-check and Optional Refinement

Only durable standard+ graphs use this step. direct has none; quick already completed plan-check-lite.

The compiled standard+ route contains the `plan-check` review node unconditionally (default unit `qa/plan-review`, completion gate `code-plan-check`); `execute` is record-bound to its completion marker and cannot start without it. Intensity scales the review's depth and reviewer role/family, never whether the node runs.

1. Resolve `en_plan_path`, `ko_plan_path`, and `log_dir`.
2. Run the route-bound dispatch transaction with `NODE_ID=plan-check`: the node reads `plan.md` and `checklist.md` and writes `_internal/plan_reviews/round_1.md`. Poll, then publish exact completion from the review memo.
3. Read only the memo verdict. If it reports blocking findings, pause when `--user-refine` is set; otherwise run one `code-refine` within the correction budget.
4. On a clean memo (or after the bounded refinement), continue to Step 3.

### Step 3: code-execute

For standard+, run the route-bound dispatch transaction with `NODE_ID=execute`; its route node
selects `assigned_contract=code-execute` and the portable implementer role. Pass the absolute
`plan/plan.md` path, retain the emitted attempt ID, poll, and publish exact completion. Fallback
to in-session only under the closed rules above.

Read plan frontmatter after harvest:

- `done` → impl-review, then Step 4;
- `partial` → impl-review, then Step 4 for completed work;
- `failed` → source has been rolled back. Write failed `pipeline_summary.md`, report, and stop before test or report.

The compiled route also contains the `impl-review` review node unconditionally (unit
`qa/code-review`, completion gate `code-impl-review`) between `execute` and `test`; `test`
is record-bound to its completion marker. After publishing execute's completion, run the
route-bound dispatch transaction with `NODE_ID=impl-review`: it reads the plan, source
diff, and dev logs, writes `_internal/dev_reviews/phase_review.md`, and stays read-only.
Publish its exact completion, read only the memo verdict, and route blocking findings
through the bounded refine/retry path in Step 4 — never an inline hotfix.

At `strong` and above the compiled route additionally contains `impl-review-replica`
(`replica_group=impl-review`, `independence_axis=cross-harness`, output
`_internal/dev_reviews/phase_review.replica.md`): the 2-way independent replicate-and-merge
that is the default from `strong` (CONVENTIONS §3.12). Dispatch both legs in parallel and
place the replica on a different harness or model family than the primary leg; when only
one harness is live, fall back to a same-harness independent session and record the
reduced independence in the decision record. Merge at verdict level only — the stricter
verdict wins and blocking findings are unioned — and do not proceed past the
`code-impl-review` gate until both legs' verdicts are read and the merge is recorded.

### Step 4: code-test

For standard+, run the route-bound dispatch transaction with `NODE_ID=test`; its route node
selects `assigned_contract=code-test` and the reviewer role. strong+ may select a deeper reviewer.
Pass plan verification and checklist paths, retain the emitted attempt ID, poll, and publish exact
completion from `test_logs/test_report.md`. code-test is read-only and never hotfixes.

quick reports verify-lite failure without retry. Other graphs may open at most one pipeline-level retry:

1. Record the verdict; detailed context remains in `test_logs/test_report.md` and `_internal/test_reviews/` for code-refine.
2. Same-route in-place retry (SD-67): do not restore or roll back source and never run `git reset --hard`. Redispatch code-execute in place on the unchanged route with a new attempt identity (the prior attempt row is the lineage evidence); `worker-route-guard.py` accepts the resulting moved `HEAD` only when the node is declared in the route's `resume_retry_boundaries`, the bound canonical global registry holds a different prior attempt for the same route/node, and `HEAD` is a first-parent descendant of the route's `source_commit`. Never recompile or re-pin the route to manufacture this evidence.
3. Append the preserved compatibility memo literal at affected steps:

   ```html
   <!-- memo: [테스트 실패] code-test 실패. 상세: test_logs/test_report.md, _internal/test_reviews/. 대안 필요. -->
   ```

4. Reset checklist marks to `[ ]`.
5. Pause for explicit user refine, or invoke one bounded code-refine.
6. Redispatch code-execute, then code-test.
7. On pass, continue. On a second failure, roll back, write a failed summary noting both attempts, and stop before code-report.

### Step 5: code-report

For standard+, run the route-bound dispatch transaction with `NODE_ID=report`; its route node
selects `assigned_contract=code-report` and the writer role. Pass plan, checklist, dev logs,
test logs, and review paths, retain the emitted attempt ID, poll, and publish exact completion
from the final report. Use the closed fallback when needed.

### Step 6: Pipeline Summary

Before writing shared singleton files such as `pipeline_summary.md` or `pipeline_state.yaml`, acquire the OPERATIONS §5.8 `.pipeline-lock` and release it immediately after the write. Spec updates also use their owning Skill's lock. `plans/<cycle>/` remains path-separated. On lock exit 3, stop the write and report.

Write the dev-mode summary, then report its path and a two- or three-line verdict.

### Step 7: Refresh `analysis_project/code/`

After reporting, inspect changed files from dev logs or `git diff <safety-commit>..HEAD --name-only`.

| Change | Route |
|---|---|
| At most three files in one module; function, class, signature, rename, one-line, or small logic change; only Interface Reference affected | **A — direct edit:** update the module document's Interface Reference and at most one short Role/body line. |
| Four or more files; module or model-folder add/delete/rename; broad cleanup; config mechanism, preferred layer, train/eval split, seed, or reproducibility change | **B — invoke analyze-project:** run incremental code mode with `--skip-qa`. |

Ambiguity defaults to B.

```bash
/analyze-project --mode code --skip-qa
```

Report how many analysis artifacts changed. Skip Step 7 only on explicit input such as `"분석 자료 update skip"` or `"--no-analyze-update"`. Apply the same logic after debug fixes; they usually take route A.
