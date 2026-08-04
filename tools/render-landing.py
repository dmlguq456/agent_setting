#!/usr/bin/env python3
"""Render the public GitHub Pages surface: docs/index.html + docs/map.html.

The landing page is an app shell: a scrolling narrative sidebar on the left and
a full-bleed diagram canvas on the right that carries the agent map — the same
layered structure the internal operator hub (root hub.html) shows, re-cut for a
public audience so the flagship subsystems are visible: sealed N-way dispatch,
the Fleet view over it, per-role model tiers, the fixed artifact system, the
persistent memory store, and the loops that keep the harness honest.

Sources: manifest.json (tracks, hooks, loops) and
harness-manifest.json (capability census, summaries, taxonomy). Both pages are
self-contained (no CDN/network), share one design system, and are dark-first
with a light override. The internal operator hub is intentionally NOT published.

Usage:
  python3 tools/render-landing.py          # write docs/index.html + docs/map.html
  python3 tools/render-landing.py --check  # verify both files are current
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
REPO_URL = "https://github.com/dmlguq456/agent_setting"
INSTALL_CMD = (
    "curl -fsSL https://github.com/dmlguq456/agent_setting/"
    "releases/latest/download/install.sh | sh"
)


def load_data() -> dict:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    harness = json.loads((ROOT / "harness-manifest.json").read_text(encoding="utf-8"))
    caps = harness["capabilities"]
    units = harness["units"]
    entries = sorted(
        name for name, spec in caps.items()
        if spec["invocation"]["class"] == "entry-router"
    )
    hard_hooks = [h for h in manifest["hooks"] if h.get("hard_block")]
    roles = sorted({spec["role"] for spec in units.values()})
    return {
        "caps": caps,
        "units": units,
        "roles": roles,
        "entries": entries,
        "tracks": manifest["tracks"],
        "hard_hooks": hard_hooks,
        "loops": manifest["loops"],
        "cap_total": len(caps),
        "entry_total": len(entries),
        "unit_total": len(units),
        "role_total": len(roles),
        "hook_total": len(manifest["hooks"]),
        "hard_total": len(hard_hooks),
        "loop_total": len(manifest["loops"]),
    }


# ---------------------------------------------------------------- design system

CSS = r"""
  :root {
    color-scheme: dark light;
    --font-ui: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont,
               "SF Pro Text", "Segoe UI", "Apple SD Gothic Neo", "Noto Sans KR", system-ui, sans-serif;
    --font-mono: "JetBrains Mono", ui-monospace, "SF Mono", SFMono-Regular, Menlo, monospace;

    --bg: #08080B;
    --bg-2: #0B0B10;
    --panel: rgba(255,255,255,.030);
    --panel-2: rgba(255,255,255,.058);
    --solid: #101016;
    --border: rgba(255,255,255,.085);
    --border-2: rgba(255,255,255,.16);
    --text: #ECECF2;
    --text-2: #9E9EAE;
    --text-3: #6B6B7B;

    --g1: #6D6DF6; --g2: #A855F7; --g3: #22D3EE;
    --accent: #8B8BFA;
    --accent-soft: rgba(109,109,246,.15);
    --ok: #34D399; --warn: #FBBF24; --danger: #FB7185; --info: #60A5FA;

    --term-bg: #08080D; --term-br: rgba(255,255,255,.13); --term-tx: #C9C9D6;

    --grid-line: rgba(255,255,255,.035);
    --wire: rgba(150,150,255,.34);
    --glow-a: rgba(109,109,246,.20);
    --glow-b: rgba(34,211,238,.11);
    --shadow: 0 1px 2px rgba(0,0,0,.5), 0 12px 34px rgba(0,0,0,.42);
    --r-lg: 18px; --r-md: 12px; --r-sm: 8px;
  }
  @media (prefers-color-scheme: light) {
    :root {
      --bg: #FBFBFD;
      --bg-2: #F4F4F8;
      --panel: rgba(20,20,45,.028);
      --panel-2: rgba(20,20,45,.055);
      --solid: #FFFFFF;
      --border: rgba(20,20,45,.10);
      --border-2: rgba(20,20,45,.18);
      --text: #16161C;
      --text-2: #55555F;
      --text-3: #86868F;
      --accent: #4F4FD4;
      --accent-soft: rgba(109,109,246,.10);
      --grid-line: rgba(20,20,60,.045);
      --wire: rgba(90,90,190,.34);
      --glow-a: rgba(109,109,246,.14);
      --glow-b: rgba(34,180,238,.10);
      --shadow: 0 1px 2px rgba(20,20,45,.05), 0 10px 28px rgba(20,20,45,.07);
      --term-br: rgba(255,255,255,.09);
    }
  }

  * { box-sizing: border-box; margin: 0; }
  html, body { height: 100%; }
  body {
    font-family: var(--font-ui); background: var(--bg); color: var(--text);
    line-height: 1.6; -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility;
    font-size: 15px;
  }
  a { color: inherit; text-decoration: none; }
  code, .mono { font-family: var(--font-mono); font-variant-ligatures: none; }
  ::selection { background: rgba(109,109,246,.32); }

  /* ── app shell ───────────────────────────────────────── */
  .shell { display: flex; height: 100vh; overflow: hidden; }
  .side {
    width: 396px; flex: none; height: 100vh; overflow-y: auto; overscroll-behavior: contain;
    border-right: 1px solid var(--border); background: var(--bg-2);
    position: relative; scrollbar-width: thin;
  }
  .side::-webkit-scrollbar { width: 8px; }
  .side::-webkit-scrollbar-thumb { background: var(--border-2); border-radius: 8px; }
  .side::before {
    content: ""; position: absolute; inset: 0 0 auto 0; height: 420px; pointer-events: none;
    background:
      radial-gradient(520px 300px at 15% -8%, var(--glow-a), transparent 70%),
      radial-gradient(420px 260px at 95% 2%, var(--glow-b), transparent 72%);
  }
  .side-in { position: relative; padding: 26px 28px 60px; }

  .brand { display: flex; align-items: center; gap: 10px; font-weight: 750; letter-spacing: -.02em; font-size: 16px; }
  .brand svg { display: block; }
  .badges { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 18px; }
  .badge {
    font-size: 11.5px; font-weight: 600; color: var(--text-2);
    border: 1px solid var(--border); background: var(--panel); border-radius: 999px; padding: 3px 10px;
  }
  .badge.hot { color: #fff; border-color: transparent; background: linear-gradient(115deg, var(--g1), var(--g2)); }

  .side h1 { margin-top: 20px; font-size: 30px; line-height: 1.12; letter-spacing: -.035em; font-weight: 780; }
  .grad {
    background: linear-gradient(102deg, var(--g1) 4%, var(--g2) 52%, var(--g3) 100%);
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }
  .side .sub { margin-top: 14px; color: var(--text-2); font-size: 15px; }
  .runtimes { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 16px; }
  .runtimes span {
    display: inline-flex; align-items: center; gap: 6px; font-size: 12.5px; color: var(--text-2);
    border: 1px solid var(--border); border-radius: 999px; padding: 4px 11px; background: var(--panel);
  }
  .runtimes i { width: 6px; height: 6px; border-radius: 50%; background: linear-gradient(120deg, var(--g1), var(--g3)); }

  .install {
    margin-top: 20px; display: flex; align-items: stretch; overflow: hidden;
    border: 1px solid var(--border-2); border-radius: var(--r-md);
    background: var(--solid); box-shadow: var(--shadow);
  }
  .install .p { display: flex; align-items: center; padding-left: 13px; color: var(--g2); font-family: var(--font-mono); font-size: 13px; }
  .install code {
    flex: 1; min-width: 0; font-size: 11.5px; padding: 12px 10px; color: var(--text);
    overflow-x: auto; white-space: nowrap; scrollbar-width: none;
  }
  .install code::-webkit-scrollbar { display: none; }
  .install button {
    border: 0; border-left: 1px solid var(--border); background: var(--panel);
    color: var(--text-2); font-family: var(--font-ui); font-size: 12px; font-weight: 600;
    padding: 0 14px; cursor: pointer; white-space: nowrap; transition: color .15s, background .15s;
  }
  .install button:hover { color: var(--text); background: var(--panel-2); }
  .fine { margin-top: 10px; font-size: 12px; color: var(--text-3); }
  .fine a { color: var(--text-2); text-decoration: underline; text-underline-offset: 3px; }

  .sblock { margin-top: 34px; }
  .skick {
    font-size: 11px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase;
    color: var(--text-3); margin-bottom: 12px; display: flex; align-items: center; gap: 8px;
  }
  .skick::after { content: ""; flex: 1; height: 1px; background: var(--border); }
  .sblock > p { font-size: 13.5px; color: var(--text-2); }

  .jump { display: flex; flex-direction: column; gap: 2px; }
  .jump a {
    display: flex; align-items: center; gap: 10px; padding: 7px 10px; border-radius: var(--r-sm);
    font-size: 13.5px; color: var(--text-2); transition: background .15s, color .15s;
  }
  .jump a:hover, .jump a.on { background: var(--panel); color: var(--text); }
  .jump .n {
    font-family: var(--font-mono); font-size: 10.5px; color: var(--text-3);
    border: 1px solid var(--border); border-radius: 5px; padding: 1px 5px; flex: none;
  }
  .jump a.on .n { color: var(--accent); border-color: var(--accent); }

  .flag {
    border: 1px solid var(--border); border-radius: var(--r-md); padding: 14px 15px;
    background: linear-gradient(150deg, var(--accent-soft), transparent 62%), var(--panel);
    margin-bottom: 9px;
  }
  .flag h3 { font-size: 14px; letter-spacing: -.01em; display: flex; align-items: center; gap: 8px; }
  .flag h3 .dot { width: 7px; height: 7px; border-radius: 50%; background: linear-gradient(120deg, var(--g1), var(--g3)); flex: none; }
  .flag ul { margin: 9px 0 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 5px; }
  .flag li { font-size: 12.5px; color: var(--text-2); padding-left: 15px; position: relative; }
  .flag li::before {
    content: ""; position: absolute; left: 3px; top: 8px; width: 4px; height: 4px;
    border-radius: 50%; background: var(--accent);
  }
  .flag li b { color: var(--text); font-weight: 620; }

  .profs { display: flex; flex-direction: column; gap: 8px; }
  .prof {
    display: flex; align-items: center; gap: 12px; padding: 12px 14px;
    border: 1px solid var(--border); border-radius: var(--r-md); background: var(--panel);
    cursor: pointer; transition: border-color .15s, background .15s; text-align: left; font: inherit; color: inherit;
  }
  .prof:hover { border-color: var(--border-2); background: var(--panel-2); }
  .prof.on { border-color: var(--accent); background: var(--accent-soft); }
  .prof .cnt { font-size: 20px; font-weight: 750; letter-spacing: -.02em; min-width: 30px; }
  .prof .nm { font-family: var(--font-mono); font-size: 13px; font-weight: 600; }
  .prof .ds { font-size: 12px; color: var(--text-3); }
  .prof .tag {
    margin-left: auto; font-size: 10px; font-weight: 700; letter-spacing: .05em; color: #fff;
    background: linear-gradient(120deg, var(--g1), var(--g2)); border-radius: 999px; padding: 2px 8px;
  }

  ol.steps { list-style: none; padding: 0; counter-reset: s; display: flex; flex-direction: column; gap: 13px; }
  ol.steps li { display: flex; gap: 12px; font-size: 13.5px; color: var(--text-2); }
  ol.steps .n {
    counter-increment: s; flex: none; width: 22px; height: 22px; border-radius: 50%; margin-top: 1px;
    background: var(--panel-2); color: var(--text); font-size: 11.5px; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
  }
  ol.steps .n::before { content: counter(s); }
  ol.steps b { color: var(--text); font-weight: 620; }
  ol.steps code, .flag code {
    font-size: 11.5px; background: var(--panel); border: 1px solid var(--border);
    border-radius: 6px; padding: 1px 6px; color: var(--text);
  }

  .slinks { display: flex; flex-wrap: wrap; gap: 7px; }
  .slinks a {
    font-size: 12.5px; color: var(--text-2); border: 1px solid var(--border);
    border-radius: 999px; padding: 5px 12px; background: var(--panel); transition: all .15s;
  }
  .slinks a:hover { color: var(--text); border-color: var(--border-2); }
  .sfoot { margin-top: 34px; padding-top: 18px; border-top: 1px solid var(--border); font-size: 12px; color: var(--text-3); }

  /* ── stage / canvas ──────────────────────────────────── */
  .stage { flex: 1; min-width: 0; display: flex; flex-direction: column; height: 100vh; position: relative; }
  .bar {
    flex: none; display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
    padding: 12px 22px; border-bottom: 1px solid var(--border); background: var(--bg-2); z-index: 5;
  }
  .bar .ttl { font-size: 13px; font-weight: 650; letter-spacing: -.01em; }
  .bar .ttl span { color: var(--text-3); font-weight: 400; }
  .filters { display: flex; gap: 4px; margin-left: auto; align-items: center; }
  .filters .lab { font-size: 11.5px; color: var(--text-3); margin-right: 4px; }
  .filters button {
    font-family: var(--font-mono); font-size: 11.5px; font-weight: 600; cursor: pointer;
    border: 1px solid var(--border); border-radius: 999px; padding: 4px 11px;
    background: var(--panel); color: var(--text-2); transition: all .15s;
  }
  .filters button:hover { color: var(--text); }
  .filters button.on { color: #fff; border-color: transparent; background: linear-gradient(120deg, var(--g1), var(--g2)); }
  .legend { display: flex; gap: 12px; align-items: center; font-size: 11.5px; color: var(--text-3); }
  .legend i { display: inline-block; width: 9px; height: 9px; border-radius: 3px; margin-right: 5px; vertical-align: -1px; }
  .legend .e { background: linear-gradient(120deg, var(--g1), var(--g2)); }
  .legend .s { background: var(--panel-2); border: 1px solid var(--border-2); }
  .legend .g { background: var(--warn); }

  .canvas {
    flex: 1; overflow: auto; position: relative; padding: 30px 26px 44px;
    background:
      radial-gradient(760px 420px at 22% -6%, var(--glow-a), transparent 68%),
      radial-gradient(620px 380px at 88% 6%, var(--glow-b), transparent 70%),
      linear-gradient(var(--grid-line) 1px, transparent 1px) 0 0 / 100% 34px,
      linear-gradient(90deg, var(--grid-line) 1px, transparent 1px) 0 0 / 34px 100%,
      var(--bg);
  }
  .diagram { position: relative; min-width: 1020px; max-width: 1400px; margin: 0 auto; }
  #wires { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0; overflow: visible; }
  .rows { position: relative; z-index: 1; display: grid; grid-template-columns: 214px minmax(0,1fr) 214px; gap: 18px; align-items: start; }
  .col { display: flex; flex-direction: column; gap: 22px; }
  .col.main { gap: 40px; }

  .node {
    border: 1px solid var(--border); border-radius: var(--r-lg); background: var(--panel);
    backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
    padding: 16px 18px; box-shadow: var(--shadow); position: relative;
  }
  .node.solid { background: linear-gradient(165deg, var(--panel-2), var(--panel)); }
  .node > .head { display: flex; align-items: baseline; gap: 9px; margin-bottom: 13px; flex-wrap: wrap; }
  .node > .head .lv {
    font-family: var(--font-mono); font-size: 10.5px; font-weight: 700; letter-spacing: .06em;
    color: var(--accent); border: 1px solid var(--accent); border-radius: 5px; padding: 1px 6px;
  }
  .node > .head h3 { font-size: 14.5px; letter-spacing: -.015em; font-weight: 700; }
  .node > .head .note { font-size: 12px; color: var(--text-3); margin-left: auto; }
  .node > .head button.note { border: 0; background: none; cursor: pointer; font: inherit; font-size: 12px; color: var(--text-3); }
  .node > .head button.note:hover { color: var(--text-2); }

  .utter { display: flex; align-items: center; gap: 14px; }
  .utter .av {
    width: 30px; height: 30px; border-radius: 50%; flex: none; display: grid; place-items: center;
    border: 1px solid var(--border-2); background: var(--panel-2); font-size: 11px; color: var(--accent);
  }
  .utter .say { font-size: 14.5px; }
  .utter .say em { font-style: normal; color: var(--text-3); }
  .utter .tail { margin-left: auto; font-size: 11px; color: var(--text-3); font-family: var(--font-mono); text-align: right; line-height: 1.5; }

  .chips { display: flex; flex-wrap: wrap; gap: 6px; }
  .chip {
    font-family: var(--font-mono); font-size: 11.5px; color: var(--text-2);
    border: 1px solid var(--border); border-radius: 6px; padding: 4px 9px; background: var(--panel);
    white-space: nowrap; transition: all .14s;
  }
  button.chip { cursor: pointer; font-family: var(--font-mono); }
  button.chip:hover { color: var(--text); border-color: var(--border-2); background: var(--panel-2); transform: translateY(-1px); }
  .chip.entry { color: var(--text); border-color: var(--border-2); background: var(--panel-2); font-weight: 600; }
  .chip.gate { color: var(--warn); border-color: rgba(251,191,36,.34); background: rgba(251,191,36,.07); }
  .chip.dim { opacity: .22; }

  .contract { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  .sub { border: 1px solid var(--border); border-radius: var(--r-md); padding: 12px 13px; background: var(--panel); }
  .sub .t {
    font-size: 10.5px; font-weight: 700; letter-spacing: .09em; text-transform: uppercase;
    color: var(--text-3); margin-bottom: 9px;
  }
  .ladder { display: flex; align-items: center; gap: 3px; flex-wrap: wrap; }
  .ladder .st {
    font-family: var(--font-mono); font-size: 10.5px; padding: 3px 7px; border-radius: 5px; cursor: pointer;
    border: 1px solid var(--border); color: var(--text-3); background: var(--panel);
  }
  .ladder .st.on { color: var(--text); border-color: var(--border-2); background: var(--panel-2); }
  .ladder .st.top { color: var(--danger); border-color: rgba(251,113,133,.36); background: rgba(251,113,133,.08); }
  .seal { font-family: var(--font-mono); font-size: 11px; color: var(--text-2); line-height: 1.85; }
  .seal b { color: var(--accent); font-weight: 600; }
  .seal .k { color: var(--text-3); }

  .tracks { display: flex; flex-direction: column; gap: 8px; }
  .track {
    display: flex; align-items: stretch; border-radius: 9px; overflow: hidden;
    border: 1px solid color-mix(in srgb, var(--tc) 26%, transparent);
    background: color-mix(in srgb, var(--tc) 7%, transparent);
  }
  .track .lab {
    width: 116px; flex: none; display: flex; align-items: center; padding: 9px 12px;
    font-size: 12px; font-weight: 650; color: var(--tc); letter-spacing: -.01em;
    border-right: 1px solid color-mix(in srgb, var(--tc) 22%, transparent);
  }
  .track .flow { flex: 1; min-width: 0; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; padding: 9px 12px; }
  .track .arw { color: var(--text-3); font-size: 11px; }

  /* dispatch fabric */
  .fabric { display: grid; grid-template-columns: 1.15fr 1fr; gap: 16px; }
  .tree { display: flex; flex-direction: column; gap: 9px; }
  .tier { display: flex; align-items: center; gap: 10px; }
  .tier .d {
    font-family: var(--font-mono); font-size: 10px; font-weight: 700; color: var(--text-3);
    border: 1px solid var(--border); border-radius: 5px; padding: 2px 6px; flex: none; letter-spacing: .04em;
  }
  .tier .box {
    flex: 1; min-width: 0; border: 1px solid var(--border); border-radius: 9px; padding: 8px 11px;
    background: var(--panel); font-size: 12.5px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
    cursor: pointer; text-align: left; color: inherit; font-family: inherit; transition: all .14s;
  }
  .tier .box:hover { border-color: var(--border-2); background: var(--panel-2); }
  .tier .box b { font-weight: 650; }
  .tier .box .m { font-family: var(--font-mono); font-size: 10.5px; color: var(--text-3); margin-left: auto; }
  .tier.w2 .box { border-color: var(--border-2); background: var(--panel-2); }
  .nway { padding-left: 34px; }
  .nway .nh { font-size: 10.5px; color: var(--text-3); font-family: var(--font-mono); margin-bottom: 6px; letter-spacing: .04em; }
  .legs { display: flex; gap: 7px; }
  .leg {
    flex: 1; border: 1px dashed var(--border-2); border-radius: 8px; padding: 7px 8px;
    font-family: var(--font-mono); font-size: 10.5px; color: var(--text-2); background: var(--panel);
    text-align: center; cursor: pointer; transition: all .14s;
  }
  .leg:hover { border-style: solid; background: var(--panel-2); color: var(--text); }
  .leg span { display: block; font-size: 9.5px; color: var(--text-3); margin-top: 2px; }
  .fall { display: flex; flex-direction: column; gap: 6px; }
  .fall .hop {
    display: flex; align-items: center; gap: 8px; font-family: var(--font-mono); font-size: 11px;
    color: var(--text-2); border: 1px solid var(--border); border-radius: 7px; padding: 6px 9px;
    background: var(--panel); cursor: pointer; width: 100%; text-align: left; transition: all .14s;
  }
  .fall .hop:hover { border-color: var(--border-2); background: var(--panel-2); }
  .fall .hop .i { width: 5px; height: 5px; border-radius: 50%; background: var(--ok); flex: none; }
  .fall .hop.last .i { background: var(--text-3); }
  .fall .hop .x { margin-left: auto; color: var(--text-3); font-size: 10px; }
  .metrics { display: flex; gap: 8px; margin-top: 13px; flex-wrap: wrap; }
  .metric { border: 1px solid var(--border); border-radius: 9px; padding: 8px 12px; background: var(--panel); flex: 1; min-width: 112px; }
  .metric b { display: block; font-size: 15px; letter-spacing: -.02em; }
  .metric span { font-size: 11px; color: var(--text-3); }

  /* fleet terminal mockup */
  .term {
    border: 1px solid var(--term-br); border-radius: 11px; background: var(--term-bg);
    overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,.4); margin-top: 14px;
  }
  .term .tb {
    display: flex; align-items: center; gap: 7px; padding: 8px 12px;
    border-bottom: 1px solid var(--term-br); background: rgba(255,255,255,.025);
  }
  .term .tb i { width: 8px; height: 8px; border-radius: 50%; background: rgba(255,255,255,.14); }
  .term .tb .nm { font-family: var(--font-mono); font-size: 10.5px; color: #8A8A9A; margin-left: 5px; }
  .term .tb .live { margin-left: auto; font-family: var(--font-mono); font-size: 9.5px; color: var(--ok); display: flex; align-items: center; gap: 5px; }
  .term .tb .live i { width: 5px; height: 5px; background: var(--ok); box-shadow: 0 0 8px var(--ok); }
  .term .body { padding: 10px 13px 12px; font-family: var(--font-mono); font-size: 11px; color: var(--term-tx); line-height: 1.85; }
  .term .r { display: flex; align-items: center; gap: 9px; white-space: nowrap; }
  .term .r .s { width: 9px; flex: none; }
  .term .r .nmx { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; }
  .term .r .tag { color: #6E6E80; }
  .term .r .t { color: #55556A; width: 36px; text-align: right; }
  .term .r.child .nmx { color: #9C9CB0; }
  .term .r.child .nmx::before { content: "↳ "; color: #55556A; }
  .term .w { color: var(--ok); } .term .i2 { color: #6E6E80; }
  .term .b2 { color: var(--warn); } .term .dn { color: var(--info); }
  .term .hd { color: #55556A; border-bottom: 1px dashed rgba(255,255,255,.08); padding-bottom: 4px; margin-bottom: 5px; display: block; }
  .term .ft { color: #55556A; border-top: 1px dashed rgba(255,255,255,.08); padding-top: 5px; margin-top: 5px; display: block; }

  /* model tier matrix */
  .tiers { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .prof-row { display: flex; flex-direction: column; gap: 7px; }
  .pcard {
    display: block; border: 1px solid var(--border); border-radius: 9px;
    padding: 9px 11px; background: var(--panel); cursor: pointer; text-align: left; color: inherit;
    font-family: inherit; transition: all .14s; width: 100%;
  }
  .pcard:hover { border-color: var(--border-2); background: var(--panel-2); }
  .pcard .ptop { display: flex; align-items: center; gap: 8px; }
  .pcard .pn { font-family: var(--font-mono); font-size: 12px; font-weight: 650; }
  .pcard .pd { display: block; font-size: 11px; color: var(--text-3); margin-top: 2px; line-height: 1.45; }
  .pcard .pe {
    margin-left: auto; font-family: var(--font-mono); font-size: 10px; color: var(--text-3);
    border: 1px solid var(--border); border-radius: 5px; padding: 1px 6px; white-space: nowrap;
  }
  .pcard.deep .pn { color: var(--g2); }
  .pcard.bal .pn { color: var(--accent); }
  .pcard.light .pn { color: var(--g3); }
  .pcard.mini .pn { color: var(--text-3); }
  .pcard.mini { opacity: .7; }
  .maptab { width: 100%; border-collapse: collapse; font-size: 11.5px; }
  .maptab th {
    text-align: left; font-size: 10px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase;
    color: var(--text-3); padding: 0 8px 7px 0; border-bottom: 1px solid var(--border);
  }
  .maptab td { padding: 6px 8px 6px 0; border-bottom: 1px solid var(--border); color: var(--text-2); }
  .maptab td:first-child { font-family: var(--font-mono); font-size: 11px; color: var(--text); }
  .maptab td .pp { font-family: var(--font-mono); font-size: 10.5px; color: var(--accent); }
  .maptab tr:last-child td { border-bottom: 0; }

  /* artifact system */
  .flowline { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 13px; }
  .flowline .fx {
    font-family: var(--font-mono); font-size: 11.5px; border: 1px solid var(--border-2); border-radius: 7px;
    padding: 5px 11px; background: var(--panel-2); color: var(--text); cursor: pointer;
  }
  .flowline .fx:hover { border-color: var(--accent); }
  .flowline .fa { color: var(--text-3); font-size: 12px; }
  .flowline .fn { font-size: 11.5px; color: var(--text-3); margin-left: 6px; }
  .buckets { display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; }
  .bucket { border: 1px solid var(--border); border-radius: 9px; padding: 10px 9px; background: var(--panel); text-align: center; }
  .bucket b { display: block; font-family: var(--font-mono); font-size: 11px; color: var(--text); }
  .bucket span { font-size: 10.5px; color: var(--text-3); }
  .bucket .ow { display: block; font-size: 9.5px; color: var(--accent); font-family: var(--font-mono); margin-top: 3px; }
  .bucket.hi { border-color: var(--border-2); background: var(--panel-2); }
  .rules { display: flex; gap: 7px; flex-wrap: wrap; margin-top: 12px; }
  .rule {
    font-size: 11px; color: var(--text-2); border: 1px solid var(--border); border-radius: 7px;
    padding: 5px 10px; background: var(--panel); display: flex; align-items: center; gap: 6px;
  }
  .rule::before { content: "✓"; color: var(--ok); font-size: 10px; }

  /* side rails */
  .rail { border: 1px solid var(--border); border-radius: var(--r-lg); background: var(--panel); padding: 14px 15px; box-shadow: var(--shadow); }
  .rail .rh { display: flex; align-items: baseline; gap: 7px; margin-bottom: 4px; }
  .rail .rh h4 { font-size: 13px; font-weight: 700; letter-spacing: -.01em; }
  .rail .rh .tag { font-family: var(--font-mono); font-size: 9.5px; color: var(--text-3); letter-spacing: .05em; }
  .rail .rd { font-size: 11.5px; color: var(--text-3); margin-bottom: 12px; line-height: 1.5; }
  .rail .items { display: flex; flex-direction: column; gap: 6px; }
  .ritem {
    border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px; background: var(--panel);
    transition: all .14s; cursor: pointer; width: 100%; text-align: left; color: inherit; font-family: inherit;
  }
  .ritem:hover { border-color: var(--border-2); background: var(--panel-2); }
  .ritem .n { font-family: var(--font-mono); font-size: 11px; color: var(--text); display: flex; align-items: center; gap: 6px; }
  .ritem .n .hard {
    font-size: 8.5px; font-weight: 700; letter-spacing: .06em; color: var(--danger);
    border: 1px solid rgba(251,113,133,.4); border-radius: 4px; padding: 0 4px; margin-left: auto;
  }
  .ritem .b { font-size: 10.5px; color: var(--text-3); margin-top: 3px; line-height: 1.45; }
  .rfoot { margin-top: 11px; padding-top: 10px; border-top: 1px solid var(--border); font-size: 11px; color: var(--text-3); }

  .spine { display: flex; flex-direction: column; }
  .step { position: relative; padding-left: 20px; padding-bottom: 13px; }
  .step:last-child { padding-bottom: 0; }
  .step::before {
    content: ""; position: absolute; left: 4px; top: 5px; width: 8px; height: 8px; border-radius: 50%;
    background: var(--bg-2); border: 1.5px solid var(--accent);
  }
  .step:not(:last-child)::after {
    content: ""; position: absolute; left: 7.5px; top: 15px; bottom: 2px; width: 1px;
    background: linear-gradient(180deg, var(--accent), var(--border));
  }
  .step .sn { font-size: 12px; font-weight: 650; color: var(--text); }
  .step .sb { font-size: 10.5px; color: var(--text-3); line-height: 1.5; margin-top: 2px; }
  .step .sb code { font-size: 10px; color: var(--text-2); }

  /* loops strip */
  .loops { position: relative; z-index: 1; margin-top: 28px; }
  .loops-head { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
  .loops-head .ln {
    font-family: var(--font-mono); font-size: 10.5px; font-weight: 700; letter-spacing: .06em;
    color: var(--accent); border: 1px solid var(--accent); border-radius: 5px; padding: 1px 6px;
  }
  .loops-head h3 { font-size: 14px; font-weight: 700; }
  .loops-head .d { font-size: 12px; color: var(--text-3); }
  .loops-head::after { content: ""; flex: 1; height: 1px; background: var(--border); }
  .loop-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 9px; }
  .loop {
    border: 1px dashed var(--border-2); border-radius: var(--r-md); padding: 11px 12px; background: var(--panel);
    transition: all .14s; cursor: pointer; text-align: left; color: inherit; font-family: inherit; width: 100%;
  }
  .loop:hover { border-style: solid; background: var(--panel-2); }
  .loop .n { font-size: 12.5px; font-weight: 650; display: flex; align-items: center; gap: 6px; }
  .loop .n .k { font-family: var(--font-mono); font-size: 9.5px; color: var(--text-3); margin-left: auto; }
  .loop .b { font-size: 10.5px; color: var(--text-3); margin-top: 4px; line-height: 1.45;
    display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }

  /* inspector */
  .inspector {
    position: absolute; right: 22px; bottom: 20px; width: 344px; z-index: 20;
    border: 1px solid var(--border-2); border-radius: var(--r-lg); background: var(--solid);
    box-shadow: 0 8px 40px rgba(0,0,0,.45); padding: 15px 17px;
    opacity: 0; transform: translateY(8px); pointer-events: none; transition: opacity .18s, transform .18s;
  }
  .inspector.on { opacity: 1; transform: none; pointer-events: auto; }
  .inspector .ih { display: flex; align-items: center; gap: 8px; }
  .inspector .ih .k {
    font-size: 9.5px; font-weight: 700; letter-spacing: .07em; text-transform: uppercase;
    color: var(--accent); border: 1px solid var(--accent); border-radius: 4px; padding: 1px 5px; white-space: nowrap;
  }
  .inspector .ih .t { font-family: var(--font-mono); font-size: 13px; font-weight: 650; }
  .inspector .ih button {
    margin-left: auto; border: 0; background: transparent; color: var(--text-3);
    font-size: 15px; cursor: pointer; line-height: 1; padding: 0 2px;
  }
  .inspector .ib { font-size: 12.5px; color: var(--text-2); margin-top: 9px; line-height: 1.55; }
  .inspector .im { font-family: var(--font-mono); font-size: 10.5px; color: var(--text-3); margin-top: 9px; }

  /* ── map page ────────────────────────────────────────── */
  .page, .page .shell { height: auto; overflow: visible; }
  .page .stage { height: auto; }
  .page .canvas { overflow: visible; }
  .mapwrap { position: relative; z-index: 1; max-width: 1180px; margin: 0 auto; }
  .maphead { margin-bottom: 26px; }
  .maphead h1 { font-size: clamp(26px, 3.6vw, 38px); letter-spacing: -.03em; line-height: 1.12; }
  .maphead p { margin-top: 12px; color: var(--text-2); max-width: 620px; font-size: 15px; }
  .stats { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 20px; }
  .stat { border: 1px solid var(--border); border-radius: var(--r-md); background: var(--panel); padding: 10px 16px; min-width: 100px; }
  .stat b { display: block; font-size: 20px; letter-spacing: -.02em; }
  .stat span { font-size: 11.5px; color: var(--text-3); }
  .cap-group { margin-bottom: 30px; }
  .cap-group h3 { font-size: 15px; letter-spacing: -.015em; }
  .cap-group .desc { font-size: 12.5px; color: var(--text-3); margin: 3px 0 13px; }
  .cap-grid { display: grid; gap: 9px; grid-template-columns: repeat(auto-fill, minmax(272px, 1fr)); }
  .cap { border: 1px solid var(--border); border-radius: var(--r-md); background: var(--panel); padding: 13px 15px; transition: all .15s; }
  .cap:hover { border-color: var(--border-2); background: var(--panel-2); }
  .cap.dim { opacity: .26; }
  .cap .name { display: flex; align-items: center; gap: 8px; justify-content: space-between; }
  .cap .name .mono { font-size: 12.5px; font-weight: 650; color: var(--text); }
  .cap .pill {
    flex: none; font-size: 9.5px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase;
    border-radius: 999px; padding: 2px 7px; color: #fff; background: linear-gradient(120deg, var(--g1), var(--g2));
    white-space: nowrap;
  }
  .cap .pill.stage { color: var(--text-3); background: var(--panel-2); border: 1px solid var(--border); }
  .cap p { font-size: 12px; color: var(--text-2); margin-top: 6px;
    display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
  .backhome {
    display: inline-flex; align-items: center; gap: 7px; font-size: 13px; color: var(--text-2);
    border: 1px solid var(--border); border-radius: 999px; padding: 7px 15px; background: var(--panel); margin-bottom: 22px;
  }
  .backhome:hover { color: var(--text); border-color: var(--border-2); }

  /* ── responsive ──────────────────────────────────────── */
  @media (max-width: 1240px) {
    .side { width: 344px; }
    .fabric, .contract, .tiers { grid-template-columns: 1fr; }
    .buckets { grid-template-columns: repeat(3, 1fr); }
    .loop-grid { grid-template-columns: repeat(3, 1fr); }
  }
  @media (max-width: 980px) {
    html, body { height: auto; }
    .shell { flex-direction: column; height: auto; overflow: visible; }
    .side { width: 100%; height: auto; overflow: visible; border-right: 0; border-bottom: 1px solid var(--border); }
    .stage { height: auto; }
    .canvas { overflow-x: auto; padding: 22px 16px 32px; }
    .diagram { min-width: 900px; }
    .inspector { position: fixed; left: 16px; right: 16px; bottom: 16px; width: auto; }
    .side-in { padding: 22px 20px 40px; }
    .side h1 { font-size: 29px; }
  }
"""

LOGO = (
    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
    '<defs><linearGradient id="lg" x1="0" y1="0" x2="24" y2="24">'
    '<stop offset="0" stop-color="#6D6DF6"/><stop offset=".55" stop-color="#A855F7"/>'
    '<stop offset="1" stop-color="#22D3EE"/></linearGradient></defs>'
    '<path d="M12 2 21 7v2L12 14 3 9V7l9-5Z" fill="url(#lg)"/>'
    '<path d="M3 12.5 12 17.5 21 12.5V15L12 20 3 15v-2.5Z" fill="url(#lg)" opacity=".55"/></svg>'
)

COPY_JS = (
    "navigator.clipboard.writeText(document.getElementById('cmd').textContent)"
    ".then(()=>{this.textContent='Copied';setTimeout(()=>this.textContent='Copy',1400)})"
)

TRACK_COLOR = {
    "--cat-1": "#A47AE0", "--cat-2": "#6B96F0", "--cat-3": "#5FC684",
    "--cat-4": "#C07FE0", "--cat-5": "#D9A93C", "--cat-6": "#85AEFF",
    "--cat-7": "#F87171", "--cat-8": "#D1D5DB",
}

ARTIFACT_BUCKETS = [
    ("research/", "external evidence", "autopilot-research", False),
    ("analysis_project/", "source analysis", "analyze-project", False),
    ("spec/", "current blueprint", "autopilot-spec", True),
    ("plans/", "code cycles", "autopilot-code", True),
    ("documents/", "drafts", "draft / refine", False),
    ("experiments/", "runs &amp; logs", "autopilot-lab", False),
]

ARTIFACT_RULES = [
    "one root per project",
    "the owning capability updates it",
    "spec revisions snapshot the prior version",
    "worktree snapshot writes fail closed",
    "no code without a spec",
]

# What each hard guard denies, read from the hook scripts' own header contracts.
GUARD_NOTE = {
    "artifact-guard": "writes outside the canonical artifact root",
    "builtin-memory-guard": "direct writes to built-in file memory",
    "core-first-guard": "adapter edits before the core contract is read",
    "git-state-guard": "edits during a merge, rebase, or cherry-pick",
    "spec-skill-gate": "a spec-changing Skill with no current spec read",
}

MEMORY_STEPS = [
    ("Capsule probe", "Every eligible main prompt runs <code>mem candidates</code> over the "
     "active capsule index — at most 3 headline+ID hits in 1,200 bytes, bodies untouched."),
    ("Opportunity receipt", "The probe writes a same-turn receipt even on zero hits. Material "
     "main-session mutation is gated on it, so retrieval can't be silently skipped."),
    ("Agent-owned recall", "No score threshold adopts a hit. The agent reads the full record by "
     "ID, then cross-checks it against live code."),
    ("Session distillation", "SessionEnd dispatches a no-tools distiller. Automatic writes declare "
     "one purpose: decision, user-correction, unresolved-obligation, or artifact-pointer."),
    ("Supersede, never delete", "Changed decisions are superseded — one active canonical path, "
     "full history auditable, deleted rows recoverable from the graveyard."),
    ("Pending protection", "Handoffs stay <code>pending</code> until an explicit consume; prune, "
     "merge, and delete fail closed against them."),
]

MODEL_PROFILES = [
    ("deep", "deep", "highest-confidence convergence, failure-mode and security judgment", "deep · xhigh"),
    ("balanced-deep", "bal", "deep-model judgment at a lower coordination budget", "deep · medium"),
    ("light", "light", "low-latency production, structured checking, broad exploration", "light · medium"),
    ("mini", "mini", "lifecycle and classification only — refused for substantive nodes", "mini · medium"),
]

STAGE_MODEL_MAP = [
    ("owner (standard+)", "deep orchestrator", "deep"),
    ("frame · plan", "deep maker", "balanced-deep"),
    ("plan (strong+)", "deep maker", "deep"),
    ("execute", "fast implementer", "light"),
    ("impl-review", "fast reviewer", "light"),
    ("failure-mode", "deep reviewer", "deep"),
    ("adversary leg", "external adversary", "deep"),
    ("test · report", "fast reviewer / writer", "light"),
]

FLEET_ROWS = [
    ("w", "●", "agent_setting", "claude · owner d1", "working", "12m", False),
    ("w", "│", "code-execute", "claude · light", "working", "4m", True),
    ("dn", "│", "impl-review", "codex · light", "done", "2m", True),
    ("b2", "│", "failure-mode", "codex · deep", "blocked", "1m", True),
    ("i2", "○", "sr_corrnet_runtime", "interactive", "idle", "38m", False),
]


def _mono(slug: str) -> str:
    return slug.split("__", 1)[-1] if "__" in slug else slug


def build_info(d: dict) -> dict:
    """Inspector payload keyed by node id — capability summaries, guards, loops, concepts."""
    info: dict[str, dict] = {}
    for name, spec in d["caps"].items():
        entry = spec["invocation"]["class"] == "entry-router"
        info[f"cap:{name}"] = {
            "kind": "entry router" if entry else "stage",
            "title": name,
            "body": str(spec.get("summary", "")).strip(),
            "meta": f"group: {spec['group']} · family: {spec['family']}",
        }
    for hook in d["hard_hooks"]:
        info[f"hook:{hook['mono']}"] = {
            "kind": "hard guard",
            "title": hook["mono"],
            "body": f"Denies {GUARD_NOTE.get(hook['mono'], 'the unsafe call')} — on {hook['event']}, "
                    f"before the tool runs rather than in review. The model judges; this code enforces.",
            "meta": hook["event"],
        }
    for loop in d["loops"]:
        info[f"loop:{loop['mono']}"] = {
            "kind": "loop",
            "title": loop["mono"],
            "body": loop["blurb"],
            "meta": loop["schedule"],
        }
    concepts = [
        ("fx:main", "main session", "dispatch depth 0",
         "Context owner, router, and final integrator — not the default executor. It recovers memory and "
         "artifacts, proposes the route card, dispatches, harvests, and integrates.",
         "never runs separable standard+ stages inline"),
        ("fx:owner", "capability owner", "dispatch depth 1",
         "A thin conductor bound to one sealed route. It reads stage verdict metadata rather than stage "
         "bodies and passes context between stages only through files.",
         "quick = exactly one owner, no depth 2"),
        ("fx:stage", "stage workers", "dispatch depth 2",
         "plan · plan-check · execute · impl-review · test · report. Each is a separately launched headless "
         "session with a sealed role, model profile, and disjoint write scope. Only execute mutates source.",
         "depth 3 is forbidden"),
        ("fx:nway", "N-way parallel group", "dispatch",
         "2–4 route-declared siblings started in exactly one dispatch-batch transaction. Width, leg indexes, "
         "disjoint scopes, sealed profiles, and harness evidence are verified before any process starts — a "
         "capacity shortage creates zero rows and zero model processes.",
         "standard 2 · strong 3 · thorough 4"),
        ("fx:family", "cross-family diversity", "dispatch",
         "Legs spread across model families by default: a checker lands on a different family than its maker, "
         "and consecutive nodes don't home to the conductor's own harness. Routing everything to one harness "
         "is the exception that carries a recorded reason.",
         "cross-harness = ≥2 families"),
        ("fx:fallback", "checked fallback chain", "dispatch",
         "same-harness-headless → cross-harness-headless → native-subagent → inline. Every hop keeps the same "
         "route id, write scope, completion gate, and attempt identity; degradation is recorded with its "
         "failure class, never silent.",
         "SD-50"),
        ("fx:registry", "attempt registry", "dispatch",
         "One canonical jobs.log for every runtime. A start writes a registered row first, then atomically "
         "claims its fenced PID/start identity. A duplicate or already-started claim spawns zero children.",
         ".dispatch/jobs.log"),
        ("fx:liveness", "liveness classification", "dispatch",
         "ALIVE · SUSPECT · DEAD · EXITED, derived from exact recorded PID plus start time — never an "
         "indefinite wait and never a path-based guess. Exit 3 means something is unharvested.",
         "utilities/dispatch-liveness.sh"),
        ("fx:fleet", "Fleet", "live view",
         "The cross-harness dashboard over that same registry: interactive sessions and dispatched workers in "
         "one tree, each with state, harness, sealed model profile, context gauge, and token accounting. "
         "Orphaned rows are surfaced rather than dropped.",
         "part of the harness, not a separate product"),
        ("rt:card", "route card", "contract",
         "Before material work the agent proposes task, reason, route, scope, and completion in five fields. "
         "You approve a filled-in proposal instead of recalling capability names or flags.",
         "WORKFLOW §0.4"),
        ("rt:seal", "sealed route", "contract",
         "The compiler binds capability, intensity, topology, node write scopes, and model profiles to the "
         "registry digest, source commit, and physical cwd. A worker cannot renegotiate it, and a caller cannot "
         "swap a sealed profile for a trailing model flag.",
         "route_hash · registry_digest"),
        ("rt:intensity", "intensity ladder", "contract",
         "direct → quick → standard → strong → thorough → adversarial. Intensity selects the stage graph and "
         "dispatch depth; verification rigor is derived from it rather than set on a separate axis. Token "
         "pressure can never downshift it.",
         "CONVENTIONS §1.1"),
        ("rt:gate", "artifact order gates", "contract",
         "No code without a spec; no spec without prior evidence. Writes outside the canonical artifact root, "
         "or a source edit with no route record for this cwd, fail closed before the edit — not in review.",
         "artifact-guard · material-route-guard"),
        ("rt:compose", "compose-on-demand", "contract",
         "Curated recipes are fast paths, not a ceiling. For a request no recipe enumerates, the entry composes "
         "a node graph from the same unit catalog; the composed route passes the same validator, is hash-sealed "
         "exactly like a recipe, and still requires the route card.",
         "composed: true"),
        ("md:role", "portable model roles", "model tiers",
         "Shared contracts name behavior, never a vendor model. Every unit in the catalog binds exactly one "
         "role and a route node's role must equal its unit's declared role; the shared vocabulary also covers "
         "conductor and adversarial nodes as deep orchestrator and external adversary.",
         f"{d['role_total']} roles · {d['unit_total']} units"),
        ("md:profile", "execution profiles", "model tiers",
         "Role and budget are separate axes. deep, balanced-deep, light, and mini are distinct operating points; "
         "adapters map them to concrete models, and an adapter without a verified effort axis must report "
         "reduced granularity instead of claiming parity.",
         "CONVENTIONS §2.2"),
        ("md:map", "per-node selection", "model tiers",
         "Node meaning and risk select the profile — not dispatch depth or role wording. Route compilation seals "
         "owner_model_profile and every node and parallel-leg profile; capacity failover may substitute a checked "
         "model while preserving and reporting the profile intent.",
         "sealed at compile time"),
        ("ev:root", "one artifact root", "artifacts",
         "Every capability writes to one project-wide root, resolved from the primary checkout. Linked task "
         "worktrees are source-only: writes to their artifact snapshot fail closed, so evidence never forks.",
         ".agent_reports/"),
        ("ev:order", "fixed artifact order", "artifacts",
         "research / analyze-project → spec → plans for code, and research → draft → refine for documents. "
         "The folder set is fixed, each artifact has exactly one owning capability, and spec revisions snapshot "
         "the prior version instead of overwriting it.",
         "WORKFLOW §0.1 · §6"),
        ("lp:self", "loops that report, never apply", "self-improvement",
         "Drill replays behavioral fixtures and scores them after instruction changes. On-call corroborates "
         "memory-backed incidents against live evidence before filing a proposal. Runtime-watch fingerprints "
         "the vendors' own docs and probes local CLIs. Every one of them proposes; none edits policy.",
         f"{d['loop_total']} loops"),
    ]
    for key, title, kind, body, meta in concepts:
        info[key] = {"kind": kind, "title": title, "body": body, "meta": meta}
    return info


# ------------------------------------------------------------------ canvas

def build_canvas(d: dict) -> str:
    caps = d["caps"]

    def cap_chip(name: str) -> str:
        spec = caps.get(name)
        if spec is None:
            return ""
        entry = spec["invocation"]["class"] == "entry-router"
        cls = "chip" + (" entry" if entry else "")
        return (f'<button class="{cls}" '
                f'data-info="cap:{name}">{html.escape(name)}</button>')

    tracks_html = []
    for track in d["tracks"]:
        color = TRACK_COLOR.get(track["color_token"], "#8B8BFA")
        flow = []
        for i, slug in enumerate(track["steps"]):
            if i:
                flow.append('<span class="arw">&rarr;</span>')
            flow.append(cap_chip(_mono(slug)))
        for gate in track.get("gates", []):
            flow.append(f'<span class="chip gate">&#9679; {html.escape(gate)}</span>')
        tracks_html.append(
            f'<div class="track" style="--tc:{color}">'
            f'<div class="lab">{html.escape(track["label"])}</div>'
            f'<div class="flow">{"".join(flow)}</div></div>'
        )

    guards = "".join(
        f'<button class="ritem" data-info="hook:{h["mono"]}">'
        f'<div class="n">{html.escape(h["mono"])}<span class="hard">HARD</span></div>'
        f'<div class="b">{GUARD_NOTE.get(h["mono"], html.escape(h["event"]))}</div></button>'
        for h in d["hard_hooks"]
    )

    memory = "".join(
        f'<div class="step"><div class="sn">{title}</div><div class="sb">{body}</div></div>'
        for title, body in MEMORY_STEPS
    )

    buckets = "".join(
        f'<div class="bucket{" hi" if hi else ""}"><b>{name}</b><span>{desc}</span>'
        f'<span class="ow">{owner}</span></div>'
        for name, desc, owner, hi in ARTIFACT_BUCKETS
    )

    rules = "".join(f'<span class="rule">{r}</span>' for r in ARTIFACT_RULES)

    loops = "".join(
        f'<button class="loop" data-info="loop:{l["mono"]}">'
        f'<div class="n">{html.escape(l["name"])}<span class="k">{l["type"]}</span></div>'
        f'<div class="b">{html.escape(l["blurb"])}</div></button>'
        for l in d["loops"]
    )

    stage_chips = "".join(
        f'<span class="chip">{s}</span>' for s in
        ("code-plan", "plan-check", "code-execute", "impl-review", "code-test", "code-report")
    )

    profile_cards = "".join(
        f'<button class="pcard {css}" data-info="md:profile">'
        f'<span class="ptop"><span class="pn">{name}</span><span class="pe">{effort}</span></span>'
        f'<span class="pd">{desc}</span></button>'
        for name, css, desc, effort in MODEL_PROFILES
    )

    stage_rows = "".join(
        f'<tr><td>{stage}</td><td>{role}</td><td><span class="pp">{profile}</span></td></tr>'
        for stage, role, profile in STAGE_MODEL_MAP
    )

    role_chips = "".join(
        f'<button class="chip" data-info="md:role">{html.escape(r)}</button>' for r in d["roles"]
    )

    fleet_rows = "".join(
        f'<div class="r{" child" if child else ""}"><span class="s {cls}">{dot}</span>'
        f'<span class="nmx">{name}</span><span class="tag">{tag}</span>'
        f'<span class="{cls}">{state}</span><span class="t">{age}</span></div>'
        for cls, dot, name, tag, state, age, child in FLEET_ROWS
    )

    return f"""
    <div class="diagram" id="diagram">
      <svg id="wires" aria-hidden="true">
        <defs>
          <linearGradient id="wg" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="1200">
            <stop offset="0" stop-color="#6D6DF6" stop-opacity=".95"/>
            <stop offset="1" stop-color="#22D3EE" stop-opacity=".8"/>
          </linearGradient>
          <marker id="arrow" viewBox="0 0 8 8" refX="6.4" refY="4"
                  markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M0 1 L7 4 L0 7 z" fill="#22D3EE" fill-opacity=".85"/>
          </marker>
        </defs>
      </svg>

      <div class="rows">
        <div class="col">
          <div class="rail" id="n-mem">
            <div class="rh"><h4>Memory</h4><span class="tag">SQLITE · FTS5</span></div>
            <div class="rd">Runs alongside every layer to the right. One store across every
            session, project, and runtime — the agent decides what matters, the code owns
            the mechanics.</div>
            <div class="spine">{memory}</div>
            <div class="rfoot">Workers are exempt: no probe, no inject, no distill, no sync.</div>
          </div>
        </div>

        <div class="col main">
          <div class="node solid" id="n-utter">
            <div class="utter">
              <div class="av">&#9679;</div>
              <div class="say">&ldquo;Implement and test the login API, <em>then leave a change report.&rdquo;</em></div>
              <div class="tail">L0<br />one sentence in</div>
            </div>
          </div>

          <div class="node" id="n-route">
            <div class="head"><span class="lv">L1</span><h3>Routing contract</h3>
              <span class="note">core/ decides the route before a file is touched</span></div>
            <div class="contract">
              <div class="sub"><div class="t">Route handshake</div>
                <div class="chips">
                  <button class="chip entry" data-info="rt:card">route card</button>
                  <button class="chip" data-info="rt:gate">spec gate</button>
                  <button class="chip" data-info="rt:gate">artifact order</button>
                  <button class="chip entry" data-info="rt:seal">sealed route</button>
                  <button class="chip" data-info="rt:compose">compose-on-demand</button>
                </div>
                <div class="seal" style="margin-top:11px">
                  <span class="k">route_hash</span> <b>rt-35552ff2&hellip;</b><br />
                  <span class="k">write_scope</span> source-scoped, plans/&lt;cycle&gt;/**<br />
                  <span class="k">bound to</span> registry digest &middot; commit &middot; cwd
                </div>
              </div>
              <div class="sub"><div class="t">Intensity ladder</div>
                <div class="ladder">
                  <button class="st on" data-info="rt:intensity">direct</button>
                  <button class="st on" data-info="rt:intensity">quick</button>
                  <button class="st on" data-info="rt:intensity">standard</button>
                  <button class="st on" data-info="rt:intensity">strong</button>
                  <button class="st on" data-info="rt:intensity">thorough</button>
                  <button class="st top" data-info="rt:intensity">adversarial</button>
                </div>
                <div class="t" style="margin-top:14px">Governance</div>
                <div class="chips">
                  <span class="chip">CORE</span><span class="chip">WORKFLOW</span>
                  <span class="chip">CONVENTIONS</span><span class="chip">OPERATIONS</span>
                  <span class="chip">MEMORY</span><span class="chip">DESIGN_PRINCIPLES</span>
                </div>
              </div>
            </div>
          </div>

          <div class="node" id="n-tracks">
            <div class="head"><span class="lv">L2</span><h3>Pipelines</h3>
              <span class="note">{d['entry_total']} entry routers &middot; {d['cap_total']} capabilities</span></div>
            <div class="tracks">{"".join(tracks_html)}</div>
          </div>

          <div class="node solid" id="n-fabric">
            <div class="head"><span class="lv">L3</span><h3>Dispatch fabric</h3>
              <span class="note">the owner conducts &middot; workers never route</span></div>
            <div class="fabric">
              <div class="tree">
                <div class="tier"><span class="d">d0</span>
                  <button class="box" data-info="fx:main"><b>main session</b> router &middot; integrator
                    <span class="m">context owner</span></button></div>
                <div class="tier w2"><span class="d">d1</span>
                  <button class="box" data-info="fx:owner"><b>capability owner</b> sealed route, thin conductor
                    <span class="m">deep orchestrator</span></button></div>
                <div class="tier"><span class="d">d2</span>
                  <button class="box" data-info="fx:stage"><b>stage workers</b> file-only handoff
                    <span class="m">3-line verdict</span></button></div>
                <div class="chips" style="padding-left:34px">{stage_chips}</div>
                <div class="nway">
                  <div class="nh">N-way group &middot; one transaction &middot; 2&ndash;4 legs</div>
                  <div class="legs">
                    <button class="leg" data-info="fx:nway">maker<span>family A</span></button>
                    <button class="leg" data-info="fx:family">checker<span>family B</span></button>
                    <button class="leg" data-info="fx:family">adversary<span>family C</span></button>
                  </div>
                </div>
              </div>
              <div>
                <div class="sub" style="margin-bottom:12px"><div class="t">Checked fallback</div>
                  <div class="fall">
                    <button class="hop" data-info="fx:fallback"><i class="i"></i>same-harness headless<span class="x">1</span></button>
                    <button class="hop" data-info="fx:fallback"><i class="i"></i>cross-harness headless<span class="x">2</span></button>
                    <button class="hop" data-info="fx:fallback"><i class="i"></i>native subagent<span class="x">3</span></button>
                    <button class="hop last" data-info="fx:fallback"><i class="i"></i>inline, reason recorded<span class="x">4</span></button>
                  </div>
                </div>
                <div class="sub"><div class="t">Accounting</div>
                  <div class="chips">
                    <button class="chip" data-info="fx:registry">jobs.log</button>
                    <button class="chip" data-info="fx:liveness">liveness</button>
                    <button class="chip entry" data-info="fx:fleet">Fleet</button>
                  </div>
                </div>
              </div>
            </div>

            <div class="term" id="n-fleet">
              <div class="tb"><i></i><i></i><i></i><span class="nm">fleet &mdash; live cross-harness view</span>
                <span class="live"><i></i>LIVE</span></div>
              <div class="body">
                <span class="hd">session / node&nbsp;&nbsp;&middot;&nbsp;&nbsp;harness &middot; profile&nbsp;&nbsp;&middot;&nbsp;&nbsp;state</span>
                {fleet_rows}
                <span class="ft">orphan rows surfaced &middot; context gauge &middot; token accounting per session</span>
              </div>
            </div>
          </div>

          <div class="node" id="n-tiers">
            <div class="head"><span class="lv">L4</span><h3>Model tier per role</h3>
              <button class="note" data-info="md:map">role and budget are separate axes &mdash; both sealed</button></div>
            <div class="tiers">
              <div>
                <div class="sub" style="margin-bottom:12px"><div class="t">Execution profiles</div>
                  <div class="prof-row">{profile_cards}</div>
                </div>
                <div class="sub"><div class="t">Roles in the unit catalog &mdash; {d['role_total']}</div>
                  <div class="chips">{role_chips}</div>
                </div>
              </div>
              <div class="sub">
                <div class="t">Selection, per node</div>
                <table class="maptab">
                  <tr><th>node</th><th>role</th><th>profile</th></tr>
                  {stage_rows}
                </table>
              </div>
            </div>
          </div>

          <div class="node" id="n-art">
            <div class="head"><span class="lv">L5</span><h3>Fixed artifact system</h3>
              <button class="note" data-info="ev:root">.agent_reports/ &mdash; one root per project</button></div>
            <div class="flowline">
              <button class="fx" data-info="ev:order">research</button><span class="fa">&rarr;</span>
              <button class="fx" data-info="ev:order">spec</button><span class="fa">&rarr;</span>
              <button class="fx" data-info="ev:order">plans</button>
              <span class="fn">one direction &mdash; a later stage never invents its own evidence</span>
            </div>
            <div class="buckets">{buckets}</div>
            <div class="rules">{rules}</div>
          </div>
        </div>

        <div class="col">
          <div class="rail" id="n-guards">
            <div class="rh"><h4>Guards</h4><span class="tag">FAIL-CLOSED</span></div>
            <div class="rd">Wrap every layer to the left. Deterministic hooks run before the
            tool call — the model judges, the code enforces.</div>
            <div class="items">{guards}</div>
            <div class="rfoot">{d['hard_total']} hard blocks of {d['hook_total']} hooks &middot;
            write scope, spec read, artifact root, git state, memory path</div>
          </div>
        </div>
      </div>

      <div class="loops" id="n-loops">
        <div class="loops-head"><span class="ln">L6</span><h3>The harness watches itself</h3>
          <button class="d" data-info="lp:self" style="border:0;background:none;cursor:pointer;font:inherit;font-size:12px;color:var(--text-3)">{d['loop_total']} loops that test, corroborate, and propose &mdash; none of them edits policy</button></div>
        <div class="loop-grid">{loops}</div>
      </div>
    </div>"""


CANVAS_JS = r"""
(function () {
  "use strict";
  var INFO = JSON.parse(document.getElementById("info-data").textContent);

  /* ── wires: measured from real element boxes, so any reflow stays correct ── */
  var EDGES = [
    ["n-utter", "n-route"],
    ["n-route", "n-tracks"],
    ["n-tracks", "n-fabric"],
    ["n-fabric", "n-tiers"],
    ["n-tiers", "n-art"]
  ];
  // The rails flank every layer, so a literal edge to one of them would misread as
  // "only this layer". Their relationship is carried by position and copy instead.
  var SIDE = [];

  function draw() {
    var svg = document.getElementById("wires");
    var host = document.getElementById("diagram");
    if (!svg || !host) return;
    while (svg.lastChild && svg.lastChild.nodeName !== "defs") svg.removeChild(svg.lastChild);
    var base = host.getBoundingClientRect();
    var ns = "http://www.w3.org/2000/svg";
    // userSpaceOnUse: a bounding-box gradient collapses on a zero-width vertical path.
    var grad = document.getElementById("wg");
    if (grad) grad.setAttribute("y2", String(Math.max(400, host.scrollHeight)));

    function box(id) {
      var el = document.getElementById(id);
      if (!el) return null;
      var r = el.getBoundingClientRect();
      return { l: r.left - base.left, t: r.top - base.top, w: r.width, h: r.height };
    }
    function path(dAttr, dashed) {
      if (!dashed) {
        // Soft halo behind the wire. An SVG filter can't do this here: a zero-width
        // vertical path gives an objectBoundingBox filter a zero-sized region.
        var halo = document.createElementNS(ns, "path");
        halo.setAttribute("d", dAttr);
        halo.setAttribute("fill", "none");
        halo.setAttribute("stroke", "#6D6DF6");
        halo.setAttribute("stroke-width", "7");
        halo.setAttribute("stroke-linecap", "round");
        halo.setAttribute("opacity", ".16");
        svg.appendChild(halo);
      }
      var p = document.createElementNS(ns, "path");
      p.setAttribute("d", dAttr);
      p.setAttribute("fill", "none");
      p.setAttribute("stroke", dashed ? "var(--wire)" : "url(#wg)");
      p.setAttribute("stroke-width", dashed ? "1.1" : "2");
      p.setAttribute("stroke-linecap", "round");
      if (dashed) { p.setAttribute("stroke-dasharray", "3 5"); p.setAttribute("opacity", ".7"); }
      else { p.setAttribute("marker-end", "url(#arrow)"); }
      svg.appendChild(p);
    }
    function dot(x, y) {
      var c = document.createElementNS(ns, "circle");
      c.setAttribute("cx", x); c.setAttribute("cy", y); c.setAttribute("r", "3");
      c.setAttribute("fill", "var(--wire)");
      svg.appendChild(c);
    }

    EDGES.forEach(function (e) {
      var a = box(e[0]), b = box(e[1]);
      if (!a || !b) return;
      var x = a.l + a.w / 2, y1 = a.t + a.h + 3, y2 = b.t - 3;
      var mid = (y1 + y2) / 2;
      path("M" + x + " " + y1 + " C " + x + " " + mid + ", " + x + " " + mid + ", " + x + " " + y2, false);
      dot(x, y1);
    });

    SIDE.forEach(function (e) {
      var a = box(e[0]), b = box(e[1]);
      if (!a || !b) return;
      var fromRight = e[2] === "right";
      var x1 = fromRight ? a.l + a.w : a.l;
      var x2 = fromRight ? b.l : b.l + b.w;
      var y1 = a.t + Math.min(a.h * 0.4, 150);
      var y2 = b.t + Math.min(b.h / 2, 90);
      var cx = (x1 + x2) / 2;
      path("M" + x1 + " " + y1 + " C " + cx + " " + y1 + ", " + cx + " " + y2 + ", " + x2 + " " + y2, true);
    });
  }

  /* ── inspector ── */
  var panel = document.getElementById("inspector");
  function show(key) {
    var item = INFO[key];
    if (!item || !panel) return;
    panel.querySelector(".k").textContent = item.kind;
    panel.querySelector(".t").textContent = item.title;
    panel.querySelector(".ib").textContent = item.body;
    panel.querySelector(".im").textContent = item.meta || "";
    panel.classList.add("on");
  }
  document.addEventListener("click", function (ev) {
    var host = ev.target.closest ? ev.target.closest("[data-info]") : null;
    if (host) { show(host.getAttribute("data-info")); return; }
    if (panel && !(ev.target.closest && ev.target.closest(".inspector"))) panel.classList.remove("on");
  });
  var close = document.getElementById("insp-close");
  if (close) close.addEventListener("click", function () { panel.classList.remove("on"); });

  /* ── jump list follows the canvas ── */
  var canvas = document.querySelector(".canvas");
  var links = Array.prototype.slice.call(document.querySelectorAll(".jump a[data-target]"));
  links.forEach(function (a) {
    a.addEventListener("click", function (ev) {
      ev.preventDefault();
      var el = document.getElementById(a.dataset.target);
      if (!el) return;
      // Desktop: the canvas is the scroller. Stacked mobile: the page is.
      if (canvas && canvas.scrollHeight > canvas.clientHeight + 4) {
        canvas.scrollTo({ top: el.offsetTop - 34, behavior: "smooth" });
      } else {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });
  if (canvas && links.length) {
    canvas.addEventListener("scroll", function () {
      var y = canvas.scrollTop + 110, cur = links[0];
      links.forEach(function (a) {
        var el = document.getElementById(a.dataset.target);
        if (el && el.offsetTop <= y) cur = a;
      });
      links.forEach(function (a) { a.classList.toggle("on", a === cur); });
    }, { passive: true });
  }

  draw();
  window.addEventListener("resize", draw);
  if (window.ResizeObserver) {
    var host = document.getElementById("diagram");
    if (host) new ResizeObserver(function () { draw(); }).observe(host);
  }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(draw);
})();
"""


def render_index(d: dict) -> str:
    info_json = json.dumps(build_info(d), ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Agent Harness — one agent workflow, three harnesses</title>
<meta name="description" content="A portable, deterministic operating layer for Claude Code, Codex, and OpenCode: routed capabilities, sealed N-way cross-harness dispatch, a live Fleet view, per-role model tiers, a fixed artifact system, and one persistent memory store." />
<!-- GENERATED by tools/render-landing.py — DO NOT EDIT BY HAND. -->
<style>{CSS}</style>
</head>
<body>
<div class="shell">

  <aside class="side"><div class="side-in">
    <a class="brand" href="index.html">{LOGO}<span>Agent&nbsp;Harness</span></a>
    <div class="badges">
      <span class="badge hot">v2.0</span>
      <span class="badge">MIT</span>
      <span class="badge">{d['cap_total']} capabilities</span>
      <span class="badge">{d['unit_total']} role units</span>
      <span class="badge">{d['hook_total']} hooks</span>
    </div>

    <h1>One agent workflow.<br /><span class="grad">Three harnesses.</span></h1>
    <p class="sub">A portable, deterministic operating layer for coding agents. Describe the
    outcome once — routing, cross-harness dispatch, model selection, verification, and evidence
    are the harness's job, not yours.</p>
    <div class="runtimes">
      <span><i></i>Claude Code</span><span><i></i>Codex CLI</span><span><i></i>OpenCode</span>
    </div>

    <div class="install" id="install">
      <span class="p">$</span>
      <code id="cmd">{INSTALL_CMD}</code>
      <button onclick="{html.escape(COPY_JS, quote=True)}">Copy</button>
    </div>
    <p class="fine">SHA-256 checksummed release &middot;
      <a href="{REPO_URL}/releases">release notes</a></p>

    <div class="sblock">
      <div class="skick">The map</div>
      <div class="jump">
        <a href="#n-utter" data-target="n-utter" class="on"><span class="n">L0</span>One sentence in</a>
        <a href="#n-route" data-target="n-route"><span class="n">L1</span>Routing contract</a>
        <a href="#n-tracks" data-target="n-tracks"><span class="n">L2</span>Pipelines</a>
        <a href="#n-fabric" data-target="n-fabric"><span class="n">L3</span>Dispatch fabric &amp; Fleet</a>
        <a href="#n-tiers" data-target="n-tiers"><span class="n">L4</span>Model tier per role</a>
        <a href="#n-art" data-target="n-art"><span class="n">L5</span>Fixed artifact system</a>
        <a href="#n-loops" data-target="n-loops"><span class="n">L6</span>Self-watching loops</a>
      </div>
    </div>

    <div class="sblock">
      <div class="skick">What makes it different</div>

      <div class="flag">
        <h3><span class="dot"></span>Sealed N-way dispatch</h3>
        <ul>
          <li><b>Bounded depth</b> — d0 main, d1 owner, d2 stages. Depth 3 is forbidden and
          workers never route.</li>
          <li><b>N-way groups</b> — 2–4 declared legs start in one transaction. A capacity
          shortage creates zero rows, not a half-started group.</li>
          <li><b>Different families by default</b> — a checker lands on a different model family
          than its maker; one-harness routing is the exception with a recorded reason.</li>
          <li><b>Recorded degradation</b> — same-harness → cross-harness → native → inline, each
          hop keeping the same route id, scope, and attempt identity.</li>
        </ul>
      </div>

      <div class="flag">
        <h3><span class="dot"></span>Fleet, over the same registry</h3>
        <ul>
          <li><b>One attempt registry</b> — a start writes its row before it claims a fenced PID,
          so a duplicate claim spawns zero children.</li>
          <li><b>PID-exact liveness</b> — ALIVE · SUSPECT · DEAD · EXITED instead of waiting on a
          notification that may never arrive.</li>
          <li><b>Nothing is dropped</b> — orphaned rows are surfaced, not hidden, next to context
          gauge and per-session token accounting.</li>
        </ul>
      </div>

      <div class="flag">
        <h3><span class="dot"></span>Model tier chosen per role</h3>
        <ul>
          <li><b>Two axes, never merged</b> — {d['role_total']} portable roles say what a node does;
          <code>deep</code> / <code>balanced-deep</code> / <code>light</code> / <code>mini</code>
          say what it may spend.</li>
          <li><b>Sealed at compile time</b> — a caller can't swap a sealed profile for a trailing
          model flag, and <code>mini</code> is refused for substantive nodes.</li>
          <li><b>Intent survives failover</b> — a capacity substitute preserves and reports the
          profile it stood in for.</li>
        </ul>
      </div>

      <div class="flag">
        <h3><span class="dot"></span>A fixed artifact system</h3>
        <ul>
          <li><b>One root per project</b> — <code>.agent_reports/</code>, resolved from the primary
          checkout; worktree snapshot writes fail closed.</li>
          <li><b>Fixed order</b> — research → spec → plans. No code without a spec, no spec without
          prior evidence.</li>
          <li><b>One owner per artifact</b> — and spec revisions snapshot the prior version instead
          of overwriting it.</li>
        </ul>
      </div>

      <div class="flag">
        <h3><span class="dot"></span>Memory that survives the session</h3>
        <ul>
          <li><b>Recall can't be skipped</b> — each prompt runs a bounded capsule probe and writes a
          receipt that material work is gated on.</li>
          <li><b>No classifier decides for you</b> — code owns scope fences and limits; the agent
          reads the full record and judges relevance.</li>
          <li><b>Sessions distill themselves</b> — a no-tools distiller writes purpose-labelled
          records at session end. No manual “remember this”.</li>
          <li><b>History is never lost</b> — supersede over delete, a graveyard for restores, and
          pending handoffs that fail closed until consumed.</li>
        </ul>
      </div>

      <div class="flag">
        <h3><span class="dot"></span>Guards instead of good intentions</h3>
        <ul>
          <li><b>{d['hard_total']} hard blocks</b> of {d['hook_total']} hooks — write scope, spec read,
          artifact root, git state, and memory path are denied before the tool call, not flagged after.</li>
          <li><b>Route participation is required</b> — a source edit with no compiled route for this
          working directory is refused, hotfix included.</li>
          <li><b>Behavior is regression-tested</b> — the drill loop replays fixtures and scores them
          after instruction changes, then drafts a diagnosis without applying it.</li>
        </ul>
      </div>
    </div>

    <div class="sblock">
      <div class="skick">Quickstart</div>
      <ol class="steps">
        <li><span class="n"></span><div><b>Install the verified release.</b> One line, SHA-256
          checksummed, no clone — and <code>verify</code> / <code>update</code> /
          <code>uninstall</code> stay reversible.</div></li>
        <li><span class="n"></span><div><b>Activate per runtime.</b>
          <code>harness install claude</code>, repeat for
          <code>codex</code> / <code>opencode</code>, then <code>harness verify</code>.</div></li>
        <li><span class="n"></span><div><b>Describe the outcome.</b> The harness proposes the route
          card and closes the loop with durable evidence.</div></li>
      </ol>
    </div>

    <div class="sblock">
      <div class="skick">Go deeper</div>
      <div class="slinks">
        <a href="map.html">Capability catalog</a>
        <a href="{REPO_URL}">GitHub</a>
        <a href="{REPO_URL}/releases">Releases</a>
        <a href="{REPO_URL}/blob/main/MANUAL.md">Manual</a>
      </div>
    </div>

    <div class="sfoot">Agent Harness — a portable operating layer for coding agents. MIT licensed.</div>
  </div></aside>

  <main class="stage">
    <div class="bar">
      <div class="ttl">Agent map <span>&mdash; the whole harness, one canvas</span></div>
      <div class="legend">
        <span><i class="e"></i>entry router</span>
        <span><i class="s"></i>stage</span>
        <span><i class="g"></i>gate</span>
      </div>
    </div>

    <div class="canvas">{build_canvas(d)}</div>

    <div class="inspector" id="inspector">
      <div class="ih"><span class="k"></span><span class="t"></span>
        <button id="insp-close" aria-label="close">&times;</button></div>
      <div class="ib"></div>
      <div class="im"></div>
    </div>
  </main>

</div>
<script type="application/json" id="info-data">{info_json}</script>
<script>{CANVAS_JS}</script>
</body>
</html>
"""


# ------------------------------------------------------------------- map page

MAP_GROUP_ORDER = [
    ("research", "Research first", "Ground new intent in evidence before building.",
     ["autopilot-research", "analyze-project"]),
    ("code", "Code &amp; experiments", "Spec-governed implementation and rapid experiment loops.",
     ["autopilot-spec", "autopilot-code", "autopilot-lab", "autopilot-ship",
      "code-plan", "code-execute", "code-refine", "code-test", "code-report"]),
    ("docs", "Documents", "Papers, reports, proposals — drafted, refined, applied.",
     ["autopilot-draft", "autopilot-refine", "autopilot-apply",
      "draft-strategy", "draft-refine"]),
    ("design", "Design", "Reference-grounded visual design with token contracts.",
     ["autopilot-design", "design-init", "design-refs", "design-tokens",
      "design-components", "design-review", "design-handoff"]),
    ("ops", "Cross-project &amp; operations", "Continuity, inspection, and the user profile.",
     ["analyze-user", "audit", "post-it"]),
]

def render_map(d: dict) -> str:
    caps = d["caps"]
    listed: set[str] = set()
    groups_html = []
    for _key, title, desc, names in MAP_GROUP_ORDER:
        cards = []
        for name in names:
            spec = caps.get(name)
            if spec is None:
                continue
            listed.add(name)
            entry = spec["invocation"]["class"] == "entry-router"
            pill = "entry" if entry else "stage"
            pill_class = "" if entry else " stage"
            summary = html.escape(str(spec.get("summary", "")).strip())
            cards.append(
                f'<div class="cap">'
                f'<div class="name"><span class="mono">{name}</span>'
                f'<span class="pill{pill_class}">{pill}</span></div>'
                f"<p>{summary}</p></div>"
            )
        groups_html.append(
            f'<div class="cap-group"><h3>{title}</h3>'
            f'<div class="desc">{desc}</div>'
            f'<div class="cap-grid">{"".join(cards)}</div></div>'
        )
    orphans = sorted(set(caps) - listed)
    if orphans:
        cards = "".join(
            f'<div class="cap">'
            f'<div class="name"><span class="mono">{n}</span></div>'
            f'<p>{html.escape(str(caps[n].get("summary", "")).strip())}</p></div>'
            for n in orphans
        )
        groups_html.append(
            f'<div class="cap-group"><h3>Other</h3><div class="cap-grid">{cards}</div></div>'
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Capability catalog — Agent Harness</title>
<meta name="description" content="Every Agent Harness capability and pipeline stage." />
<!-- GENERATED by tools/render-landing.py — DO NOT EDIT BY HAND. -->
<style>{CSS}</style>
</head>
<body class="page">
<div class="shell">
  <main class="stage">
    <div class="bar">
      <a class="ttl" href="index.html" style="display:flex;align-items:center;gap:9px">{LOGO}
        <span style="color:var(--text);font-weight:650">Agent Harness</span></a>
    </div>

    <div class="canvas">
      <div class="mapwrap">
        <a class="backhome" href="index.html">&larr; Back to the map</a>
        <div class="maphead">
          <h1>Every capability, <span class="grad">one catalog.</span></h1>
          <p>One portable catalog projected into three runtimes. Entry routers own whole
          pipelines; stages are the sealed workers they dispatch.</p>
          <div class="stats">
            <div class="stat"><b>{d['cap_total']}</b><span>capabilities</span></div>
            <div class="stat"><b>{d['entry_total']}</b><span>entry routers</span></div>
            <div class="stat"><b>{d['unit_total']}</b><span>role units</span></div>
            <div class="stat"><b>{d['role_total']}</b><span>model roles</span></div>
            <div class="stat"><b>3</b><span>runtimes</span></div>
          </div>
        </div>
        {"".join(groups_html)}
      </div>
    </div>
  </main>
</div>
</body>
</html>
"""


def main() -> int:
    check = "--check" in sys.argv[1:]
    data = load_data()
    outputs = {
        DOCS / "index.html": render_index(data),
        DOCS / "map.html": render_map(data),
    }
    if check:
        stale = [
            str(path.relative_to(ROOT))
            for path, want in outputs.items()
            if not path.is_file() or path.read_text(encoding="utf-8") != want
        ]
        if (DOCS / "hub.html").exists():
            stale.append("docs/hub.html (internal hub must not be published)")
        if stale:
            print("stale: " + ", ".join(stale))
            return 1
        print("docs/ landing up-to-date")
        return 0
    DOCS.mkdir(exist_ok=True)
    for path, want in outputs.items():
        path.write_text(want, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    legacy = DOCS / "hub.html"
    if legacy.exists():
        legacy.unlink()
        print("removed docs/hub.html (internal operator hub stays local-only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
