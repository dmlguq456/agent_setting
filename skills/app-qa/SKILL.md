---
name: app-qa
description: App QA phase — functional review (품질관리팀 code-review + test) + visual review (디자인팀 critic, UI 있을 시). Verifies build output against PRD.
argument-hint: "<app name or path>"
---

## Language Rule
- Korean output.

## App Resolution

1. `$ARG` 가 폴더 경로면 그것 사용
2. fuzzy search `.claude_reports/apps/*$ARG*`

## Pre-Check

- `03_build/build_log.md` 존재 확인 → 부재 시 "먼저 `/app-build` 실행 필요"
- `phases.build: done` 검증

## Procedure

### Step 1: 변경 사항 식별

```bash
git diff --name-only HEAD~1  # 최근 변경
```

또는 `03_build/_internal/step_logs/` 에서 변경 파일 추출.

### Step 2: Functional QA — 품질관리팀 호출

#### code-review 모드

```
Agent(품질관리팀, mode=code-review):
  "Code review for app <name> build phase.
   Changed files: <list>
   Step logs: 03_build/_internal/step_logs/
   Write review to .claude_reports/apps/<name>/04_qa/code_review.md"
```

#### test 모드

```
Agent(품질관리팀, mode=test):
  "Graduated tests for app <name> build phase.
   Targets: <changed files>
   Write report to .claude_reports/apps/<name>/04_qa/test_report.md"
```

### Step 3: Visual QA — 디자인팀 critic (UI 있을 시)

`02_design/` 디렉토리 존재 + frontend 파일 변경 있으면:

```
Agent(디자인팀, mode=critic):
  "Visual review for app <name> after build.
   Changed UI files: <frontend files list>
   Use preview_screenshot if dev server available.
   Write critique to .claude_reports/apps/<name>/04_qa/visual_qa.md"
```

`--qa quick` 시 skip.

### Step 4: 결과 통합

`04_qa/summary.md`:

```markdown
# QA Summary

## Functional QA
- code-review: ✅ / 🔴 N issues (M major)
- test: ✅ All N levels passed / ❌ Failed at Level K

## Visual QA
- critic: ✅ / 🟡 N suggestions / 🔴 N issues

## 종합 판정
- ✅ 모두 통과 → ship phase 진행 가능
- 🔴 발견 → fix 필요
```

### Step 5: 🔴 발견 시 처리

사용자에 보고:
- 어떤 issue 인지 (file:line)
- 어떻게 fix 할지 권장
- 다음 액션: `/app-build` 다시 (fix scope 만) 또는 `Agent(개발팀, mode=<backend|frontend>, "fix: <issue>")`

`pipeline_state.yaml` 의 `phases.qa: failed` 기록.

### Step 6: ✅ 통과 시

`pipeline_state.yaml` 의 `phases.qa: done`.

## Output

- `.claude_reports/apps/<name>/04_qa/code_review.md` — functional 정적 리뷰
- `.claude_reports/apps/<name>/04_qa/test_report.md` — graduated tests
- `.claude_reports/apps/<name>/04_qa/visual_qa.md` — UI critique (UI 있을 시)
- `.claude_reports/apps/<name>/04_qa/summary.md` — 종합 판정

## Return Format

통과:
```
.claude_reports/apps/<name>/04_qa/ -- ✅ QA passed (functional + visual)
```

실패:
```
.claude_reports/apps/<name>/04_qa/ -- 🔴 K issues found (M major) — see summary.md
```

## Update agent memory

- 자주 발견하는 frontend / backend 함정
- 시각·기능 검증의 충돌 사례 (기능은 OK 인데 UX 가 안 좋음 등)
- 사용자 QA 강도 선호 (standard 가 정착인지 thorough 자주 쓰는지)
