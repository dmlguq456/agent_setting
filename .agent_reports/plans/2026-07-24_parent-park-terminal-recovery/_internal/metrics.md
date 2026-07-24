# Execution metrics and exceptions

- intensity: strong (previously approved scope continuation)
- execution: inline self-repair exception
- reason: the defect is the registered parent-parking hook itself. The current session and the previously completed worker both reproduced a recovery-free terminal-unverifiable lock before any source/preflight/git access. Starting another registered owner would exercise the broken mechanism and cannot repair the installed hook. The operator restarted this session with `AGENT_PARENT_PARK_BYPASS=1` explicitly.
- `STAGE_DISPATCH_INLINE_OK=1` is limited to this dispatch-infrastructure self-modification cycle.
- assurance compensation: core-first spec transaction, historical diff review, completion-surface matrix, focused hook/join/wait/cleanup regression, portable boundary checks, integrated-tree verification.
- no registry row was manually rewritten and no unverifiable process was assumed dead.
- spec transaction: route `rt-8d1d633110f89e31`, lock-acquired next-version 25; historical v25 and pre-v27 v26 snapshots recovered, current component advanced atomically to v27/SD-83.
- implementation surface: core contract 2 files, Codex adapter contract 2 files, hook 1 file, focused fixture 1 file. Shared quiescence classifier, join, wait, fallback, governor, cleanup, registry, and native-subagent code were not changed.
- portable guard comparison: source branch and pre-change main both `PASS=327 FAIL=29`; the 29 failure descriptions are byte-identical and all predate this diff, so new portable regressions = 0.
- integration: source `a9462fc1` fast-forwarded to main. Installed runtime projection and strict hook trust both report `ok`; an actual current-session PreToolUse probe with `AGENT_PARENT_PARK_BYPASS` removed returned exit 0 with empty stdout/stderr.
- cleanup: guarded check `eligible`, apply `removed`; active PID 0, stale registry row 0, registry rewrite 0, source branch retained.
