#!/usr/bin/env bash
# auto-memory 읽기 전용 recall — Hermes session_search(FTS5) 벤치마킹 이식 (T1, 2026-06-15)
#
# 과거 세션이 남긴 메모리(~/.claude/projects/<encoded-cwd>/memory/*.md)를 키워드로 검색한다.
# 세션 시작 시 자동 주입되는 MEMORY.md 인덱스로는 못 찾는 _본문_ 까지 on-demand 회상.
# 읽기 전용 — 정보 제공만, write 없음. (불변식: recall=정보 제공, 결정·저장은 사용자.)
#
# 사용:
#   recall.sh "<query>"          # 현 cwd 메모리만 (per-cwd 격리 = default)
#   recall.sh "<query>" --all    # 전 cwd 메모리 (per-cwd 격리 정책상 _명시_ 시만)
#
# cwd 인코딩: 절대경로의 / . _ 를 모두 '-' 로 치환 (Claude Code projects/ 규칙).
set -u
ROOT="$HOME/.claude/projects"
Q="${1:-}"
case "$Q" in ""|-h|--help) echo "usage: recall.sh \"<query>\" [--all]"; exit 2;; esac
ALL=0; [ "${2:-}" = "--all" ] && ALL=1

enc=$(printf '%s' "$PWD" | sed 's#[/._]#-#g')
cwd_mem="$ROOT/$enc/memory"

if command -v rg >/dev/null 2>&1; then
  do_search(){ rg -i -n --no-heading -C1 -g '*.md' -- "$Q" "$1" 2>/dev/null; }
else
  do_search(){ grep -i -n -r -C1 --include='*.md' -- "$Q" "$1" 2>/dev/null; }
fi

if [ "$ALL" -eq 1 ]; then
  echo "# memory recall: \"$Q\"  [scope: 전 cwd]"
  [ -d "$ROOT" ] || { echo "(메모리 root 없음: $ROOT)"; exit 0; }
  out=$(do_search "$ROOT" | head -80)
else
  echo "# memory recall: \"$Q\"  [scope: 현 cwd = $PWD]"
  if [ ! -d "$cwd_mem" ]; then
    echo "(현 cwd 메모리 없음: $cwd_mem)"
    echo "→ 전 cwd 검색하려면: recall.sh \"$Q\" --all"
    exit 0
  fi
  out=$(do_search "$cwd_mem" | head -80)
fi

if [ -z "$out" ]; then echo "(매칭 없음)"; else printf '%s\n' "$out"; fi
