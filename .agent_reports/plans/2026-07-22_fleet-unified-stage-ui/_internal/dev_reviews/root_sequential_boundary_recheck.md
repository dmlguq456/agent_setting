# Root adjudication — sequential adaptation boundary recheck

Status: **PASS; the correction worker's boundary FAIL is a concurrency false negative.**

## Cause

The correction worker started `bash tools/adaptation-guard.test.sh` and
`bash tools/check-adaptation-boundary.sh` concurrently. The guard suite is a
negative-sentinel test: it temporarily replaces two adaptation baseline hashes
with `-` and temporarily grows `adapters/claude/CLAUDE.md` by one byte, then
restores the exact pre-test working tree. The concurrent boundary process read
those intentional temporary mutations and reported exactly those three sentinel
failures.

The worker log establishes the overlap: `item_93` (guard) and `item_94`
(boundary) both entered `in_progress` before either completed. The boundary
reported missing hashes and `16385 > 16384`; afterward `item_93` completed with
`working tree restored to pre-test baseline` and `guard green again after
restore`.

## Sequential reproduction

Root reran the gates in one `set -e` shell, in this order, from the task
worktree:

```text
git status --porcelain=v1 > BEFORE
bash tools/adaptation-guard.test.sh
bash tools/check-adaptation-boundary.sh
git status --porcelain=v1 > AFTER
diff -u BEFORE AFTER
```

Observed result:

```text
PASS: all adaptation-guard negative tests
WARN: 130 concrete Claude/model references remain in portable areas.
OK: adaptation boundary checks passed
SEQUENTIAL_BOUNDARY_RECHECK=PASS
```

The before/after status diff was empty. After restoration, the two exemption
rows contain their valid canonical hashes and `adapters/claude/CLAUDE.md` is
5,614 bytes. A separate boundary-only run in the same worktree also exited 0.

## Adjudication

- No source correction is required for this gate.
- The depth-2 execute worker's implementation and its 781/781 Fleet result
  remain valid evidence.
- `execute_fix2_review_correction.md` and `owner_handoff_followup.md` are
  preserved as historical worker outputs, but their adaptation-boundary
  blocker is superseded by this sequential root evidence.
- The next authorized action is the already-required fresh independent
  cross-harness review of the final diff, followed by test/report stages if it
  passes.
