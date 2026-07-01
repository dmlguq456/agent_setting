import path from "node:path"
import { fileURLToPath } from "node:url"
import { spawnSync, spawn } from "node:child_process"
import { existsSync } from "node:fs"

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
const promptBySession = new Map()

function baseDir(ctx) {
  return ctx.worktree || ctx.directory || process.cwd()
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

function textFromParts(parts) {
  if (!Array.isArray(parts)) return ""
  return parts
    .filter((part) => part && part.type === "text" && typeof part.text === "string")
    .map((part) => part.text)
    .join("\n")
    .trim()
}

function appendContext(output, text) {
  if (!text) return
  if (!Array.isArray(output.system)) output.system = []
  output.system.push(text)
}

export const AgentHarnessGuards = async (ctx) => ({
  event: async ({ event }) => {
    // session.idle fires after each turn (the session is waiting for the user).
    // Use it as the auto-distillation trigger; preflight session-end debounces
    // per session and the --pure worker never re-enters this plugin. Mirrors the
    // Claude SessionEnd + codex session-end detached distiller.
    if (event && event.type === "session.idle") {
      const sid = (event.properties && event.properties.sessionID) || "opencode-plugin"
      spawnDetached("session-end", [baseDir(ctx), sid])
    }
  },
  "chat.message": async (input, output) => {
    const prompt = textFromParts(output.parts)
    if (prompt) promptBySession.set(input.sessionID || "opencode-plugin", prompt)
  },
  "experimental.chat.system.transform": async (input, output) => {
    const sid = input.sessionID || "opencode-plugin"
    const cwd = baseDir(ctx)
    if (!seenLifecycle.has(sid)) {
      seenLifecycle.add(sid)
      appendContext(output, collectPreflight("start", [cwd, sid]))
      appendContext(output, collectPreflight("memory", [cwd]))
    }
    appendContext(output, collectPreflight("prompt-signal", [cwd, sid]))
    appendContext(output, collectPreflight("mode", [cwd, sid]))
    const prompt = promptBySession.get(sid) || ""
    if (prompt) appendContext(output, collectPreflight("recall", [prompt, cwd]))
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
    // Spec read-grounding marker — record an actual prd.md read so the capability
    // gate above can pass. Mirrors Claude's PostToolUse[Read] spec-read-marker.
    // Non-blocking: a marker failure must never abort a successful read.
    const toolName = typeof input.tool === "string" ? input.tool : input.tool?.name || ""
    if (toolName === "read") {
      const readFile = normalizeFile(ctx, args.filePath || args.path || args.file)
      if (readFile) collectPreflight("read", [readFile, input.sessionID || "opencode-plugin"])
    }
  },
})
