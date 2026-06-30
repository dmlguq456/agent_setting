#!/usr/bin/env node
/**
 * Adapter visual harness CLI.
 *
 * Renders one HTML file in headless Chromium, captures a screenshot, and prints
 * machine-readable status lines. Adapter-owned wrappers call this script; do
 * not project the whole design-mcp package as a runtime-native surface.
 */
import fs from "node:fs"
import path from "node:path"

function usage() {
  console.error("usage: visual-check.mjs <file.html> [--out <dir>] [--viewport <width>x<height>]")
}

function parseArgs(argv) {
  const args = { file: "", out: "", width: 1440, height: 900 }
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i]
    if (arg === "--out") {
      args.out = argv[++i] || ""
    } else if (arg === "--viewport") {
      const raw = argv[++i] || ""
      const match = raw.match(/^(\d+)x(\d+)$/)
      if (!match) throw new Error(`bad viewport: ${raw}`)
      args.width = Number(match[1])
      args.height = Number(match[2])
    } else if (!args.file) {
      args.file = arg
    } else {
      throw new Error(`unknown argument: ${arg}`)
    }
  }
  if (!args.file) throw new Error("missing file")
  return args
}

function printField(key, value) {
  process.stdout.write(`${key}=${String(value)}\n`)
}

let args
try {
  args = parseArgs(process.argv.slice(2))
} catch (error) {
  usage()
  console.error(String(error?.message || error))
  process.exit(64)
}

const file = path.resolve(args.file)
if (!fs.existsSync(file)) {
  printField("status", "unavailable")
  printField("reason", "file-not-found")
  printField("file", file)
  process.exit(66)
}
if (!/\.html?$/i.test(file)) {
  printField("status", "unavailable")
  printField("reason", "not-html")
  printField("file", file)
  process.exit(64)
}

const outDir = path.resolve(args.out || path.join(path.dirname(file), ".visual-harness"))
fs.mkdirSync(outDir, { recursive: true })
const screenshot = path.join(outDir, `${path.basename(file).replace(/\W+/g, "-")}.png`)

let chromium
try {
  ;({ chromium } = await import("playwright"))
} catch (error) {
  printField("status", "tool-contract")
  printField("reason", "playwright-unavailable")
  printField("file", file)
  printField("detail", String(error?.message || error).replace(/\n/g, " "))
  process.exit(69)
}

const browser = await chromium.launch({ headless: true })
const errors = []
try {
  const page = await browser.newPage()
  page.on("pageerror", (error) => errors.push(String(error?.message || error)))
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text())
  })
  page.on("requestfailed", (request) => errors.push(`request failed: ${request.url()}`))
  await page.setViewportSize({ width: args.width, height: args.height })
  await page.goto(`file://${file}`, { waitUntil: "load", timeout: 20000 })
  await page.waitForTimeout(250)
  await page.screenshot({ path: screenshot, fullPage: false, type: "png" })
  printField("status", errors.length ? "failed" : "ok")
  printField("file", file)
  printField("screenshot", screenshot)
  printField("viewport", `${args.width}x${args.height}`)
  printField("console_errors", errors.length)
  errors.slice(0, 5).forEach((error, index) => printField(`console_error_${index + 1}`, error.replace(/\n/g, " ")))
  process.exit(errors.length ? 2 : 0)
} finally {
  await browser.close()
}
