# Metrics and orchestration notes

- intensity: strong (shared dispatch/security/lifecycle contract)
- topology: isolated worktree, main-session implementation
- inline exception: runtime policy for this session forbids spawning sub-agents; dispatch infrastructure self-modification also couples broker/client/preflight acceptance anchors. Work remains isolated in its own worktree and receives explicit staged review/test evidence.
- starting source head: `edb29709`
- O2/O3 source changes: forbidden in this cycle
- source commit: `8897bf76`
- main integration commit: `70bac6ef`
- verification: broker 10/10; portable guards 359/359; adaptation boundary/runtime projection PASS
- independent reviewer: not used and not claimed (session native-subagent policy)
