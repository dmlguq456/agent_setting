# Cross-harness live-session state — discovery & tap points (verified field intel)

> 출처: 코드베이스 직접 조사 (Explore agent, 2026-07-01). `/home/Uihyeop/agent_setting` + `~/.claude`·`~/.codex`·`~/.local/share/opencode` 실측. 모든 주장 file:line 인용. 이 문서는 `agent-fleet-dashboard` spec 의 기술 근거 (tap 지점·discovery·liveness).

## 0. Universal common denominator — process scan (모든 세션을 잡는 유일 메커니즘)

`/proc/<pid>/cwd` 와 `ps -o etime=` 는 세 하네스 모두 읽힘. 각 하네스 라이브 프로세스 1개씩 실측:

| Harness | `comm` | Binary | argv 형태 | `/proc/<pid>/cwd` | `ps etime` |
|---|---|---|---|---|---|
| Claude Code | `claude` | `~/.local/bin/claude` | `claude --teammate-mode tmux …`, `claude --resume <uuid>`, `claude -p "…/autopilot-…"` | ✅ | ✅ |
| Codex CLI | `codex` | `~/.local/bin/codex`(node)→vendored rust | 여기선 `codex app-server`(codex-companion plugin 이 `app-server-broker.mjs … --cwd <path>` 로 spawn). 인터랙티브=`codex`, 헤드리스=`codex exec …` | ✅ | ✅ |
| opencode | `opencode` | `~/.opencode/bin/opencode`(bun 단일 ELF) | 그냥 `opencode` (argv 에 세션 id 없음) | ✅ | ✅ |

핵심:
- `comm` 이 정확히 `claude`/`codex`/`opencode` — leaf 프로세스에 python/node wrapper 없음.
- cwd symlink 에 `(deleted)` 접미사 = 세션 살아있는데 worktree 가 지워진 orphan → 그 자체가 stale 신호.
- argv richness 차이: claude 는 argv 에 slash-command/prompt 노출(mode/skill 보임); codex 는 broker 만 `--cwd`; opencode 는 argv 에 세션 id 없음 → pid→session 은 `/proc/cwd` == DB `session.directory` 매칭으로.
- statusline 이 이미 이 방식: `ps -eo pid=,etime=,args=` + `os.readlink("/proc/<pid>/cwd")` (`adapters/claude/statusline.sh:107,181`).

## 1. Claude Code

- **세션 id** = UUID `session_id`. **Transcript**: `~/.claude/projects/<enc-cwd>/<session_id>.jsonl` (`enc-cwd` = cwd 의 `/`·`.`·`_` → `-`).
- **per-PID 라이브 상태 파일**: `~/.claude/sessions/<PID>.json` — 세션당 1파일, PID 키, Claude 가 네이티브로 씀. `{pid, sessionId, cwd, startedAt, version, kind, entrypoint, name, status, updatedAt, statusUpdatedAt, bridgeSessionId}`. `status ∈ {idle, shell, busy}`. **모델/토큰/rate-limit 은 없음**.
- **statusLine tap** (`settings.json:227-231`, `refreshInterval:60`): stdin JSON 에 전 telemetry 있음 — `session_id`, `effort.level`, `model.{id,display_name}`, `context_window.{…,used_percentage,…}`, `cost.*`, `rate_limits.{five_hour,seven_day}.{used_percentage,resets_at}`, `fast_mode`, `thinking.enabled`.
- **⚠️ 단일 파일 덮어쓰기 확정**: `statusline.sh:10` 이 `> $AGENT_HOME/.statusline-last.json` — **모든 세션이 같은 파일에 덮어씀**(last-writer-wins). 렌더 사본 `.statusline-last-out.txt`(`:259`) 도 동일. **세션별 아님**.
- **우리가 추가 가능**: 모든 hook stdin 에 `session_id` 있음(`herdr-agent-state.sh:64` 가 이미 읽어 소켓 emit). SessionStart/UserPromptSubmit/Stop hook 에서 `~/.claude/.statusline/<session_id>.json` 세션별 파일 write 가능 — **오늘은 그런 파일 없음**.
- **liveness**: `utilities/dispatch-liveness.sh`(transcript mtime) + `sessions/<PID>.json`(status+statusUpdatedAt+pid 생존).

## 2. Codex CLI

- **세션 id** = UUID. **Rollout transcript**(codex 가 세션별 JSONL 씀): `~/.codex/sessions/YYYY/MM/DD/rollout-<ISO-ts>-<session_id>.jsonl`. Index: `~/.codex/session_index.jsonl`.
- **디스크에서 passive 로 복구 가능한 라이브 상태** (주입 불요):
  - `session_meta`(line 1): `session_id`, `cwd`, `originator`, `cli_version`, `model_provider`. 기본 모델은 `~/.codex/config.toml:2` (`model=gpt-5.5`, `model_reasoning_effort=high`).
  - `event_msg/task_started`: `model_context_window`, `collaboration_mode_kind`.
  - **`token_count` 이벤트(매 턴 append)** = Claude usage 대응 tap: `info.total_token_usage.*`, `info.model_context_window`, **`rate_limits.{primary,secondary}.{used_percent,window_minutes,resets_at}`** + `plan_type`. (실측: primary 94% / 300min, secondary 53% / 10080min.)
- **TUI status_line**(`config.toml:35`)은 TUI 에서만 렌더, **파일 dump 안 함** (`adapters/codex/ADAPTATION.md:273-291`). **`[notify]` 없음**. hook 은 있으나 status 파일 안 씀. herdr 소켓 emitter 만 있음(`~/.codex/herdr-agent-state.sh`).
- **process**: `comm=codex`. **liveness**: `adapters/codex/bin/dispatch-liveness.py` (rollout `payload.cwd` 매칭 + mtime ≤ `DISPATCH_STALE_MIN=15`).

## 3. opencode

- **세션 id** = `ses_<base62>` (+ slug). **저장 = SQLite** `~/.local/share/opencode/opencode.db` (WAL; `mode=ro` 로 안전 read). ⚠️ `sqlite3` CLI 미설치 — Python `sqlite3` 로 접근.
- **passive 라이브 상태**: `session` 테이블에 세션별 model/cwd/cost/token 라이브 보유 — `directory`(=cwd), `agent`, `model`(JSON `{"id":"glm-5.2",…}`), `cost`, `tokens_input/output/reasoning/cache_read/cache_write`, `time_updated`. `parent_id` 로 sub-agent 구분.
- **⚠️ rate-limit / context-% 컬럼 없음** — context% 는 `tokens_input` vs 모델 window 로 유도해야. statusline-to-disk·notify hook 없음(plugin `agent-harness-guards.js` 는 status 파일 안 씀).
- **process**: `comm=opencode`, argv 에 세션 id 없음 → pid→session 은 `/proc/cwd == session.directory`. **liveness**: `adapters/opencode/bin/dispatch-liveness.py` (`MAX(time_updated)` ≤ 15min).

## 4. Dispatch 심화 ("running:" 패널 소스)

### 4a. statusline.sh 잡스캔이 뽑는 것 (`adapters/claude/statusline.sh:107-214`)
- 입력 `COLUMNS=100000 ps -eo pid=,etime=,args=` (`:108` COLUMNS 핀 필수 — 없으면 argv 잘려 매칭 전멸).
- **매치 게이트**(`:179-180`): `/autopilot-([a-z-]+)` **AND** `"claude" in args`. Fallback(`:206`): `loops/(oncall|note|study|drill)`.
- 뽑는 값: harness key(`:185`), mode `--mode`(`:186`), qa `--qa`(`:187`), cwd=`/proc/cwd`(`:181`), slug=basename(`:189`), elapsed=etime→mins(`:121-127`), **live stage**=`live_stage()`(`:131-171`, `<jcwd>/…/plans/*_<slug>/` 에서 done→test→exec→plan 유도, argv key 를 override 해 `key▸stage` 라벨).
- `related()` cwd 필터(`:111-118`): 같은 cwd·조상/자손·형제 worktree(`<repo>-wt/`)만 표시(루프는 항상).
- **TOP-3 CAP**(`:211-212`): `[:3]` + `+N` 배지 — **대시보드가 없앨 truncation (uncapped 렌더)**.

### 4b. jobs.log dispatch registry (§5.10)
- **경로**: `<agent-home>/.dispatch/jobs.log` (기본 `~/.claude/.dispatch/jobs.log`; override `AGENT_DISPATCH_JOBS`). 실측 ~147 rows.
- **canonical schema** (`core/OPERATIONS.md:95`, writer `adapters/codex/bin/dispatch-headless.py:151-157`): tab 6필드 `<ISO-ts>\t<status>\t<repo>\t<worktree>\t<slug>\t<pipe>`; status `open`→`done`.
- **writers**: codex/opencode `dispatch-headless.py`(flock). **Claude 는 전용 스크립트 없음** — 오케스트레이터가 `claude -p` spawn 전 수동 append (`core/OPERATIONS.md:95`).
- **⚠️ 라이브 파일 vs spec 불일치 (대시보드 필수 고려)**: 실제 파일의 field-2 = `done`(137)/`running`(5)/`cancelled`(2)/`killed`(1), **`open` 0개**. `pipe` 는 종종 한국어 free-text, `worktree` 가 `-`/`(main-tree)` 인 행도. 3행은 malformed(field 수 1·5·11). → **`$2=="open"` 필터인 `harness-status.sh`·`dispatch-liveness.sh` 가 현재 아무것도 못 잡음**. 대시보드는 `{open, running}` 을 live 로 받고 malformed/`-` 행 tolerant 해야.

### 4c. dispatch-liveness.sh 알고리즘 (`utilities/dispatch-liveness.sh`)
- `JOBS`=arg or `$AGENT_HOME/.dispatch/jobs.log`; `STALE_MIN=15`; `status=="open"` 만 처리(`:19`); job→transcript = `wt | sed 's#[/._]#-#g'` → `$PROJ/$enc/*.jsonl` newest mtime; ≤15min ALIVE / else SUSPECT / 없음 DEAD; suspect·dead 있으면 exit 3. **`open` 키라 라이브 파일(전부 running/done)엔 매칭 0 — 4b 와 같은 vocabulary gap.**

### 4d. Codex/opencode dispatch 가 statusline 스캔에 뜨나 — NO
- `statusline.sh:180` 이 **`"claude" in args`** 요구. codex 헤드리스는 `codex exec … < <prompt>.txt`(`dispatch-headless.py:122-136`) — argv 에 `claude`·`/autopilot-` 없음(capability 는 prompt 파일 안, mode/qa 는 jobs.log `pipe`). → **codex/opencode 헤드리스는 statusline "running:" 에 안 보임**; jobs.log + 각 `dispatch-liveness.py` 로만 추적. statusline 스캔이 잡는 건 (a) Claude autopilot 헤드리스, (b) `loops/*` 둘뿐.

## 5. 요약 — tap 매트릭스

| Need | Claude Code | Codex CLI | opencode |
|---|---|---|---|
| 세션 id | UUID | UUID | `ses_…`(+slug) |
| per-session transcript | `projects/<enc-cwd>/<uuid>.jsonl` | `sessions/Y/M/D/rollout-*-<uuid>.jsonl` | `opencode.db` rows |
| per-session 라이브 status 파일 | `sessions/<PID>.json` (status only, **no model/tokens**) | 없음(rollout 내부) | 없음(DB 내부) |
| model/cwd | `.statusline-last.json`(**공유·덮어씀**) or hook stdin | rollout `session_meta.cwd` + config model | DB `session.model`/`directory` |
| token/context | `.statusline-last.json`(공유) | rollout `token_count.info.*` | DB `tokens_*`,`cost` (ctx-% 컬럼 없음) |
| rate limit / effort | ✅ `.statusline-last.json` | ✅ rollout `token_count.rate_limits` / config effort | ❌ 없음 |
| statusline→disk dump | ✅ but **1 공유 파일** | ❌ (TUI-only) | ❌ |
| 추가 가능한 per-session hook | ✅ (우리가 Claude hook 소유) | hook 있으나 status 파일 X | plugin 있으나 status 파일 X |
| process name | `claude` | `codex` | `opencode` |
| `/proc/cwd`+etime | ✅ | ✅ | ✅ |
| passive liveness | transcript mtime + `sessions/<PID>.json` | rollout mtime | DB `MAX(time_updated)` |
| statusline "running:" 스캔에 포함? | ✅ (autopilot+loops) | ❌ | ❌ |

**결론 — 대시보드 두 팔**: (A) 모든 하네스의 모든 세션을 열거하는 유일 tap = **프로세스 스캔**(`comm`+`/proc/cwd`+`etime`); model/token/rate-limit enrichment 은 디스크에서 passive 복구 — Claude 공유 `.statusline-last.json`(또는 우리가 추가할 per-session hook), Codex rollout `token_count`, opencode `session` DB row. (B) dispatch 패널 소스 = statusline `ps` 스캔(Claude autopilot+loops, 3개 cap) + `.dispatch/jobs.log`(단, `running`/`done` vocabulary — `open` 필터 도구는 현재 매칭 0, codex/opencode dispatch 는 jobs.log 에만).
