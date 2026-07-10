# 검증 로그 — worktree-path-guard

## hook 동작 매트릭스 (실측)

| # | 입력 | 기대 | 결과 |
|---|---|---|---|
| 1 | EnterWorktree, git cwd | deny | ✅ hook JSON deny(exit0) / CLI exit2 |
| 2 | Bash `git worktree add .claude/worktrees/foo` (밖) | deny | ✅ deny |
| 3 | Bash `git worktree add <repo>-wt/slug` (정규) | 통과 | ✅ exit0 (오차단 금지 ①) |
| 4 | Bash `git worktree remove/list/prune` | 통과 | ✅ exit0 (비-add 무간섭) |
| 5 | EnterWorktree + `.untracked.<sid>` flag | 통과 | ✅ exit0 (⚡untracked 우회) |
| 6 | EnterWorktree, 비-git cwd(`/tmp`) | 통과 | ✅ exit0 (fail-open) |
| 7 | Bash 무관 명령(`ls -la && git status`) | 통과 | ✅ exit0 |
| 8 | 빈 stdin | 통과 | ✅ exit0 |

## 단위 테스트 (hooks/portable-guards.test.sh, `== worktree path guard CLI ==`)
7개 케이스 추가, 전부 PASS:
- denies builtin EnterWorktree (exit 2)
- denies git worktree add outside -wt/ (exit 2)
- passes regular <repo>-wt/<slug> add
- leaves non-add worktree subcommands alone
- honors ⚡untracked bypass flag
- fails open outside a git repo
- leaves unrelated Bash commands alone

## 전체 스위트 결과
- `bash hooks/portable-guards.test.sh` → PASS=303 FAIL=11
- FAIL 11건은 **사전 실패**(baseline HEAD stash 대조 시 동일 재현): codex/opencode
  dispatch·harvest 래퍼(런타임 CLI 미설치), dispatch-liveness.sh(transcript 타이밍),
  codex doctor --runtime, opencode node_modules 정리 — 본 변경과 무관.
- 내 신규 7건은 전부 통과, FAIL 증가 없음.

## 정합성 검증
- `sh -n hooks/worktree-path-guard.sh` → syntax ok
- `bash -n hooks/portable-guards.test.sh` → ok
- `bash tools/check-adaptation-boundary.sh` → OK (HOOKS.md census + collapsed symlink 3-class 통과)
- `python3 tools/build-manifest.py --check` → manifest up-to-date; delta baselines bound
- byte-budget: hooks/worktree-path-guard.sh = 5236 bytes
