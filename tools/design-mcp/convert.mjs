#!/usr/bin/env node
/**
 * Output converters (spec component ⑤).
 *
 *   node convert.mjs pdf    <input.html> [out.pdf]                — print-to-PDF (deck: 1 slide = 1 page)
 *   node convert.mjs bundle <input.html> [out.html]              — inline all local assets → 1 offline file
 *   node convert.mjs pptx   <input.html> [out.pptx] [--selector .slide]
 *                                                                — per-slide full-bleed PNG + speaker notes
 *
 * PDF/PPTX need Playwright (a dep). PPTX needs pptxgenjs (a dep). Bundle is pure Node.
 */
import fs from "node:fs";
import path from "node:path";

const [, , cmd, input, ...rest] = process.argv;
if (!cmd || !input) {
  console.error("usage: convert.mjs <pdf|bundle|pptx> <input.html> [output] [--selector .slide]");
  process.exit(2);
}
const inPath = path.resolve(input);
if (!fs.existsSync(inPath)) { console.error("input not found: " + inPath); process.exit(2); }
const inDir = path.dirname(inPath);
const out = rest.find((a) => !a.startsWith("--"));
const selArg = rest.find((a) => a.startsWith("--selector"));
const selector = selArg ? selArg.split("=")[1] || rest[rest.indexOf(selArg) + 1] : ".slide";

const MIME = { ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
  ".webp": "image/webp", ".svg": "image/svg+xml", ".woff": "font/woff", ".woff2": "font/woff2", ".ttf": "font/ttf" };
const isRemote = (u) => /^(https?:|data:|#|mailto:)/.test(u);

function dataUri(file) {
  const ext = path.extname(file).toLowerCase();
  const mime = MIME[ext] || "application/octet-stream";
  return `data:${mime};base64,${fs.readFileSync(file).toString("base64")}`;
}
function inlineCssUrls(css, baseDir) {
  return css.replace(/url\(\s*['"]?([^'")]+)['"]?\s*\)/g, (m, u) => {
    if (isRemote(u)) return m;
    const f = path.resolve(baseDir, u.split("?")[0].split("#")[0]);
    return fs.existsSync(f) ? `url(${dataUri(f)})` : m;
  });
}

async function doBundle() {
  let html = fs.readFileSync(inPath, "utf8");
  // <link rel="stylesheet" href="local.css"> → <style>…</style>
  html = html.replace(/<link\b[^>]*?rel=["']stylesheet["'][^>]*?>/gi, (tag) => {
    const m = tag.match(/href=["']([^"']+)["']/i);
    if (!m || isRemote(m[1])) return tag;
    const f = path.resolve(inDir, m[1].split("?")[0]);
    if (!fs.existsSync(f)) return tag;
    return `<style>\n${inlineCssUrls(fs.readFileSync(f, "utf8"), path.dirname(f))}\n</style>`;
  });
  // <script src="local.js"> → inline
  html = html.replace(/<script\b([^>]*?)\ssrc=["']([^"']+)["']([^>]*)>\s*<\/script>/gi, (tag, pre, src, post) => {
    if (isRemote(src)) return tag;
    const f = path.resolve(inDir, src.split("?")[0]);
    if (!fs.existsSync(f)) return tag;
    return `<script${pre}${post}>\n${fs.readFileSync(f, "utf8")}\n</script>`;
  });
  // <img src="local"> and inline style url() → data URI
  html = html.replace(/(<img\b[^>]*?\ssrc=)["']([^"']+)["']/gi, (m, pre, src) => {
    if (isRemote(src)) return m;
    const f = path.resolve(inDir, src.split("?")[0]);
    return fs.existsSync(f) ? `${pre}"${dataUri(f)}"` : m;
  });
  html = html.replace(/<style\b[^>]*>([\s\S]*?)<\/style>/gi, (m, css) => m.replace(css, inlineCssUrls(css, inDir)));
  const dest = path.resolve(out || inPath.replace(/\.html?$/i, ".bundle.html"));
  fs.writeFileSync(dest, html);
  console.log("bundle → " + dest + ` (${(html.length / 1024).toFixed(0)} KB, offline-ready)`);
}

async function doPdf() {
  const { chromium } = await import("playwright");
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto("file://" + inPath, { waitUntil: "load" });
  const dest = path.resolve(out || inPath.replace(/\.html?$/i, ".pdf"));
  await p.pdf({ path: dest, printBackground: true, preferCSSPageSize: true });
  await b.close();
  console.log("pdf → " + dest);
}

async function doPptx() {
  const { chromium } = await import("playwright");
  let pptxgen;
  try { pptxgen = (await import("pptxgenjs")).default; }
  catch { console.error("pptxgenjs missing. Run: (cd ~/.claude/tools/design-mcp && npm i pptxgenjs)"); process.exit(2); }

  const b = await chromium.launch();
  const p = await b.newPage();
  await p.setViewportSize({ width: 1920, height: 1080 });
  await p.goto("file://" + inPath, { waitUntil: "load" });

  const count = await p.$$eval(selector, (els) => els.length).catch(() => 0);
  const notes = await p.evaluate(() => {
    const el = document.getElementById("speaker-notes");
    try { return el ? JSON.parse(el.textContent || "[]") : []; } catch { return []; }
  });

  const shots = [];
  const tmp = fs.mkdtempSync(path.join(path.resolve("."), ".pptx-"));
  if (count > 0) {
    for (let i = 0; i < count; i++) {
      await p.evaluate(({ sel, idx }) => {
        const deck = document.querySelector(".deck");
        if (deck) deck.style.transform = "none";
        const all = document.querySelectorAll(sel);
        all.forEach((s, k) => s.classList.toggle("active", k === idx));
      }, { sel: selector, idx: i });
      await p.waitForTimeout(120);
      const target = (await p.$(".deck")) || (await p.$(selector + ".active")) || p;
      const f = path.join(tmp, `s${String(i + 1).padStart(2, "0")}.png`);
      await (target.screenshot ? target.screenshot({ path: f }) : p.screenshot({ path: f }));
      shots.push(f);
    }
  } else {
    const f = path.join(tmp, "s01.png");
    await p.screenshot({ path: f, fullPage: true });
    shots.push(f);
  }
  await b.close();

  const pptx = new pptxgen();
  pptx.defineLayout({ name: "DECK16x9", width: 13.333, height: 7.5 });
  pptx.layout = "DECK16x9";
  shots.forEach((f, i) => {
    const slide = pptx.addSlide();
    slide.addImage({ path: f, x: 0, y: 0, w: 13.333, h: 7.5 });
    if (notes[i]) slide.addNotes(String(notes[i]));
  });
  const dest = path.resolve(out || inPath.replace(/\.html?$/i, ".pptx"));
  await pptx.writeFile({ fileName: dest });
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log(`pptx → ${dest} (${shots.length} slide${shots.length > 1 ? "s" : ""}, screenshot mode)`);
}

const map = { pdf: doPdf, bundle: doBundle, pptx: doPptx };
if (!map[cmd]) { console.error("unknown command: " + cmd); process.exit(2); }
map[cmd]().catch((e) => { console.error(String(e?.stack || e)); process.exit(1); });
