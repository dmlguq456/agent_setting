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

모든 입력은 `analysis_project/*` 또는 `research/*` 같은 `<artifact-root>/` 하위 영속 산출물에서 자동 발견. family 전체가 외부 폴더를 직접 가리키는 flag 없음.

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
