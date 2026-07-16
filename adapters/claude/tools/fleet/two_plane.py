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
    """`⚡ <agent-type> "<desc>" <glyph> <elapsed>` — no connector (spine-adjacent inset row,
    grammar #2). Active = normal weight; completed = dim (grammar #8 — dim is completed/inactive
    ONLY, never used to mute a live row)."""
    key = None if active else "dim"
    segs = [(prefix, "dim"), ("⚡ ", key), (r._pad(agent_type, 10), key),
            (r._clip_w('"%s"' % desc, desc_w), key)]
    if anchor:
        segs.append((" @" + anchor, "stg1_off"))
    segs.append((" %s %s" % (glyph, elapsed_str), key))
    return segs


def _dispatch_line(connector, harness, cap_key, cap_slug, title, contract, elapsed_str, desc_w,
                   stg_key="stg1_on"):
    """`▸ <harness plain-hue text> 🔧 <capability> · <slug> "<title>" (<job contract>) <elapsed>`
    — rail connector (grammar #3). Harness text uses the BRIGHT `hb_*` key (never the dispatch
    row's dim `h_*`) — a spawned entity's identity is still legible, only completed rows dim."""
    hb_key = "hb_" + harness if harness in r._BADGE_TEXT else "hb_other"
    segs = [(connector, "dim"), ("▸ ", stg_key),
            (r._BADGE_TEXT.get(harness, harness) + "  ", hb_key),
            ("🔧 ", None), (cap_key, stg_key), (" · " + cap_slug + "  ", "dim"),
            (r._clip_w('"%s"' % title, desc_w), None),
            (" " + contract, "dim"), ("  " + elapsed_str, "dim")]
    return segs


def _canvas_line(indent, nodes):
    """The stage canvas — one row below the conductor, stages joined by the existing breadcrumb
    separator ` › ` (grammar #4), each stage its own STG hue (same palette `_stage_segs` already
    uses: stgN_on = current/lit, stgN_off = past/pending)."""
    segs = [(indent, "dim")]
    for i, n in enumerate(nodes):
        if i:
            segs.append((" › ", "dim"))
        on, off = "stg%d_on" % (i % 5), "stg%d_off" % (i % 5)
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
    g1 = [[("●" if r._BLINK_ON else "●", "g_work" if r._BLINK_ON else "g_work_off"),
           (" ", None), ("agent_setting", "grp_hot"), ("/", "dim")]]
    g1.extend(_session_lines(s_main, layout, term_width, wide_name_width))
    g1.append(_agent_line("   │   ", "Explore",
                          "fleet 제목 파이프라인 조사 — refresh 대상 필터·sidecar 소스 확인",
                          "●", "2m51s", True, desc_w))
    g1.append(_agent_line("   │   ", "Explore", "렌더 구조·stage 존·mem 표시 조사",
                          "✓", "4m04s", False, desc_w))
    g1.append([("   │", "dim")])
    g1.append(_dispatch_line("   ├─", "claude", "code", "usage-accuracy",
                             "usage 소스 신뢰 규칙 구현", "(thr · ~thorough)", "⏳ 20m",
                             desc_w, stg_key="stg1_on"))
    g1.append(_canvas_line("   │    ", [
        {"label": "plan", "state": "done", "time": "12m"},
        {"label": "exec", "state": "active", "time": "8m", "meta": "(claude·haiku·med)"},
        {"label": "test", "state": "pending"},
        {"label": "report", "state": "pending"},
    ]))
    g1.append([("   │", "dim"), (" " * 16, None), ("└ ", "dim"),
               ("exec:B ● 3m", "stg1_on"), (" (claude·sonnet·med)", "dim")])
    g1.append(_agent_line("   │        ", "개발팀", "usage tap freshness 파서 구현",
                          "●", "1m12s", True, desc_w, anchor="exec"))
    g1.append(_agent_line("   │        ", "Explore", "usage tap 스키마 사전 조사",
                          "✓", "48s", False, desc_w, anchor="exec:B"))
    g1.append([("   │", "dim")])
    g1.append(_dispatch_line("   └─", "codex", "code", "rate-window",
                             "rate-window 헤더 재검증", "(quick · gpt·med)", "● 4m",
                             desc_w, stg_key="stg0_on"))
    g1.append(None)
    g1.extend(_session_lines(s_codex, layout, term_width, wide_name_width))
    g1.append([(" \U0001f9e0 ", "dim"), ("14:02 ", "dim"), ("+", "lvl_g"),
               (" durable/project ", "dim"), ("distiller  ", "dim"),
               ("\"fleet 두-평면 문법 확정 — 자식 행은 세션 그리드에서 탈퇴\"", "dim")])
    g1.append([(" \U0001f9e0 ", "dim"), ("13:47 ", "dim"), ("−", "lvl_r"),
               (" working/expired ", "dim"), ("curator    ", "dim"),
               ("\"usage 주간 카운터 가설 폐기 (43%는 mtime-신선 tap 오판)\"", "dim")])

    for ln in g1:
        lines.append(None if ln is None else [(r._TINT_BODY_HOT, None)] + ln)
    lines.append(None)

    # ==== group 2: worklog-board (inactive) ====
    g2 = [[("○", "grp_cold"), (" ", None), ("worklog-board", "grp"), ("/", "dim")]]
    g2.extend(_session_lines(s_worklog, layout, term_width, wide_name_width))
    g2.append([("   ▸ ", "dim"), (r._BADGE_TEXT.get("claude", "claude") + "  ", "h_claude"),
               ("loop:note ", "dim"), (r._clip_w('"오전 수집분 다이제스트"', desc_w), "dim"),
               ("  queued · next 18m", "dim")])
    for ln in g2:
        lines.append(None if ln is None else [(r._TINT_BODY, None)] + ln)

    # ---- legend (same vocabulary the standard board's legend uses) ----
    lines.append(None)
    lines.append([("  ", None), ("●", "g_work"), (" working   ", "dim"),
                  ("●", "g_work_off"), (" idle   ", "dim"),
                  ("⚡", "dim"), (" sub-agent   ", "dim"),
                  ("▸", "dim"), (" pipeline   ", "dim"),
                  ("✓", "dim"), (" done   ", "dim"),
                  ("○", "dim"), (" pending", "dim")])
    return lines
