# Phase 3 dispatch metrics

## Dispatch and fallback

- Selected intensity: `strong`; derived assurance: `standard` with one
  independent review at the riskiest point.
- `subagent-info --check`: pass (`multi_agent` enabled).
- `headless --check`: failed because installed `$CODEX_HOME` links target the
  main checkout, not this feature worktree. Exact worktree-specific bootstrap,
  skill, agent, and mode targets therefore fail the runtime projection check.
- Repointing the live interactive runtime to an unmerged feature worktree would
  mutate external session state and violate the explicit active-source boundary.
  The documented manual-main-session fallback is used.

## Separability judgment

- Plan review and final risk review are separable read-only checks and may use
  bounded independent workers.
- Source inspection, snapshot generation, registry ownership, CLI result shape,
  and the E2E fixture share one schema and rollback boundary. Splitting their
  writes across independent sessions would create a boundary-coupled partial
  implementation, so one execute writer owns them.
- Test execution remains a separate read-only stage after implementation.

## Initial scope metrics

- runtimes: 3;
- external executable surfaces kept inactive: 5 categories;
- remote/package-manager operations in core extension path: 0;
- committed fixture classes: 2.

## Independent plan-check

Initial verdict: FAIL with five HIGH findings and one MEDIUM finding.

- Closed TOCTOU with no-follow census, staging reinspection, and final source
  checksum comparison.
- Split and versioned source/projection digests; composite-keyed snapshots are
  rehashed before reuse.
- Downgraded registry to untrusted data; paths are recomputed from canonical id
  and trusted roots under one file lock/generation gate.
- Added an XDG transaction journal and next-invocation crash recovery.
- Replaced ambiguous flat names with a 64-char-bounded canonical hash suffix
  and reserved `external-` against built-ins.
- Added exact native-source detection and extension/core-doctor isolation tests
  to replace the current target-substring heuristic.

Plan status advanced to `approved` after these changes.

## Implementation review

Initial verdict: FAIL with three HIGH and four MEDIUM findings.

- Bound manifest identity to census-captured bytes and root-anchored
  `O_NOFOLLOW` traversal; the second inspection compares canonical identity,
  manifest digest, projection digest, and source checksum.
- Replaced lexical snapshot trust with XDG-root-anchored traversal, digest, and
  deletion that rejects symlinked ancestors.
- Added raw registry byte preservation, before/after hashes and generations,
  non-empty runtime/delta validation, and fail-closed recovery CAS.
- Replaced predictable temporary symlink cleanup with collision-preserving
  random names.
- Centralized absolute XDG/runtime roots, honored `$CODEX_HOME` and
  `$CLAUDE_CONFIG_DIR`, and locked resolved runtime roots into ownership state.
- Expanded high-confidence secret patterns and mapped inspect validation errors
  to exit 2.

Final independent verdict: PASS. Remaining HIGH/MEDIUM findings: 0.

## Final scope metrics

- runtime projections: 3;
- fixture classes: 2;
- independent findings closed: 7;
- network/marketplace/package-manager mutations: 0;
- executable extension surfaces activated: 0.

## Upstream integration

- implementation commit pushed: `40dcb585`;
- integrated main commit: `4e65ef3d` (English language migration);
- merge commit: `c7a2046a`;
- merge conflicts: 1 (`tools/install/paths.py`), resolved by retaining the
  English API text plus Phase 3 absolute XDG/runtime override behavior;
- post-merge portable guards: 344/344;
- post-merge independent adaptation negative cases: all pass.
