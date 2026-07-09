#!/bin/sh
# PreToolUse(Edit/Write): adapters/** 편집 전 이번 세션의 core/*.md 실제 Read 마커를 요구한다.
# S6(2026-07-09): full-copy → wrapper. 짝인 core-read-marker.sh 는 wrapper(agent-home.sh→repo root)
#   로 마커를 repo `.core-grounding` 에 쓰는데, 이 guard 가 full-copy 라 SCRIPT_DIR/.. (=~/.claude)
#   의 빈 `.core-grounding` 를 읽어 마커를 못 찾고 항상 deny 하던 회귀를 정합. repo-root portable
#   guard 를 exec 해 그쪽 SCRIPT_DIR/.. 로 AGENT_HOME=repo root 를 자기해석 → 마커 위치 일치
#   (core-read-marker.sh wrapper 와 동형). stdin-JSON / --file CLI 모드는 portable 쪽이 그대로 처리.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
AGENT_HOME="${AGENT_HOME:-$("$SCRIPT_DIR/../utilities/agent-home.sh")}"
exec "$AGENT_HOME/hooks/core-first-guard.sh" "$@"
