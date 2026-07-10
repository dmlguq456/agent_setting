#!/usr/bin/env bash
# recall — 통합 기억 회상 (thin wrapper → mem recall). 2026-06-15 전환:
#   기존 파일-스캔 방식을 버리고 통합 store(durable+working) + profile tier records + (--sessions) raw 대화를 검색.
#   사용: recall.sh "<query>" [--tier working|durable] [--scope project|global]
#         [--all] [--sessions] [--full] [--limit 1..100]
#         내부 auto probe: recall.sh "<prompt>" --auto [--json] [--no-touch]
#   조회는 handoff 비소비. 명시 recall은 last_accessed만 갱신하고 --no-touch는 access도 갱신하지 않는다.
#   상세 = tools/memory/README.md · MEMORY §7.4.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
AGENT_HOME="${AGENT_HOME:-$("$SCRIPT_DIR/../../utilities/agent-home.sh")}"
export AGENT_HOME
exec python3 "$AGENT_HOME/tools/memory/mem.py" recall "$@"
