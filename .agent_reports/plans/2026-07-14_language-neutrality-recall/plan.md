# Language-neutral user output and recall

## Goal

Remove fixed Korean output mandates and phrase-triggered recall behavior while
preserving natural-language usability across runtimes.

## Scope

- Establish an early portable rule: user-facing documents follow the user's
  communication language unless an explicit target audience or artifact
  language overrides it.
- Remove adapter/headless instructions that force Korean output.
- Retire `_RECALL_SIGNAL_WORDS` and the phrase-dependent `explicit` confidence
  path. Automatic recall evaluates every eligible project prompt with one
  content-based threshold; manual intent is expressed by invoking `mem recall`.
- Update memory specification, core contracts, tests, and generated adapter
  projections that encode these invariants.

## Parallel-work boundary

The concurrent runtime-activation session owns `tools/install/**`, `README.md`,
and `INSTALL_LAYOUT.md`. This branch does not modify those paths. Root README
Englishization is deferred until that branch lands.

## Verification

- Memory auto-recall unit and hook contract tests.
- Portable guard and adaptation-boundary tests.
- Native mode/skill/plugin generator `--check` passes after regeneration.
- Static scan finds no fixed Korean response mandate in active bootstrap,
  headless dispatch, or portable role-mode output contracts.

