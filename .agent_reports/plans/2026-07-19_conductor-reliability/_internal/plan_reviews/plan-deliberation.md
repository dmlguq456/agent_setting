# Plan deliberation (raw) — conductor-reliability

## Grounding read (all confirmed against worktree source)
- `core/CORE.md`, `spec/stage-dispatch/prd.md` §13.7.6 (SD-64/65) + §13.10 (SD-69/70/71) + §14, route.json, conductor-prompt.md.
- `utilities/capability-route.py` (`complete`→`write_completion_marker`, atomic/idempotent already), `utilities/dispatch_contract.py` (`close_attempt_row`/`close_attempt_row_if` — exact single-attempt, idempotent, revalidate-under-lock), `utilities/dispatch-registry.py` (`classify`/`reconcile`/`terminal_marker`), `tools/fleet/model.py` (`classify_attempt_evidence`), both `dispatch-headless.py` wrappers, `dispatch-liveness.sh`, `preflight.sh status`, `worker-route-guard.py` (SD-67 first-parent lineage already merged in b9364824 lineage), `dispatch-node.py`.

## Key structural decisions
1. **SD-70 fits existing primitives.** `write_completion_marker` is already atomic+idempotent; `close_attempt_row(attempt_id, note)` is already exact + never breadth. So `complete` just needs `--jobs`/`--attempt-id` wiring + marker-preserving structured-nonzero on close failure. Reconcile repair reuses `close_attempt_row_if`. Low risk.
2. **Orphan detection is a refinement of the existing exact-dead branch**, not a new scanner. Key on `worker_type=owner` + `route_id` + no `route_node` + exact `dead` + incomplete markers + orphaned dependent. Overrides only the *note*. Fail-closed on unreadable route record → zero false positives. `classify` must receive full `rows` (thread from `reconcile`).
3. **Self-hosting boundary is naturally safe:** `resolve_agent_home()` points the live conductor at the installed primary checkout, not the worktree, so editing the worktree tools does not hot-swap the running pipeline. Test worker verifies committed worktree.
4. **`.spec-grounding` already exists at primary** (`/home/Uihyeop/agent_setting/.spec-grounding`, written by spec-read-marker hooks at `$AGENT_HOME/.spec-grounding`). SD-69 fix = add it as a narrow `--add-dir` writable root in the Codex wrapper's `shell_command`, pre-created safely, using `args.agent_home` (primary) not the worktree. Git-common-dir is NOT added (Codex 0.144.6 protects `.git`/gitdir even under writable root).
5. **Parity honesty:** Claude-only `--disallowedTools` (proven-name deny); Codex-only `.spec-grounding` + no-commit. Not mirrored to adapters whose semantics don't differ. `adapters/claude/utilities/*.test.py` are symlinks to `utilities/` — edit canonical once.

## Rejected / avoided
- `--add-dir <git-common-dir>` to enable Codex commit — contradicts runtime contract (SD-69 기각). No `danger-full-access` standard stage.
- Blanket `--disallowedTools Bash` or denying `dispatch-wait.sh` — forbidden (SD-71 launch policy).
- Auto-resume / auto-relaunch / closing a live child — forbidden (SD-64).
- Breadth-close of route/node rows — forbidden (SD-70).
- Enabling Claude Stop gate without the three-condition probe — kept held (SD-71).

## Open risk flags for execute/test
- Exact `worker_type`/pipe field the *conductor owner* row actually carries in this cycle's registry — confirm the conductor registers a jobs.log row with `worker_type=owner` before relying on that key; if the depth-0-launched conductor lacks a row, orphan detection must key on the route-owner attempt evidence instead. Execute must verify against a real conductor row.
- Fleet current-attempt view: confirm the `note=` field propagates from jobs.log through the DispatchJob collector to render before adding a test.
