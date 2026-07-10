# Claude Code Adapter

This adapter maps the common agent harness onto Claude Code.

## Entry Points

| Surface | File |
|---|---|
| Session bootstrap | `adapters/claude/CLAUDE.md` |
| Runtime settings | `adapters/claude/settings.json` |
| Slash commands | `adapters/claude/commands/` |
| Runtime worker wrappers | `adapters/claude/bin/` |
| Dispatch registry metadata | `adapters/claude/bin/dispatch-headless.py` records `intensity`, `depth`, `parent_sid`, `worker_role`, `owner`, and `owner_harness` so fleet can render cross-harness ownership such as Codex → Claude. |
| Capabilities | `adapters/claude/skills/*/SKILL.md` |
| Role profiles | `adapters/claude/agents/*.md` |
| Hook scripts | `hooks/`, `utilities/` |
| Status line | `adapters/claude/statusline.sh` |

## Runtime Mapping

| Core Concept | Claude Code Implementation |
|---|---|
| capability | Skill |
| role profile | Agent |
| adapter bootstrap | `adapters/claude/CLAUDE.md` |
| agent home | `$HOME/.claude` by default; overridable with `AGENT_HOME` or `CLAUDE_HOME` |
| artifact root | `.agent_reports`, legacy fallback `.claude_reports` only when already present |
| tracked/untracked signal | `workflow-guard-hook.sh` + `adapters/claude/statusline.sh` |
| artifact-order gate | `hooks/artifact-guard.sh` |
| spec read gate | `hooks/spec-skill-gate.sh` + `hooks/spec-read-marker.sh` |
| git safety gate | `hooks/git-state-guard.sh` |
| memory write guard | `hooks/builtin-memory-guard.sh` |

## Runtime Home Projection

Target layout:

```text
$HOME/agent_setting/        # neutral repo
$HOME/agent_setting/claude_setting/ # versioned Claude projection
$HOME/.claude/              # Claude Code runtime home
```

Claude Code should see the same files it expects today, but they should be symlinked from the versioned Claude projection where practical:

```text
$HOME/.claude/CLAUDE.md      -> $HOME/agent_setting/claude_setting/CLAUDE.md
$HOME/.claude/README.md      -> $HOME/agent_setting/claude_setting/README.md
$HOME/.claude/core           -> $HOME/agent_setting/claude_setting/core
$HOME/.claude/skills         -> $HOME/agent_setting/claude_setting/skills
$HOME/.claude/agents         -> $HOME/agent_setting/claude_setting/agents
$HOME/.claude/agent-modes    -> $HOME/agent_setting/claude_setting/agent-modes
$HOME/.claude/hooks          -> $HOME/agent_setting/claude_setting/hooks
$HOME/.claude/utilities      -> $HOME/agent_setting/claude_setting/utilities
$HOME/.claude/tools          -> $HOME/agent_setting/claude_setting/tools
$HOME/.claude/commands       -> $HOME/agent_setting/claude_setting/commands
$HOME/.claude/bin            -> $HOME/agent_setting/claude_setting/bin
$HOME/.claude/statusline.sh  -> $HOME/agent_setting/claude_setting/statusline.sh
$HOME/.claude/track-toggle.sh -> $HOME/agent_setting/claude_setting/track-toggle.sh
```

Keep Claude-owned mutable state in `$HOME/.claude`: credentials, sessions, projects, history, shell snapshots, cache, daemon logs, and local DBs. Do not move those into the neutral repo.

## Model Role Mapping

Claude Code adapter 는 기존 운용 품질을 보존하기 위해 `core/CONVENTIONS.md §2` 의 portable role 을 아래처럼 concrete model 로 매핑한다. 공통 문서에는 role name 을 쓰고, Claude Code 전용 frontmatter / Agent 호출에서만 concrete name 을 쓴다.

| Portable role | Claude Code mapping | 기존 재현 의미 |
|---|---|---|
| `fast reviewer` | `sonnet` | coverage, typo, style consistency, cross-ref, structure, verbatim matching 처럼 넓고 비용 효율적인 점검 |
| `fast fact-checker` | `sonnet` | citation/venue/year/metric/lineage 를 source artifact 와 좁게 대조 |
| `fast writer` | `sonnet` | 이미 검증된 artifact 를 final report 로 조립 |
| `deep reviewer` | `opus` | methodology, domain expertise, completeness, safety/security, architecture risk |
| `deep maker` | `opus` | planning, research synthesis, visual/editorial judgment 처럼 생성 자체가 고차 판단을 요구하는 작업 |
| `fast implementer` | `sonnet` | 기본 코드 구현·리팩터링. 복잡한 API/library 설계는 호출자가 deep role 로 상향 |
| `external adversary` | Codex CLI (GPT-5) via `codex-review-team` | `intensity=adversarial` 의 독립 hostile review |
| `external adversary orchestrator` | `sonnet` wrapper | Codex CLI 호출·결과 정리만 담당하고 실제 판단은 external engine 에 위임 |

검증 rigor tier 의 기존 동작은 이 mapping 으로 재현한다 (tier 는 `--intensity` 에서 파생 — CONVENTIONS §1.1, 별도 `--qa` 축 없음): quick/light 는 fast reviewer 중심, standard 는 deep reviewer + fast reviewers, thorough/adversarial 은 deep reviewers + fast reviewers + optional external adversary. Dispatch/headless 분사는 이 표를 기본으로 삼되 wrapper 가 자동 선택하지 않는다. main/orchestrator 가 작업 난이도별로 `--model-role`, concrete `--model --effort`, 또는 명시적 `--inherit-model-settings` 를 job 마다 선택한다.

## Compatibility

Claude Code projects created before the neutral artifact root use `.claude_reports/`. This adapter recognizes both names. New projects should use `.agent_reports/`; existing projects can migrate later or keep the legacy directory indefinitely.

For shell code, use `utilities/artifact-root.sh` or the equivalent rule: prefer `.agent_reports`; use `.claude_reports` only if it already exists and `.agent_reports` does not.

For harness-home paths, use `utilities/agent-home.sh` or the equivalent rule: prefer `AGENT_HOME`, then `CLAUDE_HOME`, then `$HOME/agent_setting` when present, then `$HOME/.claude` as legacy fallback.
