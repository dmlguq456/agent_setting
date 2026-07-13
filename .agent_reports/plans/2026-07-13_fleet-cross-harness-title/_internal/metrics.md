# Execution metrics

- intensity: strong
- topology: inline
- separability: non-separable
- reason: title identity (`harness + sid`), state path, precedence, scheduler lock,
  collector assignment, and regression fixtures share one boundary contract. Splitting plan,
  implementation, and verification into independent stage sessions would duplicate and race the
  same API anchors. The implementation remains isolated in its own worktree and keeps source
  mutation in one session.
- start_head: 016a883e25ca7ec566d62f06768344067ab8e25e
