#!/usr/bin/env node
/**
 * Runtime-neutral Playwright browser fetch CLI.
 *
 * Adapter-owned wrappers call this helper to realize the portable
 * material/browser-fetch contract without exposing Claude-native WebFetch or
 * hook surfaces.
 */
import fs from "node:fs"
import path from "node:path"

function usage() {
  console.error("usage: browser-fetch.mjs [--check] <url> [--out <dir>] [--timeout <ms>] [--viewport <width>x<height>] [--text-limit <chars>]")
}

function printField(key, value) {
  process.stdout.write(`${key}=${String(value).replace(/\n/g, " ")}\n`)
}

function parseArgs(argv) {
  const args = {
    check: false,
    url: "",
    out: "",
    timeout: 30000,
    width: 1920,
    height: 1080,
    textLimit: 50000,
  }
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i]
    if (arg === "--check") {
      args.check = true
    } else if (arg === "--out") {
      args.out = argv[++i] || ""
    } else if (arg === "--timeout") {
      const raw = argv[++i] || ""
      args.timeout = Number(raw)
      if (!Number.isInteger(args.timeout) || args.timeout < 1000) throw new Error(`bad timeout: ${raw}`)
    } else if (arg === "--viewport") {
      const raw = argv[++i] || ""
      const match = raw.match(/^(\d+)x(\d+)$/)
      if (!match) throw new Error(`bad viewport: ${raw}`)
      args.width = Number(match[1])
      args.height = Number(match[2])
    } else if (arg === "--text-limit") {
      const raw = argv[++i] || ""
      args.textLimit = Number(raw)
      if (!Number.isInteger(args.textLimit) || args.textLimit < 0) throw new Error(`bad text limit: ${raw}`)
    } else if (!args.url) {
      args.url = arg
    } else {
      throw new Error(`unknown argument: ${arg}`)
    }
  }
  if (!args.url) throw new Error("missing url")
  return args
}

let args
try {
  args = parseArgs(process.argv.slice(2))
} catch (error) {
  usage()
  console.error(String(error?.message || error))
  process.exit(64)
}

let url
try {
  url = new URL(args.url)
} catch {
  printField("status", "unavailable")
  printField("reason", "bad-url")
  printField("url", args.url)
  process.exit(65)
}
if (url.protocol !== "http:" && url.protocol !== "https:") {
  printField("status", "unavailable")
  printField("reason", "unsupported-url-scheme")
  printField("url", args.url)
  process.exit(65)
}

let chromium
try {
  ;({ chromium } = await import("playwright"))
} catch (error) {
  printField("status", "tool-contract")
  printField("reason", "playwright-unavailable")
  printField("url", url.href)
  printField("detail", String(error?.message || error).replace(/\n/g, " "))
  process.exit(69)
}

if (args.check) {
  printField("status", "ok")
  printField("check", "playwright-import")
  printField("url", url.href)
  process.exit(0)
}

const outDir = path.resolve(args.out || path.join(process.cwd(), ".browser-fetch"))
const screenshotsDir = path.join(outDir, "screenshots")
const extractsDir = path.join(outDir, "browser_extracts")
fs.mkdirSync(screenshotsDir, { recursive: true })
fs.mkdirSync(extractsDir, { recursive: true })

const slug = `${url.hostname}${url.pathname || ""}`.replace(/\W+/g, "-").replace(/^-|-$/g, "") || "page"
const screenshot = path.join(screenshotsDir, `${slug}.png`)
const textFile = path.join(extractsDir, `${slug}.txt`)

const browser = await chromium.launch({
  headless: true,
  args: ["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"],
})
let exitCode = 0
try {
  const ctx = await browser.newContext({
    userAgent: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    viewport: { width: args.width, height: args.height },
    locale: "en-US",
  })
  await ctx.addInitScript("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
  const page = await ctx.newPage()
  const response = await page.goto(url.href, { waitUntil: "domcontentloaded", timeout: args.timeout })
  await page.waitForTimeout(750)
  const bodyText = await page.locator("body").innerText({ timeout: Math.min(args.timeout, 10000) }).catch(() => "")
  const sample = bodyText.slice(0, args.textLimit)
  await page.screenshot({ path: screenshot, fullPage: true, type: "png" })
  fs.writeFileSync(textFile, sample)
  const statusCode = response ? response.status() : 0
  const blocked = /captcha|access denied|are you human|verify you are human/i.test(bodyText)
  printField("status", blocked ? "blocked" : "ok")
  printField("url", url.href)
  printField("http_status", statusCode)
  printField("text_file", textFile)
  printField("screenshot", screenshot)
  printField("text_chars", sample.length)
  printField("viewport", `${args.width}x${args.height}`)
  if (blocked) {
    printField("reason", "captcha-or-access-block")
    exitCode = 2
  }
} catch (error) {
  printField("status", "failed")
  printField("reason", "browser-fetch-failed")
  printField("url", url.href)
  printField("detail", String(error?.message || error).replace(/\n/g, " "))
  exitCode = 2
} finally {
  await browser.close()
}
process.exit(exitCode)
