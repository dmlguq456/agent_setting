# Fleet post-unit migration — final report

## Outcome

Fleet now follows the post-migration portable execution model instead of treating legacy `worker_role` or stage persona as canonical identity. The implementation is integrated on `main` at source commit `a4f7f040`.

## What changed

- All three harness wrappers carry optional units through jobs.log and process environment.
- Fleet collectors and `DispatchJob` preserve that unit independently from assigned contract, worker type, model role, and legacy worker role.
- Immutable route projections retain the sealed unit-catalog digest, composed-route marker, and per-node unit choices in both internal views and JSON.
- Existing contract/stage identity remains primary in display; legacy rows with no unit remain valid.
- Memory write-event documentation now matches the existing `cwd` journal field.
- Canonical Fleet and the Claude compatibility mirror are byte-identical again.
- The existing stage-order layout was intentionally left unchanged after user feedback.

## Verification

- Fleet focused: 225 passed.
- Fleet full after latest-main rebase: 744 passed.
- Wrapper conformance: 39 passed across Codex, Claude, and OpenCode.
- Public JSON smoke, mirror parity, syntax, diff check, and adaptation boundary passed.

Detailed evidence: `test_logs/verification.md`.

## Honest residuals

- Registered Codex headless execution could not be used because the user-owned runtime profile activation is stale/failed; no registered-worker parity claim is made.
- One global portable-guard fixture is stale against the latest model-effort policy (`medium` expected, `high` current) and is outside the Fleet diff.
- Native subagent threads, registered non-interactive workers, Claude background sessions, and agent-team teammates remain distinct runtime surfaces. Claude agent-view collection remains a documented future extension, not part of this migration.

The implementation did not mutate runtime homes or the user-owned stage-dispatch work in progress.
