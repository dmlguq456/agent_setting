# 최종 보고 — worktree-path-guard hook 승격

drill g3·g6 FAIL(내장 `EnterWorktree` 로 repo 안 `.claude/worktrees/` 에 worktree 를 파
main 워킹트리를 오염) 대응으로 경로 컨벤션 `<repo>-wt/<slug>` 를 hard 강제하는 PreToolUse 가드를 신설했다.

## 변경 파일
- **신설** `hooks/worktree-path-guard.sh` — canonical 가드 (POSIX sh, dual mode)
- **신설** `adapters/claude/hooks/worktree-path-guard.sh` — collapsed symlink(`../../../hooks/...`, layer-sync 계약)
- `adapters/claude/settings.json` — PreToolUse 에 EnterWorktree·Bash matcher 2블록 등록
- `hooks/portable-guards.test.sh` — `== worktree path guard CLI ==` 7케이스 추가
- `core/OPERATIONS.md` §5.10 — 경로 rule hook 각주 + "standard+ 다파일·기능 = 분사 의무(재량 아님)" 명확화(g6)
- `core/HOOKS.md` — worktree path isolation 행(census 강제 + overclaim 경계 신고)
- `core/ADAPTATION_INVENTORY.md` — Worktree path isolation guard 행(codex/opencode overclaim 금지 신고)
- `adapters/claude/CLAUDE.md` §0(C) — 위 분사 의무 mirror
- `manifest.json` — 신규 hook 등록(재생성)

## hook 동작 매트릭스
| 케이스 | 판정 |
|---|---|
| EnterWorktree(git cwd) | **deny** |
| Bash `git worktree add`, `<repo>-wt/` 밖 | **deny** |
| Bash `git worktree add`, 정규 `<repo>-wt/slug` | 통과 |
| `git worktree remove/list/prune` | 통과(무간섭) |
| `.untracked.<sid>` flag 존재 | 통과(⚡untracked 우회) |
| 비-git cwd | 통과(fail-open) |
| 무관 Bash / 빈 입력 / 파싱 실패 | 통과 |

deny 사유엔 정규 절차(`git worktree add <root>-wt/<slug> -b <slug> <base>` → jobs.log 등록 →
headless 분사) + `/track` 우회를 실었다. 실측은 `test_logs/verification.md` 참조.

## 검증 명령·결과
- `sh -n hooks/worktree-path-guard.sh` → ok
- `bash hooks/portable-guards.test.sh` → PASS=303 FAIL=11 (신규 7건 전부 PASS; FAIL 11은 baseline 동일 재현되는 사전 실패 — codex/opencode 런타임·dispatch-liveness·node_modules, 본 변경 무관)
- `bash tools/check-adaptation-boundary.sh` → OK
- `python3 tools/build-manifest.py --check` → up-to-date
- byte-budget: 5236 bytes

## 설계 판단
"오차단 금지가 최우선" 원칙에 맞춰 막는 건 (a)EnterWorktree 전면 (b)`<repo>-wt/` 밖
`git worktree add` 둘뿐이고, 정규 경로 add·비-add 서브커맨드·untracked·비-git·파싱 실패는
전부 fail-open. 특히 오케스트레이터·conductor 의 정상 분사(`<repo>-wt/<slug>` add)는 절대
차단하지 않는다. Agent(isolation:worktree)·Workflow worktree 는 Bash/EnterWorktree 툴이
아니므로 matcher 에 애초에 안 걸린다.

## 범위 밖 (미착수)
- `loops/**` (g3 assert 화이트리스트·g9/g10 러너 fix — 타 세션 handoff) · `tools/fleet/**`
- drill 재실행 — merge 후 메인 오케스트레이터가 g3·g6 재드릴

## 인계
이 브랜치(`worktree-path-guard`)에 커밋 누적, push·merge·worktree cleanup 은 메인 오케스트레이터 몫.
