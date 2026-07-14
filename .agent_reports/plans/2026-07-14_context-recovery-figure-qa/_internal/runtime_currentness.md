# Runtime Currentness Evidence

Checked 2026-07-14 before projection edits.

- Codex official docs: Skills are discovered from `SKILL.md` metadata and
  `AGENTS.md` supplies durable repository instructions. Deterministic report QA
  therefore belongs in checked-in contract/tooling, not implicit skill choice.
  Sources: <https://developers.openai.com/codex/skills>,
  <https://developers.openai.com/codex/guides/agents-md>.
- Claude Code official docs: Skills are model-invoked by description, while
  project memory/instructions and hooks carry persistent and deterministic
  behavior. Source: <https://docs.anthropic.com/en/docs/claude-code/skills>,
  <https://docs.anthropic.com/en/docs/claude-code/memory>.
- OpenCode official docs: Skills load on demand and `AGENTS.md`/rules supply
  project instructions. Sources: <https://opencode.ai/docs/skills/>,
  <https://opencode.ai/docs/rules/>.

Local realization checks use each adapter's `mode-info material/figure-gen`,
the concrete Codex/OpenCode `figure-gen` wrapper, the Claude concrete mode,
generated projection checks, and the adaptation-boundary guard. If the
portable verifier or Python is unavailable, Codex/OpenCode wrappers return 69
and the report must remain incomplete.
