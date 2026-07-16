#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MEM="$ROOT/tools/memory/mem.py"
APPLIER="$ROOT/tools/memory/apply-distill-actions.py"
DAILY="$ROOT/tools/memory/daily-curator.py"

TMP="$(mktemp -d)"
STORE="$TMP/store"
STATE="$TMP/state"
PROJECT="$TMP/project"
EVENTS="$TMP/write-events.jsonl"
WORKER="$TMP/worker.sh"
mkdir -p "$STORE" "$STATE" "$PROJECT"
git -C "$PROJECT" init -q
trap 'rm -rf "$TMP"' EXIT

export MEM_STORE="$STORE" MEM_WRITE_EVENTS="$EVENTS" XDG_STATE_HOME="$STATE"
export MEM_DUMP_COMMIT=0 MEM_DAILY_CURATE_TIMEOUT=30

PASS=0
FAIL=0
ok() { PASS=$((PASS + 1)); printf '  PASS %s\n' "$1"; }
bad() { FAIL=$((FAIL + 1)); printf '  FAIL %s\n' "$1"; }

add_record() {
  (cd "$PROJECT" && python3 "$MEM" add "$@") | sed -n 's/.*→ \([^ ]*\).*/\1/p' | tail -n1
}

event() {
  printf '{"ts":"%s","action":"%s","id":"%s","tier":"%s","scope":"%s","type":"%s","actor":"%s","sid":"","snippet":"fixture"}\n' \
    "$1" "$2" "$3" "$4" "$5" "$6" "$7" >> "$EVENTS"
}

RECENT_A="$(add_record working lesson 'recent working memory alpha with enough useful detail')"
RECENT_B="$(add_record durable lesson 'recent durable memory beta with enough useful detail')"
OLD="$(add_record durable lesson 'older canonical memory with enough useful detail')"
PENDING="$(add_record working handoff 'HANDOFF pending memory must remain protected' --requires-consume)"
GLOBAL="$(add_record durable profile 'global profile memory must remain protected' --scope global)"

# Replace uncontrolled current-time events with a deterministic fixture.
: > "$EVENTS"
event 2026-07-14T09:00:00 add "$OLD" durable project lesson manual
event 2026-07-14T11:00:00 add "$RECENT_A" working project lesson manual
event 2026-07-14T11:05:00 add "$RECENT_B" durable project lesson distiller
event 2026-07-14T11:10:00 add "$PENDING" working project handoff manual
event 2026-07-14T11:15:00 add "$GLOBAL" durable global profile manual
event 2026-07-14T11:20:00 reinforce "$OLD" durable project lesson curator

RECENT_JSON="$(cd "$PROJECT" && python3 "$MEM" curate-recent \
  --since 2026-07-14T10:00:00 --until 2026-07-14T12:00:00 --json)"
if RECENT_JSON="$RECENT_JSON" RECENT_A="$RECENT_A" RECENT_B="$RECENT_B" \
  python3 - <<'PY'
import json, os
d = json.loads(os.environ["RECENT_JSON"])
assert d["count"] == 2 and not d["truncated"]
assert [r["id"] for r in d["records"]] == [os.environ["RECENT_A"], os.environ["RECENT_B"]]
PY
then ok "curate-recent uses event timestamps and excludes pending/global/curator events"
else bad "curate-recent focus fence"
fi

HUGE_BODY="$(python3 -c 'print("x" * 8100)')"
HUGE="$(add_record durable lesson "$HUGE_BODY")"
event 2026-07-14T16:00:00 add "$HUGE" durable project lesson manual
HUGE_JSON="$(cd "$PROJECT" && python3 "$MEM" curate-recent \
  --since 2026-07-14T15:00:00 --until 2026-07-14T17:00:00 --json)"
if HUGE_JSON="$HUGE_JSON" HUGE="$HUGE" python3 - <<'PY'
import json, os
d = json.loads(os.environ["HUGE_JSON"])
assert d["count"] == 1 and d["oversized"]
assert d["oversized_ids"] == [os.environ["HUGE"]] and d["records"] == []
PY
then ok "oversized recent bodies fail closed without entering the curator prompt"
else bad "oversized recent body bound"
fi

WATERMARK="$EVENTS.watermark.json"
printf '{"schema":1,"earliest_retained_ts":"2026-07-14T16:00:00","gap_unknown":false}\n' \
  > "$WATERMARK"
GAP_JSON="$(cd "$PROJECT" && python3 "$MEM" curate-recent \
  --since 2026-07-14T15:00:00 --until 2026-07-14T17:00:00 --json)"
if GAP_JSON="$GAP_JSON" python3 - <<'PY'
import json, os
d = json.loads(os.environ["GAP_JSON"])
assert d["journal_gap"] and d["earliest_retained_ts"] == "2026-07-14T16:00:00"
PY
then ok "rotated journal gaps are explicit and cannot silently advance a cursor"
else bad "journal rotation gap fence"
fi
rm -f "$WATERMARK"

SNAP="$TMP/snapshot.ids"
FOCUS="$TMP/focus.ids"
OUT="$TMP/actions.jsonl"
RECEIPT="$TMP/receipt.json"
printf '%s %s %s\n' "$RECENT_A" "$RECENT_B" "$OLD" > "$SNAP"
printf '%s %s\n' "$RECENT_A" "$RECENT_B" > "$FOCUS"
printf '{"action":"merge","ids":["%s","%s"],"canonical":"%s"}\n' \
  "$RECENT_A" "$OLD" "$OLD" > "$OUT"
if (cd "$PROJECT" && python3 "$APPLIER" "$OUT" "$MEM" --mode daily \
    --snapshot-ids "$SNAP" --focus-ids "$FOCUS" --receipt "$RECEIPT" --strict >/dev/null) \
    && RECEIPT="$RECEIPT" python3 - <<'PY'
import json, os
d = json.load(open(os.environ["RECEIPT"], encoding="utf-8"))
assert d["status"] == "ok" and d["applied_count"] == 1
assert [a["action"] for a in d["applied"]] == ["merge"]
PY
then ok "daily applier allows focus merge with older canonical and receipts actions"
else bad "daily applier valid actions"
fi

printf '{"action":"add","tier":"durable","type":"lesson","body":"forbidden"}\n{"action":"prune","id":"%s"}\n{"action":"reinforce","id":"%s"}\n' "$OLD" "$RECENT_B" > "$OUT"
rc=0
(cd "$PROJECT" && python3 "$APPLIER" "$OUT" "$MEM" --mode daily \
  --snapshot-ids "$SNAP" --focus-ids "$FOCUS" --receipt "$RECEIPT" --strict >/dev/null 2>&1) || rc=$?
if [ "$rc" -ne 0 ] && RECEIPT="$RECEIPT" python3 - <<'PY'
import json, os
d = json.load(open(os.environ["RECEIPT"], encoding="utf-8"))
assert d["invalid"] == 3 and d["applied_count"] == 0
PY
then ok "daily applier rejects add, reinforce, and non-focus mutation"
else bad "daily applier invalid action gate"
fi

printf '{"action":"prune","id":"%s"}\n{"action":"add","tier":"durable","type":"lesson","body":"forbidden"}\n' \
  "$RECENT_B" > "$OUT"
rc=0
(cd "$PROJECT" && python3 "$APPLIER" "$OUT" "$MEM" --mode daily \
  --snapshot-ids "$SNAP" --focus-ids "$FOCUS" --receipt "$RECEIPT" \
  --validate-only --strict >/dev/null 2>&1) || rc=$?
if [ "$rc" -ne 0 ] && (cd "$PROJECT" && python3 "$MEM" show "$RECENT_B" >/dev/null) \
    && RECEIPT="$RECEIPT" python3 - <<'PY'
import json, os
d = json.load(open(os.environ["RECEIPT"], encoding="utf-8"))
assert d["validation_only"] and d["invalid"] == 1 and d["applied_count"] == 0
PY
then ok "mixed valid/invalid output is rejected before any daily mutation"
else bad "daily validation-before-apply gate"
fi

git -C "$STORE" init -q
git -C "$STORE" config user.name fixture
git -C "$STORE" config user.email fixture@example.invalid
git -C "$STORE" config push.default current
git -C "$STORE" remote add origin "$TMP/mirror.git"
MIRROR_BRANCH="$(git -C "$STORE" branch --show-current)"
rc=0
(cd "$PROJECT" && MEM_DUMP_COMMIT=1 MEM_DUMP_PUSH=1 python3 "$MEM" \
  sync --mirror-only --strict >/dev/null 2>&1) || rc=$?
git init --bare -q "$TMP/mirror.git"
retry_rc=0
(cd "$PROJECT" && MEM_DUMP_COMMIT=1 MEM_DUMP_PUSH=1 python3 "$MEM" \
  sync --mirror-only --strict >/dev/null 2>&1) || retry_rc=$?
if [ "$rc" -ne 0 ] && [ "$retry_rc" -eq 0 ] \
    && git --git-dir="$TMP/mirror.git" rev-parse --verify \
      "refs/heads/$MIRROR_BRANCH" >/dev/null 2>&1
then ok "strict mirror blocks on push failure and retries an unchanged dump"
else bad "strict dump commit/push propagation"
fi

cat > "$WORKER" <<'SH'
#!/usr/bin/env bash
[ "${STUB_WORKER_FAIL:-0}" = "1" ] && exit 9
printf '%s\n' "${STUB_WORKER_OUTPUT:-}"
SH
chmod +x "$WORKER"

# Rebuild a clean journal window for orchestrator cursor tests. RECENT_B remains
# live and becomes the first successful no-action review.
: > "$EVENTS"
event 2026-07-14T11:30:00 add "$RECENT_B" durable project lesson manual
CURSOR="$STATE/agent-memory/daily-state.json"
REPORT="$STATE/agent-memory/daily-report.json"
UNSUPPORTED_STATE="$STATE/agent-memory/unsupported-state.json"
UNSUPPORTED_REPORT="$STATE/agent-memory/unsupported-report.json"
rc=0
python3 "$DAILY" --project "$PROJECT" --state "$UNSUPPORTED_STATE" \
  --report "$UNSUPPORTED_REPORT" --now 2026-07-14T12:00:00 >/dev/null || rc=$?
if [ "$rc" -ne 0 ] && [ ! -f "$UNSUPPORTED_STATE" ] \
    && UNSUPPORTED_REPORT="$UNSUPPORTED_REPORT" python3 - <<'PY'
import json, os
r = json.load(open(os.environ["UNSUPPORTED_REPORT"], encoding="utf-8"))
assert r["projects"][0]["phase"] == "unsupported-worker"
PY
then ok "unsupported runtime worker leaves the project cursor untouched"
else bad "unsupported worker fail-closed receipt"
fi

if python3 "$DAILY" --project "$PROJECT" --worker "$WORKER" \
    --state "$CURSOR" --report "$REPORT" --now 2026-07-14T12:00:00 >/dev/null \
    && CURSOR="$CURSOR" REPORT="$REPORT" python3 - <<'PY'
import json, os
s = json.load(open(os.environ["CURSOR"], encoding="utf-8"))
r = json.load(open(os.environ["REPORT"], encoding="utf-8"))
assert list(s["projects"].values())[0]["last_success_at"] == "2026-07-14T12:00:00"
assert r["status"] == "ok" and r["projects"][0]["applied_count"] == 0
PY
then ok "successful no-action curator advances project cursor"
else bad "initial daily curator success"
fi

RETRY="$(add_record working thread 'retry memory created after the first successful cursor')"
event 2026-07-14T12:30:00 add "$RETRY" working project thread manual
rc=0
STUB_WORKER_FAIL=1 python3 "$DAILY" --project "$PROJECT" --worker "$WORKER" \
  --state "$CURSOR" --report "$REPORT" --now 2026-07-14T13:00:00 >/dev/null || rc=$?
if [ "$rc" -ne 0 ] && CURSOR="$CURSOR" REPORT="$REPORT" python3 - <<'PY'
import json, os
s = json.load(open(os.environ["CURSOR"], encoding="utf-8"))
r = json.load(open(os.environ["REPORT"], encoding="utf-8"))
assert list(s["projects"].values())[0]["last_success_at"] == "2026-07-14T12:00:00"
assert r["status"] == "failed" and r["projects"][0]["phase"] == "worker"
PY
then ok "worker failure leaves cursor unchanged and records failed phase"
else bad "cursor fail-closed on worker failure"
fi

if python3 "$DAILY" --project "$PROJECT" --worker "$WORKER" \
    --state "$CURSOR" --report "$REPORT" --now 2026-07-14T13:00:00 >/dev/null \
    && CURSOR="$CURSOR" python3 - <<'PY'
import json, os
s = json.load(open(os.environ["CURSOR"], encoding="utf-8"))
assert list(s["projects"].values())[0]["last_success_at"] == "2026-07-14T13:00:00"
PY
then ok "next daily run retries the unchanged window and advances on success"
else bad "cursor retry"
fi

GRAD="$(add_record working decision 'working memory selected for daily graduation action')"
event 2026-07-14T13:30:00 add "$GRAD" working project decision manual
ACTION=$(printf '{"action":"graduate","id":"%s","to":"durable"}' "$GRAD")
if STUB_WORKER_OUTPUT="$ACTION" python3 "$DAILY" --project "$PROJECT" --worker "$WORKER" \
    --state "$CURSOR" --report "$REPORT" --now 2026-07-14T14:00:00 >/dev/null \
    && (cd "$PROJECT" && python3 "$MEM" show "$GRAD") | grep -q '^tier: durable$' \
    && REPORT="$REPORT" GRAD="$GRAD" python3 - <<'PY'
import json, os
r = json.load(open(os.environ["REPORT"], encoding="utf-8"))
p = r["projects"][0]
assert r["applied_count"] == 1 and p["mirror_sync"] == "ok"
assert p["actions"] == [{"action": "graduate", "target": os.environ["GRAD"]}]
PY
then ok "daily action is applied, mirrored, and fully receipted"
else bad "daily action receipt and mirror"
fi

PROJECT2="$TMP/project2"
mkdir -p "$PROJECT2"
git -C "$PROJECT2" init -q
BUDGET_A="$(add_record working thread 'first project memory for bounded worker budget test')"
BUDGET_B="$(cd "$PROJECT2" && python3 "$MEM" add working thread \
  'second project memory for bounded worker budget test' \
  | sed -n 's/.*→ \([^ ]*\).*/\1/p' | tail -n1)"
event 2026-07-14T14:30:00 add "$BUDGET_A" working project thread manual
event 2026-07-14T14:31:00 add "$BUDGET_B" working project thread manual
rc=0
python3 "$DAILY" --project "$PROJECT" --project "$PROJECT2" --worker "$WORKER" \
  --max-workers 1 --state "$CURSOR" --report "$REPORT" \
  --now 2026-07-14T15:00:00 >/dev/null || rc=$?
if [ "$rc" -ne 0 ] && REPORT="$REPORT" python3 - <<'PY'
import json, os
r = json.load(open(os.environ["REPORT"], encoding="utf-8"))
assert r["worker_runs"] == 1 and r["failed_count"] == 1
assert sorted(p["phase"] for p in r["projects"]) == ["complete", "worker-budget"]
PY
then ok "deep-worker budget defers excess projects without silent cursor advance"
else bad "daily worker budget"
fi

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
