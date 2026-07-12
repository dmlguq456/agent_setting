#!/usr/bin/env bash
# fleet.sh — 현재 터미널 런처 → fleet.py (agent-fleet-dashboard, PRD §3·§9).
#   · 기본: 현재(풀사이즈) 터미널에서 fleet.py 직접 실행 — tmux 안/밖 동일.
#   · --window: tmux 세션 안이면 풀사이즈 새 tmux 창(new-window)에서 실행; tmux 밖이면 직접 실행으로 대체.
#   · 스크롤은 키보드(j/k, PgUp/PgDn, g/G)가 기본 탐색 — 마우스 `+N` 클릭 토글은 opt-in
#     (`tmux set -g mouse on` 필요하며, 켜면 페인의 기본 클릭-선택/복사 기능을 대신 가져감).
#   설치: ~/.claude/tools/fleet/ 심링크 → `bash ~/.claude/tools/fleet/fleet.sh [옵션]`.
#   옵션은 그대로 fleet.py 로 전달(--interval/--section/--harness/--once/--json …). --window 만 여기서 소비.
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

# FLEET_PYTHON overrides interpreter discovery. On Windows the `python`/`python3`
# on PATH are the WindowsApps app-execution aliases (a pymanager stub that can
# crash with "Internal error 0x00000001"); the launcher points FLEET_PYTHON at a
# real python.exe to bypass it.
PY=${FLEET_PYTHON:-$(command -v python3 || command -v python || true)}
if [ -z "$PY" ]; then echo "fleet: python3 가 필요합니다." >&2; exit 1; fi
if [ ! -f "$FLEET_PY" ]; then echo "fleet: fleet.py 를 찾을 수 없습니다 ($FLEET_PY)." >&2; exit 1; fi

# --window 를 맨 먼저, 한 번만 걸러낸다 — 이후 모든 라우팅·run_direct·tmux cmd 빌드는
# 반드시 이 필터된 ARGS 만 사용한다(raw "$@" 금지). fleet.py 는 --window 를 모르므로
# 여기서 안 걸러내면 --window --once 가 argparse exit 2 로 죽는다.
want_window=0
ARGS=()
for a in "$@"; do
  if [ "$a" = "--window" ]; then
    want_window=1
  else
    ARGS+=("$a")
  fi
done

# --once/--json 은 런처가 필요 없음(스냅샷·파이프) → 직접 실행
direct=0
for a in ${ARGS[@]+"${ARGS[@]}"}; do case "$a" in --once|--json) direct=1 ;; esac; done

run_direct() { exec "$PY" "$FLEET_PY" "$@"; }

# (구 스크롤/마우스 안내 echo 는 제거 — curses 가 바로 덮어 읽을 수 없었고, 키 안내는
#  이제 footer 키 바가 상시 표시. 마우스 opt-in 상세는 위 헤더 주석 참조.)

if [ "$direct" = "1" ]; then
  run_direct ${ARGS[@]+"${ARGS[@]}"}
fi

if [ "$want_window" = "1" ]; then
  if [ -n "${TMUX:-}" ]; then
    cmd="$(printf '%q' "$PY") $(printf '%q' "$FLEET_PY")"
    for a in ${ARGS[@]+"${ARGS[@]}"}; do cmd="$cmd $(printf '%q' "$a")"; done
    tmux new-window "$cmd"
    exit 0
  fi
  echo "fleet: tmux 세션 밖이라 --window 를 무시하고 현재 터미널에서 직접 실행합니다." >&2
  run_direct ${ARGS[@]+"${ARGS[@]}"}
fi

# 기본: tmux 안/밖 상관없이 현재(풀사이즈) 터미널에서 직접 실행
run_direct ${ARGS[@]+"${ARGS[@]}"}
