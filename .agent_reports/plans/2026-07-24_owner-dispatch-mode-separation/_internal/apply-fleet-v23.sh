#!/usr/bin/env bash
set -euo pipefail

spec_root=${AGENT_SPEC_ROOT:?}
test "${AGENT_SPEC_LOCK_HELD:-}" = 1
test "${AGENT_SPEC_NEXT_VERSION:-}" = 22
snapshot="$spec_root/_internal/versions/v22"
test ! -e "$snapshot"
mkdir -p "$snapshot"
cp "$spec_root/prd.md" "$snapshot/prd.md"
cp "$spec_root/pipeline_state.yaml" "$snapshot/pipeline_state.yaml"
cp "$spec_root/pipeline_summary.md" "$snapshot/pipeline_summary.md"
cd "$spec_root"
apply_patch <<'PATCH'
*** Begin Patch
*** Update File: prd.md
@@
 > · **v22 hotfix 2026-07-23** (분사 attempt-owned Claude stream의 Agent lifecycle을 dispatch 행에 직접 연결하고 exact child-session association을 fallback으로 사용; dispatch context는 계속 미수집·미표시)
+> · **v23 hotfix 2026-07-24** (dispatch mode-axis projection — capability mode와 worker mode/unit 분리, owner stage-persona 표시·bootstrap 오염 차단, F-40)
@@
-## 5. 능동 변경 — fleet-owned local state write
+## 4.13 [v23 신설] dispatch mode-axis projection — F-40
+
+- **F-40a (수집)**: current jobs/env의 `capability_mode`와 `worker_mode`를 별도
+  필드로 손실 없이 보존한다. `worker_mode`는 non-owner unit projection이고 unit을
+  대체하지 않는다. legacy `mode`는 read-only compatibility field로 유지한다.
+- **F-40b (owner 표시)**: depth-1 owner options에는 capability mode만 행동 knob로
+  표시한다. owner의 legacy slash mode는 capability mode로 승격하지 않고
+  `mode-axis-conflict` ambiguity로 남겨 plan/dev/qa persona가 owner 정체성처럼
+  보이지 않게 한다.
+- **F-40c (stage 표시)**: depth-2는 assigned contract/route node를 주 라벨, unit을
+  보조 라벨로 유지한다. worker mode는 JSON/evidence에는 남기되 capability knob나
+  중복 persona 라벨로 렌더하지 않는다. route의 top-level capability mode는 route
+  카드에서만 표시한다.
+- **F-40d (호환)**: 구 `mode=` row는 원문을 보존하고 worker type/unit/route 증거가
+  없을 때만 기존 표시 fallback에 사용한다. 새 분리 필드와 충돌하면 exact 필드가
+  우선하며 ambiguity를 숨기지 않는다. canonical Fleet와 Claude mirror는 byte parity다.
+
+**acceptance**: owner current row는 `dev`만 표시하고 `plan/plan-author` 0회, plan
+depth-2 row는 `capability_mode=dev`, `worker_mode=unit=plan/plan-author`를 JSON에 별도
+보존하며 중복 knob 0회, legacy owner slash mode는 conflict로 분류, old scalar rows와
+public JSON consumer 회귀 0, mirror parity 통과.
+
+## 5. 능동 변경 — fleet-owned local state write
@@
 - **F-39 lock**: title/NOW worker는 default concurrency 3(max 4), rolling 4 starts/60s(max 4), main/child debounce 600/150s다. 공유 lease/kill switch/no-live-provider tests와 shell-free pluggable no-tools provider 경계를 유지하고 vendor를 hard-pin하지 않는다.
+
+## 확정 결정 (v23 승격, 2026-07-24 — dispatch mode-axis projection)
+
+- **F-40 lock**: current writer의 `capability_mode`, `worker_mode`, `unit`을 별도
+  보존한다. owner는 capability mode만 렌더하며 slash-shaped legacy owner mode를
+  capability mode로 표시하지 않는다. depth-2 worker mode는 unit/contract 라벨과
+  중복 렌더하지 않고 JSON evidence로만 보존한다.
*** Update File: pipeline_state.yaml
@@
-  spec: done            # PRD v22: attempt-owned dispatch subagents; no dispatch context
+  spec: done            # PRD v23: dispatch capability/worker mode-axis projection
@@
-  dev: done             # v22 scope: subagents linked to dispatch job; context still absent
-last_updated: 2026-07-23
+  dev: in_progress      # F-40 collector/model/render + mirror parity
+last_updated: 2026-07-24
+spec_version: v23
+decisions_locked:
+  - 'F-40(v23): capability_mode, worker_mode, unit은 독립 필드다. owner는 capability mode만 표시하고 legacy slash mode는 conflict이며, depth-2 worker mode는 JSON evidence로 보존하되 contract/unit과 중복 렌더하지 않는다'
*** Update File: pipeline_summary.md
@@
 # agent-fleet-dashboard — Spec Pipeline Summary
+
+## 2026-07-24 · v23 mode-axis projection
+
+Fleet가 current jobs/env의 `capability_mode`와 `worker_mode`를 분리 수집한다.
+owner는 capability mode만 표시하고 legacy slash mode를 owner 행동으로 승격하지
+않는다. depth-2 worker mode는 exact unit과 함께 JSON evidence로 보존하되 기존
+contract/unit 라벨과 중복 표시하지 않는다.
+
*** End Patch
PATCH
grep -Fq '**v23 hotfix 2026-07-24**' prd.md
grep -Fq 'spec_version: v23' pipeline_state.yaml
grep -Fq '## 2026-07-24 · v23' pipeline_summary.md
