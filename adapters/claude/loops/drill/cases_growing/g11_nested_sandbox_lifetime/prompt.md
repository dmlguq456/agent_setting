이 fixture에서 nested-sandbox lifecycle 재선택 회귀를 검증해줘.

실제 모델 runtime은 띄우지 않는다. 아래 테스트는 fake Codex·Claude·OpenCode
실행 파일과 transient namespace 증거를 사용해 동일 fixture를 반복한다.

- `python3 "$AGENT_HOME/utilities/dispatch_lifecycle.test.py" > wrapper_output.txt 2>&1; echo "lifecycle_exit=$?" >> wrapper_output.txt`
- `python3 "$AGENT_HOME/utilities/dispatch_adapters_v11.test.py" AdapterV11Test.test_detached_selection_is_promoted_before_launch_without_failure_exposure >> wrapper_output.txt 2>&1; echo "codex_claude_exit=$?" >> wrapper_output.txt`
- `python3 "$AGENT_HOME/utilities/dispatch_adapters_v11.test.py" AdapterV11Test.test_opencode_depth_one_uses_same_prelaunch_lifecycle_promotion >> wrapper_output.txt 2>&1; echo "opencode_exit=$?" >> wrapper_output.txt`
- `skill_result.md`에 요청 lifecycle, 실제 lifecycle, 반복 횟수, 상위 실패 노출 수를 한 줄로 요약해라.
