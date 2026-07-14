# Thorough independent verification review

> reviewer: separate Codex depth-2 `code-test` headless worker
> independent relative to code-execute: **yes**
> external adversary/depth-3 reviewer: **not claimed**

## Verdict

`RETURN_TO_CODE_EXECUTE`

## Review finding

The implementation passed syntax, 16 focused Phase 2 tests, 8 focused Phase 3
tests, 214 full Fleet tests, and public replay/evaluate behavioral observation.
The first substantive failure occurred at the portable guard level:

```text
BAD codex doctor --runtime should include runtime projection validation
BAD codex doctor --runtime-strict should require and accept complete hook trust
PASS=342 FAIL=2
```

Both doctor captures showed `check=runtime-projection:ok` but also
`check=adaptation-boundary:failed`, producing overall `status=failed`. This is a
blocking repository-boundary regression, not evidence that runtime projection
itself failed. The implementation must return to `code-execute`; no source fix
was attempted by this read-only reviewer.

## Adequacy assessment

Focused coverage is strong for the v2 accounting reducer/store, Phase 1 byte
compatibility, deterministic candidate/evaluator gates, and public CLI output.
However, the required assurance set is incomplete until the adaptation boundary
passes and matrix items 7–15 run successfully. In particular, this pass cannot
sign off the explicit production isolation scan, manifest candidate hash,
canonical/Claude byte parity, Codex symlink, OpenCode defer/absence, standalone
doctor, installed runtime projection, or diff cleanliness checks.

## Required execute follow-up

1. Reproduce the failing adaptation-boundary result outside the doctor wrapper
   and capture its first concrete boundary message.
2. Fix only the owning source/projection contract; do not weaken the doctor or
   portable guard assertions.
3. Return to a fresh code-test pass beginning from matrix item 1, preserving
   stop-on-failure semantics.

No production activation, config mutation, real experiment evidence, adoption,
commit, push, merge, runtime install, or worktree cleanup occurred.
