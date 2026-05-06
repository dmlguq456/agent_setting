---
name: autopilot-research
description: "Research survey pipeline — paper search, analysis, and 9 markdown reports (field intelligence only; no PPT/paper drafts). 2-level architecture (orchestrator → agent). Hand off to autopilot-doc (writing/slides) or autopilot-code (build) for actual document/code creation."
argument-hint: "<query> [--depth shallow|medium|deep] [--refs <folder>] [--qa light|standard|thorough] [--from search|analyze|report]"
---

## Language Rule
- When explaining something to the user, write in Korean.

## Argument Parsing
Parse `$ARGUMENTS` for optional flags:

- **query**: research topic, paper title, arXiv ID, or PDF path (remaining text after flags)
- **--depth**: `shallow` | `medium` (default) | `deep`
- **--refs \<folder\>**: path to local reference PDFs (user must specify, no default)
- **--qa**: `light` | `standard` (default) | `thorough` — override QA intensity for report QA loop
- **--from**: `search` | `analyze` | `report` — resume the pipeline at a specific stage (see Resume below)

## Decision Defaults (no autonomy gating)

The pipeline auto-proceeds with sane defaults. There is no autonomy-level dial. Pause points are limited to:

| Decision Point | Default Behavior |
|---|---|
| Search results review | Auto-proceed. |
| Query expansion rounds | Auto-proceed. |
| Phase B loopback | Auto-proceed up to the depth-gated limit. |
| Missing refs folder | **Always ask** (only when `--refs` was specified but the path is invalid). |
| Search returned 0 papers | Auto-stop with `pipeline_summary(failed)` (no useful continuation possible). |
| Report generation | Auto-proceed. |

## Resume (`--from`)

`--from <stage>` re-enters an existing artifact directory and runs from that stage onward. Stages:
- `search` — Step 2 (Paper Search)
- `analyze` — Step 3 (Phase A skimming + B chaining + C code search + analysis_summary)
- `report` — Step 4 (Report Generation + QA loop)

When `--from` is used, the positional argument should be either the artifact directory path or a fuzzy-matchable topic name. The orchestrator resolves it via `ls -d .claude_reports/research/*$ARG* 2>/dev/null`. Read `pipeline_state.yaml` to recover `query`, `depth`, `qa_level`, `refs_folder`. CLI flags override stored values.

### pipeline_state.yaml

Written/updated at `{artifact_dir}/pipeline_state.yaml` after each completed stage:

```yaml
pipeline: autopilot-research
query: <original query>
depth: medium
qa_level: standard
refs_folder: <path or null>
last_completed_stage: analyze    # one of: search, analyze, report
artifact_dir: <abs path>
```

## Pipeline

### Step 1: Input Parsing & Validation
- Detect query type: keyword, paper title, arXiv ID, PDF path, folder path
- If `--refs` specified: verify folder exists. If not → ask user (Critical, always ask). Abort if user says no.
- Construct topic name (sanitize: lowercase, hyphens, max 30 chars)
- Set artifact_dir: `.claude_reports/research/{topic}/`
- `mkdir -p {artifact_dir}` (only AFTER validation)

### Step 2: Paper Search (direct Agent call)

#### Step 2a: 초기 쿼리 확장 (LLM 지식 기반)
오케스트레이터가 사용자 쿼리로부터 **2~3개 동의어/대체 표현**을 생성한다.
목적: 같은 분야인데 다른 이름으로 불리는 연구를 첫 검색부터 포함.
(예: "user-defined keyword spotting" → + "query-by-example KWS", "personalized wake word detection")
`queries = [original_query, variant_1, variant_2]`

> Step 2e의 **논문 기반 확장**과 다름: 2a는 LLM 사전 지식으로 동의어 생성, 2e는 실제 발견된 논문에서 새 키워드 추출.

#### Step 2b: HF MCP Pre-Fetch
Before invoking the agent, attempt HF `paper_search` for all queries:
- For each query in `queries`: call `paper_search` and collect results
- If successful: store combined as `hf_results_json`
- If MCP unavailable or fails: `hf_results_json = null`, note in pipeline log

#### Step 2c: Invoke Agent
```
Agent(subagent_type="연구팀"):
  "Research survey mode: Paper search.
   Queries: {queries_list}
   Original query: {original_query}
   Query type: {detected_type}
   Output directory: {artifact_dir}
   Max results per source per query: 10
   {If --refs: 'Reference folder: {refs_path}'}
   {If hf_results_json: 'HF paper_search results (pre-fetched): {hf_results_json}'}
   Timeout rule: If any single source takes >3 minutes, skip it and proceed to the next.

   ## search_results.json Schema
   {
     "query": "string", "date": "YYYY-MM-DD", "sources_used": ["string"],
     "total_papers": int,
     "papers": [{"title": "string (required)", "authors": ["string"],
       "year": int|null, "citation_count": int|null,
       "discovery_count": int (required, >=1), "sources": ["string"],
       "arxiv_id": string|null, "oa_url": string|null,
       "openalex_id": string|null, "referenced_works": ["string"]|null,
       "venue": string|null, "venue_tier": int|null (1-4), "raw_type": string|null,
       "url": string|null (landing page URL from any source — used by 탐색팀 for paywall access)}]
   }

   ## Google Scholar HTML Parsing Patterns
   - Split blocks: <div class='gs_r gs_or gs_scl'>
   - Title: strip tags from <h3> content
   - Year: , (\d{4})\s*[-–] pattern (leading comma required)
   - Citation: >Cited by (\d+)< pattern

   Follow your Role 2a procedure. Return file paths + 3-5 line Korean summary."
```

#### Step 2d: Post-Search Validation
1. Read `{artifact_dir}/search_results.json`
2. Verify valid JSON — if parse fails, re-invoke Agent once: "Your search_results.json was invalid. Fix and rewrite."
3. Verify `papers` array non-empty, each paper has `title`
4. If still fails after retry: pipeline_summary(failed) → STOP
5. If `total_papers == 0`: pipeline_summary(failed, "검색 결과 0건") → STOP

**Error handling**: If Agent call fails or returns no output → pipeline_summary(failed) → STOP.

#### Step 2e: Query Expansion Rounds (depth-gated)
발견된 논문의 제목/키워드에서 새로운 검색어를 추출하여 추가 검색 라운드를 실행한다.

**라운드 제어** (depth 파라미터):
- `shallow`: 추가 라운드 없음 (Round 1만)
- `medium`: 최대 1회 추가 라운드 (Round 1 → keyword 추출 → Round 2)
- `deep`: 최대 2회 추가 라운드 (Round 1 → Round 2 → Round 3)

**각 라운드 절차**:
1. 오케스트레이터가 `search_results.json`의 논문 제목들을 읽고, 빈출 키워드/새로운 용어를 추출
   (예: Round 1에서 "query-by-example", "metric learning", "prototypical network"가 반복 등장)
2. 기존 쿼리에 없는 새 키워드로 2~3개 추가 쿼리 생성
3. 새 쿼리만으로 연구팀 재호출 (기존 쿼리 재검색 안 함):
   ```
   Agent(subagent_type="연구팀"):
     "Research survey mode: Paper search.
      Queries: {new_queries_only}
      Original query: {original_query} (for context, do NOT re-search)
      Output directory: {artifact_dir}
      Max results per source per query: 10
      MERGE mode: append to existing search_results.json — update discovery_count for duplicates, add new papers.
      ..."
   ```
4. 병합 후 Post-Search Validation 재실행
5. 새 논문이 3편 미만이면 → 라운드 종료 (수렴)

**수렴 조건** (일찍 끝나는 경우):
- 추가 라운드에서 새 논문 < 3편 → 더 이상 확장하지 않음
- 새 키워드를 추출할 수 없음 (기존 쿼리와 동일) → 종료

Auto-proceed after expansion rounds (no user gate).

### Step 3: Paper Analysis (direct Agent calls)

#### Step 3a: Playwright Pre-Check + 탐색팀 Pre-Fetch
```
Bash: python3 -c "from playwright.async_api import async_playwright; print('OK')"
Bash: ls ~/.cache/ms-playwright/chromium_headless_shell-*/ > /dev/null 2>&1 && echo 'BROWSER_OK'
```
Set `playwright_available = true/false`.

If `playwright_available == true`:
  Read `search_results.json` and identify paywall papers (no arXiv ID AND no oa_url → likely paywall).
  If paywall papers exist, invoke 탐색팀 to pre-fetch their content:
  ```
  Agent(subagent_type="탐색팀"):
    "Mode: fetch_papers
     URLs: {paywall_url_list}
     Output directory: {artifact_dir}
     Extract full text from each URL. Write to browser_extracts/{filename}.txt.
     Return summary of successes and failures."
  ```
  The extracted texts will be available for 연구팀 to Read during Phase A skimming.
  If 탐색팀 fails or playwright unavailable: proceed without — 연구팀 will fall through to abstract-only.

#### Step 3b: Phase A — Parallel Skimming Batches
Read `search_results.json`. Classify each paper's access type FIRST:
- **accessible**: has `arxiv_id` OR `oa_url` OR matching file in `browser_extracts/`
- **paywall-only**: no `arxiv_id`, no `oa_url`, no browser extract → abstract/metadata only

Construct batches (accessible papers only get full-read treatment):
- Full-read accessible (citations > 10 AND not null AND accessible): 1 paper per Agent call
- Abstract-only (citations <= 10 OR null OR paywall-only): up to 10 per Agent call
- **Exception**: `discovery_count >= 3` AND accessible → upgrade to full-read (1 per call)
- **Paywall-only papers**: always go in abstract-only batches regardless of citation count
  (attempting WebFetch on paywall sites causes timeout/hang — never do this)

For each batch:
```
Agent(subagent_type="연구팀"):
  "Research survey mode: Paper analysis.
   Papers: {batch_json}
   Output directory: {artifact_dir}
   Refs folder: {refs_path or 'none'}
   Browser extracts: {artifact_dir}/browser_extracts/ (pre-fetched by 탐색팀, if available)

   ## CRITICAL RULES
   - Per-paper timeout: 60초 이내에 본문을 얻지 못하면 즉시 다음 논문으로. 절대 한 논문에 60초 이상 소비 금지.
   - Paywall fast-detect: arxiv_id도 oa_url도 없고 browser_extracts에도 없는 논문 → WebFetch 시도하지 말고 바로 OpenAlex Abstract만 사용.
   - WebFetch가 3xx redirect 무한 루프나 빈 응답을 반환하면 즉시 스킵.
   - 한 배치의 전체 처리 시간이 10분을 넘기지 않도록 한다.

   ## Paywall Access
   If browser_extracts/{filename}.txt exists for a paper: Read the pre-extracted text.
   If not: skip to metadata fallback (OpenAlex Abstract). Do NOT attempt browser access directly.
   Playwright 실행은 탐색팀(browser-team)이 전담 — 연구팀은 절대 직접 Playwright를 실행하지 않는다.

   Follow your Role 2b procedure. Return file paths + Korean summary."
```
Launch batches in parallel. **Error handling**: Individual batch failure → log and continue. Total failure (0 batches succeed) → pipeline_summary(failed) → STOP.

#### Step 3c: Phase B — Reference Chaining (depth-gated)
If `depth == shallow`: SKIP Phase B entirely.
```
Agent(subagent_type="연구팀"):
  "Research survey mode: Reference chaining.
   Paper cards: {artifact_dir}/cards/
   Search results: {artifact_dir}/search_results.json
   Depth: {depth}
   Output: {artifact_dir}/chaining_results.md
   Follow your Role 2b reference chaining procedure. Return file paths + Korean summary."
```

**Loopback control** (orchestrator responsibility):
1. Parse `chaining_results.md` → extract papers with `reference_frequency >= 2`
2. If new papers exist AND loopback_count < limit (medium: 1, deep: 2):
   - Construct Phase A batches for new papers only (top 10)
   - Invoke additional skimming Agent calls
   - Increment loopback_count
   - Re-invoke Phase B for further chaining
3. When limit reached or no new papers → proceed to Phase C

#### Step 3d: Phase C — Code & Model Search
```
Agent(subagent_type="연구팀"):
  "Research survey mode: Code and model search.
   Paper cards: {artifact_dir}/cards/
   Output: {artifact_dir}/code_resources/
   Aggregate: {artifact_dir}/code_search.md
   Follow your Role 2c procedure. Return file paths + Korean summary."
```

#### Step 3e: Compile analysis_summary.md
```
Agent(subagent_type="연구팀"):
  "Research survey mode: Compile analysis summary.
   Compile from: cards/, chaining_results.md (if exists), code_search.md (if exists).
   Set phase flags: chaining_available, code_search_available.
   Output: {artifact_dir}/analysis_summary.md
   Return file path + Korean summary."
```

#### Step 3 Status Check
Read `{artifact_dir}/analysis_summary.md`.
- Not exists or 0 papers → pipeline_summary(failed) → STOP
- Depth-aware: `shallow` + `chaining_available == false` + `code_search_available == true` → **done** (intentional skip)
- Otherwise partial flags → **partial**, warn user, proceed

### Step 4: Report Generation (direct Agent call + QA loop)

#### Step 4a: Generate Reports
```
Agent(subagent_type="연구팀"):
  "Research survey mode: Report generation.
   Analysis directory: {artifact_dir}
   Topic: {topic}
   Output directory: {artifact_dir}
   Date: {YYYY-MM-DD}

   ## Source Files to Read
   - analysis_summary.md (MUST READ — taxonomy, core papers, themes, evolution, gaps)
   - chaining_results.md (foundational dependencies, if exists)
   - code_search.md (code/model resources)
   - search_results.json (paper metadata)
   - Read key card files from cards/ (at least top 15-20 by discovery_count)

   ## Report Structure (9 files, ALL in Korean, technical terms English-parenthesized)

   ### 00_briefing.md — Executive Briefing
   - **Level 0** (1 line): 한 문장 요약
   - **Level 1** (3-5 lines): 핵심 발견 요약
   - **Level 2** (1 page):
     - Mermaid paper relationship diagram (`graph TD`, styled key nodes, 4 subgraphs: Backbone/QbE/QbT/On-Device)
     - Research axes table: axis | description | key papers | paper count
     - Key findings (numbered, 5-7 items)
     - Recommended architecture stack (ASCII pipeline: input → feature → encoder → matching → output)
     - Model size spectrum (ASCII: MCU→Edge→GPU→Server with params and best metric per tier)
   - **Level 3**: 전체 보고서 가이드 table (file | content | key question answered)

   ### 01_landscape.md — Research Landscape
   - Problem definition (formal: few-shot, zero-shot, open-set variants)
   - 3D taxonomy: enrollment method (audio/text/multi-modal) × learning paradigm (metric/contrastive/classification/KD/meta) × architecture (CNN/Conformer/Hybrid/MLP)
   - Temporal evolution table: period | key transition | representative papers
   - Research axes detailed breakdown with paper counts
   - Enrollment method comparison (QbE vs QbT vs Multi-modal, with paper lists per category)

   ### 02_core_papers.md — Core Paper Analysis
   - Grade classification: **필독** (DC>=5 or CC>100), **정독** (DC>=3 or CC>30), **참조** (rest)
   - Paper lineage diagrams (ASCII: metric learning lineage, phoneme matching lineage, multi-modal lineage)
   - Per-paper detailed cards for 필독+정독:
     authors | venue/year | DC/CC | code link | core insight | architecture (diagram if possible) | key results table | limitations | connections
   - 참조 grade: compact table only (title | year | contribution | params)

   ### 03_baselines.md — Benchmark Comparison Tables
   Tables (each ending with bold **Takeaway** line):
   1. GSC closed-set (12-class): model/year/acc-v1/acc-v2/params/MACs/latency/code
   2. LibriPhrase text-enrollment: model/year/EER-Easy/EER-Hard/AUC-Easy/AUC-Hard/params/code
   3. splitGSC few-shot open-set: model/backbone/params/5-shot-acc/AUROC/code
   4. Zero-shot audio enrollment: model/size-quant/AUC/EER/training-data/code
   5. Continuous speech KWS: model/keywords/recall@2FA-clean/other/speed
   6. Multilingual UD-KWS: model/params/languages/metric/score/code
   7. On-device deployment: model/year/platform/params/power/accuracy/method
   8. Model size spectrum ASCII (MCU→Server with params and best metric at each tier)
   - Only include numbers directly from card files — NO fabrication

   ### 04_technical_deep_dive.md — Technical Deep Dive
   - 5-8 technology themes, each with: problem definition → approach comparison table → key insight
     Expected themes: phoneme-level supervision, audio-text modality gap, metric/contrastive losses, KD for lightweight, open-set rejection, streaming detection, data augmentation/synthesis
   - Loss function comparison table (MANDATORY): loss | papers | mechanism | pros | cons | best-for
   - Closing section: **미해결 과제와 연구 기회** (5-8 gaps with difficulty/impact ratings + solution directions)

   ### 05_datasets.md — Dataset Specifications
   - Primary benchmarks (detailed field/value tables): GSC v1/v2 (+ splitGSC split details), LibriPhrase (+ key eval numbers), Qualcomm KWSD, Hey-Snips
   - Training datasets: MSWC, LibriSpeech, VoxCeleb, WenetPhrase, Common Voice
   - Each dataset: year/size/speakers/keywords/language/access URL/license/usage count
   - Noise/augmentation datasets table
   - Dataset usage map (ASCII diagram: training datasets → evaluation benchmarks)
   - Recommended benchmark combination table: scenario → datasets → metrics

   ### 06_implementation.md — Goal-Adaptive Action Roadmap
   First **infer the user's primary goal** from the original query and select the matching template. Always state the inferred goal at the top of the file (`> Inferred goal: {goal} — {one-line rationale}`). If ambiguous, default to **build** but log the assumption.

   **Goal detection cues** (non-exhaustive, infer from `original_query`):
   - **build** — "구현", "implement", "develop", "build a system", "재현", "프로젝트" → code/system implementation
   - **seminar** — "세미나", "발표", "lecture", "presentation", "slides", "talk" → talk/slide preparation
   - **write** — "논문 작성", "survey 쓰기", "review writing", "thesis" → paper/survey writing
   - **research** — "연구 방향", "research direction", "open problem", "hypothesis", "what's next" → research direction scoping
   - **adopt** — "기술 도입", "선택", "어떤 모델 써야", "production 적용" → technology selection / adoption decision

   **Template by goal** (always end with a Cross-References section + 5-7 line Korean summary):

   #### Goal: build — Implementation Roadmap
   - Architecture decision matrix (5-8 decisions): each with Option A/B/C + Recommendation + reasoning. Decision keys depend on domain (e.g., backbone, loss, training paradigm, deployment target, data pipeline).
   - Phased implementation plan (typically 6-12 weeks): Phase 0 (Infrastructure: dataset pipeline, eval metrics, reference code) → Phase 1-N (incremental capability buildup, ending with optimization/deployment).
   - Key technical decisions with runnable Python code snippets (feature extraction, evaluation protocol, etc.)
   - Paper-to-code mapping table: technique → source paper → reference repo → status
   - Risk assessment table: risk | probability | impact | mitigation

   #### Goal: seminar — Seminar Preparation Roadmap
   - Slide structure outline organized by chapter (target audience-aware slide count, e.g., 30-50 for 60-min)
   - Per-chapter cheat sheet (key papers, takeaways, transitions, time budget)
   - Deep-dive slide candidates for expert audiences (5-10 backup slides)
   - Demo candidates with reproducible inference setup (link to repos)
   - Q&A anticipation table (5-10 likely questions with brief answers + supporting paper)

   #### Goal: write — Writing Roadmap
   - Section-by-section outline (Abstract → Intro → Related Work → Methods → Experiments → Conclusion, or domain-appropriate variant)
   - Argument scaffolding: thesis → supporting evidence per claim → counter-considerations / limitations
   - Figure/table candidates with caption drafts and source paper references
   - Citation map: which papers to cite where (with rationale linking to claim)
   - Writing-stage timeline (literature consolidation → outline → draft → revision → submission)

   #### Goal: research — Research Direction Roadmap
   - Open-problem identification: 5-8 gaps with severity (impact × tractability) ratings
   - Hypothesis candidates: testable hypotheses with expected outcomes
   - Experimental setup proposals: minimal viable experiment per hypothesis (data, baseline, metric, resource estimate)
   - Decision matrix: which direction first (impact × feasibility × novelty)
   - Risk register: scientific risks (negative results, scooping) + mitigation

   #### Goal: adopt — Technology Adoption Roadmap
   - Selection criteria matrix (cost, latency, accuracy, license, maintenance) weighted to user constraints
   - Candidate shortlist (3-5 options) with pros/cons aligned to criteria
   - Pilot evaluation plan: which to try first, measurement protocol, decision threshold
   - Integration considerations: data pipeline, monitoring, rollback path
   - Risk assessment: technical + organizational

   **Schema flexibility**: section names above are guides, not hard requirements. Adapt headings, decision keys, phase counts to the actual domain (e.g., "MCU optimization" only relevant if on-device is in scope). Numbers/examples in cards must drive the template, not the other way around.

   **CRITICAL — Output scope strictly limited to the 9 markdown reports** (00_briefing through 08_reading_guide). Specifically for goal=seminar:
   - Produce `06_implementation.md` with chapter outline + cheat sheet + Q&A + deep-dive candidates ONLY.
   - Do **NOT** produce `seminar_slides.md`, `notion_seminar_slides.md`, slide-by-slide markdown, PPTX, or any other slide-rendering artifact.
   - Slide-by-slide draft generation belongs to autopilot-doc presentation mode. Never overstep.

   Same restriction applies to other goals: do NOT generate paper drafts, code, PPTX, or any final-form document — only the 9 markdown analysis reports.

   **MANDATORY closing section — `## Next Pipeline`** (always include at end of `06_implementation.md`, regardless of goal):

   This file is a **high-level outline / sketch** based on field analysis. For the actual document creation or implementation, hand off to a downstream pipeline. Pick the recommendation by detected goal:

   | Inferred Goal | Recommended next command | Hand-off rationale |
   |---|---|---|
   | build | `/autopilot-code` (dev mode) with this artifact_dir as context | Code implementation needs init-plan → execute-plan → run-test loop |
   | seminar | `/autopilot-doc --mode presentation --refs {artifact_dir}` | Slide-by-slide markdown draft (PPTX export is NOT supported — user converts to PPT manually with their lab template) |
   | write | `/autopilot-doc --mode write --refs {artifact_dir}` | Full paper draft (Abstract → Conclusion) generation |
   | research | `/autopilot-doc --mode proposal --refs {artifact_dir}` (or stay in research-only mode) | Proposal mode covers hypothesis + experiment design framing |
   | adopt | `/autopilot-doc --mode report --refs {artifact_dir}` (or `--mode proposal` for go/no-go decision) | Tech adoption is a structured report/proposal |
   | review | `/autopilot-doc --mode review --refs {artifact_dir} --review-format <openreview\|acl-arr\|ieee-conf\|journal\|PATH>` (REQUIRED; pipeline aborts at pre-flight if missing) | Reviewer report draft following the venue's review form |

   Include the recommended next command verbatim in this section so the user can copy-paste it. Note that the artifact_dir produced by autopilot-research is directly usable as `--refs` for autopilot-doc.

   **Boundary disclaimer** (also include): "이 06_implementation.md는 분야 분석에서 도출된 high-level 계획입니다. 본격적인 문서 작성·코드 구현은 autopilot-doc / autopilot-code로 인계됩니다."

   ### 07_resources.md — Code, Data & Model Resources
   - Tier-based repos: Tier 1 (directly usable for UD-KWS) / Tier 2 (backbone/infra) / Tier 3 (supplementary)
     Columns: repo | paper | stars | language | last-update | reproducibility | notes
   - Code-not-available high-impact papers (institution/reason)
   - Pre-trained models table: model | architecture | params | framework | checkpoint | URL
   - Reproducibility assessment matrix: paper | code | data | checkpoint | overall rating

   ### 08_reading_guide.md — Recommended Reading Paths
   - 4-5 purpose-based tracks:
     Track A: UD-KWS 입문자 (what is this field)
     Track B: 경량 모델 설계 (small model, good performance)
     Track C: 실전 구현 (I want to build a system)
     Track D: 연구자 (where are the open problems)
     Track E (optional): On-device 배포 전문가
   - Each track: target audience, goal, ordered paper list (5-7), reading point per paper, estimated time
   - Per-paper markers: 필수/권장/선택 for each track

   ## Quality Directives
   - Cross-reference other reports: [text](filename.md)
   - Every comparison table MUST end with bold **Takeaway** line
   - Mermaid: use graph TD with style directives for key nodes
   - Code snippets in 06_implementation.md must be runnable Python
   - Numbers only from card files / analysis_summary — NO fabrication
   - Do NOT return report content in response — write files only
   Return file paths + 3-5 line Korean summary."
```

#### Step 4b: QA Loop (max 2 rounds)
QA level: `--qa` flag if provided, else auto-detect (<=10 papers: light, 11-25: standard, >25 or deep: thorough).

| Level | Model | Reviewers |
|---|---|---|
| light | sonnet | 1 |
| standard | opus | 1 |
| thorough | opus | 2 parallel (completeness + accuracy) |

```
round = 0, review_dir = {artifact_dir}/report_reviews/
Loop:
  round += 1
  Invoke 품질관리팀: "Review research survey report. Topic: {topic}. Verify: coverage, no fabrication, progressive disclosure, actionable roadmap. Write to: {review_dir}/round_{round}.md."
  No 🔴 → exit. 🔴 + round < 2 → re-invoke 연구팀 to fix. round >= 2 + 🔴 → write unresolved.md, exit.
```

#### Step 4c: Status Check
Verify `{artifact_dir}/00_briefing.md` exists. Not exists → pipeline_summary(failed) → STOP.

### Step 5: Pipeline Summary
Write `{artifact_dir}/pipeline_summary.md` BEFORE reporting:
```markdown
# Research Survey Pipeline Summary: {topic}
- **Date**: {YYYY-MM-DD}
- **Query**: {query}
- **Depth**: {depth}
- **Status**: done / partial / failed
- **From-Stage**: {stage if resumed via --from, else "N/A"}

## Process Log
| Step | Action | Result | Notes |
|---|---|---|---|
| 1 | Input parsing | {type} | topic: {topic} |
| 2a | Query Expansion | {N} queries | original + {N-1} variants |
| 2b-c | Paper Search (Agent) | {N} papers | sources: {list} |
| 2e | Query Expansion Rounds | {N} rounds | new papers per round: {list} |
| 3 | Paper Analysis (Agent x N) | {N} analyzed | depth: {depth}, loopbacks: {N} |
| 4 | Report Generation (Agent + QA) | 9 files | QA: {level}, rounds: {N} |

## Artifacts
- Search: {artifact_dir}/search_results.json
- Analysis: {artifact_dir}/analysis_summary.md
- Reports: {artifact_dir}/00_briefing.md ~ 08_reading_guide.md

## Decision Points
| Step | Decision | Response | Action |
|---|---|---|---|
| (from in-memory log) |
```

### Step 6: Briefing
Read `00_briefing.md` and `06_implementation.md` (for the inferred goal + Next Pipeline) and present:
1. Level 0 summary (one line)
2. Level 1 overview (3-5 lines)
3. Key stats: total papers, core papers, code availability
4. File paths for all 9 reports (00_briefing ~ 08_reading_guide)
5. **Next pipeline recommendation**: read the `## Next Pipeline` section from `06_implementation.md` and present the inferred goal + recommended next command verbatim. Make it copy-paste-ready.
6. "질문이 있으시면 물어보세요. 보고서를 기반으로 답변드리겠습니다."

> Pipeline completion: Step 5 determines formal status. Step 6 is optional interaction.

**Scope boundary**: autopilot-research produces *field intelligence* (markdown analysis only). It does NOT produce final documents (papers/slides/PPTX/code). For document/slide creation, hand off to autopilot-doc; for code implementation, hand off to autopilot-code. The `06_implementation.md` outline is the bridge artifact between these pipelines.

## Decision Logging
Record after each gate: `{step | decision | response | action}`. Populate pipeline_summary Decision Points table.

## Safety Rules
- Do NOT fabricate citations, URLs, or metrics
- Source failure → continue with remaining sources
- `--refs` folder missing → ask (Critical, always)
- Rate limits: arXiv ~3s, OpenAlex 10 req/s, S2 1 req/s, Google Scholar 3s + 50/day
- Context protection: each Agent returns ONLY file paths + 3-5 line summary
- Context budget: deep 모드에서 오케스트레이터 context가 누적됨 (쿼리 확장 라운드 + 스키밍 배치 + loopback). Agent 결과는 항상 파일로 저장하고 요약만 context에 유지. search_results.json 전체를 context에 올리지 않고 paper count + top-5만 참조.
- MERGE mode 무결성: 제목 fuzzy matching은 lowercase + 구두점 제거 + a/an/the 제거로 정규화. 같은 논문의 discovery_count는 단조 증가만 허용 (감소 금지).
- Playwright 고아 프로세스: 탐색팀 호출 전후로 `pkill -f chromium_headless_shell` 실행

## Task
$ARGUMENTS
