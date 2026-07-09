# GSD (Get Shit Done) — Technology Deep-Dive Card

> Spec-driven / context-engineering meta-prompting framework for AI coding agents.
> **주의**: 프로젝트가 최근 대규모 리네이밍·이전을 거쳤다. 원본 `gsd-build/get-shit-done` (by TÂCHES, "Get Shit Done") 은 **archived** 상태이고, 활성 개발은 `open-gsd/gsd-core` (npm `@opengsd/gsd-core`, 슬로건 "Git. Ship. Done.") 로 이전됐다. 본 카드는 **활성 repo (`open-gsd/gsd-core`, branch `next`, version 1.7.0-rc.4 기준 — 문서 내 changelog 참조는 v1.43 대까지 존재)** 를 1차 근거로 하고, 원본 개념 (`.planning/`, PROJECT/REQUIREMENTS/ROADMAP/STATE) 은 그대로 계승됨을 확인했다.

---

## 1. Repo structure — core vs runtime-specific

Top-level (open-gsd/gsd-core, branch `next`, 2691 tracked paths):

| 디렉토리 | 역할 | core vs runtime |
|---|---|---|
| `commands/gsd/*.md` | user-facing slash-command 진입점 (prompt-based, YAML frontmatter) | **core** (모든 런타임에 projection) |
| `agents/gsd-*.md` | 35+ 전문화 subagent system-prompt (planner, executor, verifier, plan-checker, security-auditor, code-reviewer, roadmapper, debugger …) | **core** |
| `skills/gsd-*/SKILL.md` | ~61 concrete skill + 6 namespace meta-skill (`gsd-workflow`, `gsd-project`, `gsd-quality`, `gsd-context`, `gsd-manage`, `gsd-ideate`) | **core**, 런타임별로 flat/nested projection |
| `gsd-core/workflows/*.md` | orchestration logic — thin orchestrator가 참조하는 step-by-step 프로세스 (gate/checkpoint 정의 포함) | **core** |
| `gsd-core/{contexts,references,templates}` | 컨텍스트 조각, reference 문서, 산출물 템플릿 | **core** |
| `gsd-core/bin/` (`gsd-tools.cjs`, `gsd_run`, `lib/*.cjs`) | CLI Tools Layer — state machine, phase/verify/init, capability-registry, state-transition | **core** (런타임 중립 Node CLI) |
| `capabilities/<id>/capability.json` | 35개 capability manifest — 16개 **runtime** (claude, codex, cursor, opencode, windsurf, copilot, cline, augment, kilo, kimi, qwen, trae, antigravity, codebuddy, zcode, hermes) + 19개 **feature** (drift, schema-gate, security, tdd, ui, nyquist, research, mempalace, intel, audit …) | **runtime-specific + feature 계약** |
| `hooks/*.js|*.sh` + `hooks/hooks.json` | Claude Code hook 표면 (SessionStart/PreToolUse/PostToolUse/SubagentStop/Stop/PreCompact/FileChanged) | **runtime-specific** (Claude/Codex hook surface) |
| `bin/install.js`, `bin/gsd-mcp-server.js` | npm installer + MCP 서버 | packaging/runtime |
| `.claude-plugin/{plugin.json,marketplace.json}` | Claude Code **plugin + marketplace** manifest | Claude-specific |
| `.opencode/plugins/gsd-core.js` | OpenCode plugin entry (`package.json` `main`) | OpenCode-specific |
| `GEMINI.md`, `AGENTS.md`, `CONTEXT.md` | 런타임별 always-load 문서 | runtime-specific |
| `src/`, `scripts/`, `tests/`, `.changeset/`, `eslint-rules/` | TypeScript 소스, build/lint 스크립트, 테스트, changeset 릴리스 관리 | build/dev infra |

핵심 계층 분리 (docs/ARCHITECTURE.md 의 다이어그램): **Command Layer (`commands/gsd/*.md`) → Workflow Layer (`gsd-core/workflows/*.md`) → Agent (fresh-context subagents) → CLI Tools Layer (`gsd-tools.cjs`) → File System (`.planning/`)**. runtime-neutral 계약은 `gsd-core/`·`agents/`·`commands/`·`skills/` 에 있고, 각 런타임 어댑팅은 `capabilities/<runtime>/capability.json` + installer 가 담당한다.

## 2. Installation / packaging + fork-drift 대응

- **주 배포 = npm package** `@opengsd/gsd-core`, 설치는 `npx @opengsd/gsd-core@latest`. installer(`bin/install.js`)가 런타임(Claude Code/OpenCode/Codex/Cursor/…)·scope(global/local)를 프롬프트로 물어 **런타임별로 변환·설치**한다. README 경고: *"The installer is required for cross-runtime compatibility — do not copy files from `agents/` or `commands/` directly."* (`agents/`/`commands/` 를 직접 복사하지 말 것 — 변환 converter를 거쳐야 함).
- **동시에 Claude Code plugin** 이기도 함: `.claude-plugin/plugin.json` (`commands`/`skills`/`hooks` 필드) + `.claude-plugin/marketplace.json` (marketplace 등록). 즉 npm installer 경로와 Claude plugin/marketplace 경로가 **둘 다** 존재.
- **update/upgrade = `/gsd-update`** (installer 재실행 래퍼). 흐름(docs/how-to/update-gsd.md):
  1. 설치 버전·scope 감지 → 2. npm latest 조회 → 3. changelog diff를 확인 요청 **전에** 보여줌 → 4. 확인 → 5. GSD-managed 디렉토리 안의 **사용자 추가 파일**을 `gsd-user-files-backup/` 으로 백업 → 6. installer 재실행 → 7. update-check 캐시 클리어 → 8. **로컬 수정 파일** 백업 여부 보고.
- **Fork-drift 문제의 실제 대응 메커니즘 (중요)**:
  - **hash-manifest 기반 drift 감지**: installer가 자신이 설치한 파일의 manifest hash 를 보관. 사용자가 GSD 설치 파일(예: agent system-prompt)을 직접 수정하면 hash 불일치로 감지 → `gsd-local-patches/` 에 백업 후 새 버전으로 교체.
  - **`/gsd-update --reapply`**: `gsd-local-patches/` 의 로컬 수정본을 새 설치 파일에 **머지(re-apply)**. 이미 latest면 다운로드 skip 하고 patch reapply만 수행.
  - **경계 규칙**: GSD-managed 디렉토리 **밖**의 파일(`gsd-` prefix 없는 custom agent, `commands/gsd/` 밖 command, `CLAUDE.md`, custom hook)은 installer가 절대 건드리지 않음. → 커스터마이징은 "GSD 소유 영역 밖에 두거나, 소유 영역 안이면 patch/reapply 사이클로 관리" 라는 명시적 모델. (우리 harness 의 fork-drift 고민과 정확히 대응되는 지점.)
  - RC 채널: `@next` dist-tag (`/gsd-update --next|--rc`), allowlist 강제(latest/next 만).

## 3. Command 정의 방식

- Command = `commands/gsd/*.md` — **YAML frontmatter (name, description, allowed-tools) + prompt body**. body가 workflow를 bootstrap. (docs/ARCHITECTURE.md "Commands" 섹션)
- 런타임별 projection: Claude Code = slash `/gsd-command-name`; OpenCode/Kilo = slash-hyphen; **Codex = skill `$gsd-command-name` (shell-var style)**; Copilot = slash; Kimi CLI = Agent Skill `/skill:gsd-...`; Antigravity = Skills.
- Workflow logic 는 command 와 분리되어 `gsd-core/workflows/*.md` 에 있고 command가 이를 참조 (thin orchestrator 패턴). Skill 은 `skills/gsd-*/SKILL.md` (progressive-disclosure).
- 두 단계 hierarchical routing (v1.40): non-recursive skill-loader 런타임(cline/qwen/hermes/augment/trae)에서는 top-level에 6개 namespace router만 노출하고 ~61 concrete skill을 router 아래 nesting → eager listing을 ~67 → ~6 entries로 축소. recursive loader 런타임(claude/cursor/codex/copilot/windsurf/…)은 flat 유지.

## 4. Context injection 전략 / token budget

- **핵심 설계원칙 = "Fresh Context Per Agent"**: 모든 heavy work(research/plan/execute)를 fresh 200K subagent에서 실행, main 세션은 lean(30–40%) 유지 → context rot 방지. (README, docs/ARCHITECTURE.md Design Principle 1·2)
- **File-based state as cross-session memory**: `.planning/` 의 `STATE.md`·`CONTEXT.md` 등 구조화 산출물이 세션·`/clear` 경계를 넘어 컨텍스트를 복원. DB·서버 없음.
- Always-load vs on-demand:
  - always-load(런타임별): `GEMINI.md`/`AGENTS.md`/`CONTEXT.md`, 그리고 slash-command 호출 시 해당 **workflow 파일이 verbatim 으로** 컨텍스트에 로드됨.
  - on-demand: agent가 `gsd-tools.cjs init <workflow>` 로 필요한 context만 로드; concrete skill은 namespace router가 routing table로 지목해야 읽힘.
- **명시적 token-budget 기법**:
  - **workflow size-budget** (`tests/workflow-size-budget.test.cjs`): 워크플로 파일당 **byte 상한** (XL tier 90,000 bytes). line 아님 — Codex `project_doc_max_bytes` 32,768 truncation과 정렬.
  - **two-stage skill routing** (#2792): eager skill-listing token cost 절감(6 router).
  - router description = pipe-separated keyword tag (≤60 chars) — "Tool Attention" 연구 인용, prose 대비 ~40% token으로 라우팅.
  - MCP tool schema 주입 비용(서버당 20k+/turn)은 GSD 밖(`.claude/settings.json` enable/disable)이라고 명시 — GSD가 통제하지 않음.
  - `~92% lower per-turn token overhead` 는 GSD 마케팅/파생 plugin(jnuyens/gsd-plugin) 문구로 등장 — gsd-core repo 파일에서 이 수치를 직접 검증하지는 못함(파생 프로젝트 주장으로 취급).

## 5. spec → plan → execute 진행 gate — 실제 구현

진행 게이트는 **prompt convention + config toggle + 선언적 capability gate + CLI 검증 쿼리** 의 다층 구조. hook은 대부분 **soft(advisory)**, 실제 blocking은 workflow/CLI 계층에서.

- **phase loop**: Discuss → Plan → Execute → Verify → Ship (milestone 당 phase 단위 반복).
- **config `gates.*`** (`.planning/config.json`): `confirm_project`, `confirm_phases`, `confirm_roadmap`, `confirm_breakdown`, `confirm_plan`, `execute_next_plan`, `issues_review`, `confirm_transition` — interactive mode에서 각 단계 확인 체크포인트. `mode: "yolo"` 면 auto-approve. → **prompt/워크플로 주도 게이트**.
- **선언적 capability gate (진짜 blocking 메커니즘)**: `capabilities/<feature>/capability.json` 의 `gates[]` 배열이 workflow 상의 **point** (`plan:pre`, `execute:wave:post`)에 `check.query` (예: `verify.schema-drift`, `verify.codebase-drift`) 를 걸고 `blocking: true|false`, `when: <config flag>`, `onError` 를 선언. CLI Tools Layer(`gsd_run query ...`)가 이 쿼리를 평가해 gate를 집행.
  - 예 1 (**schema-gate**): planning 단계(`plan:pre`)에서 ORM schema 파일(Prisma/Drizzle/Payload/Supabase/TypeORM) 감지 시 planner prompt에 `[BLOCKING] schema push` task를 주입 → "push 없이는 phase가 verification 통과 불가". build/type-check가 통과해도(타입이 config에서 옴) live DB push 누락을 false-positive로 막는 gate.
  - 예 2 (**drift**): `execute:wave:post` 에서 schema drift gate = **blocking:true** (schema 파일 변경됐는데 DB push 미실행 시 verification 차단), codebase drift gate = blocking:false(warn). `plan:pre` 에서 stale STRUCTURE.md 를 warn-only 로 사전 경고.
- **verifier / plan-checker / UAT** = "defense in depth": plan은 실행 전 `gsd-plan-checker` agent가 검증, 실행은 task당 atomic commit, 실행 후 verifier가 phase goal 대비 검증, UAT가 최종 human gate. `config.workflow.{plan_check,verifier,nyquist_validation,ui_safety_gate,security_enforcement,...}` 로 on/off.
- **hook 계층은 soft**: `gsd-workflow-guard.js` 는 주석에 *"This is a SOFT guard — it advises, not blocks. The edit still proceeds."* 라고 명시. `.planning/config.json` 의 `hooks.workflow_guard`(default **false**)로만 켜지고, GSD workflow 밖 직접 edit 시 `/gsd:quick`·`/gsd:fast` 사용을 권고하는 advisory 주입 + state-tracking 우회 경고. `gsd-phase-boundary.sh` (opt-in `hooks.community`)는 `.planning/` 파일 수정 시 "STATE.md 갱신했나?" reminder만 emit. `gsd-read-guard.js` 는 non-Claude 런타임(read-before-edit 미준수 모델)용 advisory. → **hook은 state-tracking 우회를 막는 nudge, 실제 progression 차단은 아님.**
  - 단, `gsd-workflow-guard.js` 에는 예외적 **hard block** 하나 존재: `worktree-agent-*` 브랜치에서 `git add -f/--force` 시 `decision: 'block'` + exit 2 (gitignore 계약 보호).

## 6. State file 관리

- **state 디렉토리 = `.planning/`** (원본의 명명 그대로 계승). 내용물: `PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, `config.json`, `phases/`, `research/`. (docs/ARCHITECTURE.md File System 다이어그램)
- 형식: human-readable **Markdown + JSON** 혼합. `config.json` 이 설정 SoT, `STATE.md` 가 진행 상태(frontmatter + body sections). DB/서버 없음 → git commit 가능(team visibility), `/clear` 후에도 생존.
- **state lifecycle 엔진**: `gsd-core/bin/lib/state-transition.cjs` (ADR-1769) — `STATE.md` 를 pure-core `transitionCore(content, intent, deps)` + injected I/O 로 변환. `FIELD_CLASSIFICATION` 테이블이 frontmatter↔body 충돌 시 어느 필드가 이기는지(preserve-when-unchanged / preserve-always / derive / preserve-if-placeholder) 단일 관리. 필드: `current_phase`, `current_phase_name`, `current_plan`, `status`, `stopped_at`, `paused_at`, `progress.{total,completed}_phases`, `last_activity` 등. `beginPhase` 등 intent 로 phase 전이. 관련 lib: `state.cjs`(주 state, `state.cts` 컴파일)·`phase.cjs`·`verify.cjs`·`init.cjs`·`phase-lifecycle.cjs`.
- **설정 기본값 철학 "Absent = Enabled"**: `config.json` 에 키가 없으면 default `true`. 사용자는 기능을 끄기 위해서만 명시.
- MCP-backed state option: `bin/gsd-mcp-server.js` + `bin/gsd-mcp-server` — 일부 파생/plugin 문구는 "MCP-backed project state" 를 강조하나 core repo의 1차 state 저장은 `.planning/` 파일시스템(`stateIO: filesystem`, capability manifest 명시).

## 7. Multi-runtime 지원 — projection 방식

**강력한 multi-runtime**. 단일 런타임 아님. `capabilities/` 에 **16개 runtime-role capability**: `claude`, `codex`, `cursor`, `opencode`, `windsurf`, `copilot`, `cline`, `augment`, `kilo`, `kimi`, `qwen`, `trae`, `antigravity`, `codebuddy`, `zcode`, `hermes`.

- **projection 메커니즘 = capability manifest + installer converter**. 각 `capabilities/<id>/capability.json` 이 런타임 표면 계약을 선언:
  - `configHome`(예: claude=`.claude`/`CLAUDE_CONFIG_DIR`, codex=`.codex`/`CODEX_HOME`), `configFormat`(settings-json vs toml), `commandStyle`(claude=`slash-hyphen`, codex=`shell-var`), `hooksSurface`(settings-json vs codex-hooks-json), `hookEvents`, `supportTier`(claude=1, codex=1), `installSurface`.
  - `artifactLayout`: kind(skills/commands/agents) × global/local × `converter`(예: `convertClaudeCommandToClaudeSkill`, `convertClaudeCommandToCodexSkill`) × `nesting`(flat/nested) × `recursive`. → **core의 Claude-command 정의를 각 런타임 표면으로 변환**하는 것이 projection의 본질.
  - `hostIntegration`: `embeddingMode`(claude=imperative, codex=declarative), `dispatch`(namedDispatch/nested/maxDepth — claude=5, codex=1 / background / subagentToolkit), `modelMode`, `hookBus`, `stateIO`(filesystem), `transport`(mcp).
- feature capability(drift/schema-gate/security/tdd/ui/nyquist/research/mempalace/…)는 `runtimeCompat.supported: ["*"]` 로 런타임 무관하게 gate/contribution/step을 주입 — **feature ⟂ runtime 직교 설계**.
- **runtime-aware model resolution**: `config.runtime` + `model_policy.runtime_tiers.<runtime>.<tier>` 로 opus/sonnet/haiku tier를 런타임-native model ID(예: `gpt-5-pro`)로 해석. codex/opencode는 inline `model` param 미지원이라 install-time에 agent frontmatter에 model ID를 **정적 embed**(그래서 override 변경 시 `gsd install <runtime>` 재실행 필요), 그 외는 spawn-time 해석.
- `capabilities/claude-orchestration` 은 Claude가 다른 런타임 job을 orchestrate 하는 cross-AI 실행(`config.workflow.cross_ai_execution`) 지원 흔적.

---

## 특기 사항 (drift-prevention 관점 종합)

우리 harness의 fork-drift·버전 트래킹 고민과 직접 대응되는, GSD가 실제로 구현한 3중 방어:
1. **installer hash-manifest**: 설치 파일의 hash를 기록 → 사용자 직접 수정 감지 → `gsd-local-patches/` 백업 → `/gsd-update --reapply` 로 새 버전에 로컬 patch 재적용. (source-of-truth는 upstream, 로컬 수정은 patch layer로 분리 관리)
2. **소유 경계 규칙**: GSD-managed 디렉토리(`gsd-` prefix / `commands/gsd/`) vs 사용자 영역을 명확히 갈라 후자는 installer가 절대 안 건드림. (우리의 "산출물은 소유 스킬로만 수정" convention과 유사)
3. **런타임 drift는 converter로 흡수**: core를 한 번 정의하고 런타임 표면 차이는 capability manifest converter가 흡수 → "직접 복사 금지" 강제로 fork별 표면 drift를 원천 차단.

## 미검증 / 주의

- 원본 `gsd-build/get-shit-done` 은 archived. 별 수(58.9K~64.7K)·contributor·release 통계는 블로그/검색 요약 값이라 시점별로 상충(v1.38.5 April 2026 vs v1.43 changelog vs plugin.json 1.7.0-rc.4) — **버전 넘버링이 repo(1.7.0-rc.4)와 docs changelog(v1.4x)에서 불일치**하므로 정확한 최신 버전은 릴리스 페이지 재확인 필요. 확정적으로 단언하지 않음.
- `~92% token overhead 감소`, `MCP-backed state` 강조는 주로 파생 plugin(`jnuyens/gsd-plugin`)·마케팅 문구 — gsd-core 소스에서 수치 자체는 직접 검증 못 함.
- `jnuyens/gsd-plugin`(Claude Code-native GSD 재구현)과 `rokicool/gsd-opencode`(OpenCode 포트)는 별개 커뮤니티 파생 repo. 본 카드는 canonical `open-gsd/gsd-core` 기준.

## Sources

- https://github.com/gsd-build/get-shit-done (원본, archived; README가 open-gsd/gsd-core로 이전 안내)
- https://github.com/open-gsd/gsd-core (활성 canonical repo)
- https://api.github.com/repos/open-gsd/gsd-core (metadata: default_branch=next, archived=false)
- https://api.github.com/repos/open-gsd/gsd-core/git/trees/next?recursive=1 (전체 파일 트리, 2691 paths)
- https://raw.githubusercontent.com/open-gsd/gsd-core/next/README.md
- https://raw.githubusercontent.com/open-gsd/gsd-core/next/package.json
- https://raw.githubusercontent.com/open-gsd/gsd-core/next/.claude-plugin/plugin.json
- https://raw.githubusercontent.com/open-gsd/gsd-core/next/.claude-plugin/marketplace.json
- https://raw.githubusercontent.com/open-gsd/gsd-core/next/hooks/hooks.json
- https://raw.githubusercontent.com/open-gsd/gsd-core/next/hooks/gsd-workflow-guard.js
- https://raw.githubusercontent.com/open-gsd/gsd-core/next/hooks/gsd-phase-boundary.sh
- https://raw.githubusercontent.com/open-gsd/gsd-core/next/hooks/gsd-read-guard.js
- https://raw.githubusercontent.com/open-gsd/gsd-core/next/docs/ARCHITECTURE.md
- https://raw.githubusercontent.com/open-gsd/gsd-core/next/docs/CONFIGURATION.md
- https://raw.githubusercontent.com/open-gsd/gsd-core/next/docs/how-to/update-gsd.md
- https://raw.githubusercontent.com/open-gsd/gsd-core/next/capabilities/claude/capability.json
- https://raw.githubusercontent.com/open-gsd/gsd-core/next/capabilities/codex/capability.json
- https://raw.githubusercontent.com/open-gsd/gsd-core/next/capabilities/drift/capability.json
- https://raw.githubusercontent.com/open-gsd/gsd-core/next/capabilities/schema-gate/capability.json
- https://raw.githubusercontent.com/open-gsd/gsd-core/next/capabilities/schema-gate/fragments/plan-pre.md
- https://raw.githubusercontent.com/open-gsd/gsd-core/next/gsd-core/bin/lib/state-transition.cjs
- https://github.com/jnuyens/gsd-plugin (파생 Claude Code-native plugin — 대조용)
- https://github.com/rokicool/gsd-opencode (파생 OpenCode 포트 — 대조용)
