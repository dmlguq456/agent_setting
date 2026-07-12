# harness-installer scaffold v1 — autopilot-spec Step 4 결과

브랜치 `harness-installer-scaffold` · 커밋 `9792fd3084ab1a11370f5affea655f4263ed4d56`.

## 생성 파일

- `tools/install/harness.sh` — thin POSIX sh launcher. 심링크 경유 시 실경로 해석(`fleet.sh` 동형 loop, BASH_SOURCE 없이 `$0` 만 사용) 후 `exec python3 installer.py "$@"`.
- `tools/install/installer.py` — argparse 서브명령 트리(`install [claude|codex|opencode|all]` / `verify [runtime]` / `update [--reapply]` / `status` / `uninstall [runtime]`) + 공통 옵션(`--runtime`(반복)/`--scope`/`--dry-run`/`--json`/`--yes`/`--plugin`) + exit code 상수(0/1/2/3/4/64, PRD 표와 1:1) + `--json` 출력 shape(`{runtime, channel, checks, drift, exit}`). usage 오류는 argparse 기본 exit(2) 대신 `_UsageExitParser` 로 64 강제.
- `tools/install/projector.py` — symlink projection plan stub. `plan(runtimes, scope)` 은 항상 빈 리스트 반환(INSTALL_LAYOUT 레시피 이식은 구현 사이클 몫, OpenCode 는 INST-OPEN-4 실측 후).
- `tools/install/manifest.py` — hash-manifest 기록·drift·reapply stub. `record()`/`reapply()` 는 `NotImplementedError`(HLS §3.2 GSD `bin/install.js` 정독 게이트 TODO 명시), `check_drift()` 는 항상 `[]`.
- `tools/install/verifier.py` — check 목록 실행기(runner)만. `driver.checks()` 가 비면 `"<runtime>.no-checks"` fallback 항목 1개로 pass 처리.
- `tools/install/drivers/__init__.py` — `get_driver(runtime)` + `RUNTIMES = ("claude","codex","opencode")`.
- `tools/install/drivers/claude.py` / `codex.py` / `opencode.py` — 채널 driver 인터페이스 stub(`install()`/`status()` 는 `NotImplementedError`, `checks()` 는 `[]`). 각 docstring 에 호출 대상(기존 `sync-native-*.py`·`preflight.sh`, 재구현 금지)과 PRD 표의 탑재 가능/불가 경계, Codex "plugin 만으로 완결 불가", OpenCode legacy 배선 drift(INST-OPEN-4) 를 주석으로 명시.
- `adapters/claude/plugin-marketplace/.claude-plugin/marketplace.json` — Codex 동형 대칭. `name: agent-harness`, plugin entry `agent-harness-claude`, `source: "./plugins/agent-harness-claude"` (relative-path).
- `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/.claude-plugin/plugin.json` — `name`/`description`/`author` 만.
- `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/README.md` — "sync-native 생성기 산출 자리, 손 편집 금지" 한 줄 안내.
- `.gitignore` — 루트 `plugins/` 무차별 ignore 규칙이 `adapters/claude/plugin-marketplace/plugins/`(Codex/OpenCode 와 이름 패턴 동일)까지 오폭해 신규 파일이 untracked 로 잡혀, Codex/OpenCode 선례와 동형으로 `!adapters/claude/plugin-marketplace/` + `!adapters/claude/plugin-marketplace/**` 예외 2줄 추가.

## 구문 검증

- `sh -n tools/install/harness.sh` → 통과.
- `python3 -c "import py_compile; py_compile.compile('tools/install/installer.py', doraise=True)"` → 통과.
- 동일하게 `projector.py`/`manifest.py`/`verifier.py`/`drivers/__init__.py`/`drivers/{claude,codex,opencode}.py` 전부 `py_compile` 통과.
- `python3 -m json.tool` 로 `marketplace.json`/`plugin.json` 파싱 통과.
- 런타임 스모크: `sh tools/install/harness.sh install claude --dry-run --json` / `verify --json` / `status` / `uninstall` 정상 실행(exit 0), 잘못된 서브명령(`bogus`) 은 exit 64 확인.

## 커밋

`9792fd3084ab1a11370f5affea655f4263ed4d56` — "harness-installer scaffold: tools/install/ CLI skeleton + Claude plugin-marketplace skeleton" (13 files changed, 432 insertions).

## 미결·주의사항

- **hash-manifest 실구현 금지 확인**: `manifest.record`/`manifest.reapply` 는 의도적으로 `NotImplementedError` — PRD "구현 선행 게이트"(GSD `bin/install.js` 정독, HLS §3.2 공유) 를 아직 통과하지 않았음. 다음 사이클에서 이 게이트를 먼저 통과해야 함.
- **driver.checks() / install() 전부 미구현** — `verify`/`status` 는 현재 항상 "scaffold stub" 문구로 pass 를 리턴한다(진짜 검증 아님). 구현 사이클에서 채워야 실제 Migration Order 대체가 완성됨.
- **projector.plan() 은 빈 계획** — INSTALL_LAYOUT.md 의 실제 symlink 나열을 옮기지 않았다(파일 자체는 이번 스캐폴딩에서 손대지 않음, 규칙 준수).
- **OpenCode 배선 drift(INST-OPEN-4)** — `drivers/opencode.py` docstring 에 legacy 배선(단수형 디렉토리·`skills.paths`) 을 그대로 베끼지 않는다고 명시했으나, 구현 Step 0 실측 자체는 아직 수행 안 함.
- **`.gitignore` 예외 추가**는 이번 스코프 밖이었지만 신규 산출물이 untracked 되는 구조적 문제라 함께 처리함 — conductor 확인 권장(기존 adapter 파일 자체는 미수정).
- merge·브랜치 삭제·worktree 정리는 하지 않음 — main orchestrator 몫.
