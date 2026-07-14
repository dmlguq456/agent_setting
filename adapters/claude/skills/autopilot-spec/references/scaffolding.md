### Step 4: Scaffolding + Skeleton 코드 생성 (mode 5종 통일)

> **Stage-dispatch (`standard+`, OPERATIONS §5.10 ③④·SD-1·SD-2)**: autopilot-spec 는 비대칭 — PRD 작성은 conductor-inline (conductor 가 `spec/prd.md` 를 직접 쓰고 그 자체가 conductor 의 판단 자리라 dispatch 되는 stage 아님). 유일하게 명확한 dispatchable stage 는 **scaffold** (개발팀 new-lib) — 분리 가능한 artifact-producing stage: `standard+` 자리에서 **depth-2 headless session** 으로 dispatch, **file-only handoff** (입력은 파일에서 읽고 이전 stage 대화는 절대 참조 X) — depth-1 conductor 는 path 만 넘기고 verdict/status 만 읽는다. `direct/quick` 은 inline 유지, stage session 은 재dispatch 안 함 (depth 3+ 금지). 모든 pipe 가 4 단계 대칭 구조인 건 아니다 — per-pipe 본문 rewrite 는 후속 과제.

#### stage-worker 매핑

| stage | in-session team | input artifacts | output artifacts | write class |
|---|---|---|---|---|
| PRD authoring | conductor-inline (N/A) | research/analysis 산출 | `spec/prd.md` | conductor-inline (not dispatched) |
| scaffold (Phase 2) | 개발팀 new-lib | `prd.md` | scaffolded source/dirs | scaffold source |

mode 5종 모두 scaffold 단계 통일 — 빈 자리에서도 _뼈대 + skeleton_ 까지 spec 단에서 완성, 이후 autopilot-code 는 _layout 위 logic 추가_ 자리만 담당. _기존 repo 최대 활용_ — autopilot-research 의 외부 ref 또는 사용자 코드베이스의 내부 유사 모델이 1순위, generic skeleton 은 마지막 fallback.

#### Phase 0: ref source 결정 + 컨펌

자료 우선순위 (높을수록 우선):

| 순위 | source | 자리 |
|---|---|---|
| 1 | 내부 — `analysis_project/code/similar_models.md` 또는 사용자 `--ref <path>` 명시 | 같은 코드베이스 안 가장 유사 자리 — 컨벤션 정합 100% |
| 2 | 외부 — `research/{topic}/code_resources/` (autopilot-research 의 repo 카드) 또는 `07_resources.md` (pre-trained ckpt URL) 또는 사용자 `--ref <url>` 명시 | research 산출. paper 의 official repo / HF transformers / espnet / lightning 등 |
| 3 | Generic skeleton fallback | 1·2 모두 부재 자리만. 사용자 컨펌 후 진행 |

> **컨벤션 prepend 우선순위** — `analysis_project/code/experiment_conventions.md` (1순위 — per-project source of truth) + `mem profile 07_coding_convention` (`python3 <agent-home>/tools/memory/mem.py profile 07_coding_convention`) (2순위 — cross-project default, per-project 부재·빈 자리만 보강) 가 _ref source 우선순위와 독립_ 으로 매번 실행해 그 body 를 따름. Phase 2 (개발팀 new-lib prompt) 에 prepend — 충돌 자리는 per-project 우선, 본 프로젝트의 실제 컨벤션 침범 X.

```
=== ref source 결정 ===
mode: <list>
ref 1순위 (내부): <similar_models 추천 또는 --ref 명시 — 있으면>
ref 2순위 (외부): <research/code_resources / 07_resources 의 후보 — 있으면>
fallback: generic skeleton (위 둘 부재 자리만)

이 ref 로 진행? (진행 / 수정 — 다른 ref 명시 / 중단)
```

#### Phase 1: ref repo / ckpt 가져오기

| 자리 | 처리 |
|---|---|
| Public git repo (GitHub / GitLab) | Bash `git clone <url> /tmp/<name>_ref` 자동 |
| HF model / dataset | `huggingface-cli download X/Y` 또는 HF MCP |
| 로컬 path (similar_models / `--ref <path>`) | path 그대로 |

private repo 자리는 사용자가 자기 환경에서 미리 clone 한 후 `--ref <local-path>` 로 명시 → _로컬 path_ 자리 흡수 (본 skill 안 처리 X).

#### Phase 1.5 (신설): Pretrained ckpt 사전 동작 점검

ML / DL 자리 default — 학습·재학습 시작 _전_ 에 _ref 가 빈 자리에서 동작하는지_ 검증. _학습은 비싸니 inference 1 sample 로 먼저_ 확인.

점검 흐름:
1. ckpt URL / path 확인 (Phase 0 의 외부 ref source 또는 사용자 명시)
2. ref repo 의 inference 명령 추출 — autopilot-research 의 `07_resources` / `06_implementation` 에 _Quick verify 명령_ 누적되어 있으면 그대로 사용. 없으면 ref repo 의 README / `inference.py` / `demo.py` 자동 추출
3. 1 sample inference 실행 — Bash 직접 또는 테스트팀 _smoke_ 모드 호출
4. 통과 기준 — 에러 없이 끝남 + 출력 shape / 값 reasonable
5. 결과 보고 + 사용자 컨펌

```
=== Pretrained ckpt 사전 동작 점검 ===
ckpt: <URL or path>
inference 명령: <한 줄>
결과: ✅ 통과 (output shape <X> / 값 reasonable) | ❌ 실패 (root cause: <한 줄>)

(통과 → Phase 2 진행 / 실패 → 다른 ref / 그대로 진행 / 중단)
```

**Phase 1.5 는 ML / DL 자리 default 필수** — ckpt 자리는 _사전 검증 무조건_. 학습·재학습 비용 큰 자리라 _ckpt 가 빈 자리에서 동작_ 확인 후 진입.

자동 skip 자리 (좁게):

| 자리 | 사유 |
|---|---|
| mode `library` / `api` / `cli` 의 _코드만 가져오는 자리_ | ckpt 없으면 검증 대상 X |
| 사용자 코드베이스의 similar_models 자리 (이미 동작 확인된 내부 ref) | 재검증 무의미 |
| Disk / network 한계 자리 — ckpt 가 매우 무거움 (예: 100 GB+, 또는 사용자 환경 disk 부족) | 사용자 발화로 명시 skip 가능 (`"ckpt 너무 무거우니 검증 skip"` / `--no-verify`). 단 _default 는 검증_. ckpt size 가 사용자 환경 한계 초과 인지되면 메인 에이전트가 _skip 권유_ 한 줄 — 사용자 컨펌 |

_가벼운 ckpt_ (수십 MB ~ 수 GB 자리) 는 _사용자 발화 skip 요청 무시_ — 검증 강제. ML 자리에서 빈 자리 baseline 의 _ref ckpt 가 빈 자리에서 안 도는데 fine-tuning 시작_ 자리 사용자 보호 가치 크다.

#### Phase 2: 우리 컨벤션 으로 옮기기 (개발팀 new-lib)

```
Agent(개발팀, mode="new-lib"):
  "Mode: scaffold for {target_mode}.
   ref source: {ref_path}
   대상 폴더: spec/ + (mode 별 자리)

   ## 코드 수정 4 원칙 (필수 준수)
   1. 최소 수정 — ref 의 _필요 자리만_ 복사 후 우리 컨벤션 으로 옮김
   2. 원래 layer 1순위 — experiment_conventions.md 의 preferred layer (per-project 1순위) + mem profile 07_coding_convention (cross-project default, 보강) 사용. 충돌 자리는 per-project 우선
   3. 마이너 변경 = config — model.py 수정 X
   4. 변형 prefix — fine-tuning 변형은 experiment_conventions.md 의 prefix 패턴 따름 (per-project 부재면 mem profile 07_coding_convention 의 패턴 — 예: _ft01_)

   ## 본 프로젝트 컨벤션 (1순위 — source of truth)
   {analysis_project/code/experiment_conventions.md 의 컨벤션 인용 — 있으면}

   ## 사용자 cross-project default (2순위 — per-project 부재·빈 자리만 보강)
   {mem profile 07_coding_convention 의 model 폴더 / config / prefix / preferred layer / framework 인용 — per-project 와 충돌 시 per-project 우선}

   ## mode 별 scaffold 산출물
   {mode_specific_outputs}

   ## 안 함
   - 새 layer 도입 (preferred layer list 외)
   - ref repo 의 _불필요 자리_ (다른 dataset 전용 / 다른 task / experiment 자국)
   - 라이브러리화·정련 (autopilot-code 영역)

   Return: 생성 파일 list + 요약."
```

mode 별 scaffold 산출물:

| mode | 산출물 |
|---|---|
| **app** | (현행) `create-next-app` + `prisma/schema.prisma` + 빈 page routes + 기본 layout |
| **library** | `pyproject.toml` / `setup.py` + `src/<pkg>/__init__.py` 의 공개 API skeleton + ref 의 export 구조 |
| **api** | `app/main.py` (FastAPI) 또는 `index.ts` (Express) + router skeleton + ref 의 middleware·auth 구조 |
| **cli** | `cli.py` (argparse / typer) entry + 명령·서브명령 skeleton + ref 의 명령 구조 |
| **research** | `train.py` / `eval.py` / `config.yaml` / `model/<name>/` skeleton + ref 의 training loop·model layer 구조 (preferred layer 만 + inference 가능 자리까지) |

복합 mode (`research,cli`) 면 _두 자리 모두 scaffold_.

#### Phase 3: skeleton 결과 컨펌

```
=== Scaffold 결과 ===
mode: <list>
ref source: <내부 / 외부 / generic>
생성 파일:
  <list>

(app mode) scaffolding 명령: create-next-app 등 실행됨 ✓
(research mode) Phase 1.5 ckpt 점검 결과: ✅ 통과 / ❌ 실패 / skip

(진행 — Step 5 spec 완성 / 수정 — scaffold 다시 / back-jump Phase 0 / 중단)
```

### Step 5: [CONFIRM Gate — refine 진입 가능]

```
Spec 완성:
  mode: <list>
  주요 결정: <요약 3-5 bullet>

(진행 — autopilot-design 또는 autopilot-code / 수정 — refine v2 / 중단)
```

`--user-refine` on 또는 사용자 _수정_ 발화 시 PRD refine loop.
