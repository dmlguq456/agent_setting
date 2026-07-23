#!/bin/sh
# PreToolUse(Agent|Task): give native Claude subagent spawns the config-declared
# default model tier instead of silently inheriting the interactive session
# model (core/ADAPTATION.md §3). Injection re-emits the FULL tool_input with a
# `model` field added; it is skipped whenever the caller already chose a model,
# the spawn is an intentional parent-inherit surface (subagent_type=fork), or
# the resolved agent definition frontmatter pins a model. Tier resolution
# (CFG_NATIVE_SUBAGENT -> CFG_TIER_<T>_MODEL) reads the Claude adapter
# models.conf relative to this script's realpath — <hookdir>/../config/ for an
# adapter-local or fixture layout, <hookdir>/../adapters/claude/config/ for the
# canonical shared hooks/ layer; no concrete model ID is hardcoded here
# (tools/check-model-config.py).
# Runtime override: CLAUDE_NATIVE_SUBAGENT_MODEL=<alias> forces the injected
# model; CLAUDE_NATIVE_SUBAGENT_MODEL=inherit disables injection entirely.
# Fail-open: on any parse/filesystem doubt emit nothing and exit 0 (inheritance
# preserved). This hook never exits non-zero and never writes stderr.
''''exec python3 "$0" "$@" # '''
import glob
import json
import os
import re
import sys

FRONTMATTER_MODEL = re.compile(r"^model:[ \t]*(.*?)[ \t]*$")


def parse_conf(path):
    conf = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            val = val.strip()
            if val[:1] in ('"', "'"):
                val = val[1:].split(val[0], 1)[0]
            else:
                val = val.split("#", 1)[0].strip()
            conf[key.strip()] = val
    return conf


def frontmatter_model(path):
    """Return the frontmatter model pin, or None when the file pins nothing."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() in ("---", "..."):
            break
        match = FRONTMATTER_MODEL.match(line)
        if match:
            value = match.group(1).strip().strip("\"'")
            # Since v2.1.196 a frontmatter `inherit` value is treated as unset.
            if value and value != "inherit":
                return value
            return None
    return None


def agent_definition(name):
    """First existing definition file for the agent name, or None (built-in)."""
    home = os.path.expanduser("~")
    candidates = []
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "").strip()
    if project_dir:
        candidates.append(os.path.join(project_dir, ".claude", "agents", name + ".md"))
    candidates.append(os.path.join(home, ".claude", "agents", name + ".md"))
    candidates.extend(sorted(glob.glob(
        os.path.join(home, ".claude", "plugins", "cache", "*", "*", "*", "agents", name + ".md"))))
    candidates.extend(sorted(glob.glob(
        os.path.join(home, ".claude", "plugins", "marketplaces", "*", "plugins", "*", "agents", name + ".md"))))
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def main():
    payload = json.loads(sys.stdin.read())
    if payload.get("tool_name") not in ("Agent", "Task"):
        return
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return
    if tool_input.get("model"):
        return  # explicit per-invocation choice (including explicit inherit)
    subagent_type = str(tool_input.get("subagent_type") or "")
    if subagent_type == "fork":
        return  # fork intentionally inherits the parent model
    # Namespaced plugin types (`plugin:agent`) resolve to the last segment.
    name = subagent_type.rsplit(":", 1)[-1]
    if name:
        definition = agent_definition(name)
        if definition and frontmatter_model(definition):
            return  # agent definition owns its model pin
    override = os.environ.get("CLAUDE_NATIVE_SUBAGENT_MODEL", "").strip()
    if override == "inherit":
        return  # runtime escape hatch: keep session inheritance
    if override:
        target = override
    else:
        hook_dir = os.path.dirname(os.path.realpath(__file__))
        conf_path = None
        for candidate in (
            os.path.join(hook_dir, "..", "config", "models.conf"),
            os.path.join(hook_dir, "..", "adapters", "claude", "config", "models.conf"),
        ):
            if os.path.isfile(candidate):
                conf_path = candidate
                break
        if conf_path is None:
            return
        conf = parse_conf(conf_path)
        tier = conf.get("CFG_NATIVE_SUBAGENT", "").strip()
        target = conf.get("CFG_TIER_%s_MODEL" % tier.upper(), "").strip() if tier else ""
    if not target:
        return
    updated = dict(tool_input)
    updated["model"] = target
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "updatedInput": updated,
    }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
