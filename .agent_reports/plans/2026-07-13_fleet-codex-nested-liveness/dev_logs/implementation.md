# Implementation log

## Diagnosis

The live depth-2 Codex process wrote its rollout under:

`<worktree>/.dispatch/codex-home/sessions/...`

Both Fleet and `dispatch-liveness.py` searched only the caller's default `~/.codex/sessions` for non-profile jobs. The rows were therefore marked dead and then hidden by dead-row folding.

## Change

- Added a deterministic worktree-local session candidate for non-profile Codex jobs.
- Kept profile jobs restricted to `.dispatch/homes/<slug>.<profile>/sessions`.
- Chose the newest worktree-matching rollout across candidate stores.
- Mirrored canonical Fleet changes into the Claude adapter projection.
