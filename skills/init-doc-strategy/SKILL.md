---
name: init-doc-strategy
description: Create an initial document strategy (rebuttal/write/review/report/proposal/presentation) based on analyzed reference materials
argument-hint: "<mode> --refs <folder> --output <artifact-dir> [--qa quick|light|standard|thorough] <task description>"
---

## Language Rule
- Think and reason in English internally.
- Write all user-facing output in Korean.

## Argument Parsing
Parse `$ARGUMENTS`:
- **mode**: first word — `rebuttal | write | review | report | proposal | presentation`
- **--refs <folder>**: path to reference materials
- **--output <dir>**: artifact output directory (`.claude_reports/documents/{date}_{name}/`)
- **--qa <level>**: `quick | light | standard | thorough` — overrides auto-detect (autopilot-doc propagates this)
- Remaining text: task description / context

## Pre-Check
- Verify analysis files exist in `{output_dir}/analysis/`:
  - `material_index.md` (required for all modes)
  - `reviewer_analysis.md` (required for rebuttal mode)
  - `ref_analysis.md` (required for write/review/report/proposal/presentation modes)
- If missing, report error — autopilot-doc Step 1 should have created these.

## Delegate to 연구팀
Invoke the **research-team** (연구팀) agent as a subagent with the following prompt:

````
Document strategy mode. Create an initial {mode} strategy document.

Mode: {mode}
Task: {task description}
Date: {YYYY-MM-DD}
Reference materials folder: {refs_folder}
Analysis directory: {output_dir}/analysis/
Save English strategy to: {output_dir}/strategy/strategy.md
Target venues (for academic modes): NeurIPS, ICML, ICLR, ICASSP, Interspeech, IEEE/ACM T-ASLP

## Inputs
1. Read all analysis files in the analysis directory (material_index.md, reviewer_analysis.md or ref_analysis.md)
2. Read relevant reference PDFs from the refs folder as needed for deeper understanding
3. Consider venue-specific conventions and expectations (for academic modes: rebuttal/write/review) or domain best practices and industry standards (for professional modes: report/proposal/presentation)

## Mode-Specific Instructions

### If mode = rebuttal
```markdown
---
type: rebuttal
venue: {venue if known, or "TBD"}
status: draft
date: {YYYY-MM-DD}
---

# Rebuttal Strategy: {paper title}

## 1. Meta-Review Summary
- Overall reviewer consensus (positive/mixed/negative), common themes
- Key strengths acknowledged (leverage these), critical weaknesses (prioritize these)
- Estimated acceptance likelihood and what would tip the balance

## 2. Response Priority Matrix
| Priority | Reviewer | Point | Severity | Category | Strategy |
|---|---|---|---|---|---|

Categories: Methodology, Experiments, Writing, Novelty, Comparison, Theory, Reproducibility
Strategies: Defend, Acknowledge+Mitigate, Partial-Agree+Extend, Concede+Revise, Clarify

## 3. Reviewer-by-Reviewer Detailed Strategy

### Reviewer {N} — Score: {X}, Confidence: {Y}
#### Sentiment: {positive/neutral/negative/hostile}
#### Key Leverage Points
#### Point-by-Point Response

##### R{N}.{M}: {summary of reviewer point}
- **Severity**: Critical / Major / Minor / Nitpick
- **Category**: {category}
- **Strategy**: {strategy type}
- **Core Argument**: {1-2 sentence rebuttal logic}
- **Supporting Evidence**: {what data/results/citations support the rebuttal}
- **Tone**: {defensive → neutral → concessive spectrum}
- **Draft Response Outline**:
  - Opening: {acknowledgment or framing}
  - Body: {main argument}
  - Evidence: {specific results to cite}
  - Closing: {what was done / will be done}

## 4. Additional Experiments Plan
| Experiment | Purpose | Addresses Points | Feasibility (days) | Priority |
|---|---|---|---|---|

## 5. Paper Revision Plan
| Section | Proposed Change | Addresses | Priority |
|---|---|---|---|

## 6. Response Tone & Style Guidelines
- Overall tone, per-reviewer adjustments, phrases to use/avoid, word count budget

## 7. Risk Assessment
- Weakest defense points, potential follow-up questions, contingency if experiments fail, AC perspective
```

### If mode = write
```markdown
---
type: write / venue: {target venue} / status: draft / date: {YYYY-MM-DD}
---
# Paper Writing Strategy: {topic}
## 1. Positioning Analysis — research gap, how this fills it, differentiation from closest work
## 2. Contribution Statement — primary (1 sentence), secondary, scope limitations
## 3. Paper Outline — section-by-section with key points and target page allocation
## 4. Key Arguments & Evidence — per section: argument + supporting evidence
## 5. Related Work Strategy — framing prior work to highlight novelty
## 6. Experiment Design Strategy — experiments proving claims, baselines, ablations
## 7. Risk & Weakness Mitigation — anticipated reviewer concerns and preemptive responses
## 8. Venue-Specific Considerations — page limits, formatting, reviewer expectations
```

### If mode = review
```markdown
---
type: review / status: draft / date: {YYYY-MM-DD}
---
# Paper/Document Review: {title}
## Summary / ## Strengths / ## Weaknesses / ## Questions for Authors
## Missing References / ## Minor Issues / ## Overall Assessment & Recommendation / ## Confidence
```

### If mode = report
```markdown
---
type: report / status: draft / date: {YYYY-MM-DD}
---
# Report Strategy: {topic}
## 1. Objective & Scope — what the report aims to establish, audience, constraints
## 2. Key Findings Summary — top 3-5 findings with evidence strength rating
## 3. Analysis Framework — methodology for organizing and presenting findings
## 4. Section Plan — section-by-section outline with key points and evidence mapping
## 5. Data & Evidence Inventory — what data supports each finding, gaps to note
## 6. Recommendations Strategy — how to frame actionable recommendations
## 7. Risk & Limitations — caveats, data quality issues, scope limitations
```

### If mode = proposal
```markdown
---
type: proposal / status: draft / date: {YYYY-MM-DD}
---
# Proposal Strategy: {topic}
## 1. Problem Statement — clear articulation of the problem and its significance
## 2. Prior Art & Context — what exists, why it's insufficient
## 3. Proposed Approach — technical plan, innovation, differentiation
## 4. Feasibility Evidence — preliminary results, related successes, team capability
## 5. Work Plan — phases, milestones, deliverables, timeline
## 6. Resource Plan — team, budget, equipment, data needs
## 7. Expected Impact — outcomes, metrics for success, broader implications
## 8. Risk Mitigation — key risks and contingency plans
```

### If mode = presentation
> Note: This strategy document serves as the direct slide production guide. No separate draft is generated for presentation mode.

```markdown
---
type: presentation / status: draft / date: {YYYY-MM-DD}
---
# Presentation Strategy: {topic}
## 1. Audience Analysis — who they are, what they know, what they need
## 2. Core Message — one sentence the audience should remember
## 3. Story Arc — narrative structure (hook → problem → solution → evidence → call-to-action)
## 4. Slide Outline — slide-by-slide plan with key visuals and talking points
## 5. Key Visuals Strategy — diagrams, charts, demos to include
## 6. Anticipated Questions — likely Q&A and prepared responses
## 7. Time Allocation — per-section timing budget
## 8. Delivery Notes — tone, pacing, emphasis points
```

## Quality Requirements
Every reviewer point must appear in rebuttal strategy (missing a point is a critical error). Severity classification must be justified. All citations must reference actual materials in the refs folder — do NOT fabricate. Strategy must be actionable with specific plans, not vague advice. For academic modes (rebuttal/write/review): apply venue-specific norms (e.g., NeurIPS rebuttal length limits, ICASSP culture). For professional modes (report/proposal/presentation): apply industry best practices relevant to the domain.

Write the strategy file directly. Return ONLY the file path and a 3-5 line Korean summary of the strategy. Do NOT return the strategy content itself.
````

The agent writes the strategy file directly; the orchestrator only receives paths and a summary.

## QA Scaling
Auto-detect from strategy scope. Two reviewer roles run **in parallel** at Standard+:
- **Quality reviewer**: completeness / logical soundness / venue norms / reviewer-coverage (rebuttal)
- **Fact-checker** (NEW): refs/cards/PDFs verbatim 대조, citation/venue/metric/year 검증

| Level | Condition | Quality reviewer | Fact-checker (parallel) | Max rounds |
|---|---|---|---|---|
| **Quick** | (manual via `--qa quick` only) | 1× 품질관리팀 (`model: "sonnet"`), spot-check만 | _skip_ | **1 (no re-invoke even on 🔴)** |
| **Light** | review/presentation mode, or report with ≤3 refs | 1× 품질관리팀 (`model: "sonnet"`) | _skip_ | 2 |
| **Standard** | write/report/proposal mode, or rebuttal with ≤3 reviewers | 1× 품질관리팀 (default opus) | **1× 품질관리팀 fact-check (`model: "sonnet"`)** | 2 |
| **Thorough** | rebuttal with ≥4 reviewers, or report/proposal with ≥10 refs | 2× 품질관리팀 in parallel (opus) | **1× 품질관리팀 fact-check (`model: "sonnet"`)** | 2 |

**Why Sonnet for fact-checker**: refs/cards verbatim 대조는 _창의적 판단_이 아닌 _단순 매칭 작업_이라 Sonnet으로 충분, 비용 효율적.

## Post-Strategy Review Loop (max 2 revision rounds; quick = 1 round)
The log directory is the artifact root folder (parent of `strategy/`).
- `mkdir -p {log_dir}/strategy_reviews` before invoking QA.

After the 연구팀 agent returns:
1. **Invoke quality + fact-check reviewers in parallel** (single message with multiple Agent calls per QA Scaling):

   **Quality reviewer prompt** (opus or sonnet per level):
   ```
   Review this document strategy for completeness and logical soundness.
   Strategy file: [path]. Mode: {mode}.
   For rebuttal mode, verify ALL reviewer points are addressed.
   Do NOT verify individual fact citations (model venue/year/metric) — that's the fact-checker's role.
   Write review to: {log_dir}/strategy_reviews/round_{N}_quality.md.
   Return ONLY the file path and a one-line verdict.
   ```

   **Fact-checker prompt** (sonnet, parallel — Standard/Thorough only):
   ```
   You are a fact-check focused reviewer — NOT narrative quality.
   Strategy file: [path]. Mode: {mode}. Refs folder: {refs_folder}.

   For every domain claim in the strategy (citation / model name / venue / year /
   metric / dataset / lineage / classification), open the corresponding ground-truth
   source and verbatim compare:
   - Paper cards: {refs_folder}/cards/*.md (if exists)
   - Reference PDFs: {refs_folder}/*.pdf (only if cards lack the specific fact)
   - Reviewer comments (rebuttal mode): {analysis_dir}/reviewer_analysis.md

   Output a single table (no narrative):
   | Section | Claim in strategy | Source (file:line or section) | Match (✅/❌) | Severity (🔴/🟡) |

   Do NOT comment on completeness, narrative arc, or strategic soundness
   — that's the quality reviewer's job. Stay narrowly on fact verification.

   Cost-aware mode (sonnet): table-only output. Limit to ~30 most material claims.

   Write to: {log_dir}/strategy_reviews/round_{N}_factcheck.md.
   Return ONLY path + one-line verdict.
   ```

2. **Check verdict (both reviewers):**
   - **No 🔴 from either**: proceed to Korean Version Generation.
   - **qa_level == quick**: after round 1, exit regardless of 🔴. Add 🔴 issues to `## 미해결 이슈` section in the strategy. Proceed to Korean Version Generation.
   - **🔴 from quality reviewer**: re-invoke 연구팀 with quality findings (max 2 rounds).
   - **🔴 from fact-checker**: re-invoke 연구팀 with **mandatory ref-grounding** (re-read named cards/PDFs). Max 2 rounds.
   - **🔴 from both**: re-invoke 연구팀 with combined findings.
3. **If 🔴 issues remain after 2 rounds**: Add to `## 미해결 이슈` section in the strategy, report to user. Tag fact-check residuals with `[FACT-RESIDUAL]`.

## Korean Version Generation
After review loop completes, invoke 연구팀 one final time:
```
Translate mode. Create the Korean version of the finalized strategy.
English strategy file: {strategy_path}
Save Korean version to: {same directory}/strategy_ko.md
Create a full Korean translation (NOT a summary). All sections with same detail.
Code identifiers, paper titles, and technical terms stay in English.
Return ONLY the file path.
```
Then report to the user: English and Korean strategy paths, strategy summary, and QA verdict.

## Task
$ARGUMENTS
