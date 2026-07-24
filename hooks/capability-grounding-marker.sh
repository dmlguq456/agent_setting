#!/bin/sh
# PostToolUse(Skill): record an inline entry-capability grounding marker so Fleet can show
# `capability(mode·intensity)` for entry-skill work that runs inline and thus leaves no jobs.log
# dispatch row. Capability is exact (the Skill name); mode/intensity are best-effort from the
# invocation args (structured `--mode`/`--intensity`, else the fixed intensity vocabulary).
# POSIX sh reads the hook JSON on stdin; python3 parses it and calls the portable utility.

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
AGENT_HOME="${AGENT_HOME:-$("$SCRIPT_DIR/../utilities/agent-home.sh" 2>/dev/null)}"
[ -n "$AGENT_HOME" ] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

# The heredoc below feeds python its program on stdin, so the hook JSON must be captured first
# and handed over out-of-band (env), not left on stdin.
CG_INPUT=$(cat 2>/dev/null)
[ -n "$CG_INPUT" ] || exit 0

AGENT_HOME="$AGENT_HOME" \
CG_UTIL="$SCRIPT_DIR/../utilities/capability-grounding.sh" \
CG_INPUT="$CG_INPUT" \
python3 - <<'PY'
import json, os, re, subprocess, sys

try:
    payload = json.loads(os.environ.get("CG_INPUT") or "")
except Exception:
    sys.exit(0)
if payload.get("tool_name") != "Skill":
    sys.exit(0)
tool_input = payload.get("tool_input") or {}
skill = str(tool_input.get("skill") or "").strip()
ENTRY = {
    "autopilot-apply", "autopilot-code", "autopilot-design", "autopilot-draft",
    "autopilot-lab", "autopilot-note", "autopilot-refine", "autopilot-research",
    "autopilot-ship", "autopilot-spec",
}
if skill not in ENTRY:
    sys.exit(0)
sid = str(payload.get("session_id") or "").strip()
if not sid:
    sys.exit(0)
cwd = str(payload.get("cwd") or "").strip()
args = str(tool_input.get("args") or "")

INTENSITIES = ("direct", "quick", "standard", "strong", "thorough", "adversarial")
intensity = ""
match = re.search(r"--intensity[=\s]+([a-z]+)", args)
if match and match.group(1) in INTENSITIES:
    intensity = match.group(1)
else:
    for word in re.findall(r"[a-z]+", args.lower()):
        if word in INTENSITIES:
            intensity = word
            break
mode = ""
match = re.search(r"--mode[=\s]+([a-z0-9/_,-]+)", args)
if match:
    mode = match.group(1)

cmd = ["sh", os.environ["CG_UTIL"], "record", "--sid", sid, "--capability", skill,
       "--agent-home", os.environ.get("AGENT_HOME", "")]
if mode:
    cmd += ["--mode", mode]
if intensity:
    cmd += ["--intensity", intensity]
if cwd:
    cmd += ["--cwd", cwd]
try:
    subprocess.run(cmd, timeout=5, check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except Exception:
    pass
PY
exit 0
