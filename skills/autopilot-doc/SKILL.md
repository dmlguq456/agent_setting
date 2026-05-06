---
name: autopilot-doc
description: "Document strategy & draft pipeline — analyze-refs → strategy → review → draft → draft-review. All 7 modes produce both strategy AND draft (markdown only). review mode requires `--review-format` (fail-fast at pre-flight if missing). presentation mode produces slide-by-slide markdown; PPTX export is NOT supported by this pipeline (use PowerPoint directly). `--refs` accepts an autopilot-research artifact_dir to chain pipelines."
argument-hint: "<mode> <task description> [--refs <folder>] [--type <survey-type>] [--review-format <name|path>] [--qa light|standard|thorough] [--user-refine] [--from analyze|strategy|strategy-refine|draft|draft-refine|finalize]"
---

## Language Rule
- Write user-facing output in Korean. (Material analysis results and pipeline_summary.md are written directly in the artifacts — no separate user output needed for those steps.)

## Argument Parsing
Parse `$ARGUMENTS` for mode, flags, and task description:

**Mode** (first word, required):
- `rebuttal` — Rebuttal strategy for reviewer comments
- `write` — Paper writing strategy (outline, positioning, contributions)
- `review` — Paper/document review (as reviewer: strengths/weaknesses/questions). Produces strategy + full review draft (OpenReview-ready).
- `survey` — General-purpose research survey with **active source discovery**: literature, market, technology, product, or company analysis. Searches for sources automatically; `--refs` is optional supplementary input.
- `report` — Technical report / white paper (findings, analysis, recommendations)
- `proposal` — Research or project proposal (problem, approach, plan, budget)
- `presentation` — Presentation strategy (story arc, slide structure, key messages) + slide-by-slide markdown draft. PPTX export is NOT performed by this pipeline (markdown-only); use PowerPoint manually with the lab template.

**`--refs <folder>`** — path to reference materials folder:
- Contains: PDFs, reviewer comments (txt/md), original paper, conference guidelines, data files, etc.
- **Required** for: rebuttal, write, review, report, proposal, presentation.
- **Optional** for: survey (survey mode discovers sources automatically; `--refs` provides supplementary materials to merge with search results).
- If omitted and mode is NOT survey: ask the user for the folder path. Do NOT assume a default location.

**`--qa <level>`** — override QA intensity for the pipeline:
- `--qa light` → 연구팀 review uses sonnet, single-pass review
- `--qa standard` → 연구팀 review uses opus, single-pass review
- `--qa thorough` → 연구팀 review uses opus, parallel reviewers (domain expert + methodology reviewer), cross-validation against all reference materials **(default)**
- If omitted, defaults to `thorough`.
- **Propagation**: Pass `--qa <level>` to init-doc-strategy and refine-doc-strategy as an argument flag.

**`--user-refine`** (boolean flag) — pause at refine points so the user can add their own `<!-- memo: ... -->` comments on top of 연구팀's memos before refine-doc-strategy runs.

Pause behavior: after 연구팀 writes memos at Step 3 (strategy review) or Step 5 (draft review), do NOT invoke refine-doc-strategy. Instead:
1. Update `pipeline_state.yaml` at `{strategy_folder}/` with `user_refine: true`, `paused_at_stage: <strategy-refine|draft-refine>`.
2. Print to user (Korean) the memo file path and the resume command:
   ```
   연구팀 메모가 {ko_path}에 기록되었습니다.
   직접 메모를 추가한 뒤 다음 명령으로 재개하세요:
       /autopilot-doc --mode {mode} --from <strategy-refine|draft-refine> <strategy_folder>
   ```
3. Exit. Do NOT write `pipeline_summary.md` (pipeline is paused, not terminated).

If 연구팀 added no memos, the pause is skipped (nothing to refine).

**`--from <stage>`** — resume the pipeline at a specific stage. Stages:
- `analyze` — Step 1 (Material Analysis); for survey mode also re-runs Step 0 (Source Discovery)
- `strategy` — Step 2 (init-doc-strategy)
- `strategy-refine` — Step 3 wrapper: 연구팀 review + (user memos if `--user-refine`) + refine-doc-strategy on the strategy
- `draft` — Step 4 (Draft Generation)
- `draft-refine` — Step 5 wrapper: 연구팀 review + (user memos if `--user-refine`) + refine-doc-strategy on the draft
- `finalize` — Step 6 (Pipeline Summary)

When resuming with `--from`, the positional argument should be either the artifact directory path or a fuzzy-matchable short name. The orchestrator resolves it via the same fuzzy lookup used by Plan Resolution in autopilot-code: `ls -d .claude_reports/documents/*$ARG* 2>/dev/null`. Read `pipeline_state.yaml` to recover `mode`, `qa_level`, `refs_folder`, `user_refine`. CLI flags override state file; missing flags inherit from state.

**`--type <survey-type>`** — sub-type for survey mode (only used when mode=survey):
- `literature` (default) — academic literature survey
- `market` — market landscape, competitors, trends
- `technology` — technology comparison, maturity assessment
- `product` — product analysis, feature comparison
- `company` — company research, strategy analysis
- If omitted and mode=survey, defaults to `literature`.
- Ignored for all non-survey modes.

**`--review-format <format>`** — review form/template (**REQUIRED** for mode=review; pipeline aborts if missing):
- Built-in venue specs (preset name → internal section template):
  - `openreview` — Summary / Strengths and Weaknesses / Soundness, Presentation, Significance, Originality (1-4) / Questions for Authors / Limitations / Overall Recommendation (1-6) / Confidence (1-5) / Compliance with policies. Used by NeurIPS, ICML, ICLR, AAAI, etc.
  - `acl-arr` — ACL Rolling Review: Paper Summary / Summary of Strengths / Summary of Weaknesses / Comments, Suggestions and Typos / Confidence / Soundness (1-5) / Excitement (1-5) / Reproducibility (1-5) / Ethical Concerns / Reviewer Confidence
  - `ieee-conf` — IEEE conference style (ICASSP, INTERSPEECH, etc.): narrative review with Strengths / Weaknesses / Detailed Comments / Recommendation (Accept/Reject/Borderline) / Confidence
  - `journal` — Generic journal review (T-ASLP, JASA, IEEE TPAMI, etc.): free-form narrative covering Significance / Originality / Technical Quality / Clarity / Recommendation (Accept/Minor Revision/Major Revision/Reject) + Detailed comments by section
- `<path>` — path to a custom review format spec file (markdown/txt/pdf) describing the venue's required sections. The file MUST exist; verified at Step 0 pre-flight.
- **NO default** — must be explicitly chosen. If `--review-format` is omitted in review mode, the pipeline aborts at Step 0 with a clear error message and the list of built-in options.
- If reviewer guidelines PDF/doc is also found in `--refs`, the agent layers those constraints on top of the chosen template.
- Ignored for all non-review modes.

The remaining text (after removing mode and flags) is the task description.

> **Note on presentation mode**: This pipeline produces only the slide-by-slide markdown draft (`draft/draft.md` and `draft/draft_ko.md`). PPTX export is **NOT supported** because pandoc + Korean lab templates have unreliable compatibility (font/layout drift, OOXML strictness). The user converts markdown → PPT manually in PowerPoint using their lab template directly.

## Decision Defaults (no autonomy gating)

The pipeline runs with sane defaults and only pauses on genuinely ambiguous or destructive situations.

| Decision Point | Default Behavior |
|---|---|
| Confirm material analysis | Auto-proceed. |
| Missing refs folder | **Always ask** at pre-flight (mode-dependent). |
| No reviewer comments for rebuttal | **Always ask** at pre-flight. |
| Strategy review → memos added | Auto-refine (or pause for user-memo if `--user-refine` is set). |
| Draft review → memos added | Auto-refine (or pause for user-memo if `--user-refine` is set). |
| `--review-format` missing (review mode) | Abort at pre-flight. |
| Reviewer guidelines absent in refs (review mode) | Use built-in spec only; inform user. |
| Survey search results review | Auto-proceed. |
| Survey search found 0 results | **Always ask** — proceed with `--refs` only or adjust query. |

**Logging**: When the pipeline pauses (missing required input, 0 search results, or `--user-refine`), record the event for the Decision Points table in `pipeline_summary.md`. Auto-decisions are not individually logged.

## pipeline_state.yaml

Written/updated at `{strategy_folder}/pipeline_state.yaml` after each completed stage. Used by `--from` resume:

```yaml
pipeline: autopilot-doc
mode: presentation
qa_level: thorough
user_refine: true
refs_folder: <path>
review_format: <name|path or null>
survey_type: <type or null>
last_completed_stage: strategy        # one of: discovery, analyze, strategy, strategy-refine, draft, draft-refine, finalize
paused_at_stage: strategy-refine      # set only when --user-refine triggered a pause
artifact_dir: <abs path>
```

CLI flags on resume override stored values. After the pause is consumed (refine completes), clear `paused_at_stage` and update `last_completed_stage`.

## Refs Folder Convention
The `--refs` folder is user-specified (no default). May contain PDFs, txt/md reviewer comments, notes, data files, subdirectories. On first invocation, list contents and confirm with the user. For rebuttal mode, warn if no reviewer comments are found.

## Artifact Structure
All outputs go to:
```
.claude_reports/documents/{YYYY-MM-DD}_{short-name}/
├─ strategy/
│  ├─ strategy.md          (English strategy document)
│  └─ strategy_ko.md       (Korean strategy document)
├─ draft/                   (generated for: rebuttal, write, report, proposal, survey, review, presentation)
│  ├─ draft.md             (English draft; for presentation: slide-by-slide markdown)
│  └─ draft_ko.md          (Korean draft)
├─ discovery/               (survey mode only: search results)
│  └─ search_results.json  (discovered sources with metadata)
├─ analysis/
│  ├─ reviewer_analysis.md  (rebuttal: per-reviewer breakdown)
│  ├─ ref_analysis.md       (reference material analysis)
│  └─ material_index.md     (inventory of all input materials)
├─ strategy_reviews/        (QA and 연구팀 strategy reviews)
├─ draft_reviews/           (QA and 연구팀 draft reviews)
└─ pipeline_summary.md
```

## Pipeline

### Pre-flight Validation [ALL modes — runs first, before any work]
Validate mode-specific required inputs. If any check fails, **abort immediately** with a clear error message — do NOT create the artifact directory or invoke any sub-skills/agents. The user must rerun with the missing input.

**Universal checks** (all modes):
1. Mode is one of the 7 supported modes (rebuttal / write / review / survey / report / proposal / presentation). Otherwise abort: "Unknown mode: {mode}. Supported: ...".
2. For all modes except `survey`: `--refs` is provided AND folder exists. Otherwise abort: "--refs <folder> is required for {mode} mode and was not found at {path}."

**Mode-specific checks**:

- **review mode** — `--review-format` is REQUIRED. Validate:
  - If value is one of `openreview` / `acl-arr` / `ieee-conf` / `journal` → OK (built-in spec).
  - Else treat as a path → `os.path.exists(value)` must be True AND extension must be one of `.md`, `.txt`, `.pdf`. Otherwise abort.
  - If flag is missing entirely → abort with: "review mode requires --review-format. Built-in options: openreview, acl-arr, ieee-conf, journal. Or provide a path to a custom format spec (.md/.txt/.pdf)."

- **presentation mode** — no extra pre-flight requirements. PPTX export is NOT performed; user converts the markdown draft to PPT manually.

- **rebuttal mode** — refs folder must contain at least one reviewer-comment file (txt/md/pdf with reviewer-style content detected by filename or content scan). If none found, ask the user before proceeding.

- **survey mode** — if `--refs` not provided, no check needed (search will discover sources).

**Abort behavior**:
- Print the error message in Korean to the user.
- Do NOT call `mkdir`, do NOT invoke any sub-skill, do NOT write `pipeline_summary.md`.
- Exit with status: aborted (pre-flight).

After all pre-flight checks pass: create `artifact_dir` and proceed to Step 0 (survey) or Step 1 (other modes).

### Step 0: Source Discovery [survey mode only — skip for all other modes]
**Applicable modes**: survey only. All other modes skip to Step 1.

Survey mode actively searches for sources instead of relying solely on `--refs`. The search approach adapts to `--type`:

**0a. Query Expansion**
Generate 2-3 synonym/alternative queries from the task description using LLM knowledge:
- `literature`: academic terminology variants (e.g., "speech enhancement" → "speech denoising", "noise reduction")
- `market`: industry/business terms (e.g., "음성 향상 시장" → "speech enhancement market", "audio AI industry")
- `technology`: technical variants + product names
- `product`: product category + brand names
- `company`: company name + subsidiaries + competitors

**0b. Multi-Source Search**
Invoke the **research-team** (연구팀) agent for source discovery:

```
Research survey mode: Source discovery for {survey_type} survey.

Queries: {queries_list}
Original query: {original_query}
Survey type: {survey_type}
Output directory: {artifact_dir}/discovery/
{If --refs: 'Supplementary materials folder: {refs_folder}'}

Search sources by survey type:
- literature: HF paper_search, Semantic Scholar, arXiv, WebSearch (Google Scholar)
- market: WebSearch (industry reports, news, analyst coverage), WebFetch (company sites)
- technology: WebSearch (tech blogs, benchmarks, documentation), HF paper_search (if academic)
- product: WebSearch (product reviews, comparisons, official sites), WebFetch
- company: WebSearch (company info, press releases, financials), WebFetch (investor pages)

Max results per source per query: 10
Timeout: 3 minutes per source; skip on timeout.

Save results to: {artifact_dir}/discovery/search_results.json
Schema: {"query": "string", "survey_type": "string", "date": "YYYY-MM-DD",
  "sources_used": ["string"], "total_results": int,
  "results": [{"title": "string", "url": "string", "source": "string",
    "year": int|null, "snippet": "string", "relevance_score": float|null}]}

Return file path + a brief Korean summary of what was found.
```

**0c. Post-Search Validation**
1. Read `search_results.json` — verify valid JSON and non-empty results
2. If 0 results found → ask the user whether to proceed with `--refs` only or adjust the query.
3. Otherwise present a brief search summary (N results from M sources) and auto-proceed.

**0d. Reference Chaining** (literature type only)
For literature surveys, extract references from top-ranked papers and discover additional sources:
1. Read top 5 papers from search results (by citation count or relevance)
2. Extract cited references and check if any important ones are missing from results
3. If new relevant references found: run one additional search round with extracted keywords
4. Merge into `search_results.json` (update discovery_count for duplicates)

**0e. Merge with --refs**
If `--refs` was provided, merge:
1. Inventory `--refs` folder → add to `search_results.json` as source="user_provided"
2. Deduplicate by title similarity
3. User-provided materials get priority (higher relevance score)

After Step 0, proceed to Step 1 with the combined discovery results as the analysis input.

### Step 1: Material Analysis
Read and catalog all materials from refs folder (non-survey modes) or discovery results (survey mode).

1. **Inventory**: List all files with brief descriptions. Write to `analysis/material_index.md`.
2. **Analyze by mode**:
   - **rebuttal**: Parse reviewer comments → `analysis/reviewer_analysis.md` (per-reviewer, per-point breakdown with severity classification)
   - **write**: Analyze reference papers → `analysis/ref_analysis.md` (methods, gaps, positioning opportunities)
   - **review**: Analyze target paper/document → `analysis/ref_analysis.md` (methodology assessment, quality analysis)
   - **survey**: Analyze all reference materials → `analysis/ref_analysis.md` (categorization, comparison, gap analysis — adapted to survey type: literature/market/technology/product/company)
   - **report**: Analyze source data/papers → `analysis/ref_analysis.md` (findings, evidence assessment, data quality)
   - **proposal**: Analyze related work and context → `analysis/ref_analysis.md` (prior art, feasibility evidence, competitive landscape)
   - **presentation**: Analyze source document/paper → `analysis/ref_analysis.md` (key messages, audience analysis, narrative structure)
3. Read PDF files using the Read tool. For large PDFs (>10 pages), read in page ranges.
4. Present the analysis summary briefly and auto-proceed to Step 2 — no confirmation required.

### Step 2: init-doc-strategy
Invoke Skill: `init-doc-strategy` with args: `<mode> --refs <folder> --output <artifact-dir> [--type <survey-type>] <task description>`. Wait for completion.

### Step 3: Strategy Review (연구팀 as domain expert)
1. Resolve strategy paths:
   - `strategy_folder` = `.claude_reports/documents/{YYYY-MM-DD}_{short-name}/`
   - `en_strategy_path` = `{strategy_folder}/strategy/strategy.md`
   - `ko_strategy_path` = `{strategy_folder}/strategy/strategy_ko.md`

2. Invoke reviewers based on `--qa` level:

   **`light`** — Single 연구팀 agent (sonnet model):
   - One-pass review focusing on critical issues only.
   - Review log: `{strategy_folder}/strategy_reviews/research_review.md`

   **`standard`** — Single 연구팀 agent (opus model):
   - Thorough single-pass review.
   - Review log: `{strategy_folder}/strategy_reviews/research_review.md`

   **`thorough`** (default) — Two parallel 연구팀 agents (opus model):
   - **Reviewer A (Domain Expert)**: Cross-checks strategy against reference materials, domain conventions (academic venues for paper modes: NeurIPS, ICML, ICLR, ICASSP, Interspeech, T-ASLP; industry standards for report/proposal/presentation modes), and completeness of coverage.
     - Review log: `{strategy_folder}/strategy_reviews/research_review_domain.md`
   - **Reviewer B (Methodology Reviewer)**: Evaluates logical consistency, persuasiveness of arguments, experimental design soundness, and identifies potential weaknesses an adversarial reviewer would exploit.
     - Review log: `{strategy_folder}/strategy_reviews/research_review_methodology.md`
   - Both reviewers write `<!-- memo: ... -->` comments in the Korean strategy.
   - After both complete, merge memos and deduplicate.

   Common prompt for all levels:
   ```
   Review this document strategy as the user's domain expert proxy.
   Mode: {mode} | KO strategy: {ko_strategy_path} | EN strategy: {en_strategy_path}
   Analysis: {strategy_folder}/analysis/ | Refs: {refs_folder} | Log: {review_log_path}

   Cross-check: actual refs/reviewer comments, domain conventions,
   logical consistency, completeness (any missed reviewer points or gaps?).
   Write memos as `<!-- memo: ... -->` in the Korean strategy.
   Write a structured review log to the log file.
   Return a summary of memos added (or "no issues found").
   ```

3. If memos were added:
   - **`--user-refine` pause**: if the flag is set, update `pipeline_state.yaml` (`user_refine: true`, `paused_at_stage: strategy-refine`), print the resume command (`/autopilot-doc --mode {mode} --from strategy-refine {strategy_folder}`), and exit. Do NOT invoke refine-doc-strategy.
   - Otherwise: invoke Skill `refine-doc-strategy` with the Korean strategy path as args.
4. If no memos: Skip to Step 4. (When resumed via `--from strategy-refine`, the orchestrator skips the 연구팀 review and runs refine-doc-strategy directly using the pre-existing memos.)

### Step 4: Draft Generation
**Applicable modes**: rebuttal, write, report, proposal, survey, review, presentation. (All modes generate drafts.)

1. Verify strategy is finalized: `{strategy_folder}/strategy/strategy.md` exists and has no `## 미해결 이슈` section (or issues are acceptable).
2. Invoke the **research-team** (연구팀) agent as a subagent:

```
Draft generation mode. Generate a document draft based on the finalized strategy.

Mode: {mode}
Task: {task description}
Strategy (EN): {en_strategy_path}
Strategy (KO): {ko_strategy_path}
Analysis directory: {strategy_folder}/analysis/
Reference materials: {refs_folder}
Save English draft to: {strategy_folder}/draft/draft.md
Save Korean draft to: {strategy_folder}/draft/draft_ko.md

Read the strategy document and all analysis files. Generate a complete first draft following the mode-specific structure below. The draft should be a working document ready for user editing — not a summary of the strategy.

## Mode-Specific Draft Structure

### rebuttal
- Frontmatter: type, venue, status: draft, date
- Per-reviewer response sections following the strategy's priority matrix
- Each response: acknowledgment → core argument → evidence → conclusion
- Tone calibrated per the strategy's tone guidelines
- Additional experiments section with preliminary descriptions
- Revision summary table

### write
- Frontmatter: type, venue, status: draft, date
- Full paper outline with section drafts:
  - Abstract (structured: background → gap → method → results → impact)
  - Introduction (hook → context → gap → contribution → outline)
  - Related Work (organized by strategy's framing)
  - Method (following strategy's outline, with placeholder equations)
  - Experiments (setup → results → ablation, with table skeletons)
  - Conclusion
- Figure/table placeholders with captions

### report
- Frontmatter: type, status: draft, date
- Executive Summary
- Introduction / Background
- Methodology / Approach
- Findings / Analysis (with data tables, charts description)
- Discussion
- Recommendations (prioritized, actionable)
- Appendices (if needed)

### proposal
- Frontmatter: type, status: draft, date
- Executive Summary
- Problem Statement / Motivation
- Proposed Approach / Technical Plan
- Preliminary Results / Feasibility Evidence
- Timeline & Milestones
- Resource Requirements / Budget (if applicable)
- Expected Outcomes / Impact
- Risk Assessment

### survey
- Frontmatter: type, survey_type, status: draft, date
- For literature survey: Taxonomy → Chronological Development → Detailed Comparison → Gaps → Future Directions
- For market survey: Market Overview → Competitor Analysis → Trend Analysis → Opportunity Assessment → Recommendations
- For technology survey: Technology Landscape → Comparison Matrix → Maturity Assessment → Adoption Recommendations
- For product survey: Product Overview → Feature Comparison → User/Market Fit → Recommendations
- For company survey: Company Profile → Strategy Analysis → Competitive Position → Outlook

### review
Adapt the section structure to `--review-format` (default: openreview). If reviewer guidelines exist in refs/, follow those; otherwise use the format-specific template below.

**Frontmatter** (always): type, venue, paper_title, status: draft, date, review_format

**`openreview` (default — NeurIPS/ICML/ICLR/AAAI)**:
- Summary (3-5 sentences: paper's core contribution, approach, main results)
- Strengths and Weaknesses
  - Strengths (4-6 specific, evidence-anchored points)
  - Weaknesses (4-6 specific, evidence-anchored points; tie each to a section/figure/table where possible)
- Soundness (1-4): score + 1-2 sentence justification
- Presentation (1-4): score + justification
- Significance (1-4): score + justification
- Originality (1-4): score + justification
- Questions for Authors (3-7 numbered, actionable; prioritize ones that could change the score)
- Limitations (does the paper acknowledge them? are there unaddressed ones?)
- Overall Recommendation (1-6, e.g., "4: Weak Accept") + 2-3 sentence justification
- Confidence (1-5)
- Compliance With LLM Reviewing Policy: Affirmed (boilerplate)
- Code Of Conduct Acknowledgement: Affirmed (boilerplate)

**`acl-arr`**:
- Paper Summary
- Summary of Strengths
- Summary of Weaknesses
- Comments, Suggestions and Typos (line-anchored where possible)
- Confidence
- Soundness (1-5)
- Excitement (1-5)
- Reproducibility (1-5)
- Ethical Concerns (Yes/No + explanation)
- Reviewer Confidence

**`ieee-conf` (ICASSP, INTERSPEECH, etc.)**:
- Brief Summary
- Strengths
- Weaknesses
- Detailed Comments (ordered by significance; include actionable suggestions)
- Recommendation (Accept / Borderline Accept / Borderline Reject / Reject)
- Confidence (Low / Medium / High)

**`journal` (T-ASLP, JASA, IEEE TPAMI, etc.)**:
- Significance and Originality
- Technical Quality and Soundness
- Clarity of Presentation
- Recommendation (Accept / Minor Revision / Major Revision / Reject)
- Detailed Comments by Section (per-section bullet points)
- Specific Comments (line-anchored or page-anchored)
- Required Changes / Suggested Changes (split if revision recommended)

**Custom path**: read the format spec file and produce a draft that satisfies its required sections.

### presentation
Generate slide-by-slide markdown. **PPTX export is NOT performed** — the user will copy/paste content into PowerPoint manually using their lab template.

- **Frontmatter** (YAML): title, subtitle (optional), author, date
- **Slide structure**: each slide is a level-1 heading (`# Slide title`). Use the slide structure from the strategy doc as the source of truth for chapter divisions and per-slide content.
- **Required sections**:
  1. Title slide (frontmatter — first slide content)
  2. Outline / Table of Contents (`# Outline` or `# 목차`)
  3. Section dividers (`# Ch.1 — chapter title`, `# Ch.2 — ...`)
  4. Per-slide content slides (with concise bullets, tables, image placeholders `[FIGURE: description]`, code blocks where useful)
  5. Conclusion / Take-home messages
  6. Q&A / Thank you / References
- **Speaker notes**: every content slide should have a clearly-marked speaker note section (e.g., `> **Speaker note**: ...` blockquote) bridging slide content with verbal narration
- **Slide budget**: derive from strategy doc's time allocation (e.g., 60-min talk = 30-50 slides; 20-min conference talk = 12-18 slides). Mark backup slides with `# Backup — title` after the main flow.
- **Visual placeholders**: use `[FIGURE: brief description of what should be drawn]` for diagrams that the user will add manually in PowerPoint.
- **References slide**: list key paper citations near the end (typically `# References`).

## Quality Requirements
- Every claim must trace back to a specific reference in the refs folder or analysis.
- Do NOT fabricate citations, data, or results.
- Mark uncertain or placeholder content with `[TODO: ...]`.
- **Mode-specific completeness criteria**:
  - **rebuttal**: 90%+ — every reviewer point MUST have a drafted response (hard constraint). Missing a point is a critical error.
  - **write/report/proposal**: 70-80% — all sections with substantive content, no heading-only sections.
  - **survey**: 60-70% — flexible based on reference volume. Comparison matrices and taxonomy structure are required; individual item details may use [TODO].
  - **review**: 80%+ — every required section per `--review-format` must be filled with concrete claims. Strengths/weaknesses must reference specific paper sections/figures/tables. Score justifications are mandatory.
  - **presentation**: 70-80% — every slide has a title and at least one substantive bullet/figure placeholder/table. Speaker notes for ≥80% of content slides. Slide count within ±20% of strategy's target.

Write both files directly. Return ONLY the file paths and a 3-5 line Korean summary.
```

3. **IMPORTANT**: Do NOT read, re-write, or duplicate the draft files yourself. The agent writes them directly.

### Step 5: Draft Review (연구팀 as QA)
**Applicable modes**: rebuttal, write, report, proposal, survey, review, presentation. (All modes that generated drafts.)

1. Resolve draft paths:
   - `en_draft_path` = `{strategy_folder}/draft/draft.md`
   - `ko_draft_path` = `{strategy_folder}/draft/draft_ko.md`

2. Invoke reviewers based on `--qa` level (same scaling as Step 3 strategy review):

   **`light`** — Single 연구팀 agent (sonnet model):
   - One-pass review focusing on critical issues only.
   - Review log: `{strategy_folder}/draft_reviews/draft_review.md`

   **`standard`** — Single 연구팀 agent (opus model):
   - Thorough single-pass review.
   - Review log: `{strategy_folder}/draft_reviews/draft_review.md`

   **`thorough`** — Two parallel 연구팀 agents (opus model):
   - **Reviewer A (Content Expert)**: Cross-checks draft against strategy, verifies all strategy points are addressed, checks factual accuracy against refs.
     - Review log: `{strategy_folder}/draft_reviews/draft_review_content.md`
   - **Reviewer B (Quality Reviewer)**: Evaluates writing quality, logical flow, completeness, identifies gaps and weak arguments.
     - Review log: `{strategy_folder}/draft_reviews/draft_review_quality.md`
   - Both reviewers write `<!-- memo: ... -->` comments in the Korean draft.
   - After both complete, merge memos and deduplicate.

   Common prompt for all levels:
   ```
   Review this document draft as the user's domain expert proxy.
   Mode: {mode} | KO draft: {ko_draft_path} | EN draft: {en_draft_path}
   Strategy: {en_strategy_path} | Analysis: {strategy_folder}/analysis/ | Refs: {refs_folder}
   Log: {review_log_path}

   Cross-check: strategy coverage (all points addressed?), factual accuracy against refs,
   logical flow, writing quality, completeness, [TODO] items.
   For rebuttal: verify every reviewer point has a response.
   Write memos as `<!-- memo: ... -->` in the Korean draft.
   Write a structured review log to the log file.
   Return a summary of memos added (or "no issues found").
   ```

3. If memos were added:
   - **`--user-refine` pause**: if the flag is set, update `pipeline_state.yaml` (`user_refine: true`, `paused_at_stage: draft-refine`), print the resume command (`/autopilot-doc --mode {mode} --from draft-refine {strategy_folder}`), and exit. Do NOT invoke refine-doc-strategy.
   - Otherwise: invoke Skill `refine-doc-strategy` with the Korean draft path as args.
   - Note: refine-doc-strategy handles draft paths (draft/draft.md ↔ draft/draft_ko.md) via auto-detection.
4. If no memos: Skip to Step 6. (When resumed via `--from draft-refine`, run refine-doc-strategy directly on the pre-existing memos.)

### Step 6: Pipeline Summary
**Always write** `{strategy_folder}/pipeline_summary.md` before reporting to the user.

```markdown
# Document Strategy Pipeline Summary: {task name}

- **Date**: {YYYY-MM-DD} | **Mode**: {mode} | **Type**: {survey_type or "N/A"} | **Status**: done / reviewed / draft
- **User-Refine**: {true | false}
- **Refs folder**: {refs_folder}

## Process Log
| Step | Action | Result | Notes |
|---|---|---|---|
| 0 | Source Discovery | completed / skipped (non-survey) | {N} results from {M} sources |
| 1 | Material Analysis | completed | {N} files |
| 2 | init-doc-strategy | created | {strategy path} |
| 3 | Strategy Review (연구팀) | memos added / no issues | {memo count} |
| 3b | refine-doc-strategy | refined / skipped | |
| 4 | Draft Generation | created | {draft path} |
| 5 | Draft Review (연구팀) | memos added / no issues | {memo count} |
| 5b | refine-doc-strategy (draft) | refined / skipped | |

## Artifacts
- Strategy (EN/KO): {en_path} / {ko_path}
- Draft (EN/KO): {draft_en_path} / {draft_ko_path}
- Analysis: {reviewer_analysis or ref_analysis path}
- Material Index: {path} | Strategy Review: {path} | Draft Review: {path}

## Decision Points
| Step | Decision | User Response | Action Taken |
|---|---|---|---|
| (filled from orchestrator's in-memory decision log) |
```

When writing pipeline_summary.md, populate the Decision Points table from the in-memory decision records. If no decisions were recorded (clean run with no `--user-refine`, no missing inputs), write: `| - | No pause points triggered | - | - |`.

Then report to the user:
- Strategy file paths + 2-3 line summary of the strategy.
- Draft file paths + 2-3 line summary of the draft.
- For presentation mode: remind the user that PPTX export is manual — they should open the markdown draft and copy slide content into PowerPoint with their lab template.
- For review mode: confirm the `--review-format` used (default: openreview) and any venue-specific adaptations from refs/.

## Safety Rules
- Do NOT fabricate citations or invent results — only reference materials actually present in the refs folder.
- The draft is a working first draft for user editing, NOT a final document. Mark uncertain content with `[TODO: ...]`.
- For rebuttal mode: ensure EVERY reviewer point is addressed — missing a point is a critical error.
- For review mode: scores must be justified with concrete evidence; never fabricate scores without backing in the paper text. `--review-format` is mandatory — pre-flight aborts otherwise.
- For presentation mode: never insert real figures/images automatically — use `[FIGURE: ...]` placeholders. PPTX export is NOT performed by this pipeline; the user converts the markdown draft to PPT manually using their lab template.
- Present material inventory to the user briefly and auto-proceed.

## Task
$ARGUMENTS
