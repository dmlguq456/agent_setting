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
# effort intensity ramp — low/medium recede, high normal, xhigh/max stand out (subtle "구분감")
_LVL_INT = {"low": curses.A_DIM, "medium": curses.A_DIM, "high": 0,
            "xhigh": curses.A_BOLD, "max": curses.A_BOLD}
# qa rigor ramp (a dispatch job's analogue of effort) — quick recedes, adversarial stands out
_QA_INT = {"quick": curses.A_DIM, "light": curses.A_DIM, "standard": 0,
           "thorough": curses.A_BOLD, "adversarial": curses.A_BOLD}
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
    # model · effort = harness-tinted, subtle (user 2026-07-01: "은은하게라도 구분감").
    # model text = harness hue dim; effort = same hue with an intensity ramp (low→dim … max→bold).
    # capture the PURE hue (before the badge DIM below) so model/effort can vary intensity freely.
    _hue = {h: _COLOR.get("h_" + h, 0) for h in ("claude", "codex", "opencode")}
    for h, hue in _hue.items():
        _COLOR["model_" + h] = hue          # harness-tinted, NORMAL brightness (was dim → too dark)
        for lvl, it in _LVL_INT.items():
            _COLOR["eff_%s_%s" % (h, lvl)] = hue | it
        # bright harness color = a TOP-LEVEL session / account; a dispatch job keeps the DIM
        # harness (h_<h>) → main↔spawned weight is carried by font-color intensity (no bg fill).
        _COLOR["hb_" + h] = hue
    _COLOR["model_other"] = 0
    _COLOR["hb_other"] = 0
    for lvl, it in _LVL_INT.items():
        _COLOR["eff_other_" + lvl] = it
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
    # qa rigor ramp (dispatch tag after the name): quick dim … adversarial bold
    for lvl, it in _QA_INT.items():
        _COLOR["qa_" + lvl] = it
    # stage breadcrumb — each pipeline stage a DISTINCT color (user); the CURRENT stage is BOLD
    # (bright, "눈에 띄는"), past/pending stages the same hue but DIM. Palette cycles by stage index.
    _stage_raw = [_hue.get("opencode", 0), _hue.get("claude", 0), _COLOR.get("green", 0),
                  _COLOR.get("yellow", 0), _hue.get("codex", 0)]  # blue · cyan · green · yellow · magenta
    for i, base in enumerate(_stage_raw):
        _COLOR["stg%d_on" % i] = base | curses.A_BOLD
        _COLOR["stg%d_off" % i] = base | curses.A_DIM
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


def _model_key(harness):
    return "model_" + harness if harness in ("claude", "codex", "opencode") else "model_other"


def _eff_key(harness, effort):
    h = harness if harness in ("claude", "codex", "opencode") else "other"
    lvl = effort if effort in _LVL_INT else "medium"
    return "eff_%s_%s" % (h, lvl)


def _clean_model(name):
    """'Opus 4.8 (1M context)' → 'Opus 4.8' (drop the trailing parenthetical — redundant, ugly when truncated)."""
    return name.split(" (", 1)[0] if name else name


# mid-height bar (━ filled / ─ empty): the glyphs sit at the cell's vertical centre, so gauges on
# adjacent rows keep an above/below gap and never merge into a solid vertical wall (no blank line
# needed). Filled carries the level color; the empty track is dim — the fill reads by color too.
_BAR_FULL, _BAR_EMPTY = "━", "─"


def _gauge_segs(pct, width):
    """Two colored segments — filled ━ (level color) + empty ─ track (dim). Fills exactly `width`."""
    p = max(0, min(100, int(pct or 0)))
    filled = min(width, int(round(p / 100.0 * width)))
    return [(_BAR_FULL * filled, _pct_key(pct)), (_BAR_EMPTY * (width - filled), "dim")]


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


def _gate_info(cwd, sid=None):
    """(gate, pipeline) for a cwd — gate ∈ 'tracked'/'untracked'/None, pipeline = spec/ exists.
    Walks up to the nearest .agent_reports/.claude_reports. untracked if the GLOBAL `.untracked`
    marker exists, or (sid given) this session's `.untracked.<sid>` — per-session tracked mode,
    matching the statusline. pipeline = a `spec/pipeline_state.yaml` under that root (§0 gate).
    Cached per (cwd,sid) per tick."""
    if not cwd:
        return (None, False)
    now = time.time()
    if now - _GATE_CACHE["ts"] > _GATE_TTL:
        _GATE_CACHE.update(ts=now, map={})
    cache = _GATE_CACHE["map"]
    ck = (cwd, sid)
    if ck in cache:
        return cache[ck]
    d = cwd
    result = (None, False)
    for _ in range(40):
        for rd in (".agent_reports", ".claude_reports"):
            base = os.path.join(d, rd)
            if os.path.isdir(base):
                untracked = os.path.exists(os.path.join(base, ".untracked")) or \
                    bool(sid and os.path.exists(os.path.join(base, ".untracked." + sid)))
                pipe = os.path.exists(os.path.join(base, "spec", "pipeline_state.yaml"))
                result = ("untracked" if untracked else "tracked", pipe)
                break
        if result[0] is not None or d in ("/", ""):
            break
        d = os.path.dirname(d)
    cache[ck] = result
    return result


def _project_gate(cwd, sid=None):
    """spec-gate word only ('tracked'/'untracked'/None) — thin wrapper over _gate_info."""
    return _gate_info(cwd, sid)[0]


# ---------- row builders (return a single segment-line: [(text, color_key), ...]) ----------
# Design pass 2026-07-01 (deep) — a dispatch JOB is a session-analogue, not a lesser row: its
# fields map onto the SAME columns as a session's, so the whole board reads with one grammar:
#     column        session            dispatch job
#     harness       ▐reverse badge▌    dim font       ← weight = main vs spawned
#     name          bright             dim
#     model slot    model              process = pipeline·mode   (e.g. code · dev)
#     effort slot   effort (low→max)   qa (quick→adversarial)    ← both are the "intensity" dial
#     gauge slot    context % bar      stage breadcrumb (plan › exec › test)  ← "how far along"
# main↔dispatch weight is carried by the badge (reverse vs dim font), so the identity columns can
# stay aligned for comparison. Job flow never sits under branch/gate.
_HW = 11                      # session harness field — WIDE gap to the name (user widened it)
_BRANCH_COL = 43              # absolute col where branch starts (both row types)
_NAME_COL = 15                # absolute col where the NAME starts — SHARED by both row types so
                              # everything from the name onward aligns (session: prefix 4 + harness
                              # 11; dispatch: prefix 6 + harness 9 — deeper indent, narrower harness)
_NW_S = _BRANCH_COL - _NAME_COL   # name field (both row types): col 15 → branch 43 = 28
_BRW = 14                     # ⎇branch field (always ≥1 trailing space so it never touches model)
_EFF_W = 6                    # effort sub-column (session effort: low..max)
_MW = 16 + _EFF_W             # model + effort field: model 16 + effort 6
_CTX_W = 14                   # context-window gauge width (the metric the user reads most)
_CLOCK = "⏱ "                 # elapsed-time marker before uptime (⏱ = 2 cells, see _WIDE)

# known pipeline stage sequences → the stage breadcrumb (process viz). Unknown keys/stages fall
# back to a single lit stage token (never a fabricated track). Keyed by the dispatch `key`.
_PIPE_STAGES = {
    "code": ["plan", "exec", "test"],
    "review": ["plan", "exec", "test"],
    "spec": ["spec", "design", "dev"],
    "research": ["search", "analyze", "report"],
    "draft": ["draft", "refine", "apply"],
}

# plain-text column labels (icons removed per user — "위에 아이콘들은 전부 빼자")
_COL_HEAD = ("    " + "harness".ljust(_HW) + "session".ljust(_NW_S)
             + "branch".ljust(_BRW) + "model".ljust(_MW - _EFF_W)
             + "effort".ljust(_EFF_W) + "    context / stage")


def _gate_word(gate, pipe):
    """Binary spec-gate vocabulary — EXACTLY the statusline's 📌tracked / ⚡untracked, nothing
    else (a third 'spec' state confused the mental model). `pipe` is accepted but not shown.
      tracked    — under the agent pipeline (no `.untracked` marker)
      untracked  — a `.untracked` marker is set (⚡, /track) — ad-hoc, bypasses the pipeline
    Returns (word, color_key); ('', None) when there is no artifact root at all."""
    if gate == "untracked":
        return "untracked", "gate_u"
    if gate == "tracked":
        return "tracked", "gate_t"
    return "", None


def _gate_tag(gate, pipe):
    """(text, color_key) for the dim gate tag shown after a session name, or ('', None)."""
    word, key = _gate_word(gate, pipe)
    return (" " + word, key) if word else ("", None)


def _branch_seg(cwd, branch):
    """A single dim branch cell (icon removed per user — plain text, ≥1 trailing space)."""
    br = branch or _git_branch(cwd)
    return (_pad((br or "—")[: _BRW - 1], _BRW), "dim")


def _me_segs(harness, left, dial, dial_key, width):
    """The shared 'model+effort' / 'process+qa' cell: a harness-tinted-dim LEFT label + a RIGHT
    'intensity dial' sub-column (effort for sessions, qa for jobs), separated by a plain gap (no
    dot). `dial_key` carries the dial's intensity color. Fills exactly `width`; dial empty → left
    spans the whole width."""
    left = left or "—"
    lkey = _model_key(harness)
    if dial:
        lw = max(1, width - _EFF_W - 1)
        return [(_pad(left[:lw], lw + 1), lkey),
                (_pad(dial[:_EFF_W], _EFF_W), dial_key)]
    return [(_pad(left[: max(1, width - 1)], width), lkey)]


def _stage_segs(key, stage, working=False):
    """Process viz — the pipeline lifecycle as a breadcrumb: each stage a DISTINCT color, the rest
    of the sequence the same hue but DIM. The CURRENT stage is bold/bright and, when the job is
    actively `working`, BLINKS in sync with the working dot (shared `_BLINK_ON`, ~2 Hz) so the eye
    is drawn to where work is happening right now. Unknown pipeline/stage → a single lit token."""
    def _cur_key(i):
        # working → pulse on/off with the dot; idle/other → steady bright
        if working and not _BLINK_ON:
            return "stg%d_off" % (i % 5)
        return "stg%d_on" % (i % 5)
    seq = _PIPE_STAGES.get(key)
    if seq and stage in seq:
        out = []
        for i, st in enumerate(seq):
            if i:
                out.append((" › ", "dim"))
            out.append((st, _cur_key(i) if st == stage else "stg%d_off" % (i % 5)))
        return out
    if stage:
        return [(stage, _cur_key(0))]
    return [("—", "dim")]


def _session_row(s, narrow, is_parent=False, child_count=0):
    live = s.liveness
    slug = s.slug or (s.cwd.rsplit("/", 1)[-1] if s.cwd else "?")
    dim_tel = live in ("stale", "dead") or s.app_server
    name_key = ("name_work" if live == "working"
                else ("name_dim" if dim_tel else "name_idle"))
    gch, gkey = _glyph(live)
    hn = _BADGE_TEXT.get(s.harness, "?")

    # main↔spawned weight = font-color intensity (no bg fill — the reverse badge read as weird):
    # a live top-level session gets the BRIGHT harness color; muted (stale/dead/app-server) drops
    # to dim. Dispatch rows use the DIM harness color (see _dispatch_row).
    hkey = (_BADGE_KEY.get(s.harness, "dim") if dim_tel
            else ("hb_" + s.harness if s.harness in _BADGE_TEXT else "hb_other"))
    segs = [("  ", None), (gch, gkey), (" ", None), (_pad(hn, _HW), hkey)]

    # name zone: slug(focus) + ▾N(dim) + gate tag(dim), padded to the shared branch column.
    used = 0
    slug_show = slug[: min(len(slug), _NW_S - 1)]
    segs.append((slug_show, name_key)); used += len(slug_show)
    if is_parent and child_count and used + 3 <= _NW_S:
        t = " ▾%d" % child_count
        segs.append((t, "dim")); used += len(t)
    if s.gate:
        gate, pipe = s.gate, False
    else:
        gate, pipe = _gate_info(s.cwd, s.session_id)
    gtag, gk = _gate_tag(gate, pipe)
    if gtag and used + len(gtag) <= _NW_S:
        segs.append((gtag, gk)); used += len(gtag)
    if used < _NW_S:
        segs.append((" " * (_NW_S - used), None))

    segs.append(_branch_seg(s.cwd, s.branch))
    segs += _me_segs(s.harness, _clean_model(dash(s.model)), s.effort,
                     _eff_key(s.harness, s.effort), _MW)

    # STATUS-ZONE — ctx gauge (mid-line ━/─, level color); 4-col gap so it reads separate from effort
    if s.ctx_pct is not None and not dim_tel:
        segs += [("    ", None)] + _gauge_segs(s.ctx_pct, _CTX_W) + [(" %3d%%" % s.ctx_pct, _pct_key(s.ctx_pct))]
    else:
        segs += [("    ", None), ("─" * _CTX_W, "dim"), (" %4s" % dash(s.ctx_pct, lambda v: "%d%%" % v), "dim")]
    if s.app_server:
        segs.append(("  app-server", "dim"))
    if s.orphan:
        segs.append(("  worktree-gone", "g_dead"))

    segs.append((_RFLUSH, None))                                     # cost · ⏱uptime flush right
    if not narrow:
        cost = dash(s.cost, lambda v: "$%.2f" % v)
        ck = "cost_hi" if (isinstance(s.cost, (int, float)) and s.cost > 100) else "dim"
        segs += [("%9s" % cost, ck), ("   ", None)]
    segs += [(_CLOCK, "dim"), ("%6s" % fmt_min(s.elapsed_min), "dim")]
    return segs


def _mq_tag(mode, qa_text, qa_key):
    """The `(mode · qa)` tag shown after a dispatch name (mode dim, qa in its rigor color, middle
    dot). Returns (segments, display_width). Empty (mode and qa both absent) → ([], 0)."""
    if not mode and not qa_text:
        return [], 0
    out = [(" (", "dim")]
    w = 2
    if mode:
        out.append((mode, "dim")); w += len(mode)
    if qa_text:
        if mode:
            out.append(("·", "dim")); w += 1        # flush middle dot (tighter than ' · ')
        out.append((qa_text, qa_key)); w += len(qa_text)
    out.append((")", "dim")); w += 1
    return out, w


def _dispatch_row(j, orphan=False, parent_model=None, parent_harness=None, is_last=True):
    """A dispatch job rendered as a session-ANALOGUE, mirroring the session columns 1:1:
      harness  |  name (mode · qa)  |  branch  |  MODEL (the job's real model)  |  stage breadcrumb
    mode+qa ride together in a `(mode · qa)` tag right after the name; the model slot shows the
    job's own main model; the gauge slot is the stage breadcrumb (per-stage colors, current bold,
    blinks while working). Weight vs a session = dim-font harness + ↳ + dim name.
    """
    key = j.key or "?"
    stage = j.stage or ""
    qa_base = j.qa or ""
    qa_text = ""
    if j.qa:
        qa_text = ("~" + j.qa) if j.qa_source in ("jobslog", "plan", "default") else j.qa
    name = j.slug or key
    harness = j.harness or parent_harness
    gch, gkey = _glyph(j.liveness)
    hn = _BADGE_TEXT.get(j.harness, "—") if j.harness else "—"
    qa_key = "qa_" + qa_base if qa_base in _QA_INT else "dim"

    # DIFFERENTIAL indent (harness 2 cols deeper than a session) via a tree connector that branches
    # off the parent's dot column; the harness field is narrowed by 2 so the NAME still lands at the
    # shared _NAME_COL — i.e. everything from the name onward aligns with sessions. DIM = spawned.
    conn = "└─" if is_last else "├─"
    segs = [("  ", None), (conn, "dim"), (gch, gkey), (" ", None),
            (_pad(hn, _HW - 2), _BADGE_KEY.get(j.harness, "dim"))]
    avail = _NW_S
    tag_segs, tagw = _mq_tag(j.mode, qa_text, qa_key)
    otag = "  (orphan)" if orphan else ""
    nm = name[: max(3, avail - tagw - len(otag) - 1)]   # -1 → always ≥1 gap before branch
    used = len(nm)
    segs.append((nm, "name_dim"))
    segs += tag_segs; used += tagw
    if otag and used + len(otag) <= avail:
        segs.append((otag, "gate_u")); used += len(otag)
    if used < avail:
        segs.append((" " * (avail - used), None))

    segs.append(_branch_seg(j.cwd, j.branch))
    # model slot → the job's OWN main model (harness-tinted dim), same cell a session uses.
    segs += _me_segs(harness, _clean_model(dash(j.model or parent_model)), None, None, _MW)

    # gauge slot → stage breadcrumb (process viz): per-stage colors, current bold + blinks if working.
    segs.append(("    ", None))                       # 4-col gap (reads separate from effort/qa)
    segs += _stage_segs(key, stage, working=(j.liveness == "working"))

    segs.append((_RFLUSH, None))
    segs += [(_CLOCK, "dim"), ("%6s" % fmt_min(j.elapsed_min), "dim")]
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
    # account-level usage — shared per harness/account. ONE LINE PER HARNESS (user 2026-07-01:
    # "모든 윈도우가 쭉 붙어있다 → 서로 간격 띄우고 게이지 길게"): long gauges, generous gaps, aligned.
    # rate is account-shared → take the FRESHEST session's value per harness (a stale session's
    # per-file rate is old; e.g. a 16-min-old file showed 7d 100% while the live rate was 15%).
    _rl = {}   # harness -> (rl_5h, rl_7d, mtime)
    for s in sessions:
        if s.rl_5h is not None or s.rl_7d is not None:
            cur = _rl.get(s.harness)
            if cur is None or (s.mtime or 0) > (cur[2] or 0):
                _rl[s.harness] = (s.rl_5h, s.rl_7d, s.mtime)
    if _rl:
        hs = [h for h in ("claude", "codex", "opencode") if h in _rl]
        for idx, h in enumerate(hs):
            r5, r7, _mt = _rl[h]
            row = [("usage  " if idx == 0 else "       ", "head"),
                   (_pad(h, 11), "hb_" + h if h in _BADGE_TEXT else "hb_other")]  # bright = account
            for gi, (lbl, v) in enumerate((("5h ", r5), ("7d ", r7))):
                pctstr = ("%d%%" % v) if v is not None else "—"
                row.append(("     " + lbl if gi else lbl, "dim"))        # wide gap between the 5h/7d windows
                row += _gauge_segs(v, 16) if v is not None else [("·" * 16, "dim")]
                row.append((" %4s" % pctstr, _pct_key(v)))
            lines.append(row)
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
        ggate, gpipe = _gate_info(gcwd)                # project spec-gate (word after the rule)
        gword, gwkey = _gate_word(ggate, gpipe)
        head_segs = [("── ", "head"), ("📁 ", "dim"), ("%s " % name, "head"), (_HFILL, None)]
        if gword:
            head_segs += [("  ", None), (gword, gwkey), (" ──", "head")]
        else:
            head_segs.append(("──", "head"))
        lines.append(head_segs)

        # rows stay tight (no blank line — that spread them too far apart); the mid-line gauge
        # glyph (━/─) is what keeps the stacked context bars from merging into a solid wall.
        for s in _sort_group_sessions(shown):
            kids = _sort_group_jobs(children.get(s.session_id, []))
            lines.append(_session_row(s, narrow, is_parent=bool(kids), child_count=len(kids)))
            for i, cj in enumerate(kids):
                lines.append(_dispatch_row(cj, orphan=False, parent_model=s.model,
                                           parent_harness=s.harness, is_last=(i == len(kids) - 1)))
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
_WIDE = set("🧠✨⏳📁🚀🛰📌⚡📋⚙📊🐛📈🔬💻⏱")


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
        # wake exactly at the next 0.5s blink boundary (regular period) but stay key-responsive (≤200ms)
        _nb = (int(time.time() * 2) + 1) / 2.0
        stdscr.timeout(max(30, min(200, int((_nb - time.time()) * 1000) + 1)))
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
