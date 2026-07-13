#!/usr/bin/env sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
jobs="$tmp/jobs.log"; : > "$jobs"
before=$(sha256sum "$jobs")
route() { AGENT_HOME="$tmp" HARNESS_ROUTE_SLOT="${HARNESS_ROUTE_SLOT:-0}" "$root/utilities/dispatch-route.sh" --jobs "$jobs" "$@"; }
assert() { printf '%s\n' "$1" | grep -qx "$2"; }

out=$(route --stage plan); assert "$out" 'adapter=codex'; assert "$out" 'role=deep maker'
out=$(route --stage plan --adapter claude); assert "$out" 'adapter=claude'
out=$(route --stage report); assert "$out" 'adapter=claude'
out=$(HARNESS_ROUTE_SLOT=1 route --stage report); assert "$out" 'adapter=codex'
out=$(HARNESS_CAPACITY_BIAS=codex route --stage report); assert "$out" 'adapter=codex'
out=$(route --stage code-review --maker-family claude); assert "$out" 'adapter=codex'
out=$(route --stage code-review --maker-family gpt); assert "$out" 'adapter=claude'
printf '%s\tdone\tx\tx\tx\tharness=claude,note=dead-session-limit\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$jobs"
out=$(route --stage code-review --adapter claude); assert "$out" 'adapter=codex'; printf '%s\n' "$out" | grep -q '^rejected.1=claude:usage-limited'; assert "$out" 'fallback.1=codex:known-limit-on-claude'
out=$(route --stage test --maker-family unknown); assert "$out" 'trace.2=affinity=diverse;maker_family=unknown;required=none;bias=auto'; assert "$out" 'trace.3=usage-selection=known-limit:claude'
out=$(route --stage plan --adapter opencode); assert "$out" 'status=unknown'; assert "$out" 'family=unknown'
out2=$(route --stage test --maker-family gpt); [ "$out" != "$out2" ]
after=$(sha256sum "$jobs"); [ "$before" != "$after" ] # fixture write only
before=$(sha256sum "$jobs"); route --stage plan >/dev/null; after=$(sha256sum "$jobs"); [ "$before" = "$after" ]
printf '%s\tdone\tx\tx\tx2\tharness=codex,note=dead-usage-limit\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$jobs"
if out=$(route --stage report 2>/dev/null); then exit 1; else rc=$?; fi
[ "$rc" -eq 1 ]; assert "$out" 'status=unavailable'; assert "$out" 'fallback.1=none:no-eligible-known-candidate'
rm "$jobs"; out=$(route --stage report); assert "$out" 'trace.1=explicit=none;family=none;eligibility=usage-unknown'
! route --stage plan --adapter claude --family gpt >/dev/null 2>&1
echo 'dispatch-route: PASS'
