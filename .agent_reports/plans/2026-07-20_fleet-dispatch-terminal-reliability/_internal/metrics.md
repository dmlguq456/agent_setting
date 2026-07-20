# Cycle Metrics

- capability: `autopilot-code`
- mode: `debug`
- intensity: `strong`
- derived rigor: `standard`
- spec-significance: `within-spec`
- execution: `inline exception`
- exception: This cycle modifies the registered headless dispatch, watchdog,
  fallback, and liveness machinery that would otherwise execute its own stages.
  Re-entering the known-broken self-hosted path could create duplicate or stale
  attempts. `STAGE_DISPATCH_INLINE_OK` is therefore asserted for this cycle;
  independent assurance is supplied by hermetic fixtures and the full relevant
  test suites.
- Herdr input: used the investigation's registered-dispatch versus in-session
  activity separation; did not duplicate its separately owned cross-capability
  DAG/process-view work.
- verification:
  - Fleet canonical full suite: `720 passed`
  - Fleet Claude-mirror focused suite: `114 passed`
  - dispatch registry/liveness suite: `18 passed`
  - route/contract group: `62 passed`
  - progress/fallback/completion/registry group: `56 passed`
  - adapter/foreground/SD-15 group: `33 passed`
  - `git diff --check`: passed
  - Fleet live `--once` smoke: passed
  - live agent-note default view: depth-2 `exec` visible, parent `exec` active
  - full-drill conformance pre-stage Fleet regression: passed
  - adaptation boundary: passed
  - runtime doctor/projection: passed
