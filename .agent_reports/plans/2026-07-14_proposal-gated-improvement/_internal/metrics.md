# Execution Metrics

- intensity: standard
- subagent dispatch: not used
- reason: the user did not request subagent work and the active collaboration policy forbids spawning it; schema, CLI, and tests are also boundary-coupled and benefit from one in-context implementation pass
- execution: isolated worktree, inline stage gates
- safety-critical exclusions: runtime homes, plugin caches, generated adapters, hooks, cron, activation
