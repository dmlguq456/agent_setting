# Thorough Independent Verification Review — Retry 1

> reviewer: separate Codex depth-2 code-test headless worker
> independent relative to code-execute: **yes**
> external adversary/depth-3 reviewer: **not claimed**

## Verdict

RETURN_TO_CODE_EXECUTE

## Review finding

The corrected implementation freshly passed syntax, 16 focused Phase 2 tests,
8 focused Phase 3 tests, 214 Fleet tests, and deterministic public replay/evaluate
observation. The first substantive failure was matrix item 6:

    BAD codex check-runtime-projection should reject miswired skill and agent links
    BAD codex doctor --runtime should include runtime projection validation
    PASS=342 FAIL=2

The failed assertions read fixed global /tmp/codex_rp_bad.out and
/tmp/codex_doctor_runtime.out captures. Those files contained paths from the
separate language-neutrality worktree, not this assigned worktree. This makes
the portable guard non-isolated under concurrent worktree verification and
invalidates the two affected assertions. The correction should move the fixed
capture paths under the script's existing unique $TMP directory (or an
equivalent run-unique namespace) while preserving all assertions.

## Adequacy assessment

The focused v2 coverage remains strong for content-free exact-session
accounting, Phase 1 byte/zero compatibility, frozen offline forecast behavior,
strict paired evaluation, deterministic bootstrap, pending adoption, synthetic
fixture boundary, and production false. It is not adequate for final sign-off
because the matrix stopped at item 6. Items 7–15, including standalone boundary,
manifest, repository doctor, installed-wiring read-only checks, diff check,
production isolation scan, mirror/hash/symlink verification, and OpenCode defer,
must run in a fresh retry after the guard's temporary-output collision is fixed.

## Required execute follow-up

1. Replace the runtime-projection/doctor assertion captures in
   hooks/portable-guards.test.sh with per-run $TMP paths.
2. Keep the negative miswire and doctor assertions unchanged in meaning; do not
   mask failures or relax exit/status expectations.
3. Request a new independent code-test retry beginning at matrix item 1.

No source fix, production activation, real experiment evidence, adoption,
runtime installation/config mutation, commit, push, merge, or worktree cleanup
was performed by this reviewer. The flat component-spec gate limitation and
native apply_patch target-inference limitation remain documented Codex
limitations, not pass evidence.
