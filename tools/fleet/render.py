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

_BADGE_TEXT = {"claude": "[Claude]", "codex": "[Codex]", "opencode": "[opencode]"}
_BADGE_KEY = {"claude": "badge_claude", "codex": "badge_codex", "opencode": "badge_opencode"}
_LIVE_RANK = {"working": 0, "idle": 1, "blocked": 2, "done": 3, "stale": 4, "dead": 5, "unknown": 6}
_JOB_LIVE_RANK = {"working": 0, "stale": 1, "dead": 2, "unknown": 3}
_EFFORT_KEY = {"low": "dim", "medium": "ok", "high": "warn", "xhigh": "blocked", "max": "dead"}
_NARROW_CUTOFF = 70
_LOOPS_KEYS = ("oncall", "note", "study", "drill")
# command-center / launch icons (R5) — single source; degrade to ASCII (e.g. "⌘"/"▸") here in
# ONE place if double-width alignment breaks in a target terminal.
_ICON_PARENT = "🛰️"   # command-center: a session that spawned ≥1 child dispatch job
_ICON_CHILD = "🚀"     # launch: a child dispatch job row nested under its parent session

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
        "badge_claude": curses.COLOR_CYAN, "badge_codex": curses.COLOR_MAGENTA,
        "badge_opencode": curses.COLOR_GREEN,
        "head": curses.COLOR_CYAN,
        "pct_g": curses.COLOR_GREEN, "pct_y": curses.COLOR_YELLOW, "pct_r": curses.COLOR_RED,
        # per-model colors so different models are distinguishable at a glance (user 2026-07-01)
        "m_opus": curses.COLOR_MAGENTA, "m_sonnet": curses.COLOR_CYAN, "m_haiku": curses.COLOR_GREEN,
        "m_fable": curses.COLOR_YELLOW, "m_gpt": curses.COLOR_BLUE, "m_glm": curses.COLOR_RED,
    }
    n = 1
    for key, fg in spec.items():
        try:
            curses.init_pair(n, fg, bg)
            _COLOR[key] = curses.color_pair(n)
            n += 1
        except Exception:
            _COLOR[key] = 0
    # badges: bold colored TEXT (no reverse-video background block — the filled span read badly)
    for k in ("badge_claude", "badge_codex", "badge_opencode"):
        _COLOR[k] = _COLOR.get(k, 0) | curses.A_BOLD
    # percentages read at a glance — bold so ctx%/rate% stand out (user: '% 표기가 잘 안보인다')
    for k in ("pct_g", "pct_y", "pct_r", "m_opus", "m_sonnet", "m_haiku", "m_fable", "m_gpt", "m_glm"):
        _COLOR[k] = _COLOR.get(k, 0) | curses.A_BOLD
    _COLOR["model"] = curses.A_BOLD              # default/unknown model name — bold (user: 모델명 더 눈에 띄게)
    # status glyphs pop: working = blinking green ● (live-LED signal), others bold (user: 점멸 신호)
    _COLOR["g_work"] = _COLOR.get("work", 0) | curses.A_BOLD | curses.A_BLINK
    _COLOR["g_idle"] = _COLOR.get("warn", 0) | curses.A_BOLD
    _COLOR["g_stale"] = _COLOR.get("stale", 0) | curses.A_BOLD
    _COLOR["g_dead"] = _COLOR.get("dead", 0) | curses.A_BOLD
    _COLOR["idle"] = curses.A_DIM
    _COLOR["dim"] = curses.A_DIM
    _COLOR["unknown"] = curses.A_DIM


def _attr(key):
    return _COLOR.get(key, 0)


def _live_key(state):
    return {"working": "work", "idle": "idle", "blocked": "blocked", "done": "done",
            "stale": "stale", "dead": "dead"}.get(state, "unknown")


# leading status glyph — the row's primary at-a-glance anchor (working/idle stand out; user 2026-07-01)
_LIVE_GLYPH = {"working": "●", "idle": "○", "blocked": "◑", "done": "✓",
               "stale": "◌", "dead": "✕", "unknown": "·"}
_GLYPH_KEY = {"working": "g_work", "idle": "g_idle", "blocked": "g_idle", "done": "done",
              "stale": "g_stale", "dead": "g_dead", "unknown": "dim"}


def _glyph(state):
    return _LIVE_GLYPH.get(state, "·"), _GLYPH_KEY.get(state, "dim")


def _pct_key(v):
    if v is None:
        return "dim"
    return "pct_r" if v >= 80 else ("pct_y" if v >= 50 else "pct_g")


_MODEL_COLORS = (("opus", "m_opus"), ("sonnet", "m_sonnet"), ("haiku", "m_haiku"),
                 ("fable", "m_fable"), ("gpt", "m_gpt"), ("glm", "m_glm"))


def _model_key(name):
    """Color key by model family substring — different models render in different colors."""
    if not name:
        return "model"
    low = name.lower()
    for sub, key in _MODEL_COLORS:
        if sub in low:
            return key
    return "model"


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
def _session_row(s, narrow, is_parent=False):
    """Single segment-line per session (PRD §4 v2 — the wide 3-line panel is retired).

    Format: `  [Badge] <slug>  ✨<model> ·<effort>  🧠<ctx%>  5h<r>/7d<r>  ⏳<elapsed>  <liveness>`
    app_server codex appends a dim `⚙app-server` marker right after the badge. Dim rule (§6/§7):
    stale/dead/app_server sessions render telemetry segments dim (last-observed, not live) —
    badge/slug/liveness always keep normal coloring. `is_parent=True` (R5, caller-computed —
    this row has ≥1 nested child job) prepends the command-center icon after badge/slug.
    """
    badge = _BADGE_TEXT.get(s.harness, "[?]")
    bkey = _BADGE_KEY.get(s.harness, "head")
    slug = s.slug or (s.cwd.rsplit("/", 1)[-1] if s.cwd else "?")
    live = s.liveness
    lkey = _live_key(live)
    dim_telemetry = live in ("stale", "dead") or s.app_server
    tkey = "dim" if dim_telemetry else None

    # aligned columns — leading is ONLY glyph+badge+name (all fixed/ASCII → clean vertical lines).
    # branch·gate go after the name (padded by display width); parent/markers go to the very end.
    el = fmt_min(s.elapsed_min)
    model = dash(s.model)
    gch, gkey = _glyph(live)

    segs = [("  ", None), (gch, gkey), (" ", None),
            (_pad(badge, 10), bkey), (" ", None),                # whole badge in the harness color (text, not bg)
            (_pad(slug, 18), None)]

    # git branch (⎇) — same info the statusline shows, per session (and per dispatch worktree)
    br = _git_branch(s.cwd)
    br_txt = ("⎇ " + br) if br else ""
    segs += [("  ", None), (br_txt, "warn"), (" " * max(1, 16 - _dw(br_txt)), None)]

    # per-session spec-gate, full label after the name (a tracked repo can host untracked work)
    gate = _project_gate(s.cwd, s.session_id)
    gate_full, gate_c = {"tracked": ("📌 tracked(pipeline)", "work"),
                         "untracked": ("⚡ untracked(ad-hoc)", "warn")}.get(gate, ("", "dim"))
    segs += [(gate_full, gate_c), (" " * max(1, 21 - _dw(gate_full)), None)]

    # model + effort — fixed width so 🧠 aligns (truncate long names like 'Opus 4.8 (1M context)')
    MW = 28
    eff = (" ·" + s.effort) if s.effort else ""
    mtrunc = model[: max(1, MW - len(eff))]
    segs += [("✨", "dim"), (mtrunc, "dim" if dim_telemetry else _model_key(s.model))]
    if eff:
        segs.append((eff, "dim" if dim_telemetry else _EFFORT_KEY.get(s.effort, "dim")))
    segs.append((" " * max(0, MW - len(mtrunc) - len(eff)), None))   # exact MW; separator is the ' 🧠' below

    ctx_str = dash(s.ctx_pct, lambda v: "%d%%" % v)
    if s.ctx_pct is not None and not dim_telemetry:                  # visual context gauge
        segs += [(" 🧠", "dim"), (_bar(s.ctx_pct), _pct_key(s.ctx_pct)), (" %4s" % ctx_str, _pct_key(s.ctx_pct))]
    else:
        segs += [(" 🧠", "dim"), ("░░░░░", "dim"), (" %4s" % ctx_str, "dim")]

    if not narrow:                                                   # rate limit is per-account (top bar), not per row
        segs.append(("  %8s" % dash(s.cost, lambda v: "$%.2f" % v), "dim"))
    segs.append(("  ⏳" + el, "dim"))                                 # liveness shown by leading glyph
    if is_parent:
        segs.append(("  🛰️", None))                                  # orchestrator marker at end (no column shift)
    if s.app_server:
        segs.append(("  ⚙app-server", "dim"))
    if s.orphan:
        segs.append(("  ⚠worktree-gone", "dead"))
    return segs


def _dispatch_row(j, orphan=False, parent_model=None):
    """Single segment-line per dispatch job, nested under its parent session (R1) or
    surfaced as a project-level orphan (`orphan=True`, R2) — same builder, one code path
    so `--section dispatch` degrade (nesting suppressed, sessions absent) stays flat via
    this same function.

    Format: `    └▸🚀<key>▸<stage> (<mode>·~<qa>)  ⏳<elapsed>  <liveness>  <slug>  (orphan)`
    qa is dim + `~`-prefixed when NOT argv-explicit (`j.qa_source` in jobslog/plan/default —
    i.e. inferred, not user-specified); argv-source qa renders normal, no `~`.
    """
    key = j.key or "?"
    stage = ("▸" + j.stage) if j.stage else ""
    qa_text = None
    qa_dim = False
    if j.qa:
        if j.qa_source in ("jobslog", "plan", "default"):
            qa_text = "~" + j.qa
            qa_dim = True
        else:
            qa_text = j.qa
    el = fmt_min(j.elapsed_min)
    lkey = _live_key(j.liveness)
    name = j.slug or key
    gch, gkey = _glyph(j.liveness)                    # leading status glyph, same slot idea as session
    segs = [("    └▸", "dim"), (gch, gkey), (" " + _ICON_CHILD + " ", "dim")]
    if j.harness:                                    # dispatch badge in the harness color too (same as session)
        segs.append((_BADGE_TEXT.get(j.harness, "[?]"), _BADGE_KEY.get(j.harness, "head")))
    segs.append((" " + name, None))                  # name right after badge — same slot as a session's slug (order consistency)
    if key and key != name:                          # pipe key/stage as detail AFTER the name (loops: key==name → skip)
        segs.append(("  " + key, "head"))
    segs.append((stage, "done"))
    if j.mode or qa_text:
        segs.append((" (", "dim"))
        if j.mode:
            segs.append((j.mode, None))
        if j.mode and qa_text:
            segs.append(("·", "dim"))
        if qa_text:
            segs.append((qa_text, "dim" if qa_dim else None))
        segs.append((")", "dim"))
    dmodel = j.model or parent_model                 # own model if resolvable, else parent's (same config for now — per-dispatch later)
    if dmodel:
        segs.append(("  ✨", "dim")); segs.append((dmodel, _model_key(dmodel)))
    br = _git_branch(j.cwd)                           # dispatch worktree branch (wt/branch)
    if br:
        segs.append(("  ⎇ " + br, "warn"))
    segs.append(("  ⏳" + el, "dim"))                 # liveness shown by leading glyph now
    if orphan:
        segs.append(("  (orphan)", "dim"))
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
    # account-level usage bar — rate limits are shared per harness/account, so shown ONCE at the top
    _rl = {}
    for s in sessions:
        if s.harness not in _rl and (s.rl_5h is not None or s.rl_7d is not None):
            _rl[s.harness] = (s.rl_5h, s.rl_7d)
    if _rl:
        bar = [("  usage   ", "head")]
        for h in ("claude", "codex", "opencode"):
            if h in _rl:
                r5, r7 = _rl[h]
                bar += [(_BADGE_TEXT.get(h, h), _BADGE_KEY.get(h, "head")),
                        (" 5h ", "dim"), (dash(r5, lambda v: "%d%%" % v), _pct_key(r5)),
                        ("  7d ", "dim"), (dash(r7, lambda v: "%d%%" % v), _pct_key(r7)),
                        ("      ", None)]
        lines.append(bar)
        lines.append(None)

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
            lines.append([("━━ 📁 %s  (+%d folded)" % (name, len(group_sessions)), "dim")])
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
        gate = _project_gate(gcwd)                     # project spec-gate (word = the explanation)
        head_segs = [("━━ 📁 %s" % name, "head")]      # session count dropped — glyphs carry status
        if gate == "tracked":
            head_segs.append(("  📌 tracked", "work"))
        elif gate == "untracked":
            head_segs.append(("  ⚡ untracked", "warn"))
        lines.append(head_segs)

        for si, s in enumerate(_sort_group_sessions(shown)):
            if si:
                lines.append(None)                  # blank line between sessions (readability — user 2026-07-01)
            has_children = bool(children.get(s.session_id))
            lines.append(_session_row(s, narrow, is_parent=has_children))
            for cj in _sort_group_jobs(children.get(s.session_id, [])):
                lines.append(_dispatch_row(cj, orphan=False, parent_model=s.model))
        if group_sessions and hidden:
            lines.append([("  +%d stale/companion hidden" % hidden, "dim")])

        # orphans: project-level fallback, marker suppressed when nesting is intentionally
        # off (`--section dispatch` — sessions absent, every job would otherwise "orphan").
        for oj in _sort_group_jobs(orphans):
            lines.append(_dispatch_row(oj, orphan=show_sessions))
        for lj in _sort_group_jobs(loops_jobs):
            lines.append(_dispatch_row(lj, orphan=False))

    if not order:
        lines.append([("  (no active sessions or dispatch jobs)", "dim")])

    if malformed:
        lines.append(None)
        lines.append([("  +%d malformed jobs.log rows skipped" % malformed, "dim")])

    # legend — explains the visual encoding
    lines.append(None)
    lines.append([
        ("  ", None), ("●", "g_work"), (" working  ", "dim"),
        ("○", "g_idle"), (" idle  ", "dim"),
        ("◌", "g_stale"), (" stale  ", "dim"),
        ("✕", "g_dead"), (" dead     ", "dim"),
        ("📌", "work"), (" tracked  ", "dim"),
        ("⚡", "warn"), (" untracked     ", "dim"),
        ("🛰️", None), (" orchestrator  ", "dim"),
        ("🚀", None), (" dispatch", "dim"),
    ])

    return lines


# ---------- plain (--once) ----------
def _plain(segs):
    return "" if segs is None else "".join(t for t, _ in segs)


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


def _addline(stdscr, row, segs, w):
    if segs is None:
        return
    col = 0
    for text, color in segs:
        if col >= w - 1:
            break
        avail = w - 1 - col
        piece = ""
        pw = 0
        for ch in text:                                       # clip by display width, not len
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
    global _OFFSET
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
        # redraw every wake (covers KEY_RESIZE and tick) — _draw clamps _OFFSET internally.
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
