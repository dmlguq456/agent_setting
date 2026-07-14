#!/usr/bin/env bash
set -euo pipefail

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
RESOLVER="$ROOT/utilities/artifact-root.sh"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

ok() { printf 'ok - %s\n' "$1"; }
fail() { printf 'not ok - %s\n' "$1" >&2; exit 1; }

repo="$TMP/project"
linked="$TMP/project-wt/topic"
mkdir -p "$repo/.agent_reports" "$(dirname "$linked")"
git -C "$TMP" init -q project
git -C "$repo" config user.name test
git -C "$repo" config user.email test@example.com
printf 'root\n' > "$repo/.agent_reports/marker"
git -C "$repo" add .
git -C "$repo" commit -qm init
git -C "$repo" worktree add -q -b topic "$linked"

actual=$("$RESOLVER" "$linked")
[ "$actual" = "$repo/.agent_reports" ] || fail "linked worktree resolves primary artifact root"
ok "linked worktree resolves primary artifact root"

override="$TMP/override/.agent_reports"
mkdir -p "$(dirname "$override")"
actual=$(AGENT_ARTIFACT_ROOT="$override" "$RESOLVER" "$linked")
[ "$actual" = "$override" ] || fail "absolute override wins"
ok "absolute override wins"

set +e
AGENT_ARTIFACT_ROOT=relative "$RESOLVER" "$linked" >/dev/null 2>&1
rc=$?
set -e
[ "$rc" -eq 64 ] || fail "relative override fails"
ok "relative override fails"

legacy="$TMP/legacy"
legacy_wt="$TMP/legacy-wt/topic"
mkdir -p "$legacy/.claude_reports" "$(dirname "$legacy_wt")"
git -C "$TMP" init -q legacy
git -C "$legacy" config user.name test
git -C "$legacy" config user.email test@example.com
printf 'legacy\n' > "$legacy/.claude_reports/marker"
git -C "$legacy" add .
git -C "$legacy" commit -qm init
git -C "$legacy" worktree add -q -b topic "$legacy_wt"
actual=$("$RESOLVER" "$legacy_wt")
[ "$actual" = "$legacy/.claude_reports" ] || fail "legacy fallback is primary-scoped"
ok "legacy fallback is primary-scoped"

nongit="$TMP/nongit"
mkdir -p "$nongit/.agent_reports" "$nongit/a/b"
actual=$("$RESOLVER" "$nongit/a/b")
[ "$actual" = "$nongit/.agent_reports" ] || fail "non-git upward discovery"
ok "non-git upward discovery"
