# Portable Role Profiles

This directory describes runtime-neutral delegation roles. It is not a native
agent registry for any one tool.

Claude Code realizes these profiles as native Agent files under
`adapters/claude/agents/`. Codex and future runtimes should read this directory
for role meaning, then map each role to their own model, tool, and delegation
mechanism.

## Role Catalog

| Role profile | Portable model role | Primary responsibility | Claude realization |
|---|---|---|---|
| `plan-team` | `deep maker` | Read source and artifacts, produce or refine implementation plans | `adapters/claude/agents/plan-team.md` |
| `dev-team` | `fast implementer` by default | Implement backend/frontend/refactor/new-lib work through mode personas | `adapters/claude/agents/dev-team.md` |
| `qa-team` | variable reviewer | Read-only code, plan, test, ML, data, and security review | `adapters/claude/agents/qa-team.md` |
| `research-team` | variable research reviewer | Paper-grounded review, survey, fact-check, and adversarial claim verification | `adapters/claude/agents/research-team.md` |
| `material-team` | `deep maker` plus fast tool worker | Fetch, extract, visualize, and analyze supporting materials | `adapters/claude/agents/material-team.md` |
| `design-team` | `deep maker` plus verifier | Visual making, critique, and independent breakage verification | `adapters/claude/agents/design-team.md` |
| `editorial-team` | `deep maker` / `fast reviewer` by mode | User-facing wording, translation, polish, and review | `adapters/claude/agents/editorial-team.md` |
| `external-adversary` | `external adversary` plus orchestrator | Independent hostile review through a different runtime/process | `adapters/claude/agents/codex-review-team.md` |

## Adapter Requirements

An adapter that supports role delegation must document:

- how a role is invoked;
- what tools are available to that role;
- how mode personas under `roles/modes/` are loaded or approximated;
- which concrete model or reasoning profile maps to the portable model role;
- where role output is written when a skill requires durable review logs;
- what happens when a role is unavailable.

Concrete model names do not belong in this directory. Use the portable model
roles from `core/ADAPTATION.md` and let adapter documents define concrete
mapping.
