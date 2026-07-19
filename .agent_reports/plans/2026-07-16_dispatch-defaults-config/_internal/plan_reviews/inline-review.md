# Inline plan-check fallback

## Assurance

Standard code QA requested a selected independent pass under 1x-deep-reviewer+2x-fast-reviewers, final verification, and one round. The immutable stage kernel forbids another worker, so this is an inline fallback and does not claim independent-agent coverage.

## Review

- Every A–D item has a named file, action, and verification step; all explicit exclusions are retained.
- Core contract and SD-48 guidance precede utility changes and form the first commit.
- Worktree/artifact boundaries, worker no-merge/no-push rules, and no-drill scope are explicit.
- Adapter, family, config, bias, and hard eligibility are separated; omitted cells are neutral and OpenCode is excluded automatically.
- g9 owner/child SID contracts differ correctly; stderr-only auth coverage is recognized; fresh supported Codex evidence remains mandatory.
- The plan corrects the stale dispatch-node.py auto-forward premise and records forwarding only as follow-up.
- The exec/review versus canonical topology conflict is resolved explicitly rather than hidden.
- The handoff is sufficient without conversation history.

Verdict: PASS for the code-plan gate, with explicit limitations that independent review was unavailable and primary-home read markers initially could not persist. Neither limitation reduces implementation or verification requirements.
