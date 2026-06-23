# 축 3 — 실험 추적/대시보드 (TensorBoard 류, 로컬·파일기반)

> **목표 렌즈**: 이미 디스크에 쌓이는 append-only 실험 로그 (`.claude_reports/experiments/{date}_{slug}/_RUNLOG.md` — timeline + parent 링크) 를 **TensorBoard 처럼 라이브 차트화 + run 비교/계보 렌더** 하는 경량 임베드 컴포넌트를 찾는다. 통째 tracking 서버 (별도 DB·데몬 강제) 는 적합도 하향. local-first · BYOK · Next.js 임베드 가능 · 디스크=상태(append-only 선호) · 라이선스 명확(MIT/Apache).
>
> **메타데이터 출처**: GitHub REST API 실측 (`api.github.com/repos/...`, 2026-06-23 기준) + README/소스 WebFetch. 못 구한 값은 (미확인) 표기.
>
> **이 축은 OD/OCD (open-design / open-codesign) 대응물이 없음** (둘 다 디자인 도구) — 각 후보를 "_내 _RUNLOG/jsonl 디스크 로그를 라이브 차트화_" 목표에 얼마나 바로 쓰는지로만 평가.

---

## 후보 1 — aim (aimhubio/aim)

- **레포**: [aimhubio/aim](https://github.com/aimhubio/aim) — ⭐6,169 · Apache-2.0 · push 2026-06-22 · archived=false
- **한 줄 정체**: RocksDB 기반 임베디드 스토리지 + FastAPI 서버 + React UI 로 된 풀 오픈소스 실험 추적기. "TensorBoard alternative" 를 표방.
- **데이터 계약(메트릭 스키마)**: **자체 RocksDB 임베디드 스토리지** (schemaless key-value). aim repository = 개별 RocksDB DB 들의 모음, run 마다 Meta container(params/metadata) + Sequence container(value series) 두 컨테이너 생성. 커스텀 인코딩 레이어가 계층 데이터를 KV 로 변환. → **jsonl/append-only 텍스트가 아님**. 내 `_RUNLOG.md` 를 직접 못 먹음; aim SDK (`aim.Run().track()`) 로 별도 적재 필요.
- **라이브 tail-follow**: RocksDB 임베디드 읽기 + FastAPI 서버가 UI 에 push. 파일 tail 메커니즘이 아니라 SDK→스토리지→서버 경로.
- **비교/계보 UI**: run 비교 강력 (다중 run 오버레이, group/aggregate). lineage(parent-child) 는 명시적 ablation tree 보다는 tag/param 기반 grouping 쪽.
- **대용량 다운샘플**: "최대 5M step sequence 지원" (2022-06 출시) 명시. 다운샘플 전략 내장 (구체 알고리즘은 미확인).
- **임베드 가능 여부**: **불가에 가까움 — 통째 서버 앱**. `aim up` = Python(FastAPI/uvicorn) 서버 + 번들된 React UI. 차트 컴포넌트만 떼서 Next.js 에 import 하는 공식 경로 없음. (이 축 핵심 기준에서 큰 감점.)
- **lift 할 구체 모듈/파일**: 직접 lift 보다는 _RocksDB 인코딩 레이어 설계_ (Meta/Sequence container 분리) 를 데이터 모델 참고용으로. 차트 UI 코드는 React 종속 + 서버 결합이라 발췌 난이도 높음.
- **적합도**: **중하** — 추적 기능은 성숙하나 통째 서버 + RocksDB 종속이라 "디스크 로그 임베드 차트" 목표와 어긋남.
- **채택 리스크**: RocksDB(aimrocks) 네이티브 종속 (NFS 비호환 이슈 보고됨), Python 서버 필수, 통째 채택 외 경로 빈약.

---

## 후보 2 — Trackio (gradio-app/trackio) ⭐축의 다크호스

- **레포**: [gradio-app/trackio](https://github.com/gradio-app/trackio) — ⭐1,542 · **MIT** · push 2026-06-18 · archived=false. (canonical = `gradio-app/trackio`, HF 제품. `tahjholden/trackio` 등은 fork.)
- **한 줄 정체**: HF 의 lightweight·local-first 실험 추적 라이브러리. **코어 < 3,000 줄 Python**, 대시보드는 Gradio + **Svelte 5**. wandb drop-in (`wandb.init/log/finish` API 호환).
- **데이터 계약(메트릭 스키마)**: **SQLite** (`.db` 파일, `TRACKIO_DIR`). `metrics(id, run_id, timestamp, run_name, step, metrics TEXT)` — metrics 컬럼은 JSON 텍스트. 부속 테이블 `configs`·`system_metrics`·`traces`·`alerts`. → **단일 파일 SQLite + JSON payload** = 내 선호(파일=상태)에 매우 근접. jsonl 은 아니지만 단일 `.db` 파일이라 서버 데몬 불필요.
- **라이브 tail-follow**: **SQLite WAL 모드** (`PRAGMA journal_mode=WAL`, non-Spaces) — 동시 write/read 비블로킹. 대시보드는 **mtime 기반 read 캐시 무효화** (`_LOGS_READ_CACHE` + `_sqlite_db_invalidation_mtime_ns`) 로 효율적 polling. → 별도 데몬 없이 파일 mtime 만으로 라이브 반영. 이 축 목표에 거의 정확히 부합.
- **비교/계보 UI**: 다중 run 비교 대시보드 내장. lineage(parent-child) 는 미확인 — wandb 식 flat run 모델에 가까움 (내 `_RUNLOG` parent 링크와 1:1 매핑은 직접 만들어야 함).
- **대용량 다운샘플**: (미확인) — 코어가 작아 다운샘플 정교함은 기대 낮음.
- **임베드 가능 여부**: **부분 가능** — 대시보드가 **Gradio 앱** 이라 Next.js 에 컴포넌트로 박기보다 iframe 임베드 또는 Svelte 5 프런트 발췌. 다만 **SQLite 스키마 + WAL+mtime polling 계약** 자체가 lift 대상으로 매우 깔끔 — 내가 동일 스키마로 `_RUNLOG` 를 적재하고 차트는 자체 엔진(uPlot/perspective)으로 그리는 그림이 자연스러움.
- **lift 할 구체 모듈/파일**: `trackio/sqlite_storage.py` (스키마 + WAL + mtime invalidation 패턴) 가 **데이터수집 계약의 레퍼런스**. wandb-호환 `init/log/finish` 표면도 참고. 차트 UI 는 Svelte 라 그대로보다 패턴만.
- **적합도**: **상 (데이터 계약 측면)** — 단일 SQLite 파일 + WAL + mtime polling = "디스크=상태, 데몬 없음" 목표의 정확한 구현체. < 3000줄이라 통독·발췌 현실적.
- **채택 리스크**: 신생(2025) — 성숙도·계보 UI 약함. 대시보드 자체는 Gradio 결합이라 Next.js 네이티브 임베드엔 프런트 재작성 필요. 하지만 **스토리지 계약 lift** 만 노리면 리스크 낮음.

---

## 후보 3 — ClearML (clearml/clearml + clearml-server)

- **레포**: [clearml/clearml](https://github.com/clearml/clearml) — ⭐6,740 · Apache-2.0 · push 2026-06-18 · archived=false. 서버: [clearml/clearml-server](https://github.com/clearml/clearml-server).
- **한 줄 정체**: 실험관리 + 데이터관리 + 파이프라인 + 오케스트레이션 + 서빙을 한 번에 묶은 풀 MLOps 플랫폼.
- **데이터 계약(메트릭 스키마)**: 서버 백엔드 = **MongoDB(메타) + Elasticsearch(메트릭/스칼라 시계열) + Redis(캐시/큐)**. → 파일 기반 아님. SDK 가 서버 API 로 전송.
- **라이브 tail-follow**: SDK→API server→ES 적재, WebUI 가 조회. 파일 tail 개념 없음.
- **비교/계보 UI**: run 비교·파이프라인 DAG·lineage 매우 강력 (전체 플랫폼급).
- **대용량 다운샘플**: ES 기반 집계로 처리 (구체 미확인). 대용량엔 강함.
- **임베드 가능 여부**: **불가 — 통째 멀티서비스 서버**. self-host = docker-compose 로 MongoDB+ES+Redis+API+WebUI 5종, **최소 8GB(권장 16GB) RAM**, `vm.max_map_count` 튜닝 필요. Next.js 임베드 대상 아님.
- **lift 할 구체 모듈/파일**: 없음 (아키텍처가 무거워 발췌 비현실적). 기능 레퍼런스로만.
- **적합도**: **하** — local-first/디스크=상태/임베드 모든 핵심 제약 위반. 데몬+3 DB 강제.
- **채택 리스크**: 종속성 무게 최상 (ES+Mongo+Redis 데몬). 본 목적에 과도.

---

## 후보 4 — Weights & Biases OSS 부분 (wandb/*)

- **레포**: [wandb/wandb](https://github.com/wandb/wandb) — ⭐11,138 · **MIT** · push 2026-06-23 · archived=false. 관련: [wandb/server](https://github.com/wandb/server) (self-host, MIT LICENSE), [wandb/weave](https://github.com/wandb/weave), `wandb-core`(MIT, PyPI).
- **한 줄 정체**: 클라이언트 SDK 는 MIT 오픈, 그러나 **백엔드 서버(`wandb/local` 도커 이미지) 는 클로즈드 바이너리** (무료는 4 user 제한, 프로덕션 기능은 라이선스 구매).
- **데이터 계약(메트릭 스키마)**: SDK 가 로컬에 `.wandb` 바이너리(transaction log)로 적재 후 서버로 sync. 스키마는 비공개 바이너리. → 파일은 있으나 _자체 binary_ 라 외부 파싱 비현실.
- **라이브 tail-follow**: SDK→서버 sync. 오픈된 tail 경로 없음.
- **비교/계보 UI**: 업계 표준급 비교/스윕/lineage — 그러나 **UI 는 클로즈드 서버 측**.
- **대용량 다운샘플**: 서버 측 (클로즈드).
- **임베드 가능 여부**: **불가** — UI/서버가 OSS 아님. `wandb-core`/`weave` 는 OSS 지만 _차트 대시보드_ 가 아니라 SDK 백엔드/GenAI 관측 툴킷이라 이 축 목표와 무관.
- **lift 할 구체 모듈/파일**: 차트/대시보드 관점에선 없음. (OSS 부분은 SDK·weave 로, 본 축 외.)
- **적합도**: **하** — 핵심 가치인 대시보드 UI 가 비공개. wandb-호환 _API 표면_ 만 참고 가치 (그건 Trackio 가 이미 OSS 로 모사).
- **채택 리스크**: 라이선스 분리 (SDK 오픈/서버 클로즈드) — lift 대상 자체가 없음.

---

## 후보 5 — MLflow tracking UI (mlflow/mlflow)

- **레포**: [mlflow/mlflow](https://github.com/mlflow/mlflow) — ⭐26,694 · Apache-2.0 · push 2026-06-23 · archived=false.
- **한 줄 정체**: 가장 큰 OSS ML 플랫폼. tracking server(FastAPI) + React UI + backend store.
- **데이터 계약(메트릭 스키마)**: 백엔드 store 2 종 — **file store(`./mlruns` 디렉터리, 파일 기반!)** 또는 **DB store(기본 `sqlite:///mlflow.db`)**. file store 는 run 별 디렉터리에 metric/param/tag 를 텍스트 파일로 적재 (metric = `step value timestamp` 줄 추가 = **append-only 텍스트 라인**!). → **file store 가 내 선호와 정확히 일치** (다만 공식적으로 maintenance mode, DB 권장).
- **라이브 tail-follow**: file store 면 디렉터리/파일 read (mtime), DB store 면 SQLite 조회. UI 가 polling. 명시적 inotify/websocket 라이브 stream 은 아님.
- **비교/계보 UI**: run 비교 테이블·차트 오버레이 내장. parent-child run (nested runs) 지원 — **내 `_RUNLOG` parent 링크와 매핑 가능한 nested run 모델 있음**.
- **대용량 다운샘플**: UI 차트가 일정 포인트 초과 시 다운샘플 (구체 미확인).
- **임베드 가능 여부**: **부분 — UI 는 React 서버 앱** (`mlflow ui`, port 5000, FastAPI). 컴포넌트 발췌보다 통째 실행 또는 iframe. 단 **file-store 포맷 + REST API** 는 공개 계약이라 lift 가치 있음.
- **lift 할 구체 모듈/파일**: **file store 의 metric 라인 포맷** (`mlruns/<exp>/<run>/metrics/<key>` = append-only `timestamp value step` 줄) 이 데이터 계약 레퍼런스. tracking REST API 스키마도 표준.
- **적합도**: **중** — file store append-only 포맷 + nested run lineage 는 매력적이나, UI 자체는 무거운 React 앱이라 임베드 X. 데이터 계약 레퍼런스로는 Trackio 와 양강.
- **채택 리스크**: 전체 패키지 무거움(에이전트/LLM 기능까지 번들). file store 는 maintenance mode (장기 신뢰 ↓). UI lift 비현실.

---

## 후보 6 — sacred + omniboard (IDSIA/sacred + vivekratnavel/omniboard)

- **레포**: [IDSIA/sacred](https://github.com/IDSIA/sacred) — ⭐4,366 · MIT · push 2025-10-22 · archived=false. [vivekratnavel/omniboard](https://github.com/vivekratnavel/omniboard) — ⭐548 · MIT · **push 2023-02-01(정체)** · archived=false.
- **한 줄 정체**: sacred = 실험 config/로그/재현 도구, omniboard = sacred 용 웹 대시보드(MongoDB observer 조회).
- **데이터 계약(메트릭 스키마)**: sacred observer 가 보통 **MongoDB** 에 적재 (FileStorageObserver 로 JSON 파일도 가능하나 omniboard 는 Mongo 전제). → omniboard 라이브 차트는 **MongoDB 필수**.
- **라이브 tail-follow**: omniboard 가 Mongo 폴링.
- **비교/계보 UI**: omniboard 가 run 비교·metric 차트 제공. lineage 약함.
- **대용량 다운샘플**: (미확인, 약할 것).
- **임베드 가능 여부**: **불가에 가까움** — omniboard 는 Node+React 통째 앱 + MongoDB 종속. sacred 의 FileStorageObserver(JSON) 만 데이터 계약 참고 가능.
- **lift 할 구체 모듈/파일**: sacred `FileStorageObserver` 의 run dir JSON 레이아웃(config.json/run.json/metrics.json) 정도. omniboard 차트는 Mongo 결합이라 발췌 난이도 높음.
- **적합도**: **하** — omniboard 정체(2023 마지막 push) + Mongo 종속. 임베드 부적합.
- **채택 리스크**: omniboard 유지보수 정체, MongoDB 데몬 강제.

---

## 후보 7 — tensorboard tfevents 포맷 + 독립 파서

- **tensorflow/tensorboard**: [tensorflow/tensorboard](https://github.com/tensorflow/tensorboard) — ⭐7,192 · Apache-2.0 · push 2026-06-19. **tfevents 포맷** = TFRecord(길이+CRC32C+payload) 안에 **protobuf `Event`/`Summary`** 직렬화. scalar 는 `Summary.Value` 로 인코딩. → **protobuf-in-TFRecord binary**. append-only 이긴 하나(이벤트가 줄줄이 append) 텍스트가 아니라 protobuf binary.
- **tbparse**: [j3soon/tbparse](https://github.com/j3soon/tbparse) — ⭐209 · Apache-2.0 · push 2024-08-16. **순수 Python, 서버 없음**. `SummaryReader(log_dir).scalars → pandas DataFrame`. TF 는 image/audio 에만 필요, **scalar/tensor/histogram 은 tensorflow 없이 파싱**. PyTorch/TF/tensorboardX 이벤트 지원.
- **tensorboard-aggregator**: [Spenhouet/tensorboard-aggregator](https://github.com/Spenhouet/tensorboard-aggregator) — ⭐173 · MIT · push 2025-05-29. 다중 tb run 을 summary/CSV 로 집계.

- **데이터 계약**: protobuf-in-TFRecord (tfevents) — 표준이지만 내 선호(jsonl/텍스트)와 거리. 단 **PyTorch `SummaryWriter`/tensorboardX 로 적으면 생태계가 거대** = 표준 채택의 안전판.
- **라이브 tail-follow**: TensorBoard 자체가 logdir 폴링으로 tfevents append 를 라이브 반영 (검증된 메커니즘). tbparse 는 1회 read.
- **비교/계보 UI**: TensorBoard run 비교 강력. lineage 는 약함(run = logdir).
- **대용량 다운샘플**: TensorBoard 가 scalar reservoir sampling(다운샘플) 내장 — **대용량 다운샘플의 검증된 레퍼런스**.
- **임베드 가능 여부**: TensorBoard 자체는 무거운 서버 앱(불가). 하지만 **tbparse 로 tfevents→DataFrame→자체 차트** 경로가 현실적 — 파서는 라이브러리라 임베드 파이프라인에 박기 좋음.
- **lift 할 구체 모듈/파일**: **tbparse `SummaryReader`** (tfevents 파싱을 라이브러리로 흡수) + TensorBoard 의 **reservoir sampling 다운샘플 아이디어**. tfevents writer 는 tensorboardX 로 외부 의존.
- **적합도**: **중** — "이미 tfevents 가 있으면" 라이브 차트화에 tbparse 가 깔끔한 어댑터. 다만 내 `_RUNLOG` 는 tfevents 가 아니라 직접 적용은 변환 한 겹 필요. 표준 포맷 호환 어댑터로서 가치.
- **채택 리스크**: tbparse 는 소규모(⭐209, 2024 push) + tensorboard 라이브러리 의존. binary 포맷이라 jsonl 선호와 불일치.

---

## 후보 8 — 차트 엔진 (uPlot / perspective)

### leeoniya/uPlot
- **레포**: [leeoniya/uPlot](https://github.com/leeoniya/uPlot) — ⭐10,256 · **MIT** · push 2026-04-22 · archived=false.
- **한 줄 정체**: 의존성 0 의 초경량 Canvas2D 시계열 차트 (~48KB min). line/area/ohlc/bars.
- **데이터 계약**: 데이터 무관 — `[xs[], ys[]...]` 배열을 넘기면 됨. 메트릭 스키마는 내가 정함.
- **라이브 tail-follow**: `setData()` 호출로 실시간 갱신 (mechanism 은 내가 결선 — Trackio/file polling 과 조합).
- **비교/계보 UI**: 없음 — 순수 차트 프리미티브. 비교 UI 는 내가 구성.
- **대용량 다운샘플**: **내장 없음** — "aggregation 은 미리 하라" 명시. 단 성능 압도적(166K pts 25ms, ~100K pts/ms cold 후). 다운샘플은 내가 (서버측/Trackio 스키마에서) 처리.
- **임베드 가능 여부**: **상 — 완벽** . 의존성 0, React/Vue/Svelte 래퍼 존재, Next.js 에 그대로 import. 이 축의 _차트 빌딩블록_ 으로 최적.
- **lift 할 구체 모듈/파일**: uPlot 코어 그대로 npm 의존 + React 래퍼(`uplot-react` 등). 발췌가 아니라 dependency 로 채택.
- **적합도**: **상 (차트 엔진 측면)** — local-first·임베드·MIT·경량 모든 제약 만족. 데이터 준비만 내가 하면 됨.
- **채택 리스크**: 매우 낮음 — 성숙·소형·무의존. 다운샘플/비교 UI 는 직접 구현 부담(그러나 작음).

### finos/perspective
- **레포**: [finos/perspective](https://github.com/finos/perspective) — ⭐~11,000 · Apache-2.0 · 최신 v4.5.1(2026-05-31). (API 메타 일시 실패 → WebFetch 실측.)
- **한 줄 정체**: 대용량·스트리밍 데이터용 인터랙티브 분석/시각화 컴포넌트 (`<perspective-viewer>` 웹컴포넌트 + WASM 데이터 엔진).
- **데이터 계약**: **Apache Arrow**(read/write/stream) + CSV/JSON. columnar. → Arrow 스키마면 강력하나 내 텍스트 로그와 거리 한 겹.
- **라이브 tail-follow**: WASM 스트리밍 데이터 모델 + WebSocket(원격 서버 모드) 로 실시간 업데이트 1급 지원.
- **비교/계보 UI**: pivot/group/filter 가 강력 (run 비교를 pivot 으로 구성 가능). lineage 전용 UI 는 아님.
- **대용량 다운샘플**: **WASM columnar 엔진이 대용량/스트리밍을 1급으로 처리** — 수백만 포인트에 강함(이 축에서 uPlot 의 약점을 보완).
- **임베드 가능 여부**: **상 — 웹컴포넌트** (`<perspective-viewer>`) 로 Next.js 임베드 명시 지원. Python/Node/Rust 바인딩도 있으나 클라이언트 WASM 만으로 동작 가능.
- **lift 할 구체 모듈/파일**: `@finos/perspective` + `@finos/perspective-viewer`(+`-viewer-d3fc`) npm 패키지 — dependency 채택. Arrow 어댑터.
- **적합도**: **중상 (대용량 차트 엔진 측면)** — 임베드·대용량·스트리밍 강점. 단 WASM 무게(번들 큼) + Arrow 데이터 준비 오버헤드가 uPlot 대비 부담. "수백만 포인트가 정말 필요할 때" 의 상위 옵션.
- **채택 리스크**: 번들 크기(WASM), Arrow 변환 레이어 필요. 경량 목표엔 uPlot 이 1순위, perspective 는 대용량 확장 시 백업.

---

## 축 3 비교표

| 후보 | stars | license | 데이터 계약 | tail-follow | 임베드 가능 | 적합도 |
|---|---|---|---|---|---|---|
| **aim** | 6.2k | Apache-2.0 | RocksDB 임베디드 (자체 KV) | SDK→FastAPI push | 통째 서버 (불가) | 중하 |
| **Trackio** | 1.5k | MIT | **단일 SQLite(.db) + JSON payload** | **WAL + mtime polling** | 부분(Gradio/Svelte) · 스토리지 계약 lift 깔끔 | **상(계약)** |
| **ClearML** | 6.7k | Apache-2.0 | Mongo+ES+Redis | SDK→API→ES | 통째 멀티서비스(불가) | 하 |
| **wandb OSS** | 11.1k | MIT(SDK)/closed(서버) | `.wandb` 자체 binary | SDK→서버 sync | UI 비공개(불가) | 하 |
| **MLflow** | 26.7k | Apache-2.0 | **file store(append-only 텍스트)** 또는 SQLite | dir/DB polling | UI=React 서버(부분) · file 포맷 lift | 중 |
| **sacred+omniboard** | 4.4k/548 | MIT/MIT | MongoDB(or JSON observer) | Mongo polling | omniboard 통째+Mongo(불가) | 하 |
| **tfevents+tbparse** | 7.2k/209 | Apache-2.0 | protobuf-in-TFRecord (binary) | logdir polling(TB) | tbparse=라이브러리(가능) · TB=서버(불가) | 중 |
| **uPlot** | 10.3k | MIT | 데이터무관(배열) | `setData()` (내가 결선) | **상(의존성0, Next.js native)** | **상(차트엔진)** |
| **perspective** | ~11k | Apache-2.0 | Arrow/CSV/JSON(columnar) | WASM stream / WebSocket | **상(웹컴포넌트)** · 대용량 1급 | 중상(대용량 백업) |

---

## 축 3 단독 1픽

이 축은 **두 역할**이 분리되므로 1픽도 둘로 나눈다 (둘 다 필요):

### (a) 데이터수집 계약 1픽 — **Trackio (gradio-app/trackio)** 의 `sqlite_storage.py` 패턴
- **이유**: 내 제약(local-first·디스크=상태·데몬 없음·MIT) 에 가장 정확히 부합하는 _구현된 계약_. **단일 SQLite `.db` 파일 + WAL + mtime 기반 read 캐시 무효화** = 별도 DB 서버/데몬 없이 라이브 tail 을 이미 푼 레퍼런스다. 코어 < 3,000줄이라 통독·발췌가 현실적이고, wandb-호환 API 표면도 덤. 내 `_RUNLOG`/jsonl 을 이 스키마(`metrics(run_id, step, timestamp, metrics_json)`)로 적재 → 차트는 자체 엔진으로 그리는 그림이 가장 깔끔.
- **차점**: MLflow **file store 의 append-only 텍스트 metric 라인** + nested-run lineage 모델 (내 `_RUNLOG` parent 링크와 1:1 매핑되는 유일한 후보) — 텍스트 append 선호가 SQLite 보다 강하면 이쪽. tfevents+tbparse 는 "PyTorch SummaryWriter 표준 호환이 필요할 때" 의 어댑터 백업.

### (b) 차트 엔진 1픽 — **uPlot (leeoniya/uPlot)**
- **이유**: 의존성 0·~48KB·MIT·Next.js native import·압도적 성능(100K pts/ms). 데이터 무관이라 위 (a) 계약에서 뽑은 배열을 그대로 `setData()` 로 라이브 갱신. 통째 서버 채택이 아니라 _빌딩블록 dependency_ 라는 이 축 핵심 제약에 완벽 부합.
- **백업/확장**: **perspective** — 정말 수백만 포인트·스트리밍 pivot 비교가 필요해지면 WASM columnar 엔진(`<perspective-viewer>` 웹컴포넌트)으로 격상. 단 WASM 번들 무게 + Arrow 변환 오버헤드라 1순위는 uPlot, perspective 는 대용량 한계 도달 시 백업.

---

## 축 3 핵심 takeaway

**통째 tracking 서버(aim·ClearML·wandb·MLflow UI·omniboard)는 전부 임베드·local-first 제약에서 탈락 — 정답은 "조립": Trackio 의 단일-SQLite+WAL+mtime polling _데이터 계약_ 을 lift 해 디스크 로그를 적재하고, 의존성 0 의 uPlot 으로 Next.js 안에서 라이브 차트화하며(대용량 시 perspective 백업), tfevents 호환이 필요하면 tbparse 한 겹을 어댑터로 끼운다.**

---

### Sources
- GitHub REST API (api.github.com/repos/*) 메타데이터, 2026-06-23 실측
- [gradio-app/trackio](https://github.com/gradio-app/trackio) · [sqlite_storage.py](https://github.com/gradio-app/trackio/blob/main/trackio/sqlite_storage.py) · [Trackio docs](https://huggingface.co/docs/trackio/index) · [HF blog](https://huggingface.co/blog/trackio)
- [aimhubio/aim](https://github.com/aimhubio/aim) · [Aim storage docs](https://aimstack.readthedocs.io/en/stable/guides/deep_dive/storage.html)
- [clearml/clearml](https://github.com/clearml/clearml) · [clearml-server](https://github.com/clearml/clearml-server) · [ClearML config docs](https://clear.ml/docs/latest/docs/deploying_clearml/clearml_server_config/)
- [wandb/wandb](https://github.com/wandb/wandb) · [wandb/server](https://github.com/wandb/server) · [wandb/weave](https://github.com/wandb/weave)
- [mlflow/mlflow](https://github.com/mlflow/mlflow) · [MLflow backend stores](https://mlflow.org/docs/latest/tracking/backend-stores)
- [IDSIA/sacred](https://github.com/IDSIA/sacred) · [vivekratnavel/omniboard](https://github.com/vivekratnavel/omniboard)
- [tensorflow/tensorboard](https://github.com/tensorflow/tensorboard) · [j3soon/tbparse](https://github.com/j3soon/tbparse) · [Spenhouet/tensorboard-aggregator](https://github.com/Spenhouet/tensorboard-aggregator)
- [leeoniya/uPlot](https://github.com/leeoniya/uPlot) · [finos/perspective](https://github.com/finos/perspective)
