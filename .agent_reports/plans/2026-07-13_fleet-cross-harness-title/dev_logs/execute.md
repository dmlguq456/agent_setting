# Execute log

Implemented F-21 in the canonical fleet and regenerated the Claude fleet mirror.

- neutral `<state>/<harness>/<sid>.json` title state with legacy Claude read fallback
- Codex native title from the newest read-only state DB, with JSONL index fallback
- Claude/Codex transcript normalization and one shared debounced scheduler
- default Haiku no-tools provider plus shell-free custom argv provider
- live-TUI-only spawning; `--json`/`--once` remain snapshot-only
- Claude statusline moved to the neutral state namespace
- INSTALL_LAYOUT provider/state documentation

The first real smoke exposed that `session_index.jsonl` lagged active Codex sessions.
Local runtime inspection found `state_5.sqlite/threads.title` as the current native source;
the implementation and PRD were corrected before final verification.

Latest main (`a2fa614`, Pocock closure) was merged without conflicts and its new
skill-conformance projection remained intact.
