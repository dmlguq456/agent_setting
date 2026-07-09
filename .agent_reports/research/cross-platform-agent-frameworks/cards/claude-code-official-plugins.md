# Claude Code Official Plugin / Marketplace / Hooks / Skills / Agents Architecture

> 조사 시점: 2026-07. 출처는 전부 공식 문서 `code.claude.com/docs/en/*` (Anthropic). 각 주장 옆에 URL 표기, 전체 목록은 하단 `## Sources`.

## 1. Plugin packaging structure

플러그인은 자체 디렉터리 하나로 구성되며, 그 안에 컴포넌트 폴더들과 (선택적) `.claude-plugin/plugin.json` manifest 가 놓인다. [plugins]

**핵심 규칙 (문서가 명시한 common mistake)**: `commands/`, `agents/`, `skills/`, `hooks/` 를 `.claude-plugin/` **안에 넣으면 안 된다**. `.claude-plugin/` 안에는 오직 `plugin.json` 만. 나머지 디렉터리는 전부 plugin root 레벨에 위치. plugin root 는 `~/.claude/` 가 아니라 개별 플러그인 자신의 디렉터리다. [plugins]

**디렉터리 레이아웃** (모두 plugin root 기준) [plugins]:

| Directory / file | Purpose |
|---|---|
| `.claude-plugin/plugin.json` | manifest (컴포넌트가 default 위치를 쓰면 optional) |
| `skills/` | `<name>/SKILL.md` 디렉터리들 (신규 플러그인 권장) |
| `commands/` | flat Markdown skill 파일들 (레거시 — 신규는 `skills/` 사용) |
| `agents/` | 커스텀 agent 정의 |
| `hooks/hooks.json` | 이벤트 핸들러 |
| `.mcp.json` | MCP 서버 설정 |
| `.lsp.json` | LSP 서버 설정 |
| `monitors/monitors.json` | background monitor 설정 |
| `bin/` | 플러그인 enable 동안 Bash 도구 PATH 에 추가되는 executable |
| `settings.json` | enable 시 적용되는 default settings (`agent`, `subagentStatusLine` 키만 지원) |

skill 하나만 배포하는 플러그인은 `skills/` 없이 plugin root 에 `SKILL.md` 를 직접 둘 수 있다. [plugins]

**plugin.json manifest schema** (Quickstart + plugins-reference 참조) [plugins]:
- `name` (string, unique identifier + skill namespace — skill 이 `/name:skill` 로 prefix)
- `description` (string, 플러그인 매니저에 표시)
- `version` (string, **optional**. 설정 시 이 필드가 바뀔 때만 사용자가 업데이트 수신. 생략 + git 배포 시 commit SHA 를 버전으로 사용해 매 커밋이 새 버전)
- `author` (object, `name` required / `email` optional)
- 추가 필드: `homepage`, `repository`, `license` (full schema 는 plugins-reference)

standalone `.claude/` 설정과의 차이: standalone 은 `/hello` 같은 짧은 이름, 플러그인은 `/plugin-name:hello` namespaced (충돌 방지). [plugins]

## 2. Marketplace mechanism

**marketplace 는 카탈로그** — 중앙 discovery, version tracking, 자동 업데이트, 다중 source type(git repo / local path) 지원. [plugin-marketplaces]

**파일 위치**: repo 루트의 `.claude-plugin/marketplace.json`. [plugin-marketplaces]

**marketplace.json schema** [plugin-marketplaces]:
- required: `name` (kebab-case, 사용자당 name 하나만 등록 — 같은 이름 추가 시 기존 대체), `owner` (object: `name` required, `email` optional), `plugins` (array)
- optional 최상위: `$schema`, `description`, `version`, `metadata.pluginRoot`, `allowCrossMarketplaceDependenciesOn`, `renames` (v2.1.193+ — old name→new name 또는 null 매핑)
- 각 plugin entry: required `name` + `source`; optional `displayName`, `description`, `version`, `author`, `homepage`, `repository`, `license`, `keywords`, `category`, `tags`, `strict`, `relevance`, `defaultEnabled`, 그리고 컴포넌트 경로 필드 `skills`/`commands`/`agents`/`hooks`/`mcpServers`/`lspServers`

**Plugin source types** (`source` 필드) [plugin-marketplaces]:
- relative path (`"./my-plugin"`, `./` 로 시작, marketplace root 기준)
- `github` (object: `repo`, `ref?`, `sha?`)
- `url` (git URL: `url`, `ref?`, `sha?`)
- `git-subdir` (monorepo sparse clone: `url`, `path`, `ref?`, `sha?`)
- `npm` (`package`, `version?`, `registry?`)

설치 시 플러그인은 `~/.claude/plugins/cache` 에 복사됨 (in-place 사용 X → `../shared-utils` 같은 외부 경로 불가, symlink 로 우회). [plugin-marketplaces]

**설치/배포/discovery 명령** (`/plugin` 및 CLI `claude plugin`) [plugin-marketplaces, plugins]:
- `/plugin marketplace add <owner/repo | git-url | url | ./local>` (옵션 `--scope user|project|local`, `--sparse`)
- `/plugin marketplace list` / `remove` / `update [name]`
- `/plugin install <plugin>@<marketplace>`
- `/plugin validate .` / `claude plugin validate .`
- 로컬 개발: `claude --plugin-dir ./my-plugin` (또는 `.zip`), `--plugin-url <zip-url>`, `/reload-plugins`

**공식 marketplace**: `claude-plugins-official` (Anthropic 큐레이션, 첫 인터랙티브 실행 시 자동 등록), `claude-community` (커뮤니티 제출, 리뷰 후 등재). [plugins]

**팀 강제**: `.claude/settings.json` 의 `extraKnownMarketplaces` + `enabledPlugins` 로 프로젝트 신뢰 시 자동 프롬프트. 관리자 제한은 managed settings 의 `strictKnownMarketplaces`. [plugin-marketplaces]

## 3. Hooks — event types & settings schema

Hook 은 `settings.json`(user/project/local/managed) 또는 플러그인 `hooks/hooks.json` 의 `hooks` 객체로 설정. 구조: 이벤트명 → matcher 그룹 배열 → 각 그룹 `{ "matcher": <pattern>, "hooks": [ { "type": ..., ... } ] }`. [hooks]

**주요 hook event 종류** [hooks]:
- 세션: `SessionStart`, `SessionEnd`, `Setup`
- 턴: `UserPromptSubmit`, `UserPromptExpansion`, `Stop`, `StopFailure`
- tool loop: `PreToolUse`(block 가능), `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `PermissionRequest`, `PermissionDenied`
- agent/team: `SubagentStart`, `SubagentStop`, `TeammateIdle`, `TaskCreated`, `TaskCompleted`
- 환경/async: `Notification`, `MessageDisplay`, `CwdChanged`, `FileChanged`, `ConfigChange`, `InstructionsLoaded`, `PreCompact`, `PostCompact`, `WorktreeCreate`, `WorktreeRemove`, `Elicitation`, `ElicitationResult`
> (WebFetch 요약이 "31개 이벤트"로 집계 — 위는 대표 목록. tool-name matcher 는 `PreToolUse`/`PostToolUse` 등, `Bash`/`Edit|Write`/`mcp__.*` 정규식 unanchored 지원.) [hooks]

**hook handler `type`**: `command`(shell), `http`, `mcp_tool`, `prompt`(LLM 평가), `agent`(subagent 평가). 공통 필드 `if`(permission-rule 필터, tool 이벤트 한정), `timeout`, `statusMessage`, `async`. Exit code 2 = blocking error(stderr 사용), exit 0 = stdout JSON 파싱(`decision`, `hookSpecificOutput.additionalContext`, `permissionDecision` 등). 경로 placeholder `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`. [hooks]

## 4. Skills — SKILL.md format & progressive disclosure

Skill = `SKILL.md` (YAML frontmatter + Markdown body) 를 담은 디렉터리. Claude Code 는 [Agent Skills](https://agentskills.io) 오픈 표준을 따르고 invocation control / subagent 실행 / dynamic context injection 을 확장. [skills]

**저장 위치 & override 우선순위** [skills]: Enterprise(managed) > Personal(`~/.claude/skills/`) > Project(`.claude/skills/`) > 번들 skill. Plugin skill 은 `plugin-name:skill-name` namespace 라 충돌 안 남. 커스텀 커맨드(`.claude/commands/*.md`)는 skill 로 병합됨.

**frontmatter 필드 (전부 optional, `description` 권장)** [skills]:
- `name` (표시 이름, 기본값 = 디렉터리명)
- `description` (무엇을/언제 — Claude 가 자동 적용 판단에 사용)
- `when_to_use` (트리거 문구 추가; `description`+`when_to_use` 합쳐 skill 리스팅에서 **1,536자로 truncate**)
- `argument-hint`, `arguments` (`$name` 치환)
- `disable-model-invocation` (true → Claude 자동 로드 금지, `/name` 수동 전용)
- `user-invocable` (false → `/` 메뉴 숨김)
- `allowed-tools` / `disallowed-tools` (skill 활성 동안 도구 허용/제거)
- `model`, `paths`(glob — 매칭 파일 작업 시에만 자동 활성), `context: fork`(subagent 실행)

**Progressive disclosure (3-level on-demand 로딩)** — 문서가 명시한 핵심 메커니즘 [skills]:
1. **Level 1 (항상 로드)**: skill 이름 + `description`/`when_to_use` 만 컨텍스트에 상주. "모든 skill 이름은 항상 포함되되, 많으면 description 이 character budget(모델 컨텍스트의 ~1%)에 맞춰 축약/드롭됨. 가장 안 쓰는 것부터 드롭." `/doctor` 로 축약/드롭 현황 확인.
2. **Level 2 (호출 시 로드)**: `SKILL.md` **body 전문**은 skill 이 invoke 될 때만 로드. 한 번 로드되면 이후 턴에도 컨텍스트에 상주(recurring token 비용 → body 는 간결히).
3. **Level 3 (필요 시 로드)**: skill 디렉터리 내 번들 파일(template/examples/scripts/reference doc)은 `SKILL.md` 에서 참조해 두면 Claude 가 필요할 때만 navigate·로드. "10,000줄 도메인 지식을 넣어도 실제 필요 전까지 context 비용 0."

> 예외: subagent 에 skill 을 preload 하면 startup 에 full content 가 주입됨(Level 1→2 구분 없이). malformed frontmatter 시 body 는 empty metadata 로 로드되어 `/skill-name` 은 동작하나 자동 매칭용 description 이 없음. [skills, sub-agents]

## 5. Subagents — definition format

Subagent = YAML frontmatter 를 가진 Markdown 파일. 각자 독립 context window + 커스텀 system prompt(=markdown body) + 도구 제한 + 독립 permission. [sub-agents]

**저장 위치 & 우선순위** [sub-agents]: managed(1, 최고) > `--agents` CLI JSON(2) > `.claude/agents/`(3, project) > `~/.claude/agents/`(4, user) > plugin `agents/`(5). 재귀 스캔, 정체성은 `name` frontmatter 로만 결정(파일명·subfolder 무관, 단 plugin 은 subfolder 가 scoped id `plugin:sub:name` 에 포함).

**frontmatter 필드** [sub-agents]:
- `name` (required, 소문자+하이픈, hook 의 `agent_type` 값)
- `description` (required, 언제 위임할지 — "use proactively" 넣으면 적극 위임 유도)
- `tools` (optional, 생략 시 전부 상속. Skill preload 는 `Skill` 나열 대신 `skills` 필드로)
- `model` (`sonnet`/`opus`/`haiku`/`fable`/full ID/`inherit`, 기본 `inherit`)
- `permissionMode` (`default`/`acceptEdits`/`auto`/`dontAsk`/`bypassPermissions`/`plan`/`manual`)
- 추가: `disallowedTools`, `mcpServers`, `hooks`, `maxTurns`, `skills`, `initialPrompt`, `memory`, `effort`, `background`, `isolation`, `color`, `prompt`(CLI JSON 에서 system prompt)

**도구 제한**: `tools` 화이트리스트 또는 `disallowedTools` 블랙리스트. 내장 Explore/Plan 은 read-only(Write/Edit deny). **보안**: plugin subagent 는 `hooks`/`mcpServers`/`permissionMode` 필드 무시됨(무력화). [sub-agents]

## 6. Upstream sync / fork-drift 문제에 대한 공식 답

Anthropic 플러그인 시스템은 fork-drift 문제에 **명시적 버전·업데이트 메커니즘**으로 답한다 (직접 fork 후 수동 rebase 하는 방식이 아님) [plugin-marketplaces, plugins]:

- **버전 해석 우선순위**: (1) `plugin.json` 의 `version` → (2) marketplace entry 의 `version` → (3) plugin source 의 git commit SHA. `version` 을 생략하면 매 commit 이 새 버전으로 취급되어 자동 최신 추종. 명시하면 그 문자열이 바뀔 때만 업데이트 수신(pin).
- **업데이트 명령**: `/plugin marketplace update [name]` 으로 카탈로그 refresh, `/plugin update` / background auto-update 로 개별 플러그인 갱신. resolved version 이 이미 가진 것과 같으면 skip.
- **pin 정밀도**: `ref`(branch/tag) + `sha`(40자 commit) 로 정확한 커밋 고정. `sha` 가 있으면 upstream branch 삭제돼도(대부분 git host) 설치 성공.
- **release channels**: 같은 repo 의 다른 ref/SHA 를 가리키는 두 marketplace(stable / latest) 로 채널 분리, managed settings 로 사용자 그룹별 배정.
- **rename/remove 마이그레이션**: marketplace `renames` 맵(v2.1.193+)이 old name→new name(또는 null) 을 기록해 기존 사용자가 `plugin-not-found` 없이 자동 이관. append-only history, chain 지원.
- **dependency pinning**: `{plugin-name}--v{version}` git-tag convention + semver range 로 의존 플러그인 버전 제약.

즉 이 프로젝트의 "fork drift" 관심사에 대해, **upstream 을 fork 하지 않고 marketplace source 로 참조 + version/SHA pin + `marketplace update`/auto-update 로 당겨오는 것이 공식 해법**이다. 다만 이는 "제3자 플러그인을 소비"하는 모델에 최적화돼 있고, 소비자가 로컬에서 플러그인을 수정하며 upstream 도 따라가는(양방향 divergence) 시나리오에 대한 3-way merge 류 도구는 문서에 없음 — 로컬 수정은 `strict:false` marketplace 재정의나 별도 fork+자체 marketplace 로 흡수하는 방식.

---

## Sources
- https://code.claude.com/docs/en/plugins
- https://code.claude.com/docs/en/plugin-marketplaces
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/plugins-reference (문서 내 참조 — full manifest/version-management schema)
- https://code.claude.com/docs/en/discover-plugins (문서 내 참조 — 설치/보안)
