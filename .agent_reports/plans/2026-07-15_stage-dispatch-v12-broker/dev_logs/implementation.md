# Implementation evidence

## Result

Implemented SD-51~53 as a harness-neutral, deterministic depth-0 launch broker. Logical `depth=2,parent=<conductor>` remains in the global registry while the broker, not the conductor runtime, owns the target adapter process launch.

## Main changes

- Added `utilities/dispatch-broker.py`: Unix-socket request transport, schema-v1 declarative envelope, allowlisted adapter command construction, atomic request states, immutable terminal states, request/attempt idempotency, broker PID/start-tick/heartbeat/lease/fencing identity, and registry reconciliation.
- Replaced conductor-local target wrapper execution in `stage-dispatch-fallback.py` with broker submission for both same-harness and cross-harness headless hops. Direct recursive executors are disabled by default.
- Bound broker root/instance/jobs identity into route evidence, nested eligibility, all three adapter wrappers, Codex/OpenCode preflight, and Claude projection/docs.
- Root standard+ `--start` prepares the broker before launching the conductor. Descendants may consume the inherited binding but cannot create, rotate, or replace it.
- Added `broker_request_id` to the canonical attempt row and preserved route id/node, logical parent, fallback ordinal, target harness, and attempt id.
- Added fenced restart recovery: a successor instance may recover only a pre-existing exact request from its proven predecessor. A claim-only crash launches once; a post-registry crash reconciles the existing attempt and never relaunches it.

## Regression adjustments

- Updated the legacy concurrency fixture to provide the v11-required inherited global registry and checked nested tuple evidence.
- Classified the broker utilities in Codex/OpenCode projection census and projected them into the Claude utility surface.
- Updated the context-footprint baseline for the intentional broker bootstrap contract text.
- Kept O1 PID/start-tick and harness-aware liveness behavior intact; its conformance test passes.

## Scope boundary

- O2 worker commit ownership: not implemented.
- O3 self-modification stale-digest handling: not implemented.
- No runtime-owned credentials, sessions, caches, databases, or user config were modified.

## Commits

- Source: `8897bf76` (`feat(dispatch): add harness-neutral depth-0 broker`)
- Source branch currentness merge: `fe32d20d`
- Main integration: `70bac6ef`

No independent subagent review is claimed. The session policy prohibited native subagents; this inline exception is recorded in `_internal/metrics.md`.
