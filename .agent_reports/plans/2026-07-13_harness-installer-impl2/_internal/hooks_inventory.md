# INST-OPEN-1 — hook 전수 조사 + Claude plugin 탑재 결정 (draft)

> 조사 대상: `hooks/*.sh` (전수) + `utilities/workflow-guard-hook.sh` + `adapters/claude/settings.json`
> 등록 현황. 판정 기준(task/PRD §INST-OPEN-1): **self-contained + fail-open 가드만** 탑재
> (하네스 상태 = mem DB · jobs.log · artifact root 부재 시 조용히 no-op). **memory(mem-\*) ·
> statusline(herdr) · dispatch 계열은 제외**(CLI 설치 전제). plugin 은 설치본 self-contained →
> hook 경로는 `${CLAUDE_PLUGIN_ROOT}` 재기준, 영속 상태는 `${CLAUDE_PLUGIN_DATA}`.
> **이 표는 code-execute 가 생성기(`sync-native-plugin.py`)의 hook 탑재 목록으로 그대로 소비.**

## 판정 표 (settings.json 등록 hook 전수)

| hook (event) | 계열 | self-contained? | fail-open? | 판정 | 사유 (한 줄) |
|---|---|---|---|---|---|
| `git-state-guard.sh` (PreToolUse) | guard | ✅ git 만 의존, AGENT_HOME 무 | ✅ non-git dir → `exit 0` (L39-40) | **채택** | merge/rebase/detached HEAD 중 편집 차단 — 하네스 상태 무관, 어떤 소비자에게도 유효한 순수 git 가드 |
| `artifact-guard.sh` (PreToolUse) | guard | ✅ cwd 상향 탐색만, AGENT_HOME 무·마커는 artifact root 내부 | ✅ artifact root 없으면 `exit 0` (L69) | **채택** | autopilot 산출물 생성 순서 강제 — plugin 이 싣는 skills 와 짝. artifact root 부재 시 조용히 no-op |
| `spec-skill-gate.sh` (PreToolUse) | guard(spec) | ⚠️ `$AGENT_HOME/.spec-grounding` 마커 write | ✅ spec 없으면 통과 | **제외(defer)** | spec-read-marker 와 짝 + grounding 상태를 AGENT_HOME 에 write → `${CLAUDE_PLUGIN_DATA}` 재기준 배선 필요. cycle 2 self-contained 보장 위해 이월(소비자 spec 파이프 지원 원하면 재검토) |
| `spec-read-marker.sh` (PostToolUse) | marker | ⚠️ `$AGENT_HOME/.spec-grounding` write | ✅ | **제외(defer)** | 위 gate 의 짝 — 함께 이월 |
| `core-first-guard.sh` (PreToolUse) | guard(dev) | ⚠️ `$AGENT_HOME/.core-grounding` + core/adapters 구조 | ✅ repo 밖 통과 | **제외** | 하네스 _자체 개발_(core/ 먼저 편집) 가드 — skills 소비자에겐 무의미(repo core/ 편집 안 함) |
| `core-read-marker.sh` (PostToolUse) | marker | ⚠️ `$AGENT_HOME/.core-grounding` write | ✅ | **제외** | 위 core-first-guard 의 짝 |
| `builtin-memory-guard.sh` (PreToolUse) | **memory** | ⚠️ deny 메시지가 `mem.py` 지시 | ✅ | **제외** | memory 계열 — mem CLI 부재 시 deny 안내가 오도. CLI 설치 전제 |
| `mem-turn-nudge.sh` (UserPromptSubmit) | **memory** | ✕ mem DB | — | **제외** | memory 계열 |
| `mem-recall-inject.sh` (UserPromptSubmit) | **memory** | ✕ mem DB | — | **제외** | memory 계열 |
| `mem-briefing-inject.sh` (UserPromptSubmit) | **memory** | ✕ mem DB | — | **제외** | memory 계열 |
| `mem-distill-dispatch.sh` (SessionEnd) | **memory+dispatch** | ✕ | — | **제외** | memory+dispatch 계열 |
| `mem.py sync` / `mem.py inject` (SessionEnd/Start) | **memory** | ✕ mem DB | — | **제외** | memory 계열(hook script 아닌 mem CLI 직호출) |
| `herdr-agent-state.sh` (Perm/Pre/Session/Stop) | **statusline** | ✕ HERDR_ENV/SOCKET | ✅ env 없으면 `exit 0` | **제외** | herdr statusline 통합 — statusline 계열 |
| `workflow-guard-hook.sh` (Session/UserPrompt) | **statusline** | ⚠️ AGENT_HOME + 모드 상태 write | ✅ | **제외** | 워크플로우 모드 신호(📌/⚡) statusline 표면 — statusline 계열 |
| `stage-dispatch-reminder.sh` (PreToolUse) | **dispatch** | ✕ dispatch-headless.py 전제 | ✅ | **제외** | conductor/스테이지 분사 인프라 전제 — dispatch 계열 |
| `worktree-path-guard.sh` (PreToolUse) | **dispatch** | ✕ jobs.log/worktree 컨벤션 | ✅ | **제외** | worktree 분사 컨벤션 전제 — dispatch 계열 |
| `design-postwrite.sh` (PostToolUse) | design | ✕ `node AGENT_HOME/tools/design-mcp/...` 실행 | — | **제외** | plugin root 밖 node 툴 실행 — self-contained 위반 |
| `spec-sync-nudge.sh` (PostToolUse) | nudge(spec) | ⚠️ AGENT_HOME + spec 상태 | ✅ | **제외(defer)** | spec 파이프 nudge — spec-skill-gate 와 함께 이월 |

## 결론 — cycle 2 채택 set = **2개**

```
git-state-guard.sh      (PreToolUse)
artifact-guard.sh       (PreToolUse)
```

두 hook 모두 (1) AGENT_HOME 참조 0 (self-contained), (2) 하네스 상태 부재 시 `exit 0` no-op
(fail-open), (3) memory/statusline/dispatch 계열 아님. plugin `hooks/hooks.json` 은 이 둘을
`PreToolUse` 에 `${CLAUDE_PLUGIN_ROOT}/hooks/<name>` 경로로 등록한다.

**이월(defer) 후보** = spec-skill-gate + spec-read-marker + spec-sync-nudge (spec 파이프 3종
묶음). 채택하려면 `.spec-grounding` write 를 `${CLAUDE_PLUGIN_DATA}` 로 재기준하는 배선이
필요 — cycle 2 self-contained 원칙을 흐리므로 별도 사이클. **소비자가 plugin 만으로 spec 파이프를
쓰려는 요구가 확인되면 재개.**

## PRD 갱신 필요 여부 (code-report 에 명시할 것)

PRD §INST-OPEN-1 은 "파일별 목록은 구현 plan 에서 확정" 이라 열어 둔 상태. 본 표로 **파일별
확정 완료** → **INST-OPEN-1 closeable**. 단 이 스테이지는 prd.md 를 편집하지 않는다 —
code-report 가 final_report 에 "PRD §INST-OPEN-1 을 '확정(채택 2 / defer 3 / 제외 나머지)'
으로 닫을 수 있으며, 실제 prd 편집은 main orchestrator 의 autopilot-spec update 몫" 이라고
기록한다.

---

## 선례 정독 노트 — `adapters/codex/bin/sync-native-plugin.py` (168줄)

동형 이식할 골격(Claude 판이 그대로 미러):

- **상수 블록** (L15-24): `ROOT = parents[3]`, `ADAPTER`, `PLUGIN_NAME`, `PLUGIN_ROOT`,
  `MARKETPLACE_ROOT`, `MARKETPLACE`(json 경로), `MARKETPLACE_PLUGIN_LINK`(symlink),
  `MARKETPLACE_PLUGIN_TARGET`(상대경로), `SKILLS`, `VALIDATOR`(optional).
- **`plugin_json()` / `marketplace_json()`** (L27-73): dict 리터럴 반환 — 결정론(날짜/타임스탬프 무).
- **`write_json()`** (L76-78): `json.dumps(indent=2)+"\n"`, parent mkdir.
- **`sync()`** (L81-99): 전제 존재 확인 → plugin.json write → `skills/` **shutil.copytree**
  (기존 트리 rmtree 후 재복사 = 손편집 무효화) → marketplace.json write → marketplace 내
  plugin symlink 재생성.
- **`check_file()` + `check()`** (L102-152): plugin.json/marketplace.json 바이트 일치 →
  각 SKILL.md 원본 대조 → 잉여 파일 탐지(expected set) → (있으면) 외부 validator 실행 →
  `stale[]` 비면 exit 0, 아니면 stale 나열 후 exit 1.
- **`main()`** (L155-164): `--check` → `check()`, else `sync()`.

**Claude 판 차이점(주의):**
1. `ADAPTER = ROOT/"adapters"/"claude"`; `PLUGIN_NAME="agent-harness-claude"`;
   marketplace 는 `.claude-plugin/marketplace.json`(codex 는 `.agents/plugins/`);
   plugin.json 은 `.claude-plugin/plugin.json`.
2. **skills 뿐 아니라 agents + hooks + hooks.json 도 복사** — codex 생성기는 skills 만 담지만
   Claude plugin 은 skills(28) + agents(9) + hooks(2 채택) + hooks.json 을 물리 포함.
   → `sync()`/`check()` 를 3~4 종 콘텐츠로 확장(각각 copytree/copy + check 대조).
3. **`.mcp.json` 부재 확인**(repo root·adapters/claude 둘 다 없음) → MCP 콘텐츠 미탑재.
4. **`bin/` 미탑재**: `adapters/claude/bin/` = dispatch-headless.py·mem-distill-worker.sh·
   install-windows.sh (전부 dispatch/mem/Windows 계열, 소비자 self-contained bin 아님) → skip.
5. **agents frontmatter**: plugin agents 는 `hooks`/`mcpServers`/`permissionMode` frontmatter
   를 Claude 가 무시 → **verbatim 복사**(스트립 불요), 생성기 docstring 에 "이 키들은 plugin
   컨텍스트에서 inert" 명시.
6. plugin.json 은 이미 skeleton 존재(`name`/`description`/`author`) — 생성기가 결정론 재생성.
   settings 키는 `agent`·`subagentStatusLine` 만 유효 → plugin.json 에 일반 settings 키 미포함.

## 선례 정독 노트 — `tools/install/drivers/codex.py` `_plugin_action` (L33-86)

Claude `_plugin_action` 이 미러할 골격:

- marketplace source = `paths.resolve_source(<repo-local marketplace path>)`;
  `marketplace_cmd = [CLI, "plugin", "marketplace", "add", <source>, "--json"]`;
  `plugin_cmd = [CLI, "plugin", "add|install", <spec>, "--json"]`.
- **dry_run** → 두 명령 문자열을 `detail` 로 반환(`status:"planned"`), subprocess 미실행.
- **CLI 부재**(`shutil.which(CLI) is None`) → `status:"skipped"` SKIP 반환.
- marketplace add → returncode≠0 이면 `status:"blocked"`; timeout/FileNotFound → blocked.
- plugin add/install → 동일 패턴; 성공 시 `status:"registered"`.
- `subprocess.run(..., capture_output=True, text=True, timeout=60)`.

**Claude 판 차이점(주의):**
1. CLI 명령어: codex 는 `codex plugin add <spec>`, Claude 는 `claude plugin install <spec>`
   (공식 CLI 동사 `install`, PRD §"CLI wrapping" 확인). marketplace 는 양쪽 `marketplace add`.
2. spec = `agent-harness-claude@agent-harness`. marketplace name = `agent-harness`
   (marketplace.json `name`).
3. marketplace source 경로 = repo-local `adapters/claude/plugin-marketplace`
   (codex 는 `codex_setting/codex-plugin-marketplace`; Claude 는 native 라 adapters 경로 직접).
   → `paths.resolve_source("adapters/claude/plugin-marketplace")`.
4. **INST-D-5 병행 유지**: Claude plugin 은 skills/agents/hooks 를 담지만 settings.json 복사·
   statusline·mem 복원·CLAUDE.md·launcher 는 **못 담는다**(plugin 은 `agent`/`subagentStatusLine`
   키만) → `plugin=True` 여도 기존 symlink+copy_once projection 을 **항상 병행**(codex 와 동일
   원칙). "plugin 이면 symlink 생략" 금지.
5. `--json` 플래그: claude plugin CLI 의 비대화 출력 플래그는 code-execute 가 실 CLI 로
   확인(runtime-currentness) — 부재 시 플래그 없이 호출·비대화 확인 방식으로 조정.
