# Code-test retry r4 semantic review — entry Skill layer

## Verdict

**FAIL.** Correction r4 fixes the previous P0 completely: the draft-strategy
backlink reaches the intended post-approval owner heading in canonical,
Claude-native, and Claude-plugin trees, and the repository gate explicitly
checks all three delegate documents. The 39 moved owner documents, lossless
semantics, exact footprints, routing descriptions, projections, adaptation
decisions, worker-bootstrap v5, deny zones, primary checkout, and unrelated
projection baseline all reconfirm. A separate all-13 capability-contract audit
found one remaining blocking plan mismatch, and two approved portable
documentation updates are absent.

## Findings

### 1. P1 blocking — owner-status generation covers a group, not all entry routers

The approved plan requires every one of the 13 entry-router capability
contracts to identify its post-approval load phase and owner contract.
`tools/build-manifest.py` initializes `entry_layer`, but emits it only inside
`if spec["group"] == "entry"`. Invocation class, not group, defines the entry
router set.

Observed coverage:

- 13 manifest `entry-router` capabilities;
- 10 capability contracts with the generated owner-status row;
- missing: `capabilities/analyze-project.md`,
  `capabilities/analyze-user.md`, and `capabilities/audit.md`.

These three are valid entry routers in groups `pre`, `pre`, and `ops`, so the
group predicate silently excludes them. `tools/harness_manifest.py` verifies
that an owner file exists, but the current deterministic gates do not require
the generated row on exactly all 13 entry-router capability contracts. This is
why generation, conformance, routing, footprint, topology, and adaptation all
pass despite the incomplete contract projection.

Smallest correction: keep execution-topology generation conditional on group
`entry`, but derive `entry_layer` independently from
`spec["invocation"]["class"] == "entry-router"`; regenerate capability
contracts, then add an exact-set assertion that all and only the 13 entry
routers carry the post-approval owner row.

### 2. P1 — two approved portable-source alignment edits are absent

The plan/checklist explicitly name `core/DESIGN_PRINCIPLES.md` and
`capabilities/README.md`. Neither is changed from the starting commit, and a
targeted scan finds no compact pre-approval router / post-approval owner /
assigned-stage distinction in either file. The corresponding checklist items
remain incomplete.

Smallest correction: add the planned portable layering statement to those two
documents without duplicating execution procedure, then include their required
phrases in an existing deterministic contract gate.

## Prior P0 disposition — fixed

The three delegate documents now resolve to an actually present
`## Paste-Ready Cheatsheet Format — Separate User and Tracking Surfaces`
heading in their corresponding `autopilot-draft` owner documents. The six files
are byte-identical by three-file group. The repository gate explicitly loops
the three `OWNER_TREES` delegate paths, and its execution passes. This finding
is closed.

The added owner section preserves the required card-body versus tracking-only
metadata separation. Independent line comparison proves that all 13 relocated
starting bodies remain present: 12 exact, with only the 14-line authority
section inserted in `autopilot-draft`; there are no deletes or replacements.

## Reconfirmed passing surfaces

- 39 moved owner documents resolve 375 concrete paths and 90 anchors.
- Canonical and both Claude owner/reference trees are byte-identical.
- All five runtime surfaces preserve 13 exact manifest descriptions (65 total).
- Entry footprints exactly match the checked baseline: 26,825/2,217 bytes for
  canonical and both Claude trees, 35,173/2,843 for Codex, and 33,717/2,731 for
  OpenCode.
- Two generation runs in a temporary current-tree copy are byte-stable, and
  `generate.py --check` passes.
- Adaptation inventory and boundary decisions pass with only the documented
  91-reference warning.
- Worker-bootstrap v5 bytes and hashes are exact; worker/type, utilities,
  dispatch, runtime-bin, and fleet deny zones are clean.
- The primary checkout has no tracked or staged source change; its untracked
  rows are the canonical cycle artifacts only.
- Current and starting-commit generated-projections tests fail first with the
  identical unrelated `legacy artifact root was not selected for orientation`
  baseline.
- The source worktree status remained byte-for-byte stable throughout this
  read-only test stage.

## Handoff

The complete command and evidence matrix is
`test_logs/verification-matrix-r4.md`. Return to `code-execute` for the exact
13-entry capability-row correction and the two omitted portable documentation
updates, then rerun this matrix. Final retry-r4 verdict: **FAIL**.
