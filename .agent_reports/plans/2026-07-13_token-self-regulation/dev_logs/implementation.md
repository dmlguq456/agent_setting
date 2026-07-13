# Implementation Log

## `tools/fleet/token_budget.py` and Fleet schema/collectors

**Decision:** Added one shared stdlib parser so Codex Fleet and the policy CLI use the same active-context formula and raw cumulative fields. Legacy `Session.tokens` remains unchanged for render compatibility; new explicit fields prevent cross-harness semantic reuse.

- Codex: `last_token_usage` -> active context, `total_token_usage` -> cumulative counters.
- Claude: current usage -> active context; total input/output -> cumulative counters; unexposed cache cumulative stays `None`.
- OpenCode: latest message prompt -> active context; session table -> cumulative counters.
- Canonical Fleet files were copied byte-for-byte to the Claude mirror.

## `utilities/token-budget.py`

**Decision:** Implemented exact-session observation with three output formats and XDG-only transition state. Unknown, malformed, stale, ambiguous, decreasing, normal, repeated, or native-owned states emit no hook directive; no runtime configuration or transcript is modified. Persisted normal baselines make later cumulative-counter decreases visible in `kv`/`json`, and token-count event time is preferred over file mtime for stale detection.

Transition writes use an atomic, cross-platform lock directory with a bounded wait. State I/O failures are silent fail-open outcomes.

## `core/CONVENTIONS.md` and `core/OPERATIONS.md`

**Decision:** Made the portable contract core-first: token pressure is an output-only axis orthogonal to intensity and cannot reduce dispatch/depth, required stages, QA, safety, input, or guards. This explicitly resolves the research roadmap's unsafe dispatch-suppression suggestion.

## Codex preflight/hook/docs

**Decision:** Added `preflight.sh token-budget` and called its `hook` format from UserPromptSubmit after existing recall/briefing handling. The budget lookup has an independent one-second default timeout (clamped to 0.05–5 seconds), kills its process group on POSIX timeout, and returns no context on failure. The adapter documents native rollout budget as a validated opt-in only because current 0.144.1 rejects the public config path.

## Contract tests

**Decision:** Added focused parser/collector/transition tests plus portable-guard and adaptation-boundary assertions. The hook test proves first-band injection and repeated-band zero output with a synthetic exact-session rollout.

## Independent implementation review

Two read-only reviewers found no P0 blocker and identified four concrete hardening items: persisted counter-decrease visibility, event-time stale detection, bounded prompt-hook execution, and removal of the POSIX-only `fcntl` dependency. All four were corrected before final verification; documentation was also narrowed so only `kv`/`json` are described as read-only while `hook` explicitly owns XDG transition state.
