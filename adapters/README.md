# Adapters

Adapters map the model-agnostic core contract in `CORE.md` onto a concrete agent runtime.

An adapter owns runtime-specific details:

- bootstrap file names and loading behavior;
- hook/event schemas;
- slash command registration;
- permission model and tool names;
- status UI;
- compatibility shims for local paths and legacy names.

The core owns workflow meaning, artifact layout, memory lifecycle, and safety invariants. New adapters should not redefine those concepts; they should document how their runtime implements them.

Path convention: portable docs use `<agent-home>`. Shell code should resolve it with `utilities/agent-home.sh` or the same rule: `AGENT_HOME`, then an adapter compatibility variable such as `CLAUDE_HOME`, then the adapter default.

## Current Adapters

| Adapter | Status | Entry |
|---|---|---|
| Claude Code | primary | `adapters/claude/README.md` + root `CLAUDE.md` |
| Codex | experimental | `adapters/codex/README.md` |
