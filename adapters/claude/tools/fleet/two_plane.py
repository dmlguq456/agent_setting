"""Two-plane provisional-grammar demo (v10, additive, demo-only fixture screen).

Renders the "grid plane" (session rows) via the REAL render engine's own row builders
(`render._session_row` / `_session_row_2line` / `_session_row_stack`, unmodified) so color,
alignment and cell format stay structurally identical to the normal board. Everything a
session spawns (⚡ sub-agents, ▸ dispatch pipelines, the stage canvas, node-anchored ⚡,
per-repo mem events) secedes from that grid into a separate "process plane" rendered by the
bespoke builders below — the shape the grid's own row builders don't produce (a session row
is one line; a process-plane entity can be several, with its own connector glyphs).

Entirely self-contained: never touches live collection, `demo.py`'s fixture, or any existing
render path. Gated behind `render.set_two_plane_demo(True)` (wired to `fleet.py --demo
two-plane`) — the flag defaults False, so every existing render path is untouched.
"""
import time

from . import render as r
from .model import Session, DispatchJob


def _fixture():
    """The pixture cast (§ prd.md spec-read gate checked — no F-29/F-30 vocabulary reused for
    a different meaning here; sessions/jobs below are plain rows, not F-29 SubAgent/F-30 route
    records)."""
    S, J = Session, DispatchJob
    sessions = [
        S(harness="claude", pid=97001, cwd="/home/demo/agent_setting",
          session_id="tp-claude-main", slug="fleet-ui-two-plane-demo",
          title="fleet UI two-plane demo", model="opus", effort="high",
          ctx_pct=42, elapsed_min=134, liveness="working",
          gate="tracked", branch="main"),
        S(harness="codex", pid=97002, cwd="/home/demo/agent_setting",
          session_id="tp-codex-main", slug="usage-probe-rate-window",
          title="usage probe rate-window", model="gpt", effort="medium",
          ctx_pct=18, elapsed_min=41, liveness="idle",
          gate="tracked", branch="wt-usage"),
        S(harness="claude", pid=97003, cwd="/home/demo/worklog-board",
          session_id="tp-claude-worklog", slug="weekly-board-cleanup",
          title="주간 보드 정리", model="opus", effort="medium",
          ctx_pct=31, elapsed_min=62, liveness="idle",
          gate="tracked", branch="main"),
    ]
    jobs = [
        J(key="code", stage="exec", mode="dev", qa="thorough", qa_source="jobslog",
          harness="claude", model="Opus 4.8", effort="high", elapsed_min=20,
          slug="usage-accuracy", cwd="/home/demo/agent_setting-wt/usage-accuracy",
          parent_sid="tp-claude-main", is_child=True, depth=1, liveness="working",
          intensity="thorough", capability_owner="autopilot-code"),
        J(key="code", stage="exec", mode="dev", qa="quick", qa_source="argv",
          harness="codex", model="gpt-5.5", effort="medium", elapsed_min=4,
          slug="rate-window", cwd="/home/demo/agent_setting-wt/rate-window",
          parent_sid="tp-claude-main", is_child=True, depth=1, liveness="working",
          intensity="quick", capability_owner="autopilot-code"),
        J(key="note", elapsed_min=0, slug="loop-note", cwd="/home/demo/worklog-board",
          parent_sid=None, liveness="queued"),
    ]
    return sessions, jobs


def _desc_w(term_width):
    """Description-quote budget scaled to terminal width — keeps the 60-col capture readable
    without a fixed cap clipping every width the same way."""
    return max(16, min(70, (term_width or 120) - 46))


def _pad_dw(s, w):
    """Pad `s` to exactly `w` DISPLAY cells — `render._pad` truncates/pads by Python character
    count, which under-pads a CJK string (each Hangul syllable is 2 cells, e.g. "개발팀" is 3
    chars/6 cells) relative to an ASCII one of the same character count, breaking column
    rhythm between sibling rows (a Korean agent_type vs. "Explore"). Composed from the engine's
    own `_dw`/`_clip_w` (measurement + truncation) — no table edits, no new render.py surface."""
    s = s or ""
    dw = r._dw(s)
    if dw >= w:
        return r._clip_w(s, w, ellipsis="")
    return s + " " * (w - dw)


# Fixed indent rhythm (grammar v2, user-confirmed 2026-07-16): the ├─/└─ tree lattice is
# retired in favor of the session-child ↳ spawn arrow render.py's own `_dispatch_prefix`
# already uses for depth-1 dispatch rows (see render.py's "user pick over ├─/└─ tree bars"
# comment) — no vertical spine (`│`) survives anywhere in this view. Same-level child rows
# share one indent constant so their leading glyph lands in the same column.
_ARROW_PREFIX = "   ↳ "      # dispatch (▸) rows — arrow + space, ▸ lands at column 5
_AGENT_IND = "     "         # session's own ⚡ sub-agent rows — ⚡ also lands at column 5
_NODE_IND = " " * 8          # canvas row + its node-anchored ⚡ children (nested under ▸)
_SUBNODE_IND = " " * 10      # canvas' own `└ exec:B …` worker sub-row, one level under _NODE_IND

# Stage palette in its PLAIN (non-bold) intensity — reused engine keys, not new table entries
# (round-2, user-confirmed): bold is reserved for the main-session row (_ROW_BOLD) alone, so
# every stage-colored cell in this view (canvas active node, ▸ row's 🔧/glyph) uses the plain
# hue instead of the engine's bold stgN_on. Index order matches render.py's own stage palette
# (0=blue·1=cyan·2=green·3=yellow·4=magenta, see _stage_raw).
_STAGE_PLAIN = ("eff_high", "fam_opus", "lvl_g", "g_idle", "fam_fable")


def _with_branch_glyph(lines, pad_width=None):
    """Prepend the ⎇ glyph to the FIRST `branch_s`-keyed segment in each line (session rows
    only ever carry one). Additive to this view only — `render._branch_seg` itself is untouched,
    so every other caller's output is unaffected."""
    out = []
    for segs in lines:
        new = []
        done = False
        for t, k in segs:
            if not done and k == "branch_s":
                stripped = t.strip()
                t = r._pad("⎇ " + stripped, pad_width) if pad_width else ("  ⎇ " + stripped)
                done = True
            new.append((t, k))
        out.append(new)
    return out


def _session_lines(s, layout, term_width, wide_name_width):
    """The grid plane, unmodified: reuse the exact row builder the normal board would pick for
    this width/layout, then bold the whole row (main-session font-weight rule, `_ROW_BOLD` —
    none of this fixture's sessions are stale/dead so all three qualify, same as the real
    engine's own `_sess_bold_ids` condition)."""
    if layout == "wide":
        lines = _with_branch_glyph([r._session_row(s, False, name_width=wide_name_width)],
                                   pad_width=r._BRW)
    elif layout == "narrow":
        l1, l2 = r._session_row_2line(s, term_width=term_width)
        lines = _with_branch_glyph([l1, l2])
    else:
        lines = _with_branch_glyph(r._session_row_stack(s, term_width=term_width))
    bold = s.liveness not in ("stale", "dead") and not s.app_server and not s.detached
    if bold:
        lines = [[(r._ROW_BOLD, None)] + ln for ln in lines]
    return lines


def _agent_line(prefix, agent_type, desc, glyph, elapsed_str, active, desc_w, anchor=None):
    """`⚡ <agent-type> "<desc>" <glyph> <elapsed>` — no connector, pure indent (grammar #2, the
    tree lattice never reached this row kind — only the spine it sat beside is gone now).
    Active = normal weight; completed = dim (grammar #8 — dim is completed/inactive ONLY, never
    used to mute a live row). `agent_type`/desc/anchor are padded to fixed DISPLAY widths
    (`_pad_dw`, CJK-aware) so the desc/anchor/status columns line up across sibling rows even
    when one carries a Korean agent_type ("개발팀") and another an ASCII one ("Explore")."""
    key = None if active else "dim"
    quoted = _pad_dw(r._clip_w('"%s"' % desc, desc_w), desc_w)
    segs = [(prefix, "dim"), ("⚡ ", key), (_pad_dw(agent_type, 10), key), (quoted, key)]
    if anchor:
        segs.append((" @" + _pad_dw(anchor, 8), "stg1_off"))
    segs.append((" %s %s" % (glyph, elapsed_str), key))
    return segs


def _dispatch_line(connector, harness, cap_key, cap_slug, title, contract, elapsed_str, desc_w,
                   stg_key=_STAGE_PLAIN[1], mode="dev"):
    """`↳ ▸ <harness plain-hue text> 🔧 <capability>·<mode> ⎇ <slug> "<title>" (<contract>) <elapsed>`
    — session-child spawn arrow, no rail lattice (grammar #3, round-2). Harness text uses the
    BRIGHT `hb_*` key (never the dispatch row's dim `h_*`) — a spawned entity's identity is
    still legible, only completed rows dim. `stg_key` is one of the plain (non-bold) `_STAGE_PLAIN`
    hues — bold is reserved for the main-session row alone (round-2, user-confirmed).
    r3: `·<mode>` restores the existing options-column mode field (dev|debug|audit — parity),
    `⎇ <slug>` marks the slug as the task branch/worktree name (user: bare "usage-accuracy" was
    unreadable), and the contract carries NO qa level — qa was retired as a separate axis
    (CONVENTIONS §1.1: rigor derives from intensity). The contract DOES carry the registry's
    `worker_role` (owner/quick_owner/review/support — the depth-1 bootstrap type evidence);
    stage workers surface as canvas nodes instead of rows, so `pipeline_stage` never appears."""
    hb_key = "hb_" + harness if harness in r._BADGE_TEXT else "hb_other"
    segs = [(connector, "dim"), ("▸ ", stg_key),
            (r._BADGE_TEXT.get(harness, harness) + "  ", hb_key),
            ("🔧 ", None), (cap_key, stg_key), ("·" + mode + " ", "dim"),
            ("⎇ " + cap_slug + "  ", "dim"),
            (r._clip_w('"%s"' % title, desc_w), None),
            (" " + contract, "dim"), ("  " + elapsed_str, "dim")]
    return segs


def _canvas_line(indent, nodes):
    """The stage canvas — one row below the conductor, stages joined by the existing breadcrumb
    separator ` › ` (grammar #4), each stage its own STG hue. Active nodes use the PLAIN
    (non-bold) `_STAGE_PLAIN` hue rather than the engine's bold `stgN_on` — bold is reserved for
    the main-session row alone (round-2, user-confirmed). Done/pending keep the existing dim
    `stgN_off` unchanged."""
    segs = [(indent, "dim")]
    for i, n in enumerate(nodes):
        if i:
            segs.append((" › ", "dim"))
        on, off = _STAGE_PLAIN[i % 5], "stg%d_off" % (i % 5)
        state = n["state"]
        if state == "done":
            segs.append((n["label"] + " ✓" + n.get("time", ""), off))
        elif state == "active":
            segs.append((n["label"] + " ● " + n.get("time", ""), on))
            if n.get("meta"):
                segs.append((" " + n["meta"], "dim"))
        else:
            segs.append((n["label"] + " ○", off))
    return segs


def build_lines(term_width, layout):
    """Return the flat segment-line list for the two-plane demo screen — same contract
    `render._build_lines` returns ([(text, color_key), ...] per line, `None` = blank), so both
    `render_once` (plain --once) and the live curses draw loop can consume it unmodified."""
    sessions, jobs = _fixture()
    s_main, s_codex, s_worklog = sessions
    wide_name_width = r._wide_name_width(term_width) if layout == "wide" else None
    desc_w = _desc_w(term_width)
    lines = []

    # ---- top intel zone: usage (1 row/harness) · pulse · mem summary ----
    gw = 12
    lines.append([("  usage ", "head"), (r._pad("claude code", 14), "hb_claude"),
                  ("[", "dim")] + r._gauge_segs(62, gw) +
                 [(" %3d%%" % 62, r._pct_key(62)), ("]", "dim"),
                  ("  ↻ 2h11m · 5h window", "dim")])
    lines.append([("        ", "head"), (r._pad("codex", 14), "hb_codex"),
                  ("[", "dim")] + r._gauge_segs(18, gw) +
                 [(" %3d%%" % 18, r._pct_key(18)), ("]", "dim"),
                  ("  weekly 43%", "dim")])
    lines.append(r._pulse_segs(sessions, jobs))
    fake_mem = {"today": {"added": 4, "added_working": 3, "added_durable": 1,
                          "expired": 0, "pruned": 1},
                "last_distill_min": 45, "alerts": {}}
    mem_line = r._mem_summary_segs(fake_mem)
    if mem_line:
        lines.append(mem_line)
    lines.append([(r._HFILL, None)])
    lines.append(None)
    _sh = " " * (r._INSET + r._PAD_IN) if r._TINT_OK else ""
    if layout != "wide":
        lines.append([(_sh + "  SESSIONS", "head"), (r._RFLUSH, None),
                      ("two-plane demo", "head")])
    else:
        lines.append([(_sh + r._col_head(wide_name_width or r._NW_S), "head"),
                      (r._RFLUSH, None), ("time" + " " * (r._INSET + r._PAD_IN + 1), "head")])
    lines.append(None)

    # ==== group 1: agent_setting (active) ====
    # header glyph/name: plain (non-bold) hue — bold is reserved for the main-session row alone
    # (round-2, user-confirmed). "●"/"grp_hot" (bold) → "●"/"grp_live" keeps the same green.
    g1 = [[("●", "lvl_g" if r._BLINK_ON else "g_work_off"),
           (" ", None), ("agent_setting", "grp_live"), ("/", "dim")]]
    g1.extend(_session_lines(s_main, layout, term_width, wide_name_width))
    g1.append(_agent_line(_AGENT_IND, "Explore",
                          "fleet 제목 파이프라인 조사 — refresh 대상 필터·sidecar 소스 확인",
                          "●", "2m51s", True, desc_w))
    g1.append(_agent_line(_AGENT_IND, "Explore", "렌더 구조·stage 존·mem 표시 조사",
                          "✓", "4m04s", False, desc_w))
    g1.append(None)
    g1.append(_dispatch_line(_ARROW_PREFIX, "claude", "code", "usage-accuracy",
                             "usage 소스 신뢰 규칙 구현", "(thr · owner)", "⏳ 20m",
                             desc_w, stg_key=_STAGE_PLAIN[1]))
    g1.append(_canvas_line(_NODE_IND, [
        {"label": "plan", "state": "done", "time": "12m"},
        {"label": "exec", "state": "active", "time": "8m", "meta": "(claude·haiku·med)"},
        {"label": "test", "state": "pending"},
        {"label": "report", "state": "pending"},
    ]))
    g1.append([(_SUBNODE_IND, None), ("└ ", "dim"),
               ("exec:B ● 3m", _STAGE_PLAIN[1]), (" (claude·sonnet·med)", "dim")])
    g1.append(_agent_line(_NODE_IND, "개발팀", "usage tap freshness 파서 구현",
                          "●", "1m12s", True, desc_w, anchor="exec"))
    g1.append(_agent_line(_NODE_IND, "Explore", "usage tap 스키마 사전 조사",
                          "✓", "48s", False, desc_w, anchor="exec:B"))
    g1.append(None)
    g1.append(_dispatch_line(_ARROW_PREFIX, "codex", "code", "rate-window",
                             "rate-window 헤더 재검증", "(quick · quick_owner · gpt·med)", "● 4m",
                             desc_w, stg_key=_STAGE_PLAIN[0]))
    g1.append(None)
    g1.extend(_session_lines(s_codex, layout, term_width, wide_name_width))
    g1.append([(" \U0001f9e0 ", "dim"), ("14:02 ", "dim"), ("+", "lvl_g"),
               (" durable/project ", "dim"), ("distiller  ", "dim"),
               ("\"fleet 두-평면 문법 확정 — 자식 행은 세션 그리드에서 탈퇴\"", "dim")])
    # "−" was "lvl_r" (bold red) — the engine has no plain (non-bold) red hue in its table
    # (red is reserved as its "one true alarm", always bold by design), so this bespoke
    # +/− pair falls back to "dim" rather than inventing a new table entry (round-2).
    g1.append([(" \U0001f9e0 ", "dim"), ("13:47 ", "dim"), ("−", "dim"),
               (" working/expired ", "dim"), ("curator    ", "dim"),
               ("\"usage 주간 카운터 가설 폐기 (43%는 mtime-신선 tap 오판)\"", "dim")])

    # in-card blank separators stay ON the tint band — an untinted (None) blank row splits the
    # card into visual fragments (user: "분사 세션을 틴트로 갈라버리면 어쩌냐"). Only the
    # BETWEEN-cards gap below stays untinted.
    for ln in g1:
        lines.append([(r._TINT_BODY_HOT, None)] + (ln if ln is not None else []))
    lines.append(None)

    # ==== group 2: worklog-board (inactive) ====
    # "grp" (bold, no hue) → None: no color to keep here, only the bold to drop (round-2).
    g2 = [[("○", "grp_cold"), (" ", None), ("worklog-board", None), ("/", "dim")]]
    g2.extend(_session_lines(s_worklog, layout, term_width, wide_name_width))
    g2.append([("   ▸ ", "dim"), (r._BADGE_TEXT.get("claude", "claude") + "  ", "h_claude"),
               ("loop:note ", "dim"), (r._clip_w('"오전 수집분 다이제스트"', desc_w), "dim"),
               ("  queued · next 18m", "dim")])
    for ln in g2:
        lines.append([(r._TINT_BODY, None)] + (ln if ln is not None else []))

    # ---- legend (same vocabulary the standard board's legend uses) ----
    # "g_work" (bold) → "lvl_g" (plain green, round-2): this legend row is this view's own,
    # not a reused engine chrome function, so the bold-only-on-main-session rule applies here too.
    lines.append(None)
    lines.append([("  ", None), ("●", "lvl_g"), (" working   ", "dim"),
                  ("●", "g_work_off"), (" idle   ", "dim"),
                  ("⚡", "dim"), (" sub-agent   ", "dim"),
                  ("▸", "dim"), (" pipeline   ", "dim"),
                  ("✓", "dim"), (" done   ", "dim"),
                  ("○", "dim"), (" pending", "dim")])
    return lines
