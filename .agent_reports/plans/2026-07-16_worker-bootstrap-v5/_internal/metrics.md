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
- worker_bootstrap_bytes: kernel=1571, owner=2028, stage=1906, review=1878,
  support=1862
- implementation_commits: b915b699, 9bc65481; integrated by main merge
- relevant_gates: typed renderer/custom prompt/dispatch route/artifact root,
  profile builder+activation, generated projections, Skill conformance,
  adaptation boundary, strict context footprint, Codex/OpenCode runtime doctor
- preexisting_gate: `tools/routing-contract.test.sh` has the same three failures
  on pre-change main (compact Codex lab/refine projection and Claude bootstrap
  wording); no worker-bootstrap assertion failed.
