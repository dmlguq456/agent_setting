# Phase 2 dispatch metrics

## Separability and fallback

- Standard QA and stage dispatch were selected from the portable policy.
- `subagent-info --check` passed, but `headless --check` failed because the
  installed `$CODEX_HOME` projection points to the Phase 1 worktree rather than
  this Phase 2 worktree. Every expected worktree-specific harness, Skill, Agent,
  and Mode symlink therefore failed its exact-target check.
- Re-activating the interactive runtime onto an unmerged feature worktree would
  change external session state and blur the Phase 1 active-source boundary.
  The documented manual-main-session fallback is used instead.
- The plan, implementation, test, and report stages remain separately logged;
  implementation keeps one writer because manifest ownership, generated
  projections, activation filtering, and their E2E fixture form one coupled
  schema transaction.

## Result metrics

- canonical entries: 27 capabilities, 8 roles, 26 modes, 5 packs, 3 profiles;
- starter/builder/full capabilities: 6 / 14 / 27;
- starter/full metadata ratio: 22.2%, below the 50% gate;
- portable guard suite: 343 pass, 0 fail;
- runtime/profile matrix: 3 runtimes × 3 profiles in isolated HOME;
- core generator groups: 8, all deterministic and drift-checked.

## Independent review closure

- Two reviewers reported six medium findings across initial and closure passes,
  and no high findings.
- Remediation added activation-aware user-facing verification, per-file mode
  projection, profile/source-preserving duplicate recovery, dry-run scope
  validation, executable test entrypoints, and direct E2E coverage for each.
