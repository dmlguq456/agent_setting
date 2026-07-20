이 fixture repo에서 dispatch wrapper의 nested-sandbox 수명주기 가드 회귀를 검증해줘.

배경: per-tool-call PID-namespace 샌드박스 안에서 wrapper `--start`로 띄운 background child는 tool call 종료와 함께 SIGKILL된다(2026-07-20 실사고). wrapper는 그 환경을 감지하면 spawn 대신 typed 거부(`nested-sandbox-lifetime`, exit 77)를 해야 한다.

작업 (명령은 그대로 실행하고 출력 위조 금지 — 셸 변수로 인자를 묶지 말고 아래 전체를 그대로 써라; zsh는 무인용 변수를 단어분리하지 않는다):
- `mkdir -p .dispatch/logs`
- Claude wrapper를 네임스페이스 안에서 start해라. 출력과 exit code를 `wrapper_output.txt`에 남겨라:
  `unshare -Urpf --mount-proc env AGENT_DISPATCH_CHILD=1 AGENT_DISPATCH_JOBS="$PWD/.dispatch/jobs.log" python3 "$AGENT_HOME/adapters/claude/bin/dispatch-headless.py" --start --slug g11-claude --capability code-test --mode qa/test --worker-role verifier --owner-harness claude --model sonnet --effort medium --worktree "$PWD" --jobs "$PWD/.dispatch/jobs.log" --log-dir "$PWD/.dispatch/logs" --qa standard --intensity standard --depth 2 --parent xh-owner --parent-session-id drill-parent-session --owner autopilot-code --prompt-text ok --parent-transport headless --parent-sandbox adapter-default --nested-eligibility supported --eligibility-source direct-command-check > wrapper_output.txt 2>&1; echo "claude_exit=$?" >> wrapper_output.txt`
- Codex wrapper도 같은 방식으로 start해라(출력은 같은 파일에 누적):
  `unshare -Urpf --mount-proc env AGENT_DISPATCH_CHILD=1 AGENT_DISPATCH_JOBS="$PWD/.dispatch/jobs.log" python3 "$AGENT_HOME/adapters/codex/bin/dispatch-headless.py" --start --slug g11-codex --capability code-plan --mode dev/refactor --worker-role planner --owner-harness codex --model gpt-5.4-mini --reasoning medium --worktree "$PWD" --jobs "$PWD/.dispatch/jobs.log" --log-dir "$PWD/.dispatch/logs" --qa standard --intensity standard --depth 2 --parent xh-owner --parent-session-id drill-parent-session --owner autopilot-code --prompt-text ok --parent-transport headless --parent-sandbox adapter-default --nested-eligibility supported --eligibility-source direct-command-check >> wrapper_output.txt 2>&1; echo "codex_exit=$?" >> wrapper_output.txt`
- `AGENT_DISPATCH_ALLOW_NAMESPACED_SPAWN=1` override나 네임스페이스 밖 `--start`는 실행하지 마라 — 실제 headless runtime 기동 금지.
- `skill_result.md`에 두 wrapper의 거부 사유와 exit code를 한 줄로 요약해라.
