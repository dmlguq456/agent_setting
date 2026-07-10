---
slug: worktree-path-guard
date: 2026-07-10
capability: autopilot-code
intensity: standard
status: implemented
branch: worktree-path-guard
source: drill g3/g6 FAIL 진단 (2026-07-10_1156)
---

# worktree-path-guard hook 승격

## 배경
drilled 세션들이 내장 `EnterWorktree` 도구(기본 경로 = repo 안 `.claude/worktrees/`)로
worktree 격리 요구를 충족했다고 믿으며 컨벤션(`<repo>-wt/<slug>` 형제 디렉토리,
OPERATIONS §5.10 ②)을 우회 → main 워킹트리에 미추적 `.claude/` 오염. 규칙이 두 문서에
이미 있는데도 세션 간 이행이 비결정적 → §0.5 결정론 원칙상 hook 승격 자리
(`builtin-memory-guard` 동형: 내장 하네스 표면이 컨벤션과 다른 기본값 제공 → PreToolUse deny + 정규 경로 안내).

## 설계
`hooks/worktree-path-guard.sh` — POSIX sh, no jq, dual mode(hook stdin JSON + CLI).
PreToolUse(EnterWorktree|Bash) 2갈래 deny:
- (a) `EnterWorktree` 전면 deny — 내장 경로가 repo 안이라 컨벤션과 상충.
- (b) Bash `git worktree add` 대상이 `<repo>-wt/` 밖이면 deny.

오차단 금지(fail-open 우선, 막는 건 위 2갈래뿐):
- ⚡untracked 세션 flag(artifact-guard 와 동일 `<artifact-root>/.untracked.<sid>`) → 통과
- 정규 경로 `<repo>-wt/<slug>` 의 `git worktree add` → 절대 차단 안 함(오케스트레이터·conductor 분사 흐름)
- `git worktree remove|list|prune|move…` 등 비-add 서브커맨드 → 무간섭
- 비-git cwd / tool 미상 / 입력 파싱 실패 → 통과(가드 오작동으로 세션 마비 방지, git-state-guard 선례)
- Agent(isolation:worktree)·Workflow worktree 는 Bash/EnterWorktree 툴이 아니라 애초에 미매칭

deny 사유에 정규 절차(형제 디렉토리 add + jobs.log 등록 + §5.10 headless 분사) + `/track` 우회 안내.

## 배선·layer-sync
- canonical `hooks/worktree-path-guard.sh` + collapsed symlink `adapters/claude/hooks/... -> ../../../hooks/...`
- `adapters/claude/settings.json` PreToolUse 에 matcher 2블록(EnterWorktree, Bash) 등록
- codex/opencode 는 EnterWorktree 표면 없음 → git-worktree-add 경로 체크만 portable,
  built-in-tool deny 는 Claude-native. ADAPTATION_INVENTORY 에 명시 신고(overclaim 금지).

## 지침 보강 (core-first)
- OPERATIONS §5.10: 경로 naming rule 에 hook 각주 + 본작업 행에 "standard+ 다파일·기능 = headless 분사 의무(재량 아님)" (g6 (2) 조건부 문구 명확화)
- CLAUDE.md §0(C): "풀 ceremony 가 필요하면" → "다파일·기능 본작업은 분사 의무" mirror
- HOOKS.md: worktree path isolation 행 추가(census 강제)
- manifest.json: 신규 hook 등록

## 범위 밖
loops/** (g3 assert 화이트리스트·러너 fix — 타 세션 handoff), tools/fleet/**, drill 재실행.
