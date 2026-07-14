# Context Recovery and Spectrogram Report QA — PRD

> mode: library + cli · date: 2026-07-14 · status: approved by user request

## 1. Problem

A context-recovery request ignored existing reports, memory, and the current
spec, then reused a 20–1000 Hz metric crop as a report spectrogram display.
The report called the resulting 0–1 kHz image full-band, while verification
checked only file existence, dimensions, count, and links.

## 2. Context-Recovery Contract

Read-only orientation uses this order before capability routing:

1. Run a targeted, agent-chosen memory recall for the current judgment. When a
   result is a snippet, immediately read its full body by record ID.
2. Resolve the existing artifact root: `.agent_reports/` first; use
   `.claude_reports/` only when `.agent_reports/` is absent.
3. Read the newest relevant report or experiment artifact and its current
   PRD/spec or experiment contract.
4. Inspect primary code, data, and raw logs only for unresolved questions.

`analyze-project` is eligible only when persistent analysis is absent,
demonstrably stale for downstream work, or explicitly requested by the user.
Read-only orientation never creates or refreshes analysis by itself.

When inputs conflict, apply this evidence precedence and warn about drift:

1. latest spec or explicit user confirmation;
2. durable project fact;
3. latest experiment contract;
4. legacy document.

Memory remains navigation and continuity evidence. Current targets must be
opened before a remembered summary is treated as current fact.

## 3. Spectrogram Contract

Analysis and presentation ranges are independent named values. A report figure
script must not derive its display range from a metric crop:

```python
METRIC_BAND_HZ = (20, 1000)
FIGURE_BAND_HZ = (0, 24000)
```

Every report spectrogram is registered in a versioned JSON manifest with
`sample_rate_hz`, `min_hz`, `max_hz`, `dynamic_range_db`,
`shared_scale_per_figure`, `colormap`, figure/group IDs, generated PNG path,
and explicit per-panel `vmin_db`/`vmax_db`. The schema rejects unknown versions
and wrong field types. Equal panel scales and the declared dynamic range are
verified rather than inferred from the `shared_scale_per_figure` flag alone.

The 48 kHz report profile is fail-closed at `sample_rate_hz=48000`,
`min_hz=0`, `max_hz=24000`, and `shared_scale_per_figure=true`.
Missing or mismatched metadata blocks completion.

## 4. Claim–Evidence Gate

Band-sensitive report claims are registered in the same manifest. Each claim
records normalized report prose, a stable hash-derived ID, a closed semantic
type, and cited figure or metric evidence IDs. The verifier derives — rather
than trusts — the required range for full-band and broadband claims as 0 Hz
through Nyquist. High-frequency claims must attach an explicit Hz/kHz range to
the high-frequency term in report prose and declare the identical manifest
range. Every
cited evidence range must contain the derived range. Markdown prose is
normalized across line wrapping, and the whole report is scanned so an
unregistered band-sensitive sentence fails closed.

A low-band metric may coexist with a full-band figure, but it cannot be cited
as evidence for a claim outside the metric range.

## 5. Visual Review Evidence

After generation, at least one representative PNG per report figure group is
opened and inspected. Evidence records the reviewed PNG, its SHA-256 hash,
reviewer/tool, timestamp, an evidence note, and affirmative checks for 0–24 kHz
y-axis, ticks, colorbar, common scale, and readable labels. A changed PNG makes
the hash stale and invalidates the review. A missing PNG, missing review field,
or negative check blocks completion.

## 6. Runtime Projection

Portable meaning lives in core, capability, role, and portable tool sources.
The portable role mode projects into the generated Codex mode; Claude's
concrete figure mode receives the relevant invariant without erasing its
adapter-specific choices; OpenCode exposes it through its mode map and
figure-generation wrapper. Unsupported runtime mechanics fail with an explicit
fallback. Generated adapter files are regenerated and checked for drift.

## 7. Acceptance

- Existing-report orientation does not select `analyze-project`.
- A 20–1000 Hz metric leaves the report figure at 0–24 kHz.
- Missing metadata or a non-24 kHz display fails verification.
- A band claim unsupported by its figure or metric fails verification.
- A representative PNG has recorded visual-review evidence.
- Unit/integration tests and adapter invariant checks pass.
