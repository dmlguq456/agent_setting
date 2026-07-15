# Implementation log

- Implemented the v9 topology registry and exact validator.
- Added immutable route compilation, high-level node dispatch, route identity in jobs rows, and hash-bound completion.
- Added detached resource execution, shared model-worker governor, mandatory smoke attestation, shared report media verifier, absolute cwd enforcement, and identifier-aware spec nudge.
- Generated compact sibling projections without graph duplication.
- Source-writing implementation used the approved inline reason `dispatch-infra-self-modification` because nested dispatch could not initialize safely in the worker sandbox.
- Main-session integration rebased onto current `origin/main`, made the shared governor state hermetic in portable guards, and taught loop runners to resolve the governor from the loaded harness when an isolated `AGENT_HOME` lacks utilities.
- Final source commit: `26497cd0`, pushed to `origin/capability-routing-topology`.
