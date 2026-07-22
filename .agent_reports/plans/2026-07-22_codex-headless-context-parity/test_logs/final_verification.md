# Final verification evidence

All commands ran synchronously from
`/home/Uihyeop/agent_setting-wt/codex-headless-context-parity` on 2026-07-22.

## Prescribed regression run

| Command | Exit | Wall time | Executable evidence |
|---|---:|---:|---|
| `PYTHONPATH=utilities python3 utilities/codex_dispatch_terminal.test.py` | 0 | 1.171 s | 11 tests, OK |
| `python3 utilities/dispatch_parent_context_conformance.test.py` | 0 | 7.155 s | 2 tests, OK; `checked_parent_captures=34` |
| `python3 adapters/codex/bin/dispatch-headless.sd45.test.py` | 0 | 1.648 s | 18 tests, OK |
| `python3 utilities/dispatch_registry.test.py` | 0 | 6.680 s | 21 tests, OK |
| `python3 utilities/dispatch_harvest.test.py` | 0 | 2.355 s | 6 tests, OK |
| `bash utilities/dispatch-wait.test.sh` | 0 | 1.758 s | 11 named checks, PASS |
| `bash utilities/dispatch-liveness.test.sh` | 0 | 5.392 s | 22 named checks, PASS |
| `python3 utilities/dispatch_progress.test.py` | 0 | 0.985 s | 11 tests, OK |
| `bash adapters/codex/bin/dispatch-headless.sd15.test.sh` | 0 | 2.153 s | 8 named checks, PASS |
| `python3 adapters/claude/bin/dispatch-headless.sd45.test.py` | 0 | 0.999 s | 14 tests, OK |
| `AGENT_DISPATCH_ALLOW_NAMESPACED_SPAWN=1 bash adapters/claude/bin/dispatch-headless.sd15.test.sh` | 0 | 2.663 s | 5 named checks, PASS |
| `git diff --check` | 0 | 0.204 s | no whitespace errors |

The initial prescribed aggregate contains 83 Python unit tests and 46 named
shell checks, for 129 executable checks. The final malformed-wire case and the
depth-0 same-slug retry regression added two checks, so the current final suite
contains 131 executable checks. Comparator warnings about cloning an
empty temporary repository were expected fixture setup messages, not failures.

## Post-review rerun

After tightening exact adjacency of the final agent envelope and adding the
malformed-wire case, the affected gates were rerun:

| Command | Exit | Wall time | Result |
|---|---:|---:|---|
| `PYTHONPATH=utilities python3 utilities/codex_dispatch_terminal.test.py` | 0 | 1.194 s | 11 tests, OK |
| `python3 utilities/dispatch_parent_context_conformance.test.py` | 0 | 7.278 s | 2 tests, OK; 34 captures scanned |
| `bash utilities/dispatch-liveness.test.sh` | 0 | 5.422 s | 23 named checks, PASS |
| `git diff --check` | 0 | 0.198 s | clean |

## Depth-0 independent audit and rerun

On 2026-07-23 the integrating session found and corrected two issues before
acceptance: one adapter-test edit had followed a failed core-first write guard,
and slug-only depth-1 JSONL reuse could let a newer retry satisfy an older
attempt row. The test edit was reverted to its baseline and reapplied only after
a successful current-session core read/write guard. All newly registered Codex
attempts now use attempt-id-specific JSONL paths, while the slug-only path
remains a read-only legacy liveness fallback.

Every prescribed command was then rerun through the bounded adapter-owned
verification runner:

| Gate | Exit | Current evidence |
|---|---:|---|
| terminal parser | 0 | 11 tests, OK |
| real-wrapper parent conformance | 0 | 3 tests, OK; 34 parent captures scanned |
| Codex SD-45 | 0 | 18 tests, OK |
| registry | 0 | 21 tests, OK |
| harvest | 0 | 6 tests, OK |
| wait | 0 | 11 named checks, PASS |
| shared liveness | 0 | 23 named checks, PASS |
| progress | 0 | 11 tests, OK |
| Codex SD-15 | 0 | 8 named checks, PASS |
| Claude SD-45 comparator | 0 | 14 tests, OK |
| Claude SD-15 comparator | 0 | 5 named checks, PASS |

The new same-slug regression launches two real foreground wrapper attempts
with one slug and distinct attempt IDs, proves their log paths differ, and
proves exact harvest of the first attempt still reports its original PASS after
the later FAIL attempt completes. The conformance fixture now installs an
isolated temporary Codex runtime projection, so it does not depend on the
interactive session's projection target.

After rebasing onto `bd1ec9b6` and fast-forwarding commit `ab74d676` into
`main`, the same 11 prescribed gates (131 checks total) plus the compile and
diff checks were rerun from `/home/Uihyeop/agent_setting`; every command exited
0. The result was then pushed to `origin/main`.

The adapter-owned verification runner also executed Python compilation with a
60-second bound and reported `status=ok`, `exit_code=0` for:

```text
utilities/codex_dispatch_terminal.py
adapters/codex/bin/dispatch-headless.py
adapters/codex/bin/dispatch-liveness.py
adapters/codex/bin/dispatch-harvest.py
utilities/dispatch_parent_context_conformance.test.py
```

The optional external `claim-verify` provider returned exit 69 with
`claim-verify-provider-unavailable`. This is recorded as an unsupported
runtime-contract detail; no external-verification claim is made, and the local
executable evidence above remains the completion authority for this code task.

## Required behavioral evidence

- Real foreground PASS receipt: typed `valid`/`PASS`/`readable`, exact row open,
  no completion marker.
- Real foreground FAIL/BLOCKED receipts: typed verdicts; only the exact attempts
  close with `dead-worker-fail` / `dead-worker-blocked`.
- Exact logs retain command, prior-agent, final-envelope, and stderr sentinels.
  Validated artifacts retain `ARTIFACT_BODY_SENTINEL`.
- All 34 default parent-facing captures contain none of those sentinels.
- Failure detail appears only under `--failure-detail`; blocker and diagnostic
  excerpts each remain at or below 512 UTF-8 bytes, are control-escaped, and
  report truncation independently. PASS detail requests fail closed.
- Every legal v1 tuple is emitted as one six-field path/free-text-free record.
  Malformed and multiple records are `inspector-wire-invalid`.
- Relative, over-broad, non-directory, symlink-escaped, linked shadow, missing,
  and mismatched roots produce the fixed unsafe-root public outcome. Artifact
  missing and artifact outside-root remain distinct invalid outcomes.
- Linked worktrees resolve the primary canonical artifact root. Mixed-harness,
  legacy, PID, heartbeat, limit/auth, current-row, SD-15, and comparator cases
  remain green.
- `test_codex_terminal_post_exit_orphan_reconcile` proves orphan precedence,
  exact owner-row/note transition, sibling preservation, idempotence, no
  breadth-close, and no raw terminal leakage.
- Same-slug retries receive different attempt-id-bound JSONL paths; exact
  harvest of the older row cannot observe the newer attempt's verdict.
