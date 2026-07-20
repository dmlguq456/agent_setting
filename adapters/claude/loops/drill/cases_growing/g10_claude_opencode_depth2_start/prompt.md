이 fixture repo에서 작은 코드 작업을 수행하면서, 현재 drill adapter의 depth-1 owner가 OpenCode depth-2 worker를 실제 `--start`로 띄우는지 확인해줘.

작업:
- `src/slugger.py`를 만들고 `slugify(value: str) -> str`를 구현해라. 앞뒤 공백 제거, lowercase, 연속 non-alphanumeric은 single `-`로 치환, 앞뒤 `-` 제거.
- `skill_result.md`에 한 줄로 구현 요약과 dispatch 시작 요약을 적어라.

dispatch 요구사항:
- `.dispatch/g10_parent.env`를 source해 `PARENT_ADAPTER`, `PARENT_RUNTIME_SURFACE`, `PARENT_SESSION_ID`를 사용해라.
- 직접 jobs.log를 쓰지 말고 반드시 adapter dispatch wrapper를 사용해라.
- fleet에서는 fixture worktree 그룹 안에서 선택 adapter owner 아래 OpenCode depth-2 child가 보여야 한다.
- fleet 계층 판정은 실행 뒤 `assert.sh`가 jobs registry로 수행한다. 작업 중 fleet UI를 직접 실행하거나 fleet 소스를 분석하지 마라.
- `mkdir -p .dispatch "$AGENT_HOME/.dispatch/logs"` 후 `RUN_ID="$(date -u +%H%M%S)-$$"`, `OWNER_SLUG="g10-owner-$RUN_ID"`, `CHILD_SLUG="g10-opencode-$RUN_ID"`, `SHARED_JOBS="${AGENT_DISPATCH_JOBS:-$AGENT_HOME/.dispatch/jobs.log}"`, `SHARED_LOG_DIR="$AGENT_HOME/.dispatch/logs"`를 설정해라. 등록·감시·수확은 모두 이 단일 registry를 사용해야 한다.
- `printf 'OWNER_SLUG=%s\nCHILD_SLUG=%s\n' "$OWNER_SLUG" "$CHILD_SLUG" > .dispatch/g10_slugs.env`를 남겨라.
- depth-1 owner 등록은 `.dispatch/register_owner.sh "$OWNER_SLUG" "$SHARED_JOBS" "$SHARED_LOG_DIR"`만 사용하고 stdout/stderr를 `dispatch_wrapper_output.txt`에 누적해라. owner는 `--start`하지 마라. 등록 직후 `.dispatch/g10_parent.env`를 다시 source해 wrapper가 확정한 실제 `PARENT_SESSION_ID`를 이후 child 등록에 사용해라.
- `opencode_depth2_prompt.md`를 `sed`로 복사하면서 marker의 `parent=xh-parent`만 `parent=$OWNER_SLUG`로 바꿔 `.dispatch/opencode_depth2_prompt.runtime.md`를 만들어라.
- OpenCode child는 `$AGENT_HOME/adapters/opencode/bin/preflight.sh dispatch --start`와 다음 args로 시작하고 출력을 같은 wrapper 파일에 누적해라: `--worktree "$PWD" --jobs "$SHARED_JOBS" --log-dir "$SHARED_LOG_DIR" --slug "$CHILD_SLUG" --capability code-test --mode qa/test --intensity standard --depth 2 --parent "$OWNER_SLUG" --parent-session-id "$PARENT_SESSION_ID" --worker-type review --assigned-contract code-test --owner autopilot-code --owner-harness "$PARENT_ADAPTER" --inherit-model-settings --prompt-file "$PWD/.dispatch/opencode_depth2_prompt.runtime.md"`.
- owner와 child의 새 registry row에는 `worker_role`이 없어야 한다.
- child가 prompt marker를 응답해야 한다. parent가 marker나 child log를 위조하지 마라.
- owner/child를 직접 harvest하거나 `done`으로 바꾸지 마라. runner의 `assert.sh`가 live 계층을 판정한 뒤 두 row를 수확한다.
- `claude -p`, `codex exec`, `opencode run`을 직접 호출하지 마라.
