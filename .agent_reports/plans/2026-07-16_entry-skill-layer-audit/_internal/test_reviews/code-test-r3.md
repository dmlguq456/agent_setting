# Code-test retry semantic review — entry Skill layer

## Verdict

**FAIL.** Most of correction pass r3 is verified: all 39 moved owner documents
resolve their own Markdown paths and anchors, the adaptation and exact
footprint gates now pass, and the owner bodies remain lossless after the
documented deterministic path relocation. One prior P0 finding remains: the
draft-strategy authority backlink targets an owner file that does not contain
the named section.

## Remaining finding

### P0 — draft-strategy backlink reaches a file but not the claimed owner section

`skills/draft-strategy/references/delegate-prompt.md:162` links to
`../../autopilot-draft/references/owner-execution.md#paste-ready-cheatsheet-format--separate-user-and-tracking-surfaces`.
The target file exists, but its complete heading inventory is at lines 1, 5,
15, 33, 39, 54, 73, 83, and 92; none names the paste-ready cheatsheet contract.
The file ends at line 94. The same broken target is mirrored at
`adapters/claude/skills/draft-strategy/references/delegate-prompt.md:162` and
the Claude plugin copy at line 162.

The section that actually carries the heading is the source delegate document
itself at `skills/draft-strategy/references/delegate-prompt.md:160`, not the
claimed post-approval autopilot-draft owner document. Therefore the new link
changes the old stale router target into a different stale fragment; it does
not establish the requested owner authority.

The regression is masked by the targeted gate. Although
`tools/entry-skill-layer.test.py:23-47` has a valid path/anchor resolver, the
call sites at lines 55-77 iterate only the 13 manifest `entry-router` owner
documents. `draft-strategy` is not in that set, so its cross-Skill delegate
backlink is never supplied to `resolve_owner`. This contradicts the correction
evidence's claim that the cross-reference was included in the new gate.

Smallest correction: put the paste-ready authority section under the intended
post-approval `autopilot-draft` owner/reference surface (or point to the true
existing owner if another file is authoritative), regenerate both Claude
mirrors, and add the three draft-strategy delegate documents explicitly to the
path-and-anchor gate. The test should fail if the target file exists but the
fragment is absent.

## Rechecked prior findings

- **Moved owner paths and anchors — fixed.** An independent manifest-derived
  audit resolved 111 Markdown paths and 90 fragments across 39 canonical,
  Claude-native, and Claude-plugin owner documents. The repository gate also
  passes. The 13 canonical bodies equal their starting-commit bodies after the
  generator's documented one-level relocation transform, and all 26 Claude
  copies are byte-identical to canonical.
- **Adaptation inventory — fixed.** `core/ADAPTATION_INVENTORY.md:73` classifies
  both helpers as portable canonical-only/deferred, both boundary decision
  lists include them, and `check-adaptation-boundary.sh` exits 0.
- **Exact footprint surface — fixed.** Strict mode loads exact total/max
  baselines for all five router trees, each with exactly 13 entries and no
  warnings.
- **Routing metadata and sibling runtime boundaries — pass.** All 65 projected
  descriptions exactly join the manifest `Use when` and `Not for` values.
  Canonical/Claude routers expose one post-approval owner edge, while all 26
  Codex/OpenCode routers remain compact runtime-native projections without
  projected portable procedure bodies.
- **Projection baseline — unchanged.** Current and starting-commit `/tmp`
  snapshots both fail first with `legacy artifact root was not selected for
  orientation` and emit the same failure output; this known baseline is not a
  new regression.
- **Claims and protected surfaces — pass.** Changed claim-language is negative
  or static-byte-only; worker-bootstrap v5 bytes/hashes are exact; deny zones
  are clean; the primary checkout has no tracked or staged source change.

## Handoff

The full bounded command matrix is recorded at
`test_logs/verification-matrix-r3.md` in this cycle.

Return to `code-execute` for the single remaining backlink/coverage correction,
then rerun the full matrix. Final verdict for this retry: **FAIL**.
