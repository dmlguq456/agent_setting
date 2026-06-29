#!/usr/bin/env node
/**
 * Headless console check for a single HTML file (spec component ⑥ post-write hook).
 *
 *   node console-check.mjs <file.html>     — direct: print console errors, exit 2 if any
 *   node console-check.mjs --hook          — read PostToolUse JSON from stdin, filter to design
 *                                            HTML saves, then check. Silent unless errors found.
 *
 * Never blocks the save (the tool already ran); exit 2 + stderr just feeds the agent an alert.
 * Hard 10s timeout so a hanging page can't stall the session.
 */
import fs from "node:fs";
import path from "node:path";

// Only spend a browser launch on HTML that is plausibly a design artifact.
const DESIGN_RE = /(designs?\/|\/design\/|spec\/design|preview\.html$|slides?\.html$|03_components|scaffolds\/)/;

async function readStdin() {
  const chunks = [];
  for await (const c of process.stdin) chunks.push(c);
  return Buffer.concat(chunks).toString("utf8");
}

async function resolveTarget() {
  if (process.argv.includes("--hook")) {
    let payload = {};
    try { payload = JSON.parse(await readStdin() || "{}"); } catch { return null; }
    const ti = payload.tool_input || {};
    const fp = ti.file_path || ti.filePath || ti.path;
    if (!fp || !/\.html?$/i.test(fp) || !DESIGN_RE.test(fp)) return null; // not a design HTML → skip
    return fp;
  }
  return process.argv[2];
}

async function check(file) {
  const abs = path.resolve(file);
  if (!fs.existsSync(abs)) return { errors: [], skipped: "not found" };
  const { chromium } = await import("playwright");
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(String(e?.message || e)));
    page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
    page.on("requestfailed", (r) => errors.push(`request failed: ${r.url()}`));
    await page.goto("file://" + abs, { waitUntil: "load", timeout: 8000 });
    await page.waitForTimeout(250);
    return { errors };
  } finally {
    await browser.close();
  }
}

const target = await resolveTarget();
if (!target) process.exit(0); // nothing to check

let res;
try {
  res = await Promise.race([
    check(target),
    new Promise((_, rej) => setTimeout(() => rej(new Error("console-check timeout")), 10000)),
  ]);
} catch (e) {
  // Render tooling itself failed — stay silent in hook mode (don't nag on infra issues).
  if (!process.argv.includes("--hook")) console.error(String(e?.message || e));
  process.exit(0);
}

if (res.errors && res.errors.length) {
  process.stderr.write(
    `⚠️ design console-check: ${path.basename(target)} 에서 콘솔 에러 ${res.errors.length}건 — 턴 종료 전에 고치세요:\n` +
      res.errors.slice(0, 5).map((e) => "  • " + e).join("\n") + "\n"
  );
  process.exit(2); // feed alert back to the agent
}
process.exit(0);
