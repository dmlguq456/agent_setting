# Registered depth-1 fallback owner — finish original context-parity task

Finish the original approved task in one registered depth-1 Codex session.
The normal depth-2 pipeline is unavailable for this self-hosting change: the
current Codex parent wait/liveness surface leaves a completed `PASS` child open
until a depth-0 caller manually reads the terminal handoff and writes the
completion marker. That is the defect being fixed. Do not dispatch children.
Record this concrete `runtime-unavailable` inline exception in
`/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_codex-headless-context-parity/_internal/metrics.md`.

Worktree:
`/home/Uihyeop/agent_setting-wt/codex-headless-context-parity`

Canonical artifact directory:
`/home/Uihyeop/agent_setting/.agent_reports/plans/2026-07-22_codex-headless-context-parity`

Read and obey:

- `baseline_comparison.md`
- `plan/plan.md`, `plan/plan_ko.md`, `plan/checklist.md`
- `_internal/plan_reviews/round_1.md`
- `_internal/plan_reviews/refine_round_1.md`
- `_internal/plan_reviews/round_2.md`
- `.agent_reports/spec/stage-dispatch/prd.md` SD-1/SD-2
- the `autopilot-code` owner contract and relevant stage contracts

First amend the English plan, Korean companion, and checklist to close every
round-2 finding. This is a correction, not another independent review round:

1. Freeze every `artifact_state` token and every legal
   state/source/verdict/artifact_state/blocker_reason/exit-code combination.
   Define relative, over-broad, non-directory, escaped, shadow, missing, and
   mismatched roots as fixed unsafe-root outcomes. Keep paths/free text out of
   `codex-terminal-v1`.
2. Split the deterministic lifecycle matrix: real foreground wrapper fixtures
   prove stream isolation, exact JSONL/artifact retention, receipt fields, and
   PASS-open versus FAIL/BLOCKED-closed transitions. Closed failures are read
   only through a supported exact-attempt selector if proven; otherwise use
   explicitly supplemental controlled open rows built from the same
   wrapper-shaped JSONL for liveness/wait checks. Preserve current-row
   filtering.
3. Add a named post-exit orphan-reconcile regression proving precedence,
   exact row/note transition, idempotence, no breadth-close, and no raw terminal
   leakage at the affected liveness/registry seam.
4. Replace the captured-output placeholder with a deterministic path or make
   the conformance test perform the negative scan internally.

Then implement the refined plan. Scope is limited to the 13 planned files:

- `utilities/codex_dispatch_terminal.py`
- `utilities/codex_dispatch_terminal.test.py`
- `adapters/codex/bin/dispatch-headless.py`
- `adapters/codex/bin/dispatch-liveness.py`
- `utilities/dispatch-liveness.sh`
- `utilities/dispatch-wait.sh`
- `adapters/codex/bin/dispatch-harvest.py`
- `utilities/dispatch_parent_context_conformance.test.py`
- `adapters/codex/bin/dispatch-headless.sd45.test.py`
- `utilities/dispatch-wait.test.sh`
- `utilities/dispatch-liveness.test.sh`
- `utilities/dispatch_harvest.test.py`
- `utilities/dispatch_registry.test.py`

Run the exact `preflight.sh write <path> codex-headless` guard immediately
before each file's first edit and use `apply_patch`. Do not modify core, specs,
capability topology, intensity routing, Fleet UI/schema, Claude adapter,
runtime config, credentials, or unrelated files. Do not commit, push, merge,
reset, checkout, or clean the worktree.

Required behavior:

- successful parent-facing receipt/liveness/wait/harvest output contains only
  bounded typed decision data and artifact readability metadata, never raw
  worker transcript or artifact body;
- failure-only details are opt-in, labeled, control-escaped, independently
  capped at 512 UTF-8 bytes without broken code points/escape tokens, and
  impossible on PASS;
- exact attempt/route/log/root binding and completion authority remain intact;
- legacy, mixed-harness, PID/heartbeat, current-row, fallback, post-exit orphan,
  and raw debug-log behavior remain compatible;
- success, failure, blocked, malformed, missing, unsafe-root, multibyte,
  control-character, linked-worktree, and sentinel-isolation fixtures pass.

Run all focused tests in the plan plus `git diff --check`. Write test evidence,
`pipeline_summary.md`, and a truthful `final_report.md` under the canonical
artifact directory. A PASS requires executable evidence, not prose.

Your final response must contain exactly:

artifact: <absolute path to final_report.md>
verdict: PASS|FAIL|BLOCKED
blocker: <none or concise enum>
