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
import re
import sys
import time

from .model import fmt_min, dash, project_of

# harness = dim lowercase word in its identity color (no bracket chip, no reverse-video)
_BADGE_TEXT = {"claude": "claude code", "codex": "codex", "opencode": "opencode"}
_BADGE_KEY = {"claude": "h_claude", "codex": "h_codex", "opencode": "h_opencode"}
_LIVE_RANK = {"working": 0, "idle": 1, "blocked": 2, "done": 3, "stale": 4, "dead": 5, "unknown": 6}
_JOB_LIVE_RANK = {"working": 0, "stale": 1, "dead": 2, "unknown": 3}
# effort → 2-char suffix after the model (design review r2: the effort column repeated 'xhigh'
# everywhere and burned a column; a dim suffix keeps the info without the noise)
# qa rigor ramp (a dispatch job's analogue of effort) — quick recedes, adversarial stands out
_QA_INT = {"quick": curses.A_DIM, "light": curses.A_DIM, "standard": 0,
           "thorough": curses.A_BOLD, "adversarial": curses.A_BOLD}
_NARROW_CUTOFF = 70
_TWO_LINE_CUTOFF = 110      # width below which sessions render as 2-line cards (round-4 responsive)
_LAYOUT = "auto"            # 'auto' (width decides) | 'wide' | 'narrow' | 'stack' — `w` key cycles
_LOOPS_KEYS = ("oncall", "note", "study", "drill")


def _cycle_layout():
    global _LAYOUT
    _LAYOUT = {"auto": "wide", "wide": "narrow", "narrow": "stack", "stack": "auto"}[_LAYOUT]


def _layout_mode(w):
    """wide (1-line grid) / narrow (2-line cards) / stack (ultra-narrow, fields stacked
    vertically — user 2026-07-02: '세로로 나열하는 느낌'). auto: width decides."""
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
_A_B, _A_D = curses.A_BOLD, curses.A_DIM
_HUE_OF = {
    None: ("d", 0), "dim": ("d", _A_D), "head": ("d", _A_D), "unknown": ("d", _A_D),
    "name_work": ("d", _A_B), "name_idle": ("d", _A_B), "name_dim": ("d", _A_D),
    "grp": ("d", _A_B), "branch_s": ("d", 0), "cost_hi": ("d", _A_B),
    "qa_quick": ("d", _A_D), "qa_light": ("d", _A_D), "qa_standard": ("d", 0),
    "qa_thorough": ("d", _A_B), "qa_adversarial": ("d", _A_B),
    "g_work": ("g", _A_B), "g_work_off": ("g", _A_D), "g_idle": ("y", 0),
    "g_stale": ("d", _A_D), "g_dead": ("r", _A_B),
    "lvl_g": ("g", 0), "lvl_y": ("y", 0), "lvl_r": ("r", _A_B),
    "grp_live": ("g", 0), "grp_hot": ("g", _A_B), "gate_t": ("g", _A_D), "gate_u": ("y", _A_D),
    "eff_low": ("d", _A_D), "eff_medium": ("y", _A_D), "eff_high": ("y", 0),
    "eff_xhigh": ("y", _A_B), "eff_max": ("r", _A_B),
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
    # (effort heat ramp retired 2026-07-02 — user: effort 폰트는 기본색으로)
    # htop chrome (round-4, user: 헤더 행 배경색): the ONE background pair on screen — BLACK on
    # WHITE full-width bars wrapping the board (column-header bar + footer key bar). htop's CYAN
    # read as 촌스러움 (user 2026-07-02) → neutral white, the design round's V3 alternative.
    # Structural, one-shot — NOT a per-item classification color, so the fg color-axis budget
    # ("무지개 노이즈" rule) is untouched. dim is invisible on the bar → keycaps use BOLD.
    try:
        curses.init_pair(15, curses.COLOR_BLACK, curses.COLOR_WHITE)
        _COLOR["hdr_bar"] = curses.color_pair(15)
    except Exception:
        _COLOR["hdr_bar"] = curses.A_REVERSE
    _COLOR["hdr_key"] = _COLOR["hdr_bar"] | curses.A_BOLD
    # bar BLANKS are drawn as white-fg █ blocks on the DEFAULT bg (pair 16), not as bg-colored
    # spaces: ncurses collapses blank runs into ECH/EL erase sequences, and on terminals without
    # working BCE the erased cells come out BLACK — the bar broke between words and after the
    # text (user 2026-07-02: "헤더 안이어지는데" ×2). A block glyph is a real character, so it is
    # physically written every time and looks identical to a white background cell.
    try:
        curses.init_pair(16, curses.COLOR_WHITE, bg)
        _COLOR["hdr_blk"] = curses.color_pair(16)
    except Exception:
        _COLOR["hdr_blk"] = 0
    # round-5 panel tints (herdr 식 은은한 배경, 256-color only): (7 hue × tint level) pairs so
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
                    # ≈ #0e0f21 — slightly darker, desaturated (user 튜닝 이력: #005f00 너무
                    # 밝음 → #07081a 너무 어두움 → #0f123d 컬러 과함 → 이 값: 회색에 가까운
                    # 미드나잇, '컬러감은 죽이고')
                    curses.init_color(17, 55, 60, 130)
                    # 18 = the main-session variant of the active midnight (~#131523) — one
                    # whisper brighter than 17. Non-redefinable terminals fall back to 17
                    # (stock 18 #000087 would be loud) → no differentiation, never worse.
                    curses.init_color(18, 63, 68, 135)
            except Exception:
                pass
            if not curses.can_change_color():
                _TINT_LVL["S"] = 17
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


# status dot — SHAPE+SIZE gradient (design r2, a11y): the less active the state, the smaller
# the glyph. ● working (blinks) · ○ idle · ◍ detached · tiny '·' stale · ✕ dead. Readable
# without color (◌ vs ◦ were near-identical dim circles before).
_LIVE_GLYPH = {"working": "●", "idle": "●", "blocked": "◑", "done": "✓",
               "stale": "·", "dead": "✕", "unknown": "·"}
_DETACHED_GLYPH = "○"   # ring = 빈 자리(클라이언트 없음); idle 은 꽉 찬 dim ●
_GLYPH_KEY = {"working": "g_work", "idle": "dim", "blocked": "g_idle", "done": "green",
              "stale": "g_stale", "dead": "g_dead", "unknown": "dim"}


_BLINK_ON = True     # manual blink phase (toggled ~2 Hz in the live loop) — drives the spinner too
_SPIN = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"   # braille loading spinner — working SESSIONS animate (user 2026-07-03);
                     # the blinking green ● moved up to the directory title


def _glyph(state):
    """Session/job status glyph. working = braille spinner frame (green, advances every wake);
    idle = dim grey FILLED ●, detached = dim ring ○ (user 2026-07-03 최종)."""
    if state == "working":
        return _SPIN[int(time.time() * 10) % len(_SPIN)], "g_work"
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


def _wt_count(cwd):
    """Linked-worktree count for the repo owning `cwd` — counted from .git/worktrees/ entries
    (pure filesystem, no subprocess; follows a worktree's `gitdir:` file back to the main repo).
    Surfaces leftover/parallel worktrees that have no live session (user 2026-07-03: wt 개수)."""
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
_HW = 16                      # session harness field ("claude code" = 11 chars + 5 gap; user: 조금 더 넓게)
_BRANCH_COL = 48              # absolute col where branch starts (both row types)
_NAME_COL = 4 + _HW           # absolute col where the NAME starts — SHARED by both row types so
                              # everything from the name onward aligns (session: prefix 4 + harness
                              # 14; dispatch: prefix 6 + harness 12 — deeper indent, narrower harness)
_NW_S = _BRANCH_COL - _NAME_COL   # name field (both row types): col 18 → branch 46 = 28
_BRW = 14                     # ⎇branch field (always ≥1 trailing space so it never touches model)
_MW = 23                      # model cell: name + FULL effort word ('Opus 4.8 xhigh' — no abbrev)
_EFW = 7                      # effort subfield ("medium"=6 +1 gap) — FIXED width so every row's
                              # effort lands in the same column, under its own 'effort' header
_CTX_W = 16                   # context gauge (kept wide)
_CLOCK = ""                   # elapsed time = bare value (1d4h) — ⏱ had width bugs, 'up' read 이상함

# known pipeline stage sequences → the stage breadcrumb (process viz). Unknown keys/stages fall
# back to a single lit stage token (never a fabricated track). Keyed by the dispatch `key`.
_PIPE_STAGES = {
    "code": ["plan", "exec", "test"],
    "review": ["plan", "exec", "test"],
    "spec": ["spec", "design", "dev"],
    "research": ["search", "analyze", "report"],
    "draft": ["draft", "refine", "apply"],
}

# plain-text column labels (icons removed per user — "위에 아이콘들은 전부 빼자").
# 'effort' gets its OWN header over the fixed subcolumn inside the model cell (user 2026-07-02).
_COL_HEAD = ("    " + "harness".ljust(_HW) + "session".ljust(_NW_S)
             + "branch".ljust(_BRW) + "model".ljust(_MW)
             + "    context / stage")


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


def _branch_seg(cwd, branch, dim=True):
    """A single branch cell — normal brightness on main session rows, dim on dispatch rows."""
    br = branch or _git_branch(cwd)
    return (_pad((br or "—")[: _BRW - 1], _BRW), "dim" if dim else "branch_s")


def _eff_key(effort, dim):
    """Effort = plain default fg (user 2026-07-02: 기본색으로) — heat ramp retired; only the
    row's brightness axis applies (dim on dispatch/stale rows)."""
    return "dim" if dim else None


def _model_cell(model, effort, width, dim=False):
    """model + effort written TOGETHER as one flowing phrase ('Fable 5 xhigh' — user 2026-07-03:
    항목으로 나누지 말고), padded to `width` as a whole; rides the row's brightness axis."""
    name = _clean_model(dash(model)) or "—"
    sfx = effort or ""
    lkey = _model_key(model, dim=dim)
    if sfx:
        name = name[: max(1, width - len(sfx) - 4)]
        pad = max(0, width - len(name) - len(sfx) - 3)
        return [(name, lkey), (" (" + sfx + ")", _eff_key(sfx, dim)), (" " * pad, None)]
    return [(_pad(name[: width - 1], width), lkey)]


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
    if seq and stage in ("", key, "open", "running"):
        # pre-plan boot (live_stage fell back to the argv key) / registry-only rows: show the
        # WHOLE track unlit — the breadcrumb is visible from the first tick and lights up
        # left→right (plan › exec › test) as plans/ artifacts appear. (user 2026-07-02:
        # "구체적으로 plan → exec → test 순이 떠야하는건데")
        out = []
        for i, st in enumerate(seq):
            if i:
                out.append((" › ", "dim"))
            out.append((st, "stg%d_off" % (i % 5)))
        return out
    if stage:
        return [(stage, _cur_key(0))]
    return [("—", "dim")]


def _session_row(s, narrow, is_parent=False, child_count=0):
    live = s.liveness
    slug = s.slug or (s.cwd.rsplit("/", 1)[-1] if s.cwd else "?")
    dim_tel = live in ("stale", "dead") or s.app_server or s.detached
    name_key = ("name_work" if live == "working"
                else ("name_dim" if dim_tel else "name_idle"))
    gch, gkey = _glyph(live)
    if s.detached and live not in ("stale", "dead"):
        gch, gkey = _DETACHED_GLYPH, "dim"   # detached: 어둡게 (user 2026-07-03)
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

    segs.append(_branch_seg(s.cwd, s.branch, dim=dim_tel))     # main row = bright branch/model
    segs += _model_cell(s.model, s.effort, _MW, dim=dim_tel)

    # STATUS-ZONE — ctx gauge (mid-line ━/─, level color); 4-col gap so it reads separate from effort
    if s.ctx_pct is not None and not dim_tel:
        segs += [("    ", None)] + _gauge_segs(s.ctx_pct, _CTX_W) + [(" %3d%%" % s.ctx_pct, _pct_key(s.ctx_pct))]
    else:
        segs += [("    ", None), ("─" * _CTX_W, "dim"), (" %4s" % dash(s.ctx_pct, lambda v: "%d%%" % v), "dim")]
    if s.app_server:
        segs.append(("  app-server", "dim"))
    if s.orphan:
        segs.append(("  worktree-gone", "g_dead"))

    segs.append((_RFLUSH, None))                                     # ⏱uptime flush right
    # (cost 표시는 제거 — user 2026-07-02: 금액 관련은 안 떠도 됨)
    segs += [(_CLOCK, "dim"), ("%6s" % fmt_min(s.elapsed_min), "dim")]
    return segs


def _mq_tag(mode, qa_text, qa_key, profile=None):
    """The `(mode · qa · profile)` tag shown after a dispatch name (mode dim, qa in its rigor
    color, profile dim, middle dot). Returns (segments, display_width). Empty (mode, qa_text
    and profile all absent) → ([], 0)."""
    if not mode and not qa_text and not profile:
        return [], 0
    out = [(" (", "dim")]
    w = 2
    has_prev = False
    if mode:
        out.append((mode, "dim")); w += len(mode)
        has_prev = True
    if qa_text:
        if has_prev:
            out.append(("·", "dim")); w += 1        # flush middle dot (tighter than ' · ')
        out.append((qa_text, qa_key)); w += len(qa_text)
        has_prev = True
    if profile:
        if has_prev:
            out.append(("·", "dim")); w += 1
        out.append((profile, "dim")); w += len(profile)
    out.append((")", "dim")); w += 1
    return out, w


def _dispatch_row(j, orphan=False, parent_model=None, parent_harness=None, is_last=True,
                  parent_effort=None):
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
    gch, gkey = _glyph(j.liveness)
    hn = _BADGE_TEXT.get(j.harness, "—") if j.harness else "—"
    qa_key = "qa_" + qa_base if qa_base in _QA_INT else "dim"

    # DIFFERENTIAL indent (harness 2 cols deeper than a session) with a ↳ spawn arrow off the
    # parent's dot column (user pick over ├─/└─ tree bars); the harness field is narrowed by 2 so
    # the NAME still lands at the shared _NAME_COL — name onward aligns with sessions. DIM = spawned.
    segs = [("  ", None), ("↳ ", "dim"), (gch, gkey), (" ", None),
            (_pad(hn, _HW - 2), _BADGE_KEY.get(j.harness, "dim"))]
    avail = _NW_S
    tag_segs, tagw = _mq_tag(j.mode, qa_text, qa_key, profile=j.profile)
    otag = "  (orphan)" if orphan else ""
    nm = name[: max(3, avail - tagw - len(otag) - 1)]   # -1 → always ≥1 gap before branch
    used = len(nm)
    segs.append((nm, "name_dim"))
    segs += tag_segs; used += tagw
    if otag and used + len(otag) <= avail:
        segs.append((otag, "gate_u")); used += len(otag)
    if used < avail:
        segs.append((" " * (avail - used), None))

    segs.append(_branch_seg(j.cwd, j.branch))                  # dispatch row = everything dim
    # model slot → the job's OWN main model (dim family color) + effort (headless has no
    # statusline → parent's effort, the shared settings default — user 2026-07-03: 분사도 effort).
    segs += _model_cell(j.model or parent_model, parent_effort, _MW, dim=True)

    # gauge slot → capability-LABELED stage breadcrumb: `code: plan › exec › test` — the process
    # kind rides the track it names, where the eye reads progress (user 2026-07-02: name 앞보다
    # 여기가 autopilot-code 정체를 직관적으로 전달). loops jobs (key == slug) skip the label.
    segs.append(("    ", None))                       # 4-col gap (reads separate from effort/qa)
    if key and key != name:
        segs.append((key + ": ", "name_dim"))
    segs += _stage_segs(key, stage, working=(j.liveness == "working"))

    segs.append((_RFLUSH, None))
    segs += [(_CLOCK, "dim"), ("%6s" % fmt_min(j.elapsed_min), "dim")]
    return segs


# ---------- 2-line cards (round-4 responsive narrow mode) ----------
# L1 = identity (dot · harness · name · ▾N · gate · branch) / L2 = telemetry (model · effort ·
# bracket gauge · cost · ⏱). model keeps its fixed width so gauges align vertically across cards
# (the nvtop column feel). Same segment parts as the 1-line rows — zero new color keys.
def _session_row_2line(s, is_parent=False, child_count=0, _split=False):
    live = s.liveness
    slug = s.slug or (s.cwd.rsplit("/", 1)[-1] if s.cwd else "?")
    dim_tel = live in ("stale", "dead") or s.app_server or s.detached
    name_key = ("name_work" if live == "working"
                else ("name_dim" if dim_tel else "name_idle"))
    gch, gkey = _glyph(live)
    if s.detached and live not in ("stale", "dead"):
        gch, gkey = _DETACHED_GLYPH, "dim"
    hn = _BADGE_TEXT.get(s.harness, "?")
    hkey = (_BADGE_KEY.get(s.harness, "dim") if dim_tel
            else ("hb_" + s.harness if s.harness in _BADGE_TEXT else "hb_other"))
    l1 = [("  ", None), (gch, gkey), (" ", None), (_pad(hn, _HW), hkey), (slug, name_key)]
    if is_parent and child_count:
        l1.append((" ▾%d" % child_count, "dim"))
    gate, pipe = (s.gate, False) if s.gate else _gate_info(s.cwd, s.session_id)
    gtag, gk = _gate_tag(gate, pipe)
    if gtag:
        l1.append((gtag, gk))
    br = s.branch or _git_branch(s.cwd)
    br_seg = ("  " + br, "dim" if dim_tel else "branch_s") if br else None
    if not _split and br_seg:
        l1.append(br_seg)
    if s.app_server:
        l1.append(("  app-server", "dim"))
    if s.orphan:
        l1.append(("  worktree-gone", "g_dead"))

    # L2: elapsed time sits UNDER the harness column (fills the old empty indent — user
    # 2026-07-03: 시간을 harness 아래로), model under the name, gauge right after (no deep
    # indent / no far-right flush).
    l2 = [("    ", None), (_pad(fmt_min(s.elapsed_min), _HW), "dim")]
    l2 += _model_cell(s.model, s.effort, _MW, dim=dim_tel)
    if s.ctx_pct is not None and not dim_tel:
        l2 += [("[", "dim")] + _gauge_segs(s.ctx_pct, 12) + \
              [(" %3d%%" % s.ctx_pct, _pct_key(s.ctx_pct)), ("]", "dim")]
    else:
        l2 += [("[", "dim"), ("·" * 12, "dim"),
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


def _session_row_stack(s, is_parent=False, child_count=0):
    """Ultra-narrow card = the 2-line card with ONLY the context gauge pushed to its own line
    (user 2026-07-03): L1 identity / L2 time+model / L3 gauge (aligned under the model)."""
    l1, l2 = _session_row_2line(s, is_parent, child_count)
    gi = _stack_split(l2)
    return [l1, l2[:gi], [(" " * (4 + _HW), None)] + l2[gi:]]


def _dispatch_row_stack(j, orphan=False, parent_model=None, parent_effort=None):
    l1, l2 = _dispatch_row_2line(j, orphan=orphan, parent_model=parent_model,
                                 parent_effort=parent_effort)
    gi = _stack_split(l2)
    return [l1, l2[:gi], [(" " * (4 + _HW), None)] + l2[gi:]]


def _dispatch_row_2line(j, orphan=False, parent_model=None, parent_effort=None, _split=False):
    key = j.key or "?"
    name = j.slug or key
    gch, gkey = _glyph(j.liveness)
    hn = _BADGE_TEXT.get(j.harness, "—") if j.harness else "—"
    qa_base = j.qa or ""
    qa_text = (("~" + j.qa) if j.qa_source in ("jobslog", "plan", "default") else j.qa) if j.qa else ""
    qa_key = "qa_" + qa_base if qa_base in _QA_INT else "dim"
    tag_segs, _tw = _mq_tag(j.mode, qa_text, qa_key, profile=getattr(j, "profile", None))

    l1 = [("  ", None), ("↳ ", "dim"), (gch, gkey), (" ", None),
          (_pad(hn, _HW - 2), _BADGE_KEY.get(j.harness, "dim")), (name, "name_dim")]
    l1 += tag_segs
    if orphan:
        l1.append(("  (orphan)", "gate_u"))
    br = j.branch or _git_branch(j.cwd)
    br_seg = ("  " + br, "dim") if br else None
    if not _split and br_seg:
        l1.append(br_seg)

    l2 = [("    ", None), (_pad(fmt_min(j.elapsed_min), _HW), "dim")]
    l2 += _model_cell(j.model or parent_model, parent_effort, _MW, dim=True)
    if key and key != name:
        l2.append((key + ": ", "name_dim"))
    l2 += _stage_segs(key, j.stage or "", working=(j.liveness == "working"))
    if _split:
        return l1, l2, br_seg
    return l1, l2


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
    def k(s):
        r = _LIVE_RANK.get(s.liveness, 9)
        if s.detached and r < 3:
            r = 3          # detached sinks below working/idle (user 2026-07-03: 제일 아래로)
        return (r, -(s.elapsed_min or 0))
    return sorted(ss, key=k)


def _sort_group_jobs(js):
    return sorted(js, key=lambda j: (_JOB_LIVE_RANK.get(j.liveness, 9), -(j.elapsed_min or 0)))


_SHOW_ALL = False   # --all: reveal stale/dead/app_server sessions (folded by default per group)


def set_show_all(v):
    global _SHOW_ALL
    _SHOW_ALL = bool(v)


def _build_lines(sessions, jobs, section, narrow, malformed, layout="wide"):
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
    _rl = {}   # harness -> (rl_5h, rl_7d, rl_ms, mtime, rl_rs)
    for s in sessions:
        if s.rl_5h is not None or s.rl_7d is not None or s.rl_ms:
            cur = _rl.get(s.harness)
            if cur is None or (s.mtime or 0) > (cur[3] or 0):
                _rl[s.harness] = (s.rl_5h, s.rl_7d, s.rl_ms, s.mtime, s.rl_rs)
    # harnesses with LIVE sessions but no rate source still get a row with an explicit note —
    # a silently missing row read as a bug (2026-07-02 user: "opencode go 공급자로서 안뜨는거야?").
    # opencode-go has no usage API (gateway 404s; docs: console-only), so say so on the board.
    _live_h = set(s.harness for s in sessions
                  if s.liveness not in ("stale", "dead") and not s.app_server and not s.is_child)
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
            r5, r7, rms, _mt, rrs = _rl[h]
            # 5h/7d + per-model buckets — ALL labels dim (a colored 'fable' read like a harness).
            # htop BRACKET METERS (round-4): `[━━━━──────── 33%]` — the bracket draws the capacity
            # vessel, % sits inside. Session-row ctx gauges stay bare (htop's list bars are bare too).
            # ↻ = time until the window resets (API resets_at — was collected and discarded).
            gw = 8 if layout != "wide" else 12
            rs5, rs7 = (rrs or (None, None))[0], (rrs or (None, None))[1]
            gauges = [("5h ", r5, rs5), ("7d ", r7, rs7)] + \
                     [(lbl + " ", v, None) for lbl, v in (rms or [])]
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
    # (round-4b, user: "일단 띄우고 필요없으면 쳐내지뭐"). Counts skip app-server companions.
    _real = [s for s in sessions if not s.app_server]
    n_wk = sum(1 for s in _real if s.liveness == "working")
    n_id = sum(1 for s in _real if s.liveness == "idle")
    n_dt = sum(1 for s in _real if s.detached and s.liveness not in ("stale", "dead"))
    jw = sum(1 for j in jobs if j.liveness == "working")
    pulse = [("  fleet ", "head"),
             ("● %d" % n_wk, "g_work"), (" working   ", "dim"),
             ("○ %d" % n_id, "g_idle"), (" idle   ", "dim")]
    if n_dt:
        pulse += [(_DETACHED_GLYPH + " %d" % n_dt, "g_idle"), (" detached   ", "dim")]
    if jobs:
        pulse += [("↳ %d" % len(jobs), "dim"),
                  (" job%s (%d working)" % ("s" if len(jobs) != 1 else "", jw), "dim")]
    lines.append(pulse)                 # (Σ cost 롤업 제거 — user: 금액 표시 삭제)

    # alert strip — CONDITIONAL (zero lines when healthy): compaction-imminent contexts and
    # stalled dispatches (the stealth-death guard §5.10, surfaced on the board instead of only
    # in dispatch-liveness.sh runs). dead jobs = red, warnings = yellow.
    alerts = []
    for s in _real:
        if s.ctx_pct is not None and s.ctx_pct >= 80 and s.liveness in ("working", "idle"):
            alerts.append(("ctx %d%% %s" % (s.ctx_pct, s.slug or "?"),
                           "lvl_r" if s.ctx_pct >= 90 else "lvl_y"))
    for j in jobs:
        if j.liveness == "stale":
            alerts.append(("job stale %s" % (j.slug or j.key), "lvl_y"))
        elif j.liveness == "dead":
            alerts.append(("job dead %s" % (j.slug or j.key), "lvl_r"))
    if alerts:
        arow = [("  alert ", "head")]
        for ai, (txt, akey) in enumerate(alerts[:6]):
            if ai:
                arow.append(("   ", None))
            arow.append(("⚠ " + txt, akey))
        lines.append(arow)
    # usage/intel zone = PLAIN bg + a full-width dim rule below it (user 2026-07-03: intel
    # 틴트는 활성 카드와 헷갈림 → 틴트 제거, 구분선으로 존 경계) — tint stays directory-only.
    lines.append([(_HFILL, None)])

    # header bar REPLACES the `──` zone divider — htop separates meters from the process list
    # with its bar, not a rule. One blank line above it (user 2026-07-02: header 위에 한칸) so
    # the top intel zone and the bar don't touch. Narrow mode's 2-line cards have no single
    # column mapping → the bar degrades to a zone label + current-mode hint.
    # column header = PLAIN dim labels, no bar/tint at all (user 2026-07-02: 전체 헤더는 컬러
    # 빼자) — the tinted panels below carry the block language; the header just names columns.
    lines.append(None)
    _sh = " " * (_INSET + _PAD_IN) if _TINT_OK else ""   # shift matches panel content columns
    if layout != "wide":
        lines.append([(_sh + "  SESSIONS", "head"), (_RFLUSH, None),
                      ("%s · press w to cycle  " % layout, "head")])
    else:
        # right-flushed 'time' label sits over the (inset) elapsed-time column — trailing
        # spaces mirror the tint rows' right inset so the label right-aligns with the values.
        lines.append([(_sh + _COL_HEAD, "head"), (_RFLUSH, None),
                      ("time" + " " * (_INSET + _PAD_IN + 1), "head")])
    lines.append(None)                  # gap below the column header (user: 헤더 한칸 아래 띄우기)

    first = True
    folded_groups = []       # dormant dirs — aggregated into ONE line at the bottom (user: the
                             # stack of per-dir folded rules at the bottom was visual noise)
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
        ggate, gpipe = _gate_info(gcwd)                # project spec-gate (word after the name)
        gword, gwkey = _gate_word(ggate, gpipe)
        if not gword:
            # no artifact root at all = outside the pipeline → same word as the exempt state
            # (user 2026-07-03: untracked 일 때도 라벨을 띄우자 — no more blank gate slots)
            gword, gwkey = "untracked", "gate_u"
        # section title — NO indicator glyph at all (2026-07-03 user 이력: ▍ 어색 → dot 은 세션과
        # 혼동 → "다른 활성 방식"): the TITLE ITSELF carries the active state — green bold name
        # while the group works, plain bold otherwise. Doubles with the active card tint.
        n_work = sum(1 for s in live_sessions if s.liveness == "working") + \
                 sum(1 for j in group_jobs if j.liveness == "working")
        # trailing slash = the universal "this is a directory" marker (ls convention — user
        # 2026-07-03: 폴더(repo)임을 간단하게), dim so the name stays the focal word.
        # The blinking green ● now lives HERE (directory level = "work happening inside") —
        # sessions animate a spinner instead, so the dot no longer collides with row vocabulary.
        head_segs = []
        if n_work:
            head_segs += [("●", "g_work" if _BLINK_ON else "g_work_off"), (" ", None)]
        head_segs += [(name, "grp_hot" if n_work else "grp"), ("/", "dim")]
        _nwt = _wt_count(gcwd)
        if _nwt:
            # statusline 과 같은 표기 (🚧 N = 병렬 작업장·잔존 worktree, §5.10) — 이름 바로 옆
            head_segs += [(" 🚧 %d" % _nwt, "g_idle")]
        if gword:
            head_segs += [("  ", None), (gword, gwkey)]
        # group header = the card's TITLE row (user 2026-07-03 pick: 카드 안 타이틀) — first
        # tinted row of the panel, ▍ anchor on the card's padding edge; no floating label.
        _g0 = len(lines)                # panel start (title INCLUDED in the tint range)
        lines.append(head_segs)
        _rail_key = "grp_live" if n_work else "dim"
        _body_tint = _TINT_BODY_HOT if n_work else _TINT_BODY

        # rows stay tight (no blank line — that spread them too far apart); the mid-line gauge
        # glyph (━/─) is what keeps the stacked context bars from merging into a solid wall.
        _srow = {"wide": None, "narrow": _session_row_2line, "stack": _session_row_stack}[layout]
        _jrow = {"wide": None, "narrow": _dispatch_row_2line, "stack": _dispatch_row_stack}[layout]
        _sess_ids = set()               # line indices of MAIN-session rows (whisper-brighter tint)
        for s in _sort_group_sessions(shown):
            kids = _sort_group_jobs(children.get(s.session_id, []))
            _n0 = len(lines)
            if _srow:
                lines.extend(_srow(s, is_parent=bool(kids), child_count=len(kids)))
            else:
                lines.append(_session_row(s, narrow, is_parent=bool(kids), child_count=len(kids)))
            _sess_ids.update(range(_n0, len(lines)))
            for i, cj in enumerate(kids):
                if _jrow:
                    lines.extend(_jrow(cj, orphan=False, parent_model=s.model,
                                       parent_effort=s.effort))
                else:
                    lines.append(_dispatch_row(cj, orphan=False, parent_model=s.model,
                                               parent_harness=s.harness, parent_effort=s.effort,
                                               is_last=(i == len(kids) - 1)))
        if group_sessions and hidden:
            lines.append([("     +%d stale/companion hidden" % hidden, "dim")])

        # orphans / loops: project-level fallback (standalone tree rows)
        for oj in _sort_group_jobs(orphans):
            if _jrow:
                lines.extend(_jrow(oj, orphan=show_sessions))
            else:
                lines.append(_dispatch_row(oj, orphan=show_sessions))
        for lj in _sort_group_jobs(loops_jobs):
            if _jrow:
                lines.extend(_jrow(lj, orphan=False))
            else:
                lines.append(_dispatch_row(lj, orphan=False))

        # group BODY (round-5): every row of the group rides the body tint — the whole directory
        # is one solid panel, brighter when active (user: 디렉토리 블록 전체에 틴트, 헤더만 X).
        # Fallback (_TINT_OK False → 8-color): the previous ▍ rail marks the block instead.
        for _i in range(_g0, len(lines)):
            ln = lines[_i]
            if not ln or _is_fill(ln[0][0]):
                continue
            if _TINT_OK:
                _tch2 = (_TINT_BODY_HOT.replace("B", "S") if _i in _sess_ids else _TINT_BODY_HOT) \
                        if n_work else \
                        (_TINT_BODY.replace("b", "s") if _i in _sess_ids else _TINT_BODY)
                lines[_i] = [(_tch2, None)] + ln
            elif ln[0][1] in (None, "dim") and ln[0][0].startswith(" "):
                lines[_i] = [("▍", _rail_key), (ln[0][0][1:], ln[0][1])] + ln[1:]
        if _TINT_OK:
            # breathing row below the title + bottom padding (title-top padding tried and
            # removed — user 2026-07-03: 별로) — inserted AFTER the tint loop (one sentinel each).
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

    # legend — status dots (columns are labelled by the header row)
    lines.append(None)
    lines.append([
        ("  ", None), ("⠹", "g_work"), (" working   ", "dim"),
        ("●", "dim"), (" idle   ", "dim"),
        (_DETACHED_GLYPH, "dim"), (" detached   ", "dim"),
        ("·", "g_stale"), (" stale   ", "dim"),
        ("✕", "g_dead"), (" dead     ", "dim"),
        ("▾N", "dim"), (" child jobs   ", "dim"),
        ("↳", "dim"), (" dispatch   ", "dim"),
        ("🚧 N", "dim"), (" worktrees", "dim"),
    ])

    return lines


# ---------- plain (--once) ----------
def _plain(segs):
    if segs is None:
        return ""
    out = []
    for t, _ in segs:
        if _is_fill(t):
            if t[1] in _TINT_CHARS:
                continue                       # tint sentinel — background only, no text
            out.append("─────" if t == _HFILL else "   ")
        else:
            out.append(t)
    return "".join(out)


def render_once(collect_all, hfilter, section):
    sessions, jobs = collect_all(harness_filter=hfilter)
    malformed = _malformed()
    try:
        import shutil
        tw = shutil.get_terminal_size().columns
    except Exception:
        tw = 200
    lines = _build_lines(sessions, jobs, section, narrow=False, malformed=malformed,
                         layout=_layout_mode(tw))
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
_WIDE = set("🧠✨⏳📁🚀🛰📌⚡📋⚙📊🐛📈🔬💻⏱↻")


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
_INSET = 2                  # panel outer margin (cols) — 바깥 여백은 이대로 (user)
_PAD_IN = 2                 # EXTRA inner padding: tint edge ↔ content (user: 여백을 늘리자)
_RFLUSH = "\x00 \x00"
_HFILL = "\x00─\x00"

# row-tint sentinels (round-5 — herdr-style panel tints): a LEADING sentinel marks the whole
# row's background level. b/c = group body/cap · B/C = the ACTIVE-group variants (brighter,
# user 2026-07-02: 활성 디렉토리 틴트를 더 눈에 띄게) · i = intel zone (usage/pulse/alert).
_TINT_BODY, _TINT_CAP = "\x00b\x00", "\x00c\x00"
_TINT_BODY_HOT, _TINT_CAP_HOT = "\x00B\x00", "\x00C\x00"
_TINT_INTEL = "\x00i\x00"
_TINT_CHARS = {"b", "c", "B", "C", "i", "s", "S"}
# 256-color background levels per sentinel char. Base panels = dark GREY (235/238); the
# ACTIVE-group variants are a dark COLORED tint (user 2026-07-02 최종: 기본은 어둡게, 활성
# 디렉토리만 컬러 — 미드나잇 블루). 17 = #00005f, the cube's darkest blue: natively subtle
# even where init_color is ignored (green 22 #005f00 read too bright — user ×2).
_TINT_LVL = {"b": 235, "c": 238, "B": 17, "C": 17, "i": 235,
             "s": 236, "S": 18}   # s/S = MAIN-session rows, one whisper brighter (user 2026-07-03)


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
    # tinted panels are INSET two columns on both sides AND their content shifts inward with
    # them (user 2026-07-02: 좌우여백이 안 보임 — near-black tint vs default bg alone is
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
                try:
                    stdscr.addstr(row, col, piece, _key_attr(color, tint))
                except curses.error:
                    pass
            col += pw
        return col

    endcol = _draw(left, start_col)
    # band lines (htop WHITE bars = full width · round-5 tint panels = inset cards) paint their
    # background across; tint rows stop at w-1 so the right margin stays on the default bg.
    bar = bool(segs) and segs[0][1] == "hdr_bar"
    band = bar or tint is not None
    band_lim = w if bar else (w - _INSET)
    fill_key = "hdr_bar" if bar else None      # tint rows fill with the default-hue tint pair
    if fillch is not None:              # right may be EMPTY (a bare full-width rule line) — the
        rw = sum(_dw(t) for t, _ in right)   # fill itself must still draw (bug: divider invisible)
        rpad = (2 + _PAD_IN) if tint is not None else 0   # right-flushed text sits in from the band edge
        rcol = max(endcol + (0 if fillch == "─" else 2), (band_lim if band else w - 1) - rw - rpad)
        if fillch == "─" and rcol > endcol:
            _draw([("─" * (rcol - endcol), "head")], endcol)  # fill the gap to make a full-width rule
        elif band and band_lim > endcol:
            # paint the ENTIRE gap to the band edge first, then draw `right` over it — glyph
            # width disagreements (⏱ = 2 cells in our table, 1 by wcwidth/tmux) otherwise leave
            # an unpainted hole right before the time (user 2026-07-02: 시간 앞 블록 컬러 잘림).
            _draw([(" " * (band_lim - endcol), fill_key)], endcol, lim=band_lim)
        if right:
            _draw(right, rcol, lim=band_lim if band else None)
    elif band and endcol < band_lim:
        _draw([(" " * (band_lim - endcol), fill_key)], endcol, lim=band_lim)


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
    lines = _build_lines(sessions, jobs, section, narrow, malformed, layout=_layout_mode(w))
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
    # htop F-key bar (round-4): CYAN full-width, keycaps BOLD (dim is invisible on CYAN), the
    # scroll indicator rides the right edge. `w` cycles layout auto → narrow → wide.
    wlbl = "wide/narrow" if _LAYOUT == "auto" else ("%s!" % _LAYOUT)
    fsegs = [(" ", "hdr_bar"),
             ("q", "hdr_key"), (" quit · ", "hdr_bar"),
             ("r", "hdr_key"), (" refresh · ", "hdr_bar"),
             ("a", "hdr_key"), (" all · ", "hdr_bar"),
             ("w", "hdr_key"), (" " + wlbl + " · ", "hdr_bar"),
             ("jk", "hdr_key"), (" scroll · ", "hdr_bar"),
             ("g/G", "hdr_key"), (" top/end", "hdr_bar"),
             (_RFLUSH, None), (" ".join(parts) + " " if parts else "", "hdr_bar")]
    _addline(stdscr, h - 1, fsegs, w)
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
        _nb = (int(time.time() * 10) + 1) / 10.0   # 10fps wake — the spinner cadence
        stdscr.timeout(max(20, min(100, int((_nb - time.time()) * 1000) + 1)))
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
        elif ch in (ord("w"), ord("W")):
            _cycle_layout()
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
