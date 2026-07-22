---
status: complete
created: 2026-07-22
review_source: round_1.md
---

# Refinement record — round 1

## Result

Revised `plan/plan.md`, `plan/plan_ko.md`, and `plan/checklist.md` in place.
`baseline_comparison.md` was not changed because the review identified no
baseline inconsistency. No source, spec, core, registry, runtime configuration,
or tracked worktree file was edited.

## Must-fix mapping

1. Bounded failure text → primary/Korean Phase 1.1, 1.2, 2.1, 2.5, 3.1, 3.4,
   Safety invariants 3/9, Verification evidence, and checklist Phases 1-3. The
   default is a fixed blocker enum; optional failure fields are labeled,
   control-escaped, independently capped at 512 UTF-8 bytes, multibyte-safe, and
   impossible on `PASS`. `PASS` with a non-`none` blocker is invalid.
2. Artifact-root and wire grammar → Phase 1.1 fixes selected-row worktree plus
   `utilities/artifact-root.sh` as authority, retains pipe metadata only as a
   cross-check, adds no registry column, forbids shadow fallback, and freezes one
   six-field `codex-terminal-v1` enum record with explicit 0/2/3/4/64 behavior.
   Phase 1.2/3.3/3.4 and the checklist name linked-worktree, missing/mismatched
   root, unsafe path, malformed/multiple wire, and mixed-harness fixtures.
3. Real Codex wrapper boundary → Phase 3.1 now requires the actual foreground
   `dispatch-headless.py --start` subprocess with deterministic fake
   `codex exec --json` for `PASS`/`FAIL`/`BLOCKED`, captured wrapper streams,
   exact JSONL, registry before/after, positive log/artifact retention, negative
   parent leakage, and exact row-transition assertions. Renderer cases remain
   supplemental in Phase 3.2.
4. Guards and rollback → exact `preflight.sh write <path> codex-headless`
   commands precede every planned file's first edit. The Verification placeholder
   was removed. Each phase now has a focused test gate and guarded, phase-owned
   `apply_patch` rollback boundary that forbids reset/checkout and unrelated-file
   changes.

## Assurance and checks

- `preflight.sh qa-policy thorough code` reported
  `assurance_scope=plan-check:selected-independent-pass:final-verify`,
  `max_round=2`, with reviewer counts as an upper bound for the selected pass.
- Source seams were re-read only to remove ambiguity exposed by the review:
  `utilities/artifact-root.sh`, the Codex terminal parser and its callers, the
  foreground wrapper path, liveness/wait, harvest, and existing fake-Codex
  foreground fixtures.
- Artifact consistency checks must confirm that the English primary, Korean
  companion, and checklist all contain the same four corrections, exact file
  scope, phase gates, and no baseline edit.
- Unsupported runtime-contract detail: none. This stage produced plan artifacts
  only and made no claim that implementation tests already pass.
