## Argument Parsing
Parse `$ARGUMENTS` for mode, flags, and task description:

**`--mode` (optional, auto-inferred from query)** — _form-first_. 3 modes by output form:

- `paper` — **LaTeX 학술 산출물 = paste-ready cheatsheet draft**. 'draft' 는 _백지 본문 작성_ 이 아니라 **cheatsheet (사용자가 LaTeX 에 직접 paste 하는 카드 묶음 = mutation/edit plan) 의 초안**. 논문이 신규든 이미 완성됐든 _경우와 무관하게_ 산출물은 cheatsheet draft 이며, `autopilot-apply` 가 `main.tex` 에 paste·적용한다. 형식 강제는 `conventions/paper.md` 의 _Paste-ready cheatsheet 형식 강제_.
  - 신규 submission / thesis / book chapter: 새 본문 블록을 cheatsheet entry 로 산출.
  - **camera-ready / major revision (default)**: 기존 완성 본문에 적용할 수정 cheatsheet entry 로 산출 — 본문 통합·anchor 정책·natural-integration rule 강제.
- `presentation` — **PPT 용 slide-by-slide markdown**. 학회 발표 / 세미나 / 강의 / cheatsheet variant. PPTX export NOT supported — PowerPoint 수동 변환. 16:9 슬라이드 분량 강제.
- `doc` — **Word/HWP/markdown prose**. 기술 보고서 / 분기 보고 / mid-report / post-mortem / grant proposal / rebuttal 응답 form / peer review 작성 / tech blog / institutional memo 등. audience-driven 톤·시제·절 구조 가변.

> **Purpose / genre 는 자연어로 task description 에 명시** — `--subtype` enum 없음. 예시 호출:
> - `/autopilot-draft "ICML 2026 camera-ready cheatsheet" --mode paper` → paper mode + paste-ready cheatsheet 의도 자연어로 전달
> - `/autopilot-draft "DSC 데이터셋 mid-report" --mode doc` → doc mode + mid-report 시제·구조 자연어로
> - `/autopilot-draft "OpenReview 응답 작성, reviewer cytr·95wX 응답" --mode doc` → doc mode + rebuttal-response 의도

**Auto-inference** (mode 미지정 시):
- "발표·세미나·슬라이드·presentation·PPT·deck" → `presentation`
- "논문·paper·camera-ready·revision·LaTeX·thesis·book chapter" → `paper`
- "보고서·기술 분석·report·제안서·proposal·grant·rebuttal·리뷰 응답·OpenReview 응답·peer review·블로그·메모" → `doc`
- 그 외 / 명시적이지 않으면 → `doc` (가장 일반적 form)
- 추론 결과를 한 줄로 사용자에게 통보 후 진행. 모호하면 Step 0 Scope Clarification에서 확인.

> **Note**: `survey` mode is removed. For 학술/산업/시장 조사, use `/autopilot-research --mode academic|technology|market` first → autopilot-draft은 `research/{topic}/` artifact를 implicit으로 자동 발견.

**Input Discovery (implicit)** — 입력은 `<artifact-root>/` 하위 영속 산출물에서 자동 발견:

- **`analysis_project/paper/`** — 보유 논문 분석 (autopilot-draft의 모든 모드에서 활용 가능)
- **`analysis_project/doc/{matching}/`** — doc-creation 자료 (reviewer comments, format templates, samples). `{matching}`은 task description 키워드와 fuzzy match.
- **`research/{topic}/`** — 외부 분야 조사 (autopilot-research가 만든 artifact). 마찬가지로 fuzzy match.
- **`analysis_project/code/`** — 코드 컨텍스트 (doc mode 의 report·proposal·tech blog 등에서 종종 인용)

mode별 _필수·권장_ 입력:

| mode | 필수 input | 권장 input |
|---|---|---|
| `paper` | (없음) | `analysis_project/paper/` (자기 paper / 인용 paper), `analysis_project/doc/{matching}/formats/` (venue LaTeX template), `research/{topic}/` (분야 컨텍스트) |
| `presentation` | (없음) | `analysis_project/doc/{matching}/formats/` (lab/venue slide template), `analysis_project/paper/` (발표 대상 paper), `research/{topic}/` |
| `doc` | _genre 에 따라 자연어로 명시_ — rebuttal-response 의도면 `analysis_project/doc/{matching}/reviewers/` 필요, peer review 작성 의도면 `analysis_project/doc/{matching}/formats/` (venue review form) + `analysis_project/paper/` (대상 paper) 필요 | `analysis_project/doc/{matching}/formats/` (기관 template), `analysis_project/paper/`, `research/{topic}/` |

> doc mode 안의 _자연어 의도_ 가 사전 분석 요건을 결정. task description 에 "rebuttal 응답" / "peer review 작성" / "grant proposal" 같이 명시하면 pre-flight 가 그 의도 기준으로 필요 자료 점검.

매치 0: 사용자에게 안내 — "필요 자료를 `analyze-project --mode {paper|doc} <folder>` 로 먼저 사전 분석하세요" + 진행 여부 확인.
매치 다수: 후보 list 보여주고 선택 요청.

> **Prompt template variables**: 본 SKILL.md의 agent/sub-skill prompt 안에 등장하는 변수:
> - `{discovered_inputs}` — Pre-flight Step 2 (Input Discovery)에서 결정된 input path list. Agent prompt 구성 시 orchestrator가 newline-join 형식으로 expand (`Discovered inputs:\n  - <path1>\n  - <path2>\n  ...`). sub-skill 호출 시에는 `--inputs <comma-separated paths>` 인수로 전달.
> - 단일 ground-truth 경로는 `analysis_project/paper/*.md` (analyze-project --mode paper 산출물).

**검증 rigor (intensity-derived — 별도 `--qa` 축 없음)** — rigor tier 정의 + model role·round 매트릭스는 [`CONVENTIONS.md §1.1`](../../core/CONVENTIONS.md#11-verification-rigor-tiers-intensity-derived-canonical-sot) 단일 source. 검증 rigor 는 사용자 선택 축이 아니라 `--intensity` 에서 결정론적으로 파생된다. 본 skill 적용:

- rigor 파생: `direct`→none/light, `quick`→quick, `standard|strong`→standard, `thorough`→thorough, `adversarial`→adversarial. routine work 는 standard 이하에서 시작하며 명시 escalation 시 상향
- **Why fact-checker is separate**: quality reviewer 는 narrative/coverage/logic 에 집중, fact-checker 는 citation/venue/year/metric/lineage 만 narrow 하게 ground-truth (cards/PDFs) 와 verbatim 대조 — matching task 라 fast fact-checker role 로 충분 (Claude adapter: sonnet)
- **Propagation**: 선택된 `--intensity` (와 그로부터 파생된 rigor tier) 를 draft-strategy / draft-refine 에 flag 로 전달
- **`quick` interactions**: `--from strategy-refine` 또는 `--from draft-refine` 으로 재개 시 frontmatter `intensity == quick` 이면 abort ("intensity=quick 에서는 refine 단계가 skip 됩니다. --intensity 를 standard 이상으로 명시해 재개하세요.")

**`--user-refine`** (boolean flag — opt-in only)

**Default: false. The orchestrator (메인 에이전트) MUST NOT add this flag on its own — it is set only when the user typed `--user-refine` (or an explicit Korean equivalent like "사용자 검토 끼워" / "memo 추가하게 멈춰줘") in the original prompt.**
When present, pause at refine points so the user can add their own `<!-- memo: ... -->` comments on top of 연구팀's memos before draft-refine runs.

Pause behavior: after 연구팀 writes memos at Step 3 (strategy review) or Step 5 (draft review), do NOT invoke draft-refine. Instead:
1. Update `pipeline_state.yaml` at `{strategy_folder}/` with `user_refine: true`, `paused_at_stage: <strategy-refine|draft-refine>`.
2. Print the memo file path and resume command in the user's communication language:
   ```
   연구팀 메모가 {ko_path}에 기록되었습니다.
   직접 메모를 추가한 뒤 다음 명령으로 재개하세요:
       /autopilot-draft --mode {mode} --from <strategy-refine|draft-refine> <strategy_folder>
   ```
3. Exit. Do NOT write `pipeline_summary.md` (pipeline is paused, not terminated).

If 연구팀 added no memos, the pause is skipped (nothing to refine).

**`--from <stage>`** — resume the pipeline at a specific stage. Stages:
- `analyze` — Step 1 (Material Analysis)
- `strategy` — Step 2 (draft-strategy)
- `strategy-refine` — Step 3 wrapper: 연구팀 review + (user memos if `--user-refine`) + draft-refine on the strategy
- `draft` — Step 4 (Draft Generation)
- `draft-refine` — Step 5 wrapper: 연구팀 review + (user memos if `--user-refine`) + draft-refine on the draft
- `finalize` — Step 6 (Pipeline Summary)

When resuming with `--from`, the positional argument should be either the artifact directory path or a fuzzy-matchable short name. The orchestrator resolves it via the same fuzzy lookup used by Plan Resolution in autopilot-code: `ls -d <artifact-root>/documents/*$ARG* 2>/dev/null`. Read `pipeline_state.yaml` to recover `mode`, `intensity`, `discovered_inputs` (list), `user_refine`. CLI flags override state file; missing flags inherit from state.

**Format spec auto-discovery (no flag)** — venue/journal/lab-specific format references (review form / rebuttal template / paper template / grant body sections / etc.) are discovered automatically from `analysis_project/doc/{matching}/formats/`. There is no `--format-ref` flag. User pre-processes the spec once via `/analyze-project --mode doc <folder>`, after which all autopilot-draft modes pick it up.

- **No built-in presets**. There is no single "openreview format" or "journal format" — even the same venue changes its review/rebuttal template year-to-year, and journals/labs each define their own. The user pre-processes the actual document via `/analyze-project --mode doc`.
- **Acceptable file types in `formats/`**: `.md`, `.txt`, `.pdf`, `.html`, `.docx` (or any plain-text-ish format the agent can Read).

**What the format spec should contain** (any subset — agent extracts what it can):

| Mode | format spec typical content |
|---|---|
| `paper` | venue paper template (예: NeurIPS 2026 LaTeX style) / page limits / section requirements / citation style / required disclosures |
| `presentation` | lab/venue slide template / time limits / required sections / branding rules / sample past presentations |
| `doc` | _genre 별 다양_ — task description 자연어 의도가 결정. 예: rebuttal-response → rebuttal length limit / sub-type indication (meta-reviewer-only one-shot / reviewer-dialogue multi-round / response-with-paper-revision). peer review → review template sections / rating axes / length / tone. report → 기관 template / required sections / 청중 기대. proposal → grant body required sections (NRF/NSF/internal) / page limits / evaluation criteria. tech blog · memo → optional |

**Resolution order** (every mode):

1. **Auto-discovery in `analysis_project/doc/{matching}/formats/`** — agent looks at `analysis_project/doc/{matching}/formats/*` (where `{matching}` was discovered by Input Discovery). The format extraction was already performed by `analyze-project --mode doc`.
   - 1 candidate found → use it, log to user: "format spec auto-discovered: {path}".
   - 2+ candidates → ask user at Step 0 to pick one.
   - 0 candidates → mode-specific fallback (below).
2. **Mode-specific fallback** when auto-discovery yields no candidate:

| Mode | Behavior when no format spec available |
|---|---|
| `paper` | Warn-and-fallback to generic LaTeX article layout. Strong warning if target venue is academic — Suggest: "venue paper template (e.g. NeurIPS LaTeX style) significantly improves draft quality; run `/analyze-project --mode doc <folder>` first to extract it." |
| `presentation` | Warn-and-fallback to generic slide-by-slide markdown. Lab/venue slide templates improve fit but not blocking. |
| `doc` | _자연어 의도 기반 분기_. **peer review 작성** 의도 (task description 에 "peer review" / "review form" / "리뷰 작성" 같은 표현) → **hard-fail** ("venue review form REQUIRED — run `/analyze-project --mode doc <folder>` first. Venues differ year-to-year — no built-in presets."). **rebuttal-response** 의도 (task description 에 "rebuttal" / "OpenReview 응답" / "리뷰 응답") → **prompt user**: (a) materialize the format via `/analyze-project --mode doc <folder>` and retry / (b) declare format constraints inline in `<task description>` (length limit, sub-type, scope) / (c) opt into generic conference rebuttal layout (warn quality drop). **report / proposal / blog / memo** → warn-and-fallback to generic prose layout. NRF / NSF / 산학협력단 grant 의도면 기관 template 추천. |

> Sub-type information (rebuttal sub-type · review template sections · paper page limits · grant evaluation criteria 등) 은 모두 **auto-discovered format spec file 에서 추출**. 별도 flag 없음. File 에 정보 부족하면 Step 0 (fallback prompt 내) 에서 user 에게 묻거나 documented assumptions 으로 진행.

The remaining text (after removing mode and flags) is the task description.

> **Note on presentation mode**: This pipeline produces only the slide-by-slide markdown draft (`draft/draft.md` and `draft/draft_ko.md`). PPTX export is **NOT supported** because pandoc + Korean lab templates have unreliable compatibility (font/layout drift, OOXML strictness). The user converts markdown → PPT manually in PowerPoint using their lab template directly.

## Decision Defaults (no autonomy gating)

The pipeline runs with sane defaults and only pauses on genuinely ambiguous or destructive situations.

| Decision Point | Default Behavior |
|---|---|
| Confirm material analysis | Auto-proceed. |
| Missing refs folder | **Always ask** at pre-flight (mode-dependent). |
| No reviewer comments (doc mode + rebuttal-response 의도) | **Always ask** at pre-flight. |
| Strategy review → memos added | Auto-refine (or pause for user-memo if `--user-refine` is set). |
| Draft review → memos added | Auto-refine (or pause for user-memo if `--user-refine` is set). |
| Format spec resolution | _Always_ from `analysis_project/doc/{matching}/formats/` (classified by `analyze-project --mode doc` in advance). No `--format-ref` flag. Mode-specific fallback: `paper` / `presentation` warn-and-fallback (generic layout). `doc` 의 _peer review 의도_ hard-fails / _rebuttal-response 의도_ prompts user / 그 외 (report·proposal·blog·memo) warn-and-fallback. |
| Scope Clarification triggered | Ask 2-4 questions; auto-proceed if `--no-clarify`. |

**Logging**: When the pipeline pauses (missing required input, 0 search results, or `--user-refine`), record the event for the Decision Points table in `pipeline_summary.md`. Auto-decisions are not individually logged.

## pipeline_state.yaml

Written/updated at `{strategy_folder}/pipeline_state.yaml` after each completed stage. Used by `--from` resume:

```yaml
pipeline: autopilot-draft
mode: presentation
intensity: thorough                   # verification rigor derives from this (CONVENTIONS §1.1); no separate qa axis
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

External materials must be pre-processed into `<artifact-root>/` _before_ invoking autopilot-draft. The pipeline reads from these persistent sources only — no `--refs` flag, no ad-hoc folder paths.

| Input type | Pre-processing skill | Output location |
|---|---|---|
| Academic papers (PDFs) | `/analyze-project --mode paper` | `analysis_project/paper/` |
| Reviewer comments / format templates / past samples / mixed doc materials | `/analyze-project --mode doc <folder>` | `analysis_project/doc/{name}/` |
| External field research | `/autopilot-research <topic>` | `research/{topic}/` |
| Codebase context (proposal/report 모드에서 언급용) | `/analyze-project --mode code` | `analysis_project/code/` |

On invocation, autopilot-draft runs Input Discovery (Pre-flight Step 2) — fuzzy match task description vs above persistent sources — and gathers `discovered_inputs` paths to pass to sub-skills. For rebuttal mode, fails with clear message if no reviewer materials match.

## Artifact Structure
All outputs go to:
```
<artifact-root>/documents/{YYYY-MM-DD}_{short-name}/
├─ pipeline_summary.md       (T1 — entry/index + integrated history)
├─ draft/                    (T1 — generated for all 3 modes; latest only)
│  ├─ draft.md              (primary-language draft; for presentation: slide-by-slide markdown; for paper: LaTeX-ready prose / paste blocks)
│  └─ draft_ko.md           (Korean mirror — conditional: primary 가 사용자 작업 언어와 다를 때만)
├─ strategy/                 (T2 — latest only)
│  ├─ strategy.md           (primary-language strategy document)
│  └─ strategy_ko.md        (Korean mirror — conditional)
├─ analysis/                 (T2)
│  ├─ reviewer_analysis.md   (doc mode + rebuttal-response 의도: per-reviewer breakdown)
│  ├─ ref_analysis.md        (reference material analysis)
│  └─ material_index.md      (inventory of all input materials)
└─ _internal/                (T3 — audit / reviews / version snapshots)
   ├─ strategy_reviews/      (QA and 연구팀 strategy reviews)
   ├─ draft_reviews/         (QA and 연구팀 draft reviews)
   └─ versions/              (autopilot-refine snapshots)
      ├─ v1/strategy/, draft/
      └─ v{N}/...
```
