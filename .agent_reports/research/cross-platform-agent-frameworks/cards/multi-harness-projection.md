# Multi-Harness Projection: single source → N AI coding agents

작업 주제: "하나의 source of truth 를 여러 AI coding agent harness(Claude Code / Codex CLI / Cursor / Windsurf / OpenCode / Gemini CLI 등)로 projection" 하는 실존 도구를 확인하고, (1) core format 과 projection mechanism, (2) lowest-common-denominator flattening/capability loss, (3) 한 runtime 에만 있는 기능(예: Claude Code hooks)을 없는 runtime 에 어떻게 처리하는지를 정리한다.

결론 요약: 이 카테고리는 **실존한다**. 성숙한 도구가 최소 3개(ruler, rulesync, agent_sync) 있고, prose-only 표준(AGENTS.md)이 별도 축으로 존재. 이 프로젝트(gsd-research)의 harness 는 그 자체가 "core → Claude/Codex projection" 시스템이므로, 아래 도구들은 직접 선행 사례(prior art)에 해당한다. **주의**: `.agent_reports/`·`research/`·`analysis_project/` 산출물 디렉토리가 현재 프로젝트에 없어 이 카드는 web source + agent memory 에만 근거한다.

---

## 1) Ruler (intellectronica/ruler)

- **Repo**: https://github.com/intellectronica/ruler — npm `@intellectronica/ruler`, 30+ agent 지원 주장.
- **Core format**: `.ruler/` 디렉토리 안 Markdown 파일들 = single source of truth. 우선순위: repo root `AGENTS.md` > `.ruler/AGENTS.md` > legacy `.ruler/instructions.md` > 나머지 `.md` sorted.
- **Projection mechanism**: **concatenation + file distribution** (templating engine 아님). 발견된 모든 Markdown rule 을 이어 붙여 각 agent 의 native 위치(`CLAUDE.md`, `AGENTS.md`, `.clinerules` 등)로 복사. 각 조각에 `<!-- Source: <path> -->` 주석을 prepend 해 traceability 확보. 덮어쓰기 전 `.bak` backup 생성.
- **feature 범위**: 단순 rule 외에 MCP server 설정(TOML/legacy JSON, merge/overwrite 전략), **Skills(experimental)** — `.ruler/skills/` → agent native dir(`.claude/skills/` 등), **Subagents(experimental)** — YAML frontmatter Markdown 을 target agent 포맷으로 transform(Claude Code / Cursor / Codex CLI / GitHub Copilot 4종만).
- **Capability loss (문서화된 구체 사례)**:
  - Tool vocabulary translation: Claude 어휘 `Read`/`Grep`/`Bash` → Copilot alias `read`/`search`/`execute`. **"Tools that do not have a Copilot equivalent are dropped silently"** (조용히 drop = lossy).
  - Subagent primitive 부재 처리: "Other agents (Windsurf, RooCode, Aider, Gemini CLI, …) do not yet have a comparable native subagent primitive and are **skipped with a warning**."
  - Skills: native skills 지원 agent 에만 전파, 나머지는 warning 후 skip.
- **한 runtime 전용 기능 처리 방식**: **skip + warning** 전략. 없는 곳엔 억지 emulation 하지 않고 건너뛴다(보수적). MCP 는 full config 를 주고 agent 가 지원 필드만 소비하도록 둠.

## 2) rulesync (dyoshikawa/rulesync)

- **Repo**: https://github.com/dyoshikawa/rulesync — Node.js CLI(npm), 40+ tool + open standard(AGENTS.md, AgentsSkills). PHP(jpcaparas)·Python(PyPI) 이식본도 존재하나 별개 구현.
- **Core format**: `.rulesync/` 디렉토리. rule 파일은 YAML frontmatter + Markdown. frontmatter 에 `root`(overview 1개 = AGENTS.md 급), `targets`, `globs`, 그리고 **tool 별 override 블록**(`cursor:`, `antigravity:`, `devin:`, `augmentcode:`, `kiro:`, `takt:` 등)을 담아 per-tool 세부를 표현.
- **Projection mechanism**: `rulesync generate --targets <tools> --features <features>`. per-tool 세부는 concatenation 이 아니라 **각 tool 의 native 규약으로 변환·라우팅**. 예: Kiro 는 `inclusion` frontmatter(always/fileMatch/manual/auto)로 매핑, OpenCode/Kilo 는 non-root rule 을 `opencode.json`/`kilo.jsonc` 의 `instructions` array 에 non-destructive merge 등록, Qwen 은 `globs`⇄`paths` 매핑. Symlink 를 따라가 shared file 중복 없이 참조 가능(입력 트리 = trust boundary, realpath containment check 없음).
- **feature 범위(rule 이상)**: rules, ignore, MCP, commands, subagents, skills, **hooks**, permissions.
- **feature parity 처리**: support matrix 가 ✅/blank. "A ✅ means the feature is supported in **at least one mode** (project, global, or **simulated**)." → 비대칭 지원 시 flattening 발생.
- **한 runtime 전용 기능 처리 = 두 갈래(이 카드의 핵심 발견)**:
  - **(a) Simulated features** — native command/subagent/skill 이 없는 tool(cursor, codexcli 등)에는 그 기능을 **prompt-level 관례로 emulate**. `--simulate-commands/-subagents/-skills` 플래그로 생성하고, 사용자는 `s/your-command`(s/ = simulate/), "Call your-subagent to…", "Use the skill your-skill to…" 같은 프롬프트 관용구로 호출. 즉 native primitive 부재를 **문서화된 텍스트 컨벤션으로 대체**(진짜 실행 격리는 아님).
  - **(b) Hooks event-name translation** — `.rulesync/hooks.json` 에 **canonical camelCase** event 로 1회 작성 → tool 별 번역: Cursor as-is; Claude Code / Factory Droid / Codex CLI / Gemini CLI / Goose 는 PascalCase; **OpenCode·Kilo 는 JavaScript plugin 으로 emit**(`.opencode/plugins/rulesync-hooks.js`); Copilot/Copilot CLI 는 자체 camelCase 로 rename(`beforeSubmitPrompt`→`userPromptSubmitted`); deepagents-cli 는 dot-notation(`session.start`); Kiro 는 `.kiro/agents/default.json`; Qwen 은 `.qwen/settings.json`. → hook 처럼 "존재하되 표현이 제각각"인 기능은 **event 어휘 정규화 + tool 별 재작성**으로 처리(단순 skip 아님).

## 3) 기타 실존 도구 / 표준

- **agent_sync (yelmuratoff/agent_sync)**: https://github.com/yelmuratoff/agent_sync — "Write AI rules once → sync to Claude, Cursor, Copilot, Gemini and 10 more." (rule-sync 계열, 미상세 검증.)
- **ai-rules-sync (lbb00)**: https://github.com/lbb00/ai-rules-sync — rules/skills/commands/subagents 를 Cursor/Claude Code/Copilot/OpenCode/Trae/Codex/Gemini CLI/Warp 로 sync.
- **AGENTS.md (agentsmd/agents.md)**: https://github.com/agentsmd/agents.md — projection tool 이 **아님**. "a simple, open format for guiding coding agents" = 단일 공유 Markdown **convention**. **prose instruction 전용**(dev tips / testing / PR guideline); hooks·MCP·skills·machine schema 없음. 20+ tool 이 이 파일을 직접 읽는 방식이라 projection 이 불필요(공통 분모를 파일 하나로 통일). 검색상 2025-08 OpenAI 주도 open spec 화(Google/Cursor/Factory 참여), 2025-12 Linux Foundation 산하 Agentic AI Foundation 에 기부, 60,000+ repo 채택 주장(repo README 자체엔 governance 명시 없음 — 2차 source 근거).

---

## 세 질문에 대한 종합 답

1. **core format & projection**: 두 축이 있다. (a) **prose 단일 파일 표준**(AGENTS.md) — projection 없이 모든 tool 이 같은 파일을 읽음, 최소공통분모. (b) **build-step 도구**(ruler=concatenation+복사 / rulesync=frontmatter 라우팅+tool 별 변환). templating engine 보다는 "정규화된 source → per-tool 규약으로 transform/route" 패턴. symlink 는 rulesync 가 중복제거 용도로만 사용(projection 수단은 아님).

2. **LCD flattening / capability loss**: 문서화된 실사례 — ruler 는 Copilot 에 없는 tool 어휘를 **silently drop**, native subagent 없는 tool 은 **skip+warning**. rulesync 는 support matrix 의 blank cell = 그 tool 에서 해당 feature 소실. prose 표준(AGENTS.md)은 정의상 최소공통분모(실행 가능 기능 0).

3. **한 runtime 에만 있는 기능(hooks 등) 처리**: 세 전략이 관측됨 — (i) **skip + warning**(ruler, 보수적), (ii) **event-vocabulary 정규화 후 tool 별 재작성/plugin 컴파일**(rulesync hooks: OpenCode/Kilo 는 JS plugin 으로까지 emit), (iii) **prompt-level simulation**(rulesync simulated commands/subagents/skills: native primitive 없는 곳에 텍스트 컨벤션 `s/…` 로 대체). 즉 "없으면 버린다 / 있으면 어휘만 맞춘다 / 흉내낸다" 세 층위가 실제로 쓰인다. **어느 도구도 hook 같은 실행 격리 기능을 없는 runtime 에서 진짜로 재현하지는 못하며**, 최선이 (ii)·(iii) 수준의 관례적 대체다 — 이 프로젝트 harness 의 core→adapter parity 한계 논의에 직접 대응되는 지점.

## Sources
- https://github.com/intellectronica/ruler
- https://github.com/dyoshikawa/rulesync
- https://github.com/dyoshikawa/rulesync/blob/main/docs/guide/simulated-features.md
- https://github.com/dyoshikawa/rulesync/blob/main/docs/reference/file-formats.md
- https://github.com/agentsmd/agents.md
- https://github.com/yelmuratoff/agent_sync
- https://github.com/lbb00/ai-rules-sync
- https://www.morphllm.com/agents-md-guide (AGENTS.md spec/governance, 2차 source)
- https://addozhang.medium.com/agents-md-a-new-standard-for-unified-coding-agent-instructions-0635fc5cb759 (2차 source)
