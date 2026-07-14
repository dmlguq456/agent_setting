---
# GENERATED METADATA — edit harness-manifest.json, then run tools/generate.py.
name: analyze-project
description: "Use when invoking the portable analyze-project capability. Upfront analysis that structures primary code, paper, and document materials for downstream work."
argument-hint: "[--mode code|paper|doc] [<scope/target/input-folder>] [--skip-qa]"
metadata:
  group: pre
  fam: pre
  modes: ["code", "paper", "doc"]
  blurb: "Upfront analysis that structures primary code, paper, and document materials for downstream work."
---

# analyze-project

사전조사 분석 entry. 코드·논문·문서 primary 자료를 구조화해 다운스트림(autopilot-code / autopilot-lab / autopilot-draft / autopilot-research) 입력으로 만든다. 이 파일은 라우터와 mode 계약만 담고, mode별 Phase 상세 절차·산출물 템플릿은 필요할 때 아래 reference를 Read 한다.

> Caller note: this skill performs deep analysis. Callers should invoke at `high` or `xhigh` effort when the runtime supports it; at lower effort, depth narrows automatically.

> **산출물 폴더 컨벤션**: [CONVENTIONS.md §5](../../core/CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) (3-tier T1/T2/T3). 본 skill의 산출물은 `<artifact-root>/analysis_project/{code,paper,doc}/` 하위. 각 mode의 main outputs는 root, raw scan log/QA reviews는 `_internal/`.

> **Workspace assumption**: Claude는 프로젝트 루트에서 실행됨. `<artifact-root>/`는 현재 dir에 생성. 본 skill의 input scope (코드 / PDFs / doc materials)도 현재 dir 또는 그 하위 폴더 기준.
> `<artifact-root>` 해석·치환(`.agent_reports` 우선, legacy `.claude_reports` fallback): [CONVENTIONS §5.1](../../core/CONVENTIONS.md#51-workspace-assumption-전제).

## Language Rule
- Write canonical technical analysis in English for code/paper modes. In doc
  mode, follow the explicit target audience or artifact language; absent one,
  use the audience-language-first artifact rule from
  `<agent-home>/roles/response-policy.md`.

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
| Neither / unclear | ask user: "code, paper, doc 중 어느 mode인가요?" — adapter pause/autonomy rule 적용(Claude Code: [CLAUDE.md](../../adapters/claude/CLAUDE.md) §2) (ScheduleWakeup 10-15분 동시 호출; 답 없으면 cwd 신호 강한 쪽으로 자율 진행) |

> **`paper` mode is never auto-selected** — paper analysis requires explicit `--mode paper` because PDF presence alone is ambiguous (could be reviewer comments, templates, etc. for doc mode). The boundary between paper and doc is genuinely fuzzy in the wild.

## Output Directories

| Mode | Output | Scoping |
|---|---|---|
| code | `<artifact-root>/analysis_project/code/` | flat (project-level, accumulates over time) |
| paper | `<artifact-root>/analysis_project/paper/` | flat (project's paper collection accumulates) |
| doc | `<artifact-root>/analysis_project/doc/{name}/` | per-task subdir |

`{name}` for doc mode: derived from input folder basename (positional arg) or cwd basename (default — when positional 생략, 즉 자동 발견 모드). 예: `--mode doc` (positional 없이) within `/.../tf_restormer/` cwd → `analysis_project/doc/tf_restormer/`. 명시 override: `--mode doc tf_restormer_patent` → `analysis_project/doc/tf_restormer_patent/`.

---

## Mode Overview

3-mode 공통 흐름: input 발견 → 분석(직접 수행 또는 연구팀 위임) → `<artifact-root>/analysis_project/` 구조화 산출 → 검증. 각 mode의 Phase별 절차·프롬프트·템플릿 전문은 해당 reference에 verbatim 보존.

- **code** — codebase 모듈 분석 → topic별 md + Interface Reference + CLAUDE.md 갱신 + lab 사전 자료 4종(`experiment_conventions` / `experiment_readiness` / `cleanup_candidates` / `similar_models`). Phase 0에서 `_last_run.yaml` 검사로 incremental vs full 자동 분기, Phase 5 QA(품질관리팀). → `references/mode-code.md`
- **paper** — reference PDF·자기 논문 분석을 연구팀에 위임. 목적 분기: (A) reference-survey(인용·grounding용 외부 PDF) / (B) own-paper review(작성 중 main.tex — `00_self_paper_analysis.md`가 MAIN 산출). 통합 `00_overview_and_constraints.md`가 최중요 산출. → `references/mode-paper.md`
- **doc** — 문서 작성 자료(reviewer comments / templates / samples / misc) 분류 후 연구팀 위임 분석, per-task `doc/{name}/` 산출 + `00_overview.md` 인벤토리. → `references/mode-doc.md`

## Reference Index

| 파일 | 언제 로드 (의무) | 내용 |
|---|---|---|
| `references/mode-code.md` | `--mode code` 실행 시 (필수) | Phase 0(Incremental vs Full 분기·`_last_run.yaml` schema) · 1(Codebase Analysis) · 2(Documentation·Interface Reference 필수 섹션) · 3(CLAUDE.md) · 3.5(lab 사전 자료 4종: `experiment_conventions`/`experiment_readiness`/`cleanup_candidates`/`similar_models` 템플릿) · 4(Coverage 검증) · 5(QA Verification) |
| `references/mode-paper.md` | `--mode paper` 실행 시 (필수) | 연구팀 위임 프롬프트 전문(Inputs, §0 own-paper 완전 분석 / §1-6 reference-survey, `00_overview_and_constraints.md` 구조) + Post-Analysis |
| `references/mode-doc.md` | `--mode doc` 실행 시 (필수) | Phase 1(input scope resolution·분류 heuristic 표) · 2(Per-Category Analysis 위임 프롬프트 — reviewers/formats/samples/misc, `00_overview.md`) · 3(Verify) |
| `references/outputs-and-integration.md` | 산출물 구조 확정·후속 skill 연계 판단 자리 | mode별 standard output structure, cross-skill integration(autopilot-code·lab·draft·research 연계 규칙), typical workflow |
