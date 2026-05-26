---
name: autopilot-lab
description: "_빠른 실험 prototype_ entry — ML 실험·연구 hands-on (training loop·eval·ablation grid) 1순위, 일반 one-shot script (데이터 정제·변환) 부수 수용. 4 단계 (spec → scaffold → run+iterate → summary). _덮어쓰기·휘발·즉흥 다음 실험_ 의 구조적 차단: experiment 단위 폴더 강제, STORY narrative + _RUNLOG timeline 누적, 직전 실험의 summary 가 다음 실험 spec 의 input. analyze-project 가 추출한 experiment_conventions.md / similar_models.md 자동 read — 사용자 코드베이스 layer·prefix·config 패턴 1순위 준수. 정련·라이브러리화 졸업 자리는 autopilot-code 로 hand-off."
argument-hint: "<task description> [--mode ml|script|auto] [--ref <similar-model-path>] [--qa quick|light|standard|thorough|adversarial] [--from spec|scaffold|run|summary]"
---

> 산출물 폴더: `.claude_reports/experiments/` ([CONVENTIONS.md §5](../../CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) 3-tier). _RUNLOG timeline 한 자리 + experiment 단위 폴더 누적.

## Purpose — _빠른 실험 prototype_ entry

기존 _autopilot-code (정련·brownfield)_, _autopilot-spec (비코드 청사진)_, _autopilot-research (markdown 보고서)_ 의 빈 자리:

- 사용자가 _시간 쫒기는 자리에서 idea 빨리 돌려본다_
- 결과 누적 안 되어 _어제 뭘 했는지 휘발·다음 실험 즉흥_
- argparse·logger·ckpt scaffold 매번 재생산
- 사용자 코드베이스의 layer / prefix / config 패턴 무시한 채 새 layer 도입

본 skill 은 _시간 쫒기는 자리에 ceremony 를 _작게_ 넣는다_ — spec 1 화면 + summary 1 화면. _덮어쓰기·휘발·즉흥_ 의 구조적 원인을 차단.

### 자리 비교

| skill | 자리 | 산출물 |
|---|---|---|
| `autopilot-research` | 사전 조사 (외부 paper·tech·market) | markdown 보고서 |
| `analyze-project` | 코드 청사진 추출 | `analysis_project/` |
| `autopilot-spec` | 비코드 청사진 (PRD·스택·skeleton) | `specs/<name>/` |
| **`autopilot-lab`** (본 skill) | **빠른 실험 prototype (CLI 위주, hands-on)** | **`experiments/`** |
| `autopilot-code` | brownfield 정련·라이브러리화 | `plans/` 또는 `specs/<name>/dev_log/` |
| `autopilot-draft / refine` | 문서 작업 | `documents/` |

## 흐름 안에서 본 skill 의 자리

```
사전:    autopilot-research (외부) + analyze-project (코드 청사진 + 실험 컨벤션 추출)
           ↓
실험 ready 점검 (analyze-project 산출 experiment_readiness.md)
   ├─ 미흡 → autopilot-code (cleanup + refactor + ready 정리) → 다시 점검
   └─ ready ↓
청사진(옵션): autopilot-spec --mode research,cli (재현성 자리)
           ↓
실험:     autopilot-lab  ← 본 skill. 반복 호출 (idea 마다 한 폴더)
           ↓
졸업:    autopilot-code (라이브러리화·논문 코드 정리)
```

## Default Invocation Rule (메인 Claude 자동 라우팅)

본 skill 은 글로벌 [`CLAUDE.md`](../../CLAUDE.md) §6 "autopilot-* 호출 패턴" 의 _컨펌 의무_ 적용 대상.

### Trigger 신호 (자연어 발화 예시)

**ml 모드** (default — 학습·평가 실험):
- "lr 1e-3 → 3e-4 비교" / "ablation 돌려봐" / "X 데이터 baseline 돌려"
- "TF_Restormer 에서 MDTA 빼고 비교" / "loss 함수 바꿔 실험"
- "새 모델 prototype 하나 시작"

**script 모드** (one-shot 데이터·변환):
- "X 데이터셋 sample 정제" / "wav split script" / "metric 재계산"

### Default 옵션 권장값

- `--mode`: `auto` (default) — 발화·cwd 단서로 ml/script 추론. ml 우세 (사용자 자리 1순위).
- `--ref`: 자동 (analyze-project 의 `similar_models.md` 추천 가장 유사 자리). 사용자 명시 시 override.
- `--qa`: `light` (default — 실험 prototype 자리는 가벼움 우선. high-stakes 신호 시 standard 자동 상향)
- `--from`: 자동 (`_RUNLOG.md` 의 직전 실험 발견 시 컨텍스트 자동 load)

### Override 1순위 — autopilot 우회

- 단발 데이터 정제·변환 (한 줄) — `Agent(개발팀)` 직접
- 단발 plot 만 — `Agent(자료팀, mode="figure-gen")` 직접
- 정련 / 라이브러리화 / spec 정돈 — `/autopilot-code` 또는 `/autopilot-spec`
- `/autopilot-lab <args>` slash 직접 입력 — 컨펌 skip

## Language Rule
- Think and reason in English internally. Write user-facing output in Korean.
- Code identifiers, layer names, config keys stay in English.

## Argument Parsing

### --mode
- `auto` (default) — 발화·cwd 단서로 추론
- `ml` — 학습·평가 실험 (train.py / eval.py / config.yaml / ckpt / metrics)
- `script` — 한 번 돌고 끝나는 데이터 변환·정제·분석 script

### --ref <path>
참고 코드 path 명시 (예: `model/TF_Restormer`). 미명시 시 `similar_models.md` 자동 추천.

### --qa
- `quick` / `light` (default) / `standard` / `thorough` / `adversarial` — [CONVENTIONS.md §1](../../CONVENTIONS.md)
- 본 skill default 가 `light` 인 이유: 실험 prototype 은 _빠른 cycle_ 이 1순위. high-stakes 신호 (논문 결과·외부 공개) 시 사용자가 standard+ 명시 또는 메인 Claude 자동 상향.

### --from
- `spec` / `scaffold` / `run` / `summary` — 단계 재개
- 직전 실험의 `pipeline_state.yaml` 발견 시 자동 추론

## Step 0: Auto-Load Context (매번 자동 read — 사용자 재설명 부담 차단)

본 skill 의 핵심 — _사용자가 매번 상황 재설명 안 함_. 호출 자리에서 다음 자료 자동 read:

| Layer | 자료 | 누적 단위 | 자리 |
|---|---|---|---|
| **실험 컨벤션 (per-project)** | `.claude_reports/analysis_project/code/experiment_conventions.md` | 프로젝트 단위 | **1순위** — 본 프로젝트의 실제 컨벤션이 source of truth. 개별 프로젝트의 특수 사정 (외부 ref 기반 / 다른 framework / legacy 자리) 그대로 우선 |
| 사용자 일관 패턴 (cross-project) | `~/.claude/user_profile/07_coding_convention.md` | cross-project | **2순위 (default·fallback)** — per-project 부재 또는 _빈 자리_ 만 보강. 사용자 cross-project 의 model 폴더 / config / prefix / preferred layer / framework / metric 누적. 부재 시 `/analyze-user coding_convention` 권장 안내 |
| 프로젝트 timeline | `.claude_reports/experiments/_RUNLOG.md` 의 최근 5 줄 | 한 실험 = 한 줄 | 직전 실험 컨텍스트 |
| 직전 실험 상세 | 직전 실험 폴더의 `summary.md` + `STORY.md` | 한 실험 narrative | 결과·다음 후보 인용 |
| 외부 조사 | `.claude_reports/research/` 최근 산출 (있으면) | topic 별 | motivation 기반 |
| 코드 청사진 | `.claude_reports/analysis_project/code/` (있으면) | 프로젝트 단위 | baseline 파악 |
| **유사 모델** | `.claude_reports/analysis_project/code/similar_models.md` | 프로젝트 단위 | `--ref` 자동 추천 |
| Cleanup 후보 | `.claude_reports/analysis_project/code/cleanup_candidates.md` (있으면) | 프로젝트 단위 | dead code 자리 회피 |
| 실험 ready 점검 | `.claude_reports/analysis_project/code/experiment_readiness.md` (있으면) | 프로젝트 단위 | 미흡 시 _autopilot-code 권장_ 한 줄 |

### 컨벤션·ready 부재 자리 (`experiment_conventions.md` 없음)

`analyze-project --mode code` 한 번도 안 돌렸으면:
1. **Lightweight scan** 자동 — `model/*/` 폴더 ls + `config.*` sample read + 한 모델 sample read
2. 추출 draft (모델 폴더 구조 / config 메커니즘 / prefix 패턴 / preferred layer 후보) 사용자 _한 화면 컨펌_
3. yes → `analysis_project/code/experiment_conventions.md` 저장 → 본 호출 진행
4. 수정 → 사용자 직접 편집 후 진행

이후 호출은 본 파일 read-only — 매번 재추출 X.

### 실험 ready 미흡 자리

`experiment_readiness.md` 의 항목 중 ❌ 가 있으면 lab 진행 _보류_:
```
=== 실험 ready 미흡 ===
- ❌ model 단위 폴더 분리 — model/ 폴더 없음
- ❌ train.py / eval.py 분리 — main.py 한 파일에 다 박힘
- ⚠️ config 메커니즘 일관성 — argparse / yaml 혼재

권장: /autopilot-code "model/ 폴더 분리 + train/eval 분리 + config 통일" 먼저
(진행 — 미흡 무시하고 lab 시작 / autopilot-code 호출 / 중단)
```

## 코드 수정 4 원칙 (sub-agent 호출 자리에 매번 prepend)

`analysis_project/code/experiment_conventions.md` (**1순위 — per-project 가 source of truth**) + `~/.claude/user_profile/07_coding_convention.md` (2순위 — cross-project default, per-project 부재·빈 자리만 보강) 의 _preferred layer / config 메커니즘 / prefix 패턴_ 을 source 로 다음 4 원칙을 개발팀 _new-lib_ mode prompt 에 매번 prepend. _충돌 자리는 per-project 우선_ — 본 프로젝트의 실제 컨벤션 침범 X.

1. **최소 수정** — 기존 모델 폴더 복사 후 변형 (`--ref` 또는 `similar_models.md` 추천). 새 layer 도입 default X
2. **원래 layer 1순위** — `experiment_conventions.md` 의 _preferred layer_ list 가 1순위. 새 layer 도입은 _명시 컨펌_ 필요
3. **마이너 변경 = config** — model.py 직접 수정 X, `config.yaml` 가능한 자리는 config 로
4. **변형 prefix** — fine-tuning 변형은 `experiment_conventions.md` 의 prefix 패턴 (예: `_ft01_`·`_ft02_`) 따라 base 파일 옆에 둠. 새 base 는 새 모델 폴더

## Procedure — 4 단계

### Step 1: spec (1 화면)

**1-1. Step 0 컨텍스트 자동 read** — 위 8 자료. 사용자 보고는 _한 줄 요약_ ("직전 실험: lr_1e-3 (val PSNR 28.4), 컨벤션 ready ✓, 유사 모델: TF_Restormer").

**1-2. 사용자 발화 → spec draft** — 메인 Claude 가 자동 컨텍스트 + 사용자 _이번에 뭘 바꿀지 한 줄_ → spec draft.

**1-3. 한 화면 컨펌**:

```
=== Experiment Spec ===
프로젝트:     <name>
실험 이름:    <date>_<slug> (예: 2026-05-26_lr_sweep)
참고 모델:    model/TF_Restormer (similar_models.md 추천)
mode:        ml
motivation:  <자동 요약 — 직전 실험에서 도출>
이번 시도:   <한 줄 — 사용자 발화 기반>

데이터셋:     <auto from ref>
metric:      <auto from ref — PSNR / SSIM / SI-SDR / 등>
ablation grid: <자동 또는 사용자 명시>

실험 ready:  ✓ (또는 ❌ — 위 보류 흐름)
컨벤션 ready: ✓
연구팀 plan-review: <on / off — 직전 실험과 겹침·motivation 점검>

이대로 진행? (진행 / 수정 / 중단)
```

**1-4. 연구팀 _plan-review_ 호출 (qa standard+ 자리만)**:

```
Agent(subagent_type="연구팀"):
  "Mode: plan-review (실험 자리).
   직전 실험 RUNLOG: {_RUNLOG.md 최근 5 줄}
   현 spec: {experiment_spec.md draft}
   research 산출 (있으면): {research_dir}

   점검:
   - 이전 실험과 _중복_ 자리? (같은 ablation 이미 돌렸는지)
   - motivation 이 직전 결과 흐름과 정합?
   - ablation grid 가 _하나 변경 변수_ 원칙 따르는지 (controlled experiment)
   - 예상 metric 범위가 직전 baseline 대비 합리적?

   메모: experiment_spec.md 안에 `<!-- review: ... -->` 형태로.
   Return: 메모 추가된 파일 + 한국어 요약 한 줄."
```

quick / light 자리는 본 review skip.

**1-5. spec 저장** — `experiments/{date}_{slug}/experiment_spec.md` (1 화면, 7-12 줄).

### Step 2: scaffold (개발팀 _new-lib_)

**2-1. 참고 모델 결정** — `--ref` 명시 또는 `similar_models.md` 추천. 사용자 _컨펌 한 줄_ ("model/TF_Restormer 참고 — ok?").

**2-2. 개발팀 _new-lib_ 호출**:

```
Agent(subagent_type="개발팀", mode="new-lib"):
  "Mode: scaffold for experiment prototype.
   참고 모델: {ref_path}
   실험 폴더: experiments/{date}_{slug}/
   spec: experiments/{date}_{slug}/experiment_spec.md

   ## 코드 수정 4 원칙 (필수 준수)
   1. 최소 수정 — ref 모델 복사 후 변형, 새 layer 도입 default X
   2. 원래 layer 1순위 — experiment_conventions.md preferred layer 사용
   3. 마이너 변경 = config — model.py 수정 X, config.yaml 변경
   4. 변형 prefix — fine-tuning 변형은 base 옆에 _ft01_ 식

   ## experiment_conventions.md 의 preferred layer
   {preferred_layer_list 인용}

   ## scaffold 산출물
   - experiments/{date}_{slug}/train.py (ref 의 train.py 복사 + 변형 자리만 수정)
   - experiments/{date}_{slug}/eval.py (ref 복사)
   - experiments/{date}_{slug}/config.yaml (ref 복사 + 이번 실험 ablation 자리 표기)
   - 또는 base 모델 폴더에 _ft01_ prefix 파일 (사용자 컨벤션 따라)

   ## 안 함
   - 새 layer 도입
   - ref 모델 폴더의 _이미 사용 중인 layer_ 변경
   - 라이브러리화·정련 (이건 autopilot-code 영역)

   Return: 생성 파일 list + 한국어 요약 (어떤 자리 변형했는지)."
```

**2-3. 한 화면 컨펌**:

```
=== Scaffold 완료 ===
- experiments/{date}_{slug}/train.py
- experiments/{date}_{slug}/eval.py
- experiments/{date}_{slug}/config.yaml
- (또는 model/<base>/_ft01_<variant>.py)

변경 자리: <한 줄>

(진행 — run / 수정 — scaffold 다시 / 중단)
```

### Step 3: run + iterate (사용자 직접 또는 테스트팀 smoke)

**3-1. run 명령 안내**:

```
실행:
  cd experiments/{date}_{slug}
  python train.py --config config.yaml
또는 사용자가 cluster 에 submit.
```

본 skill 은 _실행 자체 자동 X_ — 사용자 환경 (cluster·GPU·queue) 가변. 사용자 직접 실행 후 _이어서_ 보고.

**3-2. 테스트팀 _smoke_ (옵션, 사용자 발화 시)**:

```
"smoke 1 epoch 돌려봐" 같은 발화 자리:
Agent(subagent_type="테스트팀"):
  "Mode: smoke (1 epoch / minimum batch).
   target: experiments/{date}_{slug}/train.py
   목적: scaffold 의 _basic 동작_ 검증 (data load / forward / backward / loss / optimizer step).
   실제 metric 수렴 검증 X.
   Return: 통과·실패 + 첫 epoch loss·시간."
```

**3-3. 수렴 안 됨 → 품질관리팀 _ml-debug_ escalate (사용자 발화 시)**:

```
"loss 가 안 떨어져" / "NaN" / "수렴 이상" 발화 자리:
Agent(subagent_type="품질관리팀", mode="ml-debug"):
  "Mode: ml-debug.
   target: experiments/{date}_{slug}/
   현상: {사용자 발화 + 사용 가능 log}
   참고: experiment_spec.md
   
   점검 axis:
   - data: shape / range / NaN / class balance
   - model: init / freeze / grad flow
   - loss: scale / sign / numerical stability
   - optim: lr / weight decay / warmup
   - infra: batch size / device / mixed precision
   
   Return: 가장 가능성 높은 root cause 1-2 + 검증 명령."
```

**3-4. plot / 결과 시각화 → 자료팀 _figure-gen_ (사용자 발화 시)**:

```
"결과 plot 그려줘" / "ablation 표 정리" 발화 자리:
Agent(subagent_type="자료팀", mode="figure-gen"):
  "Mode: figure-gen.
   target: experiments/{date}_{slug}/runs/*/metrics.json
   spec: 사용자 코드베이스의 figure 컨벤션 (project_user_paper_figure_style 메모리 또는 cwd 의 기존 plot 참고)
   
   Output: experiments/{date}_{slug}/figures/{plot_name}.{png,pdf}."
```

### Step 4: summary (1 화면 + RUNLOG 갱신)

**4-1. 결과 정리** — 사용자가 "결과 정리해" 발화 또는 메인 Claude 가 _run 종료 보고_ 인지:

```
=== Summary draft ===
실험:        {date}_{slug}
시도:        <spec 의 이번 시도 한 줄>
결과:        <metric 표 — best / final / 차이>
ablation:    <표 — 변수 × metric>
관찰:        <2-3 bullet>
다음 후보:    <한 줄 — 다음 실험 시드>

이대로 저장? (저장 / 수정 / 중단)
```

**4-2. 저장 — 세 파일 자동 갱신**:

- `experiments/{date}_{slug}/summary.md` — 위 한 화면
- `experiments/{date}_{slug}/STORY.md` — narrative 추가 (motivation·이전 정리·이번 시도·결과·다음 후보 한 단락)
- `.claude_reports/experiments/_RUNLOG.md` — 한 줄 append:
  ```
  | 2026-05-26 | lr_sweep | TF_Restormer base, lr 1e-3→3e-4 | val PSNR 28.4→28.7 (+0.3) | 다음: warmup 1k step 추가 |
  ```

**4-3. 연구팀 _research-survey_ (옵션, qa standard+ + 사용자 발화 시)**:

```
"결과를 기존 paper 와 비교해줘" 발화 자리:
Agent(subagent_type="연구팀", mode="research-survey"):
  "Mode: research-survey (실험 결과 자리).
   결과: experiments/{date}_{slug}/summary.md
   사전 자료: .claude_reports/research/ + analysis_project/paper/
   
   비교 axis:
   - 본 실험의 metric vs 기존 paper baseline
   - 본 실험의 변경 자리가 paper 어디 자리와 닿나
   - 본 실험의 관찰이 paper 의 주장·반박과 어떤 자리
   
   Return: 비교 표 + 한국어 한 단락 요약 (summary.md 에 ## 기존 paper 와의 비교 섹션 추가)."
```

## 산출물 구조

```
.claude_reports/experiments/
├── _RUNLOG.md                      [T1] timeline (한 실험 = 한 줄, 모든 실험 누적)
├── {date}_{slug}/                  ← 한 실험 = 한 폴더
│   ├── pipeline_state.yaml         [T1] --from 재개용
│   ├── STORY.md                    [T1] narrative 누적 (motivation·이전·이번·결과)
│   ├── experiment_spec.md          [T1] 1 화면 spec
│   ├── summary.md                  [T1] 결과·다음 후보
│   ├── train.py / eval.py / config.yaml  [T1] scaffold
│   ├── runs/                       [T2] 각 run 의 결과
│   │   └── run-001/
│   │       ├── metrics.json
│   │       ├── ckpt/
│   │       └── log.txt
│   ├── figures/                    [T2] plot (자료팀 산출)
│   └── _internal/                  [T3]
│       ├── plan_reviews/           ← 연구팀 plan-review log
│       └── debug_reviews/          ← 품질관리팀 ml-debug log
```

**또는** _코드 컨벤션이 model/{name}/ 단위_ 자리 (TF_Restormer 등):

```
model/
├── TF_Restormer/                   ← base
│   ├── model.py
│   ├── config.yaml
│   ├── _ft01_lr_sweep.py           ← variation (lab 가 생성)
│   └── _ft02_no_mdta.yaml
└── ...

.claude_reports/experiments/
├── _RUNLOG.md
└── {date}_{slug}/
    ├── experiment_spec.md
    ├── summary.md
    ├── STORY.md
    ├── runs/                       ← 실험 log·ckpt·metric
    └── _internal/
```

`experiment_conventions.md` 의 prefix 패턴이 _model 폴더 내 variation_ 자리면 후자, _별도 폴더_ 자리면 전자. 사용자 코드베이스 컨벤션 1순위.

## Pipeline state

`experiments/{date}_{slug}/pipeline_state.yaml`:

```yaml
pipeline: autopilot-lab
slug: <slug>
date: <date>
mode: ml                       # ml | script
ref: model/TF_Restormer        # 참고 자리
qa_level: light
phases:
  spec: done
  scaffold: done
  run: in_progress             # 사용자 직접 실행 자리
  summary: pending
last_updated: <timestamp>
```

## CONFIRM Gate 응답 분기 (모든 Gate 공통)

| 응답 | 처리 |
|---|---|
| **진행** | 다음 단계 |
| **수정** | 현 단계 refine (`_internal/refine_v{N}.md`) |
| **back-jump** | 이전 단계 재실행 |
| **중단** | 멈춤, `pipeline_state.yaml` 보존 |

발화 모호 시 옵션 다시 물음 (임의 추측 X).

## Forbidden Zones (명시 요청 없이 X)

- 새 layer 도입 (preferred layer list 외)
- ref 모델 폴더 직접 수정 (variation 만, base 보존)
- 라이브러리화·module 정련 (autopilot-code 영역)
- PRD·스택 결정 (autopilot-spec 영역)
- 실험 자동 실행 (사용자 환경·queue 가변 — 명령만 안내)
- ckpt·log destructive 삭제 (`_internal/` 외)

## 졸업 자리 — autopilot-code 로 hand-off

lab 의 산출물이 _되는 prototype_ 까지 도달하면:
- 라이브러리화·논문 코드 정리 → `/autopilot-code "X 라이브러리화"`
- PRD 정돈 → `/autopilot-spec --mode research,cli`

lab 자체는 누적되어도 _ceiling 1 화면 (summary)_ 이라 난잡해지기 어렵게 설계 — 라이브러리화 의도가 생기면 autopilot-code 로 _졸업_.

## Update memory

- 사용자 자주 만나는 ablation 패턴
- preferred layer 확장 자리
- 자주 만나는 실험 ready 미흡 자리
- 자주 만나는 ml-debug root cause

## Return Format

```
.claude_reports/experiments/{date}_{slug}/ -- ✅ {phase} 단계 완료
```

다음 단계 안내:
- spec → "scaffold 진행할까요?"
- scaffold → "실행 명령: cd experiments/{date}_{slug} && python train.py --config config.yaml"
- run 진행 → "결과 보고 받으면 summary 정리합니다"
- summary → "_RUNLOG.md 한 줄 추가. 다음 실험: <한 줄>"

## Examples

### 예시 1 — lr sweep (반복 실험)

```
사용자: lr 1e-3 → 3e-4 비교
→ Step 0: _RUNLOG 최근 5 줄 read, similar_models 의 TF_Restormer 자동 추천
→ Step 1: spec draft (motivation: 직전 baseline 의 val 28.4 에서 lr 영향 점검)
   → 컨펌
→ Step 2: 개발팀 new-lib
   → model/TF_Restormer/_ft01_lr_3e-4.yaml 생성 (config 만 변경, model.py 손 안 댐)
   → 컨펌
→ Step 3: 사용자 실행 — python train.py --config _ft01_lr_3e-4.yaml
→ Step 4: 결과 보고 → summary draft → 컨펌 → _RUNLOG 갱신
```

### 예시 2 — ablation (MDTA 제거)

```
사용자: TF_Restormer 에서 MDTA 빼고 비교
→ Step 0: 직전 lr_sweep 의 best config 자동 인용
→ Step 1: spec — _ft02_no_mdta variant
→ Step 2: 개발팀 — preferred layer (MDTA / GDFN / LayerNorm2d) 중 MDTA 만 standard MHA 로 교체
   → 컨벤션 4 원칙 prepend — _새 layer 도입 X_, MHA 는 standard PyTorch 자리
→ Step 3: 사용자 실행
→ Step 4: summary — "MDTA 제거 시 val 28.7 → 28.1 (-0.6) — MDTA 기여 +0.6 검증"
```

### 예시 3 — 데이터 정제 one-shot (script 모드)

```
사용자: clean wav 에서 silence cut
→ Step 1: spec — script 모드, motivation: 다음 실험 input
→ Step 2: 개발팀 — scripts/silence_cut.py 한 파일 (model 폴더 자리 X)
→ Step 3: 사용자 실행
→ Step 4: summary — "X 시간 wav → Y 시간 (Z% cut), 다음 실험에 사용"
```

## Task
$ARGUMENTS
