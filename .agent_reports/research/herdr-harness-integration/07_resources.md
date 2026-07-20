# 07 — Resources

## Herdr primary sources

- [Herdr repository](https://github.com/ogulcancelik/herdr)
- [v0.7.4 latest release](https://github.com/ogulcancelik/herdr/releases/tag/v0.7.4)
- [Agents](https://herdr.dev/docs/agents/)
- [Socket API](https://herdr.dev/docs/socket-api/)
- [Session state and restore](https://herdr.dev/docs/session-state/)
- [Persistence and remote access](https://herdr.dev/docs/persistence-remote/)
- [Integrations](https://herdr.dev/docs/integrations/)
- [Plugins](https://herdr.dev/docs/plugins/)
- [`agent.send` schema, v0.7.4](https://github.com/ogulcancelik/herdr/blob/v0.7.4/src/api/schema/agents.rs)
- [`agent.send` implementation, v0.7.4](https://github.com/ogulcancelik/herdr/blob/v0.7.4/src/app/api/agents.rs)

## Codex primary source

- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents.md)

## Local evidence

- `core/OPERATIONS.md:98,123,131-142` — native/headless 구분, stage handoff, fallback, attempt/completion
- `core/HOOKS.md:58` — Herdr optional external integration
- `adapters/codex/bin/install-runtime-projection.sh:78-96,121` — hooks.json backup/symlink
- `adapters/codex/bin/dispatch-headless.py:1235-1258` — ambient environment inheritance
- `hooks/herdr-agent-state.sh:10-20` — worker suppression guard
- `tools/fleet/collectors/liveness.py:11-12` — blocked/Herdr socket가 현재 MVP 밖
- `.agent_reports/spec/agent-fleet-dashboard/prd.md:359-364,488` — 현 Herdr 제한 결정

## Local commands verified

```text
herdr --version                         -> 0.6.6
herdr status                            -> protocol 12, server running
herdr integration status               -> claude v4, codex v4
codex features list                     -> multi_agent stable true
preflight subagent-info --check         -> PASS
utilities/dispatch-concurrency.test.sh  -> PASS (3 concurrent workers)
utilities/capability_route.test.py      -> PASS (18 tests)
```
