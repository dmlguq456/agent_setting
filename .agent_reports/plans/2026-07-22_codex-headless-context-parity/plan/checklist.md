# Initial implementation checklist

## Preconditions

- [x] Assigned starting commit confirmed:
  `8db730a48ca82ec23a9cd1a39fb65dd507e1be5a`.
- [x] SD-1/SD-2, `core/OPERATIONS.md` worker/file-only rules, and the exact
  worker envelope were read.
- [x] Relevant project-analysis directory checked; no handoff-specific analysis
  was available.
- [x] Claude success/fail/blocked local baseline measured.
- [x] Current Codex parser/liveness/wait/harvest fixture matrix measured.
- [x] `qa-policy thorough code` recorded in the primary plan.
- [x] Execute owner re-established the assigned SD-1/SD-2 spec read marker; the
  bounded worker kernel prohibited loading unrelated core/bootstrap documents.
- [x] Execute owner ran the exact `preflight.sh write <path> codex-headless`
  command printed immediately before each Phase 1-3 file in `plan.md`; no
  placeholder/final-after-edit guard is accepted.
- [x] The runtime-unavailable inline QA fallback is recorded honestly; no
  independent delegation is claimed.
- [x] Round 1 and round 2 findings are mapped to the corrected artifacts. Per
  assignment this was a correction, not a third independent review round.
- [x] Round 2 correction freezes the artifact-state/wire matrix, splits the
  wrapper-transition and supplemental liveness lifecycles, names the post-exit
  orphan-reconcile regression, and makes the conformance scan self-contained.

## Phase 1 — safe terminal inspection

- [x] Update `utilities/codex_dispatch_terminal.py` with
  absent/valid/invalid structured outcomes.
- [x] Preserve `inspect_terminal_log` compatibility.
- [x] Bind selection to the exact final agent message before `turn.completed`.
- [x] Add non-`-` artifact existence/root/symlink validation without reading the
  artifact body.
- [x] Resolve the canonical root from the selected row's fourth-column worktree
  with `utilities/artifact-root.sh`; cross-check existing pipe metadata, add no
  registry column, and never fall back to linked-worktree shadow reports.
- [x] Freeze the CLI as exactly one six-field `codex-terminal-v1` ASCII enum
  record with defined 0/2/3/4/64 exit behavior; shell callers never decode or
  receive artifact paths.
- [x] Freeze `artifact_state` to exactly
  `unchecked|none|readable|missing|outside-root|unsafe-root` and accept only the
  legal state/source/verdict/artifact-state/blocker tuples enumerated in
  `plan.md`; exit 64 emits no record and the v1 wire contains no path/free text.
- [x] Map relative, over-broad, non-directory, symlink-escaped, shadow, missing,
  and metadata-mismatched roots to the identical exit-4
  `error/runtime-error/-/unsafe-root/contract-violation` tuple. Keep artifact
  `missing` and `outside-root` as the distinct exit-3 invalid tuples.
- [x] Default all parent output to fixed `blocker_reason` enums. Require
  `PASS` + `blocker: none`; make non-`none` invalid.
- [x] Add explicit, default-off, failure-only blocker/diagnostic excerpts, each
  labeled/control-escaped and at most 512 UTF-8 bytes without splitting a code
  point or escape; no agent-message diagnostic source and no `PASS` detail.
- [x] Expose a validated Python artifact reference only as URL-safe unpadded
  `artifact_path_b64`; parent surfaces do not decode/open it.
- [x] Expand `utilities/codex_dispatch_terminal.test.py` with verdict, malformed,
  decoy, tail, linked-worktree/missing/mismatched-root, space/control path,
  symlink, exact wire/exit, malformed/multiple-record, mixed-harness,
  oversized/multibyte blocker/diagnostic, and bad-`PASS` cases.
- [x] Phase 1 parser gate passes before Phase 2; on failure use only guarded
  phase-local `apply_patch` old-block restoration (no reset/checkout).

## Phase 2 — parent-facing integration

- [x] Update Codex foreground receipt with normalized fields,
  `artifact_path_b64`, and fixed `blocker_reason`; never emit blocker/diagnostic
  detail from the receipt.
- [x] Preserve exact fail/blocked closure and `terminal_verdict` compatibility.
- [x] Prove parsed `PASS` cannot close a row or create/replace a completion
  marker.
- [x] Update Codex Python liveness so `PASS` becomes `COMPLETED`/exit 3.
- [x] Update shared shell liveness to use the safe Codex inspector for exact
  `log_file` rows and selected worktrees, accepting exactly the v1 six-field
  enum record and rejecting malformed/multiple records.
- [x] Preserve mixed-harness, PID, heartbeat, orphan, limit/auth, and legacy
  liveness paths.
- [x] Update wait exit-3 wording to include terminal completion while preserving
  0/2/3 semantics and bounded polling.
- [x] Update Codex harvest to emit the normalized handoff and artifact
  readability plus `artifact_path_b64`/fixed blocker reason without artifact or
  transcript bodies.
- [x] Add one explicit failure-only blocker/diagnostic detail option to harvest;
  enforce independent 512-byte caps and reject all `PASS` detail.
- [x] Preserve exact selector, profile cleanup, registry row, `job_pipe`, and
  hash-bound completion-marker behavior.
- [x] Phase 2 parser/headless/registry/harvest/liveness/wait focused gate passes
  before Phase 3; rollback, if needed, touches only the five Phase 2 source files
  via guarded `apply_patch` old blocks.

## Phase 3 — deterministic conformance

- [x] Add `utilities/dispatch_parent_context_conformance.test.py`.
- [x] Freeze fake-Claude `PASS`/`FAIL`/`BLOCKED` log-only baseline.
- [x] Build a fake `codex exec --json` and invoke the actual
  `adapters/codex/bin/dispatch-headless.py --start --launch-lifecycle foreground-scoped`
  subprocess for `PASS`, `FAIL`, and `BLOCKED`; capture wrapper stdout/stderr,
  exact JSONL, and registry before/after.
- [x] Feed wrapper-produced rows/logs through receipt, Python liveness, shared
  shell liveness/wait, and harvest according to the lifecycle-valid matrix:
  real `PASS` stays current/open and traverses every surface; real
  `FAIL`/`BLOCKED` are already closed and use only a proven exact-attempt
  read-only harvest selector; failure liveness/wait uses labeled supplemental
  controlled current/open rows with byte-identical wrapper-shaped JSONL.
- [x] Assert command/prior-agent/final-message sentinels remain in every exact
  attempt log but in no wrapper/parent output for any verdict.
- [x] Assert `ARTIFACT_BODY_SENTINEL` remains in the validated artifact but in no
  receipt/liveness/wait/harvest output; a simulated next stage decodes and opens
  the validated path directly.
- [x] Assert blocker/diagnostic excerpts are absent by default, explicitly
  labeled/bounded/escaped only for failures, and never available for `PASS`.
- [x] Assert a foreign/newer log cannot satisfy the exact selected attempt.
- [x] Assert wrapper-boundary registry transitions: `PASS` stays open with no
  completion marker; `FAIL`/`BLOCKED` close only the exact attempt; unrelated
  rows remain byte-for-byte unchanged.
- [x] Assert real failure rows remain closed and byte-identical after read-only
  harvest; supplemental failure rows remain open during liveness/wait and do
  not weaken current-row filtering or affect the real closed attempts.
- [x] Extend Codex SD-45 receipt tests.
- [x] Extend wait and shared liveness terminal-matrix tests.
- [x] Extend harvest handoff/path/diagnostic tests.
- [x] Extend registry liveness with a `PASS`-is-`COMPLETED` case.
- [x] Add named `test_codex_terminal_post_exit_orphan_reconcile` to
  `utilities/dispatch_registry.test.py`, proving existing precedence, exact
  row/note closure, second-run idempotence, sibling byte preservation, no
  breadth-close, and no raw terminal leakage.
- [x] Retain blocked sandbox-init, exact completion, ambiguous selector, legacy
  read-only, idempotent close, SD-15, and orphan regressions.
- [x] Phase 3 targeted plus real-wrapper conformance gate passes; rollback, if
  needed, touches only six Phase 3 test files with guarded `apply_patch`.

## Verification commands

- [x] `PYTHONPATH=utilities python3 utilities/codex_dispatch_terminal.test.py`
- [x] `python3 utilities/dispatch_parent_context_conformance.test.py`
- [x] `python3 adapters/codex/bin/dispatch-headless.sd45.test.py`
- [x] `python3 utilities/dispatch_registry.test.py`
- [x] `python3 utilities/dispatch_harvest.test.py`
- [x] `bash utilities/dispatch-wait.test.sh`
- [x] `bash utilities/dispatch-liveness.test.sh`
- [x] `python3 utilities/dispatch_progress.test.py`
- [x] `bash adapters/codex/bin/dispatch-headless.sd15.test.sh`
- [x] `python3 adapters/claude/bin/dispatch-headless.sd45.test.py`
- [x] `AGENT_DISPATCH_ALLOW_NAMESPACED_SPAWN=1 bash adapters/claude/bin/dispatch-headless.sd15.test.sh`
- [x] `git diff --check`
- [x] Scoped diff inspection confirms no spec, core, Claude wrapper, Fleet
  schema/collector, completion schema, fallback ordering, native-subagent,
  runtime-config, commit, merge, push, or cleanup changes.

## Required evidence for code-test/code-report

- [x] Command, exit code, duration, and test count for every targeted command.
- [x] Per-phase owned-file list, focused-gate result, and non-destructive rollback
  boundary record.
- [x] Captured wrapper stdout/stderr and all parent-facing outputs for the
  three-verdict matrix.
- [x] Conformance test owns a deterministic temporary capture tree, scans every
  parent capture internally before cleanup, reports the checked capture count,
  and positively proves sentinel presence in exact logs/artifacts; there is no
  external capture-directory placeholder.
- [x] Blocker/diagnostic byte-length evidence for oversized ASCII, control, and
  multibyte boundaries plus `PASS` absence/invalid-blocker evidence.
- [x] Registry before/after evidence proving `PASS` stays open until exact marker
  harvest and failure closes only the exact attempt.
- [x] Exact v1 wire/exit evidence, malformed/multiple-record rejection, and
  mixed-harness bypass, covering every legal tuple and representative illegal
  cross-products with no path/free text in the record.
- [x] Linked-worktree/missing-root/mismatch/space-control-path/artifact
  containment/symlink negative evidence.
- [x] Post-exit orphan-reconcile evidence records precedence, exact row/note
  before/after, second-run no-op, unchanged sibling row, and zero raw-terminal
  sentinel leakage.
- [x] Final scoped file list and diff summary.
- [x] Thorough assurance result or explicit inline-review fallback record.
