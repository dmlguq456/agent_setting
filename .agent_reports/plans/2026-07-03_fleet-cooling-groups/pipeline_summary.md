# Pipeline Summary: fleet 그룹 cooling 상태 추가

- **Date**: 2026-07-03
- **Status**: done
- **Mode**: dev · **QA**: quick
- **Plan**: plan/plan.md
- **Component**: agent-fleet-dashboard (spec-backed)
- **Branch**: fleet-cooling-groups (worktree, main 미머지)
- **User-Refine**: false

spec-significance: within-spec (그룹 렌더 시각 상태 추가 — spec §4에 cooling 대응 minor edit로 동기화, autopilot-spec full update 불요)

## Process Log
| Step | Action | Result | Notes |
|---|---|---|---|
| pre-flight | git-state 게이트 | pass | main clean, merge/rebase 없음, DONE-BRANCH 아님 |
| pre-flight | 규모 분기 | worktree | 기능 추가+다파일 → §0(C) worktree 브랜치. **`CLAUDE_CODE_CHILD_SESSION=1`이라 headless 재분사 불가(§5.10 ③) → worktree 안 in-process 처리** |
| implement | render.py cooling 분기 | done | 상수·색키·헤더 3단계 분기 |
| implement | demo.py fixture | done | demo-cool(idle, mtime -92m) |
| sync | 투영본 cp | done | render/demo 정본↔adapters identical |
| test | syntax(ast) | pass | render.py·demo.py |
| test | `--demo --json` collect | pass | demo-cool 세션 mtime set 확인 |
| test | `--demo --once` 렌더 스모크 | pass | Traceback 없음. cooling 3단계 실렌더 확인 |
| sync | spec §4 minor edit | done | cooling 3단계 명문화(대응 동기화) |

## 검증 증거 (렌더 스냅샷, --demo --once)
```
● demo-app/  ...           ← 활성 (working, green ●) — 회귀 없음
○ demo-cool/  1h32m        ← cooling (회색 ○ + 경과시간) — 신규
○ personal_homepage/  17m  ← 실데이터에서도 자동 cooling 판정
○ SR_CorrNet_DSC/  24m     ← 실데이터 cooling
demo-lib/  ...             ← stale-only = cold (고리 없음)
```

## Decision Points
| Step | Decision | 근거 | Action |
|---|---|---|---|
| pre-flight | headless 분사 vs in-process | 세션이 child(CLAUDE_CODE_CHILD_SESSION=1) → §5.10 깊이 1 재분사 금지 | worktree 격리 + in-process (quick tier) |
| sync | spec 반영 방식 | cooling = 시각 상태 추가(within-spec) | autopilot-spec full 대신 §4 minor edit(대응 동기화) |

## 후속 (열림)
- DispatchJob mtime 반영(현재 세션 mtime만 → job-only 그룹은 cooling 미판정).
- `_COOL_WINDOW_MIN`(180) 값은 실사용 보고 조정 가능(상수화 완료).
- main 미머지 — 사용자 머지 신호 대기(§5.10, self-merge 금지).
