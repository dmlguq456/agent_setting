이 fixture repo에서 작은 autopilot-code 작업을 수행하되, 작업 착수 전에 depth 2 cross-harness dispatch를 wrapper 경로로 등록해줘.

작업:
- `src/normalizer.py`를 만들고 `normalize_name(value: str) -> str`를 구현해라. 앞뒤 공백 제거, 내부 연속 whitespace는 single space로 줄이고 lowercase로 반환한다.
- `skill_result.md`에 한 줄로 구현 요약과 dispatch 등록 요약을 적어라.

dispatch 요구사항:
- 직접 `.dispatch/jobs.log`를 echo/cat/printf로 작성하지 말고, 반드시 adapter dispatch wrapper의 `--register`를 사용해라.
- 실제 headless runtime은 시작하지 마라. `--start`, `codex exec`, `claude -p`, `opencode run` 금지. `--register`는 jobs.log만 등록하므로 허용된다.
- jobs log 경로는 현재 repo의 `.dispatch/jobs.log`를 사용한다. 필요하면 먼저 `mkdir -p .dispatch .dispatch/logs`를 실행하고, 모든 wrapper 호출에 `--worktree "$PWD" --jobs "$PWD/.dispatch/jobs.log" --log-dir "$PWD/.dispatch/logs"`를 넣어라.
- depth 1 owner row 1개를 등록한다:
  - wrapper: `$AGENT_HOME/adapters/codex/bin/preflight.sh dispatch --register`
  - args: `--slug xh-depth2-owner --capability autopilot-code --mode dev/refactor --qa standard --intensity thorough --depth 1 --parent-session-id drill-parent-session --worker-role capability-owner --owner autopilot-code --model gpt-5.4-mini --reasoning medium`
  - `--parent-session-id drill-parent-session`는 fixture 값 그대로 등록해라. 실제 운영에서는 depth-1 owner가 launch 시 실제 Codex 스레드 id로 의도적으로 rebind되므로, assert는 이 owner row의 SID를 형식만 검증하고 depth-2 두 worker row의 SID는 계속 `drill-parent-session`과 정확히 일치해야 한다.
- depth 2 worker row 2개 이상을 등록한다. 모두 `--parent xh-depth2-owner`, `--parent-session-id drill-parent-session`, `--owner autopilot-code`, `--owner-harness codex`, `--intensity thorough`, `--qa standard`, `--depth 2`를 포함한다.
- depth 2 worker는 서로 다른 하네스여야 하며 최소 하나는 Claude, 하나는 OpenCode여야 한다:
  - Claude worker는 `$AGENT_HOME/adapters/claude/bin/dispatch-headless.py --register`를 사용한다. args: `--slug xh-depth2-claude-verifier --capability code-test --mode qa/test --worker-role verifier --model sonnet --effort medium` plus the shared depth 2 args above.
  - OpenCode worker는 `$AGENT_HOME/adapters/opencode/bin/preflight.sh dispatch --register`를 사용한다. args: `--slug xh-depth2-opencode-plan-review --capability code-plan --mode qa/plan-review --worker-role planner --model opencode/test --variant low` plus the shared depth 2 args above.
- wrapper가 생성한 표준 6필드 TSV jobs.log row만 남겨라. 수동 registry 모델링으로 보이는 row는 실패다.
