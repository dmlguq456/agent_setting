# 02 — Standards & Conventions

> 이 도메인엔 공식 "표준화 기구 표준" 이 드물다. 가장 표준에 가까운 것은 (1) **Claude Code plugin/marketplace/hooks/skills/subagent 규격** (Anthropic host 규격 — 다른 프레임워크가 투영해 들어가는 target) 과 (2) 신흥 **AGENTS.md** prose 컨벤션이다. 출처는 `claude-code-official-plugins.md`, `multi-harness-projection.md` §3.

## 1. Claude Code Official Schema — 사실상의 host 규격

Anthropic 공식 문서(`code.claude.com/docs/en/*`)가 정의하는 5개 컴포넌트 스키마가 사실상 이 생태계의 표준 표면이다. GSD·SuperClaude·claude-flow·Superpowers 모두 이 규격으로 투영해 들어간다.

| 컴포넌트 | 파일/위치 | 핵심 스키마 필드 | 근거 |
|---|---|---|---|
| **plugin** | `.claude-plugin/plugin.json` (manifest, optional) | `name`(skill namespace), `description`, `version`(생략 시 commit SHA=버전), `author` | `claude-code-official-plugins.md` §1 |
| **marketplace** | repo 루트 `.claude-plugin/marketplace.json` | `name`(kebab), `owner`, `plugins[]`, `renames`(v2.1.193+), `source`(github/url/git-subdir/npm) | §2 |
| **hooks** | `hooks/hooks.json` 또는 `settings.json` | 31 event(`PreToolUse` block 가능, `SessionStart`, `PreCompact`…), handler `type`(command/http/mcp_tool/prompt/agent) | §3 |
| **skills** | `skills/<name>/SKILL.md` | frontmatter 전부 optional, `description`+`when_to_use` **1,536자 truncate**, `disable-model-invocation`, `paths` glob, `context: fork` | §4 |
| **subagents** | `.claude/agents/*.md` | `name`(required), `description`(required), `tools`/`disallowedTools`, `model`, `permissionMode` | §5 |

**핵심 컨벤션 (문서가 명시한 common mistake)**: `commands/`·`agents/`·`skills/`·`hooks/` 를 `.claude-plugin/` **안에 넣으면 안 된다** — `.claude-plugin/` 에는 오직 `plugin.json` 만, 나머지는 plugin root 레벨 (`claude-code-official-plugins.md` §1). 우리 harness 의 `adapters/claude/` 구조가 이 규약과 정렬되는지 자체 점검 가치.

**override 우선순위 (표준화된 계층)**: skill 은 Enterprise(managed) > Personal(`~/.claude/skills/`) > Project(`.claude/skills/`) > 번들. subagent 는 managed > `--agents` CLI > project > user > plugin (`claude-code-official-plugins.md` §4-5). → 우리 harness 의 override-layer 설계에 참고할 정립된 우선순위 모델.

## 2. AGENTS.md — prose-only 공통 컨벤션 (신흥 표준)

- **성격**: projection tool 이 아니라 "모든 coding agent 가 직접 읽는 단일 Markdown" 컨벤션 — dev tips / testing / PR guideline 만 담는 **prose 전용**, hooks·MCP·skills·machine schema 표현 불가 (`multi-harness-projection.md` §3).
- **거버넌스**: 2025-08 OpenAI 주도 open spec(Google/Cursor/Factory 참여) → 2025-12 Linux Foundation 산하 Agentic AI Foundation 기부, 60,000+ repo 채택 주장 (2차 source 근거, repo README 자체엔 governance 명시 없음 — caveat).
- **포섭 관계**: 다른 프레임워크가 이 표준을 per-agent memory 파일 축으로 흡수 — spec-kit `agent-context` 가 Claude=`CLAUDE.md`/Gemini=`GEMINI.md` 매핑, ruler 가 `AGENTS.md` 를 최우선 source 로 (`spec-kit.md` §3, `multi-harness-projection.md` §1).

## 3. 표준/규격 요약 표

| org / spec | scope | year | status |
|---|---|---|---|
| Anthropic — Claude Code plugin/marketplace | plugin 유통·버전·hook·skill·subagent host 규격 | 2025~ (v2.1.193+ `renames`) | **active, de-facto** |
| agentskills.io — SKILL.md 표준 | progressive disclosure skill 포맷 (오픈 표준) | 2025~ | **active, 다수 채택** (Superpowers·GSD·BMAD) |
| AGENTS.md (Agentic AI Foundation / Linux Foundation) | prose-only agent 지침 공통 파일 | 2025-08 spec, 2025-12 LF 기부 | **active, 신흥 표준** |

## 4. Cross-references

- Claude 공식 version/SHA-pin 메커니즘의 fork-drift 해법 상세 → [04_technical_deep_dive](04_technical_deep_dive.md) §(a)
- 각 프레임워크가 이 규격으로 어떻게 투영하는지 비교 → [03_vendor_comparison](03_vendor_comparison.md)
- one-runtime-only 기능(hook)의 표준 부재로 인한 capability loss → [04_technical_deep_dive](04_technical_deep_dive.md) §(d)

**요점 (어느 표준/컨벤션을 따라야 하는가)**: 우리 harness 는 이미 Claude 규격으로 투영하므로 **Claude 공식 plugin/skill/subagent 스키마를 adapter 층의 정준 target 으로 고정**하고, core 층에는 **AGENTS.md 급 prose LCD 를 최소공통 계약**으로 두는 2단 정렬이 자연스럽다 — machine 기능(hook/gate)은 adapter 별로만 표현하고 core 는 prose+manifest 로 유지. agentskills.io SKILL.md 는 skill 포맷의 사실상 표준이므로 신규 skill 은 이 포맷을 따른다.
