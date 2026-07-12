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
    vertically — user 2026-07-02: '세로로 나열하는 느낌'). auto: width decides.
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
    "g_stale": ("d", _A_D), "g_dead": ("r", _A_B),
    "lvl_g": ("g", 0), "lvl_y": ("y", 0), "lvl_r": ("r", _A_B),
    "grp_live": ("g", 0), "grp_hot": ("g", _A_B), "gate_t": ("g", _A_D), "gate_u": ("y", _A_D),
    "grp_cool": ("y", _A_D), "grp_cold": ("d", _A_D),   # cooling=dim yellow / cold=dim grey (tint 행 색)
    "eff_low": ("d", _A_D), "eff_medium": ("d", 0), "eff_high": ("l", 0),
    "eff_xhigh": ("m", _A_B), "eff_max": ("r", _A_B),
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
    _COLOR["grp_cool"] = _COLOR.get("yellow", 0) | curses.A_DIM  # cooling: 어두운 노랑(●·이름·✓경과시간)
    _COLOR["grp_cold"] = curses.A_DIM                            # cold(오래된 비활성): 회색 고리 ○
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
    # effort ramp v3 (2026-07-03 — user: 노란색 거슬림 + high/xhigh 는 색으로 달라야):
    # low/medium = no hue (weight only) < high = BLUE < xhigh = MAGENTA (bold) < max = RED
    # (bold, the one true alarm — unchanged). No yellow anywhere in the ramp.
    _COLOR["eff_low"] = curses.A_DIM
    _COLOR["eff_medium"] = 0
    _COLOR["eff_high"] = _COLOR.get("h_opencode", 0) & ~curses.A_DIM   # plain blue
    _COLOR["eff_xhigh"] = (_COLOR.get("h_codex", 0) & ~curses.A_DIM) | curses.A_BOLD  # bold magenta
    _COLOR["eff_max"] = _COLOR.get("red", 0) | curses.A_BOLD
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
                    # cooling 배경 = 어두운 갈색 (≈#1e130a) — 무시되면 stock 94(#875f00 brown)
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
    return {"working": "g_work", "idle": "g_work_off", "stale": "g_stale",
            "dead": "g_dead"}.get(state, "dim")


# status dot — SHAPE+SIZE gradient (design r2, a11y): the less active the state, the smaller
# the glyph. Working uses a bright green spinner; live idle/detached use the same dim-green
# loading axis; stale/dead recede to grey/red. Readable without color.
_LIVE_GLYPH = {"working": "●", "idle": "●", "blocked": "◑", "done": "✓",
               "stale": "·", "dead": "✕", "queued": "◦", "unknown": "·"}
_DETACHED_GLYPH = "○"   # ring = 빈 자리(클라이언트 없음); idle 은 꽉 찬 dim-green ●
_GLYPH_KEY = {"working": "g_work", "idle": "g_work_off", "blocked": "g_idle", "done": "green",
              "stale": "g_stale", "dead": "g_dead", "queued": "dim", "unknown": "dim"}

# group "cooling" state (user 2026-07-03): a directory with NO active work whose newest session
# transcript write is within this window reads as "완료 직후 식는 중" — a middle state between hot
# (green ● + green-bold title) and cold (no glyph). It gets a grey ring + time-since-last-activity
# in the header, so a just-finished repo says "done & waiting", not fully dormant. Tune freely.
_COOL_WINDOW_MIN = 180
# shape-size gradient (design r2): 더 최근·활동적일수록 채워진 큰 글리프. 방금 끝난 디렉토리(cooling)
# = 채운 ● (아직 온기), 오래돼 잠든 디렉토리(cold) = 빈 고리 ○. 활성 working ● 은 녹색이라 회색과 구분.
_COOL_FILLED = "●"      # cooling(방금 끝남, ≤_COOL_WINDOW_MIN) directory — 채운 원형(회색)
_COOL_RING = "○"        # cold(오래된 비활성) directory — 고리 원형(회색)
_COOL_TIME_ICON = "✓"   # 경과시간 프리픽스 — 이 값이 "완료 후 경과시간"임을 표시(done-then-elapsed)


_BLINK_ON = True     # manual blink phase (toggled ~2 Hz in the live loop) — drives the spinner too
_SPIN = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"   # braille loading spinner — working SESSIONS animate (user 2026-07-03);
                     # the blinking green ● moved up to the directory title


def _glyph(state, dim=False):
    """Session/job status glyph. working = braille spinner frame — BRIGHT green for a main
    session, DIM green for a dispatch job (user 2026-07-03: 스피너 컬러도 메인·분사 구분).
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
_NAME2_MAX = 40               # 2-line name zone tail-cut cap (display cells) — no fixed branch
                              # column there, so an unbounded title could push branch off-draw (F-14)
_TITLE_MAX = 24               # F-16: display-name budget (session title AND dispatch composed
                              # label+slug) — tighter than the raw name-zone width so a long
                              # harness ai-title/plan slug doesn't dominate the row
_OPTW = 18                    # F-15a options column width (dim mode·qa·profile token, sits
                              # between the model cell and the stage breadcrumb — declutters
                              # the name zone, which used to carry this as a parenthetical tag)
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

# depth-2 stage worker role → human stage label (SD-F1). Code workers use their sub-skill
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
    """(base_label, suffix) for a depth-2 stage worker_role, e.g. 'stage-search:phase-A' ->
    ('search', ':phase-A'). base_label is None when worker_role isn't a known stage sub-skill —
    callers fall back to the existing _ROLE_SHORT/_compact_dispatch_name path."""
    if not worker_role:
        return None, ""
    base, _sep, suffix = worker_role.partition(":")
    label = _STAGE_ROLE.get(base)
    if label is None:
        return None, ""
    return label, (":" + suffix if suffix else "")

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
    """Effort heat ramp (restored 2026-07-03 — user: effort 컬러 다시): low/medium recede,
    high = yellow, xhigh = bold yellow, max = bold red. Dispatch/stale rows stay flat dim."""
    if dim:
        return "dim"
    return ("eff_" + effort) if effort in ("low", "medium", "high", "xhigh", "max") else None


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
        cur_i = seq.index(stage)
        out = []
        for i, st in enumerate(seq):
            if i:
                out.append((" › ", "dim"))
            # P1-5: a stage BEFORE the current one is done — a bright ✓ marker makes the
            # "past stages are folded into this breadcrumb" contract visible (F-15b).
            label = st + ("✓" if i < cur_i else "")
            out.append((label, _cur_key(i) if st == stage else "stg%d_off" % (i % 5)))
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


def _session_row(s, narrow, is_parent=False, child_count=0):
    live = s.liveness
    slug = s.slug or (s.cwd.rsplit("/", 1)[-1] if s.cwd else "?")
    dim_tel = live in ("stale", "dead") or s.app_server or s.detached
    dead_stale = live in ("stale", "dead")   # F-13: telemetry gone, replaced with a single age cell
    name_key = ("name_work" if live == "working"
                else ("name_dim" if dim_tel else "name_idle"))
    gch, gkey = _glyph(live)
    if s.detached and live not in ("stale", "dead"):
        gch, gkey = _DETACHED_GLYPH, "g_work_off"   # detached: loading axis, dim-green
    hn = _BADGE_TEXT.get(s.harness, "?")

    # main↔spawned weight = font-color intensity (no bg fill — the reverse badge read as weird):
    # a live top-level session gets the BRIGHT harness color; muted (stale/dead/app-server) drops
    # to dim. Dispatch rows use the DIM harness color (see _dispatch_row).
    hkey = (_BADGE_KEY.get(s.harness, "dim") if dim_tel
            else ("hb_" + s.harness if s.harness in _BADGE_TEXT else "hb_other"))
    segs = [("  ", None), (gch, gkey), (" ", None), (_pad(hn, _HW), hkey)]

    # name zone: title-or-slug(focus) + ▾N(dim) + gate tag(dim), padded to the shared branch column.
    used = 0
    name_txt = s.title or slug
    shown = _clip_w(name_txt, min(_NW_S - 1, _TITLE_MAX))   # F-16: tighter display-name budget
    segs.append((shown, name_key)); used += _dw(shown)   # display width, not char count (F-14 #4)
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
    if dead_stale:
        # F-13: a stale/dead row has no live model/effort/ctx to show — a wall of "—" placeholders
        # read as broken telemetry rather than "this session stopped". One `last seen <age>` cell
        # replaces the whole model+gauge zone (LIVE rows keep the explicit "—" convention, F-3).
        age_min = int((time.time() - s.mtime) / 60) if s.mtime else (s.elapsed_min or 0)
        segs += [(" " * _MW, None), ("    ", None), ("last seen %s" % fmt_min(age_min), "dim")]
    else:
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
    """The `(mode · qa:<level> · profile)` tag shown after a dispatch name (mode dim, qa in its rigor
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
        qa_label = "qa:" + qa_text
        out.append((qa_label, qa_key)); w += len(qa_label)
        has_prev = True
    if profile:
        if has_prev:
            out.append(("·", "dim")); w += 1
        out.append((profile, "dim")); w += len(profile)
    out.append((")", "dim")); w += 1
    return out, w


_DISPATCH_NAME_MAX = 18


def _compact_dispatch_name(name, max_width=_DISPATCH_NAME_MAX):
    if not name or len(name) <= max_width:
        return name or ""
    if max_width <= 1:
        return name[:max_width]
    return name[: max_width - 1] + "…"


def _dispatch_prefix(j):
    depth = max(1, min(3, int(getattr(j, "depth", 1) or 1)))
    return "↳ " if depth == 1 else "  " * depth


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
        # whole tag already renders "dim" (see _mq_tag), so no separate color key is needed.
        return _compact_dispatch_name(label + suffix, 14)
    m = _G_CASE_PREFIX.match(value)
    role = _ROLE_SHORT.get(value) or (m.group(1) if m else value.replace("-", "_"))
    return _compact_dispatch_name(role, 14)


_PROFILE_MAX = 28


def _dispatch_role_suffix(j, check_text=None, max_width=None):
    raw_role = getattr(j, "worker_role", None)
    if getattr(j, "key", None) in _LOOPS_KEYS and raw_role == getattr(j, "slug", None):
        raw_role = None
    role = _short_role(raw_role)
    intensity = _short_level(getattr(j, "intensity", None))
    check = _short_level(check_text)
    parts = []
    if intensity:
        parts.append(("intensity", intensity))
    if role:
        parts.append(("role", role))
    if check:
        parts.append(("qa", "qa:" + check))
    if max_width is not None:
        # F-9(c) width-drop priority: qa first, then intensity, then role — mode isn't part of
        # this suffix (owned by _mq_tag's own mode segment). Drops whole components instead of
        # silently tail-cutting the joined string (which used to chop qa:thorough mid-word).
        for kind in ("qa", "intensity", "role"):
            joined = "/".join(t for _k, t in parts)
            if len(joined) <= max_width:
                break
            parts = [(k, t) for k, t in parts if k != kind]
    return "/".join(t for _k, t in parts)


def _dispatch_profile(j, check_text=None):
    profile = getattr(j, "profile", None)
    budget = _PROFILE_MAX - (len(profile) + 1 if profile else 0)
    role_suffix = _dispatch_role_suffix(j, check_text, max_width=max(0, budget))
    if role_suffix:
        profile = (profile + "/" + role_suffix) if profile else role_suffix
    return _compact_dispatch_name(profile, _PROFILE_MAX) if profile else None

def _dispatch_stage_label(j):
    """(label_prefix, is_stage_worker) — the depth-2 stage-role label ('exec', 'plan'...) that
    now identifies a depth-2 child in the NAME zone (F-15a P0-1: identity lives here, not in a
    duplicated breadcrumb). depth-1 conductors/orphans have no such label — their identity is
    just their own slug."""
    if max(1, int(getattr(j, "depth", 1) or 1)) < 2:
        return None
    label, suffix = _stage_role_label(getattr(j, "worker_role", None))
    if label is None:
        return None
    return label + suffix


def _opts_segs(j, qa_text, qa_key):
    """F-15a options column — the job's (mode · qa · profile) dial, relocated OUT of the name
    zone into its own dim slot between the model cell and the stage breadcrumb (P0-1/R2: the
    name zone is identity-only now). Reuses `_mq_tag`'s content, just without the enclosing
    parens (this is a column, not an inline tag) and without a leading name to hang off of."""
    profile = _dispatch_profile(j, qa_text)
    parts = []
    w = 0
    if j.mode:
        parts.append((j.mode, "dim")); w += len(j.mode)
    if profile:
        if parts:
            parts.append(("·", "dim")); w += 1
        parts.append((profile, "dim")); w += len(profile)
    return parts, w


def _dispatch_row(j, orphan=False, parent_model=None, parent_harness=None, is_last=True,
                  parent_effort=None, stage_override=None):
    """A dispatch job rendered as a session-ANALOGUE, mirroring the session columns 1:1:
      harness  |  [stage label] name  |  branch  |  MODEL  |  options  |  stage breadcrumb
    F-15a: the name zone is identity-only (no more parenthetical mode/qa tag — that moved to
    its own options column after the model cell). A depth-2 stage worker's identity is its
    stage label + slug (P0-1); its breadcrumb slot shows its own micro-status instead of
    repeating the parent conductor's full breadcrumb.
    """
    key = j.key or "?"
    depth = max(1, int(getattr(j, "depth", 1) or 1))
    stage = stage_override if stage_override is not None else (j.stage or "")
    qa_base = j.qa or ""
    qa_text = ""
    if j.qa:
        qa_text = ("~" + j.qa) if j.qa_source in ("jobslog", "plan", "default") else j.qa
    slug_name = j.slug or key
    gch, gkey = _glyph(j.liveness, dim=True)
    hn = _BADGE_TEXT.get(j.harness, "—") if j.harness else "—"
    qa_key = "qa_" + qa_base if qa_base in _QA_INT else "dim"

    # DIFFERENTIAL indent (harness 2 cols deeper than a session) with a ↳ spawn arrow off the
    # parent's dot column (user pick over ├─/└─ tree bars); the harness field is narrowed by 2 so
    # the NAME still lands at the shared _NAME_COL — name onward aligns with sessions. DIM = spawned.
    prefix = _dispatch_prefix(j)
    segs = [("  ", None), (prefix, "dim"), (gch, gkey), (" ", None),
            (_pad(hn, max(1, _HW - len(prefix))), _BADGE_KEY.get(j.harness, "dim"))]
    avail = _NW_S
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
    segs.append((nm, "name_dim"))
    if otag and used + len(otag) <= avail:
        segs.append((otag, "gate_u")); used += len(otag)
    if used < avail:
        segs.append((" " * (avail - used), None))

    segs.append(_branch_seg("" if key in _LOOPS_KEYS else j.cwd, j.branch))  # loop temp repos hide throwaway branches
    if j.liveness == "dead":
        # P2-11: a dead job's last-known stage replaces the redundant "last seen <age>" (the
        # time column already shows elapsed) — "dead @exec" tells you WHERE it died.
        last_stage = stage if stage not in (None, "", "open", "running") else key
        segs.append(("    ", None))
        segs.append(("dead @%s" % last_stage, "g_dead"))
    elif j.liveness == "stale":
        # F-13: a stale job has no live model/effort/stage worth showing — collapse the whole
        # telemetry zone (model cell + stage breadcrumb) into one `last seen <age>` cell.
        segs.append(("    ", None))
        segs.append(("last seen %s" % fmt_min(j.elapsed_min), "dim"))
    else:
        # model slot → the job's OWN main model (dim family color) + effort. SD-F3: the job's own
        # effort is first-class; when it's absent (proc-scan rows — env doesn't export it yet),
        # fall back to the parent's effort marked with the derived-value `~` prefix (legend F-9d).
        eff = j.effort or (("~" + parent_effort) if parent_effort else None)
        segs += _model_cell(j.model or parent_model, eff, _MW, dim=True)

        # F-15a options column (fixed-ish gap, dim mode/qa/profile) — a declutter move OUT of
        # the name zone, not a new axis.
        segs.append(("    ", None))
        opt_segs, optw = _opts_segs(j, qa_text, qa_key)
        segs += opt_segs
        if optw < _OPTW:
            segs.append((" " * (_OPTW - optw), None))

        segs.append(("  ", None))
        if depth >= 2:
            # P0-1: a depth-2 stage worker never repeats its parent conductor's full
            # breadcrumb — its identity already rode the name zone (label above); this slot
            # is its own micro-status only.
            if j.liveness == "working":
                segs.append(("running", "stg0_on" if _BLINK_ON else "stg0_off"))
            elif stage and stage not in ("open", "running"):
                segs.append((stage, "stg0_off"))
        else:
            if key and key != slug_name:
                # SD-F1: a depth-2 stage worker's `key` IS its capability (code-plan/code-execute/
                # code-test/code-report) — reuse _stage_role_label (same helper the F-13 legend
                # uses) to humanize it instead of leaking the raw capability token onto the board.
                role_label, role_suffix = _stage_role_label(key)
                prefix_text = (role_label + role_suffix) if role_label else key
                segs.append((prefix_text + ": ", "name_dim"))
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
        gch, gkey = _DETACHED_GLYPH, "g_work_off"
    hn = _BADGE_TEXT.get(s.harness, "?")
    hkey = (_BADGE_KEY.get(s.harness, "dim") if dim_tel
            else ("hb_" + s.harness if s.harness in _BADGE_TEXT else "hb_other"))
    l1 = [("  ", None), (gch, gkey), (" ", None), (_pad(hn, _HW), hkey),
          (_clip_w(s.title or slug, min(_NAME2_MAX, _TITLE_MAX)), name_key)]   # F-16
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


def _dispatch_row_stack(j, orphan=False, parent_model=None, parent_effort=None, stage_override=None):
    l1, l2 = _dispatch_row_2line(j, orphan=orphan, parent_model=parent_model,
                                 parent_effort=parent_effort, stage_override=stage_override)
    gi = _stack_split(l2)
    return [l1, l2[:gi], [(" " * (4 + _HW), None)] + l2[gi:]]


def _dispatch_row_2line(j, orphan=False, parent_model=None, parent_effort=None, _split=False,
                        stage_override=None):
    """F-15a narrow card — L1 = identity ONLY (stage label + slug, no mode/qa tag); L2 =
    elapsed · model · options (relocated from L1) · breadcrumb/micro-status."""
    key = j.key or "?"
    depth = max(1, int(getattr(j, "depth", 1) or 1))
    slug_name = j.slug or key
    gch, gkey = _glyph(j.liveness, dim=True)
    hn = _BADGE_TEXT.get(j.harness, "—") if j.harness else "—"
    qa_base = j.qa or ""
    qa_text = (("~" + j.qa) if j.qa_source in ("jobslog", "plan", "default") else j.qa) if j.qa else ""
    qa_key = "qa_" + qa_base if qa_base in _QA_INT else "dim"

    prefix = _dispatch_prefix(j)
    label = _dispatch_stage_label(j)
    if label:
        slug_room = max(1, _DISPATCH_NAME_MAX - len(label) - 1)
        shown_name = label + " " + _compact_dispatch_name(slug_name, slug_room)
    else:
        shown_name = _compact_dispatch_name(slug_name)
    l1 = [("  ", None), (prefix, "dim"), (gch, gkey), (" ", None),
          (_pad(hn, max(1, _HW - len(prefix))), _BADGE_KEY.get(j.harness, "dim")), (shown_name, "name_dim")]
    if orphan:
        l1.append(("  (orphan)", "gate_u"))
    br = None if key in _LOOPS_KEYS else (j.branch or _git_branch(j.cwd))
    br_seg = ("  " + br, "dim") if br else None
    if not _split and br_seg:
        l1.append(br_seg)

    stage = stage_override if stage_override is not None else (j.stage or "")
    eff = j.effort or (("~" + parent_effort) if parent_effort else None)
    l2 = [("    ", None), (_pad(fmt_min(j.elapsed_min), _HW), "dim")]
    l2 += _model_cell(j.model or parent_model, eff, _MW, dim=True)
    l2.append(("    ", None))
    opt_segs, optw = _opts_segs(j, qa_text, qa_key)
    l2 += opt_segs
    if optw < _OPTW:
        l2.append((" " * (_OPTW - optw), None))
    l2.append(("  ", None))
    if depth >= 2:
        # P0-1: no repeated parent breadcrumb — own micro-status only.
        if j.liveness == "working":
            l2.append(("running", "stg0_on" if _BLINK_ON else "stg0_off"))
        elif stage and stage not in ("open", "running"):
            l2.append((stage, "stg0_off"))
    else:
        if key and key != slug_name:
            # SD-F1/D1: same capability→label humanization as the wide-layout _dispatch_row —
            # the narrow 2-line card must not leak the raw code-* capability key either.
            role_label, role_suffix = _stage_role_label(key)
            prefix_text = (role_label + role_suffix) if role_label else key
            l2.append((prefix_text + ": ", "name_dim"))
        l2 += _stage_segs(key, stage, working=(j.liveness == "working"))
    if _split:
        return l1, l2, br_seg
    return l1, l2


# ---------- grouping assembler ----------
def _group_key_session(s):
    return project_of(s.cwd)


def _mem_row(s, layout="wide"):
    """F-18b: mem-worker 세션의 dim 1-line — 기본 숨김, `a` 토글 시만. 라벨 'mem'."""
    name = _clip_w(s.title or s.slug or (s.harness or "?"), 40)
    seg = [("  🧠 ", "dim"), ("mem ", "dim"),
           (name, "dim"), ("  ", None),
           ((s.harness or "—"), "dim"), ("  ", None),
           (fmt_min(s.elapsed_min), "dim")]
    return [seg]


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
    # Loop/drill temp repos are throwaway execution roots. Without a visible parent, keep
    # them under the loop control plane instead of presenting /tmp/drill-* as a project.
    if j.key in _LOOPS_KEYS:
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
_FOLD_CHILD_LIVENESS = {"done", "queued", "idle", "unknown"}   # F-15b P0-2: depth-2 stage-worker
                                                                # rows folded into the conductor
                                                                # breadcrumb unless working/stale/dead


def set_show_all(v):
    global _SHOW_ALL
    _SHOW_ALL = bool(v)


def _build_lines(sessions, jobs, section, narrow, malformed, layout="wide", memory=None):
    """Return a flat list of segment-lines for the whole screen (None = blank line).

    Same contract consumed by BOTH `render_once` (plain, full output) and `_draw` (viewport
    slices this same list) — `_OFFSET` must never be read here (see module docstring).

    `memory` = F-19 collectors.memory.collect() result (or None — panel/alerts simply omitted;
    tests default to None so every pre-F-19 call site keeps working unchanged).
    """
    # F-18b: mem-worker (distiller/curator/F-17 refresher) census — computed on the ORIGINAL
    # session list, before is_child/mem filtering, so folded/mem-only groups still surface a
    # total in the legend even when no group header badge fires.
    n_mem_total = sum(1 for s in sessions if getattr(s, "mem_worker", False))
    mem_by_group = {}
    for s in sessions:
        if getattr(s, "mem_worker", False):
            gk_mem = _group_key_session(s)
            mem_by_group[gk_mem] = mem_by_group.get(gk_mem, 0) + 1
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
    top_jobs = [j for j in jobs if not (getattr(j, "parent_slug", None) and getattr(j, "depth", 1) >= 2)]
    depth_jobs = [j for j in jobs if getattr(j, "parent_slug", None) and getattr(j, "depth", 1) >= 2]
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
    _real = [s for s in sessions if not s.app_server and not getattr(s, "mem_worker", False)]
    n_wk = sum(1 for s in _real if s.liveness == "working")
    n_id = sum(1 for s in _real if s.liveness == "idle")
    n_dt = sum(1 for s in _real if s.detached and s.liveness not in ("stale", "dead"))
    jw = sum(1 for j in jobs if j.liveness == "working")
    spin = _SPIN[int(time.time() * 10) % len(_SPIN)]
    pulse = [("  fleet ", "head"),
             (spin + " %d" % n_wk, "g_work"), (" working   ", "dim"),
             ("● %d" % n_id, "g_work_off"), (" idle   ", "dim")]
    if n_dt:
        pulse += [(_DETACHED_GLYPH + " %d" % n_dt, "g_work_off"), (" detached   ", "dim")]
    if jobs:
        pulse += [("↳ %d" % len(jobs), "dim"),
                  (" job%s (%d working)" % ("s" if len(jobs) != 1 else "", jw), "dim")]
    lines.append(pulse)                 # (Σ cost 롤업 제거 — user: 금액 표시 삭제)
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
        # Depth 1 jobs can nest under an on-screen parent session; depth 2 jobs nest under
        # their capability-owner job via parent_slug. This keeps main-session context light
        # while fleet still shows cross-harness orchestration shape.
        children = {}      # session_id -> [jobs] (nested under an on-screen parent)
        job_children = {}  # parent dispatch slug -> [depth-2 jobs]
        orphans = []       # project-level fallback (parent dead/off-screen/no-env)
        loops_jobs = []    # no-parent-is-normal (cron loops) — no orphan marker
        for j in group_jobs:
            if getattr(j, "parent_slug", None) and getattr(j, "depth", 1) >= 2:
                job_children.setdefault(j.parent_slug, []).append(j)
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
        # cooling (round-6, user 2026-07-03): no active work, but the newest session transcript
        # write is ≤ _COOL_WINDOW_MIN old → the directory just finished and is "식는 중". A middle
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
        # 2026-07-03: 폴더(repo)임을 간단하게), dim so the name stays the focal word.
        # The blinking green ● now lives HERE (directory level = "work happening inside") —
        # sessions animate a spinner instead, so the dot no longer collides with row vocabulary.
        head_segs = []
        if n_work:
            head_segs += [("●", "g_work" if _BLINK_ON else "g_work_off"), (" ", None)]
        elif _cool_min is not None:
            # 방금 끝남 = 채운 ● (회색): 아직 온기 — dead ✕/stale · 와 확실히 구분
            head_segs += [(_COOL_FILLED, "grp_cool"), (" ", None)]
        else:
            # 오래된 비활성 = 고리 ○ (회색): 잠든 디렉토리 (shape-size gradient ● > ○)
            head_segs += [(_COOL_RING, "grp_cold"), (" ", None)]
        # cooling 디렉토리는 이름도 어두운 노랑(인디케이터 포함 통일) — cold 는 기본 제목색 유지
        _name_key = "grp_hot" if n_work else ("grp_cool" if _cool_min is not None else "grp")
        head_segs += [(name, _name_key), ("/", "dim")]
        _nwt = _wt_count(gcwd)
        if _nwt:
            # statusline 과 같은 표기 (🚧 N = 병렬 작업장·잔존 worktree, §5.10) — 이름 바로 옆
            head_segs += [(" 🚧 %d" % _nwt, "g_idle")]
            _seen_glyphs.add("wt")
        _nmem = mem_by_group.get(name, 0)
        if _nmem:
            head_segs += [(" 🧠 %d" % _nmem, "dim")]
            _seen_glyphs.add("mem")
        if _cool_min is not None:
            # 완료 후 경과시간 (끝나고 대기하는 시간) — ✓ 프리픽스로 "완료 후 경과"임을 명시
            head_segs += [("  ", None), ("%s %s" % (_COOL_TIME_ICON, fmt_min(_cool_min)), "grp_cool")]
        if gword:
            head_segs += [("  ", None), (gword, gwkey)]
        # group header = the card's TITLE row (user 2026-07-03 pick: 카드 안 타이틀) — first
        # tinted row of the panel, ▍ anchor on the card's padding edge; no floating label.
        _g0 = len(lines)                # panel start (title INCLUDED in the tint range)
        lines.append(head_segs)
        _rail_key = "grp_live" if n_work else "dim"
        if n_work:
            _body_tint = _TINT_BODY_HOT       # 활성 = midnight-blue 컬러 틴트
        elif _cool_min is not None:
            _body_tint = _TINT_BODY_COOL      # 방금 끝남 = 중간레벨 (활성과 비활성 사이)
        else:
            _body_tint = _TINT_BODY           # 비활성 = 기본 어두운 grey

        # rows stay tight (no blank line — that spread them too far apart); the mid-line gauge
        # glyph (━/─) is what keeps the stacked context bars from merging into a solid wall.
        _srow = {"wide": None, "narrow": _session_row_2line, "stack": _session_row_stack}[layout]
        _jrow = {"wide": None, "narrow": _dispatch_row_2line, "stack": _dispatch_row_stack}[layout]
        # LIVE main-session lines get bold text (user 2026-07-03, after a whole-row tint-
        # brightening attempt read as "좌우로 쭉 다 밝아져서 별로" — weight, not background,
        # carries the distinction). Excludes stale/dead/app-server/detached (already faded dim).
        _sess_bold_ids = set()

        def _emit_dispatch_tree(job, parent_model=None, parent_harness=None, parent_effort=None,
                                orphan=False, is_last=True):
            # SD-F2 — a depth-1 conductor's OWN breadcrumb tracks its active depth-2 stage
            # worker, not its static argv/plan-derived `stage`. `job_children` is the
            # enclosing closure dict, so this is readable before the row renders.
            stage_override = _conductor_stage_override(job)
            if job.liveness == "stale":
                _seen_glyphs.add("stale")
            elif job.liveness == "dead":
                _seen_glyphs.add("dead")
            if _jrow:
                lines.extend(_jrow(job, orphan=orphan, parent_model=parent_model,
                                   parent_effort=parent_effort, stage_override=stage_override))
            else:
                lines.append(_dispatch_row(job, orphan=orphan, parent_model=parent_model,
                                           parent_harness=parent_harness,
                                           parent_effort=parent_effort, is_last=is_last,
                                           stage_override=stage_override))
            for sub in _sort_group_jobs(job_children.get(job.slug, [])):
                # F-15b P0-2: a depth-2 stage worker that is done/queued/idle is already
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
            kids = [(k, _stage_role_label(getattr(k, "worker_role", None))[0])
                    for k in job_children.get(job.slug, []) if getattr(k, "depth", 1) == 2]
            kids = [(k, label) for k, label in kids if label is not None]
            if not kids:
                return None
            active = [label for k, label in kids if k.liveness == "working"]
            if active:
                return active[0]
            return job.stage

        for s in _sort_group_sessions(shown):
            if getattr(s, "mem_worker", False):
                # F-18b: `a` 토글로만 노출되는 dim mem row — 활성 row 렌더러(스타일/기울기/depth
                # nesting)를 타지 않고 전용 요약 1-line 으로.
                lines.extend(_mem_row(s, layout))
                _seen_glyphs.add("mem")
                continue
            kids = _sort_group_jobs(children.get(s.session_id, []))
            nested_n = len(kids) + sum(len(job_children.get(k.slug, [])) for k in kids)
            if s.liveness == "stale":
                _seen_glyphs.add("stale")
            elif s.liveness == "dead":
                _seen_glyphs.add("dead")
            if s.detached and s.liveness not in ("stale", "dead"):
                _seen_glyphs.add("detached")
            if nested_n:
                _seen_glyphs.add("child")
            _n0 = len(lines)
            if _srow:
                lines.extend(_srow(s, is_parent=bool(nested_n), child_count=nested_n))
            else:
                lines.append(_session_row(s, narrow, is_parent=bool(nested_n), child_count=nested_n))
            if not (s.liveness in ("stale", "dead") or s.app_server or s.detached):
                _sess_bold_ids.update(range(_n0, len(lines)))
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

        # group BODY (round-5): every row of the group rides the body tint — the whole directory
        # is one solid panel, brighter when active (user: 디렉토리 블록 전체에 틴트, 헤더만 X).
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

    # legend — status dots (columns are labelled by the header row). F-12(c): working/idle/
    # dispatch/`~` are always-relevant vocabulary and stay unconditional; the rest only appear
    # when this build actually used them (_seen_glyphs, tracked above — local, not global).
    lines.append(None)
    legend = [
        ("  ", None), ("⠹", "g_work"), (" working   ", "dim"),
        ("●", "g_work_off"), (" idle   ", "dim"),
    ]
    if "detached" in _seen_glyphs:
        legend += [(_DETACHED_GLYPH, "g_work_off"), (" detached   ", "dim")]
    if "stale" in _seen_glyphs:
        legend += [("·", "g_stale"), (" stale   ", "dim")]
    if "dead" in _seen_glyphs:
        legend += [("✕", "g_dead"), (" dead     ", "dim")]
    if "child" in _seen_glyphs:
        legend += [("▾N", "dim"), (" child jobs   ", "dim")]
    if jobs:
        legend += [("↳", "dim"), (" dispatch   ", "dim")]
    if "wt" in _seen_glyphs:
        legend += [("🚧 N", "dim"), (" worktrees   ", "dim")]
    if n_mem_total or "mem" in _seen_glyphs:
        # 전역 총계 — mem-only 그룹은 fold 되어 header badge 가 안 뜰 수 있으므로 legend 에서
        # 항상 존재를 노출 (group badge 는 활성 그룹 컨텍스트, 여긴 board 전역). F-19: mem-worker
        # 세션이 0 이어도 write-events 요약행/alert 가 떴으면 legend 는 여전히 노출한다.
        legend += [("🧠 %d" % n_mem_total, "dim"), (" mem   ", "dim")]
    legend += [("~", "dim"), (" derived/inherited value", "dim")]  # F-9(d)
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
                         layout=_layout_mode(tw), memory=mem_snapshot)
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
_INSET = 2                  # panel outer margin (cols) — 바깥 여백은 이대로 (user)
_PAD_IN = 2                 # EXTRA inner padding: tint edge ↔ content (user: 여백을 늘리자)
_RFLUSH = "\x00 \x00"
_HFILL = "\x00─\x00"

# row-tint sentinels (round-5 — herdr-style panel tints): a LEADING sentinel marks the whole
# row's background level. b/c = group body/cap · B/C = the ACTIVE-group variants (brighter,
# user 2026-07-02: 활성 디렉토리 틴트를 더 눈에 띄게) · i = intel zone (usage/pulse/alert).
_TINT_BODY, _TINT_CAP = "\x00b\x00", "\x00c\x00"
_TINT_BODY_HOT, _TINT_CAP_HOT = "\x00B\x00", "\x00C\x00"
_TINT_BODY_COOL = "\x00k\x00"    # cooling(방금 끝남) body — 중간레벨 (활성 blue 와 비활성 grey 사이)
_TINT_INTEL = "\x00i\x00"
_TINT_CHARS = {"b", "c", "B", "C", "k", "i"}

# row-bold marker (user 2026-07-03, after the whole-row tint-brightening attempt was rejected —
# "좌우로 쭉 다 밝아져서 별로": a MAIN session's rows are entirely BOLD instead — same tint as
# any other row in the card, font weight carries the distinction). Inserted AFTER any tint
# sentinel (so tint detection in _addline is unaffected) by the group-loop post-pass.
_ROW_BOLD = "\x00!\x00"
# 256-color background levels per sentinel char. Base panels = dark GREY (235/238); the
# ACTIVE-group variants are a dark COLORED tint (user 2026-07-02 최종: 기본은 어둡게, 활성
# 디렉토리만 컬러 — 미드나잇 블루). 17 = #00005f, the cube's darkest blue: natively subtle
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


def _draw(stdscr, sessions, jobs, section, malformed, memory=None):
    global _OFFSET, _TOGGLE_ROWS
    _TOGGLE_ROWS = {}    # reset before any early-return so a stale map never survives a click
    h, w = stdscr.getmaxyx()
    stdscr.erase()
    narrow = w < _NARROW_CUTOFF
    lines = _build_lines(sessions, jobs, section, narrow, malformed, layout=_layout_mode(w),
                         memory=memory)
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
    wlbl = "wide/narrow/stack" if _LAYOUT == "auto" else ("%s!" % _LAYOUT)
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
            mem_snapshot = _collect_memory()
            last = now
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
