#!/usr/bin/env python3
"""Build manifest.json from the Claude adapter projection definitions.

This is an adapter-derived compatibility manifest, not the portable source of
truth. Portable meaning lives in core/, capabilities/, and roles/.

SoT = the adapter definitions themselves:
  - adapters/claude/skills/*/SKILL.md   frontmatter  (name, argument-hint, metadata:{group,fam,modes,blurb})
  - adapters/claude/agents/*.md  frontmatter  (name, model, metadata:{modes,blurb})
  - loops/README.md     "현역" table  + LOOP_LAYER constant
  - adapters/claude/settings.json  Claude adapter hook registration (read-only)
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
import hashlib

try:
    import yaml
except ImportError:
    sys.stderr.write("PyYAML required: pip install pyyaml\n")
    sys.exit(2)

# realpath (not abspath): this script is executed via the collapsed adapter symlink
# (adapters/claude/tools/build-manifest.py -> ../../../tools/build-manifest.py). abspath
# keeps the symlink path, resolving REPO_ROOT to repo/adapters/claude (double-path bug);
# realpath follows the link to the canonical tools/, giving the true repo root either way.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))  # tools/ -> repo root
MANIFEST_PATH = os.path.join(REPO_ROOT, "manifest.json")

# harness-layer-sync HLS-3 (hash-manifest) / HLS-7 (surface 파생). The exemption ledger
# is the single declaration file for adapter shared-layer exceptions (like GSD's
# gsd-file-manifest.json + FIELD_CLASSIFICATION: one row = one decision). delta rows bind
# a canonical raw-byte sha256 baseline; the guard reds when live canonical drifts from it.
EXEMPTIONS_PATH = os.path.join(REPO_ROOT, "tools", "adaptation-exemptions.tsv")
SHARED_LAYERS = ("hooks", "utilities", "tools")

# Fixed provenance string — NO date/timestamp (idempotency invariant).
GENERATED_FROM = ("Claude adapter projection definitions "
                  "(adapters/claude/skills/*/SKILL.md, adapters/claude/agents/*.md, loops/README.md, adapters/claude/settings.json)")

# hard_block allowlist = PreToolUse guards only (consumer attempt1 §2.4 / Claude adapter hook settings
# PreToolUse). herdr-agent-state is also registered on PreToolUse but is a state-marker,
# NOT a guard -> hard_block stays false for it.
GUARDS = {"artifact-guard", "git-state-guard", "spec-skill-gate", "core-first-guard", "builtin-memory-guard"}

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


# ---------------------------------------------------------------------------
# harness-layer-sync HLS-3 / HLS-7 — adaptation shared-layer surface + delta hash-manifest
#
# GSD-grounded (bin/install.js fileHash L7718 / saveLocalPatches L8057): baseline binding
# is a raw-byte sha256 of the CANONICAL file, and drift = live-hash != recorded-baseline.
# We keep only that half of GSD's model (the guard reds on drift → human re-derives the
# delta), dropping gsd-local-patches/reapply 3-way merge: our delta set is 2 internally
# owned files, not consumed upstream, so automatic patch replay is overkill.
# ---------------------------------------------------------------------------
def _sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _read_exemptions():
    """Parse tools/adaptation-exemptions.tsv -> list of dicts. Comment/blank lines skipped.
    Fields: adapter_path, class(wrapper|delta), rationale, delta_baseline."""
    rows = []
    if not os.path.exists(EXEMPTIONS_PATH):
        return rows
    with open(EXEMPTIONS_PATH, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            cells = line.rstrip("\n").split("\t")
            if len(cells) < 2:
                continue
            rows.append({
                "adapter_path": cells[0],
                "class": cells[1],
                "rationale": cells[2] if len(cells) > 2 else "",
                "delta_baseline": cells[3] if len(cells) > 3 else "-",
            })
    return rows


def _canonical_for(adapter_path):
    """adapters/claude/<layer>/<name> -> <layer>/<name> (canonical top-level path)."""
    m = re.match(r"^adapters/claude/(hooks|utilities|tools)/(.+)$", adapter_path)
    if not m:
        return None
    return "%s/%s" % (m.group(1), m.group(2))


def delta_baselines():
    """For each delta exemption, the canonical path + its live raw-byte sha256.
    Used by --sync-baselines (write) and --check (verify)."""
    out = []
    for row in _read_exemptions():
        if row["class"] != "delta":
            continue
        canonical = _canonical_for(row["adapter_path"])
        if not canonical:
            continue
        canonical_abs = os.path.join(REPO_ROOT, canonical)
        live = _sha256(canonical_abs) if os.path.exists(canonical_abs) else None
        out.append({
            "adapter_path": row["adapter_path"],
            "canonical": canonical,
            "recorded": row["delta_baseline"],
            "live": live,
        })
    return out


def sync_baselines():
    """Rewrite the delta_baseline (4th) column of each delta row with the live canonical
    sha256. Idempotent: byte-identical output when nothing changed. Returns changed count."""
    if not os.path.exists(EXEMPTIONS_PATH):
        sys.stderr.write("no exemptions file at %s\n" % EXEMPTIONS_PATH)
        return 0
    live_by_path = {b["adapter_path"]: b["live"] for b in delta_baselines()}
    changed = 0
    lines = open(EXEMPTIONS_PATH, encoding="utf-8").read().split("\n")
    for i, line in enumerate(lines):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        cells = line.split("\t")
        if len(cells) < 2 or cells[1] != "delta":
            continue
        want = live_by_path.get(cells[0])
        if not want:
            continue
        while len(cells) < 4:
            cells.append("-")
        if cells[3] != want:
            cells[3] = want
            lines[i] = "\t".join(cells)
            changed += 1
    open(EXEMPTIONS_PATH, "w", encoding="utf-8").write("\n".join(lines))
    return changed


def check_baselines():
    """Return (ok, messages). ok=False if any delta baseline is unset/invalid/drifted."""
    ok = True
    msgs = []
    for b in delta_baselines():
        rec = b["recorded"]
        if b["live"] is None:
            ok = False
            msgs.append("delta baseline: canonical %s is missing" % b["canonical"])
            continue
        if not re.fullmatch(r"[0-9a-f]{64}", rec or ""):
            ok = False
            msgs.append("delta baseline unset/invalid for %s (expected sha256 of %s = %s; run --sync-baselines)"
                        % (b["adapter_path"], b["canonical"], b["live"]))
            continue
        if rec != b["live"]:
            ok = False
            msgs.append("delta baseline DRIFT for %s: canonical %s now %s but ledger records %s "
                        "(canonical changed — re-derive the delta patch, then --sync-baselines)"
                        % (b["adapter_path"], b["canonical"], b["live"], rec))
    return ok, msgs


def _layer_files(layer):
    """Top-level (non-directory) canonical files under <layer>/, sorted. __pycache__ excluded."""
    d = os.path.join(REPO_ROOT, layer)
    if not os.path.isdir(d):
        return []
    return sorted(
        f for f in os.listdir(d)
        if os.path.isfile(os.path.join(d, f)) and not f.endswith((".pyc", ".pyo"))
    )


def adaptation_surface(kind):
    """Filesystem-derived surface sets (HLS-7 — replaces hardcoded enumerations).
      codex-hooks     : adapters/codex/hooks/*.py native bridge basenames
      shared-canonical: '<layer>/<name>\t<class>' for every top-level shared file
    """
    if kind == "codex-hooks":
        d = os.path.join(REPO_ROOT, "adapters", "codex", "hooks")
        if not os.path.isdir(d):
            return []
        return sorted(f for f in os.listdir(d) if f.endswith(".py"))
    if kind == "shared-canonical":
        cls_by_path = {r["adapter_path"]: r["class"] for r in _read_exemptions()}
        rows = []
        for layer in SHARED_LAYERS:
            for name in _layer_files(layer):
                adapter_path = "adapters/claude/%s/%s" % (layer, name)
                rows.append("%s/%s\t%s" % (layer, name, cls_by_path.get(adapter_path, "collapsed")))
        return rows
    sys.stderr.write("unknown adaptation-surface kind: %s\n" % kind)
    sys.exit(2)


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
    # HLS-7: filesystem-derived surface sets consumed by check-adaptation-boundary.sh.
    if "--adaptation-surface" in argv:
        i = argv.index("--adaptation-surface")
        kind = argv[i + 1] if i + 1 < len(argv) else ""
        for line in adaptation_surface(kind):
            print(line)
        return 0
    # HLS-3: regenerate delta baselines (canonical raw-byte sha256) into the exemption ledger.
    if "--sync-baselines" in argv:
        n = sync_baselines()
        print("synced %d delta baseline(s) in %s" % (n, os.path.relpath(EXEMPTIONS_PATH, REPO_ROOT)))
        return 0

    check = "--check" in argv
    text = render(build_manifest())
    if check:
        rc = 0
        existing = ""
        if os.path.exists(MANIFEST_PATH):
            existing = open(MANIFEST_PATH, encoding="utf-8").read()
        if text != existing:
            sys.stderr.write("manifest drift: manifest.json is out of date — run "
                             "`python3 tools/build-manifest.py`\n")
            rc = 1
        # HLS-3: --check is the single drill/CI entry point — also verify delta baselines.
        ok, msgs = check_baselines()
        for m in msgs:
            sys.stderr.write(m + "\n")
        if not ok:
            rc = 1
        if rc == 0:
            print("manifest up-to-date; delta baselines bound")
        return rc
    open(MANIFEST_PATH, "w", encoding="utf-8").write(text)
    print("wrote %s" % os.path.relpath(MANIFEST_PATH, REPO_ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
