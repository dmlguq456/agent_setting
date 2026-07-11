#!/usr/bin/env bash
# Cluster J (v15, D-37/D-38/D-39) — write-events 저널 + mem log + mem doctor.
# ABSOLUTE: every case uses isolated MEM_STORE/MEM_PROJECTS/MEM_WRITE_EVENTS (mktemp -d).
# NEVER writes real runtime memory. This suite spawns NO `claude` (ISO-2).
set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MEM="$ROOT/tools/memory/mem.py"
APPLIER="$ROOT/tools/memory/apply-distill-actions.py"
[ -f "$MEM" ] || { echo "FAIL: mem.py not found at $MEM"; exit 1; }

PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); printf '  ok  %s\n' "$1"; }
bad() { FAIL=$((FAIL+1)); printf '  BAD %s\n' "$1"; }

BASE_STORE="$(mktemp -d)"; BASE_PROJ="$(mktemp -d)"; WORKDIR="$(mktemp -d)"
trap 'rm -rf "$BASE_STORE" "$BASE_PROJ" "$WORKDIR"' EXIT
export MEM_STORE="$BASE_STORE" MEM_PROJECTS="$BASE_PROJ" MEM_WRITE_EVENTS="$BASE_STORE/write-events.jsonl"
cd "$WORKDIR"   # non-git → project_key = bare enc_cwd (repo-independent)

PKEY="$(PYTHONPATH="$ROOT/tools/memory" python3 -c 'import mem; print(mem.project_key())')"

initdb() { PYTHONPATH="$ROOT/tools/memory" python3 -c 'import mem; mem.get_con().close()' >/dev/null 2>&1; }
sql() { python3 - "$MEM_STORE/memory.db" "$@" <<'PY'
import sqlite3, sys
con = sqlite3.connect(sys.argv[1]); con.execute("PRAGMA busy_timeout=5000")
cur = con.execute(sys.argv[2], sys.argv[3:] if len(sys.argv) > 3 else [])
rows = cur.fetchall(); con.commit()
for r in rows: print("|".join("" if x is None else str(x) for x in r))
con.close()
PY
}
seed() { # id tier scope type cwd_origin strength last_accessed body [expires] [delivery_state] [created]
  python3 - "$MEM_STORE/memory.db" "$@" <<'PY'
import sqlite3, sys, datetime
db, rid, tier, scope, rtype, cwd, strg, la, body = sys.argv[1:10]
exp = sys.argv[10] if len(sys.argv) > 10 and sys.argv[10] else None
delivery = sys.argv[11] if len(sys.argv) > 11 and sys.argv[11] else "ordinary"
created = sys.argv[12] if len(sys.argv) > 12 and sys.argv[12] else datetime.date.today().isoformat()
con = sqlite3.connect(db); con.execute("PRAGMA busy_timeout=5000")
today = datetime.date.today().isoformat()
con.execute("INSERT OR REPLACE INTO records(id,tier,scope,type,cwd_origin,created,updated,"
            "expires,source,tags,links,body,strength,last_accessed,injection_flag,delivery_state) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,?)",
            (rid, tier, scope, rtype, cwd, created, today, exp, None, "[]", "[]",
             body, int(strg), la or today, delivery))
try: con.execute("INSERT INTO records_fts(id, body) VALUES(?,?)", (rid, body))
except Exception: pass
con.commit(); con.close()
PY
}
raw_delete() { # id — 3-table delete (records+fts+trig), 테스트 fixture cleanup 전용
  python3 - "$MEM_STORE/memory.db" "$@" <<'PY'
import sqlite3, sys
con = sqlite3.connect(sys.argv[1]); con.execute("PRAGMA busy_timeout=5000")
rid = sys.argv[2]
con.execute("DELETE FROM records WHERE id=?", (rid,))
try: con.execute("DELETE FROM records_fts WHERE id=?", (rid,))
except Exception: pass
try: con.execute("DELETE FROM records_trig WHERE id=?", (rid,))
except Exception: pass
con.commit(); con.close()
PY
}
raw_delete_like() { # pattern — 3-table delete by id LIKE pattern
  python3 - "$MEM_STORE/memory.db" "$@" <<'PY'
import sqlite3, sys
con = sqlite3.connect(sys.argv[1]); con.execute("PRAGMA busy_timeout=5000")
pat = sys.argv[2]
ids = [r[0] for r in con.execute("SELECT id FROM records WHERE id LIKE ?", (pat,)).fetchall()]
for rid in ids:
    con.execute("DELETE FROM records WHERE id=?", (rid,))
    try: con.execute("DELETE FROM records_fts WHERE id=?", (rid,))
    except Exception: pass
    try: con.execute("DELETE FROM records_trig WHERE id=?", (rid,))
    except Exception: pass
con.commit(); con.close()
PY
}
events() { [ -f "$MEM_WRITE_EVENTS" ] && cat "$MEM_WRITE_EVENTS" || true; }
event_count() { events | grep -c . || true; }
last_event_field() { # field
  events | tail -1 | python3 -c "import json,sys; print(json.load(sys.stdin).get(sys.argv[1],''))" "$1"
}

initdb
TODAY="$(python3 -c 'import datetime;print(datetime.date.today().isoformat())')"

# =====================================================================
echo "== D-37: 전 변이 경로 저널 append =="

: > "$MEM_WRITE_EVENTS"
python3 "$MEM" add working thread "journal add body one" >/dev/null
[ "$(last_event_field action)" = add ] && [ "$(last_event_field actor)" = manual ] \
  && ok "add → action=add actor=manual" || bad "add journal mismatch: $(events | tail -1)"

python3 "$MEM" note "journal note body two" >/dev/null
[ "$(last_event_field action)" = note ] && ok "note → action=note" || bad "note journal mismatch"

seed j_consume working project handoff "$PKEY" 1 "$TODAY" "consume me body" "" pending
python3 "$MEM" consume j_consume >/dev/null
[ "$(last_event_field action)" = consume ] && [ "$(last_event_field id)" = j_consume ] \
  && ok "consume → action=consume" || bad "consume journal mismatch: $(events | tail -1)"

seed j_reinforce durable project lesson "$PKEY" 1 "$TODAY" "reinforce me body"
python3 "$MEM" reinforce j_reinforce >/dev/null
[ "$(last_event_field action)" = reinforce ] && ok "reinforce → action=reinforce" || bad "reinforce journal mismatch"

seed j_prune durable project note "$PKEY" 1 "$TODAY" "prune me body"
python3 "$MEM" prune j_prune >/dev/null
[ "$(last_event_field action)" = prune ] && ok "prune → action=prune" || bad "prune journal mismatch"

seed j_mc durable project lesson "$PKEY" 1 "$TODAY" "merge canonical body"
seed j_mb durable project lesson "$PKEY" 1 "$TODAY" "merge fold-in body"
python3 "$MEM" merge --canonical j_mc j_mc j_mb >/dev/null
[ "$(last_event_field action)" = merge ] && [ "$(last_event_field id)" = j_mc ] \
  && ok "merge → action=merge id=canonical" || bad "merge journal mismatch: $(events | tail -1)"

seed j_grad working project thread "$PKEY" 1 "$TODAY" "graduate me body"
python3 "$MEM" graduate j_grad >/dev/null
[ "$(last_event_field action)" = graduate ] && ok "graduate → action=graduate" || bad "graduate journal mismatch"

seed j_ra working project thread "-orphan-dir-nonexistent" 1 "$TODAY" "reattribute me body"
python3 "$MEM" reattribute j_ra >/dev/null
[ "$(last_event_field action)" = reattribute ] && ok "reattribute → action=reattribute" || bad "reattribute journal mismatch"

seed j_del durable project note "$PKEY" 1 "$TODAY" "delete me body"
python3 "$MEM" delete j_del >/dev/null
[ "$(last_event_field action)" = delete ] && ok "delete → action=delete" || bad "delete journal mismatch"

python3 "$MEM" restore j_del >/dev/null
[ "$(last_event_field action)" = restore ] && [ "$(last_event_field actor)" = restore ] \
  && ok "restore → action=restore actor=restore" || bad "restore journal mismatch: $(events | tail -1)"

OLD="$(python3 -c 'import datetime;print((datetime.date.today()-datetime.timedelta(days=5)).isoformat())')"
seed j_exp working project thread "$PKEY" 1 "$TODAY" "expire me body" "$OLD"
python3 "$MEM" lifecycle --apply >/dev/null
[ "$(last_event_field action)" = lifecycle-expire ] && [ "$(last_event_field actor)" = lifecycle ] \
  && ok "lifecycle --apply → action=lifecycle-expire actor=lifecycle" \
  || bad "lifecycle journal mismatch: $(events | tail -1)"

N_ACTIONS=11
[ "$(event_count)" -ge "$N_ACTIONS" ] && ok "저널 라인수 >= $N_ACTIONS (전 변이 경로 커버)" \
  || bad "저널 라인수 부족: $(event_count)"

# =====================================================================
echo "== D-37: actor 결정론 (env MEM_DISTILL / MEM_ACTOR) =="

: > "$MEM_WRITE_EVENTS"
MEM_DISTILL=1 python3 "$MEM" add working thread "distiller-origin body" >/dev/null
[ "$(last_event_field actor)" = distiller ] && ok "MEM_DISTILL=1 → actor=distiller" \
  || bad "distiller actor mismatch: $(last_event_field actor)"

seed j_curate durable project note "$PKEY" 1 "$TODAY" "curator prune target"
MEM_DISTILL=1 MEM_ACTOR=curator python3 "$MEM" prune j_curate >/dev/null
[ "$(last_event_field actor)" = curator ] \
  && ok "MEM_ACTOR=curator overrides MEM_DISTILL=1 → actor=curator" \
  || bad "curator override failed: $(last_event_field actor)"

# apply-distill-actions.py --mode curate wires MEM_ACTOR=curator itself
seed j_curate2 durable project note "$PKEY" 1 "$TODAY" "applier curator target"
OUT="$WORKDIR/actions.jsonl"; SNAP="$WORKDIR/snap_ids.txt"
printf '{"action":"prune","id":"j_curate2"}\n' > "$OUT"
printf 'j_curate2\n' > "$SNAP"
: > "$MEM_WRITE_EVENTS"
MEM_DISTILL=1 python3 "$APPLIER" "$OUT" "$MEM" --mode curate --snapshot-ids "$SNAP" >/dev/null
[ "$(last_event_field actor)" = curator ] \
  && ok "apply-distill-actions.py --mode curate → actor=curator (env wiring)" \
  || bad "applier curator wiring failed: $(events | tail -1)"

# =====================================================================
echo "== D-37: fail-open (저널 write 실패가 mutation을 막지 않음) =="

BAD_DIR="$(mktemp -d)"; chmod 000 "$BAD_DIR"
MEM_WRITE_EVENTS="$BAD_DIR/nested/write-events.jsonl" python3 "$MEM" add working thread "fail-open body should still write" >/dev/null
COUNT="$(sql "SELECT COUNT(*) FROM records WHERE body LIKE 'fail-open body%'")"
[ "$COUNT" = 1 ] && ok "저널 append 실패해도 DB write 성공 (fail-open)" \
  || bad "fail-open 위반: mutation 이 저널 실패에 막힘 (count=$COUNT)"
chmod 755 "$BAD_DIR"; rm -rf "$BAD_DIR"

# =====================================================================
echo "== D-37: rotation (256KB/500줄 bound) =="

: > "$MEM_WRITE_EVENTS"
python3 - "$MEM_WRITE_EVENTS" <<'PY'
import json, sys
path = sys.argv[1]
with open(path, "w", encoding="utf-8") as f:
    for i in range(3000):
        f.write(json.dumps({"ts": "t", "action": "add", "id": f"pad_{i}", "tier": "working",
                             "scope": "project", "type": "note", "actor": "manual", "sid": "",
                             "snippet": "x" * 100}) + "\n")
PY
SZ_BEFORE="$(wc -c < "$MEM_WRITE_EVENTS")"
[ "$SZ_BEFORE" -gt 262144 ] || bad "rotation fixture setup: pre-size too small ($SZ_BEFORE)"
python3 "$MEM" add working thread "rotation trigger body" >/dev/null
LINES_AFTER="$(event_count)"
[ "$LINES_AFTER" -le 501 ] && ok "rotation: append 후 줄수 <= 501 (최근 500 + 신규1), got $LINES_AFTER" \
  || bad "rotation 미작동: 줄수=$LINES_AFTER"
[ "$(last_event_field id)" != "" ] && [ "$(events | tail -1 | grep -c 'rotation trigger')" = 1 ] \
  && ok "rotation: 최신 이벤트 보존" || bad "rotation: 최신 이벤트 유실"

# =====================================================================
echo "== D-38: mem log 필터 =="

: > "$MEM_WRITE_EVENTS"
python3 "$MEM" add working thread "log-fixture-one-body" >/dev/null
seed j_log2 durable project note "$PKEY" 1 "$TODAY" "log-fixture-two-body"
python3 "$MEM" prune j_log2 >/dev/null
python3 "$MEM" add durable thread "log-fixture-three-body" >/dev/null

OUT="$(python3 "$MEM" log --limit 20)"
echo "$OUT" | grep -q "log-fixture-three-body" && ok "mem log: 기본 출력에 최근 이벤트 포함" \
  || bad "mem log 기본 출력 누락"

OUT_ACTION="$(python3 "$MEM" log --action prune)"
LC="$(echo "$OUT_ACTION" | grep -c '  prune')"
[ "$LC" = 1 ] && ok "mem log --action prune → prune 1건만" || bad "mem log --action 필터 실패 (n=$LC)"

OUT_JSON="$(python3 "$MEM" log --json --limit 5)"
python3 -c "import json,sys; d=json.loads(sys.argv[1]); assert 'events' in d and isinstance(d['events'], list)" "$OUT_JSON" \
  && ok "mem log --json → 파싱 가능한 events 배열" || bad "mem log --json 형식 오류"

OUT_LIMIT="$(python3 "$MEM" log --json --limit 1)"
N="$(python3 -c "import json,sys; print(len(json.loads(sys.argv[1])['events']))" "$OUT_LIMIT")"
[ "$N" = 1 ] && ok "mem log --limit 1 → 1건" || bad "mem log --limit 무시됨 (n=$N)"

# =====================================================================
echo "== D-39: mem doctor — clean store → exit 0 =="

: > "$MEM_WRITE_EVENTS"; rm -f "$MEM_STORE/deleted-records.jsonl" "$MEM_STORE/dump.jsonl"
python3 -c "
import sys; sys.path.insert(0, '$ROOT/tools/memory')
import mem
con = mem.get_con()
con.execute('DELETE FROM records')
try: con.execute('DELETE FROM records_fts')
except Exception: pass
try: con.execute('DELETE FROM records_trig')
except Exception: pass
con.commit(); con.close()
"
MEM_DISTILL=1 python3 "$MEM" add working thread "clean doctor fixture body" >/dev/null
python3 "$MEM" export --target dump >/dev/null
python3 "$MEM" doctor >/tmp/doctor_clean.out; RC=$?
[ "$RC" = 0 ] && ok "doctor: clean store → exit 0" || bad "doctor clean rc=$RC: $(cat /tmp/doctor_clean.out)"
grep -q '\[FAIL\]' /tmp/doctor_clean.out && bad "doctor clean: FAIL 항목 존재해선 안 됨" \
  || ok "doctor clean: FAIL 항목 없음"

# =====================================================================
echo "== D-39: mem doctor — 위반 fixture 별 WARN/FAIL =="

# ③ schema invariant violation — pending 아닌 working 인데 expires NULL
seed viol_expires working project thread "$PKEY" 1 "$TODAY" "missing expires body" "" ordinary
sql "UPDATE records SET expires=NULL WHERE id='viol_expires'" >/dev/null
python3 "$MEM" doctor >/tmp/doctor_schema.out; RC=$?
grep -q '\[FAIL\] schema-invariants' /tmp/doctor_schema.out \
  && ok "doctor: non-pending working NULL expires → schema-invariants FAIL" \
  || bad "doctor schema-invariants 미검출: $(cat /tmp/doctor_schema.out)"
[ "$RC" = 2 ] && ok "doctor: FAIL 존재 → exit 2" || bad "doctor exit code != 2 (got $RC)"
raw_delete viol_expires >/dev/null

# ⑤ stale pending
OLD22="$(python3 -c 'import datetime;print((datetime.date.today()-datetime.timedelta(days=25)).isoformat())')"
seed viol_pending working project handoff "$PKEY" 1 "$TODAY" "stale pending body" "" pending "$OLD22"
python3 "$MEM" doctor >/tmp/doctor_pending.out; RC=$?
grep -q '\[WARN\] stale-pending' /tmp/doctor_pending.out \
  && ok "doctor: 21일+ pending 미소비 → stale-pending WARN" \
  || bad "doctor stale-pending 미검출: $(cat /tmp/doctor_pending.out)"
raw_delete viol_pending >/dev/null

# ④ working bloat
for i in $(seq 1 151); do seed "bloat_$i" working project thread "$PKEY" 1 "$TODAY" "bloat body $i" >/dev/null; done
python3 "$MEM" doctor >/tmp/doctor_bloat.out
grep -q '\[WARN\] working-bloat' /tmp/doctor_bloat.out \
  && ok "doctor: working 151건 > ceiling → working-bloat WARN" \
  || bad "doctor working-bloat 미검출: $(cat /tmp/doctor_bloat.out)"
raw_delete_like 'bloat_%' >/dev/null

# ⑥ durable soft-ceiling
for i in $(seq 1 81); do seed "dur_$i" durable project lesson "$PKEY" 1 "$TODAY" "durable body $i" >/dev/null; done
python3 "$MEM" doctor >/tmp/doctor_durable.out
grep -q '\[WARN\] durable-ceiling' /tmp/doctor_durable.out \
  && ok "doctor: durable 81건 > soft-ceiling(80) → durable-ceiling WARN" \
  || bad "doctor durable-ceiling 미검출: $(cat /tmp/doctor_durable.out)"
raw_delete_like 'dur_%' >/dev/null

# ⑦ graveyard parity — graveyard 에 있는 id 가 DB 에도 생존
seed viol_grave durable project note "$PKEY" 1 "$TODAY" "graveyard-parity body"
python3 -c "
import sys, json, datetime; sys.path.insert(0, '$ROOT/tools/memory')
import mem
with open(mem.GRAVEYARD, 'a', encoding='utf-8') as f:
    rec = {c: None for c in mem.RECORD_COLS}
    rec.update(id='viol_grave', tier='durable', scope='project', type='note', tags=[], links=[])
    rec['_deleted_at'] = 'x'; rec['_action'] = 'prune'; rec['_canonical'] = None
    f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + '\n')
"
python3 "$MEM" doctor >/tmp/doctor_grave.out
grep -q '\[WARN\] graveyard-parity' /tmp/doctor_grave.out \
  && ok "doctor: graveyard id 가 DB 에 생존 → graveyard-parity WARN" \
  || bad "doctor graveyard-parity 미검출: $(cat /tmp/doctor_grave.out)"
raw_delete viol_grave >/dev/null

# ⑧ dump freshness — DB updated 가 dump.jsonl 의 max(updated) 보다 최신
python3 "$MEM" export --target dump >/dev/null
FUTURE="$(python3 -c 'import datetime;print((datetime.date.today()+datetime.timedelta(days=1)).isoformat())')"
seed viol_dump durable project note "$PKEY" 1 "$TODAY" "dump-fresh body"
sql "UPDATE records SET updated='$FUTURE' WHERE id='viol_dump'" >/dev/null
python3 "$MEM" doctor >/tmp/doctor_dump.out
grep -q '\[WARN\] dump-freshness' /tmp/doctor_dump.out \
  && ok "doctor: DB 최신 updated 가 dump 보다 최신 → dump-freshness WARN" \
  || bad "doctor dump-freshness 미검출: $(cat /tmp/doctor_dump.out)"
raw_delete viol_dump >/dev/null

# ⑨ worker health — 활성 project 인데 저널에 distiller/curator 무소식
: > "$MEM_WRITE_EVENTS"
seed viol_worker working project thread "$PKEY" 1 "$TODAY" "worker-health body"
python3 "$MEM" doctor >/tmp/doctor_worker.out
grep -q '\[WARN\] worker-health' /tmp/doctor_worker.out \
  && ok "doctor: 활성 프로젝트 + 저널 무소식 → worker-health WARN" \
  || bad "doctor worker-health 미검출: $(cat /tmp/doctor_worker.out)"

echo
echo "RESULT: PASS=$PASS FAIL=$FAIL"
[ "$FAIL" = 0 ]
