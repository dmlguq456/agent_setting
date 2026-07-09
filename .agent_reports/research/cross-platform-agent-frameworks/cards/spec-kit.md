# spec-kit (GitHub `github/spec-kit`, CLI: `specify`)

> Spec-Driven Development (SDD) toolkit for AI coding agents. Executable spec 를 먼저 만들고 그로부터 구현을 유도한다.
> Python CLI (`specify`), MIT license, v0.12.x 대. Primarily Python(~95%) + shell/PowerShell scripts.
> **주의**: 카드 작성 시점 기준 활발히 진화 중 — 초기 구조(`_agent_config.AGENT_CONFIG`)와 최신 구조(`integrations/` 서브패키지 registry)가 코드베이스에 혼재. 아래는 두 세대를 모두 표기하되 최신 쪽을 authoritative 로 취급.

## 1. Layer structure — core vs adapter projection

- **핵심 발견 (multi-runtime projection YES)**: spec-kit 은 **하나의 runtime-neutral core 템플릿·스크립트 소스에서 30+ AI coding agent 별 command file 을 projection** 한다. 지원 예: GitHub Copilot, Claude Code, Gemini, Cursor, VS Code, Codex, Kilo Code, Zed, Goose, Kimi, Tabnine 등. [README, deepwiki]
- **Core (runtime-neutral)**: `templates/` 의 SDD command 템플릿(`spec-template.md`, `plan-template.md`, `tasks-template.md`)과 `scripts/bash|powershell/` 유틸이 agent-agnostic 원본. 템플릿은 agent 무관 placeholder 를 쓴다. [repo `templates/`, `scripts/`]
- **Adapter (runtime-specific projection)**: 최신 세대는 `src/specify_cli/integrations/` 아래 **integration 서브패키지 + `INTEGRATION_REGISTRY`** (`_register_builtins()` 로 등록) 가 single source of truth. 각 integration 은 base class 를 상속:
  - `MarkdownIntegration` (`.md` command file, 대부분) / `TomlIntegration` (Gemini, Tabnine 등) / `YamlIntegration` (Goose recipe) / `SkillsIntegration` (`SKILL.md` 하위디렉터리) / `IntegrationBase` (완전 커스텀). [AGENTS.md, deepwiki]
  - 각 integration 이 `config`(`name`,`folder`,`commands_subdir`,`install_url`,`requires_cli`)와 `registrar_config`(`dir`,`format`,`args` placeholder,`extension`)를 선언. `key` 속성은 CLI 실행 파일명과 매칭. [AGENTS.md]
- **Projection 메커니즘 (실제 코드 동작)**: `CommandRegistrar` 가 agent type 별로 같은 템플릿을 렌더링하되 **placeholder 를 format 에 맞게 치환** — Markdown agent 의 `$ARGUMENTS` → TOML/YAML agent 의 `{{args}}`, script 경로는 공용 `{SCRIPT}`. 출력 디렉터리는 `config["folder"] + config["commands_subdir"]` 조합 (예: `.gemini/commands/`, `.kilocode/workflows/`, `.agents/skills/`). 이 덕에 **템플릿 중복 없이** agent 별 format-specific command file 이 생성된다. [deepwiki, AGENTS.md]
- **초기 세대 흔적**: `src/specify_cli/__init__.py` 는 `._agent_config` 의 `AGENT_CONFIG` dict 를 import 하고, `_get_skills_dir()` 이 `agent_config.get("folder")` 로 agent 별 폴더(fallback `.agents/skills`)를 계산. `_install_shared_infra()`/`_refresh_shared_templates()` 가 bundled `core_pack` 에서 스크립트·템플릿을 복사하며 `__SPECKIT_COMMAND_<NAME>__` placeholder 를 markdown agent 는 `.`, skills agent 는 `-` 로 resolve. [src/specify_cli/__init__.py]

## 2. Distribution — installer, templates, updates

- **Installer**: `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z` (또는 `pipx`). npx 아님 — **Python/uv 기반**. 요구: Python 3.11+, Git, 지원 AI agent. [README, installation.html]
- **Template 배포 (classic flow)**: `specify init` 이 GitHub Releases 에서 **per-agent × per-shell zip** 을 다운로드. `download_and_extract_template()` 이 `https://api.github.com/repos/github/spec-kit/releases/latest` 를 조회하고 asset 명 패턴 `spec-kit-template-{ai_assistant}-{script_type}.zip` (script_type = `sh`|`ps`) 을 매칭해 스트리밍 추출. `--script` 플래그가 어느 shell variant 를 command file 에 wire 할지 결정. [deepwiki, releases]
- **Air-gapped/최신 방향**: core template pack 을 CLI 패키지에 **embed** 하는 방향으로 이동 중 (Issue #1711) — `core_pack` 번들 + `_install_shared_infra()`. 즉 다운로드 의존을 줄이는 진화. [issue #1711, src/specify_cli/__init__.py]
- **Updates without losing customizations**: **template resolution priority (high→low)** = (1) project-local overrides `.specify/templates/overrides/` → (2) installed presets → (3) installed extensions → (4) spec-kit core defaults. `_refresh_shared_templates()` 는 default-sensitive 템플릿만 갱신하고 스크립트는 안 건드림. 사용자 커스터마이즈는 overrides/presets 계층에 두어 core 갱신과 분리. [README]
- `specify` 는 `self_check`/`self_upgrade`, `integration list`, `bundle install` 등 서브커맨드 보유(`GITHUB_API_LATEST` 로 버전 체크). [src/specify_cli/__init__.py]

## 3. Context loading strategy

- **Always-on (per-agent memory file)**: `agent-context` extension 이 integration 별 default context 파일을 매핑(`extensions/agent-context/agent-context-defaults.json`) — Claude=`CLAUDE.md`, Gemini=`GEMINI.md`, Cursor=`.cursor/rules/specify-rules.mdc`. `update-agent-context` 스크립트가 project metadata 를 파싱해 이 "memory" 파일들을 동기화 → agent 가 항상 project 상태를 인지. 이 파일들이 agent 세션에 상시 로드되는 층. [deepwiki]
- **On-demand**: SDD command(`/speckit.specify`, `.plan`, `.tasks`, `.implement` 등)는 slash command 호출 시에만 해당 템플릿이 로드된다. 렌더 시점에 CLI 가 `constitution.md`, 사용자 prompt, 기존 파일 내용을 템플릿 marker 에 채워 최종 prompt 를 구성. [WebSearch/blog 요약 — *repo 파일로 직접 재확인 못 함, 다소 unverified*]
- **Project constitution**: `.specify/memory/constitution.md` 가 프로젝트 원칙·거버넌스를 담아 여러 단계에서 참조됨. [README 생성 구조]

## 4. Workflow gate enforcement (spec→plan→tasks→implement)

- **부분적 machine-enforced, 완전하진 않음**: `scripts/bash/check-prerequisites.sh` 가 게이트 역할 일부 수행 — feature 디렉터리 존재 확인, **`plan.md` 는 무조건 required**, `--require-tasks` 플래그로 `tasks.md` 존재를 강제(implement 단계용), `--include-tasks`/`--json` 등 지원. [scripts/bash/check-prerequisites.sh]
- **한계**: 이 스크립트는 `spec` 이 `plan` 에 선행하는지, 3단계 전체 progression 을 검증하지 **않음**. plan.md 를 무조건 요구하고 tasks 를 플래그로 강제할 뿐, 순서 보장은 외부 workflow orchestration(각 slash command 정의)이 담당. → **script 로 뒷받침되지만 순서 자체는 convention 성격이 강함** (state file 로 강제하는 형태 아님). [check-prerequisites.sh]
- feature 디렉터리·번호는 `create-new-feature.sh`, `setup-plan.sh`, `setup-tasks.sh` 가 생성/배치. [README 생성 구조]

## 5. State / artifact management (생성 폴더 구조)

`specify init <project>` 산출:
```
<project>/
├── .specify/
│   ├── memory/constitution.md              # 프로젝트 원칙 (거버넌스)
│   ├── scripts/bash/                        # check-prerequisites, common, create-new-feature, setup-plan, setup-tasks
│   │   (및 powershell/ 변종)
│   └── templates/                           # spec-template.md, plan-template.md, tasks-template.md (+ overrides/)
└── specs/
    └── <NNN-feature-name>/
        ├── spec.md      # /speckit.specify 산출 (what/why)
        ├── plan.md      # /speckit.plan 산출 (tech stack/architecture)
        ├── tasks.md     # /speckit.tasks 산출 (ordered task breakdown)
        ├── data-model.md
        ├── research.md
        └── contracts/
```
- agent 별 command file 은 별도 위치(`.claude/commands/`, `.github/prompts/`, `.gemini/commands/` 등 `folder+commands_subdir`)에 projection. [README, AGENTS.md]
- **tracked**: `.specify/`(core scripts·templates·constitution) + `specs/`(feature artifact) + agent command 디렉터리. 사용자 커스터마이즈는 `.specify/templates/overrides/`. [README]

## 6. Notable design choices — core/adapter/project drift 방지

- **Single-source projection**: agent-agnostic 템플릿 1벌 + placeholder 치환(`$ARGUMENTS`↔`{{args}}`, `{SCRIPT}`)으로 30+ agent 를 커버 → adapter 별 로직 중복 최소화, core 수정이 전 agent 에 전파. (본 gsd-research harness 의 core/CORE.md ↔ adapters/claude 매핑과 동형 철학)
- **Registry as SoT**: `INTEGRATION_REGISTRY`/`_register_builtins()` 를 Python integration 메타데이터의 단일 출처로 명시 — 새 agent 는 (base class 선택 → subpackage → 등록 → optional override) 4단계. [AGENTS.md]
- **계층적 template resolution (overrides > presets > extensions > core)**: 사용자 커스터마이즈를 core 와 물리적으로 분리해 **update 시 core 갱신이 커스터마이즈를 덮지 않음** → project drift 완화. `_refresh_shared_templates()` 는 스크립트 미변경.
- **CLI 는 agent-context state 를 내부에 안 들고**, 외부 rules·`update-agent-context` script 가 관리 → CLI core 와 project-level agent memory 의 관심사 분리. [deepwiki]
- **Extensions vs Presets 구분**: extensions=새 capability/command 추가, presets=기존 workflow 동작 커스터마이즈(용어 강제·템플릿 재구성). Bundles(`bundle.yml`)로 role-oriented 묶음 배포. [README]
- **평가**: multi-runtime projection·registry SoT·계층 resolution 은 drift 방지 설계로 견고. 다만 **workflow 순서 게이트는 machine-enforced 라기보다 스크립트+convention 혼합** — plan.md 존재만 hard, spec→plan→tasks 순서는 orchestration 의존. 이는 본 harness 의 `artifact-guard.sh`(생성 순서 hard 강제)보다 느슨한 편.

## Unverified / caveats
- On-demand 템플릿 렌더 시 constitution+prompt+기존파일을 marker 에 주입한다는 서술은 blog/WebSearch 요약 기반 — repo 원본 파일로 직접 재확인하지 못함(§3). 나머지 핵심 주장(projection, registry, download 패턴, check-prerequisites)은 repo/AGENTS.md/deepwiki 로 교차확인.
- `_agent_config.AGENT_CONFIG`(구세대) vs `integrations/` registry(신세대) 공존은 진행 중 리팩터로 보이며 버전에 따라 정확한 경로가 다를 수 있음.
- star/version 수치(119k stars, v0.12.8 등)는 조회 시점 값, 시간에 따라 변동.

## Sources
- https://github.com/github/spec-kit — main README (repo 구조, installer, supported agents, 생성 폴더 구조, template resolution priority, extensions/presets/bundles)
- https://github.com/github/spec-kit/blob/main/AGENTS.md — integration base class·`config`/`registrar_config`·placeholder·registry·새 agent 추가 절차
- https://raw.githubusercontent.com/github/spec-kit/main/src/specify_cli/__init__.py — `AGENT_CONFIG` import, `_get_skills_dir`, `_install_shared_infra`/`_refresh_shared_templates`, `core_pack`, `GITHUB_API_LATEST`
- https://raw.githubusercontent.com/github/spec-kit/main/scripts/bash/check-prerequisites.sh — prerequisite gate 로직(`plan.md` required, `--require-tasks`, `--json`)
- https://deepwiki.com/github/spec-kit/6-templates-and-scripts — INTEGRATION_REGISTRY, adapter base classes, CommandRegistrar projection, agent-context defaults, download_and_extract_template
- https://github.github.com/spec-kit/ 및 https://github.github.com/spec-kit/installation.html — 공식 문서(installer, high-level)
- https://github.com/github/spec-kit/releases — per-agent/per-shell template zip assets
- https://github.com/github/spec-kit/issues/1711 — core template pack 를 CLI 에 embed (air-gapped) 진화 방향
- https://developer.microsoft.com/blog/spec-driven-development-spec-kit ; https://virtuslab.com/blog/ai/spec-kit-tames-ai-coding-chaos — 보조 요약(교차 참고, 일부 §3 서술 근거)
