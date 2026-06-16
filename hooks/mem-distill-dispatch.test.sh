#!/usr/bin/env bash
# Standalone test for mem-distill-dispatch.sh (spec v7 §5.5 D-12/D-13/D-14).
# Fully isolated via MEM_STORE + MEM_PROJECTS temp dirs — never touches real ~/.claude/memory.
# Real `claude` spawn is ALWAYS avoided via a PATH-injected `claude` stub (sentinel / argv-capture).
# Covers Phase-3 Verification ②③④⑥ from plan: 2026-06-16_distiller-v7-hardening/plan/plan.md
#
# ⚠️ ⑤ (live D-14 permission probe) is OUT OF SCOPE here (this file = stubs only, never real claude).
#    ⑤ WAS run live on 2026-06-16 (claude 2.1.178 / sonnet-4-6) — see test_logs/perm_probe_5*.log:
#        - python3 <mem.py> ...   → ALLOWED ✅ (mem.py runs, record written)   [allowedTools pattern OK]
#        - touch / non-mem.py     → NOT executed ✅ under default mode (prompt→headless hang→no run)
#                                    ⇒ arbitrary bash physically blocked = D-14 goal MET.
#        - model id sonnet-4-6    → valid ✅
#        - ⚠️ --permission-mode dontAsk / bypassPermissions = allow-all (touch RAN) → FORBIDDEN.
#          Keep default (unset). The pattern 'Bash(python3 *mem.py*:*)' is the merge-gate, CONFIRMED.
#    DEFERRED (before flipping MEM_DISTILL_ENABLE=1 — D5 hard gate): R1 env-inheritance, ghost-marker,
#    R7 (mem sync double-absorb / herdr state pollution) one-time live checks; plus optional clean-deny
#    improvement (non-mem.py currently hangs→zombie until stale-lock GC 60min; acceptEdits/auto modes
#    unverified, or wrap claude in `timeout N`). HARD RULE: ENABLE=1 FORBIDDEN until the deferred
#    live checks pass. D-14 security (arbitrary-exec block) already holds under default; the deferred
#    items are robustness/efficiency, not the security gate.
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DISPATCH="$ROOT/hooks/mem-distill-dispatch.sh"
TURNNUDGE="$ROOT/hooks/mem-turn-nudge.sh"
MEM="$ROOT/tools/memory/mem.py"
[ -f "$DISPATCH" ] || { echo "FAIL: dispatch hook not found at $DISPATCH"; exit 1; }
[ -f "$TURNNUDGE" ] || { echo "FAIL: turn-nudge hook not found at $TURNNUDGE"; exit 1; }

PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); printf '  ✅ %s\n' "$1"; }
bad() { FAIL=$((FAIL+1)); printf '  ❌ %s\n' "$1"; }

# ---- isolated store/projects ----
STORE="$(mktemp -d)"; PROJ="$(mktemp -d)"
STUBBIN="$(mktemp -d)"      # sentinel stub (touch CLAUDE_CALLED iff claude invoked)
STUBCAP="$(mktemp -d)"      # argv-capture stub (echoes argv to ARGV file)
trap 'rm -rf "$STORE" "$PROJ" "$STUBBIN" "$STUBCAP"' EXIT
export MEM_STORE="$STORE" MEM_PROJECTS="$PROJ"

# RP-M4 decision: stubs kept INLINE (not extracted to hooks/test-helpers/dispatch-stub.sh).
# Rationale — each stub is 2 lines; the two test files' isolation setups differ (this file uses
# per-stub temp dirs + sentinel/argv variants, distill.test.sh shares one TMPSTUB), so a shared
# source would add coupling for negligible LOC savings. Extraction cost > benefit here.

# sentinel stub: marks invocation (used by ②③④ to detect spawn/no-spawn)
printf '#!/bin/sh\ntouch "%s/CLAUDE_CALLED"\n' "$STUBBIN" > "$STUBBIN/claude"
chmod +x "$STUBBIN/claude"

# argv-capture stub: appends its full argv (one per line) to ARGV (used by ⑥)
printf '#!/bin/sh\nfor a in "$@"; do printf "%%s\\n" "$a"; done >> "%s/ARGV"\n' "$STUBCAP" > "$STUBCAP/claude"
chmod +x "$STUBCAP/claude"

# ---- fixture jsonl helper: writes a 2-msg session so delta is non-empty (marker unset → full yield) ----
mkfix() {  # $1=sid
  local sid="$1" enc
  enc="$PROJ/-home-fake-$sid"; mkdir -p "$enc"
  cat > "$enc/$sid.jsonl" <<JSONL
{"type":"user","message":{"role":"user","content":"dispatch test prompt $sid"},"uuid":"${sid}u1","timestamp":"t1","isSidechain":false}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"dispatch test reply $sid"}]},"uuid":"${sid}a1","timestamp":"t2","isSidechain":false}
JSONL
}

# ============================================================
# ② 양쪽 호출모드 STORE 기반 marker/lock materialize (RP-M3 — path materialization, not narrative)
#    stdin-JSON(SessionEnd) 과 argument(turn-counter) 가 같은 STORE-resolve 규칙을 쓰는지 단언.
#    두 호출을 *별도 sid* 로 격리 — ②a 의 detached child trap-rmdir 이 ②b 의 같은-sid lock 을
#    늦게 지우는 race 를 차단(A-neg sentinel 격리와 동형). 규칙이 같으므로 같은 sid 면 같은 경로(자명).
# ============================================================
echo "== ② 양쪽 호출모드(stdin-JSON + argument) → STORE 기반 marker/lock materialize (sid 격리) =="
SID2="dispatchsid2"
mkfix "$SID2"
# 두 호출 다 delta non-empty 전제 확인
delta2="$(python3 "$MEM" distill "$SID2")"
[ -n "${delta2//[[:space:]]/}" ] && ok "②: non-empty delta (양 모드 분사 전제)" || bad "②: delta empty — fixture 이상"

# (a) stdin-JSON 모드 (SessionEnd 경로)
echo "{\"session_id\":\"$SID2\",\"cwd\":\"/tmp\"}" \
  | MEM_DISTILL_ENABLE=1 PATH="$STUBBIN:$PATH" bash "$DISPATCH"
[ -d "$STORE/.distill-lock-$SID2" ] \
  && ok "②a stdin-JSON: lock dir = \$STORE/.distill-lock-$SID2 (MEM_STORE 기반 materialize)" \
  || bad "②a stdin-JSON: lock dir 미생성"
# marker: dispatch 는 marker 를 advance 하지 않음(detached child 분사 책임) — 경로 규칙이 STORE
# 기반으로 materialize 되는지만 직접 확인(mem.py --advance 로 생성 → STORE 하위 존재). fallback 없이
# 명시적: lock-dir 동기 단언이 이미 "dispatch 도달 + spawn 진입"을 증명하므로 marker 는 경로 규칙만.
python3 "$MEM" distill "$SID2" --advance >/dev/null 2>&1
[ -f "$STORE/.distill-state-$SID2" ] \
  && ok "②a stdin-JSON: marker path = \$STORE/.distill-state-$SID2 materialize (advance via mem.py; dispatch 아님)" \
  || bad "②a stdin-JSON: marker 경로 불일치"
# ②a 정리 (lock — child trap 과 무관하게 동기 제거)
rmdir "$STORE/.distill-lock-$SID2" 2>/dev/null || true

# (b) argument 모드 (turn-counter 경로) — 별도 sid 로 격리(②a detached child 의 late trap-rmdir 이
#     이 lock 을 못 건드리게, race-free). stdin 모드와 동일 STORE-resolve 규칙을 쓰는지 단언.
SID2B="dispatchsid2b"
mkfix "$SID2B"
delta2b="$(python3 "$MEM" distill "$SID2B")"
[ -n "${delta2b//[[:space:]]/}" ] && ok "②: argument 모드 delta non-empty(분사 전제)" || bad "②: argument fixture delta empty"
MEM_DISTILL_ENABLE=1 PATH="$STUBBIN:$PATH" bash "$DISPATCH" distill "$SID2B" "/tmp"
[ -d "$STORE/.distill-lock-$SID2B" ] \
  && ok "②b argument: lock dir = \$STORE/.distill-lock-$SID2B (stdin 모드와 동일 STORE-resolve 규칙)" \
  || bad "②b argument: lock dir 미생성 — argument 모드가 stdin 모드와 STORE-resolve 분기"
rmdir "$STORE/.distill-lock-$SID2B" 2>/dev/null || true

# ============================================================
# ③ lock 동시 1개 (pre-existing lock ⇒ skip; absent ⇒ spawn-path)
# ============================================================
echo "== ③ lock 동시 1개 — 사전 lock 존재 시 skip, 제거 후 재호출 시 spawn 경로 진입 =="
SID3="dispatchsid3"
mkfix "$SID3"
# 도는 distiller 모사: lock 사전 생성
mkdir -p "$STORE/.distill-lock-$SID3"
rm -f "$STUBBIN/CLAUDE_CALLED"
rc3=0
echo "{\"session_id\":\"$SID3\",\"cwd\":\"/tmp\"}" \
  | MEM_DISTILL_ENABLE=1 PATH="$STUBBIN:$PATH" bash "$DISPATCH" || rc3=$?
[ "$rc3" = "0" ] && ok "③ 사전 lock 존재 → exit 0 (skip)" || bad "③ 사전 lock skip 시 exit code: $rc3"
[ ! -e "$STUBBIN/CLAUDE_CALLED" ] \
  && ok "③ 사전 lock 존재 → sentinel ABSENT (분사 skip, 동시 1개)" \
  || bad "③ 사전 lock 임에도 claude 분사됨 (lock skip 실패)"
# lock 제거 후 재호출 → spawn 경로 진입 (동기 lock 재생성으로 단언, race-free)
rmdir "$STORE/.distill-lock-$SID3" 2>/dev/null || true
MEM_DISTILL_ENABLE=1 PATH="$STUBBIN:$PATH" bash "$DISPATCH" distill "$SID3" "/tmp"
[ -d "$STORE/.distill-lock-$SID3" ] \
  && ok "③ lock 제거 후 재호출 → spawn 경로 진입 (lock dir 재생성)" \
  || bad "③ lock 제거 후 재호출 — spawn 경로 미진입 (lock dir 부재)"
rmdir "$STORE/.distill-lock-$SID3" 2>/dev/null || true

# ============================================================
# ④ 재귀가드 양 hook 양 모드 (MEM_DISTILL=1 ⇒ 즉시 exit 0, spawn 0)
# ============================================================
echo "== ④ 재귀가드 — MEM_DISTILL=1 시 dispatch(양 모드)·turn-nudge 즉시 exit 0, sentinel ABSENT =="
SID4="dispatchsid4"
mkfix "$SID4"

# dispatch stdin-JSON 모드
rm -f "$STUBBIN/CLAUDE_CALLED"
rc4a=0
echo "{\"session_id\":\"$SID4\",\"cwd\":\"/tmp\"}" \
  | MEM_DISTILL=1 MEM_DISTILL_ENABLE=1 PATH="$STUBBIN:$PATH" bash "$DISPATCH" || rc4a=$?
[ "$rc4a" = "0" ] && ok "④ dispatch stdin-JSON: 재귀가드 exit 0" || bad "④ dispatch stdin-JSON exit: $rc4a"
[ ! -e "$STUBBIN/CLAUDE_CALLED" ] \
  && ok "④ dispatch stdin-JSON: MEM_DISTILL=1 → sentinel ABSENT" \
  || bad "④ dispatch stdin-JSON: 재귀가드 실패 (sentinel PRESENT)"

# dispatch argument 모드
rm -f "$STUBBIN/CLAUDE_CALLED"
rc4b=0
MEM_DISTILL=1 MEM_DISTILL_ENABLE=1 PATH="$STUBBIN:$PATH" bash "$DISPATCH" distill "$SID4" "/tmp" || rc4b=$?
[ "$rc4b" = "0" ] && ok "④ dispatch argument: 재귀가드 exit 0" || bad "④ dispatch argument exit: $rc4b"
[ ! -e "$STUBBIN/CLAUDE_CALLED" ] \
  && ok "④ dispatch argument: MEM_DISTILL=1 → sentinel ABSENT" \
  || bad "④ dispatch argument: 재귀가드 실패 (sentinel PRESENT)"

# turn-nudge (stdin 파이프 주입 — guard-path drain + exit0 under pipefail 확인, Step 2.1 RP-M5)
rm -f "$STUBBIN/CLAUDE_CALLED"
rc4c=0
printf '{"hook_event_name":"UserPromptSubmit","session_id":"%s","prompt":"x"}' "$SID4" \
  | MEM_DISTILL=1 MEM_DISTILL_ENABLE=1 MEM_STORE="$STORE" MEM_NUDGE_INTERVAL=1 \
    PATH="$STUBBIN:$PATH" bash "$TURNNUDGE" || rc4c=$?
[ "$rc4c" = "0" ] \
  && ok "④ turn-nudge: MEM_DISTILL=1 + stdin 파이프 → drain + exit 0 (pipefail 무탈)" \
  || bad "④ turn-nudge: 재귀가드 exit code under pipefail: $rc4c"
[ ! -e "$STUBBIN/CLAUDE_CALLED" ] \
  && ok "④ turn-nudge: MEM_DISTILL=1 → sentinel ABSENT (재분사 차단)" \
  || bad "④ turn-nudge: 재귀가드 실패 (sentinel PRESENT)"

# ============================================================
# ⑥ argv capture — 모델 sonnet + no --dangerously-skip-permissions + mem.py-only allowedTools
# ============================================================
echo "== ⑥ argv capture — --model claude-sonnet-4-6 · no --dangerously-skip-permissions · mem.py-only allowedTools =="
SID6="dispatchsid6"
mkfix "$SID6"
rm -f "$STUBCAP/ARGV"
MEM_DISTILL_ENABLE=1 PATH="$STUBCAP:$PATH" bash "$DISPATCH" distill "$SID6" "/tmp"
# detached child(setsid)의 argv write 가 도달할 시간 — 폴링 (최대 ~5s, CI/부하 환경 마진)
for _ in $(seq 1 50); do [ -s "$STUBCAP/ARGV" ] && break; sleep 0.1; done
argv="$(cat "$STUBCAP/ARGV" 2>/dev/null || true)"
printf '%s\n' "$argv" | grep -qx -- "--model" && printf '%s\n' "$argv" | grep -qx -- "claude-sonnet-4-6" \
  && ok "⑥ argv: --model claude-sonnet-4-6 포함" \
  || bad "⑥ argv: --model claude-sonnet-4-6 부재: [$argv]"
printf '%s\n' "$argv" | grep -qx -- "--dangerously-skip-permissions" \
  && bad "⑥ argv: --dangerously-skip-permissions 가 존재함 (D-14 위반)" \
  || ok "⑥ argv: --dangerously-skip-permissions 부재 (D-14)"
# 패턴값은 glob/괄호 메타문자 포함 → -F(fixed-string)로 정확 매치 (basic-regex 해석 회피)
printf '%s\n' "$argv" | grep -qx -- "--allowedTools" && printf '%s\n' "$argv" | grep -Fxq -- "Bash(python3 *mem.py*:*)" \
  && ok "⑥ argv: --allowedTools 'Bash(python3 *mem.py*:*)' 포함 (mem.py-only)" \
  || bad "⑥ argv: mem.py-only allowedTools 패턴 부재: [$argv]"
rmdir "$STORE/.distill-lock-$SID6" 2>/dev/null || true

echo
echo "RESULT: PASS=$PASS FAIL=$FAIL"
[ "$FAIL" = "0" ]
