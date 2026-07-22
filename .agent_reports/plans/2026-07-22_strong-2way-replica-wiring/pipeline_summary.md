# Pipeline summary — strong+ 2-way replica wiring

- **결과**: 완료. strong 이상 intensity가 2-way cross-harness replicate-and-merge
  그래프로 컴파일되도록 3개 층(registry·compiler·skills) 배선.
- **근본 원인**: 9b4e81b2(7/21)가 core 문서만 갱신하고 실행 표면 미배선;
  C6(63f521c8)이 복제 없는 컴파일 route를 skill 문서의 정본으로 고착.
- **변경**:
  - `capabilities/topologies.json`: 10개 recipe에 `standard_plus.replication`
    선언 (autopilot-note 제외 — review-worker 부재 carve-out).
  - `tools/capability_topology.py`: replication 블록 fail-closed 검증.
  - `utilities/capability-route.py`: `_expand_replication` — strong+에서 대상
    리뷰 노드를 `<id>-replica`로 복제(출력 `name.replica.ext`, 하류 depends_on
    확장, replica_group/independence_axis 부여), composed 검증에도 동일 적용.
  - skills(autopilot-code owner-execution·arguments-and-decisions·dev-pipeline)
    + `capabilities/autopilot-code.md`: strong 정의를 계약과 정합화, conductor
    verdict-merge(stricter-wins·blocking 합집합·독립성 저하 보고) 명문화.
  - `spec/stage-dispatch/prd.md`: v21/SD-76 사후 spec-sync.
  - 투영 재생성: Claude 미러 + plugin-marketplace + manifest/hub.
- **검증**: `test_logs/test_report.md` — 신규 5개 테스트 셀 포함 전 스위트 green.
- **잔여**:
  - `codex-headless-context-parity` plan 실행은 별도 소유·별도 사용자 확인 대기
    (본 사이클 범위 외 유지).
  - autopilot-note에 독립 리뷰 스테이지를 신설할지는 별도 결정 필요(현재는
    정직한 carve-out).
  - 실전 strong 사이클 1회 완주로 conductor merge 동작 실증(다음 strong 작업에서
    자연 검증됨 — replica leg는 route에 이미 존재).
- **dispatch 결정**: inline (`_internal/metrics.md`, STAGE_DISPATCH_INLINE_OK —
  dispatch 인프라 자기수정: registry digest 변경이 in-flight route seal과 경합).
