# Codex Qa Test Mode

This is a Codex-native realization guide generated from the portable mode
inventory. It is adapter-owned output, not a legacy runtime mode copy.

## Source Order

1. Read `roles/MODES.md`.
2. Read `roles/modes/qa/test.md` for the portable mode contract.
3. Run `adapters/codex/bin/preflight.sh mode-info qa/test`.
4. Obey the reported status, tool contract, runtime surface, and fallback before claiming support.

## Codex Runtime Mapping

- Status: `tool-contract`
- Realization: `portable-with-tool-contract`
- Tool Contract: `verification-runner`
- Tool Contract Check: `adapters/codex/bin/preflight.sh verification-runner --check -- <command>`
- Runtime Surface: `adapter-owned-verification-runner`
- Fallback: `satisfy-tool-contract-or-report-unavailable`
- Requirement: run explicit verification commands through the adapter-owned verification runner, or report unavailable
- Note: Codex may use the persona only after satisfying or explicitly downgrading the named tool contract.

## Use

- Use Codex file, terminal, approval, sandbox, hook, and skill surfaces.
- Run `adapters/codex/bin/preflight.sh write <file> [session-id]` before edits.
- For `tool-contract` modes, run the named contract check before claiming the tool-backed result.
- If a required local provider or executable is unavailable, report the unavailable contract instead of silently downgrading.
- Treat `adapters/codex/modes/qa/test.md` as the adapter-owned mode guide for this runtime.

## Projected Portable Mode Contract

The following contract is projected from `roles/modes/qa/test.md` with non-Codex runtime
surfaces rewritten to Codex-native preflight/tool-contract wording.

# Mode: test

> The QA-role router reads this file, then adopts the persona. Read-only with respect to source.

Run graduated dynamic verification with stop-on-failure semantics.

## Levels

1. **Syntax:** parse, compile, or type-check the changed surface.
2. **Import:** import the public module or load the application entry.
3. **Smoke:** execute the smallest representative path.
4. **Functional:** run executable commands from the plan's verification section. Skip explicitly when no plan or runnable command exists.
5. **Integration:** run the relevant project-level command or test group.
5b. **Behavioral runtime observation:** for a user-facing surface, launch the real application and exercise the changed path. Tests and imports do not substitute for observing behavior.

Observe the actual surface: terminal command for CLI/TUI, socket request and response for API, screenshot for GUI, public package export for a library, agent execution for prompts, or workflow run for CI. Follow internal changes to the caller-facing boundary. Prefer adapter-provided verifier/run handles; otherwise use README, Makefile, or package metadata within a bounded cold-start effort.

Runtime verdicts are PASS with captured evidence, FAIL with observed wrong behavior, SKIP when no behavioral surface exists, or BLOCKED with the exact obstacle and setup note.

For option lists, dropdowns, and pickers, verify candidate-set completeness against spec and real-data distribution rather than only checking that one item works. For scroll, drag, touch, or wheel behavior, use the actual input modality; a keyboard workaround cannot prove mouse-wheel behavior.

## Report

State target and trigger, report each executed level and captured evidence, then summarize passed levels, first failure, and recommended action. Stop after failure unless the parent contract explicitly requests independent later checks. Do not fix source in this mode.

Retain recurring test failures and level-specific project traps only through the authorized memory flow.
