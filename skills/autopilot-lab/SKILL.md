---
name: autopilot-lab
description: "_빠른 실험 prototype_ entry — 무거운 학습은 사용자가 돌리고, lab 은 그 앞뒤를 돕는다. 2 모드: **setup** (학습 실험 세팅 — spec → scaffold → 실행 명령 안내) / **eval** (학습 완료 ckpt 평가·분석 — metric·ablation·paper 비교·plot). 확장 케이스(기존 세팅에 새 데이터로 재평가·추가 fine-tuning)는 `--parent <slug>` 계보로 흡수 — 새 모드 없음 (fine-tune=setup --parent 로 새 config 갈래, 재평가=eval --parent). experiment 단위 폴더 강제 + STORY narrative + _RUNLOG timeline (⏳대기→✅완료 상태 + 부모 링크) 누적 → 덮어쓰기·휘발·즉흥 차단. analyze-project 의 experiment_conventions.md / similar_models.md 자동 read — 사용자 코드베이스 layer·prefix·config 패턴 1순위. 정련·라이브러리화 졸업은 autopilot-code."
argument-hint: "<task description> [--mode setup|eval|auto] [--parent <slug>] [--ref <similar-model-path>] [--qa quick|light|standard|thorough|adversarial] [--from spec|scaffold|run|eval|summary]"
---

> 산출물 폴더: `.claude_reports/experiments/` ([CONVENTIONS.md §5](../../CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) 3-tier). _RUNLOG timeline 한 자리 + experiment 단위 폴더 누적.

## Purpose — _빠른 실험 prototype_ entry

기존 _autopilot-code (정련·brownfield)_, _autopilot-spec (비코드 청사진)_, _autopilot-research (markdown 보고서)_ 의 빈 자리:

- 사용자가 _시간 쫓기는 자리에서 idea 빨리 돌려본다_
- 결과 누적 안 되어 _어제 뭘 했는지 휘발·다음 실험 즉흥_
- argparse·logger·ckpt scaffold 매번 재생산
- 사용자 코드베이스의 layer / prefix / config 패턴 무시한 채 새 layer 도입

본 skill 은 _시간 쫓기는 자리에 ceremony 를 _작게_ 넣는다_ — spec 1 화면 + summary 1 화면. _덮어쓰기·휘발·즉흥_ 의 구조적 원인을 차단.

**핵심 전제** — _무거운 학습·평가 compute 는 사용자 환경(cluster·GPU·queue)에서 사용자가 직접 돌린다._ lab 은 실행 자체를 자동화하지 않는다. lab 의 역할은 학습 _앞_ (세팅·scaffold·실행 명령) 과 _뒤_ (평가·분석·기록) 를 도와 한 실험을 _남게_ 만드는 것.

### 자리 비교

| skill | 자리 | 산출물 |
|---|---|---|
| `autopilot-research` | 사전 조사 (외부 paper·tech·market) | markdown 보고서 |
| `analyze-project` | 코드 청사진 추출 | `analysis_project/` |
| `autopilot-spec` | 비코드 청사진 (PRD·스택·skeleton) | `specs/<name>/` |
| **`autopilot-lab`** (본 skill) | **빠른 학습 실험 prototype (setup·eval, hands-on)** | **`experiments/`** |
| `autopilot-code` | brownfield 정련·라이브러리화·_단발 데이터 script_ | `plans/` 또는 `specs/<name>/dev_log/` |
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
실험:     autopilot-lab  ← 본 skill. 한 실험 = setup → [사용자 학습] → eval
           ↓               (확장: --parent 로 부모 실험 이어가기)
졸업:    autopilot-code (라이브러리화·논문 코드 정리)
```

## 모드 — 한 실험의 lifecycle

한 실험의 전체 흐름 = **setup (lab)** → [사용자가 학습 실행] → **eval (lab)**. 두 번의 lab 호출이 _대기·완료_ 2-beat 로 `_RUNLOG` 한 줄을 채운다.

| 모드 | 자리 | 하는 일 | 산출물 / 상태 |
|---|---|---|---|
| **setup** | 학습 _전_ | spec(뭘 학습·ablation) → scaffold(ref 또는 부모 ckpt 에서 train/eval/config) → 실행 명령 안내 | scaffold 코드 + `_RUNLOG` ⏳ 대기 |
| **eval** | 학습 _후_ | eval spec(ckpt·데이터·metric) → eval 실행 안내 → 분석(metric·ablation·paper 비교·plot) → summary | summary + `_RUNLOG` ✅ 완료 |

### 확장 — `--parent <slug>` 계보 (새 모드 없이 흡수)

기존 실험을 _부모_ 로 이어가는 두 케이스:

| 케이스 | 호출 | 의미 |
|---|---|---|
| 기존 세팅 + **새 평가 데이터로 재평가** | `eval --parent <slug>` | 학습 X — 부모 ckpt 를 새 데이터에 평가만 |
| 기존 세팅 + **새 학습 데이터로 fine-tune 후 재평가** | `setup --parent <slug>` → [학습] → `eval` | fine-tune = _학습_ = setup. 단 ref 가 아니라 _부모 ckpt 에서 이어서_ scaffold |

부모 링크는 `_RUNLOG` · `STORY.md` · `pipeline_state.yaml` 에 남아 timeline 에 _실험 계보_ (baseline → ft01 → ft01+newdata …) 가 보인다.

> **script(단발 데이터 변환·정제) 는 lab 모드 아님** — one-shot 유틸은 `Agent(개발팀)` 직접 또는 `/autopilot-code`. lab 은 _학습 실험_ 에 집중.

## Default Invocation Rule (메인 Claude 자동 라우팅)

본 skill 은 글로벌 [`CLAUDE.md`](../../CLAUDE.md) §6 "autopilot-* 호출 패턴" 의 _컨펌 의무_ 적용 대상.

### Trigger 신호 (자연어 발화 예시)

**setup 모드** (학습 _전_ 세팅):
- "lr 1e-3 → 3e-4 비교" / "ablation 돌려봐" / "X 데이터 baseline 돌려"
- "TF_Restormer 에서 MDTA 빼고 학습" / "loss 함수 바꿔 실험" / "새 모델 prototype 하나 시작"

**eval 모드** (학습 _후_ 평가·분석):
- "이 ckpt 평가해" / "결과 정리·분석해" / "test set 성능 보자" / "기존 paper 와 비교해줘"

**계보 (`--parent`)**:
- "그 모델에 newdata 추가해서 fine-tune" → `setup --parent <직전/지정 slug>`
- "그 모델 새 test set 으로 평가" → `eval --parent <slug>`

### Default 옵션 권장값

- `--mode`: `auto` (default) — 발화로 setup/eval 추론. 학습 동사("돌려/학습/ablation") → setup, 평가 동사("평가/분석/비교") → eval. ckpt 존재 + 평가 발화 → eval.
- `--parent`: 자동 — _이어가는 발화_ ("거기서·그 모델에·추가로") + 직전 `_RUNLOG` 실험 발견 시 그 slug 추정. 사용자 명시 override.
- `--ref`: 자동 (`similar_models.md` 추천 가장 유사 자리). setup `--parent` 자리는 ref 대신 부모 ckpt.
- `--qa`: `light` (default — 실험 prototype 빠른 cycle. high-stakes 신호(논문 결과·외부 공개) 시 standard 자동 상향)
- `--from`: 자동 (`pipeline_state.yaml` / `_RUNLOG.md` 직전 실험 발견 시 컨텍스트 자동 load)

### Override 1순위 — autopilot 우회

- 단발 데이터 정제·변환·script (한 줄) — `Agent(개발팀)` 직접 또는 `/autopilot-code` (lab 모드 아님)
- 단발 plot 만 — `Agent(자료팀, mode="figure-gen")` 직접
- 정련 / 라이브러리화 / spec 정돈 — `/autopilot-code` 또는 `/autopilot-spec`
- `/autopilot-lab <args>` slash 직접 입력 — 컨펌 skip

## Language Rule
- Think and reason in English internally. Write user-facing output in Korean.
- Code identifiers, layer names, config keys stay in English.

## Argument Parsing

### --mode
- `auto` (default) — 발화로 setup/eval 추론
- `setup` — 학습 실험 세팅 (spec → scaffold → 실행 명령 안내). 학습은 사용자가 실행
- `eval` — 학습 완료 ckpt 평가·분석 (eval spec → 실행 안내 → 분석 → summary)

### --parent <slug>
이어갈 부모 실험. 부모 폴더의 `summary.md` / `STORY.md` / `config` / ckpt path 자동 read.
- `setup --parent <slug>` — 부모 ckpt 에서 이어 학습 (fine-tuning). ref baseline 대신 부모 자산 사용
- `eval --parent <slug>` — 부모 ckpt 를 (새) 데이터에 평가. 학습 없음

### --ref <path>
참고 코드 path 명시 (예: `model/TF_Restormer`). 미명시 시 `similar_models.md` 자동 추천. setup `--parent` 자리는 무시 (부모 ckpt 우선).

### --qa
- `quick` / `light` (default) / `standard` / `thorough` / `adversarial` — [CONVENTIONS.md §1](../../CONVENTIONS.md)
- 본 skill default 가 `light` 인 이유: 실험 prototype 은 _빠른 cycle_ 이 1순위. high-stakes 신호(논문 결과·외부 공개) 시 사용자가 standard+ 명시 또는 메인 Claude 자동 상향.

### --from
- setup 모드: `spec` / `scaffold` / `run` — 단계 재개
- eval 모드: `eval` / `summary` — 단계 재개
- `pipeline_state.yaml` 발견 시 자동 추론

## Step 0: Auto-Load Context (매번 자동 read — 사용자 재설명 부담 차단)

본 skill 의 핵심 — _사용자가 매번 상황 재설명 안 함_. 호출 자리에서 다음 자료 자동 read:

| Layer | 자료 | 누적 단위 | 자리 |
|---|---|---|---|
| **실험 컨벤션 (per-project)** | `.claude_reports/analysis_project/code/experiment_conventions.md` | 프로젝트 단위 | **1순위** — 본 프로젝트의 실제 컨벤션이 source of truth. 개별 프로젝트의 특수 사정(외부 ref 기반 / 다른 framework / legacy 자리) 그대로 우선 |
| 사용자 일관 패턴 (cross-project) | `~/.claude/user_profile/07_coding_convention.md` | cross-project | **2순위 (default·fallback)** — per-project 부재 또는 _빈 자리_ 만 보강. 부재 시 `/analyze-user coding_convention` 권장 안내 |
| 프로젝트 timeline | `.claude_reports/experiments/_RUNLOG.md` 의 최근 5 줄 | 한 실험 = 한 줄 | 직전 실험 컨텍스트 + ⏳ 대기/✅ 완료 상태 |
| 직전 실험 상세 | 직전 실험 폴더의 `summary.md` + `STORY.md` | 한 실험 narrative | 결과·다음 후보 인용 |
| **부모 실험** (`--parent` 자리) | 부모 폴더의 `summary.md` / `STORY.md` / `config` / ckpt path | 한 실험 | fine-tune base 또는 재평가 대상 |
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

### 실험 ready 미흡 자리 (setup 모드)

`experiment_readiness.md` 의 항목 중 ❌ 가 있으면 setup 진행 _보류_:
```
=== 실험 ready 미흡 ===
- ❌ model 단위 폴더 분리 — model/ 폴더 없음
- ❌ train.py / eval.py 분리 — main.py 한 파일에 다 박힘
- ⚠️ config 메커니즘 일관성 — argparse / yaml 혼재

권장: /autopilot-code "model/ 폴더 분리 + train/eval 분리 + config 통일" 먼저
(진행 — 미흡 무시하고 setup 시작 / autopilot-code 호출 / 중단)
```

## 코드 수정 4 원칙 (sub-agent 호출 자리에 매번 prepend)

`analysis_project/code/experiment_conventions.md` (**1순위 — per-project 가 source of truth**) + `~/.claude/user_profile/07_coding_convention.md` (2순위 — cross-project default, per-project 부재·빈 자리만 보강) 의 _preferred layer / config 메커니즘 / prefix 패턴_ 을 source 로 다음 4 원칙을 개발팀 _new-lib_ mode prompt 에 매번 prepend. _충돌 자리는 per-project 우선_ — 본 프로젝트의 실제 컨벤션 침범 X.

1. **최소 수정** — 기존 모델 폴더 복사 후 변형 (`--ref` 또는 `similar_models.md` 추천). 새 layer 도입 default X
2. **원래 layer 1순위** — `experiment_conventions.md` 의 _preferred layer_ list 가 1순위. 새 layer 도입은 _명시 컨펌_ 필요
3. **마이너 변경 = config** — model.py 직접 수정 X, `config.yaml` 가능한 자리는 config 로
4. **변형 prefix** — fine-tuning 변형은 `experiment_conventions.md` 의 prefix 패턴 (예: `_ft01_`·`_ft02_`) 따라 base 파일 옆에 둠. 새 base 는 새 모델 폴더

---

# Procedure

전체 = **setup** → [사용자 학습] → **eval**. `--mode auto` 면 발화로 분기. 각 모드는 독립 호출이고 `pipeline_state.yaml` 에 상태 누적.

## ━━━ setup 모드 ━━━ (학습 전 세팅)

### S1: spec (1 화면)

**S1-1. Step 0 컨텍스트 자동 read** — 위 자료. 사용자 보고는 _한 줄 요약_ ("직전 실험: lr_1e-3 (val PSNR 28.4), 컨벤션 ready ✓, 유사 모델: TF_Restormer"). `--parent` 면 부모 결과·config 도 한 줄 인용.

**S1-2. 사용자 발화 → spec draft** — 자동 컨텍스트 + 사용자 _이번에 뭘 바꿀지 한 줄_ → spec draft.

**S1-3. 한 화면 컨펌**:

```
=== Experiment Spec (setup) ===
프로젝트:     <name>
실험 이름:    <date>_<slug> (예: 2026-05-26_lr_sweep)
mode:        setup
참고:        model/TF_Restormer (similar_models.md 추천)
             또는 parent: <slug> (fine-tune base — ckpt 이어서)
motivation:  <자동 요약 — 직전/부모 실험에서 도출>
이번 시도:   <한 줄 — 사용자 발화 기반>

데이터셋:     <auto from ref / parent + (fine-tune 면) 추가 데이터>
metric:      <auto — PSNR / SSIM / SI-SDR / 등>
ablation grid: <자동 또는 사용자 명시>

실험 ready:  ✓ (또는 ❌ — 위 보류 흐름)
컨벤션 ready: ✓
연구팀 plan-review: <on / off>

이대로 진행? (진행 / 수정 / 중단)
```

**S1-4. 연구팀 _plan-review_ 호출 (qa standard+ 자리만)**:

```
Agent(subagent_type="연구팀"):
  "Mode: plan-review (실험 자리).
   직전 실험 RUNLOG: {_RUNLOG.md 최근 5 줄}
   현 spec: {experiment_spec.md draft}
   research 산출 (있으면): {research_dir}

   점검:
   - 이전 실험과 _중복_ 자리? (같은 ablation 이미 돌렸는지 — ✅ 완료뿐 아니라 ⏳ 대기 줄도 이미 세팅된 중복 후보)
   - motivation 이 직전/부모 결과 흐름과 정합?
   - ablation grid 가 _하나 변경 변수_ 원칙 따르는지 (controlled experiment)
   - 예상 metric 범위가 직전 baseline 대비 합리적?

   메모: experiment_spec.md 안에 `<!-- review: ... -->` 형태로.
   Return: 메모 추가된 파일 + 한국어 요약 한 줄."
```

quick / light 자리는 본 review skip.

**S1-5. spec 저장** — `experiments/{date}_{slug}/experiment_spec.md` (1 화면, 7-12 줄). `--parent` 면 `parent:` 필드 기록.

### S2: scaffold (개발팀 _new-lib_)

**S2-1. base 결정**:
- `--parent` (fine-tune) — _부모 config 를 복사해 새 `_ftNN_` config 갈래를 판다_. 부모 config·model.py 보존, 새 변형 파일에 `init_ckpt = 부모 ckpt` + `dataset = +새 데이터`. **코드 변경 아님 — config 분기** (4 원칙 #3·#4).
- ref (신규) — `--ref` 또는 `similar_models.md` 추천 모델 복사 후 변형.
- 사용자 _컨펌 한 줄_.

**S2-2. 개발팀 _new-lib_ 호출**:

```
Agent(subagent_type="개발팀", mode="new-lib"):
  "Mode: scaffold for experiment prototype.
   참고: {ref_path 또는 parent ckpt + config}
   실험 폴더: experiments/{date}_{slug}/
   spec: experiments/{date}_{slug}/experiment_spec.md

   ## 코드 수정 4 원칙 (필수 준수)
   1. 최소 수정 — ref/부모 복사 후 변형, 새 layer 도입 default X
   2. 원래 layer 1순위 — experiment_conventions.md preferred layer 사용
   3. 마이너 변경 = config — model.py 수정 X, config.yaml 변경
   4. 변형 prefix — fine-tuning 변형은 base 옆에 _ft01_ 식

   ## experiment_conventions.md 의 preferred layer
   {preferred_layer_list 인용}

   ## scaffold 산출물
   - experiments/{date}_{slug}/train.py (ref 의 train.py 복사 + 변형 자리만 수정)
   - experiments/{date}_{slug}/eval.py (ref 복사)
   - experiments/{date}_{slug}/config.yaml (ref/부모 복사 + 이번 실험 ablation 자리 표기)
   - (--parent / fine-tune) 부모 config 를 복사해 _새 `_ftNN_` config 갈래_ 생성 — init_ckpt = 부모 ckpt path, dataset = +새 데이터. 부모 config·model.py 는 보존 (덮어쓰기 X)
   - 또는 base 모델 폴더에 _ft01_ prefix 파일 (사용자 컨벤션 따라)

   ## 안 함
   - 새 layer 도입
   - ref/부모 모델 폴더의 _이미 사용 중인 layer_ 변경
   - 라이브러리화·정련 (이건 autopilot-code 영역)

   Return: 생성 파일 list + 한국어 요약 (어떤 자리 변형했는지)."
```

**S2-3. 한 화면 컨펌**:

```
=== Scaffold 완료 ===
- experiments/{date}_{slug}/train.py
- experiments/{date}_{slug}/eval.py
- experiments/{date}_{slug}/config.yaml
- (또는 model/<base>/_ft01_<variant>.py)
- (--parent 면) init_ckpt: experiments/<parent>/runs/run-001/ckpt/best.pt

변경 자리: <한 줄>

(진행 — run / 수정 — scaffold 다시 / 중단)
```

### S3: run 명령 안내 + `_RUNLOG` ⏳ 대기

**S3-1. run 명령 안내**:

```
실행:
  cd experiments/{date}_{slug}
  python train.py --config config.yaml
또는 사용자가 cluster 에 submit.
```

본 skill 은 _실행 자체 자동 X_ — 사용자 환경(cluster·GPU·queue) 가변. 사용자 직접 실행 후 eval 모드로 _이어서_.

**S3-2. `_RUNLOG.md` 대기 줄 append** (run 전 기록):

`.claude_reports/experiments/_RUNLOG.md` 에 _상태 ⏳ 대기_ 한 줄을 먼저 append (결과 칸 `—`). 실험이 _세팅됐고 학습 대기_ 임이 timeline 에 즉시 보이게 — 긴 cluster queue 중에도 in-flight·중복 세팅 추적. `pipeline_state` 의 `run: in_progress` 와 짝.

```
| 2026-05-26 | lr_sweep | TF_Restormer base, lr 1e-3→3e-4 | ⏳ 대기 | — |
```

**S3-3. 테스트팀 _smoke_ (옵션, 사용자 발화 시)** — scaffold 의 _basic 동작_ 검증:

```
"smoke 1 epoch 돌려봐" 같은 발화 자리:
Agent(subagent_type="테스트팀"):
  "Mode: smoke (1 epoch / minimum batch).
   target: experiments/{date}_{slug}/train.py
   목적: scaffold 의 basic 동작 검증 (data load / forward / backward / loss / optimizer step).
   실제 metric 수렴 검증 X.
   Return: 통과·실패 + 첫 epoch loss·시간."
```

**S3-4. 수렴 안 됨 → 품질관리팀 _ml-debug_ escalate (사용자 발화 시)**:

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

→ 학습이 끝나면 사용자가 `/autopilot-lab "결과 평가"` (eval 모드) 로 이어옴.

## ━━━ eval 모드 ━━━ (학습 후 평가·분석)

학습 완료된 ckpt 를 평가·분석한다. 대상은 _직전 setup 실험_ (자동) 또는 `--parent <slug>` (재평가·새 데이터).

### E1: eval spec (1 화면)

**E1-1. 대상 결정** — `--from`/직전 `_RUNLOG` ⏳ 대기 줄 또는 `--parent` 로 _어떤 실험·ckpt_ 인지 확정. 평가 데이터(기존 test set 또는 새 데이터)·metric 자동 추론.

**E1-2. 한 화면 컨펌**:

```
=== Eval Spec ===
대상 실험:    <date>_<slug> (또는 parent: <slug>)
ckpt:        experiments/<slug>/runs/run-001/ckpt/best.pt
mode:        eval
평가 데이터:   <기존 test set / 새 데이터 — 재평가 자리>
metric:      <PSNR / SSIM / SI-SDR / 등>
비교 대상:    <sibling 실험 / 부모 / paper baseline>

이대로 진행? (진행 / 수정 / 중단)
```

### E2: eval 실행 안내

**E2-1. eval 명령 안내** — scaffold 된 `eval.py` 를 ckpt + 데이터에 실행:

```
실행:
  cd experiments/<slug>
  python eval.py --config config.yaml --ckpt runs/run-001/ckpt/best.pt [--data <new_data>]
```

무거운 평가는 사용자 직접. _가벼운 평가_ (작은 test set) 자리는 사용자 발화 시 테스트팀 자동 실행 가능:

```
"가볍게 평가 돌려줘" 자리:
Agent(subagent_type="테스트팀"):
  "Mode: functional (eval run).
   target: experiments/<slug>/eval.py + ckpt
   Return: metric 값 + 산출 경로 (runs/run-001/metrics.json)."
```

### E3: 분석 + summary + `_RUNLOG` ✅

**E3-1. 결과 정리** — 사용자가 "결과 정리해" 발화 또는 메인 Claude 가 eval 종료 보고 인지:

```
=== Summary draft ===
실험:        {date}_{slug}
시도:        <spec 의 이번 시도 한 줄>
결과:        <metric 표 — best / final / 차이>
ablation:    <표 — 변수 × metric (sibling 실험 비교)>
부모 대비:    <parent 있으면 — delta>
관찰:        <2-3 bullet>
다음 후보:    <한 줄 — 다음 실험 시드>

이대로 저장? (저장 / 수정 / 중단)
```

**E3-2. plot / 시각화 → 자료팀 _figure-gen_ (옵션, 사용자 발화 시)**:

```
"결과 plot 그려줘" / "ablation 표 정리" 발화 자리:
Agent(subagent_type="자료팀", mode="figure-gen"):
  "Mode: figure-gen.
   target: experiments/{date}_{slug}/runs/*/metrics.json
   spec: 사용자 코드베이스의 figure 컨벤션 (project_user_paper_figure_style 메모리 또는 cwd 의 기존 plot 참고)
   Output: experiments/{date}_{slug}/figures/{plot_name}.{png,pdf}."
```

**E3-3. paper 비교 → 연구팀 _research-survey_ (옵션, qa standard+ + 사용자 발화 시)**:

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

**E3-4. 저장 — 세 파일 갱신**:

- `experiments/{date}_{slug}/summary.md` — 위 한 화면
- `experiments/{date}_{slug}/STORY.md` — narrative 추가 (motivation·이전/부모 정리·이번 시도·결과·다음 후보 한 단락)
- `.claude_reports/experiments/_RUNLOG.md` — S3-2 에서 append 한 _해당 실험(date+slug) 줄_ 을 찾아 _상태 ✅ 완료 + 결과·다음_ 으로 **갱신** (새 줄 append X — 한 실험 = 한 줄 유지):
  ```
  | 2026-05-26 | lr_sweep | TF_Restormer base, lr 1e-3→3e-4 | ✅ 완료 | val PSNR 28.4→28.7 (+0.3) · 다음: warmup 1k step |
  ```
  - 부모 있으면 _시도_ 칸에 `(← <parent_slug>)` 표기. 드물게 ⏳ 줄이 없으면(예: setup 없이 `--from eval` 직접 진입) 새로 append. 중단·실패는 `❌ 중단` 으로 갱신.

## 산출물 구조

```
.claude_reports/experiments/
├── _RUNLOG.md                      [T1] timeline (한 실험 = 한 줄 — `날짜｜slug｜시도(← parent)｜상태｜결과·다음`; 상태 ⏳대기→✅완료/❌중단 갱신)
├── {date}_{slug}/                  ← 한 실험 = 한 폴더
│   ├── pipeline_state.yaml         [T1] --from 재개용 (mode·parent·phases)
│   ├── STORY.md                    [T1] narrative 누적 (motivation·이전/부모·이번·결과)
│   ├── experiment_spec.md          [T1] 1 화면 spec
│   ├── summary.md                  [T1] 결과·다음 후보 (eval 산출)
│   ├── train.py / eval.py / config.yaml  [T1] scaffold (setup 산출)
│   ├── runs/                       [T2] 각 run 의 결과 (사용자 실행 산출)
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
mode: setup                    # setup | eval
parent: <slug 또는 null>        # 계보 (fine-tune base / 재평가 대상)
ref: model/TF_Restormer        # 참고 자리 (parent 자리는 null)
qa_level: light
phases:                        # setup: spec/scaffold/run | eval: eval/summary
  spec: done
  scaffold: done
  run: in_progress             # 사용자 직접 학습 자리
  eval: pending
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
- ref/부모 모델 폴더 직접 수정 (variation 만, base 보존)
- 라이브러리화·module 정련 (autopilot-code 영역)
- PRD·스택 결정 (autopilot-spec 영역)
- 단발 데이터 변환·정제 script (autopilot-code / 개발팀 영역 — lab 모드 아님)
- 실험 자동 실행·학습·평가 (사용자 환경·queue 가변 — 명령만 안내. 가벼운 eval 만 발화 시 테스트팀)
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
.claude_reports/experiments/{date}_{slug}/ -- ✅ {mode}:{phase} 단계 완료
```

다음 단계 안내:
- spec → "scaffold 진행할까요?"
- scaffold → "실행 명령: cd experiments/{date}_{slug} && python train.py --config config.yaml"
- run 안내 → "_RUNLOG ⏳ 대기 기록. 학습 끝나면 `결과 평가` 로 이어오세요 (eval 모드)"
- eval → "metric·분석 정리"
- summary → "_RUNLOG ✅ 완료 갱신. 다음 실험: <한 줄>"

## Examples

### 예시 1 — lr sweep (setup → eval 한 사이클)

```
사용자: lr 1e-3 → 3e-4 비교                           [setup 모드]
→ S0: _RUNLOG 최근 5 줄 read, similar_models 의 TF_Restormer 자동 추천
→ S1: spec draft (motivation: 직전 baseline val 28.4 에서 lr 영향 점검) → 컨펌
→ S2: 개발팀 new-lib → model/TF_Restormer/_ft01_lr_3e-4.yaml (config 만, model.py 손 안 댐) → 컨펌
→ S3: 실행 명령 안내 + _RUNLOG "⏳ 대기" 줄 append

[사용자가 cluster 에서 학습]

사용자: lr_sweep 결과 평가해                          [eval 모드 — 직전 실험 자동]
→ E1: 대상 = 2026-05-26_lr_sweep, ckpt 자동 → 컨펌
→ E2: eval 실행 안내 (또는 가벼우면 테스트팀)
→ E3: summary draft → 컨펌 → _RUNLOG 줄을 "✅ 완료 val 28.4→28.7 (+0.3)" 로 갱신
```

### 예시 2 — ablation (MDTA 제거, setup)

```
사용자: TF_Restormer 에서 MDTA 빼고 비교
→ S0: 직전 lr_sweep best config 자동 인용
→ S1: spec — _ft02_no_mdta variant
→ S2: 개발팀 — preferred layer (MDTA / GDFN / LayerNorm2d) 중 MDTA 만 standard MHA 로 교체
   → 4 원칙 prepend — _새 layer 도입 X_, MHA 는 standard PyTorch
→ S3: 실행 안내 + ⏳ 대기
→ (학습 후) eval → "MDTA 제거 시 val 28.7 → 28.1 (-0.6) — MDTA 기여 +0.6 검증"
```

### 예시 3 — 추가 데이터 fine-tuning (setup --parent, 계보)

```
사용자: lr_sweep 모델에 newdata 추가해서 fine-tune     [setup --parent lr_sweep]
→ S0: 부모(lr_sweep) summary·config·ckpt path 자동 read
→ S1: spec — parent: lr_sweep, 이번 시도: + newdata fine-tune, motivation: 도메인 적응
→ S2: 개발팀 — config 의 init_ckpt = experiments/lr_sweep/runs/run-001/ckpt/best.pt
       데이터셋에 newdata 추가, _ft03_finetune prefix
→ S3: 실행 안내 + _RUNLOG "⏳ 대기 (← lr_sweep)" 줄

[사용자 학습] → eval → "fine-tune 후 newdata val +1.2, 기존 test 유지" + 계보 timeline 에 baseline→lr_sweep→ft 보임
```

### 예시 4 — 새 데이터로 재평가 (eval --parent, 학습 없음)

```
사용자: 그 모델 newtestset 으로 평가만 해봐            [eval --parent <slug>]
→ E1: 대상 = 부모 ckpt, 평가 데이터 = newtestset (학습 X) → 컨펌
→ E2: eval 실행 안내 (eval.py --ckpt <부모> --data newtestset)
→ E3: summary — "기존 test 28.7 / newtestset 26.9 — 도메인 gap 1.8" → _RUNLOG 새 줄 ✅ (← parent)
```

## Task
$ARGUMENTS
