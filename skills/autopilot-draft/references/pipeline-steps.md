## Pipeline

### Pre-flight Validation [ALL modes — runs first, before any work]
Validate mode-specific required inputs. If any check fails, **abort immediately** with a clear error message — do NOT create the artifact directory or invoke any sub-skills/agents.

**Universal checks** (all modes):
1. Mode is one of the 3 supported modes (`paper` / `presentation` / `doc`) — explicit `--mode` 또는 auto-inference. Otherwise abort: "Unknown mode: {mode}. Supported: paper / presentation / doc."
2. **Input Discovery** (replacing old `--refs` check): run fuzzy match on task description vs `<artifact-root>/analysis_project/{paper,doc}/*` and `<artifact-root>/research/*`. Per mode:
   - `paper` / `presentation`: no hard requirement, but warn if no matches at all and ask user to confirm.
   - `doc`: 자연어 _genre 의도_ 가 분기 — task description 키워드 검사:
     - "rebuttal" / "OpenReview 응답" / "리뷰 응답" → reviewer-comment file in `analysis_project/doc/*/reviewers/` REQUIRED. None → abort with: "rebuttal-response 의도는 reviewer comments 가 필요합니다. `/analyze-project --mode doc <folder>` 로 먼저 materialize 하세요."
     - "peer review" / "review form" / "리뷰 작성" → venue review form in `analysis_project/doc/*/formats/` REQUIRED. None → abort with similar message.
     - 그 외 (report·proposal·blog·memo) → no hard requirement, warn if 0 matches and ask user.
   - Stash discovered paths into orchestrator context as `{discovered_inputs}` for downstream Steps.

**Mode-specific checks**:

**Universal format spec resolution** (runs before mode-specific checks):

1. Auto-discover in `analysis_project/doc/{matching}/formats/` (already classified by `analyze-project --mode doc`):
   - 1 candidate → use it; log "format spec auto-discovered: {path}".
   - 2+ candidates → ask user at Step 0 which to use.
   - 0 candidates → mode-specific fallback below.

**Mode-specific pre-flight** (after universal resolution):

- **`paper` mode** — format spec optional. Absent 시 fallback to generic LaTeX article layout. 학술 venue target 이면 (task description 또는 discovered inputs 로 감지) 강하게 권장: "venue paper template (e.g. NeurIPS LaTeX style) significantly improves draft quality; `/analyze-project --mode doc <folder>` 먼저 실행하세요."

- **`presentation` mode** — format spec **선택적** (markdown deliverable; slide template 적용은 PowerPoint 수동 단계). lab/venue slide template 있으면 wording / 구조 fit 도움.

- **`doc` mode** — _genre 의도 기반 분기_:
  - **peer review 의도** (task description 에 "peer review" / "review form" / "리뷰 작성") → format spec REQUIRED. 부재 시 **abort**: "peer review 작성은 venue review form 이 필요합니다. `analysis_project/doc/{matching}/formats/` 에 form 없으면 `/analyze-project --mode doc <folder>` 로 먼저 추출. Venues differ year-to-year — no built-in presets."
  - **rebuttal-response 의도** ("rebuttal" / "OpenReview 응답" / "리뷰 응답") → 두 check:
    - Reviewer-comment file in `analysis_project/doc/{matching}/reviewers/` REQUIRED (위 Input Discovery 단계에서 abort).
    - Format spec 부재 → prompt user at Step 0: (a) `/analyze-project --mode doc <folder>` 로 materialize / (b) `<task description>` 안에 format constraints (length, sub-type, scope) inline 명시 / (c) generic conference rebuttal layout fallback (warns quality drop). Sub-type info (meta-only / reviewer-dialogue / response-with-revision) 는 format spec file 또는 task description 에서 — _no separate flag_.
  - **그 외 의도** (report · mid-report · post-mortem · grant proposal · tech blog · memo) → format spec optional. Absent 시 fallback to generic prose layout. NRF / NSF / 산학협력단 grant 의도면 기관 template 추천 ("`/analyze-project --mode doc <funding_body_template_folder>` 먼저"). 기업 / 기관 internal template 있으면 동일.

**Abort behavior**:
- Print the error message in Korean to the user.
- Do NOT call `mkdir`, do NOT invoke any sub-skill, do NOT write `pipeline_summary.md`.
- Exit with status: aborted (pre-flight).

After all pre-flight checks pass: create `artifact_dir` and proceed to Step 0.

### Step 0: Scope Clarification (사전 조율) — skipped if `--no-clarify`
> 이 Step 0 은 [CONVENTIONS.md §6.6](../../core/CONVENTIONS.md#66-autopilot-intake-gate) Autopilot Intake Gate 의 문서 트랙 인스턴스 — 4속성(타입 선택지·탈출구·앞 1라운드·비가역 결정 커버리지) 공유, 질문 뱅크는 §6.6 문서 행.

**Purpose**: Catch ambiguous queries before launching the pipeline. autopilot-draft 산출물 품질은 task 명확도에 비례하므로, 모호한 입력은 30% signal·70% noise를 만든다.

**Trigger conditions** (any one matches → run clarification):
- Mode auto-inference 신뢰도 낮음 (키워드 매치 약함, 또는 multi-match)
- Task description < 15 words AND no specific deliverable hint
- Mode가 `review`인데 venue/length/style 미명시
- Mode가 `presentation`인데 청중·시간 미명시
- Mode가 `proposal`인데 grant body·deadline·예산 범위 미명시

**Action**: 메인 에이전트가 mode-aware 2-4개 sharp question을 던진다. 사용자 답변을 task description에 통합 후 Step 1 진행. adapter pause/autonomy rule 적용(Claude Code: [CLAUDE.md](../../adapters/claude/CLAUDE.md) §2) — 질문 던질 때 ScheduleWakeup 15-20분 동시 호출, 답 없으면 가장 가능성 높은 mode·길이·청중 default 로 자율 진행.

**Mode-specific question seed**:
- `paper` / `report` / `proposal`: 청중, 길이/페이지 제한, 강조 포인트, deadline
- `presentation`: 청중 (전공자/비전공자/임원), 시간 (30/45/60min), 핵심 메시지 1개
- `review`: venue / 리뷰 가이드라인 / 점수 체계
- `rebuttal`: rebuttal 길이 제한, 추가 실험 가능 여부, 톤 (defensive vs concessive)

**Skip 조건**:
- `--no-clarify` 명시
- task description이 충분히 구체적 (12+ words + concrete deliverable + constraints)
- `--from <stage>` 재개 (기존 pipeline_state.yaml에 이미 정보 있음)

**Output**: 사용자 답변을 통합한 refined task description을 메모리에 저장 + `pipeline_state.yaml`의 `clarified_intent` 필드에 기록.

### Step 1: Material Analysis
Read and catalog all materials from refs folder.

1. **Inventory**: List all files with brief descriptions. Write to `analysis/material_index.md`.
2. **Analyze by mode**:
   - **rebuttal**: Parse reviewer comments → `analysis/reviewer_analysis.md` (per-reviewer, per-point breakdown with severity classification)
   - **paper**: Analyze reference papers → `analysis/ref_analysis.md` (methods, gaps, positioning opportunities)
   - **review**: Analyze target paper/document → `analysis/ref_analysis.md` (methodology assessment, quality analysis)
   - **report**: Analyze source data/papers → `analysis/ref_analysis.md` (findings, evidence assessment, data quality)
   - **proposal**: Analyze related work and context → `analysis/ref_analysis.md` (prior art, feasibility evidence, competitive landscape)
   - **presentation**: Analyze source document/paper → `analysis/ref_analysis.md` (key messages, audience analysis, narrative structure)
3. Read PDF files using the Read tool. For large PDFs (>10 pages), read in page ranges.
4. Present the analysis summary briefly and auto-proceed to Step 2 — no confirmation required.

### Step 2: draft-strategy
Invoke Skill: `draft-strategy` with args: `<resolved_mode> --inputs <comma-separated-discovered-paths> --output <artifact-dir> <task description>`.

**Mode 변환** (autopilot-draft 의 form-first 3-mode + doc intent → draft-strategy 의 직접 mode 라벨 6종 — 단일 source 는 draft-strategy/SKILL.md `## Mode mapping`):

| autopilot-draft mode | task description intent 키워드 | `<resolved_mode>` |
|---|---|---|
| `paper` | (분기 없음) | `paper` |
| `presentation` | (분기 없음) | `presentation` |
| `doc` | rebuttal · 응답 · OpenReview · reviewer · 반박 | `rebuttal` |
| `doc` | peer review · 심사 · review form · 검토 의견 | `review` |
| `doc` | 보고서 · report · 진행 · 결과 · status · 중간보고 | `report` |
| `doc` | 제안서 · proposal · grant · RFP | `proposal` |
| `doc` | 그 외 (memo · blog · 일반 prose) | `report` (default fallback) |

`<discovered-paths>`는 Pre-flight Step 2 (Input Discovery)가 발견한 `analysis_project/{paper,doc}/...`, `research/{topic}/` 경로 list (콤마 join). 매치 0이면 Pre-flight에서 이미 abort/warn 처리됨. Wait for completion.

**Post-invocation requirement**: After `draft-strategy` returns, read the generated `{strategy_folder}/strategy/strategy.md`. **Verify it contains a `## Style Guide` section.** If absent, append the following template at the strategy file's end, then write the same content (translated) to `strategy_ko.md`:

    ## Style Guide

    > 본 산출물 전반에 적용되는 양식 규칙. Draft 생성·refine 모든 단계에서 이 섹션을 우선 참조.

    ### Citation / venue 표기
    > **사용자 venue 약어맵·표기 선호는 `mem profile 02_paper_writing_style` 의 "Citation·venue 표기" 섹션이 1순위** (사용자 도메인별 venue 약어·형식 — skeleton 이 아니라 profile taste). profile 에 없으면 아래 generic 기본 seed 적용. (2026-06-16 audit #2 — venue 약어맵을 skill 에서 profile 02 로 이관.)
    - published 우선: `{venue 약어} {year}` (공백 1개). arXiv-only: `_arXiv:XXXX.XXXXX_` (italic). 둘 다: `{venue} {year} / arXiv:2402.XXXXX` (학회 → arXiv, slash).
    - Author-year inline: `[Author et al., YYYY]` (대괄호 + comma + space).
    - venue 약어 매핑: `mem profile 02` 의 약어맵 참조 (없으면 published 학회명 그대로). Year 단독 표기 금지 — 항상 venue 동반.

    ### Figure caption template
    - `**Figure N**: {caption 1줄}. Source: cards/{file}.md` (논문 인용 figure인 경우)
    - 자체 도식: `**Figure N**: {caption}` (Source 줄 생략)

    ### Bullet depth
    - 본문 bullet: 최대 3-level. 4-level 이상 금지 (구조 약화).
    - Speaker note (presentation mode): numbered `1. / 2. / 3.` (Markdown ordered list).

    ### Speaker note numbering
    - `1. {발화 1}` / `2. {발화 2}` / `3. {발화 3}` — ordered list, period + space.
    - Dash bullets (`- ...`) 사용 금지 (Speaker note 한정).

    ### 모델 분류 표기 (research cards 기반)
    - 모델명 / venue / task / year는 _반드시_ research cards (`{research_artifact}/cards/*.md`)에서 verbatim 인용.
    - cards에 없는 모델: 본문에서 _제외_하거나 `[?]` 표시. 인용 책임 단일 source: cards.
    - Task category 라벨 통일: 사용된 cards의 `## 분류` section에 등장한 라벨만 사용 (자체 분류 카테고리 신설 금지 — 새 라벨이 필요하면 strategy 본문에 명시 후 cards 보강 별도 진행).

이 Style Guide는 본 artifact의 _single source of truth_ for 양식. Draft 생성·refine 시 이 섹션이 변경되지 않으면 양식 일관성 유지.

### Step 4: Draft Generation
**Applicable modes**: paper / presentation / doc — 모든 form mode 가 draft 를 생성 (doc 의 genre 세분 rebuttal·report·proposal·review 는 draft-strategy 내부 라벨).

#### Step 4.0a: Multi-source Figure Discovery

Draft 생성 전, figure_index.md 또는 figure asset이 있을 수 있는 _세 source_를 순차 검색:

1. **Source 1 — research figures**: `<artifact-root>/research/*/figures/figure_index.md` glob (top match by topic relevance to task description).
2. **Source 2 — analysis_project paper figures**: `<artifact-root>/analysis_project/paper/figures/figure_index.md` (analyze-project --mode paper에서 figure extraction이 함께 수행된 경우 존재).
3. **Source 3 — artifact self figures**: `{artifact_dir}/assets/figures/figure_index.md` 또는 단순히 `{artifact_dir}/assets/figures/*.png` (사용자 직접 추출·생성).

발견된 모든 source의 figure_index를 merge → paper_id × figure path 매핑 dict 생성. 중복은 source 1 > 2 > 3 우선 (research가 가장 신뢰).

#### Step 4.0b: On-demand Figure Extraction (figure_index 부재 시)

세 source 모두 figure_index.md가 없거나 figure assets이 비어 있으면, draft orchestrator가 _자체적으로_ figure extraction 시도:

1. **Source paper PDFs 위치 확인**:
   - `<artifact-root>/analysis_project/paper/cards/*.md`에서 `**PDF 위치**` 또는 `**arXiv ID**` field grep
   - `<artifact-root>/research/*/cards/*.md`에서 동일 field grep
   - 발견된 PDF paths를 input set으로 수집
2. **PDF input set이 비어 있지 않으면 → 자료팀 호출**:
   ```
   Agent(subagent_type="자료팀",
         description="PDF figure/table extraction for doc",
         prompt="pdf-extract mode. Input PDFs: {pdf_paths}.
                 Output: <artifact-root>/analysis_project/paper/figures/ (또는 적합한 공용 위치).
                 figure_index.md 생성 — paper_id × figure path 매핑.
                 본 doc draft에서 자동 embed 용도.

                 **고해상도 정책 (memory feedback_presentation_figure_embed.md 강제)**:
                 - DPI 600-800 (default 800) — publication / PPT zoom-in quality
                 - Caption-aware crop (figure body + caption만, 본문/footer noise 제거)
                 - Two-column paper: column-width 표/figure는 _해당 column만_ crop (이웃 column 잔영 제거)
                 - Page-wide 표 (computational cost 같은): page-wide bbox 유지
                 - 표 (table) 추출도 동일 정책 적용 — 메인 결과 표는 markdown 텍스트보다 paper PNG embed가 _기본_")
   ```
3. **추출 완료 후** figure_index.md를 다시 파싱하여 매핑 dict에 추가 (Source 2 위치).
4. **PDF source도 없으면** warn "figure source 부재 — analyze-project --mode paper 또는 autopilot-research 먼저 호출 권장" → 그대로 draft 진행 (figure embed 없이).

이로써 _autopilot-research를 거치지 않은 doc artifact_도 figure 자동 embed 가능.

#### Step 4.0b-quality: 해상도·crop 정책 (영구 — 메모리 강제)

본 정책은 **모든 PDF 기반 figure / table 추출에 강제 적용** (memory `feedback_presentation_figure_embed.md` Round-3 update, 2026-05-12):

| 항목 | 값 | 비고 |
|---|---|---|
| **Paper figure / table (PDF embedded)** | **DPI 600-800 (default 800)** | publication quality, PPT zoom 200%까지 sharp |
| **Caption-aware crop bbox** | `caption.y_top - 5 ~ next_significant_element.y_top - 5` | caption + body만, 본문/footer noise 제거 |
| **Two-column paper layout** | column-width 표/figure는 _해당 column만_ x bbox 좁히기 | 이웃 column 잔영 제거 (예: ICML left col = x∈[50,303], right col = x∈[315,562]) |
| **Page-wide element** | x_full = [50, page_w-50] 유지 | wide table / wide figure (예: computational cost) |
| **Slide-source render** (samsung seminar 같은 _이미 slide_인 PDF) | DPI 160-180 full page | 페이지 전체 = 한 slide, 추가 crop 불필요 |
| **표 embed default** | _paper crop PNG_ > markdown table | 메인 성능 표 (Table 1/3/9 등) 발표용 — markdown re-typing 대신 paper 직접 캡쳐가 _신뢰성_ 우선 |

**Visual sanity check (orchestrator 측)**: 추출 후 _최소 1-2개 PNG_를 Read tool로 시각 검증. 다른 column 잔영 / footer noise / 텍스트 흐림이 있으면 _즉시 재추출_ (bbox 조정 + DPI 상향).

#### Step 4.0c: Path Convention (자동 계산, 사용자 수동 X)

Draft markdown에 figure embed 시 _상대 경로_는 **draft 파일 위치 기준 자동 계산** — 사용자가 수동으로 path 입력 X. 표준 환경:

- draft 위치: `{artifact_dir}/draft/draft_ko.md` (or draft.md)
- artifact_dir: `<artifact-root>/documents/{date}_{name}/`
- 세 source 별 path:
  - **Source 1 (research)**: `<artifact-root>/research/{topic}/figures/` → draft 기준 `../../../research/{topic}/figures/{file}.png` (3단 위)
  - **Source 2 (analysis_project paper)**: `<artifact-root>/analysis_project/paper/figures/` → draft 기준 `../../../analysis_project/paper/figures/{file}.png` (3단 위)
  - **Source 3 (artifact self)**: `{artifact_dir}/assets/figures/` → draft 기준 `../assets/figures/{file}.png` (1단 위)
- figure_index.md 경로도 위와 동일 패턴

Draft 작성 sub-agent (연구팀)에게 위 path convention을 전달; sub-agent가 잘못된 상대 경로 사용하지 않도록 명시. 세 source 중 어디서 가져온 figure인지에 따라 상대 경로 결정.

#### Step 4.1: Draft Generation (연구팀 호출)

1. Verify strategy is finalized: `{strategy_folder}/strategy/strategy.md` exists and has no `## 미해결 이슈` section (or issues are acceptable).
2. Invoke the **research-team** (연구팀) agent as a subagent:

```
Draft generation mode. Generate a document draft based on the finalized strategy.

Mode: {mode}
Task: {task description}
Strategy (EN): {en_strategy_path}
Strategy (KO): {ko_strategy_path}
Analysis directory: {strategy_folder}/analysis/
Discovered inputs: {discovered_inputs}

**Style Guide (MANDATORY)**: Before writing any draft content, read `{strategy_folder}/strategy/strategy.md` and locate the `## Style Guide` section. Apply its rules to **every** citation, figure caption, bullet depth, speaker note, model classification, and venue/year tag in the draft. Style Guide rules override any default formatting you might use. If the Style Guide says `IS 2024` for Interspeech 2024 papers, you must use `IS 2024` — never `Interspeech 2024` or `Interspeech, 2024`. If a model lookup fails (the cards/* don't contain it), use `[?]` rather than fabricating venue/year.

Save draft to: {strategy_folder}/draft/draft.md (single file — primary language is determined by mode/subtype default below).

**Draft language determination — single source per mode/subtype**:

_draft.md is a **single output** in the primary language for the mode/subtype. There is no `draft_ko.md` / `draft_en.md` mirror by default. A mirror is generated only when the primary language is **not** the user's working language — in that case Step 4-KO is invoked to produce a `_ko.md` mirror; otherwise Step 4-KO is **skipped**._

Mode × genre (자연어 task description 으로 결정) default table:

| mode + genre 의도 | primary language | rationale |
|---|---|---|
| `paper` (학술 본문 — submission / camera-ready / major revision full paper) | **English** | venue is English-only; user reviews English source directly |
| `paper` + task description 에 "camera-ready paste-ready cheatsheet" / "mutation cheatsheet" 같은 _작업 안내문_ 의도 | **Korean** | cheatsheet 자체는 internal work-tool — 사용자가 LaTeX paste 하면서 읽음. 한국어 자연 |
| `presentation` (학회 발표 / 세미나 / 강의) | audience-driven | Korean audience → Korean; English conference talk → English (task description 으로 명시) |
| `doc` + rebuttal-response 의도 | venue-driven (보통 영문) | reviewer 가 venue 언어로 읽음 |
| `doc` + peer review 작성 의도 | venue-driven (보통 영문) | OpenReview / journal portal 영문 |
| `doc` + report / mid-report / post-mortem 의도 | audience-driven | 한국 기관 / 위원회 → Korean; international → English |
| `doc` + grant proposal 의도 | audience-driven | NRF / 산학협력단 → Korean; NSF / Horizon → English |
| `doc` + tech blog / institutional memo 의도 | audience-driven | 청중 / 발행처 따라 |

If the user explicitly states the output language in the task description (e.g., "영문 paper 본문 작성" / "한국어 보고서"), that always wins.

**Language enforcement** — once the primary language is determined, the body of `draft.md` MUST be that language end-to-end:
- All narrative, headers (H1/H2/H3), 위치/Location lines, reasoning lines, paste sequence list, final verification checklist, every comment outside LaTeX blocks
- LaTeX blocks themselves stay as-is (English / math content preserved verbatim)
- For mixed-source content (e.g., a quoted English title in a Korean body), the quote itself stays English but the surrounding prose follows the primary language
- 연구팀 agent default Language Rule (_user-facing output in Korean_) is **overridden** by this primary-language assignment — if primary is English, output English; if Korean, Korean. The orchestrator's prompt must state the primary language explicitly.

**Mirror generation** (Step 4-KO — conditional, NOT default):
- Trigger: primary language ≠ user's working language (e.g., paper body in English, user works in Korean — mirror needed for review).
- If the user's working language is Korean and primary is also Korean (paste-ready cheatsheet / Korean presentation / Korean report), Step 4-KO is **skipped entirely** — no `_ko.md` file produced.
- The editorial-team owns the mirror; 연구팀 does not write `_ko.md` directly.

Read the strategy document and all analysis files. Generate a complete first draft following the mode-specific structure below. The draft should be a working document ready for user editing — not a summary of the strategy.

## Tone Propagation (modes: presentation + doc)

**FIRST**, read the strategy frontmatter `tone` field:
- If `tone: administrative` — apply administrative-tone constraints to the **entire draft** (slide titles, bullets, conclusion, visual placeholders). Specifically:
  - **AVOID**: marketing superlatives ("genuinely novel", "sole occupied axis", "global rights asset", "world-first", "compelling contribution"), "X strengths summary" framing, "core message" + "Hook → Call-to-Action" arc, heroic asks ("Approve to secure as global asset"), decision-options box (approve/conditional/hold), animated narrative voice
  - **PREFER**: simple fact lists, status updates, neutral reporter stance, calm review request ("검토 부탁드립니다" / "kindly request the committee's review")
  - Conclusion slide: replace "Key messages + Call-to-Action" with **"Presentation summary + review request"**; remove "X strengths" enumeration in favor of plain fact recap
  - Speaker stance: **neutral reporter, not advocate**. The speaker (often a student or researcher) is reporting upward to decision-makers, not pitching to peers
- If `tone: default` or absent — existing pitch-deck patterns apply (Hook, Core Message, Story Arc, Call-to-Action, persuasive framing)

This propagation is mandatory: a `tone: administrative` strategy with a heroic-pitch draft is a critical mismatch and must be reworked.

## Mode-Specific Conventions & Draft Structure

> mode 별 conventions 는 본 skill 폴더의 `conventions/` 하위 4 파일에 분리. draft 생성·refine·audit 시점 모두 해당 mode 파일 + `common.md` _필수 read_.

- [§Common (모든 mode 적용)](conventions/common.md) — Paragraph Cohesion 4-step / Anchor 정책 / 약자 정책 / LLM-flavor 회피 / 편집팀 다듬기 / 언어 결정
- [§paper (LaTeX 학술 본문)](conventions/paper.md) — 본문 구조 + Camera-ready Natural-integration rule + 5 rule + Paste-ready cheatsheet 형식 강제 (10 항목 + Hard-fail)
- [§presentation (PPT 슬라이드 markdown)](conventions/presentation.md) — §0~§10 (16:9 분량 / Figure 텍스트 / 공통 scale / window·y-limit / 청중 친화 단위 / 기존 deck 톤 / Asset / Path / raw asset link / Plot 먼저 / 적용 범위) + Slide Format Conventions + Top-of-file guide + 슬라이드 단위 형식 + 구조 요건 + 작성 톤 + Quality
- [§doc (Word/HWP/markdown prose)](conventions/doc.md) — 자연어 genre 의도 별 4 sub-section (보고서·mid-report·post-mortem / grant proposal / rebuttal-response / peer review 작성)

> **외부 폴더 conventions 가 필요하면 안 됨** — autopilot-draft skill 의 4 파일이 single source. SKILL.md 본문에 인용된 룰 (예: §presentation-0 자가 검사) 도 본 4 파일에서 가져온 _복제_ 가 아니라 _참조_.

## Quality Requirements
- **Style Guide compliance**: every claim, citation, figure caption, bullet, and speaker note must match the `## Style Guide` section in `strategy.md`. Style Guide is _the_ authoritative format spec for this artifact — not your generic markdown habits.
- Every claim must trace back to a specific reference in the refs folder or analysis.
- Do NOT fabricate citations, data, or results.
- Mark uncertain or placeholder content with `[TODO: ...]`.
- **Mode-specific completeness criteria**:
  - **paper**: 70-80% — all sections with substantive content, no heading-only sections. camera-ready / paste-ready cheatsheet 의도면 §paper 의 _Paste-ready cheatsheet 형식 강제_ 룰 모두 통과.
  - **presentation**: 70-80% — every slide has 제목/부제(선택)/bullets/시각자료/Speaker note 5 슬롯이 채워짐. Speaker notes ≥80% of content slides. 슬라이드 카운트는 strategy outline과 ±10% 이내. `---` 구분자가 모든 슬라이드 사이에 있는지 확인. **§presentation-0 자가 검사 항목 통과 필수**:
    - 매 슬라이드 bullet ≤ 5~6 줄
    - 매 bullet 한 줄 1~2 키워드 (≤ 10 단어, 풀 문장 X)
    - 그림 / 표 면적 ≥ 60% (시각자료 placeholder 가 _구체적_ — 도식 type + component list + layout/color hint 명시)
    - 표 행 ≤ 6 / 열 ≤ 5 (초과 시 별도 슬라이드 분리)
    - 매 페이지 자가 검사 ("이게 슬라이드 한 장에 들어가는가") 통과 — markdown 본문이 PPT 옮긴 시점에 _분량 초과_ 로 깨지지 않음 보장.
  - **doc**: genre 의도 별 가변.
    - _rebuttal-response 의도_: 90%+ — every reviewer point MUST have a drafted response (hard constraint). Missing a point is a critical error.
    - _peer review 작성 의도_: 80%+ — every required section per the auto-discovered format spec must be filled with concrete claims. Strengths/weaknesses must reference specific paper sections/figures/tables. Score justifications are mandatory.
    - _기술 보고서 / proposal / blog / memo_: 70-80% — all sections with substantive content, no heading-only sections.

Write **only** the English draft. Return ONLY the file path and a 3-5 line Korean summary.
```

3. **IMPORTANT**: Do NOT read, re-write, or duplicate the draft file yourself. The agent writes it directly.

#### Step 4-KO: Mirror generation (편집팀) — _conditional, NOT default_

**Skip condition (default)**: primary draft language == user's working language. In that case `draft.md` 자체가 사용자 영역 산출이므로 mirror 단계 자체가 불필요. 진행하지 않는다.

**Trigger**: primary draft language ≠ user's working language. 예:
- paper mode (academic body) — primary English, user works in Korean → English `draft.md` + Korean `draft_ko.md` mirror for review
- presentation mode with English audience, Korean user → English `draft.md` + Korean `draft_ko.md` mirror

When triggered, invoke the **편집팀** (editorial-team) agent in 모드 A (옮기기) — the only path to `_ko.md` / `_en.md` mirror.

```
모드 A — {원본 언어}에서 {대상 언어}로 옮기기.
원본 draft 경로: {strategy_folder}/draft/draft.md
대상 출력 경로: {strategy_folder}/draft/draft_{ko|en}.md
<agent-home>/adapters/claude/agents/editorial-team.md 의 모드 A 절차를 따른다.
<agent-home>/adapters/claude/agents/editorial-team.md 의 판교체 회피 절(표기 결정·거부 패턴)을 강제 적용 (한국어 산출 시). 사용자 표기 선호는 `mem profile 02_paper_writing_style` 보조 참조.
모드별 영어 유지 어휘 ({mode} 에 맞게):
- paper/rebuttal/review: LaTeX 명령·논문 제목·저자·학회·약자·모델·데이터셋·지표는 영어 그대로
- report/proposal: 회사·기관·프로젝트·기술 용어는 영어 그대로
- presentation: 슬라이드의 본문 인용·LaTeX·모델·논문 제목은 원본 언어 그대로
한 문서 안에서 같은 개념은 같은 표기로 통일.
완료 시 파일 경로 + 한국어 요약 3-5 줄 + 의도적으로 한 표기 결정 한두 개만 돌려준다.
```

> **사용자 작업 언어 판정**: orchestrator (메인 에이전트) 가 task description 의 language signal (사용자가 어느 언어로 prompt 를 줬는지, _영문/국문 양쪽_ 같은 명시 단어, venue 정보) 을 보고 판정. 모호하면 Step 0 Scope Clarification 에서 확인 (있으면).

### Step 4b — Post-draft factual detector (orchestrator-side, all modes)

**Always runs** — even at `--qa quick` or `--qa light`. Orchestrator executes directly (no sub-agent). Cost is small: regex + cards grep only.

1. **Run detector**: apply regex + cards lookup + section-context cross-check to `{strategy_folder}/draft/draft.md` (and the mirror file `draft_ko.md` or `draft_en.md` if Step 4-KO was triggered).
   - For each domain claim (model name / venue / year / metric / dataset / lineage / citation), attempt lookup in `{research_artifact}/cards/*.md`.
   - Classify each claim as: **verified** (exact match in cards), **unverified** (no matching card found), **ambiguous** (partial match or unclear), **conflict** (cards contain contradicting value).
2. **Classify results**: count N (unverified), M (ambiguous), K (conflict).
3. **Do NOT modify the draft** — preserve the sub-agent's output verbatim.
4. **Append row to `{strategy_folder}/pipeline_summary.md` Decision Points section**:
   ```
   | Step 4 | draft factual check | auto | {N + K} unverified/conflict + {M} ambiguous in draft — recommend /audit before publish |
   ```
5. **One-line chat alert** (Korean):
   ```
   ⚠ Draft 사실 확인: 미검증 {N}건, 모호 {M}건, 충돌 {K}건 — `/audit {artifact_short_name} --scope facts` 권장 (draft 단계라 facts 측면 명시; 점검만 하려면 `--report-only` 추가, 그렇지 않으면 자동으로 autopilot-refine fix-chain 트리거)
   ```

If N + M + K == 0: emit `✅ Draft 사실 확인: 검증된 클레임 {verified}건, 문제 없음` and log accordingly.

### Step 5.5: Editorial polish (편집팀 모드 B — conditional)

draft 본문이 사용자가 직접 검토 / paste 작업하는 산출물 — final 단계 직전에 _마지막 1회_ 편집팀 다듬기.

호출 조건 (single source — `adapters/claude/agents/editorial-team.md` 모드 B 호출 조건):
- `qa_level` 가 **standard / thorough / adversarial** 일 때만 호출. `quick` / `light` 는 skip.
- skip 시 곧장 Step 6 (pipeline_summary) 진행.

```
Agent({
  subagent_type: "편집팀",
  prompt: `polish {strategy_folder}/draft/draft.md (and {strategy_folder}/draft/draft_ko.md if Step 4-KO mirror exists)
사용자가 직접 검토·paste 하는 draft 다. 편집팀 모드 B 다듬기 — 판교체 정리·표기 일관성·호흡.
보존: 본문 _내용_ (claim / 수치 / citation / 결정 / LaTeX 블록 / 코드 블록 / 수식 블록). 다듬기 대상: 한국어 wording · 영문 어색한 표현 · 표기 일관성 만.`
})
```

편집팀이 in-place Edit 으로 마무리한 뒤 Step 6 진행. (단발성 — single-pass, snapshot X.)

> **paper mode + paste-ready cheatsheet subtype**: LaTeX 블록 안 본문은 편집팀이 _읽지만 수정 안 함_. cheatsheet 의 한국어 안내 wording 만 polish.
