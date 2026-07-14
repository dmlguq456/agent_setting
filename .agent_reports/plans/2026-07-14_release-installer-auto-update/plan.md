# Release installer and automatic update

## Context

- Specs: `.agent_reports/spec/harness-productization/prd.md` v6 and
  `.agent_reports/spec/harness-installer/prd.md` v4.
- Starting point: branch `release-installer-auto-update` from `29b527c1`.
- Intensity: strong. This is a security-sensitive distribution boundary.

## Goal

Give general users a checksum-verified one-line managed release installation
with automatic packaged updates, while preserving linked checkout behavior for
maintainers and simplifying the README product pitch.

## Change sequence

1. Extend the portable agent-home contract to resolve managed releases before
   linked-checkout fallbacks.
2. Add a standalone release distribution module with GitHub Release metadata,
   checksum verification, safe extraction, staged publish, packaged activation,
   atomic pointers, rollback, update locking, and scheduler lifecycle.
3. Route managed `harness update` calls to that module; preserve local
   drift/reapply semantics outside a managed install.
4. Add a thin `install.sh`, deterministic release builder, and tag-driven
   GitHub Actions release workflow.
5. Replace clone-first README quickstart with the one-line installer and reduce
   the headline value proposition to five concrete strengths.
6. Verify archive attacks, checksum failure, no-op/update/rollback behavior,
   linked-source preservation, scheduler fallback, existing activation/profile/
   extension regression, generated projections, and adapter boundaries.

## Ownership boundaries

- Network access exists only in bootstrap/managed update metadata and asset
  download. Runtime activation and built-in behavior stay local.
- The updater targets only activation records whose mode is `packaged` and
  whose source is the previously managed release.
- Runtime credentials, sessions, databases, logs, foreign cache, linked
  checkout contents, and Git state are outside installer ownership.
- Release activation does not imply the current runtime session reloaded;
  `session_action` remains authoritative.

## Rollback design

- Download and extraction occur in an XDG data staging directory.
- The archive checksum and every member path/link are validated before publish.
- Multi-runtime activation uses the existing invocation transaction.
- If pointer/state commit fails after activation, the previous release is
  reactivated and previous pointer/state bytes are restored.
- At least the previous release is retained.

## Completion

All checklist items pass, specs/pipeline records are marked complete, source and
generated projections are clean, and the branch is committed and pushed for
main integration.
