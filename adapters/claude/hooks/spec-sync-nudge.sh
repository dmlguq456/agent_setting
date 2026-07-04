#!/usr/bin/env bash
# spec-sync-nudge — PostToolUse(Edit|Write|MultiEdit) 사후 동기화 nudge.
#   spec-backed 프로젝트에서 소스 파일 직접 편집이 spec 서술을 stale 하게 만들 수 있을 때,
#   편집으로 *사라진 토큰*(값·식별자)을 spec/*.md 에서 grep 해 히트를 additionalContext 로
#   메인에 사전주입한다. CLAUDE §3 "대응 동기화는 변경의 일부" 를 결정론 hook 이 뒷받침 —
#   메인이 "spec 도 고쳐야 하나?" 판단을 잊어도 drift 후보가 눈앞에 놓인다.
#   drill a_postedit_spec_sync 의 결정론 backstop (HOOKS.md design-bias: 출력 shape 은 conformance).
#
#   Guards (모두 clean no-op exit 0 — never-block 불변식):
#     - MEM_DISTILL=1 → distiller 세션 재귀 차단 (세 메모리 hook 과 동일 가드)
#     - SPEC_SYNC_NUDGE=0 → per-shell opt-out
#     - hook_event_name ≠ PostToolUse → no-op
#     - spec-backed(.agent_reports|.claude_reports /spec/pipeline_state.yaml) 아님 → no-op
#     - 편집 파일이 spec 디렉토리 자체 → no-op (spec 편집은 대상 아님)
#     - 사라진 토큰 없음 / spec 히트 없음 → no-op (압도적 다수 정상 경로)
#
#   Read-only 불변식: DB·파일 write 0. additionalContext 만 emit — 메인 상태 무변경.
#
#   Cap (context blowup 방지):
#     SPEC_SYNC_HITS   (default 8)  — 주입 최대 히트 줄 수
#     SPEC_SYNC_TOKENS (default 12) — 검사 최대 사라진-토큰 수
#
#   Portable CLI:
#     spec-sync-nudge.sh --file <path> [--old <s>] [--new <s>] [--cwd <dir>] [--format text|claude-json]
#   인자 없으면 stdin 에서 PostToolUse hook JSON 을 읽어 claude-json 출력.
#   등록은 adapter hook 설정이 담당한다 (matcher Edit|Write|MultiEdit, timeout 10).
set -euo pipefail
HOOK_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")" && pwd)"
AGENT_HOME="${AGENT_HOME:-$("$HOOK_DIR/../utilities/agent-home.sh")}"
export AGENT_HOME

usage() {
  cat <<'EOF'
usage: spec-sync-nudge.sh --file <path> [--old <s>] [--new <s>] [--cwd <dir>] [--format text|claude-json]

Without arguments, reads Claude PostToolUse hook JSON from stdin and emits Claude hook JSON.
EOF
}

# 재귀가드 (불변식): distiller 세션이면 trigger X, stdin drain 후 즉시 exit 0.
[ "${MEM_DISTILL:-}" = "1" ] && { cat >/dev/null 2>&1; exit 0; }
# per-shell opt-out.
[ "${SPEC_SYNC_NUDGE:-1}" = "0" ] && { cat >/dev/null 2>&1; exit 0; }

# 핵심 로직 = portable python (regex/glob/JSON escaping 안전). CLI/stdin 두 모드.
NUDGE_PY='
import os, sys, json, re, glob

MODE = os.environ.get("SSN_MODE", "stdin")
FMT = os.environ.get("SSN_FORMAT", "claude-json")

if MODE == "cli":
    file_path = os.environ.get("SSN_FILE", "")
    old = os.environ.get("SSN_OLD", "")
    new = os.environ.get("SSN_NEW", "")
    cwd = os.environ.get("SSN_CWD") or os.getcwd()
else:
    try:
        d = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if (d.get("hook_event_name") or "") != "PostToolUse":
        sys.exit(0)
    cwd = d.get("cwd") or os.getcwd()
    ti = d.get("tool_input") or {}
    file_path = ti.get("file_path") or ti.get("filePath") or ti.get("path") or ""
    op, np = [], []
    if "old_string" in ti or "new_string" in ti:
        op.append(ti.get("old_string") or ""); np.append(ti.get("new_string") or "")
    for e in (ti.get("edits") or []):
        if isinstance(e, dict):
            op.append(e.get("old_string") or ""); np.append(e.get("new_string") or "")
    old = "\n".join(op); new = "\n".join(np)

if not file_path:
    sys.exit(0)
if not os.path.isabs(file_path):
    file_path = os.path.join(cwd, file_path)

def find_spec_dir(start):
    d = os.path.dirname(os.path.abspath(start)); prev = None
    while d and d != prev:
        for art in (".agent_reports", ".claude_reports"):
            spec = os.path.join(d, art, "spec")
            if os.path.isfile(os.path.join(spec, "pipeline_state.yaml")):
                return spec
        prev, d = d, os.path.dirname(d)
    return None

spec_dir = find_spec_dir(file_path)
if not spec_dir:
    sys.exit(0)

# 편집 파일이 spec 디렉토리 자체 → 대상 아님
try:
    if os.path.commonpath([os.path.abspath(file_path), os.path.abspath(spec_dir)]) == os.path.abspath(spec_dir):
        sys.exit(0)
except ValueError:
    pass

# prose/문서 편집은 대상 아님 — spec drift 의 핵심은 code/config 값 변경이다.
# 문서 워딩 reword 로 흔한 단어(runtime/bootstrap 등)를 지우면 무관한 spec 산문과
# 오탐 매칭됨(실관찰). spec 자체도 .md 지만 위 spec-dir 스킵이 이미 걸러낸다.
PROSE_EXT = {".md", ".markdown", ".mdx", ".rst", ".txt", ".adoc", ".org"}
if os.path.splitext(file_path)[1].lower() in PROSE_EXT:
    sys.exit(0)

# 사라진 토큰: old 에 있고 new 에 없는 값/식별자
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}|\d+(?:\.\d+)?")
STOP = {"def","for","pass","return","self","the","and","not","import","from","class",
        "true","false","none","null","eof","this","that","with","print","range","function"}
new_set = set(TOKEN_RE.findall(new or ""))
removed, seen = [], set()
maxtok = int(os.environ.get("SPEC_SYNC_TOKENS", "12"))
for t in TOKEN_RE.findall(old or ""):
    if t in new_set or t in seen or t.lower() in STOP:
        continue
    # alpha 식별자는 code-like(대문자·숫자·`_` 포함)만 후보 — 흔한 소문자 산문 단어 배제(오탐 억제).
    # 숫자·버전 토큰(30·512·1e-4 형태)은 항상 후보 (config 값 drift 의 주 신호).
    if t[:1].isalpha():
        if len(t) < 3:
            continue
        if t.islower() and "_" not in t and not any(c.isdigit() for c in t):
            continue
    seen.add(t); removed.append(t)
    if len(removed) >= maxtok:
        break
if not removed:
    sys.exit(0)

# spec markdown (prd.md + design/*.md 등), _internal 스냅샷 제외
md = [f for f in glob.glob(os.path.join(spec_dir, "**", "*.md"), recursive=True)
      if "_internal" not in os.path.relpath(f, spec_dir).split(os.sep)]
md.sort()

def bounded(line, tok):
    return re.search(r"(?<![A-Za-z0-9_])" + re.escape(tok) + r"(?![A-Za-z0-9_])", line) is not None

hits, cap = [], int(os.environ.get("SPEC_SYNC_HITS", "8"))
base = os.path.dirname(spec_dir)
for mf in md:
    try:
        with open(mf, encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                for t in removed:
                    if bounded(line, t):
                        hits.append((os.path.relpath(mf, base), i, t, line.rstrip().strip()))
                        break
                if len(hits) >= cap:
                    break
    except Exception:
        continue
    if len(hits) >= cap:
        break
if not hits:
    sys.exit(0)

rows = []
for rel, ln, tok, text in hits:
    snip = text if len(text) <= 120 else text[:117] + "..."
    rows.append("  {}:{}  «{}»  {}".format(rel, ln, tok, snip))
body = ("# \U0001f517 spec 동기화 nudge — 방금 편집이 아래 spec 서술과 어긋날 수 있음\n"
        "편집으로 사라진 값/식별자가 spec 에 아직 남아 있습니다. 대응 동기화(변경의 일부)를 검토하세요:\n"
        + "\n".join(rows))

if FMT == "text":
    print(body)
else:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": body}}, ensure_ascii=False))
'

if [ "$#" -gt 0 ]; then
  FILE=""; OLD=""; NEW=""; CWD="$PWD"; FORMAT="text"
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --file)   [ "$#" -ge 2 ] || { echo "spec-sync-nudge: --file requires a path" >&2; exit 64; }; FILE=$2; shift 2 ;;
      --old)    [ "$#" -ge 2 ] || { echo "spec-sync-nudge: --old requires a value" >&2; exit 64; }; OLD=$2; shift 2 ;;
      --new)    [ "$#" -ge 2 ] || { echo "spec-sync-nudge: --new requires a value" >&2; exit 64; }; NEW=$2; shift 2 ;;
      --cwd)    [ "$#" -ge 2 ] || { echo "spec-sync-nudge: --cwd requires a dir" >&2; exit 64; }; CWD=$2; shift 2 ;;
      --format) [ "$#" -ge 2 ] || { echo "spec-sync-nudge: --format requires a value" >&2; exit 64; }
                case "$2" in text|claude-json) FORMAT=$2 ;; *) echo "spec-sync-nudge: unknown format: $2" >&2; exit 64 ;; esac; shift 2 ;;
      -h|--help) usage; exit 0 ;;
      *) echo "spec-sync-nudge: unknown argument: $1" >&2; usage >&2; exit 64 ;;
    esac
  done
  [ -n "$FILE" ] || { echo "spec-sync-nudge: --file is required" >&2; exit 64; }
  SSN_MODE=cli SSN_FILE="$FILE" SSN_OLD="$OLD" SSN_NEW="$NEW" SSN_CWD="$CWD" SSN_FORMAT="$FORMAT" \
    python3 -c "$NUDGE_PY" || true
  exit 0
fi

input=$(cat 2>/dev/null || true)
[ -z "$input" ] && exit 0
printf '%s' "$input" | SSN_MODE=stdin SSN_FORMAT=claude-json python3 -c "$NUDGE_PY" || true
exit 0
