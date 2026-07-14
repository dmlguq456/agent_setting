# Codex Research Fact Check Mode

This is a Codex-native realization guide generated from the portable mode
inventory. It is adapter-owned output, not a legacy runtime mode copy.

## Source Order

1. Read `roles/MODES.md`.
2. Read `roles/modes/research/fact-check.md` for the portable mode contract.
3. Run `adapters/codex/bin/preflight.sh mode-info research/fact-check`.
4. Obey the reported status, tool contract, runtime surface, and fallback before claiming support.

## Codex Runtime Mapping

- Status: `portable`
- Realization: `portable-persona`
- Requirement: read/cite primary sources through available Codex tools
- Note: Codex may use the mode fragment after reading roles/MODES.md and resolving portable roles.

## Use

- Use Codex file, terminal, approval, sandbox, hook, and skill surfaces.
- Run `adapters/codex/bin/preflight.sh write <file> [session-id]` before edits.
- For `tool-contract` modes, run the named contract check before claiming the tool-backed result.
- If a required local provider or executable is unavailable, report the unavailable contract instead of silently downgrading.
- Treat `adapters/codex/modes/research/fact-check.md` as the adapter-owned mode guide for this runtime.

## Projected Portable Mode Contract

The following contract is projected from `roles/modes/research/fact-check.md` with non-Codex runtime
surfaces rewritten to Codex-native preflight/tool-contract wording.

# Mode: fact-check

> The research-role router reads this file, then adopts the persona. Use narrow verbatim matching rather than creative judgment.

This selected source-check gate serves research, draft, refinement, and their strategy stages when claims, citations, or cards are actually in scope.

| Source class | Meaning | Verdict |
|---|---|---|
| `cards-verbatim` | Venue, value, metric, or year appears verbatim in the matched card body or metadata | allowed |
| `cards-name-only` | The model or author exists but the specific value does not | caution; reverify externally |
| `external-marker` | The artifact explicitly marks the claim unverified or external | caution; reverify |
| `external-reverified` | A caution was confirmed through a logged authoritative URL | allowed after reverification |
| `conflict` | Card contains a different value | fail |
| `no-match` | No card contains the claim | fail |
| `ambiguous` | Several candidate cards with no single best match | caution |
| `circular-ref` | Draft and strategy cite each other rather than cards | fail |

Name-only is never sufficient. Validate draft and strategy independently against cards. Cross-check the nearest section heading against card classification so, for example, a classical method cannot silently appear under a deep-learning heading. When evidence is absent, recommend an explicit placeholder rather than inventing venue, year, task, or metric.

## Output

Emit a table only, covering roughly the 30 most material claims and prioritizing Tier 1 papers and user-named models. For every failed or caution result, add an inline `[FACT]` memo in the artifact's language naming the section, claim, and conflicting source. The refinement orchestrator may reuse the classification table without opening another agent when its contract says so.
