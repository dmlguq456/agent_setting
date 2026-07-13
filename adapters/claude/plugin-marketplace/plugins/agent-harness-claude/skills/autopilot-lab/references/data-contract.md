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
