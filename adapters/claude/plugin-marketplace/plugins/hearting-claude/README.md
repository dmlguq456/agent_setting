sync-native 생성기 산출 자리 — 손 편집 금지. SoT 는 `capabilities/`·`roles/`·core;
내용물(skills/agents/hooks/.mcp.json/bin)은 빌드 시점에 `adapters/claude/bin/sync-native-*.py`
가 이 디렉토리 아래 물리 포함시킨다 (Claude plugin cache 는 `../` 상위 참조를 차단하는
self-contained 모델이라 — PRD `.agent_reports/spec/harness-installer/prd.md` "설치본은
self-contained" 절 참조). 구현은 autopilot-code 사이클 몫.
