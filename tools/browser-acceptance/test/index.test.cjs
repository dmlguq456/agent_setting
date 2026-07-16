"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const lib = require("..");

/** Minimal Playwright-compatible fakes (BA-5: unit gate needs no browser). */
class FakeLocator {
  constructor(page, chain) {
    this.page = page;
    this.chain = chain;
  }
  locator(selector) {
    return new FakeLocator(this.page, [...this.chain, selector]);
  }
  key() {
    return this.chain.join(" >> ");
  }
  async count() {
    this.page.queries.push(this.key());
    return this.page.dom.get(this.key())?.count ?? 0;
  }
  async textContent() {
    this.page.queries.push(this.key());
    return this.page.dom.get(this.key())?.text ?? null;
  }
  async isVisible() {
    this.page.queries.push(this.key());
    return this.page.dom.get(this.key())?.visible ?? false;
  }
  async getAttribute(name) {
    return this.page.dom.get(this.key())?.attrs?.[name] ?? null;
  }
  async click() {
    const node = this.page.dom.get(this.key());
    if (node?.onClick) node.onClick(node);
  }
}

class FakePage {
  constructor() {
    this.dom = new Map();
    this.queries = [];
    this.gotoCalls = [];
    this.waitCalls = [];
    this.listeners = new Map();
    this.mountedSelectors = new Set();
    this.evaluations = [];
    this.evaluateResults = [];
    this.scriptTags = [];
  }
  locator(selector) {
    return new FakeLocator(this, [selector]);
  }
  async goto(url, opts) {
    this.gotoCalls.push({ url, opts });
  }
  async waitForSelector(selector, opts) {
    this.waitCalls.push({ selector, opts });
    if (!this.mountedSelectors.has(selector)) {
      throw new Error(`Timeout waiting for ${selector}`);
    }
  }
  on(event, handler) {
    const list = this.listeners.get(event) || [];
    list.push(handler);
    this.listeners.set(event, list);
  }
  off(event, handler) {
    const list = (this.listeners.get(event) || []).filter((entry) => entry !== handler);
    this.listeners.set(event, list);
  }
  emit(event, payload) {
    for (const handler of this.listeners.get(event) || []) handler(payload);
  }
  async evaluate(script) {
    this.evaluations.push(String(script));
    return this.evaluateResults.shift();
  }
  async addScriptTag(opts) {
    this.scriptTags.push(opts);
  }
  async screenshot(opts) {
    fs.writeFileSync(opts.path, "png");
  }
}

test("CJS entry: require works and exposes the six primitives", () => {
  for (const name of ["gotoAndWaitMount", "scoped", "openDisclosure", "captureConsole", "runScopedAxe", "writeEvidence"]) {
    assert.equal(typeof lib[name], "function", name);
  }
  const source = fs.readFileSync(require.resolve(".."), "utf8");
  assert.doesNotMatch(source, /^await /m, "no top-level await (BA-1)");
});

test("gotoAndWaitMount waits for the root and fails structured on no-mount", async () => {
  const page = new FakePage();
  page.mountedSelectors.add("#reader-root");
  const outcome = await lib.gotoAndWaitMount(page, "http://app/reader", "#reader-root");
  assert.equal(outcome.mounted, true);
  assert.equal(page.gotoCalls.length, 1);
  assert.equal(page.waitCalls[0].selector, "#reader-root");
  assert.equal(page.waitCalls[0].opts.state, "visible");

  await assert.rejects(
    lib.gotoAndWaitMount(page, "http://app/other", "#missing-root", { timeout: 10 }),
    (error) => error.code === "mount-timeout"
  );
});

test("scoped exposes only scope-bound queries", async () => {
  const page = new FakePage();
  page.dom.set("#main >> .row", { count: 2, visible: true, text: "row" });
  const scope = lib.scoped(page, "#main");
  assert.equal(await scope.count(".row"), 2);
  assert.ok(page.queries.every((query) => query.startsWith("#main >> ")), "every query chains under the scope");
  assert.equal(scope.page, undefined, "no page escape hatch");
  assert.throws(() => lib.scoped(page, ""), (error) => error.code === "scope-required");
});

test("openDisclosure opens a collapsed group once and is idempotent", async () => {
  const page = new FakePage();
  const node = {
    attrs: { "aria-expanded": "false" },
    onClick: (self) => {
      self.attrs["aria-expanded"] = "true";
    },
  };
  page.dom.set("#hubs-toggle", node);
  const first = await lib.openDisclosure(page, "#hubs-toggle");
  assert.deepEqual({ opened: first.opened, already: first.alreadyExpanded }, { opened: true, already: false });
  const second = await lib.openDisclosure(page, "#hubs-toggle");
  assert.deepEqual({ opened: second.opened, already: second.alreadyExpanded }, { opened: false, already: true });
});

test("openDisclosure fails structured when expansion never happens", async () => {
  const page = new FakePage();
  page.dom.set("#stuck", { attrs: { "aria-expanded": "false" }, onClick: () => {} });
  await assert.rejects(
    lib.openDisclosure(page, "#stuck", { timeout: 60 }),
    (error) => error.code === "disclosure-timeout"
  );
});

test("captureConsole collects error console + pageerror and stops cleanly", () => {
  const page = new FakePage();
  const capture = lib.captureConsole(page);
  page.emit("console", { type: () => "error", text: () => "boom" });
  page.emit("console", { type: () => "log", text: () => "noise" });
  page.emit("pageerror", new Error("crashed"));
  const collected = capture.stop();
  assert.equal(collected.length, 2);
  assert.deepEqual(collected.map((entry) => entry.kind), ["console", "pageerror"]);
  page.emit("pageerror", new Error("after stop"));
  assert.equal(capture.errors.length, 2, "stop() detaches listeners");
});

test("runScopedAxe injects axe when missing and stays scope-bound", async () => {
  const page = new FakePage();
  page.evaluateResults = [false, { violations: [{ id: "contrast", impact: "serious", help: "x", nodes: [1, 2] }] }];
  const outcome = await lib.runScopedAxe(page, { scope: "#reader", axeSource: "window.axe = {}" });
  assert.equal(page.scriptTags.length, 1, "axe source injected");
  assert.ok(page.evaluations[1].includes('"#reader"'), "axe runs against the scope node");
  assert.equal(outcome.violations[0].id, "contrast");

  page.evaluateResults = [false];
  await assert.rejects(
    lib.runScopedAxe(page, { scope: "#reader" }),
    (error) => error.code === "axe-source-required"
  );
});

test("runScopedAxe fails structured when the scope is absent", async () => {
  const page = new FakePage();
  page.evaluateResults = [true, { __missing_scope: true }];
  await assert.rejects(
    lib.runScopedAxe(page, { scope: "#gone" }),
    (error) => error.code === "scope-missing"
  );
});

test("writeEvidence aggregates a deterministic verdict and fails closed on schema gaps", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "ba-evidence-"));
  const result = lib.createResult({ url: "http://app/reader", scope: "#reader" });
  result.checks.push({ id: "readonly-controls", verdict: "PASS" });
  const pass = lib.writeEvidence(dir, result);
  assert.equal(pass.verdict, "PASS");
  const onDisk = JSON.parse(fs.readFileSync(pass.path, "utf8"));
  assert.equal(onDisk.schema_version, lib.SCHEMA_VERSION);
  assert.ok(onDisk.finished_at);

  result.console_errors.push({ kind: "pageerror", text: "boom" });
  assert.equal(lib.writeEvidence(dir, result).verdict, "FAIL");

  const broken = { ...result };
  delete broken.axe;
  assert.throws(() => lib.writeEvidence(dir, broken), (error) => error.code === "result-schema-invalid");
  assert.throws(
    () => lib.writeEvidence(dir, { ...result, checks: [{ id: "x", verdict: "MAYBE" }] }),
    (error) => error.code === "result-schema-invalid"
  );
  assert.throws(() => lib.createResult({}), (error) => error.code === "result-init-invalid");
  fs.rmSync(dir, { recursive: true, force: true });
});

test("takeScreenshot writes into the evidence dir with a safe name", async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "ba-shot-"));
  const page = new FakePage();
  const file = await lib.takeScreenshot(page, dir, "reader view/1");
  assert.equal(file, "reader_view_1.png");
  assert.ok(fs.existsSync(path.join(dir, file)));
  fs.rmSync(dir, { recursive: true, force: true });
});
