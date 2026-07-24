# Execution metrics and exceptions

- intensity: strong (previously approved scope continuation)
- execution: inline self-repair exception
- reason: the defect is the registered parent-parking hook itself. The current session and the previously completed worker both reproduced a recovery-free terminal-unverifiable lock before any source/preflight/git access. Starting another registered owner would exercise the broken mechanism and cannot repair the installed hook. The operator restarted this session with `AGENT_PARENT_PARK_BYPASS=1` explicitly.
- `STAGE_DISPATCH_INLINE_OK=1` is limited to this dispatch-infrastructure self-modification cycle.
- assurance compensation: core-first spec transaction, historical diff review, completion-surface matrix, focused hook/join/wait/cleanup regression, portable boundary checks, integrated-tree verification.
- no registry row was manually rewritten and no unverifiable process was assumed dead.
- spec transaction: route `rt-8d1d633110f89e31`, lock-acquired next-version 25; historical v25 and pre-v27 v26 snapshots recovered, current component advanced atomically to v27/SD-83.
