# design-mcp

Playwright-wrapped MCP server that gives a Claude Code agent the **visual feedback loop**
at the heart of design work: render a page → see it → read console errors → query the DOM.
Implements component ① of `claude-design-harness-spec.md` ("전체 하네스의 절반").

## Tools

| tool | purpose |
|---|---|
| `preview({ path, viewportWidth?, viewportHeight?, waitUntil? })` | Load an HTML file into headless Chromium. Resets the console buffer. Serves the project root as a dev server so relative assets / ES modules / fetch resolve. |
| `screenshot({ savePath, steps?, fullPage?, hq?, clip? })` | Capture to PNG/JPEG. `steps[]` run JS + wait before each capture → multiple states (slides, scroll, interactions). Multi-step → `NN-` prefix. Does **not** return pixels (token saving) — use `view_image`. |
| `getConsoleLogs()` | Console logs + errors since last `preview`. First check after every build. |
| `eval_js({ code })` | Run JS in page context (DOM queries, computed styles, interaction tests). Bare expression auto-returned; multi-statement needs explicit `return`. |
| `view_image({ path, maxSize? })` | Load an image as a vision input (downscaled to ≤1000px long edge). |
| `image_metadata({ path })` | Dimensions / format / alpha / animation without sending pixels. |

## Registration

Registered at **user scope** so every project shares it:

```bash
claude mcp add design --scope user -- node ~/.claude/tools/design-mcp/server.js
```

The static server roots at the launch cwd (the project). Override with `DESIGN_ROOT=/abs/path`.
Browsers resolve from the default Playwright cache (`~/.cache/ms-playwright`).

## Smoke test

```bash
cd ~/.claude/tools/design-mcp && npm run smoke
```

Validates §2.5 of the spec: preview→screenshot→view_image round-trip, console-error capture,
`eval_js` computed-style query, two-state `screenshot.steps`. All deps are pinned in
`package-lock.json`.

## Used by

`autopilot-design` (design-init self-provisions & smoke-tests it; design-components /
design-review / design-tokens render through it). Replaces the older ad-hoc
`preview_screenshot` + per-tool rasterizer references.
