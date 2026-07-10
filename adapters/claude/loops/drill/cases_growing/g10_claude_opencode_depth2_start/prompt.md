이 fixture repo에서 작은 코드 작업을 수행하면서, Claude Code depth 1 owner가 OpenCode depth 2 worker를 실제 `--start`로 띄우는지 확인해줘.

작업:
- `src/slugger.py`를 만들고 `slugify(value: str) -> str`를 구현해라. 앞뒤 공백 제거, lowercase, 연속 non-alphanumeric은 single `-`로 치환, 앞뒤 `-` 제거.
- `skill_result.md`에 한 줄로 구현 요약과 dispatch 시작 요약을 적어라.

dispatch 요구사항:
- 직접 `.dispatch/jobs.log`를 echo/cat/printf로 작성하지 말고, 반드시 adapter dispatch wrapper를 사용해라.
- 이 케이스는 메인 세션 아래에 억지로 붙이지 않는다. fleet에서는 fixture worktree 기준의 별도 `drill:g10_claude_opencode_depth2_start/` 그룹으로 보이고, 그 그룹 안에서 Claude owner 아래 OpenCode depth-2 child가 들여쓰기되어 보여야 한다.
- fleet UI가 보는 shared registry를 사용해야 한다. 먼저 `mkdir -p .dispatch "$AGENT_HOME/.dispatch/logs"`를 실행하고, `RUN_ID="$(date -u +%H%M%S)-$$"`, `OWNER_SLUG="g10-owner-$RUN_ID"`, `CHILD_SLUG="g10-opencode-$RUN_ID"`, `SHARED_JOBS="$AGENT_HOME/.dispatch/jobs.log"`, `SHARED_LOG_DIR="$AGENT_HOME/.dispatch/logs"`를 설정해라.
- `printf 'OWNER_SLUG=%s\nCHILD_SLUG=%s\n' "$OWNER_SLUG" "$CHILD_SLUG" > .dispatch/g10_slugs.env`를 남겨 assert가 실제 slug를 알 수 있게 해라.
- 모든 wrapper 호출에 `--worktree "$PWD" --jobs "$SHARED_JOBS" --log-dir "$SHARED_LOG_DIR"`를 넣어라. repo-local `.dispatch/jobs.log`에 내부 depth row를 쓰면 fleet UI에 parent/child dispatch로 보이지 않으므로 실패다.
- wrapper stdout/stderr는 `dispatch_wrapper_output.txt`에 누적 저장해라.
- depth 1 Claude owner row 1개를 등록한다:
  - wrapper: `$AGENT_HOME/adapters/claude/bin/dispatch-headless.py --register`
  - args: `--slug "$OWNER_SLUG" --capability autopilot-code --mode dev/refactor --qa standard --intensity standard --depth 1 --parent-session-id drill-claude-parent-session --worker-role capability-owner --owner autopilot-code --owner-harness claude --model sonnet --effort medium`
- depth 2 OpenCode worker row 1개를 실제 시작한다:
  - wrapper: `$AGENT_HOME/adapters/opencode/bin/preflight.sh dispatch --start`
  - 실행 전에 `opencode_depth2_prompt.md`를 `.dispatch/opencode_depth2_prompt.runtime.md`로 복사하되, marker line의 `parent=xh-claude-owner`를 `parent=$OWNER_SLUG`로 바꿔라. 관찰용 sleep 지시가 있으면 그대로 보존해라.
  - args: `--slug "$CHILD_SLUG" --capability code-test --mode qa/test --qa standard --intensity standard --depth 2 --parent "$OWNER_SLUG" --parent-session-id drill-claude-parent-session --worker-role verifier --owner autopilot-code --owner-harness claude --inherit-model-settings --prompt-file "$PWD/.dispatch/opencode_depth2_prompt.runtime.md"`
- OpenCode worker는 `.dispatch/opencode_depth2_prompt.runtime.md`의 marker를 응답해야 한다. parent Claude가 직접 marker를 쓰거나 child log를 위조하지 마라.
- `--start`는 OpenCode worker에만 사용한다. `claude -p`나 `opencode run`을 직접 호출하지 말고 wrapper를 통해서만 호출한다.
