# Runtime Watch Loop

Purpose: track fast-changing Codex and Claude Code runtime facts without auto-editing harness policy.

Trigger policy:
- Conservative schedule: at most daily, after oncall, or manually after a runtime/pricing/limit incident.
- Change-triggered: write a full report only when an official-source fingerprint changes, a local runtime/projection probe changes, or the previous report is older than `RUNTIME_WATCH_MAX_AGE_HOURS` (default 72).
- Token guard: deterministic shell probe first. Do not launch LLM/headless review by default. If a report proposes policy edits, route the edit through autopilot-spec/autopilot-code in a normal session.
- Fingerprint guard: hash normalized visible text, not request IDs or hydration scripts; ignore the probe timestamp when detecting change.

Official normative sources:
- OpenAI Codex pricing: `https://developers.openai.com/codex/pricing`
- OpenAI Codex changelog: `https://developers.openai.com/codex/changelog`
- OpenAI Codex rate card: `https://help.openai.com/en/articles/20001106-codex-rate-card-2`
- OpenAI Codex with ChatGPT plan: `https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan`
- Claude Code with Pro/Max plan: `https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan`
- Claude Code changelog (official repository): `https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md`

Required report sections:
- `runtime support`: what official sources currently state.
- `local projection`: what local CLI/runtime/projection probes show.
- `parity gap`: where Codex, Claude Code, and this adapter differ.
- `fallback`: what the harness should do when docs/runtime data is missing or unsupported.
- `proposal`: concrete edits to consider; report only, no auto-apply.

2026-07-13 incident anchor:
- Codex local wham usage reported `primary_window.limit_window_seconds=604800`, `used_percent=10`, `secondary_window=null`.
- Fleet was still rendering the API primary window as `5h 10% reset 6d22h`.
- Runtime-watch exists to catch this class of currentness drift early while preserving zero-injection and core-first/source-order invariants.

Probe command:

```bash
bash loops/runtime-watch.sh --probe
```

Manual report command:

```bash
bash loops/runtime-watch.sh --run
```

Output:
- Default report directory: `/home/nas/user/Uihyeop/notes/runtime-watch/`.
- Override with `RUNTIME_WATCH_OUT_DIR`.
- State directory: `${XDG_STATE_HOME:-$HOME/.local/state}/agent-runtime-watch`.
- Provider overrides for scheduled environments: `RUNTIME_WATCH_FETCH_CMD` (executable receiving one URL) and `RUNTIME_WATCH_LOCAL_PROBE_CMD` (executable emitting stable local probe lines).
