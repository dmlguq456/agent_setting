# Depth-2 code-test retry 2 — fresh thorough verification

You are the separate deep reviewer/verifier after two bounded code-execute
corrections. Depth 3 is forbidden. Source is read-only. Do not commit, push,
merge, install runtime projections, mutate config, or touch the main checkout.

Read the full original handoff at
`.agent_reports/plans/2026-07-13_token-self-regulation-phase2-3/_internal/stage_prompts/code-test.md`
and obey its entire v2 assertion set and required 15-item matrix. Also read:

- `test_logs/verification.md`, `test_logs/verification_retry1.md`, and their
  `_internal/test_reviews/` reports for the prior stopped passes;
- `dev_logs/correction_01.md`, `dev_logs/correction_02.md`, and their
  `_internal/dev_reviews/` reports for the owning corrections.

Restart the matrix at item 1. Earlier PASS results are diagnosis only, never
current evidence. Run every command once through verification-runner, in order,
and stop on the first substantive failure. For long commands, capture output to
a unique `mktemp` file from the initial invocation and poll that same process;
never launch a duplicate. In particular, run the full portable guard exactly
once and verify its runtime-projection/doctor capture isolation under the
script's cycle-local `$TMP`.

Write only fresh retry evidence after explicit preflight:

- `test_logs/verification_retry2.md`
- `test_logs/commands_retry2.log`
- `_internal/test_reviews/thorough_review_retry2.md`

Runtime projection checks remain read-only installed-main wiring evidence and
must not be described as exercising the uninstalled worktree diff. Preserve
the flat component-spec gate limitation, native `apply_patch` target-inference
limitation, OpenCode defer, synthetic/non-evidentiary fixture boundary, pending
adoption, and production dynamic false. Report exact counts/hashes/bytes where
the original matrix asks for them.

End with `READY_FOR_CODE_REPORT` or `RETURN_TO_CODE_EXECUTE`.
