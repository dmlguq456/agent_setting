# Implementation log

## Execution identity

- Date: 2026-07-22
- Starting commit: `8db730a48ca82ec23a9cd1a39fb65dd507e1be5a`
- Capability/mode: `autopilot-code`, `dev/refactor`
- QA/intensity: `thorough code`, `standard`
- Topology: registered dispatch-depth-1 owner, inline
- Inline exception: `runtime-unavailable`; recorded in `_internal/metrics.md`.
  No depth-2 child was dispatched because the lifecycle seam under repair is
  what currently prevents this owner from closing a terminal PASS child.

## Plan correction

Amended `plan/plan.md`, `plan/plan_ko.md`, and `plan/checklist.md` before source
execution. The correction:

1. froze all six `artifact_state` values and every legal wire/exit tuple;
2. normalized relative, over-broad, non-directory, escaped, shadow, missing,
   and mismatched roots to the fixed unsafe-root outcome;
3. split real-wrapper transition evidence from supplemental controlled-open
   failure liveness/wait evidence;
4. named `test_codex_terminal_post_exit_orphan_reconcile`; and
5. moved negative capture scanning inside the deterministic conformance test.

## Source decisions

- `utilities/codex_dispatch_terminal.py`: retained
  `inspect_terminal_log` for registry compatibility and added a separate
  root-bound structured inspector plus the path-free `codex-terminal-v1` CLI.
  Failure detail is opt-in, failure-only, control-escaped, and independently
  capped at 512 UTF-8 bytes per field.
- `adapters/codex/bin/dispatch-headless.py`: foreground receipt now renders only
  normalized handoff fields. Exact FAIL/BLOCKED closure remains unchanged;
  PASS remains observational and open. Every new registered attempt uses an
  attempt-id-specific JSONL path so a same-slug retry cannot alias the earlier
  attempt's terminal result.
- Python/shared liveness inspect the exact row log and worktree. PASS is
  `COMPLETED`/exit 3; failures and invalid/error states are typed without raw
  log text. Existing orphan precedence is preserved.
- `utilities/dispatch-wait.sh`: synchronous 0/2/3 polling is unchanged; exit-3
  wording now covers terminal completion.
- `adapters/codex/bin/dispatch-harvest.py`: added an exact attempt selector,
  normalized artifact/readability output, and the explicit `--failure-detail`
  option. Completion-marker and exact closure authority are unchanged.

## Test construction

- Parser fixtures cover success, failure, blocked, absent, malformed,
  interposed-event, bad PASS blocker, large tails, multibyte/control detail,
  artifact missing/escape, all wire tuples, CLI exits, and every named unsafe
  root class including linked-worktree shadow.
- Real `dispatch-headless.py --start --launch-lifecycle foreground-scoped`
  runs use a deterministic fake `codex exec --json` for PASS/FAIL/BLOCKED.
  They retain raw sentinels in exact JSONL/artifacts and scan 34 parent-facing
  captures for non-leakage before temporary cleanup. The fixture owns an
  isolated temporary Codex runtime projection and includes a same-slug,
  two-attempt PASS-then-FAIL exact-log regression.
- Real failure rows are verified closed and read only by exact attempt harvest.
  Byte-identical wrapper-shaped logs are attached to explicitly supplemental
  current/open rows for Python/shared liveness and wait.
- The named post-exit orphan test proves PASS observation does not mask orphan
  precedence, only the exact owner row receives `dead-parent-orphaned`, the
  sibling remains byte-identical, and a second reconcile is a no-op.

## Scope

During depth-0 review, the adapter SD-45 test change was reverted and reapplied
under a successful current-session core-first read/write guard after the worker's
first guard invocation had failed. The complete prescribed suite was rerun
after that correction and the exact-log fix.

Exactly the assigned 13 tracked files changed. No core, spec, capability
topology, Fleet schema/collector, Claude adapter, runtime configuration,
credential, completion-marker schema, or fallback ordering file changed. No
reset, destructive checkout, or asynchronous wait occurred. Depth-0 committed
the source as `ab74d676`, fast-forwarded and pushed `main`, then removed the
eligible linked worktree after the integrated suite passed.

## Runtime-currentness check

The integrating session refreshed the official Codex manual and checked the
installed CLI surface. Current Codex documentation and `codex exec --help`
still define `codex exec --json` as a JSONL event stream containing
`turn.completed` and `item.*` events. Anthropic's current Claude Code CLI
reference still defines `-p/--print` as non-interactive mode with
`text|json|stream-json` output. The local adapter implementation remains a
checked projection over those separate runtime surfaces; no Claude-native tool
was used to claim Codex support.
