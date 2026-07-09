# Mode `code`

Analyzes the codebase and produces module-level documentation.

## Phase 0: Incremental vs Full 분기 (자동)

호출 자리에서 `<artifact-root>/analysis_project/code/_last_run.yaml` 검사:

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
Write analysis results as topic-separated md files in `<artifact-root>/analysis_project/code/`.
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
- `<artifact-root>/analysis_project/code/` document list with coverage table
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
- **Model role**: Light QA using fast reviewer (Claude adapter: sonnet) — documentation is not as critical as code changes.
- Reviews logged to `<artifact-root>/analysis_project/code/_internal/reviews/`.

---
