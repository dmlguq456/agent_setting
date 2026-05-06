---
name: init-doc-strategy
description: Create an initial document strategy (rebuttal/write/review/report/proposal/presentation) based on analyzed reference materials
argument-hint: "<mode> --refs <folder> --output <artifact-dir> <task description>"
---

## Language Rule
- Think and reason in English internally.
- Write all user-facing output in Korean.

## Argument Parsing
Parse `$ARGUMENTS`:
- **mode**: first word — `rebuttal | write | review | report | proposal | presentation`
- **--refs <folder>**: path to reference materials
- **--output <dir>**: artifact output directory (`.claude_reports/documents/{date}_{name}/`)
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
Auto-detect from strategy scope:

| Level | Condition | Action |
|---|---|---|
| **Light** | review/presentation mode, or report with ≤3 refs | 1× 품질관리팀 (`model: "sonnet"`) |
| **Standard** | write/report/proposal mode, or rebuttal with ≤3 reviewers | 1× 품질관리팀 (default opus) |
| **Thorough** | rebuttal with ≥4 reviewers, or report/proposal with ≥10 refs | 2× 품질관리팀 in parallel (opus) |

## Post-Strategy Review Loop (max 2 revision rounds)
The log directory is the artifact root folder (parent of `strategy/`).
- `mkdir -p {log_dir}/strategy_reviews` before invoking QA.

After the 연구팀 agent returns:
1. **Invoke 품질관리팀:** "Review this document strategy for completeness and logical soundness. Strategy file: [path]. Mode: {mode}. For rebuttal mode, verify ALL reviewer points are addressed. Write review to: {log_dir}/strategy_reviews/round_{N}.md. Return ONLY the file path and a one-line verdict."
2. **Check verdict:** No 🔴 issues → proceed to Korean Version Generation. 🔴 issues found → re-invoke 연구팀 to revise (max 2 rounds).
3. **If 🔴 issues remain after 2 rounds**: Add to `## 미해결 이슈` section in the strategy, report to user.

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
