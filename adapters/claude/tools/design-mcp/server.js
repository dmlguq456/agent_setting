#!/usr/bin/env node
/**
 * Design MCP Server
 * -----------------
 * Wraps Playwright (headless Chromium) so an agent can RENDER a page,
 * SEE it (screenshot → view_image), read CONSOLE errors, and QUERY the DOM (eval_js).
 * This is the "visual feedback loop" that turns a coding agent into a design agent.
 *
 * Tools: preview · screenshot · getConsoleLogs · eval_js · view_image · image_metadata
 *
 * A single persistent browser context/page lives for the process lifetime so console
 * output and page state accumulate across calls. The console buffer resets on preview.
 *
 * Static files are served from DESIGN_ROOT (default: the launch cwd) so relative assets
 * (./style.css, /styles/tokens.css, ES modules, fetch) resolve like a real dev server.
 */
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { chromium } from "playwright";
import sharp from "sharp";

// ---------------------------------------------------------------------------
// Static file server (serves the project root so a browser can load its files)
// ---------------------------------------------------------------------------
const MIME = {
  ".html": "text/html; charset=utf-8",
  ".htm": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".webp": "image/webp",
  ".ico": "image/x-icon",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".ttf": "font/ttf",
  ".otf": "font/otf",
  ".map": "application/json; charset=utf-8",
  ".txt": "text/plain; charset=utf-8",
};

// staticRoot is mutable: defaults to launch cwd, but preview() may re-root it
// to the directory of an HTML file that lives outside the project tree.
let staticRoot = process.env.DESIGN_ROOT
  ? path.resolve(process.env.DESIGN_ROOT)
  : process.cwd();

function makeStaticServer() {
  return http.createServer((req, res) => {
    try {
      let urlPath = decodeURIComponent(new URL(req.url, "http://x").pathname);
      if (urlPath === "/") urlPath = "/index.html";
      const resolved = path.resolve(staticRoot, "." + urlPath);
      // Path-traversal guard: must stay within staticRoot.
      if (!resolved.startsWith(staticRoot)) {
        res.writeHead(403);
        res.end("Forbidden");
        return;
      }
      fs.stat(resolved, (err, stat) => {
        if (err) {
          res.writeHead(404, { "content-type": "text/plain" });
          res.end("Not found: " + urlPath);
          return;
        }
        const target = stat.isDirectory() ? path.join(resolved, "index.html") : resolved;
        fs.readFile(target, (e, data) => {
          if (e) {
            res.writeHead(404, { "content-type": "text/plain" });
            res.end("Not found: " + urlPath);
            return;
          }
          const mime = MIME[path.extname(target).toLowerCase()] || "application/octet-stream";
          res.writeHead(200, { "content-type": mime, "cache-control": "no-store" });
          res.end(data);
        });
      });
    } catch (e) {
      res.writeHead(500);
      res.end(String(e));
    }
  });
}

let httpServer, httpPort;
function ensureStaticServer() {
  if (httpServer) return Promise.resolve(httpPort);
  httpServer = makeStaticServer();
  return new Promise((resolve, reject) => {
    httpServer.on("error", reject);
    httpServer.listen(0, "127.0.0.1", () => {
      httpPort = httpServer.address().port;
      resolve(httpPort);
    });
  });
}

// ---------------------------------------------------------------------------
// Persistent browser + page (console buffer accumulates, resets on preview)
// ---------------------------------------------------------------------------
let browser, page;
let consoleBuffer = [];

async function ensurePage() {
  if (!browser) {
    browser = await chromium.launch({ headless: true });
  }
  if (!page) {
    page = await browser.newPage();
    page.on("console", (m) => {
      let loc = "";
      try {
        const l = m.location();
        loc = l && l.url ? `${l.url}:${l.lineNumber ?? 0}` : "";
      } catch {}
      consoleBuffer.push({ type: m.type(), text: m.text(), location: loc });
    });
    page.on("pageerror", (e) => {
      consoleBuffer.push({ type: "error", text: String(e?.stack || e), location: "pageerror" });
    });
    page.on("requestfailed", (r) => {
      const f = r.failure();
      consoleBuffer.push({
        type: "error",
        text: `request failed: ${r.url()} — ${f ? f.errorText : "unknown"}`,
        location: "network",
      });
    });
  }
  return page;
}

// Resolve a preview path argument to a URL on the static server.
// Accepts: relative-to-root, or absolute. If absolute & outside root, re-root.
function resolvePreviewUrl(p) {
  const abs = path.resolve(p.startsWith("/") ? p : path.join(staticRoot, p));
  if (abs.startsWith(staticRoot + path.sep) || abs === staticRoot) {
    const rel = path.relative(staticRoot, abs).split(path.sep).join("/");
    return { url: `http://127.0.0.1:${httpPort}/${rel}`, abs };
  }
  // Outside the project tree → serve that file's directory.
  staticRoot = path.dirname(abs);
  return { url: `http://127.0.0.1:${httpPort}/${path.basename(abs)}`, abs };
}

// Wrap an eval_js snippet: a single bare expression is auto-returned;
// anything with ; / newline / `return` is treated as a function body.
function wrapEval(code) {
  const t = code.trim();
  const isExpr = !/[;\n]/.test(t) && !/\breturn\b/.test(t);
  return isExpr ? `(async()=>(${t}))()` : `(async()=>{${code}\n})()`;
}

function jsonText(obj) {
  return { content: [{ type: "text", text: JSON.stringify(obj, null, 2) }] };
}
function errText(msg) {
  return { content: [{ type: "text", text: msg }], isError: true };
}

// ---------------------------------------------------------------------------
// MCP server + tools
// ---------------------------------------------------------------------------
const server = new McpServer({ name: "design", version: "1.0.0" });

server.tool(
  "preview",
  "Load an HTML file (path relative to the project root, or absolute) into the headless browser. All subsequent tools act on this page. Resets the console buffer.",
  {
    path: z.string().describe("HTML file path (relative to project root or absolute)"),
    viewportWidth: z.number().optional().describe("default 1440"),
    viewportHeight: z.number().optional().describe("default 900"),
    waitUntil: z
      .enum(["load", "domcontentloaded", "networkidle", "commit"])
      .optional()
      .describe("default 'load'"),
  },
  async ({ path: p, viewportWidth = 1440, viewportHeight = 900, waitUntil = "load" }) => {
    try {
      await ensureStaticServer();
      const pg = await ensurePage();
      consoleBuffer = [];
      const { url, abs } = resolvePreviewUrl(p);
      if (!fs.existsSync(abs)) return errText(`File not found: ${abs}`);
      await pg.setViewportSize({ width: viewportWidth, height: viewportHeight });
      await pg.goto(url, { waitUntil, timeout: 20000 });
      return jsonText({
        ok: true,
        url,
        title: await pg.title(),
        viewport: { width: viewportWidth, height: viewportHeight },
        consoleErrors: consoleBuffer.filter((l) => l.type === "error").length,
      });
    } catch (e) {
      return errText(`preview failed: ${String(e?.message || e)}`);
    }
  }
);

server.tool(
  "screenshot",
  "Capture the current page to a PNG/JPEG file (the agent then views it via view_image). steps[] run JS + wait before each capture to record multiple states (slides, scroll, interactions); multi-step captures are saved with 01-/02- prefixes.",
  {
    savePath: z.string().describe("Output file path. With multiple steps, an NN- prefix is added."),
    steps: z
      .array(
        z.object({
          code: z.string().optional().describe("JS to run in page context before capture"),
          delayMs: z.number().optional().describe("wait after code, default 200"),
        })
      )
      .optional()
      .describe("default a single immediate capture"),
    fullPage: z.boolean().optional().describe("capture full scroll height, default false"),
    hq: z.boolean().optional().describe("PNG when true (default), JPEG when false"),
    clip: z
      .object({ x: z.number(), y: z.number(), width: z.number(), height: z.number() })
      .optional()
      .describe("crop region (ignored if fullPage)"),
  },
  async ({ savePath, steps, fullPage = false, hq = true, clip }) => {
    try {
      if (!page) return errText("No page loaded. Call preview first.");
      const stepList = steps && steps.length ? steps : [{}];
      const files = [];
      for (let i = 0; i < stepList.length; i++) {
        const { code, delayMs = 200 } = stepList[i];
        if (code) await page.evaluate(wrapEval(code));
        await page.waitForTimeout(delayMs);
        const out =
          stepList.length > 1
            ? savePath.replace(/(\.\w+)$/, `-${String(i + 1).padStart(2, "0")}$1`)
            : savePath;
        fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
        const opts = { path: out, fullPage, type: hq ? "png" : "jpeg" };
        if (clip && !fullPage) opts.clip = clip;
        await page.screenshot(opts);
        files.push(out);
      }
      return jsonText({ files });
    } catch (e) {
      return errText(`screenshot failed: ${String(e?.message || e)}`);
    }
  }
);

server.tool(
  "getConsoleLogs",
  "Return console logs + errors accumulated since the last preview. First check after every build.",
  {},
  async () => {
    return jsonText({
      logs: consoleBuffer,
      errors: consoleBuffer.filter((l) => l.type === "error").map((l) => l.text),
    });
  }
);

server.tool(
  "eval_js",
  "Run JS in the current page context (DOM queries, computed styles, interaction tests). A bare expression is auto-returned; for multiple statements, include an explicit `return`. Result is JSON-serialized.",
  { code: z.string() },
  async ({ code }) => {
    try {
      if (!page) return errText("No page loaded. Call preview first.");
      const result = await page.evaluate(wrapEval(code));
      return jsonText({ result });
    } catch (e) {
      return errText(`eval_js failed: ${String(e?.message || e)}`);
    }
  }
);

server.tool(
  "view_image",
  "Load an image file as a vision input (downscaled to max 1000px on the long edge to save tokens).",
  { path: z.string(), maxSize: z.number().optional().describe("long-edge px, default 1000") },
  async ({ path: p, maxSize = 1000 }) => {
    try {
      const abs = path.resolve(p);
      if (!fs.existsSync(abs)) return errText(`Image not found: ${abs}`);
      const buf = await sharp(abs)
        .resize({ width: maxSize, height: maxSize, fit: "inside", withoutEnlargement: true })
        .png()
        .toBuffer();
      return { content: [{ type: "image", data: buf.toString("base64"), mimeType: "image/png" }] };
    } catch (e) {
      return errText(`view_image failed: ${String(e?.message || e)}`);
    }
  }
);

server.tool(
  "image_metadata",
  "Return dimensions/format/alpha/animation of an image without sending pixels.",
  { path: z.string() },
  async ({ path: p }) => {
    try {
      const abs = path.resolve(p);
      if (!fs.existsSync(abs)) return errText(`Image not found: ${abs}`);
      const m = await sharp(abs).metadata();
      return jsonText({
        width: m.width,
        height: m.height,
        format: m.format,
        hasAlpha: !!m.hasAlpha,
        animated: (m.pages || 1) > 1,
        frames: m.pages || 1,
      });
    } catch (e) {
      return errText(`image_metadata failed: ${String(e?.message || e)}`);
    }
  }
);

// ---------------------------------------------------------------------------
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  // (stderr only — stdout is the MCP channel)
  process.stderr.write(`[design-mcp] ready (root=${staticRoot})\n`);
}

// Allow `node server.js --selftest` without MCP (used by smoke-test).
if (process.argv.includes("--selftest")) {
  // no-op: smoke-test.mjs imports the helpers it needs directly.
} else if (fileURLToPath(import.meta.url) === path.resolve(process.argv[1] || "")) {
  main().catch((e) => {
    process.stderr.write(`[design-mcp] fatal: ${String(e?.stack || e)}\n`);
    process.exit(1);
  });
}

process.on("SIGTERM", async () => {
  try { await browser?.close(); } catch {}
  try { httpServer?.close(); } catch {}
  process.exit(0);
});
