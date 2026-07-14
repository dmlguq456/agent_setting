# Plan check — round 1

Verdict: pass with implementation constraints incorporated.

1. **Could cleanup delete unrelated work?** The target must be a registered linked worktree and every destructive gate is per-target. `--all-eligible` still evaluates each target independently; locked/external worktrees remain untouched.
2. **Could a stale jobs row block forever or be erased prematurely?** An open row is reconciled only after clean, merged, pushed, unlocked, and no-active-process gates pass. Otherwise it remains evidence and cleanup blocks.
3. **Could tracked `.agent_reports` in a worker still be mistaken for canonical?** The resolver ignores the worker-local snapshot in Git linked worktrees and derives the primary checkout. A write guard rejects explicit worker-local paths.
4. **Could runtime permissions become too broad?** Claude/Codex receive one `--add-dir`. OpenCode receives an exact canonical-root pattern while preserving user config; no wildcard allow is introduced.
5. **Could hook timing remove work before merge/push?** Hooks are explicitly non-authoritative. Only main/orchestrator calls `--apply` after integration verification and push.
6. **Could cleanup depend on artifact recovery and regress the source-only rule?** No artifact copy/harvest condition exists; durable outputs were canonical from creation.

Residual risk: exact process-cwd discovery is Linux-specific. The implementation must treat unreadable `/proc` entries as unknown only when no exact registered PID exists, document the portability fallback, and fail closed on evidence errors that affect target safety.
