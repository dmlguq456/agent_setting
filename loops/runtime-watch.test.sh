#!/usr/bin/env bash
set -uo pipefail

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
WATCH="$ROOT/loops/runtime-watch.sh"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

fetch="$tmp/fetch"
local_probe="$tmp/local-probe"
cat > "$fetch" <<'SH'
#!/usr/bin/env bash
printf '<html><body><main>stable official content</main><script>request-id=%s</script></body></html>\n' "$RANDOM"
SH
cat > "$local_probe" <<'SH'
#!/usr/bin/env bash
printf 'codex_cli=codex-test\nclaude_cli=claude-test\nprojection=status-ok\n'
SH
chmod +x "$fetch" "$local_probe"

run_watch() {
  AGENT_HOME="$ROOT" \
  RUNTIME_WATCH_FETCH_CMD="$fetch" \
  RUNTIME_WATCH_LOCAL_PROBE_CMD="$local_probe" \
  RUNTIME_WATCH_STATE_DIR="$tmp/state" \
  RUNTIME_WATCH_OUT_DIR="$tmp/out" \
  bash "$WATCH" --run
}

first=$(run_watch)
case "$first" in *'status=report-written'*) ;; *) echo "FAIL first run: $first" >&2; exit 1 ;; esac
report=$(printf '%s' "$first" | sed 's/.* report=//')
first_mtime=$(stat -c %Y "$report")
sleep 1
second=$(run_watch)
second_mtime=$(stat -c %Y "$report")

case "$second" in *'status=unchanged'*) ;; *) echo "FAIL stable rerun: $second" >&2; exit 1 ;; esac
[ "$first_mtime" = "$second_mtime" ] || { echo 'FAIL unchanged report was rewritten' >&2; exit 1; }
grep -q '^## Runtime Support$' "$report" || { echo 'FAIL report contract' >&2; exit 1; }
echo 'runtime-watch conformance: PASS'
