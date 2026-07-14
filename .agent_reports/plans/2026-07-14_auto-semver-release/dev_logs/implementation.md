# Implementation log

- Added `tools/release/plan.py`, a standard-library planner that compares the
  highest reachable stable tag with an exact commit and emits skip/patch/minor/major.
- Made final release relevance path-aware, with documentation/report/CI/test-only
  exclusions and a patch fallback for unclassified behavior changes.
- Extended the Release workflow to run on `main`, serialize repository releases,
  validate and build before tag creation, create an annotated tag at the tested
  SHA, and publish all four assets in the same run.
- Preserved explicit valid SemVer/prerelease tag pushes as maintainer overrides.
- Tightened the asset builder to accept only the release tag grammar and updated
  lifecycle fixtures to valid prerelease identifiers.
- Added the public `RELEASE_POLICY.md`, README link, installer v6/productization
  v8 contracts, snapshots, and adapter-boundary classification for the CI-only tool.

## Corrections during implementation

- The release lifecycle used `v-integration`, which the new boundary correctly
  rejected; the fixture now uses valid `v0.0.0-integration`.
- The adaptation census initially treated the new repository-only planner as an
  unclassified runtime tool. It is now explicitly deferred from Claude Code,
  Codex, and OpenCode runtime projections.
- Main advanced by one routing cleanup commit during work; the implementation
  was rebased onto it and all focused release/boundary checks were rerun.
