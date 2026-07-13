# Install Layout

This harness is runtime-neutral. The git repository should live outside vendor runtime homes, and each runtime home should project the harness through symlinks or adapter bootstrap files.

> **실행 안내 — `harness install` / `harness verify` 가 담당한다.** 이 문서는 더 이상
> 복사해서 실행하는 shell 레시피나 수동 검증 절차를 담지 않는다. 설치·검증·갱신·상태·
> 제거는 모두 `tools/install/harness.sh`
> (`install`/`verify`/`update`/`status`/`uninstall` 서브명령) 가 기계화한다. 수동
> 레시피는 PRD `.agent_reports/spec/harness-installer/prd.md`
> (harness-installer cycle 1~2) 로 대체됐다.
>
> **설계 안내 — 이 문서가 유지하는 것은 계약 서술뿐이다.** 무엇이 어디로 매핑되는지,
> 왜 그렇게 하는지, 어떤 경우가 위험한지만 다룬다. 표면 × 채널 결정 매트릭스와 채널별
> 상세 스펙의 단일 출처는 PRD `[cli]`·`plugin 채널` 절이고, 아래에는 그 요약과 이
> 문서에만 있는 로컬 사실(Windows 구체 경로, fleet 계약)만 남긴다.

## Target Layout

```text
$HOME/agent_setting/        # canonical git repo: common core + adapters + projections
$HOME/.claude/              # Claude Code runtime home
$HOME/.codex/               # Codex runtime home
$HOME/.config/opencode/     # OpenCode global config home
$HOME/.local/share/opencode/  # OpenCode data home (DB, logs, snapshots)
```

Do not make `$HOME/.claude`, `$HOME/.codex`, or `$HOME/.config/opencode` the canonical repo. Those directories contain runtime-owned state such as credentials, sessions, logs, SQLite databases, caches, and shell snapshots.

## Claude Code Projection

Claude Code expects files under `$HOME/.claude`. Runtime-owned files stay there;
harness-owned files are symlinked from the versioned Claude projection, and
`settings.json`/`keybindings.json` are copied once (never re-linked).

```bash
harness install claude
```

**Contract, not recipe**:

| 표면 | 배선 | 계약 |
|---|---|---|
| `CLAUDE.md`/`core`/`skills`/`agents`/`hooks`/`tools`/… | symlink | repo 수정이 즉시 반영 — harness-owned, 런타임에서는 read-only |
| `settings.json`/`keybindings.json` | copy-once + hash-manifest | 한 번만 복사하고 다시는 링크하지 않는다 (↓ 설정 파일) |
| plugin 채널(`--plugin`) | `claude plugin marketplace add` + `claude plugin install` wrapping | symlink+copy-once projection 과 항상 병행 (↓ plugin 채널) |

- **설정 파일** — Claude Code 는 `settings.json`/`keybindings.json` 을 in-place 로
  다시 쓴다 (`/model`, `/config`, in-app keybinding 편집). 이때 atomic write 가
  symlink 를 일반 파일로 대체하므로, 한 번만 복사하고 다시는 링크하지 않는다 —
  한 번이라도 링크하면 repo 가 조용히 오염된다. drift 는 `verify` / `update --reapply`
  가 hash-manifest 로 감지·백업·재적용한다.
- **plugin 채널** — plugin 은 `agent`/`subagentStatusLine` 키만 유효해 settings.json
  의 일반 키·env·permissions·statusline·plugin 내 CLAUDE.md 를 싣지 못한다. 그래서
  symlink+copy-once projection 과 항상 병행한다. 콘텐츠
  (skills/agents/hooks+hooks.json) 는 `adapters/claude/bin/sync-native-plugin.py` 가
  SoT 로부터 물리적으로 생성한다 (self-contained cache 모델 — `../` 상위 참조 불가).

Keep these local to `$HOME/.claude`: `.credentials.json`, `.dispatch/`, `cache/`, `daemon/`, `history.jsonl`, `ide/`, `projects/`, `sessions/`, `session-env/`, `shell-snapshots/`, runtime logs, and other runtime-generated state.

If present, existing `worklog-board/` and `worklog-board-wt/` directories under
`$HOME/.claude` are local worklog app workspaces, not harness projection
targets. Do not move their data during harness installation. Their notes data
root is `<agent-notes-root>`, which is mutable continuity state and should not
be committed to this repo. Adapter docs own concrete local path realizations.

## Windows Projection (Git Bash)

Claude Code runs on Windows, but the harness assumes a POSIX runtime. Two
Windows-specific facts break the projection silently — a one-shot installer
(`adapters/claude/bin/install-windows.sh`, run from Git Bash) repairs both and
is idempotent. `harness install claude` invokes this delegate automatically
on a detected Windows host; the direct command remains available for manual
repair:

```bash
bash ~/.claude/adapters/claude/bin/install-windows.sh
```

1. **Unreliable `$HOME`.** The shell Claude Code spawns for hook / statusLine
   commands sees `$HOME` as either empty or the MSYS `/home/<user>` — never the
   real `%USERPROFILE%` where `.claude` actually lives. Every
   `bash "$HOME/.claude/hooks/<x>.sh"` command therefore fails to resolve and the
   hook/statusline no-ops with no obvious cause. The installer injects
   `HOME` / `CLAUDE_HOME` / `AGENT_HOME` into the runtime `settings.json` `env`
   block (which Claude Code applies to command execution) so those paths resolve.

2. **`core.symlinks=false`.** A Windows checkout writes repo symlinks out as
   small pointer-TEXT files (content = the link target path), not real files. So
   the entry files the Linux projection step symlinks into the runtime home
   (`CLAUDE.md`, `statusline.sh`, `track-toggle.sh`) are absent or pointer-text on
   Windows, and `~/.claude/CLAUDE.md` never loads. The installer copies each from
   its single source of truth (`adapters/claude/<name>`) into the runtime home
   when the target is missing or a pointer — the Windows equivalent of the Linux
   `ln -sfn` step.

The installer also restores the per-machine memory DB from the git-tracked
`dump.jsonl` mirror when it is missing (`mem import`).

**`fleet` on Windows.** `fleet --json` and `fleet --once` (plain snapshot) run
on native Windows under Git Bash — `render.py` imports `curses` lazily, so the
snapshot/scripting paths need no `curses` at all and write UTF-8 directly (so a
cp949/non-UTF-8 console codepage does not raise `UnicodeEncodeError`). Only the
live full-screen TUI (`fleet` with no `--once`) needs `curses`; install it with
`pip install windows-curses`, or run the live view under WSL/Linux. The
installer also drops a `fleet` launcher into `~/.local/bin` (put that dir on
your Git Bash `PATH`) so `fleet` works as a one-word command. Everything else
(hooks, memory, statusline, skills) runs under Git Bash.

## Cross-harness CLI — `fleet`

`fleet` (the cross-harness live dashboard, `tools/fleet/`) is runtime-neutral — it
observes every harness (Claude Code · Codex · opencode) from the process table and
on-disk state, so it belongs to no single adapter. The launcher `tools/fleet/fleet.sh`
runs from the repo directly; to get the one-word `fleet` command, symlink it onto `PATH`:

```bash
export AGENT_HOME="$HOME/agent_setting"
mkdir -p "$HOME/.local/bin"
ln -sfn "$AGENT_HOME/tools/fleet/fleet.sh" "$HOME/.local/bin/fleet"   # needs ~/.local/bin on PATH
```

No install step at all still works — run it by path: `bash "$AGENT_HOME/tools/fleet/fleet.sh"`
(or, via the Claude projection above, `bash ~/.claude/tools/fleet/fleet.sh`). Zero-dep
(stdlib python3 + curses); nothing to build.

Session titles are also cross-harness. Fleet reads Codex's native state DB title with
the JSONL `thread_name` index as a compatibility fallback, and may
refresh active Claude/Codex titles into
`${FLEET_TITLE_STATE_DIR:-${XDG_STATE_HOME:-~/.local/state}/agent-fleet/titles}/<harness>/`.
The default refresher is the existing no-tools Haiku provider. To use a GPT-mini-class
or other small model, point `FLEET_TITLE_COMMAND` at a no-tools wrapper; the value is
parsed as an argv template, never through a shell:

```bash
export FLEET_TITLE_MODEL="small-model"
export FLEET_TITLE_COMMAND='my-title-wrapper --model {model} --prompt {prompt}'
```

The wrapper owns its provider-specific no-tools restriction. `fleet --json` and
`fleet --once` never start title workers.

## Codex Projection

Keep `$HOME/.codex` runtime-owned. The portable harness projects through a
stable pointer plus adapter-owned Codex-native Skills, custom Agents, plugin
marketplace, mode guides, and hook bridges:

```bash
harness install codex
```

**Contract, not recipe**:

| 표면 | 배선 | 계약 |
|---|---|---|
| `AGENTS.md`/core/capabilities/roles/bin/tools/utilities/scaffolds | symlink (`agent-*` pointer 이름) | `codex_setting/` 에 생성된 projection 을 경유한다 |
| Codex-native skills/agents/modes | symlink fan-out (`skills/*`, `agents/*.toml`) | `codex_setting/codex-{skills,agents,modes}` — `capabilities/`·`roles/` 로부터 생성, 재구현 금지 |
| plugin 채널(`--plugin`) | `codex plugin marketplace add` + `codex plugin add <spec>@<marketplace>` wrapping | symlink projection 과 항상 병행 (↓ plugin 채널) |
| hooks | `codex_setting/codex-hooks` → `hooks.json` | adapter-owned hook bridge, `type:"command"` 만 실행 |
| `/statusline` 대상 `config.toml` | copy 안 함, fragment 만 유지 | `config.toml` 은 runtime-owned (↓ statusline) |

- **plugin 채널** — marketplace 는 `codex_setting/codex-plugin-marketplace`
  (`.agents/plugins/marketplace.json`). plugin 이 싣지 못하는 것 — custom agents
  (`.codex/agents/*.toml`)·prompts·`config.toml` fragment·`AGENTS.md` — 은 plugin
  채널과 무관하게 symlink projection 이 계속 담당한다. 그래서 Codex 는 plugin
  채널만으로는 완결할 수 없고, `plugin=True` 여도 symlink projection 은 항상 병행한다
  (INST-D-5).
- **statusline** — `config.toml` 은 TUI 가 직접 다시 쓰는 runtime-owned 파일이라
  전체를 projection 하지 않는다. `codex_setting/codex-config/tui-statusline.toml`
  조각만 유지하고, 적용은 `codex_setting/bin/preflight.sh tui-config` 가 맡는다
  (`[tui].status_line`·`[tui].status_line_use_colors` 만 갱신).

For a project-scoped install, `harness install codex --scope project` symlinks
the generated TOML files into the project's `.codex/agents/` directory instead
of `$HOME/.codex/agents/`.

Do not symlink Claude-native surfaces such as `settings.json`, `commands/`,
root `skills/`, root `agents/`, `statusline.sh`, or `hooks/` into `$HOME/.codex`.
Future Codex-specific bootstrap files should live under `adapters/codex/` and
be symlinked or generated into `codex_setting/` without moving Codex
credentials, logs, sessions, or SQLite state into the repo.

## OpenCode Projection

OpenCode loads config from `opencode.json` / `opencode.jsonc` (project or
global `~/.config/opencode/`) and reads instruction files listed in the
`instructions` array. Keep `$HOME/.config/opencode` and
`$HOME/.local/share/opencode` runtime-owned; the harness merges its
instruction/skill entries into the existing config **non-destructively**
(existing user config preserved, conflicts reported and the run stopped
rather than resolved by guessed intent) and projects adapter-owned surfaces
through a stable pointer:

```bash
harness install opencode
```

**Contract, not recipe**:

| 표면 | 배선 | 계약 |
|---|---|---|
| `AGENTS.md`/core/capabilities/roles/bin/tools/utilities | symlink (`agent-*` pointer 이름) | `opencode_setting/` 생성 projection 경유 |
| OpenCode-native skills/agents/commands | symlink fan-out (`agent/*.md`, `command/*.md`) | `opencode_setting/opencode-{skills,agents,commands}` — 재구현 금지 |
| guard plugin | `opencode_setting/opencode-plugins/agent-harness-guards.js` | JS/TS plugin hook 표면(OpenCode 는 marketplace·번들 포맷이 없다 — plugin 채널 자체가 미존재, installer symlink 가 유일 경로) |
| `opencode.json`/`opencode.jsonc` `instructions[]`/`plugin[]` | non-destructive merge | 기존 사용자 config 보존, 충돌 시 report 후 중단 (자동 merge 강행 금지) |

⚠️ **INST-OPEN-4 (열려 있음, 이 사이클 미변경)**: 현행 공식 OpenCode 문서는 **복수형**
디렉토리(`.opencode/skills|commands|agents|plugins/`, global
`~/.config/opencode/…`)를 쓰고 **`skills.paths` config key 는 문서에 없다**(skill
노출은 `permission.skill` 규칙 + convention 디렉토리). 이 문서·`opencode_setting`
배선의 단수형(`agent/`·`command/`)·`skills.paths` 는 legacy 일 가능성이 있다 —
migration 은 별도 사이클 과제로 남아 있다.

Do not symlink Claude-native surfaces such as `settings.json`, `commands/`,
`skills/`, `statusline.sh`, or `hooks/` into `$HOME/.config/opencode`.
Future OpenCode-specific bootstrap files should live under `adapters/opencode/`
and be symlinked or generated into `opencode_setting/` without moving
OpenCode credentials, DB state, logs, sessions, or snapshots into the repo.

## Migration / Verification

The manual `ln -sfn` recipes and the ~275-line manual verification battery
this section used to hold are now machine-checked:

```bash
harness install [claude|codex|opencode|all]
harness verify  [claude|codex|opencode|all] --json
```

`verify` runs each driver's `checks()` list (symlink existence · generator
`--check` drift · preflight contract assertions · plugin marketplace/
registration checks · bootstrap load smoke) and reports pass/fail per check —
this is the full mechanization of what the removed Migration Order section
ran by hand.

**Contract-level invariants that remain true regardless of implementation**
(kept as prose, not runnable steps):

- **Exit codes** (`tools/install/installer.py`, PRD `[cli]` "### Exit code"):
  `0` success (verify: every check passed) · `1` execution failure (I/O,
  unmet precondition) · `2` verify failure (≥1 check ✗) · `3` **BLOCKED** —
  a target runtime process is active or a destination is a pre-existing
  real file/dir the installer refuses to overwrite (this is the direct
  successor of the old Migration Order step 2's "stop long-running runtime
  processes first" rule — the installer now detects and refuses instead of
  relying on the operator to remember) · `4` drift detected (`--reapply` or
  a manual backup check needed) · `64` usage error.
- **Never overwrite runtime-owned state.** The installer's symlink step
  refuses (`status: "blocked"`) rather than clobbers when a destination is
  a real file/dir, not a symlink — this preserves an operator's pre-existing
  vanilla runtime config instead of silently replacing it.
- **hash-manifest drift**: only files the installer actually *copies*
  (`settings.json`, `keybindings.json`, Windows copy-branch files) are
  hash-tracked — symlinks are self-evidently canonical and excluded, plugin
  cache is runtime-owned and excluded. A mismatch on `verify`/`update` means
  the user edited a copied file in place; `update --reapply` backs it up
  under `local-patches/` before reapplying, and a 3-way conflict is reported
  rather than auto-merged.
- **Plugin registration checks are always read-only.** `verify` never calls
  a mutating plugin command (`marketplace add`/`plugin install`/`plugin add`)
  — only read-only list/query subcommands. Runtime-currentness of the exact
  CLI verbs/flags for each runtime's plugin channel is verified against that
  runtime's live CLI + current docs before being wired into a driver
  (`core/ADAPTATION.md` §2.2), not assumed from another adapter.

Do not run drill automatically during migration; it invokes headless runtime sessions and can spend tokens. Run a targeted drill only after `harness verify` reports clean.
