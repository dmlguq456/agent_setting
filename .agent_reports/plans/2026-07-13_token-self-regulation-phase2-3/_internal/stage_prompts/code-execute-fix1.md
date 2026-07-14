# Depth-2 code-execute correction handoff — portable boundary failure

You are a deep maker correction pass for the existing thorough Phase 2/3 cycle.
Depth 3 is forbidden. Work only in this worktree. Do not commit, push, merge,
install runtime projections, mutate runtime config, or touch the main checkout.

Read the plan, checklist, implementation log/review, and the failed independent
test evidence:

- `.agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/test_logs/verification.md`
- `.agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/test_logs/commands.log`
- `.agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/_internal/test_reviews/thorough_review.md`

The first blocking failure is exact:

```text
BAD codex doctor --runtime should include runtime projection validation
BAD codex doctor --runtime-strict should require and accept complete hook trust
PASS=342 FAIL=2
```

Both doctor captures had `check=runtime-projection:ok` and
`check=adaptation-boundary:failed`, so diagnose the standalone boundary failure
and repair only its owning source/projection contract. Do not weaken, skip, or
rewrite the doctor/portable guard assertions to accept a failure. Preserve every
Phase 2/3 contract and all source already passing 16 + 8 + 214 tests.

Ownership: source/projection/docs/tests as narrowly required, plus a new
`dev_logs/correction_01.md` and `_internal/dev_reviews/correction_01.md`; update
implementation/checklist status only if necessary. Do not alter test logs or
pipeline summary. Explicit write preflight before edits. If native `apply_patch`
target inference fails after preflight, record and use the documented shell
`apply_patch` fallback.

Reproduce using verification-runner. After the fix, run only correction-focused
sanity sufficient to hand back to a fresh full test pass:

1. standalone `bash tools/check-adaptation-boundary.sh`;
2. `python3 tools/build-manifest.py --check` if projection/manifest changed;
3. focused portable guard or the smallest exact doctor-runtime fixture if
   available; otherwise full `bash hooks/portable-guards.test.sh`;
4. `git diff --check`;
5. explicit production-dynamic-absent scan.

Do not claim the full verification matrix; a fresh independent code-test pass
will restart at item 1. End with `READY_FOR_CODE_TEST_RETRY` or
`BLOCKED_CORRECTION`.
