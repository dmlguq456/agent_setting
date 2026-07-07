# Context Footprint Audit — 2026-07-07

Scope: Claude/Codex harness ceremony and early-context footprint in `/home/Uihyeop/agent_setting`.

Caveat: `tiktoken` is not installed locally, so this report uses character counts as the primary metric. Token estimates should be treated as rough relative signals only; Korean and Markdown-heavy text can diverge from `chars/4` substantially.

## Runtime Doc Check

- Codex official skills docs: Codex starts with skill name/description/path, loads full `SKILL.md` only when selected, and budgets the initial skills list to at most 2% of the model context or 8,000 chars when the window is unknown. Source: https://developers.openai.com/codex/skills
- Codex official AGENTS.md docs: Codex reads `AGENTS.md` before doing work. Source: https://developers.openai.com/codex/guides/agents-md
- Claude Code official skills docs: skill body is loaded only when used; moving procedural content out of `CLAUDE.md` into skills is intended to reduce always-on context. Source: https://docs.anthropic.com/en/docs/claude-code/skills
- Claude context docs: system prompt, messages, tool definitions, and tool results count toward context; larger context can degrade recall. Source: https://docs.anthropic.com/en/docs/build-with-claude/context-windows

## Measured Static Footprint

| Item | Chars | Lines | Interpretation |
|---|---:|---:|---|
| `adapters/codex/AGENTS.md` | 18,587 | 98 | Codex always-on project/bootstrap guidance candidate. |
| `adapters/claude/CLAUDE.md` | 15,188 | 148 | Claude always-on project/bootstrap guidance candidate. |
| `core/{CORE,WORKFLOW,CONVENTIONS,OPERATIONS,MEMORY}.md` total | 83,704 | 1,158 | Not automatically needed in full; expensive if read wholesale at start. |
| Codex `autopilot-code/SKILL.md` | 8,446 | 129 | Loaded when selected; now relatively thin. |
| Claude `autopilot-code/SKILL.md` | 4,063 | 74 | P3 split: selected body is now router-sized; detailed policy moved to direct references. |
| Codex native skills full bodies, 28 files | 126,372 | n/a | Progressive disclosure means not all should load up front. |
| Codex plugin skills full bodies, duplicate 28 files | 126,372 | n/a | Same bodies duplicated through plugin projection. |
| Claude skills full bodies, 28 files | 545,686 | n/a | Large if selected skills remain monolithic. |

## Skill Metadata Footprint

| Surface | Items | Chars | Notes |
|---|---:|---:|---|
| Codex local skill metadata | 28 | 3,501 | P2 shortened generated descriptions; plugin-only runtime makes this inactive by default when plugin is installed. |
| Codex plugin skill metadata | 28 | 4,845 | P2 shortened generated descriptions; active plugin surface remains under the 8,000-char budget signal. |
| Codex local + plugin metadata | 56 | 8,346 | Still duplicate if `--skills-mode both` is used; normal runtime should choose one surface. |
| Claude skill metadata projection | 28 | 2,834 | P2 replaced long descriptions with compact `metadata.blurb` summaries. |

Main waste signal: Codex currently projects the same 28 harness skills twice (local adapter skills and installable plugin skills). Even if Codex truncates to 8,000 chars, the duplicate set can crowd out useful metadata and degrade trigger clarity.

## Lifecycle Hook Footprint

Measured in current repo with synthetic session id `measure-token`.

| Event / command | Codex chars | Claude chars | Per-turn? | Notes |
|---|---:|---:|---|---|
| SessionStart memory injection | 1,761 | 1,871 | session start | Already capped; includes working/durable/profile summary. |
| UserPromptSubmit workflow anchor | 83 | 83 | every prompt | Good: one-line tracked/untracked anchor. |
| UserPromptSubmit recall, neutral prompt | 0 | 0 | conditional | No signal word, no injection. |
| UserPromptSubmit recall, signal prompt | 1,743 | 1,743 | conditional | Triggered by “지난번…” style prompt. |
| Codex `status` | 813 | n/a | manual/worker startup | Not per-turn by contract. |
| Codex `prompt-signal` | 739 | n/a | manual/worker startup | Not per-turn by contract. |
| Codex dispatch dry-run stdout | 957 | n/a | manual dispatch | Does not include generated prompt body in dry-run. |
| Codex first daily briefing observed via hook | 4,651 | n/a | once/day/desk-like | Neutral hook run injected the oncall briefing once; direct `briefing` afterward returned 0. Needs gating review if it appears outside intended desk. |

## Findings

1. The largest repeatable fixed-cost issue is not plan/test QA anymore. It is skill metadata duplication in Codex: local + plugin exposes the same 28 capabilities twice, roughly 15.5k chars before runtime truncation.
2. Claude `autopilot-code` remains monolithic at 36.2k chars. Codex's corresponding skill is 8.4k chars, so Claude-side skill body thinning still has a clear payoff.
3. Hook ceremony is mostly under control after prior changes: ordinary UserPromptSubmit is about 83 chars, recall is conditional, and memory start is about 1.8k chars.
4. The daily briefing path is a possible hidden spike. A measured Codex UserPromptSubmit emitted 4.65k chars because an oncall briefing was available. It should be confirmed that this only fires on the intended discussion desk / once per day, not in normal coding repos.
5. The core source-order contract can cause accidental over-read: reading all five core docs at startup costs about 83.7k chars. The bootstrap should keep “read core first before adapter edits” but avoid implying all core docs are needed for ordinary work.

## Recommended Next Actions

1. Codex duplicate skill exposure P1 applied: runtime projection now supports `--skills-mode native|plugin|both`, and plugin install defaults to plugin-only skill discovery.
2. Skill description shortening P2 applied: active Codex plugin metadata is now about 4.8k chars and Claude skill metadata about 2.8k chars.
3. Claude `autopilot-code` thinning P3 applied: selected body is now about 4.1k chars, with detailed policy in references loaded by selected mode/stage.
4. Briefing gate P0 applied: normal `agent_setting` coding sessions no longer receive daily oncall briefing unless `MEM_BRIEFING_DESK` points there.
5. Deterministic footprint guard P4 applied: `tools/context-footprint.py` reports bootstrap, metadata, active duplicate exposure, hook samples, and largest skill bodies with warning thresholds.
