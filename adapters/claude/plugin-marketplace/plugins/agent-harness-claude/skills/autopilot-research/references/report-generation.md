### Step 4: Report Generation (direct Agent call + selected report-check gate)

> **Stage-dispatch back-reference** (OPERATIONS §5.10 ③④·SD-1·SD-2): `standard+` 에서 아래 Step 4a/4b 는 각각 독립된 depth-2 headless stage 로 dispatch 된다 — 전체 계약 원문·conditional stage(2e/3c) 목록은 [pipeline-search-analysis.md](pipeline-search-analysis.md) 의 stage-worker 매핑 표 참조, 본 문서는 report-side row 만 반복한다.

| stage | in-session team | input artifacts | output artifacts | write class |
|---|---|---|---|---|
| Step 4a (Report Generation) | 연구팀 | `analysis_summary.md`, `_internal/chaining_results.md`(있으면), `_internal/code_search.md`(있으면), `_internal/search_results.json`, `cards/` | `{00-08}_*.md`(mode-specific report set) | root (deliverable, T1/T2) |
| Step 4b (QA Loop) | 연구팀 (quality/fact-check/claim-verify subroles) / codex-review-team (adversarial external) | report set + `cards/` | `_internal/reviews/round_{n}_*.md`, `unresolved.md`(있으면) | _internal (raw, T3) |

두 stage 간 **file-only handoff** — 4b 는 4a 가 쓴 report 파일만 읽고, 4a 세션의 대화·중간 판단은 넘어오지 않는다.

> **자료팀 위임 (옵션)** — 보고서에 _집계 통계 시각화_ 나 _cross-card metric 비교 plot_ 등 _custom 분석 figure_ 가 필요하면 본 Step 안에서 `Agent(자료팀, "<spec>")` 직접 호출 가능. paper figure 직접 추출 (자료팀 영역) 과 다른 자리 — 자료팀은 _카드 데이터로부터 새 시각화_ 만들 때. 일반 survey 자료 (taxonomy table / lineage ASCII / per-paper card) 는 연구팀 본 자리 처리.

#### Step 4a: Generate Reports
```
Agent(subagent_type="연구팀"):
  "Research survey mode: Report generation.
   Analysis directory: {artifact_dir}
   Topic: {topic}
   Output directory: {artifact_dir}
   **Routing**: T1/T2 chapter files (00_briefing.md ~ NN_*.md, analysis_summary.md) → root `{artifact_dir}/`. Reviews/raw metadata are written elsewhere by other steps — do not touch _internal/ here.
   Date: {YYYY-MM-DD}

   ## Source Files to Read
   - analysis_summary.md (MUST READ — taxonomy, core papers, themes, evolution, gaps)
   - _internal/chaining_results.md (foundational dependencies, if exists)
   - _internal/code_search.md (code/model resources)
   - _internal/search_results.json (paper metadata)
   - Read key card files from cards/ (at least top 15-20 by discovery_count)

   ## Report Structure (mode-specific)

   The report set differs per mode. Common rules across all modes:
   - **Audience language**: default to the user's communication language. An explicit audience, publication, or artifact-language requirement overrides that default.
   - Preserve paper titles, author names, venues, model names, acronyms, metrics, and other canonical domain terms when translation would reduce precision.
   - Save each report file to root `{artifact_dir}/{filename}.md`. _internal/en/ 같은 분리 경로 안 씀 — 단일 산출.
   - Every comparison table ends with bold **Takeaway** line
   - Numbers/claims sourced only from analysis_summary / cards — NO fabrication
   - Cross-references via `[text](filename.md)` (same-directory link).
   - **Confidence 표기 (adversarial 한정 — R3)**: claim-verify 가 돈 자리면 핵심 finding 에 confidence(high/medium/low) 명시 — high=복수 primary + 만장일치 survive / medium=secondary or split vote / low=single source·blog 또는 abstain. 규칙 single source = [`claim-verify.md`](../../roles/modes/research/claim-verify.md).
   - **검증 탈락 섹션 (adversarial 한정 — R4)**: claim-verify 가 kill·abstain 한 claim 은 본문에서 제거/한정하고, briefing 또는 analysis_summary 말미 `## 검증 탈락 (refuted/unverified)` 섹션에 _무엇을·왜(반증 근거 URL)_ 투명 기록. 재현성·신뢰.

   ### Mode `academic` (default) — 9 files

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

   **Template by goal** (always end with a Cross-References section plus a 5-7 line summary in the selected report language):

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
   - Do **NOT** produce `seminar_slides.md`, slide-by-slide markdown, PPTX, or any other slide-rendering artifact.
   - Slide-by-slide draft generation belongs to autopilot-draft presentation mode. Never overstep.

   Same restriction applies to other goals: do NOT generate paper drafts, code, PPTX, or any final-form document — only the 9 markdown analysis reports.

   **MANDATORY closing section — `## Next Pipeline`** (always include at end of `06_implementation.md`, regardless of goal):

   This file is a **high-level outline / sketch** based on field analysis. For the actual document creation or implementation, hand off to a downstream pipeline. Pick the recommendation by detected goal:

   | Inferred Goal | Recommended next command | Hand-off rationale |
   |---|---|---|
   | build | `/autopilot-code --mode dev "<task>"` | Code implementation needs code-plan → code-execute → code-test loop. autopilot-code reads `analysis_project/{code,paper}/` + `research/{topic}/` implicitly. |
   | seminar | `/autopilot-draft "<task>" --mode presentation` | Slide-by-slide markdown draft (PPTX export is NOT supported — user converts to PPT manually with their lab template). research artifact는 implicit 인지. |
   | write | `/autopilot-draft "<task>" --mode paper` | LaTeX paper draft (Abstract → Conclusion) generation. |
   | research | `/autopilot-draft "<task> grant proposal" --mode doc` (or stay in research-only mode) | doc mode + grant-proposal genre intent — hypothesis + experiment design framing. |
   | adopt | `/autopilot-draft "<task> tech adoption report" --mode doc` | doc mode + report/proposal intent — structured go/no-go decision document. |
   | review | `/autopilot-draft "<task> peer review" --mode doc` (REQUIRED: pre-process the venue's review form via `/analyze-project --mode doc <folder>` first — no built-in presets, venues differ year-to-year) | doc mode + peer-review intent — reviewer report draft following the venue's review form. |

   Include the recommended next command verbatim in this section so the user can copy-paste it. autopilot-draft은 `research/{topic}/` 산출물을 prompt 키워드 fuzzy match로 자동 인지하므로 별도 path 인자 불요.

   **Boundary disclaimer** (also include): "이 06_implementation.md는 분야 분석에서 도출된 high-level 계획입니다. 본격적인 문서 작성·코드 구현은 autopilot-draft / autopilot-code로 인계됩니다."

   ### 07_resources.md — Code, Data & Model Resources
   - Tier-based repos: Tier 1 (directly usable for UD-KWS) / Tier 2 (backbone/infra) / Tier 3 (supplementary)
     Columns: repo | paper | stars | language | last-update | reproducibility | notes | **Quick verify command** (1-line — install + 1-sample inference, copy-paste-ready)
   - Code-not-available high-impact papers (institution/reason)
   - Pre-trained models table: model | architecture | params | framework | checkpoint | URL | **Quick verify command** (1-line — download + 1-sample inference + expected output shape)
   - Reproducibility assessment matrix: paper | code | data | checkpoint | overall rating

   > **Quick verify command 의 자리** — autopilot-spec Phase 1.5 의 _pretrained ckpt 사전 동작 점검_ 자리가 본 표를 1순위 source 로 자동 인용. 사용자가 spec 진입 후 ref 검증 자리에서 추가 자료 검색 없이 _바로 실행 가능_ 한 1-line 명령 누적이 목표. 명령 추출 출처: ref repo 의 README quickstart / inference.py 의 docstring / HF model card 의 _How to use_ 섹션.

   ### 08_reading_guide.md — Recommended Reading Paths
   - 4-5 purpose-based tracks:
     Track A: UD-KWS 입문자 (what is this field)
     Track B: 경량 모델 설계 (small model, good performance)
     Track C: 실전 구현 (I want to build a system)
     Track D: 연구자 (where are the open problems)
     Track E (optional): On-device 배포 전문가
   - Each track: target audience, goal, ordered paper list (5-7), reading point per paper, estimated time
   - Per-paper markers: 필수/권장/선택 for each track

   ### Mode `technology` — 7 files

   ### 00_briefing.md — Executive Briefing
   - 1-line summary, 3-5 line key findings, 1-page overview
   - Mermaid: technology landscape (categories, vendors, standards) — `graph TD`
   - Top-3 actionable insights (e.g., "production 환경엔 X 코덱이 사실상 표준", "오픈소스 대안 Y가 부상")

   ### 01_landscape.md — Technology Landscape
   - Category taxonomy (codecs / protocols / processing / hardware 등)
   - Key technologies × categories matrix
   - Lineage diagram (어떤 기술이 어디서 파생됐는지)
   - Adoption stage per technology (emerging / mainstream / legacy)

   ### 02_standards.md — Standards & Specs
   - Standards inventory: org (3GPP / ITU-T / IEEE / W3C / IETF) | spec ID | scope | year | status
   - Per-standard detail: 핵심 sections, mandatory vs optional features, profile/level
   - Cross-references between specs (예: VoLTE는 3GPP 26.171 + IETF SDP + ITU-T G.722.2)
   - **Takeaway**: 어느 표준을 따라야 하는가 (production / research 별도)

   ### 03_vendor_comparison.md — Vendor / Solution Comparison
   - Vendor matrix: vendor | product/SDK | licensing | platform | strengths | weaknesses
   - Capability checklist: feature × vendor (Yes/No/Partial)
   - Cost·license model 비교 (proprietary / open-source / royalty)
   - **Takeaway**: 사용 시나리오별 추천 솔루션

   ### 04_technical_deep_dive.md — Algorithm·Protocol Details
   - 3-5 핵심 기술 테마, each: 문제 정의 → 알고리즘 비교 → key insight
   - Critical equations / pseudocode / state machines (필요 시)
   - Performance trade-off 분석 (latency / quality / complexity)

   ### 05_deployment.md — Deployment Considerations
   - Reference architectures (network topology / signal flow)
   - Latency budget breakdown
   - Integration paths (existing system → new tech 마이그레이션)
   - Failure modes + mitigation
   - Cost model (CapEx / OpEx / per-call cost 등 해당 시)

   ### 06_implementation.md — Goal-Adaptive Action Roadmap (academic mode와 동일 템플릿; build / adopt 우선)

   ### 07_resources.md — Open-source Code, Models, Tools
   - Tier-based resources: Tier 1 (직접 사용 가능) / Tier 2 (참조용) / Tier 3 (실험용)
   - Pre-trained checkpoints (있다면) | platform support | license | **Quick verify command** (1-line — download + 1-sample inference + expected output)
   - Evaluation tools, test datasets, benchmarking suites
   - **Quick verify command 의 자리** — autopilot-spec Phase 1.5 자동 인용 source (academic mode 의 안내와 동일).

   ### Mode `market` — 5 files

   ### 00_briefing.md — Executive Briefing
   - 1-line summary, 3-5 line key findings, 1-page overview
   - Top-3 strategic implications

   ### 01_market_overview.md — Market Sizing & Segmentation
   - Total Addressable Market (TAM) / Serviceable (SAM) / Obtainable (SOM)
   - Segment breakdown: by region / customer type / use case
   - Growth rate (CAGR) + projection 3-5년
   - Source attribution table (출처 / 발행일 / 신뢰도)
   - **Takeaway**: 시장 규모 + 어디서 성장 동인이 나오는가

   ### 02_key_players.md — Competitor Profiles
   - Top 5-10 players: name | revenue / market share | products | strategy | recent moves
   - Positioning map (2D, 예: price vs feature)
   - Recent M&A / partnership / funding 동향
   - **Takeaway**: 경쟁 구도 1줄 요약

   ### 03_trends.md — Market Trends & Drivers
   - Driver factors (technology / regulation / customer need)
   - Inhibitor factors (cost / risk / inertia)
   - Disruptor candidates (incumbent를 위협할 수 있는 신기술·플레이어)
   - Timeline (단기 / 중기 / 장기 trend 분리)

   ### 04_opportunities.md — Opportunity Assessment
   - Whitespace identification (충족되지 않는 needs)
   - Entry strategy options (organic / partnership / acquisition)
   - Risk register
   - **Recommended actions** (prioritized)

   ## Quality Directives
   - Cross-reference other reports: [text](filename.md)
   - Every comparison table MUST end with bold **Takeaway** line
   - Mermaid: use graph TD with style directives for key nodes
   - Code snippets in 06_implementation.md must be runnable Python
   - Numbers only from card files / analysis_summary — NO fabrication
   - Do NOT return report content in response — write files only
   Return file paths (under `{artifact_dir}/`) plus a 3-5 line summary in the user's communication language."
```

#### Step 4a-Polish: Editorial polish (편집팀 모드 B — optional)

연구팀이 한국어로 직접 작성한 보고서 세트에 편집팀 모드 B (다듬기) 호출 — 판교체·번역체 회피, 표기 일관성, 줄바꿈·호흡 마무리. _수정만_ (mirror 생성 아님).

호출 조건 (single source — `adapters/claude/agents/editorial-team.md` 모드 B 호출 조건):
- **기본**: 파생 rigor 가 `standard / thorough / adversarial` 일 때만 호출 (intensity `standard+`)
- **skip**: intensity `direct` / `quick` (파생 rigor light/quick) 또는 사용자 명시 skip

```
모드 B — 다듬기 (다중 파일, in-place).
대상 디렉토리: {artifact_dir}/
대상 파일: 연구팀이 작성한 mode-specific report 세트 전체 (academic 9 개, technology 7 개, market 5 개)

<agent-home>/adapters/claude/agents/editorial-team.md 의 모드 B 절차를 적용한다.
판교체·번역체 회피 + 표기 일관성 (한 문서 안 같은 개념은 같은 표기) + 줄바꿈·bullet·공백 호흡.
영어로 그대로 둘 어휘: 논문 제목·저자·학회·약자·모델·데이터셋·지표 등 도메인 용어. 그 외 일반 표현은 한국어로.
파일 간 표기 일관성도 강제 — 첫 파일에서 결정한 표기를 이후 파일에도 동일 적용.
내용 (claim / 수치 / citation) 은 손대지 않음 — 표현·표기·가독성만.

완료 시 변경 요약 + 의도적으로 한 표기 결정 두세 개만 돌려준다.
```

> 연구팀이 자연 산출 언어 (한국어) 로 직접 작성하고, 편집팀이 _수정만_ — 두 번 쓰는 노동 회피.

#### Step 4b: QA Loop (max 2 rounds; quick = 1 round; adversarial = 2 + external 1)
Rigor tier: derived deterministically from the selected `--intensity`, not a separate `--qa` selector (direct→none/light, quick→quick, standard|strong→standard, thorough→thorough, adversarial→adversarial; see [CONVENTIONS.md §1.1](../../core/CONVENTIONS.md#11-verification-rigor-tiers-intensity-derived-canonical-sot)).

**Two reviewer roles run in parallel** at standard+ (**three at adversarial** — + claim-verify):
- **Quality reviewer(s)**: coverage / no-fabrication / progressive disclosure / actionable roadmap
- **Fact-checker** (연구팀 subrole): cards/ verbatim 대조 — reports에 인용된 venue/year/metric/lineage가 source cards와 일치하는지 narrow 검증 (내부 provenance). classification 8-row table 의 canonical 정의는 [`research-team.md`](../../adapters/claude/agents/research-team.md) single source.
- **Claim-verifier** (연구팀 subrole, _adversarial 한정_): claim ↔ 외부 모순 증거 적대적 검증 (외부 truth) — fact-check 와 보완층. 정의 = [`claim-verify.md`](../../roles/modes/research/claim-verify.md).

| Level | Quality reviewer | Fact-checker (parallel) | Max rounds |
|---|---|---|---|
| **quick** | 1× fast reviewer, spot-check만 | _skip_ | **1 (no re-invoke even on 🔴)** |
| **light** | 1× fast reviewer | _skip_ (quality reviewer covers basic spot-checks) | 2 |
| **standard** | 1× deep reviewer | **1× fast fact-checker** | 2 |
| **thorough** | 2× deep reviewers parallel (completeness + accuracy) | **1× fast fact-checker** | 2 |
| **adversarial** | 2× deep reviewers parallel + 1× external adversary (`codex-review-team` in Claude adapter) | **1× fast fact-checker** + **1× fast claim-verifier (N-vote 적대적)** | 2 + external 1 |

> **claim-verify (adversarial 한정 — 3번째 reviewer role)**: fact-checker 가 _claim ↔ 우리 cards verbatim_(내부 정합)을 본다면, claim-verify 는 _claim ↔ 외부 모순 증거_(외부 진위)를 본다. material claim 마다 N-vote default-refute + WebSearch 모순 탐색 → 카드 정합해도 _카드가 틀리면_ kill. 정의 single source = [`roles/modes/research/claim-verify.md`](../../roles/modes/research/claim-verify.md), CONVENTIONS §1.1.

**Why fast fact-checker**: cards verbatim 대조는 _창의적 판단_이 아닌 _단순 매칭 작업_이라 fast role 로 충분. Claude adapter 는 이 role 을 sonnet 으로 매핑한다.

```
round = 0, review_dir = {artifact_dir}/_internal/reviews/
Loop:
  round += 1

  # Parallel reviewer invocation (single message with multiple Agent calls per QA Scaling)

  Quality reviewer prompt (deep or fast reviewer per level):
    "Review research survey report — _coverage / no-fabrication / disclosure / roadmap_ focus.
     Topic: {topic}. Reports dir: {artifact_dir}.
     Verify: coverage, no fabrication, progressive disclosure, actionable roadmap.
     Do NOT individually verify each citation (model venue/year/metric) — that's the fact-checker's role at standard+.
     Write to: {review_dir}/round_{round}_quality.md (or round_{round}.md at light level).
     Return ONLY path + one-line verdict."

  Fact-checker prompt (fast fact-checker, parallel — standard/thorough only):
    "You are a fact-check focused reviewer — NOT report quality.
     Topic: {topic}. Reports dir: {artifact_dir}. Cards: {artifact_dir}/cards/.

     For every domain claim in the reports (model name / venue / year / metric / dataset /
     lineage / classification mentioned in 00_briefing through last report), open the
     corresponding card and verbatim compare:
     - Single source of truth: {artifact_dir}/cards/*.md
     - If a report claim has no matching card → flag as 🔴 (fabrication risk)

     Do NOT comment on coverage, narrative, or roadmap quality — that's the quality reviewer's job.
     Fast fact-checker mode: table-only output. Limit to ~30 most material claims (prioritize Tier 1 papers + key models in user-prompt).

     Output table:
     | Report | Section | Claim | Source card (file:line) | Match (✅/❌) | Severity (🔴/🟡) |

     Write to: {review_dir}/round_{round}_factcheck.md.
     Return ONLY path + one-line verdict."

  Claim-verifier prompt (fast fact-checker/reviewer, N-vote — adversarial ONLY; persona: roles/modes/research/claim-verify.md):
    "You are an ADVERSARIAL claim verifier — NOT provenance (fact-checker's job), NOT report quality.
     Topic: {topic}. Reports dir: {artifact_dir}. Cards: {artifact_dir}/cards/.
     For each MATERIAL claim (central/supporting; prioritize high source-quality + key models in user-prompt),
     run 3 skeptical voters that each TRY TO REFUTE: WebSearch for contradicting evidence, check quote-support,
     source-quality vs claim strength, recency (outdated SOTA?), marketing/cherry-pick/single-run.
     Default refuted=true if uncertain. Kill on ≥2/3 refutes; quorum: need ≥2 valid votes (else 🟡 abstain=unverified, do NOT pass).
     Cost-aware: limit to ~25 most material claims.
     Output table: | Claim | Source(quality) | Vote(survive-refute) | Verdict(✅/🔴killed/🟡abstain) | Confidence(high/med/low) | 반증 근거(URL) |
     ALL killed/abstain claims MUST be listed (반증 투명성). Write to: {review_dir}/round_{round}_claimverify.md.
     Return ONLY path + one-line verdict."

  No 🔴 from any reviewer → exit.
  intensity == quick → after round 1, write unresolved.md if any 🔴 remain (tag fact-check residuals as [FACT-RESIDUAL]), exit. NEVER re-invoke 연구팀.
  🔴 from quality + round < 2 → re-invoke 연구팀 with quality findings.
  🔴 from fact-checker + round < 2 → re-invoke 연구팀 with mandatory ref-grounding (re-read named cards).
  🔴 from claim-verify (killed) + round < 2 → re-invoke 연구팀: killed claim 은 본문에서 제거/한정(qualify) + report "검증 탈락(refuted)" 섹션으로 이동(반증 근거 첨부). 🟡 abstain = confidence low 로 강등.
  🔴 from both + round < 2 → re-invoke 연구팀 with combined findings.
  round >= 2 + 🔴 remain → write unresolved.md (tag fact-check residuals as [FACT-RESIDUAL]), exit.
```

#### Step 4c: Status Check
Verify `{artifact_dir}/00_briefing.md` exists. Not exists → pipeline_summary(failed) → STOP.
