# Final report — automatic SemVer release

## Outcome

`main` and the stable distribution no longer depend on a maintainer remembering
to create a release. Runtime-affecting changes automatically publish after full
validation; documentation/report/test-only pushes are recorded as skipped runs.

## Policy

- breaking signal → major
- release-relevant `feat` → minor
- other release-relevant change → patch
- docs, reports, CI, research, fixtures, and tests only → no release
- explicit valid SemVer/prerelease tag → maintainer-selected version

## First automatic release

- Version: `v1.1.0`
- Implementation/tag target: `9314c9a49571e51ea777a9caf78be16181496565`
- Workflow run: `29321551547` (success)
- Public latest metadata, four assets, both checksums, archive marker, and
  installer embedded version: verified

The version decision remains source-controlled and inspectable in
`RELEASE_POLICY.md` and `tools/release/plan.py`.
