# BMAD-METHOD (Breakthrough Method for Agile AI-Driven Development)

- Repo: `github.com/bmad-code-org/BMAD-METHOD` (MIT, 43K+ stars, author Brian "BMad" Madison)
- Current line: **v6.x** (CHANGELOG top = `v6.10.0`, 2026-07-03) — "Skills Architecture". 이 카드는 v6 main 기준 (구 v4 `.bmad-core` 구조와 다름 — 아래 6번 주의).
- 성격: AI coding agent 용 **methodology + 산출물(skill) 프레임워크**. "partnership over automation" 표방, 전 lifecycle (analysis → planning → architecture → implementation).

## 1. Layer 구조 — core 정의 vs runtime/IDE adapter

**핵심 계층은 세 겹으로 분리된다.**

1. **Authoring layer (tool-agnostic source):** 모든 agent/workflow 는 `src/` 아래 **skill 디렉터리**로 저장된다. 두 module 로 그룹화 — `src/core-skills/` (bmad-help, bmad-brainstorming, bmad-party-mode, bmad-shard-doc, review-* 등)와 `src/bmm-skills/` (phase 별: `1-analysis/`, `2-plan-workflows/`, `3-solutioning/`, `4-implementation/`). 각 skill 은 `SKILL.md` (frontmatter `name`+`description`, XML-ish `<workflow>` 스텝) + `customize.toml` 로 구성. persona agent 는 `customize.toml` 에 `[agent]` 섹션, workflow 는 `[workflow]`, standalone skill 은 `customize.toml` 없음 — 이게 "persona vs workflow" 판별의 SoT. (근거: `.claude-plugin/marketplace.json` skill 목록, `src/core-skills/bmad-help/SKILL.md`, `tools/installer/ide/_config-driven.js` 주석)
2. **Projection/installer layer:** `tools/installer/` (Node CLI, `bmad-cli.js`) 가 source skill 을 각 tool 의 규약 경로로 **복제·투영**한다. tool 별 규칙은 `tools/installer/ide/platform-codes.yaml` + `_config-driven.js` 가 config-driven 으로 처리.
3. **Runtime layer:** 실제 coding assistant (Claude Code, Cursor, Codex 등)가 투영된 skill 디렉터리를 자기 native skill/agent 로 로드.

**멀티 어시스턴트 타겟 — Yes, 광범위.** `platform-codes.yaml` 에 등록된 tool 은 (verified list 일부): claude-code, cursor, codex, github-copilot (이상 `preferred: true`), 그리고 amp(Sourcegraph), Google Antigravity, antigravity-cli, auggie, cline, cortex(Snowflake), crush, Factory droid, firebender, gemini CLI, Block goose, hermes, iflow, junie, IBM bob, codewhale, codebuddy, adal, command-code 등 20+ 종.

**투영 메커니즘 (기술):**
- 각 platform 은 `installer.target_dir` (project-local)와 `global_target_dir` (user-home)를 선언. 예: claude-code → `.claude/skills` / `~/.claude/skills`; cursor → `.agents/skills` / `~/.agents/skills`; codex → `.agents/skills` / `~/.codex/skills`.
- **cross-tool 표준 경로 `.agents/skills` (+ `~/.agents/skills`)** 를 다수 tool 이 공유 — cursor, codex, amp, gemini, copilot, goose, crush 등이 같은 디렉터리를 읽는다. 즉 한 번 설치로 여러 tool 이 동일 skill 세트를 본다.
- platform 별 부가 투영: **command pointer** 파일 생성 (예: OpenCode 는 `@skills/<id>` 본문, Copilot 은 `.github/agents` 로 custom-agent picker 용, `commands_target_dir` 필드). 예약어 충돌 회피 로직 존재 (`RESERVED_OPENCODE_COMMANDS`). persona-only surfacing 하는 tool 은 `[agent]` 섹션 있는 skill 만 노출. (근거: `_config-driven.js`)
- web 용 별도 투영: `web-bundles/` 가 Gemini Gems / ChatGPT Custom GPT 용 단일 번들 (prd-coach, ux-coach 등)을 `tools/bundle-web-bundles.js` 로 생성.

## 2. Packaging / installation / upstream update

- **npm 패키지 `bmad-method`**, 설치는 `npx bmad-method install` (interactive picker). prerelease 는 `@next` tag.
- 비대화형 CI 설치: `--directory`, `--modules`, `--tools` (예 `--tools claude-code`), `--set key=val` override, `--yes`. (근거: README, installer)
- 전제: Node v20.12+ (`.nvmrc`), 일부 skill 은 Python 3.11+ (`tomllib`, `uv run`) 사용.
- **module 확장 생태계:** 공식 module = BMM(core, 34+ workflow), BMB(Builder, custom agent 생성), TEA(Test Architect), BMGD/GDS(game), CIS(creative), 신규 **bmad-loop**(unattended dev-loop orchestrator, v6.10 marketplace module). 외부 official module 은 `external-official-modules.yaml` 등록으로 installer picker 에 노출. module 별 `module.yaml` 에 `post-install-notes` (조건부 가능) 로 설치 후 안내.
- **fork drift 회피 = re-install 재투영 + 별도 override layer.** upstream 갱신은 `npx bmad-method install` 재실행으로 source skill 을 최신 복제. 사용자 커스터마이징은 **source 를 fork/수정하지 않고** 별도 override 파일에 둠 (아래 4·5 참고: `_bmad/custom/*.toml`, `config.user.toml`). 이 override 는 재설치해도 보존되는 layer 이므로 fork divergence 를 피한다. (근거: `resolve_customization.py` docstring — 3-layer merge, "No removal mechanism … fork the skill" 를 최후 수단으로만 언급.)
  - ⚠️ *부분 미검증*: 재설치 시 override 디렉터리를 실제로 건드리지 않고 skill 본문만 덮어쓰는지는 installer file-ops 코드까지 읽어 확정하진 않음. 3-layer 설계 의도상 그러하나 코드 line 단위 확인은 안 함.

## 3. Context loading — always vs on-demand, token economy

- **On-demand, per-skill 로드가 기본.** skill 은 각각 독립 `SKILL.md` 로, description frontmatter 로 runtime 이 필요 시 로드 (Claude Code skill 규약과 동일). `bmad-help` SKILL 은 명시적으로 "Recommend running each skill in a **fresh context window**" — 즉 대형 단일 프롬프트 대신 skill 단위로 context 를 갈아끼우는 token 절약 전략.
- **Catalog/manifest 로 카탈로그 자체는 경량 CSV:** `{project-root}/_bmad/_config/bmad-help.csv` (module,skill,display-name,menu-code,phase,preceded-by,followed-by,required,output-location,outputs). help skill 은 전체 skill 본문이 아니라 이 CSV + config JSON 만 읽어 "다음 할 일"을 라우팅 → 전체 catalog dump 회피 ("surface only what's relevant … don't dump the entire catalog").
- **persistent_facts / project-context:** dev workflow 는 `{workflow.persistent_facts}` (verbatim 또는 `file:` glob) 와 `**/project-context.md` 를 로드해 workflow 실행 동안 유지 — 선택적 grounding context. (근거: `bmad-dev-story/SKILL.md` Step 3·4)
- config 병합은 script 로 (프롬프트 토큰 대신 코드로): `resolve_config.py` / `resolve_customization.py` 가 TOML/YAML 을 merge 해 JSON 으로 반환.

## 4. Workflow gates — phase 전환 강제 방식

**메커니즘 + 상태파일 혼합. 순수 convention 이 아니라 status-file 기반 state machine 이 존재하지만, 전역 강제 hook 은 아님.**

- **soft 순서 vs hard gate 구분이 명시됨:** help CSV 의 `preceded-by`/`followed-by` = **soft suggestion**, `required=true` 항목 = **hard gate** ("must complete before the user can meaningfully proceed to later phases"). (근거: `bmad-help/SKILL.md` "these are soft suggestions, not hard gates — see `required` for gating")
- **implementation phase 는 story status state machine 으로 게이트:** `sprint-status.yaml` (`{implementation_artifacts}/sprint-status.yaml`) 의 `development_status` 섹션에서 story key `number-number-name` 의 status(`ready-for-dev`, `in-progress` 등)를 위→아래 순서로 읽어 다음 작업을 선택. dev-story skill 은 story file 의 특정 영역(frontmatter `baseline_commit`, task checkbox, Dev Agent Record, File List, Change Log, Status)만 수정하도록 제한. (근거: `bmad-dev-story/SKILL.md` Step 1 `<step tag="sprint-status">`)
- **HALT condition:** dev-story 는 "session boundary/milestone 로 멈추지 말라"고 강제하되, ready story 없음·validate 필요 등에서 명시적 `HALT` 로 이전 phase skill(create-story, validate-create-story)로 되돌림 — phase 간 전이가 workflow 스텝의 `<check>`/`HALT`/`goto` 로직으로 코드화됨.
- **강제의 성격:** 이 gate 들은 **prompt/workflow-script 내 규칙 + status 파일** 이지, runtime hook(파일시스템 레벨 차단)은 아님. 단 신규 **bmad-loop** module 은 "per-project hooks and policy" 를 설치한다고 CHANGELOG(v6.10) 에 명시 — unattended 자동화 트랙에서는 실제 hook 을 wire-up 함. 즉 기본 트랙은 workflow-script gate, 자동화 module 은 hook 까지 확장.
- **bmad-dev-auto (v6.10):** spec **frontmatter status state machine** (`status: draft` 등)으로 orchestrator 가 poll 하는 방식 — gate 를 파일 frontmatter 상태로 표현. subagent 는 synchronous invoke 강제 (event loop 부재).

## 5. State / artifact 관리 — 폴더·파일

- **프로젝트 상태 루트 = `{project-root}/_bmad/`** (v6; 구버전의 `.bmad-core` 아님):
  - `_bmad/_config/bmad-help.csv` — 설치된 전 module skill manifest
  - `_bmad/config.toml` + `_bmad/config.user.toml` + `_bmad/custom/config.toml` + `_bmad/custom/config.user.toml` — 4-layer 병합 config (core.communication_language, modules.bmm.project_knowledge 등)
  - `_bmad/bmm/config.yaml` — BMM module config (project_name, languages, user_skill_level, implementation_artifacts 경로 등)
  - `_bmad/custom/{skill-name}.toml` (team, committed) / `{skill-name}.user.toml` (personal, gitignored) — per-skill override
  - `_bmad/scripts/` — `resolve_config.py`, `resolve_customization.py`, `memlog.py`
- **implementation 산출물:** `{implementation_artifacts}/sprint-status.yaml` + story files (`*-*-*.md`, 예 `1-2-user-authentication.md`). story file 섹션 = Story, Acceptance Criteria, Tasks/Subtasks, Dev Notes, Dev Agent Record, File List, Change Log, Status.
- **planning 산출물:** PRD / architecture / epics·stories / `project-context.md` (`bmad-generate-project-context`), `product-brief`, `prfaq` 등 phase skill 이 `output-location` 에 생성.
- ⚠️ *부분 미검증*: `implementation_artifacts` 의 정확한 default 상대경로 값(예 `_bmad/bmm/...` 인지 `docs/stories/` 인지)은 config.yaml 실물을 열어 확정하지 않음 — 변수 참조까지만 확인.

## 6. core method ↔ per-tool adapter drift 회피 (notable)

- **단일 source, 기계적 투영:** adapter 를 tool 마다 손으로 쓰지 않고 `platform-codes.yaml` + `_config-driven.js` 가 하나의 skill source 를 각 tool 규약으로 자동 생성 → tool 별 로직 중복/divergence 최소화. 새 tool 지원 = platform-codes 에 target_dir 한 줄 추가에 가까움 ("config-driven").
- **cross-tool 공유 표준 `.agents/skills`** 채택으로 다수 tool 이 동일 산출물을 읽음 → tool 별 사본 divergence 축소.
- **override layer 분리로 upstream/local drift 차단:** 사용자 수정은 source skill 이 아니라 `_bmad/custom/*.toml` 3-layer 로 → 재설치(upstream 갱신)해도 local 커스터마이징 보존, fork 불필요. `resolve_customization.py` 는 "removal mechanism 없음 — 지우려면 fork" 로 fork 를 예외적 최후수단으로만 남겨 divergence 를 억제.
- **CI validation 으로 source 정합성 유지:** `tools/validate-skills.js`, `validate-file-refs.js`, `validate-doc-links.js`, `skill-validator.md`, husky pre-commit — skill 참조·링크 무결성을 빌드 시 검증.
- ⚠️ **버전 주의(중요):** 웹의 다수 블로그·구 문서는 v4 계열의 `.bmad-core/` (agents/·tasks/·templates/·checklists/·workflows/ 서브폴더, `agent.md` persona + `dependencies` on-demand 로딩)를 설명한다. 현재 main 은 그 구조를 **skill 아키텍처 + `_bmad/`** 로 대체했다. "핵심 개념(persona agent, on-demand dependency 로딩, story-driven dev, human-in-loop planning)"은 계승되나 폴더·파일 이름은 v6 에서 바뀌었으므로, 구 자료의 `.bmad-core` 경로를 현행으로 인용하면 안 된다.

## Sources

- `https://github.com/bmad-code-org/BMAD-METHOD` — repo 루트 구조, README (installation, 지원 IDE, module 목록)
- `https://raw.githubusercontent.com/bmad-code-org/BMAD-METHOD/main/README.md` — `npx bmad-method install`, "Claude Code, Cursor, etc.", 12+ agents / 34+ workflows
- `https://raw.githubusercontent.com/bmad-code-org/BMAD-METHOD/main/tools/installer/ide/platform-codes.yaml` — 지원 tool 20+ 종, target_dir/global_target_dir, `.agents/skills` cross-tool 표준
- `https://raw.githubusercontent.com/bmad-code-org/BMAD-METHOD/main/tools/installer/ide/_config-driven.js` — config-driven projection, command pointer 생성, persona vs workflow 판별(`[agent]` in customize.toml)
- `https://raw.githubusercontent.com/bmad-code-org/BMAD-METHOD/main/.claude-plugin/marketplace.json` — skill 목록/모듈 분할(core-skills, bmm-skills phase 1~4), version 6.8.0
- `https://raw.githubusercontent.com/bmad-code-org/BMAD-METHOD/main/src/core-skills/bmad-help/SKILL.md` — help CSV manifest, resolve_config 4-layer merge, soft suggestion vs `required` hard gate, fresh-context-window 권장
- `https://raw.githubusercontent.com/bmad-code-org/BMAD-METHOD/main/src/scripts/resolve_customization.py` — 3-layer TOML override (skill default / team committed / user gitignored), "No removal mechanism … fork the skill"
- `https://raw.githubusercontent.com/bmad-code-org/BMAD-METHOD/main/src/bmm-skills/4-implementation/bmad-dev-story/SKILL.md` — sprint-status.yaml state machine, story file 섹션·수정 제한, HALT 조건, persistent_facts / project-context 로딩
- `https://raw.githubusercontent.com/bmad-code-org/BMAD-METHOD/main/tools/installer/README.md` — module.yaml post-install-notes, external-official-modules.yaml 등록
- `https://raw.githubusercontent.com/bmad-code-org/BMAD-METHOD/main/CHANGELOG.md` — v6.10.0 (2026-07-03): bmad-loop hooks/policy, bmad-dev-auto spec-frontmatter state machine, skills architecture
- 디렉터리 목록: GitHub Contents API (`/repos/bmad-code-org/BMAD-METHOD/contents/{src,tools,...}`)

*미검증 표시 항목*: (2) 재설치 시 override 보존의 file-ops 코드 수준 확인, (5) `implementation_artifacts` default 실경로 값 — 둘 다 설계 문서/변수 참조로는 확인, 구현 line 단위 미확인.
