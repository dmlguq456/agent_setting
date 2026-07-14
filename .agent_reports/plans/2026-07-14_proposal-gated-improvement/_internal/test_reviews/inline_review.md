# Inline Test-Adequacy Review

No independent agent review is claimed; the active collaboration policy did
not permit subagent dispatch. The standard QA fallback was an inline risk pass.

Covered risks:

- illegal and out-of-order proposal transitions;
- missing human approval provenance;
- stale proposal context;
- activation before portable adoption;
- runtime update requiring revalidation;
- repo/runtime-home/symlink store escape;
- oversized evidence and incomplete context;
- read-only list behavior;
- real runtime config/plugin immutability;
- generated, adapter, extension, activation, and release regressions.

Residual scope is intentional: no scheduled collection, runtime hook, plugin
activation, source patch application, or authenticated approval service exists
in v1.
