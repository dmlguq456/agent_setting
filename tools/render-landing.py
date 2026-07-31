#!/usr/bin/env python3
"""Render the public GitHub Pages surface: docs/index.html + docs/map.html.

Sources: manifest.json (resolved profile counts/membership) and
harness-manifest.json (capability census, summaries, taxonomy). Both pages are
self-contained (no CDN/network), share one design system, and support
light/dark. The internal operator hub (root hub.html) is intentionally NOT
published here.

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
    resolved = manifest["resolved_profiles"]
    caps = harness["capabilities"]
    entries = sorted(
        name for name, spec in caps.items()
        if spec["invocation"]["class"] == "entry-router"
    )
    membership = {
        name: [
            profile for profile in ("starter", "builder", "full")
            if name in resolved[profile]["capabilities"]
        ]
        for name in caps
    }
    return {
        "caps": caps,
        "entries": entries,
        "membership": membership,
        "cap_total": len(caps),
        "entry_total": len(entries),
        "unit_total": resolved["full"]["counts"]["units"],
        "starter_caps": resolved["starter"]["counts"]["capabilities"],
        "builder_caps": resolved["builder"]["counts"]["capabilities"],
        "full_caps": resolved["full"]["counts"]["capabilities"],
    }


# ---------------------------------------------------------------- design system

CSS = r"""
  :root {
    color-scheme: light dark;
    --font-ui: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont,
               "SF Pro Text", "Segoe UI", "Apple SD Gothic Neo", "Noto Sans KR", system-ui, sans-serif;
    --font-mono: "JetBrains Mono", ui-monospace, "SF Mono", SFMono-Regular, Menlo, monospace;

    --surface: #FCFCFD;
    --surface-2: #F5F5F7;
    --surface-3: #EDEDF1;
    --panel: #FFFFFF;
    --border: #E7E7EC;
    --border-strong: #D8D8DF;
    --text: #17171B;
    --text-2: #55555E;
    --text-3: #8A8A93;

    --g1: #5B5BD6; --g2: #8B5CF6; --g3: #2AA9C9;
    --accent: var(--g1);
    --accent-soft: #EEEEFC;
    --accent-text: #4747C2;

    --r-lg: 20px; --r-md: 14px; --r-sm: 10px;
    --shadow-1: 0 1px 2px rgba(20,20,40,.05), 0 8px 24px rgba(20,20,40,.06);
    --shadow-2: 0 2px 4px rgba(20,20,40,.06), 0 16px 40px rgba(20,20,40,.10);
    --nav-bg: rgba(252,252,253,.8);
    --blob-a: rgba(91,91,214,.16); --blob-b: rgba(42,169,201,.12);
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --surface: #101014;
      --surface-2: #17171D;
      --surface-3: #1F1F27;
      --panel: #16161C;
      --border: #26262F;
      --border-strong: #34343F;
      --text: #F1F1F4;
      --text-2: #B4B4BE;
      --text-3: #7C7C87;
      --accent: #9C9CF2;
      --accent-soft: #23233F;
      --accent-text: #B9B9F7;
      --shadow-1: 0 1px 2px rgba(0,0,0,.4), 0 10px 30px rgba(0,0,0,.35);
      --shadow-2: 0 2px 6px rgba(0,0,0,.5), 0 20px 50px rgba(0,0,0,.5);
      --nav-bg: rgba(16,16,20,.75);
      --blob-a: rgba(101,101,235,.22); --blob-b: rgba(45,180,214,.14);
    }
  }

  * { box-sizing: border-box; margin: 0; }
  html { scroll-behavior: smooth; }
  body {
    font-family: var(--font-ui); background: var(--surface); color: var(--text);
    line-height: 1.62; -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility;
  }
  a { color: var(--accent-text); text-decoration: none; }
  a:hover { text-decoration: underline; text-underline-offset: 3px; }
  code, .mono { font-family: var(--font-mono); }
  .wrap { max-width: 1100px; margin: 0 auto; padding: 0 24px; }

  /* ── nav ─────────────────────────────────────────────── */
  .nav-shell {
    position: sticky; top: 0; z-index: 40;
    background: var(--nav-bg); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
    border-bottom: 1px solid var(--border);
  }
  nav { display: flex; align-items: center; justify-content: space-between; padding: 14px 0; gap: 16px; }
  .brand { display: inline-flex; align-items: center; gap: 10px; font-weight: 800; font-size: 16.5px; letter-spacing: -.01em; color: var(--text); }
  .brand:hover { text-decoration: none; }
  .brand svg { display: block; }
  .nav-links { display: flex; gap: 6px; font-size: 14px; flex-wrap: wrap; align-items: center; }
  .nav-links a { color: var(--text-2); padding: 7px 12px; border-radius: 999px; }
  .nav-links a:hover { background: var(--surface-3); color: var(--text); text-decoration: none; }
  .nav-links a.cta {
    color: #fff; background: linear-gradient(120deg, var(--g1), var(--g2));
    font-weight: 600;
  }
  .nav-links a.cta:hover { filter: brightness(1.08); }

  /* ── hero ────────────────────────────────────────────── */
  .hero-shell { position: relative; overflow: hidden; }
  .hero-shell::before, .hero-shell::after {
    content: ""; position: absolute; border-radius: 50%; filter: blur(90px); pointer-events: none;
  }
  .hero-shell::before {
    width: 640px; height: 640px; left: 50%; top: -320px; transform: translateX(-78%);
    background: radial-gradient(circle at center, var(--blob-a), transparent 65%);
  }
  .hero-shell::after {
    width: 560px; height: 560px; left: 50%; top: -220px; transform: translateX(6%);
    background: radial-gradient(circle at center, var(--blob-b), transparent 65%);
  }
  header.hero { position: relative; padding: 92px 0 74px; text-align: center; }
  .hero-badge {
    display: inline-flex; align-items: center; gap: 8px;
    font-size: 13px; font-weight: 600; color: var(--accent-text);
    background: var(--accent-soft); border: 1px solid transparent;
    padding: 6px 14px; border-radius: 999px; margin-bottom: 26px;
  }
  .hero-badge .sep { color: var(--text-3); font-weight: 400; }
  .hero h1 {
    font-size: clamp(38px, 6.2vw, 64px); line-height: 1.06; letter-spacing: -.035em; font-weight: 800;
  }
  .grad {
    background: linear-gradient(105deg, var(--g1) 10%, var(--g2) 55%, var(--g3) 100%);
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }
  .hero p.sub { margin: 22px auto 0; max-width: 620px; font-size: 18.5px; color: var(--text-2); }
  .runtimes { margin-top: 20px; display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; font-size: 13.5px; color: var(--text-2); }
  .runtimes span {
    display: inline-flex; align-items: center; gap: 7px;
    border: 1px solid var(--border); border-radius: 999px; padding: 5px 13px; background: var(--panel);
  }
  .runtimes .dot { width: 7px; height: 7px; border-radius: 50%; background: linear-gradient(120deg, var(--g1), var(--g3)); }
  .install {
    margin: 36px auto 0; max-width: 730px; display: flex; align-items: stretch;
    border: 1px solid var(--border-strong); border-radius: 14px; overflow: hidden;
    background: var(--panel); box-shadow: var(--shadow-2); text-align: left;
  }
  .install .prompt { display: flex; align-items: center; padding: 0 0 0 18px; color: var(--g2); font-family: var(--font-mono); font-size: 14px; user-select: none; }
  .install code { flex: 1; font-size: 13.5px; padding: 16px 14px; overflow-x: auto; white-space: nowrap; color: var(--text); scrollbar-width: none; }
  .install code::-webkit-scrollbar { display: none; }
  .install button {
    border: 0; border-left: 1px solid var(--border); background: var(--surface-2);
    color: var(--text-2); font-family: var(--font-ui); font-size: 13px; font-weight: 600;
    padding: 0 20px; cursor: pointer; transition: color .15s, background .15s; white-space: nowrap;
  }
  .install button:hover { color: var(--text); background: var(--surface-3); }
  .hero .fineprint { margin-top: 15px; font-size: 13px; color: var(--text-3); }

  /* ── sections ────────────────────────────────────────── */
  section { padding: 72px 0; }
  section + section { border-top: 1px solid var(--border); }
  .kicker {
    font-size: 12.5px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase;
    color: var(--accent-text); margin-bottom: 10px;
  }
  h2 { font-size: clamp(24px, 3.4vw, 32px); letter-spacing: -.025em; margin-bottom: 10px; line-height: 1.25; }
  p.lede { color: var(--text-2); max-width: 660px; margin-bottom: 36px; font-size: 16px; }
  p.lede .mono { font-size: .9em; color: var(--text); }

  .grid { display: grid; gap: 18px; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }
  .card {
    border: 1px solid var(--border); border-radius: var(--r-lg); background: var(--panel);
    padding: 24px; box-shadow: var(--shadow-1);
    transition: transform .18s ease, box-shadow .18s ease;
  }
  .card:hover { transform: translateY(-3px); box-shadow: var(--shadow-2); }
  .card .icon {
    width: 38px; height: 38px; border-radius: 11px; display: flex; align-items: center; justify-content: center;
    background: var(--accent-soft); color: var(--accent-text); margin-bottom: 14px;
  }
  .card h3 { font-size: 16.5px; margin-bottom: 6px; letter-spacing: -.01em; }
  .card p { font-size: 14px; color: var(--text-2); }

  /* pipeline strip */
  .pipeline {
    display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 10px;
    border: 1px solid var(--border); border-radius: var(--r-lg); background: var(--surface-2);
    padding: 22px 18px; margin-top: 34px; font-family: var(--font-mono); font-size: 13.5px;
  }
  .pipeline .stage {
    background: var(--panel); border: 1px solid var(--border-strong); border-radius: 999px;
    padding: 7px 16px; color: var(--text); box-shadow: var(--shadow-1);
  }
  .pipeline .stage.hot { border-color: transparent; color: #fff; background: linear-gradient(120deg, var(--g1), var(--g2)); }
  .pipeline .arrow { color: var(--text-3); user-select: none; }

  /* architecture */
  .arch { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
  .layer {
    border: 1px solid var(--border); border-radius: var(--r-lg); background: var(--panel);
    padding: 22px; box-shadow: var(--shadow-1);
  }
  .layer h4 {
    font-size: 12px; text-transform: uppercase; letter-spacing: .09em; color: var(--text-3);
    margin-bottom: 14px; display: flex; align-items: center; gap: 8px;
  }
  .layer h4 .pip { width: 8px; height: 8px; border-radius: 3px; background: linear-gradient(120deg, var(--g1), var(--g3)); }
  .layer ul { list-style: none; padding: 0; font-size: 14px; }
  .layer li { padding: 7px 0; border-top: 1px solid var(--border); color: var(--text-2); }
  .layer li:first-child { border-top: 0; }
  .layer li .mono { font-size: 12.5px; color: var(--text); }
  .maplink-card {
    margin-top: 22px; display: flex; align-items: center; justify-content: space-between; gap: 14px;
    border: 1px solid var(--border); border-radius: var(--r-lg); padding: 20px 24px;
    background: linear-gradient(115deg, var(--accent-soft), transparent 70%), var(--panel);
    box-shadow: var(--shadow-1); flex-wrap: wrap;
  }
  .maplink-card strong { letter-spacing: -.01em; }
  .maplink-card .go {
    color: #fff; background: linear-gradient(120deg, var(--g1), var(--g2));
    border-radius: 999px; padding: 9px 18px; font-size: 14px; font-weight: 600; white-space: nowrap;
  }
  .maplink-card .go:hover { text-decoration: none; filter: brightness(1.08); }

  /* profiles */
  .profiles { display: grid; gap: 18px; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
  .profile {
    position: relative; border: 1px solid var(--border); border-radius: var(--r-lg);
    padding: 26px; background: var(--panel); box-shadow: var(--shadow-1);
  }
  .profile.featured { border-color: transparent; }
  .profile.featured::before {
    content: ""; position: absolute; inset: -1px; border-radius: inherit; padding: 1.5px;
    background: linear-gradient(135deg, var(--g1), var(--g2), var(--g3));
    -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
    -webkit-mask-composite: xor; mask-composite: exclude; pointer-events: none;
  }
  .profile .tag {
    position: absolute; top: -11px; right: 20px; font-size: 11.5px; font-weight: 700;
    color: #fff; background: linear-gradient(120deg, var(--g1), var(--g2));
    border-radius: 999px; padding: 3px 11px; letter-spacing: .03em;
  }
  .profile h3 { font-size: 17px; font-family: var(--font-mono); }
  .profile .count { font-size: 38px; font-weight: 800; letter-spacing: -.03em; margin: 10px 0 2px; }
  .profile .count small { font-size: 13.5px; font-weight: 500; color: var(--text-3); letter-spacing: 0; }
  .profile p { font-size: 14px; color: var(--text-2); min-height: 3.2em; }
  .profile code {
    display: block; margin-top: 16px; font-size: 12.5px;
    background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--r-sm);
    padding: 11px 13px; overflow-x: auto; white-space: nowrap;
  }

  /* quickstart */
  ol.steps { counter-reset: s; list-style: none; padding: 0; max-width: 760px; }
  ol.steps li { display: flex; gap: 18px; padding: 18px 0; border-top: 1px solid var(--border); }
  ol.steps li:first-child { border-top: 0; }
  ol.steps .n {
    counter-increment: s; flex: none; width: 30px; height: 30px; border-radius: 50%;
    background: var(--accent-soft); color: var(--accent-text); font-weight: 700; font-size: 14px;
    display: flex; align-items: center; justify-content: center; margin-top: 2px;
  }
  ol.steps .n::before { content: counter(s); }
  ol.steps .body { font-size: 15px; color: var(--text-2); }
  ol.steps .body b { color: var(--text); font-weight: 650; }
  ol.steps code {
    font-size: 13px; background: var(--surface-2); border: 1px solid var(--border);
    border-radius: 7px; padding: 2px 8px;
  }

  footer { border-top: 1px solid var(--border); padding: 36px 0 52px; font-size: 13.5px; color: var(--text-3); }
  .foot { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 12px; align-items: center; }
  .foot a { color: var(--text-2); }

  /* ── map page ────────────────────────────────────────── */
  .map-hero { padding: 64px 0 40px; position: relative; }
  .map-hero h1 { font-size: clamp(30px, 4.6vw, 44px); letter-spacing: -.03em; }
  .map-hero p { margin-top: 14px; max-width: 640px; color: var(--text-2); font-size: 16.5px; }
  .stats { display: flex; gap: 14px; flex-wrap: wrap; margin-top: 26px; }
  .stat {
    border: 1px solid var(--border); border-radius: var(--r-md); background: var(--panel);
    padding: 12px 18px; box-shadow: var(--shadow-1); min-width: 108px;
  }
  .stat b { display: block; font-size: 22px; letter-spacing: -.02em; }
  .stat span { font-size: 12.5px; color: var(--text-3); }

  .filters { display: flex; gap: 8px; flex-wrap: wrap; margin: 8px 0 26px; }
  .filters button {
    font-family: var(--font-ui); font-size: 13px; font-weight: 600; cursor: pointer;
    border: 1px solid var(--border); border-radius: 999px; padding: 7px 15px;
    background: var(--panel); color: var(--text-2); transition: all .15s;
  }
  .filters button:hover { color: var(--text); }
  .filters button.on {
    color: #fff; border-color: transparent;
    background: linear-gradient(120deg, var(--g1), var(--g2));
  }
  .cap-group { margin-bottom: 40px; }
  .cap-group h3 { font-size: 18px; letter-spacing: -.015em; margin-bottom: 4px; }
  .cap-group .desc { font-size: 14px; color: var(--text-3); margin-bottom: 16px; }
  .cap-grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fill, minmax(310px, 1fr)); }
  .cap {
    border: 1px solid var(--border); border-radius: var(--r-md); background: var(--panel);
    padding: 15px 17px; box-shadow: var(--shadow-1); transition: transform .15s, box-shadow .15s, opacity .2s;
  }
  .cap:hover { transform: translateY(-2px); box-shadow: var(--shadow-2); }
  .cap.dim { opacity: .28; }
  .cap .name { display: flex; align-items: center; gap: 8px; justify-content: space-between; }
  .cap .name .mono { font-size: 13.5px; font-weight: 650; color: var(--text); }
  .cap .pill {
    font-size: 10.5px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase;
    border-radius: 999px; padding: 2px 8px; color: var(--accent-text); background: var(--accent-soft);
    white-space: nowrap;
  }
  .cap .pill.stage { color: var(--text-3); background: var(--surface-3); }
  .cap p { font-size: 13px; color: var(--text-2); margin-top: 7px;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

  @media (max-width: 640px) {
    header.hero { padding: 64px 0 52px; }
    section { padding: 52px 0; }
    .install .prompt { display: none; }
    .nav-links a:not(.cta):not(.keep) { display: none; }
  }
"""

LOGO = (
    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
    '<defs><linearGradient id="lg" x1="0" y1="0" x2="24" y2="24">'
    '<stop offset="0" stop-color="#5B5BD6"/><stop offset=".55" stop-color="#8B5CF6"/>'
    '<stop offset="1" stop-color="#2AA9C9"/></linearGradient></defs>'
    '<path d="M12 2 21 7v2L12 14 3 9V7l9-5Z" fill="url(#lg)"/>'
    '<path d="M3 12.5 12 17.5 21 12.5V15L12 20 3 15v-2.5Z" fill="url(#lg)" opacity=".55"/>'
    "</svg>"
)

ICONS = {
    "route": '<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="19" r="3"/><circle cx="18" cy="5" r="3"/><path d="M12 19h4.5a3.5 3.5 0 0 0 0-7h-9a3.5 3.5 0 0 1 0-7H12"/></svg>',
    "net": '<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="5" r="2.6"/><circle cx="5" cy="19" r="2.6"/><circle cx="19" cy="19" r="2.6"/><path d="M12 7.6 6 16.5m6-8.9 6 8.9M7.6 19h8.8"/></svg>',
    "shield": '<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 5 6v5c0 4.7 3 8.6 7 10 4-1.4 7-5.3 7-10V6l-7-3Z"/><path d="m9 12 2 2 4-4"/></svg>',
    "db": '<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><ellipse cx="12" cy="5.5" rx="7" ry="2.8"/><path d="M5 5.5v13c0 1.5 3.1 2.8 7 2.8s7-1.3 7-2.8v-13"/><path d="M5 12c0 1.5 3.1 2.8 7 2.8s7-1.3 7-2.8"/></svg>',
    "blueprint": '<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9l-6-6Z"/><path d="M14 3v6h6M9 13h6M9 17h4"/></svg>',
    "units": '<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/></svg>',
}


def nav(active: str) -> str:
    map_extra = "keep" if active == "map" else ""
    return f"""
  <div class="nav-shell"><div class="wrap"><nav>
    <a class="brand" href="index.html">{LOGO}<span>Agent&nbsp;Harness</span></a>
    <div class="nav-links">
      <a href="index.html#features">Features</a>
      <a href="index.html#how">How it works</a>
      <a href="index.html#profiles">Profiles</a>
      <a href="map.html" class="{map_extra}">Agent map</a>
      <a href="{REPO_URL}">GitHub</a>
      <a href="index.html#install" class="cta keep">Install</a>
    </div>
  </nav></div></div>"""


COPY_JS = (
    "navigator.clipboard.writeText(document.getElementById('cmd').textContent)"
    ".then(()=>{this.textContent='Copied ✓';setTimeout(()=>this.textContent='Copy',1400)})"
)

FOOTER = f"""
<footer><div class="wrap"><div class="foot">
  <div style="display:flex;align-items:center;gap:9px">{LOGO}<span>Agent Harness — a portable operating layer for coding agents. MIT licensed.</span></div>
  <div>
    <a href="{REPO_URL}">GitHub</a> ·
    <a href="{REPO_URL}/releases">Releases</a> ·
    <a href="map.html">Agent map</a>
  </div>
</div></div></footer>"""


def render_index(d: dict) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Agent Harness — one agent workflow, three harnesses</title>
<meta name="description" content="A portable, deterministic operating layer for Claude Code, Codex, and OpenCode: routed capabilities, sealed dispatch, durable artifacts, persistent memory." />
<!-- GENERATED by tools/render-landing.py — DO NOT EDIT BY HAND. -->
<style>{CSS}</style>
</head>
<body>
{nav('home')}

<div class="hero-shell"><div class="wrap">
  <header class="hero" id="install">
    <div class="hero-badge">v2.0 released <span class="sep">·</span> MIT licensed <span class="sep">·</span> {d['cap_total']} capabilities</div>
    <h1>One agent workflow.<br /><span class="grad">Three harnesses.</span></h1>
    <p class="sub">A portable, deterministic operating layer for coding agents —
    routed capabilities, sealed cross-harness dispatch, durable artifacts, and
    persistent memory. Write the contract once; run it everywhere.</p>
    <div class="runtimes">
      <span><i class="dot"></i>Claude Code</span>
      <span><i class="dot"></i>Codex CLI</span>
      <span><i class="dot"></i>OpenCode</span>
    </div>
    <div class="install">
      <span class="prompt">$</span>
      <code id="cmd">{INSTALL_CMD}</code>
      <button onclick="{html.escape(COPY_JS, quote=True)}">Copy</button>
    </div>
    <p class="fineprint">SHA-256 checksummed release · <a href="{REPO_URL}/releases">release notes ↗</a></p>
  </header>
</div></div>

<div class="wrap">
  <section id="features">
    <div class="kicker">Why a harness layer</div>
    <h2>Vendor CLIs disagree on everything.<br />Your workflow shouldn't.</h2>
    <p class="lede">The harness keeps one portable semantic core —
    <span class="mono">core → capabilities/roles → adapters</span> — and projects it
    into each runtime's native skills, hooks, agents, and commands.</p>
    <div class="grid">
      <div class="card"><div class="icon">{ICONS['route']}</div>
        <h3>Routed capabilities</h3>
        <p>{d['entry_total']} entry routers behind one routing contract: every material task
        gets an explicit route card, a sealed intensity, and a five-field completion report.</p></div>
      <div class="card"><div class="icon">{ICONS['net']}</div>
        <h3>Cross-harness orchestration</h3>
        <p>Standard+ work compiles an immutable route and dispatches registered headless
        workers across model families — reviews land as files, watched live on the Fleet dashboard.</p></div>
      <div class="card"><div class="icon">{ICONS['shield']}</div>
        <h3>Guards, not vibes</h3>
        <p>Write scopes, spec-read gates, artifact ordering, and route participation are
        enforced by hooks and scripts. The model judges; the code enforces.</p></div>
      <div class="card"><div class="icon">{ICONS['db']}</div>
        <h3>Memory that survives sessions</h3>
        <p>One SQLite store with tiered records, capsule-index recall on every prompt, and
        automatic session distillation — no manual “remember this”.</p></div>
      <div class="card"><div class="icon">{ICONS['blueprint']}</div>
        <h3>Blueprint-governed pipelines</h3>
        <p>Research → spec → code → experiment, with PRD updates versioned and drift
        surfaced instead of silently absorbed.</p></div>
      <div class="card"><div class="icon">{ICONS['units']}</div>
        <h3>Roles as a catalog</h3>
        <p>{d['unit_total']} portable units — planner, reviewer, implementer, and material personas —
        each worker runs a sealed role, model profile, and write scope.</p></div>
    </div>
  </section>

  <section id="how">
    <div class="kicker">How it works</div>
    <h2>Describe the outcome. The harness closes the loop.</h2>
    <p class="lede">“Implement and test the login API, then leave a change report” is a
    complete instruction — routing, staging, verification, and evidence are the harness's job.</p>
    <div class="pipeline">
      <span class="stage">route card</span><span class="arrow">→</span>
      <span class="stage hot">plan</span><span class="arrow">→</span>
      <span class="stage hot">execute</span><span class="arrow">→</span>
      <span class="stage hot">test</span><span class="arrow">→</span>
      <span class="stage hot">report</span><span class="arrow">→</span>
      <span class="stage">durable evidence</span>
    </div>

    <div class="arch" style="margin-top:44px">
      <div class="layer">
        <h4><span class="pip"></span>Core contracts</h4>
        <ul>
          <li><span class="mono">core/WORKFLOW.md</span> — routing</li>
          <li><span class="mono">core/CONVENTIONS.md</span> — QA &amp; roles</li>
          <li><span class="mono">core/OPERATIONS.md</span> — dispatch</li>
          <li><span class="mono">core/MEMORY.md</span> — memory</li>
        </ul>
      </div>
      <div class="layer">
        <h4><span class="pip"></span>Portable catalog</h4>
        <ul>
          <li>{d['cap_total']} capabilities · {d['entry_total']} entry routers</li>
          <li>{d['unit_total']} role units with sealed profiles</li>
          <li>Topology registry &amp; sealed routes</li>
          <li>Memory store + recall bridge</li>
        </ul>
      </div>
      <div class="layer">
        <h4><span class="pip"></span>Runtime adapters</h4>
        <ul>
          <li>Claude Code — hooks · skills · fleet</li>
          <li>Codex CLI — preflight · managed entry</li>
          <li>OpenCode — plugin · commands</li>
        </ul>
      </div>
    </div>
    <div class="maplink-card">
      <div><strong>Explore the full agent map</strong><br />
        <span style="font-size:14px;color:var(--text-2)">Every capability, pipeline stage, and profile — visualized.</span></div>
      <a class="go" href="map.html">Open the map →</a>
    </div>
  </section>

  <section id="profiles">
    <div class="kicker">Profiles</div>
    <h2>Start small. Grow without forking.</h2>
    <p class="lede">Profiles are manifest-computed; dependency closure is automatic and
    switching later is one command.</p>
    <div class="profiles">
      <div class="profile">
        <h3>starter</h3>
        <div class="count">{d['starter_caps']}<small> capabilities</small></div>
        <p>Everyday essentials: the code pipeline, analysis, memory, and reports.</p>
        <code>harness install claude --profile starter</code>
      </div>
      <div class="profile featured">
        <span class="tag">DEFAULT</span>
        <h3>builder</h3>
        <div class="count">{d['builder_caps']}<small> capabilities</small></div>
        <p>Analyze, specify, implement, verify, and ship software with project memory.</p>
        <code>harness install claude --profile builder</code>
      </div>
      <div class="profile">
        <h3>full</h3>
        <div class="count">{d['full_caps']}<small> capabilities</small></div>
        <p>Everything — research writing, the design pipeline, experiments, operations.</p>
        <code>harness install claude --profile full</code>
      </div>
    </div>
  </section>

  <section id="quickstart">
    <div class="kicker">Quickstart</div>
    <h2>Three steps to a routed workflow.</h2>
    <ol class="steps" style="margin-top:28px">
      <li><span class="n"></span><div class="body"><b>Install the verified release.</b><br />
        <code style="display:block;margin-top:8px;padding:10px 13px;border-radius:10px;overflow-x:auto;white-space:nowrap">{INSTALL_CMD}</code></div></li>
      <li><span class="n"></span><div class="body"><b>Activate a profile per runtime.</b><br />
        <code>harness install claude --profile builder</code> — repeat with
        <code>codex</code> / <code>opencode</code>, then <code>harness verify</code>.</div></li>
      <li><span class="n"></span><div class="body"><b>Describe the outcome in your agent CLI.</b><br />
        “Implement and test the login API, then leave a change report.” The harness
        proposes the route card and closes the loop with durable evidence.</div></li>
    </ol>
  </section>
</div>
{FOOTER}
</body>
</html>
"""


# ------------------------------------------------------------------- map page

MAP_GROUP_ORDER = [
    ("research", "Research first", "Ground new intent in evidence before building.",
     ["autopilot-research", "analyze-project"]),
    ("code", "Code & experiments", "Spec-governed implementation and rapid experiment loops.",
     ["autopilot-spec", "autopilot-code", "autopilot-lab", "autopilot-ship",
      "code-plan", "code-execute", "code-refine", "code-test", "code-report"]),
    ("docs", "Documents", "Papers, reports, proposals — drafted, refined, applied.",
     ["autopilot-draft", "autopilot-refine", "autopilot-apply",
      "draft-strategy", "draft-refine"]),
    ("design", "Design", "Reference-grounded visual design with token contracts.",
     ["autopilot-design", "design-init", "design-refs", "design-tokens",
      "design-components", "design-review", "design-handoff"]),
    ("ops", "Cross-project & operations", "Continuity, inspection, and the user profile.",
     ["analyze-user", "audit", "post-it"]),
]


def render_map(d: dict) -> str:
    caps = d["caps"]
    membership = d["membership"]
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
            profiles = " ".join(membership.get(name, []))
            summary = html.escape(str(spec.get("summary", "")).strip())
            cards.append(
                f'<div class="cap" data-profiles="{profiles}">'
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
            f'<div class="cap" data-profiles="{" ".join(membership.get(n, []))}">'
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
<title>Agent map — Agent Harness</title>
<meta name="description" content="Every Agent Harness capability, pipeline stage, and profile — visualized." />
<!-- GENERATED by tools/render-landing.py — DO NOT EDIT BY HAND. -->
<style>{CSS}</style>
</head>
<body>
{nav('map')}

<div class="hero-shell"><div class="wrap">
  <header class="map-hero">
    <div class="kicker">Agent map</div>
    <h1>The whole harness, <span class="grad">at a glance.</span></h1>
    <p>One portable catalog projected into three runtimes. Entry routers own whole
    pipelines; stages are the sealed workers they dispatch. Filter by profile to see
    exactly what an installation exposes.</p>
    <div class="stats">
      <div class="stat"><b>{d['cap_total']}</b><span>capabilities</span></div>
      <div class="stat"><b>{d['entry_total']}</b><span>entry routers</span></div>
      <div class="stat"><b>{d['unit_total']}</b><span>role units</span></div>
      <div class="stat"><b>3</b><span>runtimes</span></div>
    </div>
  </header>
</div></div>

<div class="wrap">
  <section style="padding-top:40px">
    <div class="filters" id="filters">
      <button class="on" data-p="all">All</button>
      <button data-p="starter">starter · {d['starter_caps']}</button>
      <button data-p="builder">builder · {d['builder_caps']}</button>
      <button data-p="full">full · {d['full_caps']}</button>
    </div>
    {"".join(groups_html)}
  </section>

  <section>
    <div class="maplink-card">
      <div><strong>Ready to run it?</strong><br />
        <span style="font-size:14px;color:var(--text-2)">One line installs the checksummed release for every runtime.</span></div>
      <a class="go" href="index.html#install">Install Agent Harness →</a>
    </div>
  </section>
</div>
{FOOTER}

<script>
  const buttons = document.querySelectorAll('#filters button');
  buttons.forEach(btn => btn.addEventListener('click', () => {{
    buttons.forEach(b => b.classList.toggle('on', b === btn));
    const p = btn.dataset.p;
    document.querySelectorAll('.cap').forEach(card => {{
      const set = (card.dataset.profiles || '').split(/\\s+/);
      card.classList.toggle('dim', p !== 'all' && !set.includes(p));
    }});
  }}));
</script>
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
