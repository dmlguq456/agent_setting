# dispatch-defaults-config checklist

## Core-first safety commit

- [x] Re-read PRD v16 §13.8 and core/OPERATIONS.md §5.10; record marker limitations.
- [x] Run preflight write guards before every source edit.
- [x] Add SD-16 defaults consumption and SD-48 no-reconfirmation/current-record-path guidance.
- [x] Relax only the g9 depth-1 owner SID; preserve exact child SIDs.
- [x] Add the runtime-parent prompt clarification and sync both mirror files.
- [x] Run bash -n, targeted SID checks, mirror cmp, and git diff --check.
- [x] Create the core-first safety/contract commit. (efeab72e)

## Implementation commit

- [x] Add profiles/dispatch-defaults.yaml with schema comments, full coordinate scaffold, owner set, relief policy, canonical grounded defaults, and omitted plan/unsupported cells.
- [x] Add strict standard-library utilities/dispatch-defaults.py validation, affinity lookup, and policy queries.
- [x] Replace selector affinity heuristics while preserving role logic, cascade order, hard eligibility, traces, and OpenCode default exclusion.
- [x] Convert selector tests to temporary fixture configs and cover valid, omitted, diverse, precedence, owner, relief, malformed, and read-only cases.
- [x] Confirm the stderr-only Codex auth regression remains present; do not duplicate it.
- [x] Create the implementation commit after verification. (7697c3b6)

## Test-stage gate (not this stage — code-test owns these; left unchecked for that stage)

- [ ] Run Python compile/validation/query checks from the task worktree.
- [ ] Run selector syntax and fixture suites from the task worktree.
- [ ] Run the nested-eligibility unit suite from the task worktree.
- [ ] Record a fresh live Codex child eligibility JSON probe and require status=supported.
- [ ] Run applicable adaptation-boundary, diff, status, and scope checks.
- [ ] Confirm no g9/g10 drill, primary-checkout write, or worktree-report write occurred.
- [ ] Record commands/results/warnings in canonical test artifacts.
- [ ] Hand off without merge, push, or cleanup.

