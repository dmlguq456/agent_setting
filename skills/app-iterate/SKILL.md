---
name: app-iterate
description: "[DEPRECATED — autopilot-code 의 _앱 mode_ 자체가 iteration. 별도 phase 의미 약함]. 과거: feedback 수집·분류 (next-spec / immediate fix / discard) → 다음 사이클 spec 인계. 현재: 사용자 발화가 직접 다음 의도. `/autopilot-code` 호출 시 큰 묶음 feedback 자리는 첫 단계 logic 으로 분류·우선순위 자동 처리."
argument-hint: "<app name or path> + user feedback  # DEPRECATED — /autopilot-code 자연어 호출"
---

> **DEPRECATED (2026-05-25)** — autopilot-code 의 앱 mode 자체가 iteration. 본 파일은 _레거시 참조_ 용.

## Language Rule
- Korean output.

## App Resolution

1. `--app <name>` 또는 폴더 경로
2. fuzzy search `.claude_reports/apps/*$ARG*`

## Pre-Check

- `phases.ship: done` 검증 → 사용자가 실제 배포 후 사용해본 상태여야 의미 있음
- 단 _개발 중 미들 피드백_ 도 받을 수 있음 → ship 안 됐으면 사용자에 confirm 후 진행

## Procedure

### Step 1: 현재 spec Read

`.claude_reports/apps/<name>/01_spec/PRD.md` + 최근 사이클 변경 (`build_log.md`).

### Step 2: 사용자 피드백 수집

사용자가 args 또는 첨부 파일로 제공. 형식 자유:

- "X 페이지에서 Y 버튼이 안 보임" (버그)
- "Z 기능이 있으면 좋겠음" (새 피처)
- "W 가 느림" (성능)
- "사용자 흐름이 헷갈림" (UX)

### Step 3: 분류 (Claude 1차 분류)

각 피드백 항목을 세 카테고리로:

| 분류 | 트리거 | 다음 액션 |
|---|---|---|
| **다음 사이클 spec** | 새 피처 / UX 개선 / 성능 최적화 | app-spec 다음 사이클에 P0/P1/P2 로 추가 |
| **즉시 fix** | 버그 / 명백한 회귀 | `/app-build` 즉시 호출 (fix scope) 또는 `Agent(개발팀, mode=<backend|frontend>, "bug fix: <issue>")` 직접 호출 |
| **discard** | out of scope / 사용자 confusion / 이미 의도된 동작 | 이유 명시 후 기록만 |

### Step 4: 사용자 분류 검토 (필수 컨펌)

Claude 의 1 차 분류는 _추정_ 이라 사용자 검토 자리 필수. 다음 자리에 _개입 기회 명시_:

```
=== 피드백 분류 결과 ===
F1 "X 페이지 Y 버튼 안 보임"     → 즉시 fix       (버그)
F2 "Z 기능 있으면 좋겠음"         → 다음 사이클 spec (새 피처, P1)
F3 "W 가 느림"                  → 다음 사이클 spec (성능, P0?)
F4 "사용자 흐름 헷갈림"           → 다음 사이클 spec (UX, P1)
F5 "X 가 안 됨"                 → discard         (의도된 동작)

분류 검토 — 어떻게 진행할까요?
  (a) 이 분류 그대로
  (b) 재분류 — "F2 즉시 fix 로" / "F5 도 spec 으로" 같이 명시
  (c) priority 조정 — "F3 P0" 같이 명시
  (d) 항목 추가 / 제거 — "F6 으로 X 도 추가" / "F5 빼" 같이 명시
  (e) 중단
```

응답 받아 분류 재조정 후 Step 5 (feedback_log.md 작성) 으로.

### Step 5: feedback_log.md 작성

`.claude_reports/apps/<name>/06_iterate/feedback_log.md`:

```markdown
# Feedback Log — Cycle <N>

**Received**: <date>
**Source**: <user chat / 직접 사용 / 외부 사용자>

## 다음 사이클 spec 으로

### F1: <짧은 제목>
- **원본 피드백**: <인용>
- **분류 사유**: 새 피처 — 현 PRD 에 없음
- **권장 priority**: P1
- **spec 반영 방향**: ...

### F2: ...

## 즉시 fix

### B1: <짧은 제목>
- **원본 피드백**: ...
- **재현 방법**: ...
- **추정 원인**: ...
- **수정 권장**: `Agent(개발팀, mode=frontend, "...")`

## Discarded

### D1: <짧은 제목>
- **원본 피드백**: ...
- **discard 사유**: ...
```

### Step 6: 다음 사이클 인계

요약 보고:

```
피드백 N건 처리:
- 다음 사이클 spec 으로: M건 (다음 spec phase 에 반영)
- 즉시 fix: K건 (지금 build phase 호출 권장)
- discarded: P건

다음 액션:
- 즉시 fix 가 있으면: /app-build <app> --fix
- 새 사이클 시작: /app-spec --app <name> --user-refine
  (이미 정리된 feedback_log.md 를 자동 참조)
```

### Step 7: pipeline_state.yaml 업데이트

- `phases.iterate: done`
- `current_cycle` 증가 (1 → 2, 등)
- 다음 사이클 phases 초기화:
  ```yaml
  phases:
    init: done       # init 은 cycle 1 에서만
    spec: pending    # 새 사이클
    design: pending
    build: pending
    qa: pending
    ship: pending
    iterate: pending
  ```

## Output

- `.claude_reports/apps/<name>/06_iterate/feedback_log.md`
- `pipeline_state.yaml` (`current_cycle++`, phases reset)

## Return Format

```
.claude_reports/apps/<name>/06_iterate/ -- ✅ feedback logged (N new spec, K fixes, P discarded)
```

## Update agent memory

- 피드백 분류 패턴 (어떤 표현이 새 피처 vs 버그 vs discard 인지)
- 사용자 피드백 톤 (구체적 vs 추상적, 솔루션 제시 vs 문제 보고)
- 사이클당 평균 피드백 수
- 자주 등장하는 UX 마찰 지점
