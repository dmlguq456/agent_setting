#!/usr/bin/env bash
# auto-memory 읽기 전용 recall — Hermes session_search(SQLite FTS5) 벤치마킹 이식 (T1, 2026-06-15)
#
# 과거가 남긴 것을 키워드로 회상한다 (읽기 전용 — 정보 제공만, write 없음):
#   - 정제 메모리 : ~/.claude/projects/<encoded-cwd>/memory/*.md   (기본 — 신호 깨끗)
#   - raw 세션 대화: ~/.claude/projects/<encoded-cwd>/*.jsonl       (--sessions — 미정제까지, 노이즈↑)
#
# Hermes 는 FTS5 DB 색인을 쓰지만, 우리 규모(cwd 당 .md 수십·.jsonl 수십)에선 ripgrep 즉석 검색이
# 충분하고 외부 의존·유지보수 DB 0 (불변식). 데이터 폭증 시 같은 인터페이스로 FTS5 교체 가능.
#
# 사용:
#   recall.sh "<query>"                 # 현 cwd 정제 메모리
#   recall.sh "<query>" --sessions      # + 현 cwd raw 세션 transcript
#   recall.sh "<query>" --all           # 전 cwd 정제 메모리
#   recall.sh "<query>" --all --sessions
#
# cwd 인코딩: 절대경로의 / . _ 를 '-' 로 치환 (Claude Code projects/ 규칙).
set -u
ROOT="$HOME/.claude/projects"
Q=""; ALL=0; SESS=0
for a in "$@"; do
  case "$a" in
    --all) ALL=1;;
    --sessions) SESS=1;;
    -h|--help) echo "usage: recall.sh \"<query>\" [--all] [--sessions]"; exit 2;;
    *) [ -z "$Q" ] && Q="$a";;
  esac
done
[ -z "$Q" ] && { echo "usage: recall.sh \"<query>\" [--all] [--sessions]"; exit 2; }

enc=$(printf '%s' "$PWD" | sed 's#[/._]#-#g')
HAVE_RG=0; command -v rg >/dev/null 2>&1 && HAVE_RG=1

search_md(){ # $1=dir — 정제 메모리
  if [ "$HAVE_RG" -eq 1 ]; then rg -i -n --no-heading -C1 -g '*.md' -- "$Q" "$1" 2>/dev/null
  else grep -i -n -r -C1 --include='*.md' -- "$Q" "$1" 2>/dev/null; fi
}
search_jsonl(){ # $1=dir — raw 세션: 긴 JSON 줄에서 _매치 주변 context_ 만 뽑아 노이즈 억제
  if [ "$HAVE_RG" -eq 1 ]; then
    # PCRE2(-P) 로 query 를 literal(\Q..\E) 처리 + 앞뒤 window. 미지원 환경이면 max-columns 미리보기로 폴백.
    rg -i -oP -n --no-heading -g '*.jsonl' ".{0,40}\\Q${Q}\\E.{0,160}" "$1" 2>/dev/null \
      || rg -i -n --no-heading --max-columns=200 --max-columns-preview -g '*.jsonl' -- "$Q" "$1" 2>/dev/null
  else
    grep -i -n -r --include='*.jsonl' -- "$Q" "$1" 2>/dev/null | grep -ioE ".{0,40}${Q}.{0,160}" 2>/dev/null
  fi
}

# --- 정제 메모리 (항상) ---
echo "# memory recall: \"$Q\"  [메모리 / $([ "$ALL" -eq 1 ] && echo '전 cwd' || echo '현 cwd')]"
if [ "$ALL" -eq 1 ]; then
  mout=$([ -d "$ROOT" ] && search_md "$ROOT" | head -60)
else
  md="$ROOT/$enc/memory"
  if [ -d "$md" ]; then mout=$(search_md "$md" | head -60); else mout="(현 cwd 메모리 없음: $md)"; fi
fi
[ -z "$mout" ] && echo "(메모리 매칭 없음)" || printf '%s\n' "$mout"

# --- raw 세션 transcript (opt-in) ---
if [ "$SESS" -eq 1 ]; then
  echo
  echo "# raw 세션 transcript: \"$Q\"  [$([ "$ALL" -eq 1 ] && echo '전 cwd' || echo '현 cwd')]  (미정제 — 노이즈 주의, 정제 메모리 우선)"
  if [ "$ALL" -eq 1 ]; then
    sout=$(for d in "$ROOT"/*/; do search_jsonl "$d"; done | head -50)
  else
    pd="$ROOT/$enc"
    if [ -d "$pd" ]; then sout=$(search_jsonl "$pd" | head -50); else sout="(현 cwd 세션 기록 없음: $pd)"; fi
  fi
  [ -z "$sout" ] && echo "(세션 매칭 없음)" || printf '%s\n' "$sout"
fi
