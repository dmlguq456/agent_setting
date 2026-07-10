# Portable Role Profiles

This directory describes runtime-neutral delegation roles. It is not a native
agent registry for any one tool.

Claude Code realizes these profiles as native Agent files under
`adapters/claude/agents/`. Codex and OpenCode read this directory for role
meaning, then map each role to their own model, tool, and delegation mechanism
through adapter-owned wrappers or native agent surfaces.

## Role Catalog

| Role profile | Portable model role | Primary responsibility | Claude realization | Codex realization | OpenCode realization |
|---|---|---|---|---|---|
| `plan-team` | `deep maker` | Read source and artifacts, produce or refine implementation plans | `adapters/claude/agents/plan-team.md` | `adapters/codex/agents/plan-team.toml` | `adapters/opencode/agents/plan-team/plan-team.md` |
| `dev-team` | `fast implementer` by default | Implement backend/frontend/refactor/new-lib work through mode personas | `adapters/claude/agents/dev-team.md` | `adapters/codex/agents/dev-team.toml` | `adapters/opencode/agents/dev-team/dev-team.md` |
| `qa-team` | variable reviewer | Read-only code, plan, test, ML, data, and security review | `adapters/claude/agents/qa-team.md` | `adapters/codex/agents/qa-team.toml` | `adapters/opencode/agents/qa-team/qa-team.md` |
| `research-team` | variable research reviewer | Paper-grounded review, survey, fact-check, and adversarial claim verification | `adapters/claude/agents/research-team.md` | `adapters/codex/agents/research-team.toml` | `adapters/opencode/agents/research-team/research-team.md` |
| `material-team` | `deep maker` plus fast tool worker | Fetch, extract, visualize, and analyze supporting materials | `adapters/claude/agents/material-team.md` | `adapters/codex/agents/material-team.toml` | `adapters/opencode/agents/material-team/material-team.md` |
| `design-team` | `deep maker` plus verifier | Visual making, critique, and independent breakage verification | `adapters/claude/agents/design-team.md` | `adapters/codex/agents/design-team.toml` | `adapters/opencode/agents/design-team/design-team.md` |
| `editorial-team` | `deep maker` / `fast reviewer` by mode | User-facing wording, translation, polish, and review | `adapters/claude/agents/editorial-team.md` | `adapters/codex/agents/editorial-team.toml` | `adapters/opencode/agents/editorial-team/editorial-team.md` |
| `external-adversary` | `external adversary` plus orchestrator | Independent hostile review through a different runtime/process | `adapters/claude/agents/codex-review-team.md` | `adapters/codex/agents/external-adversary.toml` | `adapters/opencode/agents/external-adversary/external-adversary.md` |

Codex and OpenCode native agent files are generated adapter-owned projections
from this table. They are not copies of Claude Agent frontmatter, and they must
not expose Claude agent files as native runtime input.

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

## Behavior Contract (separate from the role catalog)

Beyond the delegation-role catalog above, this directory also holds the
portable **response behavior contract** for the main agent's own responses:

- `response-policy.md` — the runtime-neutral minimum behavior contract
  (concise output, promise–action match, verify-before-assert, convention
  adherence, pause/autonomy, follow-through). The three adapter bootstraps
  reference it as the single source for these portable clauses and add their
  own locale-specific voice (tone, sentence endings) on top. `core/DESIGN_PRINCIPLES.md`
  points here for the portable layer; the adapter bootstrap owns the runtime
  specialization.

This is a behavior contract, not an agent role — it does not appear in the
Role Catalog table and has no per-adapter native agent file.
