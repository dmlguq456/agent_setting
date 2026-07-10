---
slug: fleet-cooling-groups
mode: dev
qa_level: quick
status: done
date: 2026-07-03
component: agent-fleet-dashboard
safety_commit: b83c580
---

# fleet 디렉토리 그룹 "대기(cooling)" 상태 추가

## 목표
fleet 디렉토리(그룹) 헤더의 활동 상태를 2단계(활성/비활성)에서 **3단계**로 확장.
"작업 끝난 지 얼마 안 된(≤3h) 레포"를 완전 비활성도 활성도 아닌 "완료 직후 식는 중"
중간 상태로 표시 — 회색 원형 고리 `○` + 완료 후 경과시간.

## 배경
- 현행 `render.py` 그룹 헤더: `n_work>0` → 녹색 `●`(blink) + green-bold(`grp_hot`) / else 글리프 없음(`grp`).
- 사용자 요청(2026-07-03): 끝난 지 1~3h 이내 레포를 중간 성격 "대기 레포"로, 디렉토리 앞 회색 고리 + 경과시간.

## 변경 (Change Plan)
| 파일 | 변경 |
|---|---|
| `tools/fleet/render.py` | `_COOL_WINDOW_MIN`(180)·`_COOL_RING`(`○`) 상수 + `grp_cool` 색키(A_DIM) + 그룹 헤더 cooling 분기 |
| `tools/fleet/demo.py` | `import time` + `demo-cool` cooling fixture(idle 세션, mtime=now-92m) |
| `adapters/claude/tools/fleet/{render,demo}.py` | 정본 → 투영본 동기화(물리 복사 두 벌, identical 유지) |
| `.agent_reports/spec/agent-fleet-dashboard/prd.md` | §4 그룹 레이아웃에 cooling 3단계 minor edit(대응 동기화) |

## 판정 로직
```
_last_act = max(s.mtime for s in group_sessions if s.mtime)   # 세션 transcript epoch
n_work>0                                  → 활성 (현행 ● green blink)
n_work==0 & 0≤(now-_last_act)/60≤180      → cooling (○ grey + fmt_min 경과시간)
그 외 (3h 초과 / mtime 없음)               → cold (현행, 무표시)
```
- DispatchJob엔 mtime 필드가 없어 우선 세션 mtime 기준. (후속: job mtime 반영 여지)
- cooling 레포는 세션이 idle로 남아(48h live 창) 그룹 fold(R4) 대상이 아님 → 헤더 정상 노출.
- 활성/비활성 기존 렌더는 순수 추가 분기만(회귀 없음).

## 제약 메모
- 이 세션이 `CLAUDE_CODE_CHILD_SESSION=1`이라 OPERATIONS §5.10 ③(깊이 1) 상 headless 재분사 불가
  → worktree 격리 + in-process 구현(quick tier). 상세는 pipeline_summary.md.
