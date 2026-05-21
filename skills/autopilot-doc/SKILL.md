---
name: autopilot-doc
description: "Document strategy & draft pipeline — analyze → strategy → strategy-refine → draft → draft-refine → finalize. 6 modes produce both strategy AND draft (markdown only). All inputs (refs / templates / reviewer comments / samples) are discovered implicitly from `.claude_reports/{analysis_project,research}/*` — pre-process external materials via `/analyze-project --mode {paper|doc}` first (cwd 자동 발견). Format specs (venue/journal/lab guidelines + templates + samples) are auto-loaded from `analysis_project/doc/{matching}/formats/` — no explicit `--format-ref` flag. `review` mode hard-fails if format spec missing; other modes warn-and-fallback to generic layout. `presentation` mode produces slide-by-slide markdown only (PPTX export NOT supported — use PowerPoint directly); slide template format-ref is N/A since markdown is the deliverable."
argument-hint: "<task description> [--mode rebuttal|paper|review|report|proposal|presentation] [--qa quick|light|standard|thorough] [--user-refine] [--no-clarify] [--from analyze|strategy|strategy-refine|draft|draft-refine|finalize]"
---

> **산출물 폴더 컨벤션**: [SKILL_OUTPUT_CONVENTION.md](../../SKILL_OUTPUT_CONVENTION.md) (3-tier: T1 root / T2 named subdir / T3 `_internal/`). reviewer 로그는 `_internal/strategy_reviews/`·`_internal/draft_reviews/`. 버전 스냅샷은 `_internal/versions/v{N}/strategy/`, `v{N}/draft/` (refine-doc의 `_v{N}.md` 형제 패턴은 폐기).

## Language Rule
- Write user-facing output in Korean. (Material analysis results and pipeline_summary.md are written directly in the artifacts — no separate user output needed for those steps.)

## Argument Parsing
Parse `$ARGUMENTS` for mode, flags, and task description:

**`--mode` (optional, auto-inferred from query)**:
- `rebuttal` — Rebuttal strategy for reviewer comments
- `paper` — Academic paper writing / camera-ready / major revision (outline, positioning, contributions). Covers initial submission, accepted-paper finalization, and revision cycles.
- `review` — Paper/document review (as reviewer: strengths/weaknesses/questions). Produces strategy + full review draft (OpenReview-ready).
- `report` — Technical report / white paper (findings, analysis, recommendations)
- `proposal` — Research or project proposal (problem, approach, plan, budget)
- `presentation` — Presentation strategy (story arc, slide structure, key messages) + slide-by-slide markdown draft. PPTX export is NOT performed by this pipeline (markdown-only); use PowerPoint manually with the lab template.

**Auto-inference** (mode 미지정 시):
- "리뷰 응답·rebuttal·reviewer comment" → `rebuttal`
- "발표·세미나·슬라이드·presentation" → `presentation`
- "리뷰·review·peer review·reviewer 입장" → `review`
- "보고서·report·기술 분석" → `report`
- "제안서·proposal·연구계획·grant" → `proposal`
- "논문·paper·camera-ready·revision·book chapter·기술 블로그" → `paper`
- 그 외 / 명시적이지 않으면 → `paper` (default for academic longform)
- 추론 결과를 한 줄로 사용자에게 통보 후 진행. 모호하면 Step 0 Scope Clarification에서 확인.

> **Note**: `survey` mode is removed. For 학술/산업/시장 조사, use `/autopilot-research --mode academic|technology|market` first → autopilot-doc은 `research/{topic}/` artifact를 implicit으로 자동 발견.

**Input Discovery (implicit, no `--refs` flag)** — `--refs <folder>`는 family에서 제거됨. 입력은 `.claude_reports/` 하위 영속 산출물에서 자동 발견:

- **`analysis_project/paper/`** — 보유 논문 분석 (autopilot-doc의 모든 모드에서 활용 가능)
- **`analysis_project/doc/{matching}/`** — doc-creation 자료 (reviewer comments, format templates, samples). `{matching}`은 task description 키워드와 fuzzy match.
- **`research/{topic}/`** — 외부 분야 조사 (autopilot-research가 만든 artifact). 마찬가지로 fuzzy match.
- **`analysis_project/code/`** — 코드 컨텍스트 (proposal/report 모드에서 종종 인용)

mode별 _필수_ 입력:
| mode | 필수 input | 권장 input |
|---|---|---|
| `rebuttal` | `analysis_project/doc/{matching}/reviewers/` (reviewer comments) | `analysis_project/paper/` (원 paper 분석), `analysis_project/doc/{matching}/formats/` (rebuttal guideline) |
| `review` | `analysis_project/doc/{matching}/formats/` (review form) | `analysis_project/paper/` (대상 paper 분석) |
| `paper` | (없음) | `analysis_project/paper/`, `analysis_project/doc/{matching}/formats/` (venue paper template), `research/{topic}/` (분야 컨텍스트) |
| `proposal`, `report`, `presentation` | (없음) | mode 적합한 자료들 (위 패턴 응용) |

매치 0: 사용자에게 안내 — "필요 자료를 `analyze-project --mode {paper|doc} <folder>` 로 먼저 사전 분석하세요" + 진행 여부 확인.
매치 다수: 후보 list 보여주고 선택 요청.

> **Prompt template variables**: 본 SKILL.md의 agent/sub-skill prompt 안에 등장하는 변수:
> - `{discovered_inputs}` — Pre-flight Step 2 (Input Discovery)에서 결정된 input path list. Agent prompt 구성 시 orchestrator가 newline-join 형식으로 expand (`Discovered inputs:\n  - <path1>\n  - <path2>\n  ...`). sub-skill 호출 시에는 `--inputs <comma-separated paths>` 인수로 전달.
> - 단일 ground-truth 경로는 `analysis_project/paper/*.md` (analyze-project --mode paper 산출물; cards/ 서브디렉터리는 폐기된 옛 컨벤션).
>
> Mode별 _자동 발견 입력 카테고리_ (Pre-flight에서 결정):
> - rebuttal: `analysis_project/doc/{matching}/reviewers/` + `analysis_project/paper/` (선택) + `analysis_project/doc/{matching}/formats/` (선택)
> - review: `analysis_project/doc/{matching}/formats/` (REQUIRED) + `analysis_project/paper/` (선택)
> - paper/proposal/report/presentation: 사용 가능한 `analysis_project/paper/` + `research/{topic}/` + `analysis_project/doc/{matching}/formats/` 조합

**`--qa <level>`** — override QA intensity for the pipeline:
- `--qa quick` → fastest path: **skip Step 3 (strategy refine) and Step 5 (draft refine) entirely** + run a single sonnet quality reviewer pass at each review point with **no re-invoke** even if memos are added (memos are saved as audit trail, refine-doc is NOT invoked). `--user-refine` is silently ignored. fact-checker disabled.
- `--qa light` → 연구팀 review uses sonnet, single-pass review
- `--qa standard` → 연구팀 quality reviewer (opus) **+ 연구팀 fact-checker (sonnet, parallel)** — fact-checker performs verbatim cards/PDFs 대조
- `--qa thorough` → 2× 연구팀 quality reviewers in parallel (opus, domain expert + methodology) **+ 연구팀 fact-checker (sonnet, parallel)**, cross-validation against all reference materials **(default)**
- If omitted, defaults to `thorough`.
- **Why a separate fact-checker**: quality reviewers focus on narrative/coverage/logic; fact-checker narrowly verifies citation/venue/year/metric/lineage against ground-truth sources (cards/PDFs). Sonnet is sufficient because fact-check is a matching task, not creative judgment.
- **Propagation**: Pass `--qa <level>` to init-doc-strategy and refine-doc as an argument flag.
- **`quick` mode interactions**: On `--from strategy-refine` or `--from draft-refine`, if frontmatter `qa_level == quick`, abort with: "qa_level=quick에서는 refine 단계가 스킵됩니다. --qa <level>을 다른 값으로 명시해 재개하세요."

**`--user-refine`** (boolean flag — opt-in only)

**Default: false. The orchestrator (메인 Claude) MUST NOT add this flag on its own — it is set only when the user typed `--user-refine` (or an explicit Korean equivalent like "사용자 검토 끼워" / "memo 추가하게 멈춰줘") in the original prompt.** Inferring this flag from generic "신중히 진행해 줘" / "한 번 봐줘" / camera-ready / submission 같은 high-stakes 신호로 자동 추가하는 행동 금지 — 그 경우 사용자가 의도하지 않은 pause 가 걸려 작업이 멈춘다.

When present, pause at refine points so the user can add their own `<!-- memo: ... -->` comments on top of 연구팀's memos before refine-doc runs.

Pause behavior: after 연구팀 writes memos at Step 3 (strategy review) or Step 5 (draft review), do NOT invoke refine-doc. Instead:
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
- `analyze` — Step 1 (Material Analysis)
- `strategy` — Step 2 (init-doc-strategy)
- `strategy-refine` — Step 3 wrapper: 연구팀 review + (user memos if `--user-refine`) + refine-doc on the strategy
- `draft` — Step 4 (Draft Generation)
- `draft-refine` — Step 5 wrapper: 연구팀 review + (user memos if `--user-refine`) + refine-doc on the draft
- `finalize` — Step 6 (Pipeline Summary)

When resuming with `--from`, the positional argument should be either the artifact directory path or a fuzzy-matchable short name. The orchestrator resolves it via the same fuzzy lookup used by Plan Resolution in autopilot-code: `ls -d .claude_reports/documents/*$ARG* 2>/dev/null`. Read `pipeline_state.yaml` to recover `mode`, `qa_level`, `discovered_inputs` (list), `user_refine`. CLI flags override state file; missing flags inherit from state.

**Format spec auto-discovery (no flag)** — venue/journal/lab-specific format references (review form / rebuttal template / paper template / grant body sections / etc.) are discovered automatically from `analysis_project/doc/{matching}/formats/`. There is no `--format-ref` flag. User pre-processes the spec once via `/analyze-project --mode doc <folder>`, after which all autopilot-doc modes pick it up.

- **No built-in presets**. There is no single "openreview format" or "journal format" — even the same venue changes its review/rebuttal template year-to-year, and journals/labs each define their own. The user pre-processes the actual document via `/analyze-project --mode doc`.
- **Acceptable file types in `formats/`**: `.md`, `.txt`, `.pdf`, `.html`, `.docx` (or any plain-text-ish format the agent can Read).

**What the format spec should contain** (any subset — agent extracts what it can):

| Mode | format spec typical content |
|---|---|
| `review` | review template sections / rating axes (1-N with labels) / length limit / tone / submission portal layout |
| `rebuttal` | rebuttal length limit / allowed scope / **sub-type indication** (meta-reviewer-only one-shot vs reviewer-dialogue multi-round vs response-with-paper-revision) / submission window / examples of past-year rebuttals if available |
| `paper` | venue paper template (e.g. NeurIPS 2026 LaTeX style) / page limits / section requirements / citation style / required disclosures |
| `presentation` | lab/venue slide template / time limits / required sections / branding rules / sample past presentations |
| `proposal` | grant body's required sections (NRF/NSF/internal) / page/word limits / required attachments / evaluation criteria |
| `report` | company/team report template / required sections / branding / audience expectations |

**Resolution order** (every mode):

1. **Auto-discovery in `analysis_project/doc/{matching}/formats/`** — agent looks at `analysis_project/doc/{matching}/formats/*` (where `{matching}` was discovered by Input Discovery). The format extraction was already performed by `analyze-project --mode doc`.
   - 1 candidate found → use it, log to user: "format spec auto-discovered: {path}".
   - 2+ candidates → ask user at Step 0 to pick one.
   - 0 candidates → mode-specific fallback (below).
2. **Mode-specific fallback** when auto-discovery yields no candidate:

| Mode | Behavior when no format spec available |
|---|---|
| `review` | **Hard fail at pre-flight** — review mode cannot proceed without a venue review form. Abort with: "review mode requires a format file in `analysis_project/doc/{matching}/formats/` — run `/analyze-project --mode doc <folder>` first to extract it. Venues differ year-to-year — no built-in presets." |
| `rebuttal` | **Pre-flight prompt** — ask user: (a) materialize the format via `/analyze-project --mode doc <folder>` and retry, or (b) declare format constraints inline in `<task description>` (length limit, sub-type, scope), or (c) opt into generic conference rebuttal layout (warn quality drop). |
| `proposal` | Warn-and-fallback to generic proposal layout. Recommend running `/analyze-project --mode doc <funding_body_template_folder>` first for NRF/NSF/internal grants. |
| `paper` | Warn-and-fallback to generic paper/article layout. Strong warning if target venue is academic — Suggest: "venue paper template (e.g. NeurIPS LaTeX style) significantly improves draft quality; run `/analyze-project --mode doc <folder>` first to extract it." |
| `presentation` | Warn-and-fallback to generic slide-by-slide markdown. Lab/venue slide templates improve fit but not blocking. |
| `report` | Warn-and-fallback to generic report layout. Suggest internal company template if applicable (preprocess via `analyze-project --mode doc`). |

> Sub-type information for rebuttal (meta-only / reviewer-dialogue / response-with-revision), section structure for review, page limits for paper, etc. are all **extracted from the auto-discovered format spec file**. No separate flags. If the file lacks the info, agent asks the user at Step 0 (within fallback prompt) or proceeds with documented assumptions.

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
| Format spec resolution | _Always_ from `analysis_project/doc/{matching}/formats/` (classified by `analyze-project --mode doc` in advance). No `--format-ref` flag. If missing, mode-specific fallback: `review` hard-fails; `rebuttal` prompts user; `paper`/`proposal`/`report` warn-and-fallback to generic layout; `presentation` N/A (markdown only). |
| Reviewer guidelines absent in refs (review mode) | Use built-in spec only; inform user. |
| Scope Clarification triggered | Ask 2-4 questions; auto-proceed if `--no-clarify`. |

**Logging**: When the pipeline pauses (missing required input, 0 search results, or `--user-refine`), record the event for the Decision Points table in `pipeline_summary.md`. Auto-decisions are not individually logged.

## pipeline_state.yaml

Written/updated at `{strategy_folder}/pipeline_state.yaml` after each completed stage. Used by `--from` resume:

```yaml
pipeline: autopilot-doc
mode: presentation
qa_level: thorough
user_refine: true
discovered_inputs:                    # list of paths discovered by Pre-flight Step 2 (Input Discovery)
  - <path-to-analysis_project/paper-or-doc-or-research-artifact>
  - ...
format_ref: <path or null>          # auto-discovered from analysis_project/doc/{matching}/formats/ (no flag)
format_ref_source: <auto-discovered|user-supplied-at-prompt|fallback-generic>
clarified_intent: <string or null>    # captured by Step 0 Scope Clarification, used on resume
last_completed_stage: strategy        # one of: clarify, analyze, strategy, strategy-refine, draft, draft-refine, finalize
paused_at_stage: strategy-refine      # set only when --user-refine triggered a pause
artifact_dir: <abs path>
```

CLI flags on resume override stored values. After the pause is consumed (refine completes), clear `paused_at_stage` and update `last_completed_stage`.

## Input Sources Convention

External materials must be pre-processed into `.claude_reports/` _before_ invoking autopilot-doc. The pipeline reads from these persistent sources only — no `--refs` flag, no ad-hoc folder paths.

| Input type | Pre-processing skill | Output location |
|---|---|---|
| Academic papers (PDFs) | `/analyze-project --mode paper` | `analysis_project/paper/` |
| Reviewer comments / format templates / past samples / mixed doc materials | `/analyze-project --mode doc <folder>` | `analysis_project/doc/{name}/` |
| External field research | `/autopilot-research <topic>` | `research/{topic}/` |
| Codebase context (proposal/report 모드에서 언급용) | `/analyze-project --mode code` | `analysis_project/code/` |

On invocation, autopilot-doc runs Input Discovery (Pre-flight Step 2) — fuzzy match task description vs above persistent sources — and gathers `discovered_inputs` paths to pass to sub-skills. For rebuttal mode, fails with clear message if no reviewer materials match.

## Artifact Structure
All outputs go to:
```
.claude_reports/documents/{YYYY-MM-DD}_{short-name}/
├─ pipeline_summary.md       (T1 — entry/index + integrated history)
├─ draft/                    (T1 — generated for all 6 modes; latest only)
│  ├─ draft.md              (English draft; for presentation: slide-by-slide markdown)
│  └─ draft_ko.md           (Korean draft)
├─ strategy/                 (T2 — latest only)
│  ├─ strategy.md           (English strategy document)
│  └─ strategy_ko.md        (Korean strategy document)
├─ analysis/                 (T2)
│  ├─ reviewer_analysis.md   (rebuttal: per-reviewer breakdown)
│  ├─ ref_analysis.md        (reference material analysis)
│  └─ material_index.md      (inventory of all input materials)
└─ _internal/                (T3 — audit / reviews / version snapshots)
   ├─ strategy_reviews/      (QA and 연구팀 strategy reviews)
   ├─ draft_reviews/         (QA and 연구팀 draft reviews)
   └─ versions/              (autopilot-refine snapshots)
      ├─ v1/strategy/, draft/
      └─ v{N}/...
```

## Pipeline

### Pre-flight Validation [ALL modes — runs first, before any work]
Validate mode-specific required inputs. If any check fails, **abort immediately** with a clear error message — do NOT create the artifact directory or invoke any sub-skills/agents.

**Universal checks** (all modes):
1. Mode is one of the 6 supported modes (rebuttal / paper / review / report / proposal / presentation) — explicit `--mode` 또는 auto-inference. Otherwise abort: "Unknown mode: {mode}. Supported: ...".
2. **Input Discovery** (replacing old `--refs` check): run fuzzy match on task description vs `.claude_reports/analysis_project/{paper,doc}/*` and `.claude_reports/research/*`. Per mode:
   - rebuttal: at least one match in `analysis_project/doc/*/reviewers/` REQUIRED. If none → abort with: "rebuttal mode needs reviewer comments. Run `/analyze-project --mode doc <folder>` first to materialize them."
   - review: at least one match in `analysis_project/doc/*/formats/` REQUIRED. If none → abort with similar message for review form.
   - paper/proposal/report/presentation: no hard requirement, but warn if no matches at all and ask user to confirm.
   - Stash discovered paths into orchestrator context as `{discovered_inputs}` for downstream Steps.

**Mode-specific checks**:

**Universal format spec resolution** (runs before mode-specific checks):

1. Auto-discover in `analysis_project/doc/{matching}/formats/` (already classified by `analyze-project --mode doc`):
   - 1 candidate → use it; log "format spec auto-discovered: {path}".
   - 2+ candidates → ask user at Step 0 which to use.
   - 0 candidates → mode-specific fallback below.

**Mode-specific pre-flight** (after universal resolution):

- **review mode** — format spec is REQUIRED.
  - If still no format spec after auto-discovery → **abort** with: "review mode requires a format file in `analysis_project/doc/{matching}/formats/`. Run `/analyze-project --mode doc <folder>` first to extract it. Venues differ year-to-year — no built-in presets. Acceptable file types: .md/.txt/.pdf/.html/.docx."

- **rebuttal mode** — two checks:
  - Reviewer-comment file required in `analysis_project/doc/{matching}/reviewers/` (txt/md/pdf with reviewer-style content). If none found after Input Discovery, ask the user before proceeding.
  - format spec absent (no auto-discovery hit) → prompt user at Step 0: "(a) materialize the format via `/analyze-project --mode doc <folder>` and retry / (b) declare format constraints (length, sub-type, scope) inline in `<task description>` / (c) opt into generic conference rebuttal layout (warns quality drop)". Sub-type info (meta-only / reviewer-dialogue / response-with-revision) is extracted from the format spec file or stated in task description — _no separate flag_.

- **presentation mode** — format spec **N/A** (markdown deliverable; slide template은 PowerPoint 단). 사용자가 task에 format 관련 표현을 넣어도 markdown 산출 자체에는 무시.

- **proposal / report / paper modes** — format spec optional. If absent, fallback to generic mode-specific layout. For `paper` targeting an academic venue (detected from task description or discovered inputs), strongly recommend pre-processing the venue's paper template via `/analyze-project --mode doc`.

**Abort behavior**:
- Print the error message in Korean to the user.
- Do NOT call `mkdir`, do NOT invoke any sub-skill, do NOT write `pipeline_summary.md`.
- Exit with status: aborted (pre-flight).

After all pre-flight checks pass: create `artifact_dir` and proceed to Step 0.

### Step 0: Scope Clarification (사전 조율) — skipped if `--no-clarify`
**Purpose**: Catch ambiguous queries before launching the pipeline. autopilot-doc 산출물 품질은 task 명확도에 비례하므로, 모호한 입력은 30% signal·70% noise를 만든다.

**Trigger conditions** (any one matches → run clarification):
- Mode auto-inference 신뢰도 낮음 (키워드 매치 약함, 또는 multi-match)
- Task description < 15 words AND no specific deliverable hint
- Mode가 `review`인데 venue/length/style 미명시
- Mode가 `presentation`인데 청중·시간 미명시
- Mode가 `proposal`인데 grant body·deadline·예산 범위 미명시

**Action**: 메인 Claude가 mode-aware 2-4개 sharp question을 던진다. 사용자 답변을 task description에 통합 후 Step 1 진행.

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

### Step 2: init-doc-strategy
Invoke Skill: `init-doc-strategy` with args: `<mode> --inputs <comma-separated-discovered-paths> --output <artifact-dir> <task description>`. `<discovered-paths>`는 Pre-flight Step 2 (Input Discovery)가 발견한 `analysis_project/{paper,doc}/...`, `research/{topic}/` 경로 list (콤마 join). 매치 0이면 Pre-flight에서 이미 abort/warn 처리됨. Wait for completion.

**Post-invocation requirement**: After `init-doc-strategy` returns, read the generated `{strategy_folder}/strategy/strategy.md`. **Verify it contains a `## Style Guide` section.** If absent, append the following template at the strategy file's end, then write the same content (translated) to `strategy_ko.md`:

    ## Style Guide

    > 본 산출물 전반에 적용되는 양식 규칙. Draft 생성·refine 모든 단계에서 이 섹션을 우선 참조.

    ### Citation format
    - 학회/저널 published 우선: `IS 2024`, `T-ASLP 2023`, `ICASSP 2025`, `Interspeech 2024`, `NeurIPS 2024` (학회명 약어 + 4-digit year, 공백 1개).
    - arXiv-only 논문: `_arXiv:XXXX.XXXXX_` (italic, prefix `arXiv:`).
    - 둘 다 존재: 학회 우선 표기 + arXiv id 보조 `IS 2024 / arXiv:2402.XXXXX` (slash 구분, 학회 → arXiv 순).
    - Author-year inline: `[Wang et al., 2024]` (대괄호 + comma + space).

    ### Year / venue 표기 표준
    - 학회 논문: `{학회 약어} {year}` (e.g., `Interspeech 2024`, `ICASSP 2025`).
    - 약어 매핑 고정: `Interspeech → IS`, `ICASSP → ICASSP`, `NeurIPS → NeurIPS`, `ICLR → ICLR`, `T-ASLP → T-ASLP`, `JASA → JASA`.
    - arXiv preprint: `arXiv:{YYMM.XXXXX}` (italic 권장).
    - Year 단독 표기 금지: 항상 venue 동반.

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

### Step 3: Strategy Review (연구팀 as domain expert)
1. Resolve strategy paths:
   - `strategy_folder` = `.claude_reports/documents/{YYYY-MM-DD}_{short-name}/`
   - `en_strategy_path` = `{strategy_folder}/strategy/strategy.md`
   - `ko_strategy_path` = `{strategy_folder}/strategy/strategy_ko.md`

2. Invoke reviewers based on `--qa` level. **Quality reviewer(s) and fact-checker run in parallel** at standard+:

   **`quick`** — Single 연구팀 quality reviewer (sonnet, spot-check only):
   - One-pass review. Memos may be added but refine-doc is NOT invoked at Step 3 (see step 3 below).
   - Review log: `{strategy_folder}/_internal/strategy_reviews/research_review.md`

   **`light`** — Single 연구팀 quality reviewer (sonnet):
   - One-pass review focusing on critical issues only.
   - Review log: `{strategy_folder}/_internal/strategy_reviews/research_review.md`

   **`standard`** — 1× 연구팀 quality reviewer (opus) + 1× 연구팀 fact-checker (sonnet, parallel):
   - Quality review log: `{strategy_folder}/_internal/strategy_reviews/research_review_quality.md`
   - Fact-check log: `{strategy_folder}/_internal/strategy_reviews/research_review_factcheck.md`

   **`thorough`** (default) — **axis-decomposed parallel 연구팀** (모든 audit-aligned axes를 각각 별도 instance가 검토) + 1× 연구팀 fact-checker:
   - **Axis A — Domain quality** (opus): refs/reviewer comments 대조, 학술 venue 컨벤션 (NeurIPS / ICML / ICASSP / Interspeech / T-ASLP — paper modes), industry standards (report/proposal/presentation), 완전성 / cohesion.
     - Review log: `{strategy_folder}/_internal/strategy_reviews/research_review_domain.md`
   - **Axis B — Methodology** (opus): 논리 일관성, 주장 설득력, 실험 설계, adversarial reviewer 약점.
     - Review log: `{strategy_folder}/_internal/strategy_reviews/research_review_methodology.md`
   - **Axis C — Style Guide** (sonnet): `## Style Guide` section 존재 + citation/figure-caption/bullet-depth/speaker-note 양식 일관성.
     - Review log: `{strategy_folder}/_internal/strategy_reviews/research_review_style.md`
   - **Axis D — Cross-ref + Coverage** (sonnet): `cards/{file}.md` 인용 target 존재 + analysis/refs에 있으나 strategy에 인용 안 된 _orphan card_ 식별 (omission detection — UniSE-class 누락 방지).
     - Review log: `{strategy_folder}/_internal/strategy_reviews/research_review_coverage.md`
   - **Fact-checker** (sonnet): citation/venue/year/metric/lineage verbatim 대조 (cards/PDFs).
     - Review log: `{strategy_folder}/_internal/strategy_reviews/research_review_factcheck.md`
   - 모든 reviewer가 `<!-- memo: ... -->` 코멘트를 KO strategy에 작성. 각자 `[axis name]` prefix 명시 (예: `[STYLE]`, `[COVERAGE]`).
   - 5 instance 완료 후 메모 merge + 중복 제거.

   _이 axis decomposition은 "user-catchable points 전부 연구팀이 대신"의 multi-axis 구현 — 한 instance가 모든 axis를 다루기 부담스러운 thorough+에서 활성_.

   **Quality reviewer prompt** (light/standard/thorough A & B):
   ```
   Review this document strategy as the user's domain expert proxy.
   **Task type: paper-driven doc** (mode: {mode}) — apply Role 1 Step 3 axes from agents/research-team.md, with audit-aspect alignment.

   Mode: {mode} | KO strategy: {ko_strategy_path} | EN strategy: {en_strategy_path}
   Analysis: {strategy_folder}/analysis/ | Discovered inputs: {discovered_inputs} | Log: {review_log_path}

   **Default axes** (quality / cohesion / coverage):
   - Cross-check: actual refs/reviewer comments, domain conventions
   - Logical consistency, completeness (any missed reviewer points or gaps?)

   **Audit-aspect axes** (catch what /audit would catch, _at plan time_):
   - **Style Guide compliance** — `## Style Guide` section exists in strategy.md? Citation/figure-caption/bullet-depth/speaker-note rules followed?
   - **Structure** — T1/T2/T3 layout per SKILL_OUTPUT_CONVENTION.md respected?
   - **Cross-ref** — every `cards/{file}.md` citation target exists?
   - **Coverage (omission detection)** — are there cards/papers in analysis/refs that the strategy SHOULD cite but doesn't? Flag as `<!-- memo: [COVERAGE] ... -->` per orphan.

   Do NOT verify individual fact citations (model venue/year/metric) — that's the fact-checker's role at standard+.
   Write memos as `<!-- memo: ... -->` in the Korean strategy.
   Write a structured review log to the log file.
   Return a summary of memos added (or "no issues found").
   ```

   **Fact-checker prompt** (sonnet, parallel — standard/thorough only):
   ```
   You are a fact-check focused reviewer — NOT narrative quality.
   Mode: {mode} | KO strategy: {ko_strategy_path} | Discovered inputs: {discovered_inputs} | Log: {fact_log_path}

   For every domain claim in the strategy (citation / model name / venue / year /
   metric / dataset / lineage / classification), open the corresponding ground-truth
   source and verbatim compare:
   - Paper analyses: `.claude_reports/analysis_project/paper/*.md` (if exists — single source of truth, produced by `/analyze-project --mode paper`)
   - Original PDFs: only if listed in {discovered_inputs} AND paper analyses lack the specific fact
   - Reviewer comments (rebuttal mode): {strategy_folder}/analysis/reviewer_analysis.md

   Do NOT comment on completeness, narrative arc, or strategic soundness — that's the quality reviewer's job.
   Stay narrowly on fact verification. Cost-aware mode (sonnet): table-only output. Limit to ~30 most material claims.

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
   - **`qa_level == quick` short-circuit**: do NOT invoke refine-doc. Memos remain in the strategy as audit trail (no edits applied). Log to pipeline_summary Decision Points: `Step 3 | strategy refine skipped (qa=quick) | auto | proceed to Step 4`. Skip to Step 4.
   - **`--user-refine` pause**: if the flag is set, update `pipeline_state.yaml` (`user_refine: true`, `paused_at_stage: strategy-refine`), print the resume command (`/autopilot-doc --mode {mode} --from strategy-refine {strategy_folder}`), and exit. Do NOT invoke refine-doc.
   - Otherwise: invoke Skill `refine-doc` with the Korean strategy path as args.
4. If no memos: Skip to Step 4. (When resumed via `--from strategy-refine`, the orchestrator skips the 연구팀 review and runs refine-doc directly using the pre-existing memos.)

### Step 4: Draft Generation
**Applicable modes**: rebuttal, paper, report, proposal, review, presentation. (All 6 modes generate drafts.)

#### Step 4.0a: Multi-source Figure Discovery

Draft 생성 전, figure_index.md 또는 figure asset이 있을 수 있는 _세 source_를 순차 검색:

1. **Source 1 — research figures**: `.claude_reports/research/*/figures/figure_index.md` glob (top match by topic relevance to task description).
2. **Source 2 — analysis_project paper figures**: `.claude_reports/analysis_project/paper/figures/figure_index.md` (analyze-project --mode paper에서 figure extraction이 함께 수행된 경우 존재).
3. **Source 3 — artifact self figures**: `{artifact_dir}/assets/figures/figure_index.md` 또는 단순히 `{artifact_dir}/assets/figures/*.png` (사용자 직접 추출·생성).

발견된 모든 source의 figure_index를 merge → paper_id × figure path 매핑 dict 생성. 중복은 source 1 > 2 > 3 우선 (research가 가장 신뢰).

#### Step 4.0b: On-demand Figure Extraction (figure_index 부재 시)

세 source 모두 figure_index.md가 없거나 figure assets이 비어 있으면, draft orchestrator가 _자체적으로_ figure extraction 시도:

1. **Source paper PDFs 위치 확인**:
   - `.claude_reports/analysis_project/paper/cards/*.md`에서 `**PDF 위치**` 또는 `**arXiv ID**` field grep
   - `.claude_reports/research/*/cards/*.md`에서 동일 field grep
   - 발견된 PDF paths를 input set으로 수집
2. **PDF input set이 비어 있지 않으면 → 탐색팀 호출**:
   ```
   Agent(subagent_type="탐색팀",
         description="PDF figure/table extraction for doc",
         prompt="extract_pdf_figures mode. Input PDFs: {pdf_paths}.
                 Output: .claude_reports/analysis_project/paper/figures/ (또는 적합한 공용 위치).
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
- artifact_dir: `.claude_reports/documents/{date}_{name}/`
- 세 source 별 path:
  - **Source 1 (research)**: `.claude_reports/research/{topic}/figures/` → draft 기준 `../../../research/{topic}/figures/{file}.png` (3단 위)
  - **Source 2 (analysis_project paper)**: `.claude_reports/analysis_project/paper/figures/` → draft 기준 `../../../analysis_project/paper/figures/{file}.png` (3단 위)
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

Save English draft to: {strategy_folder}/draft/draft.md

**Do NOT write `draft_ko.md` yourself.** The Korean mirror is produced by the **번역팀** (translation-team) agent in a follow-up step (Step 4-KO below). 연구팀 only writes English here — splitting Korean off to a dedicated translator is what prevents 판교체 leaking into the user-facing artifact.

Read the strategy document and all analysis files. Generate a complete first draft following the mode-specific structure below. The draft should be a working document ready for user editing — not a summary of the strategy.

## Tone Propagation (modes: report / proposal / presentation)

**FIRST**, read the strategy frontmatter `tone` field:
- If `tone: administrative` — apply administrative-tone constraints to the **entire draft** (slide titles, bullets, conclusion, visual placeholders). Specifically:
  - **AVOID**: marketing superlatives ("genuinely novel", "sole occupied axis", "global rights asset", "world-first", "compelling contribution"), "X strengths summary" framing, "core message" + "Hook → Call-to-Action" arc, heroic asks ("Approve to secure as global asset"), decision-options box (approve/conditional/hold), animated narrative voice
  - **PREFER**: simple fact lists, status updates, neutral reporter stance, calm review request ("검토 부탁드립니다" / "kindly request the committee's review")
  - Conclusion slide: replace "Key messages + Call-to-Action" with **"Presentation summary + review request"**; remove "X strengths" enumeration in favor of plain fact recap
  - Speaker stance: **neutral reporter, not advocate**. The speaker (often a student or researcher) is reporting upward to decision-makers, not pitching to peers
- If `tone: default` or absent — existing pitch-deck patterns apply (Hook, Core Message, Story Arc, Call-to-Action, persuasive framing)

This propagation is mandatory: a `tone: administrative` strategy with a heroic-pitch draft is a critical mismatch and must be reworked.

## Mode-Specific Draft Structure

### rebuttal
- Frontmatter: type, venue, status: draft, date
- Per-reviewer response sections following the strategy's priority matrix
- Each response: acknowledgment → core argument → evidence → conclusion
- Tone calibrated per the strategy's tone guidelines
- Additional experiments section with preliminary descriptions
- Revision summary table

### paper
- Frontmatter: type, venue, status: draft, date
- Full paper outline with section drafts:
  - Abstract (structured: background → gap → method → results → impact)
  - Introduction (hook → context → gap → contribution → outline)
  - Related Work (organized by strategy's framing)
  - Method (following strategy's outline, with placeholder equations)
  - Experiments (setup → results → ablation, with table skeletons)
  - Conclusion
- Figure/table placeholders with captions

**Camera-ready / major-revision specific — Natural-integration rule for paper-body mutations** (cross-ref: `init-doc-strategy/SKILL.md` paper mode "Natural-integration rule" — single source of truth):

> When converting **reviewer concerns / rebuttal materials → paper-body mutation paste-ready blocks**, ask one question per mutation: *"Can this be naturally integrated as a 1-2 sentence inline rewrite that flows with the surrounding paragraphs?"*
> - **YES → inline rewrite mutation** (good: subsection-head opening + body-paragraph touch-up + Figure cascade reference; experimental numbers stay in body / Appendix, not in opening/intro)
> - **NO → drop / Appendix defer** (rebuttal-format artifacts — model-by-model comparison tables, structured Q&A blocks, point-by-point response paragraphs — do NOT belong as paper-body mutations even if reviewer "strongly recommended integration"; pasting verbatim reads as rebuttal-style out-of-flow content)

**Hard-fail rejection signals** — refuse to write a mutation entry if its paste-ready block is (a) a standalone `\begin{table}` / `\begin{itemize}` sourced from rebuttal, (b) injecting experimental numbers verbatim into an opening / framing paragraph, or (c) a new `\paragraph{...}` INSERT that the existing surrounding text doesn't bridge to.

**Why**: established 2026-05-19 after a camera-ready cycle that mechanically converted every reviewer concern into 🔴 mandatory body mutations (including rebuttal-format comparison tables). User-rejected pattern: "rebuttal자료를 본문에 그대로 가져다 붙이지 말고 자연스럽게 문장으로 녹여 넣어라."

#### Paste-ready cheatsheet 형식 강제 (paper mode camera-ready / paste-ready subtype)

> **언제 적용되는가**: paper mode 의 산출물이 _연속 본문 paragraph 가 아니라 사용자가 LaTeX 에 직접 paste 하는 _카드 묶음__ 일 때 (camera-ready / major revision / `subtype: camera-ready-paste-ready` 같은 frontmatter). 즉 사용자가 _preview 로 보면서_ 카드 단위로 paste 작업하는 산출물.

본 형식은 **사용자가 preview 에서 보는 것** 과 **에이전트 추적용 메타** 를 _명확히 분리_ 한다. 사용자가 한 사이클에 한 번 보면 끝나는 정보가 매 entry 옆에 박혀 있으면 preview 가 줄글로 깨지고 paste 자리를 찾기 어려워진다. 사용자 불만 (2026-05-21): _"preview 에서 그냥 쭉 줄글로 깨진다 — 형식 자체 문제다"_.

**1. Frontmatter 는 최소만**

`draft.md` / `draft_ko.md` 의 frontmatter 에는 **사용자에게 의미 있는 필드만**:
- `type`, `venue`, `paper_id`, `status`, `date`, `baseline` (LaTeX 파일 경로)

**금지 (추적용은 별도 파일로)**:
- `changelog:` 배열 → `_internal/draft_meta.yaml` 또는 `pipeline_summary.md` 으로 격리
- `mutation_count`, `intentional_id_gaps`, `predecessor`, `strategy_ref`, `qa_level`, `subtype`, `scope` 같은 추적용 → 같은 격리 파일로
- frontmatter 안 긴 `note` 줄 (변경 이력) → frontmatter 밖 평문으로 또는 격리 파일로

이유: YAML frontmatter 가 길면 preview 에서 줄글로 깨져 사용자가 본문 첫 줄까지 도달하는 데 한 화면을 소비한다.

**2. 본문 맨 앞 안내 blockquote 최대 1개, 한 줄**

`> **Legend**: ...` 같이 한 번 보면 끝나는 안내는 _하나_ 만, _한 줄_ 로. "사용 방식" / "Strategy details" / "Wording invariants" / "Preserve note" 같은 추가 안내 blockquote 는 박지 않는다 — 사이클이 끝나면 의미 없는 메타.

**3. 각 entry 는 _카드 단위_**

한 entry 의 골격:

```markdown
### {ID} {tier 이모지} — {짧은 한 줄 action}

**위치**: `\section{...}` 또는 `\label{...}` 또는 `\paragraph{...}` (한 줄, inline code 활용)

​```latex
% paste-ready 블록
...
​```

**한 줄 이유** (선택): 왜 이 자리에 이게 필요한지 한 문장. 두 줄 넘어가면 cut.
```

- H3 헤더 한 줄
- `**위치**:` 한 줄 — `**Anchor**` / `**latex anchor**` 같은 영어 라벨 금지, `**위치**:` 통일
- LaTeX 블록 한 개 (필요 시 함께 paste 할 짧은 블록 하나 더)
- `**한 줄 이유**` 선택, 두 줄 이내

**4. entry 안 절대 박지 않는 것**

- Reviewer 매핑 (`Reviewer: cytr-W3`) → `_internal/draft_meta.md`
- dependency 표 / cross-ref dependency 표 → `_internal/draft_meta.md`
- Wording invariant 안내 / Style Guide 인용 → 본문 맨 앞에 한 줄 또는 격리 파일
- Verification gate / column count 안내 → 본문 끝의 _마무리 확인 목록_ 안 한 줄로 통합
- inline `<!-- memo: [REFINE-R2] F{N} applied: ... -->` 표시 → 본문에 절대 박지 않음. refine 추적은 `pipeline_summary.md` `## 마이너 변경 로그` 안에만.

**5. paste 순서는 본문 끝에 단순 ordered list**

- 표 (`| 단계 | mutation | 위치 |`) 가 아니라 ordered list (`1. M34: ...` / `2. M37 Step 1: ...`)
- 각 단계는 한 줄 — mutation ID + 한 줄짜리 action. 의존성은 본문 entry 안 `**위치**:` 옆에 inline 으로 한 줄 (`함께 paste: M{X}`) — 별도 표 X.

**6. 사용자 결정 분기점은 _발생 entry 안 한 줄_**

Pre-flight 표 / 분기점 표로 앞 페이지에 7행 표 박지 않는다. M2 위치 분기는 M2 entry 안에 한 줄 (`> 위치 선택: (a) §1 끝 / (b) §Acknowledgements 옆 — spec 기준 (a) 권장`), M27-Step3 BibTeX 부재 분기는 M27 entry 안에 한 줄. _발생 자리에서 한 번_.

**7. body audit 진단표는 한 번 보고 끝 — 본문에 박지 않음**

본문 적용 현황 (`§A Applied 16건 / Intentional 5건 / 잔존 2건`) 표 는 사용자가 _작업 시작 전 한 번_ 보고 끝나는 reference. 본문 카드 흐름 안에 박지 말고 `_internal/body_audit.md` 또는 `analysis/` 안 별도 파일로. 본문에는 한 줄 link 만 (`> 본문 적용 현황: [audit.md](./audit.md) 참조`).

**8. 마무리 확인 목록은 본문 맨 끝 한 묶음**

`§F final verification checklist` 는 한 곳에. 각 entry 마다 verification gate 박지 않고 마지막에 한 번에 모음.

**9. 추적 정보는 `_internal/draft_meta.md` 으로 격리**

사이클 중 추적용 메타:
- 변경 이력 (changelog 배열 본문)
- mutation 별 Reviewer 매핑 + dependency 표 + Wording note
- inline refine marker (`[REFINE-R2] F{N} applied`)
- mutation_count / tier 통계

이 모두 `_internal/draft_meta.md` 안. 사용자 영역 (`draft.md` / `draft_ko.md`) 에는 절대 안 박는다.

**Hard-fail 추가** — 사용자 영역 draft 본문에 다음이 등장하면 즉시 거부 + 재작성:
- frontmatter 줄 수 > 7 (필수 6 필드 + `---` 두 줄)
- 본문 맨 앞 안내 blockquote 2 개 이상
- 한 entry 안 markdown 표 (paste-ready LaTeX 안의 `\begin{tabular}` 는 OK — markdown `|...|` 표 만 hard-fail)
- 본문 안 inline `<!-- memo: ... -->` marker 등장
- ordered list 아니라 _표 형태_ 의 paste 순서 안내

**Why**: 사용자가 preview 로 보면서 paste 작업한다. preview 에서는 frontmatter / blockquote / 메타 표 가 줄글로 깨져 _paste 자리를 찾기 어렵다_. 사용자 영역과 추적 영역이 같은 위계로 섞이면 매번 사용자가 "이게 내가 봐야 할 건가, 에이전트 추적용인가" 분간해야 한다 — 짜증의 직접 원인.

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

### review
Adapt the section structure to the auto-discovered format spec at `{format_ref}` (read it first). No built-in presets — extract the venue's required sections / rating axes / length limits from the format spec file.

**Frontmatter** (always): type, venue, paper_title, status: draft, date, format_ref (path to auto-discovered format spec)

**Procedure**:

1. Read the format spec at `{format_ref}` first. Extract: required sections, rating axes (with score scales 1-N and meanings), length limits, tone/style guidelines, submission portal layout.
2. If the format spec is a venue's reviewer guidelines PDF/doc, prefer its exact section names verbatim. If it's a sample review, infer the structure.
3. Layer any additional reviewer guidelines from siblings in `analysis_project/doc/{matching}/formats/` on top.
4. Produce a draft that satisfies every required section from the format spec.

**Common patterns** (reference only — the actual structure must come from the format spec, not from these):

- _OpenReview-family_ (NeurIPS, ICML, ICLR, AAAI variants): Summary / Strengths / Weaknesses / numeric ratings (Soundness, Presentation, Significance, Originality on 1-4 or 1-5) / Questions / Limitations / Overall Recommendation + Confidence
- _ACL ARR_: Paper Summary / Strengths / Weaknesses / Comments+Typos / Soundness, Excitement, Reproducibility (1-5) / Ethical Concerns
- _IEEE conference_ (ICASSP, INTERSPEECH): Brief Summary / Strengths / Weaknesses / Detailed Comments / Recommendation (Accept/Reject scale) / Confidence
- _Journal_ (T-ASLP, JASA, TPAMI, etc.): Significance / Technical Quality / Clarity / Recommendation (Accept/Minor Revision/Major Revision/Reject) / Per-section comments

These are starting hints only. Always follow the format spec file's actual specification — venue templates change year-to-year.

### presentation
Generate a **PPT cheatsheet markdown** — single file, optimized for human reading and slide-by-slide copy/paste into PowerPoint. **NOT a pandoc conversion target**. Avoid pandoc-specific syntax (`::: notes`, `:::: {.columns}`, YAML frontmatter for auto-title generation).

> **Figure & Tone conventions (MANDATORY)**: see [`PRESENTATION_FIGURE_CONVENTIONS.md`](./PRESENTATION_FIGURE_CONVENTIONS.md) — figure 안 텍스트 최소화 / spectrogram per-signal 정규화 / 50 ms RMS / 청중 친화 단위 (dBFS / 배수) / 기존 deck 톤 분석 (python-pptx) / asset 게으르게 활용 금지 / 상대 경로 / 한국어 폰트 / draft 전 plot 검토. cheatsheet variant (기존 PPT 본문 일부 보강) 에서 특히 강제.

**Slide Format Conventions** (mandatory — derived from user feedback to prevent revision loops):

1. **Chapter visualization in slide headers** — every body slide's heading: `## Slide N — [Ch.N 챕터명] (sub.번호) 슬라이드 제목`. Chapter-transition slides marked with `— 시작` / `— start`. Each slide has a `**챕터**: N. 챕터명 (M장 중 K번째)` meta line below the title.

2. **Visual placeholder must include chapter band** — every body slide's `**시각자료**:` block first line: `- **상단 헤더 띠**: "N. 챕터명"` (per Korean industry-academia format spec). Chapter-transition slides additionally specify "Ch.X와 색상/strength를 다르게 — 챕터 전환 시각 신호".

3. **Concrete visual placeholders** — NO vague terms like "X 카드", "적절한 도식", "comparison chart". Every visual specifies (a) diagram type + (b) component list + (c) layout/color hints. Example: ❌ "학회 위상 카드" → ✅ "NeurIPS/ICLR/ICML 3-row table (h5-index 컬럼 + acceptance-rate 컬럼)".

4. **Table column header clarity** — NO ambiguous headers like "비교 1위" or "vs ours". Use full noun phrases with clear semantic units. If needed, add a 1-line column-meaning footnote above the table.

5. **Foreign-language quote → Korean keyword gloss** (mandatory for non-AI audiences) — every English quote (paper review citation, technical term, model description) gets a Korean appeal-commentary box directly below:
   ```
   > "English quote..."
   > — Source

   📌 **핵심 키워드 — "X"**: 한국어 풀이 1문장 (청중 친화 어필 메시지)
   ```

6. **Speaker notes default = empty** — do NOT auto-fill speaker notes in the initial draft. Wait for explicit user request as a separate post-polish step. Reason: speaker notes drift with slide-content edits; auto-fill wastes regeneration cost during iterative refinement.

7. **No body-bullet ↔ visual redundancy** — the same fact should NOT appear in both body bullets AND visual placeholder. Body bullets = "what the speaker says"; visual = "what the audience sees at-a-glance". If redundant, simplify one of the two.

8. **Slide-number consistency on insertion/deletion** — when inserting/removing/renumbering a slide, update ALL of the following in the same edit pass:
   - (a) All subsequent slide numbers (`Slide N+1`, `Slide N+2`, ...)
   - (b) Contents slide's chapter slide-counts ("Ch.N (M장)")
   - (c) Changelog entry inside the frontmatter `changelog:` array (per `refine-doc` convention — never a top-of-file HTML comment, which breaks markdown preview when frontmatter is present)
   - (d) Time-budget line in the top-of-file guide
   - (e) Cross-references in other slides ("Slide M의 ...")
   - (f) Chapter meta lines ("M장 중 K번째")

**Top-of-file guide** (mandatory header before any slides):

```markdown
# {발표 제목} — Seminar Slide Deck

> **사용 가이드**: 본 markdown은 PPT 복사·붙여넣기용 단일 파일이다. 각 슬라이드는 `---`로 분리되어 있으며, 슬라이드 번호·제목·bullet·시각자료·Speaker note 순서로 구성된다.
>
> - **총 슬라이드 수**: **N main + M backup = total**
> - **시간 분배 ({X}분 기준)**: Opening / Ch.0 / Ch.1 / ... 분 단위 명시
> - **청중 baseline**: 한 줄로 청중 특성과 작성 톤 (약어 풀어쓰기 / 직관 비유 / 수식 최소 등)
> - **설계 의도**: 챕터 구성·narrative arc 한 단락
```

**슬라이드 단위 형식** (모든 main + backup 슬라이드):

```markdown
---

## Slide N — {짧은 슬라이드 제목}

**제목**: {실제 슬라이드에 들어갈 제목 문구 (한국어 또는 본인이 쓰는 발표 언어)}

**부제** (선택): {부제 문구 — 첫 슬라이드 또는 챕터 디바이더에 한정}

- 본문 bullet 1 (개념/이름/수치 위주, 간결하게)
- 본문 bullet 2
- 본문 bullet 3 (보통 3-5개)

| 표가 더 적합한 경우 | 이렇게 markdown 표 |
|---|---|
| 모델 A | 수치 |
| 모델 B | 수치 |

**시각자료**:
- 좌측 1/2 (또는 메인): {도식·차트 설명}
- 우측 1/2 (또는 보조): {보조 시각}
- 또는 전체 화면: {풀 페이지 도식 설명}

<!-- 자동 figure embed (Step 4.0a/4.0b 결과 figure_index.md 매핑이 있는 슬라이드만) -->
<!-- Source 1 (research): <img src="../../../research/{topic}/figures/{paper_id}_fig{N}.png" alt="..." width="500" /> -->
<!-- Source 2 (analysis paper): <img src="../../../analysis_project/paper/figures/{paper_id}_fig{N}.png" alt="..." width="500" /> -->
<!-- Source 3 (artifact self): <img src="../assets/figures/slideXX_*.png" alt="..." width="500" /> -->
<!-- 작은 크기 (width=500) 미리보기 수준; 사용자 메모리 정책 — feedback_figure_combined_pptx_only.md 참조 -->
<!-- Path은 draft 위치 기준 자동 계산 (Step 4.0c Path Convention) — 사용자 수동 X -->
{자동 embed: 사용 가능 figure 목록 (figure_index.md 매핑) 중 본 슬라이드 토픽과 매치되는 figure가 있으면 inline `<img width="500" />` syntax로 자동 embed. 자동 매핑이 모호하면 placeholder만 두고 사용자 polish 영역으로 표시.}

**Speaker note**:
1. {발화 1 — 슬라이드 본문 보충, 직관 풀이, 비유, 일화}
2. {발화 2 — 다음 슬라이드/챕터로 가는 transition}
3. {발화 3 — 청중 질문 예상 시 짧은 답변 메모, 선택}

**Citation** (선택): [Author Year, Venue](cards/{file}.md) — 정확한 paper card를 가리키는 인라인 링크
```

**구조 요건**:
- **표지** (Slide 1) — 제목 + 부제 + 발표자/소속 + 날짜 + 발표 자료 출처 한 줄
- **목차** (Slide 2) — 챕터별 슬라이드 수와 한 줄 설명
- **챕터 디바이더** — `## Slide N — Ch.X 제목` 형식. 슬라이드 본문은 챕터 의도/시기 한두 줄. 별도 슬라이드 카운트에 포함.
- **본문 슬라이드** — 위 슬라이드 단위 형식
- **챕터 마무리** (선택) — Ch.X 정리 + Ch.X+1 transition. 인지 부담 분산용
- **Conclusion** — Take-home 5 / Open Problems / 한 페이지 요약 / Q&A / Thank you
- **Backup** — `## Slide BN — Backup: 제목` 형식. 메인 흐름 끝난 뒤 배치
- **References** (선택) — 마지막에 핵심 인용 정리

**작성 톤**:
- 본문 bullet은 *키워드 + 수치 + 모델명* 위주. 풀 문장 지양 (그건 speaker note에).
- 약어는 첫 등장 시 풀어쓰기: `Speech Enhancement (SE)`, `NFE (Number of Function Evaluations)` 등.
- Citation은 paper card markdown 링크로 (`[Author Year](../../research/{topic}/cards/{file}.md)` 또는 같은 artifact_dir 내 cards/).

**Quality**:
- 모든 본문 슬라이드에 **Speaker note 필수** (≥80% — 기술 비중 낮은 표지·인사 슬라이드 제외).
- 모든 슬라이드에 시각자료 placeholder (텍스트만으로 끝나는 슬라이드는 cheatsheet로서 약함).
- 시각자료 설명은 *PPT에서 그릴 수 있을 만큼 구체적*으로 (예: "5-stage timeline 가로 막대, 색상 5개" 같은 수준).
- Strategy doc의 슬라이드 outline을 그대로 매핑 (총 슬라이드 수와 챕터 시간 분배 일치).

## Quality Requirements
- **Style Guide compliance**: every claim, citation, figure caption, bullet, and speaker note must match the `## Style Guide` section in `strategy.md`. Style Guide is _the_ authoritative format spec for this artifact — not your generic markdown habits.
- Every claim must trace back to a specific reference in the refs folder or analysis.
- Do NOT fabricate citations, data, or results.
- Mark uncertain or placeholder content with `[TODO: ...]`.
- **Mode-specific completeness criteria**:
  - **rebuttal**: 90%+ — every reviewer point MUST have a drafted response (hard constraint). Missing a point is a critical error.
  - **paper/report/proposal**: 70-80% — all sections with substantive content, no heading-only sections.
  - **review**: 80%+ — every required section per the auto-discovered format spec must be filled with concrete claims. Strengths/weaknesses must reference specific paper sections/figures/tables. Score justifications are mandatory.
  - **presentation**: 70-80% — every slide has 제목/부제(선택)/bullets/시각자료/Speaker note 5개 슬롯이 채워짐 (시각자료가 텍스트만 있는 슬라이드에 빠지면 cheatsheet 가치 손상). Speaker notes ≥80% of content slides. 슬라이드 카운트는 strategy outline과 ±10% 이내. `---` 구분자가 모든 슬라이드 사이에 있는지 확인.

Write **only** the English draft. Return ONLY the file path and a 3-5 line Korean summary.
```

3. **IMPORTANT**: Do NOT read, re-write, or duplicate the draft file yourself. The agent writes it directly.

#### Step 4-KO: Korean draft generation (번역팀)

After 연구팀 finishes the English draft, invoke the **번역팀** (translation-team) agent. 번역팀 owns Korean readability and is the only path to `draft_ko.md`.

```
모드 A — 영문에서 국문으로 옮기기.
영문 draft 경로: {strategy_folder}/draft/draft.md
국문 출력 경로: {strategy_folder}/draft/draft_ko.md
~/.claude/agents/translation-team.md 의 모드 A 절차를 따른다.
~/.claude/projects/*/memory/feedback_korean_readability_policy.md 의 판교체 회피 원칙을 강제 적용.
모드별 영어 유지 어휘 ({mode} 에 맞게):
- paper/rebuttal/review: LaTeX 명령·논문 제목·저자·학회·약자·모델·데이터셋·지표는 영어 그대로
- report/proposal: 회사·기관·프로젝트·기술 용어는 영어 그대로
- presentation: 슬라이드의 본문 영어 인용·LaTeX·모델·논문 제목은 영어 그대로
한 문서 안에서 같은 개념은 같은 표기로 통일.
완료 시 파일 경로 + 한국어 요약 3-5 줄 + 의도적으로 한 표기 결정 한두 개만 돌려준다.
```

### Step 4b — Post-draft factual detector (orchestrator-side, all modes)

**Always runs** — even at `--qa quick` or `--qa light`. Orchestrator executes directly (no sub-agent). Cost is small: regex + cards grep only.

1. **Run detector**: apply regex + cards lookup + section-context cross-check to `{strategy_folder}/draft/draft.md` and `{strategy_folder}/draft/draft_ko.md`.
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

### Step 5: Draft Review (연구팀 as QA)
**Applicable modes**: rebuttal, paper, report, proposal, review, presentation. (All 6 modes that generated drafts.)

1. Resolve draft paths:
   - `en_draft_path` = `{strategy_folder}/draft/draft.md`
   - `ko_draft_path` = `{strategy_folder}/draft/draft_ko.md`

2. Invoke reviewers based on `--qa` level (same scaling as Step 3). **Quality reviewer(s) and fact-checker run in parallel** at standard+:

   **`quick`** — Single 연구팀 quality reviewer (sonnet, spot-check only):
   - One-pass review. Memos may be added but refine-doc is NOT invoked at Step 5 (see step 3 below).
   - Review log: `{strategy_folder}/_internal/draft_reviews/draft_review.md`

   **`light`** — Single 연구팀 quality reviewer (sonnet):
   - One-pass review focusing on critical issues only.
   - Review log: `{strategy_folder}/_internal/draft_reviews/draft_review.md`

   **`standard`** — 1× 연구팀 quality reviewer (opus) + 1× 연구팀 fact-checker (sonnet, parallel):
   - Quality review log: `{strategy_folder}/_internal/draft_reviews/draft_review_quality.md`
   - Fact-check log: `{strategy_folder}/_internal/draft_reviews/draft_review_factcheck.md`

   **`thorough`** — **axis-decomposed parallel 연구팀** (audit-aligned axes 각각 별도 instance) + 1× 연구팀 fact-checker:
   - **Axis A — Content / Strategy coverage** (opus): strategy 본문이 draft에 모두 반영됐는지, factual coherence, rebuttal mode면 모든 reviewer point에 응답 있는지.
     - Review log: `{strategy_folder}/_internal/draft_reviews/draft_review_content.md`
   - **Axis B — Writing quality** (opus): 논리 flow, 완전성, 약한 주장 / [TODO] 잔존 등.
     - Review log: `{strategy_folder}/_internal/draft_reviews/draft_review_quality.md`
   - **Axis C — Style Guide compliance** (sonnet): strategy의 `## Style Guide` rule을 draft가 _모든_ citation / figure caption / bullet depth / speaker note에서 따랐는지. 일관성 일탈 (`IS 2024` vs `Interspeech 2024` 혼용 같은 것) 식별.
     - Review log: `{strategy_folder}/_internal/draft_reviews/draft_review_style.md`
   - **Axis D — Cross-ref + Coverage** (sonnet): draft 안 `cards/{file}.md` link target 존재 + analysis/refs에 있으나 draft에 인용 안 된 orphan card 식별 (omission detection — UniSE-class 누락 방지).
     - Review log: `{strategy_folder}/_internal/draft_reviews/draft_review_coverage.md`
   - **Fact-checker** (sonnet): citation/venue/year/metric/lineage verbatim 대조 (cards/PDFs).
     - Review log: `{strategy_folder}/_internal/draft_reviews/draft_review_factcheck.md`
   - 모든 reviewer가 KO draft에 `<!-- memo: ... -->` 작성. 각자 `[axis name]` prefix 명시 (예: `[STYLE]`, `[COVERAGE]`, `[FACT]`).
   - 5 instance 완료 후 메모 merge + 중복 제거.

   _이 axis decomposition은 "user-catchable points 전부 연구팀이 대신"의 multi-axis 구현. 예: presentation mode 자료에서 사용자가 거슬려할 출처 표기 일관성·orphan 카드 누락·잘못된 모델 분류 모두 별도 axis instance가 책임._

   **Quality reviewer prompt** (light/standard에서 단일 instance가 모든 axes 다룰 때):
   ```
   Review this document draft as the user's domain expert proxy.
   **Task type: paper-driven doc** (mode: {mode}) — apply Role 1 Step 3 axes from agents/research-team.md, audit-aspect aligned.

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

   **Fact-checker prompt** (sonnet, parallel — standard/thorough only):
   ```
   You are a fact-check focused reviewer — NOT narrative quality.
   Mode: {mode} | KO draft: {ko_draft_path} | Discovered inputs: {discovered_inputs} | Log: {fact_log_path}

   For every domain claim in the draft (citation / model name / venue / year /
   metric / dataset / lineage / classification), open the corresponding ground-truth
   source and verbatim compare:
   - Paper analyses: `.claude_reports/analysis_project/paper/*.md` (if exists — single source of truth, produced by `/analyze-project --mode paper`)
   - Original PDFs: only if listed in {discovered_inputs} AND paper analyses lack the specific fact
   - Strategy: {en_strategy_path} — **DO NOT use as primary source**. Strategy must itself be verified against paper analyses. Using strategy as ground truth = circular reference (forbidden).

   Do NOT comment on writing quality, narrative arc, or strategy coverage — that's the quality reviewer's job.
   Stay narrowly on fact verification. Cost-aware mode (sonnet): table-only output. Limit to ~30 most material claims.

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
   - **`qa_level == quick` short-circuit**: do NOT invoke refine-doc. Memos remain in the draft as audit trail (no edits applied). Log to pipeline_summary Decision Points: `Step 5 | draft refine skipped (qa=quick) | auto | proceed to Step 6`. Skip to Step 6.
   - **`--user-refine` pause**: if the flag is set, update `pipeline_state.yaml` (`user_refine: true`, `paused_at_stage: draft-refine`), print the resume command (`/autopilot-doc --mode {mode} --from draft-refine {strategy_folder}`), and exit. Do NOT invoke refine-doc.
   - Otherwise: invoke Skill `refine-doc` with the Korean draft path as args.
   - Note: refine-doc handles draft paths (draft/draft.md ↔ draft/draft_ko.md) via auto-detection.
4. If no memos: Skip to Step 6. (When resumed via `--from draft-refine`, run refine-doc directly on the pre-existing memos.)

### Step 6: Pipeline Summary
**Always write** `{strategy_folder}/pipeline_summary.md` before reporting to the user.

```markdown
# Document Strategy Pipeline Summary: {task name}

- **Date**: {YYYY-MM-DD} | **Mode**: {mode} | **Format-ref**: {format_ref or "fallback-generic"} ({format_ref_source}) | **Status**: done / reviewed / draft
- **User-Refine**: {true | false}
- **Discovered inputs**: {discovered_inputs}

## Process Log
| Step | Action | Result | Notes |
|---|---|---|---|
| 0 | Scope Clarification | clarified / skipped | {questions asked or "--no-clarify"} |
| 1 | Material Analysis | completed | {N} files |
| 2 | init-doc-strategy | created | {strategy path} |
| 3 | Strategy Review (연구팀) | memos added / no issues | {memo count} |
| 3b | refine-doc | refined / skipped | |
| 4 | Draft Generation | created | {draft path} |
| 5 | Draft Review (연구팀) | memos added / no issues | {memo count} |
| 5b | refine-doc (draft) | refined / skipped | |

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
- For review mode: confirm the format spec file used (auto-discovered from `analysis_project/doc/{matching}/formats/`). No built-in presets.

## Safety Rules
- Do NOT fabricate citations or invent results — only reference materials actually present in `{discovered_inputs}`.
- The draft is a working first draft for user editing, NOT a final document. Mark uncertain content with `[TODO: ...]`.
- For rebuttal mode: ensure EVERY reviewer point is addressed — missing a point is a critical error.
- For review mode: scores must be justified with concrete evidence; never fabricate scores without backing in the paper text. An auto-discovered format spec in `analysis_project/doc/{matching}/formats/` is mandatory — pre-flight aborts otherwise.
- For rebuttal mode: rebuttal sub-type (meta-only / reviewer-dialogue / response-with-revision) must be derivable from format spec content OR task description by Step 1. Strategy and tone differ across sub-types — if neither source provides it, Step 0 prompt asks the user to declare.
- For all other modes: format spec is optional but improves quality significantly when supplied. The agent should note the format spec source in the strategy frontmatter so future refine-doc rounds know what to honor.
- For presentation mode: never insert real figures/images automatically — describe visuals in the `**시각자료**:` block with concrete-enough wording (e.g., "5-stage timeline 가로 막대, 색상 5개"). PPTX export is NOT performed by this pipeline; the user reads the cheatsheet markdown and creates slides manually in PowerPoint with their lab template.
- Present material inventory to the user briefly and auto-proceed.

## Task
$ARGUMENTS
