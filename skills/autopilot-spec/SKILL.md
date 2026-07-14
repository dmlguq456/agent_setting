---
# GENERATED METADATA — edit harness-manifest.json, then run tools/generate.py.
name: autopilot-spec
description: "Use when invoking the portable autopilot-spec capability. Create or update requirements/blueprints while keeping `prd.md` as the only spec-change path."
argument-hint: "<task description> [--mode auto|app|library|api|cli|research|update (comma-separated for multiple)] [--intensity direct|quick|standard|strong|thorough|adversarial] [--user-refine]"
metadata:
  group: entry
  fam: code
  modes: ["app", "library", "api", "cli", "research", "update"]
  blurb: "Create or update requirements/blueprints while keeping `prd.md` as the only spec-change path."
---

> 산출물 폴더: `<artifact-root>/spec/` (CONVENTIONS.md §5.4.3 3-tier). 숫자 prefix 없는 평이한 이름 — `prd.md` (T1, 항상 최신) · `stack.md` · `design/` · `ship.md` · `pipeline_state.yaml` · `_internal/`.
> `<artifact-root>` 해석·치환(`.agent_reports` 우선, legacy `.claude_reports` fallback): [CONVENTIONS §5.1](../../core/CONVENTIONS.md#51-workspace-assumption-전제).

> **Intake 게이트**: 진입 직후 입력이 비가역 결정 커버리지(스택·인증·DB·배포타깃·핵심 entity 등)에 미달이면 [CONVENTIONS.md §6.6](../../core/CONVENTIONS.md#66-autopilot-intake-gate) 의 1라운드 구조화 질문 먼저 (AskUserQuestion, 항상 탈출구). slash 직접 args 충분·이미 명시·throwaway(/track)·재개(--from) 시 skip (별도 flag 불요).

## Purpose — _요구사항·청사진 작성_ entry

본 skill 은 _코드 작업이 아닌_ 자리 담당. _무엇을 만들지·어떻게 정돈할지·공개 자리 어떤 API_ 같은 _spec 청사진_ 결정:

| Mode | 자리 | spec 의 핵심 |
|---|---|---|
| **app** | 사용자 대상 앱 (Next.js / Expo 등) | 피처·시나리오·API Contract·data model·ui flow + 스택·scaffolding·skeleton |
| **library** | 공개 라이브러리·패키지 (npm·pip·crate) | 공개 API (export 함수·class·type) + 사용 예시 + 호환성·versioning + module 구조 |
| **api** | 백엔드 API 서비스 (UI 없음) | endpoint·body·error·auth·rate limiting + 데이터 모델 |
| **cli** | 명령줄 도구 | 명령·옵션·서브 명령·input/output·exit code |
| **research** | 연구·실험 코드 정돈·재현성 | entry point (train·eval) + 실험 설정 (configs) + 재현 명령 + 예상 metric + baseline 비교 |

복합 mode (예: `library + cli`, `research + cli`) 자연 — 한 프로젝트가 _여러 측면_ 가지면 _복합 PRD_ 자연. PRD 가 _공통 + mode 별 섹션_ 으로 구성.

> 코드 작업 자체 (실제 함수·class·API 구현·리팩터링·디버그) 는 **autopilot-code** 가 담당 — `spec/` 컨텍스트 자동 감지로 spec Read 후 그 청사진 따라 구현 (작업 산출물은 `plans/`).

## 흐름 안에서 본 skill 의 자리

```
사전:    autopilot-research (외부 조사) + analyze-project (기존 코드 분석)
           ↓
청사진:   autopilot-spec  ← 본 skill. mode 별 PRD + (app mode 만) scaffolding·skeleton
           ↓
시각:    autopilot-design  ← (옵션, UI 자리만)
           ↓
구현:    autopilot-code  ← spec 자동 Read, 그 청사진 따라 구현 (반복)
           ↓
배포:    autopilot-ship  ← (가끔, app mode 만) ship 첫 setup·env·domain·migration deploy 안내 (별도 skill)
```

## Default Invocation Rule (메인 에이전트 자동 라우팅)

본 skill 은 runtime adapter bootstrap 의 "autopilot-* 호출 패턴" 컨펌 의무 적용 대상(Claude Code: [`CLAUDE.md`](../../adapters/claude/CLAUDE.md) §0).

### Trigger 신호 (자연어 발화 예시)

| mode | 발화 |
|---|---|
| **app** | "X 앱 만들어줘" / "Y 서비스" / "PRD 부터" |
| **library** | "X 라이브러리로 정리" / "npm 패키지로 만들자" / "공개 API 정리" |
| **api** | "X API 서버 만들자" / "endpoint 정리" |
| **cli** | "X CLI 도구" / "명령줄 옵션 정리" |
| **research** | "X 연구 코드 정돈" / "재현성 준비" / "학회 공개 코드 준비" |
| **복합** | "라이브러리 + CLI 도구로" / "연구 코드 + 재현 가능 CLI" |

> 배포 셋업 ("Vercel 셋업" / "env 변경·domain 연결") 은 본 skill 이 아닌 별도 [`autopilot-ship`](../autopilot-ship/SKILL.md) 으로 라우팅.

### Default 옵션 권장값

- `--mode`: **`auto`** (default) — 발화·기존 코드·산출물 검사로 자동 추론 (단일 또는 복수)
- 검증 강도: `--intensity` 에서 파생 (별도 `--qa` 축 없음 — [CONVENTIONS §1.1](../../core/CONVENTIONS.md#11-verification-rigor-tiers-intensity-derived-canonical-sot)). default 는 standard-tier. high-stakes 신호 시 intensity 상향
- `--user-refine`: **off** (사용자 명시 시만 on)

### Override 1순위 — autopilot 우회

- 코드 작업 (구현·리팩터링·디버그) — `/autopilot-code` 직접 (spec 자동 Read)
- 디자인만 — `/autopilot-design` 직접
- 작은 작업 (한 파일 수정·rename) — `Agent(개발팀)` 직접
- `/autopilot-spec <args>` slash 직접 입력 — 컨펌 skip

## Language Rule
- User-facing output follows the user's communication language unless an explicit audience or artifact-language requirement overrides it.
- Preserve code identifiers, file paths, and technical terms as written when translation would reduce precision.

## Spec 변경 canonical 경로·게이트 (개요)

`prd.md` 는 본 skill 의 단일 출처 — 모든 spec 변경의 canonical 경로다. 상세 규칙·표·PRD 템플릿·버전 규약은 아래 reference 에 100% 보존되며, 본 절은 게이트 개요만이다 (원문 규칙은 `references/` 참조).

- **update mode = 유일 경로** (`references/invocation-and-modes.md`): 모든 `prd.md` 갱신은 반드시 본 skill 의 update mode 를 거친다 — 사용자 요청·autopilot-code 감지 drift·WORKFLOW §7 사후 수정 무관. `prd.md` 는 _ad-hoc hand-edit 금지_. update mode 는 별도 라벨이 아니라 _재진입 시 자동 활성_ (`pipeline_state.yaml` 존재 자리).
- **버전 snapshot** (`references/invocation-and-modes.md`): 덮어쓰기 _전_ 직전 `prd.md` 를 `spec/_internal/versions/v{N}/prd.md` 로 자동 snapshot 후 덮어씀, 변경 narrative 는 `pipeline_summary.md` 통합. minor 편집은 직접 Edit + minor-log (snapshot 없음, 누적 5 → `/audit` alert).
- **Intake 게이트** (위 blockquote): 진입 직후 입력이 비가역 결정 커버리지 미달이면 CONVENTIONS §6.6 1라운드 구조화 질문 먼저 (slash 충분·명시·throwaway·재개 시 skip).
- **동시성 lock** (`references/prd-authoring.md`): 쓰기 단계 진입 _직전_ `.pipeline-lock` 획득 (OPERATIONS §5.8), BLOCKED 면 쓰기 멈추고 사용자 보고.
- **Forbidden Zones · CONFIRM Gate 응답 분기** (`references/operations-and-examples.md`): 배포·결제·DNS·env 실값 등 명시 요청 없이 X / 각 Gate 응답은 진행·수정·back-jump·중단 분기.

## Reference Index

| 파일 | 언제 로드 (의무) | 내용 |
|---|---|---|
| `references/invocation-and-modes.md` | 옵션 해석·mode 추론·신규 vs 재진입 분기 자리 | Argument Parsing(`--mode`/`--intensity`/`--user-refine`), Mode 자동 추론 단서, Context Auto-Detection(`pipeline_state.yaml` 자동 검사·발화→step 분류·자동 컨펌 한 화면·update mode canonical 경로·refine v{N+1} 버전 관리) |
| `references/prd-authoring.md` | PRD 작성 시 (Procedure Step 1~3.5) | Procedure(중간 컨펌 default·동시성 가드) + Step 1(정보 수집)·2(한 화면 컨펌)·3a-3d(PRD 3 자리 분할 + 의미↔규칙 경계 체크) + PRD 본문 템플릿 + Architecture Diagrams + Step 3.5(묶음 갱신 logic) |
| `references/scaffolding.md` | Scaffolding + Skeleton 시 (Step 4 Phase 0~3) | Phase 0 ref source·1 ref repo/ckpt 가져오기·1.5 pretrained ckpt 사전 동작 점검·2 개발팀 new-lib·3 결과 컨펌 + Step 5 CONFIRM Gate |
| `references/operations-and-examples.md` | 배포 라우팅·CONFIRM Gate 분기·Return·memory·Examples 자리 | 배포 셋업 자리(autopilot-ship 라우팅)·Forbidden Zones·CONFIRM Gate 응답 분기·Pipeline state 관리·Return Format·Update memory·Examples 1-4 |
