#!/usr/bin/env bash
# Portable loop/drill adapter runner — the core/adapter split for loop engineering.
#
# Loop CASES (prompt/fixture/assert) are runtime-neutral; only the RUNNER is
# adapter-specific. This library runs a prompt on the chosen runtime adapter and
# normalizes the result to (a) a transcript file and (b) a
# "turns|in_tok|out_tok|cost" metrics line on stdout — the same contract for all
# three adapters, so `run.sh` and the loop scripts stay adapter-agnostic.
#
#   run_case_on_adapter <adapter> <prompt_file> <repo_dir> <timeout_s> <max_turns> <out_json> <out_transcript>
#     adapters: claude | codex | opencode
#     stdout  : turns|in_tok|out_tok|cost
#
# Prereq for codex/opencode: the runtime projection must be installed (so the
# harness bootstrap + hooks/plugin load in the headless run); otherwise the case
# runs without the harness and the assertion is meaningless. Callers should gate
# on `preflight.sh doctor --runtime` (codex) / installed plugin (opencode).
#
# JSON event schemas (probed 2026-07-01):
#   codex exec --json : {"type":"item.completed","item":{"type":"agent_message","text":..}}
#                       {"type":"turn.completed","usage":{"input_tokens","output_tokens"}}
#   opencode run --format json : {"type":"text","part":{"text":..}}
#                       {"type":"step_finish","part":{"tokens":{"input","output"},"cost":..}}

DRILL_CLAUDE_TOOLS="${DRILL_CLAUDE_TOOLS:-Bash,Read,Write,Edit,Glob,Grep,Skill,Agent,TodoWrite}"

run_case_on_adapter() {
  case "$1" in
    claude)   _loop_run_claude   "${@:2}" ;;
    codex)    _loop_run_codex    "${@:2}" ;;
    opencode) _loop_run_opencode "${@:2}" ;;
    *) echo "?|?|?|?"; return 64 ;;
  esac
}

_loop_run_claude() {
  local pf=$1 repo=$2 to=$3 maxturns=$4 j=$5 t=$6
  local bin="${CLAUDE_BIN:-$HOME/.local/bin/claude}"
  local settings="${DRILL_CLAUDE_SETTINGS:-$AGENT_HOME/adapters/claude/settings.json}"
  local settings_arg=()
  [ -f "$settings" ] && settings_arg=(--settings "$settings")
  ( cd "$repo" && timeout "$to" "$bin" -p "$(cat "$pf")" \
      "${settings_arg[@]}" --allowedTools "$DRILL_CLAUDE_TOOLS" --output-format json ${maxturns:+--max-turns "$maxturns"} ) \
      > "$j" 2>"${j%.json}.stderr.txt"
  python3 - "$j" "$t" <<'PY'
import json, sys
try: d = json.load(open(sys.argv[1]))
except Exception: d = {}
open(sys.argv[2], "w").write(d.get("result", "") or "")
u = d.get("usage", {}) or {}
tin = (u.get("input_tokens", 0) or 0) + (u.get("cache_creation_input_tokens", 0) or 0) + (u.get("cache_read_input_tokens", 0) or 0)
print(f"{d.get('num_turns','?')}|{tin}|{u.get('output_tokens',0)}|{round(d.get('total_cost_usd') or 0, 3)}")
PY
}

_loop_run_codex() {
  local pf=$1 repo=$2 to=$3 maxturns=$4 j=$5 t=$6
  local bin="${CODEX_BIN:-codex}"
  ( cd "$repo" && timeout "$to" "$bin" exec --cd "$repo" --sandbox workspace-write --skip-git-repo-check --json - < "$pf" ) \
      > "$j" 2>"${j%.json}.stderr.txt"
  python3 - "$j" "$t" <<'PY'
import json, sys
texts = []; tin = tout = turns = 0
for line in open(sys.argv[1], encoding="utf-8", errors="replace"):
    line = line.strip()
    if not line: continue
    try: e = json.loads(line)
    except Exception: continue
    et = e.get("type")
    if et == "item.completed":
        it = e.get("item") or {}
        if it.get("type") == "agent_message" and it.get("text"):
            texts.append(it["text"])
    elif et == "turn.completed":
        turns += 1
        u = e.get("usage") or {}
        tin += (u.get("input_tokens", 0) or 0)
        tout += (u.get("output_tokens", 0) or 0)
open(sys.argv[2], "w").write("\n".join(texts))
print(f"{turns or '?'}|{tin}|{tout}|0")
PY
}

_loop_run_opencode() {
  local pf=$1 repo=$2 to=$3 maxturns=$4 j=$5 t=$6
  local bin="${OPENCODE_BIN:-opencode}"
  command -v "$bin" >/dev/null 2>&1 || bin="$HOME/.opencode/bin/opencode"
  local model_arg=(); [ -n "${OPENCODE_LOOP_MODEL:-}" ] && model_arg=(-m "$OPENCODE_LOOP_MODEL")
  ( cd "$repo" && timeout "$to" "$bin" run --dir "$repo" --format json "${model_arg[@]}" "$(cat "$pf")" ) \
      > "$j" 2>"${j%.json}.stderr.txt"
  python3 - "$j" "$t" <<'PY'
import json, sys
parts = {}; tin = tout = turns = 0; cost = 0.0
for line in open(sys.argv[1], encoding="utf-8", errors="replace"):
    line = line.strip()
    if not line: continue
    try: e = json.loads(line)
    except Exception: continue
    et = e.get("type"); part = e.get("part") or {}
    if et == "text":
        pid = part.get("id")
        if pid and isinstance(part.get("text"), str):
            parts[pid] = part["text"]   # keep latest snapshot per part id (dedupe streaming)
    elif et == "step_finish":
        turns += 1
        tk = part.get("tokens") or {}
        tin += (tk.get("input", 0) or 0)
        tout += (tk.get("output", 0) or 0)
        cost += (part.get("cost", 0) or 0)
open(sys.argv[2], "w").write("\n".join(parts.values()))
print(f"{turns or '?'}|{tin}|{tout}|{round(cost, 3)}")
PY
}
