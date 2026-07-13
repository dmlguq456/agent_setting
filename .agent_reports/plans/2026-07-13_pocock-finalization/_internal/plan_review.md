# Plan-check — standard

1. **Scope bounded?** Yes. Only P4/P8, `skill-conformance` projection closure, and stale Pocock artifacts are included. Ponytail and Codex runtime dispatch/liveness are excluded.
2. **Authority order correct?** Yes. Portable classification is recorded in `core/ADAPTATION_INVENTORY.md` before adapter projection changes; live Claude skill tree remains canonical with root `skills/` mirrored.
3. **Runtime evidence current?** Yes. Official Claude Code docs reconfirmed description/`when_to_use`, `disable-model-invocation`, and `user-invocable` behavior before the projection decision.
4. **Verification concrete?** Yes. Conformance, g7, mirror, plugin/manifest generators, focused adaptation-boundary filtering, and semantic diff review all have executable checks.

Verdict: **PASS — safe to execute.**
