---
name: autopilot-lab
description: "빠른 실험 prototype entry — 학습 세팅(setup)과 ckpt 평가(eval) 앞뒤를 돕는다"
argument-hint: "<task description> [--mode setup|eval|auto] [--parent <slug>] [--ref <similar-model-path>] [--intensity direct|quick|standard|strong|thorough|adversarial] [--qa quick|light|standard|thorough|adversarial] [--report] [--from spec|scaffold|run|eval|summary]"
metadata:
  group: entry
  fam: code
  modes: [setup, eval]
  blurb: "빠른 실험 prototype entry — 학습 세팅(setup)과 ckpt 평가(eval) 앞뒤를 돕는다"
---

> 산출물 폴더: `<artifact-root>/experiments/` ([CONVENTIONS.md §5](../../core/CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) 3-tier). _RUNLOG timeline 한 자리 + experiment 단위 폴더 누적.

## Required Reads

- 모든 호출: `references/auto-load-context.md` — Step 0 자동 read 목록(실험 컨벤션·`_RUNLOG`·직전/부모 실험·유사 모델·ready 점검 등) + 컨벤션·ready 부재/미흡 처리 흐름. 매 호출 시 이 컨텍스트를 먼저 로드해 사용자 재설명 부담을 없앤다.
- 기계판독 출력(`metrics.jsonl`·`run.json`·parent 계보·종료 dispatch·`report/`): `references/data-contract.md` — scaffold 의 logger, run.json 출생/갱신, dispatch emit 자리에서 참조.
- `--mode setup` (또는 auto→setup): `references/setup-procedure.md` (S1 spec → S2 scaffold → S3 run).
- `--mode eval` (또는 auto→eval): `references/eval-procedure.md` (E1 eval spec → E2 실행 → E3 분석·summary).
- 산출물 폴더 구조·`pipeline_state.yaml`·졸업 hand-off·Update memory·Return Format·Examples: `references/outputs-and-examples.md`.

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

**lab 은 main 이 아니라 _전용 worktree + 실험 브랜치_ 에서 진행한다.** 실험 시작 자리(setup, 또는 부모 없는 첫 eval)에서 main 워킹트리를 직접 건드리지 않고, [OPERATIONS §5.10](../../core/OPERATIONS.md) 명명 규칙대로 형제 worktree `<repo>-wt/<exp-slug>` 를 파고 그 안 실험 브랜치(`exp/<slug>` 또는 기존 feature 브랜치)에서 작업한다. 이미 해당 worktree·브랜치가 있으면 재사용.

### autopilot-code 의 worktree 와 결정적 차이

| | autopilot-code worktree | **autopilot-lab worktree+브랜치** |
|---|---|---|
| 성격 | **머지 전제 _임시_ 분사** — 격리해 작업 후 main 으로 merge, 브랜치는 수확 뒤 disposable | **머지 안 하는 _별도 작업 라인_** — 실험은 그 자체로 main 에 통째 들어가지 않는다 |
| main 청결 보장 | merge 후 브랜치 정리 | **"안 merge" 로 보장** (gitignore 아님) |
| 산출물 | 코드 변경 → main 의 일부가 됨 | 실험 config·scaffold·로그 → **브랜치에 남고 main 엔 안 감** |
| 수명 | 작업 1건 = 브랜치 1개, 짧게 | 실험 라인이 길게 유지 (계보 `--parent` 누적) |

### 따름 규칙

1. **실험 config 는 gitignore 하지 말고 _브랜치에 커밋_** — `_ft*`·`_tune_*`·`exp_*` 등 실험 config 는 그 브랜치에서 tracked. 어떤 config 가 어떤 결과를 냈는지 git 으로 재현 가능하게. (main 의 `.gitignore` 는 이들을 계속 ignore — main 청결은 _안 merge_ 가 보장.)
2. **무거운 산출물(ckpt·log·`<artifact-root>/`)은 브랜치에서도 gitignore 유지** — 재현 기록은 `<artifact-root>/experiments/{slug}/` (영속) + 커밋된 config 가 함께 담당.
3. **main 으로 가는 건 _졸업_ 뿐** — (a) 재사용 코드(seam·모듈)는 `autopilot-code` 로 main 졸업, (b) 이긴 config 는 영구 파일명으로 rename 해 졸업. 실험 브랜치 자체를 main 에 통째 merge 하지 않는다.
4. **브랜치는 실험 라인의 작업 공간** — archive 가 아니다. `<artifact-root>/experiments/` + 커밋된 config 가 archive 라 브랜치는 졸업 후 정리 가능.

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

## Default Invocation Rule (메인 에이전트 자동 라우팅)

본 skill 은 runtime adapter bootstrap 의 "autopilot-* 호출 패턴" 컨펌 의무 적용 대상(Claude Code: [`CLAUDE.md`](../../adapters/claude/CLAUDE.md) §0).

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

- 단발 데이터 정제·변환·script — _로그 남기고 싶으면_ `/autopilot-code --qa quick` (가벼운 plan + execute + test, `plans/` 에 로그). 진짜 throwaway(로그 불필요)만 메인 에이전트 직접. lab 모드 아님
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
- `quick` / `light` (default) / `standard` / `thorough` / `adversarial` — [CONVENTIONS.md §1](../../core/CONVENTIONS.md)
- 본 skill default 가 `light` 인 이유: 실험 prototype 은 _빠른 cycle_ 이 1순위. high-stakes 신호(논문 결과·외부 공개) 시 사용자가 standard+ 명시 또는 메인 에이전트 자동 상향.

### --from
- setup 모드: `spec` / `scaffold` / `run` — 단계 재개
- eval 모드: `eval` / `summary` — 단계 재개
- `pipeline_state.yaml` 발견 시 자동 추론

## 코드 수정 4 원칙 (sub-agent 호출 자리에 매번 prepend)

`analysis_project/code/experiment_conventions.md` (**1순위 — per-project 가 source of truth**) + `mem profile 07_coding_convention` (2순위 — cross-project default, per-project 부재·빈 자리만 보강) 의 _preferred layer / config 메커니즘 / prefix 패턴_ 을 source 로 다음 4 원칙을 개발팀 _new-lib_ mode prompt 에 매번 prepend. _충돌 자리는 per-project 우선_ — 본 프로젝트의 실제 컨벤션 침범 X.

1. **최소 수정** — 기존 모델 폴더 복사 후 변형 (`--ref` 또는 `similar_models.md` 추천). 새 layer 도입 default X
2. **원래 layer 1순위** — `experiment_conventions.md` 의 _preferred layer_ list 가 1순위. 새 layer 도입은 _명시 컨펌_ 필요
3. **마이너 변경 = config** — model.py 직접 수정 X, `config.yaml` 가능한 자리는 config 로
4. **변형 prefix** — fine-tuning 변형은 `experiment_conventions.md` 의 prefix 패턴 (예: `_ft01_`·`_ft02_`) 따라 base 파일 옆에 둠. 새 base 는 새 모델 폴더

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
- 단발 데이터 변환·정제 script (`autopilot-code --qa quick` 또는 메인 에이전트 직접 — lab 모드 아님)
- 실험 자동 실행·학습·평가 (사용자 환경·queue 가변 — 명령만 안내. 가벼운 eval 만 발화 시 테스트팀)
- ckpt·log destructive 삭제 (`_internal/` 외)

## Reference Map

- `references/auto-load-context.md`: Step 0 자동 read 컨텍스트 목록(per-project 컨벤션 1순위 / cross-project profile 2순위 등) + 컨벤션·ready 부재 자리 처리 + 실험 ready 미흡 보류 흐름.
- `references/data-contract.md`: 출력 데이터계약 — `metrics.jsonl` per-step append-only 스트림, `run.json` run manifest(출생→done+best), parent 계보 SoT, 종료 dispatch(방출만), `report/` iframe 렌더 규약.
- `references/setup-procedure.md`: setup 모드 절차 — S1 spec(worktree 확보·1 화면 컨펌·연구팀 plan-review) → S2 scaffold(개발팀 new-lib·4 원칙 prepend·metrics.jsonl logger) → S3 run 명령 안내·`_RUNLOG` ⏳ 대기·run.json 출생·smoke/ml-debug 옵션.
- `references/eval-procedure.md`: eval 모드 절차 — E1 eval spec(+eval-only `--parent` run.json 출생) → E2 eval 실행 안내 → E3 분석·figure-gen·paper 비교·`REPORT.md`·`summary`/`STORY`·`_RUNLOG` ✅·run.json done·dispatch emit.
- `references/outputs-and-examples.md`: `experiments/` 산출물 구조(폴더형·model/{name}형 2 컨벤션), `pipeline_state.yaml`, 졸업 자리(autopilot-code/spec hand-off), Update memory, Return Format, Examples 4개(lr sweep 사이클·MDTA ablation·fine-tune 계보·재평가).

## Task
$ARGUMENTS
