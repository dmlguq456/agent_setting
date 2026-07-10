이 fixture repo에서 작은 코드 작업을 수행하면서, Claude Code depth 1 owner가 OpenCode depth 2 worker를 실제 `--start`로 띄우는지 확인해줘.

작업:
- `src/slugger.py`를 만들고 `slugify(value: str) -> str`를 구현해라. 앞뒤 공백 제거, lowercase, 연속 non-alphanumeric은 single `-`로 치환, 앞뒤 `-` 제거.
- `skill_result.md`에 한 줄로 구현 요약과 dispatch 시작 요약을 적어라.

dispatch 요구사항:
- 직접 `.dispatch/jobs.log`를 echo/cat/printf로 작성하지 말고, 반드시 adapter dispatch wrapper를 사용해라.
- jobs log 경로는 현재 repo의 `.dispatch/jobs.log`를 사용한다. 먼저 `mkdir -p .dispatch .dispatch/logs`를 실행하고, 모든 wrapper 호출에 `--worktree "$PWD" --jobs "$PWD/.dispatch/jobs.log" --log-dir "$PWD/.dispatch/logs"`를 넣어라.
- wrapper stdout/stderr는 `dispatch_wrapper_output.txt`에 누적 저장해라.
- depth 1 Claude owner row 1개를 등록한다:
  - wrapper: `$AGENT_HOME/adapters/claude/bin/dispatch-headless.py --register`
  - args: `--slug xh-claude-owner --capability autopilot-code --mode dev/refactor --qa standard --intensity standard --depth 1 --parent-session-id drill-claude-parent-session --worker-role capability-owner --owner autopilot-code --owner-harness claude --model sonnet --effort medium`
- depth 2 OpenCode worker row 1개를 실제 시작한다:
  - wrapper: `$AGENT_HOME/adapters/opencode/bin/preflight.sh dispatch --start`
  - args: `--slug xh-claude-opencode-verifier --capability code-test --mode qa/test --qa standard --intensity standard --depth 2 --parent xh-claude-owner --parent-session-id drill-claude-parent-session --worker-role verifier --owner autopilot-code --owner-harness claude --inherit-model-settings --prompt-file "$PWD/opencode_depth2_prompt.md"`
- OpenCode worker는 `opencode_depth2_prompt.md`의 marker를 응답해야 한다. parent Claude가 직접 marker를 쓰거나 child log를 위조하지 마라.
- `--start`는 OpenCode worker에만 사용한다. `claude -p`나 `opencode run`을 직접 호출하지 말고 wrapper를 통해서만 호출한다.
