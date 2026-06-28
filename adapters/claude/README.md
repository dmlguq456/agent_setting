# Claude Code Adapter

This adapter maps the common agent harness onto Claude Code.

## Entry Points

| Surface | File |
|---|---|
| Session bootstrap | `CLAUDE.md` |
| Runtime settings | `settings.json` |
| Slash commands | `commands/` |
| Capabilities | `skills/*/SKILL.md` |
| Role profiles | `agents/*.md` |
| Hook scripts | `hooks/`, `utilities/` |
| Status line | `statusline.sh` |

## Runtime Mapping

| Core Concept | Claude Code Implementation |
|---|---|
| capability | Skill |
| role profile | Agent |
| adapter bootstrap | `CLAUDE.md` |
| agent home | `$HOME/.claude` by default; overridable with `AGENT_HOME` or `CLAUDE_HOME` |
| artifact root | `.agent_reports`, legacy fallback `.claude_reports` only when already present |
| tracked/untracked signal | `workflow-guard-hook.sh` + `statusline.sh` |
| artifact-order gate | `hooks/artifact-guard.sh` |
| spec read gate | `hooks/spec-skill-gate.sh` + `hooks/spec-read-marker.sh` |
| git safety gate | `hooks/git-state-guard.sh` |
| memory write guard | `hooks/builtin-memory-guard.sh` |

## Model Role Mapping

Claude Code adapter 는 기존 운용 품질을 보존하기 위해 `CONVENTIONS.md §2` 의 portable role 을 아래처럼 concrete model 로 매핑한다. 공통 문서에는 role name 을 쓰고, Claude Code 전용 frontmatter / Agent 호출에서만 concrete name 을 쓴다.

| Portable role | Claude Code mapping | 기존 재현 의미 |
|---|---|---|
| `fast reviewer` | `sonnet` | coverage, typo, style consistency, cross-ref, structure, verbatim matching 처럼 넓고 비용 효율적인 점검 |
| `fast fact-checker` | `sonnet` | citation/venue/year/metric/lineage 를 source artifact 와 좁게 대조 |
| `fast writer` | `sonnet` | 이미 검증된 artifact 를 final report 로 조립 |
| `deep reviewer` | `opus` | methodology, domain expertise, completeness, safety/security, architecture risk |
| `deep maker` | `opus` | planning, research synthesis, visual/editorial judgment 처럼 생성 자체가 고차 판단을 요구하는 작업 |
| `fast implementer` | `sonnet` | 기본 코드 구현·리팩터링. 복잡한 API/library 설계는 호출자가 deep role 로 상향 |
| `external adversary` | Codex CLI (GPT-5) via `codex-review-team` | `--qa adversarial` 의 독립 hostile review |
| `external adversary orchestrator` | `sonnet` wrapper | Codex CLI 호출·결과 정리만 담당하고 실제 판단은 external engine 에 위임 |

QA 레벨의 기존 동작은 이 mapping 으로 재현한다: quick/light 는 fast reviewer 중심, standard 는 deep reviewer + fast reviewers, thorough/adversarial 은 deep reviewers + fast reviewers + optional external adversary.

## Compatibility

Claude Code projects created before the neutral artifact root use `.claude_reports/`. This adapter recognizes both names. New projects should use `.agent_reports/`; existing projects can migrate later or keep the legacy directory indefinitely.

For shell code, use `utilities/artifact-root.sh` or the equivalent rule: prefer `.agent_reports`; use `.claude_reports` only if it already exists and `.agent_reports` does not.

For harness-home paths, use `utilities/agent-home.sh` or the equivalent rule: prefer `AGENT_HOME`, then `CLAUDE_HOME`, then `$HOME/.claude`.
