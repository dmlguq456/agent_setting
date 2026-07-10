## Argument Parsing

### --mode (auto-detect default)

| 값 | 의미 |
|---|---|
| `auto` (default) | 발화·코드 단서로 자동 추론. 단일 또는 복수 mode |
| `app` | 앱 spec — PRD + 스택 + scaffolding + skeleton |
| `library` | 라이브러리 spec — 공개 API + 사용 예시 + 호환성·versioning + module 구조 |
| `api` | API 서비스 spec — endpoint + auth + 데이터 모델 |
| `cli` | CLI spec — 명령·옵션·input/output |
| `research` | 연구 코드 spec — entry + configs + 재현 명령 + 예상 metric |
| `app,library` 등 콤마 | 복수 mode — 한 PRD 안 mode 별 독립 섹션 |

### 검증 강도 (intensity 파생)
- 검증 rigor 는 별도 `--qa` 축이 아니라 `--intensity` 에서 결정론적으로 파생된다 (default standard-tier) — tier 정의·매핑은 [CONVENTIONS.md §1.1](../../core/CONVENTIONS.md#11-verification-rigor-tiers-intensity-derived-canonical-sot) 단일 source.
- `--intensity quick` 는 작은 spec tweak·update mode 자리 권장 — refine 단계 skip / 1 라운드 강제. ad-hoc 직접 Edit 대신 quick 으로 돌려 snapshot·log artifact 를 남긴다.

### --user-refine
- PRD 작성 후 사용자 메모 받고 refine loop (`_internal/refine_v{N}.md` 백업)

## Mode 자동 추론 단서 (`auto` 기본)

| 단서 | 추론 mode |
|---|---|
| `package.json` 의 `bin` 필드 / `setup.py` 의 `entry_points` / `pyproject.toml` 의 `[project.scripts]` | **cli** |
| `package.json` 의 `main` / `exports` / `pyproject.toml` 의 `[project]` + `__init__.py` 의 명시 export | **library** |
| `argparse` / `click` / `commander` / `typer` import | **cli** |
| `configs/*.yaml` + 학습·평가 metric 출력 / `*.ipynb` | **research** |
| Next.js / Expo / SvelteKit / Astro / Vite + React framework | **app** |
| FastAPI / Express / Hono + UI 없음 | **api** |
| 발화 키워드 | 발화 mode |

자동 추론 결과는 _컨펌 한 줄_ 로 사용자 확인 후 진행:

```
=== mode 추론 ===
- 발화 "정돈·공개" + 기존 코드 분석:
  · train.py / eval.py + argparse  → cli ✓
  · configs/ + 학습 metric 출력      → research ✓
  · models/__init__.py 의 export    → library ✓ (옵션)

복합 mode: research + cli (+ library 옵션) — 이대로 진행?
(진행 / 수정 — mode 추가·제거 / 단일 mode 선택 / 중단)
```

## Context Auto-Detection (신규 vs 재진입 자동 분기 + 자료 자동 read)

본 skill 은 호출 자리에서 _발화 + cwd_ 검사로 자동 분기 + 다음 자료 자동 read:

| 자료 | 자리 | 우선순위 |
|---|---|---|
| `mem profile 07_coding_convention` (`python3 <agent-home>/tools/memory/mem.py profile 07_coding_convention`) | 사용자 cross-project 컨벤션 (model 폴더 / config / prefix / preferred layer / framework) | 2순위 (cross-project default·fallback) |
| `<artifact-root>/analysis_project/code/experiment_conventions.md` | per-project 컨벤션 (본 프로젝트 실제 자리) | **1순위** (충돌 시 per-project 우선, mem profile 07 은 빈 자리 보강) |
| `<artifact-root>/analysis_project/code/similar_models.md` | 본 프로젝트 모델 간 유사도 | scaffold Phase 0 의 ref 1순위 후보 |
| `<artifact-root>/research/<topic>/` | 외부 ref repo 카드 + 07_resources 의 Quick verify | scaffold Phase 0 의 ref 2순위 + Phase 1.5 검증 source |

### 1단계 — pipeline_state.yaml 자동 검사

| 감지 조건 | 처리 |
|---|---|
| `<artifact-root>/spec/pipeline_state.yaml` 부재 | **신규** — Step 1 부터 처음. 산출 `spec/` 신설 |
| `<artifact-root>/spec/pipeline_state.yaml` 존재 | **재진입** — `phases:` 상태 read + 발화 의도 분류 후 해당 step 부터 refine v{N+1} |

spec 대상 = cwd 의 `<artifact-root>/spec/` (1 repo = 1 spec). 모노레포 예외 (`spec/<component>/` 여럿) 면 발화·cwd 로 대상 component 식별.

### 2단계 — 발화 → step 자동 분류 (재진입 자리)

| 발화 신호 | 추론 step | 흐름 |
|---|---|---|
| "스택 바꾸자" / "Vercel 대신 Cloudflare" / "framework 교체" | Step 2 (스택 후보 재선정) | refine v{N+1} + 이후 step 무효화 |
| "Y endpoint 추가" / "data model 의 X entity 필드 변경" / "ui flow 의 X 화면" | Step 3a (PRD 핵심 mode) | refine + 묶음 갱신 (api_contract / data_model / Component diagram) |
| "Component diagram 손보자" / "Deployment 자리 추가" | Step 3b (Architecture Diagrams) | refine v{N+1} |
| "복합 mode 추가 — Y mode 도" / "이 spec 에 cli 도 같이" | Step 3c (복합 mode 다른 섹션) | refine + mode 추가 |
| "skeleton 다시 — ref 바꾸자" / "ref repo 다른 자리" | Step 4 Phase 0 (ref source) | Phase 1·1.5·2·3 재실행 |
| "skeleton 의 train.py 수정" / "scaffold 결과 손보자" | Step 4 Phase 2 (개발팀 new-lib) | Phase 2·3 재실행 |

> "Vercel 셋업" / "배포 셋업" / "env 변경" / "도메인 연결" 발화는 본 skill 이 아닌 별도 [`autopilot-ship`](../autopilot-ship/SKILL.md) 으로 라우팅.

### 3단계 — 자동 컨펌 한 화면

```
=== autopilot-spec 호출 자리 ===
프로젝트: <name>
산출물: spec/ (발견 — 기존 spec) 또는 (부재 — 신규)
phases (재진입 시): spec=done, scaffolding=done, dev=in_progress
발화: "<사용자 한 줄>"
→ 추론: <step / 신규> 자리 — refine v{N+1} (재진입 시)

진행? (진행 / 다른 step 으로 / 새 spec 으로 / 중단)
```

신규 vs 재진입 분류는 _명시 옵션 (`--from`) 없이도_ 동작 — 사용자 발화 + cwd 자동 판단. 사용자가 명시적 `--from <step>` 입력하면 그대로.

### update mode — 기존 spec 갱신의 canonical 경로 (first-class)

본 skill 은 _초기 생성_ 뿐 아니라 _기존 spec 의 update·iteration_ 을 동급 일급 capability 로 담당. **모든 spec 변경 (`prd.md` 갱신) 은 반드시 본 skill 의 update mode 를 거친다** — 사용자 직접 요청이든, autopilot-code 에서 감지된 drift 든, WORKFLOW §7/adapter 사후 수정 흐름이든 무관. `prd.md` 는 _ad-hoc hand-edit 금지_ — update mode 를 거쳐야 버전 snapshot 이 자동 적용되어 drift·휘발 차단.

update mode 가 하는 일 (3 가지, 한 트랜잭션):

1. `spec/prd.md` (항상 최신 T1 파일) 를 새 내용으로 갱신.
2. **덮어쓰기 _전_ 에** 직전 `prd.md` 를 `spec/_internal/versions/v{N}/prd.md` 로 자동 snapshot (autopilot-refine 의 doc versioning 미러 — [CONVENTIONS §5.4.3](../../core/CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3)). 역할 주체만 autopilot-spec, 대상이 spec.
3. 변경 narrative 를 `pipeline_summary.md` 에 통합 기록. 영향 받는 인접 파일 (`data_model.md` / `api_contract.md` / `ui_flow.md` / `stack.md`) + Architecture Diagrams 는 위 _Step 3.5 묶음 갱신 logic_ 으로 한 트랜잭션 동기화.

> update mode 는 _별도 mode 라벨_ 이 아니라 **재진입 시 자동 활성** — `pipeline_state.yaml` 존재 자리 (위 Context Auto-Detection) 면 본 경로. mode 5종 (app/library/api/cli/research) 은 _spec 의 종류_, update 는 _기존 spec 갱신 동작_ — 직교. 따라서 update 자리에서도 해당 spec 의 원래 mode 섹션을 그대로 갱신한다.

**사후 수정 (WORKFLOW §7 / adapter bootstrap) drift → 본 경로 라우팅**:

- autopilot-code 작업 중 spec 영향 변경 (새 endpoint / schema·data-model / entity 의미 / ui-flow / 마이그레이션 / 외부 연동) 감지 시 → autopilot-code 가 update mode back-jump 호출.
- **drift 가 CLEAR** (변경 의도·범위 명확) → 자율 진행 + 한 줄 보고.
- **drift 가 AMBIGUOUS** (의도 해석 갈림 / 영향 범위 불명) → 사용자에게 먼저 확인 후 진행 (임의 추측 X).

작은 spec tweak 은 `--intensity quick` 으로 inline micro-plan + plan-check-lite + verify-lite만 수행한다. Durable snapshot/log는 spec 영향이 실제로 있고 autopilot-spec update가 `prd.md`를 갱신할 때 남긴다; `--intensity quick`만으로 plan/log/snapshot artifact를 강제하지 않는다.

### refine v{N+1} 버전 관리 (doc 트랙과 동일 원리)

위 update mode 의 버전 메커니즘. Spec versioning 은 doc 트랙 ([CONVENTIONS §5.4.3](../../core/CONVENTIONS.md#5-skill-output-convention-3-tier-t1t2t3) — autopilot-refine 이 doc artifact 에 쓰는 `_internal/versions/v{N}/` 메커니즘 재사용). `prd.md` 가 _항상 최신_ (T1) — 사용자는 최신만 봄.

- **major 변경 / refine (v{N+1})** — 새 내용으로 `prd.md` 를 덮어쓰기 _전_ 에 직전 `prd.md` 를 `spec/_internal/versions/v{N}/prd.md` 로 자동 snapshot 후 덮어씀 (autopilot-refine 이 doc 에 쓰는 것과 같은 메커니즘 — 역할 주체만 autopilot-spec, 대상이 spec). 변경 narrative 는 `pipeline_summary.md` 에 통합 기록.
- **minor 편집** — 직접 Edit + `pipeline_summary.md` minor-log (snapshot 없음). 누적 5 → `/audit` chat alert.
- 사용자 수동 버전 관리 X.
