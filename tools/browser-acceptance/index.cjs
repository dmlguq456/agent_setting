"use strict";
/**
 * browser-acceptance — injected-page acceptance primitives (spec/browser-acceptance BA-1~6).
 *
 * CJS-safe: no top-level await; every async lives inside an exported function
 * (BA-1).  Zero dependencies: the caller injects a Playwright-compatible
 * `page` and, for axe runs, the axe-core source; the resolvers below only
 * locate an existing install and fail with explicit guidance (BA-2).
 *
 * The library collects deterministic evidence (console, scoped axe,
 * screenshots, result JSON).  What to check and what a failure means stays a
 * caller judgment (PRD §3).
 */

const fs = require("node:fs");
const path = require("node:path");

const SCHEMA_VERSION = 1;
const REQUIRED_RESULT_FIELDS = ["schema_version", "url", "scope", "started_at", "checks", "console_errors", "axe", "screenshots"];
const DESIGN_MCP_DIR = path.join(__dirname, "..", "design-mcp");

function nowIso() {
  return new Date().toISOString();
}

function structuredError(code, message) {
  const error = new Error(`${code}: ${message}`);
  error.code = code;
  return error;
}

/** BA-3 ①: navigate, then explicitly wait for the app root to mount. */
async function gotoAndWaitMount(page, url, rootSelector, opts = {}) {
  const timeout = opts.timeout ?? 15000;
  const waitUntil = opts.waitUntil ?? "domcontentloaded";
  const started = Date.now();
  await page.goto(url, { waitUntil, timeout });
  try {
    await page.waitForSelector(rootSelector, { state: "visible", timeout });
  } catch (cause) {
    throw structuredError(
      "mount-timeout",
      `root ${JSON.stringify(rootSelector)} not visible within ${timeout}ms after ${url} (${cause.message})`
    );
  }
  return { url, rootSelector, mounted: true, elapsed_ms: Date.now() - started };
}

/**
 * BA-3 ②: scope-bound query surface.  Deliberately exposes no whole-page
 * query method and no `page` reference — every lookup chains under the scope.
 */
function scoped(page, scopeSelector) {
  if (!scopeSelector || typeof scopeSelector !== "string") {
    throw structuredError("scope-required", "scoped(page, scopeSelector) requires a non-empty selector");
  }
  const root = () => page.locator(scopeSelector);
  return {
    scopeSelector,
    locator: (selector) => root().locator(selector),
    count: (selector) => root().locator(selector).count(),
    textContent: (selector) => root().locator(selector).textContent(),
    isVisible: (selector) => root().locator(selector).isVisible(),
  };
}

/** BA-3 ③: idempotently open a collapsed disclosure and wait for expansion. */
async function openDisclosure(page, triggerSelector, opts = {}) {
  const timeout = opts.timeout ?? 5000;
  const trigger = page.locator(triggerSelector);
  const expanded = await trigger.getAttribute("aria-expanded");
  if (expanded === "true") {
    return { triggerSelector, opened: false, alreadyExpanded: true };
  }
  await trigger.click();
  const deadline = Date.now() + timeout;
  for (;;) {
    if ((await trigger.getAttribute("aria-expanded")) === "true") break;
    if (opts.expandedSelector && (await page.locator(opts.expandedSelector).isVisible())) break;
    if (Date.now() >= deadline) {
      throw structuredError("disclosure-timeout", `${triggerSelector} did not report aria-expanded=true within ${timeout}ms`);
    }
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  return { triggerSelector, opened: true, alreadyExpanded: false };
}

/** BA-3 ④: collect page errors and console errors until stopped. */
function captureConsole(page) {
  const errors = [];
  const onConsole = (message) => {
    if (message.type() === "error") {
      errors.push({ kind: "console", text: message.text(), at: nowIso() });
    }
  };
  const onPageError = (error) => {
    errors.push({ kind: "pageerror", text: String(error && error.message ? error.message : error), at: nowIso() });
  };
  page.on("console", onConsole);
  page.on("pageerror", onPageError);
  return {
    errors,
    stop() {
      page.off("console", onConsole);
      page.off("pageerror", onPageError);
      return errors.slice();
    },
  };
}

/** BA-3 ⑤: run injected axe-core against the scope only. */
async function runScopedAxe(page, opts = {}) {
  const scope = opts.scope;
  if (!scope) throw structuredError("scope-required", "runScopedAxe requires opts.scope");
  let source = opts.axeSource;
  if (!source && opts.axeSourcePath) source = fs.readFileSync(opts.axeSourcePath, "utf8");
  const hasAxe = await page.evaluate("typeof window.axe !== 'undefined'");
  if (!hasAxe) {
    if (!source) {
      throw structuredError("axe-source-required", "window.axe is absent; pass opts.axeSource or opts.axeSourcePath (see resolveAxeSource())");
    }
    await page.addScriptTag({ content: source });
  }
  const raw = await page.evaluate(
    `(async () => {
       const node = document.querySelector(${JSON.stringify(scope)});
       if (!node) return { __missing_scope: true };
       const outcome = await window.axe.run(node);
       return { violations: outcome.violations.map((v) => ({
         id: v.id, impact: v.impact, help: v.help, nodes: v.nodes.length,
       })) };
     })()`
  );
  if (raw && raw.__missing_scope) {
    throw structuredError("scope-missing", `axe scope not found in document: ${scope}`);
  }
  return { scope, violations: (raw && raw.violations) || [] };
}

/** Evidence skeleton for one acceptance pass (BA-4). */
function createResult(init = {}) {
  if (!init.url || !init.scope) {
    throw structuredError("result-init-invalid", "createResult requires {url, scope}");
  }
  return {
    schema_version: SCHEMA_VERSION,
    url: init.url,
    scope: init.scope,
    started_at: nowIso(),
    checks: [],
    console_errors: [],
    axe: { violations: [] },
    screenshots: [],
  };
}

/** Screenshot into the evidence dir; returns the relative path to record. */
async function takeScreenshot(page, dir, name) {
  fs.mkdirSync(dir, { recursive: true });
  const file = `${name.replace(/[^A-Za-z0-9._-]/g, "_")}.png`;
  await page.screenshot({ path: path.join(dir, file) });
  return file;
}

/**
 * BA-4: validate the result contract, aggregate the deterministic verdict
 * (zero failures = PASS), and write result.json.  Missing fields fail closed.
 */
function writeEvidence(dir, result) {
  for (const field of REQUIRED_RESULT_FIELDS) {
    if (!(field in result)) {
      throw structuredError("result-schema-invalid", `missing field: ${field}`);
    }
  }
  const failedChecks = result.checks.filter((check) => check.verdict !== "PASS");
  for (const check of result.checks) {
    if (!check.id || !["PASS", "FAIL"].includes(check.verdict)) {
      throw structuredError("result-schema-invalid", `check needs {id, verdict PASS|FAIL}: ${JSON.stringify(check)}`);
    }
  }
  const finished = {
    ...result,
    finished_at: nowIso(),
    verdict:
      failedChecks.length === 0 && result.console_errors.length === 0 && result.axe.violations.length === 0
        ? "PASS"
        : "FAIL",
  };
  fs.mkdirSync(dir, { recursive: true });
  const target = path.join(dir, "result.json");
  fs.writeFileSync(target, JSON.stringify(finished, null, 2) + "\n", "utf8");
  return { path: target, verdict: finished.verdict };
}

/** BA-2 resolvers: locate an existing install, never vendor one. */
function resolveFrom(request) {
  const candidates = [process.cwd(), DESIGN_MCP_DIR];
  for (const base of candidates) {
    try {
      return require.resolve(request, { paths: [base] });
    } catch {
      /* try next candidate */
    }
  }
  return null;
}

function resolvePlaywright() {
  const resolved = resolveFrom("playwright");
  if (!resolved) {
    throw structuredError(
      "playwright-unresolved",
      `no playwright install found from ${process.cwd()} or ${DESIGN_MCP_DIR}; install it in the app repo or pass your own page`
    );
  }
  return require(resolved);
}

function resolveAxeSource() {
  const resolved = resolveFrom("axe-core/axe.min.js") || resolveFrom("axe-core/axe.js");
  if (!resolved) {
    throw structuredError(
      "axe-unresolved",
      `no axe-core install found from ${process.cwd()} or ${DESIGN_MCP_DIR}; install axe-core in the app repo or pass opts.axeSource`
    );
  }
  return resolved;
}

module.exports = {
  SCHEMA_VERSION,
  gotoAndWaitMount,
  scoped,
  openDisclosure,
  captureConsole,
  runScopedAxe,
  createResult,
  takeScreenshot,
  writeEvidence,
  resolvePlaywright,
  resolveAxeSource,
};
