## 배포 셋업 자리 — autopilot-ship

배포 셋업 (ship 첫 setup·env·domain·migration deploy) 은 별도 skill [`autopilot-ship`](../autopilot-ship/SKILL.md) 담당. _작업 본질에 맞는 분리_ ([CONVENTIONS §6.3](../../core/CONVENTIONS.md)) — autopilot-spec 은 _초기 설계 (요구사항·기본 틀·skeleton)_, autopilot-ship 은 _마지막 배포 + 재호출_ 자리.

호출 자리:
- 배포 셋업 / env 변경 / 도메인 / migration → `/autopilot-ship <task>` 직접
- 또는 자연어 발화 — "배포 셋업" / "Vercel" / "env 변경" / "도메인" — 메인 에이전트가 autopilot-ship 으로 자동 라우팅

## Forbidden Zones (명시 요청 없이 X)

- 실제 배포 명령 (`vercel deploy`, `fly deploy` 등) — 안내만
- 결제 정보·credit card 등록
- DNS 직접 변경
- 도메인 구매
- 환경변수 _실제 값_ 입력 (사용자 dashboard 직접)
- production DB migration 자동 실행

## CONFIRM Gate 응답 분기 (모든 Gate 공통)

| 응답 | 처리 |
|---|---|
| **진행** | 다음 단계 또는 종료 |
| **수정** | 현 단계 refine v2 (`_internal/refine_v{N}.md` 백업) |
| **back-jump** | 이전 단계 재실행 + 하위 무효화 |
| **중단** | 멈춤, `pipeline_state.yaml` 상태 보존 |

발화 모호 시 옵션 다시 물음 (임의 추측 X).

## Pipeline state 관리

`spec/pipeline_state.yaml`:

```yaml
project_name: <name>
created: <date>
mode: [library, cli, research]   # 또는 단일 [app]
(app mode 만) stack:
  framework: <chosen>
  db: <chosen>
phases:
  spec: done                    # PRD 완성
  (app mode 만) scaffolding: done
  (app mode 만) skeleton: done
  design: pending               # autopilot-design 진행 시 done
  dev: in_progress              # autopilot-code 가 누적
  (app mode 만) ship_setup: pending
last_updated: <timestamp>
```

autopilot-code 의 작업 산출물은 형제 bucket `plans/<date>_<slug>/` 에 누적 (spec/ 안이 아님 — 청사진과 작업 layer 분리).

## Return Format

```
<artifact-root>/spec/ -- ✅ spec completed (mode: <list>)
```

다음 단계 안내:
- spec 완료 → "autopilot-design (시각 자리) 또는 autopilot-code (구현·정돈)"
- (app mode) setup 완료 → "이후 push 만으로 자동 deploy"

## Update memory

- 사용자 자주 만나는 mode 조합 (예: research + cli)
- mode 자동 추론 단서 보강
- 스택·언어 선호
- ship setup 자주 만나는 함정

## Examples

### 예시 1 — 가사관리 앱 (단일 app mode)

```
/autopilot-spec "할 일 + 가계부 가사관리 웹 앱"
→ mode auto → app 추론
→ PRD: 피처·시나리오·API Contract·data model·ui flow
→ 스택: Next.js + Prisma + Turso
→ scaffolding + skeleton
→ spec/가사관리/prd.md
```

### 예시 2 — TF-Restormer 연구 코드 정돈 (복합 research + cli)

```
/autopilot-spec "TF-Restormer 정돈·재현성 준비"
→ mode auto → research + cli 추론 (configs/ + argparse + ipynb 단서)
→ PRD 공통: module 구조, 의존성, license
→ PRD [research]: entry / configs / 재현 명령 / 예상 metric
→ PRD [cli]: train.py / eval.py 명령·옵션
→ spec/TF-Restormer/prd.md (코드 생성 X — autopilot-code 가 본 spec 따라 정돈)
```

### 예시 3 — npm 라이브러리 (복합 library + cli)

```
/autopilot-spec "audio-utils — Node 라이브러리 + CLI 도구"
→ mode auto → library + cli
→ PRD [library]: 공개 API (loadAudio / saveAudio / ...) + 사용 예시 + semver
→ PRD [cli]: au-tool 명령 + 옵션
→ Phase 0: ref source — Phase 1: github clone 한 ref repo → Phase 2: src/{io,core,utils}/ 의 export skeleton + cli entry (Phase 1.5 skip — 코드만 가져오는 자리)
→ spec/audio-utils/prd.md + spec/audio-utils/ scaffold (skeleton)
```

### 예시 4 — ASR Conformer baseline (research + cli, Phase 1.5 ckpt 검증)

```
/autopilot-spec "Conformer ASR baseline — fine-tuning 시작 자리"
→ mode auto → research + cli (configs / argparse / metric 단서)
→ Step 1: 정보 수집 — research/asr-conformer/ 의 code_resources (espnet, transformers) 인용 자리 N. similar_models 부재 (빈 코드 자리) → 외부 ref 1순위
   "위 자료들로 진행?" → 진행
→ Step 2: mode + 스택 (PyTorch + lightning) 컨펌
→ Step 3a: PRD [research] entry / configs / metric (WER / CER) → 컨펌
→ Step 3b: Component diagram (data → encoder → decoder → metric) → 컨펌
→ Step 3c: PRD [cli] train / eval / serve 명령 → 컨펌
→ Step 4 Phase 0: ref source — espnet asr1 recipe + HF transformers Conformer ckpt → 컨펌
→ Step 4 Phase 1: git clone espnet + huggingface-cli download nvidia/conformer-asr-small → /tmp/asr_ref
→ Step 4 Phase 1.5: ckpt 사전 동작 점검
   inference 명령: research/asr-conformer/07_resources 에 누적된 Quick verify 명령
   결과: ✅ sample WAV 1 개 → 텍스트 출력 정상 → Phase 2 진행
→ Step 4 Phase 2: 개발팀 new-lib
   - model/Conformer/ 폴더 (preferred layer 만 — MHSA / Conv / FFN)
   - train.py / eval.py / config.yaml skeleton (lightning)
   - cli.py (typer — train / eval / inference 서브명령)
→ Step 4 Phase 3: 결과 컨펌
→ Step 5: spec 완성 → 다음 — /autopilot-lab "ASR fine-tuning Common Voice ko"
```
