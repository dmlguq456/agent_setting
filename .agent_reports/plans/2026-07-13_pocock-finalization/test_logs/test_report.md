# Test report — Pocock finalization

**Target:** `.agent_reports/plans/2026-07-13_pocock-finalization/plan.md` and changed skill/projection files
**Rigor:** standard, commands executed through `adapters/codex/bin/preflight.sh verification-runner`

## Level 1 — syntax

- PASS: `bash -n` for the changed/consumed shell checkers and g7 fixture/assert scripts.

## Level 2 — import

- SKIP: no Python module source changed.

## Level 3 — smoke

- PASS: `tools/skill-conformance/check.sh skills adapters/claude/skills`.
- Result: `PASS: skill conformance (structure + invocation policy 26 classifications)`.

## Level 4 — functional

- PASS: mirror parity excluding `skills/.sync_state.json`.
- PASS: registry has 13 entry-router rows and both Claude trees expose 13 `Use when…` descriptions.
- PASS: P8 old phrases absent; two positive replacements present in both trees; diff contains only the two intended lines per tree.
- PASS: Claude plugin + manifest + Codex/OpenCode native skill projection checks.
- PASS: Claude projection symlinks resolve and focused adaptation-boundary output contains no `skill-conformance` failure.
- NOTE: two initial composite assertions failed because of `awk`/quote escaping in the test command. Both were replaced with simpler assertions and passed; source files did not change in response.

## Level 5 — integration/regression

- PASS: g7 static fixture/assert live gate.
- PASS: parent-invoked forbidden flip negative control.
- PASS: user-only missing flag negative control and explicit flag positive control.
- Full repo boundary check exits 1 only for pre-existing `INSTALL_LAYOUT.md` documentation parity. No Pocock/skill-conformance failure remains.

## Level 5b — behavioral runtime observation

- BLOCKED/DOWNGRADED: a separate headless Claude/Codex model-invocation observation was unavailable because Codex runtime projection reported `hooks-json:failed reason=not-harness-hook-projection`.
- The trigger change is a soft routing hint, not a deterministic activation promise. Static frontmatter, scanner, registry, official-doc currentness, and the existing C1 invocation runtime evidence are the applicable proof in this cycle.

## QA policy

- `standard code` requested independent reviewers, but the same headless/runtime constraint prevented an independent pass. Per reported fallback, this is an inline evidence review; independent QA is not claimed.

## Verdict

**PASS — all 4 applicable levels passed; import skipped, behavioral observation explicitly downgraded.**
