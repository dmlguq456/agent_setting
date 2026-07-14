# Test report — README product surface

> 2026-07-13 · mode `qa/test` · verification contract `verification-runner`

## Verdict

PASS. 요청된 source/projection/installer 검사와 전체 portable guard 회귀군이 모두 통과했다.

## Level 1 — syntax

- PASS: 변경 Python 4개를 `ast.parse`로 검사.
- 대상: Claude/fleet dispatch tests, `tools/build-manifest.py`, fleet dispatch tests, Claude installer driver.

## Level 2 — import

- PASS: 변경 Python 모듈 import.
- `tools/install/drivers/claude.py`는 installer의 정상 import context와 동일하게 `PYTHONPATH=tools/install`을 적용했다. 최초 무설정 import의 `ModuleNotFoundError: paths`는 호출 context 오류로 재분류했다.

## Level 3 — README surface smoke

- PASS: 상대 Markdown 링크 16개가 모두 로컬 파일을 가리킨다.
- PASS: 요구된 heading 순서(value 이후 install → examples → benefits → runtime → architecture → docs → verification)를 확인했다.
- PASS: `harness --help`, `install --help`, `verify --help`가 README 명령을 수용한다.
- PASS: `install all --dry-run`, Claude/Codex `--plugin --dry-run`이 성공했다.
- PASS: current source active-reference census 0건. `.agent_reports/**`, `.claude_reports/**`, `.dispatch/**`, `.git/**`는 제외했다.
- PASS: 퇴역 경로와 manifest의 `sync-skills` 항목이 모두 부재한다.

## Level 4 — deterministic functional checks

모든 명령은 `adapters/codex/bin/preflight.sh verification-runner`를 통해 실행했다.

- PASS: `python3 tools/build-manifest.py --check`
- PASS: `adapters/claude/bin/sync-native-plugin.py --check`
- PASS: Codex `sync-native-{skills,plugin,agents,modes}.py --check`
- PASS: OpenCode `sync-native-{skills,commands,agents}.py --check`
- PASS: `tools/check-adaptation-boundary.sh` (portable 영역의 허용된 runtime reference 56건 warning만 존재)
- PASS: `tools/skill-conformance/check.sh` (26 classifications)
- PASS: `adapters/codex/bin/preflight.sh doctor`
- PASS: `hooks/portable-guards.test.sh` (343 checks)
- PASS: root/Claude fleet dispatch test suites (58 tests each)
- PASS: portable/Claude fleet fixture parity와 portable/Claude skill tree parity
- PASS: `git diff --check`

첫 병렬 실행에서는 같은 runtime projection fixture를 동시에 검사하며 2개 항목이 일시 실패했다. 테스트를 단독 재실행해 `PASS=343 FAIL=0`으로 닫았으며 최종 판정은 이 결과를 사용한다.

## Level 5 — installer integration and behavioral CLI observation

- PASS: `/tmp/agent-harness-readme-install` 격리 HOME에서 `harness install all --yes --json` 후 `harness verify --json` exit 0.
- PASS: Claude/Codex/OpenCode symlink, manifest, native projection, bootstrap smoke를 실제 verifier가 확인했다.
- PASS: 현재 Codex home을 worktree projection(27 skills, 9 agents)으로 연결한 뒤 `doctor --runtime` exit 0.
- ENVIRONMENT NOTE: Claude/OpenCode 사용자 홈은 기존 `/home/Uihyeop/agent_setting` checkout을 가리킨다. worktree source 검증에는 격리 HOME을 사용했으며, 임시 Codex projection은 최종 handoff에서 main checkout으로 복원한다.

## Unsupported/downgraded contracts

- 독립 depth-2 planner/verifier dispatch는 등록 후 Codex app-server가 read-only filesystem으로 초기화되지 않아 실행 불가. QA는 adapter가 선언한 `manual-main-session` fallback으로 수행했으며 독립 QA를 주장하지 않는다.
- Codex `apply_patch` target detector가 qualified target을 인식하지 못한 경우 explicit preflight 후 shell `apply_patch` fallback을 사용했다.
