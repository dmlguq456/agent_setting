#!/usr/bin/env python3
"""Build manifest.json from the agent harness definitions (mechanical transcription).

SoT = the definitions themselves:
  - adapters/claude/skills/*/SKILL.md   frontmatter  (name, argument-hint, metadata:{group,fam,modes,blurb})
  - adapters/claude/agents/*.md  frontmatter  (name, model, metadata:{modes,blurb})
  - loops/README.md     "현역" table  + LOOP_LAYER constant
  - adapters/claude/settings.json  Claude Code adapter hook registration (read-only)
  - TRACKS              documented constant (below), validated against discovered skills

manifest.json is a PURE derivation — never hand-edit it. Edit the definitions, then
re-run this script (or `/sync-skills`, which calls it). The build is byte-identical on
re-run (idempotent): GENERATED_FROM is a fixed string (NO date/timestamp), every list is
sorted by a stable key, json.dumps uses ensure_ascii=False + indent=2 + sort_keys=False
(field order preserved) + a trailing newline.

Custom skill/agent fields live nested under the reserved `metadata:` frontmatter key
(CC's recommended nest for custom fields — Desktop/strict-validator compatible). This
script FLATTENS metadata.* up to top-level manifest fields, so the manifest stays flat
and matches the consumer's setting_* columns 1:1.

Consumer mapping note: the consumer's `setting_hooks.kind` column == this manifest's
`hooks[].event` field (naming difference only). body_md / updated_at columns are derived
by the consumer from its own manual_docs body, NOT from this manifest (so they are omitted
here, by design).

Usage:
  python3 tools/build-manifest.py            # write manifest.json at repo root
  python3 tools/build-manifest.py --check    # build in memory, diff vs existing, exit 1 on drift
"""
import sys
import os
import re
import json
import glob
import shlex

try:
    import yaml
except ImportError:
    sys.stderr.write("PyYAML required: pip install pyyaml\n")
    sys.exit(2)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # tools/ -> repo root
MANIFEST_PATH = os.path.join(REPO_ROOT, "manifest.json")

# Fixed provenance string — NO date/timestamp (idempotency invariant).
GENERATED_FROM = ("agent harness definitions "
                  "(adapters/claude/skills/*/SKILL.md, adapters/claude/agents/*.md, loops/README.md, Claude adapter settings.json)")

# hard_block allowlist = PreToolUse guards only (consumer attempt1 §2.4 / Claude adapter settings.json
# PreToolUse). herdr-agent-state is also registered on PreToolUse but is a state-marker,
# NOT a guard -> hard_block stays false for it.
GUARDS = {"artifact-guard", "git-state-guard", "spec-skill-gate", "builtin-memory-guard"}

# loop -> layer constant (source: loops/README.md 계층 table membership + consumer §2.5;
# study=L4 per the OPS-view divergence recorded in consumer §23.12 V1). The 계층 table
# itself is left semantically unchanged — this map is the machine-readable layer source.
LOOP_LAYER = {"oncall": "L3", "note": "L3", "drill": "L4", "study": "L4"}

# 4-track skeleton — documented constant (source: README.md §4 / WORKFLOW.md §1 4-track
# chains; gate positions = artifact-guard rule, not parseable from prose, per consumer
# §2.6). `steps` reference real skill slugs and are VALIDATED against discovered skills in
# build_tracks() (typo in a hand-typed slug => hard ERROR, since tracks is the one curated
# constant in an otherwise pure transcription).
TRACKS = [
    {"id": "research-lab", "label": "연구·실험", "color_token": "--cat-1",
     "steps": ["skill__analyze-project", "skill__autopilot-research", "skill__autopilot-spec",
               "skill__autopilot-code", "skill__autopilot-lab"],
     "gates": ["artifact-guard:after-research", "artifact-guard:after-spec"]},
    {"id": "library", "label": "라이브러리·CLI", "color_token": "--cat-5",
     "steps": ["skill__analyze-project", "skill__autopilot-spec", "skill__autopilot-code"],
     "gates": ["artifact-guard:after-analyze", "artifact-guard:after-spec"]},
    {"id": "document", "label": "문서", "color_token": "--cat-2",
     "steps": ["skill__analyze-project", "skill__autopilot-research", "skill__autopilot-draft",
               "skill__autopilot-refine", "skill__autopilot-apply"],
     "gates": ["artifact-guard:after-research"]},
    {"id": "app", "label": "앱", "color_token": "--cat-3",
     "steps": ["skill__autopilot-spec", "skill__autopilot-design", "skill__autopilot-code",
               "skill__autopilot-ship"],
     "gates": ["artifact-guard:after-spec"]},
]


# ---------------------------------------------------------------------------
# frontmatter parsing (tolerant — mirrors the CC loader / consumer parseFrontmatter,
# which are line-regex tolerant; survives a future unquoted-colon description without
# crashing the build)
# ---------------------------------------------------------------------------
def _split_frontmatter(path):
    raw = open(path, encoding="utf-8").read()
    if not raw.startswith("---"):
        return ""
    parts = raw.split("---", 2)   # ['', frontmatter, body]
    return parts[1] if len(parts) >= 2 else ""


def _scalar(fm_text, key):
    m = re.search(r'(?m)^%s:[ \t]*(.+?)[ \t]*$' % re.escape(key), fm_text)
    if not m:
        return ""
    v = m.group(1).strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
        v = v[1:-1]
    return v


def _metadata_block(fm_text):
    """Extract the `metadata:` mapping by yaml-parsing just that indented block.
    Tolerates blank lines inside the block (stops at the next column-0 key)."""
    m = re.search(r'(?ms)^metadata:[ \t]*\n((?:(?:[ \t]+\S.*|[ \t]*)\n)*)', fm_text)
    if not m:
        return {}
    block = "metadata:\n" + m.group(1)
    try:
        d = yaml.safe_load(block)
        md = d.get("metadata") if isinstance(d, dict) else None
        return md if isinstance(md, dict) else {}
    except Exception:
        return {}


def parse_frontmatter(path):
    """Return a dict with name/argument-hint/model + metadata(dict).
    Strict yaml first; on any failure fall back to line-regex + isolated metadata parse."""
    fm_text = _split_frontmatter(path)
    fm = None
    try:
        loaded = yaml.safe_load(fm_text)
        if isinstance(loaded, dict):
            fm = loaded
    except Exception:
        fm = None
    if fm is None:
        sys.stderr.write("WARN: %s — strict YAML frontmatter parse failed; using tolerant "
                         "fallback (likely an unquoted ':' in a value)\n" % path)
        fm = {
            "name": _scalar(fm_text, "name"),
            "argument-hint": _scalar(fm_text, "argument-hint"),
            "model": _scalar(fm_text, "model"),
            "metadata": _metadata_block(fm_text),
        }
    md = fm.get("metadata")
    if not isinstance(md, dict):
        fm["metadata"] = {}
    return fm


# ---------------------------------------------------------------------------
# builders
# ---------------------------------------------------------------------------
def build_skills():
    rows = []
    for path in sorted(glob.glob(os.path.join(REPO_ROOT, "adapters", "claude", "skills", "*", "SKILL.md"))):
        d = os.path.basename(os.path.dirname(path))
        fm = parse_frontmatter(path)
        md = fm["metadata"]
        rows.append({
            "slug": "skill__%s" % d,
            "name": fm.get("name", "") or "",
            "group": md.get("group", "") or "",
            "fam": md.get("fam", "") or "",
            "modes": md.get("modes", []) or [],
            "blurb": md.get("blurb", "") or "",
            "argument_hint": fm.get("argument-hint", "") or "",
        })
    return sorted(rows, key=lambda r: r["slug"])


def build_agents():
    rows = []
    for path in sorted(glob.glob(os.path.join(REPO_ROOT, "adapters", "claude", "agents", "*.md"))):
        stem = os.path.splitext(os.path.basename(path))[0]
        fm = parse_frontmatter(path)
        md = fm["metadata"]
        rows.append({
            "slug": "agent__%s" % stem,
            "name": fm.get("name", "") or "",
            "model": fm.get("model", "") or "",
            "modes": md.get("modes", []) or [],
            "blurb": md.get("blurb", "") or "",
        })
    return sorted(rows, key=lambda r: r["slug"])


def _parse_hook_command(cmd):
    """Return (mono, name, basename) or None. Strips env prefix + interpreter + path,
    retains the meaningful trailing arg (state for herdr, subcommand for mem.py) in name."""
    try:
        toks = shlex.split(cmd)
    except ValueError:
        toks = cmd.split()
    i = 0
    while i < len(toks) and re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', toks[i]):
        i += 1
    toks = toks[i:]
    if toks and toks[0] in ("bash", "sh", "zsh", "python3", "python", "node"):
        toks = toks[1:]
    if not toks:
        return None
    base = os.path.basename(toks[0])
    rest = toks[1:]
    if base.endswith(".sh"):
        mono = base[:-3]
    elif base.endswith(".py"):
        mono = base
    else:
        mono = base
    args = [a for a in rest if not a.startswith("-")]
    if base.endswith(".py") and args:
        name = "%s %s" % (mono, args[0])
    elif mono == "herdr-agent-state" and args:
        name = "%s %s" % (mono, args[0])
    else:
        name = mono
    return mono, name, base


def build_hooks():
    cfg = json.load(open(os.path.join(REPO_ROOT, "adapters", "claude", "settings.json"), encoding="utf-8"))
    rows = []
    seen = {}     # slug -> name; detects (mono,event) collisions that differ only by arg
    for event, entries in cfg.get("hooks", {}).items():
        for entry in entries:
            for h in entry.get("hooks", []):
                if h.get("type") != "command":
                    continue
                parsed = _parse_hook_command(h.get("command", ""))
                if not parsed:
                    continue
                mono, name, base = parsed
                if base.endswith(".test.sh"):     # exclude test harnesses (consumer §2.4)
                    continue
                slug = "hook__%s__%s" % (mono, event)
                if slug in seen:
                    if seen[slug] == name:
                        continue                  # true duplicate (identical registration)
                    # same (mono,event), different arg (e.g. herdr idle vs working on one
                    # event): make the loss VISIBLE and keep both rather than silently drop.
                    sys.stderr.write("WARN: hook slug collision %s (%r vs %r) — "
                                     "disambiguating with numeric suffix\n"
                                     % (slug, seen[slug], name))
                    n = 2
                    while ("%s__%d" % (slug, n)) in seen:
                        n += 1
                    slug = "%s__%d" % (slug, n)
                seen[slug] = name
                rows.append({
                    "slug": slug,
                    "name": name,
                    "mono": mono,
                    "event": event,
                    "hard_block": (event == "PreToolUse" and mono in GUARDS),
                })
    return sorted(rows, key=lambda r: (r["event"], r["mono"], r["slug"]))


def _split_row(line):
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def _is_separator(line):
    return bool(re.match(r'^\s*\|?\s*:?-{2,}', line)) and set(line.strip()) <= set("|-: ")


_HYUNYEOK_HEADER = ["루프", "형", "트리거", "대상", "하는 일", "산출", "사용자 접점"]
_LOOP_CELL = re.compile(r'\*\*(.+?)\*\*\s*\(`([^`]+)`\)')


def build_loops():
    lines = open(os.path.join(REPO_ROOT, "loops", "README.md"), encoding="utf-8").read().split("\n")
    # locate the 현역 table by EXACT 7-column header (the 후보 table shares the 형 column,
    # so a loose match would grab the wrong table).
    start = None
    for idx, line in enumerate(lines):
        if line.lstrip().startswith("|") and _split_row(line) == _HYUNYEOK_HEADER:
            start = idx
            break
    if start is None:
        return []
    rows = []
    for line in lines[start + 1:]:
        if not line.lstrip().startswith("|"):
            break                                   # table ended
        if _is_separator(line):
            continue                                # skip |---|---| row
        cells = _split_row(line)
        if len(cells) != len(_HYUNYEOK_HEADER):
            sys.stderr.write("WARN: loops 현역 row has %d cols (expected %d), skipped: %s\n"
                             % (len(cells), len(_HYUNYEOK_HEADER), line.strip()[:60]))
            continue
        rec = dict(zip(_HYUNYEOK_HEADER, cells))
        m = _LOOP_CELL.search(rec["루프"])
        if not m:
            continue
        name_kr = m.group(1).strip()
        mono = m.group(2).strip().rstrip("/")        # drill cell is `drill/` -> drill
        rows.append({
            "slug": "loop__%s" % mono,
            "name": name_kr,
            "mono": mono,
            "type": "time" if "시간" in rec["형"] else "event",
            "schedule": rec["트리거"],                # verbatim (markdown retained; consumer renders)
            "blurb": rec["하는 일"],
            "output_path": rec["산출"],
            "layer": LOOP_LAYER.get(mono, ""),
        })
    return sorted(rows, key=lambda r: r["slug"])


def build_tracks(skill_slugs):
    for t in TRACKS:
        for s in t["steps"]:
            if s not in skill_slugs:
                sys.stderr.write("ERROR: track '%s' references unknown skill slug '%s'\n" % (t["id"], s))
                sys.exit(1)
    return [dict(t) for t in TRACKS]


def build_manifest():
    skills = build_skills()
    skill_slugs = {r["slug"] for r in skills}
    return {
        "generated_from": GENERATED_FROM,
        "skills": skills,
        "agents": build_agents(),
        "hooks": build_hooks(),
        "loops": build_loops(),
        "tracks": build_tracks(skill_slugs),
    }


def render(manifest):
    return json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def main(argv):
    check = "--check" in argv
    text = render(build_manifest())
    if check:
        existing = ""
        if os.path.exists(MANIFEST_PATH):
            existing = open(MANIFEST_PATH, encoding="utf-8").read()
        if text != existing:
            sys.stderr.write("manifest drift: manifest.json is out of date — run "
                             "`python3 tools/build-manifest.py`\n")
            return 1
        print("manifest up-to-date")
        return 0
    open(MANIFEST_PATH, "w", encoding="utf-8").write(text)
    print("wrote %s" % os.path.relpath(MANIFEST_PATH, REPO_ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
