# Cross-Platform Agent Frameworks — Analysis Summary

> **Survey mode**: technology (not academic paper survey). 대상: open-source AI coding agent framework 들이 우리 harness (model/tool-neutral `core/` contract → `adapters/{claude,codex,opencode}` runtime projection → per-project `.agent_reports` artifact pipeline) 와 같은 문제 — **neutral "core" layer 와 runtime-specific "adapter" layer 사이의 drift 방지** — 를 어떻게 푸는가.
> **근거 범위**: 이 요약의 모든 주장은 `cards/*.md` 9종에 소급된다. 카드가 unverified/caveat 로 표시한 항목은 여기서도 그대로 표시한다.
>
> **Phase flags**: `chaining_available=false`, `code_search_available=false` (technology mode — academic reference chaining/code search 단계 없음).

---

## 1. Taxonomy — layer strategy 로 프레임워크 분류

두 개의 독립 축으로 분류한다. **축 A = runtime 다중성** (single-runtime 결합 vs multi-runtime projection), **축 B = workflow gate 강제 수준** (convention-only vs machine-enforced).

### 축 A: runtime 다중성

- **Multi-runtime projection (single source → N runtime 변환)**: GSD, spec-kit, BMAD-METHOD, Superpowers, claude-flow, Agent OS, 그리고 전용 projection 도구 (ruler / rulesync / agent_sync / ai-rules-sync). 이들은 하나의 runtime-neutral source 를 두고 installer/registry/converter 가 각 runtime 표면으로 투영한다. 우리 harness 의 `core/` → `adapters/*` 와 동형.
- **Single-runtime (Claude Code 직접 결합)**: SuperClaude — technical-architecture.md 가 "operating exclusively within Claude Code" 명시. "projection" 개념은 있으나 *다른 runtime 으로의 투영*이 아니라 *같은 runtime 안 selective context 주입* (loading 축). 비교축이 근본적으로 다름.
- **표준/명세 (framework 아님)**: Claude Code official plugin/marketplace 는 Anthropic 의 single-runtime plugin **호스트 규격** (다른 프레임워크가 투영해 들어가는 target). AGENTS.md 는 **prose-only 공통 파일 convention** — projection 자체가 불필요한 lowest-common-denominator.

### 축 B: workflow gate 강제 수준

- **Machine-enforced (hook/CLI/state-machine 이 실제 차단)**: GSD (capability manifest `gates[]` + CLI query 평가, `blocking:true` 일부; hook 대부분은 soft), claude-flow (Claude Code hooks 로 lifecycle 강제 + 12 background worker), 우리 harness (`artifact-guard.sh` 생성 순서 hard-block). Superpowers 는 bootstrap hook 재주입 = mechanism, 단계 순서는 instruction("mandatory").
- **Hybrid (state-file state machine + convention)**: BMAD-METHOD (`sprint-status.yaml` / spec frontmatter status state machine + soft `preceded-by`/hard `required` 구분; 기본 트랙은 workflow-script gate, `bmad-loop` 자동화 module 만 실제 hook wire-up), spec-kit (`check-prerequisites.sh` 가 `plan.md` 무조건 required + `--require-tasks` 강제하나 spec→plan→tasks *순서*는 orchestration 의존).
- **Convention-only (prompt/문서 규범, 기계 차단 없음)**: SuperClaude (RULES.md workflow rule, "no gating system", design→implement 점프 가능), Agent OS (명시적 "provides scaffolding without enforcing execution order"; pre-flight check 는 install 시점만).

---

## 2. Per-framework synthesis (핵심 drift-prevention 메커니즘)

- **GSD (`open-gsd/gsd-core`)** — 가장 완성된 multi-runtime 사례. 16개 runtime-role capability manifest (`capabilities/<id>/capability.json`) 가 `commandStyle`/`hooksSurface`/`artifactLayout.converter` 등 runtime 표면 계약을 선언하고 installer converter 가 core 의 Claude-command 정의를 각 runtime 표면으로 변환. drift 방어는 **3중**: (1) installer **hash-manifest** 로 사용자의 직접 수정 감지 → `gsd-local-patches/` 백업 → `/gsd-update --reapply` 로 새 버전에 로컬 patch 재적용, (2) **소유 경계 규칙** (`gsd-` prefix 밖 파일은 installer 불가침), (3) runtime drift 를 converter 로 흡수 ("직접 복사 금지"). 우리 harness 의 fork-drift·버전 트래킹 고민에 가장 직접 대응.
- **spec-kit (`github/spec-kit`)** — `INTEGRATION_REGISTRY` (`_register_builtins()`) 가 SoT 인 **registry + placeholder-substitution** projection. agent-agnostic 템플릿 1벌 + `CommandRegistrar` 가 format 별 placeholder 치환 (Markdown `$ARGUMENTS` ↔ TOML/YAML `{{args}}`, `{SCRIPT}`) 으로 30+ agent 커버. drift 방어 = **계층적 template resolution** (overrides > presets > extensions > core) 로 사용자 커스터마이즈를 core 갱신과 물리 분리. workflow 순서 게이트는 script+convention 혼합으로 우리 `artifact-guard.sh` 보다 느슨.
- **BMAD-METHOD (`bmad-code-org/BMAD-METHOD` v6)** — 3-layer (authoring `src/*-skills/` → installer projection → runtime). `platform-codes.yaml` + `_config-driven.js` 가 20+ tool 로 config-driven 투영, **cross-tool 공유 표준 `.agents/skills`** 로 다수 tool 이 동일 산출물 공유. drift 방어 = **`_bmad/custom/*.toml` 3-layer override** (skill default / team committed / user gitignored) — 재설치해도 로컬 보존, fork 는 "removal mechanism 없음" 최후수단. 게이트는 `sprint-status.yaml` / spec-frontmatter status state machine.
- **SuperClaude (`SuperClaude-Org`)** — **single-runtime (Claude Code 전용)** structured prompt-engineering context pack + Python installer + plugin. drift 방어가 **약함**: `~/.claude/` 직접 덮어쓰기 구조인데 로컬 편집 보존/merge 전략을 설치 문서가 다루지 않음 (자인된 gap). 게다가 **문서 자체가 버전 drift** (technical-architecture 의 "no orchestration" 서사 vs CLAUDE.md/plugin.json 의 pm_agent/execution Python 모듈 광고가 한 repo 에 혼재) — "core 먼저 수정, 파생 후행" 규율의 반례.
- **Superpowers (`obra/superpowers`)** — harness 별 adapter 폴더 (`.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/` …) 분리 + core `skills/` (agentskills.io 표준 SKILL.md). drift 방어 = **session lifecycle 재주입** (bootstrap 을 SessionStart + compaction 후 자동 재주입 → context 유실 skill drift 방지) + **core/실험/커뮤니티 skills 를 별도 repo 로 분리** (`superpowers` vs `-lab` vs `-skills`). 단 plugin update 가 로컬 수정을 어떻게 보존하는지는 문서에서 검증 불가.
- **Agent OS (`buildermethods/agent-os` v3)** — two-tier core (base `~/agent-os/` shared template + project `.agent-os/` committable) + tool adapter. drift 방어 = **profile inheritance** (동일 파일명 child override → 재설치/update 시 로컬 보존, `project-update.sh` 가 `index.yml` regenerate 시 manual description 보존) + `.agent-os/` self-contained committable 로 코드-표준 drift 억제. 게이트는 convention-over-mechanism (명시적 "without enforcing execution order").
- **claude-flow (`ruvnet/ruflo`, npm 은 여전히 `claude-flow`)** — v3 monorepo `@claude-flow/*` 로 core(cli/guidance/hooks/memory/security) vs adapter(`@claude-flow/codex` dual-mode) 구획. 게이트는 **machine (Claude Code hooks 로 lifecycle 강제 + 12 worker auto-dispatch + swarm consensus)** 이나 spec→plan 순서 불변식은 아님. drift 방어 = **MetaHarness snapshot 감사** (config 스냅샷 → 회귀/drift 사후 탐지) + `ruflo verify` (cryptographic witness manifest). 다만 **파일 복사식 스캐폴딩** 모델이라 프레임워크 스스로 367개 중복 SKILL.md drift (#1834) 를 겪는 중 — 배포 모델의 구조적 취약성 자증.
- **Claude Code official plugins (Anthropic 공식)** — fork-drift 에 대한 **공식 답 = fork 안 하고 marketplace source 참조 + version/SHA pin + auto-update 로 당겨오기**. 버전 해석 우선순위 (plugin.json version → marketplace entry version → git SHA), `renames` 맵으로 rename 마이그레이션, `ref`+`sha` pin. 단 소비자가 로컬 수정하며 upstream 도 따라가는 **양방향 divergence 용 3-way merge 도구는 없음** — 로컬 수정은 별도 fork+자체 marketplace 로 흡수.
- **Projection 전용 도구 (ruler / rulesync)** — framework 가 아니라 순수 "single source → N runtime" 빌드 도구. ruler = **concatenation + 파일 복사** (`<!-- Source: -->` 주석으로 traceability, `.bak` 백업). rulesync = **frontmatter per-tool override 라우팅 + tool 별 native 변환**. one-runtime-only 기능 처리의 3전략을 실증 (아래 §4).

---

## 3. Cross-framework comparison table

| Framework | Layer structure | Packaging / install | Context loading | Workflow gate mechanism | State / artifact location | Drift-prevention mechanism |
|---|---|---|---|---|---|---|
| **GSD** | core (`gsd-core/`, `agents/`, `commands/`, `skills/`) + 16 runtime capability manifest + installer converter | npm `@opengsd/gsd-core` (`npx`) **또는** Claude plugin/marketplace; `/gsd-update` | fresh-context-per-agent; file-based `.planning/` state; workflow size-byte budget (XL 90KB); two-stage skill routing | **machine (부분)**: capability `gates[]` + CLI `gsd_run query` 평가, `blocking:true` 일부 (schema/drift); hook 대부분 soft(advisory) | `.planning/` (Markdown + JSON, git-committable, DB 없음); state-transition.cjs 엔진 | hash-manifest drift 감지 → `gsd-local-patches/` → `--reapply` 재적용; 소유 경계 규칙; converter 로 runtime drift 흡수 |
| **spec-kit** | core `templates/`+`scripts/` (agent-agnostic) + `integrations/` registry (base class 별 adapter) | Python `uv tool install specify-cli`; per-agent×per-shell zip from GitHub Releases (→ embed 이동 중) | per-agent memory 파일 (CLAUDE.md/GEMINI.md) always-on; slash command 시 템플릿 on-demand; `constitution.md` | **script+convention 혼합**: `check-prerequisites.sh` = `plan.md` required + `--require-tasks`; spec→plan→tasks 순서는 orchestration 의존 | `.specify/` (memory/scripts/templates) + `specs/<NNN>/` (spec/plan/tasks.md); agent command 는 별도 folder projection | registry SoT; 계층적 template resolution (overrides>presets>extensions>core); `_refresh_shared_templates` 는 script 미변경 |
| **BMAD-METHOD** | authoring `src/*-skills/` → installer projection (`_config-driven.js`) → runtime native | npm `npx bmad-method install` (interactive); `@next` prerelease; module 생태계 | on-demand per-skill (fresh context window 권장); `bmad-help.csv` 경량 catalog; `resolve_config.py` script merge | **state-machine + convention**: `sprint-status.yaml` / spec-frontmatter status; soft `preceded-by` vs hard `required`; `bmad-loop` module 만 실제 hook | `_bmad/` (config 4-layer, `custom/*.toml` override); `{implementation_artifacts}/sprint-status.yaml` + story files | `_bmad/custom/*.toml` 3-layer override (재설치 보존); cross-tool `.agents/skills`; CI validate-skills; fork 는 최후수단 |
| **SuperClaude** | **single-runtime (Claude Code)**; core (always: FLAGS/RULES/PRINCIPLES) vs on-demand loading 축 | pipx/pip/npm `SuperClaude install`; `~/.claude/` 직접 배치; plugin marketplace 지향(v5 계획) | trigger-based selective (command/agent/keyword/flag); FLAGS/RULES/PRINCIPLES always; `@import` 미사용 | **convention-only**: RULES.md workflow rule, confidence-check skill; "no gating system", design→implement 점프 가능 | Serena MCP `.serena/memories/` cross-session; task/plan/memory tracked 되나 not enforced | **약함**: `~/.claude/` 덮어쓰기, 로컬 편집 보존 전략 부재(자인 gap); 문서 자체 버전 drift; 버전 격리 convention 부재 |
| **Superpowers** | harness별 adapter 폴더 (`.claude-plugin/`, `.codex-plugin/`…) + core `skills/` (agentskills.io 표준) | runtime별 개별 설치 (`/plugin install`, `agy`, `pi install`); update 는 agent-dependent | progressive disclosure 3-level (description→body→supporting); `using-superpowers` bootstrap 만 always | **mechanism 쪽 강함**: bootstrap hook 재주입, "mandatory workflows"; 7단계 순차 gate (단계 순서는 instruction) | design doc / plan / git worktree 로 분산; 중앙 store 명시 안 됨 | session lifecycle 재주입 (SessionStart+compaction); core/lab/community repo 분리; writing-skills 로 skill 품질 drift 억제 |
| **Agent OS** | two-tier: base `~/agent-os/` shared template + project `.agent-os/`; tool adapter | install script (email-gated, verbatim 미확인); `project-update.sh` | on-demand/conditional: `/inject-standards` + `index.yml` catalog query (auto-suggest/explicit) | **convention-only (명시)**: "scaffolding without enforcing execution order"; pre-flight check 는 install 시점만 | `product/` + `specs/<feature>/spec.md` + `standards/index.yml`; `.agent-os/` committable | profile inheritance (동일 파일명 override, 재설치 보존); update 시 index regeneration; committable self-contained |
| **claude-flow** | monorepo `@claude-flow/*` core(cli/guidance/hooks/memory) vs adapter(`@claude-flow/codex`) | npm `ruflo`/`npx ruflo init`; MCP server; Claude plugin marketplace (35 plugin) — 3경로 | `SessionStart` restore; SONA/ReasoningBank vector 재사용; init 이 `.claude/`+CLAUDE.md 스캐폴딩 | **machine**: Claude Code hooks (single dispatcher) + 12 worker auto-dispatch + swarm consensus (Raft/Byzantine); 순서 불변식 아님 | Hybrid memory (SQLite+WAL / AgentDB HNSW `agentdb.rvf` / PostgreSQL); `.harness/manifest.json` | MetaHarness snapshot 감사 (drift 사후 탐지); `ruflo verify` witness manifest; **자신이 중복 SKILL.md drift 겪음(#1834)** |
| **Claude Code official** | single-runtime plugin **host 규격** (다른 프레임워크의 projection target) | `/plugin install <p>@<marketplace>`; source: github/url/git-subdir/npm; `~/.claude/plugins/cache` 복사 | progressive disclosure 3-level (name+desc always → body on-invoke → bundled files on-demand); 1536자 truncate | hook (31 event, `PreToolUse` block 가능); skill `disable-model-invocation`/`paths` glob | `~/.claude/skills`(personal) / `.claude/skills`(project); managed>personal>project>bundled override | **fork 안 함**: marketplace source 참조 + version/SHA pin + auto-update; `renames` 마이그레이션; 양방향 merge 도구는 없음 |
| **AGENTS.md 표준** | projection 없음 — 단일 공유 Markdown convention (LCD) | tool 이 파일을 직접 읽음 (20+/60,000+ repo 채택 주장) | 파일 하나 always-read (prose only) | 없음 (prose instruction 전용) | `AGENTS.md` 파일 (dev tips/testing/PR guideline) | 정의상 최소공통분모 — 실행 기능 0, drift 발생 여지 최소 (표현할 게 없어서) |
| **ruler / rulesync** (projection 도구) | `.ruler/`·`.rulesync/` single source → N runtime | npm CLI (`@intellectronica/ruler`, `rulesync generate`) | N/A (build-step; concatenation 또는 frontmatter 라우팅) | N/A — gate 대상이 아니라 규칙 배포 도구 | 각 agent native 위치로 파일 distribute (`CLAUDE.md`, `.clinerules` …) | ruler: `.bak` 백업 + source 주석; rulesync: per-tool override + hook event 정규화 |

---

## 4. Cross-framework 관찰 패턴/테마

**(1) Single-source projection 이 지배적 패턴, 구현 기법은 3갈래.** 거의 모든 multi-runtime 프레임워크가 "core 1벌 정의 → runtime 표면 차이는 변환으로 흡수" 라는 우리 harness 와 동형 철학을 공유. 구체 기법:
- **Manifest/converter 패턴 (GSD)**: `capability.json` 이 runtime 표면 계약(commandStyle/hooksSurface/artifactLayout.converter)을 선언, installer 가 변환. 가장 표현력 높음.
- **Registry + placeholder-substitution 패턴 (spec-kit)**: `INTEGRATION_REGISTRY` SoT + base class 별 format 치환 (`$ARGUMENTS`↔`{{args}}`). 30+ agent 를 템플릿 중복 없이 커버.
- **Config-driven 파일 복제 패턴 (BMAD `platform-codes.yaml`, claude-flow init, ruler concatenation)**: target_dir 선언 → 파일 복사. 단순하나 claude-flow 사례(#1834)처럼 복제본 drift 취약.

**(2) Hash-manifest + patch-reapply 패턴 (GSD 고유).** GSD 만이 installer hash-manifest 로 사용자 직접 수정을 *감지*하고 `gsd-local-patches/` 에 분리 → `--reapply` 로 upstream 갱신본에 로컬 patch 를 재적용하는 **양방향 divergence 관리**를 구현. Claude 공식 규격조차 이 양방향 merge 를 "문서에 없다"고 인정하는 지점을 GSD 는 채운다. 우리 harness 의 fork-drift 관심사에 가장 직접 대응.

**(3) Override-layer 물리 분리 패턴 (spec-kit / BMAD / Agent OS 공통).** 사용자 커스터마이즈를 core 와 물리적으로 다른 계층에 두어 update 가 로컬을 덮지 않게 함 — spec-kit `overrides>presets>extensions>core` resolution, BMAD `_bmad/custom/*.toml` 3-layer (team-committed vs user-gitignored 구분까지), Agent OS profile inheritance (동일 파일명 override). 우리 harness 의 "산출물은 소유 스킬로만 수정 + `_internal/versions/`" convention 과 같은 계보.

**(4) Version/SHA pin + source 참조 패턴 (Claude 공식 marketplace).** fork 자체를 회피 — upstream 을 복사·수정하지 않고 marketplace source + version/SHA pin 으로 참조, `renames` 맵으로 rename 흡수. 소비자-only 시나리오엔 최적이나 양방향 divergence 엔 3-way merge 부재.

**(5) Prose-only lowest-common-denominator 패턴 (AGENTS.md).** projection 을 아예 포기하고 모든 tool 이 읽는 단일 prose 파일로 통일. drift 여지가 최소인 대신 hooks·MCP·skills·machine schema 를 표현할 수 없는 실행 기능 0. 다른 프레임워크들이 이 표준을 per-agent memory 파일 축(spec-kit `agent-context`, ruler 의 `AGENTS.md` 우선순위)으로 포섭.

**(6) One-runtime-only 기능(hooks 등)의 3층 처리 (multi-harness-projection 카드 핵심).** neutral core 를 runtime 에 투영할 때 한쪽에만 있는 primitive 처리는 실증적으로 3전략: **(i) skip+warning** (ruler — Copilot 에 없는 tool 어휘 silent drop, native subagent 없으면 skip), **(ii) event-vocabulary 정규화 + tool별 재작성/plugin 컴파일** (rulesync hooks — canonical camelCase → PascalCase/JS plugin emit), **(iii) prompt-level simulation** (rulesync `s/command` 텍스트 컨벤션). **어느 도구도 hook 같은 실행 격리를 없는 runtime 에서 진짜 재현하지 못하며** 최선이 (ii)·(iii) 관례적 대체 — 우리 harness 의 core→adapter parity 한계 논의에 직접 대응.

**(7) Gate 강제는 스펙트럼이지 이분법 아님.** 순수 convention(SuperClaude, Agent OS 명시적) → state-file state machine(BMAD sprint-status, spec-kit check-prerequisites) → hook/CLI machine-enforced(GSD capability gates, claude-flow, 우리 artifact-guard) 로 연속. 주목할 차이: **gate 의 *대상*이 다름** — GSD/우리 harness 는 산출물 *생성 순서 불변식* (spec→plan→code), claude-flow 는 *agent 조율/합의 lifecycle*, BMAD 는 *story status 전이*. 같은 "machine-enforced" 라도 무엇을 강제하는지가 프레임워크 철학을 가른다.

**(8) File-based state + fresh-context 가 공통 memory 전략.** 대부분 DB 없이 git-committable Markdown/JSON 파일 (GSD `.planning/`, spec-kit `specs/`, BMAD `_bmad/`, Agent OS `.agent-os/`) 로 세션·`/clear` 경계를 넘는다. 예외는 claude-flow (SQLite+HNSW vector DB) 와 SuperClaude (Serena MCP). "fresh context per agent + file 로 복원" 이 context rot 방지의 지배적 관용구.

---

## 5. Gaps / open questions

- **양방향 divergence 관리의 희소성**: 소비자가 로컬 수정하며 upstream 도 따라가는 3-way merge 를 실제 구현한 건 GSD (hash-manifest+reapply) 정도. Claude 공식 규격도 "없다"고 인정. 우리 harness 가 참고할 prior art 는 사실상 GSD 하나 — 검증 심화 가치 있음 (installer file-ops 코드 line 단위는 GSD 카드도 일부만 확인).
- **Gate 대상의 직접 비교 부재**: 프레임워크마다 gate 대상(순서 불변식 vs 조율 vs status 전이)이 달라 "누가 더 강한 gate 인가"를 단순 비교 불가. 우리 harness 의 *생성 순서 불변식* 강제와 가장 가까운 건 GSD capability gate 뿐이고, 그마저 대부분 soft.
- **parity 한계의 정직한 인정**: hook 같은 실행 격리 기능은 어떤 도구도 없는 runtime 에서 진짜 재현 못 함 (multi-harness 카드 결론). 우리 harness 의 core→adapter parity 도 이 한계를 공유하는지, (ii)/(iii) 수준 대체를 쓰는지 자체 점검 필요.
- **버전 넘버링/문서 drift 자증 사례**: GSD (repo 1.7.0-rc.4 vs changelog v1.4x 불일치), SuperClaude (한 repo 내 orchestration 서사 상충), claude-flow (#1834 중복 skill) 모두 프레임워크 스스로 drift 를 겪음 — "core 먼저 수정" 규율의 실효성을 외부 사례로 교차검증할 수 있으나, 각 카드가 unverified 로 남긴 구현 line 단위 확인은 미완.
- **커스터마이즈 보존의 코드 수준 미검증**: BMAD (재설치 시 override file-ops), Agent OS (email-gated install 문서), Superpowers (update 시 로컬 보존) 모두 설계 의도까지만 확인되고 구현 검증은 카드에서 미완 — 우리 harness 설계 참고 전 재확인 권장.

---

## Sources

카드별 1차 출처는 각 `cards/*.md` 의 `## Sources` 절 참조 (repo tree, raw 파일, deepwiki, 공식 문서 URL). 본 요약은 다음 9개 카드에 전적으로 근거:
`cards/gsd.md`, `cards/spec-kit.md`, `cards/bmad-method.md`, `cards/superclaude.md`, `cards/superpowers.md`, `cards/agent-os.md`, `cards/claude-flow.md`, `cards/claude-code-official-plugins.md`, `cards/multi-harness-projection.md`.
