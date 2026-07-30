#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PROBE="$ROOT/utilities/note-db-readiness.sh"
fixture_root=$(mktemp -d)
trap 'rm -rf "$fixture_root"' EXIT HUP INT TERM

expect_unavailable() {
  expected=$1
  shift
  set +e
  output=$(env -u DATABASE_URL -u TURSO_AUTH_TOKEN -u DATABASE_AUTH_TOKEN "$@" 2>&1)
  rc=$?
  set -e
  [ "$rc" -eq 69 ] || { printf 'expected exit 69, got %s\n%s\n' "$rc" "$output" >&2; exit 1; }
  printf '%s\n' "$output" | grep -q '^note_db_state=unavailable$'
  printf '%s\n' "$output" | grep -q "^reason=$expected$"
}

expect_unavailable worklog-board-app-unset "$PROBE" --check

missing_url="$fixture_root/missing-url"
mkdir -p "$missing_url"
printf '{}\n' > "$missing_url/package.json"
expect_unavailable database-url-unset env WORKLOG_BOARD_APP="$missing_url" "$PROBE" --check

local_db="$fixture_root/local-db"
mkdir -p "$local_db"
printf '{}\n' > "$local_db/package.json"
printf 'DATABASE_URL=file:local.db\n' > "$local_db/.env.local"
expect_unavailable local-database-fallback env WORKLOG_BOARD_APP="$local_db" "$PROBE" --check

unsafe_env="$fixture_root/unsafe-env"
mkdir -p "$unsafe_env"
printf '{}\n' > "$unsafe_env/package.json"
unsafe_marker="$fixture_root/dotenv-shell-content-executed"
printf '%s\n' 'DATABASE_URL=file:local.db' "UNRELATED=\$(touch \"$unsafe_marker\")" > "$unsafe_env/.env.local"
expect_unavailable local-database-fallback env WORKLOG_BOARD_APP="$unsafe_env" "$PROBE" --check
[ ! -e "$unsafe_marker" ] || { echo 'probe executed dotenv shell content' >&2; exit 1; }

missing_client="$fixture_root/missing-client"
mkdir -p "$missing_client"
printf '{}\n' > "$missing_client/package.json"
printf 'DATABASE_URL=libsql://fixture.invalid\n' > "$missing_client/.env.local"
expect_unavailable libsql-client-unavailable env WORKLOG_BOARD_APP="$missing_client" "$PROBE" --check

app="$fixture_root/app"
mkdir -p "$app/node_modules/@libsql/client" "$app/ops/cron"
printf '{}\n' > "$app/package.json"
cat > "$app/node_modules/@libsql/client/index.js" <<'JS'
exports.createClient = function () {
  return {
    execute() {
      if (process.env.FAKE_DB_MODE === "timeout") return new Promise(() => {});
      if (process.env.FAKE_DB_MODE === "fail") return Promise.reject(new Error(process.env.PROBE_SECRET));
      return Promise.resolve({ rows: [{ ready: 1 }] });
    },
    close() {},
  };
};
JS
printf 'DATABASE_URL=libsql://fixture.invalid\nTURSO_AUTH_TOKEN=do-not-print-this-token\n' > "$app/.env.local"

output=$(WORKLOG_BOARD_APP="$app" "$PROBE" --check)
printf '%s\n' "$output" | grep -q '^note_db_state=connected$'
printf '%s\n' "$output" | grep -q '^probe=select-1$'
if printf '%s\n' "$output" | grep -q 'do-not-print-this-token'; then
  echo 'probe leaked a credential' >&2
  exit 1
fi

expect_unavailable db-probe-timeout env WORKLOG_BOARD_APP="$app" FAKE_DB_MODE=timeout NOTE_DB_READINESS_TIMEOUT_MS=100 "$PROBE" --check
failure_output=$(env -u DATABASE_URL -u TURSO_AUTH_TOKEN -u DATABASE_AUTH_TOKEN WORKLOG_BOARD_APP="$app" FAKE_DB_MODE=fail PROBE_SECRET=do-not-print-error-secret "$PROBE" --check 2>&1 || true)
printf '%s\n' "$failure_output" | grep -q '^reason=db-probe-failed$'
if printf '%s\n' "$failure_output" | grep -q 'do-not-print-error-secret'; then
  echo 'probe leaked an exception secret' >&2
  exit 1
fi

set +e
"$PROBE" --bad >/dev/null 2>&1
bad_rc=$?
set -e
[ "$bad_rc" -eq 64 ]

echo 'note-db-readiness tests: ok'
