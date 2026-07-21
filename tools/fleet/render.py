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
try:
    import curses
except ImportError:  # native Windows without windows-curses: plain --once / --json still work
    curses = None
import glob
import os
import re
import sys
import time

from .model import fmt_min, dash, project_of

# curses attribute constants — real values when curses is present, harmless 0 fallbacks
# otherwise, so this module imports (and the plain --once path runs) with no curses at all.
# The live TUI (run_live) still requires curses and guards for its absence explicitly.
_A_BOLD = getattr(curses, "A_BOLD", 0)
_A_DIM = getattr(curses, "A_DIM", 0)

# harness = dim lowercase word in its identity color (no bracket chip, no reverse-video)
_BADGE_TEXT = {"claude": "claude code", "codex": "codex", "opencode": "opencode"}
_BADGE_KEY = {"claude": "h_claude", "codex": "h_codex", "opencode": "h_opencode"}
_LIVE_RANK = {"working": 0, "idle": 1, "blocked": 2, "done": 3, "stale": 4, "dead": 5, "unknown": 6}
_JOB_LIVE_RANK = {"working": 0, "queued": 1, "stale": 2, "dead": 3, "unknown": 4}
# effort → 2-char suffix after the model (design review r2: the effort column repeated 'xhigh'
# everywhere and burned a column; a dim suffix keeps the info without the noise)
# qa rigor ramp (a dispatch job's analogue of effort) — quick recedes, adversarial stands out
_QA_INT = {"quick": _A_DIM, "light": _A_DIM, "standard": 0,
           "thorough": _A_BOLD, "adversarial": _A_BOLD}
_NARROW_CUTOFF = 70
_TWO_LINE_CUTOFF = 138     # width below which sessions render as 2-line cards (F-15a P0-3: the
                           # wide 1-line grid now needs room for the options column too, so the
                           # dead-zone between the old 110 cutoff and wide's real ~138-col need
                           # is gone — 2-line cards are the PRIMARY layout, wide 1-line is rare)
_LAYOUT = "auto"            # 'auto' (width decides) | 'wide' | 'narrow' | 'stack' — `w` key cycles
_LOOPS_KEYS = ("oncall", "note", "study", "drill")
_ALERT_TAIL = re.compile(r"-\d{8,}-\d+$")   # loop job `<case>-<ts>-<pid>` tail (F-10 alert humanize)


def _cycle_layout():
    global _LAYOUT
    _LAYOUT = {"auto": "wide", "wide": "narrow", "narrow": "stack", "stack": "auto"}[_LAYOUT]


def _layout_mode(w):
    """wide (1-line grid) / narrow (2-line cards) / stack (ultra-narrow, fields stacked
    vertically. Auto lets the terminal width decide.
    F-15a P0-3: <70 stack · <138 narrow (2-line, the PRIMARY layout — most real terminals are
    ≤120 cols) · ≥138 wide (1-line, needs room for the options column too)."""
    if _LAYOUT != "auto":
        return _LAYOUT
    if w < _NARROW_CUTOFF:
        return "stack"
    if w < _TWO_LINE_CUTOFF:
        return "narrow"
    return "wide"

_COLOR = {}   # color_key → curses attr (filled by _init_colors); empty ⇒ plain mode
_TINT_OK = False   # 256-color tint pairs initialized (round-5 panels); False ⇒ rail+gap fallback
_TINT_PAIR = {}    # (tint_char, hue_char) → curses attr — the (fg, tint_bg) composed pairs

# fg color_key → (hue, attr) decomposition (spec §5.2) — the basis for composing (fg, tint_bg)
# pairs. hue: d=default g=green y=yellow r=red c=cyan m=magenta l=blue. Keys absent here render
# as default-hue plain text under tint (safe degradation).
_A_B, _A_D = _A_BOLD, _A_DIM
_HUE_OF = {
    None: ("d", 0), "dim": ("d", _A_D), "head": ("d", _A_D), "unknown": ("d", _A_D),
    "name_work": ("d", _A_B), "name_idle": ("d", _A_B), "name_dim": ("d", _A_D),
    "grp": ("d", _A_B), "branch_s": ("d", 0), "cost_hi": ("d", _A_B),
    "qa_quick": ("d", _A_D), "qa_light": ("d", _A_D), "qa_standard": ("d", 0),
    "qa_thorough": ("d", _A_B), "qa_adversarial": ("d", _A_B),
    "g_work": ("g", _A_B), "g_work_off": ("g", _A_D), "g_idle": ("y", 0),
    "g_stale": ("d", _A_D), "g_dead": ("r", _A_B), "g_unused": ("y", _A_D),
    # Badge text, NOT the glyph: plain yellow, distinct from the dim g_unused glyph so the
    # ●>○>◌ ink-weight gradient still reads.
    "g_unused_b": ("y", 0),
    "lvl_g": ("g", 0), "lvl_y": ("y", 0), "lvl_r": ("r", _A_B),
    "grp_live": ("g", 0), "grp_hot": ("g", _A_B), "gate_t": ("g", _A_D), "gate_u": ("y", _A_D),
    "grp_cool": ("y", _A_D), "grp_cold": ("d", _A_D),   # Cooling is dim yellow; cold is dim grey.
    "eff_low": ("d", _A_D), "eff_medium": ("d", 0), "eff_high": ("l", 0),
    "eff_xhigh": ("m", _A_B), "eff_max": ("r", _A_B),
    "effd_low": ("d", _A_D), "effd_medium": ("d", _A_D), "effd_high": ("l", _A_D),
    "effd_xhigh": ("m", _A_D), "effd_max": ("r", _A_D),
    "h_claude": ("c", _A_D), "h_codex": ("m", _A_D), "h_opencode": ("l", _A_D),
    "hb_claude": ("c", 0), "hb_codex": ("m", 0), "hb_opencode": ("l", 0), "hb_other": ("d", 0),
    "fam_opus": ("c", 0), "fam_sonnet": ("l", 0), "fam_haiku": ("g", 0),
    "fam_fable": ("m", 0), "fam_gpt": ("y", 0), "fam_other": ("d", 0),
    "famd_opus": ("c", _A_D), "famd_sonnet": ("l", _A_D), "famd_haiku": ("g", _A_D),
    "famd_fable": ("m", _A_D), "famd_gpt": ("y", _A_D), "famd_other": ("d", _A_D),
    # stage palette indices 0-4 = blue·cyan·green·yellow·magenta (see _stage_raw)
    "stg0_on": ("l", _A_B), "stg1_on": ("c", _A_B), "stg2_on": ("g", _A_B),
    "stg3_on": ("y", _A_B), "stg4_on": ("m", _A_B),
    "stg0_off": ("l", _A_D), "stg1_off": ("c", _A_D), "stg2_off": ("g", _A_D),
    "stg3_off": ("y", _A_D), "stg4_off": ("m", _A_D),
}


def _key_attr(key, tint=None):
    """Attr for a color_key, composed with the row's tint background when active (spec §5.3)."""
    if tint is None or not _TINT_OK:
        return _COLOR.get(key, 0)
    hue, attr = _HUE_OF.get(key, ("d", 0))
    pair = _TINT_PAIR.get((tint, hue))
    if pair is None:
        return _COLOR.get(key, 0)
    return pair | attr


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
    # unused (F-26): dim yellow — distinct from idle's dim GREEN (live-but-quiet) and from
    # stale's colorless dim. The shape carries the meaning on its own; color only reinforces.
    _COLOR["g_unused"] = _COLOR.get("yellow", 0) | curses.A_DIM
    _COLOR["g_unused_b"] = _COLOR.get("yellow", 0)
    # level bars (ctx / usage): green <50 / yellow <80 / red ≥80 (red bold = alarm)
    _COLOR["lvl_g"] = _COLOR.get("green", 0)
    _COLOR["lvl_y"] = _COLOR.get("yellow", 0)
    _COLOR["lvl_r"] = _COLOR.get("red", 0) | curses.A_BOLD
    # per-MODEL family colors, in TWO intensities (2026-07-02: main↔dispatch contrast = whole-row
    # brightness): fam_* = BRIGHT (main session rows) / famd_* = DIM (dispatch rows recede).
    _hue = {h: _COLOR.get("h_" + h, 0) for h in ("claude", "codex", "opencode")}
    _fam = {"opus": curses.COLOR_CYAN, "sonnet": curses.COLOR_BLUE, "haiku": curses.COLOR_GREEN,
            "fable": curses.COLOR_MAGENTA, "gpt": curses.COLOR_YELLOW}
    n_pair = 10                                     # pairs 1-9 reserved above; families from 10
    for fam, fg in _fam.items():
        try:
            curses.init_pair(n_pair, fg, bg)
            hue = curses.color_pair(n_pair)
            n_pair += 1
        except Exception:
            hue = 0
        _COLOR["fam_" + fam] = hue
        _COLOR["famd_" + fam] = hue | curses.A_DIM
    _COLOR["fam_other"] = 0                        # unknown family → default fg
    _COLOR["famd_other"] = curses.A_DIM
    # branch: normal on main session rows, dim on dispatch rows (same brightness axis)
    _COLOR["branch_s"] = 0
    for h, hue in _hue.items():
        # bright harness color = a TOP-LEVEL session / account; a dispatch job keeps the DIM
        # harness (h_<h>) → main↔spawned weight is carried by font-color intensity (no bg fill).
        _COLOR["hb_" + h] = hue
    _COLOR["hb_other"] = 0
    _COLOR["grp"] = curses.A_BOLD      # group (directory) card title
    _COLOR["grp_live"] = _COLOR.get("green", 0)
    _COLOR["grp_hot"] = _COLOR.get("green", 0) | curses.A_BOLD   # active card title (working)
    _COLOR["grp_cool"] = _COLOR.get("yellow", 0) | curses.A_DIM  # Cooling indicator, name, and elapsed time.
    _COLOR["grp_cold"] = curses.A_DIM                            # Cold inactive group: grey ring.
    # harness identity = dim colored text (color lives ONLY here for identity)
    for h in ("claude", "codex", "opencode"):
        _COLOR["h_" + h] = _COLOR.get("h_" + h, 0) | curses.A_DIM
    # session name = THE left pillar of every row (design r2): bright bold for any live session —
    # the eye lands here first; only stale/dead recede. working is distinguished by its dot blink.
    _COLOR["name_work"] = curses.A_BOLD
    _COLOR["name_idle"] = curses.A_BOLD
    _COLOR["name_dim"] = curses.A_DIM
    # gate words · cost alarm · structure
    _COLOR["gate_t"] = _COLOR.get("green", 0) | curses.A_DIM
    _COLOR["gate_u"] = _COLOR.get("yellow", 0) | curses.A_DIM
    _COLOR["cost_hi"] = curses.A_BOLD
    # qa rigor ramp (dispatch tag after the name): quick dim … adversarial bold
    for lvl, it in _QA_INT.items():
        _COLOR["qa_" + lvl] = it
    # Effort ramp v3: avoid excess yellow while distinguishing high and xhigh.
    # low/medium = no hue (weight only) < high = BLUE < xhigh = MAGENTA (bold) < max = RED
    # (bold, the one true alarm — unchanged). No yellow anywhere in the ramp.
    _COLOR["eff_low"] = curses.A_DIM
    _COLOR["eff_medium"] = 0
    _COLOR["eff_high"] = _COLOR.get("h_opencode", 0) & ~curses.A_DIM   # plain blue
    _COLOR["eff_xhigh"] = (_COLOR.get("h_codex", 0) & ~curses.A_DIM) | curses.A_BOLD  # bold magenta
    _COLOR["eff_max"] = _COLOR.get("red", 0) | curses.A_BOLD
    # dispatch-row effort: the SAME hue ramp at dim weight (user 2026-07-20: 분사 행에도
    # 컬러 — a flat grey effort read as part of the grey subtitle). Bold is stripped so a
    # dim row never carries a bolder cell than its parent session's.
    for _e in ("low", "medium", "high", "xhigh", "max"):
        _COLOR["effd_" + _e] = (_COLOR.get("eff_" + _e, 0) & ~curses.A_BOLD) | curses.A_DIM
    # htop chrome: the one background pair on screen — black on
    # WHITE full-width bars wrapping the board (column-header bar + footer key bar). htop's CYAN
    # looked dated, so use neutral white.
    # Structural, one-shot — NOT a per-item classification color, so the fg color-axis budget
    # The no-rainbow-noise rule remains; keycaps use bold because dim vanishes on the bar.
    try:
        curses.init_pair(15, curses.COLOR_BLACK, curses.COLOR_WHITE)
        _COLOR["hdr_bar"] = curses.color_pair(15)
    except Exception:
        _COLOR["hdr_bar"] = curses.A_REVERSE
    _COLOR["hdr_key"] = _COLOR["hdr_bar"] | curses.A_BOLD
    # F-27 warning bar: the SAME structural bar as hdr_bar, in red. It exists because a footer
    # warning must still BE a bar — reusing the body glyph role `g_dead` for a footer head made
    # the row fail _addline's bar test, so the two warning prompts lost their band and rendered
    # as a red-text/black-tail fragment while the benign prompt got a clean full-width bar. That
    # inverts the hierarchy the double-confirm ladder depends on: the live-session prompt must
    # read as MORE serious, not like a render glitch.
    try:
        curses.init_pair(17, curses.COLOR_WHITE, curses.COLOR_RED)
        _COLOR["hdr_warn"] = curses.color_pair(17) | curses.A_BOLD
    except Exception:
        _COLOR["hdr_warn"] = curses.A_REVERSE | curses.A_BOLD
    # The one key the user must press, advertised on top of the red bar.
    _COLOR["hdr_warn_key"] = _COLOR["hdr_warn"] | curses.A_REVERSE
    # bar BLANKS are drawn as white-fg █ blocks on the DEFAULT bg (pair 16), not as bg-colored
    # spaces: ncurses collapses blank runs into ECH/EL erase sequences, and on terminals without
    # working BCE the erased cells come out BLACK — the bar broke between words and after the
    # text. A block glyph is a real character, so it is
    # physically written every time and looks identical to a white background cell.
    try:
        curses.init_pair(16, curses.COLOR_WHITE, bg)
        _COLOR["hdr_blk"] = curses.color_pair(16)
    except Exception:
        _COLOR["hdr_blk"] = 0
    # Subtle panel tints in 256-color mode: seven hues by tint level.
    # text keeps its fg INSIDE a tinted band. Greyscale-only backgrounds — no new fg axis.
    # Failure of any init → _TINT_OK False → rail+gap fallback (spec §4, zero regression).
    global _TINT_OK
    _TINT_OK = False
    _TINT_PAIR.clear()
    try:
        if curses.COLORS >= 256:
            # deepen the midnight-blue active tint (~#0c0f30) where the terminal honors palette
            # redefinition; ignored → stock 17 (#00005f), already subtle (user's terminal was
            # shown to ignore init_color — the green attempt stayed bright, hence the hue move).
            try:
                if curses.can_change_color():
                    # Approximately #0e0f21: dark, desaturated, near-grey midnight blue.
                    curses.init_color(17, 55, 60, 130)
                    # Cooling background is dark brown; stock 94 is the fallback.
                    curses.init_color(94, 120, 75, 38)
            except Exception:
                pass
            hues = {"d": -1, "g": curses.COLOR_GREEN, "y": curses.COLOR_YELLOW,
                    "r": curses.COLOR_RED, "c": curses.COLOR_CYAN,
                    "m": curses.COLOR_MAGENTA, "l": curses.COLOR_BLUE}
            n_pair = 20
            for tch, lvl in _TINT_LVL.items():
                for hch, fg in hues.items():
                    curses.init_pair(n_pair, fg, lvl)
                    _TINT_PAIR[(tch, hch)] = curses.color_pair(n_pair)
                    n_pair += 1
            _TINT_OK = True
    except Exception:
        _TINT_OK = False
        _TINT_PAIR.clear()
    # stage breadcrumb — each pipeline stage a DISTINCT color (user); the CURRENT stage is BOLD
    # Bright current stages stand out; past and pending stages use the same hue dimmed.
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
    return {"working": "g_work", "idle": "g_work_off", "unused": "g_unused",
            "stale": "g_stale", "dead": "g_dead"}.get(state, "dim")


# status dot — SHAPE+SIZE gradient (design r2, a11y): the less active the state, the smaller
# the glyph. Working uses a bright green spinner; live idle/detached use the same dim-green
# loading axis; stale/dead recede to grey/red. Readable without color.
# F-26 `unused` = ◌ (U+25CC DOTTED CIRCLE). Shape gradient reads ● (filled) > ○ (ring) >
# ◌ (dotted ring = never filled), which is exactly the "started but never prompted" meaning.
# ○ was NOT available: _DETACHED_GLYPH already owns it, and detached (attach axis) vs unused
# (activity-history axis) are unrelated — separating them by color alone would break the
# "Readable without color" contract this table is built on.
_LIVE_GLYPH = {"working": "●", "idle": "●", "unused": "◌", "blocked": "◑", "done": "✓",
               "stale": "·", "dead": "✕", "queued": "◦", "unknown": "·"}
_DETACHED_GLYPH = "○"   # Ring means no attached client; idle uses a filled dim-green dot.
_GLYPH_KEY = {"working": "g_work", "idle": "g_work_off", "unused": "g_unused",
              "blocked": "g_idle", "done": "green",
              "stale": "g_stale", "dead": "g_dead", "queued": "dim", "unknown": "dim"}

# group "cooling" state (user 2026-07-03): a directory with NO active work whose newest session
# A recent transcript write reads as cooling after completion, between hot
# (green ● + green-bold title) and cold (no glyph). It gets a grey ring + time-since-last-activity
# in the header, so a just-finished repo says "done & waiting", not fully dormant. Tune freely.
_COOL_WINDOW_MIN = 180
# Shape-size gradient: recent active states are larger and filled; cold groups use a ring.
_COOL_FILLED = "●"      # Recently completed directory within the cooling window.
_COOL_RING = "○"        # Long-inactive directory.
_COOL_TIME_ICON = "✓"   # Prefix for elapsed time since completion.


_BLINK_ON = True     # manual blink phase (toggled ~2 Hz in the live loop) — drives the spinner too
_SPIN = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"   # braille loading spinner — working SESSIONS animate (user 2026-07-03);
                     # the blinking green ● moved up to the directory title


def _glyph(state, dim=False):
    """Session/job status glyph. working = braille spinner frame — BRIGHT green for a main
    session, dim green for a dispatch job so main and dispatch spinners differ.
    idle = dim-green FILLED ●, detached = dim-green ring ○."""
    if state == "working":
        return _SPIN[int(time.time() * 10) % len(_SPIN)], ("g_work_off" if dim else "g_work")
    return _LIVE_GLYPH.get(state, "·"), _GLYPH_KEY.get(state, "dim")


def _pct_key(v):
    if v is None:
        return "dim"
    return "lvl_r" if v >= 80 else ("lvl_y" if v >= 50 else "lvl_g")


_FAMILIES = ("opus", "sonnet", "haiku", "fable", "gpt")


def _model_family(model):
    """Model-family token from a model/bucket name: 'Opus 4.8'→opus, 'gpt-5.5'→gpt, 'fable'→fable.
    Unknown (glm/deepseek/…) → 'other' (default fg — distinct from the colored families)."""
    m = (model or "").lower()
    for fam in _FAMILIES:
        if fam in m:
            return fam
    return "other"


def _model_key(model, dim=False):
    return ("famd_" if dim else "fam_") + _model_family(model)


# bare model-ROLE tokens (dispatch env exports the portable role, not a concrete model id) →
# proper-noun display. Family word only — never a fabricated version number (the env doesn't
# say WHICH opus the harness resolved).
_ROLE_MODEL_NAME = {"opus": "Opus", "sonnet": "Sonnet", "haiku": "Haiku", "fable": "Fable"}


def _clean_model(name):
    """'Opus 4.8 (1M context)' → 'Opus 4.8' (drop the trailing parenthetical — redundant, ugly
    when truncated); bare role tokens 'opus'/'sonnet' → 'Opus'/'Sonnet' (user 2026-07-20)."""
    if not name:
        return name
    name = name.split(" (", 1)[0]
    return _ROLE_MODEL_NAME.get(name.lower(), name)


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


def _wt_count(cwd):
    """Linked-worktree count for the repo owning `cwd` — counted from .git/worktrees/ entries
    (pure filesystem, no subprocess; follows a worktree's `gitdir:` file back to the main repo).
    Surface leftover or parallel worktrees with no live session."""
    d = cwd
    for _ in range(30):
        g = os.path.join(d, ".git")
        if os.path.isdir(g):
            base = g
            break
        if os.path.isfile(g):
            try:
                with open(g) as f:
                    gd = f.read().split("gitdir:", 1)[1].strip()
            except Exception:
                return 0
            base = gd.split("/worktrees/")[0] if "/worktrees/" in gd else gd
            break
        nd = os.path.dirname(d)
        if nd == d:
            return 0
        d = nd
    else:
        return 0
    try:
        return len([n for n in os.listdir(os.path.join(base, "worktrees")) if not n.startswith(".")])
    except OSError:
        return 0


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
_HW = 16                      # Bare harness-badge width — narrow/stack L1 badges and the
                              # dispatch-prefix budget math still use this unmerged value.
_HMW = 32                     # F-33 (v11, 사용자 확정 2026-07-16): WIDE-layout harness field with
                              # model/effort folded in as a parenthetical ('claude code (Fable 5
                              # · xhigh)') — replaces the separate model column (_MW) on the wide
                              # session/dispatch rows only; narrow/stack keep _HW plus their own
                              # L2 model cell, unchanged.
_NAME_COL = 4 + _HMW          # absolute col where the NAME starts on a WIDE row — SHARED by both
                              # row types so everything from the name onward aligns (session:
                              # prefix 4 + harness-model _HMW; dispatch: prefix 6 + harness-model
                              # narrowed by 2 — deeper indent, same total).
_NW_S = 28                    # wide-layout name field width (both row types) — a fixed constant
                              # (previously derived from a hardcoded branch column) so growing
                              # _NAME_COL above for the harness/model merge never shrinks it.
_NAME2_MAX = 40               # 2-line name zone tail-cut cap (display cells) — no fixed branch
                              # column there, so an unbounded title could push branch off-draw (F-14)
_NAME_GAP = 1                 # Cells inside the name zone reserved as a guaranteed separator
                              # before the branch column. Without it a name+suffix that exactly
                              # fills the zone renders as "trackedmain" — the padding below only
                              # fires on `used < avail`. Latent pre-v8 (a 77-cell zone was rarely
                              # filled); the 40-cell cap makes filling it the common case.
_NAME_WIDE_MAX = 40           # F-22 minor (v8): FIXED upper bound for the wide-layout name zone.
                              # Adjust here and nowhere else. Without it the zone absorbed ALL
                              # remaining slack (measured: 168 cols → 77, 200 → 109), which
                              # stretched the name so far that branch/model/context drifted out
                              # of comfortable scan range. Slack past this cap is NOT
                              # redistributed to other columns — it stays as end-of-row padding.
_TITLE_MAX = 24               # Legacy/fallback title budget and F-15 dispatch-name cap.
                              # F-22 session rows expand beyond this only when terminal width
                              # is known; dispatch labels stay compact inside the wider column.
_OPTW = 18                    # F-15a options column width (dim mode·qa·profile token, sits
                              # between the model cell and the stage breadcrumb — declutters
                              # the name zone, which used to carry this as a parenthetical tag)
_BRW = 14                     # ⎇branch field (always ≥1 trailing space so it never touches model)
_MW = 23                      # model cell: name + FULL effort word ('Opus 4.8 xhigh' — no abbrev)
_EFW = 7                      # effort subfield ("medium"=6 +1 gap) — FIXED width so every row's
                              # effort lands in the same column, under its own 'effort' header
_CTX_W = 24                   # context gauge (kept wide; 16→24 2026-07-15 user: 진행이 안 보임)
_CLOCK = ""                   # Bare elapsed value; icons caused width and readability issues.

# known pipeline stage sequences → the stage breadcrumb (process viz). Unknown keys/stages fall
# back to a single lit stage token (never a fabricated track). Keyed by the dispatch `key`.
_PIPE_STAGES = {
    "code": ["plan", "exec", "test"],
    "review": ["plan", "exec", "test"],
    "spec": ["spec", "design", "dev"],
    "research": ["search", "analyze", "report"],
    "draft": ["draft", "refine", "apply"],
}

# dispatch-depth-2 stage worker role → human stage label (SD-F1). Code workers use their sub-skill
# names; other pipelines use the portable `stage-<name>` role emitted by dispatch. The label
# also drives the parent conductor's active breadcrumb via _conductor_stage_override().
_STAGE_ROLE = {
    "code-plan": "plan",
    "code-execute": "exec",
    "code-test": "test",
    "code-report": "report",
    "stage-search": "search",
    "stage-analyze": "analyze",
    "stage-report": "report",
}


def _stage_role_label(worker_role):
    """(base_label, suffix) for a dispatch-depth-2 stage worker_role, e.g. 'stage-search:phase-A' ->
    ('search', ':phase-A'). base_label is None when worker_role isn't a known stage sub-skill —
    callers fall back to the existing _ROLE_SHORT/_compact_dispatch_name path."""
    if not worker_role:
        return None, ""
    base, _sep, suffix = worker_role.partition(":")
    label = _STAGE_ROLE.get(base)
    if label is None:
        return None, ""
    return label, (":" + suffix if suffix else "")

# Plain-text column labels without decorative icons.
# 'effort' gets its OWN header over the fixed subcolumn inside the model cell (user 2026-07-02).
_STAGE_RESERVE = 20           # trailing room for the dispatch stage breadcrumb after the
                              # options column (plan✓ › exec › test = 19 + gap) — without this
                              # the name column absorbs all slack and the breadcrumb clips at
                              # the panel edge (user 2026-07-15: 분사 세션 단계가 잘림).
                              # 22→20 (2026-07-20): the redundant 'code: ' prefix left the
                              # breadcrumb (entry skill leads the options column now), so the
                              # freed cells flow to the name/ctx slack ledger.


def _wide_slack(term_width):
    """Terminal slack available to the wide-layout name column past its fixed
    columns and framing, or None when `term_width` is unknown (hermetic callers).
    Shared by `_wide_name_width` and `_wide_ctx_width` below so the fixed_row/
    framing reservation is computed in exactly one place (user 2026-07-16: the
    ctx-gauge width ask reuses the same reservation math F-22's name-cap already
    established, rather than duplicating it)."""
    if not term_width:
        return None
    # F-33 (v11): no more separate model column (_MW) — model/effort now ride inside
    # _NAME_COL's harness-model field (_HMW), so the column merge's freed width flows
    # straight into this reservation and out to the name/ctx-gauge slack below.
    fixed_row = _NAME_COL + _BRW + 4 + _CTX_W + 5 + _STAGE_RESERVE
    if _TINT_OK:
        framing = (_INSET + _PAD_IN) + _INSET + (2 + _PAD_IN) + 6 + 2
    else:
        framing = 1 + 6 + 2
    return int(term_width) - fixed_row - framing


_CTX_BOOST = 12               # (user 2026-07-20: "context를 좀 더 꽉차게 확장") — the FIRST
                              # cells of wide-layout slack past the base name column widen the
                              # ctx gauge, BEFORE the name starts growing toward its F-22 cap.
                              # At a 160-col terminal this puts the gauge at 36 instead of 30.


def _wide_alloc(term_width):
    """(name_width, ctx_width) for the wide layout — ONE slack ledger for both
    columns, so their budgets can never double-spend the same cells. Priority
    (user 2026-07-20): gauge boost (_CTX_BOOST) → name growth to _NAME_WIDE_MAX
    (F-22) → everything past the cap back to the gauge (user 2026-07-16: right
    edges keep lining up per width, no blank padding before the time column)."""
    raw = _wide_slack(term_width)
    if raw is None:
        return _NW_S, _CTX_W
    surplus = max(0, raw - _NW_S)
    boost = min(_CTX_BOOST, surplus)
    grow = min(_NAME_WIDE_MAX - _NW_S, surplus - boost)
    return _NW_S + grow, _CTX_W + boost + (surplus - boost - grow)


def _wide_name_width(term_width):
    """Responsive wide-layout name column, between _NW_S and _NAME_WIDE_MAX
    (F-22 minor, v8) — see `_wide_alloc` for the slack priority."""
    return _wide_alloc(term_width)[0]


def _wide_ctx_width(term_width):
    """Wide-layout ctx-gauge width — see `_wide_alloc` for the slack priority."""
    return _wide_alloc(term_width)[1]


def _col_head(name_width):
    # F-33 (v11): the model/effort header folds into the harness column now that the row
    # content does too — no more separate "model" header between branch and the gauge.
    return ("    " + "harness (model·effort)".ljust(_HMW) + "session".ljust(name_width)
            + "branch".ljust(_BRW)
            + "    context / stage")


def _branch_seg(cwd, branch, dim=True):
    """A single branch cell — normal brightness on main session rows, dim on dispatch rows."""
    br = branch or _git_branch(cwd)
    return (_pad((br or "—")[: _BRW - 1], _BRW), "dim" if dim else "branch_s")


def _eff_key(effort, dim):
    """Effort heat ramp: low and medium recede,
    high = blue, xhigh = bold magenta, max = bold red. Dim rows (dispatch/stale) keep the
    ramp's HUE at dim weight (user 2026-07-20: 분사 행에도 컬러 — flat grey read as subtitle)."""
    known = effort in ("low", "medium", "high", "xhigh", "max")
    if dim:
        return ("effd_" + effort) if known else "dim"
    return ("eff_" + effort) if known else None


# 2-char effort forms — the F-9(c) middle rung in `_harness_model_cell`'s fit ladder: a
# narrowed dispatch cell shortens the effort word before it would ever clip the model name
# (user 2026-07-20: 'Opus 4.'/'Sonn' 잘림 대신 풀네임).
_EFF_SHORT = {"low": "lo", "medium": "md", "high": "hi", "xhigh": "xh", "max": "mx"}


def _model_cell(model, effort, width, dim=False):
    """Render model and effort together as one flowing phrase, padded to width."""
    name = _clean_model(dash(model)) or "—"
    sfx = effort or ""
    lkey = _model_key(model, dim=dim)
    if sfx:
        name = name[: max(1, width - len(sfx) - 4)]
        pad = max(0, width - len(name) - len(sfx) - 3)
        return [(name, lkey), (" (" + sfx + ")", _eff_key(sfx, dim)), (" " * pad, None)]
    return [(_pad(name[: width - 1], width), lkey)]


def _harness_model_cell(harness, model, effort, width, hkey, dim=False, unknown="?"):
    """F-33 (v11, 사용자 확정 2026-07-16) — WIDE-layout harness field with model/effort folded
    in as a parenthetical: 'claude code (Fable 5·xhigh)'. The harness text keeps its
    existing hb_*/h_* badge color (`hkey`); the parenthetical reuses `_model_cell`'s
    family/effort colors and the flush '·' stays dim (user 2026-07-16: the spaced
    ' · ' read too wide — the freed cells go to the model name). No model value ->
    the parenthetical is omitted entirely (honest gap, F-3), matching a dead/stale row that
    has no live telemetry to show. Always returns segments summing to exactly `width` cells
    (long names/ids clip the same way `_model_cell` already did, never overflow) — the last
    cell is always left as guaranteed padding so a maxed-out clip never runs the closing `)`
    straight into the name column (the `_NAME_GAP` collision, same idiom, new spot)."""
    hn = _BADGE_TEXT.get(harness, unknown) if harness else unknown
    segs = [(hn, hkey)]
    used = len(hn)
    name = _clean_model(dash(model)) if model else None
    if name and name != "—":
        room = width - used - 4          # " (" prefix + trailing ")" + 1 guaranteed gap
        # F-9(c) fit ladder (user 2026-07-20: 'Opus 4.'/'Sonn' mid-word clips) — the FULL
        # model name outranks the effort word: effort shortens to its 2-char form, then
        # drops whole, before the model name loses a single character. Color keys stay
        # keyed by the full effort value even when the short form is shown.
        eff_full = effort or ""
        eff = eff_full
        if eff and room < len(name) + 1 + len(eff):
            eff = _EFF_SHORT.get(eff_full, eff_full)
        if eff and room < len(name) + 1 + len(eff):
            eff = ""
        if eff:
            segs += [(" (", "dim"), (name, _model_key(model, dim=dim)),
                     ("·", "dim"), (eff, _eff_key(eff_full, dim)), (")", "dim")]
            used += 2 + len(name) + 1 + len(eff) + 1
        elif room > 0:
            nm = name[: max(1, room)]
            segs += [(" (", "dim"), (nm, _model_key(model, dim=dim)), (")", "dim")]
            used += 2 + len(nm) + 1
    if used < width:
        segs.append((" " * (width - used), None))
    return segs


_STAGE_ZONE_MAX = 30          # D3 (v9) — one constant, one place, same idiom as
                               # _NAME_WIDE_MAX(:523)/_DISPATCH_NAME_MAX(:887)/_PROFILE_MAX(:944).
                               # 168-col zero-overflow was previously incidental (a measured
                               # 5-cell slack, not a bound): a longer conductor/qa label or a
                               # further-along stage re-broke it. Widest real row since the
                               # dispatch-depth-1 entry-skill prefix moved to the options dial
                               # (2026-07-20) is a prefixed dispatch-depth-2 stage worker
                               # ("exec: plan✓ › exec › test" = 25) — 30 keeps headroom
                               # without regressing anything currently on screen.


def _drop_past_stages(items, cur_i, max_width):
    """SD-F2 (prd.md:164) — a breadcrumb's information value is "where now", not "where
    I've been": fold PAST stages (i < cur_i) first, earliest first, so the active stage (and
    anything after it) survives longest. Whole-component drop (a stage + its separator, F-9(c)
    idiom) — never a mid-token tail-cut."""
    items = list(items)
    def width():
        w = sum(_dw(t) for _i, t, _k in items)
        return w + max(0, len(items) - 1) * 3   # " › " separators, _dw == 3
    while width() > max_width and items and items[0][0] < cur_i:
        items = items[1:]
    return items


def _route_stage_segs(route_seq, working, max_width):
    """F-28b route-aware breadcrumb (prd.md:303). `route_seq` = [(node_id, state), ...] in the
    route's own DAG order (flattened level order — route.py's `view["nodes"]` is already in
    that order, one entry per node). `state` comes from `route.py`'s §3.3 single judge
    (active/done/failed/pending) — this function ONLY renders what was already decided
    (SD-F2: node lit-ness is the child's live evidence, never re-derived here)."""
    def _cur_key(i):
        if working and not _BLINK_ON:
            return "stg%d_off" % (i % 5)
        return "stg%d_on" % (i % 5)
    cur_i = next((i for i, (_nid, st) in enumerate(route_seq) if st == "active"), None)
    if cur_i is None:
        done_idx = [i for i, (_nid, st) in enumerate(route_seq) if st == "done"]
        cur_i = min((done_idx[-1] + 1) if done_idx else 0, max(0, len(route_seq) - 1))
    items = []
    for i, (nid, st) in enumerate(route_seq):
        if st == "failed":
            items.append((i, nid + "✕", "lvl_r"))
        elif st == "done":
            items.append((i, nid + "✓", "stg%d_off" % (i % 5)))
        elif st == "active":
            items.append((i, nid, _cur_key(i)))
        else:
            items.append((i, nid, "stg%d_off" % (i % 5)))
    if max_width is not None:
        items = _drop_past_stages(items, cur_i, max_width)
    out = []
    for n, (_i, label, key_) in enumerate(items):
        if n:
            out.append((" › ", "dim"))
        out.append((label, key_))
    return out


def _stage_segs(key, stage, working=False, max_width=None, route_seq=None):
    """Process viz — the pipeline lifecycle as a breadcrumb: each stage a DISTINCT color, the rest
    of the sequence the same hue but DIM. The CURRENT stage is bold/bright and, when the job is
    actively `working`, BLINKS in sync with the working dot (shared `_BLINK_ON`, ~2 Hz) so the eye
    is drawn to where work is happening right now. Unknown pipeline/stage → a single lit token.

    `max_width` (D3, v9): when given and the full breadcrumb would exceed it, past stages fold
    via `_drop_past_stages` before anything is emitted — the cap lives in the assembly, not as
    a post-hoc truncation, so a dropped stage never leaves a half-drawn ✓ or separator.

    `route_seq` (F-28b, v10): when given (a resolved route's node list — see
    `_route_stage_segs`), it REPLACES `_PIPE_STAGES.get(key)` entirely — record-derived nodes,
    not the hardcoded 3-stage table. `None` (the default) is the entire pre-v10 behavior,
    unchanged (prd.md:303 — record-less jobs keep the existing breadcrumb)."""
    if route_seq is not None:
        return _route_stage_segs(route_seq, working, max_width)

    def _cur_key(i):
        # working → pulse on/off with the dot; idle/other → steady bright
        if working and not _BLINK_ON:
            return "stg%d_off" % (i % 5)
        return "stg%d_on" % (i % 5)
    seq = _PIPE_STAGES.get(key)
    if seq and stage in seq:
        cur_i = seq.index(stage)
        items = []
        for i, st in enumerate(seq):
            # P1-5: a stage BEFORE the current one is done — a bright ✓ marker makes the
            # "past stages are folded into this breadcrumb" contract visible (F-15b).
            label = st + ("✓" if i < cur_i else "")
            items.append((i, label, _cur_key(i) if st == stage else "stg%d_off" % (i % 5)))
        if max_width is not None:
            items = _drop_past_stages(items, cur_i, max_width)
        out = []
        for n, (_i, label, key_) in enumerate(items):
            if n:
                out.append((" › ", "dim"))
            out.append((label, key_))
        return out
    if seq and stage in ("", key, "open", "running"):
        # pre-plan boot (live_stage fell back to the argv key) / registry-only rows: show the
        # WHOLE track unlit — the breadcrumb is visible from the first tick and lights up
        # left→right (plan › exec › test) as plans/ artifacts appear. (user 2026-07-02:
        # Preserve the concrete plan → exec › test sequence.)
        # A leading `pre` token carries the BOOT-PHASE liveness (user 2026-07-20: "plan 전에
        # 이게 죽었나 살았나") — it blinks like any current stage while the classifier says
        # working, sits dim while queued/stale, and leaves the track the moment `plan`
        # lights. The evidence is F-25's existing verdict; this is display only.
        pre_key = ("stg0_on" if _BLINK_ON else "stg0_off") if working else "stg0_off"
        out = [("pre", pre_key), (" › ", "dim")]
        for i, st in enumerate(seq):
            if i:
                out.append((" › ", "dim"))
            out.append((st, "stg%d_off" % (i % 5)))
        return out
    if stage:
        # F-11: no known pipeline track for this key (seq is None) — jobs.log raw status vocab
        # ("open"/"running") shouldn't leak onto the board as-is. "open" humanizes to "queued";
        # "running" (no track to light up) renders dim rather than as a bright lit token that
        # would misleadingly imply an active named stage. jobs.log status vocabulary itself is
        # unchanged — display layer only.
        if stage == "open":
            return [("queued", _cur_key(0))]
        if stage == "running":
            return [("running", "stg0_off")]
        return [(stage, _cur_key(0))]
    return [("—", "dim")]


def _dispatch_stage_segs(j, key, stage, slug_name, working=False, route_seq=None):
    depth = max(1, int(getattr(j, "depth", 1) or 1))
    intensity = getattr(j, "intensity", None) or ""
    if depth == 1 and intensity == "quick":
        return [("quick/exec", "stg0_on" if working and _BLINK_ON else "stg0_off")]
    if depth >= 2:
        # P0-1: a dispatch-depth-2 stage worker never repeats its parent conductor's full
        # breadcrumb — its identity already rode the name zone (label above); this slot
        # is its own micro-status only. route_seq is a dispatch-depth-1 CONDUCTOR concern only —
        # never consulted here, unconditionally (F-28b plan §4.2, unchanged from pre-v10).
        if j.liveness == "working":
            return [("running", "stg0_on" if _BLINK_ON else "stg0_off")]
        if stage and stage not in ("open", "running"):
            return [(stage, "stg0_off")]
        return []
    if route_seq:
        # F-28b (v10): a resolved route replaces the whole breadcrumb — record nodes are the
        # real pipeline shape, not a role-label prefix over the hardcoded 3-stage table.
        return _stage_segs(key, stage, working=working, max_width=_STAGE_ZONE_MAX,
                           route_seq=route_seq)
    if key and key != slug_name and not _entry_skill(j):
        # SD-F1: a dispatch-depth-2 stage worker's `key` IS its capability (code-plan/code-execute/
        # code-test/code-report) — reuse _stage_role_label (same helper the F-13 legend
        # uses) to humanize it instead of leaking the raw capability token onto the board.
        # When `_entry_skill` already leads the options column with this very token (user
        # 2026-07-20: "code가 표시가 되어있는데"), the prefix is a same-row duplicate — skip.
        role_label, role_suffix = _stage_role_label(key)
        prefix_text = (role_label + role_suffix) if role_label else key
        prefix_seg = (prefix_text + ": ", "name_dim")
        body = _stage_segs(key, stage, working=working,
                           max_width=max(0, _STAGE_ZONE_MAX - _dw(prefix_seg[0])))
        segs = [prefix_seg] + body
        if sum(_dw(t) for t, _k in segs) > _STAGE_ZONE_MAX:
            # F-9(c): past stages already folded as far as they can (SD-F2 keeps the active
            # stage) — the next whole component to drop is the role-label prefix itself.
            return body
        return segs
    return _stage_segs(key, stage, working=working, max_width=_STAGE_ZONE_MAX)


def _stage_zone_segs(bc):
    """Stage-zone lead-in (user 2026-07-20: "stages 앞에 콜론 등으로 구분감") — a dim ' : '
    separates the breadcrumb from the options dial. The leading space is load-bearing: a
    dial that overflows _OPTW leaves no pad, and a flush colon would read as the dial's own
    label ('layer2: pre'). Skipped when the breadcrumb already opens with its own
    'label: ' prefix (SD-F1 rows) — a second colon would stutter — and on an empty
    breadcrumb, where a dangling colon would mark nothing."""
    if not bc:
        return bc
    lead_text, lead_key = bc[0]
    own_prefix = lead_key == "name_dim" and lead_text.endswith(": ")
    return ([("  ", None)] if own_prefix else [(" : ", "dim")]) + bc


def _session_name(s):
    """The session name chain, made explicit (F-26): AI/sidecar title → registry name → slug
    → cwd basename. `registry_name` is a real link in this chain, not decoration: a session
    that has never been prompted has no title, and without the registry name it would render
    as an anonymous cwd basename — which is exactly how the ghost session hid."""
    slug = s.slug or (s.cwd.rsplit("/", 1)[-1] if s.cwd else "?")
    return s.title or getattr(s, "registry_name", None) or slug


def _unused_badge(s, compact=False):
    """`unused <age>` — F-26's first-class signal (prd.md:248). Says the session was started
    and never prompted, and for how long it has sat that way. Age comes from the process, not
    the registry clock (the registry's updatedAt froze at startup — that IS the finding).

    compact drops the age. Two of F-26's requirements collide on a tight row: the badge is
    specified as `unused <경과>` (prd.md:248) but prd.md:247 also demands no anonymous rows,
    and the badge is what starves the name. The age is the recoverable half — every layout
    already carries elapsed time in its own time cell — so it yields first, and only when the
    name would otherwise be clipped."""
    if compact:
        return " unused"
    return " unused %s" % fmt_min(s.elapsed_min if s.elapsed_min is not None else None)


def _session_row(s, narrow, is_parent=False, child_count=0, name_width=None, ctx_width=None):
    live = s.liveness
    slug = s.slug or (s.cwd.rsplit("/", 1)[-1] if s.cwd else "?")
    dim_tel = live in ("stale", "dead") or s.app_server or s.detached
    dead_stale = live in ("stale", "dead")   # F-13: telemetry gone, replaced with a single age cell
    name_key = ("name_work" if live == "working"
                else ("name_dim" if dim_tel else "name_idle"))
    gch, gkey = _glyph(live)
    if s.detached and live not in ("stale", "dead"):
        gch, gkey = _DETACHED_GLYPH, "g_work_off"   # detached: loading axis, dim-green
    # main↔spawned weight = font-color intensity (no bg fill — the reverse badge read as weird):
    # a live top-level session gets the BRIGHT harness color; muted (stale/dead/app-server) drops
    # to dim. Dispatch rows use the DIM harness color (see _dispatch_row).
    hkey = (_BADGE_KEY.get(s.harness, "dim") if dim_tel
            else ("hb_" + s.harness if s.harness in _BADGE_TEXT else "hb_other"))
    # F-33 (v11): harness field carries model/effort as a parenthetical — a dead/stale row has
    # no live telemetry to show (F-13), so it renders the bare harness name only.
    segs = [("  ", None), (gch, gkey), (" ", None)]
    segs += _harness_model_cell(s.harness, None if dead_stale else s.model,
                                None if dead_stale else s.effort, _HMW, hkey, dim=dim_tel)

    # F-22: reserve identity suffixes first, then let the title consume the
    # responsive name column. Calls without a terminal-derived width retain the
    # legacy 24-cell cap for hermetic/backward-compatible row construction.
    avail = max(3, name_width or _NW_S)
    name_txt = _session_name(s)
    suffix = []
    suffix_w = 0
    if is_parent and child_count:
        child_tag = " ▾%d" % child_count
        if _dw(child_tag) < avail:
            suffix.append((child_tag, "dim"))
            suffix_w += _dw(child_tag)
    # F-26: the unused badge outranks the provenance tag — it is the whole reason the
    # row is surfaced, so it is the last identity tag to drop, not the first.
    unused_at = None
    if live == "unused":
        ub = _unused_badge(s)
        if suffix_w + _dw(ub) < avail:
            unused_at = len(suffix)
            suffix.append((ub, "g_unused_b"))
            suffix_w += _dw(ub)
    # Degradation ladder, tightest-last (the F-22 40-cell cap makes this reachable at every
    # width, so it cannot be left to chance): provenance drops first, then the badge's age,
    # and only then does the name itself clip. The name is what identifies the row — F-26
    # exists to stop anonymous rows (prd.md:247), so it yields last.
    prov = getattr(s, "provenance", None)
    if prov:
        ptag = " %s" % prov
        # best-effort by contract → only shown when the name keeps its full width anyway.
        if avail - suffix_w - _dw(ptag) - _NAME_GAP >= _dw(name_txt):
            suffix.append((ptag, "dim"))
            suffix_w += _dw(ptag)
    if unused_at is not None and avail - suffix_w - _NAME_GAP < _dw(name_txt):
        short = (_unused_badge(s, compact=True), "g_unused_b")
        suffix_w -= _dw(suffix[unused_at][0]) - _dw(short[0])
        suffix[unused_at] = short
    title_budget = max(1, avail - suffix_w - _NAME_GAP)
    if name_width is None:
        title_budget = min(title_budget, _TITLE_MAX)
    shown = _clip_w(name_txt, title_budget)
    segs.append((shown, name_key))
    used = _dw(shown)
    for text, key in suffix:
        segs.append((text, key))
        used += _dw(text)
    if used < avail:
        segs.append((" " * (avail - used), None))

    segs.append(_branch_seg(s.cwd, s.branch, dim=dim_tel))     # main row = bright branch/model
    if dead_stale:
        # F-13: a stale/dead row has no live model/effort/ctx to show — a wall of "—" placeholders
        # read as broken telemetry rather than "this session stopped". One `last seen <age>` cell
        # replaces the whole model+gauge zone (LIVE rows keep the explicit "—" convention, F-3).
        age_min = int((time.time() - s.mtime) / 60) if s.mtime else (s.elapsed_min or 0)
        segs += [("    ", None), ("last seen %s" % fmt_min(age_min), "dim")]
    else:
        # STATUS-ZONE — ctx gauge (mid-line ━/─, level color). model/effort now live in the
        # harness field (F-4); `ctx_width` (F-22-adjacent, user 2026-07-16) lets wide-layout
        # callers widen the gauge into the slack the column merge freed up; legacy/hermetic
        # callers keep _CTX_W.
        cw = ctx_width or _CTX_W
        if s.ctx_pct is not None and not dim_tel:
            segs += [("    ", None)] + _gauge_segs(s.ctx_pct, cw) + [(" %3d%%" % s.ctx_pct, _pct_key(s.ctx_pct))]
        else:
            segs += [("    ", None), ("─" * cw, "dim"), (" %4s" % dash(s.ctx_pct, lambda v: "%d%%" % v), "dim")]
    if s.app_server:
        segs.append(("  app-server", "dim"))
    if s.orphan:
        segs.append(("  worktree-gone", "g_dead"))

    segs.append((_RFLUSH, None))                                     # ⏱uptime flush right
    # Cost display intentionally omitted.
    segs += [(_CLOCK, "dim"), ("%6s" % fmt_min(s.elapsed_min), "dim")]
    return segs


_DISPATCH_NAME_MAX = 18


def _compact_dispatch_name(name, max_width=_DISPATCH_NAME_MAX):
    if not name or len(name) <= max_width:
        return name or ""
    if max_width <= 1:
        return name[:max_width]
    return name[: max_width - 1] + "…"


def _dispatch_prefix(j):
    # Every dispatch depth fans out with the same ↳ spawn arrow, nested two cells deeper per level
    # (user 2026-07-16: dispatch-depth-2 rows lost their arrow when they were indent-only), and the
    # whole ladder starts one level in — the dispatch-depth-1 arrow sits UNDER its parent session's
    # text, not on the session's own glyph column (user 2026-07-16 "분사 세션의 화살표를
    # 좀 더 들여쓰자"). Width = (depth+1)*2; the harness field absorbs it (_HMW - len).
    depth = max(1, min(3, int(getattr(j, "depth", 1) or 1)))
    return "  " * depth + "↳ "


_LEVEL_SHORT = {
    "direct": "direct",
    "quick": "q",
    "light": "lt",
    "standard": "std",
    "strong": "strong",
    "thorough": "thr",
    "adversarial": "adv",
}

_ROLE_SHORT = {
    "capability-owner": "owner",
    "deep-reviewer": "review",
    "fast-reviewer": "review",
    "fast-implementer": "impl",
    "dev-refactor": "impl",
    "dev-new-lib": "impl",
    "research-survey": "research",
}

# drill/loop case ids (g6_worktree_dispatch, g9_cross_harness_depth2_dispatch, g8b_...) shrink
# to their gN prefix by a GENERAL rule instead of a per-case hardcoded entry above (F-9(b) —
# each new drill case used to need a code change here).
_G_CASE_PREFIX = re.compile(r"^(g\d+[a-z]?)")


def _short_level(value):
    if not value:
        return ""
    prefix = "~" if str(value).startswith("~") else ""
    raw = str(value)[1:] if prefix else str(value)
    return prefix + _LEVEL_SHORT.get(raw, raw)


def _short_role(value):
    if not value:
        return ""
    label, suffix = _stage_role_label(value)
    if label is not None:
        # stage suffix (":phase-A") rides along as part of the same dim profile tag — the
        # whole tag already renders "dim" (see _opts_segs), so no separate color key is needed.
        return _compact_dispatch_name(label + suffix, 14)
    m = _G_CASE_PREFIX.match(value)
    role = _ROLE_SHORT.get(value) or (m.group(1) if m else value.replace("-", "_"))
    return _compact_dispatch_name(role, 14)


_PROFILE_MAX = 28


def _strip_autopilot(name):
    if name and name.startswith("autopilot-"):
        return name[len("autopilot-"):]
    return name


def _entry_skill(j):
    """Skill identity for the options dial.

    A dispatch-depth-1 row names its entry capability. A dispatch-depth-2 row instead names the
    assigned stage: route node when present, otherwise the registered capability
    key. This prevents inherited owner mode (``dev/refactor``) from masquerading
    as the child's own work.
    """
    if max(1, int(getattr(j, "depth", 1) or 1)) >= 2:
        owner = getattr(j, "capability_owner", None)
        contract = getattr(j, "assigned_contract", None)
        assigned = (
            contract
            if contract and _strip_autopilot(contract) != _strip_autopilot(owner or "")
            else getattr(j, "route_node", None) or getattr(j, "key", None)
        )
        return _compact_dispatch_name(_strip_autopilot(assigned), _PROFILE_MAX)
    cap = _strip_autopilot(getattr(j, "capability_owner", None) or "")
    key = getattr(j, "key", None)
    skill = cap or (key if key in _PIPE_STAGES else None)
    if not skill:
        return None
    if skill in (getattr(j, "mode", None) or "").split("/"):
        return None
    return skill


def _dispatch_role_suffix(j, max_width=None):
    # qa is data-only now (kept in --json): the retired qa axis left the display entirely
    # (user 2026-07-16 — rigor derives from intensity, CONVENTIONS §1.1).
    worker_type = getattr(j, "worker_type", None)
    raw_role = worker_type if worker_type in {"owner", "stage", "review", "support"} else getattr(j, "worker_role", None)
    if getattr(j, "key", None) in _LOOPS_KEYS and raw_role == getattr(j, "slug", None):
        raw_role = None
    # A capability name is not a role (user 2026-07-20: "code가 표시가 되어있는데 굳이
    # autopilot-code가 왜 표시되는지") — a worker_role that restates the job's own key/
    # capability_owner drops, and a '<capability>-<role>' composite ('autopilot-code-owner')
    # keeps only its role tail instead of rendering as 'autopilot_cod…'.
    # Writer-vocabulary normalization (user 2026-07-20: "codex랑 claude가 서로 다르게 뜨는데")
    # — the codex conductor misfiles PORTABLE MODEL-ROLE phrases ('deep orchestrator',
    # 'deep maker') and team personas ('plan-team') into worker_role, where claude writes
    # harness role tokens + a separate model_role. Harness role tokens are always kebab, so
    # a space marks the model-role phrase: the orchestrator phrase IS the conductor
    # ('owner'), every other model-role/persona restates an axis the row already shows
    # (model cell / name-zone stage label) and drops. Display-only; the registry row keeps
    # the raw value.
    if raw_role and " " in raw_role:
        raw_role = "capability-owner" if raw_role.endswith("orchestrator") else None
    if raw_role and raw_role.endswith("-team"):
        raw_role = None
    if raw_role:
        bare = _strip_autopilot(raw_role)
        dups = [d for d in (_strip_autopilot(getattr(j, "capability_owner", None) or "") or None,
                            getattr(j, "key", None)) if d]
        if bare in dups:
            raw_role = None
        else:
            for d in dups:
                if bare.startswith(d + "-"):
                    raw_role = bare[len(d) + 1:]
                    break
    role = _short_role(raw_role)
    # intensity left this suffix for the dial's paren knob group (user 2026-07-20
    # hierarchical dial, _opts_segs) — it is a BEHAVIOUR axis, not part of the
    # environment tail this function feeds.
    if not role:
        return ""
    if max_width is not None and len(role) > max_width:
        # F-9(c): drop the whole component instead of tail-cutting it mid-token.
        return ""
    return role


def _dispatch_profile(j):
    # environment tail ONLY now — the worker role left for the dial's paren knob group
    # (user 2026-07-20: "owner의 위치가 애매" — 'boot/owner' read as one env path).
    profile = getattr(j, "profile", None)
    return _compact_dispatch_name(profile, _PROFILE_MAX) if profile else None

def _dispatch_stage_label(j):
    """(label_prefix, is_stage_worker) — the dispatch-depth-2 stage-role label ('exec', 'plan'...) that
    now identifies a dispatch-depth-2 child in the NAME zone (F-15a P0-1: identity lives here, not in a
    duplicated breadcrumb). dispatch-depth-1 conductors/orphans have no such label — their identity is
    just their own slug."""
    if max(1, int(getattr(j, "depth", 1) or 1)) < 2:
        return None
    route_node = getattr(j, "route_node", None)
    if route_node:
        return _compact_dispatch_name(route_node, 14)
    label, suffix = _stage_role_label(getattr(j, "assigned_contract", None))
    if label is None:
        label, suffix = _stage_role_label(getattr(j, "key", None))
    if label is None:
        # Legacy rows may only carry the old overloaded worker_role.
        label, suffix = _stage_role_label(getattr(j, "worker_role", None))
    if label is None:
        return None
    return label + suffix


def _opts_segs(j):
    """F-15a options column — HIERARCHICAL dial (user 2026-07-20: "계층적으로
    code (mode inten) / boot 순"). Three axes, three visual levels instead of the flat
    '·' chain that mixed them: the entry skill heads the dial, its behaviour knobs
    (mode·intensity) ride in a dim paren group, and the environment tail
    (profile home / role suffix) is set off by ' / '. A dispatch-depth-2 worker names its
    assigned stage skill and keeps only worker-local intensity/profile: inherited
    owner mode and internal personas (qa/development/maker) are not child identity.
    qa left this dial with the retired qa axis (user 2026-07-16 — rigor derives
    from intensity, CONVENTIONS §1.1)."""
    depth = max(1, int(getattr(j, "depth", 1) or 1))
    entry = _entry_skill(j)
    if depth >= 2:
        knob_items = [t for t in (_short_level(getattr(j, "intensity", None)),) if t]
    else:
        knob_items = [t for t in (j.mode, _short_level(getattr(j, "intensity", None))) if t]
    # the worker ROLE is a behaviour knob too (who the worker acts as), not environment —
    # it rides the paren group's last slot (user 2026-07-20: "owner의 위치가 애매").
    role = "" if depth >= 2 else _dispatch_role_suffix(
        j, max_width=max(0, _PROFILE_MAX - sum(len(t) + 1 for t in knob_items)))
    if role:
        knob_items.append(role)
    knobs = "·".join(knob_items)
    tail = _dispatch_profile(j)
    contract_status = getattr(j, "attempt_contract_status", None)
    if contract_status == "legacy-read-only":
        tail = " / ".join(value for value in (tail, "legacy") if value)
    elif contract_status and contract_status != "current":
        tail = " / ".join(value for value in (tail, "contract!") if value)
    parts = []
    w = 0

    def _add(text, key):
        nonlocal w
        parts.append((text, key))
        w += len(text)

    if entry:
        _add(entry, "name_dim")
    if knobs:
        if entry:
            # flush paren (user 2026-07-20: "code 뒤에 괄호 여백 지우고") — same idiom as
            # the F-33 flush '·'.
            _add("(", "dim"); _add(knobs, "dim"); _add(")", "dim")
        else:
            _add(knobs, "dim")
    if tail:
        if parts:
            _add(" / ", "dim")
        _add(tail, "dim")
    return parts, w


def _dispatch_row(j, orphan=False, parent_model=None, parent_harness=None, is_last=True,
                  parent_effort=None, stage_override=None, name_width=None, route_seq=None):
    """A dispatch job rendered as a session-ANALOGUE, mirroring the session columns 1:1:
      harness (model · effort)  |  [stage label] name  |  branch  |  options  |  stage breadcrumb
    F-33 (v11): model/effort fold into the harness field (no more separate model column).
    F-15a: the name zone is identity-only (no more parenthetical mode/qa tag — that moved to
    its own options column). A dispatch-depth-2 stage worker's identity is its stage label + slug
    (P0-1); its breadcrumb slot shows its own micro-status instead of repeating the parent
    conductor's full breadcrumb.
    """
    key = j.key or "?"
    depth = max(1, int(getattr(j, "depth", 1) or 1))
    stage = stage_override if stage_override is not None else (j.stage or "")
    # The dispatched session's own haiku sidecar title is its identity when present
    # (user 2026-07-16: the summary agent attaches to every dispatched session); the
    # slug stays the fallback — same title → name → slug chain as session rows.
    slug_name = getattr(j, "title", None) or j.slug or key
    gch, gkey = _glyph(j.liveness, dim=True)
    dead_stale_j = j.liveness in ("dead", "stale")
    # SD-F3: the job's own effort is first-class; when it's absent (proc-scan rows — env
    # doesn't export it yet), fall back to the parent's effort, shown plain (user
    # 2026-07-16: the `~` derived-value marker is retired — qa left the display with the
    # retired qa axis at the same time). A dead/stale row has no live telemetry (F-13).
    eff = None if dead_stale_j else (j.effort or parent_effort or None)

    # DIFFERENTIAL indent (harness 2 cols deeper than a session) with a ↳ spawn arrow off the
    # parent's dot column (user pick over ├─/└─ tree bars); the harness field is narrowed by 2 so
    # the NAME still lands at the shared _NAME_COL — name onward aligns with sessions. DIM =
    # spawned. F-33 (v11): the widened field also carries the job's own model/effort as a
    # parenthetical (SD-F3).
    prefix = _dispatch_prefix(j)
    segs = [("  ", None), (prefix, "dim"), (gch, gkey), (" ", None)]
    segs += _harness_model_cell(j.harness, None if dead_stale_j else (j.model or parent_model),
                                eff, max(1, _HMW - len(prefix)),
                                _BADGE_KEY.get(j.harness, "dim"), dim=True, unknown="—")
    avail = max(3, name_width or _NW_S)
    otag = "  (orphan)" if orphan else ""
    label = _dispatch_stage_label(j)
    name_room = min(_TITLE_MAX, max(3, avail - len(otag)))
    if label:
        # P2-6 composed cap: slug shares the same budget as its stage label.
        slug_room = max(1, name_room - len(label) - 1)
        nm = label + " " + _compact_dispatch_name(slug_name, slug_room)
    else:
        nm = _compact_dispatch_name(slug_name, name_room)
    used = len(nm)
    # user 2026-07-20: 분사 행 제목도 컬러 — the dim HARNESS hue, so the title row stays
    # dark but no longer reads identical to its grey subtitle line underneath. Dead/stale
    # rows keep the colorless dim (F-13: no live telemetry, nothing to tint).
    name_key_j = "name_dim" if dead_stale_j else _BADGE_KEY.get(j.harness, "name_dim")
    segs.append((nm, name_key_j))
    if otag and used + len(otag) <= avail:
        segs.append((otag, "gate_u")); used += len(otag)
    if used < avail:
        segs.append((" " * (avail - used), None))

    segs.append(_branch_seg("" if key in _LOOPS_KEYS else j.cwd, j.branch))  # loop temp repos hide throwaway branches
    if j.liveness == "dead":
        segs.append(("    ", None))
        if getattr(j, "note", None) == "dead-parent-orphaned":
            # SD-64/71: distinct from the generic dead-conductor cell — never blank, and
            # always names the exact node a dispatch-depth-0 decision would resume from.
            boundary = getattr(j, "resume_boundary", None) or "-"
            segs.append(("⚠ ORPHANED resume=%s" % boundary, "g_dead"))
        else:
            # P2-11: a dead job's last-known stage replaces the redundant "last seen <age>"
            # (the time column already shows elapsed) — "dead @exec" tells you WHERE it died.
            last_stage = stage if stage not in (None, "", "open", "running") else key
            segs.append(("dead @%s" % last_stage, "g_dead"))
    elif j.liveness == "stale":
        # F-13: a stale job has no live model/effort/stage worth showing — collapse the whole
        # telemetry zone (model cell + stage breadcrumb) into one `last seen <age>` cell.
        segs.append(("    ", None))
        segs.append(("last seen %s" % fmt_min(j.elapsed_min), "dim"))
    else:
        # F-15a options column (fixed-ish gap, dim mode/qa/profile) — a declutter move OUT of
        # the name zone, not a new axis. model/effort now live in the harness field (F-4/SD-F3).
        segs.append(("    ", None))
        opt_segs, optw = _opts_segs(j)
        segs += opt_segs
        if optw < _OPTW:
            segs.append((" " * (_OPTW - optw), None))

        segs += _stage_zone_segs(
            _dispatch_stage_segs(j, key, stage, slug_name, working=(j.liveness == "working"),
                                 route_seq=route_seq))

    segs.append((_RFLUSH, None))
    segs += [(_CLOCK, "dim"), ("%6s" % fmt_min(j.elapsed_min), "dim")]
    return segs


# ---------- 2-line cards (round-4 responsive narrow mode) ----------
# L1 = identity (dot · harness · name · ▾N · gate · branch) / L2 = telemetry (model · effort ·
# bracket gauge · cost · ⏱). model keeps its fixed width so gauges align vertically across cards
# (the nvtop column feel). Same segment parts as the 1-line rows — zero new color keys.
def _session_row_2line(s, is_parent=False, child_count=0, _split=False, term_width=None):
    live = s.liveness
    slug = s.slug or (s.cwd.rsplit("/", 1)[-1] if s.cwd else "?")
    dim_tel = live in ("stale", "dead") or s.app_server or s.detached
    name_key = ("name_work" if live == "working"
                else ("name_dim" if dim_tel else "name_idle"))
    gch, gkey = _glyph(live)
    if s.detached and live not in ("stale", "dead"):
        gch, gkey = _DETACHED_GLYPH, "g_work_off"
    hn = _BADGE_TEXT.get(s.harness, "?")
    hkey = (_BADGE_KEY.get(s.harness, "dim") if dim_tel
            else ("hb_" + s.harness if s.harness in _BADGE_TEXT else "hb_other"))
    l1 = [("  ", None), (gch, gkey), (" ", None), (_pad(hn, _HW), hkey)]
    suffix = []
    if is_parent and child_count:
        suffix.append((" ▾%d" % child_count, "dim"))
    unused_at = None
    if live == "unused":                       # F-26 parity with the wide row
        unused_at = len(suffix)
        suffix.append((_unused_badge(s), "g_unused_b"))
    # provenance is optional here: in the narrow/stack layouts every suffix cell
    # is taken straight out of the name, so a 9-cell tag can clip a real name down to "age…".
    # A name the user can read outranks knowing who launched it — drop the tag instead.
    # Position is fixed here (identity tags, before branch) to match the wide row; whether it
    # is actually inserted is decided below, once the name's budget is known.
    prov_seg = (" %s" % s.provenance, "dim") if getattr(s, "provenance", None) else None
    prov_pos = len(suffix)
    br = s.branch or _git_branch(s.cwd)
    br_seg = ("  " + _clip_w(br, _BRW - 2), "dim" if dim_tel else "branch_s") if br else None
    if not _split and br_seg:
        suffix.append(br_seg)
    if s.app_server:
        suffix.append(("  app-server", "dim"))
    if s.orphan:
        suffix.append(("  worktree-gone", "g_dead"))
    name_txt = _session_name(s)
    if term_width:
        # A tinted L1 has 4 left cells (inset+padding) and a 2-cell right
        # inset. Reserve those six cells plus every suffix before clipping.
        prefix_w = sum(_dw(text) for text, _key in l1)
        avail = int(term_width) - 6 - prefix_w
        suffix_w = sum(_dw(text) for text, _key in suffix)
        # Shed the badge's age before shedding the name (see _unused_badge). L2 carries the
        # elapsed time directly beneath, so nothing is lost — it is the same value twice.
        if unused_at is not None and avail - suffix_w < _dw(name_txt):
            short = (_unused_badge(s, compact=True), "g_unused_b")
            suffix_w -= _dw(suffix[unused_at][0]) - _dw(short[0])
            suffix[unused_at] = short
        # Add provenance only if the name still gets its full width afterwards.
        if prov_seg and avail - suffix_w - _dw(prov_seg[0]) >= _dw(name_txt):
            suffix.insert(prov_pos, prov_seg)
            suffix_w += _dw(prov_seg[0])
        title_budget = max(4, avail - suffix_w)
    else:
        if prov_seg:
            suffix.insert(prov_pos, prov_seg)
        title_budget = min(_NAME2_MAX, _TITLE_MAX)
    l1.append((_clip_w(name_txt, title_budget), name_key))
    l1.extend(suffix)

    # L2: elapsed time sits UNDER the harness column (fills the old empty indent — user
    # Put time under the harness, model under the name, and gauge immediately after.
    # indent / no far-right flush).
    l2 = [("    ", None), (_pad(fmt_min(s.elapsed_min), _HW), "dim")]
    l2 += _model_cell(s.model, s.effort, _MW, dim=dim_tel)
    if s.ctx_pct is not None and not dim_tel:
        l2 += [("[", "dim")] + _gauge_segs(s.ctx_pct, 18) + \
              [(" %3d%%" % s.ctx_pct, _pct_key(s.ctx_pct)), ("]", "dim")]
    else:
        l2 += [("[", "dim"), ("·" * 18, "dim"),
               (" %3s" % dash(s.ctx_pct, lambda v: "%d%%" % v), "dim"), ("]", "dim")]
    if _split:
        return l1, l2, br_seg
    return l1, l2


def _stack_split(l2):
    """Index where the gauge/stage part of a narrow L2 begins (the '[' of the bracket meter,
    a stage-track segment, or the 'key: ' label) — the ultra-narrow card breaks there."""
    for i, (t, k) in enumerate(l2):
        if (t == "[" and k == "dim") or (isinstance(k, str) and k.startswith("stg")) \
                or (k == "name_dim" and t.endswith(": ")):
            return i
    return len(l2)


def _session_row_stack(s, is_parent=False, child_count=0, term_width=None):
    """Ultra-narrow card = the 2-line card with ONLY the context gauge pushed to its own line
    (user 2026-07-03): L1 identity / L2 time+model / L3 gauge (aligned under the model)."""
    l1, l2 = _session_row_2line(s, is_parent, child_count, term_width=term_width)
    gi = _stack_split(l2)
    return [l1, l2[:gi], [(" " * (4 + _HW), None)] + l2[gi:]]


def _dispatch_row_stack(j, orphan=False, parent_model=None, parent_effort=None, stage_override=None,
                        route_seq=None):
    l1, l2 = _dispatch_row_2line(j, orphan=orphan, parent_model=parent_model,
                                 parent_effort=parent_effort, stage_override=stage_override,
                                 route_seq=route_seq)
    gi = _stack_split(l2)
    return [l1, l2[:gi], [(" " * (4 + _HW), None)] + l2[gi:]]


def _dispatch_row_2line(j, orphan=False, parent_model=None, parent_effort=None, _split=False,
                        stage_override=None, route_seq=None):
    """F-15a narrow card — L1 = identity ONLY (stage label + slug, no mode/qa tag); L2 =
    elapsed · model · options (relocated from L1) · breadcrumb/micro-status."""
    key = j.key or "?"
    depth = max(1, int(getattr(j, "depth", 1) or 1))
    # The dispatched session's own haiku sidecar title is its identity when present
    # (user 2026-07-16: the summary agent attaches to every dispatched session); the
    # slug stays the fallback — same title → name → slug chain as session rows.
    slug_name = getattr(j, "title", None) or j.slug or key
    gch, gkey = _glyph(j.liveness, dim=True)
    hn = _BADGE_TEXT.get(j.harness, "—") if j.harness else "—"

    prefix = _dispatch_prefix(j)
    label = _dispatch_stage_label(j)
    if label:
        slug_room = max(1, _DISPATCH_NAME_MAX - len(label) - 1)
        shown_name = label + " " + _compact_dispatch_name(slug_name, slug_room)
    else:
        shown_name = _compact_dispatch_name(slug_name)
    # user 2026-07-20: 분사 행 제목도 컬러 (dim harness hue) — same rule as the wide row.
    name_key_j = ("name_dim" if j.liveness in ("dead", "stale")
                  else _BADGE_KEY.get(j.harness, "name_dim"))
    l1 = [("  ", None), (prefix, "dim"), (gch, gkey), (" ", None),
          (_pad(hn, max(1, _HW - len(prefix))), _BADGE_KEY.get(j.harness, "dim")), (shown_name, name_key_j)]
    if orphan:
        l1.append(("  (orphan)", "gate_u"))
    br = None if key in _LOOPS_KEYS else (j.branch or _git_branch(j.cwd))
    br_seg = ("  " + br, "dim") if br else None
    if not _split and br_seg:
        l1.append(br_seg)

    stage = stage_override if stage_override is not None else (j.stage or "")
    eff = j.effort or parent_effort or None
    l2 = [("    ", None), (_pad(fmt_min(j.elapsed_min), _HW), "dim")]
    l2 += _model_cell(j.model or parent_model, eff, _MW, dim=True)
    l2.append(("    ", None))
    opt_segs, optw = _opts_segs(j)
    l2 += opt_segs
    if optw < _OPTW:
        l2.append((" " * (_OPTW - optw), None))
    l2 += _stage_zone_segs(
        _dispatch_stage_segs(j, key, stage, slug_name, working=(j.liveness == "working"),
                             route_seq=route_seq))
    if _split:
        return l1, l2, br_seg
    return l1, l2


# ---------- grouping assembler ----------
def _group_key_session(s):
    return project_of(s.cwd)


def _mem_row(s, layout="wide"):
    """Render a dim one-line memory worker, hidden unless ``a`` is toggled."""
    name = _clip_w(s.title or s.slug or (s.harness or "?"), 40)
    seg = [("  🧠 ", "dim"), ("mem ", "dim"),
           (name, "dim"), ("  ", None),
           ((s.harness or "—"), "dim"), ("  ", None),
           (fmt_min(s.elapsed_min), "dim")]
    return [seg]


_GOVERNOR_QUIET_FRACTION = 0.5   # F-28c "healthy 무음" (prd.md:288/311, plan §6a) — hide the row
                                  # below half the cap. Real observed live state (this cycle):
                                  # 1 active lease / cap 5 = 20% — comfortably below half, so a
                                  # single background lease (the normal steady-state) stays
                                  # silent; the row only earns its place once congestion is
                                  # actually worth a glance.


def _governor_segs():
    """`  ⚙ governor N/cap` — F-28c (prd.md:288/311). Pulse-ADJACENT, never merged into the
    pulse row's own session/job counts (I8 — this is a wholly separate line/collector). `None`
    (source absent OR healthy-quiet) = caller omits the row entirely, same "zero lines when
    healthy" contract the alert strip already uses."""
    try:
        from .collectors import governor
        g = governor.collect()
    except Exception:
        g = None
    if not g:
        return None
    active, cap = g.get("active", 0), g.get("cap", 0)
    if cap <= 0 or active < cap * _GOVERNOR_QUIET_FRACTION:
        return None
    return [("  ⚙ ", "dim"), ("governor %d/%d" % (active, cap), "dim")]


def _pulse_segs(sessions, jobs):
    """`  fleet ⠙ N working   ● N idle ...` — whole-board census. Extracted (F-30, v10) so both
    the group view and the process view (§5.1) render the EXACT same row — one source, shared
    by the header helper contract §5.2 asks for, instead of two independently-drifting copies."""
    _real = [s for s in sessions if not s.app_server and not getattr(s, "mem_worker", False)]
    n_wk = sum(1 for s in _real if s.liveness == "working")
    n_id = sum(1 for s in _real if s.liveness == "idle")
    n_un = sum(1 for s in _real if s.liveness == "unused")
    n_dt = sum(1 for s in _real if s.detached and s.liveness not in ("stale", "dead"))
    listed_jobs = jobs if _SHOW_ALL else [j for j in jobs if j.liveness != "dead"]
    jw = sum(1 for j in listed_jobs if j.liveness == "working")
    spin = _SPIN[int(time.time() * 10) % len(_SPIN)]
    pulse = [("  fleet ", "head"),
             (spin + " %d" % n_wk, "g_work"), (" working   ", "dim"),
             ("● %d" % n_id, "g_work_off"), (" idle   ", "dim")]
    # F-26: only when there IS one — a healthy board stays quiet (F-12 contract).
    if n_un:
        pulse += [(_LIVE_GLYPH["unused"] + " %d" % n_un, "g_unused"), (" unused   ", "dim")]
    if n_dt:
        pulse += [(_DETACHED_GLYPH + " %d" % n_dt, "g_work_off"), (" detached   ", "dim")]
    if listed_jobs:
        pulse += [("↳ %d" % len(listed_jobs), "dim"),
                  (" job%s (%d working)" % ("s" if len(listed_jobs) != 1 else "", jw), "dim")]
    return pulse


def _mem_summary_segs(memory):
    """F-19 pulse-adjacent summary row — `🧠 mem  +N added(Nw·Nd) · M expired · K pruned ·
    last distill <elapsed>`. Healthy-silent: None when today's journal is empty AND no alert
    fired (mirrors the alert-strip zero-lines-when-healthy convention)."""
    if not memory:
        return None
    today = memory.get("today") or {}
    added = today.get("added", 0)
    expired = today.get("expired", 0)
    pruned = today.get("pruned", 0)
    alerts = memory.get("alerts") or {}
    alert_active = bool(alerts.get("durable_over")) or bool(alerts.get("distill_stale"))
    if not (added or expired or pruned) and not alert_active:
        return None
    last_min = memory.get("last_distill_min")
    seg = [("  🧠 ", "dim"), ("mem  ", "dim"),
           ("+%d added(%dw·%dd)" % (added, today.get("added_working", 0),
                                     today.get("added_durable", 0)), "dim"),
           (" · ", "dim"), ("%d expired" % expired, "dim"),
           (" · ", "dim"), ("%d pruned" % pruned, "dim"),
           (" · ", "dim"),
           ("last distill %s" % (fmt_min(last_min) if last_min is not None else "—"), "dim")]
    return seg


def _mem_event_rows(memory, limit=8):
    """F-19 `a`-toggle detail — most-recent-first dim rows (F-18b dim-row family): time ·
    action · tier/type · actor · snippet."""
    if not memory:
        return []
    rows = []
    for e in (memory.get("recent") or [])[:limit]:
        ts = (e.get("ts") or "—")
        if "T" in ts:
            ts = ts.split("T", 1)[1]   # HH:MM:SS only — date is always "today or recent"
        tier_type = "%s/%s" % (e.get("tier") or "-", e.get("type") or "-")
        snip = e.get("snippet") or ""
        seg = [("  🧠 ", "dim"), (ts, "dim"), ("  ", None),
               (e.get("action") or "?", "dim"), ("  ", None),
               (tier_type, "dim"), ("  ", None),
               (e.get("actor") or "?", "dim")]
        if snip:
            seg += [("  ", None), (_clip_w(snip, 60), "dim")]
        rows.append(seg)
    return rows


_MEM_DIVIDER_MARGIN = 12   # in-band card-bottom divider inset (both sides), matches the
                            # discarded two-plane demo's r5 rule — a dim `─` ON the tint, not
                            # a full-width chrome bar (F-19 repo rows, 사용자 확정 2026-07-16)
_MEM_REPO_ROW_LIMIT = 2
_MEM_REPO_TITLE_W = 22


def _mem_divider(term_width=None):
    """One dim in-band rule above a group card's per-repo mem rows — the tint prefix is
    applied by the caller's existing group-body tint loop (F-19 repo rows)."""
    return [(" ", None), ("─" * max(8, (term_width or 78) - _MEM_DIVIDER_MARGIN), "dim")]


def _mem_repo_rows(events, sid_titles, limit=_MEM_REPO_ROW_LIMIT):
    """F-19 repo rows — a group card's own today-mem events, most-recent-first, dim:
    `🧠 HH:MM ± tier/type actor ⟵ <source session title> "snippet"`. `+` (add) is green,
    `−` (expire/prune) falls back to dim (the engine's only red key is bold-only, and bold
    is reserved for the main-session row — round-2 precedent in the discarded two-plane
    demo). The source session title is shown only when the journal `sid` resolves against a
    currently-known session (honest omission otherwise, F-3)."""
    if not events:
        return []
    from .collectors.memory import ADDED_ACTIONS, EXPIRED_ACTIONS, PRUNED_ACTIONS
    rows = []
    for e in events[:limit]:
        ts = e.get("ts") or "—"
        if "T" in ts:
            ts = ts.split("T", 1)[1][:5]        # HH:MM
        action = e.get("action")
        if action in ADDED_ACTIONS:
            sign, sign_key = "+", "lvl_g"
        elif action in EXPIRED_ACTIONS or action in PRUNED_ACTIONS:
            sign, sign_key = "−", "dim"
        else:
            sign, sign_key = "·", "dim"
        tier_type = "%s/%s" % (e.get("tier") or "-", e.get("type") or "-")
        seg = [("  🧠 ", "dim"), (ts + " ", "dim"), (sign, sign_key),
               (" %s " % tier_type, "dim"), ((e.get("actor") or "?") + " ", "dim")]
        title = sid_titles.get(e.get("sid")) if e.get("sid") else None
        if title:
            seg.append(("⟵ " + _clip_w(title, _MEM_REPO_TITLE_W) + "  ", "dim"))
        snip = e.get("snippet")
        if snip:
            seg.append(('"%s"' % _clip_w(snip, 60), "dim"))
        rows.append(seg)
    return rows


def _mem_alert_bucket(memory):
    """F-19 alert-strip bucket — durable soft-ceiling + distill-silence, appended LAST in the
    dead > stale > ctx > mem priority order (§4.6)."""
    if not memory:
        return None
    alerts = memory.get("alerts") or {}
    parts = []
    over = alerts.get("durable_over") or []
    if over:
        names = []
        for cwd_origin, count in over[:4]:
            label = str(cwd_origin or "?")
            for prefix in ("git:", "root:", "id:"):
                if label.startswith(prefix):
                    label = label[len(prefix):]
            names.append("%s=%d" % (_clip_w(label, 20), count))
        more = " +%d" % (len(over) - 4) if len(over) > 4 else ""
        parts.append("durable-over %s%s" % ("·".join(names), more))
    if alerts.get("distill_stale"):
        parts.append("distill stale %s" % fmt_min(memory.get("last_distill_min")))
    if not parts:
        return None
    return (" · ".join(parts), "lvl_y")


def _group_key_job(j, session_groups=None, job_groups=None):
    session_groups = session_groups or {}
    job_groups = job_groups or {}
    if getattr(j, "parent_slug", None) and j.parent_slug in job_groups:
        return job_groups[j.parent_slug]
    if getattr(j, "parent_sid", None) and j.parent_sid in session_groups:
        return session_groups[j.parent_sid]
    if getattr(j, "parent_cwd", None):
        return project_of(j.parent_cwd)
    # Drill is fixture-rooted: keep its runner + dispatch-depth-1 owner + dispatch-depth-2 workers
    # together in one /tmp/drill-* card. Other scheduled loops stay in the shared
    # control-plane group.
    if j.key in _LOOPS_KEYS:
        drill_group = project_of(j.cwd)
        if j.key == "drill" and drill_group.startswith("drill:"):
            return drill_group
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
    def k(s):
        r = _LIVE_RANK.get(s.liveness, 9)
        if s.detached and r < 3:
            r = 3          # Detached sessions sort below working and idle sessions.
        return (r, -(s.elapsed_min or 0))
    return sorted(ss, key=k)


def _sort_group_jobs(js):
    return sorted(js, key=lambda j: (_JOB_LIVE_RANK.get(j.liveness, 9), -(j.elapsed_min or 0)))


_SHOW_ALL = False   # --all: reveal stale/dead/app_server sessions (folded by default per group)

# F-27 selectable-row stash. `_build_lines` returns a flat segment-line list and knows nothing
# about which SESSION/JOB produced which line — but a kill cursor must target a row, not a
# screen line. Stashed on the module (same pattern as _TOGGLE_ROWS) instead of changing the
# return signature, so render_once and every existing caller are untouched.
# Reset at the top of _build_lines, before any early return, so a stale map can never be read.
_SELECTABLE = []


def _selectable_session(s):
    """Kill-eligible session rows, per prd.md:253's two grades (and nothing else).

    Grade 1 (single confirm): unused / stale / dead — a row that is demonstrably not doing
    work. Plus an idle WORKER child (a leftover headless session).
    Grade 2 (warning + double confirm): working, or a registry that says busy.

    A plain interactive `idle` session is deliberately NOT selectable: it is somebody's live
    session sitting between prompts, and it appears in neither grade of the spec's list.
    """
    if getattr(s, "app_server", False):
        return False
    if s.liveness in ("unused", "stale", "dead", "working"):
        return True
    if s.liveness == "idle" and (getattr(s, "is_child", False)
                                 or getattr(s, "mem_worker", False)):
        return True
    return s.status == "busy"


def _select_entry(s, line_idx):
    return {"line": line_idx, "kind": "session", "pid": s.pid,
            "proc_start": getattr(s, "proc_start", None),
            "sid": s.session_id, "state": s.liveness,
            "status": s.status, "cwd": s.cwd, "slug": s.slug,
            "label": _session_name(s), "harness": s.harness, "source": None,
            "is_worker": bool(getattr(s, "is_child", False)
                              or getattr(s, "mem_worker", False))}


def _select_entry_job(j, line_idx):
    return {"line": line_idx, "kind": "job", "pid": j.pid,
            "proc_start": getattr(j, "proc_start", None),
            "sid": None, "state": j.liveness, "status": j.status,
            "cwd": j.cwd, "slug": j.slug,
            "label": j.slug or j.key, "harness": j.harness, "source": j.source,
            "is_worker": bool(getattr(j, "is_child", False))}
_FOLD_CHILD_LIVENESS = {"done", "queued", "idle", "unknown"}   # F-15b P0-2: dispatch-depth-2 stage-worker
                                                                # rows folded into the conductor
                                                                # breadcrumb unless working/stale/dead

# F-29 (v9, prd.md:290-295) — sub-agent observation rows. `⚡` is the PRD-specified glyph.
# Reads distinctly from dispatch's `🚀`/`↳` so the two nested-row kinds never visually merge.
# Single point of ASCII-degrade if double-width alignment ever breaks in a real terminal.
_ICON_SUBAGENT = "⚡"
_SUBAGENT_IND = "      "  # strip indent: pure inset, no connector glyph, 6 cells for a
                          # session-owned strip — well past the dispatch-depth-2 arrow column so the
                          # strip reads as INSIDE the row above, never as a sibling (사용자
                          # 2026-07-16 "들여쓰기 레벨을 충분히 안쪽으로"; the 2-cell then 4-cell
                          # insets both read too shallow). Dispatch-owned strips add 2 more
                          # cells per depth (see _subagent_strip). The per-session ⚡N
                          # name-zone badge this used to pair with stays retired.


def _subagent_elapsed_min(sa):
    started = getattr(sa, "started_at", None)
    if not started:
        return None
    return max(0, int((time.time() - started) / 60))


def _subagent_strip(subs, depth=0):
    """One horizontal strip per OWNER ROW (session or dispatch job): `⚡<type> <glyph>
    <elapsed> · <type> <glyph> <elapsed> …` — replaces the old one-row-per-subagent
    `├⚡`/`└⚡` stack (adopted from the discarded two-plane demo's `_agents_strip`,
    prd.md:290-295). ⚡ sits flush against the first label (the double-width glyph plus a
    space read as a hole — 사용자 2026-07-16), and the elapsed tail is set off by a double
    space and always dim, floating it apart from the identity the way the clock column
    separates from session rows. Active entries render normal weight (●); completed
    entries fully dim (✓) — the caller only passes completed entries at all when
    `_SHOW_ALL` (F-18b dim-row convention). `depth` = the owning dispatch row's depth
    (0 for a session row): each level pushes the strip 2 more cells inward so it stays
    visibly inside its own owner (사용자 2026-07-16 "서브 세션에 서브 에이전트도")."""
    segs = [(_SUBAGENT_IND + "  " * max(0, depth), None), (_ICON_SUBAGENT, "dim")]
    for i, sa in enumerate(subs):
        if i:
            segs.append((" · ", "dim"))
        label = sa.agent_type or "agent"
        elapsed = _subagent_elapsed_min(sa)
        tail = fmt_min(elapsed) if elapsed is not None else "—"
        glyph = "●" if sa.active else "✓"
        segs.append(("%s %s" % (label, glyph), None if sa.active else "dim"))
        segs.append(("  " + tail, "dim"))
    return [segs]


_SUMMARY_FALLBACK_W = 60   # hermetic/no-terminal-width callers (mirrors the dim-snippet clip
                           # convention used elsewhere, e.g. the memory-row snippet cells)


def _summary_row(summary, depth=0, term_width=None):
    """One dim subtitle row directly under a session/dispatch row (F-16/F-17 merge,
    사용자 확정 2026-07-19): the live one-sentence status from the SAME haiku call that
    produced the title. Pure inset — no connector/icon, `_SUBAGENT_IND` + the same
    per-depth ladder `_subagent_strip` uses, so it reads as INSIDE its owner row and
    never collides with the sub-agent strip's own indent. Caller gates presence
    (summary truthy, row not dead/stale — F-13) and ordering (this row before the
    owner's `⚡` strip, never after)."""
    indent = _SUBAGENT_IND + "  " * max(0, depth)
    maxw = max(1, term_width - _dw(indent)) if term_width else _SUMMARY_FALLBACK_W
    return [[(indent, None), (_clip_w(summary, maxw), "dim")]]


def set_show_all(v):
    global _SHOW_ALL
    _SHOW_ALL = bool(v)


# --- F-30 (v10, prd.md:304-310) — process view: pipeline-centric regrouping, `p` toggle ---
_PROCESS_VIEW = False        # False = group view (default, unchanged) | True = process view
_ROUTE_FOLD = {}             # {card_key: bool} — True = explicitly folded. User action ONLY;
                             # default fold state (§5.4 table) is computed fresh every build and
                             # never written here (so a card that becomes newly-failed re-expands
                             # on its own unless the user folded it by hand).
_FOLDABLE = []                # [{"line": idx, "card_key": ...}] — line-index map, `_build_process_
                              # lines` fills it fresh every call (`_SELECTABLE` precedent, F-27).


def set_process_view(v):
    global _PROCESS_VIEW
    _PROCESS_VIEW = bool(v)


_GATE_MARK = " ⊸"   # prd.md:308 — completion-gate PASSED. Never rendered for no-claim/absent.


def _route_node_text(n):
    """(text, color_key, mark) for one DAG node in a card's L2 flow (§5.3). State comes straight
    from `route.py`'s §3.3 judge — this only formats it. `●` nodes carry model/effort (prd.md:307
    — "전 노드에 달면 줄이 터진다", so only the active one does).

    `mark` is `_GATE_MARK` or "" and the caller emits it as its OWN segment in `gate_t` (the
    green-dim key the spec-gate word already uses), never folded into `text`: prd.md:308 makes
    gate-passed a dimension INDEPENDENT of the ✓●○✕ state glyph, and most passed nodes are
    `done` (= all-dim) nodes, where a dim mark would melt into the node's own dim phrase — the
    exact merge render.py:101 warns about. `gate_passed` is True|None only, so there is no
    "not passed" mark to render: absence of evidence draws nothing."""
    st = n["state"]
    nid = n["id"]
    elapsed = n.get("elapsed_min")
    mark = _GATE_MARK if n.get("gate_passed") else ""
    if st == "done":
        tail = fmt_min(elapsed) if elapsed is not None else ""
        return "%s ✓%s" % (nid, tail), "dim", mark
    if st == "active":
        tail = (" " + fmt_min(elapsed)) if elapsed is not None else ""
        extra = ""
        model = _clean_model(dash(n.get("model"))) if n.get("model") else None
        if model and model != "—":
            extra = " (%s%s)" % (model, ("·" + n["effort"]) if n.get("effort") else "")
        return "%s ●%s%s" % (nid, tail, extra), ("g_work" if _BLINK_ON else "g_work_off"), mark
    if st == "failed":
        tail = (" " + fmt_min(elapsed)) if elapsed is not None else ""
        return "%s ✕%s" % (nid, tail), "lvl_r", mark
    return "%s ○" % nid, "dim", mark


def _route_card_l2(view, max_width=None):
    """DAG lines for a card's body (§5.3/§5.5). A level with ONE node joins the horizontal
    flow (`plan ✓12m › execute ● 8m ...`); a level with 2+ nodes (fan-out) breaks into indented
    `├`/`└` tree rows (prd.md:307's "세로 분기"), and the flow resumes with a leading `›` after.
    `max_width`, when given, folds PAST (already-flowed) nodes first via the SAME
    `_drop_past_stages` the breadcrumb uses (§5.5 — no new cropping logic), independently per
    contiguous flow run (a run never spans a fan-out break)."""
    levels = {}
    for n in view.get("nodes") or []:
        levels.setdefault(n["level"], []).append(n)
    ordered = [levels[k] for k in sorted(levels)]
    out_lines = []
    flow_nodes = []   # [(text, key)] accumulated for the current contiguous flow run

    def _flush(prefix_needed):
        if not flow_nodes:
            return
        # The gate mark rides INSIDE the width-accounting text (`t + m`) so `_drop_past_stages`
        # folds against the node's real drawn width, then is peeled back off at emit time to get
        # its own color — the mark must never be the thing that overflows a 60-column card.
        items = [(i, t + m, k) for i, (t, k, m) in enumerate(flow_nodes)]
        if max_width is not None:
            cur_i = next((i for i, (_t, k, _m) in enumerate(flow_nodes) if k != "dim"), 0)
            items = _drop_past_stages(items, cur_i, max_width)
        segs = []
        for pos, (i, _combined, key) in enumerate(items):
            text, _key, mark = flow_nodes[i]
            if pos == 0:
                if prefix_needed:
                    segs.append(("› ", "dim"))
            else:
                segs.append((" › ", "dim"))
            segs.append((text, key))
            if mark:
                segs.append((mark, "gate_t"))
        out_lines.append(segs)
        flow_nodes.clear()

    need_prefix = False
    for level in ordered:
        if len(level) == 1:
            flow_nodes.append(_route_node_text(level[0]))
        else:
            _flush(need_prefix)
            need_prefix = False
            for bi, n in enumerate(level):
                branch = "└" if bi == len(level) - 1 else "├"
                text, key, mark = _route_node_text(n)
                row = [("  " + branch + " ", "dim"), (text, key)]
                if mark:
                    row.append((mark, "gate_t"))
                out_lines.append(row)
            need_prefix = True
    _flush(need_prefix)
    return out_lines


def _route_job_row(job, max_width=None):
    """The active node's owning job, one compact row (prd.md:308's `└▸🚀 <slug> <harness>
    <model> ⏳<elapsed>` shape) — NOT the group view's full `_dispatch_row` grid (a route card
    is not a project group; its columns don't line up with one, and forcing them to would need
    a second name-width negotiation this view doesn't have). `max_width` (§5.5): the slug is
    the one field with no fixed budget elsewhere, so it yields first — same "the variable-width
    field clips, the fixed-shape fields never do" idiom as `_compact_dispatch_name`."""
    hn = _BADGE_TEXT.get(job.harness, "—") if job.harness else "—"
    model_txt = _clean_model(dash(job.model)) or "—"
    eff = ("(%s)" % job.effort) if job.effort else ""
    tail = "⏳%s" % fmt_min(job.elapsed_min) if job.elapsed_min is not None else ""
    prefix = "     └▸🚀 "
    slug = job.slug or job.key or "?"
    fixed_bits = [b for b in (hn, model_txt, eff, tail) if b]
    if max_width is not None:
        fixed_w = _dw(prefix) + (2 * len(fixed_bits)) + sum(_dw(b) for b in fixed_bits)
        slug = _clip_w(slug, max(4, max_width - fixed_w))
    bits = [b for b in (slug, hn, model_txt, eff, tail) if b]
    return [(prefix + "  ".join(bits), "name_dim")]


def _route_card_l1(tag_bits, rid, done, total, route_elapsed, any_failed, arrow, term_width):
    """§5.5's L1 width ladder — "60열: L1 태그가 이미 20열이다 → intensity를 먼저 떨어뜨리는
    사다리" — same pick-first-fit idiom as `_prompt_variants` (render.py, F-27): try progressively
    shorter tag/detail combinations, keep the first that fits `term_width`. `tag_bits` drops
    right-to-left (intensity, then mode, capability always survives — it's the identity)."""
    def build(tags, show_elapsed, show_failed):
        segs = [("  " + arrow + " ", "dim"), ("[%s] " % "·".join(tags), "name_dim"),
                (rid, "lvl_r" if any_failed else "dim"),
                (" — %d/%d nodes" % (done, total), "dim")]
        if show_elapsed and route_elapsed is not None:
            # design_review_round_1.md 🟡2 / prd.md:307 literal ("<n/m nodes> ⏳<경과>") — the
            # bare `_CLOCK` convention (session/dispatch GRID rows, render.py:540) is the wrong
            # precedent here: `_route_job_row` already established "⏳" as THIS card's own
            # elapsed glyph (the child row below reads `⏳8m`), so the L1 header must match it —
            # a bare "  15m" both drops the spec's glyph AND reads as a stray number glued onto
            # "n/m nodes" (the exact critic misreading).
            segs += [("  ⏳", "dim"), (fmt_min(route_elapsed), "dim")]
        if show_failed and any_failed:
            segs.append((" ⚠ failed node", "lvl_r"))
        return segs

    ladder = [tag_bits]
    for n in range(len(tag_bits) - 1, 0, -1):
        ladder.append(tag_bits[:n])
    variants = [(ladder[0], True, True)]
    for tags in ladder[1:]:
        variants.append((tags, True, True))
    variants.append((ladder[-1], False, False))
    for tags, show_elapsed, show_failed in variants:
        segs = build(tags, show_elapsed, show_failed)
        if term_width is None or sum(_dw(t) for t, _k in segs) <= term_width:
            return segs
    return build(ladder[-1], False, False)


def _route_card(view, session_by_pid, term_width, now):
    """One F-30 card. Returns (out_lines, meta) — meta = {"card_key", "fold_line" (index into
    out_lines of the header row), "job_rows": [(index_into_out_lines, DispatchJob), ...]}. The
    caller (`_build_process_lines`) owns translating these to ABSOLUTE line indices for
    `_FOLDABLE`/`_SELECTABLE` — this function stays a pure line-list builder (no module-global
    writes), so it is directly unit-testable."""
    nodes = view.get("nodes") or []
    done = sum(1 for n in nodes if n["state"] == "done")
    total = len(nodes)
    any_failed = any(n["state"] == "failed" for n in nodes)
    all_done = total > 0 and done == total
    elapsed_candidates = [n["elapsed_min"] for n in nodes if n.get("elapsed_min") is not None]
    route_elapsed = max(elapsed_candidates) if elapsed_candidates else None

    cap = view.get("capability") or "?"
    try:
        from .collectors import dispatch as _dispatch_mod
        cap = _dispatch_mod._strip_autopilot_prefix(cap) or cap
    except Exception:
        pass
    tag_bits = [cap]
    if view.get("capability_mode"):
        tag_bits.append(view["capability_mode"])
    if view.get("effective_intensity"):
        tag_bits.append(view["effective_intensity"])
    rid_full = view.get("route_id") or "?"
    # §5.3 L1 spec: "route_id 단축 = rt- + 앞 8자" — the full value stays available in --json
    # (route.summary()'s route_id is never shortened); only the card label abbreviates.
    rid = (rid_full if not rid_full.startswith("rt-") or len(rid_full) <= 11
          else rid_full[:11])

    card_key = view["key"]
    # §5.4 default fold table: failed → auto-expand (handled by simply never defaulting to
    # folded when any_failed); all-done → 1-line fold; otherwise (active) → expand. A prior
    # EXPLICIT user fold (_ROUTE_FOLD) always wins over this default (user intent > default).
    default_fold = all_done and not any_failed
    folded = _ROUTE_FOLD.get(card_key, default_fold)
    # ★ collapse/expand glyph only — NEVER the words "folded"/"hidden" (§5.4 B2): `_draw`'s
    # existing single-segment-row substring check would silently hijack this row into
    # `_TOGGLE_ROWS` (the `a`-toggle map) instead of `_FOLD_ROWS`.
    arrow = "▸" if folded else "▾"

    l1 = _route_card_l1(tag_bits, rid, done, total, route_elapsed, any_failed, arrow, term_width)

    out = [l1]
    if folded:
        return out, {"card_key": card_key, "fold_line": 0, "job_rows": [], "folded": folded}

    max_width = max(20, term_width - 6) if term_width else None
    for l2_line in _route_card_l2(view, max_width):
        out.append([("    ", None)] + l2_line)

    job_rows = []
    active_nodes = sorted((n for n in nodes if n["state"] == "active" and n.get("job") is not None),
                          key=lambda n: (n["level"], n["id"]))
    for n in active_nodes:
        job = n["job"]
        out.append(_route_job_row(job, max_width=term_width))
        job_rows.append((len(out) - 1, job))
        sess = session_by_pid.get(job.pid) if job.pid else None
        subs = ([sa for sa in (getattr(sess, "subagents", None) or []) if sa.active or _SHOW_ALL]
                if sess is not None else [])
        if subs:
            out.extend(_subagent_strip(subs))

    if _SHOW_ALL:
        # prd.md:310 — completion gates stay behind the `a` toggle, never on the base screen.
        # Each name carries `⊸` iff a canonical marker PROVES it passed (prd.md:308, v10 minor
        # #2 — the evidence source the v10 cycle had to leave as an honest gap). A gate with no
        # marker prints its bare name: no-claim, NOT a failure mark.
        gate_bits = [(n["gate"], bool(n.get("gate_passed"))) for n in nodes if n.get("gate")]
        if gate_bits:
            segs = [("      gates: ", "dim")]
            for i, (name, passed) in enumerate(gate_bits):
                if i:
                    segs.append((", ", "dim"))
                segs.append((name, "dim"))
                if passed:
                    segs.append((_GATE_MARK, "gate_t"))
            out.append(segs)

    return out, {"card_key": card_key, "fold_line": 0, "job_rows": job_rows, "folded": folded}


def _degrade_candidates(jobs, covered_slugs=()):
    """Dispatch-depth-1 jobs on a recognizable `_PIPE_STAGES` pipeline with NO resolved route_id — the
    degrade card's population (prd.md:310 — record absence is a summary card, never a blank).
    Deliberately excludes: dispatch-depth-2 stage workers (those nest under their conductor's card, same
    as the group view); any job that already has a route_id itself (that route already has a
    real card, even if the record failed to load — route.py's `_heuristic_view` covers that
    case inside `route_views_by_id`, not here); and `covered_slugs` — the dispatch-depth-1 CONDUCTOR of a
    route whose route_id lives on one of ITS children (§3.2 — the route link is attached to the
    stage worker, not the top job) would otherwise show up a SECOND time as a bare degrade card
    right next to its own real route card."""
    pool = jobs if _SHOW_ALL else [j for j in jobs if j.liveness != "dead"]
    seen = set()
    out = []
    for j in pool:
        if getattr(j, "route_id", None):
            continue
        if max(1, int(getattr(j, "depth", 1) or 1)) != 1:
            continue
        if j.key not in _PIPE_STAGES:
            continue
        if j.slug in covered_slugs:
            continue
        if j.slug in seen:
            continue
        seen.add(j.slug)
        out.append(j)
    out.sort(key=lambda j: j.slug or "")
    return out


def _degrade_card(job, session_by_pid, term_width):
    """§5.3's degrade card — `source: heuristic`, existing `_PIPE_STAGES` breadcrumb, no DAG
    (there is no record to derive one from). No job-row entry (the card key IS the job)."""
    cap = job.key or "?"
    tag_bits = [cap]
    if job.mode:
        tag_bits.append(job.mode)
    tag = "·".join(tag_bits)
    card_key = job.slug or job.key or "?"
    folded = _ROUTE_FOLD.get(card_key, False)
    arrow = "▸" if folded else "▾"
    slug = job.slug or "?"
    if term_width is not None:
        fixed_w = _dw("  " + arrow + " ") + _dw("[%s] " % tag) + _dw(" — no route record")
        slug = _clip_w(slug, max(4, term_width - fixed_w))
    l1 = [("  " + arrow + " ", "dim"), ("[%s] " % tag, "name_dim"),
          (slug, "dim"), (" — no route record", "dim")]
    out = [l1]
    if folded:
        return out, {"card_key": card_key, "fold_line": 0, "job_rows": [], "folded": folded}
    breadcrumb = _stage_segs(job.key, job.stage or "", working=(job.liveness == "working"),
                             max_width=_STAGE_ZONE_MAX)
    out.append([("    ", None)] + breadcrumb)
    # F-29 — the degraded job's session's own active sub-agents, the same strip the route card
    # draws (2060-2064); silent when the pid resolves to no session or no active sub-agent.
    sess = session_by_pid.get(job.pid) if job.pid else None
    subs = ([sa for sa in (getattr(sess, "subagents", None) or []) if sa.active or _SHOW_ALL]
            if sess is not None else [])
    if subs:
        out.extend(_subagent_strip(subs))
    return out, {"card_key": card_key, "fold_line": 0, "job_rows": [], "folded": folded}


def _build_process_lines(sessions, jobs, route_views_by_id, malformed, memory, term_width, layout,
                         node_evidence=None):
    """F-30 (prd.md:304-310) — the process view: one card per ACTIVE route (pipeline-centric
    regrouping) instead of the group view's per-project regrouping. Returns the SAME flat
    segment-line contract as `_build_lines` ([[(text,key),...]|None]) — `_draw`/`render_once`/
    scroll/`_clamp_offset` are all reused unmodified (§5.2). Side effect: refreshes the
    module-level `_FOLDABLE` stash (`_SELECTABLE` precedent, F-27) and appends to the (already
    freshly-reset, by `_build_lines`) `_SELECTABLE`.

    `node_evidence` (code-test verification_round_2.md §10): the SAME terminal-row evidence
    defect 1's fix threads into route resolution — the covered-conductor exclusion below has the
    identical "a route's only surviving trace may be terminal, not live" problem defect 1 fixed
    for record lookup, and needs the identical fix for the SAME reason."""
    global _FOLDABLE
    _FOLDABLE = []
    lines = [_pulse_segs(sessions, jobs)]
    _governor = _governor_segs()
    if _governor is not None:
        lines.append(_governor)
    _mem_summary = _mem_summary_segs(memory)
    if _mem_summary is not None:
        lines.append(_mem_summary)
    if malformed:
        lines.append([("  +%d malformed jobs.log rows skipped" % malformed, "dim")])
    lines.append([(_HFILL, None)])
    lines.append(None)
    lines.append([("  PROCESS VIEW", "head"), (_RFLUSH, None), ("p group view  ", "head")])
    lines.append(None)

    session_by_pid = {s.pid: s for s in sessions if s.pid}
    now = time.time()

    real_views = sorted((v for v in route_views_by_id.values() if v.get("nodes")),
                        key=lambda v: v.get("route_id") or "")
    # A dispatch-depth-1 conductor whose CHILD carries the route_id (§3.2 — the env/pipe route link is
    # attached to the stage worker, not the top job) already has a real card via that child;
    # exclude its own bare slug from the degrade pool so it never shows up a second time.
    # ★ code-test verification_round_2.md §10 — `jobs` (live only) under-covers the SAME way
    # defect 1's `resolve_records` did: once the route-carrying child goes terminal
    # (done/killed/cancelled), `_scan_jobs_log` drops its row before a live DispatchJob is ever
    # built for it, so `jobs` alone can never see that child's `parent_slug` again — the
    # conductor stops being excluded and a valid record's OWN conductor re-appears as a
    # contradicting "no route record" card 2 lines below its real one. `node_evidence`'s
    # `parent` field (dispatch.py's `_scan_route_nodes`, same pipe row already parsed) is the
    # terminal-surviving half of this same fact.
    covered_slugs = {getattr(j, "parent_slug", None) for j in jobs
                     if getattr(j, "route_id", None) in route_views_by_id
                     and getattr(j, "parent_slug", None)}
    for rid, nodes in (node_evidence or {}).items():
        if rid not in route_views_by_id:
            continue
        for node_ev in (nodes or {}).values():
            parent = (node_ev or {}).get("parent")
            if parent:
                covered_slugs.add(parent)
    degrade_jobs = _degrade_candidates(jobs, covered_slugs)

    # F-29 — plain top-level sessions running a native sub-agent. Process view is route-centric
    # and emits no plain-session row, so without this a session's ⚡ agents are invisible here
    # even though group view shows them in its session loop. Collected up front so they alone
    # can populate the screen when no route/degrade card exists.
    sub_sessions = []
    for s in sessions:
        if (getattr(s, "app_server", False) or getattr(s, "is_child", False)
                or getattr(s, "mem_worker", False)):
            continue
        s_subs = [sa for sa in (getattr(s, "subagents", None) or []) if sa.active or _SHOW_ALL]
        if s_subs:
            sub_sessions.append((s, s_subs))

    if not real_views and not degrade_jobs and not sub_sessions:
        # prd.md:310 — an honest "nothing is running" statement, never a blank screen.
        lines.append([("  no active route", "dim")])
        return lines

    seen_keys = set()
    covered_pids = set()
    first = True
    for view in real_views:
        if not first:
            lines.append(None)
        first = False
        base = len(lines)
        card_lines, meta = _route_card(view, session_by_pid, term_width, now)
        lines.extend(card_lines)
        _FOLDABLE.append({"line": base + meta["fold_line"], "card_key": meta["card_key"],
                          "folded": meta["folded"]})
        for rel_idx, job in meta["job_rows"]:
            if job.pid:
                _SELECTABLE.append(_select_entry_job(job, base + rel_idx))
        # F1 — cover every route node's session pid regardless of fold state: a folded card
        # yields no job_rows, but its sessions are still "on a route", not routeless, and must
        # not re-appear as a routeless anchor below.
        for n in (view.get("nodes", []) or []):
            nj = n.get("job") if isinstance(n, dict) else None
            if nj is not None and getattr(nj, "pid", None):
                covered_pids.add(nj.pid)
        seen_keys.add(meta["card_key"])

    for job in degrade_jobs:
        if not first:
            lines.append(None)
        first = False
        base = len(lines)
        card_lines, meta = _degrade_card(job, session_by_pid, term_width)
        lines.extend(card_lines)
        _FOLDABLE.append({"line": base + meta["fold_line"], "card_key": meta["card_key"],
                          "folded": meta["folded"]})
        if job.pid:
            covered_pids.add(job.pid)
        seen_keys.add(meta["card_key"])

    # Routeless sessions with active sub-agents — one minimal owner anchor + the same strip,
    # skipping any pid already shown under a route/degrade card above (no double draw).
    for s, s_subs in sub_sessions:
        if s.pid and s.pid in covered_pids:
            continue
        if not first:
            lines.append(None)
        first = False
        name_w = 40 if term_width is None else max(8, min(40, term_width - 6))
        anchor = [("  ● ", "dim"), (_clip_w(_session_name(s), name_w), "name_dim")]
        if getattr(s, "model", None):
            anchor.append(("  " + str(s.model), "dim"))
        lines.append(anchor)
        lines.extend(_subagent_strip(s_subs))

    # StateTracker.sweep() precedent — a card key not seen this tick must not leak its fold
    # flag into a future, unrelated card that happens to reuse the same route_id/slug.
    for k in [k for k in _ROUTE_FOLD if k not in seen_keys]:
        del _ROUTE_FOLD[k]

    return lines


def _current_attempt_jobs(jobs):
    """Hide superseded exact route attempts unless full history is requested."""
    if _SHOW_ALL:
        return jobs
    latest_attempt = {}
    for index, job in enumerate(jobs):
        key = (getattr(job, "route_id", None), getattr(job, "route_node", None))
        if not all(key) or not getattr(job, "attempt_id", None):
            continue
        rank = (
            -(getattr(job, "registry_priority", None)
              if getattr(job, "registry_priority", None) is not None else 0),
            getattr(job, "registry_order", None) if getattr(job, "registry_order", None) is not None else -1,
            -(getattr(job, "elapsed_min", None) if getattr(job, "elapsed_min", None) is not None else 10**9),
            index,
        )
        if key not in latest_attempt or rank > latest_attempt[key][0]:
            latest_attempt[key] = (rank, job)
    return [
        job for job in jobs
        if not (getattr(job, "route_id", None) and getattr(job, "route_node", None)
                and getattr(job, "attempt_id", None)
                and latest_attempt.get((job.route_id, job.route_node), (None, job))[1] is not job)
    ]


def _build_lines(sessions, jobs, section, narrow, malformed, layout="wide", memory=None,
                 term_width=None):
    """Return a flat list of segment-lines for the whole screen (None = blank line).

    Side effect: refreshes the module-level `_SELECTABLE` stash (F-27) — see its definition.

    Same contract consumed by BOTH `render_once` (plain, full output) and `_draw` (viewport
    slices this same list) — `_OFFSET` must never be read here (see module docstring).

    `memory` = F-19 collectors.memory.collect() result (or None — panel/alerts simply omitted;
    tests default to None so every pre-F-19 call site keeps working unchanged).
    """
    global _SELECTABLE
    _SELECTABLE = []     # reset before any early return — a stale target map must never survive
    # F-28b/F-30 (v10) — resolve every route referenced by `jobs` ONCE per build (not per row).
    # Best-effort: any failure here must never break the group view — record-less/failed-load
    # jobs simply keep their pre-v10 breadcrumb (prd.md:303). `route.load()` is itself
    # mtime-cached, so repeated ticks re-parse only a route file whose inode actually changed.
    _route_views_by_id = {}
    _node_evidence = {}
    try:
        from .collectors import dispatch as _dispatch_mod
        from . import route as _route_mod
        _node_evidence = getattr(_dispatch_mod.collect, "last_route_nodes", {}) or {}
        for _v in _route_mod.collect_views(jobs, _node_evidence):
            _route_views_by_id[_v["route_id"]] = _v
    except Exception:
        _route_views_by_id = {}
        _node_evidence = {}
    display_jobs = _current_attempt_jobs(jobs)
    if _PROCESS_VIEW:
        # F-30 (§5.2) — the ONE branch point, right after the _SELECTABLE reset and the route
        # resolution both views need. `_build_process_lines` honors the exact same return
        # contract ([[(text,key),...]|None]) so _draw/render_once/scroll/_clamp_offset are all
        # reused unmodified below this branch. `_node_evidence` is threaded through too (code-test
        # verification_round_2.md §10) — the degrade-pool's covered-conductor exclusion needs it,
        # the same way route resolution itself needed it for defect 1.
        return _build_process_lines(sessions, display_jobs, _route_views_by_id, malformed, memory,
                                    term_width, layout, node_evidence=_node_evidence)
    # F-18b: mem-worker (distiller/curator/F-17 refresher) census — computed on the ORIGINAL
    # session list, before is_child/mem filtering, so folded/mem-only groups still surface a
    # total in the legend even when no group header badge fires.
    wide_name_width = _wide_name_width(term_width) if layout == "wide" else None
    wide_ctx_width = _wide_ctx_width(term_width) if layout == "wide" else None
    n_mem_total = sum(1 for s in sessions if getattr(s, "mem_worker", False))
    mem_by_group = {}
    for s in sessions:
        if getattr(s, "mem_worker", False):
            gk_mem = _group_key_session(s)
            mem_by_group[gk_mem] = mem_by_group.get(gk_mem, 0) + 1
    # F-19 repo rows: session-id -> display title, resolved on the ORIGINAL (unfiltered) list
    # so a mem event's source session still resolves even after mem-worker/child filtering
    # below drops it from the visible rows.
    sid_titles = {s.session_id: (s.title or s.slug) for s in sessions
                  if s.session_id and (s.title or s.slug)}
    # F-29 — a dispatched child session's own sub-agents survive the is_child filter below:
    # they re-attach as a strip under the dispatch row representing the child (pid join,
    # the same join title adoption uses — 사용자 2026-07-16 "서브 세션에 서브 에이전트도").
    child_subs_by_pid = {s.pid: s.subagents for s in sessions
                         if getattr(s, "is_child", False) and getattr(s, "subagents", None)}
    # headless dispatch children are shown as dispatch rows under their parent — never as
    # top-level sessions (the same headless process would otherwise double-show as session+job).
    # mem-worker sessions are excluded from grouping/census by default (F-18b) — they inherit
    # parent cwd/env and would otherwise misattribute into drill/project groups; `a` toggle
    # (_SHOW_ALL) restores them as a dedicated dim row (see _mem_row below).
    sessions = [s for s in sessions
                if not s.is_child and not (getattr(s, "mem_worker", False) and not _SHOW_ALL)]
    groups = {}
    session_groups = {}
    for s in sessions:
        gk = _group_key_session(s)
        groups.setdefault(gk, {"sessions": [], "jobs": []})["sessions"].append(s)
        if s.session_id:
            session_groups[s.session_id] = gk
    job_groups = {}
    # A route node has one current attempt. Keep older exact attempts in the alert
    # census/history, but suppress their rows by default so retries do not appear as
    # concurrent Fleet sessions. ``a`` restores the complete attempt history.
    top_jobs = [j for j in display_jobs if not (getattr(j, "parent_slug", None) and getattr(j, "depth", 1) >= 2)]
    depth_jobs = [j for j in display_jobs if getattr(j, "parent_slug", None) and getattr(j, "depth", 1) >= 2]
    for j in top_jobs + depth_jobs:
        gk = _group_key_job(j, session_groups=session_groups, job_groups=job_groups)
        groups.setdefault(gk, {"sessions": [], "jobs": []})["jobs"].append(j)
        if j.slug:
            job_groups[j.slug] = gk

    show_sessions = section in ("fleet", "both")
    show_jobs = section in ("dispatch", "both")

    order = sorted(groups.keys(), key=lambda name: _group_sort_key(name, groups[name]))

    lines = []
    # F-12(c) legend glyph-appearance tracking — LOCAL to this call (never module/global state,
    # _OFFSET invariant R3): which of the conditional legend glyphs actually got emitted this
    # build. working/idle/dispatch/`~` stay unconditional (always relevant vocabulary); the
    # rest (detached/stale/dead/child-jobs/worktrees) only show up in the legend when at least
    # one row used them.
    _seen_glyphs = set()
    # account-level usage — shared per harness/account. ONE LINE PER HARNESS (user 2026-07-01:
    # Use long gauges, generous gaps, and aligned windows.
    # rate is account-shared → take the FRESHEST session's value per harness (a stale session's
    # per-file rate is old; e.g. a 16-min-old file showed 7d 100% while the live rate was 15%).
    _rl = {}   # harness -> (rl_5h, rl_7d, rl_ms, mtime, rl_rs, rl_windows)
    for s in sessions:
        if s.rl_5h is not None or s.rl_7d is not None or s.rl_ms or getattr(s, "rl_windows", None):
            cur = _rl.get(s.harness)
            if cur is None or (s.mtime or 0) > (cur[3] or 0):
                _rl[s.harness] = (s.rl_5h, s.rl_7d, s.rl_ms, s.mtime, s.rl_rs,
                                  getattr(s, "rl_windows", None))
    # harnesses with LIVE sessions but no rate source still get a row with an explicit note —
    # A silently missing provider row looks like a bug.
    # opencode-go has no usage API (gateway 404s; docs: console-only), so say so on the board.
    _live_h = set(s.harness for s in sessions
                  if s.liveness not in ("stale", "dead") and not s.app_server and not s.is_child
                  and not getattr(s, "mem_worker", False))
    if _rl or _live_h:
        hs = [h for h in ("claude", "codex", "opencode") if h in _rl or h in _live_h]
        for idx, h in enumerate(hs):
            hn = _BADGE_TEXT.get(h, h)
            row = [("  usage " if idx == 0 else "        ", "head"),
                   (_pad(hn, 14), "hb_" + h if h in _BADGE_TEXT else "hb_other")]  # bright = account
            if h not in _rl:
                row.append(("no usage api — plan quota is console-only", "dim"))
                lines.append(row)
                continue
            r5, r7, rms, _mt, rrs, rwins = _rl[h]
            # Dynamic windows + per-model buckets — ALL labels dim (a colored 'fable' read like a harness).
            # htop BRACKET METERS (round-4): `[━━━━──────── 33%]` — the bracket draws the capacity
            # vessel, % sits inside. Session-row ctx gauges stay bare (htop's list bars are bare too).
            # ↻ = time until the window resets (API resets_at — was collected and discarded).
            gw = 8 if layout != "wide" else 12
            rs5, rs7 = (rrs or (None, None))[0], (rrs or (None, None))[1]
            if rwins:
                gauges = [(str(lbl) + " ", pct, reset) for lbl, pct, reset in rwins]
            else:
                gauges = [("5h ", r5, rs5), ("7d ", r7, rs7)]
            gauges += [(lbl + " ", v, None) for lbl, v in (rms or [])]
            now_ts = time.time()
            for gi, (lbl, v, rs) in enumerate(gauges):
                row.append(("   ", None) if gi else ("", None))          # 3-col gap between meters
                row.append((lbl, "dim"))
                row.append(("[", "dim"))
                if v is not None:
                    row += _gauge_segs(v, gw)
                    row.append((" %3d%%" % v, _pct_key(v)))
                else:
                    row += [("·" * gw, "dim"), ("   —", "dim")]
                row.append(("]", "dim"))
                if rs and rs > now_ts:
                    row.append((" ↻ " + fmt_min(int((rs - now_ts) / 60)), "dim"))
            lines.append(row)
    # fleet pulse — htop's "Tasks: N, M running" analogue: whole-board census + live spend Σ
    # Show the row by default; counts skip app-server companions. Extracted into _pulse_segs
    # (F-30, v10) so the process view (§5.1) shares this EXACT row instead of a second copy.
    # `_real` stays a LOCAL here too — the alert strip below (ctx_items) still needs it.
    _real = [s for s in sessions if not s.app_server and not getattr(s, "mem_worker", False)]
    lines.append(_pulse_segs(sessions, display_jobs))  # Aggregate cost rollup intentionally removed.
    _governor = _governor_segs()               # F-28c — pulse-adjacent, never merged into pulse
    if _governor is not None:                  # counts (I8); None = source absent or quiet.
        lines.append(_governor)
    _mem_summary = _mem_summary_segs(memory)
    if _mem_summary is not None:
        lines.append(_mem_summary)
        _seen_glyphs.add("mem")
    if _SHOW_ALL:
        _mem_events = _mem_event_rows(memory)
        if _mem_events:
            lines.extend(_mem_events)
            _seen_glyphs.add("mem")

    # alert strip — CONDITIONAL (zero lines when healthy): compaction-imminent contexts and
    # stalled dispatches (the stealth-death guard §5.10, surfaced on the board instead of only
    # in dispatch-liveness.sh runs). dead jobs = red, warnings = yellow.
    # F-10: names go through the same compaction as dispatch rows (_compact_dispatch_name) with
    # a loop job's `<case>-<ts>-<pid>` tail stripped first (raw timestamps/pids are noise here);
    # same-kind alerts aggregate into one line (`⚠ 2 dead jobs: a·b`), bucketed dead/stale/ctx.
    def _alert_name(name):
        return _compact_dispatch_name(_ALERT_TAIL.sub("", name or "") or (name or "?"), 20)

    def _bucket_text(label, names):
        if not names:
            return None
        if len(names) == 1:
            return "%s %s" % (label, names[0])
        shown = "·".join(names[:4])
        more = " +%d" % (len(names) - 4) if len(names) > 4 else ""
        return "%d %s jobs: %s%s" % (len(names), label, shown, more)

    dead_names = [_alert_name(j.slug or j.key) for j in jobs if j.liveness == "dead"]
    stale_names = [_alert_name(j.slug or j.key) for j in jobs if j.liveness == "stale"]
    ctx_items = [(s.slug or "?", s.ctx_pct) for s in _real
                 if s.ctx_pct is not None and s.ctx_pct >= 80 and s.liveness in ("working", "idle")]

    buckets = []
    dead_text = _bucket_text("dead", dead_names)
    if dead_text:
        buckets.append((dead_text, "lvl_r"))
    stale_text = _bucket_text("stale", stale_names)
    if stale_text:
        buckets.append((stale_text, "lvl_y"))
    if ctx_items:
        worst = max(pct for _n, pct in ctx_items)
        ctx_text = _bucket_text("ctx-high", [_alert_name(n) for n, _p in ctx_items]) \
            if len(ctx_items) > 1 else "ctx %d%% %s" % (ctx_items[0][1], _alert_name(ctx_items[0][0]))
        buckets.append((ctx_text, "lvl_r" if worst >= 90 else "lvl_y"))
    mem_bucket = _mem_alert_bucket(memory)   # F-19 — last in priority (dead > stale > ctx > mem)
    if mem_bucket:
        buckets.append(mem_bucket)
        _seen_glyphs.add("mem")

    if buckets:
        # priority truncation dead > stale > ctx when the row would overflow — buckets are
        # already in that priority order, so drop from the tail. Budget mirrors the existing
        # dormant-dirs line convention (`names[:90]`) rather than a hardcoded terminal width.
        kept = list(buckets)
        while len(kept) > 1 and sum(len(t) for t, _k in kept) + 3 * (len(kept) - 1) > 100:
            kept.pop()
        arow = [("  alert ", "head")]
        for ai, (txt, akey) in enumerate(kept):
            if ai:
                arow.append(("   ", None))
            arow.append(("⚠ " + txt, akey))
        lines.append(arow)
    # usage/intel zone = PLAIN bg + a full-width dim rule below it (user 2026-07-03: intel
    # Keep tint directory-only so the intelligence zone is not confused with active cards.
    lines.append([(_HFILL, None)])

    # header bar REPLACES the `──` zone divider — htop separates meters from the process list
    # with its bar, not a rule. Leave one blank line above it so
    # the top intel zone and the bar don't touch. Narrow mode's 2-line cards have no single
    # column mapping → the bar degrades to a zone label + current-mode hint.
    # Column header uses plain dim labels; tinted panels carry the visual grouping.
    lines.append(None)
    _sh = " " * (_INSET + _PAD_IN) if _TINT_OK else ""   # shift matches panel content columns
    if layout != "wide":
        lines.append([(_sh + "  SESSIONS", "head"), (_RFLUSH, None),
                      ("%s · press w to cycle  " % layout, "head")])
    else:
        # right-flushed 'time' label sits over the (inset) elapsed-time column — trailing
        # spaces mirror the tint rows' right inset so the label right-aligns with the values.
        lines.append([(_sh + _col_head(wide_name_width or _NW_S), "head"), (_RFLUSH, None),
                      ("time" + " " * (_INSET + _PAD_IN + 1), "head")])
    lines.append(None)                  # Gap below the column header.

    first = True
    folded_groups = []       # dormant dirs — aggregated into ONE line at the bottom (user: the
                             # stack of per-dir folded rules at the bottom was visual noise)
    for name in order:
        g = groups[name]
        group_sessions = g["sessions"] if show_sessions else []
        group_jobs = g["jobs"] if show_jobs else []
        if not _SHOW_ALL:
            group_jobs = [j for j in group_jobs if j.liveness != "dead"]
        if not group_sessions and not group_jobs:
            continue    # empty-group suppression per --section: no dangling header

        # group fold decision (R4) — computed BEFORE emitting anything for this group.
        live_sessions = [s for s in group_sessions
                          if s.liveness not in ("stale", "dead") and not s.app_server]
        must_show_jobs = bool(group_jobs)   # conservative: any job present blocks the fold
        fold = (not _SHOW_ALL) and (not live_sessions) and (not must_show_jobs)

        if fold:
            folded_groups.append((name, len(group_sessions)))
            continue

        if not first:
            lines.append(None)
        first = False

        shown = (group_sessions if _SHOW_ALL else
                 [s for s in group_sessions
                  if not (s.liveness in ("stale", "dead") or s.app_server)])
        hidden = len(group_sessions) - len(shown)
        shown_sids = set(s.session_id for s in shown if s.session_id)
        shown_cwds = {}
        ambiguous_cwds = set()
        for s in shown:
            if not s.cwd or not s.session_id:
                continue
            key_cwd = os.path.realpath(s.cwd)
            if key_cwd in shown_cwds:
                ambiguous_cwds.add(key_cwd)
            else:
                shown_cwds[key_cwd] = s.session_id
        for key_cwd in ambiguous_cwds:
            shown_cwds.pop(key_cwd, None)

        # pre-assemble session -> child-jobs and job -> sub-job maps before emitting rows.
        # Dispatch-depth-1 jobs can nest under an on-screen parent session; dispatch-depth-2 jobs nest under
        # their capability-owner job via parent_slug. This keeps main-session context light
        # while fleet still shows cross-harness orchestration shape.
        children = {}      # session_id -> [jobs] (nested under an on-screen parent)
        job_children = {}  # parent dispatch slug -> [dispatch-depth-2 jobs]
        orphans = []       # project-level fallback (parent dead/off-screen/no-env)
        loops_jobs = []    # no-parent-is-normal (cron loops) — no orphan marker
        visible_parent_slugs = {
            j.slug for j in group_jobs
            if j.slug and max(1, int(getattr(j, "depth", 1) or 1)) < 2
        }
        for j in group_jobs:
            if getattr(j, "parent_slug", None) and getattr(j, "depth", 1) >= 2:
                if j.parent_slug in visible_parent_slugs:
                    job_children.setdefault(j.parent_slug, []).append(j)
                else:
                    # A malformed/stale parent edge must not make a live dispatch-depth-2 row
                    # disappear from Fleet. Surface it as a project-level orphan.
                    orphans.append(j)
            elif j.is_child and j.parent_sid and j.parent_sid in shown_sids:
                children.setdefault(j.parent_sid, []).append(j)
            elif j.is_child and getattr(j, "parent_cwd", None):
                sid = shown_cwds.get(os.path.realpath(j.parent_cwd))
                if sid:
                    children.setdefault(sid, []).append(j)
                elif j.key in _LOOPS_KEYS:
                    loops_jobs.append(j)
                else:
                    orphans.append(j)
            elif j.key in _LOOPS_KEYS:
                loops_jobs.append(j)
            else:
                orphans.append(j)

        gcwd = "" if name == "loops" else (group_sessions[0].cwd if group_sessions else
                (group_jobs[0].cwd if group_jobs else ""))
        # The section title has no indicator glyph; the title itself carries active state.
        # while the group works, plain bold otherwise. Doubles with the active card tint.
        n_work = sum(1 for s in live_sessions if s.liveness == "working") + \
                 sum(1 for j in group_jobs if j.liveness == "working")
        # cooling (round-6, user 2026-07-03): no active work, but the newest session transcript
        # A write within the cooling window indicates a directory that just finished.
        # state between hot (green ●) and cold (no glyph): a grey ring + time-since-done, so a
        # just-finished repo reads as "done & waiting" rather than fully dormant. Sessions linger
        # as idle (still within the 48h live window), so the group is not folded (R4).
        _last_act = max((s.mtime for s in group_sessions if s.mtime), default=None)
        _cool_min = None
        if not n_work and _last_act is not None:
            _age = (time.time() - _last_act) / 60.0
            if 0 <= _age <= _COOL_WINDOW_MIN:
                _cool_min = int(_age)
        # trailing slash = the universal "this is a directory" marker (ls convention — user
        # Keep the folder marker dim so the repository name remains the focal point.
        # The blinking green ● now lives HERE (directory level = "work happening inside") —
        # sessions animate a spinner instead, so the dot no longer collides with row vocabulary.
        head_segs = []
        if n_work:
            head_segs += [("●", "g_work" if _BLINK_ON else "g_work_off"), (" ", None)]
        elif _cool_min is not None:
            # Recent completion uses a filled grey dot, distinct from dead and stale.
            head_segs += [(_COOL_FILLED, "grp_cool"), (" ", None)]
        else:
            # Long inactivity uses a grey ring.
            head_segs += [(_COOL_RING, "grp_cold"), (" ", None)]
        # Cooling names share the dim-yellow indicator color; cold keeps the default title color.
        _name_key = "grp_hot" if n_work else ("grp_cool" if _cool_min is not None else "grp")
        head_segs += [(name, _name_key), ("/", "dim")]
        _nwt = _wt_count(gcwd)
        if _nwt:
            # Match statusline notation for parallel or leftover worktrees.
            head_segs += [(" 🚧 %d" % _nwt, "g_idle")]
            _seen_glyphs.add("wt")
        _nmem = mem_by_group.get(name, 0)
        if _nmem:
            head_segs += [(" 🧠 %d" % _nmem, "dim")]
            _seen_glyphs.add("mem")
        if _cool_min is not None:
            # Prefix time since completion with a check mark.
            head_segs += [("  ", None), ("%s %s" % (_COOL_TIME_ICON, fmt_min(_cool_min)), "grp_cool")]
        # The group header is the card's first title row.
        # tinted row of the panel, ▍ anchor on the card's padding edge; no floating label.
        _g0 = len(lines)                # panel start (title INCLUDED in the tint range)
        lines.append(head_segs)
        _rail_key = "grp_live" if n_work else "dim"
        if n_work:
            _body_tint = _TINT_BODY_HOT       # Active: midnight-blue tint.
        elif _cool_min is not None:
            _body_tint = _TINT_BODY_COOL      # Cooling: middle level between active and inactive.
        else:
            _body_tint = _TINT_BODY           # Inactive: dark grey.

        # rows stay tight (no blank line — that spread them too far apart); the mid-line gauge
        # glyph (━/─) is what keeps the stacked context bars from merging into a solid wall.
        _srow = {"wide": None, "narrow": _session_row_2line, "stack": _session_row_stack}[layout]
        _jrow = {"wide": None, "narrow": _dispatch_row_2line, "stack": _dispatch_row_stack}[layout]
        # LIVE main-session lines get bold text (user 2026-07-03, after a whole-row tint-
        # Use font weight rather than brightening the entire row background.
        # carries the distinction). Excludes stale/dead/app-server/detached (already faded dim).
        _sess_bold_ids = set()

        def _emit_dispatch_tree(job, parent_model=None, parent_harness=None, parent_effort=None,
                                orphan=False, is_last=True):
            # SD-F2 — a dispatch-depth-1 conductor's OWN breadcrumb tracks its active dispatch-depth-2 stage
            # worker, not its static argv/plan-derived `stage`. `job_children` is the
            # enclosing closure dict, so this is readable before the row renders.
            stage_override = _conductor_stage_override(job)
            # F-28b (v10) — a resolved route (found via a dispatch-depth-2 CHILD's route_id, since the
            # env/pipe route link is attached to the stage worker, not the dispatch-depth-1 conductor
            # row itself — dispatch.py §3.2) replaces the hardcoded `_PIPE_STAGES` breadcrumb.
            route_seq = _conductor_route_seq(job)
            if job.liveness == "stale":
                _seen_glyphs.add("stale")
            elif job.liveness == "dead":
                _seen_glyphs.add("dead")
            # A child may cross harnesses (for example Codex -> Claude). Never fill an
            # unknown Claude model/effort with the Codex parent's telemetry.
            same_runtime = not job.harness or not parent_harness or job.harness == parent_harness
            row_parent_model = parent_model if same_runtime else None
            row_parent_effort = parent_effort if same_runtime else None
            # F-27: a job row is a target only with an exact pid to verify (prd.md:253).
            if job.pid:
                _SELECTABLE.append(_select_entry_job(job, len(lines)))
            if _jrow:
                lines.extend(_jrow(job, orphan=orphan, parent_model=row_parent_model,
                                   parent_effort=row_parent_effort, stage_override=stage_override,
                                   route_seq=route_seq))
            else:
                lines.append(_dispatch_row(job, orphan=orphan, parent_model=row_parent_model,
                                           parent_harness=parent_harness,
                                           parent_effort=row_parent_effort, is_last=is_last,
                                           stage_override=stage_override,
                                           name_width=wide_name_width, route_seq=route_seq))
                # F-16/F-17 merge — the job's own adopted live subtitle, directly under
                # its row and before its sub-agent strip; silent when absent/dead/stale.
                job_summary = getattr(job, "summary", None)
                if job_summary and job.liveness not in ("stale", "dead"):
                    lines.extend(_summary_row(
                        job_summary, depth=max(1, int(getattr(job, "depth", 1) or 1)),
                        term_width=term_width))
            # F-29 — the child session's own sub-agents, one strip directly under the
            # dispatch row that represents it (depth-indented; active always, completed
            # only with `a` — the same convention as session-owned strips above).
            job_subs = child_subs_by_pid.get(job.pid) if job.pid else None
            shown_job_subs = [sa for sa in (job_subs or []) if sa.active or _SHOW_ALL]
            if shown_job_subs:
                lines.extend(_subagent_strip(
                    shown_job_subs, depth=max(1, int(getattr(job, "depth", 1) or 1))))
            for sub in _sort_group_jobs(job_children.get(job.slug, [])):
                # F-15b P0-2: a dispatch-depth-2 stage worker that is done/queued/idle is already
                # absorbed into the conductor's own breadcrumb (✓/dim future segment) — only
                # working (active) or stale/dead (failed, needs to be seen) children get their
                # own row. `_SHOW_ALL` (the existing `a`-key toggle) restores the folded ones.
                if (max(1, int(getattr(sub, "depth", 1) or 1)) >= 2 and not _SHOW_ALL
                        and sub.liveness in _FOLD_CHILD_LIVENESS):
                    continue
                _emit_dispatch_tree(sub, parent_model=job.model or parent_model,
                                    parent_harness=job.harness or parent_harness,
                                    parent_effort=parent_effort, orphan=False)

        def _conductor_stage_override(job):
            # F-28b (§4.2): a route-carrying active child names its OWN node id (the real
            # pipeline node, e.g. "eval-asr") — that outranks the `_STAGE_ROLE` role-label
            # lookup, which only knows the fixed code-plan/-execute/-test/-report vocabulary.
            depth2 = [k for k in job_children.get(job.slug, []) if getattr(k, "depth", 1) == 2]
            active_routed = [k for k in depth2
                             if k.liveness == "working" and getattr(k, "route_node", None)]
            if active_routed:
                return active_routed[0].route_node
            # Some checked Codex dispatches carry a portable persona
            # (`development`) in worker_role while the job key is the actual stage
            # capability (`code-execute`). Reuse the row-label resolver so the
            # conductor and its child cannot disagree about the active stage.
            kids = [(k, _dispatch_stage_label(k)) for k in depth2]
            kids = [(k, label) for k, label in kids if label is not None]
            if not kids:
                return None
            active = [label for k, label in kids if k.liveness == "working"]
            if active:
                return active[0]
            return job.stage

        def _conductor_route_seq(job):
            """[(node_id, state), ...] | None — resolved via a dispatch-depth-2 CHILD's route_id (the
            dispatch-depth-1 conductor row itself rarely carries route_id — dispatch.py attaches the
            env/pipe route link to the stage WORKER, §3.2). `None` means "no resolved route",
            the pre-v10 breadcrumb path (record-less or a load failure — tolerant, prd.md:303)."""
            depth2 = [k for k in job_children.get(job.slug, []) if getattr(k, "depth", 1) == 2]
            rid = next((getattr(k, "route_id", None) for k in depth2
                       if getattr(k, "route_id", None)), None) or getattr(job, "route_id", None)
            if not rid:
                return None
            view = _route_views_by_id.get(rid)
            if not view or not view.get("nodes"):
                return None
            return [(n["id"], n["state"]) for n in view["nodes"]]

        rendered_parent_sids = set()  # ambiguous enrichment must not duplicate a dispatch tree
        for s in _sort_group_sessions(shown):
            if getattr(s, "mem_worker", False):
                # Memory rows use a dedicated dim summary and appear only after the ``a`` toggle.
                lines.extend(_mem_row(s, layout))
                _seen_glyphs.add("mem")
                continue
            kids = _sort_group_jobs(children.get(s.session_id, []))
            if s.session_id in rendered_parent_sids:
                kids = []
            elif s.session_id:
                rendered_parent_sids.add(s.session_id)
            nested_n = len(kids) + sum(len(job_children.get(k.slug, [])) for k in kids)
            if s.liveness == "stale":
                _seen_glyphs.add("stale")
            elif s.liveness == "dead":
                _seen_glyphs.add("dead")
            elif s.liveness == "unused":
                _seen_glyphs.add("unused")
            if s.detached and s.liveness not in ("stale", "dead"):
                _seen_glyphs.add("detached")
            if nested_n:
                _seen_glyphs.add("child")
            if getattr(s, "subagents", None):
                _seen_glyphs.add("subagent")
            _n0 = len(lines)
            if _selectable_session(s):
                _SELECTABLE.append(_select_entry(s, _n0))    # F-27 target map
            if _srow:
                lines.extend(_srow(s, is_parent=bool(nested_n), child_count=nested_n,
                                   term_width=term_width))
            else:
                lines.append(_session_row(s, narrow, is_parent=bool(nested_n),
                                          child_count=nested_n,
                                          name_width=wide_name_width,
                                          ctx_width=wide_ctx_width))
            if not (s.liveness in ("stale", "dead") or s.app_server or s.detached):
                _sess_bold_ids.update(range(_n0, len(lines)))
            if _srow is None:
                # F-16/F-17 merge — the session's own live subtitle, directly under its
                # row and before its sub-agent strip; silent when absent/dead/stale.
                sess_summary = getattr(s, "summary", None)
                if sess_summary and s.liveness not in ("stale", "dead"):
                    lines.extend(_summary_row(sess_summary, term_width=term_width))
            # F-29 (v9) — sub-agent rows, directly under the parent session's own row(s).
            # Active always shown; completed only surface with `a` (F-18b dim-row convention).
            shown_subs = [sa for sa in (getattr(s, "subagents", None) or [])
                         if sa.active or _SHOW_ALL]
            if shown_subs:
                lines.extend(_subagent_strip(shown_subs))
            for i, cj in enumerate(kids):
                _emit_dispatch_tree(cj, parent_model=s.model, parent_harness=s.harness,
                                    parent_effort=s.effort, orphan=False,
                                    is_last=(i == len(kids) - 1))
        if group_sessions and hidden:
            lines.append([("     +%d stale/companion hidden" % hidden, "dim")])

        # orphans / loops: project-level fallback (standalone tree rows)
        for oj in _sort_group_jobs(orphans):
            _emit_dispatch_tree(oj, orphan=show_sessions)
        for lj in _sort_group_jobs(loops_jobs):
            _emit_dispatch_tree(lj, orphan=False)

        # F-19 repo rows (사용자 확정 2026-07-16): this card's own today-mem events, below a
        # subtle in-band divider — entirely silent when the repo has none (healthy-silent,
        # §4.7 F-19 convention). Rides the same body-tint loop below, unmodified.
        repo_events = (memory or {}).get("by_repo", {}).get(name) if memory else None
        if repo_events:
            lines.append(_mem_divider(term_width))
            lines.extend(_mem_repo_rows(repo_events, sid_titles))

        # group BODY (round-5): every row of the group rides the body tint — the whole directory
        # The whole directory block is one panel, brighter when active.
        # Fallback (_TINT_OK False → 8-color): the previous ▍ rail marks the block instead.
        for _i in range(_g0, len(lines)):
            ln = lines[_i]
            if not ln or _is_fill(ln[0][0]):
                continue
            if _TINT_OK:
                lines[_i] = [(_body_tint, None)] + ln
            elif ln[0][1] in (None, "dim") and ln[0][0].startswith(" "):
                lines[_i] = [("▍", _rail_key), (ln[0][0][1:], ln[0][1])] + ln[1:]
        for _i in _sess_bold_ids:
            ln = lines[_i]
            if not ln:
                continue
            if _is_fill(ln[0][0]) and ln[0][0][1] in _TINT_CHARS:
                lines[_i] = [ln[0], (_ROW_BOLD, None)] + list(ln[1:])
            else:
                lines[_i] = [(_ROW_BOLD, None)] + list(ln)
        if _TINT_OK:
            # breathing row below the title + bottom padding (title-top padding tried and
            # Insert one sentinel after the tint loop.
            lines.insert(_g0 + 1, [(_body_tint, None), ("  ", None)])
            lines.append([(_body_tint, None), ("  ", None)])

    # dormant dirs — one aggregated line, clearly set apart from the active board (blank + dim).
    # Contains the word 'folded' so the click-toggle map and `a` both still reveal them.
    if folded_groups:
        names = " · ".join(n for n, _c in folded_groups)
        total = sum(c for _n, c in folded_groups)
        lines.append(None)
        lines.append(([(" " * (_INSET + _PAD_IN), None)] if _TINT_OK else []) + [("· ", "dim"),
                      ("inactive  +%d folded   " % total, "dim"),
                      (names[:90] + ("…" if len(names) > 90 else ""), "dim")])

    if not order:
        lines.append([("  (no active sessions or dispatch jobs)", "dim")])

    if malformed:
        lines.append(None)
        lines.append([("  +%d malformed jobs.log rows skipped" % malformed, "dim")])

    # legend — status dots (columns are labelled by the header row). F-12(c): working/idle/
    # dispatch/`~` are always-relevant vocabulary and stay unconditional; the rest only appear
    # when this build actually used them (_seen_glyphs, tracked above — local, not global).
    lines.append(None)
    legend = [
        ("  ", None), ("⠹", "g_work"), (" working   ", "dim"),
        ("●", "g_work_off"), (" idle   ", "dim"),
    ]
    if "unused" in _seen_glyphs:
        legend += [(_LIVE_GLYPH["unused"], "g_unused"), (" unused   ", "dim")]
    if "detached" in _seen_glyphs:
        legend += [(_DETACHED_GLYPH, "g_work_off"), (" detached   ", "dim")]
    if "stale" in _seen_glyphs:
        legend += [("·", "g_stale"), (" stale   ", "dim")]
    if "dead" in _seen_glyphs:
        legend += [("✕", "g_dead"), (" dead     ", "dim")]
    if "child" in _seen_glyphs:
        legend += [("▾N", "dim"), (" child jobs   ", "dim")]
    if "subagent" in _seen_glyphs:
        legend += [(_ICON_SUBAGENT, "dim"), (" sub-agent   ", "dim")]
    if jobs:
        legend += [("↳", "dim"), (" dispatch   ", "dim")]
    if "wt" in _seen_glyphs:
        legend += [("🚧 N", "dim"), (" worktrees   ", "dim")]
    if n_mem_total or "mem" in _seen_glyphs:
        # Always expose the board-wide memory total in the legend, even when memory-only groups fold.
        legend += [("🧠 %d" % n_mem_total, "dim"), (" mem   ", "dim")]
    # F-9(d) `~ derived/inherited value` retired with the marker itself (user 2026-07-16:
    # inherited effort now shows plain — the tilde read as noise).
    lines.append(legend)

    return lines


# ---------- plain (--once) ----------
def _plain(segs):
    if segs is None:
        return ""
    out = []
    for t, _ in segs:
        if _is_fill(t):
            if t[1] in _TINT_CHARS or t[1] == "!":
                continue                       # tint/bold sentinel — no visible text
            out.append("─────" if t == _HFILL else "   ")
        else:
            out.append(t)
    return "".join(out)


def _collect_memory():
    # F-19: best-effort — a collector import/read failure must never break the render.
    try:
        from .collectors import memory as memcol
        return memcol.collect()
    except Exception:
        return None


def render_once(collect_all, hfilter, section):
    sessions, jobs = collect_all(harness_filter=hfilter)
    malformed = _malformed()
    mem_snapshot = _collect_memory()
    try:
        import shutil
        tw = shutil.get_terminal_size().columns
    except Exception:
        tw = 200
    lines = _build_lines(sessions, jobs, section, narrow=False, malformed=malformed,
                         layout=_layout_mode(tw), memory=mem_snapshot, term_width=tw)
    out = "\n".join(_plain(l) for l in lines) + "\n"
    # Write UTF-8 bytes directly so the snapshot's box/braille glyphs survive a
    # non-UTF-8 console codepage (e.g. Windows cp949), which would otherwise raise
    # UnicodeEncodeError. Falls back to text stdout when buffer is unavailable.
    try:
        sys.stdout.buffer.write(out.encode("utf-8"))
        sys.stdout.buffer.flush()
    except (AttributeError, ValueError):
        sys.stdout.write(out)
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
_WIDE = set("🧠✨⏳📁🚀🛰⚡📋⚙📊🐛📈🔬💻⏱↻")


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


def _clip_w(s, maxw, ellipsis="…"):
    """Tail-cut `s` to display width maxw (head preserved), stopping at cell boundaries
    so a double-width char (e.g. Hangul) is never split in half. Appends `ellipsis` (width 1)
    when clipped — mirrors _compact_dispatch_name's ellipsis convention (F-14)."""
    s = s or ""
    if _dw(s) <= maxw:
        return s
    lim = maxw - (_cw(ellipsis) if ellipsis else 0)
    out, w = [], 0
    for ch in s:
        cw = _cw(ch)
        if w + cw > lim:
            break
        out.append(ch); w += cw
    return "".join(out) + (ellipsis if ellipsis else "")


# fill sentinels (3-char \x00<fill>\x00): everything after is right-aligned to the edge; the gap
# is filled with <fill> — space for _RFLUSH (invisible), ─ for _HFILL (a full-width rule).
_INSET = 2                  # Panel outer margin in columns.
_PAD_IN = 2                 # Extra inner padding between tint edge and content.
# Roles that make a line a full-width chrome BAR. A line is a bar when its FIRST segment says
# so — so any new bar variant must be registered here or the band silently never paints.
_BAR_ROLES = ("hdr_bar", "hdr_warn")

_RFLUSH = "\x00 \x00"
_HFILL = "\x00─\x00"

# row-tint sentinels (round-5 — herdr-style panel tints): a LEADING sentinel marks the whole
# row's background level. b/c = group body/cap · B/C = the ACTIVE-group variants (brighter,
# Active directories receive the stronger tint; ``i`` marks the intelligence zone.
_TINT_BODY, _TINT_CAP = "\x00b\x00", "\x00c\x00"
_TINT_BODY_HOT, _TINT_CAP_HOT = "\x00B\x00", "\x00C\x00"
_TINT_BODY_COOL = "\x00k\x00"    # Cooling body between active blue and inactive grey.
_TINT_INTEL = "\x00i\x00"
_TINT_CHARS = {"b", "c", "B", "C", "k", "i"}

# row-bold marker (user 2026-07-03, after the whole-row tint-brightening attempt was rejected —
# Main-session rows use bold rather than brightening the entire background.
# any other row in the card, font weight carries the distinction). Inserted AFTER any tint
# sentinel (so tint detection in _addline is unaffected) by the group-loop post-pass.
_ROW_BOLD = "\x00!\x00"
# 256-color background levels per sentinel char. Base panels = dark GREY (235/238); the
# Active-group variants use a dark midnight-blue tint. Color 17 is the cube's darkest blue.
# even where init_color is ignored (green 22 #005f00 read too bright — user ×2).
_TINT_LVL = {"b": 235, "c": 238, "B": 17, "C": 17, "k": 94, "i": 235}


def _is_fill(t):
    return len(t) == 3 and t[0] == "\x00" and t[2] == "\x00"


def _addline(stdscr, row, segs, w):
    if segs is None:
        return
    # leading row-tint sentinel (round-5 panels) — strip it FIRST so the fill scan below never
    # mistakes it for a fill sentinel; it sets the whole row's background level.
    tint = None
    if segs and _is_fill(segs[0][0]) and segs[0][0][1] in _TINT_CHARS:
        tint = segs[0][0][1] if _TINT_OK else None
        segs = segs[1:]
    # row-bold marker (user: main-session rows are entirely bold) — strip next, same reason.
    row_bold = False
    if segs and _is_fill(segs[0][0]) and segs[0][0][1] == "!":
        row_bold = True
        segs = segs[1:]
    # tinted panels are INSET two columns on both sides AND their content shifts inward with
    # them; near-black tint against the default background alone is
    # imperceptible; the margin must move the content). Band starts at col 2; the row's own
    # leading blanks become inner padding, so text sits at col 4+ while cols 0-1 stay default.
    start_col = _INSET if tint is not None else 0
    if tint is not None:
        segs = [(" " * _PAD_IN, None)] + list(segs)   # inner-left padding inside the band
    fillch = None
    left, right = segs, []
    for i, (t, _c) in enumerate(segs):
        if _is_fill(t):
            fillch = t[1]
            left, right = segs[:i], segs[i + 1:]
            break

    def _draw(seglist, start, lim=None):
        edge = (w - 1) if lim is None else lim
        col = start
        for text, color in seglist:
            if col >= edge:
                break
            avail = edge - col
            piece = ""
            pw = 0
            for ch in text:                                   # clip by display width, not len
                cw = _cw(ch)
                if pw + cw > avail:
                    break
                piece += ch
                pw += cw
            if piece:
                attr = _key_attr(color, tint)
                if row_bold:
                    attr |= curses.A_BOLD
                try:
                    stdscr.addstr(row, col, piece, attr)
                except curses.error:
                    pass
            col += pw
        return col

    endcol = _draw(left, start_col)
    # band lines (htop WHITE bars = full width · round-5 tint panels = inset cards) paint their
    # background across; tint rows stop at w-1 so the right margin stays on the default bg.
    bar = bool(segs) and segs[0][1] in _BAR_ROLES
    band = bar or tint is not None
    band_lim = w if bar else (w - _INSET)
    # The bar inherits its color from the leading role, so a warning bar paints red across the
    # full width exactly as the normal bar paints white — same structure, different severity.
    fill_key = segs[0][1] if bar else None     # tint rows fill with the default-hue tint pair
    if fillch is not None:              # right may be EMPTY (a bare full-width rule line) — the
        rw = sum(_dw(t) for t, _ in right)   # fill itself must still draw (bug: divider invisible)
        rpad = (2 + _PAD_IN) if tint is not None else 0   # right-flushed text sits in from the band edge
        rcol = max(endcol + (0 if fillch == "─" else 2), (band_lim if band else w - 1) - rw - rpad)
        if fillch == "─" and rcol > endcol:
            _draw([("─" * (rcol - endcol), "head")], endcol)  # fill the gap to make a full-width rule
        elif band and band_lim > endcol:
            # paint the ENTIRE gap to the band edge first, then draw `right` over it — glyph
            # width disagreements (⏱ = 2 cells in our table, 1 by wcwidth/tmux) otherwise leave
            # an unpainted hole immediately before the time.
            _draw([(" " * (band_lim - endcol), fill_key)], endcol, lim=band_lim)
        if right:
            _draw(right, rcol, lim=band_lim if band else None)
    elif band and endcol < band_lim:
        _draw([(" " * (band_lim - endcol), fill_key)], endcol, lim=band_lim)


_OFFSET = 0                 # scroll offset — READ only in _draw (see module docstring)
_TOGGLE_ROWS = {}            # screen_y -> True, reset at the top of every _draw (mouse click map)
_CLICK_ROWS = {}             # screen_y -> _SELECTABLE entry (F-27 v9 row click map, §4.2.1 —
                              # filled from _SELECTABLE, NOT _live_targets(): base mode's first
                              # click would otherwise never see a target, and gating on
                              # _live_targets() would call control.is_excluded() at ~10fps)
_FOLD_ROWS = {}               # screen_y -> card_key (F-30, v10) — filled from `_FOLDABLE` the
                              # same way `_CLICK_ROWS` is filled from `_SELECTABLE`. Reset at the
                              # top of every `_draw`, same as `_TOGGLE_ROWS`/`_CLICK_ROWS`.
_PROMPT_HITS = []             # [(screen_y, x0, x1, "kill"|"cancel")] — footer button hitboxes.
                              # Reset+rebuilt every _draw call (§4.4.1): a click 2 that lands
                              # before the next _draw must never see a stale (pre-transition)
                              # map, or the confirm→confirm2 coordinate inversion (§4.4) is
                              # silently defeated.

# --- F-27 selection mode (see _SELECTABLE stash contract in _build_lines) ---
# A MODED cursor, not a bare ↑↓ cursor: ↑↓ is already bound to scroll (a v2 contract, spec
# §3 key table), so taking it would regress scrolling for everyone who never kills anything.
# `s`/`x` enter, ↑↓/jk then move the cursor, Esc/s leave. Only the "enter" key differs from
# spec F-27's wording; the operating model (row cursor, ↑↓ move, x kill, confirm) is intact.
_SELECT_MODE = False
# The cursor is an IDENTITY (pid, proc_start), not a list index and not a screen row. An index
# silently re-aims when the board rebuilds under it: rows come and go every tick, so index 0
# can mean a different session one tick later — the user aims at A and the prompt names B.
# Anchoring on identity means a rebuild either finds the same target or finds nothing (and the
# selection drops), which are both honest outcomes.
_CURSOR_ID = None            # (pid, proc_start) | None
_PROMPT = None               # None | {"stage": confirm|confirm2|escalate, "entry": {...}}
_PENDING_KILL = None         # {"entry":..., "since": ts} — SIGTERM sent, grace running
_LAST_ACTION = None          # transient footer feedback string


def _clamp_offset(off, total, body_h):
    return max(0, min(off, max(0, total - body_h)))


# ---------------------------------------------------------------------------
# F-27 selection mode helpers. Kept out of _loop so they are testable without curses.
# ---------------------------------------------------------------------------

def _live_targets():
    """Selectable rows minus the ones that may never be signalled. The exclusion runs HERE,
    before anything can be selected — so fleet itself, its ancestry, and the driving session
    are never even reachable by a prompt (prd.md:253)."""
    from . import control
    out = []
    for e in _SELECTABLE:
        if not e.get("pid"):
            continue
        try:
            if control.is_excluded(e["pid"]):
                continue
        except Exception:
            continue                     # unresolvable → not a target (fail closed)
        out.append(e)
    return out


def _entry_id(e):
    return (e.get("pid"), e.get("proc_start"))


def _click_target_excluded(e):
    """§4.2.1 — the mouse path's exclusion check. `_CLICK_ROWS` is filled from `_SELECTABLE`
    (unfiltered), so exclusion is applied HERE, once, at click time — not every tick. The
    render.py:2207 contract ("filtered before a prompt") still holds: a click IS the selection
    attempt, so an excluded row is refused before it can ever reach `_PROMPT`."""
    from . import control
    pid = e.get("pid")
    if not pid:
        return True
    try:
        return control.is_excluded(pid)
    except Exception:
        return True                      # unresolvable → fail closed, same as _live_targets()


def _cursor_index(targets):
    """Where the cursor identity currently sits, or None if that target is gone."""
    if _CURSOR_ID is None:
        return None
    for i, e in enumerate(targets):
        if _entry_id(e) == _CURSOR_ID:
            return i
    return None


def _enter_select(targets):
    global _SELECT_MODE, _CURSOR_ID
    if not targets:
        return False
    _SELECT_MODE = True
    if _cursor_index(targets) is None:
        _CURSOR_ID = _entry_id(targets[0])
    return True


def _exit_select():
    global _SELECT_MODE, _PROMPT
    _SELECT_MODE = False
    _PROMPT = None


def reset_selection():
    """Public: drop all selection/prompt state (tests + fleet.py belt-and-suspenders)."""
    global _SELECT_MODE, _CURSOR_ID, _PROMPT, _PENDING_KILL, _LAST_ACTION
    _SELECT_MODE = False
    _CURSOR_ID = None
    _PROMPT = None
    _PENDING_KILL = None
    _LAST_ACTION = None


def _prompt_button_segs(stage, key):
    """[cancel]/[kill] click segments, in stage order (§4.4 coordinate inversion).

    confirm         → cancel-LEFT, kill-RIGHT
    confirm2/escalate → REVERSED: kill-LEFT, cancel-RIGHT

    The reversal is what makes a same-spot double-click fail-safe: confirm's [kill] (right)
    becomes confirm2's [cancel] (right) — the second click of a reflexive double-click lands
    on cancel, never on kill. See §4.4.1 for the staleness invariant this depends on."""
    kill_label = "[KILL]" if stage in ("confirm2", "escalate") else "[kill]"
    kill_seg = (kill_label, key)
    cancel_seg = ("[cancel]", key)
    if stage in ("confirm2", "escalate"):
        return [(" ", key), kill_seg, (" ", key), cancel_seg]
    return [(" ", key), cancel_seg, (" ", key), kill_seg]


def _prompt_variants(text_variants, stage, key):
    """Expand each text rung into a with-buttons rung, followed by a keyboard-only fallback
    at the SAME text width (buttons dropped). §4.5: when the buttons don't fit, the keyboard
    hint (and the name, if this rung still carries it) must not be sacrificed just to keep a
    click target — keyboard stays primary (prd.md:88·280). The final rung is never followed
    by a fallback: the narrowest rung is the guaranteed-fit floor and always carries buttons.
    """
    btn = _prompt_button_segs(stage, key)
    out = []
    last = len(text_variants) - 1
    for i, segs in enumerate(text_variants):
        out.append(list(segs) + btn)
        if i < last:
            out.append(list(segs))
    return out


def _prompt_hit_boxes(fsegs, row, width):
    """Click x-ranges for [kill]/[KILL]/[cancel] segments in fsegs, mirroring _addline's
    per-cell clip (:2126). A segment counts only if it was drawn WHOLE — a hitbox for a
    button that got clipped off the edge of the terminal must never survive (§4.5)."""
    hits = []
    col = 0
    edge = max(0, width - 1) if width else 0
    for text, _style in fsegs:
        if col >= edge:
            break
        avail = edge - col
        pw = 0
        for ch in text:
            cw = _cw(ch)
            if pw + cw > avail:
                break
            pw += cw
        stripped = text.strip()
        if stripped in ("[kill]", "[KILL]", "[cancel]") and pw == _dw(text):
            action = "cancel" if stripped == "[cancel]" else "kill"
            hits.append((row, col, col + pw, action))
        col += pw
    return hits


def _prompt_segs(prompt, width=None):
    """The confirmation bar. Always names the exact target and always shows the keys.

    A prompt is a safety affordance, not decoration: the footer is clipped at the terminal
    edge, so on a narrow screen the full phrasing would lose its tail — and the tail is where
    the keys are. ("press Y (capital) to kill" is 117 cells; at 60 the user would be asked to
    confirm without being told how.) Below the fit threshold every prompt therefore switches
    to a terse form that keeps the two things the user cannot act without: WHICH target, and
    WHICH keys. The pid is what survives on the identity side — it is unambiguous where a
    clipped name is not.
    """
    from . import control
    e = prompt["entry"]
    stage = prompt["stage"]
    who = "%s [pid %s] %s" % (e.get("label") or "?", e.get("pid"), e.get("state"))

    def pick(*variants):
        """First variant that fits. The ladder always ends in a pid-only form that fits any
        sane terminal, so a prompt can never be silently clipped."""
        for segs in variants:
            if width is None or sum(_dw(t) for t, _k in segs) <= width:
                return segs
        return variants[-1]

    if stage == "escalate":
        # SIGKILL — the one signal a process cannot refuse. It shares the warning bar with the
        # live-kill prompts: it is at least as destructive, so it may not read calmer than they do.
        return pick(*_prompt_variants([
            [(" ⚠ SIGTERM ignored for %ds — send SIGKILL to " % control.KILL_GRACE_SEC, "hdr_warn"),
             (who, "hdr_warn_key"), ("? press ", "hdr_warn"),
             ("Y", "hdr_warn_key"), (" (capital) · ", "hdr_warn"),
             ("Esc", "hdr_warn_key"), (" no", "hdr_warn")],
            [(" ⚠ SIGKILL ", "hdr_warn"), (who, "hdr_warn_key"), ("? ", "hdr_warn"),
             ("Y", "hdr_warn_key"), ("/", "hdr_warn"), ("Esc", "hdr_warn_key")],
            [(" ⚠ SIGKILL pid %s? " % e.get("pid"), "hdr_warn"),
             ("Y", "hdr_warn_key"), ("/", "hdr_warn"), ("Esc", "hdr_warn_key")],
        ], stage, "hdr_warn_key"))
    if stage == "confirm2":
        return pick(*_prompt_variants([
            [(" ⚠ LIVE session — confirm again: ", "hdr_warn"),
             (who, "hdr_warn_key"),
             (" — press ", "hdr_warn"), ("Y", "hdr_warn_key"),
             (" (capital) to kill · ", "hdr_warn"),
             ("Esc", "hdr_warn_key"), (" cancel", "hdr_warn")],
            [(" ⚠ LIVE — ", "hdr_warn"), (who, "hdr_warn_key"), (" — ", "hdr_warn"),
             ("Y", "hdr_warn_key"), (" kills · ", "hdr_warn"),
             ("Esc", "hdr_warn_key"), (" no", "hdr_warn")],
            [(" ⚠ LIVE pid %s — " % e.get("pid"), "hdr_warn"),
             ("Y", "hdr_warn_key"), (" kills · ", "hdr_warn"),
             ("Esc", "hdr_warn_key"), (" no", "hdr_warn")],
        ], stage, "hdr_warn_key"))

    warn = control.requires_double_confirm(e.get("state"), e.get("status"))
    if warn:
        return pick(*_prompt_variants([
            [(" ⚠ this session is WORKING — kill ", "hdr_warn"), (who, "hdr_warn_key"),
             ("? ", "hdr_warn"), ("y", "hdr_warn_key"), (" yes · ", "hdr_warn"),
             ("Esc", "hdr_warn_key"), (" cancel", "hdr_warn")],
            [(" ⚠ WORKING — kill ", "hdr_warn"), (who, "hdr_warn_key"), ("? ", "hdr_warn"),
             ("y", "hdr_warn_key"), ("/", "hdr_warn"), ("Esc", "hdr_warn_key")],
            [(" ⚠ kill pid %s (working)? " % e.get("pid"), "hdr_warn"),
             ("y", "hdr_warn_key"), ("/", "hdr_warn"), ("Esc", "hdr_warn_key")],
        ], "confirm", "hdr_warn_key"))
    # Benign target (unused/stale/dead). The middle rung matters: the full form overshoots 60
    # by ~3 cells, and dropping straight to pid-only would throw the NAME away while leaving
    # ~27 cells unused. Trim the decoration, keep the identity.
    return pick(*_prompt_variants([
        [(" kill ", "hdr_bar"), (who, "hdr_key"), ("? ", "hdr_bar"),
         ("y", "hdr_key"), (" yes · ", "hdr_bar"), ("Esc", "hdr_key"), (" cancel", "hdr_bar")],
        [(" kill ", "hdr_bar"), (who, "hdr_key"), ("? ", "hdr_bar"),
         ("y", "hdr_key"), ("/", "hdr_bar"), ("Esc", "hdr_key")],
        [(" kill pid %s (%s)? " % (e.get("pid"), e.get("state") or "?"), "hdr_bar"),
         ("y", "hdr_key"), ("/", "hdr_bar"), ("Esc", "hdr_key")],
    ], "confirm", "hdr_key"))


_ESC = 27


def _set_action(msg):
    global _LAST_ACTION
    _LAST_ACTION = msg


def _handle_select_key(ch):
    """Selection-mode keys. True = handled here (do not fall through to scroll)."""
    global _CURSOR_ID, _PROMPT
    targets = _live_targets()
    if ch in (_ESC, ord("s"), ord("S")):
        _exit_select()
        return True
    if not targets:
        _exit_select()
        return True
    i = _cursor_index(targets)
    if i is None:
        # The target under the cursor vanished (it finished, or it was killed). Re-anchor at
        # the top rather than guessing which row "replaced" it.
        _CURSOR_ID = _entry_id(targets[0])
        i = 0
        if ch in (ord("x"), ord("X")):
            return True                  # swallow this press: do not aim `x` at a row the
                                         # user never chose
    if ch in (curses.KEY_UP, ord("k")):
        _CURSOR_ID = _entry_id(targets[max(0, i - 1)])
        return True
    if ch in (curses.KEY_DOWN, ord("j")):
        _CURSOR_ID = _entry_id(targets[min(len(targets) - 1, i + 1)])
        return True
    if ch in (ord("x"), ord("X")):
        _PROMPT = {"stage": "confirm", "entry": targets[i]}
        return True
    return False        # q / r / a / w still work from selection mode


def _handle_base_key(ch, body_h):
    """Base-mode keys (scroll/a/w). True = handled. Kept out of _loop so scroll can be
    tested without curses — the F-27 regression budget is 0 and an untestable budget is
    not a budget."""
    global _OFFSET
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
    elif ch in (ord("w"), ord("W")):
        _cycle_layout()
    elif ch in (ord("p"), ord("P")):
        # F-30 (prd.md:305) — process view toggle. Deliberately orthogonal to `w` (layout
        # cycle keeps working inside the process view, same as the group view).
        set_process_view(not _PROCESS_VIEW)
    else:
        return False
    return True


def _getmouse_xy():
    """Extract getmouse() coords, or (None, None) on failure. A bare `except: my = None`
    (the pre-v9 shape) still calls the mouse handler with a stale/unbound `mx` from a PRIOR
    getmouse() (or unbound entirely on the first call) → NameError crashes the TUI. Returning
    a matched pair makes "couldn't read the event" and "read it" mutually exclusive states."""
    try:
        _, mx, my, _mz, _bstate = curses.getmouse()
    except Exception:
        return None, None
    return mx, my


def _handle_mouse(mx, my):
    """Mouse is the FIRST-CLASS F-27 path (prd.md:279). Returns True = handled.

    Precedence, in order — each rung is a different mode, and a click means a different
    thing in each:
      1. _PROMPT up  → only the [kill]/[cancel] hit-boxes act. A click anywhere ELSE on
         screen is swallowed (NOT a cancel): a stray click must never resolve a kill
         prompt in either direction. This mirrors _handle_prompt_key's "any other key is
         NOT consent" (render.py:2393).
      2. my in _TOGGLE_ROWS → the existing `+N hidden`/`folded` toggle. Checked before the
         row map because a toggle row is not a selectable row; the two maps never overlap.
      3. my in _FOLD_ROWS   → F-30 (v10) card/node fold-toggle — `_ROUTE_FOLD[card_key]` flips.
         Inserted here (its own rung, between the `a`-toggle and the F-27 row map) so a fold
         click can never be misread as either — I7/§5.4 B2: `_FOLD_ROWS` is disjoint from BOTH
         `_CLICK_ROWS` and `_TOGGLE_ROWS` by construction (`_draw` builds them from disjoint
         line sets, see its row loop).
      4. my in _CLICK_ROWS  → row click:
           · same identity as _CURSOR_ID → kill REQUEST → _PROMPT = {"stage": "confirm"}
           · different row              → move selection (_CURSOR_ID = id, _SELECT_MODE = True)
      5. otherwise → click outside any row → _exit_select()  (deselect, prd.md:279)

    The kill/cancel hit-boxes do not call control.kill_target directly — they replay the
    matching keyboard keystroke through _handle_prompt_key, so the mouse and keyboard share
    the exact same one decision path (§4.1: "kill 결정 경로는 하나").
    """
    global _CURSOR_ID, _SELECT_MODE, _PROMPT
    if _PROMPT is not None:
        for row, x0, x1, action in _PROMPT_HITS:
            if my == row and x0 <= mx < x1:
                if action == "kill":
                    _handle_prompt_key(ord("y") if _PROMPT["stage"] == "confirm" else ord("Y"))
                else:
                    _handle_prompt_key(_ESC)
                break
        return True                      # rung 1: every other click while prompted is swallowed
    if my in _TOGGLE_ROWS:
        set_show_all(not _SHOW_ALL)
        return True
    if my in _FOLD_ROWS:
        entry = _FOLD_ROWS[my]
        # Invert whatever was ACTUALLY drawn (entry["folded"] is the resolved state — default
        # OR a prior explicit choice, §5.4), never a re-guessed default — otherwise a card whose
        # default happens to be folded would need two clicks before anything visibly moves.
        _ROUTE_FOLD[entry["card_key"]] = not entry["folded"]
        return True
    if my in _CLICK_ROWS:
        entry = _CLICK_ROWS[my]
        reclick = _SELECT_MODE and _entry_id(entry) == _CURSOR_ID
        if _click_target_excluded(entry):
            return True                  # excluded rows are unreachable by click (§4.2.1)
        if reclick:
            _PROMPT = {"stage": "confirm", "entry": entry}
        else:
            _SELECT_MODE = True
            _CURSOR_ID = _entry_id(entry)
        return True
    _exit_select()
    return True


def _handle_prompt_key(ch):
    """Confirmation keys. The ONLY path in fleet that reaches control.kill_target."""
    global _PROMPT, _PENDING_KILL
    from . import control
    prompt, entry = _PROMPT, _PROMPT["entry"]
    stage = prompt["stage"]

    if ch in (_ESC, ord("n"), ord("N")):
        _PROMPT = None
        if stage == "escalate":
            _PENDING_KILL = None        # user declined SIGKILL → stop asking
        _set_action("cancelled")
        return
    if ch == -1:
        return                          # timeout tick, not a keypress — keep asking

    if stage == "confirm":
        if ch != ord("y"):
            return                      # any other key is NOT consent
        if control.requires_double_confirm(entry.get("state"), entry.get("status")):
            _PROMPT = {"stage": "confirm2", "entry": entry}   # live target → ask again
            return
        _PROMPT = None
        _do_kill(entry, "single")
        return
    if stage == "confirm2":
        # Deliberately a DIFFERENT key from stage 1: holding `y` cannot walk through both.
        if ch != ord("Y"):
            return
        _PROMPT = None
        _do_kill(entry, "double")
        return
    if stage == "escalate":
        # Capital `Y`, like confirm2 and for the same reason: SIGKILL is the most destructive
        # act here, so it must not be reachable by the same keystroke that started the SIGTERM.
        if ch != ord("Y"):
            return
        _PROMPT = None
        r = control.kill_target(entry["pid"], entry.get("proc_start"), entry.get("sid"),
                                entry.get("state"), "escalated",
                                registry_status=entry.get("status"),
                                is_worker=entry.get("is_worker", False),
                                kind=entry.get("kind", "session"))
        _PENDING_KILL = None
        _set_action("SIGKILL %s: %s" % (entry.get("label"), r))


def _do_kill(entry, approval):
    """SIGTERM + start the grace window. Never escalates on its own."""
    global _PENDING_KILL
    from . import control
    r = control.kill_target(entry["pid"], entry.get("proc_start"), entry.get("sid"),
                            entry.get("state"), approval,
                            registry_status=entry.get("status"),
                            is_worker=entry.get("is_worker", False),
                            kind=entry.get("kind", "session"))
    _set_action("SIGTERM %s: %s" % (entry.get("label"), r))
    if r == "ok":
        _PENDING_KILL = {"entry": entry, "since": time.time()}
        _close_job_row_if_registry(entry)


def _close_job_row_if_registry(entry):
    """prd.md:255 — after a successful kill of a registry JOB row, close it. Sessions never
    touch the registry."""
    from . import control
    if entry.get("kind") != "job" or entry.get("source") != "jobs":
        return
    if entry.get("status") != "open" or not entry.get("slug"):
        return
    try:
        from .collectors import dispatch as _dispatch
        for jobs_path in _dispatch._candidate_jobs_paths(None):
            if control.close_registry_row(jobs_path, entry["slug"], entry.get("cwd") or ""):
                control.log_action(action="close_row", pid=entry.get("pid"), sid=None,
                                   state=entry.get("state"), approval="single",
                                   result="ok", reason=entry["slug"])
                return
    except Exception:
        pass


def _poll_pending_kill():
    """Non-blocking grace check, called once per wake so the curses loop never stalls.

    When the grace expires and the target is still alive, this does NOT escalate — it raises
    a fresh prompt. Automatic escalation is exactly what prd.md:253 forbids.
    """
    global _PENDING_KILL, _PROMPT
    from . import control
    if not _PENDING_KILL or _PROMPT is not None:
        return
    entry = _PENDING_KILL["entry"]
    if time.time() - _PENDING_KILL["since"] < control.KILL_GRACE_SEC:
        return
    if not control.verify_target(entry["pid"], entry.get("proc_start")):
        _PENDING_KILL = None            # gone (or no longer provably the same process) → done
        _set_action("%s terminated" % entry.get("label"))
        return
    _PROMPT = {"stage": "escalate", "entry": entry}


_MOUSE_HINT_MIN_WIDTH = 100   # R2-3: mouse is opt-in (needs `set -g mouse on` in tmux); only
                              # advertise it where there is slack to spare — keyboard stays
                              # primary and unconditional (prd.md:88·280).


_PROCESS_HINT_MIN_WIDTH = 80  # F-30 (v10) — the base footer is already tight at 60 cols (§5.1
                              # "60열 footer가 이미 빡빡하다"); this one short segment gets its
                              # own (lower than the mouse hint's 100) width floor rather than
                              # sharing _MOUSE_HINT_MIN_WIDTH, which is about a DIFFERENT
                              # capability (mouse opt-in) and would tie the two together for no
                              # reason.


def _footer_segs(select_mode, parts, width=None):
    hint = [("click", "hdr_key"), (" row · ", "hdr_bar")] \
        if width is not None and width >= _MOUSE_HINT_MIN_WIDTH else []
    p_hint = [("p", "hdr_key"), (" %s · " % ("group" if _PROCESS_VIEW else "process"), "hdr_bar")] \
        if width is None or width >= _PROCESS_HINT_MIN_WIDTH else []
    if select_mode:
        return [(" ", "hdr_bar"),
                ("↑↓/jk", "hdr_key"), (" move · ", "hdr_bar"),
                ("x", "hdr_key"), (" kill · ", "hdr_bar"),
                ("Esc", "hdr_key"), (" cancel · ", "hdr_bar"),
                ("q", "hdr_key"), (" quit", "hdr_bar"),
                (_RFLUSH, None), (" ".join(parts) + " " if parts else "", "hdr_bar")]
    wlbl = "wide/narrow/stack" if _LAYOUT == "auto" else ("%s!" % _LAYOUT)
    return [(" ", "hdr_bar"),
            ("q", "hdr_key"), (" quit · ", "hdr_bar"),
            ("r", "hdr_key"), (" refresh · ", "hdr_bar"),
            ("a", "hdr_key"), (" all · ", "hdr_bar"),
            ("w", "hdr_key"), (" " + wlbl + " · ", "hdr_bar")] + p_hint + hint + [
            ("jk", "hdr_key"), (" scroll · ", "hdr_bar"),
            ("s", "hdr_key"), (" select · ", "hdr_bar"),
            ("g/G", "hdr_key"), (" top/end", "hdr_bar"),
            (_RFLUSH, None), (" ".join(parts) + " " if parts else "", "hdr_bar")]


def reset_scroll():
    global _OFFSET
    _OFFSET = 0


def _draw(stdscr, sessions, jobs, section, malformed, memory=None):
    global _OFFSET, _TOGGLE_ROWS, _CLICK_ROWS, _FOLD_ROWS, _PROMPT_HITS, _CURSOR_ID
    # reset before any early-return so a stale map never survives a click (§4.1 pattern) —
    # _PROMPT_HITS in particular must never carry the PRIOR stage's coordinates into this
    # draw (§4.4.1): that staleness is exactly what would defeat the confirm→confirm2
    # coordinate inversion.
    _TOGGLE_ROWS = {}
    _CLICK_ROWS = {}
    _FOLD_ROWS = {}
    _PROMPT_HITS = []
    h, w = stdscr.getmaxyx()
    stdscr.erase()
    narrow = w < _NARROW_CUTOFF
    lines = _build_lines(sessions, jobs, section, narrow, malformed, layout=_layout_mode(w),
                         memory=memory, term_width=w)
    body_h = max(1, h - 1)   # reserve 1 footer row

    # F-27: the cursor tracks a ROW, so the viewport follows it (not the reverse). Done before
    # the offset clamp so a cursor scrolled off-screen pulls the view back to itself.
    cur_line = None
    targets = _live_targets() if _SELECT_MODE else []
    if _SELECT_MODE and targets:
        i = _cursor_index(targets)
        if i is None:                    # the selected row is gone → re-anchor, never re-aim
            i = 0
            _CURSOR_ID = _entry_id(targets[0])
        cur_line = targets[i]["line"]
        if cur_line < _OFFSET:
            _OFFSET = cur_line
        elif cur_line >= _OFFSET + body_h:
            _OFFSET = cur_line - body_h + 1
    _OFFSET = _clamp_offset(_OFFSET, len(lines), body_h)

    # F-27 v9 (§4.2.1): the click map is built from _SELECTABLE, NOT _live_targets() — see the
    # module-level _CLICK_ROWS comment for why (base-mode first click / per-tick cost).
    _sel_by_line = {e["line"]: e for e in _SELECTABLE}
    # F-30 (v10, §5.4 Y2): same idiom, from `_FOLDABLE` (line-index map `_build_process_lines`
    # fills) to `_FOLD_ROWS` (screen-row map, offset-applied here — `_FOLDABLE` itself is only
    # ever line indices, exactly like `_SELECTABLE`).
    _fold_by_line = {e["line"]: e for e in _FOLDABLE}

    visible = lines[_OFFSET: _OFFSET + body_h]
    row = 0
    for segs in visible:
        _addline(stdscr, row, segs, w)
        fold_entry = _fold_by_line.get(_OFFSET + row)
        if fold_entry is not None:
            # ★ I7/§5.4 B2: a foldable row is decided FIRST and unconditionally — it never also
            # falls into the `_TOGGLE_ROWS` substring check below, even if its text happened to
            # contain "hidden"/"folded" (the card-label ban in _route_card/_degrade_card is the
            # other half of this invariant; this is the structural half).
            _FOLD_ROWS[row] = fold_entry
        elif segs is not None and len(segs) == 1 and (
                "hidden" in segs[0][0] or "folded" in segs[0][0]):
            _TOGGLE_ROWS[row] = True
        else:
            entry = _sel_by_line.get(_OFFSET + row)
            if entry is not None:
                _CLICK_ROWS[row] = entry
        row += 1
    if cur_line is not None and _OFFSET <= cur_line < _OFFSET + body_h:
        _highlight_row(stdscr, cur_line - _OFFSET, w)

    above = _OFFSET
    below = max(0, len(lines) - body_h - _OFFSET)
    parts = []
    if above:
        parts.append("↑%d" % above)
    if below:
        parts.append("↓%d" % below)
    # htop F-key bar (round-4): CYAN full-width, keycaps BOLD (dim is invisible on CYAN), the
    # scroll indicator rides the right edge. `w` cycles layout auto → narrow → wide.
    # A pending confirmation OWNS the footer: while it is up, the only thing that matters is
    # the decision in front of the user.
    fsegs = _prompt_segs(_PROMPT, w) if _PROMPT else _footer_segs(_SELECT_MODE, parts, w)
    _addline(stdscr, h - 1, fsegs, w)
    if _PROMPT:
        _PROMPT_HITS = _prompt_hit_boxes(fsegs, h - 1, w)
    stdscr.noutrefresh()
    curses.doupdate()


def _highlight_row(stdscr, y, w):
    """Reverse-video the cursor row. Painted over the already-drawn line so the row keeps its
    own colors and nothing about row assembly has to know about selection."""
    try:
        stdscr.chgat(y, 0, w, curses.A_REVERSE)
    except Exception:
        pass


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
    mem_snapshot = _collect_memory()
    last = time.time()
    _draw(stdscr, sessions, jobs, section, malformed, memory=mem_snapshot)
    while True:
        # wake exactly at the next 0.5s blink boundary (regular period) but stay key-responsive (≤200ms)
        _nb = (int(time.time() * 10) + 1) / 10.0   # 10fps wake — the spinner cadence
        stdscr.timeout(max(20, min(100, int((_nb - time.time()) * 1000) + 1)))
        ch = stdscr.getch()
        if ch in (ord("q"), ord("Q")):
            return 0
        h, w = stdscr.getmaxyx()
        body_h = max(1, h - 1)
        # --- F-27: a pending confirmation swallows ALL keys. Nothing else can happen while
        # the user is being asked, and only an explicit yes proceeds. ---
        if _PROMPT is not None:
            # §4.4.1 — _handle_mouse MUST be called from inside this block (not before it with
            # its own `continue`): the _draw two lines below is what repopulates _PROMPT_HITS
            # for the CURRENT stage before the next getch can land a click. Placing the mouse
            # call ahead of this block would let a click 2 read a stale (pre-transition) map
            # and silently defeat the confirm→confirm2 coordinate inversion (§4.4).
            if ch == curses.KEY_MOUSE:
                mx, my = _getmouse_xy()
                if mx is not None:
                    _handle_mouse(mx, my)
            else:
                _handle_prompt_key(ch)
            _draw(stdscr, sessions, jobs, section, malformed, memory=mem_snapshot)
            continue
        if _SELECT_MODE:
            if _handle_select_key(ch):
                _draw(stdscr, sessions, jobs, section, malformed, memory=mem_snapshot)
                continue
        elif ch in (ord("s"), ord("S"), ord("x"), ord("X")):
            # Enter selection mode. `x` doubles as the enter shortcut so the "press x to kill"
            # intent works from a cold start; it selects, it never kills on the first press.
            if not _enter_select(_live_targets()):
                _set_action("no selectable rows")
            _draw(stdscr, sessions, jobs, section, malformed, memory=mem_snapshot)
            continue

        # --- base mode: scroll keys UNCHANGED (F-27 regression budget = 0) ---
        if _handle_base_key(ch, body_h):
            pass
        elif ch == curses.KEY_MOUSE:
            mx, my = _getmouse_xy()
            if mx is not None:
                _handle_mouse(mx, my)
        # KEY_RESIZE: no special handling needed — _draw's clamp re-clamps against the new
        # body_h below; do NOT reset _OFFSET here (would destroy scroll position).

        force = ch in (ord("r"), ord("R"))
        now = time.time()
        if force or (now - last) >= interval:
            sessions, jobs = collect_all(harness_filter=hfilter)
            malformed = _malformed()
            mem_snapshot = _collect_memory()
            last = now
        _poll_pending_kill()     # F-27 grace window — non-blocking; may raise a re-prompt
        _BLINK_ON = (int(now * 2) % 2 == 0)     # ~2 Hz working-dot blink (manual — A_BLINK unreliable)
        # redraw every wake (covers KEY_RESIZE, blink and tick) — _draw clamps _OFFSET internally.
        _draw(stdscr, sessions, jobs, section, malformed, memory=mem_snapshot)


def run_live(collect_all, hfilter, section, interval):
    if curses is None:
        sys.stderr.write("fleet: the live TUI needs curses (unavailable here; on native "
                         "Windows run `pip install windows-curses`, or use WSL). "
                         "Use --once (snapshot) or --json meanwhile.\n")
        return 1
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
