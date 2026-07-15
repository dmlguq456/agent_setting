# 검증 기록

- `hooks/mem-turn-nudge.test.sh`: PASS=18, FAIL=0.
- `hooks/mem-distill-dispatch.test.sh`: PASS=46, FAIL=0. 12-session wave의
  동시 실행 최대 2 및 rolling start budget/kill switch를 stub으로 검증했다.
- Fleet 집중 테스트: 149 tests OK (`test_f18_attribution` 31,
  title/dispatch 118). live model provider는 호출하지 않았다.
- Python compile, JSON parse, bash/sh syntax, OpenCode plugin parse,
  `git diff --check`: exit 0.
- `python3 tools/generate.py --check`: 10 projection groups OK; delta baseline bound.
- `tools/check-adaptation-boundary.sh`: OK (portable area의 허용된 compatibility
  reference 경고 51건만 존재).
- `preflight.sh runtime-projection --require-hook-trust`: Codex projection 및 hook
  trust OK. Claude physical distill hook은 adapter와 sha256 일치하고 runtime
  settings의 두 memory lifecycle 명령에 모든 worker gate가 존재한다.
- 외부 worklog-board: `tsc --noEmit`, cron syntax, routing manual test 모두 통과.
- OpenCode runtime projection: 실제 plural `agents/commands/skills` 설치와 임시
  legacy singular fixture 모두 `headless --check` 통과.
- 전체 `portable-guards.test.sh`는 00:45경 서버의 비정상 재부팅으로 중단됐다.
  원인 증거가 없어 재실행하지 않았고, 변경 표면은 위의 집중 테스트와 정적
  adapter boundary 검사로 대체 검증했다.
