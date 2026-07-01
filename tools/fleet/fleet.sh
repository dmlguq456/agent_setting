#!/usr/bin/env bash
# fleet.sh — tmux 세로 사이드 페인 런처 → fleet.py (agent-fleet-dashboard, PRD §3·§9).
#   · tmux 세션 안: 오른쪽에 좁은 세로 페인을 열고 그 안에서 fleet.py 실행.
#   · tmux 밖 또는 --no-tmux: 현재 터미널에서 fleet.py 직접 실행(안내 한 줄).
#   설치: ~/.claude/tools/fleet/ 심링크 → `bash ~/.claude/tools/fleet/fleet.sh [옵션]`.
#   옵션은 그대로 fleet.py 로 전달(--interval/--section/--harness/--once/--json …).
set -euo pipefail

# 심링크 경유해도 실제 스크립트 위치 해석
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR=$(cd -P "$(dirname "$SOURCE")" && pwd)
  SOURCE=$(readlink "$SOURCE")
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR=$(cd -P "$(dirname "$SOURCE")" && pwd)
FLEET_PY="$SCRIPT_DIR/fleet.py"

PY=$(command -v python3 || command -v python || true)
if [ -z "$PY" ]; then echo "fleet: python3 가 필요합니다." >&2; exit 1; fi
if [ ! -f "$FLEET_PY" ]; then echo "fleet: fleet.py 를 찾을 수 없습니다 ($FLEET_PY)." >&2; exit 1; fi

# --no-tmux 명시 여부
direct=0
for a in "$@"; do [ "$a" = "--no-tmux" ] && direct=1; done

# --once/--json 은 런처 페인이 필요 없음(스냅샷·파이프) → 직접 실행
for a in "$@"; do case "$a" in --once|--json) direct=1 ;; esac; done

run_direct() { exec "$PY" "$FLEET_PY" "$@"; }

if [ "$direct" = "1" ]; then
  run_direct "$@"
fi

if [ -n "${TMUX:-}" ]; then
  # 오른쪽에 좁은(≈48열) 세로 페인 — 48열이면 fleet 이 compact 1-line 행으로 렌더(사이드 페인에 적합).
  cmd="$(printf '%q' "$PY") $(printf '%q' "$FLEET_PY")"
  for a in "$@"; do cmd="$cmd $(printf '%q' "$a")"; done
  tmux split-window -h -l 48 "$cmd" 2>/dev/null \
    || tmux split-window -h -p 30 "$cmd" 2>/dev/null \
    || { echo "fleet: tmux split 실패 — 직접 실행합니다." >&2; run_direct "$@"; }
  exit 0
fi

echo "fleet: tmux 세션 밖입니다 — 사이드 페인 없이 현재 터미널에서 직접 실행합니다." >&2
echo "       (tmux 안에서 실행하면 세로 사이드 페인으로 뜹니다. 스냅샷은 --once, 파이프는 --json.)" >&2
run_direct "$@"
