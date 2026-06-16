---
name: analyze-project
description: Pre-work analysis skill — analyzes the project's primary materials and writes structured artifacts to .claude_reports/analysis_project/. Three modes — code (codebase), paper (academic PDFs), doc (miscellaneous doc materials like reviewer comments, format templates, samples, internal notes). Mode auto-detects between code and doc when omitted; paper requires explicit --mode paper. Output is the persistent input source for downstream autopilot-{draft,code,research} skills.
argument-hint: "[--mode code|paper|doc] [<scope/target/input-folder>] [--skip-qa]"
---

> Caller note: this skill performs deep analysis. Callers should invoke at `high` or `xhigh` effort when the runtime supports it; at lower effort, depth narrows automatically.

> **산출물 폴더 컨벤션**: [CONVENTIONS.md §5](../../CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) (3-tier T1/T2/T3). 본 skill의 산출물은 `.claude_reports/analysis_project/{code,paper,doc}/` 하위. 각 mode의 main outputs는 root, raw scan log/QA reviews는 `_internal/`.

> **Workspace assumption**: Claude는 프로젝트 루트에서 실행됨. `.claude_reports/`는 현재 dir에 생성. 본 skill의 input scope (코드 / PDFs / doc materials)도 현재 dir 또는 그 하위 폴더 기준.

## Language Rule
- Write documentation files in English (code/paper modes) or Korean+English mixed (doc mode).
- When explaining something to the user, write in natural Korean (no translationese).

## Argument Parsing

```
/analyze-project [--mode code|paper|doc] [<scope/target>] [--skip-qa] [--full]
```

- `--mode <X>`: explicit mode selection. If omitted → auto-detect (code vs doc only; paper requires explicit).
- `--skip-qa`: skip Phase 5 QA Verification.
- `--full`: 강제 전체 재분석 (기존 산출물 무시). default 동작 — 기존 산출물 발견 시 **incremental** (변경 파일만 재분석, cost 10-20%), 부재 시 full.
- Positional `<scope/target>` (**모든 mode에서 OPTIONAL** — default = cwd 자동 발견):
  - `code`: 범위 좁히기 — 모듈 keyword (`engine`) 또는 sub-dir (`src/models/`). Default = project root.
  - `paper`: 외부 폴더 override (예: `~/papers/2024/`). Default = cwd + 1-level subfolders (`papers/` / `refs/` / `pdfs/`) 자동 발견.
  - `doc`: 외부 폴더 또는 sub-task name override. Default = cwd + 1-level subfolders (`docs/` / `reviews/` / `templates/` / `reviewer_comments/`) 자동 발견. 명시 시 외부 폴더 path를 그대로 input scope로 사용.

> **Workspace 원칙**: 사용자는 분석 대상 자료(PDFs / reviewer comments / templates 등)를 _프로젝트 dir 안에_ 두는 것이 표준. `cd <project>` 후 `/analyze-project --mode <X>` (positional 없이) 호출하면 90%+ 케이스 자동 처리. positional 인자는 _외부 폴더를 직접 가리키는 fallback_ 용도.

### Mode Auto-Detection (when `--mode` omitted)

Inspect current directory:

| Indicators | Detected mode |
|---|---|
| `src/`, `lib/`, `models/`, `.git`, `package.json`, `pyproject.toml`, OR `*.py`/`*.ts`/`*.go`/`*.rs` files at root | **code** |
| Many `*.pdf` / `*.docx` / `*.md` files; no source dirs; no build manifests | **doc** |
| Both indicators present | **code** (default — user can override with `--mode doc`) |
| Neither / unclear | ask user: "code, paper, doc 중 어느 mode인가요?" — 글로벌 [CLAUDE.md](../../CLAUDE.md) §2 적용 (ScheduleWakeup 10-15분 동시 호출; 답 없으면 cwd 신호 강한 쪽으로 자율 진행) |

> **`paper` mode is never auto-selected** — paper analysis requires explicit `--mode paper` because PDF presence alone is ambiguous (could be reviewer comments, templates, etc. for doc mode). The boundary between paper and doc is genuinely fuzzy in the wild.

## Output Directories

| Mode | Output | Scoping |
|---|---|---|
| code | `.claude_reports/analysis_project/code/` | flat (project-level, accumulates over time) |
| paper | `.claude_reports/analysis_project/paper/` | flat (project's paper collection accumulates) |
| doc | `.claude_reports/analysis_project/doc/{name}/` | per-task subdir |

`{name}` for doc mode: derived from input folder basename (positional arg) or cwd basename (default — when positional 생략, 즉 자동 발견 모드). 예: `--mode doc` (positional 없이) within `/.../tf_restormer/` cwd → `analysis_project/doc/tf_restormer/`. 명시 override: `--mode doc tf_restormer_patent` → `analysis_project/doc/tf_restormer_patent/`.

---

# Mode `code`

Analyzes the codebase and produces module-level documentation.

## Phase 0: Incremental vs Full 분기 (자동)

호출 자리에서 `.claude_reports/analysis_project/code/_last_run.yaml` 검사:

| 감지 | 처리 |
|---|---|
| `_last_run.yaml` 부재 또는 `--full` 명시 | **full 분석** — 전 codebase scan + 4 종 실험 자료 처음 추출 |
| `_last_run.yaml` 존재 (incremental, default) | **incremental update** — 변경 파일만 재분석 + 영향 자리만 update |

### Incremental update 절차

1. `_last_run.yaml` read — `last_scan_time` + 각 module 의 SHA / mtime
2. 변경 파일 list — `git log --since="$last_scan_time" --name-only --pretty=format:` (git 있는 자리) 또는 `find <scope> -newer _last_run.yaml -type f \( -name "*.py" -o -name "*.cpp" -o -name "*.ts" \)` (git 없는 자리)
3. 변경 자리 분류 — _작은 변경_ (한 module 안 함수·class) vs _큰 변경_ (새 module / 새 모델 폴더 / cleanup)
4. 영향 받는 산출 자리 update:
   - 변경 module 의 `<module>.md` re-write (단 영향 받지 않은 module 의 .md 는 보존)
   - `interface_reference` 통합 — 변경 module 부분만 갱신
   - 4 종 실험 자료 — 변경이 _영향 주는 자리_ 만 update:
     - `experiment_conventions.md` — 새 layer / config 변경 자리 발견 시 보강
     - `experiment_readiness.md` — train/eval 분리 / seed 자리 변경 시 재점검
     - `cleanup_candidates.md` — 변경 후 새 unused / dead branch 자리만 추가
     - `similar_models.md` — 새 모델 폴더 추가 시 행 추가, 기존 모델은 보존
5. `_last_run.yaml` 갱신 — `last_scan_time = now()`, 각 module SHA 갱신
6. QA verification (Phase 5) — _변경 자리만_ — cost 10-20% 수준

### `_last_run.yaml` schema

```yaml
mode: code
last_scan_time: "2026-05-26T15:30:00Z"
scope: "."
modules:
  - path: src/models/conformer.py
    sha: <git blob SHA or file hash>
    last_analyzed: "2026-05-26T15:30:00Z"
  - path: src/train.py
    sha: <...>
    last_analyzed: "2026-05-26T15:30:00Z"
experiment_artifacts:
  experiment_conventions_sha: <...>
  experiment_readiness_sha: <...>
  cleanup_candidates_sha: <...>
  similar_models_sha: <...>
```

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

## Phase 3.5: Experiment Conventions, Readiness, Cleanup & Similarity (lab 사전 자료)

본 phase 는 _autopilot-lab 의 Step 0 auto-load_ 가 매번 read 하는 4 종 산출. 한 번 추출하면 영속 — lab 호출 마다 재추출 X. 사용자 코드베이스의 _실험 패턴 source of truth_ 자리.

각 산출은 root `code/` 에 _flat 산출_ (다른 module 분석 파일과 같은 자리). lab 가 매번 본 4 파일을 read 한다.

### 3.5.1. `experiment_conventions.md`

본 프로젝트 코드베이스의 _실험 패턴 — source of truth_. **본 프로젝트 컨벤션이 1순위**, `mem profile 07_coding_convention` (cross-project default) 는 _per-project 부재·빈 자리만_ 보강하는 2순위 자리. 충돌 자리는 per-project 우선 — 개별 프로젝트의 특수 사정 (외부 ref 기반 / 다른 framework / legacy 코드 / 다른 layer 선호) 침범 X.

autopilot-lab / autopilot-spec / 개발팀 _new-lib_ 는 _본 파일 1순위 + mem profile 07_coding_convention 보강_ 으로 prepend.

다음 섹션 자동 추출 (본 프로젝트 실제 자리 그대로):

```markdown
## 모델 폴더 구조
- 위치: `model/{model_name}/` (실제 자리에서 grep)
- 묶음 단위: model.py + config.yaml + train.py + ... (한 폴더 안)

## 기존 모델 list
- <model_1> (한 줄 설명)
- <model_2> ...

## Config 메커니즘
- yaml / argparse / hydra 중 하나 (cwd 의 실제 자리)
- 마이너 변경이 config 로 들어가는 자리

## 튜닝 변형 prefix
- `_ft01_` · `_ft02_` ... — base 의 fine-tuning 변형 (사용자 코드에서 grep)
- 새 base = 새 모델 폴더, 변형 = 같은 폴더 안 prefix file

## Preferred layer (이미 사용 중 — autopilot-lab 의 1순위)
- <model_1>: <layer_list> (model.py 의 import + class 정의 grep)
- 새 layer 도입은 명시 컨펌 필요
```

추출 전략 — `model/*/` 폴더 ls + 한 모델 sample read + config 파일 sample read + `_ft` 패턴 grep + import 분석.

### 3.5.2. `experiment_readiness.md`

실험 ready 점검 checklist. 각 항목 ✅ / ⚠️ / ❌ + 미흡 자리는 _autopilot-code 정리 권장_ 한 줄.

| 항목 | 의미 | 점검 |
|---|---|---|
| 모델 단위 폴더 분리 | `model/{name}/` 묶음 단위 잡혀 있나 | `ls model/` 결과 |
| Config 메커니즘 일관성 | yaml/argparse/hydra 한 종 채택 | 코드 내 import grep |
| train.py / eval.py 분리 | 한 script 에 다 박혀 있지 않나 | 파일 존재 검사 |
| base 와 변형 구분 | `_ft01_` 같은 prefix 패턴 일관 | 파일명 패턴 |
| log/ckpt 구조 | `runs/{run-id}/` 같은 누적 자리 잡혔나 | 폴더 / .gitignore |
| Reproducibility | seed·git hash 기록 자리 | train.py grep |

format:
```markdown
## 실험 ready 점검

| 항목 | 상태 | 비고 |
|---|---|---|
| 모델 단위 폴더 | ✅ | model/TF_Restormer/, model/SR_CorrNet/ |
| Config | ⚠️ | yaml + argparse 혼재 |
| train/eval 분리 | ❌ | main.py 한 파일 |
| prefix 패턴 | ⚠️ | _ft01_ 한 번 사용, 다른 자리 일관 X |
| log/ckpt | ✅ | runs/ 자리 잡힘 |
| Reproducibility | ❌ | seed 자리 없음 |

## 권장
미흡 자리 (⚠️ / ❌) 정리:
/autopilot-code "main.py 를 train.py / eval.py 분리 + seed·git hash 기록 + yaml/argparse 정리"
```

### 3.5.3. `cleanup_candidates.md`

실험 시작 _전_ 손볼 자리 list. autopilot-code 호출 시 input.

| 항목 | 추출 |
|---|---|
| unused imports / dead code | static scan (`ruff` / `pyflakes` 가능 시) |
| commented-out 실험 자국 | `# old:` / `# TODO:` / `# debug:` 패턴 grep |
| 한 파일에 박힌 변형 다발 | `if config.variant == ...` 식 분기 grep |
| 사용 안 하는 layer / module | import graph (단순 grep: 정의는 있고 import 없음) |
| 다 쓴 ablation 자국 | `# ablation1` / `# v1` / `# old version` 주석 영역 |

format:
```markdown
## Cleanup 후보

| 파일 | 자리 | 종류 | 추정 |
|---|---|---|---|
| model/X.py:42 | `from old_utils import _legacy_func` | unused import | 안전 제거 |
| model/X.py:120-180 | `if config.variant == "v1":` 분기 | dead branch | v2 만 활성 — v1 제거 가능 |
| model/old_layer.py | class 정의는 있고 import 없음 | unused module | 파일 통째 삭제 후보 |
| train.py:80 | `# TODO: try learning rate ablation` | 다 쓴 주석 | 정리 |

## 정리 명령 권장
/autopilot-code "unused imports / dead branch / 주석 자국 정리"
```

### 3.5.4. `similar_models.md`

autopilot-lab 의 `--ref` 자동 추천 source. 새 실험 시작 자리에서 _가장 유사한 기존 모델_ 추천.

| 자리 | 추출 |
|---|---|
| 모델 별 1 줄 설명 | model.py 의 docstring / `__init__.py` |
| 사용한 layer set | model.py import + class 정의 |
| 데이터셋 | config.yaml 의 dataset 자리 |
| metric | train.py / eval.py 의 metric grep |

format:
```markdown
## 모델 간 유사도

| 모델 | 도메인 | 핵심 layer | 데이터셋 | metric | 유사 자리 |
|---|---|---|---|---|---|
| TF_Restormer | image / TF | MDTA, GDFN, LayerNorm2d | DIV2K / GoPro | PSNR / SSIM | (자기 자신) |
| SR_CorrNet | image SR | CorrAttention, ResBlock | DIV2K | PSNR | TF_Restormer 와 LayerNorm2d 공유 |

## 새 실험 자리 추천 logic
- 새 실험이 _image restoration_ 인지 발화 → TF_Restormer 추천
- 새 실험이 _correlation 기반_ → SR_CorrNet 추천
- 데이터셋 / metric 매칭 우선
```

본 4 파일은 _한 번 추출 후 영속_ — 사용자가 코드베이스 큰 변경 (새 layer 도입·prefix 패턴 변경·새 모델 추가) 시 _re-run analyze-project --mode code_ 로 갱신.

## Phase 4: Verify Documentation Coverage
- Check that every code file in models/, utils/, src/ etc. is covered by at least one document.
- Documentation updates are handled as an explicit step in code-execute, not by hooks.

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
Analyze the target paper(s) and generate documentation. **FIRST, determine the PURPOSE — paper mode 는 목적별로 분석이 다르다**:
- **(A) reference-survey**: 남의 논문을 _인용·grounding_ 용으로 조사 (외부 PDF 모음). → 아래 §1-6 (contribution/architecture/paper-code mapping).
- **(B) own-paper review**: _작성·검토 중인 우리 프로젝트의 자기 논문_(main.tex)을 camera-ready/revision 으로 다듬기 위한 분석. → **§0 '논문 내용 완전 분석'이 MAIN 산출**, §1-6 reference 분석은 보조/생략. 대상이 프로젝트 루트의 단일 작성중 main.tex 면 (B) 로 자동 판별 (모호하면 사용자 확인).

Scope: {$ARGUMENTS or "all"}
Date: {YYYY-MM-DD}

## Inputs
- Reference PDFs: search current dir + common subfolders (e.g., `papers/`, `refs/`, `pdfs/`) for `*.pdf`. If `<scope>` arg is provided as a folder path or keyword, use that. Otherwise auto-discover by scanning project root + 1-level subfolders.
- Existing paper docs: .claude_reports/analysis_project/paper/*.md
- Existing code docs: .claude_reports/analysis_project/code/*.md (for paper-code mapping)
- Source code: project root source dirs (`models/`, `src/`, `lib/`, etc.) for verifying paper-code alignment

## Procedure

### 0. (목적 B) 논문 내용 완전 분석 [own-paper review — REQUIRED, MAIN 산출]

대상이 _작성·검토 중인 자기 논문_(main.tex)이면, **무엇보다 먼저 논문을 끝까지 읽고 내용을 완전히 숙지·분석**해 `analysis_project/paper/00_self_paper_analysis.md` 로 정리한다. 이건 downstream autopilot-draft / 연구팀 review / autopilot-apply 가 검토 전 _숙지하는 1차 자료_ — 부실하면 하류가 표/그림 정체를 오독하고 번호·정합성을 틀린다 (실제 사고 2026-05-27: 내용 분석 없이 구조 맵만 있어 `tab:VCTK_ND`(평가셋 생성)를 'dedicated SR 학습'으로 오독, Table 번호 오기, 중복 label 미검출). **구조 맵·페이지 수 나열로 끝내지 말 것 — 내용·논리 분석이 핵심.**
  1. **섹션별 논리 흐름·주장-근거**: intro 문제 제기 → method 설계 의도 → 각 eval 의 _목적·셋업·결론_. "왜 이 실험을 이 순서로, 무엇을 보이려고" 가 드러나게.
  2. **기여(claims) 타당성·명확성**: 주장한 contribution 이 본문·실험으로 뒷받침되는가, 과장·중복·미입증은 없는가.
  3. **실험 결과 해석 일관성**: 본문 서술이 표/그림의 _실제 수치_ 와 맞는가 (예: "outperforms" 라는데 표에서 baseline 보다 낮은 칸은 없는가). 본문↔표 교차 검증.
  4. **표/그림 인벤토리 — 정체·역할**: 각 표/그림이 _무엇을 위한 것인지_ + label 이름 + 어느 섹션이 `\ref` 참조 + 핵심 내용. float 위치가 아니라 _참조 흐름·내용_ 기준 (예: `tab:augmentations`=학습 distortion / `tab:VCTK_ND`=VCTK-SSR 평가셋 생성).
  5. **label·번호 맵 + 정합성**: `main.aux` `\newlabel` 실제 PDF 번호 + `main.log` `multiply defined`(중복 label) + `\ref`/`\cite` 미정의. 추정 금지, aux/log 기계 추출.
  6. **서술 품질·용어 일관성**: 약자 정의 위치, 표기 흔들림, 명백한 문법 비문(주어-동사·관사·복수).
이게 있어야 연구팀이 _내용을 숙지한 채_ 검토한다 (CONVENTIONS 'ceremony 보다 내용 숙지가 먼저'). 목적 (A) reference-survey 면 본 §0 는 skip 하고 §1-6 로.

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

**Input scope resolution** (in priority order):
1. **Positional arg 명시**: 그 folder를 input scope로 (외부 폴더 override).
2. **Default — cwd 자동 발견**: 다음 패턴 grep within cwd + 1-level subdirs:
   - `docs/` / `reviews/` / `templates/` / `reviewer_comments/` / `format/` / `guidelines/` (sub-folder 통째로)
   - root에 흩어진 `*.docx` / `*.pdf` (paper로 분류되지 않는 것) / `*_review.md` / `*_template.*` / `*_sample.*`
3. **Output sub-folder `{name}`**: positional 명시 → 그 folder name (basename) / 자동 발견 → cwd basename 또는 task description-derived

Read input scope. Classify each file by heuristic:

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
- Cross-references useful for autopilot-draft downstream
- "intended for mode": likely autopilot-draft mode this material targets (`paper` / `presentation` / `doc` — `doc` 안 intent 라벨: rebuttal / review / report / proposal)

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
├── experiment_conventions.md       [T1] lab 사전 자료 — 모델 폴더 / config / prefix / preferred layer
├── experiment_readiness.md         [T1] lab 사전 자료 — 실험 ready 점검 (model 분리·train/eval 분리·seed 등)
├── cleanup_candidates.md           [T1] lab 사전 자료 — unused / dead branch / 주석 자국
├── similar_models.md               [T1] lab 사전 자료 — 모델 간 유사도 (lab --ref 추천 source)
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

- `autopilot-code`는 `analysis_project/code/`를 자동 인지 (code-plan에서 모듈 매핑 참조). `cleanup_candidates.md` / `experiment_readiness.md` 가 있으면 _실험 ready 정리 자리_ (cleanup + refactor + ready 정돈) input 으로 자동 사용.
- `autopilot-lab` 은 `analysis_project/code/` 의 _4 종 실험 자료_ (`experiment_conventions.md` / `experiment_readiness.md` / `cleanup_candidates.md` / `similar_models.md`) 를 매번 Step 0 에서 read — 사용자 코드베이스의 layer / prefix / config 패턴 1순위 준수. 자료 부재 시 lab 가 lightweight scan 으로 추출 후 사용자 컨펌 → 본 폴더에 저장.
- `autopilot-draft`는 form-first 3-mode (paper / presentation / doc) 에 따라:
  - `paper` → `analysis_project/paper/` (academic body 본문)
  - `presentation` → `analysis_project/paper/` + `analysis_project/doc/{matching}/formats/` (slide template)
  - `doc` → task description intent 키워드별:
    - rebuttal-response intent (응답·OpenReview·reviewer) → `analysis_project/doc/{matching}/reviewers/` + `analysis_project/paper/` (REQUIRED)
    - peer review intent (심사·review form) → `analysis_project/doc/{matching}/formats/` (REQUIRED — 부재 시 hard-fail)
    - report · proposal · generic prose intent → `analysis_project/doc/{matching}/formats/` (optional)
- `autopilot-research`는 자체 외부 검색 위주이지만, 보유 자료가 있으면 `analysis_project/paper/` 인지 가능

모든 입력은 `analysis_project/*` 또는 `research/*` 같은 `.claude_reports/` 하위 영속 산출물에서 자동 발견. family 전체가 외부 폴더를 직접 가리키는 flag 없음.

## Typical workflow

**원칙**: 분석 대상 자료(PDFs / reviewer comments / templates 등)를 _프로젝트 dir 안에_ 둔 뒤 `cd <project>` 후 호출. positional 인자 없이도 자동 발견.

```bash
cd <project_root>     # 자료를 프로젝트에 가져다 둔 후

# 1. 사전 분석 — positional 없이 (cwd 자동 발견)
/analyze-project --mode code        # 코드베이스
/analyze-project --mode paper       # cwd + papers/ / refs/ / pdfs/ 자동 grep
/analyze-project --mode doc         # cwd + docs/ / reviews/ / templates/ / reviewer_comments/ 자동 발견

# 1b. 또는 외부 폴더 override (rare)
/analyze-project --mode doc ~/external_patent_folder/   # positional = 외부 path

# 2. 후속 작업 (input은 자동 인지)
/autopilot-code --mode dev "<task>"
/autopilot-draft "<task>" --mode presentation
/autopilot-research <topic>
/autopilot-refine "<prompt>"
/autopilot-lab "<실험 한 줄>"        # ← code mode 의 4 종 실험 자료 자동 read
```
