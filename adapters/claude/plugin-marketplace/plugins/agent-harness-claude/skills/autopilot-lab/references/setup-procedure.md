# Procedure

전체 = **setup** → [사용자 학습] → **eval**. `--mode auto` 면 발화로 분기. 각 모드는 독립 호출이고 `pipeline_state.yaml` 에 상태 누적.

> **Stage-dispatch 계약** (`standard+`, OPERATIONS §5.10 ③④·SD-1·SD-2): `standard+` 자리에서 durable 한 setup/eval/report 스테이지는 각각 독립된 **depth-2 headless 세션**으로 dispatch 된다 (in-session 팀 호출은 그 세션 안에서 실행) — **file-only handoff** 원칙(입력은 산출물 파일에서 읽고, 이전 스테이지의 대화 맥락은 참조하지 않음)을 따른다. depth-1 conductor 는 경로만 넘기고 verdict/status 만 회수한다. **실제 실험 run 은 길고 비동기·human-gated (`_RUNLOG.md` ⏳ 대기줄이 실제 학습 완료를 기다림) — dispatch 대상 스테이지가 아니다.** run 세그먼트는 기존 `lab-runner.yaml` dispatch profile 을 그대로 쓰고, 본 stage-dispatch 계약은 그 profile 과 합성(compose)된다. `direct/quick` 및 단발 실험 run 안내는 inline 유지, 스테이지 세션은 재-dispatch 하지 않는다(depth 3+ 금지). pipe 본문 자체를 dispatch 명령형으로 다시 쓰는 건 별도 후속 작업.

#### stage-worker 매핑 (setup)

| stage | in-session team | input artifacts | output artifacts | write class |
|---|---|---|---|---|
| S1 spec | 연구팀 (plan-review) | `_RUNLOG.md` 최근 줄 + research 산출 | `experiments/{date}_{slug}/experiment_spec.md` | dispatched (depth-2) |
| S2 scaffold | 개발팀 (new-lib) | `experiment_spec.md` + ref/parent config | `train.py`/`eval.py`/`config.yaml`/`metrics.jsonl` logger | dispatched (depth-2) |
| S3 run | — (사용자 직접 실행 / cluster submit) | `config.yaml` | `_RUNLOG.md` ⏳ 대기줄 + `run.json`(status:"running") | **NOT dispatched** — long/async·human-gated, `lab-runner.yaml` profile 이 담당 |

eval 쪽 stage-worker 행(E2/E3-2/E3-3)은 `eval-procedure.md` 참조.

## ━━━ setup 모드 ━━━ (학습 전 세팅)

### S1: spec (1 화면)

**S1-0. worktree+실험 브랜치 확보** ([§Git 워크플로우](#git-워크플로우--별도-worktree실험-브랜치-원칙-canonical)) — main 에서 작업 시작 금지. 실험 slug 의 worktree `<repo>-wt/<slug>` 가 없으면 판다 (`git worktree add <repo>-wt/<slug> -b exp/<slug> <base>`, 기존 브랜치면 `-b` 생략). 이미 있으면 재사용. 이후 모든 편집·scaffold·config 커밋은 그 worktree 안에서. main 워킹트리는 조정만.

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
   - **metrics.jsonl logger** — train.py/eval.py 가 step 마다 `experiments/{date}_{slug}/metrics.jsonl` 에 append (한 줄 = `{step,split,name,value,ts}`, append-only). **스키마·계약 규칙·경로 경계 = §출력 데이터계약 참조** (root `metrics.jsonl` = per-step 스트림 / `runs/` 아래 `metrics.json(l)` 금지, per-run blob 은 `eval_result.json`). metrics 를 실제로 채우는 유일 지점.
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
- experiments/{date}_{slug}/metrics.jsonl (logger 포함 — train/eval 가 step 마다 append)
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

`<artifact-root>/experiments/_RUNLOG.md` 에 _상태 ⏳ 대기_ 한 줄을 먼저 append (결과 칸 `—`). 실험이 _세팅됐고 학습 대기_ 임이 timeline 에 즉시 보이게 — 긴 cluster queue 중에도 in-flight·중복 세팅 추적. `pipeline_state` 의 `run: in_progress` 와 짝.

**run.json 출생 (기계판독 짝)** — `_RUNLOG ⏳` 와 같은 자리에서 `experiments/{date}_{slug}/run.json` 을 `status:"running"` 으로 생성: `skill_mode:"setup"`(= `pipeline_state.mode`), `parent`(`--parent` slug 또는 null), `started_at`(now, ISO8601), `config_ref`(scaffold 된 config 경로), `ckpt_path`(예정 best ckpt 경로 — 예: `experiments/{date}_{slug}/runs/run-001/ckpt/best.pt`). `best`·`ended_at` 은 _생략_ (running 자리 — §출력 데이터계약 best 부재 규칙). E3-4 에서 `done`+`best`+`ended_at` 으로 갱신. (lifecycle = §출력 데이터계약)

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
