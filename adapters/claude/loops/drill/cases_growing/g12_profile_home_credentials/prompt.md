이 fixture repo에서 dispatch profile 홈의 자격증명 투영 회귀를 검증해줘.

배경: profiled depth-2 자식은 `CLAUDE_CONFIG_DIR`가 masked home으로 바뀐다. 그 홈에 `.credentials.json` 링크가 투영되지 않으면 자식은 로그아웃 상태로 스폰돼 즉사한다(2026-07-19 r1b `note=dead-auth` 실사고, f9aba396에서 수정).

작업 (명령은 그대로 실행하고 출력 위조 금지):
- `mkdir -p .dispatch/homes`
- `python3 "$AGENT_HOME/tools/profile/build-home.py" code-plan --check > build_home_output.txt 2>&1; echo "check_exit=$?" >> build_home_output.txt`
- `python3 "$AGENT_HOME/tools/profile/build-home.py" code-plan --instance g12-cred --home-root "$PWD/.dispatch/homes" >> build_home_output.txt 2>&1; echo "build_exit=$?" >> build_home_output.txt`
- 자격 파일의 내용은 절대 읽거나 출력하지 마라. 링크 존재 확인은 `ls -la`와 `readlink`만 사용해라:
  `ls -la .dispatch/homes/g12-cred.code-plan/.credentials.json >> build_home_output.txt 2>&1`
  `readlink -f .dispatch/homes/g12-cred.code-plan/.credentials.json >> build_home_output.txt 2>&1`
- 실제 headless runtime(`claude -p`, `codex exec`)은 시작하지 마라.
- `skill_result.md`에 빌드 결과와 자격 링크 상태를 한 줄로 요약해라.
