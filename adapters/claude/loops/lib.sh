#!/bin/bash
# Shared loop helpers; source this file instead of executing it directly.
# study.sh and oncall.sh source it immediately after defining LOG.

# Correct cron's restricted PATH so modern Node handles ESM and ``node:`` imports.
export PATH="$HOME/.local/bin:$PATH"

# Select the runtime adapter through LOOP_ADAPTER; Claude remains the compatibility default.
# Codex and OpenCode use their own sandbox and permission contracts.
LOOP_ADAPTER="${LOOP_ADAPTER:-claude}"

# Retry transient adapter failures with backoff. Session or usage limits abort immediately.
# Usage: run_claude_retry <timeout-seconds> <prompt-file> [extra Claude arguments...]
run_claude_retry() {
  local to="$1" pf="$2"; shift 2
  local max=3 attempt rc out
  local backoff=(0 30 120)   # Delay before each attempt; first attempt starts immediately.
  for ((attempt = 1; attempt <= max; attempt++)); do
    if [ "${backoff[attempt-1]}" -gt 0 ]; then
      echo "=== retry $attempt/$max after ${backoff[attempt-1]}s ==="
      sleep "${backoff[attempt-1]}"
    fi
    case "$LOOP_ADAPTER" in
      codex)
        out="$(timeout "$to" "${CODEX_BIN:-codex}" exec --sandbox workspace-write --skip-git-repo-check - < "$pf" 2>&1)" ;;
      opencode)
        _ocbin="${OPENCODE_BIN:-opencode}"; command -v "$_ocbin" >/dev/null 2>&1 || _ocbin="$HOME/.opencode/bin/opencode"
        out="$(timeout "$to" "$_ocbin" run "$(cat "$pf")" 2>&1)" ;;
      *)
        out="$(timeout "$to" "$HOME/.local/bin/claude" -p "$(cat "$pf")" "$@" 2>&1)" ;;
    esac
    rc=$?
    printf '%s\n' "$out"
    # Usage limits do not clear before reset, so do not retry.
    if printf '%s' "$out" | grep -qiE 'session limit|usage limit|hit your .*limit'; then
      echo "=== ABORT: session/usage limit; retry would not help (rc=$rc, attempt=$attempt) ==="
      return 2
    fi
    # Success requires exit zero and no transient-error marker.
    if [ "$rc" -eq 0 ] && ! printf '%s' "$out" \
        | grep -qiE '401|invalid authentication|overloaded|rate.?limit|internal server error|api error: 5[0-9][0-9]'; then
      return 0
    fi
  done
  echo "=== FAILED after $max attempts (rc=$rc) ==="
  return 1
}
