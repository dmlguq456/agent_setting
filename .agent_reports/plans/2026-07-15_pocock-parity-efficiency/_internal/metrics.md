# Execution metrics and topology

## Baseline

- Bootstrap bytes: Claude 11,821; Codex 26,189; OpenCode 17,153; total 55,163.
- Normalized Skill metadata chars: Claude 4,729; Codex native 3,811; Codex plugin 4,351; OpenCode 3,811.
- Existing `skill-conformance` default: root compatibility + Claude native only.
- Existing `context-footprint --strict`: no bootstrap absolute/regression failure.

## Dispatch record

- Codex headless check failed because the installed `$CODEX_HOME` projection targeted the primary checkout rather than the isolated worktree and no native skill links/plugin discovery were available for that worktree.
- OpenCode headless check passed and one depth-1 capability owner was launched.
- The owner ran baseline tests but repeated the same hermetic legacy-root fixture three times. Dispatch-injected `AGENT_ARTIFACT_ROOT` correctly forced the canonical primary artifact root, so the fixture could not observe its temporary legacy root. The worker did not unset the variable and made no implementation progress; it was terminated and the registry row was harvested to prevent further token waste.
- Inline fallback is therefore used for the boundary-coupled core/bootstrap/guard refactor. The failed cross-harness run is retained as evidence for a separate fixture-isolation fix; it is not counted as implementation or savings evidence.

## Measurement rule

Report byte/character deltas only. Do not infer tokens, cache savings, cost, or ROI from static footprint or directive counters. Real savings adoption requires production paired sessions `n>=30`.

## Final static measurement

- Bootstrap bytes: Claude 4,632; Codex 7,646; OpenCode 6,045; total 18,323.
- Bootstrap delta: -36,840 bytes, -66.8% under the same UTF-8 byte metric.
- Normalized Skill metadata: Claude 4,729 (0.0%); Codex native 3,655 (-4.1%); Codex plugin 4,195 (-3.6%); OpenCode 3,655 (-4.1%).
- Current active Codex plugin path surface: 6,565 chars; predicted cachebuster path after reinstall: 6,976 chars. The integrated runtime will instead be reactivated on the common `builder` native profile to remove native+plugin duplication.
- Ordinary/unknown/repeated hook samples: 0 chars. Manual mode/recall diagnostics remain on-demand and are not automatic hook injection.

## Integrated runtime measurement

- Activated profile: `builder` on Claude, Codex, and OpenCode.
- Per runtime: 14 capabilities, 7 portable roles, 26 modes, `freshness=fresh`, duplicate discovery 0.
- Active Codex native discovery: 14 Skill links, normalized metadata 1,946 chars, concrete runtime-path metadata 2,338 chars, duplicate names 0.
- Active Codex custom agents: 8 links (7 profile roles + `memory-scout`); stale legacy `external-adversary` compatibility link removed.
- Codex plugin discovery: inactive; the generated plugin remains a validated distribution artifact, not a second active discovery source.
- Session uptake: Claude and Codex require a new session/reinvoke; OpenCode requires restart. This does not change the verified filesystem projection.

## Static delta interpretation

The repository contains more conformance and measurement code than before, while the always-loaded runtime surface is smaller. Repository bytes, bootstrap bytes, Skill metadata, tokens, cache creation, and billable cost are deliberately separate metrics. No token or cost percentage is inferred here.
