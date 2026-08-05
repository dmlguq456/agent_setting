#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
RESOLVER="$ROOT/utilities/artifact-root.sh"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

ok() { printf 'ok - %s\n' "$1"; }
fail() { printf 'not ok - %s\n' "$1" >&2; exit 1; }

# Every call below runs with AGENT_ARTIFACT_ROOT explicitly unset -- an
# inherited value from the caller's environment must never leak into these
# assertions (a prior session or wrapper may have exported it).

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

actual=$(env -u AGENT_ARTIFACT_ROOT "$RESOLVER" "$linked")
[ "$actual" = "$repo/.agent_reports" ] || fail "linked worktree resolves primary artifact root"
ok "linked worktree resolves primary artifact root"

override="$TMP/override/.agent_reports"
mkdir -p "$(dirname "$override")"
actual=$(env -u AGENT_ARTIFACT_ROOT AGENT_ARTIFACT_ROOT="$override" "$RESOLVER" "$linked")
[ "$actual" = "$override" ] || fail "absolute override wins"
ok "absolute override wins"

set +e
env -u AGENT_ARTIFACT_ROOT AGENT_ARTIFACT_ROOT=relative "$RESOLVER" "$linked" >/dev/null 2>&1
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
actual=$(env -u AGENT_ARTIFACT_ROOT "$RESOLVER" "$legacy_wt")
[ "$actual" = "$legacy/.claude_reports" ] || fail "legacy fallback is primary-scoped"
ok "legacy fallback is primary-scoped"

# --- D-3: non-Git marker boundary -----------------------------------------

# cwd itself is the root: no marker needed, self is not inheritance.
self_root="$TMP/self-root"
mkdir -p "$self_root/.agent_reports"
actual=$(env -u AGENT_ARTIFACT_ROOT "$RESOLVER" "$self_root")
[ "$actual" = "$self_root/.agent_reports" ] || fail "cwd itself is root without a marker"
ok "cwd itself is root without a marker"

# marker-bearing ancestor -> inherited.
marked="$TMP/marked"
marked_child="$marked/a/b"
mkdir -p "$marked/.agent_reports" "$marked_child"
: > "$marked/.agent-workspace"
actual=$(env -u AGENT_ARTIFACT_ROOT "$RESOLVER" "$marked_child")
[ "$actual" = "$marked/.agent_reports" ] || fail "marker-bearing ancestor is inherited"
ok "marker-bearing ancestor is inherited"

# marker-less ancestor -> falls back to <cwd>/.agent_reports, not inherited.
unmarked="$TMP/unmarked"
unmarked_child="$unmarked/a/b"
mkdir -p "$unmarked/.agent_reports" "$unmarked_child"
actual=$(env -u AGENT_ARTIFACT_ROOT "$RESOLVER" "$unmarked_child")
[ "$actual" = "$unmarked_child/.agent_reports" ] || fail "marker-less ancestor falls back to cwd"
ok "marker-less ancestor falls back to cwd"

# only a mid-level ancestor carries the marker: it wins over a marker-less
# grandparent root further up.
tiered="$TMP/tiered"
tiered_mid="$tiered/mid"
tiered_child="$tiered_mid/leaf"
mkdir -p "$tiered/.agent_reports" "$tiered_mid/.agent_reports" "$tiered_child"
: > "$tiered_mid/.agent-workspace"
actual=$(env -u AGENT_ARTIFACT_ROOT "$RESOLVER" "$tiered_child")
[ "$actual" = "$tiered_mid/.agent_reports" ] || fail "nearest marked ancestor wins over a farther unmarked one"
ok "nearest marked ancestor wins over a farther unmarked one"

# legacy .claude_reports root plus marker is still inherited.
legacy_marked="$TMP/legacy-marked"
legacy_marked_child="$legacy_marked/a"
mkdir -p "$legacy_marked/.claude_reports" "$legacy_marked_child"
: > "$legacy_marked/.agent-workspace"
actual=$(env -u AGENT_ARTIFACT_ROOT "$RESOLVER" "$legacy_marked_child")
[ "$actual" = "$legacy_marked/.claude_reports" ] || fail "legacy root plus marker is inherited"
ok "legacy root plus marker is inherited"

echo "artifact-root.test.sh: all assertions passed"
