/**
 * Smoke test for the Design MCP server — validates §2.5 acceptance criteria by
 * spawning the real server over stdio and calling its tools as a client would.
 *
 *   [x] preview → screenshot → view_image round-trips (image bytes returned)
 *   [x] getConsoleLogs catches an intentional JS error
 *   [x] eval_js returns getComputedStyle(el).color
 *   [x] screenshot.steps captures two states (before/after a click)
 */
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "design-mcp-smoke-"));

const HTML = `<!doctype html>
<html><head><meta charset="utf-8"><title>Smoke</title>
<style>#box{color:rgb(34,197,94);font-size:24px}</style></head>
<body>
  <div id="box">hello</div>
  <button id="btn" onclick="document.getElementById('box').textContent='clicked'">go</button>
  <script>throw new Error("intentional-smoke-error");</script>
</body></html>`;
fs.writeFileSync(path.join(tmp, "page.html"), HTML);

function parse(res) {
  const t = res.content.find((c) => c.type === "text");
  return t ? JSON.parse(t.text) : null;
}
const checks = [];
function check(name, ok, detail = "") {
  checks.push({ name, ok, detail });
  console.log(`${ok ? "PASS" : "FAIL"}  ${name}${detail ? "  — " + detail : ""}`);
}

const transport = new StdioClientTransport({
  command: "node",
  args: [path.join(here, "server.js")],
  env: { ...process.env, DESIGN_ROOT: tmp },
});
const client = new Client({ name: "smoke", version: "1.0.0" });

try {
  await client.connect(transport);

  const tools = (await client.listTools()).tools.map((t) => t.name).sort();
  const expected = ["eval_js", "getConsoleLogs", "image_metadata", "preview", "screenshot", "view_image"];
  check("lists all 6 tools", expected.every((e) => tools.includes(e)), tools.join(","));

  const prev = parse(await client.callTool({ name: "preview", arguments: { path: "page.html" } }));
  check("preview loads page", prev?.ok === true && prev?.title === "Smoke", prev?.title);

  const logs = parse(await client.callTool({ name: "getConsoleLogs", arguments: {} }));
  check(
    "getConsoleLogs catches JS error",
    logs.errors.some((e) => e.includes("intentional-smoke-error")),
    `${logs.errors.length} error(s)`
  );

  const color = parse(
    await client.callTool({
      name: "eval_js",
      arguments: { code: "getComputedStyle(document.getElementById('box')).color" },
    })
  );
  check("eval_js returns computed color", color?.result === "rgb(34, 197, 94)", color?.result);

  const shot = parse(
    await client.callTool({
      name: "screenshot",
      arguments: {
        savePath: path.join(tmp, "state.png"),
        steps: [{ delayMs: 50 }, { code: "document.getElementById('btn').click()", delayMs: 100 }],
      },
    })
  );
  const twoFiles = shot?.files?.length === 2 && shot.files.every((f) => fs.existsSync(f));
  check("screenshot.steps captures two states", twoFiles, (shot?.files || []).map((f) => path.basename(f)).join(","));

  const img = await client.callTool({ name: "view_image", arguments: { path: shot.files[0] } });
  const hasImage = img.content?.some((c) => c.type === "image" && c.data?.length > 100);
  check("view_image returns image bytes", hasImage);

  const meta = parse(await client.callTool({ name: "image_metadata", arguments: { path: shot.files[0] } }));
  check("image_metadata returns dimensions", meta?.width > 0 && meta?.height > 0, `${meta?.width}x${meta?.height}`);
} catch (e) {
  check("server connected & ran", false, String(e?.message || e));
} finally {
  try { await client.close(); } catch {}
  try { fs.rmSync(tmp, { recursive: true, force: true }); } catch {}
}

const failed = checks.filter((c) => !c.ok);
console.log(`\n${checks.length - failed.length}/${checks.length} checks passed`);
process.exit(failed.length ? 1 : 0);
