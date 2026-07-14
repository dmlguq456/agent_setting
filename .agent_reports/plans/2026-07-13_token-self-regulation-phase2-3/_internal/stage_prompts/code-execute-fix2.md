# Depth-2 code-execute correction 02 — hermetic portable guard captures

You are the deep maker correction pass after code-test retry 1. Depth 3 is
forbidden. Do not commit, push, merge, install runtime projection, mutate config,
or touch the main checkout.

Read `test_logs/verification_retry1.md`, `commands_retry1.log`, and
`_internal/test_reviews/thorough_review_retry1.md`. The exact failure is a
cross-worktree test-harness race: `hooks/portable-guards.test.sh` uses fixed
`/tmp/codex_rp_*.out` (and related runtime-projection capture names), while a
concurrent `language-neutrality` worktree overwrote them. This made otherwise
valid runtime-projection/doctor assertions fail.

Fix only the owning portable guard capture contract. Move every capture read and
write in the affected runtime-projection/doctor block to that invocation's
already-created unique `$TMP` tree (including context-footprint or adjacent
captures needed for the same block). Do not weaken assertions, mask exit codes,
serialize all worktrees globally, or change production/adapter behavior. Keep
the change mechanical and internally consistent. Explicit preflight before edit.

Add `dev_logs/correction_02.md` and
`_internal/dev_reviews/correction_02.md`; do not edit test evidence or pipeline
summary. Validate through verification-runner:

1. shell syntax;
2. a static scan proving the affected block has no fixed `/tmp/codex_rp` capture;
3. one isolated full portable guard run captured once from its initial command;
4. `git diff --check` and production-dynamic-absent scan.

End with `READY_FOR_CODE_TEST_RETRY` or `BLOCKED_CORRECTION`.
