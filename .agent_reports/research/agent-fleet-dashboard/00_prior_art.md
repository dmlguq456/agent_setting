# Prior-Art Scan — Cross-Harness Agent-Fleet Terminal Dashboard

> Time-boxed lightweight scan (~20 min, WebSearch + WebFetch). Goal: survey OSS before building a
> "one live TUI showing every active AI coding-agent CLI session (Claude Code / Codex / opencode),
> pure external observer that injects nothing." Stars/licenses marked **n/v** where not verified —
> not fabricated. Date: 2026-07-01.

## Key framing: two tool classes (this decides build-vs-adopt)

The space splits cleanly, and **almost nothing is a pure external observer**:

- **(a) Orchestrator / multiplexer** — you *launch* agents through it (usually one git worktree per
  agent). It owns session lifecycle; state comes from tmux pane-text scraping or lifecycle hooks.
  → claude-squad, ccmanager, agent-deck, uzi, crystal, vibe-kanban, agent-of-empires, **herdr**.
- **(b) Pure observer / monitor** — reads state artifacts of *already-running* sessions, spawns
  nothing. Discovery = tail `~/.claude/projects/**/*.jsonl` (+ `~/.claude/sessions/{PID}.json`).
  → claude-view, claude-monitor, onikan27/claude-code-monitor, Recon, tmux-agent-status.
  **Catch: this class is almost all Claude-Code-ONLY** — it parses Claude's JSONL transcript
  format; Codex/opencode have different transcript layouts, so cross-harness needs per-harness
  adapters (exactly the state emitters this repo already writes).

Our stated vision = class (b) **but cross-harness** — which no single existing tool fully delivers.

## Comparison table

| Tool | Bucket | What it shows | Discovery method | Cross-harness? | Status / stars | License |
|---|---|---|---|---|---|---|
| **herdr** (ogulcancelik) | 1 orchestrator/mux | Sidebar per pane w/ agent state (🔴blocked 🟡working 🔵done 🟢idle); persistent+remote panes | process-name match + terminal-output heuristics; agents also push state via **Unix-socket JSON-RPC** (`pane.report_agent`/`pane.release_agent`) | **Yes** — 14+ agents (Claude, Codex, opencode, Amp, Droid, Copilot CLI…) | Active, Rust, ~**9.1k**★, v0.7.x (verified via GH) | AGPL-3.0-or-later / commercial dual |
| claude-squad (smtg-ai) | 1 orchestrator | Multiple agents in isolated tmux+worktree; TUI list, background/yolo mode | it spawns the sessions (tmux) | Yes (Claude/Codex/OpenCode/Amp) | Active, Go, popular (stars n/v) | AGPL-3.0 (n/v) |
| ccmanager (kbwo) | 1 orchestrator | Session list w/ per-project [active/busy/waiting] counts | recursive git-repo autodiscovery; spawns sessions | Yes (Claude/Gemini/Codex/Cursor/Copilot/Cline/OpenCode/Kimi) | Active, TS (stars n/v) | n/v |
| agent-deck (asheshgoplani) | 1 orchestrator | One TUI for many agents; archive/restore w/ worktree+lineage | tmux-backed sessions it owns | Yes (Claude/Gemini/OpenCode/Codex…) | Active (stars n/v) | n/v |
| uzi (devflowinc) | 1 parallel runner | Run *large numbers* of agents in parallel worktrees (CLI, less TUI) | it launches N agents in worktrees | Yes (agent-agnostic) | Active, Go (stars n/v) | n/v |
| crystal → **Nimbalyst** (stravu) | 1 orchestrator | Desktop app (Electron), parallel Codex/Claude in worktrees, compare runs | app-managed sessions | Yes (Codex+Claude) | Renamed to Nimbalyst; active (stars n/v) | n/v |
| vibe-kanban (BloopAI) | 1 orchestrator | Kanban board (CLI+web) of agent tasks, parallel worktrees, visual review | it runs tasks as agents | Yes | Bloop **shut down early 2026**; community-maintained OSS | Apache-2.0 |
| omnara (omnara-ai) | 1 remote control | "Talk to your agents from anywhere"; mobile/voice command center | agent SDK integration | Yes (Claude/Codex/n8n) | Old repo **unmaintained** → migrated to hosted omnara.com | n/v |
| agent-of-empires | 1 orchestrator | TUI **or** web/mobile; parallel branches, optional Docker sandbox | it spawns sessions | Yes (Claude/OpenCode/Codex/Gemini/Pi/Copilot/Droid) | Active (stars n/v) | n/v |
| container-use (dagger) | 1 sandbox layer | Containerized isolated envs per agent (not a dashboard) | provides envs agents run in | Yes (MCP-based) | Active (stars n/v) | n/v |
| sculptor (imbue) | 1 orchestrator | Parallel agents in containers w/ UI | app-managed | Yes | Exists (details n/v) | n/v |
| Recon | 1/2 hybrid | tmux-native TUI dashboard of Claude sessions; state from pane status-bar text | reads `~/.claude/sessions/{PID}.json` + JSONL, scrapes status bar | Claude-centric | Exists (stars n/v) | n/v |
| tmux-agent-status (samleeney) | 2 observer | tmux statusline: which sessions Claude/Codex working vs idle | scrapes tmux pane text | Claude+Codex | Small, active (stars n/v) | n/v |
| claude-view (recca0120) | 2 pure observer | "Mission control": every CC session live, cost/analytics; Rust mmap+SIMD JSONL | tails `~/.claude/projects/**/*.jsonl` | **Claude only** | Active, Rust (stars n/v) | n/v |
| claude-monitor (szaher) / onikan27 claude-code-monitor | 2 pure observer | Web/mobile dashboard of all CC sessions, focus-switch | watches `~/.claude/projects/` JSONL | **Claude only** | Active (stars n/v) | n/v |
| Claude Code Agent View (built-in) | 2 native | Anthropic's own single dashboard of every running session | built into CC (ships ~May 2026) | Claude only | Shipping (1st-party) | — |
| **htop / btop / glances / gotop** | 2 sysmon | (render patterns only — below) | /proc etc. | — | mature | GPL/Apache |
| **zellij / tmux** | 2 mux | pane layout + statusline state glyphs | — | — | mature | MIT/ISC |

## Render patterns worth stealing (bucket 2)

- **htop**: fixed summary header + scrollable table, F-key action bar, color bars, ~1.5s refresh → header fleet-summary + one-row-per-session table.
- **btop**: bordered panel-per-domain grid, braille sparklines, responsive reflow when narrow → panel-per-session grid that collapses to rows on small terminals.
- **glances**: threshold coloring (green/yellow/red) + width-adaptive columns → color = liveness/state; hide columns when narrow.
- **zellij / tmux**: declarative layout + statusline format polling a script every N s → cheap "statusline mode" (1 line/session) as the minimal viable view; full grid as the rich view.

## Patterns worth stealing for OUR case

1. **Discovery = tail JSONL transcripts, don't scrape tmux text.** The pure-observer class (claude-view/claude-monitor) proves reading `~/.claude/projects/**/*.jsonl` (+ `~/.claude/sessions/{PID}.json`) is the robust zero-injection discovery path for Claude. Do the same, plus per-harness adapters for Codex/opencode transcript dirs. Pane-text scraping (Recon) is fragile — avoid as primary.
2. **State model = herdr's {idle, working, blocked, done/release}.** Already a de-facto vocabulary and *already what this repo's `herdr-agent-state.sh` emits*. Reuse those four states + glyphs verbatim.
3. **Liveness = transcript mtime**, mirroring this repo's own `dispatch-liveness.sh` (transcript-mtime SUSPECT/DEAD). Same trick detects hung/dead panes without owning them.
4. **Per-project headless jobs**: fold `jobs.log` / dispatch registry into the same view as a second section (herdr has no notion of *our* headless dispatch jobs — that's our differentiator).
5. **Two-tier render** (statusline row ↔ full panel grid), like tmux→btop, so the cheap path works even over ssh.
6. **Idempotent, append-tolerant parsing** (claude-view uses mmap/SIMD for this) — tail incrementally, never re-read whole files each tick.

## herdr verdict

**What it is:** `github.com/ogulcancelik/herdr` — a Rust "agent multiplexer" (tmux-for-agents, ~9.1k★, AGPL-3.0/commercial dual). You run your coding agents *inside* herdr panes; it auto-detects 14+ agents (Claude/Codex/opencode incl.) and shows a sidebar with per-agent state. It exposes a **local Unix-socket JSON-RPC API** that agents push state into and that third parties can query/subscribe to. **This repo already integrates with it**: `adapters/claude/hooks/herdr-agent-state.sh` (marked "installed/managed by herdr", integration v4) connects to `$HERDR_SOCKET_PATH` and sends `pane.report_agent {pane_id, source, agent, state, seq, agent_session_id}` / `pane.release_agent` on our lifecycle hooks. So the "herdr socket" this repo emits to is **that real OSS project's receiver**, not something homegrown.

**Adopt or build?** herdr is an **orchestrator/multiplexer, not a pure external observer** — adopting it *as-is* means making herdr your terminal multiplexer (replacing tmux; agents must be launched inside herdr panes). That contradicts the "pure observer, injects nothing" goal and the per-project-headless-dispatch requirement (herdr knows nothing about our `jobs.log` dispatch jobs). **Recommendation: don't run our dashboard as a herdr client, and don't adopt herdr as the runtime — but steal its contract.** Concretely: (a) keep the socket state-vocabulary and the emitter we already wrote as the *canonical per-session state format*, (b) if herdr *is* running, our observer can optionally read its socket as one more source; (c) otherwise our observer discovers sessions itself via JSONL tailing. This keeps zero-injection and cross-harness without ceding terminal ownership.

## Build-vs-adopt recommendation

**Build our own — but thin.** No existing tool matches the target (pure external observer × cross-harness × includes our per-project headless dispatch jobs). The closest single tools are **claude-view / claude-monitor** (right *observer* architecture — JSONL tailing, zero injection — but **Claude-only**, wrong render target: web not TUI) and **herdr** (right *cross-harness state model & our existing emitter*, but it's a *multiplexer* that owns the terminal, wrong for observe-only). None is adoptable wholesale.

**Scale = SMALL, favors build-thin.** The hard parts are already solved upstream in this very repo: state vocabulary + emitters (`herdr-agent-state.sh`) and liveness (`dispatch-liveness.sh`) exist; discovery is "tail a few JSONL dirs by mtime"; render is a handful of panels on a 1–2 s tick. That's a few-hundred-line reader + a curses grid, not a framework. So: **build our own thin TUI observer, reuse the herdr state contract + our liveness helper, add the headless-dispatch section herdr lacks.**

## Render stack — validate/challenge "zero-dep python curses"

For a handful of session panels + 1–2 s refresh reading local state files:

- **python curses (stdlib, zero-dep)** — ✅ *recommended for us*. This repo is already python+bash; render load is trivial (few panels, no graphs); a fixed grid + statusline row needs no framework. Cost: manual layout math, manual resize (`KEY_RESIZE`), manual double-buffer to avoid flicker — all cheap at this scale.
- **Textual / Rich (python)** — nicer DX (CSS-ish layout, reactive, mouse, widgets) but adds a pip dep and weight; only worth it if the UI grows complex (tabs, scroll regions, mouse). Keep as the fallback if curses layout gets painful.
- **Go bubbletea / lipgloss** — best if we wanted a shippable single static binary (claude-squad/uzi chose Go), but off-language for this repo.
- **Rust ratatui** — fastest, single binary; herdr & claude-view chose Rust for perf — but perf is a non-issue at our scale and Rust is off-language.

**Verdict: zero-dep python curses is the right call** for v1 (matches repo language, zero install, trivial render budget). Only escalate to Textual if the panel layout/interaction outgrows a fixed grid.

---
*Sources (skimmed, not exhaustively read):* github.com/ogulcancelik/herdr · herdr.dev · github.com/smtg-ai/claude-squad · github.com/kbwo/ccmanager · github.com/asheshgoplani/agent-deck · github.com/devflowinc/uzi · github.com/stravu/crystal (Nimbalyst) · github.com/BloopAI/vibe-kanban · github.com/omnara-ai/omnara · github.com/njbrake/agent-of-empires · recca0120.github.io claude-view · github.com/szaher/claude-monitor · github.com/onikan27/claude-code-monitor · agent-wars.com Recon · github.com/samleeney/tmux-agent-status · runpane.com/tmux-agent-managers · github.com/bradAGI/awesome-cli-coding-agents · github.com/andyrewlee/awesome-agent-orchestrators
