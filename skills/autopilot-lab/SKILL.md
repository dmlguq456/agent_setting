---
name: autopilot-lab
description: "_빠른 실험 prototype_ entry — 무거운 학습은 사용자가 돌리고, lab 은 그 앞뒤를 돕는다. 2 모드: **setup** (학습 실험 세팅 — spec → scaffold → 실행 명령 안내) / **eval** (학습 완료 ckpt 평가·분석 — metric·ablation·paper 비교·plot·(옵션) 정식 보고서 [prose→autopilot-draft / 음성·미디어는 재생 HTML]). 확장 케이스(기존 세팅에 새 데이터로 재평가·추가 fine-tuning)는 `--parent <slug>` 계보로 흡수 — 새 모드 없음 (fine-tune=setup --parent 로 새 config 갈래, 재평가=eval --parent). experiment 단위 폴더 강제 + STORY narrative + _RUNLOG timeline (⏳대기→✅완료 상태 + 부모 링크) 누적 → 덮어쓰기·휘발·즉흥 차단. analyze-project 의 experiment_conventions.md / similar_models.md 자동 read — 사용자 코드베이스 layer·prefix·config 패턴 1순위. 정련·라이브러리화 졸업은 autopilot-code."
argument-hint: "<task description> [--mode setup|eval|auto] [--parent <slug>] [--ref <similar-model-path>] [--qa quick|light|standard|thorough|adversarial] [--report] [--from spec|scaffold|run|eval|summary]"
metadata:
  group: entry
  fam: code
  modes: [setup, eval]
  blurb: "빠른 실험 prototype entry — 학습 세팅(setup)과 ckpt 평가(eval) 앞뒤를 돕는다"
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
| `autopilot-spec` | 비코드 청사진 (PRD·스택·skeleton) | `spec/` |
| **`autopilot-lab`** (본 skill) | **빠른 학습 실험 prototype (setup·eval, hands-on)** | **`experiments/`** |
| `autopilot-code` | brownfield 정련·라이브러리화 (full) / `--qa quick`: 소규모 잡일 (가벼움 + 로그) | `plans/` |
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

## Git 워크플로우 — 별도 worktree+실험 브랜치 (원칙, canonical)

**lab 은 main 이 아니라 _전용 worktree + 실험 브랜치_ 에서 진행한다.** 실험 시작 자리(setup, 또는 부모 없는 첫 eval)에서 main 워킹트리를 직접 건드리지 않고, [OPERATIONS §5.10](../../OPERATIONS.md) 명명 규칙대로 형제 worktree `<repo>-wt/<exp-slug>` 를 파고 그 안 실험 브랜치(`exp/<slug>` 또는 기존 feature 브랜치)에서 작업한다. 이미 해당 worktree·브랜치가 있으면 재사용.

### autopilot-code 의 worktree 와 결정적 차이

| | autopilot-code worktree | **autopilot-lab worktree+브랜치** |
|---|---|---|
| 성격 | **머지 전제 _임시_ 분사** — 격리해 작업 후 main 으로 merge, 브랜치는 수확 뒤 disposable | **머지 안 하는 _별도 작업 라인_** — 실험은 그 자체로 main 에 통째 들어가지 않는다 |
| main 청결 보장 | merge 후 브랜치 정리 | **"안 merge" 로 보장** (gitignore 아님) |
| 산출물 | 코드 변경 → main 의 일부가 됨 | 실험 config·scaffold·로그 → **브랜치에 남고 main 엔 안 감** |
| 수명 | 작업 1건 = 브랜치 1개, 짧게 | 실험 라인이 길게 유지 (계보 `--parent` 누적) |

### 따름 규칙

1. **실험 config 는 gitignore 하지 말고 _브랜치에 커밋_** — `_ft*`·`_tune_*`·`exp_*` 등 실험 config 는 그 브랜치에서 tracked. 어떤 config 가 어떤 결과를 냈는지 git 으로 재현 가능하게. (main 의 `.gitignore` 는 이들을 계속 ignore — main 청결은 _안 merge_ 가 보장.)
2. **무거운 산출물(ckpt·log·`.claude_reports/`)은 브랜치에서도 gitignore 유지** — 재현 기록은 `.claude_reports/experiments/{slug}/` (영속) + 커밋된 config 가 함께 담당.
3. **main 으로 가는 건 _졸업_ 뿐** — (a) 재사용 코드(seam·모듈)는 `autopilot-code` 로 main 졸업, (b) 이긴 config 는 영구 파일명으로 rename 해 졸업. 실험 브랜치 자체를 main 에 통째 merge 하지 않는다.
4. **브랜치는 실험 라인의 작업 공간** — archive 가 아니다. `.claude_reports/experiments/` + 커밋된 config 가 archive 라 브랜치는 졸업 후 정리 가능.

> 오케스트레이션(컨펌·분사·수확)은 main 세션, 실제 편집·학습 세팅은 worktree 안에서 (§5.10 중첩 1단 한계 동일 적용).

## 모드 — 한 실험의 lifecycle

한 실험의 전체 흐름 = **setup (lab)** → [사용자가 학습 실행] → **eval (lab)**. 두 번의 lab 호출이 _대기·완료_ 2-beat 로 `_RUNLOG` 한 줄을 채운다.

| 모드 | 자리 | 하는 일 | 산출물 / 상태 |
|---|---|---|---|
| **setup** | 학습 _전_ | spec(뭘 학습·ablation) → scaffold(ref 또는 부모 ckpt 에서 train/eval/config) → 실행 명령 안내 | scaffold 코드 + `_RUNLOG` ⏳ 대기 |
| **eval** | 학습 _후_ | eval spec(ckpt·데이터·metric) → eval 실행 안내 → 분석(metric·ablation·paper 비교·plot) → **REPORT.md**(자체완결 보고서) | `REPORT.md` + summary 1줄 인덱스 + `_RUNLOG` ✅ 완료 |

### 확장 — `--parent <slug>` 계보 (새 모드 없이 흡수)

기존 실험을 _부모_ 로 이어가는 두 케이스:

| 케이스 | 호출 | 의미 |
|---|---|---|
| 기존 세팅 + **새 평가 데이터로 재평가** | `eval --parent <slug>` | 학습 X — 부모 ckpt 를 새 데이터에 평가만 |
| 기존 세팅 + **새 학습 데이터로 fine-tune 후 재평가** | `setup --parent <slug>` → [학습] → `eval` | fine-tune = _학습_ = setup. 단 ref 가 아니라 _부모 ckpt 에서 이어서_ scaffold |

부모 링크는 `_RUNLOG` · `STORY.md` · `pipeline_state.yaml` 에 남아 timeline 에 _실험 계보_ (baseline → ft01 → ft01+newdata …) 가 보인다. (기계판독 계보 그래프 엣지의 SoT 는 `run.json.parent` — 이 세 자리는 그 cross-ref/사람용 거울; §출력 데이터계약)

> **script(단발 데이터 변환·정제) 는 lab 모드 아님** — one-shot 유틸은 `Agent(개발팀)` 직접 또는 `/autopilot-code`. lab 은 _학습 실험_ 에 집중.

## Default Invocation Rule (메인 Claude 자동 라우팅)

본 skill 은 글로벌 [`CLAUDE.md`](../../CLAUDE.md) §0 "autopilot-* 호출 패턴" 의 _컨펌 의무_ 적용 대상.

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

- 단발 데이터 정제·변환·script — _로그 남기고 싶으면_ `/autopilot-code --qa quick` (가벼운 plan + execute + test, `plans/` 에 로그). 진짜 throwaway(로그 불필요)만 메인 Claude 직접. lab 모드 아님
- 단발 plot 만 — `Agent(자료팀, mode="figure-gen")` 직접
- 정련 / 라이브러리화 / spec 정돈 — `/autopilot-code` 또는 `/autopilot-spec`
- `/autopilot-lab <args>` slash 직접 입력 — 컨펌 skip

## Language Rule
- All user-facing output in natural Korean (no translationese — write Korean natively, don't translate from an English draft).
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
| 사용자 일관 패턴 (cross-project) | `mem profile 07_coding_convention` (`python3 ~/.claude/tools/memory/mem.py profile 07_coding_convention`) | cross-project | **2순위 (default·fallback)** — per-project 부재 또는 _빈 자리_ 만 보강. 부재 시 `/analyze-user coding_convention` 권장 안내 |
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

`analysis_project/code/experiment_conventions.md` (**1순위 — per-project 가 source of truth**) + `mem profile 07_coding_convention` (2순위 — cross-project default, per-project 부재·빈 자리만 보강) 의 _preferred layer / config 메커니즘 / prefix 패턴_ 을 source 로 다음 4 원칙을 개발팀 _new-lib_ mode prompt 에 매번 prepend. _충돌 자리는 per-project 우선_ — 본 프로젝트의 실제 컨벤션 침범 X.

1. **최소 수정** — 기존 모델 폴더 복사 후 변형 (`--ref` 또는 `similar_models.md` 추천). 새 layer 도입 default X
2. **원래 layer 1순위** — `experiment_conventions.md` 의 _preferred layer_ list 가 1순위. 새 layer 도입은 _명시 컨펌_ 필요
3. **마이너 변경 = config** — model.py 직접 수정 X, `config.yaml` 가능한 자리는 config 로
4. **변형 prefix** — fine-tuning 변형은 `experiment_conventions.md` 의 prefix 패턴 (예: `_ft01_`·`_ft02_`) 따라 base 파일 옆에 둠. 새 base 는 새 모델 폴더

---

## 출력 데이터계약 (기계판독 — 실험 대시보드 §25 소비)

> lab 의 _행동은 불변_, **출력 _포맷_ 만 표준화**. 아래 3종(`metrics.jsonl`·`run.json`·`report/`)은 실험 대시보드(worklog §25)가 _디스크 파일만 읽어_ 차트·계보·요약 카드를 그리는 기계판독 면이다. **디스크가 진실원천(SoT).** 계약 SoT = `e0-lab-contract-scope.md` §3 / worklog PRD §25.4 (claude_setting 은 cross-ref). 사람용 거울(`_RUNLOG`·`REPORT.md`·`summary.md`·`STORY.md`)은 _그대로 유지_ — 이 기계판독 면은 그 _옆에_ 추가될 뿐 대체가 아니다. M0("정의 자기설명화")의 실험판.

### metrics.jsonl — per-step 스트림 (append-only)

`experiments/<id>/metrics.jsonl` — **한 줄 = 1 record**. train/eval 스크립트가 step 마다 append (S2 scaffold 의 jsonl logger 가 박는 _유일 지점_).

```jsonl
{"step": 1200, "split": "val",   "name": "loss", "value": 0.342, "ts": "2026-06-23T14:02:11Z"}
{"step": 1200, "split": "train", "name": "loss", "value": 0.318, "ts": "2026-06-23T14:02:11Z"}
{"step": 1200, "split": "val",   "name": "psnr", "value": 28.41, "ts": "2026-06-23T14:02:11Z"}
```

| 필드 | 타입 | 의미 |
|---|---|---|
| `step` | int | x축 (또는 `ts` wall-time 토글) |
| `split` | str | `train`/`val`/`test` — 곡선 그룹 |
| `name` | str | metric 이름 (`loss`/`psnr`/`si_sdr`…) — 곡선 시리즈 |
| `value` | float | scalar 값 |
| `ts` | ISO8601 str | wall-clock (step↔time 토글·tail-follow 기준) |
| `kind` | str (옵션) | `scalar`(default)\|`image`\|`hist` — **scalar 우선·확장 여지만 예약** (E0 는 scalar 만) |

**계약 규칙**: append-only · 한 줄 1 record · **파일이 SoT (DB 적재 X — 대용량은 append-only 파일 스트리밍, 라이브는 tail-follow)** · worklog 는 `?name=&split=` 로 필터.

**경로 경계 (혼동 금지)**: root `experiments/<id>/metrics.jsonl` _이_ per-step 차트 스트림 = SoT. per-run 단발 eval 결과 blob 이 필요하면 `runs/run-001/eval_result.json` 으로 둔다 — **`runs/` 아래 `metrics.json`·`metrics.jsonl` 명명 금지** (차트 소비측은 root 단일 파일을 스트리밍 → per-run 분산·동명은 깨짐). 즉 root `.jsonl` = 스트림 / `runs/run-001/` = ckpt·log·(옵션)`eval_result.json`.

### run.json — run manifest (기계판독)

`experiments/<id>/run.json` — 흩어진 run 사실(slug·parent·mode·ckpt·best)을 한 기계판독 파일로 _모은_ 것 (새 계산 아님). `_RUNLOG.md` 가 이 파일의 _사람용 거울_.

```json
{ "id": "2026-06-23_lr_sweep", "parent": null, "skill_mode": "setup", "status": "done",
  "config_ref": "experiments/2026-06-23_lr_sweep/config.yaml",
  "ckpt_path": "experiments/2026-06-23_lr_sweep/runs/run-001/ckpt/best.pt",
  "started_at": "2026-06-23T09:00:00Z", "ended_at": "2026-06-23T14:30:00Z",
  "best": { "name": "psnr", "value": 28.7, "step": 18000 } }
```

| 필드 | 의미 / lab 소스 |
|---|---|
| `id` | `<date>_<slug>` = 실험 폴더명 |
| `parent` | `--parent` slug 또는 null — **계보 엣지 SoT** (비교/계보 그래프) |
| `skill_mode` | `setup`\|`eval` = `pipeline_state.mode` (출생 시점 모드 — 하드코딩 아님) |
| `status` | `running`\|`done`\|`failed` (`_RUNLOG ⏳대기/✅완료/❌중단` 거울) |
| `config_ref`·`ckpt_path` | config·best ckpt 포인터 |
| `started_at`/`ended_at` | 출생 / 종료 timestamp (ISO8601) |
| `best` | `{name,value,step}` — eval 분석 산물. **종료 dispatch·요약 카드의 소스** |

**lifecycle**: `status:"running"` 으로 _출생_ — setup 자리(S3-2, `skill_mode:"setup"`) 또는 eval-only `--parent` 직접 진입 자리(E1-3 birth, `skill_mode:"eval"`) → E3-4 에서 `done`+`best`+`ended_at` 으로 갱신.
**best 부재 규칙 (소비측 분기 단일화)**: `running`·`failed` 자리는 `best` _키 자체를 생략_ (null 아님). `done` 만 `best:{}` 객체. 정리 — `running` → `best`·`ended_at` 둘 다 없음 / `done` → `best`+`ended_at` / `failed` → `ended_at` 기록(중단 시각)·`best` 생략.

### parent 계보 SoT

비교/계보 그래프의 엣지 기계판독 SoT = `run.json.parent`. `pipeline_state.parent` 와 `_RUNLOG (← parent)`·`STORY.md` 는 _같은 값의 cross-ref/사람용 거울_ (SoT 충돌 방지 — 그래프는 run.json 만 읽음).

### 종료 dispatch (lab → worklog)

eval 종료 시 lab 은 `run.json` 의 `best` + parent 대비 delta 를 _방출_, worklog 결재함/보드가 그것을 소비·카드화한다. **lab 은 방출만 — 능동 push 아님** (수신·카드화는 worklog E3, PRD §25.7; loops 결재함 패턴 동형). dispatch 소스 = 이미 채워진 `run.json best:{}` (새 분석 0).

### report/ — 보고서 산출물 (iframe 렌더 대상)

`experiments/<id>/report/` = 대시보드 캔버스가 sandboxed iframe 으로 렌더하는 HTML 디렉토리. **한 디렉토리 규약, 두 생성 주체**:
- (a) lab 의 _기존_ 오디오/미디어 재생 HTML — E3-5 `report/report.html` (분리음·스펙트로그램·`<audio>` 임베드). **이 동작은 보존** — audio/미디어 실험은 lab 이 계속 여기 쓴다.
- (b) autopilot-draft/design 의 리치 _prose_ HTML — **prose 리치 리포트 생성 주체는 draft/design** (PRD §25.4.3 §7 lock), lab 은 직접 생성 X.

즉 "report/ = draft/design" 은 _prose 리포트_ 에 한함 — lab 의 audio HTML 자리(E3-5)를 금지하는 게 아니다. lab 자체완결 deliverable = `REPORT.md`(md) 는 그대로. 셋 공존: `REPORT.md`(lab md) · `report/report.html`(lab audio/media) · `report/*`(draft/design prose HTML).

---

# Procedure

전체 = **setup** → [사용자 학습] → **eval**. `--mode auto` 면 발화로 분기. 각 모드는 독립 호출이고 `pipeline_state.yaml` 에 상태 누적.

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

`.claude_reports/experiments/_RUNLOG.md` 에 _상태 ⏳ 대기_ 한 줄을 먼저 append (결과 칸 `—`). 실험이 _세팅됐고 학습 대기_ 임이 timeline 에 즉시 보이게 — 긴 cluster queue 중에도 in-flight·중복 세팅 추적. `pipeline_state` 의 `run: in_progress` 와 짝.

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

**E1-3. run.json 출생 (eval-only `--parent` 진입 자리 — 기계판독 짝)** — `experiments/<id>/run.json` 이 _없으면_ 여기서 출생한다 (**file-existence 가드**: setup→eval 정상 사이클은 S3-2 에서 이미 만들었으므로 _재출생·덮어쓰기 X_). `eval --parent` 직접 진입(학습 없이 재평가 — 아래 예시 4)은 S3 를 안 거쳐 run.json 이 안 태어나는 공백을 닫는다 (사람용 거울 = E3-4 의 "⏳ 줄 없으면 새 줄 append" 와 짝). 출생값: `status:"running"`, `skill_mode:"eval"`(= `pipeline_state.mode`), `parent`(`--parent` slug), `started_at`(now, ISO8601), `config_ref`(부모 config 경로 또는 null), `ckpt_path`(평가 대상 ckpt — 예: `experiments/<parent>/runs/run-001/ckpt/best.pt`), `best` _생략_. E3-4 에서 setup run 과 동일하게 `done`+`best`+`ended_at` 갱신 (S3-2 setup 출생과 대칭 — §출력 데이터계약 lifecycle).

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
   Return: metric 값 (eval 최종 묶음 — run.json best 로 요약) + per-step stream 경로 (experiments/<slug>/metrics.jsonl)."
```

### E3: 분석 + summary + `_RUNLOG` ✅

**E3-1. 결과 정리** — 사용자가 "결과 정리해" 발화 또는 메인 Claude 가 eval 종료 보고 인지:

```
=== REPORT draft (→ REPORT.md 로 저장, E3-4) ===
실험:        {date}_{slug}
시도:        <spec 의 이번 시도 한 줄>
결과:        <metric 표 — best / final / 차이>
ablation:    <표 — 변수 × metric (sibling 실험 비교)>
부모 대비:    <parent 있으면 — delta>
관찰:        <2-3 bullet>
그림:        <figures/*.png 을 REPORT.md 본문에 ![](figures/..) 로 인라인 임베드 — 경로만 적기 X>
다음 후보:    <한 줄 — 다음 실험 시드>

이대로 저장? (저장 / 수정 / 중단)
```

**E3-2. plot / 시각화 → 자료팀 _figure-gen_ (옵션, 사용자 발화 시)**:

```
"결과 plot 그려줘" / "ablation 표 정리" 발화 자리:
Agent(subagent_type="자료팀", mode="figure-gen"):
  "Mode: figure-gen.
   target: experiments/{date}_{slug}/metrics.jsonl
   spec: 사용자 코드베이스의 figure 컨벤션 (project_user_paper_figure_style 메모리 또는 cwd 의 기존 plot 참고)
   Output: experiments/{date}_{slug}/figures/{plot_name}.{png,pdf}."
```

> **생성한 figure 는 반드시 `REPORT.md` 본문에 markdown 이미지로 인라인 임베드** (`![<caption>](figures/<plot>.png)`) — `figures/` 에 저장만 하고 경로만 적는 것 **X**. REPORT.md 가 _그림 들어간_ 보고서가 되게 (그림 없는 텍스트 보고서 금지). figure 가 STORY 의 결과 서술과 직결되면 STORY.md 에도 임베드.
> **이미지 vs 오디오 경계 (보고서 형식 선택의 단일 기준)**: markdown 은 이미지를 인라인 렌더하므로 _그림은 항상 md 임베드로 충분_ — **그림만 있으면 HTML 만들지 말 것**. E3-5 의 HTML 은 _오직 오디오/미디어 재생_ 용 (markdown 이 `<audio>` 재생을 막기 때문). 즉 figure→md 인라인(default) / audio→HTML(E3-5).

**E3-3. paper 비교 → 연구팀 _research-survey_ (옵션, qa standard+ + 사용자 발화 시)**:

```
"결과를 기존 paper 와 비교해줘" 발화 자리:
Agent(subagent_type="연구팀", mode="research-survey"):
  "Mode: research-survey (실험 결과 자리).
   결과: experiments/{date}_{slug}/REPORT.md
   사전 자료: .claude_reports/research/ + analysis_project/paper/

   비교 axis:
   - 본 실험의 metric vs 기존 paper baseline
   - 본 실험의 변경 자리가 paper 어디 자리와 닿나
   - 본 실험의 관찰이 paper 의 주장·반박과 어떤 자리

   Return: 비교 표 + 한국어 한 단락 요약 (REPORT.md 에 ## 기존 paper 와의 비교 섹션 추가)."
```

**E3-5. 정식 보고서 (옵션 — 공유·의사결정용. `--report` / "보고서 써줘"·"공유용" 발화 / high-stakes(논문·외부 공개))**:

`summary.md` 는 _1 화면 실험 기록_ (계보·다음 후보). 그걸 넘어 _공유·의사결정용 정식 문서_ 가 필요하면 본 단계에서 산출. 두 형태 — 실험 성격으로 분기:

- **prose 보고서** (일반 실험) → `autopilot-draft --mode doc` 핸드오프. 입력 = `experiments/{date}_{slug}/{summary.md, STORY.md, figures/}` + runs metrics. 산출은 `documents/{date}_{slug}/` (draft 컨벤션·리뷰·다듬기). eval 은 _요청·핸드오프_ 만 — prose 생성은 draft 가 담당(machinery 중복 방지).
- **재생 HTML 보고서** (음성·오디오·미디어 실험 — 청취·스펙트로그램·시각 비교가 본질) → `자료팀 figure-gen` 으로 분리음/스펙트로그램 세그먼트 + 임베드 `<audio>`/`<img>` **단일 HTML** 생성 (`experiments/{date}_{slug}/report/report.html`). _markdown `<audio>` 는 VS Code 프리뷰가 차단_ → **audio 도메인은 HTML 기본**. 긴 오디오는 _N분 단위 세그먼트 페이지_ 분할. 필요시 `python -m http.server --bind 0.0.0.0 <port>` 로컬 서빙 + 접속 URL 안내.

기본 deliverable = `REPORT.md`(E3-4, 자체완결 정식 보고서). 본 E3-5(autopilot-draft prose / 재생 HTML)는 그 위에 _외부 공개·의사결정용 doc-pipeline_ 또는 _오디오/미디어 재생_ 이 필요할 때만 추가. 둘 다 필요하면 prose + HTML 병행(prose 가 HTML 비교본을 상대링크).

**E3-4. 저장 — 산출물 갱신** (최종 deliverable = `REPORT.md`):

- `experiments/{date}_{slug}/REPORT.md` — **eval 의 최종 산출물 = 자체완결 정식 보고서.** 구조: _요약(Executive Summary) 맨 위_ → 배경·동기 → 가설 → 방법 → 결과 → 해석 → 결론 → 다음 → 재현. **figure 는 `![](figures/..)` 본문 인라인.** **자체완결 필수** — 실험에서 도입한 조건명·구조명·약자·metric 정의를 _보고서 안에서 풀어_ 대화 맥락 없는 독자도 읽히게(예: "single/multi 같은 게 뭔지 보고서만 봐선 모름"을 차단). 사용자가 볼 것은 흩어두지 말고 _전부 이 한 파일에 통합_ (summary·STORY 요지·metrics·figure 를 여기로).
- `experiments/{date}_{slug}/summary.md` — RUNLOG/parent auto-read 용 _1줄 인덱스_ (판정 한 줄 + `REPORT.md` 포인터). _사용자 deliverable 아님._
- `experiments/{date}_{slug}/STORY.md` — narrative 누적 (motivation·이전/부모 정리·이번 시도·결과·다음 후보 한 단락)
- `.claude_reports/experiments/_RUNLOG.md` — S3-2 에서 append 한 _해당 실험(date+slug) 줄_ 을 찾아 _상태 ✅ 완료 + 결과·다음_ 으로 **갱신** (새 줄 append X — 한 실험 = 한 줄 유지):
  ```
  | 2026-05-26 | lr_sweep | TF_Restormer base, lr 1e-3→3e-4 | ✅ 완료 | val PSNR 28.4→28.7 (+0.3) · 다음: warmup 1k step |
  ```
  - 부모 있으면 _시도_ 칸에 `(← <parent_slug>)` 표기. 드물게 ⏳ 줄이 없으면(예: setup 없이 `--from eval` 직접 진입) 새로 append. 중단·실패는 `❌ 중단` 으로 갱신.
- `experiments/{date}_{slug}/run.json` — **기계판독 manifest 갱신** (S3-2 setup / E1-3 eval-only 에서 출생한 파일을 찾아). `status:"done"`, `ended_at`(now, ISO8601), `best:{name,value,step}`(eval 분석 산물 — `_RUNLOG ✅`·REPORT 와 동일 metric). 중단·실패는 `status:"failed"` + `ended_at`(중단 시각) 기록, `best` _생략_ (`_RUNLOG ❌ 중단` 거울 — §출력 데이터계약 best 부재 규칙). `_RUNLOG.md` 는 이 파일의 사람용 거울.
- **종료 dispatch (방출만)** — eval 종료 시 `run.json` 의 `best` + parent 대비 delta 를 worklog 결재함/보드가 소비하도록 _방출_. **lab 은 방출만 — 능동 push X** (수신·카드화는 worklog E3, PRD §25.7; loops 결재함 패턴 동형). 소스 = `run.json best:{}` (새 분석 0). (§출력 데이터계약 종료 dispatch)

## 산출물 구조

```
.claude_reports/experiments/
├── _RUNLOG.md                      [T1] timeline (한 실험 = 한 줄 — `날짜｜slug｜시도(← parent)｜상태｜결과·다음`; 상태 ⏳대기→✅완료/❌중단 갱신)
├── {date}_{slug}/                  ← 한 실험 = 한 폴더
│   ├── pipeline_state.yaml         [T1] --from 재개용 (mode·parent·phases)
│   ├── run.json                    [T1] **기계판독 run manifest** — S3/E1-3 출생(status:running) → E3 done+best. parent = 계보 엣지 SoT. _RUNLOG 가 사람용 거울 (§출력 데이터계약)
│   ├── metrics.jsonl               [T1] **per-step append-only 스트림** (한 줄 = {step,split,name,value,ts}) = 차트 SoT. train/eval logger 가 append
│   ├── REPORT.md                   [T1] **eval 최종 산출물** — 자체완결 정식 보고서(요약 top→배경·방법·결과·해석·결론·재현, figure 인라인)
│   ├── STORY.md                    [T1] narrative 누적 (motivation·이전/부모·이번·결과)
│   ├── experiment_spec.md          [T1] 1 화면 spec
│   ├── summary.md                  [T1] RUNLOG/parent auto-read 용 1줄 인덱스 (REPORT.md 포인터 — deliverable 아님)
│   ├── train.py / eval.py / config.yaml  [T1] scaffold (setup 산출)
│   ├── runs/                       [T2] 각 run 의 결과 (사용자 실행 산출)
│   │   └── run-001/
│   │       ├── ckpt/
│   │       ├── log.txt
│   │       └── eval_result.json    ← (옵션) per-run 단발 eval 결과 blob — **`metrics.json(l)` 명명 금지** (per-step 스트림 = root metrics.jsonl)
│   ├── figures/                    [T2] plot (자료팀 산출)
│   ├── report/                     [T2] iframe 렌더 HTML — audio/media 재생(lab E3-5 report.html) + rich prose(autopilot-draft/design 산출). 대시보드 GET /report
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
    ├── run.json                    ← 기계판독 run manifest (출생→done+best; parent = 계보 SoT)
    ├── metrics.jsonl               ← per-step append-only 스트림 (차트 SoT)
    ├── REPORT.md                   ← eval 최종 산출물 (자체완결 보고서)
    ├── experiment_spec.md
    ├── summary.md                  ← 1줄 인덱스 (REPORT.md 포인터)
    ├── STORY.md
    ├── runs/                       ← 실험 log·ckpt·(옵션)eval_result.json
    ├── report/                     ← iframe 렌더 HTML (lab audio/media + draft/design prose)
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
parent: <slug 또는 null>        # 계보 (fine-tune base / 재평가 대상). 기계판독 SoT = run.json.parent — 이 값은 그 cross-ref/거울 (§출력 데이터계약)
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
- 단발 데이터 변환·정제 script (`autopilot-code --qa quick` 또는 메인 Claude 직접 — lab 모드 아님)
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
- summary → "_RUNLOG ✅ 완료 갱신 + run.json 최종화·dispatch emit. 다음 실험: <한 줄>"

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
