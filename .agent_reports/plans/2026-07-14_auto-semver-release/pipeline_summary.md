# Pipeline summary — automatic SemVer release

Complete. Release-relevant `main` changes now automatically close the gap to a
stable GitHub Release. The first run classified accumulated feature work as a
minor change and published `v1.1.0` from the exact tested commit.

The release path is one serialized transaction:

1. Compare the highest reachable stable tag with the triggering commit.
2. Skip non-release paths or choose the highest commit-signaled SemVer bump.
3. Validate the repository and build deterministic assets at that commit.
4. Create its annotated tag with the workflow token.
5. Publish the four assets in the same run, without relying on recursive events.

Explicit valid SemVer/prerelease tags remain the manual override. Existing tags
and assets are never moved or replaced.
