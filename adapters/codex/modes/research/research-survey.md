# Codex Research Research Survey Mode

This is a Codex-native realization guide generated from the portable mode
inventory. It is adapter-owned output, not a legacy runtime mode copy.

## Source Order

1. Read `roles/MODES.md`.
2. Read `roles/modes/research/research-survey.md` for the portable mode contract.
3. Run `adapters/codex/bin/preflight.sh mode-info research/research-survey`.
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
- Treat `adapters/codex/modes/research/research-survey.md` as the adapter-owned mode guide for this runtime.

## Projected Portable Mode Contract

The following contract is projected from `roles/modes/research/research-survey.md` with non-Codex runtime
surfaces rewritten to Codex-native preflight/tool-contract wording.

# Mode: research-survey

> The research-role router reads this file, then adopts the persona.

Own paper search, analysis, cards, and report generation for the research pipeline. Read the router's Knowledge Sources first.

## Discovery

Search every configured scholarly source with multiple query variants. A paper discovered by several queries naturally receives a higher `discovery_count`, which is a strong centrality signal.

Fuzzy-match titles across sources, merge metadata and source lists, then rank by `discovery_count` descending, venue tier ascending, citation count descending, and year descending. Treat missing tier as 5 and missing citations as 0.

Venue tiers:

- Tier 1: NeurIPS, ICML, ICLR; ICASSP, Interspeech; ACL, NAACL, EMNLP; CVPR, ICCV, ECCV; major IEEE Transactions and SPL.
- Tier 2: ASRU, SLT, WASPAA, ODYSSEY, EUSIPCO, APSIPA, MMSP, Speech Communication, Computer Speech & Language, and JASA.
- Tier 3: other formal IEEE, ACM, or ISCA venues and workshops.
- Tier 4: unpublished or arXiv-only preprints.

Derive venue from OpenAlex `primary_location.raw_source_name`, raw type, or DOI patterns, and cross-check arXiv discoveries in OpenAlex for formal publication. Venue tier measures venue reputation; source quality separately classifies primary peer review, preprint, secondary synthesis, or unreliable material for claim-strength checks.

In `MERGE mode`, read existing `search_results.json`, increment discovery counts and source arrays on fuzzy duplicates, append new papers, update totals, and regenerate `search_results.md`.

## Access Ladder

Spend no more than 60 seconds obtaining any one paper, then fall through:

1. ar5iv/arXiv HTML when an arXiv ID exists;
2. open-access URL when available;
3. a material-role extraction already saved under `browser_extracts/`;
4. arXiv PDF when an ID exists;
5. OpenAlex abstract, or title and metadata when no abstract exists.

When neither arXiv nor open access exists, use a pre-extracted browser file if present, then jump directly to abstract. Do not repeatedly fetch a likely paywall.

## Reading Priority

- At least three discoveries but inaccessible: raise the recommendation to skim while remaining abstract-only.
- More than 100 citations: must read.
- 11–100 citations: skim.
- At most 10 citations: reference, upgraded to skim when discovered at least three times.
- Every Tier 1 paper is at least skim regardless of recent citation count.

## Cards and Reports

Each card records formal venue and tier, source quality, access depth, central claims with quotations where available, methods, data, metrics, limitations, code, and relationships. Never imply full-text support when only an abstract was read.

Use cards and report chapters to expose incomplete enrichment: when reference chaining is unavailable, label it and rely on card connections; when code search is unavailable, label it and use card code metadata. Return concise completion verdicts with paper counts and artifact paths.

Retain useful domain source lists, query patterns, and recurring access failures only through authorized memory and contextual agent judgment.
