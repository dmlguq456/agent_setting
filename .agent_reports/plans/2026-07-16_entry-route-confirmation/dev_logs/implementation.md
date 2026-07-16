# Implementation Log

## 2026-07-16

- Recovered the existing v3 skill-design spec and snapshotted it.
- Upgraded the component spec to v4 with the route-confirmation contract.
- Confirmed current manifest, adapter generators, conformance registry, and
  context-footprint behavior before editing.
- Recorded inline execution as the required topology exception for this run.
- Added `WORKFLOW §0.4` and aligned the portable response, autonomy,
  main-context, Skill-design, and operations contracts.
- Bumped the canonical harness manifest to schema 2 / product 1.1.0 and added
  manifest-owned `class`, `use_when`, and `not_for` metadata for all 27
  capabilities.
- Replaced the hand-owned invocation registry with a generated projection and
  strengthened the schema/scanner/conformance failure controls.
- Generated concrete discovery descriptions for Claude, Codex, and OpenCode.
  Codex/OpenCode entry-router bodies now defer full portable procedure detail
  until the approved acting owner; parent-invoked stages retain detail.
- Updated adapter bootstraps and boundary checks to enforce the one-time
  confirmation plus depth-0/1/2 reading boundary.
- Refreshed the governed footprint baseline with an explicit routing-quality
  rationale; no token or cost savings claim was made.
