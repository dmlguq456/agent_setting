---
name: analyze-project
description: Pre-work analysis skill — analyzes the project's primary materials and writes structured artifacts to .claude_reports/analysis_project/. Three modes — code (codebase), paper (academic PDFs), doc (miscellaneous doc materials like reviewer comments, format templates, samples, internal notes). Mode auto-detects between code and doc when omitted; paper requires explicit --mode paper. Output is the persistent input source for downstream autopilot-{doc,code,research} skills.
argument-hint: "[--mode code|paper|doc] [<scope/target/input-folder>] [--skip-qa]"
---

> Caller note: this skill performs deep analysis. Callers should invoke at `high` or `xhigh` effort when the runtime supports it; at lower effort, depth narrows automatically.

> **산출물 폴더 컨벤션**: [SKILL_OUTPUT_CONVENTION.md](../../SKILL_OUTPUT_CONVENTION.md) (3-tier T1/T2/T3). 본 skill의 산출물은 `.claude_reports/analysis_project/{code,paper,doc}/` 하위. 각 mode의 main outputs는 root, raw scan log/QA reviews는 `_internal/`.

> **Workspace assumption**: Claude는 프로젝트 루트에서 실행됨. `.claude_reports/`는 현재 dir에 생성. 본 skill의 input scope (코드 / PDFs / doc materials)도 현재 dir 또는 그 하위 폴더 기준.

## Language Rule
- Think and reason in English internally.
- Write documentation files in English (code/paper modes) or Korean+English mixed (doc mode).
- When explaining something to the user, write in Korean.

## Argument Parsing

```
/analyze-project [--mode code|paper|doc] [<scope/target>] [--skip-qa]
```

- `--mode <X>`: explicit mode selection. If omitted → auto-detect (code vs doc only; paper requires explicit).
- `--skip-qa`: skip Phase 5 QA Verification.
- Remaining text after flag removal is mode-specific:
  - `code`: target dir/keyword/scope (default: project root)
  - `paper`: paper id or "all" (default: "all")
  - `doc`: input folder path (REQUIRED — no default)

### Mode Auto-Detection (when `--mode` omitted)

Inspect current directory:

| Indicators | Detected mode |
|---|---|
| `src/`, `lib/`, `models/`, `.git`, `package.json`, `pyproject.toml`, OR `*.py`/`*.ts`/`*.go`/`*.rs` files at root | **code** |
| Many `*.pdf` / `*.docx` / `*.md` files; no source dirs; no build manifests | **doc** |
| Both indicators present | **code** (default — user can override with `--mode doc`) |
| Neither / unclear | ask user: "code, paper, doc 중 어느 mode인가요?" |

> **`paper` mode is never auto-selected** — paper analysis requires explicit `--mode paper` because PDF presence alone is ambiguous (could be reviewer comments, templates, etc. for doc mode). The boundary between paper and doc is genuinely fuzzy in the wild.

## Output Directories

| Mode | Output | Scoping |
|---|---|---|
| code | `.claude_reports/analysis_project/code/` | flat (project-level, accumulates over time) |
| paper | `.claude_reports/analysis_project/paper/` | flat (project's paper collection accumulates) |
| doc | `.claude_reports/analysis_project/doc/{name}/` | per-task subdir |

`{name}` for doc mode: derived from the input folder name (e.g., `--mode doc tf_restormer_patent` → `analysis_project/doc/tf_restormer_patent/`). User can override by passing a different name as the second positional arg.

---

# Mode `code`

Analyzes the codebase and produces module-level documentation.

## Phase 1: Codebase Analysis
Determine scope first:
- If `<target>` is a directory path → read files under that path recursively.
- If `<target>` is a keyword (e.g., "engine", "inference") → map to relevant modules by reading CLAUDE.md's structure section first, then read those modules.
- If `<target>` is empty → read CLAUDE.md's Project Structure section if present and derive scope; otherwise fall back to top-level entry points + obvious source dirs (`src/`, `lib/`).

Read in-scope code and identify:
- Role and interface of each file/module
- Data flow (input → processing → output)
- Dependencies between modules
- Design intent and core algorithms

## Phase 2: Documentation
Write analysis results as topic-separated md files in `.claude_reports/analysis_project/code/`.
- Split by role, not one monolithic file
- Focus on code-level details (not usage guides)
- Write in English
- Each doc MUST end with an **## Interface Reference** section:
  ```
  ## Interface Reference

  | Class/Function | File | Signature | Called by |
  |---|---|---|---|
  | `ClassName` | file.py:L | `(arg1, arg2, ...) → return` | `caller_module.func` |
  | `function_name` | file.py:L | `(arg1, ...) → return` | `caller.func1`, `caller.func2` |
  ```
  - Include all public classes, key functions, and any function with cross-module callers.
  - The "Called by" column enables downstream agents (especially 기획팀) to quickly assess change impact without grepping source.

## Phase 3: CLAUDE.md
CLAUDE.md should minimize code content and contain only:
- `.claude_reports/analysis_project/code/` document list with coverage table
- Behavioral guidelines (coding rules, restrictions, commit rules)
- Project structure overview (tree)
- Execution examples
- If CLAUDE.md already exists, preserve existing rules and merge new findings

## Phase 4: Verify Documentation Coverage
- Check that every code file in models/, utils/, src/ etc. is covered by at least one document.
- Documentation updates are handled as an explicit step in execute-plan, not by hooks.

## Phase 5: QA Verification (skipped with `--skip-qa`)

After documentation is written, invoke 품질관리팀 in code review mode to cross-check Interface Reference entries against actual source code.

- **Scope**: Documentation files updated in the current run only.
- **Minimum verification**: At least 2 Interface Reference entries per file — check signature, file path, and line number against actual source.
- **Model**: Light QA using sonnet — documentation is not as critical as code changes.
- Reviews logged to `.claude_reports/analysis_project/code/_internal/reviews/`.

---

# Mode `paper`

Analyzes academic reference PDFs and produces per-paper analysis + integrated overview.

## Delegate to 연구팀

Invoke the **research-team** (연구팀) agent as a subagent with the following prompt:

```
Analyze reference papers and generate paper documentation.

Scope: {$ARGUMENTS or "all"}
Date: {YYYY-MM-DD}

## Inputs
- Reference PDFs: search current dir + common subfolders (e.g., `papers/`, `refs/`, `pdfs/`) for `*.pdf`. If `<scope>` arg is provided as a folder path or keyword, use that. Otherwise auto-discover by scanning project root + 1-level subfolders.
- Existing paper docs: .claude_reports/analysis_project/paper/*.md
- Existing code docs: .claude_reports/analysis_project/code/*.md (for paper-code mapping)
- Source code: project root source dirs (`models/`, `src/`, `lib/`, etc.) for verifying paper-code alignment

## Procedure

### 1. Read all reference PDFs
Extract per paper: core contributions, architecture design, key equations, experimental findings, design constraints, ablation results.

### 2. Read existing analysis_project/paper/ files
Check what already exists and what needs updating.

### 3. Read code docs and source code
Read analysis_project/code/ and relevant source files to verify paper-code alignment.

### 4. Generate/Update individual paper summaries
For each paper, create or update its summary file in `.claude_reports/analysis_project/paper/` (agent decides filenames).
Each file should contain: paper title/venue/year, core contribution, architecture overview, key design decisions and why, important equations, ablation results that constrain design, paper-to-code mapping.

### 5. Generate/Update 00_overview_and_constraints.md
This is the MOST IMPORTANT file — it's the primary reference for 연구팀 during plan review.

Structure:
```markdown
# Project Overview and Design Constraints

## Paper Evolution
## Paper → Code Variant Mapping
## Core Design Principles
(each principle: what it is, why it matters with paper evidence, how it maps to code)
## Architecture Constraints
Hard Constraints (must NOT be changed):
(project-specific list — e.g., correlation input, early-split, filter estimation, etc.)
## Terminology Mapping
## Cross-Paper Relationships
```

### 6. Verify paper-code alignment
For each major component, verify alignment and document discrepancies or code-only features.

Write in English. Code identifiers stay as-is.
Return ONLY the list of created/updated file paths and a brief Korean summary.
```

## Post-Analysis
After the 연구팀 agent returns:
1. Relay the file paths and summary to the user.
2. Recommend reviewing `00_overview_and_constraints.md` first.

---

# Mode `doc`

Analyzes miscellaneous doc-creation materials (reviewer comments, format templates, past samples, internal notes, mixed reference packs) and produces structured per-task analysis.

## Phase 1: Input Discovery & Classification

Read the input folder (REQUIRED positional arg). Classify each file by heuristic:

| File pattern | Category | Output target |
|---|---|---|
| Filename contains `review`/`reviewer`/`comment` OR text contains "Reviewer 1:" / scoring | reviewer comments | `reviewers/` |
| Filename contains `template`/`format`/`guideline`/`cfp`/`instructions` | format spec | `formats/` |
| Filename suggests past example (`sample`, `past`, `example`, prior year naming) | sample | `samples/` |
| PDF with academic structure (abstract/citations) | paper-like | (suggest `--mode paper` instead; or include as `samples/`) |
| Other (notes, sketches, mixed) | misc | `misc/` |

If classification is ambiguous → 연구팀에게 위임해 판단.

## Phase 2: Per-Category Analysis

Delegate to 연구팀:

```
Analyze doc-creation materials in this folder: {input_folder}
Output: .claude_reports/analysis_project/doc/{name}/

For each file in input folder, classify and produce structured analysis:

- reviewers/ : per-reviewer breakdown — score, confidence, summary, key points (severity-tagged), tone
- formats/ : structured format extraction — required sections, length limits, page limits, submission window, sub-types (for rebuttal: meta-only / dialogue / response-with-revision), tone guidelines
- samples/ : key structural patterns and stylistic choices observable in past examples
- misc/ : free-form summary indexing the file's content for later retrieval

Also write 00_overview.md at root of {name}/:
- Inventory of all files in the input folder, with classification
- Key findings per category
- Cross-references useful for autopilot-doc downstream
- "intended for mode": likely autopilot-doc mode this material targets (rebuttal/write/review/proposal/report/presentation)

Korean prose for narrative; English/source language for verbatim quotes.
Return ONLY paths + Korean summary.
```

## Phase 3: Verify
- Confirm all input files are classified (none silently dropped).
- If classification was ambiguous, prompt user to confirm or override.
- Logged to `.claude_reports/analysis_project/doc/{name}/_internal/`.

---

# Standard output structure (per mode)

## code
```
analysis_project/code/
├── 00_overview.md or topic_*.md   [T1] 모듈별 분석
├── interface_reference 통합        [T1]
└── _internal/                      [T3]
    └── reviews/                    QA log
```

## paper
```
analysis_project/paper/
├── 00_overview_and_constraints.md  [T1] 통합 overview
├── per-paper analysis (*.md)        [T1·T2] paper별
└── _internal/                       [T3]
```

## doc
```
analysis_project/doc/{name}/
├── 00_overview.md                   [T1] 인벤토리 + 분류 + 대상 mode
├── reviewers/                       [T2] reviewer별 breakdown
├── formats/                         [T2] template/guideline 추출
├── samples/                         [T2] past examples 핵심
├── misc/                            [T2] 기타 free-form 요약
└── _internal/                       [T3] raw scan, QA reviews
```

---

# Cross-skill integration

`analyze-project`의 산출물은 _영속 자산_으로 후속 autopilot-* skill이 implicit으로 읽음:

- `autopilot-code`는 `analysis_project/code/`를 자동 인지 (init-plan에서 모듈 매핑 참조)
- `autopilot-doc`는 mode에 따라:
  - `rebuttal` → `analysis_project/doc/{matching}/reviewers/` + `analysis_project/paper/`
  - `write` → `analysis_project/paper/` + `analysis_project/doc/{matching}/formats/`
  - `review` → `analysis_project/doc/{matching}/formats/` (REQUIRED)
  - 그 외 mode 비슷한 패턴
- `autopilot-research`는 자체 외부 검색 위주이지만, 보유 자료가 있으면 `analysis_project/paper/` 인지 가능

`--refs <folder>` flag는 family 전체에서 _제거_ — 모든 입력은 `analysis_project/*` 또는 `research/*` 같은 `.claude_reports/` 하위 영속 산출물에서 자동 발견.

## Typical workflow

```bash
# 1. 사전 분석
/analyze-project --mode code        # 코드베이스
/analyze-project --mode paper       # 보유 논문 PDFs
/analyze-project --mode doc tf_restormer_patent/  # 특허 발표 자료

# 2. 후속 작업 (input은 자동 인지)
/autopilot-code --mode dev "<task>"
/autopilot-doc "<task>" --mode presentation
/autopilot-research <topic>
/autopilot-refine "<prompt>"
```
