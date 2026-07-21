# Execute stage — blocked before source mutation

## Preconditions and evidence

- Worktree began clean at `d7e5ad35865b77cfa5c05ddf4b3c4dccd87e9c72`; it matched `origin/main`.
- QA policy: `standard/code`, assurance `plan-check:selected-independent-pass:final-verify`.
- Read the assigned plan, checklist, metrics, PRD v20, and terminology audit. The PRD read-marker hook could not write to the read-only `.spec-grounding` mount; the pre-existing immutable route remains the governing evidence.
- Enumerated candidate files and ran `preflight.sh write <file> codex-headless` for every file in commits `7094c92b` and `c95ed391` before attempting their application.
- Confirmed `6b3a34bc` is not an ancestor of the starting HEAD.

## Blocking command

```text
git cherry-pick --no-commit 7094c92b c95ed391
error: could not create sequencer directory '/home/Uihyeop/agent_setting/.git/worktrees/depth1-surface-terminology-remediated/sequencer': Read-only file system
fatal: cherry-pick failed
```

The worktree's gitdir resolves to `/home/Uihyeop/agent_setting/.git/worktrees/depth1-surface-terminology-remediated`; that location is read-only in this worker runtime. No sequencer was created, source files were not changed, and no cherry-pick or merge is in progress. The assigned instruction specifically requires `git cherry-pick --no-commit` before implementation, so substituting manual patch application would violate the stage assignment.

## Required unblock

Run this execute stage in a worktree where its shared git metadata directory is writable (or provide an authorized equivalent that performs the required no-commit candidate application). Then resume from Step 0; no source diff from this stage exists.
