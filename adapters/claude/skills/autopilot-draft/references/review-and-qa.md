### Step 3: Strategy Review (연구팀 as domain expert)
1. Resolve strategy paths:
   - `strategy_folder` = `<artifact-root>/documents/{YYYY-MM-DD}_{short-name}/`
   - `en_strategy_path` = `{strategy_folder}/strategy/strategy.md`
   - `ko_strategy_path` = `{strategy_folder}/strategy/strategy_ko.md`

2. Invoke reviewers based on the intensity-derived rigor tier (CONVENTIONS §1.1). **Quality reviewer(s) and fact-checker run in parallel** at standard+:

   **`quick`** — Single 연구팀 quality reviewer (fast reviewer, spot-check only):
   - One-pass review. Memos may be added but draft-refine is NOT invoked at Step 3 (see step 3 below).
   - Review log: `{strategy_folder}/_internal/strategy_reviews/research_review.md`

   **`light`** — Single 연구팀 quality reviewer (fast reviewer):
   - One-pass review focusing on critical issues only.
   - Review log: `{strategy_folder}/_internal/strategy_reviews/research_review.md`

   **`standard`** — 1× 연구팀 quality reviewer (deep reviewer) + 1× 연구팀 fact-checker (fast fact-checker, parallel):
   - Quality review log: `{strategy_folder}/_internal/strategy_reviews/research_review_quality.md`
   - Fact-check log: `{strategy_folder}/_internal/strategy_reviews/research_review_factcheck.md`

   **`thorough`** — **axis-decomposed parallel 연구팀** only when the selected intensity calls for it (audit-aligned axes as bounded selected passes) + 1× 연구팀 fact-checker when source claims are in scope:
   - **Axis A — Domain quality** (deep reviewer): refs/reviewer comments 대조, 학술 venue 컨벤션 (NeurIPS / ICML / ICASSP / Interspeech / T-ASLP — paper modes), industry standards (report/proposal/presentation), 완전성 / cohesion.
     - Review log: `{strategy_folder}/_internal/strategy_reviews/research_review_domain.md`
   - **Axis B — Methodology** (deep reviewer): 논리 일관성, 주장 설득력, 실험 설계, adversarial reviewer 약점.
     - Review log: `{strategy_folder}/_internal/strategy_reviews/research_review_methodology.md`
   - **Axis C — Style Guide** (fast reviewer): `## Style Guide` section 존재 + citation/figure-caption/bullet-depth/speaker-note 양식 일관성.
     - Review log: `{strategy_folder}/_internal/strategy_reviews/research_review_style.md`
   - **Axis D — Cross-ref + Coverage** (fast reviewer): `cards/{file}.md` 인용 target 존재 + analysis/refs에 있으나 strategy에 인용 안 된 _orphan card_ 식별 (omission detection — UniSE-class 누락 방지).
     - Review log: `{strategy_folder}/_internal/strategy_reviews/research_review_coverage.md`
   - **Fact-checker** (fast fact-checker): citation/venue/year/metric/lineage verbatim 대조 (cards/PDFs).
     - Review log: `{strategy_folder}/_internal/strategy_reviews/research_review_factcheck.md`
   - 모든 reviewer가 `<!-- memo: ... -->` 코멘트를 KO strategy에 작성. 각자 `[axis name]` prefix 명시 (예: `[STYLE]`, `[COVERAGE]`).
   - 5 instance 완료 후 메모 merge + 중복 제거.

   _이 axis decomposition은 "user-catchable points 전부 연구팀이 대신"의 multi-axis 구현 — 한 instance가 모든 axis를 다루기 부담스러운 thorough+에서 활성_.

   **Quality reviewer prompt** (light/standard/thorough A & B):
   ```
   Review this document strategy as the user's domain expert proxy.
   **Task type: paper-driven doc** (mode: {mode}) — apply Role 1 Step 3 axes from adapters/claude/agents/research-team.md, with audit-aspect alignment.

   Mode: {mode} | KO strategy: {ko_strategy_path} | EN strategy: {en_strategy_path}
   Analysis: {strategy_folder}/analysis/ | Discovered inputs: {discovered_inputs} | Log: {review_log_path}

   **Default axes** (quality / cohesion / coverage):
   - Cross-check: actual refs/reviewer comments, domain conventions
   - Logical consistency, completeness (any missed reviewer points or gaps?)

   **Audit-aspect axes** (catch what /audit would catch, _at plan time_):
   - **Style Guide compliance** — `## Style Guide` section exists in strategy.md? Citation/figure-caption/bullet-depth/speaker-note rules followed?
   - **Structure** — T1/T2/T3 layout per CONVENTIONS.md §7 respected?
   - **Cross-ref** — every `cards/{file}.md` citation target exists?
   - **Coverage (omission detection)** — are there cards/papers in analysis/refs that the strategy SHOULD cite but doesn't? Flag as `<!-- memo: [COVERAGE] ... -->` per orphan.

   Do NOT verify individual fact citations (model venue/year/metric) — that's the fact-checker's role at standard+.
   Write memos as `<!-- memo: ... -->` in the Korean strategy.
   Write a structured review log to the log file.
   Return a summary of memos added (or "no issues found").
   ```

   **Fact-checker prompt** (fast fact-checker, parallel — standard/thorough only):
   ```
   You are a fact-check focused reviewer — NOT narrative quality.
   Mode: {mode} | KO strategy: {ko_strategy_path} | Discovered inputs: {discovered_inputs} | Log: {fact_log_path}

   For every domain claim in the strategy (citation / model name / venue / year /
   metric / dataset / lineage / classification), open the corresponding ground-truth
   source and verbatim compare:
   - Paper analyses: `<artifact-root>/analysis_project/paper/*.md` (if exists — single source of truth, produced by `/analyze-project --mode paper`)
   - Original PDFs: only if listed in {discovered_inputs} AND paper analyses lack the specific fact
   - Reviewer comments (rebuttal mode): {strategy_folder}/analysis/reviewer_analysis.md

   Do NOT comment on completeness, narrative arc, or strategic soundness — that's the quality reviewer's job.
   Stay narrowly on fact verification. Fast fact-checker mode: table-only output. Limit to ~30 most material claims.

   **CRITICAL — verification rules** (memory `feedback_factcheck_external_reverify.md`):
   - **name-only match ≠ ✅**. If the card contains the model/author name but the _specific venue / year / metric_ is NOT verbatim in the card, classify as 🟡 cards-name-only, NOT ✅. Use the `Source type` column.
   - **`[외부 추정]` / `[?]` / `[unverified]` markers in the strategy** → classify as 🟡 external-marker, trigger WebSearch/WebFetch re-verification, log the external source URL upon ✅ escalation. Otherwise remain 🟡.
   - **Circular reference FORBIDDEN**: do NOT use the strategy's own `## Style Guide` venue mapping table as ground truth when verifying body claims — both must be verified against cards _directly_.

   Output the review log as a single table with a Source type column:
   | Section | Claim in strategy | Source (file:line or section) | Match (✅/🟡/❌) | **Source type** | Severity (🔴/🟡/🟢) |

   `Source type` values:
   - `cards-verbatim` — venue/metric value itself appears verbatim in card → ✅ allowed
   - `cards-name-only` — card has name/year but venue/metric missing → 🟡, external reverify
   - `external-marker` — explicit external-estimation marker → 🟡, external reverify
   - `external-reverified` — reverified via WebSearch/WebFetch (URL in log) → ✅ allowed post-reverify
   - `conflict` — card has different value → 🔴
   - `circular-ref` — strategy↔draft comparison only → 🔴 architecture violation

   For 🔴/🟡 mismatches, also write `<!-- memo: [FACT] section X — claim Y conflicts with source Z -->` in the Korean strategy.
   Return ONLY path + one-line verdict.
   ```

3. If memos were added:
   - **`intensity == quick` short-circuit**: do NOT invoke draft-refine. Memos remain in the strategy as audit trail (no edits applied). Log to pipeline_summary Decision Points: `Step 3 | strategy refine skipped (intensity=quick) | auto | proceed to Step 4`. Skip to Step 4.
   - **`--user-refine` pause**: if the flag is set, update `pipeline_state.yaml` (`user_refine: true`, `paused_at_stage: strategy-refine`), print the resume command (`/autopilot-draft --mode {mode} --from strategy-refine {strategy_folder}`), and exit. Do NOT invoke draft-refine.
   - Otherwise: invoke Skill `draft-refine` with the Korean strategy path as args.
4. If no memos: Skip to Step 4. (When resumed via `--from strategy-refine`, the orchestrator skips the 연구팀 review and runs draft-refine directly using the pre-existing memos.)

### Step 5: Draft Review (연구팀 as QA)
**Applicable modes**: paper / presentation / doc (all 3 modes that generated drafts).

> **기본 게이트 먼저 (모든 intensity 필수, axis-decomposed 보다 우선)** — paper mode 면 review 착수 전 `conventions/paper.md §3.6` (① 문법 정합성: 주어-동사·관사·복수·시제·비문 _문장 단위_ / ② LaTeX 정합성: `main.log` multiply-defined label·`\ref` 미정의·Table/Fig 번호 `main.aux` 대조 / ③ 자산 정체: 표/그림 역할을 label·`\ref` 흐름·내용으로 파악) 를 **반드시 먼저** 적용한다. 이 기본은 fast reviewer 로 충분하며, _ceremony(단계·instance 수)보다 이 기본의 빠짐없음이 검토 품질을 결정_ 한다. 기본 누락은 thorough·deep reviewer 여도 못 잡는다.

1. Resolve draft paths:
   - `en_draft_path` = `{strategy_folder}/draft/draft.md`
   - `ko_draft_path` = `{strategy_folder}/draft/draft_ko.md`

2. Invoke reviewers based on the intensity-derived rigor tier (same scaling as Step 3). **Quality reviewer(s) and fact-checker run in parallel** at standard+:

   **`quick`** — Single 연구팀 quality reviewer (fast reviewer, spot-check only):
   - One-pass review. Memos may be added but draft-refine is NOT invoked at Step 5 (see step 3 below).
   - Review log: `{strategy_folder}/_internal/draft_reviews/draft_review.md`

   **`light`** — Single 연구팀 quality reviewer (fast reviewer):
   - One-pass review focusing on critical issues only.
   - Review log: `{strategy_folder}/_internal/draft_reviews/draft_review.md`

   **`standard`** — 1× 연구팀 quality reviewer (deep reviewer) + 1× 연구팀 fact-checker (fast fact-checker, parallel):
   - Quality review log: `{strategy_folder}/_internal/draft_reviews/draft_review_quality.md`
   - Fact-check log: `{strategy_folder}/_internal/draft_reviews/draft_review_factcheck.md`

   **`thorough`** — **axis-decomposed parallel 연구팀** (audit-aligned axes 각각 별도 instance) + 1× 연구팀 fact-checker:
   - **Axis A — Content / Strategy coverage** (deep reviewer): strategy 본문이 draft에 모두 반영됐는지, factual coherence, rebuttal mode면 모든 reviewer point에 응답 있는지.
     - Review log: `{strategy_folder}/_internal/draft_reviews/draft_review_content.md`
   - **Axis B — Writing quality** (deep reviewer): 논리 flow, 완전성, 약한 주장 / [TODO] 잔존 등.
     - Review log: `{strategy_folder}/_internal/draft_reviews/draft_review_quality.md`
   - **Axis C — Style Guide compliance** (fast reviewer): strategy의 `## Style Guide` rule을 draft가 _모든_ citation / figure caption / bullet depth / speaker note에서 따랐는지. 일관성 일탈 (`IS 2024` vs `Interspeech 2024` 혼용 같은 것) 식별.
     - Review log: `{strategy_folder}/_internal/draft_reviews/draft_review_style.md`
   - **Axis D — Cross-ref + Coverage** (fast reviewer): draft 안 `cards/{file}.md` link target 존재 + analysis/refs에 있으나 draft에 인용 안 된 orphan card 식별 (omission detection — UniSE-class 누락 방지).
     - Review log: `{strategy_folder}/_internal/draft_reviews/draft_review_coverage.md`
   - **Fact-checker** (fast fact-checker): citation/venue/year/metric/lineage verbatim 대조 (cards/PDFs).
     - Review log: `{strategy_folder}/_internal/draft_reviews/draft_review_factcheck.md`
   - 모든 reviewer가 KO draft에 `<!-- memo: ... -->` 작성. 각자 `[axis name]` prefix 명시 (예: `[STYLE]`, `[COVERAGE]`, `[FACT]`).
   - 5 instance 완료 후 메모 merge + 중복 제거.

   _이 axis decomposition은 "user-catchable points 전부 연구팀이 대신"의 multi-axis 구현. 예: presentation mode 자료에서 사용자가 거슬려할 출처 표기 일관성·orphan 카드 누락·잘못된 모델 분류 모두 별도 axis instance가 책임._

   **Quality reviewer prompt** (light/standard에서 단일 instance가 모든 axes 다룰 때):
   ```
   Review this document draft as the user's domain expert proxy.
   **Task type: paper-driven doc** (mode: {mode}) — apply Role 1 Step 3 axes from adapters/claude/agents/research-team.md, audit-aspect aligned.

   Mode: {mode} | KO draft: {ko_draft_path} | EN draft: {en_draft_path}
   Strategy: {en_strategy_path} | Analysis: {strategy_folder}/analysis/ | Discovered inputs: {discovered_inputs}
   Log: {review_log_path}

   **Default axes** (content / writing quality):
   - Strategy coverage (모든 strategy point가 draft에 반영?), logical flow, completeness, [TODO] 항목.
   - rebuttal mode: 모든 reviewer point에 응답 존재?

   **Audit-aspect axes** (사용자가 거슬려할 만한 점 — plan-time에 미리 catch):
   - **Style Guide compliance** — `## Style Guide` rule이 모든 citation / figure caption / bullet / speaker note에서 _일관_되게 따라졌는가? 출처 표기 혼용 (`IS 2024` vs `Interspeech 2024`) 같은 게 있으면 `[STYLE]` memo.
   - **Cross-ref** — `cards/{file}.md` link target이 모두 존재?
   - **Coverage (omission detection)** — analysis/refs에 있으나 draft에 인용 안 된 _orphan card_ 식별. presentation mode면 슬라이드 어디에도 안 등장하는 card list. `[COVERAGE]` memo.

   Do NOT individually verify each fact citation (venue/year/metric verbatim) — that's the fact-checker's role at standard+.
   Write memos as `<!-- memo: ... -->` in the Korean draft. `[axis prefix]` (예: `[STYLE]`, `[COVERAGE]`) 명시.
   Write a structured review log to the log file.
   Return a summary of memos added (or "no issues found").
   ```

   **Fact-checker prompt** (fast fact-checker, parallel — standard/thorough only):
   ```
   You are a fact-check focused reviewer — NOT narrative quality.
   Mode: {mode} | KO draft: {ko_draft_path} | Discovered inputs: {discovered_inputs} | Log: {fact_log_path}

   For every domain claim in the draft (citation / model name / venue / year /
   metric / dataset / lineage / classification), open the corresponding ground-truth
   source and verbatim compare:
   - Paper analyses: `<artifact-root>/analysis_project/paper/*.md` (if exists — single source of truth, produced by `/analyze-project --mode paper`)
   - Original PDFs: only if listed in {discovered_inputs} AND paper analyses lack the specific fact
   - Strategy: {en_strategy_path} — **DO NOT use as primary source**. Strategy must itself be verified against paper analyses. Using strategy as ground truth = circular reference (forbidden).

   Do NOT comment on writing quality, narrative arc, or strategy coverage — that's the quality reviewer's job.
   Stay narrowly on fact verification. Fast fact-checker mode: table-only output. Limit to ~30 most material claims.

   **CRITICAL — verification rules** (memory `feedback_factcheck_external_reverify.md`):
   - **name-only match ≠ ✅**. If the card contains the model/author name but the _specific venue / year / metric_ is NOT verbatim in the card, classify as 🟡 cards-name-only. Do NOT classify ✅ on name-only basis.
   - **`[외부 추정]` / `[?]` / `[unverified]` markers in the draft** → 🟡 external-marker, trigger WebSearch/WebFetch re-verification. Log the external source URL upon ✅ escalation; otherwise remain 🟡.
   - **Circular reference FORBIDDEN**: do NOT pass a draft claim as ✅ merely because it matches the strategy's `## Style Guide` venue mapping table. Verify against cards _directly_. If only strategy supports it, classify as 🟡 circular-ref-only.

   Output the review log as a single table with a Source type column:
   | Slide/Section | Claim in draft | Source (file:line) | Match (✅/🟡/❌) | **Source type** | Severity (🔴/🟡/🟢) |

   `Source type` values (same as Step 3 fact-checker):
   - `cards-verbatim` — venue/metric verbatim in card → ✅
   - `cards-name-only` — card has name only → 🟡, external reverify
   - `external-marker` — explicit marker present → 🟡, external reverify
   - `external-reverified` — reverified via WebSearch/WebFetch (URL in log) → ✅
   - `conflict` — card has different value → 🔴
   - `circular-ref` — only strategy/draft mutual agreement → 🔴 architecture violation

   For 🔴/🟡 mismatches, also write `<!-- memo: [FACT] slide X — claim Y conflicts with source Z -->` in the Korean draft.
   Return ONLY path + one-line verdict.
   ```

3. If memos were added:
   - **`intensity == quick` short-circuit**: do NOT invoke draft-refine. Memos remain in the draft as audit trail (no edits applied). Log to pipeline_summary Decision Points: `Step 5 | draft refine skipped (intensity=quick) | auto | proceed to Step 6`. Skip to Step 6.
   - **`--user-refine` pause**: if the flag is set, update `pipeline_state.yaml` (`user_refine: true`, `paused_at_stage: draft-refine`), print the resume command (`/autopilot-draft --mode {mode} --from draft-refine {strategy_folder}`), and exit. Do NOT invoke draft-refine.
   - Otherwise: invoke Skill `draft-refine` with the Korean draft path as args.
   - Note: draft-refine handles draft paths (draft/draft.md ↔ draft/draft_ko.md) via auto-detection.
4. If no memos: Skip to Step 5.5. (When resumed via `--from draft-refine`, run draft-refine directly on the pre-existing memos.)
