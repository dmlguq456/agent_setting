# Topology N-way profiles — pipeline summary

## Result

Fixed 2-way replication was replaced by bounded 2–4 way parallel groups with
route-sealed model profiles and perspectives. The implementation preserves
depth-2 sibling topology, exact all-or-zero batch admission, and N-1 peer proof
for one-missing-leg recovery.

The portable execution vocabulary is now `deep`, `balanced-deep`, `light`, and
`mini`. Claude and Codex distinguish all four; OpenCode reports its
balanced-deep collapse explicitly. Substantive registered depth-1/2 work rejects
mini. Fable remains an interactive main-session-only choice.

## Verification

- focused topology, route, batch, governor, contract, wrapper, join, and guard
  suites passed;
- full Fleet suite passed 875 tests in the isolated implementation worktree;
- portable guards passed 358 checks;
- generated projections, model configuration, manifest, adaptation boundary,
  runtime projection, mirror parity, and whitespace checks passed;
- independent audit found no blocking drift.

After main integration, runtime projection and 356 topology-focused tests also
passed. The integrated full Fleet rerun reproduced one pre-existing
token-accounting timestamp-order race; it is outside this diff and is recorded
in `final_report.md` rather than hidden by a retry.
