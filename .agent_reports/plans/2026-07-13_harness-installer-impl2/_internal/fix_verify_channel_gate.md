# fix: harness verify — claude.plugin-registered 채널-인지 (2026-07-13)

## 문제
`sh tools/install/harness.sh verify` 가 실 dev 머신에서 `✗ claude.plugin-registered
marketplace 'agent-harness' 미등록` 으로 exit 2. PRD(`.agent_reports/spec/harness-installer/prd.md`
§0.5 원칙 1 — 2-채널 하이브리드는 병존이지 대체가 아님) 상 dev 채널(symlink projection)
머신에서 plugin marketplace 미등록은 정상 상태인데, 기존 check 가 채널을 구분하지 않고
무조건 ✗ 로 판정하는 오탐이었다.

## 수정
`tools/install/drivers/claude.py`
- `_dev_channel_active(scope)` 신설 — `<runtime_home>/CLAUDE.md` symlink 가
  `paths.agent_home()` 안쪽을 가리키면 dev 채널 활성으로 판정하는 단일 함수.
  `checks()`(`claude.plugin-registered`)와 `status()` 가 공유.
- `checks()` 의 `_plugin_registered`: marketplace 미등록 시 `_dev_channel_active()`
  가 True 면 `ok=True` + `detail="SKIP: plugin 채널 미채택 (dev 채널 활성) — ..."`
  (parity-loss warning 원칙 — silent drop 대신 SKIP 명시). marketplace 는 등록됐는데
  plugin 미설치인 경우는 채널 무관하게 여전히 `ok=False` (진짜 drift).
- `status()`: `dev_channel_active` 필드 추가 (같은 판정 함수 재사용).

## 검증

### 1. 컴파일
```
$ python3 -m py_compile tools/install/drivers/claude.py
```
→ 통과 (에러 없음).

### 2. 실 환경 verify (read-only)
```
$ AGENT_HOME=/home/Uihyeop/agent_setting sh tools/install/harness.sh verify
```
- exit code: **0** (수정 전 2)
- `✗` 건수: **0**
- `claude.plugin-registered` 라인: `✓ claude.plugin-registered SKIP: plugin 채널
  미채택 (dev 채널 활성) — marketplace 'agent-harness' 미등록은 정상`

(`AGENT_HOME` 을 실 repo 로 override — worktree 안에서 harness.sh 를 실행하면
`paths.agent_home()` 이 worktree 자신을 repo 루트로 오인해 무관한 symlink-target
불일치가 대량 발생하므로, 실 설치 상태(`~/.claude/*` symlink → `/home/Uihyeop/agent_setting`)와
맞춰 검증했다. 드라이버 코드 자체는 이 worktree 의 수정본이 실행됨 — `sh
<worktree>/tools/install/harness.sh` 로 호출.)

### 3. 회귀 — marketplace 등록됐는데 plugin 미설치는 여전히 ✗
단일 self-contained 스크립트 1회 실행(`CLAUDE_CONFIG_DIR` 를 `mktemp -d` 임시 경로로
격리, `claude plugin marketplace add`만 실행하고 `plugin install` 은 생략) + 시작/종료
`~/.claude/*` symlink target 목록 sha256 assert:

```
marketplace add rc=0
RESULT: {'id': 'claude.plugin-registered', 'ok': False,
  'detail': "plugin 'agent-harness-claude@agent-harness' 미설치 (claude plugin install 필요)"}
REGRESSION TEST PASS: still fails as expected
real home unchanged: sha256 before=6156677a5f23d88191afea8b2b91488a094f1d2bc6e5fb5de7c2cee2d53aa069
                     after =6156677a5f23d88191afea8b2b91488a094f1d2bc6e5fb5de7c2cee2d53aa069
```

추가 확인: `~/.claude/plugins/known_marketplaces.json` (실 config, isolate 안 된 진짜
런타임 홈) 에 `agent-harness` 항목 부재 — 테스트의 `marketplace add` 가 `CLAUDE_CONFIG_DIR`
격리 안에서만 실행되고 실 런타임 홈은 무변경임을 재확인.

## 커밋
- hash: `1b7e2b4` (`tools/install/drivers/claude.py`)
- 브랜치: `harness-installer-fix-verify-gate` (main 머지 안 함)
