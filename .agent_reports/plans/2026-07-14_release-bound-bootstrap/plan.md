# Plan — release-bound bootstrap

## Outcome

Public installation must execute bootstrap code and install an archive produced
from one immutable GitHub Release tag. `raw main` must not supply distribution
logic to a release install.

## Steps

1. Update installer/productization specs and snapshot v4/v6.
2. Generate a deterministic self-contained `install.sh` release asset from the
   tagged `distribution.py`, with the exact tag embedded.
3. Convert root `install.sh` into a legacy redirect and move README commands to
   release asset URLs.
4. Expand release lifecycle tests for deterministic installer assets, exact-tag
   enforcement, override rejection, and absence of raw distribution URLs.
5. Run release/security/runtime regressions, commit and push, integrate main,
   publish `v1.0.1`, and verify the public path.

## Plan check

- Trust boundary: GitHub Release HTTPS remains the publisher anchor; archive
  SHA-256 still detects corruption, not publisher compromise.
- Compatibility: the previous raw-main command remains functional through a
  redirect, but public docs no longer recommend it.
- Pinning: users select a versioned installer asset URL; a latest installer may
  not be overridden to install a different archive tag.
- Rollback: installed updater behavior and immutable release roots are unchanged.

## Execution constraint

This external-facing fix uses an adversarial verification level. Stage dispatch
is not used because the active runtime instruction forbids spawning subagents
unless the user explicitly requests them; all stages run inline with durable
evidence and a dedicated failure-mode review.
