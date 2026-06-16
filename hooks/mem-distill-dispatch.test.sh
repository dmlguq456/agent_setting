#!/usr/bin/env bash
# Standalone test for mem-distill-dispatch.sh (spec v8 §5.5 D-12/D-13/D-14).
# Fully isolated via MEM_STORE + MEM_PROJECTS temp dirs — never touches real ~/.claude/memory.
# Real `claude` spawn is ALWAYS avoided via a PATH-injected `claude` stub (sentinel / argv-capture).
# Covers Phase-3 Verification ②③④⑥ from plan: 2026-06-16_distiller-v7-hardening/plan/plan.md
#
# ⚠️ ⑤ (live D-14 no-tools acceptance probe) is OUT OF SCOPE here (this file = stubs only, never real claude).
#    ⑤ merge-gate is now the no-tools acceptance (separate live script, `--disallowedTools` probe) that
#    verifies date>>file is blocked in the REAL operating settings.json env (blanket Bash allow + skipAutoPermissionPrompt
#    + skipDangerousModePermissionPrompt + defaultMode:auto all live) — disallow>allow precedence proved in-env.
#    allowlist probe approach (v7) is deprecated — v7 --allowedTools was empirically inert.
#    Stub tests (a)/(b) below cover JSON-lines parsing and injection-in-body at unit level;
#    live acceptance gate (Verification ①) is out of scope here (stubs only, never real claude).
#    DEFERRED (before flipping MEM_DISTILL_ENABLE=1 — D5 hard gate): R1 env-inheritance, ghost-marker,
#    R7 (mem sync double-absorb / herdr state pollution) one-time live checks; plus optional clean-deny
#    improvement. HARD RULE: ENABLE=1 FORBIDDEN until the deferred live checks pass.
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
# 단일 EXIT trap + 누적 cleanup 배열: bash 의 trap EXIT 는 append 아니라 replace 이므로,
# 신규 테스트(a/M3/M4/b)는 새 trap 을 선언하는 대신 CLEANUP 에 경로를 append 한다 (누수 방지).
CLEANUP=("$STORE" "$PROJ" "$STUBBIN" "$STUBCAP")
trap 'rm -rf "${CLEANUP[@]}"; rm -f "${SENTINEL_B:-}"' EXIT
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
# marker: v8 에서 dispatch 의 detached child 가 --advance 를 실행한다. 테스트의 수동 --advance 는
# child 와 idempotent (같은 sid → 같은 last uuid), stub-less ② 경로의 marker materialize 결정성을
# 위해 유지한다. 경로 규칙이 STORE 기반으로 materialize 되는지만 직접 확인(명시적).
python3 "$MEM" distill "$SID2" --advance >/dev/null 2>&1
[ -f "$STORE/.distill-state-$SID2" ] \
  && ok "②a stdin-JSON: marker path = \$STORE/.distill-state-$SID2 materialize (child advances; manual --advance idempotent)" \
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
# ⑥ argv capture — 모델 sonnet + no --dangerously-skip-permissions + disallowedTools
# ============================================================
echo "== ⑥ argv capture — --model claude-sonnet-4-6 · no --dangerously-skip-permissions · --disallowedTools =="
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
# v8: --disallowedTools 존재 단언
printf '%s\n' "$argv" | grep -qx -- "--disallowedTools" \
  && ok "⑥ argv: --disallowedTools 포함" \
  || bad "⑥ argv: --disallowedTools 부재 (v8 보안 미적용): [$argv]"
# --disallowedTools 다음 줄(space-joined 단일 인자)에 각 도구 포함 — S5 (list truncation 회귀 anchor)
# 값은 multi-token 단일 인자라 -x 아닌 substring 매치 (grep -q)
disallow_val="$(printf '%s\n' "$argv" | grep -A1 -x -- "--disallowedTools" | tail -n1 || true)"
printf '%s' "$disallow_val" | grep -q "Bash" \
  && ok "⑥ disallow 값: Bash 포함" \
  || bad "⑥ disallow 값: Bash 부재: [$disallow_val]"
printf '%s' "$disallow_val" | grep -q "Read" \
  && ok "⑥ disallow 값: Read 포함" \
  || bad "⑥ disallow 값: Read 부재: [$disallow_val]"
printf '%s' "$disallow_val" | grep -q "Write" \
  && ok "⑥ disallow 값: Write 포함" \
  || bad "⑥ disallow 값: Write 부재: [$disallow_val]"
printf '%s' "$disallow_val" | grep -q "Edit" \
  && ok "⑥ disallow 값: Edit 포함" \
  || bad "⑥ disallow 값: Edit 부재: [$disallow_val]"
printf '%s' "$disallow_val" | grep -q "Agent" \
  && ok "⑥ disallow 값: Agent 포함" \
  || bad "⑥ disallow 값: Agent 부재: [$disallow_val]"
rmdir "$STORE/.distill-lock-$SID6" 2>/dev/null || true

# ============================================================
# test (a) — JSON-lines 파싱 (stub): 유효 2줄 + malformed 5줄 → row count == 2
# ============================================================
echo "== test(a): JSON-lines 파싱 — 유효 2줄 + malformed 5줄 → isolated DB row count == 2 =="
SIDa="dispatchsida"
STOREa="$(mktemp -d)"; PROJa="$(mktemp -d)"
STUBa="$(mktemp -d)"
CLEANUP+=("$STOREa" "$PROJa" "$STUBa")

# fixture (isolated)
enc_a="$PROJa/-home-fake-$SIDa"; mkdir -p "$enc_a"
cat > "$enc_a/$SIDa.jsonl" <<JSONL
{"type":"user","message":{"role":"user","content":"test (a) prompt"},"uuid":"${SIDa}u1","timestamp":"t1","isSidechain":false}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"test (a) reply text"}]},"uuid":"${SIDa}a1","timestamp":"t2","isSidechain":false}
JSONL

# stub 이 PROMPT argv 무관하게 고정 JSON-lines 출력 (printf/heredoc — 셸 확장 없이 literal)
# 유효 2줄: body ≥15자, tier/type/body 모두 있음
# malformed 5줄: (1) non-JSON garbage, (2) body 누락, (3) type 누락, (4) bad tier, (5) body 2001자
LONG_BODY="$(python3 -c "print('x' * 2001)")"
cat > "$STUBa/claude" <<STUBEOF
#!/bin/sh
printf '%s\n' '{"tier":"durable","type":"lesson","body":"this is a valid durable lesson record"}' \
              '{"tier":"working","type":"thread","body":"this is a valid working thread item"}' \
              'not-json-garbage-line' \
              '{"tier":"durable","type":"lesson"}' \
              '{"tier":"durable","body":"missing type field here okay"}' \
              '{"tier":"baz","type":"lesson","body":"bad tier value test record"}' \
              "{\"tier\":\"durable\",\"type\":\"lesson\",\"body\":\"$LONG_BODY\"}"
STUBEOF
chmod +x "$STUBa/claude"

MEM_STORE="$STOREa" MEM_PROJECTS="$PROJa" MEM_DISTILL_ENABLE=1 PATH="$STUBa:$PATH" \
  bash "$DISPATCH" distill "$SIDa" "/tmp"

# 폴링: detached child 가 mem add 완료할 때까지 row-count ≥ 1 또는 최대 5초 대기 (M5)
# 유효 2줄 → row count == 2 기대, 하지만 quality_ok(≥15자) 이미 충족
for _ in $(seq 1 50); do
  cnt_a="$(MEM_STORE="$STOREa" python3 "$MEM" stats 2>/dev/null | grep -E '^\s+total:' | awk '{print $2}')"
  [ "${cnt_a:-0}" -ge 1 ] 2>/dev/null && break
  sleep 0.1
done
cnt_a="$(MEM_STORE="$STOREa" python3 "$MEM" stats 2>/dev/null | grep -E '^\s+total:' | awk '{print $2}')"
[ "${cnt_a:-0}" = "2" ] \
  && ok "test(a): row count == 2 (유효 2줄만 저장, malformed 5줄 skip)" \
  || bad "test(a): row count = ${cnt_a:-0}, 기대 2 (유효 2줄 저장 실패 or malformed 포함)"
rmdir "$STOREa/.distill-lock-$SIDa" 2>/dev/null || true

# ============================================================
# test (M3) — code-fence 출력 → 레코드 정상 파싱
# ============================================================
echo "== test(M3): code-fence 감싼 출력 → 내부 유효 줄만 레코드 생성 =="
SIDm3="dispatchsidm3"
STOREm3="$(mktemp -d)"; PROJm3="$(mktemp -d)"
STUBm3="$(mktemp -d)"
CLEANUP+=("$STOREm3" "$PROJm3" "$STUBm3")

enc_m3="$PROJm3/-home-fake-$SIDm3"; mkdir -p "$enc_m3"
cat > "$enc_m3/$SIDm3.jsonl" <<JSONL
{"type":"user","message":{"role":"user","content":"test M3 prompt"},"uuid":"${SIDm3}u1","timestamp":"t1","isSidechain":false}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"test M3 reply content"}]},"uuid":"${SIDm3}a1","timestamp":"t2","isSidechain":false}
JSONL

# stub: ```json 펜스로 감싼 유효 JSON 2줄 출력 (첫줄 ```json, 닫는 ```)
cat > "$STUBm3/claude" <<'STUBEOF'
#!/bin/sh
printf '%s\n' '```json' \
              '{"tier":"durable","type":"lesson","body":"fenced valid durable lesson record"}' \
              '{"tier":"working","type":"thread","body":"fenced valid working thread record"}' \
              '```'
STUBEOF
chmod +x "$STUBm3/claude"

MEM_STORE="$STOREm3" MEM_PROJECTS="$PROJm3" MEM_DISTILL_ENABLE=1 PATH="$STUBm3:$PATH" \
  bash "$DISPATCH" distill "$SIDm3" "/tmp"

# 폴링: row count ≥ 1 대기 (내부 유효 2줄 기대)
for _ in $(seq 1 50); do
  cnt_m3="$(MEM_STORE="$STOREm3" python3 "$MEM" stats 2>/dev/null | grep -E '^\s+total:' | awk '{print $2}')"
  [ "${cnt_m3:-0}" -ge 1 ] 2>/dev/null && break
  sleep 0.1
done
cnt_m3="$(MEM_STORE="$STOREm3" python3 "$MEM" stats 2>/dev/null | grep -E '^\s+total:' | awk '{print $2}')"
[ "${cnt_m3:-0}" = "2" ] \
  && ok "test(M3): code-fence 감싼 출력 → 내부 유효 2줄 레코드 생성 (fence skip 정상)" \
  || bad "test(M3): row count = ${cnt_m3:-0}, 기대 2 (fence skip 실패 또는 bare json.loads 회귀)"
rmdir "$STOREm3/.distill-lock-$SIDm3" 2>/dev/null || true

# ============================================================
# test (M4) — 빈 출력 → 0 레코드 + marker 값 전진
# ============================================================
echo "== test(M4): 빈 stdout → 0 레코드, marker = fixture 마지막 uuid =="
SIDm4="dispatchsidm4"
STOREm4="$(mktemp -d)"; PROJm4="$(mktemp -d)"
STUBm4="$(mktemp -d)"
CLEANUP+=("$STOREm4" "$PROJm4" "$STUBm4")

enc_m4="$PROJm4/-home-fake-$SIDm4"; mkdir -p "$enc_m4"
# mkfix 가 쓰는 마지막 uuid = ${SIDm4}a1
cat > "$enc_m4/$SIDm4.jsonl" <<JSONL
{"type":"user","message":{"role":"user","content":"test M4 prompt"},"uuid":"${SIDm4}u1","timestamp":"t1","isSidechain":false}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"test M4 reply"}]},"uuid":"${SIDm4}a1","timestamp":"t2","isSidechain":false}
JSONL
LAST_UUID_M4="${SIDm4}a1"

# stub: 빈 stdout (0줄)
printf '#!/bin/sh\n# empty output\n' > "$STUBm4/claude"
chmod +x "$STUBm4/claude"

MEM_STORE="$STOREm4" MEM_PROJECTS="$PROJm4" MEM_DISTILL_ENABLE=1 PATH="$STUBm4:$PATH" \
  bash "$DISPATCH" distill "$SIDm4" "/tmp"

# 폴링: marker state file 출현 또는 lock 소멸까지 bounded wait (최대 5초)
for _ in $(seq 1 50); do
  if [ -f "$STOREm4/.distill-state-$SIDm4" ]; then break; fi
  if [ ! -d "$STOREm4/.distill-lock-$SIDm4" ]; then
    # lock 이 사라졌으면 child 완료 — 한 번 더 대기 후 break
    sleep 0.2; break
  fi
  sleep 0.1
done

cnt_m4="$(MEM_STORE="$STOREm4" python3 "$MEM" stats 2>/dev/null | grep -E '^\s+total:' | awk '{print $2}')"
[ "${cnt_m4:-0}" = "0" ] \
  && ok "test(M4): 빈 출력 → row count == 0" \
  || bad "test(M4): row count = ${cnt_m4:-0}, 기대 0"

# marker 값 단언: state file 이 fixture 의 마지막 uuid 와 일치해야 함 (v8 신규 계약)
marker_val="$(cat "$STOREm4/.distill-state-$SIDm4" 2>/dev/null || true)"
[ "$marker_val" = "$LAST_UUID_M4" ] \
  && ok "test(M4): marker 값 = $LAST_UUID_M4 (빈 출력에도 advance 완료)" \
  || bad "test(M4): marker 값 = '${marker_val}', 기대 '$LAST_UUID_M4' (advance 미실행 또는 값 불일치)"
rmdir "$STOREm4/.distill-lock-$SIDm4" 2>/dev/null || true

# ============================================================
# test (b) — injection-in-body: body 에 셸 주입 payload → 레코드 저장, sentinel 미생성
# ============================================================
echo "== test(b): injection-in-body → record stored (row-count), sentinel NOT created (D-14) =="
SIDb="dispatchsidb"
STOREb="$(mktemp -d)"; PROJb="$(mktemp -d)"
STUBb="$(mktemp -d)"
SENTINEL_B="/tmp/cc-v8-inject-$$-$RANDOM"
CLEANUP+=("$STOREb" "$PROJb" "$STUBb")  # SENTINEL_B 는 위 단일 trap 의 rm -f 가 커버

enc_b="$PROJb/-home-fake-$SIDb"; mkdir -p "$enc_b"
cat > "$enc_b/$SIDb.jsonl" <<JSONL
{"type":"user","message":{"role":"user","content":"test (b) injection prompt"},"uuid":"${SIDb}u1","timestamp":"t1","isSidechain":false}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"test (b) injection reply"}]},"uuid":"${SIDb}a1","timestamp":"t2","isSidechain":false}
JSONL

# stub: body 에 셸 주입 payload 포함 — body ≥15자(quality_ok 통과), IF body 가 sh -c/eval 됐다면 sentinel 생성
# SENTINEL_B 는 아직 미생성 상태 (사전 생성 안 함).
# python -c 로 JSON 직렬화: 셸 이스케이프 중첩 없이 body 안 특수문자를 안전하게 인코딩.
cat > "$STUBb/claude" <<STUBEOF
#!/bin/sh
python3 -c "
import json
payload = {'tier': 'durable', 'type': 'lesson',
           'body': 'normal text \"; touch $SENTINEL_B ; echo \"'}
print(json.dumps(payload))
"
STUBEOF
chmod +x "$STUBb/claude"

MEM_STORE="$STOREb" MEM_PROJECTS="$PROJb" MEM_DISTILL_ENABLE=1 PATH="$STUBb:$PATH" \
  bash "$DISPATCH" distill "$SIDb" "/tmp"

# 폴링: row count ≥ 1 (레코드 저장 완료 대기) 또는 lock 소멸 대기 — M5 row-count 폴링
for _ in $(seq 1 50); do
  cnt_b="$(MEM_STORE="$STOREb" python3 "$MEM" stats 2>/dev/null | grep -E '^\s+total:' | awk '{print $2}')"
  [ "${cnt_b:-0}" -ge 1 ] 2>/dev/null && break
  # lock 소멸이면 child 완료 (0-record 경로 포함)
  if [ ! -d "$STOREb/.distill-lock-$SIDb" ]; then sleep 0.2; break; fi
  sleep 0.1
done

cnt_b="$(MEM_STORE="$STOREb" python3 "$MEM" stats 2>/dev/null | grep -E '^\s+total:' | awk '{print $2}')"
# S6 단언 (1): 레코드 저장됨 — DB row-count == 1 (INJECTION_PAT 플래그 여부 무관, row-count 가 stable signal)
[ "${cnt_b:-0}" = "1" ] \
  && ok "test(b): injection body → 레코드 저장됨 (row count == 1, body-token match 아님)" \
  || bad "test(b): row count = ${cnt_b:-0}, 기대 1 (injection body 저장 실패)"
# S6 단언 (2): sentinel 미생성 — body 가 sh -c/eval 된 적 없음 (D-14 핵심 단언)
[ ! -f "$SENTINEL_B" ] \
  && ok "test(b): sentinel 미생성 — injection body 셸 미실행 (D-14 단위 단언 PASS)" \
  || bad "test(b): sentinel 파일 존재! body 가 셸 실행됨 (D-14 위반 — CRITICAL)"
rm -f "$SENTINEL_B" 2>/dev/null || true
rmdir "$STOREb/.distill-lock-$SIDb" 2>/dev/null || true

echo
echo "RESULT: PASS=$PASS FAIL=$FAIL"
[ "$FAIL" = "0" ]
