# Strong plan-check — risk-focused inline fallback

## Gate verdict

PASS. The plan covers all user requirements without expanding into installer implementation or historical artifact rewriting.

## Checks

- Requirements coverage: README ordering, positioning, retirement surfaces, regeneration, deterministic ownership, and QA are explicit.
- Over-scope: runtime implementation is unchanged; only documentation, capability retirement, projections, manifest, comments, and fixtures are touched.
- Under-scope: generated Claude plugin, Codex plugin skill set, OpenCode commands, manifest, and `.sync_state.json` are included.
- Executable verification: every requested gate has a concrete command and will run through `verification-runner`.
- Spec-significant risk: none; PRD v3 already owns the decisions.

## Riskiest point

The highest risk is an apparently successful retirement that leaves a generated or test-only active reference. Mitigation: generator pruning plus a repository-wide current-source census with explicit history exclusions and an allowlist limited to the `sync-native-skills` generator name.
