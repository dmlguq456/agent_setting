# Pipeline Summary

## 2026-07-14

- Added a component blueprint for context recovery and spectrogram report QA.
- Kept self-edit and autonomous setting mutation out of scope per user direction.
- Grounded the contract in existing reports, full memory records, the current
  memory PRD, current runtime documentation, and live adapter projections.
- Implemented recall-first orientation with full-record lookup and explicit
  precedence/drift reporting without routing read-only recovery to
  `analyze-project`.
- Added a versioned fail-closed spectrogram manifest/verifier, 29 unit
  regressions, adapter-wrapper integration, claim-to-range validation, full
  PNG integrity checks, and hash-bound representative visual review.
- Synchronized Claude, Codex, OpenCode, and installable Claude/Codex plugin
  projections. `tools/generate.py` now includes plugin generation/checks.
- Independent semantic review found and drove closure of multiple false-pass
  paths; the final recheck reported no remaining P1/P2 issue.
