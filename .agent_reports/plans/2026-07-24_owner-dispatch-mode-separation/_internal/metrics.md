# Metrics and route exception

- approved route: `autopilot-code / debug / strong`
- spec gate: `SPEC-SIGNIFICANT`
- observed reproduction: owner `--mode dev` rc=64; owner `--mode
  plan/plan-author` rc=0
- registered dispatch: 0
- inline exception: the defect under repair is the dispatch-depth-1 owner bootstrap
  tuple itself. Reusing it would require the same semantically false stage mode and
  contaminate the repair owner. Work remains inline in an isolated source worktree;
  no depth-2 worker is launched through the known-bad adapter.
- runtime parity: official Codex non-interactive/custom-agent surfaces and Claude
  print/subagent surfaces do not require this harness-local overloaded mode field;
  therefore the gap is a local projection defect, not a runtime requirement.
- implementation: `89b59d72` (`fix(dispatch): separate owner capability and worker modes`)
- verification: portable guards `PASS=358 FAIL=0`; Fleet `Ran 871 tests / OK`;
  generated projections, adaptation boundary, installed runtime projection, and
  `doctor --runtime` all `status=ok`
- integration: fast-forwarded and pushed to `origin/main`
- cleanup: checked `status=eligible`, then applied `status=removed`; no active PID,
  stale registry row, or artifact harvest obligation
