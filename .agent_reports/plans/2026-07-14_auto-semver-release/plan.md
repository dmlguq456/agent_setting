# Automatic SemVer Release — Implementation Plan

## Context

- Specs: `.agent_reports/spec/harness-installer/prd.md` v6 and
  `.agent_reports/spec/harness-productization/prd.md` v8.
- Starting HEAD: `65518bc37e94799f60fc0fe4fb9adb1e54fd93dd`.
- Intensity: strong. This mutates the public distribution and tag boundary.

## Outcome

Keep the latest stable GitHub Release aligned with release-relevant changes on
`main`, without publishing for documentation/report/test-only churn.

## Steps

1. Specify the release-relevant path boundary and deterministic SemVer rules.
2. Add a standard-library planner and isolated fixtures for skip/patch/minor/major.
3. Change the release workflow to plan on `main`, validate and build before tag
   creation, then publish the tested commit in the same serialized run.
4. Preserve validated manual SemVer/prerelease tag pushes as an explicit override.
5. Run local policy, workflow, release, runtime, generation, and boundary checks.
6. Integrate to `main`, observe the automatic release, and verify its assets.

## Rollback

Revert the workflow/planner commit. Published tags and assets remain immutable;
rollback never moves or deletes a release and any correction uses a new version.

## Plan check

- Fail-safe: unclassified release-relevant changes become patch releases.
- Noise control: docs, reports, CI, research, fixtures, and tests alone are skipped.
- Race control: one repository-wide release concurrency group serializes planning.
- Tested ref: build, tag, and assets all use the triggering exact commit SHA.
- Recursion: publishing occurs in the main-push run and does not require the
  workflow-created tag to trigger another run.
