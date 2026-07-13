#!/bin/bash
# Legacy case id, portable behavior: the selected drill adapter owns depth 1
# and starts an OpenCode depth-2 verifier through adapter wrappers.
set -eu
WORK=$1
REPO="$WORK/repo"
PARENT_ADAPTER="${DRILL_ADAPTER:-claude}"
OBSERVE_SECONDS="${DRILL_G10_OBSERVE_SECONDS:-0}"
case "$PARENT_ADAPTER" in
  claude) PARENT_RUNTIME_SURFACE=claude-print-headless ;;
  codex) PARENT_RUNTIME_SURFACE=codex-exec-headless ;;
  opencode) PARENT_RUNTIME_SURFACE=opencode-run-headless ;;
  *) echo "unsupported DRILL_ADAPTER=$PARENT_ADAPTER" >&2; exit 64 ;;
esac
case "$OBSERVE_SECONDS" in
  ''|*[!0-9]*) OBSERVE_SECONDS=0 ;;
esac
PARENT_SESSION_ID="drill-$PARENT_ADAPTER-parent-session"

mkdir -p "$REPO/.dispatch" "$REPO/src" "$WORK/.pre"
cd "$REPO"
git init -q && git checkout -q -b main
git config user.email drill@test && git config user.name drill
cat > README.md <<MD
# Selected-adapter owner to OpenCode depth-2 fixture

This fixture checks one portable behavior through the selected adapter runner:

- drill parent adapter: \`$PARENT_ADAPTER\`;
- the parent registers its own depth-1 owner row through its adapter wrapper;
- the parent starts an OpenCode depth-2 child through the OpenCode wrapper;
- the child emits the fixture marker in its JSON log.
MD
cat > src/__init__.py <<'PY'
PY
cat > .dispatch/g10_parent.env <<ENV
PARENT_ADAPTER=$PARENT_ADAPTER
PARENT_RUNTIME_SURFACE=$PARENT_RUNTIME_SURFACE
PARENT_SESSION_ID=$PARENT_SESSION_ID
ENV
cat > .dispatch/register_owner.sh <<'SH'
#!/bin/bash
set -eu
OWNER_SLUG=$1
SHARED_JOBS=$2
SHARED_LOG_DIR=$3
# shellcheck source=/dev/null
. "$PWD/.dispatch/g10_parent.env"
common=(--worktree "$PWD" --jobs "$SHARED_JOBS" --log-dir "$SHARED_LOG_DIR"
  --slug "$OWNER_SLUG" --capability autopilot-code --mode dev/refactor
  --intensity standard --depth 1 --parent-session-id "$PARENT_SESSION_ID"
  --worker-role capability-owner --owner autopilot-code
  --owner-harness "$PARENT_ADAPTER" --inherit-model-settings)
case "$PARENT_ADAPTER" in
  claude) "$AGENT_HOME/adapters/claude/bin/dispatch-headless.py" --register "${common[@]}" ;;
  codex) "$AGENT_HOME/adapters/codex/bin/preflight.sh" dispatch --register "${common[@]}" ;;
  opencode) "$AGENT_HOME/adapters/opencode/bin/preflight.sh" dispatch --register "${common[@]}" ;;
  *) echo "unsupported PARENT_ADAPTER=$PARENT_ADAPTER" >&2; exit 64 ;;
esac
resolved_parent_session_id=$(awk -F '\t' -v slug="$OWNER_SLUG" -v worktree="$PWD" '
  $4 == worktree && $5 == slug { pipe = $6 }
  END {
    count = split(pipe, parts, ",")
    for (i = 1; i <= count; i++) {
      if (parts[i] ~ /^parent_sid=/) {
        sub(/^parent_sid=/, "", parts[i])
        print parts[i]
        exit
      }
    }
  }
' "$SHARED_JOBS")
case "$resolved_parent_session_id" in
  ''|*[!A-Za-z0-9_.:-]*) echo "invalid resolved parent_sid=$resolved_parent_session_id" >&2; exit 65 ;;
esac
# Codex drill runs replace the fixture placeholder with the actual outer thread
# id. Persist the wrapper-resolved value so the OpenCode child and assert use the
# same ancestry instead of inventing a second parent session.
printf 'PARENT_SESSION_ID=%s\n' "$resolved_parent_session_id" >> "$PWD/.dispatch/g10_parent.env"
printf 'resolved_parent_session_id=%s\n' "$resolved_parent_session_id"
SH
chmod +x .dispatch/register_owner.sh
{
cat <<'MD'
You are the OpenCode depth-2 verifier for the portable g10 drill case.

MD
if [ "$OBSERVE_SECONDS" -gt 0 ]; then
  printf 'First run `sleep %s` so the fleet UI has time to show this depth-2 dispatch row.\n\n' "$OBSERVE_SECONDS"
fi
cat <<MD
Do not edit files. Reply with one short line containing exactly this marker and the parent linkage:

OPENCODE_DEPTH2_VERIFIER_PASS parent=xh-parent owner_harness=$PARENT_ADAPTER depth=2
MD
} > opencode_depth2_prompt.md
git add -A && git commit -q -m init
printf '%s\n' "$REPO/.dispatch/jobs.log" > "$WORK/.pre/jobs_path"
