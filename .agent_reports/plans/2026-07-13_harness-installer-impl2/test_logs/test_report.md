# code-test — harness-installer 구현 사이클 2 — 종합 결과

plan: `../plan/plan.md` (Phase 1~5) · checklist: `../plan/checklist.md`

## 요약

| 스크립트 | 대상 | PASS | FAIL | 도달 레벨 | real-home 결정론 가드 |
|---|---|---|---|---|---|
| `01_generator_plugin_content.sh` | Phase 1 (`sync-native-plugin.py`) | 15 | 0 | syntax → import → smoke → functional | PASS |
| `02_driver_plugin_wiring_and_verify.sh` | Phase 2+3 (`drivers/claude.py` install/checks) | 24 | 0 | syntax → import → smoke → functional → **CLI-gated integration** | PASS |
| `03_install_layout_and_regression.sh` | Phase 4 (`INSTALL_LAYOUT.md`) + 회귀 | 14 | 0 | 문서 계약 검증 + 회귀 스모크 | PASS |
| **합계** | | **53** | **0** | 전 레벨(CLI-gated integration 포함) 도달 | **3/3 PASS** |

로컬에 `claude` CLI(2.1.207)가 존재해 CLI-gated integration(실제 `claude plugin marketplace add`/`plugin install`)까지 전부 실행됨 — SKIP 경로가 아니라 실제 등록·조회까지 검증됨.

## real-home 결정론 가드 (가장 중요)

세 스크립트 모두 실행 **전** 시점의 real `~/.claude/settings.json`·`~/.codex/config.toml`·`~/.config/opencode/opencode.json`·`~/.claude/plugins/`(재귀) sha256 을 스크립트 최상단(HOME 재할당 이전)에서 캡처하고, `trap ... EXIT` 로 스크립트 종료 시(정상 종료 경로) 재확인했다. **3/3 스크립트 모두 가드 통과** — 사이클 1 인시던트(`INCIDENT_real_home_touched.md`)와 동일한 실제 홈 오염은 재발하지 않았다.

추가로 최종 `git status --porcelain` 이 이번 사이클의 예상 baseline diff(`INSTALL_LAYOUT.md`, `tools/install/drivers/claude.py` 수정 + `adapters/claude/bin/sync-native-plugin.py` 신규 + `adapters/claude/plugin-marketplace/plugins/agent-harness-claude/{skills,agents,hooks}` 신규)와 정확히 일치함을 확인 — 세 스크립트의 반복 실행(touch→drift-check→regen 사이클 포함)이 repo 안에 어떤 잔여 변경도 남기지 않았다.

## 격리 계약 준수 (plan Phase 5 §1-4)

1. **단일 self-contained 스크립트**: `_internal/test_scripts/*.sh` 3개 각각 정확히 1회 `sh` 프로세스(=1회 Bash 도구 호출)로 실행 — `HOME`/`AGENT_HOME`/(`CLAUDE_CONFIG_DIR`, 필요한 스크립트만) 를 스크립트 **최상단**에서 export, 별도 Bash 호출 경계를 넘긴 적 없음.
2. **명시적 target-root 인자만**: `sync-native-plugin.py` 는 `__file__` 기준 `ROOT`(repo root)만 알고 어떤 env 도 읽지 않음 — bare `$HOME` 참조 자체가 구조적으로 불가능. `harness`/driver 호출은 전부 mktemp `HOME` 재할당 이후.
3. **결정론 가드**: 위 참조.
4. **`claude plugin` 실 CLI 호출**: 스크립트 02 는 `CLAUDE_CONFIG_DIR` 를 스크립트 **최상단**(HOME/AGENT_HOME 과 나란히)에서 mktemp 로 설정 — `checks()` 내부에서 간접 호출되는 `claude plugin marketplace list --json`/`plugin list --json` 를 포함해 스크립트 안의 **모든** `claude` CLI 호출이 처음부터 격리됨(HOME 재할당 단독에 의존하지 않음, contract §4 의 문자 그대로 준수). 등록 후 `installPath` 가 real `~/.claude/plugins` 하위가 **아님**을 명시적으로 assert.
5. **worktree 사전 상태 확인**: 세 스크립트 실행 전후 `git status --porcelain` 을 스크립트 01 §0/§5 및 이 보고서에서 캡처·비교 — repo 내 쓰기 범위가 `adapters/claude/plugin-marketplace/` 서브트리(+ 이미 진행 중이던 cycle-2 diff)로 한정됨을 실측 확인.

## Phase 1 — 생성기 (`01_generator_plugin_content.sh`, 15/15 PASS)

- syntax: `py_compile sync-native-plugin.py drivers/claude.py` — clean.
- import: 모듈 동적 로드(`main()` 트리거 없이) — `sync`/`check`/`plugin_json`/`marketplace_json`/`hooks_json` 모두 callable.
- smoke: 이미 clean 한 tree 위에서 `--check` exit 0.
- functional:
  - `sync()` 재실행 = git diff 없음(idempotent), 이후 `--check` exit 0.
  - 생성 파일 하나(`skills/audit/SKILL.md`) touch → `--check` exit 1, stale[] 가 정확히 그 파일을 지목.
  - `agents/` 밑에 SoT 에 없는 stray 파일 추가 → `--check` exit 1, stale[] 가 excess-file 로 지목(코드 리뷰 대상이던 "excess-file detection" 로직 실제 확인).
  - `sync()` 재생성 → touch·stray 모두 제거, `--check` exit 0 로 복귀, 최종 `git status` 가 최초 baseline 과 완전히 일치(결정론적 round-trip).
  - write-set confinement: marketplace 서브트리 + 생성기 스크립트 자신을 제외한 나머지 git 상태가 baseline 과 동일 — 생성기가 그 외 어디에도 쓰지 않음.

## Phase 2+3 — driver 배선 + verify checks (`02_driver_plugin_wiring_and_verify.sh`, 24/24 PASS)

- syntax/import: `drivers/claude.py` 정상.
- smoke: `install(plugin=True, dry_run=True)` — plugin action `status=planned`, detail 에 두 CLI 명령 모두 포함, 동시에 symlink/copy_once 프로젝션(10+ actions) 도 같은 결과에 존재(INST-D-5 parity 확인), `blocked=False`. `harness install claude --plugin --dry-run --json` CLI 경로로도 동일 확인(`claude.plugin.x` + 전체 projection plan 동시 출력).
- CLI-absent SKIP: `claude` 바이너리 디렉터리만 제거한 PATH 로 `_plugin_action(dry_run=False)` → `status=skipped`, subprocess 호출 없음; `claude.plugin-registered` check → `ok=True` + SKIP detail(verify 를 CLI 부재 상자에서 절대 fail 시키지 않음 확인).
- `checks()` 구성: 23개 callable, `claude.sync-native-plugin`/`claude.plugin-marketplace-source`/`claude.plugin-registered` 3개 신규 확인(cycle-1 20개 + 3).
- **CLI-gated integration** (로컬 `claude` CLI 존재 — 실제로 실행됨, SKIP 아님):
  - 등록 전: `claude.plugin-registered` → `ok=False`(SKIP 아닌 진짜 미등록 상태를 정직하게 보고).
  - `install(plugin=True, dry_run=False)` → `status=registered`.
  - 직접 `claude plugin marketplace list --json`/`plugin list --json` (mktemp `CLAUDE_CONFIG_DIR`) 로 교차 확인 — `agent-harness` marketplace + `agent-harness-claude@agent-harness` plugin(`enabled=true`) 확인, `installPath` 가 real `~/.claude/plugins` 하위가 아님을 assert.
  - 등록 후: `claude.plugin-registered` → `ok=True`.
  - `harness verify claude --json` (CLI 경유) — 3개 신규 check 모두 `ok=True` 로 노출, exit 0/2 기대 집합 안. verify 호출 직전/직후 `CLAUDE_CONFIG_DIR` 재귀 해시 동일 — verify 가 등록 상태를 mutate 하지 않음(read-only) 확인.

## Phase 4 — `INSTALL_LAYOUT.md` 축소 (`03_install_layout_and_regression.sh`, 14/14 PASS)

- 라인 수: 225 (기준 514 대비 대폭 축소).
- `ln -sfn` 발생 3건만 — Windows 산문 설명 1 + 유지하기로 한 fleet 런처 한 줄 1 + 회고적 산문 언급 1(모두 사전 서술에서 확인된 것과 일치), 런타임별 복사-붙여넣기 레시피 열거 블록은 0.
- `^rg ` 형태의 수동 Migration Order 검증 배터리 라인 0건.
- 계약 사실 보존: `harness install`/`harness verify`/`copy-once`/`INST-OPEN-4`/`install-windows.sh`/`~/.local/bin`/`Exit code` 7개 문구 전부 존재, Claude plugin self-contained + `sync-native-plugin.py` 생성기 결속 사실도 존재.
- `git diff --stat` 로 실제 diff(507 변경, 109 삽입/398 삭제) 확인.

## 회귀 (Phase 5 §6)

전체 사이클 1의 51개 테스트를 통째로 재실행하지는 않음(범위 밖, 사유: 이번 사이클 diff — `drivers/claude.py`, `INSTALL_LAYOUT.md`, 신규 생성기+생성물 — 가 건드리지 않는 표면까지 15분 규모의 통과 스위트를 중복 실행하는 비용 대비 이득이 낮음). 대신 diff 표면을 커버하는 대표 스모크 재확인:

- `py_compile tools/install/*.py tools/install/drivers/*.py adapters/claude/bin/sync-native-plugin.py` — clean.
- `python3 tools/build-manifest.py --check` — `manifest up-to-date`.
- `harness install --dry-run --json` (전체 런타임) — claude/codex/opencode 3종 모두 checks 커버, 예기치 않은 "source absent" skip 없음.
- `harness verify --json` (전체 런타임) — exit 0/2 기대 집합 안, claude 신규 check 3개 포함해 노출.
- `harness install codex --plugin --dry-run --json` — cycle-1 codex 플러그인 채널 회귀 없음(`codex.plugin.x` 여전히 marketplace add + plugin add 계획).

사이클 1 의 durable 51-test suite 원본은 `.agent_reports/plans/2026-07-13_harness-installer-impl/_internal/test_scripts/e2e_lifecycle.sh` 에 그대로 보존.

## 발견된 결함

없음. code-execute 가 dev_logs/step_01~04 에서 이미 정확히 확인한 동작(Phase 1~4)이 durable 스크립트로도 전부 재현·확인됨. 유일하게 스크립트 자체의 최초 assertion 실수(Phase 4 self-contained 사실 검사가 `${CLAUDE_PLUGIN_ROOT}` 리터럴을 과도하게 좁게 요구) 1건을 발견해 스크립트 자체를 수정했다 — 이는 제품 결함이 아니라 테스트 스크립트의 assertion 문구 문제였다.

## 산출물

- `_internal/test_scripts/01_generator_plugin_content.sh`
- `_internal/test_scripts/02_driver_plugin_wiring_and_verify.sh`
- `_internal/test_scripts/03_install_layout_and_regression.sh`
- `test_logs/01_generator_plugin_content.md`
- `test_logs/02_driver_plugin_wiring_and_verify.md`
- `test_logs/03_install_layout_and_regression.md`
- `test_logs/test_report.md` (본 파일)
- `_internal/test_reviews/{02,03}_artifacts/` — 각 스크립트의 raw JSON 산출물(verify/install `--json` 출력 등) 보존
- `plan/checklist.md` Phase 5 전 항목 `[x]` 갱신
