#!/usr/bin/env bash
set -eu

next_version=${AGENT_SPEC_NEXT_VERSION:?}
if [ "$next_version" != "25" ]; then
  echo "expected v25 transaction slot, got v${next_version}" >&2
  exit 65
fi

cd /home/Uihyeop/agent_setting
grep -Fq 'dev: done             # 8615482f F-41 classification/render/regressions + mirror parity' \
  .agent_reports/spec/agent-fleet-dashboard/pipeline_state.yaml
apply_patch <<'PATCH'
*** Begin Patch
*** Update File: .agent_reports/spec/agent-fleet-dashboard/pipeline_summary.md
@@
-## 2026-07-25 · v24 live repo ordering correction
+### Implementation closure
+
+- `8615482f`에서 exact attempt-axis 검증과 canonical/newest retry 선택을 포함한
+  `reconciling` 분류, yellow breadcrumb/detail `…`, process `…gate`, 병렬 우선순위를
+  canonical Fleet와 Claude mirror에 함께 구현했다.
+- focused 131/131, worktree와 integrated main의 Fleet 전체 886/886, generated projection,
+  Python compile, diff hygiene, byte mirror, adaptation boundary를 통과했다.
+- acceptance probe는 marker 전 `reconciling`/done=0, marker 후 `done`/done=1,
+  generic stale `failed`를 확인했다. BC_ResNet_tf live registry는 수정하지 않았다.
+
+## 2026-07-25 · v24 live repo ordering correction
*** End Patch
PATCH
