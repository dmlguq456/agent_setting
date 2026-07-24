#!/usr/bin/env bash
set -euo pipefail

spec_root=${AGENT_SPEC_ROOT:?}
test "${AGENT_SPEC_LOCK_HELD:-}" = 1
test "${AGENT_SPEC_NEXT_VERSION:-}" = 2
snapshot="$spec_root/_internal/versions/v2"
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
-# Dispatch Profiles — PRD v2
+# Dispatch Profiles — PRD v3
@@
-> 2026-07-16 · typed worker-bootstrap amendment. v1의 원 설계·실측·CLI
-> 근거는 `_internal/versions/v1/prd.md`에 보존한다.
+> 2026-07-24 · owner mode-axis amendment. v2 typed bootstrap과 v1 원 설계·실측·CLI
+> 근거는 `_internal/versions/`에 보존한다.
@@
 - **DP-17:** detailed output is artifact-only; registered worker return uses the
   portable three-line envelope.
+- **DP-18:** capability mode is an entry-contract field. Worker specialization is
+  a separate non-owner field derived from the selected portable unit; it never
+  selects the worker type or assigned contract.
+- **DP-19:** an owner bootstrap is kernel + owner type + capability contract with
+  reserved unit `_kernel/owner` and no worker specialization. A plan/dev/qa unit
+  must never be loaded into an owner prompt.
+
+## 5.1 v3 bootstrap tuple
+
+The dispatcher validates the typed tuple before materializing a prompt or registry
+row. `capability_mode` must belong to the assigned entry capability. `worker_mode`
+is absent for owners and, for route-bound non-owners, equals the exact non-reserved
+`unit`. Legacy `mode` is only a shape-classified compatibility input and cannot
+override either canonical field. Registry and environment projections preserve the
+two axes separately.
+
+Negative fixtures cover owner+stage-mode, owner+non-owner-unit,
+capability-mode catalog mismatch, route capability-mode mismatch, and
+worker-mode/unit mismatch across all three adapters. Each failure produces no
+prompt, row, or child process.
*** Update File: pipeline_state.yaml
@@
-spec_version: v2
+spec_version: v3
@@
 decisions_locked:
+  - 'DP-19: owner bootstrap = kernel + owner type + capability contract + _kernel/owner, worker specialization absent; stage/dev/qa persona injection is invalid'
+  - 'DP-18: capability_mode and non-owner worker_mode/unit are independent registry, environment, and prompt axes'
*** Update File: pipeline_summary.md
@@
 # dispatch-profiles — pipeline summary
+
+## 2026-07-24 · v3 mode-axis amendment
+
+typed bootstrap tuple에 `capability_mode`와 non-owner `worker_mode/unit`의
+독립성을 추가했다. owner는 `_kernel/owner`와 capability contract만 받고 stage
+persona를 받지 않는다. 모순 tuple은 prompt, registry row, child process를 만들기
+전에 세 adapter가 동일하게 거부한다.
+
*** End Patch
PATCH
grep -Fq '# Dispatch Profiles — PRD v3' prd.md
grep -Fq 'spec_version: v3' pipeline_state.yaml
grep -Fq '## 2026-07-24 · v3' pipeline_summary.md
