# Implementation log

## Step 1 — public product surface

- Replaced the generated/dashboard-style root README with a human-owned landing page.
- Preserved the required information order: value, quick install, natural-language examples, benefits, runtime differences, architecture, deep docs, development checks.
- Positioned the product as a portable harness with runtime-specific plugin/installer projections, not as one universal plugin.
- Checked documented installer syntax against local `harness.sh` help before writing examples.

## Step 2 — capability retirement

- Removed `capabilities/sync-skills.md`, both Claude compatibility skill trees, and `skills/.sync_state.json`.
- Removed the catalog and manifest entry.
- Replaced active README/oncall/core/MANUAL/mode/tool/test references with direct deterministic checks or human-review ownership.
- Updated the adaptation boundary to require full Claude compatibility-tree equivalence now that the sync-state exception no longer exists.

## Step 3 — generated projections

- Ran Codex skill/plugin/agent/mode generators.
- Ran OpenCode skill/command/agent generators.
- Ran the Claude plugin generator.
- Rebuilt `manifest.json`.
- Generator pruning removed the retired Codex/OpenCode/plugin surfaces; generator names such as `sync-native-skills.py` remain intentionally active.

## Step 4 — validation-driven corrections

- Fixed `tools/skill-conformance/check.sh` so git root discovery emits one canonical path instead of concatenating the repository root and fallback path.
- Renamed adaptation-boundary temporary output files so the retired capability name no longer appears in active source.
- Added explicit Codex/OpenCode native surface wording required by the projection-summary invariant.

## Source ownership

Source mutation was limited to the execution set plus the three corrections found by the first validation pass. The final test pass was source read-only.
