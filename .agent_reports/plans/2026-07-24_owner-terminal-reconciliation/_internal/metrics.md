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
