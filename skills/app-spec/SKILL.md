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

모호하면 한 줄 확인 ("이 기능의 주 사용자는 본인 / 가족 / 일반 사용자?").

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
User { id, ... }
Task { id, userId, ... }
```

## 화면 흐름 (UI 있을 시)

```
/dashboard → /tasks → /tasks/:id
```
```

복잡한 spec 이거나 사용자가 명시 요청 시:
- `Agent(기획팀, "PRD 작성: <description> + 위 PRD 구조")` 위임 가능

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
