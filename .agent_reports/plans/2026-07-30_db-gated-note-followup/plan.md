# DB-gated note follow-up implementation plan

## Objective

Implement `.agent_reports/spec/note-publication/prd.md` v1 across the portable
contracts, topology compiler, readiness surface, adapter projections, and tests.

## Scope

1. Add the conditional follow-up/update semantics to core and capability contracts.
2. Add topology registry v6 declarations and fail-closed validation.
3. Seal effective terminal anchors in compiled routes and verify them.
4. Add a shared secret-safe remote DB readiness probe plus adapter entry points.
5. Regenerate projections and run focused/full boundary verification.

## Ownership and safety

- No user DB, credential, scheduler, or runtime configuration mutation.
- Existing dirty stage-dispatch and root spec files are out of scope and remain unstaged.
- Current runtime policy forbids sub-agent dispatch for this turn, so implementation is
  inline with the recorded `user-restricted` topology exception. Verification remains
  independent at the test-contract level.

## Verification

- topology validator and route compiler unit suites;
- readiness shell fixture suite, including secret non-disclosure;
- generated projection check and adaptation boundary;
- focused capability contract searches and git diff review.
