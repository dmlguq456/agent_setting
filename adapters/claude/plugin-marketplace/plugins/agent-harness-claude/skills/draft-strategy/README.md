# draft-strategy

> This README summarizes the portable capability for users and maintainers. The model-neutral contract lives under `<agent-home>/capabilities/`; `SKILL.md` in this directory provides shared guidance for runtime-specific projections.

## Overview

Creates an initial document strategy for rebuttal, paper, review, report, proposal, or presentation from analyzed reference materials. It delegates to `연구팀`, runs the selected review/source-check pass, and creates a language companion only when the user explicitly requests one, an external audience requires one, or the existing workflow already depends on one.

autopilot-draft invokes this skill automatically at Step 2. Direct use is uncommon.

> **Paragraph Cohesion Pre-Check (all modes, 2026-05-20):** Before writing a paste-ready LaTeX, Markdown, slide, or table block, analyze the target paragraph's full narrative flow and run four checks: (1) whether the substance is already stated, (2) whether the edit breaks the paragraph axis such as motivation → design → formalization, (3) whether it creates section-level redundancy, and (4) the edit type, in cohesion order: inline EDIT > REPLACE > INSERT > DROP. Reject mechanical “INSERT after sentence X,” AFTER text that becomes more verbose than BEFORE, and repeated substance across sections. See `SKILL.md` §Paragraph Cohesion Pre-Check.

> **Paper-mode camera-ready/major-revision rule (2026-05-19):** When converting a reviewer concern into a paper-body mutation, apply the natural-integration rule after the pre-check. Ask one question: *Can this be integrated naturally as a one- or two-sentence inline rewrite?* YES → use an M15-style inline rewrite: subsection opening, body-paragraph adjustment, and Figure cascade. NO → drop or defer to the Appendix; do not place rebuttal-format tables or Q&A blocks in the body. See `SKILL.md` §Natural-integration rule.

## Invocation

```
/draft-strategy <mode> --inputs <comma-separated-paths> --output <artifact-dir> <task description>
```

### Arguments

- **mode:** first word; one of `rebuttal | paper | review | report | proposal | presentation`
- **`--inputs`:** comma-separated paths from autopilot-draft Pre-flight Step 2 Input Discovery
- **`--output`:** artifact directory, `<artifact-root>/documents/{date}_{name}/`
- Remaining text: task description

Survey work belongs to autopilot-research: `/autopilot-research <topic> --mode academic|technology|market`. Discover the format spec automatically under `analysis_project/doc/{matching}/formats/`; there is no `--format-ref` flag.

## Pre-Check

Require these analysis files under `{output_dir}/analysis/`:

- `material_index.md` for every mode
- `reviewer_analysis.md` for rebuttal
- `ref_analysis.md` for paper, review, report, proposal, and presentation

If one is missing, fail: autopilot-draft Step 1 should have created it.

## Delegation — `연구팀`

Write the strategy from the mode-specific template. When an automatically discovered format spec exists, extract venue-specific sections, length, and tone.

### Core Sections by Mode

| Mode | Core sections |
|---|---|
| rebuttal | Meta-Review / Response Priority Matrix / reviewer details / Additional Experiments / Paper Revision / Tone / Risk |
| paper | Positioning / Contribution / Outline / Key Arguments / Related Work strategy / Experiment Design / Risk / Venue |
| review | Sections extracted from the venue format spec; common pattern: Summary / Strengths / Weaknesses / Questions / Missing References / Overall / Confidence |
| report | Objective / Key Findings / Analysis Framework / Section Plan / Evidence / Recommendations / Risk |
| proposal | Problem / Prior Art / Approach / Feasibility / Work Plan / Resources / Impact / Risk |
| presentation | Audience / Core Message / Story Arc / Slide Outline / Visuals / Q&A / Time / Delivery Notes |

### Quality Requirements

- Include every reviewer point in a rebuttal strategy; omission is a critical error.
- Justify severity classifications.
- Cite only real materials from paper analyses or discovered inputs; never fabricate.
- Make the strategy concrete and actionable.
- Apply venue-specific norms to academic work and domain-relevant industry practice to professional work.

`연구팀` writes the file directly. The orchestrator receives only the path and a three- to five-line summary.

## QA Scaling

Run quality and fact-check reviewers only when required by the selected graph and QA budget.

| Level | Condition | Quality reviewer | Parallel fact-checker |
|---|---|---|---|
| Light | review/presentation, or ≤3 inputs | 1 fast reviewer | Skip |
| Standard | paper/report/proposal, or rebuttal with ≤3 reviewers | 1 deep reviewer | 1 fast fact-checker |
| Thorough | rebuttal with ≥4 reviewers, or ≥10 inputs | 2 parallel deep reviewers | 1 fast fact-checker |

The fact-checker narrowly verifies venue, year, metric, and citation values against `analysis_project/paper/*.md`. The quality reviewer focuses on narrative arc, cohesion, and coverage of all reviewer points.

## Selected Post-Strategy Review Pass

Run at most two rounds:

1. Invoke the selected quality/source-check reviewers:
   - Quality output → `round_N_quality.md`
   - Fact-check output → `round_N_factcheck.md`
2. Handle verdicts:
   - No 🔴 in either review → generate a language companion only when the explicit audience or workflow contract requires one.
   - Quality 🔴 → ask `연구팀` to revise from quality findings.
   - Fact-check 🔴 → ask `연구팀` to revise with mandatory reference grounding and reread the named paper analyses.
   - Both → ask `연구팀` to revise from the combined findings.
3. If 🔴 remains after two rounds, record it under the functional compatibility heading `## 미해결 이슈`; tag factual residuals `[FACT-RESIDUAL]`.

## Conditional Language Companion

Skip companion generation by default. Invoke the editorial translation mode only when the user explicitly requests a second language, an external audience requires one, or the existing artifact workflow already contains and requires a companion. Preserve code identifiers, paper titles, citations, paths, and precise technical terms in their source language when translation would reduce clarity. A difference between artifact and conversation languages does not create a companion requirement.

---
*Portable capability contract: `<agent-home>/capabilities/draft-strategy.md`; shared skill guidance: `<agent-home>/skills/draft-strategy/SKILL.md`.*
