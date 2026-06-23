#!/usr/bin/env bash
# recall — 통합 기억 회상 (thin wrapper → mem recall). 2026-06-15 전환:
#   기존 파일-스캔 방식을 버리고 통합 store(durable+working) + profile tier records + (--sessions) raw 대화를 검색.
#   사용: recall.sh "<query>" [--tier working|durable] [--scope project|global] [--all] [--sessions]
#   읽기 전용 — 정보 제공만(불변식). 상세 = tools/memory/README.md · MEMORY §7.4.
exec python3 "$HOME/.claude/tools/memory/mem.py" recall "$@"
