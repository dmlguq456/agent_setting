# README product surface + sync-skills retirement plan

## Context

- Governing spec: `.agent_reports/spec/harness-installer/prd.md` v3 (INST-D-8/9).
- Reference brief: `.agent_reports/spec/harness-installer/_internal/readme-reference-brief.md`.
- Mode/intensity: `dev/refactor`, `strong`; standard+ stages are `code-plan -> code-execute -> code-test -> code-report`.
- Spec significance: `within-spec`; the requested public surface and retirement are already specified.
- Starting HEAD: `98127296817688647bafe643809d48d94d82fa3b`.

## Requirements coverage

1. Replace root `README.md` with a human-owned product landing page ordered as: value -> install -> natural-language examples -> benefits -> runtime distribution differences -> architecture -> deep docs/development verification.
2. Retire the portable `sync-skills` capability from canonical capability/Claude compatibility sources, runtime-native generated projections, catalog, manifest, `.sync_state.json`, and active docs/tests/comments.
3. Preserve `sync-native-*` projection generator names and regenerate their outputs instead of hand-editing generated files.
4. Reassign mechanical consistency ownership to `build-manifest --check`, native projection `--check` commands, adaptation-boundary, skill-conformance, and `harness verify`; keep public README prose human-owned.
5. Exclude `.agent_reports/**`, `.claude_reports/**`, `.git/**`, and git history from retrospective cleanup.

## Execution steps

1. Edit canonical/human-owned sources: README, capability catalog, MANUAL/core wording, oncall/mode/tool/test references, and Claude compatibility sources; delete the retired capability/state trees.
2. Run existing generators for Codex skills/plugin/modes, OpenCode skills/commands, Claude plugin, then rebuild `manifest.json`.
3. Audit active-source references. Only generator names such as `sync-native-skills.py` may retain the `sync-skills` substring.
4. Validate README internal links and installer commands against local files/help output.
5. Run requested deterministic checks via the Codex verification runner and record exact evidence under `test_logs/`.

## Ownership and boundaries

- `code-plan`: this plan, checklist, metrics, and plan review only.
- `code-execute`: all source edits/deletions and generator writes; no verification claims.
- `code-test`: read-only source verification plus `test_logs/` evidence.
- `code-report`: `final_report.md` and `pipeline_summary.md`; no source changes.

## Verification design

- README links: extract relative Markdown links and assert each local target exists.
- Commands: compare documented installer commands with `harness.sh --help`, `install --help`, and `verify --help`; use dry-run only where safe.
- Retirement census: `rg` current source while excluding `.agent_reports/**`, `.claude_reports/**`, and `.git/**`; classify allowed `sync-native-skills` generator-name hits separately.
- Deterministic gates: build-manifest, all native projection checks, adaptation boundary, skill conformance, Codex doctor, and installer verify.

## Residual risks

- Removing a capability can leave stale generated directories unless every generator with pruning behavior is rerun.
- `sync-skills` also appears in test fixtures and comments; leaving those names would keep a false active surface even if runtime projections disappear.
- Runtime verification may expose environment-only failures (CLI availability, hook trust, or runtime-home permissions); record these as blocked/unsupported rather than treating them as product regressions.
