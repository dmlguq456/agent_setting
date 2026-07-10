# Implementation Log

## Notes

- Existing pattern reused: `spec-read-marker.sh` records actual PRD reads; `spec-skill-gate.sh` denies spec-changing work when the marker is absent or stale.
- New guard follows the same shape for adapter edits: actual `core/*.md` read marker first, adapter write guard second.
- Claude audit found that live `~/.claude/settings.json` lacked the new hooks; merged only the two hook entries into live settings and preserved the local `model`/`effortLevel` values. Backup: `~/.claude/settings.json.bak-core-first-20260703-190554`.
- Claude audit also found a fail-open for non-existent adapter subdirectories; `core-first-guard.sh` now resolves from the nearest existing ancestor directory and the portable guard test covers that path.
- Added `.core-grounding/` to `.gitignore` to keep session markers out of commits.
