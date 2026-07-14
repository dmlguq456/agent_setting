# Implementation Log

## Context recovery

- Reordered read-only orientation to targeted agent-chosen recall, full record
  lookup when shortened, canonical/legacy artifact root resolution, newest
  report/experiment plus current PRD/spec, then primary code/data.
- Added evidence precedence and drift reporting.
- Kept `analyze-project` limited to absent/stale persistent analysis or an
  explicit refresh request.

## Spectrogram report QA

- Added a versioned JSON schema and fail-closed Python verifier.
- Separated metric and display bands and required exact 48 kHz 0–24 kHz
  metadata, dynamic range, colormap, and shared per-panel vmin/vmax.
- Bound band-sensitive prose to stable claim IDs and range-compatible evidence.
  Full/broadband ranges are derived; high-frequency terms carry an adjacent
  explicit Hz/kHz range matching the manifest.
- Bound visual review to a complete, decodable, CRC-valid PNG SHA-256 and
  reviewer/timestamp/check evidence.

## Runtime realization

- Added `figure-gen --verify-report` to Codex and OpenCode with a separate
  machine-readable `report_tool_contract_check`.
- Updated Claude concrete modes/Skills, generated Codex modes/Skills/plugin,
  and generated OpenCode Skills/commands.
- Added Claude collapsed tool projections and made both installable plugins
  part of the canonical generator.
