# Fleet Herdr Tint — Quick Report

> Status: rolled back on 2026-07-19 after user feedback that the rail fallback made
> Fleet's visual design worse. The original panel tint design is restored.

## Rollback

- Reverted the `HERDR_ENV` tint-disable condition.
- Removed the fallback-specific regression tests from the canonical and Claude mirror trees.
- Kept this report as historical evidence; the implementation described below is no longer active.
- Post-rollback verification: full Fleet suite 624 passed; mirror parity passed.

## Route

- Capability: `autopilot-code`
- Mode / QA / intensity: `dev/frontend` / `quick` / `quick`
- Scope: Fleet renderer, Claude Fleet mirror, and focused regression coverage
- Spec verdict: within the existing Fleet fallback contract; no spec change

## Micro-plan and plan-check

1. Gate fixed 256-color panel tints only when `HERDR_ENV` is set.
2. Preserve the existing `_TINT_OK = False` rail-and-gap fallback.
3. Keep the normal 256-color terminal path unchanged.
4. Byte-match the canonical Fleet tree and Claude mirror.

Plan-check answers:

- Herdr only: yes; the new condition is scoped to `HERDR_ENV`.
- Normal terminal tint: preserved and covered by a positive regression test.
- Herdr fallback: `_TINT_OK` remains false, `_TINT_PAIR` remains empty, and the existing
  `▍` assembly path is reused without changing foreground roles.
- Mirror parity: confirmed by `test_mirror_parity`.

## Implementation

- `tools/fleet/render.py`: skip the fixed panel-tint pair initialization in Herdr.
- `tools/fleet/tests/test_herdr_tint.py`: cover both Herdr fallback and normal-terminal tint.
- `adapters/claude/tools/fleet/`: synchronized renderer and test mirror.

The registered quick worker could inspect the task but could not persist core/spec read
markers outside its source-only worktree sandbox. The owner harvested that clean attempt and
performed the same approved quick graph inline after passing the guards from the writable
primary session.

## Verification

- Focused Herdr tint tests: 2 passed.
- Fleet mirror parity: 1 passed.
- Full Fleet suite: 626 passed.
- `git diff --check`: passed.
- Live Herdr pane: restarted Fleet; `▍` fallback rails are visible and captured ANSI contains
  no `48;5;17`, `48;5;94`, or `48;5;235` fixed tint background.
- Inline review: no unrelated renderer behavior, Herdr config, or foreground palette changed.
  An independent reviewer was unavailable after the registered worker's guard-marker failure,
  so no independent-review claim is made.
