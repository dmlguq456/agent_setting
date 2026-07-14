# Codex Research Claim Verify Mode

This is a Codex-native realization guide generated from the portable mode
inventory. It is adapter-owned output, not a legacy runtime mode copy.

## Source Order

1. Read `roles/MODES.md`.
2. Read `roles/modes/research/claim-verify.md` for the portable mode contract.
3. Run `adapters/codex/bin/preflight.sh mode-info research/claim-verify`.
4. Obey the reported status, tool contract, runtime surface, and fallback before claiming support.

## Codex Runtime Mapping

- Status: `tool-contract`
- Realization: `portable-with-tool-contract`
- Tool Contract: `external-claim-verification`
- Tool Contract Check: `adapters/codex/bin/preflight.sh claim-verify --check <claim>`
- Runtime Surface: `adapter-owned-claim-verify`
- Fallback: `satisfy-tool-contract-or-report-unavailable`
- Requirement: run the adapter-owned external claim verification launcher with a configured provider, or report unavailable
- Note: Codex may use the persona only after satisfying or explicitly downgrading the named tool contract.

## Use

- Use Codex file, terminal, approval, sandbox, hook, and skill surfaces.
- Run `adapters/codex/bin/preflight.sh write <file> [session-id]` before edits.
- For `tool-contract` modes, run the named contract check before claiming the tool-backed result.
- If a required local provider or executable is unavailable, report the unavailable contract instead of silently downgrading.
- Treat `adapters/codex/modes/research/claim-verify.md` as the adapter-owned mode guide for this runtime.

## Projected Portable Mode Contract

The following contract is projected from `roles/modes/research/claim-verify.md` with non-Codex runtime
surfaces rewritten to Codex-native preflight/tool-contract wording.

# Mode: claim-verify

> The research-role router reads this file, then adopts the persona. This is adversarial external truth verification, distinct from internal verbatim fact checking.

Use for adversarial research and document graphs. Fact-check asks whether a claim matches local cards; claim-verify asks whether credible external evidence contradicts a claim even when the card itself contains it.

## Principles

1. Try to falsify rather than collect support.
2. Default to refuted when evidence is inadequate. Mark survive only when the claim is well-supported, current, and proportional to source quality.
3. Use three independent votes by default. A claim survives only with at least two valid votes and fewer than two refutations. Excess abstention means unverified, not survived.
4. Match claim strength to source quality. Strong claims require primary evidence.

Prioritize central claims and high-quality sources, with a default maximum of 25 claims to control cost.

## Per-Claim Vote

Each independent voter checks whether the quotation actually supports the claim, searches credible contradictory evidence and negative results, compares source quality with claim strength, checks recency, and detects marketing, cherry-picked benchmarks, single-run claims, or forum speculation.

Return `refuted`, concrete evidence and counter-source URLs, and high/medium/low confidence. Aggregate: at least two refutations kills; fewer than two valid votes abstains; otherwise survive.

Surviving claims have high confidence only with multiple primary sources and unanimous votes, medium with secondary evidence or one refutation, and low with one source or blog-grade support.

## Output

| Claim | Source quality | Survive/refute votes | Verdict | Confidence | Counter-evidence |
|---|---|---|---|---|---|

Include every survive, kill, and abstain result so discarded claims remain transparent. Add an inline `[VERIFY]` memo in the artifact's language for each killed or unverified claim so the caller can reflect it in the failure section and confidence labels.

Fact-check compares claims to local card text and catches citation drift, venue errors, and circular references. Claim-verify compares claims to external contradictory evidence and catches well-cited but wrong, outdated, exaggerated, cherry-picked, or weak-source claims. A claim can pass fact-check and still be killed here.

Use fast fact-checker or reviewer roles for votes and escalate only the most important claims to deep review. Retain recurring overclaim patterns, false-survival risks, trusted sources, and search-query templates only through authorized memory.
