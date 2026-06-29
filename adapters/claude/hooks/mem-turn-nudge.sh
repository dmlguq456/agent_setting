#!/usr/bin/env bash
# mem-turn-nudge — 결정론 turn-counter 자기회고 (DESIGN_PRINCIPLES §0.5, spec v5 Cluster B/B2).
#   Hermes nudge_interval(=10, turn_context.py:191-215) 등가물의 우리 hook 모델.
#   UserPromptSubmit 마다 세션별 카운터++; N턴 도달 시 메인 주입 0 — 대신 sibling dispatch(argument 모드)로
#   외부 detached distiller 분사(MEM_DISTILL_ENABLE 시; off=완전 no-op). 카운터는 리셋 (v7 외부화, spec §5.5.3 D-13).
#   memory.db write 감지(mtime 증가) 시 카운터 리셋 — Hermes turns_since_memory=0 등가 (write 하면 회고 불필요).
#   "언제 회고할지" 를 에이전트 판단이 아니라 결정론 카운터로 (§0.5). 등록: settings.json hooks.UserPromptSubmit.
set -euo pipefail
AGENT_HOME="${AGENT_HOME:-${CLAUDE_HOME:-$HOME/.claude}}"

# 재귀가드 (불변식, spec v7 §5.5): distiller 세션이면 turn-counter 도 분사하지 않음.
# distiller 의 `claude -p` UserPromptSubmit 가 재-dispatch 하는 것을 차단. stdin parse 전에 둔다.
# drain: 가드 발동 시 미소비 stdin 으로 인한 pipefail-유발 SIGPIPE/비0 exit 회피 (정상 경로는
# 아래 input=$(cat ...) 가 stdin 을 소비하므로 drain 불필요).
[ "${MEM_DISTILL:-}" = "1" ] && { cat >/dev/null 2>&1; exit 0; }

input=$(cat 2>/dev/null || true)
eval "$(printf '%s' "$input" | python3 -c '
import json, sys, shlex
try: d = json.load(sys.stdin)
except Exception: d = {}
print("EVENT="+shlex.quote(d.get("hook_event_name","") or ""))
print("SID="+shlex.quote(d.get("session_id","") or "default"))
' 2>/dev/null || true)"
EVENT="${EVENT:-}"; SID="${SID:-default}"
[ "$EVENT" = "UserPromptSubmit" ] || exit 0

N="${MEM_NUDGE_INTERVAL:-10}"
STORE="${MEM_STORE:-$AGENT_HOME/memory}"
DB="$STORE/memory.db"
STATE="$STORE/.turn-state-$SID"

counter=0
if [ -f "$STATE" ]; then counter=$(sed -n '1p' "$STATE" 2>/dev/null || echo 0); fi
case "$counter" in (*[!0-9]*|"") counter=0 ;; esac

# 카운터는 distiller 가 _분사될 때만_ 리셋된다(아래 fire). 카운터가 재는 건 "distiller 분사 이후 경과 턴"
# = 세션 delta 누적량이다. 메인의 명시적 mem add(사용자 "기억해") 같은 임의 memory write 는 fact 한 건을
# 저장할 뿐 세션을 distill 한 게 아니므로(공유 marker 도 안 움직임) 카운터에 영향을 주지 않는다.
# (메인이 저장한 fact 도 세션 transcript 에 남아 distiller 가 분사 시 함께 캡처한다.)
counter=$((counter + 1))

fire=0
if [ "$counter" -ge "$N" ]; then fire=1; counter=0; fi

mkdir -p "$STORE" 2>/dev/null || true
printf '%s\n' "$counter" > "$STATE" 2>/dev/null || true

# 오래된 세션 state GC (3일+ 비활성 — workflow-guard .untracked GC 패턴 동형, 2026-06-16). 무해 무시.
find "$STORE" -maxdepth 1 -name '.turn-state-*' -mmin +4320 -delete 2>/dev/null || true

# fire 액션 (D6 self-location): N턴 도달 시 메인 컨텍스트 주입 0 — 대신 sibling dispatch 를
# argument 모드로 호출해 외부 detached distiller 분사. self-location 으로 sibling 을 찾으므로
# worktree turn-nudge→worktree dispatch / live→live 가 자연 해소 (하드코딩 $HOME/.claude/hooks/ X).
# dispatch 자체 opt-in 게이트가 ENABLE off 시 no-op 으로 만듦 (게이트 단일 자리). |출력 redirect +
# || true 로 fail-safe exit 0 보장 — 메인 컨텍스트 주입 0.
# default-SID skip (QA-②): SID 비었거나 "default"(broken-stdin) 면 dispatch 호출 skip — 여러
# SID-less 세션이 한 marker/lock(.distill-state-default 등)을 공유 오염하는 surface 차단. fire
# 카운터 리셋·state persist 는 위에서 이미 진행됐으니 그대로 (skip 은 dispatch 호출만).
if [ "$fire" = "1" ] && [ -n "$SID" ] && [ "$SID" != "default" ]; then
  HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
  bash "$HOOK_DIR/mem-distill-dispatch.sh" distill "$SID" "$PWD" </dev/null >/dev/null 2>&1 || true
fi
exit 0
