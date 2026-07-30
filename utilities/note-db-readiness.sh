#!/usr/bin/env sh
set -eu

usage() {
  echo "usage: note-db-readiness.sh --check" >&2
  exit 64
}

unavailable() {
  printf 'note_db_state=unavailable\nreason=%s\n' "$1"
  exit 69
}

[ "$#" -eq 1 ] && [ "$1" = "--check" ] || usage

app=${WORKLOG_BOARD_APP:-}
[ -n "$app" ] || unavailable worklog-board-app-unset
[ -d "$app" ] || unavailable worklog-board-app-missing
[ -f "$app/package.json" ] || unavailable board-package-missing
command -v node >/dev/null 2>&1 || unavailable node-unavailable

timeout_ms=${NOTE_DB_READINESS_TIMEOUT_MS:-8000}
case "$timeout_ms" in
  ''|*[!0-9]*) unavailable invalid-timeout ;;
esac
if [ "$timeout_ms" -lt 100 ] || [ "$timeout_ms" -gt 30000 ]; then
  unavailable invalid-timeout
fi

set +e
(
  cd "$app" || exit 73
  NOTE_DB_READINESS_TIMEOUT_MS=$timeout_ms node <<'NODE'
const { createRequire } = require("node:module");
const fs = require("node:fs");

const allowed = new Set(["DATABASE_URL", "TURSO_AUTH_TOKEN", "DATABASE_AUTH_TOKEN"]);
const inherited = Object.fromEntries(
  [...allowed].filter((key) => process.env[key] !== undefined).map((key) => [key, process.env[key]])
);
const config = {};

function dotenvValue(raw) {
  const value = raw.trim();
  if (value.length >= 2 && value[0] === value[value.length - 1]
      && (value[0] === '"' || value[0] === "'")) {
    return value.slice(1, -1);
  }
  return value;
}

for (const path of [".env.local", "ops/cron/.agent.env"]) {
  if (!fs.existsSync(path)) continue;
  let body;
  try {
    body = fs.readFileSync(path, "utf8");
  } catch (_) {
    process.exit(75);
  }
  for (const line of body.split(/\r?\n/)) {
    const match = line.match(/^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/);
    if (match && allowed.has(match[1])) config[match[1]] = dotenvValue(match[2]);
  }
}
Object.assign(config, inherited);

const databaseUrl = config.DATABASE_URL || "";
if (!databaseUrl) process.exit(73);
if (/^(?:file:|:memory:)/i.test(databaseUrl)) process.exit(74);

let createClient;
try {
  ({ createClient } = createRequire(process.cwd() + "/package.json")("@libsql/client"));
} catch (_) {
  process.exit(70);
}
if (typeof createClient !== "function") process.exit(70);

const timeoutMs = Number(process.env.NOTE_DB_READINESS_TIMEOUT_MS);
const authToken = config.TURSO_AUTH_TOKEN || config.DATABASE_AUTH_TOKEN || undefined;
let client;
let timer;

(async () => {
  try {
    client = createClient({ url: databaseUrl, authToken });
    await Promise.race([
      client.execute("SELECT 1 AS ready"),
      new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error("probe-timeout")), timeoutMs);
      }),
    ]);
  } catch (error) {
    process.exitCode = error && error.message === "probe-timeout" ? 71 : 72;
  } finally {
    if (timer) clearTimeout(timer);
    if (client && typeof client.close === "function") {
      try { client.close(); } catch (_) {}
    }
  }
})();
NODE
)
probe_rc=$?
set -e

case "$probe_rc" in
  0)
    printf 'note_db_state=connected\nreason=-\nprobe=select-1\n'
    ;;
  70) unavailable libsql-client-unavailable ;;
  71) unavailable db-probe-timeout ;;
  72) unavailable db-probe-failed ;;
  73) unavailable database-url-unset ;;
  74) unavailable local-database-fallback ;;
  75) unavailable credential-source-unavailable ;;
  *) unavailable db-probe-unavailable ;;
esac
