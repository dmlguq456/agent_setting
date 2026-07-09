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
- Existing paper docs: <artifact-root>/analysis_project/paper/*.md
- Existing code docs: <artifact-root>/analysis_project/code/*.md (for paper-code mapping)
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
For each paper, create or update its summary file in `<artifact-root>/analysis_project/paper/` (agent decides filenames).
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
