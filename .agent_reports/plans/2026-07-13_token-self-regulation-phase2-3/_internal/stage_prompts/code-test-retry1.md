# Depth-2 code-test retry 1 — fresh thorough verification

You are the separate deep reviewer/verifier retry after one code-execute
correction. Depth 3 is forbidden. Source is read-only. Do not commit, push,
merge, install runtime projections, mutate config, or touch the main checkout.

Read the full original handoff at
`.agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/_internal/stage_prompts/code-test.md`
and obey its entire v2 assertion set and required 15-item matrix. Also read:

- `test_logs/verification.md` and `_internal/test_reviews/thorough_review.md`
  for the prior stopped pass;
- `dev_logs/correction_01.md` and `_internal/dev_reviews/correction_01.md` for
  the owning correction.

Restart the matrix at item 1. Do not treat earlier PASS results as current
evidence. Run every command once through verification-runner, in order, and
stop on the first substantive failure. For long commands such as
`hooks/portable-guards.test.sh`, capture output to a temporary file from the
initial invocation and return the final summary; do not launch a duplicate
while the first invocation is still running.

Write only fresh retry evidence after explicit preflight:

- `test_logs/verification_retry1.md`
- `test_logs/commands_retry1.log`
- `_internal/test_reviews/thorough_review_retry1.md`

Runtime projection checks remain read-only installed-main wiring evidence and
must not be described as exercising the uninstalled worktree diff. Preserve
the flat component-spec gate limitation, native `apply_patch` target-inference
limitation, OpenCode defer, synthetic/non-evidentiary fixture boundary, pending
adoption, and production dynamic false.

End with `READY_FOR_CODE_REPORT` or `RETURN_TO_CODE_EXECUTE`.
