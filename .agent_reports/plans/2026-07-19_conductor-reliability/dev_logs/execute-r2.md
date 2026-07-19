# code-execute r2 — conductor reliability · Codex mutation · registry hygiene

Worktree: `/home/Uihyeop/agent_setting-wt/conductor-reliability` (branch `conductor-reliability`)
Source commit: `b9364824` (post-C1..C5: `e44c77a2`)

## Self-hosting boundary (record per plan.md §0)

The live pipeline resolves tools through the **installed** `AGENT_HOME=/home/Uihyeop/agent_setting`
(`dispatch_contract.resolve_agent_home`), not this worktree. All five commits below edit and test
the **worktree copies only** — they do not hot-swap the running conductor's tools mid-cycle. No
stage in this cycle needed to invoke a worktree tool explicitly against the live registry; the
whole-cycle verification floor below runs entirely against worktree/test-fixture copies.

## Commits (core-first, then C2..C5 in plan order)

### C1 — `9d580b8e` docs(core): conductor reliability contract — SD-64/69/70/71 §5.10
Amended `core/OPERATIONS.md` §5.10 only (no `spec/**`, no `utilities/dispatch-route.sh`) with four
portable statements ahead of any adapter edit: the SD-71 standard top-of-prompt synchronous-wait
clause (amending the existing "One-shot wait contract under SD-14" bullet), the SD-64/71 post-exit
orphan-conductor reconcile classification, the SD-69 Codex linked-worktree mutation = no-commit
worker statement, and the SD-70 completion-marker ↔ exact-attempt-row binding.

Tests: `bash tools/check-adaptation-boundary.sh` (OK, pre-existing WARN unrelated), `git diff --check`
clean, no `spec/**`/`dispatch-route.sh` diff.

### C2 — `de7db348` feat(dispatch): SD-70 exact-attempt completion close + SD-64/71 orphan classify
- `utilities/capability-route.py`: `complete` subparser gains optional-but-paired `--jobs`/
  `--attempt-id`. New `complete_node()` writes the marker first (unchanged `write_completion_marker`),
  then calls `dispatch_contract.close_attempt_row` to idempotently close only that exact row
  `done note=completed-marker`. A row-close failure (unwritable registry, missing attempt) raises
  `ValueError` — caught by the existing top-level handler → structured nonzero (exit 64) with a
  `row-close-failed:*` / `attempt-row-absent:*` reason — the marker is never deleted or rewritten.
  Also writes a small `<node_id>.attempt.json` sibling file next to the completion marker recording
  the attempt linkage *before* attempting the row close, so a later reconcile can repair the exact
  row even if the close failed at complete-time.
- `utilities/dispatch-registry.py`: `classify()` gains a marker-backed exact-stale repair branch
  (`_marker_backed_repair`) that checks the attempt-linkage file before falling through to the
  generic `dead-exact-pid` path. Reuses the existing `close_attempt_row_if` revalidation-under-lock
  primitive in `reconcile()` unchanged.
- Same commit also lands the SD-64/71 orphan classify-layer primitives (`route_incomplete`,
  `has_orphaned_dependents`, the conductor branch in `classify()`) because they share the exact same
  `classify()` insertion point as the C2 marker-backed repair — the SD-64/71 *surfacing* (liveness,
  preflight, Fleet) is its own commit (C3) per plan.

Tests: `dispatch_completion_marker.test.py` (8, new SD-70 fixtures: prior-BLOCKED/current-PASS/
live-retry → only current closed; duplicate complete idempotent; missing attempt → structured
nonzero + marker preserved; unwritable jobs → marker preserved, structured nonzero, then reconcile
repairs exactly that row via the attempt-linkage file), `capability_route.test.py` (11, regression),
`dispatch_contract.test.py` (10, regression), `dispatch_registry.test.py` (13, incl. 5 new orphan
fixtures proving the C3-shared primitives already work correctly here even though C3 wires the
surfaces next).

### C3 — `225eefc6` feat(dispatch): SD-64/71 surface orphaned-conductor classification
- Two new read-only `dispatch-registry.py` operations reusing C2's primitives, never re-deriving:
  `orphan-status --attempt <id>` (single-attempt verdict + resume boundary) and `orphan-scan`
  (registry-wide fail-open count, no filter required — a status probe doesn't know a route ahead of
  time).
- `utilities/dispatch-liveness.sh` and `adapters/codex/bin/dispatch-liveness.py`: a dead conductor
  row now gets `⚠️ ORPHANED <slug> — route=…; resume boundary=…; depth-0 decision` instead of the
  generic DEAD/EXITED line; exit-3 semantics unchanged.
- `utilities/harness-status.sh` (shared by codex/opencode `preflight.sh status`): emits
  `orphaned_conductor_jobs=<n>` and, when >0, `orphaned_resume_boundary=<node>`; fails open to 0 with
  no registry.
- `tools/fleet`: `DispatchJob` gains `note`/`resume_boundary`; `collectors/dispatch.py`'s `collect()`
  in-process-loads `dispatch-registry.py` once (no subprocess per ~2s Fleet tick) and stamps a dead
  depth-1 owner row via the same classifier; `render.py` shows `⚠ ORPHANED resume=<node>` instead of
  the generic `dead @stage` cell — never blank.

No surface auto-resumes/relaunches or closes a live child anywhere — every classify() call in this
cycle is read-only detection; the only writer is the pre-existing `close_attempt_row_if` inside
`reconcile --apply`, unchanged from before this cycle.

Tests: `dispatch_registry.test.py` (13, orphan fixtures from C2 still hold), `dispatch_node.test.py`
(17, regression), manual end-to-end runs of both liveness scripts against a hand-built orphan
fixture (dead owner + open child with unknown proc state → `⚠️ ORPHANED … resume boundary=execute`;
both bash and Python variants verified), `preflight.sh status` verified against both the real
registry (`orphaned_conductor_jobs=0`) and a synthetic fixture (`=1`, resume boundary set),
`tools/fleet/tests/test_f26_registry.py` (41) + `test_f28_route.py` (23, incl. 2 new orphan
annotation fixtures) + `test_f25_state_model.py` (33) + `test_dispatch.py` (73) all green.

### C4 — `ae1165cc` feat(codex): SD-69 linked-worktree mutation boundary — no-commit + spec-grounding root
- `adapters/codex/bin/dispatch-headless.py`: `shell_command()` adds the primary
  `$AGENT_HOME/.spec-grounding` directory as a narrow `--add-dir` writable root for any route-bound
  worker, created safely (`mkdir(mode=0o700, parents=True, exist_ok=True)` — never touches a
  pre-existing dir's permissions, never widens to all of agent home, never touches `.git`).
  `is_no_commit_stage()` detects a linked-worktree Codex mutation stage (`worker_type` owner/stage +
  a worktree-mutating `write_scope` containing `source/**` + `worktree != agent_home`) and stamps
  `no_commit=1` into the jobs.log pipe (`append_job`) plus injects a one-line no-commit clause into
  the worker prompt.
- **Implementation deviation from plan.md's literal C4.2** (recorded honestly, not silently): the
  plan named `utilities/dispatch-node.py` as needing to "forward the `no_commit` marker" via a new
  `--no-commit` passthrough flag. The detection ended up fully self-contained inside
  `dispatch-headless.py`, computed from args it already receives (`route_node`/`write_scope`/
  `worktree`/`agent_home` — all already forwarded by `dispatch-node.py` today). This reaches the
  identical observable outcome (registry row carries `no_commit=1`, prompt carries the clause)
  without adding a new interface surface. `dispatch-node.py` itself needed no edit;
  `dispatch_node.test.py` (17) passes unchanged, confirming no regression.
- `utilities/worker-route-guard.py`: confirmed unchanged is correct — it doesn't read the jobs.log
  pipe at all (route file + git HEAD only), so it has no `no_commit` awareness to add; a no-commit
  stage already passes its existing `HEAD == source_commit` first-attempt gate.
- New disposable fixture `utilities/dispatch_codex_nocommit_fixture.test.py` (2 tests, real
  throwaway repo + real `git worktree add` linked worktree, no mocks): writable roots include the
  primary `.spec-grounding` + artifact root and exclude the git-common-dir/`.git`; a simulated
  source edit persists in the linked worktree while a `.spec-grounding/<marker>` write lands in the
  **primary** checkout (never the sandboxed worktree); `no_commit=1` is recorded with no commit
  claimed and `route_hash`/`source_commit` unforged. Projected to
  `adapters/claude/utilities/` (symlink, matching the existing sibling test's projection) and
  registered in `tools/check-adaptation-boundary.sh`'s deferred-utility manifest (both codex and
  opencode sections) — the boundary guard fails loud on any utility with no projection decision.

Tests: `adapters/codex/bin/dispatch-headless.sd45.test.py` (9, regression), the new fixture (2),
`worker_route_guard.test.py` (13, regression), `dispatch_node.test.py` (17, regression),
`bash tools/check-adaptation-boundary.sh` (OK).

### C5 — `e44c77a2` feat(claude): SD-71 one-shot conductor hardening — proven async-tool deny + sync-wait clause
- **Live probe, `_internal/probe_claude_tools.txt`**: ran a disposable `claude -p` (this exact
  runtime, Claude Code 2.1.215) asking it to enumerate every tool name available to it. Captured
  verbatim; the async wait/scheduling/notification subset is: `Monitor`, `ScheduleWakeup`,
  `CronCreate`, `CronDelete`, `CronList`, `PushNotification`, `RemoteTrigger`.
- **Live probe, `_internal/probe_stop_hook.txt`**: re-ran a disposable Claude 2.1.215 `-p` Stop-hook
  fixture twice (fresh temp `.claude/settings.json` + real `claude -p` invocation each time, no
  mocks). Result, reproduced identically both runs: the hook **fires** reliably (9/9 Stop events per
  run); a `{"decision":"block",...}` response does **not** hard-block — it re-invokes the model in a
  bounded loop that eventually just exits anyway; and — the load-bearing finding — **captured stdout
  was empty** (1 byte) both runs despite the hook's own JSON payload showing a real
  `last_assistant_message`. Since fire+block+stdout do not all hold (stdout fails), the Stop gate
  stays **unregistered**; the existing core/OPERATIONS.md §5.10 documented held-fallback text (added
  before this cycle) is confirmed correct and left as-is — no dead/stale claim was corrected because
  none existed.
- `adapters/claude/bin/dispatch-headless.py`: `shell_command()` now appends `--disallowedTools`
  built only from the probe-proven `PROVEN_ASYNC_DENY` tuple above, gated to a standard+ owner
  (conductor) launch only (`worker_type == "owner"` and `intensity` in
  `{standard,strong,thorough,adversarial}`) — never `Bash`, never a stage/review/support worker,
  never direct/quick. Synchronous `dispatch-wait.sh` (via `Bash`) stays fully available.
- Both Claude and Codex `dispatch_prompt()` now open a standard+ owner prompt with the SD-71
  top-of-prompt clause from the C1 core-contract text (harness-neutral prose); a stage worker or a
  direct/quick owner never gets it. Codex gets no `--disallowedTools` equivalent — parity honesty:
  its fatal-async policy differs and is out of this cycle's proven scope; only the Codex wrapper
  gets the `.spec-grounding`/no-commit changes from C4 for the same reason (Claude's execute stage
  commits normally from its own worktree and has no equivalent boundary gap). This asymmetry is
  disclosed in both wrapper comments and here.

Tests: `adapters/claude/bin/dispatch-headless.sd45.test.py` (15, incl. 6 new SD-71 deny/clause
cases), `adapters/codex/bin/dispatch-headless.sd45.test.py` (12, incl. 3 new SD-71 clause cases,
sync-wait clause only — no deny-list test since Codex gets none by design).

## Whole-cycle verification floor (run at the end, against the committed worktree)

All commands run with `env -u AGENT_DISPATCH_JOBS` to avoid this session's own exported registry
path (used for SD-58 progress heartbeats) leaking into the fixtures' own `--jobs`/canonical-registry
checks — an environment artifact of *this conversation*, not a code defect (the sd45 "noncanonical-
nested-jobs" check that surfaced it is itself an existing, working guard).

| Suite | Result |
|---|---|
| `utilities/dispatch_contract.test.py` | 10 OK |
| `utilities/dispatch_registry.test.py` | 13 OK |
| `utilities/dispatch_node.test.py` | 17 OK |
| `utilities/capability_route.test.py` | 11 OK |
| `utilities/dispatch_completion_marker.test.py` | 8 OK |
| `utilities/worker_route_guard.test.py` | 13 OK |
| `utilities/stage_dispatch_fallback.test.py` | 8 OK |
| `utilities/nested_dispatch_eligibility.test.py` | 4 OK |
| `utilities/dispatch_codex_nocommit_fixture.test.py` (new) | 2 OK |
| `adapters/codex/bin/dispatch-headless.sd45.test.py` | 12 OK |
| `adapters/claude/bin/dispatch-headless.sd45.test.py` | 15 OK |
| `tools/fleet/tests/test_f25_state_model.py` | 33 OK |
| `tools/fleet/tests/test_f26_registry.py` | 41 OK |
| `tools/fleet/tests/test_f28_route.py` | 23 OK |
| `tools/fleet/tests/test_dispatch.py` | 73 OK |
| `bash tools/check-adaptation-boundary.sh` | OK (pre-existing WARN: 103 concrete Claude/model refs, unrelated to this cycle) |
| `bash hooks/portable-guards.test.sh` | running long in background; result appended once complete |
| `git diff --check` (repo-wide) | clean |
| `git diff b9364824..HEAD --stat -- spec/` | empty (no spec touch) |
| `git diff b9364824..HEAD --stat -- utilities/dispatch-route.sh` | empty (selector-paths ownership respected) |
| `__pycache__` staged anywhere | none (cleaned before every commit) |
| unrelated dirty/untracked worktree state | none — `git status` clean at commit e44c77a2 |

## Parity honesty (explicit, per plan §2)

Claude-only: `--disallowedTools` (C5). Codex-only: `.spec-grounding` writable root + `no_commit=1`
encoding (C4). Both wrappers share the harness-neutral C1 core-contract prompt clause and the
C2/C3 registry-layer changes (those are portable `utilities/` code, not adapter-specific). This
asymmetry is intentional and disclosed in both wrapper source comments and this log — it is not an
oversight or an incomplete port.

## Known runtime limitations / honest disclosures

1. **Self-hosting boundary**: as stated above, none of this cycle's edits hot-swap the *running*
   conductor's tool policy or registry semantics mid-cycle — they take effect only for future
   launches that resolve `AGENT_HOME` to the installed copy after this branch merges.
2. **C4.2 plan deviation**: `dispatch-node.py` was not touched (see C4 section above) — the same
   observable contract is met through self-contained detection in `dispatch-headless.py`.
3. **SD-71 Stop-hook gate remains disabled** — this is not new caution added by this cycle, but a
   freshly-reproduced empirical confirmation (two independent live runs) of the pre-existing
   documented decision; C1 did not need to change that sentence.
4. **`PROVEN_ASYNC_DENY` is a snapshot of one live probe run** against Claude Code 2.1.215. If a
   future Claude Code release adds/renames async tools, the deny list will not auto-track that
   without a fresh probe — this is inherent to "probe-proven, never guessed" and was accepted as the
   plan's explicit design (`_internal/probe_claude_tools.txt` is the audit trail for exactly this).

## Verdict

PASS — all five planned commits landed in the stated order with their focused tests green in the
worktree; the whole-cycle floor above is green except `hooks/portable-guards.test.sh`, which was
still running at report time (backgrounded for the ~120s+ default timeout) — see the addendum note
appended once it completes, or the code-test stage's independent re-run.
