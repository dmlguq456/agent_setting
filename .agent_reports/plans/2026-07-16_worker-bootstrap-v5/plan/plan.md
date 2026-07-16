---
title: Worker bootstrap isolation v5
status: complete
capability: autopilot-code
mode: refactor
intensity: strong
spec: .agent_reports/spec/skill-design-refactor/prd.md
---

# Plan

1. Define the portable worker kernel, four type fragments, exact handoff
   envelope, and runtime masking support boundary.
2. Add a shared deterministic renderer/classifier and use it from Codex,
   Claude, and OpenCode headless dispatchers, including custom prompts.
3. Replace Claude masked-profile full-core bootstrap with canonical
   kernel + one declared type + selected specialization.
4. Update adapter runtime contracts and boundary checks without claiming that
   runtime-owned project instruction inheritance is physically masked.
5. Add renderer, dispatcher, profile, projection, and context-footprint tests;
   run the relevant full boundary/projection gates.
6. Integrate on current main, preserve unrelated work, commit, and push.

## Completion gate

- No dispatcher explicitly asks a worker to read a full main adapter bootstrap.
- All three render the same exact three-line handoff contract.
- Worker profile inputs are one kernel + one type, with a deterministic fallback.
- Safety, route, write-scope, artifact, liveness, and verification gates remain.
- Runtime inheritance limits and static footprint evidence are documented.
