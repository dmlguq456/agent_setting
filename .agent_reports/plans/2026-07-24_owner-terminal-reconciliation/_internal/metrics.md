# Route and execution metrics

- approved route: `autopilot-code / debug / strong`
- spec gate: `SPEC-SIGNIFICANT`
- primary capability: `autopilot-code`
- blueprint update: `autopilot-spec / update / strong`
- registered dispatch: 0
- inline exception: the registered owner/supervisor terminal path under repair is the
  failing execution surface. Reusing it would reproduce stale-open owner state and
  repeated harvest polling. Work proceeds inline in an isolated source worktree.
- user policy: Claude `deep=opus`; Fable is interactive depth-0 main-only.
- runtime currentness: official Claude Code CLI documents `opus` as a supported
  `--model` alias; the harness must not infer Fable dispatch eligibility from an
  interactive subscription/session surface.
- spec commit: `0db9b512`; primary implementation: `45b7ac86`
- integration head: `6fd83309` on `main` and `origin/main`
- verification: portable guards `PASS=358 FAIL=0`; Fleet `872/872`; model hook
  `15/15`; generated projections, adaptation boundary, strict runtime projection,
  and runtime doctor all pass
- formal drill: g9 Codex+Claude strong depth-2 parallel batch PASS; g10 OpenCode
  depth-2 fail-closed PASS; both 0 model tokens
- cleanup: `status=removed`, active PIDs 0, stale registry rows 0, harvest required 0
