# Superpowers (obra / Jesse Vincent)

> "An agentic skills framework & software development methodology that works." — Claude Code 를 위한 composable **skills** 프레임워크. GitHub: `obra/superpowers` (+ `superpowers-skills`, `superpowers-lab`, `superpowers-marketplace`).

## 1. Layer structure — core vs runtime adapter, single vs multi-runtime

- **Multi-runtime (harness-agnostic) 구조가 명시적**. repo top-level 에 harness 별 adapter 폴더가 분리돼 있다: `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`, `.kimi-plugin/`, `.opencode/`, `.pi/extensions/`, `.agents/plugins/`. [repo tree]
- **core = `skills/`** (runtime 중립 SKILL.md 모음) + `hooks/` (session lifecycle) + `scripts/`. 각 harness adapter 폴더는 동일 core skills 를 그 런타임 plugin 규격으로 노출하는 얇은 층. [repo tree]
- README: *"Installation differs by harness. If you use more than one, install Superpowers separately for each one."* → 하나의 core 를 여러 런타임에 각각 배포하는 모델. [README]
- skill 포맷은 런타임 독립 스펙(agentskills.io / agentskills.io/specification)을 따른다 — Claude Code Skills 규격과 호환되는 표준 SKILL.md. [writing-skills/SKILL.md]

## 2. Packaging / installation — upstream update vs user customization

- 런타임별 설치 경로:
  - Claude Code: `/plugin install superpowers@claude-plugins-official` (공식 marketplace)
  - Antigravity: `agy plugin install https://github.com/obra/superpowers`
  - Cursor: `/add-plugin superpowers`
  - Pi: `pi install git:github.com/obra/superpowers` [README]
- **업데이트**: *"Superpowers updates are somewhat coding-agent dependent, but are often automatic."* [README]
- **user customization 과의 공존 전략은 README 에 명시되지 않음** — 대신 커뮤니티 편집 가능한 별도 repo `obra/superpowers-skills` ("Community-editable skills") 와 실험용 `superpowers-lab` 로 확장/커스터마이즈를 repo 분리로 처리하는 것으로 보인다. plugin 업데이트가 사용자 로컬 수정을 어떻게 보존하는지는 **문서에서 검증 불가 (unverifiable)**.

## 3. Context loading strategy — progressive disclosure

- **Claude Code Skills 식 progressive disclosure 를 정식 채택**. 3단계: [writing-skills/SKILL.md]
  1. `description` frontmatter → *discovery* ("Should I load this skill right now?", "Use when..." 트리거, 최대 1024자, 3인칭)
  2. `SKILL.md` body → *understanding* (overview·patterns·quick reference, getting-started 는 150 words 이하 목표)
  3. supporting files (별도 `.md` reference, script/template, `.dot` flowchart) → *implementation*, **on-demand 로만 로드**
- frontmatter 포맷 (verbatim):
  ```yaml
  ---
  name: skill-name-with-hyphens
  description: Use when [specific triggering conditions and symptoms]
  ---
  ```
- "file-per-concern" 모델 — heavy reference 를 SKILL.md 에 embed 하지 않고 링크만 걸어 token 효율 유지. [writing-skills/SKILL.md]
- **always-loaded 층**: `using-superpowers` bootstrap 만 항상 주입 (§4), 나머지 skill 은 전부 on-demand.

## 4. Workflow gate enforcement — convention vs mechanism

- **Mechanism 쪽으로 강함**. README: *"The agent checks for relevant skills before any task. Mandatory workflows, not suggestions."* [README]
- **bootstrap hook (mechanism)**: `hooks/` 가 `using-superpowers` bootstrap 를 *"injects at session startup and again after compaction"* — 세션 시작·compaction 후 자동 재주입으로 skill 사용을 강제하는 진입점. [repo tree / superpowers overview]
- 7단계 순차 workflow gate: Brainstorming → Git worktrees → Plan writing → Subagent development(2-stage review) → TDD(red-green-refactor) → Code review(plan compliance) → Branch finishing. 각 단계는 앞 단계 산출물(예: "after design approval", "with approved design")을 전제로 활성화. [README / overview]
- 다만 이 gate 가 hook 로 hard-block 되는지, 아니면 agent instruction 으로 유도되는지의 강제 수준은 **부분적으로만 검증됨** — bootstrap 주입은 mechanism, 단계 순서 준수는 skill instruction("mandatory") 성격.

## 5. State / artifact management

- Brainstorming 후 **design document 저장**. [overview]
- Writing-plans 가 작업을 2–5분 단위 task 로 분해하며 각 task 는 *"exact file paths, complete code, verification steps"* 포함. [overview]
- git-worktrees skill 이 설계 승인 후 **isolated branch workspace 생성 + clean test baseline 검증**. [overview]
- 중앙집중 artifact store 아키텍처는 **문서에 명시 안 됨** — 산출물은 design doc / plan / worktree 로 분산.

## 6. Drift prevention — notable points

- **session lifecycle 재주입**: compaction 후 bootstrap 재주입으로 컨텍스트 유실에 따른 skill drift 방지. [repo tree]
- **skill 작성 방법론 자체를 skill 로 관리** (`writing-skills`) + testing methodology 내장 → skill 품질 drift 억제. [README]
- description-우선 discovery 규율(트리거만 기술, workflow 요약 금지)로 잘못된 skill 로드 방지. [writing-skills/SKILL.md]
- core skills 와 실험/커뮤니티 skills 를 **별도 repo 로 분리**(`superpowers` vs `superpowers-lab` vs `superpowers-skills`)해 안정 core 오염 방지.

## Sources

- README (main): https://github.com/obra/superpowers/blob/main/README.md
- Repo tree (top-level folders incl. `.claude-plugin/`, `.codex-plugin/`, `skills/`, `hooks/`): https://github.com/obra/superpowers
- SKILL.md format & progressive disclosure: https://raw.githubusercontent.com/obra/superpowers/main/skills/writing-skills/SKILL.md
- Skill spec referenced: https://agentskills.io/specification
- Related repos: https://github.com/obra/superpowers-skills , https://github.com/obra/superpowers-lab , https://github.com/obra/superpowers-marketplace
- Overview (7-stage workflow, git-worktrees/writing-plans behavior): WebSearch aggregate ("obra superpowers claude code skills github")
- Note: `hooks/README.md` returned HTTP 404 — bootstrap 세부는 repo tree 설명 및 overview 기반 (직접 파일 미확인 부분은 본문에 표기).
