# Topology N-way and model-profile plan

## Outcome

Generalize the portable topology from fixed two-leg replication to bounded,
profile-sealed parallel groups. Preserve cross-harness diversity, add asymmetric
model-profile exploration, and keep substantive registered topology nodes above
the mini profile.

## Contract

1. Introduce four portable execution profiles: `deep`, `balanced-deep`, `light`,
   and `mini`. Profiles bind a model tier plus adapter-owned effort/variant; they
   do not replace semantic model roles.
2. Use `deep/xhigh`, `deep/medium`, `light/medium`, and `mini/medium` as the
   Claude/Codex defaults. OpenCode explicitly folds `balanced-deep` into its deep
   runtime-default variant until a verified effort surface exists.
3. A sealed standard+ route assigns `model_profile` per owner/node/parallel leg.
   Registered depth-1/2 topology rejects `mini`; mini remains a lifecycle or
   explicitly micro-semantic helper profile.
4. Replace recipe-local `replications` with `parallel_groups`. A group declares
   kind, width by intensity, ordered leg profiles/perspectives, required
   diversity axes, and join policy. Width is bounded to 2–4 and every realized
   leg remains a dispatch-depth-2 sibling.
5. Generalize batch admission, immutable manifests, governor reservation/claim,
   partial one-leg recovery, receipts, and registry metadata from exactly two to
   the route-declared N members. Initial admission is all-or-zero.
6. Keep depth 3 forbidden. The depth-1 owner joins the exact group and performs
   synthesis itself or starts a later depth-2 reducer node.

## Topology placement

- Standard owner: `balanced-deep`; strong+ owner: `deep`.
- Framing: asymmetric `balanced-deep` anchor plus `light` cross-harness
  alternative at standard; strong+ adds a `deep` contrarian leg.
- Strong plan: `deep` anchor plus `balanced-deep` alternative; thorough+ adds a
  `light` implementation-risk scout.
- Strong implementation review: `balanced-deep` anchor plus `light` independent
  reviewer; thorough+ adds a `deep` failure-mode reviewer.
- Routine execute/test/report nodes default to `light`; high-judgment frame/plan
  nodes default to `balanced-deep` or `deep` as declared.
- Existing non-code anchors migrate to the same group primitive without being
  widened automatically.

## Implementation sequence

1. Update stage-dispatch and dispatch-profile blueprints.
2. Upgrade topology registry/validator/compiler and route verification.
3. Upgrade group batch manifest, governor, dispatch binding, and parent join
   metadata.
4. Add adapter model-profile resolution and generated projections.
5. Update owner/stage guidance and compatibility terminology.
6. Run focused unit tests, full manifest/projection/boundary checks, runtime
   projection checks, and an independent audit.

## Compatibility

- Topology registry v4 is read-only; new writes use v5.
- Route schema remains hash-sealed and rejects stale registry digests.
- `--replica-group` and `replica_group` remain read-only aliases for one
  compatibility window; canonical new surfaces use `--parallel-group` and
  `parallel_group`.
- Existing two-way groups are valid N-way groups of width 2.
