# SD-78 registered-headless completion join — independent audit (round 1)

Scope: working tree of `codex-dispatch-completion-join` vs `origin/main`.
New: `utilities/dispatch_completion_join.py`, `utilities/claude-session-supervisor.py`,
`utilities/codex-app-server-supervisor.py`, + matching `*.test.py`.
Modified: both adapters' `dispatch-headless.py`, `pretooluse-write-guard.py` (codex),
hooks/docs, `check-adaptation-boundary.sh`.

Method: read every new/changed file end-to-end, traced env-var/argument flow across
adapter → supervisor → join-CLI → hook boundaries, ran all new/modified unit tests,
ran `tools/check-adaptation-boundary.sh` and `tools/sync-entry-skill-layer.py --check`,
and reproduced one defect live against the real `codex-app-server-supervisor.py`.

## Findings

### 1. [MEDIUM, CONFIRMED] Final agent_message item is emitted twice into the completion log (Codex)
- File: `utilities/codex-app-server-supervisor.py:291` and `utilities/codex-app-server-supervisor.py:413-414`
- `run_turn()` already streams every `item/completed` event live via `emit({"type": "item.completed", "item": item})` (line 291), including the final turn's agent_message. After `run_turn` returns, `main()` unconditionally re-emits the same `final_item` (lines 413-414) right before `turn.completed`.
- Reproduced directly (fake App Server, single turn):
  ```
  {"type":"item.completed","item":{...,"text":"artifact: -\nverdict: PASS\nblocker: none"}}
  {"type":"item.completed","item":{...,"text":"artifact: -\nverdict: PASS\nblocker: none"}}
  {"type":"turn.completed","thread_id":"thread-1"}
  ```
  and confirmed in the 2-turn (park+resume) case: only the *last* turn's item duplicates; the intermediate `runtime_wait: registered-children` turn is emitted once, correctly.
- Impact: does not corrupt the terminal contract — `codex_dispatch_terminal.py` reads only `rows[terminal_index - 1]` (the row immediately before the single `turn.completed`), which is the duplicate copy with identical content, so verdict extraction stays correct (verified: `\tvalid\texact-turn-completed\tPASS\tnone\tnone` still parses). The defect is a redundant duplicate write of the final handoff text into the shared attempt log — log bloat and a signal that the "stream live + re-emit at the end" logic wasn't reconciled after adding live per-item streaming.
- Fix direction: drop the explicit re-emit at 413-414 (the item was already streamed by `run_turn`), or have `run_turn` suppress emission for the item that will become `final_item` and let `main()` own that single emission.
- Not caught by the shipped test (`test_runtime_wait_has_no_model_activity_until_exact_join_is_ready`) because it only asserts the row *immediately before* `turn.completed`, not total occurrence count.

### 2. [MEDIUM, PLAUSIBLE] Claude adapter has no runtime (hook-level) enforcement against a supervised owner blocking on `dispatch-wait` mid-turn
- Files: `adapters/codex/hooks/pretooluse-write-guard.py:234-260,296-303,442-448` (codex, changed) vs. `adapters/claude/hooks/*` (unchanged — no equivalent file exists) and `adapters/claude/bin/dispatch-headless.py:416-513` (prompt-only clause).
- Codex: when `AGENT_DISPATCH_COMPLETION_MODE=supervised`, `park_control_allowed()` now hard-blocks any `dispatch-wait.sh` invocation and the `wait` transport action via `hook_block(...)` (`exact_park_control(..., allow_wait=False)`); confirmed by `utilities/codex-parent-park.test.py::test_supervised_mode_denies_model_wait_and_allows_only_typed_harvest`, which checks both the `Bash dispatch-wait.sh …` call and the `wait` transport action are blocked, and only typed harvest passes.
- Claude: the equivalent SD-78 clause (`adapters/claude/bin/dispatch-headless.py:416-430`) is *prompt text only* — "Do not call dispatch-wait, Monitor, liveness, or scheduling/wakeup tools." The only runtime-enforced restriction is `--disallowedTools` for the fixed `PROVEN_ASYNC_DENY` tuple (`Monitor, ScheduleWakeup, CronCreate, CronDelete, CronList, PushNotification, RemoteTrigger`) — none of which cover `dispatch-wait.sh`, since that script is a *synchronous* Bash call and was in fact the sanctioned SD-71 mechanism until this change. There is no `adapters/claude/hooks/*` file analogous to `pretooluse-write-guard.py`'s park control, and no such hook is referenced anywhere under `adapters/claude/`.
- Impact: on Claude, a model that disregards the new prompt clause can still call `Bash("utilities/dispatch-wait.sh --attempt-id … --max 600")` inside the same supervised turn and silently revert to old-style in-turn blocking. This doesn't corrupt data (the wait still terminates correctly), but it defeats the stated SD-78 goal — "parents must stop model/tool activity after dispatching an exact child batch" — for the Claude adapter specifically, with no runtime backstop the way Codex has one. Worth confirming whether this is an accepted interim gap (Claude Code hook surface may not support the same PreToolUse pattern used by Codex) or an oversight to close with a matching hook.

### 3. [LOW, residual] Cross-turn diagnostic bleed in the (unmodified) terminal reader
- File: `utilities/codex_dispatch_terminal.py:207-220` (pre-existing, not touched by this diff).
- The `sandbox_init`/`diagnostic` scan iterates `rows[:terminal_index]` — i.e., every `item.completed` row in the *entire* log — looking for a failed `command_execution`. Before this diff, one codex dispatch log held at most one turn's worth of commands (`codex exec` was one-shot). Now a supervised owner's log genuinely concatenates multiple turns (parking turn(s) + resumed turn), so a failed command from an earlier, already-resolved turn could be misattributed as the `failure_note`/diagnostic for a later, unrelated `BLOCKED`/`FAIL` verdict.
- Not exercised by any new test (all fixtures use single-command-free turns). Recommend either scoping this scan to rows after the last `dispatch.supervisor.resumed` marker, or adding a regression test with an early-turn failing command and a later, unrelated clean `BLOCKED` verdict to confirm/refute misattribution before it's hit in production.

### 4. [LOW, note] Unconditional availability probe adds latency to every owner-eligible dispatch call
- `resolve_completion_delivery()` (both adapters) runs `claude --help` / `codex app-server --help` as a real subprocess (up to a 10s timeout) whenever `_completion_owner(args)` is true and `--completion-delivery` is left at its `auto` default — for *any* action (`register`, `start`, or `dry-run`), not just an actual launch. `utilities/dispatch_parent_context_conformance.test.py` was updated to pass `--completion-delivery poll` explicitly (line 135) to sidestep this, which confirms the behavior is understood, but it's worth confirming the added latency is acceptable across the full standard+ owner lifecycle (repeated register/dry-run-adjacent calls), not just the one `--start` launch.

## Verified correct (no defect found)

- **Parallel/sequential batch join correctness** — `dispatch_completion_join.join_batch` waits for the full `expected_attempts` set, ignores foreign `parent_attempt_id` rows and legacy/non-schema-v2 rows (fails closed instead), and returns one bounded `ready`/`timeout`/`no-children` receipt. Confirmed by `utilities/dispatch_completion_join.test.py` (5/5 pass) including an explicit parallel-close-in-order case and a foreign-row-ignored case.
- **Terminal handoff uniqueness / no false terminal** — both supervisors refuse to treat a turn as terminal while `new_attempts` (a just-registered batch) or `unresolved` (previously-delivered but still open/running) attempts exist, *regardless* of what the model's turn text says; a premature "artifact/verdict/blocker" during an open batch is structurally ignored rather than short-circuited into a false PASS/FAIL. Only one `turn.completed`/final `result` row is ever produced per attempt (aside from finding #1's cosmetic duplicate).
- **No raw child/parent context leak** — `dispatch_completion_join.py` reduces every row to `{attempt_id, slug, status, readiness, reason}` before it ever leaves the join process; both supervisors' `typed_receipt`/`_typed_receipt` validators re-derive a closed shape from a strict allow-list and reject anything else. Sentinel-tagged tests (`RAW_CHILD_SENTINEL`, `RAW_PARENT_CONTEXT_SENTINEL`, `RAW_TIMEOUT_SENTINEL`, `RAW_CLAUDE_SENTINEL`) all assert absence from supervisor stdout, and pass.
- **Foreign/stale attempt isolation** — `current_children()` filters strictly on `parent_attempt_id` plus `attempt_schema_version=2` plus a present `attempt_id`, and attempt IDs are freshly minted per attempt (`new_attempt_id`) at register/start time, so a stale or foreign attempt cannot structurally reuse a live `parent_attempt_id` to wake an unrelated parent.
- **Killed-supervisor stranding** — the owner's own registry row is covered by the pre-existing `dispatch-orphan-watch.py` + `dispatch-registry.py:cascade_orphan_children`, which terminate via `killpg` (process-group, not single-pid). Traced the process tree the new supervisors introduce (`model-worker-governor.py run` → `sh -c` → `codex-app-server-supervisor.py`/`claude-session-supervisor.py` → nested `codex app-server`/`claude` child): none of the added `subprocess.Popen`/`subprocess.run` calls pass `start_new_session=True`, so the nested App Server/Claude child inherits the same process group as the top-level watched PID, and a group-kill should reap it too. **Not verified with a live SIGKILL drill** — recommend one as follow-up, since this reasoning depends on shell/exec behavior (`sh -c` tail-exec) that wasn't directly observed under signal delivery.
- **Quick / depth-2 one-shot preservation** — `_completion_owner()` in both adapters requires `dispatch_depth == 1 and worker_type == "owner" and intensity in standard+`; quick intensity and any depth-2 call fall through unchanged to `"one-shot"` delivery (or raise a clear `completion-delivery-ineligible` contract error if `--completion-delivery supervised` is forced against an ineligible call).
- **Poll-fallback disclosure** — never silent: `completion_delivery=<value>` is printed on wrapper stdout and recorded in the registry row metadata (`completion_delivery=poll-fallback|app-server-supervised|session-resume-supervised|one-shot`) for both adapters, so a silent downgrade to polling is externally observable.
- **Generated projection parity** — `adapters/claude/skills/...` and the plugin-marketplace projection are byte-identical (`diff` clean); `tools/sync-entry-skill-layer.py --check` exits 0; `tools/check-adaptation-boundary.sh` passes, with the 3 new `utilities/*.py` files explicitly added to the codex/opencode `UTILITY_DEFERRED` census and the 3 new `*.test.py` files correctly auto-classified by the existing derived-deferred `case` rule (no forgotten-census risk).

## Test evidence

All read-only test runs pass:
```
utilities/dispatch_completion_join.test.py ............ 5/5 OK
utilities/claude_session_supervisor.test.py ......... 3/3 OK
utilities/codex_app_server_supervisor.test.py ....... 3/3 OK
utilities/codex-parent-park.test.py ................. 5/5 OK
utilities/dispatch_parent_context_conformance.test.py 3/3 OK
tools/check-adaptation-boundary.sh ................... OK (127 pre-existing WARNs, unrelated)
tools/sync-entry-skill-layer.py --check .............. exit 0
```

## Summary

No blocking or high-severity defect found. Two medium findings are real but non-corrupting:
a confirmed duplicate log write in the Codex App Server supervisor (#1), and an enforcement
asymmetry where the Claude adapter's "stop after dispatch" rule is prompt-only with no hook
backstop, unlike Codex (#2). One low residual risk in an unmodified downstream reader (#3) and
one low efficiency note (#4) round out the list. Recommend fixing #1 (trivial), deciding
whether #2 is an accepted interim gap or needs a Claude-side hook, and adding a regression
test for #3 before it surfaces in production.
