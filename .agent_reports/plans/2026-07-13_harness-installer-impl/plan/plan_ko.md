---
status: active
created: 2026-07-13
phases:
  - "Phase 0: manifest schema + layout decisions (foundation)"
  - "Phase 1: projector.py — INSTALL_LAYOUT recipe port (P0.1)"
  - "Phase 2: manifest.py — hash-manifest / drift / reapply (P0.3)"
  - "Phase 3: drivers/{claude,codex,opencode}.py — install()/status()/checks() (P0.4)"
  - "Phase 4: verifier.py real check lists (P0.2)"
  - "Phase 5: installer.py wiring — cmd_* real behavior (P0 integration)"
  - "Phase 6: mem import + ~/.local/bin launcher symlinks (P0.5)"
  - "Phase 7: P1 — plugin channel wrapping + Claude plugin content (boundary marked)"
---

# harness-installer — 구현 사이클 1

## 목표

`tools/install/` 를 scaffold 스텁 상태에서 실제로 동작하는 설치기로 채운다. 담을 것은 다음과 같다 — symlink 투영(INSTALL_LAYOUT 을 기계화), 읽기 전용 `verify` 점검 목록, `git merge-file` 로 결정론적 재적용을 하는 hash-manifest, 기존 어댑터 스크립트를 호출하는(재구현하지 않는) 세 개의 런타임 드라이버, 그리고 `mem import` 와 PATH 런처 설치. 모든 동작은 임시 `HOME` 과 `--dry-run` 아래에서만 시연하며, 실제 런타임 홈은 절대 건드리지 않는다.

## 현황 분석

### 저장소 레이아웃 실태 (이 worktree, 브랜치 `harness-installer-impl` 에서 확인)
- Claude 정본 표면은 **저장소 루트**에 있다: `core/`, `capabilities/`, `roles/`, `commands/`, `skills/`, `agents/`, `hooks/`, `utilities/`, `scaffolds/`, `tools/`, `loops/`, `manifest.json`. Claude 가 **네이티브** 런타임이다.
- 어댑터 표면: `adapters/claude/`, `adapters/codex/`, `adapters/opencode/`. Claude 런타임이 소유하는 파일: `adapters/claude/{CLAUDE.md,settings.json,statusline.sh,keybindings.json?}`.
- **`{claude,codex,opencode}_setting/` 투영 디렉토리는 이 worktree 에 실제로 존재하고 git 추적된다** (symlink-farm 투영 디렉토리 — 예: `claude_setting/{CLAUDE.md,agents,agent-modes,bin,...}`, `codex_setting/bin/preflight.sh`, `opencode_setting/...`). `INSTALL_LAYOUT.md` 의 symlink 레시피는 이들을 소스로 참조하며(`$AGENT_HOME/claude_setting/$p`, `$AGENT_HOME/codex_setting/...`, `$AGENT_HOME/opencode_setting/...`), `AGENT_HOME=<repo root>` 에서 그 소스가 올바르게 resolve 된다. (주의: 이들은 symlink 로 걸린 디렉토리라 단순 glob 으로는 순회하지 못할 수 있고, symlink 를 통한 `Read`/`ls` 로는 접근된다.) projector 는 소스 경로를 `AGENT_HOME` 기준으로 resolve 하며, 존재하는 것이 **기본 전제**다. 부재 시 건너뛰는 방어 로직은 안전망일 뿐 정상 경로가 아니다.

### 재사용 스크립트 (호출만, 재구현 금지 — 존재 확인 완료)
- `adapters/codex/bin/sync-native-{skills,agents,modes,plugin}.py` — argparse, `--check` = 읽기 전용 투영 확인, 인자 없이 호출하면 (재)생성. (`--check` 플래그 존재 확인.)
- `adapters/opencode/bin/sync-native-{skills,agents,commands}.py` — 같은 `--check` 인터페이스 (`sync-native-skills.py:121` 에서 확인).
- **Claude 에는 `sync-native-*.py` 가 없다** (네이티브 런타임 — 루트 디렉토리 자체가 정본). Claude 투영 = 순수 symlink + 한 번 복사, 생성기 없음.
- `adapters/codex/bin/preflight.sh` + `adapters/opencode/bin/preflight.sh` — 서브커맨드 계약 (`capability-info`, `role`, `permissions`, `mcp`, `headless`, `status`, `mode-info`, `dispatch`, `harvest`, `liveness`, ... 378번째 줄 이후에서 확인). **Claude 에는 `preflight.sh` 가 없다** (`*_setting/bin/preflight.sh` 자체가 어디에도 없음).
- `adapters/claude/bin/install-windows.sh` — 멱등적 Windows 복구 (settings.json 에 HOME 환경변수 주입 + symlink→copy). 호출만 하고 재구현하지 않는다 (`set -euo pipefail`, 정본·python 부재 시 66/69 로 종료).
- `tools/build-manifest.py --check` — 투영 드리프트 생성기 (Migration Order 에서 사용).
- `tools/memory/mem.py` — `mem import <path>` 가 `dump.jsonl` → `memory.db` 를 복원 (서브파서 `import`, `mem.py:3562/3654`; `import_dump()` 1757번째 줄에서 DELETE 후 replay 로 정확 복원). STORE = `$AGENT_HOME/memory` 또는 `$MEM_STORE` (`mem.py:30-32`); `dump.jsonl` 은 `agent_setting` 이 아니라 별도의 `agent-memory` 저장소에 있다.
- `tools/fleet/fleet.sh` — `~/.local/bin` symlink 패턴의 선례 런처 (INSTALL_LAYOUT 94-98번째 줄).
- 플러그인 마켓플레이스: `adapters/codex/plugin-marketplace/.agents/plugins/marketplace.json` (동작함, 재사용); `adapters/claude/plugin-marketplace/` 는 골격만 (`marketplace.json` + `plugins/agent-harness-claude/.claude-plugin/plugin.json`, 내용은 미완성).

### Scaffold 소스 상태 (커밋 9792fd3)
- `tools/install/harness.sh` — POSIX 런처, 완성됨. **건드리지 않는다.**
- `installer.py` — argparse 트리 + 종료 코드 상수 (`EXIT_OK=0/FAIL=1/VERIFY_FAIL=2/BLOCKED=3/DRIFT=4/USAGE=64`) + `--json` 형태 완성. `cmd_install` (101) 은 `projector.plan()` 을 호출하지만 plan 개수만 보고한다 (TODO: 실제 `driver.install()` + `manifest.record()`). `cmd_verify` (115) 는 이미 `verifier.run(rt, driver)` 를 연결해 뒀다 — 드라이버가 점검을 반환하면 곧바로 동작한다. `cmd_update` (130) 는 `manifest.check_drift()` 를 호출한다 (현재는 `[]`). `cmd_status` (139) 는 "channel=미확인" 스텁. `cmd_uninstall` (151) 스텁. `resolve_runtimes()` (82) + `emit()` (92) 완성.
- `projector.py` — `plan(runtimes, scope)` 이 항상 `{rt: []}` 를 반환한다 (`_PROJECTION_STUB` 비어 있음).
- `manifest.py` — `record()`/`reapply()` 가 `NotImplementedError` 를 던진다 (게이트는 이제 통과); `check_drift()` 는 `[]` 를 반환.
- `verifier.py` — `run(runtime, driver)` 가 `driver.checks()` 를 실행하고, 비어 있으면 단일 "no-checks" placeholder 로 폴백.
- `drivers/{claude,codex,opencode}.py` — `install()`/`status()` 가 `NotImplementedError` 를 던지고, `checks()` 는 `[]` 를 반환. 각 모듈은 `RUNTIME` 상수를 export 한다. `drivers/__init__` 은 `get_driver()` + `RUNTIMES` 를 노출한다 (installer 가 import).

## 변경 계획

Phase 순서 (강한 의존):
- **Phase 0 → 2 → 5** (manifest 구현 전에 스키마가, installer 연결 전에 manifest 구현이 있어야 한다).
- **Phase 1 → 3 → 4** (드라이버 전에 projector, verifier 점검 목록 전에 드라이버).
- Phase 5 는 1+2+3 에 의존.
- Phase 6 은 독립적이라 1-4 와 병렬 진행 가능.
- Phase 7 은 P1.

---

### Phase 0 — 기반: manifest 스키마 + layout 상수 (가장 먼저)

**Step 0.1 — `tools/install/paths.py` (신규 모듈) 추가: 중앙 경로 resolve.**
- `agent_home()` 추가 → 저장소 루트를 resolve: 환경변수 `AGENT_HOME` 이 있으면 그 값, 없으면 `__file__` 에서 git 루트까지 거슬러 올라감. `pathlib.Path` 반환.
- `runtime_home(runtime, scope)` 추가 → 런타임별 대상 디렉토리:
  - claude → `$HOME/.claude`
  - codex → `$HOME/.codex`
  - opencode global → `$HOME/.config/opencode`; opencode project → `$PWD/.opencode` (scope=project). 그리고 `opencode_data = $HOME/.local/share/opencode` (런타임 소유, 절대 쓰지 않음).
- `harness_state_dir(runtime, scope)` 추가 → `runtime_home / ".harness"` (런타임 홈 안에 설치기가 소유하는 하위 트리: manifest·pristine·backup 이 여기 있어 uninstall 이 자기완결적이고 대상과 함께 이동한다).
- `resolve_source(relpath)` 추가 → `agent_home() / relpath`, 그리고 `source_exists()` 헬퍼 (projector 의 SKIP 로직에서 사용).
- **완료 기준**: (`tools/install/` 에서) `python3 -c "import paths; print(paths.agent_home())"` 가 저장소 루트를 출력하고, 임시 `HOME` 아래에서 `paths.runtime_home('claude','global')` 이 `<temp HOME>/.claude` 를 출력한다.

**Step 0.2 — manifest JSON 스키마 결정 + 문서화 (`manifest.py` 모듈 docstring 으로 작성, 로직은 아직 없음).**
- manifest 파일: `<runtime_home>/.harness/manifest.json`:
  ```json
  {"schema": 1, "runtime": "claude", "scope": "global",
   "version": "<repo git SHA at install>", "timestamp": "<iso8601>",
   "files": {"settings.json": "<sha256hex>", "keybindings.json": "<sha256hex>"}}
  ```
- Pristine 스냅샷: `<runtime_home>/.harness/pristine/<relpath>` — **설치 시점에 복사한 저장소 정본 바이트** (3-way 병합의 base). 다음 설치가 성공적으로 갱신하기 전까지 불변 (가드: 드리프트가 해소되지 않은 동안 pristine 을 새 릴리스 복사본으로 덮어쓰지 않는다 — impl-inputs §A 함정 #3407).
- Backup (단일 디렉토리로 통합, impl-inputs §A 채택 노트): `<runtime_home>/.harness/local-patches/<relpath>` — 사용자가 수정한 파일의 전체 복사본, wipe 직전에 뜬다.
- `backup-meta.json`: `{"from_version": "<sha>", "pristine_hashes": {"<relpath>": "<sha256>"}}` 를 backup 옆에 둔다.
- **사이클 1 의 manifest 범위 = 한 번 복사하는 파일만**: Claude `settings.json`, `keybindings.json` (+ install-windows.sh 가 만드는 Windows 복사본). symlink 는 제외한다 (자기 정본). OpenCode `opencode.json` 은 **병합 관리 대상이라 따로 추적한다** (순수 복사가 아님) — 사이클 1 은 harness 가 관리하는 조각의 존재 여부만 기록하고, 완전한 병합 manifest 는 이후 사이클로 미룬다 (리스크에 표시).
- HLS 공유 노트: 스키마 키 이름은 겹치는 지점에서 `tools/build-manifest.py` 관례에 맞췄다; 해시 알고리즘을 갈라내지 않는다 (SHA-256 hex, GSD/HLS 와 동일).
- **완료 기준**: `manifest.py` docstring 이 정확한 스키마 + 디렉토리 레이아웃을 문서화한다; 동작 변경은 아직 없다 (함수는 여전히 raise/stub 반환).

---

### Phase 1 — projector.py: INSTALL_LAYOUT symlink 레시피 이식 (P0.1)

**대상 파일**: `tools/install/projector.py`. `_PROJECTION_STUB` + `plan()` 을 교체한다.

**Step 1.1 — 런타임별 투영 테이블을 데이터로 인코딩 (INSTALL_LAYOUT 을 그대로 반영).**
각 항목을 명시적 `action` 타입을 가진 dict 로 표현해, 런타임 소유 복사본을 symlink 와 분리한다:
- `{"action": "symlink", "source": "<relpath under AGENT_HOME>", "dest": "<abs under runtime_home>"}`
- `{"action": "copy_once", "source": ..., "dest": ...}` (settings.json, keybindings.json — 다시 링크하지 않음, INSTALL_LAYOUT 29-35번째 줄)
- `{"action": "symlink_glob", "source_dir": ..., "dest_dir": ..., "pattern": "*.toml" | "*" | "*/*.md"}` (파일별 fan-out 루프)
- `{"action": "delegate", "cmd": ["bash", "adapters/claude/bin/install-windows.sh"]}` (Windows 분기 — 재구현하지 않음)
- `{"action": "merge", ...}` (opencode.json 비파괴 병합 — opencode 드라이버가 처리하고, projector 는 의도만 내보냄)

인코딩할 테이블 (소스 = INSTALL_LAYOUT.md):
- **claude** (21-35번째 줄): `CLAUDE.md README.md core commands skills agents agent-modes hooks utilities tools scaffolds loops manifest.json statusline.sh track-toggle.sh` 각각을 `claude_setting/<p>` → `~/.claude/<p>` 로 symlink; `settings.json keybindings.json` 은 `copy_once`. (`claude_setting/` 은 존재하고 git 추적됨; 소스는 `AGENT_HOME` 기준으로 resolve — 존재가 기본이고 부재 시 건너뛰기는 안전망일 뿐.)
- **codex** (110-138번째 줄): 고정 symlink (`agent-harness`, `AGENTS.md`, `agent-core`, `agent-capabilities`, `agent-roles`, `agent-bin`, `agent-tools`, `agent-utilities`, `agent-scaffolds`, `agent-skills`, `agent-modes`, `agent-agents`, `agent-plugin-marketplace`, `agent-hooks`, `agent-config`, `hooks.json`) + 두 개의 `symlink_glob` fan-out (`codex-skills/*` → `.codex/skills/`, `codex-agents/*.toml` → `.codex/agents/`). scope=project 는 agents glob 을 `<project>/.codex/agents/` 로 재배선한다.
- **opencode** (177-225번째 줄): 포인터 symlink + 어댑터 소유 표면 symlink + agent/command 파일별 glob fan-out + `opencode.json` 병합 의도 + plugins symlink. **로컬 1.17.13 단수 배선을 사용** (`agent/`, `command/`, `skills.paths`, impl-inputs §B) — 복수형으로 바꾸지 말 것; INST-OPEN-4 는 OPEN 상태 유지.

**Step 1.2 — `plan(runtimes, scope="global")` 이 resolve 된 plan 을 계산한다.**
- 각 런타임마다 `paths.resolve_source()` + `paths.runtime_home()` 로 테이블을 펼친다. `symlink_glob` 은 `source_dir` (존재하면) 을 나열해 구체적인 파일별 항목으로 펼친다.
- 각 항목에 `"source_present": bool` 을 표기한다. 정상적인 경우 소스는 존재한다 (이 worktree 에 있음); 정말로 없는 소스는 `{"action": "skip", "reason": "source absent: <path>", ...}` 이 된다 (parity-loss SKIP 패턴, PRD "parity-loss warning") — 이는 방어적 안전망이지 예상 경로가 아니다.
- 반환 형태는 `{runtime: [entry, ...]}` 그대로 (installer 가 이미 `plan.get(rt, [])` 로 소비).
- **완료 기준**: 임시 `HOME` + `AGENT_HOME=<이 worktree 의 repo root>` 에서 `harness install --dry-run --json` 이 런타임별로 **resolve 된 전체 symlink/copy_once 목록**을 보여준다 (실제 `claude_setting/`→`~/.claude/`, `codex_setting/`→`~/.codex/`, `opencode_setting/`→`~/.config/opencode/` 항목), **`skip: source absent` 항목은 하나도 없이**. 전 과정을 이 worktree 에서 검증할 수 있다 — 별도의 materialize 된 체크아웃이 필요 없다.

---

### Phase 2 — manifest.py: hash-manifest / drift / reapply (P0.3) [Phase 0 의존]

**대상 파일**: `tools/install/manifest.py`. 세 함수 + 헬퍼를 구현한다. **전부 결정론적 코드 — LLM 병합 없음** (impl-inputs §A 채택).

**Step 2.1 — 헬퍼.**
- `_sha256(path)` → hex digest (스트리밍).
- `_manifest_path(runtime, scope)`, `_pristine_path(...)`, `_backup_path(...)` — `paths.harness_state_dir` 경유.
- `_safe_relpath(rel)` → 절대 경로, `..`, NUL, symlink 탈출을 거부 (impl-inputs §A #7 경로 안전성); manifest 에서 유도한 모든 relpath 를 디스크에 손대기 전에 통과시킨다.
- `_load_manifest`/`_write_manifest` (JSON, 키 정렬, temp+rename 방식 원자적 쓰기).

**Step 2.2 — `record(runtime, files, scope="global", version=None)`** (`NotImplementedError` 대체).
- `files` = projector 의 `copy_once` action 에서 온 copy-once 항목 목록 `{relpath, source_abs, dest_abs}`.
- 각 항목마다: pristine 스냅샷이 있는지 확인하고 (`source_abs` → pristine/<relpath> 복사는 **없을 때, 또는 깨끗한 재적용 후 설치가 갱신하는 경우에만** — 드리프트가 해소되지 않은 동안 pristine 을 절대 덮어쓰지 않음), **설치된 dest 바이트**의 SHA-256 을 계산해 `files` 맵에 추가한다.
- manifest 를 쓰되 `version` = 현재 저장소 git SHA (`git rev-parse HEAD`, 실패 시 "unknown").
- 멱등적: 재-`record` 는 manifest 를 덮어쓰지만 기존 pristine 은 보존한다.
- **완료 기준**: 임시 HOME 설치 후 `<temp>/.claude/.harness/manifest.json` 이 `settings.json`/`keybindings.json` 을 해시와 함께 나열하고, `<temp>/.claude/.harness/pristine/settings.json` 이 존재한다.

**Step 2.3 — `check_drift(runtimes, scope="global")`** (`return []` 대체).
- manifest 가 있는 각 런타임마다: 각 dest 파일의 SHA-256 을 다시 계산해 기록된 해시와 비교한다. 불일치 = 사용자 수정 → `{"runtime", "path", "detail": "hash mismatch"}` 추가. dest 부재 = `{"detail": "manifest file absent"}`.
- **불변식** (impl-inputs §A 함정): 해시 불일치는 언제나 사용자 내용이 있다는 뜻이다 — "기계적으로 보인다" 는 이유로 건너뛰지 않는다.
- **완료 기준**: 임시 HOME 에 설치하고 `<temp>/.claude/settings.json` 을 손으로 편집하면, `harness update --json` 이 그 경로를 `drift[]` 에 보고하고 `EXIT_DRIFT` (4) 로 종료한다.

**Step 2.4 — `reapply(runtimes, scope="global")`** (`NotImplementedError` 대체).
- Pre-wipe 패스 (GSD `saveLocalPatches`-before-wipe 의 순서 불변식): 드리프트된 각 파일마다 현재 dest → `local-patches/<relpath>` 로 복사 (전체 복사) 하고, `from_version` + `pristine_hashes` 를 담은 `backup-meta.json` 을 기록한다.
- **`git merge-file`** 로 3-way 병합: `git merge-file -p --diff3 <ours=current-dest> <base=pristine> <theirs=new-canonical-source>` → 병합 바이트. (pristine = 구 릴리스 base; theirs = 현재 저장소 소스.)
- 병합 결과를 dest 에 쓰는 것은 **충돌 마커가 없을 때만**; 충돌 시 충돌 마커가 남은 파일을 그대로 두고 `{"path", "status": "conflict"}` 를 보고하며 강제 병합하지 않는다 (PRD "3-way 충돌은 명시 report").
- **결정론적 사후 병합 검증기** (impl-inputs §A #5): `local-patches/<relpath>` 의 의미 있는(빈 줄·마커 아닌) 모든 줄이 병합 출력의 부분 문자열임을 확인한다; 아니면 `verify_failed` 로 표시하고 backup 을 유지한다. LLM 없음.
- 재적용이 성공하면 pristine 을 새 정본 바이트로 갱신하고 manifest 해시를 다시 쓴다.
- `{"reapplied": [...], "conflicts": [...], "verify_failed": [...]}` 반환.
- **완료 기준**: 설치 → dest 편집 → 저장소 정본 소스 변경 → `harness update --reapply --json` 이 깔끔히 병합하거나(혹은 충돌 보고) 병합된 파일이 사용자 편집 줄을 담고 있으며, `local-patches/` 에 backup 이 있다.

---

### Phase 3 — drivers/{claude,codex,opencode}.py: install()/status()/checks() (P0.4) [Phase 1 의존]

각 드라이버의 `install()` 은 projector plan (symlink/copy_once/glob/delegate/merge) 을 적용하고, 알맞은 생성기를 호출하며, manifest 를 기록한다. **checks() 는 인자 없는 callable 목록을 반환**하고, 각각 `{"id","ok","detail"}` 을 반환한다 (`verifier.run` 이 이미 순회함).

**Step 3.1 — `drivers/claude.py`.**
- `install(scope, plugin, dry_run)`: claude projector plan 적용. Claude 는 생성기가 없다 — 순수 symlink + `copy_once`. `copy_once` 에서는 `settings.json`/`keybindings.json` 에 대해 `manifest.record()` 를 호출한다. 호스트가 Windows 면 (`os.name == 'nt'` 또는 MSYS/`sys.platform` 으로 감지) 원시 symlink 대신 `delegate` 항목 (`adapters/claude/bin/install-windows.sh`) 을 실행한다. `dry_run=True` → 디스크를 건드리지 않고 계획된 action 을 반환. `plugin=True` → Phase 7 래핑 (사이클 1: P1 이 들어오지 않았으면 `SKIP(claude): plugin channel — P1, see Phase 7` 을 내보냄).
- `status()`: manifest 읽기 (version SHA, 파일 개수), `check_drift(["claude"])` 실행, `{channel, version, drift_count}` 반환.
- `checks()`: 읽기 전용 callable 목록 (점검 본체는 Phase 4 에서 구현).

**Step 3.2 — `drivers/codex.py`.**
- `install()`: codex projector plan 적용 (고정 symlink + agents/skills glob). **`plugin=True` 일 때도 symlink 투영은 항상 유지** — agents `.toml`/프롬프트/config 조각은 플러그인으로 실을 수 없다 (INST-D-5; scaffold docstring 이 이미 경고). codex 에는 copy-once 파일이 없다 → `manifest.record` 는 빈 복사 집합으로 호출 (혹은 건너뜀). 선택적으로 `sync-native-{skills,agents,modes,plugin}.py` 를 (인자 없이, 투영 재생성 목적으로) 실행 — `--generate` 의도 뒤에 둔다; 기본 설치는 투영이 이미 생성돼 있다고 가정하고, verify 가 드리프트를 잡는다.
- `status()`: 채널 감지 — `~/.codex/agent-harness` 포인터 + 플러그인 마켓플레이스 존재 확인.
- `checks()`: Phase 4.

**Step 3.3 — `drivers/opencode.py`.**
- `install()`: opencode projector plan 적용; `opencode.json` 은 **비파괴 병합** — 기존 사용자 config 를 읽어 `instructions[]` / `skills.paths` / `plugin[]` 항목을 **없을 때만** 추가하고; 같은 키에 다른 값이 충돌하면 → **보고 + 중단** (`EXIT_BLOCKED` 경로), 자동 해소 없음 (PRD "의미↔규칙 경계 체크"). 로컬 1.17.13 단수 배선 사용 (impl-inputs §B).
- `status()`: 포인터 + config 병합 존재 여부.
- `checks()`: Phase 4.
- **완료 기준 (세 드라이버 모두)**: `harness install <rt> --dry-run --json` 이 비어 있지 않은 `checks[]`/plan 을 반환하고 `NotImplementedError` 가 없으며; `status` 가 실제 채널/버전 dict 를 반환한다.

---

### Phase 4 — verifier.py 실제 점검 목록 (P0.2) [Phase 3 의존]

**대상**: 각 드라이버의 `checks()` 가 반환하는 callable 을 구현한다. `verifier.run()` 은 손댈 필요 없다 (이미 순회함). 모든 점검은 **읽기 전용** (안전 제약). Migration Order (INSTALL_LAYOUT 239-512번째 줄) 를 기계화한다.

**⚠️ 런타임별 비대칭 (세 런타임에 균일한 점검 집합을 적용하지 말 것):** Claude 는 **네이티브** 런타임이라 **`adapters/claude/bin/sync-native-*.py` 생성기도 없고** **`claude_setting/bin/preflight.sh` 도 없다**. 따라서 "sync-native `--check`" 점검과 "preflight 계약 smoke" 점검은 **codex 와 opencode 에만** 적용된다. Claude verify 경로는 대신 투영 symlink 존재 + `tools/build-manifest.py --check` + 컴파일 smoke + (CLI 있을 때만) bootstrap 로드에 기댄다. 점검 개수는 의도적으로 불균등하다: claude 약 3-4개 (sync-native 없음, preflight 없음), codex 약 4개 sync-native `--check` + preflight + symlink + bootstrap, opencode 약 3개 sync-native `--check` + preflight + symlink + drift-watch + bootstrap.

**Step 4.1 — 공유 점검 헬퍼** (`verifier.py` 또는 `checks_common.py` 에 둠): `check_symlink(dest, expected_source)` (존재 + 기대 소스로 resolve), `check_cmd(argv, must_match=[regex])` (읽기 전용 subprocess 실행, stdout grep), `check_file_exists(path)`.

**Step 4.2 — claude 점검** (preflight.sh 없음; 네이티브 런타임):
- (a) 각 claude projector 항목의 투영 symlink 존재 (dest 가 symlink → 기대 소스).
- (b) `python3 tools/build-manifest.py --check` 종료 코드 0 (투영 드리프트 생성기).
- (c) 컴파일 smoke: `python3 -c "compile(...)" tools/build-manifest.py tools/memory/mem.py` (Migration Order 252번째 줄).
- (d) bootstrap 로드 smoke (선택, `claude` CLI 있을 때만): CODEX 아날로그 — `claude` 에는 보장된 `debug prompt-input` 등가물이 없으므로 CLI 존재 뒤에 두고, 없으면 `SKIP(claude): bootstrap smoke — claude CLI absent`.

**Step 4.3 — codex 점검** (Migration Order 255-402번째 줄):
- (a) 투영 symlink 존재 (codex projector 항목).
- (b) `adapters/codex/bin/sync-native-{skills,agents,modes,plugin}.py --check` 각각 종료 코드 0.
- (c) preflight 계약 smoke — 서브커맨드 1-2개: `adapters/codex/bin/preflight.sh capability-info autopilot-code` 는 `native_skill_path=...` 를 내보내야 하고; `preflight.sh role fast reviewer` 는 `adapter=codex` 를 내보내야 한다. (안전·범위상 1-2개로 유지; 260줄짜리 전체 배터리는 사이클 1 대상이 아님.)
- (d) bootstrap 로드 smoke (`codex` CLI 있을 때만): 임시 CODEX_HOME 에 `codex_setting/AGENTS.md` symlink, `codex debug prompt-input 'bootstrap check'` 가 `AGENTS.md — Codex Adapter Bootstrap` 을 grep. CLI 존재 뒤에 두고 없으면 SKIP.

**Step 4.4 — opencode 점검** (Migration Order 403-511번째 줄):
- (a) 투영 symlink 존재 (opencode projector 항목, 단수 배선).
- (b) `adapters/opencode/bin/sync-native-{skills,agents,commands}.py --check` 각각 종료 코드 0.
- (c) preflight 계약 smoke — `adapters/opencode/bin/preflight.sh capability-info autopilot-code` 가 `native_skill_path=...` 를 내보내고; `preflight.sh role fast reviewer` 가 `adapter=opencode` 를 내보낸다.
- (d) **doc-vs-wiring 드리프트 감시** (impl-inputs §B 의무): 로컬 opencode 버전과 복수형 디렉토리 (`skills/`,`agents/`,`commands/`) 존재 여부를 기록하는 점검; 단수 1.17.13 아래에서는 통과(ok=True) 하되, 향후 버전 상승 시 드러나도록 `detail` 에 드리프트를 명시한다. 이것이 유일한 INST-OPEN-4 센티널이다.
- (e) bootstrap 로드 smoke (`opencode` CLI 있을 때만): 임시 HOME + Migration Order 486-493 의 `OPENCODE_CONFIG_CONTENT`, `opencode_setting/AGENTS.md` grep. CLI 존재 뒤에 두고 없으면 SKIP.
- **완료 기준**: `harness verify --json` 이 실제 id (`claude.symlink.core`, `codex.sync-skills`, `opencode.drift-watch`, ...) 를 가진 `checks[]` 를 반환하고, "no-checks" placeholder 가 아니라 실제 결과에 따라 0/2 로 종료한다.

---

### Phase 5 — installer.py 연결: cmd_* 실제 동작 (P0 통합) [1,2,3 의존]

**대상**: `tools/install/installer.py` 의 cmd_* 함수.

**Step 5.1 — `cmd_install`**: TODO 루프 (108-110번째 줄) 를 교체한다. 각 런타임마다 `driver.install(scope=args.scope, plugin=args.plugin, dry_run=args.dry_run)` 를 호출하고; 반환된 action 보고를 `checks[]` 로 모으며; 부재 소스·미지원 표면에 대한 `SKIP(...)` 줄을 드러낸다 (parity-loss). BLOCKED 조건 (런타임 프로세스 실행 중, opencode 병합 충돌) 에서는 `EXIT_BLOCKED` 를 반환한다. `--json` 형태 유지 (`{runtime, channel, checks, drift, exit, lines}`).
**Step 5.2 — `cmd_status`**: 스텁 (145-147번째 줄) 을 `driver.status()` 결과 (channel/version/drift) 로 교체한다.
**Step 5.3 — `cmd_update`**: `installer.py:132` 의 `if args.reapply` 드리프트 게이트 (`drift = manifest.check_drift(runtimes) if args.reapply else []`) 를 **제거**해, **일반 `update` 도 항상 드리프트를 계산·보고**하게 한다 (드리프트 감지가 `--reapply` 를 요구해선 안 됨). 새 동작: 항상 `drift = manifest.check_drift(runtimes)`; 드리프트가 있고 `--reapply` 가 **아니면** → 드리프트 목록과 함께 `EXIT_DRIFT` (4) (사용자가 결정해야 함). `--reapply` 일 때 → `manifest.reapply()` 를 호출하고 `reapplied/conflicts/verify_failed` 를 보고; 충돌 → `EXIT_DRIFT` (혹은 BLOCKED), 깨끗함 → `EXIT_OK` 로 매핑.
**Step 5.4 — `cmd_uninstall`**: manifest 범위 제거를 구현한다 — manifest 를 읽어 열거된 파일 + projector 가 만든 symlink 만 제거하고, 비어 있는 공유 디렉토리만 rmdir 하며, `.harness/manifest.json` 을 마지막에 삭제한다. 런타임 자격증명/세션/프로젝트는 절대 건드리지 않는다 (소유권 경계). 제거 전에 backup (local-patches 재사용). Dry-run 은 제거될 대상을 나열한다.
- **완료 기준**: 임시 HOME 전 과정 루프 (install → status → update → uninstall) 가 올바른 종료 코드와 `--json` 형태로 돌고; uninstall 후 임시 HOME 에는 manifest 외 파일만 남는다.

---

### Phase 6 — mem import + ~/.local/bin 런처 symlink (P0.5) [독립, 병렬 가능]

**Step 6.1 — `cmd_install` (또는 드라이버 중립 헬퍼 `bootstrap.py`) 안의 메모리 복원.**
- Claude 설치 후, `$MEM_STORE/memory.db` (기본 `$AGENT_HOME/memory/memory.db`) 가 없지만 `dump.jsonl` 이 있으면 `python3 tools/memory/mem.py import <dump.jsonl>` 를 호출한다 (재사용 — 재구현 금지). 가드: DB 가 없을 때만 (멱등적). 임시 HOME 아래에서는 `MEM_STORE` 오버라이드를 존중해 테스트가 실제 메모리 저장소를 건드리지 않게 한다.
- **완료 기준**: `MEM_STORE=<temp>/mem` + 작은 `dump.jsonl` 로 설치하면 `<temp>/mem/memory.db` 가 생성되고; 재실행은 no-op.

**Step 6.2 — PATH 런처 symlink.**
- `~/.local/bin/harness` → `tools/install/harness.sh`, `~/.local/bin/fleet` → `tools/fleet/fleet.sh` 설치 (INSTALL_LAYOUT 94-98번째 줄 패턴). `mkdir -p ~/.local/bin`; `ln -sfn`. **PATH 충돌 가드** (INST-OPEN-2): PATH 상의 기존 `harness` 가 우리 symlink 가 아니면 경고 + SKIP (덮어쓰지 않음). Dry-run 은 걸려는 링크를 출력한다.
- **완료 기준**: 임시 HOME 아래에서 설치가 `<temp>/.local/bin/{harness,fleet}` symlink 를 만들고; 외부의 기존 `harness` 는 경고+건너뛰기 줄을 유발한다.

---

### Phase 7 — P1: plugin 채널 래핑 + Claude 플러그인 콘텐츠 (경계)

**사이클 1 경계 결정:**
- **이번 사이클 안 (여력 남으면)**: **Codex** 용 `install --plugin` CLI 래핑 (동작하는 `adapters/codex/plugin-marketplace/` 재사용): `codex plugin marketplace add <path>` + `codex plugin add agent-harness-codex@agent-harness`, 그리고 verify 항목 하나. 저위험이다 (마켓플레이스가 이미 동작하고, Migration Order 353-357 이 명령을 입증). **Step 7.1.**
- **다음 사이클로 명시적 연기**:
  - **Claude 플러그인 콘텐츠 생성기** — 새 sync-native 생성기로 정본에서 `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/` (skills/agents/hooks/.mcp.json/bin) 를 물리적으로 materialize. 규모가 크고 (새 생성기 + 빌드 시점 자기완결 포함, PRD "설치본은 self-contained") 자기 사이클로 다뤄야 한다. 사이클 1 은 골격을 남기고 `SKIP(claude): plugin channel — deferred to next cycle` 을 내보낸다.
  - **Claude `install --plugin` 래핑** (`claude plugin marketplace add` + `claude plugin install`) — 위 콘텐츠 생성기에 의존하므로 함께 연기.
- **Step 7.1 (Codex 플러그인 래핑, 시간 남으면 사이클 내 P1)**: `drivers/codex.py` 에서 `plugin=True` 경로가 두 `codex plugin ...` 명령 (subprocess, `--json`) 을 호출하되, `codex` CLI 존재 뒤에 둔다 (없으면 SKIP). 플러그인 마켓플레이스가 resolve 되는지 확인하는 codex verify 점검을 추가한다. symlink 투영은 여전히 돈다 (INST-D-5).
- **완료 기준**: `harness install codex --plugin --dry-run` 이 계획된 `codex plugin marketplace add`/`plugin add` 명령을 출력하고; Claude `--plugin` 은 연기 SKIP 을 출력한다.

## 리스크

- **실제 홈에 대한 symlink/copy**: 디스크를 변경하는 모든 action 은 시연에서 `dry_run` 으로 보호하고 임시 `HOME` 을 향해야 한다. 드라이버는 테스트 중 `~/.claude`/`~/.codex`/`~/.config/opencode` 에 절대 쓰지 않는다 (검증 방법 참조).
- **install-windows.sh 위임**: Windows 에서만 발동; Linux 에서는 `delegate` action 이 no-op. WSL 에서 POSIX symlink 가 동작하면 플랫폼 감지가 실수로 이를 돌리지 않도록 한다 (WSL 은 Linux symlink 경로를 타야 함).
- **pristine 덮어쓰기** (impl-inputs §A #3407): 드리프트가 해소되지 않은 동안 pristine 을 새 릴리스 바이트로 갱신하면 3-way 델타가 뒤집힌다. 가드: pristine 은 *성공적으로 검증된* 재적용 후에만 갱신하고, 드리프트 도중에는 절대 갱신하지 않는다.
- **`git merge-file` 가용성**: 재적용은 PATH 에 `git` 이 필요하다. 사전 점검으로 게이트하고; 없으면 "backup + 보고, 자동 병합 없음" 으로 격하한다 (조용히 넘어가지 않음).
- **opencode.json 병합**: 같은 키/다른 값은 추측하지 말고 멈춰서 보고해야 한다 (유일한 의미 경계 후보이며, PRD 대로 규칙으로 해소).
- **시그니처/호출자 영향**: `projector.plan()` 반환 형태가 `{rt: [ {source,dest} ]}` 에서 `{rt: [ {action, ...} ]}` 로 바뀐다. 유일한 호출자는 `installer.cmd_install` (104/110번째 줄) 이고 현재 `len(plan.get(rt, []))` 를 읽으므로 — 여전히 유효하다. 드라이버 `install()` 시그니처 `(scope, plugin, dry_run)` 은 이미 scaffold 와 일치하니 호출자 변경 불필요. `manifest.record/check_drift/reapply` 시그니처는 보존한다 (installer 가 이미 `check_drift(runtimes)` 를 호출; 기본값 있는 선택적 `scope` 추가). `verifier.run(runtime, driver)` 는 그대로.

### 미해결

- **Claude 네이티브 런타임 비대칭 (설계 제약, 차단 요소 아님)**: `INSTALL_LAYOUT.md` 의 `$AGENT_HOME/{claude,codex,opencode}_setting/` 아래 투영 소스는 **이 worktree 에 모두 존재하고 git 추적되며** `AGENT_HOME=<repo root>` 에서 resolve 된다; 전 과정을 별도 체크아웃 없이 여기서 검증할 수 있다. 유념할 비대칭 하나 (Phase 4 에서 처리): Claude 는 네이티브라 **`claude_setting/bin/preflight.sh` 도, `adapters/claude/bin/sync-native-*.py` 도 없다** — codex/opencode 에만 있다. 그래서 verifier 점검 집합은 런타임별로 의도적으로 불균등하다 (Phase 4 노트). projector 는 여전히 소스를 `AGENT_HOME` 기준으로 resolve 하므로 (절대 경로 하드코딩 없음) HLS 정본 재구조화가 편집 없이 흘러간다.
- **INST-OPEN-4 (PRD 상 여전히 OPEN)**: OpenCode 복수형 디렉토리 / `skills.paths` 마이그레이션은 연기; 사이클 1 은 단수 1.17.13 배선을 유지하고 drift-watch 센티널 (Phase 4.4d) 만 추가한다.
- **OpenCode opencode.json 병합 manifest (모호)**: PRD 는 hash-manifest 가 *복사된* 파일만 추적한다고 하는데; `opencode.json` 은 복사가 아니라 병합 관리 대상이다. 사이클 1 은 조각 존재 여부만 기록하고 완전한 병합 인지 manifest 는 연기한다. 병합 관리 파일도 드리프트 추적이 필요한지 spec 소유자에게 확인할 것.

## 검증 방법

모든 명령은 저장소 루트에서 **일회용 HOME** 과 **AGENT_HOME/MEM_STORE 오버라이드**로 실행하며 — 실제 런타임 홈은 절대 쓰지 않는다. 기준 설정 블록 (각 Phase 점검 앞에 붙임):

```bash
cd /home/Uihyeop/agent_setting-wt/harness-installer-impl
export REAL_REPO="$PWD"
export HOME="$(mktemp -d)"                 # throwaway target home — isolates ~/.claude etc.
export AGENT_HOME="$REAL_REPO"             # source repo (see INST-STALE-1 re: *_setting/)
export MEM_STORE="$HOME/mem"; mkdir -p "$MEM_STORE"
# harness.sh is a POSIX sh launcher that exec's `python3 installer.py "$@"` — invoke it via sh, not python.
harness() { sh "$REAL_REPO/tools/install/harness.sh" "$@"; }
# (equivalent direct form if a shell function is inconvenient:
#   python3 "$REAL_REPO/tools/install/installer.py" <args> )
```

**Phase 0 (paths/schema):**
```bash
python3 -c "import sys; sys.path.insert(0,'$REAL_REPO/tools/install'); import paths; \
  print(paths.agent_home()); print(paths.runtime_home('claude','global'))"
# expect: repo root; then $HOME/.claude   (under temp HOME)
```

**Phase 1 (projector dry-run):**
```bash
harness install --dry-run --json | python3 -m json.tool
# expect: per-runtime plan with action-typed entries. In THIS worktree (no *_setting/):
#   entries with "action":"skip","reason":"source absent: .../claude_setting/core" etc.
# When AGENT_HOME points at a materialized checkout: full symlink+copy_once list, no skips.
```

**Phase 2 (manifest record + drift + reapply):**
```bash
# record: copy_once sources (claude_setting/settings.json, keybindings.json) exist in this worktree.
mkdir -p "$HOME/.claude"
harness install claude --json                               # real writes into $HOME/.claude only
test -f "$HOME/.claude/.harness/manifest.json" && echo "manifest OK"
# drift: hand-edit a recorded copy-once file, then:
echo '// user edit' >> "$HOME/.claude/settings.json" 2>/dev/null || true
harness update --json; echo "exit=$?"          # expect drift[] non-empty, exit=4
# reapply: change canonical source, then:
harness update --reapply --json                # expect reapplied[] and merged file keeps '// user edit'
grep -q 'user edit' "$HOME/.claude/settings.json" && echo "reapply preserved edit"
```

**Phase 3-4 (drivers + verify, read-only):**
```bash
harness verify --json | python3 -m json.tool
# expect: checks[] with real ids (claude.symlink.*, codex.sync-skills, opencode.drift-watch, ...),
#   exit 0 if all pass else 2. NO disk mutation (all checks read-only).
harness verify codex --json     # subset
harness status --json           # channel/version/drift per runtime, no NotImplementedError
```

**Phase 5 (full lifecycle, temp HOME):**
```bash
harness install all --dry-run --json     # plan only, no writes
harness install claude --json            # real writes into $HOME/.claude only
harness status --json
harness update --json
harness uninstall claude --dry-run --json  # lists manifest-scoped removals
harness uninstall claude --json            # removes only manifest entries + created symlinks
test ! -f "$HOME/.claude/.harness/manifest.json" && echo "clean uninstall"
# assert real homes untouched:
test -z "$(ls -A ~/.claude 2>/dev/null | grep -v '^$')" || true   # temp HOME only
```

**Phase 6 (mem import + launchers):**
```bash
printf '{"id":"t1","type":"note","body":"probe","tags":[],"links":[]}\n' > "$MEM_STORE/dump.jsonl"
harness install claude --json >/dev/null 2>&1 || true
test -f "$MEM_STORE/memory.db" && echo "mem import OK"     # DB created from dump
test -L "$HOME/.local/bin/harness" && test -L "$HOME/.local/bin/fleet" && echo "launchers OK"
# collision guard:
printf '#!/bin/sh\n' > "$HOME/.local/bin/harness2"; # foreign name test as needed
```

**Phase 7 (plugin dry-run):**
```bash
harness install codex --plugin --dry-run --json
# expect planned: codex plugin marketplace add <path> + codex plugin add agent-harness-codex@agent-harness
harness install claude --plugin --dry-run --json
# expect: SKIP(claude): plugin channel — deferred to next cycle
```

**안전 단언 (마지막에 실행, 전 과정 내내 유지돼야 함):** 위 어떤 명령도 `$HOME` (임시) 이나 `$MEM_STORE` (임시) 바깥에 쓰지 않는다. 실제 `~/.claude`/`~/.codex`/`~/.config/opencode` 는 어떤 `harness` 호출보다 앞서 `HOME` 이 mktemp 디렉토리로 재지정되므로 애초에 범위 밖이다. `code-test` 는 실행 후 실제 홈의 mtime 이 그대로인지 확인해 이를 입증해야 한다.

## 변경 이력

- **2026-07-13 (plan-check 정정 패스)** — standard-tier plan-check 가 찾은 BLOCKING 2건 + non-blocking 1건을 수정 (worktree 에 대해 파일시스템으로 검증):
  - **B1**: 뒤집힌 전제를 바로잡음. `{claude,codex,opencode}_setting/` 투영 소스 디렉토리는 **실제로 존재하고 git 추적된다** (앞서의 glob 이 symlink 로 걸린 디렉토리를 순회하지 못했고, symlink 를 통한 `Read` 로 존재를 확인). 현황 레이아웃 bullet, Phase 1.1 claude 노트, Phase 1.2 완료 기준 (이제 `skip: source absent` **없이** resolve 된 전체 symlink plan 을 기대), Phase 2 검증 주석을 다시 쓰고, Unresolved 의 "INST-STALE-1 (CLEAR-BUT-STALE, dirs absent)" 항목을 "Claude 네이티브 런타임 비대칭" 설계 제약 노트로 교체. 확인된 뉘앙스는 보존: Claude 는 네이티브 → `claude_setting/bin/preflight.sh` 도, `adapters/claude/bin/sync-native-*.py` 도 없음; 점검 집합이 균일하게 적용되지 않도록 Phase 4 에 명시적 런타임별 비대칭 배너를 추가 (claude 약 3-4개 vs codex/opencode 는 sync-native `--check` + preflight 추가).
  - **B2**: 실행 불가능한 검증 기준 블록을 수정. `tools/install/harness.sh` 는 python 이 아니라 POSIX **sh** 런처다 (`python3 installer.py "$@"` 를 exec) — `alias harness="python3 .../harness.sh"` 를 셸 함수 `harness() { sh "$REAL_REPO/tools/install/harness.sh" "$@"; }` 로 교체 (+ 직접 `python3 installer.py` 폴백 노트).
  - **N1**: `cmd_update` 를 내부적으로 일관되게 만듦 — Phase 5.3 이 이제 `installer.py:132` 의 `if args.reapply` 드리프트 게이트 **제거**를 계획하므로, 일반 `update` 도 항상 드리프트를 계산·보고한다 (Phase 2.3 의 `harness update --json` → drift[]/exit 4 기대와 일치).
