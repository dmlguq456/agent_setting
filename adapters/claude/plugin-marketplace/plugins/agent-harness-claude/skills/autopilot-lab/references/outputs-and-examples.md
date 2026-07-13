## 산출물 구조

```
<artifact-root>/experiments/
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

<artifact-root>/experiments/
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
<artifact-root>/experiments/{date}_{slug}/ -- ✅ {mode}:{phase} 단계 완료
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
