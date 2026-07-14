#!/usr/bin/env bash
# Compatibility regression for the retired automatic recall hook.
set -u

HOOK="$(cd "$(dirname "$0")" && pwd)/mem-recall-inject.sh"
[ -x "$HOOK" ] || { echo "FAIL: compatibility shim is not executable: $HOOK"; exit 1; }

PASS=0
FAIL=0
ok()  { PASS=$((PASS + 1)); printf '  ok  %s\n' "$1"; }
bad() { FAIL=$((FAIL + 1)); printf '  BAD %s\n' "$1"; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "== retired automatic recall hook =="
printf '{"hook_event_name":"UserPromptSubmit","prompt":"remember this","cwd":"%s"}\n' "$TMP" \
  | "$HOOK" >"$TMP/stdin.out" 2>"$TMP/stdin.err"
rc=$?
[ "$rc" = 0 ] && [ ! -s "$TMP/stdin.out" ] && [ ! -s "$TMP/stdin.err" ] \
  && ok "stdin hook payload is a silent no-op" \
  || bad "stdin compatibility path emitted output or failed"

"$HOOK" --prompt "remember this" --cwd "$TMP" --format text >"$TMP/cli.out" 2>"$TMP/cli.err"
rc=$?
[ "$rc" = 0 ] && [ ! -s "$TMP/cli.out" ] && [ ! -s "$TMP/cli.err" ] \
  && ok "legacy CLI arguments are a silent no-op" \
  || bad "legacy CLI compatibility path emitted output or failed"

printf 'not json' | "$HOOK" >"$TMP/malformed.out" 2>"$TMP/malformed.err"
rc=$?
[ "$rc" = 0 ] && [ ! -s "$TMP/malformed.out" ] && [ ! -s "$TMP/malformed.err" ] \
  && ok "malformed input fails open" \
  || bad "malformed input did not fail open"

"$HOOK" --help >"$TMP/help.out" 2>"$TMP/help.err"
rc=$?
[ "$rc" = 0 ] && grep -qi 'deprecated' "$TMP/help.out" \
  && grep -qi 'agent-initiated' "$TMP/help.out" \
  && ok "help points to agent-initiated retrieval" \
  || bad "help does not explain the retired contract"

echo
echo "RESULT: PASS=$PASS FAIL=$FAIL"
[ "$FAIL" = 0 ]
