#!/usr/bin/env bash
# dispatch-headless.sd15.test.sh — SD-15 (OPERATIONS §5.10 ⑨) limit-사망 즉시 감지 회귀 (codex).
#   Homomorphic with adapters/claude/bin/dispatch-headless.sd15.test.sh. codex 는 --start 가
#   preflight projection 게이트(capability-info/mode-info/headless --check)를 거치므로, bare
#   fixture 에서 full --start 를 돌리는 대신 이식된 SD-15 헬퍼(scan_death/watch_early_death/
#   close_job_row/write_reset_cache)를 import 로 직접 구동해 동일 3증명을 검증한다:
#   (1) scan_death 패턴/reset 추출 (2) launch 직후 조기 limit-death → row done,note=dead-<reason>,
#   reset=<x> 로 마감 + reset 캐시 (3) clean 조기 exit(비-limit)는 row 를 안 건드림(open 유지).
set -uo pipefail
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
WRAP="$SCRIPT_DIR/dispatch-headless.py"
fails=0
ok()  { printf 'ok   - %s\n' "$1"; }
bad() { printf 'FAIL - %s\n' "$1"; fails=$((fails + 1)); }

# --- Unit: scan_death ---
u=$(python3 - "$WRAP" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("dh", sys.argv[1])
dh = importlib.util.module_from_spec(spec); spec.loader.exec_module(dh)
cases = {
  "You've hit your session limit · resets 3pm": ("session-limit", "3pm"),
  "Error: usage_limit_reached, resets at 5:30pm": ("usage-limit", "5:30pm"),
  "exceeded retry limit, last status: 429 Too Many Requests": ("usage-limit", ""),
  "invalid api key provided": ("auth", ""),
  "websocket connect failed: Operation not permitted": ("network-operation-not-permitted", ""),
  "all good, work complete": None,
}
bad = 0
for text, want in cases.items():
    got = dh.scan_death(text)
    if got != want:
        print(f"MISMATCH {text!r}: got {got} want {want}"); bad += 1
print("SCAN_OK" if bad == 0 else "SCAN_FAIL")
PY
)
echo "$u" | grep -q SCAN_OK && ok "scan_death patterns (codex 429/usage_limit_reached) + reset" || bad "scan_death: $u"

# A depth-1 Codex owner belongs to the actual caller thread even when an older
# conductor passes a synthetic id. Depth-2 ownership remains broker-explicit.
parent=$(CODEX_THREAD_ID=real-thread python3 - "$WRAP" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("dh", sys.argv[1])
dh = importlib.util.module_from_spec(spec); spec.loader.exec_module(dh)

d1 = dh.parser().parse_args([
    "--worktree", "/work/repo", "--slug", "owner", "--capability", "autopilot-code",
    "--mode", "debug", "--depth", "1", "--parent", "synthetic-owner",
    "--parent-session-id", "synthetic-thread",
])
dh._bind_runtime_parent(d1)
print(f"D1={d1.parent_session_id}:{d1.parent_slug or '-'}")

d2 = dh.parser().parse_args([
    "--worktree", "/work/repo", "--slug", "stage", "--capability", "code-plan",
    "--mode", "debug", "--depth", "2", "--parent", "real-owner",
    "--parent-session-id", "owner-thread",
])
dh._bind_runtime_parent(d2)
print(f"D2={d2.parent_session_id}:{d2.parent_slug or '-'}")
PY
)
echo "$parent" | grep -q '^D1=real-thread:-$' \
  && echo "$parent" | grep -q '^D2=owner-thread:real-owner$' \
  && ok "depth-1 binds actual Codex thread; depth-2 keeps broker parent" \
  || bad "runtime parent binding: $parent"

command -v git >/dev/null || { echo "(git 없음 — skip launch cases)"; exit $fails; }
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
AH="$tmp/agent_setting"; mkdir -p "$AH/.dispatch/logs"

# Drive the ported SD-15 start-block helpers exactly as main()'s --start path does.
drive=$(python3 - "$WRAP" "$AH" <<'PY'
import importlib.util, subprocess, sys, time
from pathlib import Path
spec = importlib.util.spec_from_file_location("dh", sys.argv[1])
dh = importlib.util.module_from_spec(spec); spec.loader.exec_module(dh)
AH = Path(sys.argv[2])
jobs = AH / ".dispatch" / "jobs.log"
logs = AH / ".dispatch" / "logs"

def row(slug, wt):
    pipe = f"capability=code-plan,mode=dev,qa=standard,intensity=standard,depth=2,harness=codex,parent=cx,worker_role=code-plan,owner=autopilot-code"
    with jobs.open("a", encoding="utf-8") as f:
        f.write(f"2026-07-10T00:00:00Z\topen\t/repo\t{wt}\t{slug}\t{pipe}\n")

def launch(slug, body, watch):
    wt = f"/wt/{slug}"
    row(slug, wt)
    log_path = logs / f"{slug}.codex.jsonl"
    proc = subprocess.Popen(["sh", "-c", f"( {body} ) >> {log_path} 2>&1"], start_new_session=True)
    death = dh.watch_early_death(proc, log_path, watch)
    if death:
        reason, reset = death
        dh.close_job_row(jobs, slug, wt, reason, reset)
        dh.write_reset_cache(AH, "codex", reason, reset)
        return f"early_death={reason}:{reset}"
    return "early_death=-"

print(launch("limit1", "echo \"You've hit your session limit · resets 3pm\"; exit 1", 6))
print(launch("clean1", "echo ok done; exit 0", 4))
wt = "/wt/pidrow"; row("pidrow", wt)
proc = subprocess.Popen(["bash", "-c", "exec -a codex sleep 5"])
start = dh.process_start_ticks(proc.pid)
ok = dh.annotate_job_row(jobs, "pidrow", wt, f"pid={proc.pid},pid_start={start}")
proc.terminate(); proc.wait()
print("PID_ANNOTATED" if ok and f"pid={proc.pid},pid_start={start}" in jobs.read_text() else "PID_MISSING")
PY
)

echo "$drive" | grep -q 'early_death=session-limit:3pm' \
  && grep -q $'\tdone\t.*note=dead-session-limit,reset=3pm' "$AH/.dispatch/jobs.log" \
  && ok "limit-death → row done,note=dead-session-limit,reset=3pm" \
  || bad "limit-death row not closed. drive=[$drive] jobs=[$(cat "$AH/.dispatch/jobs.log")]"
[ -f "$AH/.dispatch/usage-reset.codex" ] && ok "reset cache written" || bad "no reset cache"

echo "$drive" | grep -q 'PID_ANNOTATED' \
  && ok "Codex wrapper records pid and process start ticks on the open row (O1)" \
  || bad "Codex pid annotation missing. drive=[$drive]"

echo "$drive" | grep -q 'early_death=-' \
  && awk -F'\t' '$5=="clean1"{print $2}' "$AH/.dispatch/jobs.log" | grep -qx open \
  && ok "clean fast exit → row stays open (normal harvest owns it)" \
  || bad "clean exit wrongly closed. drive=[$drive]"

# Axis 6 (SD-15b): liveness log_shows_limit judges a limit log DEAD regardless of transcript.
LIVE="$SCRIPT_DIR/dispatch-liveness.py"
live=$(python3 - "$LIVE" "$AH" <<'PY'
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("lv", sys.argv[1])
lv = importlib.util.module_from_spec(spec); spec.loader.exec_module(lv)
AH = Path(sys.argv[2])
hit = lv.log_shows_limit(AH, "limit1")
miss = lv.log_shows_limit(AH, "clean1")
worktree = AH / "nested-worktree"
local_sessions = worktree / ".dispatch" / "codex-home" / "sessions"
stores = lv.sessions_dirs_for("", "nested", AH, AH / "default-sessions", str(worktree))
profile_stores = lv.sessions_dirs_for(
    "profile=lab", "nested", AH, AH / "default-sessions", str(worktree)
)
paths_ok = stores == [local_sessions, AH / "default-sessions"]
profile_ok = profile_stores == [AH / ".dispatch" / "homes" / "nested.lab" / "sessions"]
print(
    "LIVE_OK"
    if (hit is not None and miss is None and paths_ok and profile_ok)
    else f"LIVE_FAIL hit={hit} miss={miss} stores={stores} profile={profile_stores}"
)
PY
)
echo "$live" | grep -q LIVE_OK && ok "liveness limit scan + nested CODEX_HOME resolution" || bad "liveness: $live"

echo "— codex dispatch-headless SD-15 conformance: $([ $fails -eq 0 ] && echo PASS || echo "FAIL ($fails)")"
exit $fails
