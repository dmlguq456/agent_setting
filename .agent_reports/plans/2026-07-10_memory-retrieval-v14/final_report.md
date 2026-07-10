# Final Report — Memory Retrieval v14

## Outcome
Unified Memory System now has a low-friction retrieval path and explicit delivery protection across Claude Code, Codex, and OpenCode projections.

## Delivered
- `mem show <id>`, `recall --full`, bounded limits, JSON/no-touch probes, and privacy-preserving telemetry.
- High-confidence project prompt recall without signal-word gating; non-project and untracked sessions no-op.
- Schema v5 delivery states with pending markers, explicit consume, restore, and consumption-time working TTL.
- Project-scoped dedup/upsert and transaction-bound destructive guards for pending handoffs.
- Curator prompt/applier protection, full-body memory-scout guidance, adapter bootstrap parity, and regression coverage.

## Operational Rule
When recall or injection exposes `[pending:<id>]`, read the full record, fulfill and verify the obligation, then run `mem consume <id>`. Retrieval alone never consumes it.
