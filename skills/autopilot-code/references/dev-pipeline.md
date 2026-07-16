## Pipeline: Mode dev

Select the stage graph from `--intensity` before QA. `direct` performs produce plus sanity/report without this durable pipeline. `quick` uses one depth-1 worker with an inline micro-plan, plan-check-lite, and focused verification. standard+ follows the durable pipeline below.

Use independent plan review only when selected by the graph: UI or visual risk → native `디자인팀`; research or domain risk → native `연구팀`; construction quality → native `품질관리팀`.

### Standard+ Stage Dispatch

The depth-1 owner is a thin conductor. Dispatch each durable stage as a depth-2 headless session with `adapters/claude/bin/dispatch-headless.py --depth 2 --parent <conductor-slug> --worker-role code-<stage> --owner autopilot-code --model-role <portable-stage-role>`. Codex and OpenCode use their adapter-native dispatch wrappers.

The prompt carries only subskill name, absolute input paths, output contract, intensity, and slug. It never carries plan bodies or prior-stage conversation. Each stage reads files; the conductor reads only verdict and gate state. Register every stage in `.dispatch/jobs.log`, monitor liveness, and keep conductor plus active stages at or below five processes. One-line or no-artifact micro-stages stay inline.

#### One-Shot Wait

A conductor process ends when its turn ends. After dispatch, poll in the same turn:

```bash
sh <agent-home>/utilities/dispatch-wait.sh --parent <conductor-slug>
# exit 0 = done and harvest
# exit 2 = still alive; call again
# exit 3 = suspect or dead; diagnose and redispatch
```

After harvest, change the stage row from `open` to `done` before dispatching the next stage. An open harvested row orphans the pipe and keeps Fleet and dispatch-wait active.

After judging a stage's artifact contract complete, write its completion marker before
dispatching the next stage:

```bash
python3 <agent-home>/utilities/capability-route.py complete \
  --route <route-file> --node <node-id> --evidence <stage terminal artifact>
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

Before dispatch, run `sh <agent-home>/utilities/usage-check.sh`. It reports per-harness `ok`, `limited(<reset>)`, or `unknown`; `ok` means no known block, not guaranteed capacity. Avoid limited runtimes, honor explicit `HARNESS_CAPACITY_BIAS`, otherwise balance limit avoidance, task fit, and spread. Prefer a different model family for test or review than for implementation when feasible. Preserve `depth`, `parent`, `worker_role`, `harness`, `owner_harness`, and `parent_sid` metadata across runtimes.

If a stage dies immediately from usage, session, or authentication limits, the wrapper closes its row as `done,note=dead-<reason>` and records reset time when known. The wrapper does not retry; the conductor decides redispatch or cross-harness failover.

### Optional Material Delegation

When implementation or reporting requires result plots, experiment-log visualization, or result tables, invoke native `자료팀` inside code-execute or code-report. Training and experiment execution remain in autopilot-code; material-team owns postprocessing. Record generated asset paths in the relevant dev log.

### Step 1: code-plan

Skip for direct. quick uses an inline micro-plan. For standard+, first verify the SD-13 precondition: the repository has an artifact root and `spec/`, or is explicitly untracked. Then dispatch:

```bash
AGENT_HOME=$(utilities/agent-home.sh)
REPORTS_DIR=.agent_reports; [ -d .claude_reports ] && [ ! -d .agent_reports ] && REPORTS_DIR=.claude_reports
python3 "$AGENT_HOME/adapters/claude/bin/dispatch-headless.py" --start \
  --worktree "$PWD" --slug <cycle-slug> \
  --capability code-plan --mode dev --intensity <intensity> \
  --depth 2 --parent <cycle-slug> --worker-role code-plan --owner autopilot-code \
  --model-role "deep maker" --profile code-plan \
  --prompt-text "<sub-skill contract + absolute input paths + output contract + slug>"
```

Poll in the same turn:

```bash
sh "$AGENT_HOME/utilities/dispatch-wait.sh" --parent <cycle-slug>
```

Loop until exit 0. Then read only plan status and paths. On exit 3, inspect liveness and transcript tail, then redispatch using existing artifacts. For direct, quick, or unavailable headless runtime, invoke `code-plan` in-session.

### Step 2: Plan Check and Optional Refinement

Only durable standard+ graphs use this step. direct has none; quick already completed plan-check-lite.

The self-check is inline because it writes no new durable artifact. An independently warranted review may be a bounded depth-2 review worker.

1. Resolve `en_plan_path`, `ko_plan_path`, and `log_dir`.
2. Select review only when the graph and risk require it:
   - standard: one lightweight review when warranted;
   - strong: one review at the riskiest point;
   - thorough or adversarial: bounded depth-2 or axis-separated reviewers, each returning a short memo.
3. If blocking findings exist, pause when `--user-refine` is set; otherwise run one `code-refine` within the correction budget.
4. Without findings or selected review, continue.

### Step 3: code-execute

For standard+, dispatch a depth-2 session with `--capability code-execute --worker-role code-execute --model-role "fast implementer" --profile code-execute`. Pass the absolute `plan/plan.md` path, poll, and harvest. Fallback to in-session only under the closed rules above.

Read plan frontmatter after harvest:

- `done` → Step 4;
- `partial` → Step 4 for completed work;
- `failed` → source has been rolled back. Write failed `pipeline_summary.md`, report, and stop before test or report.

### Step 4: code-test

For standard+, dispatch with `--capability code-test --worker-role code-test --model-role "fast reviewer" --profile code-test`; strong+ may select a deeper reviewer. Pass plan verification and checklist paths. Poll and read `test_logs/test_report.md` from disk. code-test is read-only and never hotfixes.

quick reports verify-lite failure without retry. Other graphs may open at most one pipeline-level retry:

1. Record the verdict; detailed context remains in `test_logs/test_report.md` and `_internal/test_reviews/` for code-refine.
2. Read `Safety commit: {hash}` from `plan/checklist.md` and restore changed source paths only:

   ```bash
   git checkout <safety-commit> -- <changed paths>
   git status
   ```

3. Append the preserved compatibility memo literal at affected steps:

   ```html
   <!-- memo: [테스트 실패] code-test 실패. 상세: test_logs/test_report.md, _internal/test_reviews/. 대안 필요. -->
   ```

4. Reset checklist marks to `[ ]`.
5. Pause for explicit user refine, or invoke one bounded code-refine.
6. Redispatch code-execute, then code-test.
7. On pass, continue. On a second failure, roll back, write a failed summary noting both attempts, and stop before code-report.

### Step 5: code-report

For standard+, dispatch with `--capability code-report --worker-role code-report --model-role "fast writer" --profile code-report`. Pass plan, checklist, dev logs, test logs, and review paths. Poll and read the report path and headline from disk. Use the closed fallback when needed.

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
