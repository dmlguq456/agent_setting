---
title: Canonical artifact root and guarded worktree cleanup
status: completed
intensity: strong
spec: ../../../spec/stage-dispatch/prd.md
---

# Plan

## Outcome

Worker worktrees become source-only execution surfaces. All durable agent artifacts route to the primary checkout's canonical artifact root, worker-local artifact writes fail closed, and main/orchestrator can automatically remove only worktrees proven clean, merged, pushed, unlocked, and inactive.

## Steps

1. Update the portable core contract for canonical artifact ownership and post-integration cleanup authority.
2. Implement one shared artifact-root resolver and wire status/spec gates/write guards to it with physical absolute path normalization.
3. Inject the canonical root and narrowly scoped external-write access in Claude, Codex, and OpenCode dispatch wrappers.
4. Implement a dry-run-first cleanup state machine with registry reconciliation, branch preservation, and bounded audit logging.
5. Project adapter entrypoints from core/capabilities, regenerate derived assets, and run unit, integration, boundary, manifest, doctor, and runtime projection checks.
6. Commit/push the feature branch, integrate through main after review, verify the integrated tree, push main, then dogfood cleanup on the feature worktree.

## Safety

- Never remove the primary worktree, a dirty/locked/unmerged/unpushed worktree, or a worktree with an active exact PID/process cwd.
- Never use `--force` and never delete the branch by default.
- Never infer merge/push completion from SessionEnd/Stop/session.idle.
- Never depend on copying or harvesting worktree-local agent artifacts.
- Preserve unrelated user/external worktrees.

## Verification

- Resolver unit cases: explicit override, main, linked worktree, legacy, non-Git.
- Guard cases: canonical allowed, linked-local denied, non-artifact unaffected.
- Dispatch cases: env/metadata plus Claude/Codex `--add-dir`, OpenCode scoped external permission.
- Cleanup fixture matrix: eligible remove/branch retained; dirty, unmerged, locked, active, primary, and push-pending blocked; stale registry reconciliation only after all gates.
- Portable guard, adapter invariant/generation/boundary checks, shell/Python syntax, doctor/runtime projection.
