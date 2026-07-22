---
status: complete
created: 2026-07-22
---

# Codex registered-headless handoff and parent-context hygiene

## Goal

Give Codex registered-headless parents a typed, exact-attempt handoff across
launch, wait/liveness, and harvest without copying raw worker content into the
parent context, while preserving all registry, Fleet, completion-marker,
fallback, liveness, and debugging contracts.

## Current state analysis

### Governing behavior

- SD-1 requires the dispatch-depth-1 owner to remain a thin conductor holding
  only stage paths, verdict/status, and gate decisions; it must not read stage
  bodies (`.agent_reports/spec/stage-dispatch/prd.md:123-128`).
- SD-2 requires file-only cross-stage handoff; prompts carry artifact paths and
  contracts, not previous conversation or copied plan bodies (`prd.md:130-136`).
- Registered workers receive the minimal typed kernel and return exactly the
  three-line envelope (`core/OPERATIONS.md:96-100`,
  `roles/worker-bootstrap.md:3-30`).
- Exact registry identity, bounded same-turn wait, liveness evidence, fallback,
  and exact completion markers are already canonical (`core/OPERATIONS.md:166-177`).

### Claude comparator

- The sibling wrapper redirects all `claude -p` output to the attempt log and
  prints only a launch receipt (`adapters/claude/bin/dispatch-headless.py:410-429,
  1068-1118,1129-1189`).
- Measured success, failure, and blocked fake-CLI fixtures all kept the raw
  marker and three-line handoff out of the parent receipt and in the attempt log.
  See `../baseline_comparison.md` for the matrix and commands.
- Claude does not type a textual zero-exit `FAIL`/`BLOCKED` receipt. That omission
  is not a behavior to copy; the parity target is transcript isolation plus
  equivalent safe information classes.

### Codex path and genuine gaps

- `utilities/codex_dispatch_terminal.py:16-115` recognizes the exact final
  handoff before `turn.completed`, including typed sandbox-init, fail, and
  blocked outcomes. It conflates absent and invalid terminal envelopes and does
  not check the artifact path against `artifact_root`.
- `adapters/codex/bin/dispatch-headless.py:554-604` already redirects
  `codex exec --json` into the attempt JSONL. Foreground launch parses the
  terminal result and closes only exact fail/blocked rows (`:1431-1455`), then
  prints a receipt (`:1466-1536`). Raw content is not currently printed.
- `adapters/codex/bin/dispatch-liveness.py:324-369` recognizes only terminal
  outcomes with a failure note. A valid `PASS` falls through to dead-PID
  classification and is shown as generic `EXITED`.
- `utilities/dispatch-liveness.sh:69-209` is the surface used by
  `utilities/dispatch-wait.sh:78-88`; it treats Codex JSONL as mtime/debug
  evidence but does not extract an exact typed handoff. Wait therefore cannot
  distinguish `PASS`, `FAIL`, and `BLOCKED` without raw-log diagnosis.
- `adapters/codex/bin/dispatch-harvest.py:39-55,118-200` reports registry rows
  and performs exact completion/closure logic, but it does not expose a safe
  terminal envelope or artifact-readability result.
- Existing coverage proves parsing, sandbox-init closure, registry exactness,
  and wait exit codes, but not end-to-end parent-output isolation. Relevant
  starting points are `utilities/codex_dispatch_terminal.test.py:10-62`,
  `utilities/dispatch_registry.test.py:44-72`,
  `utilities/dispatch_harvest.test.py:99-207`, and
  `utilities/dispatch-wait.test.sh:31-80`.

## Change plan

### Phase 1: define one safe exact-attempt terminal inspection API

Dependency: none. Complete this phase before integrating any parent-facing
surface.

1.1. Update `utilities/codex_dispatch_terminal.py`.

- Pre-edit guard: run
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write utilities/codex_dispatch_terminal.py codex-headless`
  immediately before the file's first edit.
- Preserve `inspect_terminal_log(path) -> dict | None` as a compatibility
  wrapper for current callers.
- Add a structured inspection API that distinguishes `absent`, `valid`, and
  `invalid` after examining the last exact `turn.completed` event. An invalid
  result must contain only an enum-like reason such as
  `missing-final-agent-message`, `malformed-handoff`, or
  `artifact-outside-root`; it must not contain rejected raw text.
- Continue accepting only the last agent message before the exact terminal
  event and only the exact three-line grammar. Ignore earlier agent messages,
  command output, and events after the selected terminal event.
- Make the selected registry row's fourth-column `worktree` the root-resolution
  input. Resolve it through the existing
  `utilities/artifact-root.sh <selected-worktree>` contract, including its
  absolute `AGENT_ARTIFACT_ROOT` override behavior, and pass the resolved root
  explicitly to inspection. Do not add a registry column. Treat existing
  `artifact_root` pipe metadata as a cross-check only; mismatch, resolver
  failure, or a missing root yields a fixed `artifact-root-unavailable` or
  `artifact-root-mismatch` state and must never fall back to the linked
  worktree's tracked `.agent_reports` shadow.
- For non-`-` artifacts, resolve strictly below that root, reject missing paths
  and symlink/path escapes, and return only a typed readability state plus the
  validated path. Do not open or print the artifact body. Do not decide whether
  `artifact: -` is legal; existing worker and completion-gate contracts retain
  that decision.
- Freeze the shell wire as one ASCII record with this exact v1 grammar and
  order:
  `codex-terminal-v1<TAB>state<TAB>source<TAB>verdict<TAB>artifact_state<TAB>blocker_reason<LF>`.
  Values are closed enums only: `state=valid|absent|invalid|error`,
  `source=exact-turn-completed|runtime-error|none`,
  `verdict=PASS|FAIL|BLOCKED|-`, typed artifact states, and
  `blocker_reason=none|worker-reported|contract-violation|-`. The record omits
  artifact paths and all worker-authored text, so shell liveness never decodes
  a path. Exit codes are 0/2/3/4 for valid/absent/invalid/inspection-error and
  64 for CLI misuse; codes 0/2/3/4 each emit exactly one record and never raw
  stderr. Malformed/multiple records are caller-side `inspector-wire-invalid`.
- Freeze `artifact_state` to exactly
  `unchecked|none|readable|missing|outside-root|unsafe-root`. The complete legal
  wire matrix is:

  | exit | state | source | verdict | artifact_state | blocker_reason |
  |---:|---|---|---|---|---|
  | 0 | `valid` | `exact-turn-completed` | `PASS` | `none|readable` | `none` |
  | 0 | `valid` | `exact-turn-completed` | `FAIL|BLOCKED` | `none|readable` | `none|worker-reported` |
  | 2 | `absent` | `none` | `-` | `unchecked` | `-` |
  | 3 | `invalid` | `exact-turn-completed` | `-` | `unchecked|missing|outside-root` | `contract-violation` |
  | 4 | `error` | `runtime-error` | `-` | `unchecked|unsafe-root` | `contract-violation` |

  No other tuple is legal; exit 64 emits no record. Paths and free text are
  categorically absent from `codex-terminal-v1`. A root that is relative,
  filesystem-wide/over-broad, not a directory, missing, symlink-escaped,
  resolved to a tracked worktree `.agent_reports` shadow, or mismatched with
  exact-attempt pipe metadata always maps to the single fixed tuple
  `error/runtime-error/-/unsafe-root/contract-violation` and exit 4. It never
  degrades to `missing` or a shadow fallback. A valid root plus a missing
  artifact maps to `invalid/exact-turn-completed/-/missing/contract-violation`;
  a valid root plus an escaped artifact maps to the analogous `outside-root`
  tuple.
- Define one parent-output policy for all worker-authored failure text. Default
  receipt/liveness/wait/harvest output contains only the fixed
  `blocker_reason`; `PASS` requires `blocker: none`, otherwise inspection is
  invalid with `pass-blocker-not-none`. If harvest explicitly requests failure
  detail, expose it only under `blocker_detail_excerpt` and/or
  `failure_diagnostic_excerpt`; escape controls first, then truncate each to the
  greatest complete UTF-8/code-point-and-escape prefix at or below 512 bytes.
  Emit a fixed `*_truncated=0|1` flag. Diagnostics may select only a structured
  failed `command_execution`/runtime error from the exact attempt, never an
  `agent_message`. Every `PASS`, even with the option, omits both fields.
- Python receipt/harvest callers may expose a validated artifact reference as
  RFC 4648 URL-safe UTF-8 base64 without padding under `artifact_path_b64`.
  They do not decode or open it. Liveness/wait never receive the path; a
  consuming stage may decode it only after exact-attempt `valid` + `readable`
  checks and then opens the file under its own guard.

1.2. Expand `utilities/codex_dispatch_terminal.test.py`.

- Pre-edit guard: run
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write utilities/codex_dispatch_terminal.test.py codex-headless`
  immediately before the file's first edit.
- Add named fixtures for `PASS`, `FAIL`, and `BLOCKED` with distinct raw command,
  earlier-agent-message, and final-envelope sentinels.
- Cover absent `turn.completed`, completed-without-envelope, malformed extra
  prose, a decoy earlier envelope, events after completion, oversized tails,
  artifact existence/containment, and a symlink escape.
- Prove the compatibility wrapper retains current failure notes
  (`dead-worker-fail`, `dead-worker-blocked`, `dead-sandbox-init`).
- Cover linked-worktree canonical-root resolution, missing root, root-metadata
  mismatch, spaces/control bytes in fixture paths, the exact single-record wire,
  every wire exit code, malformed/multiple CLI records, and mixed-harness bypass.
- Exercise every legal row in the frozen state/source/verdict/artifact-state/
  blocker/exit matrix and reject representative illegal cross-products. Add
  separate relative, over-broad, non-directory, symlink-escaped, shadow,
  missing, and metadata-mismatched root fixtures, all asserting the identical
  `unsafe-root` tuple and zero path/free-text leakage.
- Prove blocker/diagnostic detail is default-off, failure-only, labeled,
  control-escaped, and bounded with oversized single-line and multibyte-boundary
  cases. Add negative fixtures for `PASS` with non-`none` blocker and any `PASS`
  detail emission. Prove no agent message can source a diagnostic.

Completion evidence: parser unit suite passes; valid fixtures expose only the
three handoff fields and typed metadata; invalid fixtures expose no raw sentinel;
the exact wire/root/failure-text contract passes its boundary matrix.

Phase 1 focused gate and rollback boundary: run
`PYTHONPATH=utilities python3 utilities/codex_dispatch_terminal.test.py` before
starting Phase 2. Record the phase-owned file list and old/new blocks in the
execution step log. If the gate fails, stop; re-run each owned file's exact write
guard and restore only Phase 1 edits with `apply_patch` from those recorded old
blocks. Do not use reset/checkout and do not touch pre-existing or unrelated
worktree changes.

### Phase 2: project the safe result into parent-facing control surfaces

Dependency: Phase 1 API and tests.

2.1. Update `adapters/codex/bin/dispatch-headless.py`.

- Pre-edit guard: run
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write adapters/codex/bin/dispatch-headless.py codex-headless`
  immediately before the file's first edit.
- Replace the foreground-only dictionary probing with the structured inspection
  result, while retaining `terminal_verdict` for compatibility.
- Resolve/cross-check the canonical root from the exact selected worktree as in
  Phase 1. Add receipt fields for handoff state/source, verdict,
  artifact-readability, `artifact_path_b64`, and fixed `blocker_reason`; never
  emit blocker detail, diagnostics, transcript text, or artifact contents.
- Preserve exact `FAIL`/`BLOCKED` row closure and its evidence. A valid `PASS`
  remains an observation only: do not close the row, write a completion marker,
  or advance a route.
- Keep detached launch behavior unchanged; it returns before a terminal envelope
  exists, and later liveness/harvest owns inspection.

2.2. Update `adapters/codex/bin/dispatch-liveness.py`.

- Pre-edit guard: run
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write adapters/codex/bin/dispatch-liveness.py codex-headless`
  immediately before the file's first edit.
- Inspect the exact row's `log_file` before PID/transcript fallback for every
  verdict, not only failures.
- Render valid `PASS` as `COMPLETED ... exact turn.completed PASS; harvest
  required`, and retain exit 3 while the row is open. Render `FAIL`/`BLOCKED` as
  typed terminal failure without a transcript excerpt. Render terminal-invalid
  as typed `EXITED ... invalid-handoff` without rejected content.
- Preserve exact-attempt binding, orphan precedence, limit/auth classification,
  heartbeat/PID evidence, current-row filtering, and exit codes.

2.3. Update `utilities/dispatch-liveness.sh`.

- Pre-edit guard: run
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write utilities/dispatch-liveness.sh codex-headless`
  immediately before the file's first edit.
- For a current Codex row with an exact `log_file`, call the Phase 1 machine-safe
  inspector with the selected row's `worktree` before the generic PID/mtime
  fallback. Parse exactly six tab-separated v1 fields, reject extra/missing
  records as `inspector-wire-invalid`, consume only enums, and never decode an
  artifact path.
- Match the Python surface's `COMPLETED`/typed-failure/invalid-handoff classes
  and exit-3 behavior. Do not embed artifact body, blocker text, or raw JSONL.
- Leave Claude/OpenCode PID, transcript, limit, orphan, and legacy-row paths
  untouched; mixed-harness registries must continue to work.

2.4. Update `utilities/dispatch-wait.sh`.

- Pre-edit guard: run
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write utilities/dispatch-wait.sh codex-headless`
  immediately before the file's first edit.
- Keep selection, 0/2/3 exit semantics, interval/max bounds, and synchronous
  polling unchanged.
- Generalize the exit-3 heading from only `SUSPECT/DEAD` to
  `terminal/SUSPECT/DEAD` so a successfully completed-but-unharvested Codex
  child is not mislabeled as dead.
- Continue forwarding only the now-sanitized liveness output.

2.5. Update `adapters/codex/bin/dispatch-harvest.py`.

- Pre-edit guard: run
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write adapters/codex/bin/dispatch-harvest.py codex-headless`
  immediately before the file's first edit.
- After exact row selection, inspect only that row's `log_file` and emit the
  normalized handoff state/source/verdict, `artifact_path_b64`, fixed
  `blocker_reason`, and artifact-readability fields. Resolve from the selected
  row's worktree and cross-check pipe metadata; do not read or print contents.
- Add one explicit failure-detail option backed by the shared inspector. It may
  add only the bounded/labeled blocker and diagnostic excerpt fields defined in
  Phase 1. Reject detail for `PASS`; never enable it by default.
- Preserve existing `job_pipe` output for Fleet/debug compatibility, exact
  selector checks, current attempt validation, profile-home cleanup, and
  completion-marker replay.
- Preserve closure semantics: routed `PASS` still requires the exact hash-bound
  `--completion`; no parsed handoff may breadth-close or substitute for it.

Completion evidence: the same fixture produces a consistent typed verdict in
foreground receipt, Codex liveness, shared wait, and harvest; success output has
zero raw sentinels; requested failure fields are labeled and each at most 512
UTF-8 bytes.

Lifecycle-valid fixture matrix: the real foreground wrapper owns stream
isolation, exact JSONL/artifact retention, receipt fields, and registry
transitions. Its `PASS` row remains current/open and is used directly by Python
liveness, shared liveness/wait, and read-only harvest. Its `FAIL` and `BLOCKED`
rows must already be closed when the wrapper returns. They are inspected after
closure only by an existing supported exact-attempt read-only harvest selector
when that selector is proven by the test; normal current-row filtering is never
weakened. Failure liveness/wait coverage instead uses explicitly supplemental
controlled current/open rows whose exact log bytes are copied from the real
wrapper-shaped `FAIL`/`BLOCKED` JSONL. Assertions label those rows supplemental
and prove they do not become a way to select a closed or non-current attempt.

Phase 2 focused gate and rollback boundary: run the parser suite plus
`python3 adapters/codex/bin/dispatch-headless.sd45.test.py`,
`python3 utilities/dispatch_registry.test.py`,
`python3 utilities/dispatch_harvest.test.py`,
`bash utilities/dispatch-liveness.test.sh`, and
`bash utilities/dispatch-wait.test.sh` before Phase 3. If any fail, stop and use
`apply_patch` plus the execution logs' recorded old blocks to reverse only the
five Phase 2 source files after re-running their exact write guards; preserve
Phase 1 and all unrelated/pre-existing changes.

### Phase 3: deterministic parity and regression coverage

Dependency: Phases 1 and 2. Tests within this phase are independent except for
the final aggregate run.

3.1. Add `utilities/dispatch_parent_context_conformance.test.py`.

- Pre-edit guard: run
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write utilities/dispatch_parent_context_conformance.test.py codex-headless`
  immediately before creating the file.
- Freeze the measured Claude baseline with fake `claude -p` success/fail/blocked
  fixtures: raw content and the handoff remain in the attempt log, while the
  parent receipt contains neither.
- Build a fake `codex` executable parallel to the fake-Claude fixture. Invoke the
  actual `adapters/codex/bin/dispatch-headless.py --start` subprocess with
  `--launch-lifecycle foreground-scoped` for `PASS`, `FAIL`, and `BLOCKED`, a
  real temporary Git worktree/artifact root/registry, and deterministic fake
  `codex exec --json` stdout and stderr. Capture wrapper stdout, wrapper stderr,
  the exact attempt JSONL, and registry before/after; do not substitute a
  renderer call for this boundary test.
- Feed the wrapper-produced open `PASS` row/log through Codex Python liveness,
  shared shell liveness/wait, and read-only harvest. Inspect wrapper-produced
  closed `FAIL`/`BLOCKED` rows only through the supported exact-attempt read-only
  harvest selector after proving that selector does not change current-row
  filtering. For Python/shared liveness and wait, create explicitly
  supplemental controlled current/open rows from byte-identical copies of the
  real wrapper-shaped failure JSONL; never reopen or breadth-select the wrapper's
  closed failure attempts. Keep handcrafted parser/renderer fixtures only as
  supplemental unit coverage.
- Use separate sentinels for raw command output, prior agent content, final
  envelope, optional failure diagnostics, and artifact-body-only content. For
  every verdict, assert command/prior-agent/final-message sentinels remain in the
  exact attempt log but not wrapper stdout/stderr or any later parent-facing
  output. Assert the artifact-body sentinel remains in the validated artifact
  but not receipt/liveness/wait/harvest; a simulated next stage decodes the
  validated reference and opens the artifact directly.
- Prove optional blocker/diagnostic excerpts are absent by default, present only
  under the explicit failure option, labeled, control-escaped, and capped at 512
  UTF-8 bytes, including oversized/multibyte/control cases. Prove `PASS` cannot
  expose detail and `PASS` with non-`none` blocker is invalid.
- Assert attempt/route/log binding so another worker's newer log cannot satisfy
  the selected row. Assert `PASS` leaves its exact row open and creates no
  completion marker, while `FAIL`/`BLOCKED` close only their exact attempt with
  existing notes; unrelated and decoy rows remain byte-for-byte unchanged.
- Freeze before/after observations per verdict: wrapper `PASS` is open before
  and after liveness/wait/read-only harvest and has no completion marker;
  wrapper `FAIL`/`BLOCKED` are already exact-attempt closed before read-only
  harvest and remain byte-identical afterward; supplemental failure rows remain
  open throughout their liveness/wait observations and cannot affect the real
  closed rows.

3.2. Extend `adapters/codex/bin/dispatch-headless.sd45.test.py`.

- Pre-edit guard: run
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write adapters/codex/bin/dispatch-headless.sd45.test.py codex-headless`
  immediately before the file's first edit.
- Add receipt-rendering cases for valid pass/fail/blocked, invalid terminal, and
  no terminal as supplemental unit coverage; wrapper-boundary isolation
  authority remains in step 3.1.
- Assert `PASS` never calls row-close or completion-marker code; fail/blocked
  close only the exact attempt with existing notes.
- Assert receipt stdout does not contain raw command or prior-agent sentinels.

3.3. Extend `utilities/dispatch-wait.test.sh` and
`utilities/dispatch-liveness.test.sh`.

- Pre-edit guards, immediately before each file's first edit:
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write utilities/dispatch-wait.test.sh codex-headless`
  and
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write utilities/dispatch-liveness.test.sh codex-headless`.
- Add exact Codex `PASS`, `FAIL`, and `BLOCKED` JSONL rows under one parent.
- Assert exit 3, typed terminal wording, and zero raw sentinel leakage; retain
  all existing no-row, alive, dead, parent-filter, namespace, and limit cases.
- Add the exact v1 wire, malformed/multiple-record rejection, linked-worktree,
  missing-root, spaces/control-byte path, and mixed-harness bypass cases.

3.4. Extend `utilities/dispatch_harvest.test.py`.

- Pre-edit guard: run
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write utilities/dispatch_harvest.test.py codex-headless`
  immediately before the file's first edit.
- Add exact-row success/fail/blocked envelope output and artifact-root
  validation cases.
- Add a foreign/newer-log negative case, a malformed envelope case, default-off
  blocker/diagnostics, failure-only bounded details, oversized/multibyte/control
  cases, `PASS` with non-`none` blocker, and success non-leakage.
- Re-run existing ambiguous selector, legacy read-only, idempotent close, and
  exact completion-marker tests unchanged.

3.5. Extend `utilities/dispatch_registry.test.py` only for the liveness seam.

- Pre-edit guard: run
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write utilities/dispatch_registry.test.py codex-headless`
  immediately before the file's first edit.
- Add a valid `PASS` terminal fixture proving an open row is reported
  `COMPLETED` rather than generic `EXITED` and remains open until completion
  harvest.
- Retain the blocked sandbox-init exact-row closure fixture.
- Add the named deterministic
  `test_codex_terminal_post_exit_orphan_reconcile` regression at the Python
  liveness/registry seam. Start with one dead-PID open Codex attempt whose exact
  log contains a valid terminal envelope plus a distinct sibling row. Prove
  post-exit orphan reconciliation keeps its existing precedence over the new
  terminal display, changes only the exact target row and its existing note to
  the canonical closed form, leaves the sibling byte-for-byte unchanged, emits
  no raw terminal sentinel, and makes a second reconcile invocation a no-op.
  The concrete owner command is `python3 utilities/dispatch_registry.test.py`;
  no broad close is permitted.

Completion evidence: all targeted and aggregate commands below pass. The
conformance test creates its capture tree under its own `TemporaryDirectory`,
performs the negative sentinel scan internally before cleanup, reports the
checked capture count, and positively checks exact logs/artifacts retain their
sentinels. There is no external capture-path placeholder.

Phase 3 focused gate and rollback boundary: run every Phase 3-owned targeted
test, then `python3 utilities/dispatch_parent_context_conformance.test.py` as the
wrapper-boundary gate. On failure, stop and restore only the six Phase 3 test
files from their execution-log old blocks with `apply_patch` (delete the new
conformance file only if this phase created it), after re-running exact write
guards. Do not alter passing Phase 1/2 implementation or unrelated changes.

### Phase 4: final verification and handoff evidence

Dependency: all implementation phases.

4.1. Run the exact targeted commands listed in Verification, record stdout,
exit codes, and test counts under the cycle's `test_logs/` ownership rather than
in source or the parent conversation. Include each phase's focused-gate result,
owned-file list, and rollback boundary; no source edit is permitted in Phase 4.

4.2. Run `git diff --check` and inspect the scoped diff. Confirm no changes to
the canonical PRD, core contracts, Claude wrapper, Fleet schema/collector,
completion-marker format, fallback ordering, native-subagent surfaces, runtime
configuration, commits, merge, push, or cleanup.

4.3. Run the thorough code assurance selected by
`preflight.sh qa-policy thorough code`: one selected independent plan/code pass
with up to two review rounds and the configured upper bound of two deep plus two
fast reviewers. If independent workers are unavailable, record the required
inline-review fallback honestly; do not claim independent delegation.

## Safety invariants

1. Raw worker output remains durable and available at the exact attempt log for
   debugging, but no normal successful parent-facing output reproduces it.
2. All terminal inspection is bound to registry `attempt_id` plus that row's
   `log_file`; no cwd-wide/newest-log fallback can supply a terminal handoff for
   a current exact attempt.
3. Only an exact final three-line envelope immediately preceding the selected
   `turn.completed` is valid. Malformed terminal output fails closed without
   echoing the rejected text. `PASS` is valid only with `blocker: none`.
4. Parsed `PASS` is not success authority. Only the existing exact hash-bound
   completion marker closes/advances a routed success.
5. Existing failure notes and fallback behavior remain stable. Parser work does
   not reorder or add fallback hops or consume retry budget.
6. Registry schema, six-field row shape, status vocabulary, exact attempt
   closure, Fleet-readable metadata, and job-pipe debug data do not change.
7. Wait remains synchronous and bounded with exit 0/2/3 semantics. Liveness PID,
   heartbeat, orphan, limit/auth, and legacy fallbacks remain intact. The named
   post-exit orphan-reconcile regression fixes precedence, exact row/note
   transition, idempotence, sibling preservation, and terminal non-leakage.
8. The canonical root is resolved from the exact row worktree through
  `utilities/artifact-root.sh`, never inferred from a new registry column or a
   linked-worktree shadow. Relative, over-broad, non-directory, escaped, shadow,
   missing, and mismatched roots all produce the fixed `unsafe-root` tuple. A
   non-`-` artifact path is exposed as readable only after strict containment;
   parent surfaces never print artifact bodies.
9. The v1 shell wire is one six-field ASCII enum record and carries no path or
   worker-authored text. Failure blocker/diagnostic excerpts are opt-in,
   failure-only, explicitly labeled, control-escaped, and capped independently
   at 512 UTF-8 bytes without splitting a code point/escape. Agent messages are
   never diagnostic sources; `PASS` exposes no detail.
10. Runtime-native subagents, Claude agent teams, spec edits, unrelated
    refactors, commits, merge, push, cleanup, and runtime config are out of scope.

## Risks

- Treating a textual `PASS` as a completion marker would bypass SD-70. Mitigate
  by keeping liveness at exit 3 and leaving the row open until exact completion
  harvest.
- Shell and Python liveness may drift. Mitigate by sharing the same inspector
  CLI, freezing the six-field v1 grammar/exit codes, rejecting malformed or
  multiple records, and running the same verdict fixtures against both surfaces.
- Artifact resolution can introduce symlink or TOCTOU risk. Resolve strictly at
  every inspection from the exact row worktree, cross-check existing pipe
  metadata, report a typed unreadable state, and let the consuming stage reopen
  under its own guard rather than trusting cached content.
- Worker-authored blocker or diagnostic text can be huge or sensitive. Default
  to fixed enums, keep detail explicit/bounded/labeled and unavailable on
  success, and cover oversized single-line, control, and UTF-8 boundaries.
- Very large or malformed JSONL can create ambiguity. Retain the bounded tail,
  fail closed on invalid UTF-8/JSON/envelope state, and test boundary cases.
- Changing wait wording can break string-based tests. Preserve exit codes and
  stable class tokens while updating only the human heading and fixtures.
- The spec-read marker was read-only in this planning sandbox. Execute must
  re-establish the core/spec read marker and per-file write guards before source
  edits; do not treat this plan artifact as guard evidence.
- Phase-local rollback can overwrite pre-existing work if implemented broadly.
  Each phase therefore stops at its focused gate and uses only guarded
  `apply_patch` reversals from execution-log old blocks for that phase's owned
  files; reset/checkout and unrelated-file cleanup are forbidden.

## Verification

Run from `/home/Uihyeop/agent_setting-wt/codex-headless-context-parity` at the
assigned source lineage.

Guard and policy checks:

```sh
/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh qa-policy thorough code
git status --short
git rev-parse HEAD
```

The executable per-file write guards are enumerated immediately before each
Phase 1-3 step. Each must run before that file's first edit; this final block is
not a substitute and intentionally contains no placeholder guard.

Targeted tests:

```sh
PYTHONPATH=utilities python3 utilities/codex_dispatch_terminal.test.py
python3 utilities/dispatch_parent_context_conformance.test.py
python3 adapters/codex/bin/dispatch-headless.sd45.test.py
python3 utilities/dispatch_registry.test.py
python3 utilities/dispatch_harvest.test.py
bash utilities/dispatch-wait.test.sh
bash utilities/dispatch-liveness.test.sh
python3 utilities/dispatch_progress.test.py
bash adapters/codex/bin/dispatch-headless.sd15.test.sh
```

Comparator regression (fixture override is required only because the test
intentionally exercises detached launch inside a transient PID namespace):

```sh
python3 adapters/claude/bin/dispatch-headless.sd45.test.py
AGENT_DISPATCH_ALLOW_NAMESPACED_SPAWN=1 bash adapters/claude/bin/dispatch-headless.sd15.test.sh
```

Final scoped checks:

```sh
git diff --check
git diff -- adapters/codex/bin/dispatch-headless.py adapters/codex/bin/dispatch-liveness.py adapters/codex/bin/dispatch-harvest.py utilities/codex_dispatch_terminal.py utilities/dispatch-liveness.sh utilities/dispatch-wait.sh utilities/codex_dispatch_terminal.test.py utilities/dispatch_parent_context_conformance.test.py adapters/codex/bin/dispatch-headless.sd45.test.py utilities/dispatch_registry.test.py utilities/dispatch_harvest.test.py utilities/dispatch-wait.test.sh utilities/dispatch-liveness.test.sh
```

`utilities/dispatch_parent_context_conformance.test.py` owns the deterministic
capture directory and performs the negative sentinel scan internally; no
second shell path is required.

Expected final evidence:

- Every targeted command exits 0.
- Wrapper stdout/stderr and receipt/liveness/wait/harvest captures for all three
  verdicts contain zero command/prior-agent/final-message/artifact-body
  sentinels; exact attempt logs and validated artifacts positively retain their
  respective sentinels.
- Blocker/diagnostic details appear only with the explicit failure option, under
  required labels, and each measures no more than 512 UTF-8 bytes across ASCII,
  controls, and multibyte boundaries. `PASS` emits `blocker_reason=none` and no
  detail; `PASS` with non-`none` blocker is invalid.
- The v1 wire is exactly one six-field enum record with defined 0/2/3/4/64 exit
  behavior and only the enumerated legal tuples. Relative, over-broad,
  non-directory, escaped, shadow, missing, and mismatched roots all produce the
  fixed `unsafe-root` tuple without raw output; artifact missing/outside-root
  remain their distinct invalid tuples; mixed-harness rows bypass the parser.
- `PASS` liveness says `COMPLETED` but the routed row remains open until the exact
  completion marker is harvested.
- Fail/blocked retain existing exact failure notes and fallback behavior.
- The lifecycle matrix proves real-wrapper `PASS`-open and
  `FAIL`/`BLOCKED`-closed transitions while supplemental controlled open rows,
  made from the same wrapper-shaped JSONL, cover failure liveness/wait without
  weakening current-row filtering. The named post-exit orphan regression proves
  precedence, exact row/note transition, idempotence, no breadth-close, and no
  raw terminal leakage.
- The scoped diff contains no registry/Fleet/completion/fallback schema drift and
  no out-of-scope files.

## Decision points

No user-facing irreversible decision is required. The design deliberately uses
an additive safe inspection view and compatibility fields; it does not change
the canonical registry, route, completion, or artifact contracts.

## QA handoff

`qa-policy thorough code` reported
`assurance_scope=plan-check:selected-independent-pass:final-verify`, an upper
bound of two deep plus two fast reviewers for the selected pass, and at most two
rounds. Round 1 and round 2 produced the recorded findings. The bounded owner
assignment explicitly classified closure of the round-2 findings as a
correction, not a third independent review, and authorized implementation after
the English/Korean/checklist artifacts were amended. The implementation review
and final verify used the prescribed inline fallback because the same
self-hosting runtime defect made child dispatch unavailable; this is recorded
in `_internal/metrics.md` and no independent delegation is claimed.

## Review round 1 closure map

1. Bounded failure text: Phase 1.1 defines fixed blocker enums, invalid
   `PASS`-with-detail behavior, optional labeled 512-byte excerpts, and exact
   truncation order; Phases 2.1/2.5 constrain receipt/harvest; Phases 1.2,
   3.1, and 3.4 add oversized, multibyte, control, and `PASS` negatives;
   invariants 3/9 and final evidence carry the gate.
2. Artifact root and wire: Phase 1.1 names selected-row worktree plus
   `artifact-root.sh`, pipe-metadata cross-check, no schema column, exact v1
   six-field grammar, enum/exit behavior, and caller decoding rules; Phases
   2.1-2.5 integrate it; Phases 1.2/3.3/3.4 cover linked worktrees, missing or
   mismatched roots, unsafe paths, malformed wire, and mixed harnesses.
3. Real Codex wrapper boundary: Phase 3.1 now invokes the actual foreground
   `dispatch-headless.py --start` entry path with a fake `codex exec --json` for
   all verdicts, captures stdout/stderr/log/registry, and proves positive log and
   artifact retention plus negative parent leakage. Phase 3.2 is supplemental.
4. Guards and rollback: every Phase 1-3 file has an exact pre-edit write command;
   the Verification placeholder is removed; each phase has a focused test gate
   and guarded `apply_patch` rollback limited to that phase's owned files.

## Change history

- 2026-07-22, review round 2 correction: froze every artifact-state token and
  legal wire/exit tuple; normalized all unsafe-root variants; split real-wrapper
  transition evidence from supplemental current/open failure liveness/wait
  evidence; added the named post-exit orphan-reconcile regression; and moved
  negative capture scanning inside the deterministic conformance test.

- 2026-07-22, review round 1: bounded every parent-visible worker-authored
  failure field; froze artifact-root authority and the inspector wire; moved
  Codex isolation proof to the real wrapper boundary; added concrete per-file
  guards, phase gates, rollback boundaries, and positive log/artifact retention
  assertions. `baseline_comparison.md` was left unchanged because the review
  identified no baseline inconsistency.
