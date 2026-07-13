# Invocation contract closure implementation

## Outcome

- `core/CONVENTIONS.md`와 `core/DESIGN_PRINCIPLES.md`의 잘못된 “pure sub-skill은 disable” 규범을 runtime 호출 그래프 기준으로 교체했다.
- `tools/skill-conformance/invocation-policy.tsv`가 parent-invoked 13개를 명시하고, `check.sh`가 양 Claude skill 트리의 구조·frontmatter를 결정론적으로 검사한다.
- g7은 live tree PASS만 보는 데 그치지 않고 parent flip과 user-only missing flag를 각각 거부하고, 올바른 user-only flag는 허용하는 failure control을 포함한다.
- sync-skills 안내, drill 문서, Claude native plugin projection을 함께 동기화했다.
- plugin generator는 invocation 변경분과 함께 main에 남아 있던 3개 stale generated projection(editorial-team, autopilot-code reference, autopilot-ship)을 source와 동일하게 catch-up했다. source 계약은 변경하지 않았다.
- 활성 PRD·pipeline state를 v3 runtime 계약으로 갱신해 과거 “13개 flip” 지시가 현재 실행 계약으로 읽히지 않게 했다.

## Boundary decision

core 분류와 g7 assertion은 같은 invocation semantic anchor라 분리 실행 시 중간 상태가 거짓 PASS/FAIL을 만든다. 따라서 metrics에 non-separable 근거를 기록하고 한 브랜치에서 결합 구현했다.
