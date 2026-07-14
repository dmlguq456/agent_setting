# Metrics and dispatch exception

- intensity: strong
- execution: inline in one isolated source worktree
- `STAGE_DISPATCH_INLINE_OK`: yes
- reason 1: this change modifies the dispatch/worktree infrastructure that would otherwise launch its own stage workers, so execution and its bootstrap boundary are non-separable.
- reason 2: the active system/developer contract forbids spawning subagents unless the user explicitly requests delegation; the user requested the harness change, not subagent use.
- artifact ownership: all plan/spec/test/report writes remain in `/home/Uihyeop/agent_setting/.agent_reports`; the implementation worktree receives source writes only.
- runtime lifecycle: destructive cleanup remains main/orchestrator-owned, not hook-owned.
