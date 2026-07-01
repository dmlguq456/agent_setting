"""Render layer — curses 2-section TUI (live) + plain snapshot (--once). PRD §4.

Both paths build the same segment lines ([(text, color_key), ...]); the plain renderer joins
the text (for piping / smoke tests, no ANSI), the curses renderer paints each segment. Missing
cells render as '—' (never blank). Sections: (A) fleet vertical panel stack, (B) dispatch list.
Responsive: 3-line panels when wide, 1-line compact when narrow (tmux side pane).
"""
import curses
import sys
import time

from .model import fmt_min, dash

BADGE = {"claude": "C", "codex": "X", "opencode": "O"}
_BADGE_KEY = {"claude": "badgeC", "codex": "badgeX", "opencode": "badgeO"}
_LIVE_RANK = {"working": 0, "idle": 1, "blocked": 2, "done": 3, "stale": 4, "dead": 5, "unknown": 6}
_EFFORT_KEY = {"low": "dim", "medium": "ok", "high": "warn", "xhigh": "blocked", "max": "dead"}
_WIDE_MIN = 50

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
    spec = {
        "work": curses.COLOR_GREEN, "ok": curses.COLOR_GREEN, "done": curses.COLOR_CYAN,
        "warn": curses.COLOR_YELLOW, "blocked": curses.COLOR_YELLOW,
        "stale": curses.COLOR_RED, "dead": curses.COLOR_RED,
        "badgeC": curses.COLOR_CYAN, "badgeX": curses.COLOR_YELLOW, "badgeO": curses.COLOR_GREEN,
        "head": curses.COLOR_CYAN,
        "pct_g": curses.COLOR_GREEN, "pct_y": curses.COLOR_YELLOW, "pct_r": curses.COLOR_RED,
    }
    n = 1
    for key, fg in spec.items():
        try:
            curses.init_pair(n, fg, bg)
            _COLOR[key] = curses.color_pair(n)
            n += 1
        except Exception:
            _COLOR[key] = 0
    _COLOR["idle"] = curses.A_DIM
    _COLOR["dim"] = curses.A_DIM
    _COLOR["unknown"] = curses.A_DIM


def _attr(key):
    return _COLOR.get(key, 0)


def _live_key(state):
    return {"working": "work", "idle": "idle", "blocked": "blocked", "done": "done",
            "stale": "stale", "dead": "dead"}.get(state, "unknown")


def _pct_key(v):
    if v is None:
        return "dim"
    return "pct_r" if v >= 80 else ("pct_y" if v >= 50 else "pct_g")


# ---------- row builders (return list of segment-lines) ----------
def _session_lines(s, wide):
    badge = BADGE.get(s.harness, "?")
    bkey = _BADGE_KEY.get(s.harness, "head")
    slug = s.slug or (s.cwd.rsplit("/", 1)[-1] if s.cwd else "?")
    live = s.liveness
    lkey = _live_key(live)
    model = dash(s.model)
    ctx = dash(s.ctx_pct, lambda v: "%d%%" % v)
    el = fmt_min(s.elapsed_min)
    if not wide:
        segs = [(badge, bkey), (" " + slug, None), ("  " + live, lkey),
                ("  " + model, "dim")]
        if s.effort:
            segs.append(("·" + s.effort, _EFFORT_KEY.get(s.effort, "dim")))
        segs.append(("  🧠" + ctx, _pct_key(s.ctx_pct)))
        segs.append(("  ⏳" + el, "dim"))
        if s.orphan:
            segs.append(("  ⚠worktree-gone", "dead"))
        return [segs]
    # wide: 3-line panel
    l1 = [(badge + " ", bkey), (slug, None), ("   [" + live + "]", lkey)]
    if s.orphan:
        l1.append(("  ⚠worktree-gone", "dead"))
    l2 = [("  ✨ ", "dim"), (model, None)]
    if s.effort:
        l2.append((" ·" + s.effort, _EFFORT_KEY.get(s.effort, "dim")))
    l2 += [("    🧠 ", "dim"), (ctx, _pct_key(s.ctx_pct))]
    r5 = dash(s.rl_5h, lambda v: "%d%%" % v)
    r7 = dash(s.rl_7d, lambda v: "%d%%" % v)
    cost = dash(s.cost, lambda v: "$%.2f" % v)
    l3 = [("  5h ", "dim"), (r5, _pct_key(s.rl_5h)),
          ("  7d ", "dim"), (r7, _pct_key(s.rl_7d)),
          ("   ", "dim"), (cost, "dim"),
          ("   ⏳", "dim"), (el, "dim")]
    return [l1, l2, l3]


def _job_line(j):
    key = j.key or "?"
    stage = ("▸" + j.stage) if j.stage else ""
    opts = []
    if j.mode:
        opts.append(j.mode)
    if j.qa:
        opts.append(j.qa)
    optstr = ("(" + "·".join(opts) + ")") if opts else ""
    el = fmt_min(j.elapsed_min)
    lkey = _live_key(j.liveness)
    segs = [(key, "head"), (stage, "done")]
    if optstr:
        segs.append((" " + optstr, "dim"))
    segs.append(("  ⏳" + el, "dim"))
    segs.append(("  " + j.liveness, lkey))
    segs.append(("  " + (j.slug or ""), None))
    return segs


# ---------- section assembly ----------
def _sort_sessions(ss):
    return sorted(ss, key=lambda s: (s.harness, _LIVE_RANK.get(s.liveness, 9),
                                     -(s.elapsed_min or 0)))


def _sort_jobs(js):
    return sorted(js, key=lambda j: (_LIVE_RANK.get(j.liveness, 9), -(j.elapsed_min or 0)))


def _counts(items):
    c = {}
    for it in items:
        c[it.liveness] = c.get(it.liveness, 0) + 1
    return c


def _fleet_header(sessions):
    by = {}
    for s in sessions:
        by[s.harness] = by.get(s.harness, 0) + 1
    lc = _counts(sessions)
    hs = " · ".join("%s%d" % (BADGE.get(h, "?"), by[h]) for h in sorted(by)) or "none"
    live = " ".join("%s%d" % (k[0], lc[k]) for k in ("working", "idle", "stale", "dead") if lc.get(k))
    return [("FLEET  ", "head"), (hs, None), ("   " + live, "dim")]


def _dispatch_header(jobs, malformed):
    if not jobs:
        return [("DISPATCH  ", "head"), ("no active dispatch", "dim")]
    tail = "  (%d malformed skipped)" % malformed if malformed else ""
    return [("DISPATCH  ", "head"), ("%d jobs" % len(jobs), None), (tail, "dim")]


_SHOW_ALL = False   # --all: include stale/dead sessions in the fleet list (header counts stay full)


def set_show_all(v):
    global _SHOW_ALL
    _SHOW_ALL = bool(v)


def _build_lines(sessions, jobs, section, wide, malformed):
    """Return a flat list of segment-lines for the whole screen (None = blank line)."""
    lines = []
    if section in ("fleet", "both"):
        lines.append(_fleet_header(sessions))
        lines.append(None)
        # stale/dead are folded away by default (header keeps their count); --all reveals them.
        shown = sessions if _SHOW_ALL else [s for s in sessions if s.liveness not in ("stale", "dead")]
        for s in _sort_sessions(shown):
            lines.extend(_session_lines(s, wide))
            if wide:
                lines.append(None)
        if not sessions:
            lines.append([("  (no active sessions)", "dim")])
        else:
            hidden = len(sessions) - len(shown)
            if hidden:
                lines.append([("  +%d stale/dead hidden (--all)" % hidden, "dim")])
    if section == "both":
        lines.append(None)
    if section in ("dispatch", "both"):
        lines.append(_dispatch_header(jobs, malformed))
        lines.append(None)
        for j in _sort_jobs(jobs):
            lines.append(_job_line(j))
    return lines


# ---------- plain (--once) ----------
def _plain(segs):
    return "" if segs is None else "".join(t for t, _ in segs)


def render_once(collect_all, hfilter, section):
    sessions, jobs = collect_all(harness_filter=hfilter)
    malformed = _malformed()
    lines = _build_lines(sessions, jobs, section, wide=True, malformed=malformed)
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
def _addline(stdscr, row, segs, w):
    if segs is None:
        return
    col = 0
    for text, color in segs:
        if col >= w - 1:
            break
        piece = text[: (w - 1 - col)]
        try:
            stdscr.addstr(row, col, piece, _attr(color))
        except curses.error:
            pass
        col += len(piece)


def _draw(stdscr, sessions, jobs, section, malformed):
    h, w = stdscr.getmaxyx()
    stdscr.erase()
    wide = w >= _WIDE_MIN
    lines = _build_lines(sessions, jobs, section, wide, malformed)
    row = 0
    for segs in lines:
        if row >= h - 1:
            hidden = len(lines) - row
            try:
                stdscr.addstr(h - 1, 0, ("  +%d more (resize / narrower view)" % hidden)[: w - 1],
                              _attr("dim"))
            except curses.error:
                pass
            break
        _addline(stdscr, row, segs, w)
        row += 1
    # footer hint on the last row if space remains
    if row < h:
        try:
            stdscr.addstr(h - 1, 0, "  q quit · r refresh"[: w - 1], _attr("dim"))
        except curses.error:
            pass
    stdscr.noutrefresh()
    curses.doupdate()


def _loop(stdscr, collect_all, hfilter, section, interval):
    curses.curs_set(0)
    _init_colors()
    stdscr.timeout(200)                     # getch blocks ≤200ms → responsive keys
    sessions, jobs = collect_all(harness_filter=hfilter)
    malformed = _malformed()
    last = time.time()
    _draw(stdscr, sessions, jobs, section, malformed)
    while True:
        ch = stdscr.getch()
        if ch in (ord("q"), ord("Q")):
            return 0
        force = ch in (ord("r"), ord("R"))
        now = time.time()
        if force or (now - last) >= interval:
            sessions, jobs = collect_all(harness_filter=hfilter)
            malformed = _malformed()
            last = now
        # redraw every wake (covers KEY_RESIZE and tick)
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
