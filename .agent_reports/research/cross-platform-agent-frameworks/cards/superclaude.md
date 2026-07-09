# SuperClaude Framework — 기술 심층 카드

- **Repo**: `SuperClaude-Org/SuperClaude_Framework` (공식, MIT). default branch `master`, 최근 push 2026-06-13.
- **최신 stable release**: **v4.3.0** ("Implementation Fixes, Security Hardening & Claude Code Alignment", 2026-03-22).
- **자기 규정**: "SuperClaude is NOT standalone software with running processes, execution layers, or performance systems" — 실행 엔진이 아니라 Claude Code 가 읽는 `.md` instruction 파일 모음 (behavioral instruction injection).
- **성격**: 한 문장 요약 — Claude Code 를 대상으로 한 **structured prompt-engineering context pack + Python installer + Claude Code plugin** 의 결합. 대부분의 "지능"은 markdown context 이고, 코드는 설치/배치/보조 로직에 그침.

## 1. Layer 구조 — single-runtime vs multi-harness

- **Single-runtime (Claude Code 전용).** technical-architecture.md 가 명시: "operating exclusively within Claude Code", 다중 harness/CLI 를 독립 지원할 능력 없음. core↔runtime 을 harness 중립 계약으로 분리한 우리 방식(core/CORE.md + adapter)과 달리, SuperClaude 는 Claude Code 표면(slash command, `@agent-`, plugin/hooks, MCP)에 직접 결합.
- **core vs runtime projection 유사 개념은 존재하나 harness 축이 아니라 "loading 축"**:
  - *Core (always-loaded, MANDATORY)*: `core/FLAGS.md`, `core/RULES.md`, `core/PRINCIPLES.md` — foundational behavioral rules.
  - *Runtime projection (on-demand, trigger-based)*: command context(`/sc:` = `commands/*.md`), agent specialist(`@agent-*` = `agents/*.md`), behavioral mode(`modes/MODE_*.md`, flag/keyword 로 활성).
- 즉 "projection" 은 *다른 런타임으로의 투영*이 아니라 *같은 런타임 안에서의 selective context 주입*이다. 이 점이 우리 harness-parity 모델과 근본적으로 다르다 (⚠️ 비교축 유의).

## 2. Packaging / Installation

- **다중 배포 채널** (동일 프레임워크를 서로 다른 포장으로):
  - `pipx install SuperClaude && SuperClaude install` (권장)
  - `pip install SuperClaude && SuperClaude install`
  - `npm install -g @bifrost_inc/superclaude && superclaude install`
  - source: `git clone` + `uv pip install -e ".[dev]"`
- **설치 위치**: `~/.claude/` (~50MB). `~/.claude/CLAUDE.md` = 엔트리, `~/.claude/claude-code-settings.json` = MCP 설정, `commands/sc/`·`agents/`·`skills/`.
- **두 개의 소스 레이아웃이 repo 에 공존**:
  - `src/superclaude/**` — pip 패키지 소스 (core/·modes/ 의 `.md` + `__init__.py` 등 Python).
  - `plugins/superclaude/**` — **Claude Code plugin** (`.claude-plugin/plugin.json` v4.3.0, `commands/`·`agents/`·`skills/`·`hooks/hooks.json`·`.mcp.json`).
- **Plugin marketplace 경로 존재**: plugin.json 이 이미 있어 `/plugin install superclaude` 형태를 겨냥. 검색 요약상 이 "TypeScript plugin system" 완성형은 **v5.0(개발 중, ETA 미정)** 계획이며 v4.3.0 stable 엔 미포함 (⚠️ 문서 간 진술 상충 — 아래 6 참조).
- **Update vs drift**: 업데이트는 표준 패키지 관리(`pip install --upgrade SuperClaude`, `SuperClaude update`). installer 는 `--dry-run`, `--force --yes`, `--components core mcp modes` 컴포넌트 선택 제공. **한계(설치 문서 자인)**: user 로컬 커스터마이즈를 upgrade 시 어떻게 보존/merge 하는지 — version-specific customization 전략·migration path 를 문서가 다루지 않음. `~/.claude/` 를 직접 덮어쓰는 구조라 사용자 편집 drift 위험이 구조적으로 존재.

## 3. Context loading strategy

- **Trigger-based selective loading** (always-load 최소화):
  1. explicit command `/sc:command` → 해당 `commands/*.md` 로드
  2. manual agent `@agent-name` → `agents/*.md`
  3. keyword auto-activation → mode/agent
  4. flag 기반 mode 전환 (`modes/MODE_*.md`)
- **Always-loaded**: FLAGS/RULES/PRINCIPLES (MANDATORY 표기). 나머지는 on-demand.
- **CLAUDE.md 는 `@import` 미사용** — formal include 가 아니라 *descriptive path 참조*("static configuration guide"). 즉 로딩은 Claude 의 자율 판단+trigger 에 의존, 결정론적 include 아님.
- **MCP 통합**: plugin `.mcp.json` 은 `context7`, `sequential-thinking` 만 선언(npx 기동). 문서·릴리스는 8개 MCP server(Tavily, Context7, Sequential-Thinking, Serena 등) 통합을 광고 — 즉 일부는 사용자 설정/선택 컴포넌트.
- **modes(7)**: Brainstorming, Business_Panel, DeepResearch, Introspection, Orchestration, Task_Management, Token_Efficiency.

## 4. Workflow gate 강제

- **Spec-driven 흐름은 존재하나 convention/prompt-level, 기계적 gate 아님.**
  - 권장 시퀀스: `VAGUE IDEA? → /sc:brainstorm → PRD READY? → /sc:workflow → NEED DESIGN? → /sc:design → READY TO CODE? → /sc:implement`.
  - commands 문서 자인: 이 다이어그램은 "learning resource for humans" · visual guide 이며, command 는 독립 호출 가능하고 **design 을 건너뛰고 implement 로 점프하는 것을 막는 gating 시스템 없음**.
- **RULES.md 의 Workflow Rules**(🟡 IMPORTANT): "Task Pattern: Understand → Plan → TodoWrite(3+) → Execute → Track → Validate", "Validation Gates: Always validate before execution", "Session Lifecycle: /sc:load → Work → Checkpoint(30min) → /sc:save". → 모두 **behavioral rule(프롬프트 규범)**, hook 로 hard-block 되지 않음.
- **PM Agent (PDCA: Plan→Do→Check→Act)**: post-implementation 문서화·mistake 시 root-cause 를 "자동 활성"한다고 규정하나, 이는 hard gate 가 아니라 passive oversight(프롬프트 유도).
- **Confidence-Check skill**: 구현 전 ≥90% confidence 요구(중복/architecture/공식문서/OSS/root-cause 5-check). 그러나 이 역시 **skill 프롬프트**로 수행 — 검색상 precision/recall 1.0 자체 테스트(8 케이스)를 광고하나 결정론적 차단 장치는 아님.
- ⚠️ 우리 시스템의 `artifact-guard.sh`(신규 산출물 *생성 순서* hard-block) 같은 **mechanism-level gate 는 부재**. SuperClaude 의 gate 는 전적으로 convention.

## 5. State / artifact management

- **Session persistence via Serena MCP**: `.serena/memories/` 에 cross-session note 저장. `/sc:load`·`/sc:save` 로 명시적 세션 관리, `/sc:pm` 이 과거 세션 context 자동 복원.
- **Artifact**: task hierarchy, implementation plan, memory file — 추적되나 blocker 로 강제되지 않음("tracked but not mechanically enforced").
- **Repo 내 소스 모듈**(CLAUDE.md 참조): `src/superclaude/pm_agent/`(confidence.py, self_check.py, reflexion.py, token_budget.py), `src/superclaude/execution/`(parallel.py, reflection.py, self_correction.py) — reflexion 기반 learning·parallel execution 보조 로직. (⚠️ 이 Python 모듈의 실제 런타임 관여도는 미검증 — 문서는 "guide, not control" 로 규정.)
- **Plugin hooks** (`hooks/hooks.json`): `SessionStart` → `scripts/session-init.sh`(command hook, 결정론적) / `Stop` → **prompt hook**(미완 task/uncommitted 확인) / `PostToolUse(Write|Edit)` → **prompt hook**(edit 검증). 즉 hook 3개 중 2개가 *prompt type*(LLM 에게 부탁) — deterministic enforcement 아님. Serena 외 자체 DB 없음.

## 6. Drift 방지 (framework core ↔ user project) — 주목점

- **문서 자체가 버전 drift 를 보임 (핵심 관찰)**: technical-architecture.md 는 "No Orchestration Layer / No Python orchestration / No quality gates" 라 단언하나, 같은 repo 의 CLAUDE.md·plugin.json·검색 요약은 pm_agent/execution Python 모듈·confidence-check·parallel-execution·reflexion 을 광고. → stable(v4.3) 서사와 v5 개발 서사가 한 repo 에 혼재. 이는 우리 "core 먼저 수정, 파생 문서 후행" 규율의 반례로 인용 가치 있음 (⚠️ 상충은 실재, 어느 쪽이 런타임 진실인지는 버전별로 갈림).
- **core↔user drift 방지 장치는 약함**: 설치가 `~/.claude/` 직접 배치 + `SuperClaude update` 덮어쓰기 구조인데, 사용자 로컬 편집 보존/merge 전략을 설치 문서가 다루지 않음(자인된 gap). 버전·이력 격리(우리 `_internal/versions/`)나 소유-스킬-단일-수정 같은 convention 부재.
- **강점**: RULES priority 시스템(🔴CRITICAL/🟡IMPORTANT/🟢RECOMMENDED)+conflict resolution hierarchy(Safety First / Scope>Features / Quality>Speed)로 규범 충돌을 문서화. 단 전부 프롬프트 규범.
- **대비 요약**: SuperClaude = *convention-first, prompt-enforced, single-runtime, marketplace-plugin 지향*. 우리 하네스 = *core-contract + adapter projection, hook-enforced gate, mem DB SoT*. 두 시스템은 "context pack 큐레이션" 은 유사하나 **강제 계층(mechanism)·multi-harness parity·산출물 버전 격리** 에서 갈린다.

## Sources

- SuperClaude_Framework repo (metadata via `gh api`): default branch `master`, latest release **v4.3.0** (2026-03-22), pushed 2026-06-13 — https://github.com/SuperClaude-Org/SuperClaude_Framework
- `docs/developer-guide/technical-architecture.md` (single-runtime, core/runtime loading, "NOT standalone / no orchestration") — https://github.com/SuperClaude-Org/SuperClaude_Framework/blob/master/docs/developer-guide/technical-architecture.md
- `docs/getting-started/installation.md` (pipx/pip/npm/source, `~/.claude/`, update, customization gap) — https://github.com/SuperClaude-Org/SuperClaude_Framework/blob/master/docs/getting-started/installation.md
- `CLAUDE.md` (entry point, always-loaded vs on-demand, pm_agent/execution modules, no `@import`) — https://github.com/SuperClaude-Org/SuperClaude_Framework/blob/master/CLAUDE.md
- `docs/user-guide/commands.md` (30 `/sc:` commands, brainstorm→workflow→design→implement, convention-not-gate, Serena `/sc:load`·`/sc:save`) — https://github.com/SuperClaude-Org/SuperClaude_Framework/blob/master/docs/user-guide/commands.md
- Repo tree (`gh api .../git/trees/master?recursive=1`): `src/superclaude/**` + `plugins/superclaude/**` 이중 레이아웃, `core/RULES.md|FLAGS.md|PRINCIPLES.md`, `modes/MODE_*.md`(7), `plugins/superclaude/.claude-plugin/plugin.json`, `.mcp.json`, `hooks/hooks.json`, `skills/confidence-check/SKILL.md`
- `plugins/superclaude/.claude-plugin/plugin.json` (v4.3.0; 30 commands/20 agents/7 modes; commands·agents·skills·hooks·mcpServers 매핑) — raw via `gh api`
- `plugins/superclaude/.mcp.json` (context7 + sequential-thinking, npx 기동) — raw via `gh api`
- `plugins/superclaude/hooks/hooks.json` (SessionStart=command script; Stop·PostToolUse=prompt-type hooks — soft enforcement) — raw via `gh api`
- `plugins/superclaude/core/RULES.md` (priority 🔴🟡🟢, conflict hierarchy, Workflow/Session Lifecycle rules, PM Agent PDCA) — raw via `gh api`
- `plugins/superclaude/skills/confidence-check/SKILL.md` (≥90% pre-impl confidence, 5-check, self-test precision/recall 1.0) — raw via `gh api`
- WebSearch 요약 (component counts, v5.0 dev status, 8 MCP servers, npm 패키지명 `@bifrost_inc/superclaude`) — 위 원문으로 교차검증, 일부(8 MCP·v5 ETA)는 원문 미확인으로 ⚠️ 표기

## 미검증 / 상충 항목 (명시)
- v5.0 의 "TypeScript orchestration layer / plugin marketplace 완성형" 범위·ETA — 검색 요약에만 의존, 원문 릴리스노트 미확인.
- `src/superclaude/pm_agent/`·`execution/` Python 모듈의 실제 런타임 관여도 — 소스 직접 실행 확인 안 함(문서는 "guide, not control" 로 규정, technical-architecture 는 orchestration 부재 주장과 상충).
- 광고된 "8 MCP servers" 목록 — plugin `.mcp.json` 엔 2개만 선언(나머지는 사용자 설정/선택 컴포넌트로 추정).
