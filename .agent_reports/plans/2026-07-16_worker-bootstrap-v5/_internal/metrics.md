# Execution metrics

- topology: inline capability-owner execution in an isolated worktree
- inline_exception: active runtime policy forbids spawning native subagents unless
  the user explicitly asks; this change also edits the dispatch infrastructure
  that would launch registered workers, so self-hosted dispatch would couple the
  verification target to the executor.
- depth: 0 main + isolated implementation worktree; no depth-3
- savings_claim: none; measure static UTF-8 worker bootstrap bytes only
- runtime_support_target: Claude masked profile supported; Codex/OpenCode checked
  prompt-isolation fallback where project instruction auto-inheritance cannot be
  disabled by a verified runtime contract
