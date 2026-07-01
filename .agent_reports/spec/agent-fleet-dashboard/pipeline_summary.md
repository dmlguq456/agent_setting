# agent-fleet-dashboard — Spec Pipeline Summary

- **Date**: 2026-07-01
- **Mode**: cli (터미널 TUI 도구)
- **Status**: spec done (v1)
- **Placement**: 별도 컴포넌트 `spec/agent-fleet-dashboard/` — 기존 `spec/prd.md`(Unified Memory System) 무수정.

## Process Log
| Step | Action | Result | Notes |
|---|---|---|---|
| research | 기술 tap 매핑 조사 (Explore) | `research/agent-fleet-dashboard/01_tap_mechanics.md` | 하네스별 discovery·tap·liveness, file-cited + jobs.log open/running 버그 발견 |
| research | prior-art 스캔 (경량 web) | `research/agent-fleet-dashboard/00_prior_art.md` | herdr 정체(실OSS 멀티플렉서, 채택X) + 규모 작음 → 얇게 직접 빌드 + curses 확정 |
| spec | PRD 작성 (lean) | `prd.md` v1 | intake skip(입력 충분), 단일 mode cli, scaffold 이월 |

## 주요 결정 (locked)
- F-1 외부 관찰자(zero-injection), 유일 write=우리 소유 statusline per-session tap.
- F-2 3계층(프로세스 스캔 백본 + 하네스별 passive enrichment + curses) · 2섹션(fleet + dispatch).
- F-3 하네스 비대칭 허용(opencode rate-limit·effort 결손 칸 —).
- F-4 statusline.sh 확장 → `~/.claude/.statusline/<sid>.json` per-session(단일 파일 덮어쓰기 해소).
- F-5 dispatch uncapped + jobs.log `{open,running}` tolerant (어휘 버그 동반 정리 권고).
- F-6 herdr 4-상태 어휘 + 기존 liveness 재사용(herdr 자체 채택 X).
- F-7 zero-dep python curses, tmux 세로 사이드 페인 런처.
- F-8 sparkline·herdr 소켓·커스터마이즈 후순위(스코프 밖).

## Next
`/autopilot-code --mode dev "agent-fleet-dashboard 구현"` (worktree). 순서 = PRD §Next 1~7.

## Version History
- v1 (2026-07-01): 초기 PRD. research 2건 근거.
