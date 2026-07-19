# Implementation Plan — conductor reliability · Codex mutation · registry hygiene

- Route: `rt-1d200b72bcfb544c` node `plan` · capability `autopilot-code` (debug/strong)
- Worktree: `/home/Uihyeop/agent_setting-wt/conductor-reliability` (branch `conductor-reliability`, source `b9364824`)
- Canonical artifacts: `/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-19_conductor-reliability/`
- Governing spec (do NOT edit): `spec/stage-dispatch/prd.md` §13.7.6 (SD-64), §13.10 (SD-69/70/71), §14 (rule↔meaning boundary v18)
- Ownership guards: do NOT edit `spec/**`, `utilities/dispatch-route.sh` or its tests (owned by the concurrent `selector-paths` cycle). Source edits only in the task worktree; never `git reset --hard`; preserve unrelated dirty/untracked state.

## 0. Honest runtime facts already known (depth-0 checked; re-verify only as a probe)

- **Claude Code 2.1.215** exposes `--disallowedTools`. The exact fatal async wait/scheduling tool names must be confirmed by a live `-p` probe before any name is denied. Never blanket-deny `Bash` or the synchronous `dispatch-wait.sh` path.
- **Codex 0.144.6** keeps `.git` and the resolved gitdir protected inside a `workspace-write` writable root. Therefore `--add-dir <git-common-dir>` is **NOT** an accepted commit fix and `danger-full-access` is not adopted as a standard stage contract. The Codex linked-worktree mutation stage is a `no-commit` worker.
- `.spec-grounding` lives at the **primary checkout** (`/home/Uihyeop/agent_setting/.spec-grounding`, written by `hooks/spec-read-marker.sh` / `adapters/codex/hooks/posttooluse-read-marker.py` at `$AGENT_HOME/.spec-grounding/<marker>`). It does not exist in the linked worktree, and the Codex sandbox writable roots do not currently include it.
- **Self-hosting boundary:** the running conductor resolves tools through the **installed** `AGENT_HOME=/home/Uihyeop/agent_setting` (per `dispatch_contract.resolve_agent_home`), not the worktree. Editing `utilities/capability-route.py` / `utilities/dispatch-registry.py` in the worktree therefore does NOT change the tools the live pipeline uses this cycle. If the conductor ever needs the new interface mid-cycle, it must invoke the worktree copy explicitly and record the bootstrap boundary. Plan/execute/test all operate on the worktree copies; the independent test worker verifies the committed worktree, not execute logs.
- **Test mirror:** `adapters/claude/utilities/*.test.py` are symlinks to `utilities/*.test.py`; edit the canonical `utilities/` copy once. `adapters/claude/bin/dispatch-headless.py` and `adapters/codex/bin/dispatch-headless.py` are real sibling files — change only the surface whose runtime semantics differ, and keep parity disclosures honest.

## 1. Commit grouping (core-first, then implementation)

Order is intentional: **C1 core contract first and committed before any adapter/runtime edit** (AGENTS.md / `core/CORE.md` core-first). Then the four outcomes, ordered so the deterministic registry/marker primitives (SD-70) land before the surfaces that consume them (SD-64/71), and the Codex boundary (SD-69) and Claude hardening (SD-71 launch policy) follow. Each outcome is a self-contained commit with its own focused tests.

| Commit | Scope | Outcome |
|---|---|---|
| **C1** | `core/OPERATIONS.md` (§5.10) portable contract for all four semantics | core-first |
| **C2** | `utilities/capability-route.py` `complete` + `utilities/dispatch-registry.py` marker-backed reconcile | SD-70 (Outcome 4) |
| **C3** | `utilities/dispatch-registry.py` classify + `utilities/dispatch-liveness.sh` + `adapters/codex/bin/dispatch-liveness.py` + `adapters/codex/bin/preflight.sh` status + `tools/fleet/*` | SD-64/71 orphan (Outcome 2) |
| **C4** | `adapters/codex/bin/dispatch-headless.py` + `utilities/dispatch-node.py` (+ `worker-route-guard.py` no-commit note) + fixture | SD-69 (Outcome 3) |
| **C5** | probe evidence + `adapters/claude/bin/dispatch-headless.py` `--disallowedTools` + Stop-hook fixture + wrapper tests | SD-71 conductor hardening (Outcome 1) |

`__pycache__` created by any test run is deleted before each commit. `git diff --check` clean before each commit.

---

## C1 — Core contract (portable, committed first)

**File:** `core/OPERATIONS.md` §5.10 only. Do not touch `spec/**`.

Extend §5.10 with four portable statements (adapters realize them afterward):

1. **Standard conductor prompt clause (SD-71 보조층).** At the top of every `standard+` conductor prompt: "No asynchronous Monitor/wakeup/scheduling waits; poll synchronously with `utilities/dispatch-wait.sh` in the current turn until terminal, then harvest." Amend the existing **One-shot wait contract under SD-14** bullet (line ~138) to state this standard top-of-prompt clause is an auxiliary layer, not a substitute for runtime tool policy or post-exit reconcile.
2. **Post-exit orphan reconcile (SD-64/71).** State the deterministic classification: exact conductor attempt death (`pid`+`pid_start` mismatch/gone) ∧ at least one completion node without a marker ∧ (an open/live child OR an un-started successor node) closes the conductor row `note=dead-parent-orphaned` and surfaces the route + resume boundary on liveness / preflight status / Fleet. No automatic replacement or restart — resume is a depth-0 semantic decision. Live conductors, live children, and fully-marked routes are zero-false-positive.
3. **Codex linked-worktree mutation = no-commit worker (SD-69).** A linked-worktree Codex mutation stage produces source diff, tests, and evidence but does not `git commit`; the route `source_commit` holds until stage end; a trusted depth-0/Claude boundary commits after PASS and confirms diff attribution. Claiming a commit happened when it did not is prohibited. The worker gets the narrow primary `$AGENT_HOME/.spec-grounding` writable root and the canonical artifact root only — never all of agent home or `.git`.
4. **Completion marker ↔ exact attempt row (SD-70).** `complete` takes the canonical jobs path and the current exact attempt id, writes the marker atomically, then closes only that one attempt row `done note=completed-marker` with marker evidence; it never breadth-closes prior BLOCKED rows or a live retry. Marker and row-close are idempotent; a row-close failure preserves the marker and returns structured nonzero; reconcile repairs only the exact marker-backed stale row.

Commit C1 alone before touching adapters.

---

## C2 — SD-70: completion marker ↔ exact attempt row (Outcome 4)

### C2.1 `utilities/capability-route.py`
- **`main()` `complete` subparser** (line ~310): add `--jobs` (canonical registry path) and `--attempt-id` (exact current attempt) options. Keep them optional-but-paired: supplying one without the other is a structured error (nonzero, stable reason), so legacy plan-stage callers that pass neither keep the current marker-only behavior for one transition (the packet's "old `complete` interface still in force" for the plan row).
- **New function `complete_node(route, node, node_id, evidence, jobs=None, attempt_id=None)`** wrapping today's inline `complete` body:
  1. `marker = write_completion_marker(route, node, node_id, evidence)` (unchanged; already atomic + idempotent via `write_once`/`atomic_write`).
  2. If `jobs`/`attempt_id` given: import `close_attempt_row` from `dispatch_contract`; call it with `note="completed-marker"` and `evidence={"completion_marker": str(marker_path), "route_node": node_id, "route_id": route["route_id"]}`. `close_attempt_row` already targets exactly one `attempt_id`, is idempotent (returns `False` if no open/running row matches — treat an already-`done` matching row as success), and never breadth-closes.
  3. If the marker was written but the row-close fails (registry missing/unwritable → `DispatchContractError`, or attempt not found), **preserve the marker** and exit with a structured nonzero + reason (`row-close-failed:<reason>` / `attempt-row-absent`). Do not delete or rewrite the marker.
- **Idempotency:** a second `complete` with the same evidence returns the existing marker (already handled by sha match in `write_completion_marker`) and a no-op/idempotent row close.

### C2.2 `utilities/dispatch-registry.py` reconcile
- Add a **marker-backed exact-stale repair** path: when an open row's exact attempt is dead/gone AND a completion marker for `(route_id, node)` exists whose `evidence` names this exact attempt (via the new `completion_marker`/attempt linkage, or the marker's own attempt evidence), close ONLY that row `note=completed-marker` through the existing `close_attempt_row_if` revalidation-under-lock primitive. This is the reconcile side of SD-70 acceptance ③ (marker written, jobs unwritable at complete-time → later reconcile repairs the exact row). Do not extend `terminal_marker` breadth logic to other rows.
- Reuse `close_attempt_row_if` (already present) with a predicate that re-confirms the attempt id and marker linkage inside the lock.

### C2.3 Tests — `utilities/dispatch_completion_marker.test.py` + `utilities/capability_route.test.py`
- 3-row fixture (prior BLOCKED / current PASS / later live retry of the same node): `complete --attempt-id <current>` closes ONLY the current row; BLOCKED and live-retry rows untouched.
- duplicate `complete` (same evidence, same attempt) → success, still exactly one closed row.
- attempt mismatch / missing attempt → structured nonzero, marker preserved (or written), no row closed.
- unwritable/missing `--jobs` after marker write → marker preserved, structured nonzero; subsequent `dispatch-registry.py reconcile --apply` closes exactly the stale marker-backed row.
- Never-breadth-close assertion.

---

## C3 — SD-64/71: orphan conductor reconcile + visibility (Outcome 2)

### C3.1 `utilities/dispatch-registry.py`
- **New helper `route_incomplete(row, home)`**: given a conductor row's `route_id` (+ `route_file` in meta when present), return the set of route nodes lacking a completion marker under `home/.dispatch/completion/<route_id>/<node>.json`. Read node ids from the route record (`route_file`) if readable; otherwise fall back to markers-present enumeration and report `route-record-unreadable` (fail-closed → no orphan claim).
- **New helper `has_orphaned_dependents(row, rows, incomplete_nodes, args)`**: True iff some other row with `meta.parent == row.slug` is still open/live (classified `working`/`unknown` via `classify_attempt_evidence`), OR an incomplete node has no attempt row at all while its `depends_on` predecessors are all marked (un-started successor).
- **`classify(row, args, newest_orders)`** (line ~152): after computing `exact` and BEFORE returning the generic `exact-dead`/`dead-exact-pid`, add a conductor branch — when the row is a conductor/owner (`meta.get("worker_type") == "owner"` and `meta.get("route_id")` present and no `route_node`) AND `exact["state"] == "dead"` AND `route_incomplete(...)` non-empty AND `has_orphaned_dependents(...)`, return `("orphan", "dead-parent-orphaned", "dead-parent-orphaned")`. This overrides only the note for that specific shape; every other dead row keeps `dead-exact-pid`, and live/`working` conductors keep `active`.
- Pass `rows` into `classify` (currently it only gets `newest_orders`); thread it through `reconcile()` which already has the full `rows` list. Keep the `close_attempt_row_if` revalidation-under-lock unchanged (the fresh re-classify inside `still_safe` re-confirms `dead-parent-orphaned`).
- **Zero-false-positive guards:** require exact `dead` (never `unknown`), require an actually-unreadable-safe route record (fail closed), require a genuine open/live child or a real un-started successor. A completed route (all markers present) → `route_incomplete` empty → generic path.

### C3.2 Surfaces (three, per SD-71 acceptance ②)
- **`utilities/dispatch-liveness.sh`** + **`adapters/codex/bin/dispatch-liveness.py`**: when the exact-dead row is a conductor classified `dead-parent-orphaned`, emit a distinct `⚠️ ORPHANED <slug> — pipeline orphaned; resume boundary = <first incomplete node>; depth-0 decision` line instead of the generic `EXITED`. Read the classification via the existing `dispatch-registry.py attempt-state` / reconcile dry-run rather than re-deriving. Keep exit-3 semantics.
- **`adapters/codex/bin/preflight.sh` `status`** (line ~352, `headless_open_jobs=`): add an `orphaned_conductor_jobs=<n>` (and, when >0, `orphaned_resume_boundary=<node>`) field computed from a `dispatch-registry.py reconcile --route ... ` dry-run (no `--apply`) over the current registry. Fail-open to `0` when the registry is absent.
- **Fleet current-attempt view** — `tools/fleet/model.py` (or `tools/fleet/route.py`/`render.py` consumer): surface `note=dead-parent-orphaned` on the DispatchJob row so the current-attempt view shows the orphan + resume boundary. The `note` already flows through the jobs.log row after close; ensure the render/route layer maps it to an explicit alert cell (never blank). Add/extend the matching Fleet test (`tools/fleet/tests/test_f26_registry.py` or `test_f28_route.py`).

### C3.3 Tests — `utilities/dispatch_registry.test.py` (+ fleet test)
- Orphan fixture: dead conductor (`worker_type=owner`, incomplete markers) + one open child → `reconcile` proposes/close `dead-parent-orphaned`, all three surfaces show it, no auto-relaunch.
- Live conductor (`working`) + completed route + live child → zero orphan classification (false-positive guard).
- Un-started successor variant (no open child, but a not-yet-launched node with all predecessors marked) → orphaned.
- Reconcile does not close a live child.

---

## C4 — SD-69: Codex linked-worktree mutation boundary (Outcome 3)

### C4.1 `adapters/codex/bin/dispatch-headless.py`
- **`shell_command(args, ...)`** (line ~411, the `--add-dir` block at 417–428): for a **route-bound worker** (`args.route_id` present) add the primary `.spec-grounding` as a narrow writable root — `cmd += ["--add-dir", str(args.agent_home / ".spec-grounding")]`. Use `args.agent_home` (already `resolve_agent_home()`-derived = primary checkout), NOT the worktree. Do NOT add the git-common-dir; do NOT widen to all of agent home.
- **Safe pre-creation:** before launch (near where `.dispatch` is ensured), `(_agent_home / ".spec-grounding").mkdir(mode=0o700, parents=True, exist_ok=True)` guarded so a pre-existing dir/permission is untouched. Never create or expose `.git`.
- **No-commit encoding:** for a linked-worktree Codex mutation stage (`worker_type in {"owner","stage"}` with a worktree-mutating `write_scope` and a linked worktree), stamp `no_commit=1` into the jobs.log pipe in `append_job` (line ~504 area) and inject a one-line no-commit clause into the worker bootstrap/prompt: "You are a no-commit worker: produce source diff + tests + evidence; do NOT `git commit`; a trusted boundary commits after PASS." Keep `source_commit` pinning intact (worker-route-guard unchanged for first-attempt exact match; retries still use the SD-67 first-parent lineage already implemented).

### C4.2 `utilities/dispatch-node.py`
- When materializing a Codex mutation stage node in a linked worktree, forward the `no_commit` marker (a `--no-commit` passthrough flag or metadata) so the registry row and dispatch metadata carry it (SD-69 "encode … where the current machinery needs it"). Keep dispatch-route.sh untouched.

### C4.3 `utilities/worker-route-guard.py` (only if needed)
- The guard already permits `HEAD == source_commit` for first attempts and the SD-67 first-parent lineage for mutation-node retries. A no-commit Codex stage leaves `HEAD == source_commit`, which already passes. **No functional change expected** — only add a `no_commit` awareness comment/note if the guard reads the pipe. Confirm via the existing `utilities/worker_route_guard.test.py` (regression, no new failure).

### C4.4 Disposable linked-worktree fixture
- New test (e.g. `utilities/dispatch_codex_nocommit_fixture.test.py` or extend `adapters/codex/bin/dispatch-headless.sd45.test.py`): create a throwaway git repo + linked worktree + a primary `.spec-grounding`, run the codex wrapper argv builder (`shell_command`) and assert:
  1. writable roots include the primary `.spec-grounding` and the artifact root, and do NOT include the git-common-dir / `.git`.
  2. a simulated source edit persists in the worktree and a `.spec-grounding/<marker>` write lands in the **primary** checkout (outside the sandbox worktree).
  3. commit stays honestly unavailable (`no_commit=1` recorded; no commit claimed); `route_hash`/`source_commit` unforged.
- Delete the throwaway repo + `__pycache__` after the test.

---

## C5 — SD-71: Claude one-shot conductor hardening (Outcome 1)

### C5.1 Runtime probes (evidence captured to `_internal/`, referenced by report)
- **Tool-policy probe:** run a disposable `claude -p` in the current runtime that enumerates its available tool names (e.g. a prompt asking the model to list its tools, or `claude --help`/debug output), capture stdout to `_internal/probe_claude_tools.txt`. Only names that the probe proves to exist as asynchronous wait/scheduling tools (candidates: `Monitor`, `ScheduleWakeup`, cron/`PushNotification`/`RemoteTrigger`-class) may be denied. If a name cannot be confirmed, record `unsupported-evidence` and do NOT claim deterministic support.
- **Stop-hook fixture:** re-run a disposable Claude 2.1.215 `-p` Stop-hook fixture; capture whether the hook (a) fires, (b) can block, (c) preserves stdout. Store the transcript under `_internal/probe_stop_hook.txt`. Register a conductor Stop gate ONLY if all three hold; otherwise keep the documented held fallback (do not enable the gate).

### C5.2 `adapters/claude/bin/dispatch-headless.py`
- **`shell_command(args, ...)`** (line ~334, `cmd = ["claude", "-p", "--add-dir", args.artifact_root]`): after the model flags, append `--disallowedTools <names>` built ONLY from probe-proven async tool names, and ONLY for a `standard+` conductor/owner launch (`args.worker_type == "owner"` and intensity in the standard+ set). Never include `Bash`. Gate the list behind a constant (e.g. `PROVEN_ASYNC_DENY = (...)`) populated from C5.1 evidence; if empty, emit nothing and record `unsupported`.
- Keep synchronous `dispatch-wait.sh` (Bash) fully available.

### C5.3 Prompt contract (adapter projection of C1)
- Ensure the Claude/Codex conductor prompt renderers (worker bootstrap / `render_worker_bootstrap`) carry the standard top-of-prompt clause from C1 for owner workers. This is the auxiliary layer only.

### C5.4 Tests — `adapters/claude/bin/dispatch-headless.sd45.test.py` (or a new wrapper test)
- Deterministic deny/fallback: with a stubbed proven-names list, `shell_command` for an owner includes exactly those `--disallowedTools` names and never `Bash`; for a stage worker it includes none.
- Empty proven-names → no `--disallowedTools` emitted, `unsupported` recorded.
- Regression: existing sd45 argv assertions still pass.

---

## 2. Cross-cutting constraints & sequencing notes
- **Core-first commit** (C1) precedes every adapter/runtime commit; run the core-first guard before adapter edits.
- **Parity honesty:** Claude and Codex wrappers are siblings — only the Claude wrapper gets `--disallowedTools` (Codex fatal-async policy differs and is out of this cycle's proven scope); only the Codex wrapper gets the `.spec-grounding` writable-root + no-commit encoding (Claude execute commits normally). Disclose this asymmetry in the wrapper comments and final report; do not mirror a change into an adapter whose semantics do not differ.
- **No auto-resume / no live-child close** anywhere in C3.
- **Self-hosting:** the live conductor uses installed tools; worktree edits do not hot-swap the running pipeline. Record the bootstrap boundary in `dev_logs` if any stage must invoke a worktree tool explicitly.
- **Do not touch** `spec/**`, `utilities/dispatch-route.sh`, or `utilities/dispatch-route.sh` tests.

## 3. Verification floor
See `checklist.md` — each suite mapped to its commit.
