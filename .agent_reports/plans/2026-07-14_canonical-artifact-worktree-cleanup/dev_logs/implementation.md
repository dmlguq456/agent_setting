# Implementation log

- Added `utilities/artifact-root.sh` as the single canonical resolver. An
  explicit absolute override wins; Git linked worktrees resolve the primary
  checkout; legacy and non-Git fallbacks remain supported.
- Changed artifact/spec guards and harness status to use physical canonical
  paths. Worker-local `.agent_reports/**` and `.claude_reports/**` writes now
  fail closed, including `_internal` paths.
- Claude and Codex dispatch use one canonical `--add-dir`; OpenCode merges exact
  canonical-root `permission.external_directory` allow rules into existing
  config. All three inject `AGENT_ARTIFACT_ROOT` and record it in prompts and
  jobs metadata.
- Added `utilities/worktree-cleanup.py` with dry-run default, no force, branch
  retention, merge/upstream/process/dirty/lock gates, stale registry
  reconciliation, bounded audit, and registry-scoped `--all-eligible`.
- Added Claude/Codex/OpenCode cleanup entrypoints, harvest guidance, adapter
  docs, selective utility projections, and generated Claude plugin utility
  bundling.
- Source commit: `81ba517b`. It was merged with current `origin/main` as
  `dadf5e1c`, fast-forwarded into main, and pushed.
- The feature worktree was removed through the new guarded apply path. The
  `canonical-artifact-cleanup` branch was retained. Two unrelated worktrees
  were inspected and preserved because both were unmerged.
