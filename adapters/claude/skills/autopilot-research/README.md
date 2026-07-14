# autopilot-research

> This README summarizes the portable capability for users and maintainers. The model-neutral contract lives under `<agent-home>/capabilities/`; `SKILL.md` in this directory provides shared guidance for runtime-specific projections.

## Overview

An external field-research pipeline that produces academic, technology, or market reports. It searches and analyzes papers, discovers code/model/dataset resources, and builds a field-specific implementation guide.

> **Scope:** produce Markdown analysis reports only. Do not create slide bodies, paper drafts, code, or PPTX. Hand those off to autopilot-draft or autopilot-code.

## Invocation

```text
/autopilot-research <topic> --mode academic|technology|market [--depth shallow|medium|deep] [--intensity direct|quick|standard|strong|thorough|adversarial] [--from search|analyze|report] [--no-clarify] [--no-figures]
```

## Modes

| Mode | Purpose | Output |
|---|---|---|
| academic | Core papers, methods, datasets, and model resources | Nine Markdown reports under `research/{topic}/`, including briefing, core papers, baselines, resources, implementation, and reading guide |
| technology | Standards, industry trends, tools, and vendor comparisons | Seven Markdown reports |
| market | Market, competitors, and adoption cases | Five Markdown reports |

## Artifact location

Write under `<artifact-root>/research/{topic}/` using the three-tier convention:

- **T1 root:** `00_briefing.md`, `01_core_papers.md`, through `06_reading_guide.md` or the mode-specific set
- **T2:** `cards/` for academic paper cards and `code_resources/` for model/repository cards
- **T3:** `_internal/search_results.json`, `_internal/browser_extracts/`, and `_internal/reviews/`

## Depth

- `shallow`: top 10–20 results, abstract only
- `medium` (default): prioritize citation count and venue tier; fully read items with citation count above 10
- `deep`: delegate paywalled pages to the material team and perform reference chaining

## Verification rigor

Rigor derives from `--intensity` under `CONVENTIONS §1.1`; there is no separate `--qa` axis.

- `quick`: one review pass and no fact checker
- `direct` → light/none: one fast review pass and no fact checker
- `standard` or `strong`: deep reviewer plus fast fact checker in parallel
- `thorough`: two deep reviewers plus fast fact checker
- `adversarial`: thorough plus an external adversary and claim verification

Concrete model mapping belongs to each runtime adapter. The Claude adapter maps fast to sonnet, deep to opus, and external adversary to Codex CLI.

## Resume points

- `search`: paper search, filtering, and tier assignment
- `analyze`: per-paper cards and reference chaining
- `report`: synthesis of the mode-specific Markdown report set

## Pipeline

1. Clarify scope with two to four questions only when the query is ambiguous.
2. Search sources such as Hugging Face, OpenAlex, arXiv, Google Scholar, and Semantic Scholar as the selected mode allows.
3. Choose reading depth from citations and venue tier; delegate eligible paywalled access to the material team.
4. Generate the report set and hand off through the `## Next Pipeline` table in `06_implementation.md` to autopilot-code, autopilot-draft, or refinement.

## Implicit chaining

- autopilot-draft discovers `research/{topic}/` by fuzzy-matching prompt keywords.
- autopilot-code and code-plan recognize research context implicitly.

---

*Portable capability contract: `<agent-home>/capabilities/autopilot-research.md`; shared skill guidance: `<agent-home>/skills/autopilot-research/SKILL.md`.*
