# Dispatch decision — inline execution

`STAGE_DISPATCH_INLINE_OK` (OPERATIONS §5.10 self-modification carve-out).

이 사이클은 dispatch 인프라 자체(`utilities/capability-route.py`,
`capabilities/topologies.json` — enforced route compiler와 그 registry)를
수정한다. registry digest가 사이클 중간에 바뀌면 in-flight route seal이
전부 무효화되므로(`verify_route`의 stale registry digest 거부), 스테이지를
registry-digest에 봉인된 headless worker로 분사하는 것 자체가 수정 대상과
경합한다. 근거 기록 위치: 본 파일. 진입 HEAD: ec5b1ebe.
