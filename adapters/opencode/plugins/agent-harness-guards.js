import path from "node:path"
import { fileURLToPath } from "node:url"
import { spawnSync } from "node:child_process"

const pluginDir = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(pluginDir, "../../..")
const preflight = path.join(root, "adapters", "opencode", "bin", "preflight.sh")

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
  const name = tool.name || ""
  if (name === "write" || name === "edit") {
    return [normalizeFile(ctx, args.filePath || args.path || args.file)].filter(Boolean)
  }
  if (name === "apply_patch" || name === "patch") {
    return patchFiles(ctx, args.patchText || args.patch || "")
  }
  return []
}

function runPreflight(file, sessionID) {
  const result = spawnSync(preflight, ["write", file, sessionID || "opencode-plugin"], {
    cwd: root,
    env: { ...process.env, AGENT_HOME: process.env.AGENT_HOME || root },
    encoding: "utf8",
  })

  if (result.status !== 0) {
    const detail = [result.stdout, result.stderr].filter(Boolean).join("\n").trim()
    throw new Error(detail || `agent harness preflight failed for ${file}`)
  }
}

export const AgentHarnessGuards = async (ctx) => ({
  "tool.execute.before": async (input, output) => {
    const files = targetFiles(ctx, input.tool || {}, output.args || {})
    for (const file of files) {
      runPreflight(file, input.sessionID)
    }
  },
})
