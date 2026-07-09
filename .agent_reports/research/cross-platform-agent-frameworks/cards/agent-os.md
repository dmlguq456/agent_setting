# Agent OS (Builder Methods / Brian Casel)

> "A system for injecting your codebase standards and writing better specs for spec-driven development." GitHub: `buildermethods/agent-os` (v3.0). 표준(standards) 추출·주입 + spec-driven workflow 미들웨어.

## 1. Layer structure — core vs runtime adapter, single vs multi-runtime

- **명시적 multi-runtime**: *"Works alongside Claude Code, Cursor, Antigravity, and other AI tools."*, *"Any language, any framework"*, *"Works with any AI tool, any context."* [README / buildermethods.com/agent-os / DeepWiki]
- **레이어 (4)**: Standards(코딩 컨벤션 문서) · Instructions(context injection) · Commands(markdown 명령) · Tool-specific adapters. [buildermethods.com / DeepWiki]
- **Two-tier core**:
  - Base install `~/agent-os/` — `config.yml`, `profiles/`, 공유 scripts 저장. **명령을 직접 실행하지 않는 shared template repository**. [DeepWiki]
  - Project install `.agent-os/` — *"self-contained, committable to version control"*, 외부 의존 없음. [DeepWiki]
- **Runtime adapter 층**: 5개 command(`/discover-standards`, `/index-standards`, `/inject-standards`, `/shape-spec`, `/plan-product`)가 base·project 양쪽 markdown 으로 정의되고, **Claude Code 는 `.claude/commands/agent-os/` 로 복사본을 받음**; 다른 tool 은 command 를 직접 invoke. [DeepWiki] (Claude 전용 복사 경로는 DeepWiki 2차 출처 기반 — repo 직접 파일 미확인)
- repo top-level: `commands/agent-os/`, `profiles/default/global/`, `scripts/`, `config.yml`, `CHANGELOG.md`. [repo tree]
- **Runtime scope**: *"single-runtime per project installation"* — project install 은 한 런타임 기준, base 가 공유 템플릿. [DeepWiki]

## 2. Packaging / installation — upstream update vs user customization

- 설치는 *"a simple installation script"* (정확한 curl/npm 형식은 email-gated 문서라 **verbatim 미확인**). [buildermethods.com/agent-os]
- **inheritance 기반 커스터마이즈 보존**: `config.yml` 이 profile inheritance chain 정의. `project-install.sh` 가 `common-functions.sh` 의 `get_profile_inheritance_chain()` 으로 관계 해석, *"Child standards with same filename override parent standards."* → 사용자는 **동일 파일명 override 로 로컬 수정** 유지. [DeepWiki]
- **update**: `project-update.sh` 가 standards 를 sync 하면서 project customization 보존; `standards/index.yml` regenerate 시 *"preserving manual descriptions in metadata."* [DeepWiki]
- `config.yml` (v3.0) verbatim 확인: `version: 3.0`, `default_profile: default`, inheritance 예시는 주석 처리(profile-a inherits_from: default 등), *"Profiles not listed here still work, they just have no inheritance."* tool(claude_code/cursor) enable flag 은 이 파일엔 없음 → tool adapter 설정은 profile 하위(추정, 미확인). [config.yml]

## 3. Context loading strategy — always-loaded vs on-demand

- **on-demand / conditional 이 핵심**. `/inject-standards` 가 *"Analyzes current context to propose relevant standards"* (auto-suggest) 또는 명시 지정(explicit) — `index.yml` 를 query 해 **관련 standards 만 조건부 로드** (always-load-all 아님). [DeepWiki]
- 모든 산출물은 markdown 파일 → 파일 참조 기반 로딩. [buildermethods.com]
- `/shape-spec` 이 product doc context 와 함께 `/inject-standards` 를 자동 호출해 타겟 요구수집. [DeepWiki]
- **핵심 대비**: Superpowers 는 Claude Code Skills 의 frontmatter-description 기반 progressive disclosure(런타임 native)를 쓰는 반면, Agent OS 는 **command(`/inject-standards`) + `index.yml` catalog 기반의 자체 명시적 주입** 방식 — 런타임 skill loader 가 아니라 프레임워크 command 로 컨텍스트를 조립. [DeepWiki / writing-skills 대조]

## 4. Workflow gate enforcement — convention vs mechanism

- **Convention over mechanism (명시)**: *"The system provides scaffolding (`product/`, `specs/`, `standards/`) without enforcing execution order."* — hard gate 없음. [DeepWiki]
- `/shape-spec` 이 질문 전 `mission.md`·`roadmap.md`·`tech-stack.md` 를 읽어 **convention 으로 spec-driven 흐름을 유도**(강제 아님). [DeepWiki]
- workflow 단계: Discover → Inject → Shape → Execute (또는 plan-product / create-spec / shape-spec / execute 계열). [buildermethods.com / DeepWiki]
- **Pre-flight checks 는 install 시점에만** (directory validation, profile inheritance circular dependency detection) — 런타임 workflow gate 가 아니라 setup 무결성 검사. [DeepWiki]

## 5. State / artifact management

- Product 층: `product/mission.md`, `roadmap.md`, `tech-stack.md` (product vision). [DeepWiki]
- Spec 층: `specs/[feature-name]/spec.md` (feature 명세). [DeepWiki]
- Standards 층: `standards/index.yml` — **auto-generated catalog + detection metadata** (도메인별 `api/`, `backend/` subdir). [DeepWiki]
- project install `.agent-os/` 전체가 **version control commit 가능** — 산출물이 repo 에 남는 명시적 state. [DeepWiki]

## 6. Drift prevention — notable points

- **inheritance-based standards merging + update 시 index regeneration** 으로 일관성 유지. [DeepWiki]
- `index.yml` 구조가 현재 standards 를 indexed pattern 과 비교해 **drift detection** 가능하게 함. [DeepWiki]
- **`.agent-os/` self-contained + committable** → 표준이 코드와 함께 버전관리돼 코드-표준 drift 억제. [DeepWiki]
- 철학상 *"prevents problems before AI generates a single line of code"* (사후 lint 아닌 사전 표준 주입) — drift 를 생성 이전 단계에서 차단. [WebSearch aggregate]

## Sources

- README: https://github.com/buildermethods/agent-os/blob/main/README.md
- Repo tree (top-level: `commands/agent-os/`, `profiles/default/global/`, `scripts/`, `config.yml`): https://github.com/buildermethods/agent-os/tree/main
- config.yml (verbatim v3.0, default_profile, inheritance): https://raw.githubusercontent.com/buildermethods/agent-os/main/config.yml
- Official docs (layers, workflow, install landing — 설치 세부는 email-gated): https://buildermethods.com/agent-os , https://buildermethods.com/agent-os/installation
- DeepWiki (v3.0 architecture — base/project two-tier, inheritance, inject-standards, convention-over-mechanism; 2차 출처): https://deepwiki.com/buildermethods/agent-os
- WebSearch aggregate ("Builder Methods agent-os github Brian Casel"): including https://www.blog.brightcoding.dev/2026/07/06/agent-os-the-revolutionary-system-for-ai-powered-code-standards
- Note: 설치 정확한 command·profile 내 tool adapter enable flag 은 email-gated / repo 직접 미확인 → 본문에 unverifiable 표기.
