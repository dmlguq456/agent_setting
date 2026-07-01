"""Render layer — curses cwd-project-group TUI (live) + plain snapshot (--once). PRD §4 v3.

Both paths build the same flat segment-line list ([(text, color_key), ...] per line, None =
blank line) via `_build_lines` — the plain renderer joins the text (for piping / smoke tests,
no ANSI), the curses renderer paints each segment through a scrollable viewport. Missing cells
render as '—' (never blank). Layout: one group per project (cwd); each session (🛰️ command-center
icon if it spawned children) is followed immediately by its nested `└▸🚀` child dispatch jobs
(joined via `parent_sid`/`CLAUDE_CODE_SESSION_ID`); jobs with no on-screen parent surface as
project-level `(orphan)` rows, cron loop jobs surface flat with no orphan marker, and a group
with no live sessions and no dispatch jobs folds to a single `+N folded` summary (toggle via
`a`/click, same as `+N hidden`). Responsive: narrow (<~70 cols) drops low-priority fields;
badge/slug/liveness never drop.

Module-global state invariants (single-process / single-thread only — no concurrent `_draw`):
  - `_OFFSET` (scroll offset) is READ in exactly ONE place: `_draw` (the viewport slice
    `lines[_OFFSET:_OFFSET+body_h]`). `_build_lines` must NEVER read `_OFFSET` — this is what
    guarantees the plain/`--once` path (which calls `_build_lines` directly) can never drop
    top lines.
  - Resize safety = re-clamp `_OFFSET` against the new `body_h` on every wake via
    `_clamp_offset`, NOT reset. Do NOT reset `_OFFSET` on KEY_RESIZE — that would destroy the
    user's scroll position on every resize.
  - `reset_scroll()` (public, called by fleet.py) sets `_OFFSET=0` — belt-and-suspenders for
    the single-process-per-launch model (a fresh process already starts at 0; only load-bearing
    if `run_live` were ever called twice in one process).
  - `_TOGGLE_ROWS` is reset at the TOP of `_draw`, before any early-return / short-circuit, so a
    stale toggle map never survives to the next click.
"""
import curses
import glob
import os
import sys
import time

from .model import fmt_min, dash, project_of

# harness = dim lowercase word in its identity color (no bracket chip, no reverse-video)
_BADGE_TEXT = {"claude": "claude", "codex": "codex", "opencode": "opencode"}
_BADGE_KEY = {"claude": "h_claude", "codex": "h_codex", "opencode": "h_opencode"}
_LIVE_RANK = {"working": 0, "idle": 1, "blocked": 2, "done": 3, "stale": 4, "dead": 5, "unknown": 6}
_JOB_LIVE_RANK = {"working": 0, "stale": 1, "dead": 2, "unknown": 3}
_EFFORT_KEY = {"low": "dim", "medium": "dim", "high": "dim", "xhigh": "dim", "max": "dim"}  # metadata → dim
_NARROW_CUTOFF = 70
_LOOPS_KEYS = ("oncall", "note", "study", "drill")

_COLOR = {}   # color_key → curses attr (filled by _init_colors); empty ⇒ plain mode


# ---------- color ----------
def _init_colors():
    _COLOR.clear()
    try:
        curses.start_color()
        curses.use_default_colors()
        bg = -1
    except Exception:
        bg = curses.COLOR_BLACK
    # color discipline (design review 2026-07-01): one meaning per color.
    #   green/yellow/red = status + level ONLY · cyan/magenta/blue = harness identity ONLY
    #   white bold = the row's single focal point (session name) · dim = all metadata
    spec = {
        "green": curses.COLOR_GREEN, "yellow": curses.COLOR_YELLOW, "red": curses.COLOR_RED,
        "h_claude": curses.COLOR_CYAN, "h_codex": curses.COLOR_MAGENTA, "h_opencode": curses.COLOR_BLUE,
    }
    n = 1
    for key, fg in spec.items():
        try:
            curses.init_pair(n, fg, bg)
            _COLOR[key] = curses.color_pair(n)
            n += 1
        except Exception:
            _COLOR[key] = 0
    # status dots — working "blinks" via a manual on/off toggle in the loop (A_BLINK is stripped
    # by tmux/herdr, so we animate it ourselves: g_work bright ↔ g_work_off dim each ~500ms)
    _COLOR["g_work"] = _COLOR.get("green", 0) | curses.A_BOLD
    _COLOR["g_work_off"] = _COLOR.get("green", 0) | curses.A_DIM
    _COLOR["g_idle"] = _COLOR.get("yellow", 0)
    _COLOR["g_stale"] = curses.A_DIM
    _COLOR["g_dead"] = _COLOR.get("red", 0) | curses.A_BOLD
    # level bars (ctx / usage): green <50 / yellow <80 / red ≥80 (red bold = alarm)
    _COLOR["lvl_g"] = _COLOR.get("green", 0)
    _COLOR["lvl_y"] = _COLOR.get("yellow", 0)
    _COLOR["lvl_r"] = _COLOR.get("red", 0) | curses.A_BOLD
    # harness identity = dim colored text (color lives ONLY here for identity)
    for h in ("claude", "codex", "opencode"):
        _COLOR["h_" + h] = _COLOR.get("h_" + h, 0) | curses.A_DIM
    # session name = the single focal point per row
    _COLOR["name_work"] = curses.A_BOLD
    _COLOR["name_idle"] = 0
    _COLOR["name_dim"] = curses.A_DIM
    # gate words · cost alarm · structure
    _COLOR["gate_t"] = _COLOR.get("green", 0) | curses.A_DIM
    _COLOR["gate_u"] = _COLOR.get("yellow", 0) | curses.A_DIM
    _COLOR["cost_hi"] = curses.A_BOLD
    _COLOR["dim"] = curses.A_DIM
    _COLOR["head"] = curses.A_DIM
    _COLOR["unknown"] = curses.A_DIM


def _attr(key):
    return _COLOR.get(key, 0)


def _live_key(state):
    return {"working": "g_work", "idle": "g_idle", "stale": "g_stale",
            "dead": "g_dead"}.get(state, "dim")


# monochrome status dot (● working / ○ idle / ◦ stale / × dead) — color carries the meaning
_LIVE_GLYPH = {"working": "●", "idle": "○", "blocked": "◑", "done": "✓",
               "stale": "◦", "dead": "×", "unknown": "·"}
_GLYPH_KEY = {"working": "g_work", "idle": "g_idle", "blocked": "g_idle", "done": "green",
              "stale": "g_stale", "dead": "g_dead", "unknown": "dim"}


_BLINK_ON = True     # manual blink phase for the working dot (toggled ~2 Hz in the live loop)


def _glyph(state):
    key = _GLYPH_KEY.get(state, "dim")
    if state == "working" and not _BLINK_ON:
        key = "g_work_off"
    return _LIVE_GLYPH.get(state, "·"), key


def _pct_key(v):
    if v is None:
        return "dim"
    return "lvl_r" if v >= 80 else ("lvl_y" if v >= 50 else "lvl_g")


def _model_key(name):
    return "dim"   # model is metadata (design review) — muted, no per-model color


def _clean_model(name):
    """'Opus 4.8 (1M context)' → 'Opus 4.8' (drop the trailing parenthetical — redundant, ugly when truncated)."""
    return name.split(" (", 1)[0] if name else name


_BAR_FULL, _BAR_EMPTY = "█", "░"


def _bar(pct, width=5):
    """Compact filled gauge, e.g. 58% width5 → '███░░'. Clamped 0-100."""
    p = max(0, min(100, int(pct or 0)))
    filled = min(width, int(round(p / 100.0 * width)))
    return _BAR_FULL * filled + _BAR_EMPTY * (width - filled)


def _pad(s, w):
    """Pad/truncate ASCII text to exactly w cells (columns align across rows)."""
    s = s or ""
    return s[:w].ljust(w)


_BR_TTL = 15.0
_BR_CACHE = {"ts": 0.0, "map": {}}


def _git_branch(cwd):
    """Current branch for a cwd (⎇ display). None if not a repo. Cached 15s + 2s timeout so the
    per-tick git calls (one per unique cwd) stay cheap and never block the render."""
    if not cwd:
        return None
    now = time.time()
    if now - _BR_CACHE["ts"] > _BR_TTL:
        _BR_CACHE.update(ts=now, map={})
    cache = _BR_CACHE["map"]
    if cwd in cache:
        return cache[cwd]
    br = None
    try:
        import subprocess
        r = subprocess.run(["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
                           capture_output=True, text=True, timeout=2)
        if r.returncode == 0:
            br = r.stdout.strip() or None
    except Exception:
        br = None
    cache[cwd] = br
    return br


_GATE_TTL = 3.0
_GATE_CACHE = {"ts": 0.0, "map": {}}


def _project_gate(cwd, sid=None):
    """spec-gate: 'tracked' / 'untracked' / None (no artifact root). Walks up to the nearest
    .agent_reports/.claude_reports. untracked if the GLOBAL `.untracked` marker exists, or (when
    sid given) this session's `.untracked.<sid>` — so tracked mode is per-session, matching the
    statusline. sid=None → project-level (global marker only). Cached per (cwd,sid) per tick."""
    if not cwd:
        return None
    now = time.time()
    if now - _GATE_CACHE["ts"] > _GATE_TTL:
        _GATE_CACHE.update(ts=now, map={})
    cache = _GATE_CACHE["map"]
    ck = (cwd, sid)
    if ck in cache:
        return cache[ck]
    d = cwd
    result = None
    for _ in range(40):
        for rd in (".agent_reports", ".claude_reports"):
            base = os.path.join(d, rd)
            if os.path.isdir(base):
                untracked = os.path.exists(os.path.join(base, ".untracked")) or \
                    bool(sid and os.path.exists(os.path.join(base, ".untracked." + sid)))
                result = "untracked" if untracked else "tracked"
                break
        if result is not None or d in ("/", ""):
            break
        d = os.path.dirname(d)
    cache[ck] = result
    return result


# ---------- row builders (return a single segment-line: [(text, color_key), ...]) ----------
# column layout (design review 2026-07-01): status dot · harness · NAME(focus) · ▾children ·
# branch · gate · model·effort · ctx-gauge   —— then right-flushed cost · uptime. No cell emoji;
# the column header row labels each field once, color carries the meaning.
_COL_HEAD = ("  " + " " + "  "
             + "harness".ljust(9) + " " + "session".ljust(20) + " " + "".ljust(3) + " "
             + "branch".ljust(9) + "gate".ljust(9) + "model · effort".ljust(23)
             + " context")


def _session_row(s, narrow, is_parent=False, child_count=0):
    live = s.liveness
    slug = s.slug or (s.cwd.rsplit("/", 1)[-1] if s.cwd else "?")
    dim_tel = live in ("stale", "dead") or s.app_server
    name_key = ("name_work" if live == "working"
                else ("name_dim" if dim_tel else "name_idle"))
    gch, gkey = _glyph(live)
    hn = _BADGE_TEXT.get(s.harness, "?")
    hk = _BADGE_KEY.get(s.harness, "dim")
    orch = ("▾%d" % child_count) if (is_parent and child_count) else ""

    segs = [("  ", None), (gch, gkey), ("  ", None),
            (_pad(hn, 9), hk), (" ", None),
            (_pad(slug, 20), name_key), (" ", None),
            (_pad(orch, 3), "dim"), (" ", None)]

    br = s.branch or _git_branch(s.cwd)
    segs.append((_pad((br or "—")[:8], 9), "dim"))

    gate = s.gate or _project_gate(s.cwd, s.session_id)
    gword, gkey2 = {"tracked": ("tracked", "gate_t"), "untracked": ("adhoc", "gate_u")}.get(gate, ("", "dim"))
    segs.append((_pad(gword, 9), gkey2))

    model = _clean_model(dash(s.model))
    MW = 22
    eff = (" · " + s.effort) if s.effort else ""
    me = (model[: max(1, MW - len(eff))] + eff)
    segs.append((_pad(me, MW + 1), "dim"))

    if s.ctx_pct is not None and not dim_tel:                        # ctx gauge — a meaningful color
        segs += [(" ", None), (_bar(s.ctx_pct), _pct_key(s.ctx_pct)), (" %3d%%" % s.ctx_pct, _pct_key(s.ctx_pct))]
    else:
        segs += [(" ", None), ("░░░░░", "dim"), (" %4s" % dash(s.ctx_pct, lambda v: "%d%%" % v), "dim")]
    if s.app_server:
        segs.append(("  app-server", "dim"))
    if s.orphan:
        segs.append(("  worktree-gone", "g_dead"))

    segs.append((_RFLUSH, None))                                     # cost · uptime flush right
    if not narrow:
        cost = dash(s.cost, lambda v: "$%.2f" % v)
        ck = "cost_hi" if (isinstance(s.cost, (int, float)) and s.cost > 100) else "dim"
        segs += [("%9s" % cost, ck), ("  ", None)]
    segs.append(("%7s" % fmt_min(s.elapsed_min), "dim"))
    return segs


def _dispatch_row(j, orphan=False, parent_model=None, is_last=True):
    """A dispatch job nested under its parent session, drawn as a dim tree row:
    `      ├─ ● harness  name  key▸stage  mode·~qa  model  branch  (orphan)   uptime`
    tree line (├─ mid / └─ last) carries 'this is a child'; no launch icon. qa '~' = inferred.
    """
    key = j.key or "?"
    stage = ("▸" + j.stage) if j.stage else ""
    qa_text = ""
    if j.qa:
        qa_text = ("~" + j.qa) if j.qa_source in ("jobslog", "plan", "default") else j.qa
    name = j.slug or key
    gch, gkey = _glyph(j.liveness)
    tree = "└─" if is_last else "├─"

    segs = [("      ", None), (tree + " ", "dim"), (gch, gkey), (" ", None)]
    if j.harness:
        segs.append((_pad(_BADGE_TEXT.get(j.harness, "?"), 9), _BADGE_KEY.get(j.harness, "dim")))
        segs.append((" ", None))
    segs.append((_pad(name, 18), "name_dim" if j.liveness in ("stale", "dead") else "name_idle"))
    segs.append((" ", None))
    segs.append((_pad((key if key != name else "") + stage, 13), "dim"))   # task flow
    opts = (j.mode or "") + ("·" if (j.mode and qa_text) else "") + qa_text
    segs.append((_pad(opts, 15), "dim"))
    dmodel = j.model or parent_model
    segs.append((_pad(_clean_model(dash(dmodel)), 20), "dim"))
    br = j.branch or _git_branch(j.cwd)
    segs.append((_pad((br or "—")[:8], 9), "dim"))
    if orphan:
        segs.append(("(orphan)", "gate_u"))
    segs.append((_RFLUSH, None))
    segs.append(("%7s" % fmt_min(j.elapsed_min), "dim"))
    return segs


# ---------- grouping assembler ----------
def _group_key_session(s):
    return project_of(s.cwd)


def _group_key_job(j):
    # loops jobs (empty cwd, key in the loops vocabulary) always group under "loops" —
    # project_of('') would return '(unknown)', which is wrong for a recognized loop job.
    if not j.cwd and j.key in _LOOPS_KEYS:
        return "loops"
    return project_of(j.cwd)


def _group_sort_key(name, g):
    members_live = [s.liveness for s in g["sessions"]] + [j.liveness for j in g["jobs"]]
    if "working" in members_live:
        activity_rank = 0
    elif "idle" in members_live:
        activity_rank = 1
    else:
        activity_rank = 2
    mtimes = [s.mtime for s in g["sessions"] if s.mtime is not None]
    recency = max(mtimes) if mtimes else None
    # None mtime sorts as oldest (i.e. last) — use a very negative sentinel for the desc sort.
    recency_sort = recency if recency is not None else -1.0
    return (activity_rank, -recency_sort, name)


def _sort_group_sessions(ss):
    return sorted(ss, key=lambda s: (_LIVE_RANK.get(s.liveness, 9), -(s.elapsed_min or 0)))


def _sort_group_jobs(js):
    return sorted(js, key=lambda j: (_JOB_LIVE_RANK.get(j.liveness, 9), -(j.elapsed_min or 0)))


_SHOW_ALL = False   # --all: reveal stale/dead/app_server sessions (folded by default per group)


def set_show_all(v):
    global _SHOW_ALL
    _SHOW_ALL = bool(v)


def _build_lines(sessions, jobs, section, narrow, malformed):
    """Return a flat list of segment-lines for the whole screen (None = blank line).

    Same contract consumed by BOTH `render_once` (plain, full output) and `_draw` (viewport
    slices this same list) — `_OFFSET` must never be read here (see module docstring).
    """
    # headless dispatch children are shown as dispatch rows under their parent — never as
    # top-level sessions (the same headless process would otherwise double-show as session+job).
    sessions = [s for s in sessions if not s.is_child]
    groups = {}
    for s in sessions:
        gk = _group_key_session(s)
        groups.setdefault(gk, {"sessions": [], "jobs": []})["sessions"].append(s)
    for j in jobs:
        gk = _group_key_job(j)
        groups.setdefault(gk, {"sessions": [], "jobs": []})["jobs"].append(j)

    show_sessions = section in ("fleet", "both")
    show_jobs = section in ("dispatch", "both")

    order = sorted(groups.keys(), key=lambda name: _group_sort_key(name, groups[name]))

    lines = []
    # account-level usage bar — shared per harness/account, shown ONCE; harnesses split by │, mini gauges
    # rate is account-shared → take the FRESHEST session's value per harness (a stale session's
    # per-file rate is old; e.g. a 16-min-old file showed 7d 100% while the live rate was 15%)
    _rl = {}   # harness -> (rl_5h, rl_7d, mtime)
    for s in sessions:
        if s.rl_5h is not None or s.rl_7d is not None:
            cur = _rl.get(s.harness)
            if cur is None or (s.mtime or 0) > (cur[2] or 0):
                _rl[s.harness] = (s.rl_5h, s.rl_7d, s.mtime)
    if _rl:
        bar = [(" usage   ", "head")]
        hs = [h for h in ("claude", "codex", "opencode") if h in _rl]
        for i, h in enumerate(hs):
            if i:
                bar.append(("        │        ", "dim"))
            r5, r7, _mt = _rl[h]
            bar.append((_pad(h, 10), _BADGE_KEY.get(h, "dim")))
            for j, (lbl, v) in enumerate((("5h ", r5), ("7d ", r7))):
                pctstr = ("%d%%" % v) if v is not None else "—"
                bar += [("        " + lbl if j else lbl, "dim"),       # wide gap between the 5h and 7d gauges
                        (_bar(v, 8) if v is not None else "········", _pct_key(v)),
                        (" %4s" % pctstr, _pct_key(v))]
        lines.append(bar)
        lines.append(None)
        lines.append([(_COL_HEAD, "head")])            # column labels once → no per-cell emoji needed

    first = True
    for name in order:
        g = groups[name]
        group_sessions = g["sessions"] if show_sessions else []
        group_jobs = g["jobs"] if show_jobs else []
        if not group_sessions and not group_jobs:
            continue    # empty-group suppression per --section: no dangling header

        # group fold decision (R4) — computed BEFORE emitting anything for this group.
        live_sessions = [s for s in group_sessions
                          if s.liveness not in ("stale", "dead") and not s.app_server]
        must_show_jobs = bool(group_jobs)   # conservative: any job present blocks the fold
        fold = (not _SHOW_ALL) and (not live_sessions) and (not must_show_jobs)

        if not first:
            lines.append(None)
        first = False

        if fold:
            lines.append([("── %s  (+%d folded) " % (name, len(group_sessions)), "dim"),
                          ("─" * max(3, 70 - _dw(name) - 14), "dim")])
            continue

        shown = (group_sessions if _SHOW_ALL else
                 [s for s in group_sessions
                  if not (s.liveness in ("stale", "dead") or s.app_server)])
        hidden = len(group_sessions) - len(shown)
        shown_sids = set(s.session_id for s in shown if s.session_id)

        # pre-assemble session -> child-jobs map (R1/R2) before emitting rows.
        children = {}     # session_id -> [jobs] (nested under an on-screen parent)
        orphans = []       # project-level fallback (parent dead/off-screen/no-env)
        loops_jobs = []    # no-parent-is-normal (cron loops) — no orphan marker
        for j in group_jobs:
            if j.is_child and j.parent_sid and j.parent_sid in shown_sids:
                children.setdefault(j.parent_sid, []).append(j)
            elif j.key in _LOOPS_KEYS:
                loops_jobs.append(j)
            else:
                orphans.append(j)

        gcwd = (group_sessions[0].cwd if group_sessions else
                (group_jobs[0].cwd if group_jobs else ""))
        gate = _project_gate(gcwd)                     # project spec-gate (word after the rule)
        gword = {"tracked": "tracked", "untracked": "adhoc"}.get(gate, "")
        head_segs = [("── ", "head"), ("📁 ", "dim"), ("%s " % name, "head"), (_HFILL, None)]
        if gword:
            head_segs += [("  ", None), (gword, "gate_t" if gate == "tracked" else "gate_u"), (" ──", "head")]
        else:
            head_segs.append(("──", "head"))
        lines.append(head_segs)

        for s in _sort_group_sessions(shown):          # sessions tight (no blank between)
            kids = _sort_group_jobs(children.get(s.session_id, []))
            lines.append(_session_row(s, narrow, is_parent=bool(kids), child_count=len(kids)))
            for i, cj in enumerate(kids):
                lines.append(_dispatch_row(cj, orphan=False, parent_model=s.model, is_last=(i == len(kids) - 1)))
            if kids:
                lines.append(None)                     # separate a nested (parent+children) block
        if group_sessions and hidden:
            lines.append([("     +%d stale/companion hidden" % hidden, "dim")])

        # orphans / loops: project-level fallback (standalone tree rows)
        for oj in _sort_group_jobs(orphans):
            lines.append(_dispatch_row(oj, orphan=show_sessions))
        for lj in _sort_group_jobs(loops_jobs):
            lines.append(_dispatch_row(lj, orphan=False))

    if not order:
        lines.append([("  (no active sessions or dispatch jobs)", "dim")])

    if malformed:
        lines.append(None)
        lines.append([("  +%d malformed jobs.log rows skipped" % malformed, "dim")])

    # legend — status dots (columns are labelled by the header row)
    lines.append(None)
    lines.append([
        ("  ", None), ("●", "g_work"), (" working   ", "dim"),
        ("○", "g_idle"), (" idle   ", "dim"),
        ("◦", "g_stale"), (" stale   ", "dim"),
        ("×", "g_dead"), (" dead     ", "dim"),
        ("▾N", "dim"), (" child jobs   ", "dim"),
        ("├─", "dim"), (" dispatch", "dim"),
    ])

    return lines


# ---------- plain (--once) ----------
def _plain(segs):
    if segs is None:
        return ""
    return "".join(("─────" if t == _HFILL else "   ") if _is_fill(t) else t for t, _ in segs)


def render_once(collect_all, hfilter, section):
    sessions, jobs = collect_all(harness_filter=hfilter)
    malformed = _malformed()
    lines = _build_lines(sessions, jobs, section, narrow=False, malformed=malformed)
    out = "\n".join(_plain(l) for l in lines)
    sys.stdout.write(out + "\n")
    return 0


def _malformed():
    try:
        from .collectors import dispatch
        return getattr(dispatch.collect, "last_malformed", 0)
    except Exception:
        return 0


# ---------- curses (live) ----------
# display-width aware clipping — emoji/CJK render 2 cells but len()==1, so advancing col by
# len() drew the next segment 1 col early and overwrote the previous field's last char
# (e.g. the directory name lost a char after the 📁). Count real cells instead.
_WIDE = set("🧠✨⏳📁🚀🛰📌⚡📋⚙📊🐛📈🔬💻")


def _cw(ch):
    o = ord(ch)
    if o == 0xFE0F or 0x200B <= o <= 0x200F or o == 0x2060:   # VS16 / zero-width → 0 cells
        return 0
    if ch in _WIDE:
        return 2
    if (0x1100 <= o <= 0x115F or 0x2E80 <= o <= 0xA4CF or 0xAC00 <= o <= 0xD7A3
            or 0xF900 <= o <= 0xFAFF or 0xFF00 <= o <= 0xFF60 or 0xFFE0 <= o <= 0xFFE6
            or 0x1F000 <= o <= 0x1FAFF):                       # CJK / Hangul / fullwidth / emoji
        return 2
    return 1


def _dw(s):
    return sum(_cw(c) for c in s)


# fill sentinels (3-char \x00<fill>\x00): everything after is right-aligned to the edge; the gap
# is filled with <fill> — space for _RFLUSH (invisible), ─ for _HFILL (a full-width rule).
_RFLUSH = "\x00 \x00"
_HFILL = "\x00─\x00"


def _is_fill(t):
    return len(t) == 3 and t[0] == "\x00" and t[2] == "\x00"


def _addline(stdscr, row, segs, w):
    if segs is None:
        return
    fillch = None
    left, right = segs, []
    for i, (t, _c) in enumerate(segs):
        if _is_fill(t):
            fillch = t[1]
            left, right = segs[:i], segs[i + 1:]
            break

    def _draw(seglist, start):
        col = start
        for text, color in seglist:
            if col >= w - 1:
                break
            avail = w - 1 - col
            piece = ""
            pw = 0
            for ch in text:                                   # clip by display width, not len
                cw = _cw(ch)
                if pw + cw > avail:
                    break
                piece += ch
                pw += cw
            if piece:
                try:
                    stdscr.addstr(row, col, piece, _attr(color))
                except curses.error:
                    pass
            col += pw
        return col

    endcol = _draw(left, 0)
    if right:
        rw = sum(_dw(t) for t, _ in right)
        rcol = max(endcol + (0 if fillch == "─" else 2), w - 1 - rw)
        if fillch == "─" and rcol > endcol:
            _draw([("─" * (rcol - endcol), "head")], endcol)  # fill the gap to make a full-width rule
        _draw(right, rcol)


_OFFSET = 0                 # scroll offset — READ only in _draw (see module docstring)
_TOGGLE_ROWS = {}            # screen_y -> True, reset at the top of every _draw (mouse click map)


def _clamp_offset(off, total, body_h):
    return max(0, min(off, max(0, total - body_h)))


def reset_scroll():
    global _OFFSET
    _OFFSET = 0


def _draw(stdscr, sessions, jobs, section, malformed):
    global _OFFSET, _TOGGLE_ROWS
    _TOGGLE_ROWS = {}    # reset before any early-return so a stale map never survives a click
    h, w = stdscr.getmaxyx()
    stdscr.erase()
    narrow = w < _NARROW_CUTOFF
    lines = _build_lines(sessions, jobs, section, narrow, malformed)
    body_h = max(1, h - 1)   # reserve 1 footer row
    _OFFSET = _clamp_offset(_OFFSET, len(lines), body_h)

    visible = lines[_OFFSET: _OFFSET + body_h]
    row = 0
    for segs in visible:
        _addline(stdscr, row, segs, w)
        if segs is not None and len(segs) == 1 and (
                "hidden" in segs[0][0] or "folded" in segs[0][0]):
            _TOGGLE_ROWS[row] = True
        row += 1

    above = _OFFSET
    below = max(0, len(lines) - body_h - _OFFSET)
    parts = []
    if above:
        parts.append("↑%d" % above)
    if below:
        parts.append("↓%d" % below)
    hint = "q quit · r refresh · a all · ↑↓/jk PgUp/Dn g/G · click +N"
    footer = ("  " + " ".join(parts) + ("  " if parts else "") + hint)
    try:
        stdscr.addstr(h - 1, 0, footer[: w - 1], _attr("dim"))
    except curses.error:
        pass
    stdscr.noutrefresh()
    curses.doupdate()


def _loop(stdscr, collect_all, hfilter, section, interval):
    global _OFFSET, _BLINK_ON
    curses.curs_set(0)
    _init_colors()
    # herdr (HERDR_ENV=1) grabs mouse events itself — enabling curses mouse reporting inside it
    # deadlocks/freezes the pane (user-observed freeze 2026-07-01). Keyboard is the primary path,
    # so skip mouse under herdr; mouse click-toggle stays available in a plain terminal.
    if not os.environ.get("HERDR_ENV"):
        try:
            curses.mousemask(curses.BUTTON1_CLICKED)
        except Exception:
            pass
    stdscr.timeout(200)                     # getch blocks ≤200ms → responsive keys
    sessions, jobs = collect_all(harness_filter=hfilter)
    malformed = _malformed()
    last = time.time()
    _draw(stdscr, sessions, jobs, section, malformed)
    while True:
        ch = stdscr.getch()
        if ch in (ord("q"), ord("Q")):
            return 0
        h, w = stdscr.getmaxyx()
        body_h = max(1, h - 1)
        if ch in (curses.KEY_UP, ord("k")):
            _OFFSET -= 1
        elif ch in (curses.KEY_DOWN, ord("j")):
            _OFFSET += 1
        elif ch == curses.KEY_PPAGE:
            _OFFSET -= body_h
        elif ch == curses.KEY_NPAGE:
            _OFFSET += body_h
        elif ch in (curses.KEY_HOME, ord("g")):
            _OFFSET = 0
        elif ch in (curses.KEY_END, ord("G")):
            _OFFSET = 1 << 30    # clamp in _draw resolves this to maxoff
        elif ch in (ord("a"), ord("A")):
            set_show_all(not _SHOW_ALL)
        elif ch == curses.KEY_MOUSE:
            try:
                _, mx, my, _mz, _bstate = curses.getmouse()
            except Exception:
                my = None
            if my is not None and my in _TOGGLE_ROWS:
                set_show_all(not _SHOW_ALL)
        # KEY_RESIZE: no special handling needed — _draw's clamp re-clamps against the new
        # body_h below; do NOT reset _OFFSET here (would destroy scroll position).

        force = ch in (ord("r"), ord("R"))
        now = time.time()
        if force or (now - last) >= interval:
            sessions, jobs = collect_all(harness_filter=hfilter)
            malformed = _malformed()
            last = now
        _BLINK_ON = (int(now * 2) % 2 == 0)     # ~2 Hz working-dot blink (manual — A_BLINK unreliable)
        # redraw every wake (covers KEY_RESIZE, blink and tick) — _draw clamps _OFFSET internally.
        _draw(stdscr, sessions, jobs, section, malformed)


def run_live(collect_all, hfilter, section, interval):
    if not sys.stdout.isatty():
        sys.stderr.write("fleet: stdout is not a TTY — use --once (snapshot) or --json.\n")
        return 1
    try:
        return curses.wrapper(_loop, collect_all, hfilter, section, interval)
    except KeyboardInterrupt:
        return 0
    except Exception as e:  # pragma: no cover
        sys.stderr.write("fleet: curses failed: %s\n" % e)
        return 1
