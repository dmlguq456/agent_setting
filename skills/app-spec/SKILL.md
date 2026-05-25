---
name: app-spec
description: PRD writing and refinement — feature list, user scenarios, non-functional requirements, data model sketch, screen flow. Optionally delegates to 기획팀. Supports refine loop.
argument-hint: "<task or feature description> [--app <name>] [--user-refine]"
---

## Language Rule
- Korean output. Code identifiers, model names, technical terms in English.

## App Resolution

1. `--app <name>` 있으면 그것 사용
2. 없으면 `.claude_reports/apps/` 안 최신 `pipeline_state.yaml` 의 app 사용
3. 여러 개 있으면 "어느 앱?" 한 줄 확인
4. 부재 → "먼저 `/app-init` 실행 필요" 안내

## Pre-Check

기존 `01_spec/PRD.md` 존재 여부:
- 존재 → 업데이트 mode (기존 PRD 에 새 피처 추가)
- 부재 → 신규 작성 mode

## Procedure

### Step 1: 사용자 발화 분석

- 어떤 피처가 필요한가
- 누가 사용하는가 (사용자 페르소나)
- 어떤 시나리오에서 쓰는가
- 우선순위 신호 ("꼭 필요" / "있으면 좋겠다")

모호하면 한 줄 확인 — 옵션 한정 시 _Other_ 가능 명시. 예: "이 기능의 주 사용자는 본인 / 가족 / 일반 사용자 / 다른 자리 (직접 적어주세요)?". 사용자가 옵션 밖 의도 있을 때 표현 자리 열어둠.

### Step 2: PRD 작성 또는 갱신

`.claude_reports/apps/<name>/01_spec/PRD.md` 구조:

```markdown
# <App Name> PRD

## 피처 목록

### P0 (필수)
- [ ] 피처 1 — 한 줄 설명
- [ ] 피처 2

### P1 (있으면 좋음)
- [ ] ...

### P2 (나중에)
- [ ] ...

## 사용자 시나리오

### 시나리오 1: <이름>
사용자가 X 상황에서 Y 를 하려고 한다. ...

(3-5개)

## 비기능 요구

- 성능: ...
- 보안: ...
- 접근성: WCAG AA
- 모바일: 우선 / 동등 / 데스크탑 우선

## 데이터 모델 초안

```
User { id, email, name, createdAt }
Task { id, userId, title, completed, createdAt, updatedAt }
```

> cycle 2+ 에서 모델 변경 시 _기존 필드 보존 + 새 필드 추가_ 가 default. 필드 제거·type 변경은 _destructive_ 라 spec 에 _migration plan_ 표시 (사용 중인 row 처리 방법: backfill / nullable / drop column).

## API Contract (백/프론트 공유 계약)

본 섹션이 spec 단계의 _단일 source of truth_. build phase 의 backend / frontend 가 같은 contract 를 참조해 병렬 작업. contract 변경 시 spec phase 로 back-jump 필요 — build 안에서 임의 변경 X.

```ts
// shared types (예: app/types.ts 또는 packages/types/)
type Task = {
  id: string
  userId: string
  title: string
  completed: boolean
  createdAt: string  // ISO 8601
  updatedAt: string
}

// endpoints
POST   /api/tasks                 → Task (body: { title })
GET    /api/tasks                 → Task[]
PATCH  /api/tasks/:id             → Task (body: Partial<Task>)
DELETE /api/tasks/:id             → { ok: true }
```

- 모든 endpoint 의 _요청 body / 응답 shape / error code_ 명시
- Server actions 만 쓰는 경우에도 _function signature_ 를 contract 로 적음
- 인증 필요 endpoint 는 _Auth 요구_ 표시

## 화면 흐름 (UI 있을 시)

```
/dashboard → /tasks → /tasks/:id
```
```

기획팀 위임 기준 — _모호 표현 "복잡한 spec" 대신 명시 조건_:

| 자리 | 위임 권장 |
|---|---|
| 사용자가 _명시 요청_ ("기획팀 써줘" / "PRD 자세히") | ✓ 무조건 |
| 피처 수 _≥ 5_ + 시나리오 _≥ 5_ | ✓ 권장 |
| 비기능 요구가 _복잡_ (성능 SLA / 보안 standards / 접근성 WCAG 명시) | ✓ 권장 |
| 데이터 모델이 _≥ 4 entity + 관계 복잡_ | ✓ 권장 |
| 피처 1-3 + 시나리오 1-3 의 _간단한 spec_ | ✗ 메인 Claude 직접 |

위임 자리 — `Agent(기획팀, "PRD 작성: <description> + 위 PRD 구조 + 위 위임 사유")`.

위임 결정 _전_ 사용자에 한 줄 확인 — "기획팀 위임 권장 (사유: <자동 판단 사유>). 위임할까요? (위임 / 직접 / 중단)".

업데이트 mode 면 기존 PRD 의 피처 목록에 추가 / 시나리오 추가.

### Step 3: scenarios.md 분리

시나리오가 5개 이상이면 `scenarios.md` 로 분리:

```markdown
# 사용자 시나리오

## S1: ...
## S2: ...
```

### Step 4: Refine loop (옵션, `--user-refine` 시)

1. PRD 작성 완료 후 사용자에 검토 요청
2. 사용자 메모 (인라인 코멘트 또는 chat 답) 받음
3. 메모 반영해 v2 작성. 기존 PRD 는 `_internal/refine_v1.md` 로 백업
4. 반복 가능 (refine_v2, v3, …)

`draft-refine` skill 패턴 따라.

## Pipeline state 업데이트

`pipeline_state.yaml` 의 `phases.spec` 을 `done` 으로.

## Output

- `.claude_reports/apps/<name>/01_spec/PRD.md`
- `.claude_reports/apps/<name>/01_spec/scenarios.md` (시나리오 5+ 시)
- `_internal/refine_v{N}.md` (refine loop 시)

## Return Format

```
.claude_reports/apps/<name>/01_spec/ -- ✅ PRD completed (N features, M scenarios)
```

업데이트 mode:
```
.claude_reports/apps/<name>/01_spec/PRD.md -- ✅ PRD updated (+K features, +M scenarios)
```

## Update agent memory

- 사용자 PRD 작성 선호 (간결 vs 자세, 시나리오 형식, ascii diagram 선호 등)
- 자주 등장하는 피처 패턴 (인증, CRUD, list view 등)
- 사용자가 P0/P1/P2 분류를 어떻게 하는지
