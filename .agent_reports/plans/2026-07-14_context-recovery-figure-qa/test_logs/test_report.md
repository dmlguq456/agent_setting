# Test Report

## Semantic verifier unit/regression

- Command: `python3 tools/figure-semantic-verify.test.py`
- Verdict: PASS — 29 tests.
- Coverage includes low-band metric/display independence, 1 kHz display,
  missing metadata, unequal scales, unsupported and unregistered claims,
  contradictory full-band ranges, adjacent high-frequency ranges, Nyquist
  bounds, stale review hashes, malformed paths/IDs, duplicate JSON fields,
  truncated/CRC-invalid/palette-invalid PNGs, and non-rendered Markdown links.

## Adapter integration and projections

- `tools/generated-projections.test.sh`: PASS, including Codex/OpenCode wrapper
  positive fixtures and `max_hz=1000` negative fixtures with exit 2.
- `python3 tools/generate.py --check`: PASS — 10 projection groups.
- Codex and Claude `sync-native-plugin.py --check`: PASS.
- `tools/check-adaptation-boundary.sh`: PASS with the repository's documented
  compatibility-reference warning only.
- `tools/skill-conformance/check.sh`: PASS.
- Shell syntax, JSON schema parse, compatibility-file byte parity, and
  `git diff --check`: PASS.

## Representative figure

- Codex and OpenCode `figure-gen --verify-report`: PASS on the recorded
  manifest/report/PNG.
- Manual original-detail inspection: PASS after correcting first-pass title
  and axis-label clipping. See `visual_review.md` and the hash-bound manifest.
- Local matplotlib contract: unavailable (exit 69); the evidence PNG was
  generated with the recorded Pillow fallback. This was reported, not treated
  as a matplotlib pass.

## Independent review

- Final adversarial recheck: PASS — no remaining P1/P2 false pass or crash.
