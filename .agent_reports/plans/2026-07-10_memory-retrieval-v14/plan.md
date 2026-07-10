# Memory Retrieval v14 — Implementation Plan

## Evidence
- Claude Code/Codex concurrent diagnosis: prompt auto-recall did not fire during ordinary project work; SessionStart omitted records were reachable only by manual recall; snippet-only output forced direct DB/dump reads.
- Agent-memory forensic: commit `55076af` contained canonical handoff plus two unique supplements; `042d277` removed both supplements while canonical strength changed `1→3`. Graveyard bodies match the current merge path, confirming destructive near-duplicate misclassification.

## Plan
1. Extend schema v4→v5 with monotonic `delivery_state`; preserve it through add/upsert/export/import and protect pending records from every destructive path.
2. Add `show`, `recall --full/--limit`, `consume`, and `restore`, with one shared visibility fence and explicit consumption only.
3. Replace the signal-word-only hook with shared high-confidence auto-recall probing, no-touch candidate inspection, capped injection, and raw-prompt-free telemetry.
4. Synchronize portable memory contract, runtime projections, curator prompts, README, and memory-scout guidance.
5. Run focused migration/retrieval/handoff/auto-recall tests, existing memory/hook regressions, adapter boundary checks, and an independent review.

## QA
- Level: `standard`.
- Required regressions: v4 migration and old dump import; pending prune/merge/delete/lifecycle refusal; consume then mutation; show/full visibility and non-consumption; real merge-incident fixture; ordinary prompt hit/generic prompt no-op; no-touch access timestamp; Claude/Codex/OpenCode shared hook path.
- Final gates: `mem.py` compile, focused suites, portable guards, manifest/adaptation boundary, Codex doctor/runtime projection where non-mutating.
