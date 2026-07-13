# Execution metrics / dispatch fallback

- requested topology: `standard`, depth-1 Codex capability owner with stage dispatch.
- headless contract result: unavailable because runtime projection check reported `check=hooks-json:failed reason=not-harness-hook-projection` while all skill/agent/mode links were otherwise present.
- fallback: `autopilot-code` documented `manual-main-session-or-report-unavailable`; execute the same ordered stages in this isolated worktree.
- separability: plan/execute/test/report artifacts remain path-separated, but no child stage can be launched under the failed headless contract. This is a runtime fallback, not an SD-17 semantic non-separability exemption.
- excluded runtime work: repairing installed Codex hooks, Codex liveness, and child Git index permissions.
- qa-policy: `standard code` requested 1 deep + 2 fast independent reviewers; headless unavailable, so the documented inline-review fallback was used and independent QA is not claimed.
- verification note: two first-pass shell assertions failed because of local quoting/escaping in the test command; corrected assertions passed. No source regression was involved.
