import path from "node:path"
import { fileURLToPath } from "node:url"
import { spawnSync, spawn } from "node:child_process"
import { existsSync, mkdirSync, writeFileSync, utimesSync } from "node:fs"

const pluginDir = path.dirname(fileURLToPath(import.meta.url))
const pluginRoot = path.resolve(pluginDir, "../../..")
const envRoot = process.env.AGENT_HOME ? path.resolve(process.env.AGENT_HOME) : ""
const isHarnessRoot = (candidate) =>
  candidate &&
  existsSync(path.join(candidate, "core", "CORE.md")) &&
  existsSync(path.join(candidate, "adapters", "opencode", "bin", "preflight.sh"))
const root = isHarnessRoot(envRoot) ? envRoot : pluginRoot
const preflight = path.join(root, "adapters", "opencode", "bin", "preflight.sh")
const designPattern = /(designs?\/|\/design\/|spec\/design|preview\.html$|slides?\.html$|03_components|scaffolds\/)/
// Capabilities that mutate the spec blueprint — must pass the prd.md read gate in a
// spec-backed cwd. Mirrors Claude's PreToolUse[Skill] spec-skill-gate scope.
const specGovernedCapabilities = new Set(["autopilot-code", "autopilot-spec"])
const seenLifecycle = new Set()

function baseDir(ctx) {
  return ctx.worktree || ctx.directory || process.cwd()
}

// Headless dispatch liveness probe support.
// When the OpenCode runtime starts a headless dispatch via dispatch-headless.py,
// it exports OPENCODE_DISPATCH_SLUG (and the dispatch interpreter passes the
// same env to the runtime child). Recording two artifacts at plugin init gives
// dispatch-liveness.py a secondary, cheap signal independent of the OpenCode
// SQLite session mtime:
//   * <agent-home>/.dispatch/plugin-load.<slug>.mark — created once at plugin
//     init, proving the plugin was actually loaded by the headless runtime.
//   * <agent-home>/.dispatch/logs/<slug>.heartbeat — touched on every
//     session.idle event (idle == turn done == still alive), so a stale or
//     crashed headless that never reaches idle will have an aging heartbeat.
// Both are best-effort: a plugin must never block a turn because it failed to
// record a liveness side-channel.
function dispatchSlug() {
  return process.env.OPENCODE_DISPATCH_SLUG || ""
}

function isWorkerSession() {
  return (
    (process.env.AGENT_SESSION_ROLE || "").toLowerCase() === "worker" ||
    process.env.AGENT_DISPATCH_CHILD === "1" ||
    Boolean(process.env.AGENT_DISPATCH_DEPTH) ||
    process.env.CLAUDE_CODE_CHILD_SESSION === "1" ||
    Boolean(process.env.OPENCODE_DISPATCH_SLUG) ||
    process.env.FLEET_TITLE_REFRESH === "1" ||
    process.env.MEM_DISTILL === "1"
  )
}

function touchHeartbeat(slug) {
  if (!slug) return
  try {
    const dispatchDir = path.join(root, ".dispatch")
    const logsDir = path.join(dispatchDir, "logs")
    mkdirSync(logsDir, { recursive: true })
    const hb = path.join(logsDir, `${slug}.heartbeat`)
    const now = new Date()
    try {
      utimesSync(hb, now, now)
    } catch {
      writeFileSync(hb, `${now.toISOString()}\n`, { encoding: "utf8" })
    }
  } catch {
    // best-effort; liveness side-channel must never throw
  }
}

function markPluginLoaded(slug) {
  if (!slug) return
  try {
    const dispatchDir = path.join(root, ".dispatch")
    mkdirSync(dispatchDir, { recursive: true })
    const marker = path.join(dispatchDir, `plugin-load.${slug}.mark`)
    writeFileSync(marker, `${new Date().toISOString()}\n`, { encoding: "utf8" })
  } catch {
    // best-effort
  }
}

function normalizeFile(ctx, file) {
  if (!file || file === "/dev/null") return ""
  if (path.isAbsolute(file)) return file
  return path.resolve(baseDir(ctx), file)
}

function patchFiles(ctx, patch) {
  if (!patch) return []
  const files = []
  const pattern = /^\*\*\* (?:Add|Update|Delete) File: (.+)$|^\*\*\* Move to: (.+)$/gm
  let match
  while ((match = pattern.exec(patch)) !== null) {
    const file = normalizeFile(ctx, match[1] || match[2])
    if (file) files.push(file)
  }
  return files
}

function targetFiles(ctx, tool, args) {
  const name = typeof tool === "string" ? tool : tool?.name || ""
  if (name === "write" || name === "edit") {
    return [normalizeFile(ctx, args.filePath || args.path || args.file)].filter(Boolean)
  }
  if (name === "apply_patch" || name === "patch") {
    return patchFiles(ctx, args.patchText || args.patch || "")
  }
  return []
}

function isDesignHtml(file) {
  return /\.html?$/i.test(file) && designPattern.test(file.replaceAll(path.sep, "/"))
}

function runPreflight(command, args) {
  const result = spawnSync(preflight, [command, ...args], {
    cwd: root,
    env: { ...process.env, AGENT_HOME: root },
    encoding: "utf8",
  })

  if (result.status !== 0) {
    const detail = [result.stdout, result.stderr].filter(Boolean).join("\n").trim()
    throw new Error(detail || `agent harness preflight failed: ${command}`)
  }
}

function spawnDetached(command, args) {
  // Fire-and-forget: must not block the user's turn. The child runs the
  // preflight session-end → no-tools distiller worker independently.
  try {
    const child = spawn(preflight, [command, ...args], {
      cwd: root,
      env: { ...process.env, AGENT_HOME: root },
      detached: true,
      stdio: "ignore",
    })
    child.unref()
  } catch {
    // best-effort; distillation is non-critical
  }
}

function collectPreflight(command, args) {
  const result = spawnSync(preflight, [command, ...args], {
    cwd: root,
    env: { ...process.env, AGENT_HOME: root },
    encoding: "utf8",
  })

  return [result.stdout, result.stderr].filter(Boolean).join("\n").trim()
}

function appendContext(output, text) {
  if (!text) return
  if (!Array.isArray(output.system)) output.system = []
  output.system.push(text)
}

export const AgentHarnessGuards = async (ctx) => {
  // Record plugin-load marker once per plugin init. In a headless dispatch the
  // runtime child inherits OPENCODE_DISPATCH_SLUG, so this proves the plugin
  // was loaded by the headless runtime (dispatch-liveness.py inspects it).
  markPluginLoaded(dispatchSlug())

  return ({
  event: async ({ event }) => {
    // session.idle fires after each turn (the session is waiting for the user).
    // Use it as the auto-distillation trigger; preflight session-end debounces
    // per session and the --pure worker never re-enters this plugin. Mirrors the
    // Claude SessionEnd + codex session-end detached distiller.
    if (event && event.type === "session.idle") {
      const sid = (event.properties && event.properties.sessionID) || "opencode-plugin"
      if (!isWorkerSession()) spawnDetached("session-end", [baseDir(ctx), sid])
      // Liveness side-channel: touch the heartbeat for the active dispatch slug
      // so dispatch-liveness.py can detect stale/crashed headless sessions even
      // when the OpenCode SQLite session mtime is inconclusive.
      touchHeartbeat(dispatchSlug())
    }
  },
  "experimental.chat.system.transform": async (input, output) => {
    const sid = input.sessionID || "opencode-plugin"
    const cwd = baseDir(ctx)
    if (isWorkerSession()) {
      // Dispatch prompts own explicit status/prompt-signal bootstrap;
      // memory/briefing/context stay main-only.
      return
    }
    if (!seenLifecycle.has(sid)) {
      seenLifecycle.add(sid)
      appendContext(output, collectPreflight("memory", [cwd]))
    }
    appendContext(output, collectPreflight("prompt-signal", [cwd, sid]))
    appendContext(output, collectPreflight("briefing", [cwd]))
  },
  "command.execute.before": async (input, output) => {
    // Spec read gate — deny autopilot-code/spec in a spec-backed cwd until prd.md
    // was actually read this session. Mirrors Claude's PreToolUse[Skill] hard deny:
    // preflight `capability` exits 2 when ungrounded, and runPreflight throws to
    // abort the command before its prompt is expanded.
    const name = (input.command || "").replace(/^\//, "")
    if (specGovernedCapabilities.has(name)) {
      runPreflight("capability", [name, baseDir(ctx), input.sessionID || "opencode-plugin"])
    }
  },
  "tool.execute.before": async (input, output) => {
    const files = targetFiles(ctx, input.tool || {}, output.args || {})
    for (const file of files) {
      runPreflight("write", [file, input.sessionID || "opencode-plugin"])
    }
  },
  "tool.execute.after": async (input, output) => {
    const args = input.args || output.args || {}
    const files = targetFiles(ctx, input.tool || {}, args)
    for (const file of files) {
      if (isDesignHtml(file)) runPreflight("design", [file])
    }
    // Read-grounding marker — record actual prd.md and core/*.md reads so the
    // spec gate and core-first adapter guard can pass. Mirrors Claude's
    // PostToolUse[Read] marker pair.
    // Non-blocking: a marker failure must never abort a successful read.
    const toolName = typeof input.tool === "string" ? input.tool : input.tool?.name || ""
    if (toolName === "read") {
      const readFile = normalizeFile(ctx, args.filePath || args.path || args.file)
      if (readFile) collectPreflight("read", [readFile, input.sessionID || "opencode-plugin"])
    }
  },
  })
}
