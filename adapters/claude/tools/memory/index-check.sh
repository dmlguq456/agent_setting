#!/usr/bin/env bash
# MEMORY.md 인덱스 drift 점검 (+ --fix: 누락 포인터 append) — T1 인덱스 보강 (2026-06-15)
# NOTE(2026-06-15): store FTS5 색인은 'mem index' 가 관할. 본 스크립트는 legacy projects/<cwd>/memory/ 의 MEMORY.md *텍스트 인덱스* 점검 전용(별개 대상). store 색인 점검 아님.
#
# auto-memory 의 cwd 마다 MEMORY.md 인덱스가 얇아(파일은 있는데 인덱스 누락) recall 이
# 약해지는 문제를 잡는다. 기본은 _report_ — 누락·고아 줄만 보고. --fix 는 _append-only_:
# frontmatter(name/description)에서 누락 포인터만 추가, 기존 큐레이션 줄은 절대 건드리지 않음.
#
# 사용:
#   index-check.sh                 # 현 cwd 메모리 인덱스 점검 (report)
#   index-check.sh <memory_dir>    # 특정 메모리 dir 점검
#   index-check.sh [dir] --fix     # 누락 포인터 append (additive)
set -u
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
AGENT_HOME="${AGENT_HOME:-$("$SCRIPT_DIR/../../utilities/agent-home.sh")}"
ROOT="$AGENT_HOME/projects"
DIR=""; FIX=0
for a in "$@"; do
  case "$a" in --fix) FIX=1;; -h|--help) echo "usage: index-check.sh [memory_dir] [--fix]"; exit 2;; *) DIR="$a";; esac
done
if [ -z "$DIR" ]; then
  enc=$(printf '%s' "$PWD" | sed 's#[/._]#-#g'); DIR="$ROOT/$enc/memory"
fi
[ -d "$DIR" ] || { echo "메모리 dir 없음: $DIR"; exit 0; }
IDX="$DIR/MEMORY.md"

echo "# index-check: $DIR"
[ -f "$IDX" ] || echo "(MEMORY.md 없음 — --fix 시 헤더+포인터 생성)"

missing=0
# 정방향: 메모리 파일이 인덱스에 없음
for f in "$DIR"/*.md; do
  [ -e "$f" ] || continue
  b=$(basename "$f")
  [ "$b" = "MEMORY.md" ] && continue
  if [ -f "$IDX" ] && grep -qF "($b)" "$IDX" 2>/dev/null; then continue; fi
  name=$(awk -F': *' '/^name:/{print $2; exit}' "$f" 2>/dev/null)
  desc=$(awk -F': *' '/^description:/{print $2; exit}' "$f" 2>/dev/null)
  [ -z "$name" ] && name="$b"
  line="- [${name}](${b}) — ${desc:-(설명 없음)}"
  if [ "$FIX" -eq 1 ]; then
    [ -f "$IDX" ] || printf '# MEMORY.md — index\n\n' > "$IDX"
    printf '%s\n' "$line" >> "$IDX"; echo "[append] $b"
  else
    echo "[missing] $line"
  fi
  missing=$((missing+1))
done

# 역방향: 인덱스가 가리키는데 파일이 없음 (고아 줄 — 보고만, 자동 제거 X)
orphan=0
if [ -f "$IDX" ]; then
  while IFS= read -r ref; do
    [ -f "$DIR/$ref" ] || { echo "[orphan] 인덱스가 가리키는 파일 없음: $ref"; orphan=$((orphan+1)); }
  done < <(grep -oE '\(([A-Za-z0-9._-]+\.md)\)' "$IDX" 2>/dev/null | tr -d '()' | sort -u)
fi

if [ "$missing" -eq 0 ] && [ "$orphan" -eq 0 ]; then
  echo "인덱스 정합 — 누락 0, 고아 0"
else
  [ "$missing" -gt 0 ] && { [ "$FIX" -eq 1 ] && echo "→ $missing 줄 append 완료" || echo "→ $missing 줄 누락 (append: --fix)"; }
  [ "$orphan" -gt 0 ] && echo "→ $orphan 고아 줄 (직접 정리 권장 — 자동 제거 안 함)"
fi
