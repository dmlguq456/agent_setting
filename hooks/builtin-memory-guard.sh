#!/bin/sh
# PreToolUse(Write): 하네스 내장 file 메모리(projects/<cwd>/memory/*.md) 직접 Write 차단.
#   통합 메모리(memory.db)가 단일 SoT 이므로 내장 file 메모리는 _쓰지 않는다_ — 기억 write 는 전부
#   mem CLI(DB) 경유로 단일화 (§0.5 결정론 장치 — instruction 이 아니라 hook 이 강제, 2026-06-16).
#   mem.py 의 python 파일 I/O(Bash 경유)와 projection 은 Write 툴이 아니라 본 hook 미적용 — 무영향.
#   self-report 아닌 검증 가능 하드 게이트. POSIX sh, no jq.

input=$(cat 2>/dev/null)
[ -z "$input" ] && exit 0

fp=$(printf '%s' "$input" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//; s/"$//')

case "$fp" in
  */projects/*/memory/*.md)
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' \
      "내장 file 메모리(projects/<cwd>/memory/*.md) 직접 write 금지 — 통합 메모리는 memory.db(단일 SoT). 기억은 mem CLI 경유: python3 <agent-home>/tools/memory/mem.py add <tier> <type> \"<body>\" 또는 note \"<body>\", 사용자 통제 메모는 /post-it. (어댑터 메모리 정책 · MEMORY §7)"
    exit 0 ;;
esac
exit 0
