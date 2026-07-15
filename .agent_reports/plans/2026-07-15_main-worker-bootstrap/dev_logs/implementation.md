# 구현 기록

- Portable 경계는 `AGENT_SESSION_ROLE=worker`로 통일했다. 기존 dispatch/depth,
  Claude child, OpenCode slug, Fleet title, distill 표식도 worker 증거로 인정하며
  하나라도 있으면 main 표식보다 우선한다.
- Claude, Codex, OpenCode의 자동 memory/briefing/turn-nudge/SessionEnd curator
  경로는 state·counter·spawn 이전에 반환한다. write/core/spec/artifact/worktree,
  permission, routing, liveness, verification은 worker에서도 유지한다.
- repo 내부 dispatch, loop/drill, title, distill 실행기와 외부 worklog 예약 Claude
  호출에 worker 표식을 주입했다.
- Claude runtime-owned `~/.claude/settings.json`은 사용자 model/plugin 설정을
  보존한 채 SessionStart inject와 SessionEnd sync 명령만 병합했다. 물리
  `mem-distill-dispatch.sh` 복사본은 adapter와 동일 hash로 맞췄다.
- Fleet Codex 수집기는 tick 시작 시 `/proc/<pid>/fd`의 rollout 소유권을 먼저
  예약해 같은 cwd의 fd-less TUI가 동일 sid/title을 훔치지 못하게 했다.
- 구현 중 발견한 Codex freeform `apply_patch` hook envelope 파싱 누락도 보완했다.
