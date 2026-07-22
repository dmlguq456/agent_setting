# Codex headless parent-context parity — final owner report

## Verdict

**PASS**

The round-2 corrections were incorporated into the English plan, Korean
companion, and checklist before implementation. The refined plan is now
implemented in exactly the 13 assigned tracked files, and all required
executable verification passed.

## Outcome

Codex registered-headless foreground receipt, Python/shared liveness,
synchronous wait, and harvest now share one exact-attempt terminal inspection
contract. Normal parent-facing output contains typed verdict, blocker enum, and
artifact readability/reference metadata without worker transcript or artifact
body content.

The new contract provides:

- closed `codex-terminal-v1` enums and legal tuple/exit matrix;
- fixed unsafe-root handling for relative, over-broad, non-directory, escaped,
  linked-shadow, missing, and mismatched roots;
- strict artifact containment/readability with URL-safe unpadded base64 path
  references for Python callers and no path in the shell wire;
- attempt-id-specific JSONL paths for every new registered attempt, preventing
  a later same-slug retry from satisfying an earlier row;
- default-off, labeled, failure-only blocker/diagnostic excerpts, independently
  control-escaped and capped at 512 UTF-8 bytes without broken characters or
  escape tokens;
- typed PASS/FAIL/BLOCKED/invalid/error liveness and wait output;
- an exact attempt harvest selector for read-only inspection of closed failures;
  and
- preserved PASS completion authority: a textual PASS never closes a row,
  creates a completion marker, or advances a route.

## Lifecycle and isolation proof

The authoritative conformance test launches the real Codex foreground wrapper
with a deterministic fake `codex exec --json` for PASS, FAIL, and BLOCKED.

- PASS remains current/open before and after Python/shared liveness, wait, and
  read-only harvest; no completion marker is created.
- FAIL and BLOCKED are already exact-attempt closed when the wrapper returns and
  remain byte-identical after exact read-only harvest.
- Failure liveness/wait checks use explicitly supplemental controlled open rows
  with byte-identical wrapper-shaped JSONL; they do not reopen or select the
  real closed attempts.
- Exact attempt logs positively retain raw command, prior-agent,
  final-envelope, and stderr sentinels. Artifacts retain their body sentinel.
- The conformance test internally scanned 34 captured parent-facing stdout/
  stderr surfaces before cleanup and found zero raw or artifact-body sentinel
  leakage.

The named `test_codex_terminal_post_exit_orphan_reconcile` regression also
passes. It proves existing orphan precedence over PASS display, exact owner
row/note closure to `dead-parent-orphaned`, sibling byte preservation,
second-run idempotence, no breadth-close, and no raw terminal leakage.

## Verification

Every command required by the refined plan exited 0:

- terminal parser: 11 tests;
- real-wrapper parent conformance: 3 tests and 34 capture scans;
- Codex SD-45: 18 tests;
- registry: 21 tests;
- harvest: 6 tests;
- wait: 11 named checks;
- shared liveness: 22 named checks in the prescribed run, then 23 after the
  final malformed-wire addition;
- progress: 11 tests;
- Codex SD-15: 8 named checks;
- Claude SD-45 comparator: 14 tests;
- Claude SD-15 comparator: 5 named checks; and
- `git diff --check`: clean before and after inline review.

The current final suite totals 131 executable checks (the initial aggregate was
129 before the malformed-wire and same-slug retry cases). The complete suite
passed again under the depth-0 integrating session's bounded verification
runner after correcting one failed write-guard sequence. The
adapter-owned verification runner also compiled all four changed Python source
modules plus the conformance test successfully under a 60-second bound. Full commands, durations, and
evidence are in `test_logs/final_verification.md`.

The optional external `claim-verify` provider was unavailable (exit 69), so no
external-verification claim is made. This does not substitute for or weaken the
recorded local executable gates.

## Scope and assurance

Changed tracked files are exactly:

1. `utilities/codex_dispatch_terminal.py`
2. `utilities/codex_dispatch_terminal.test.py`
3. `adapters/codex/bin/dispatch-headless.py`
4. `adapters/codex/bin/dispatch-liveness.py`
5. `utilities/dispatch-liveness.sh`
6. `utilities/dispatch-wait.sh`
7. `adapters/codex/bin/dispatch-harvest.py`
8. `utilities/dispatch_parent_context_conformance.test.py`
9. `adapters/codex/bin/dispatch-headless.sd45.test.py`
10. `utilities/dispatch-wait.test.sh`
11. `utilities/dispatch-liveness.test.sh`
12. `utilities/dispatch_harvest.test.py`
13. `utilities/dispatch_registry.test.py`

`qa-policy thorough code` reported
`assurance_scope=plan-check:selected-independent-pass:final-verify`, with
reviewer counts as an upper bound. The assigned self-hosting exception made
depth-2 child dispatch runtime-unavailable, so implementation review and final
verification were performed inline. This fallback is recorded in
`_internal/metrics.md`; no independent delegation is claimed.

No core, specification, capability topology, Fleet UI/schema/collector,
Claude adapter, runtime config, credential, completion-marker schema, fallback
ordering, or unrelated file was changed. Depth-0 integrated the scoped source
commit `ab74d676` by fast-forward onto `main`, pushed both the feature branch
and `origin/main`, reran the full suite from the primary checkout, and removed
the eligible linked worktree. No reset, force operation, destructive checkout,
asynchronous monitor, or detached completion promise was used.

## Durable handoff

- Plan correction: `plan/plan.md`, `plan/plan_ko.md`, `plan/checklist.md`
- Implementation decisions: `dev_logs/implementation.md`
- Test evidence: `test_logs/final_verification.md`
- Pipeline summary: `pipeline_summary.md`
- Inline topology exception: `_internal/metrics.md`
