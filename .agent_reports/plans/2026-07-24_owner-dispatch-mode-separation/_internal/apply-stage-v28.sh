#!/usr/bin/env bash
set -euo pipefail

spec_root=${AGENT_SPEC_ROOT:?}
test "${AGENT_SPEC_LOCK_HELD:-}" = 1
test "${AGENT_SPEC_NEXT_VERSION:-}" = 27
snapshot="$spec_root/_internal/versions/v27"
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
 > · **v27 2026-07-24** (completion-delivery 범위별 parent park — interactive registry-open 보호와 supervised/poll successor-readiness 분리, terminal-unverifiable 전역 교착 복구, SD-83)
+> · **v28 2026-07-24** (owner dispatch mode-axis 분리 — capability mode와 depth-2 worker unit/persona의 독립 필드·owner 모순 조합 fail-closed, SD-84)
@@
-## 14. 의미↔규칙 경계 체크 (DESIGN_PRINCIPLES §0.7)
+## 13.18 v28 — owner dispatch mode-axis separation (2026-07-24)
+
+### 13.18.1 SD-84 — capability mode와 worker specialization의 완전 분리
+
+**근거**: `autopilot-code/dev` depth-1 owner를 시작할 때 adapter `--mode`는
+`<family>/<mode>`만 허용해 scalar `dev`를 거부했다. 반대로
+`worker_type=owner`, `unit=_kernel/owner`와 모순되는 `plan/plan-author`는 통과했고,
+그 값이 registry, Fleet, generated assignment, native-mode bootstrap 문구에 주입됐다.
+이는 표시 오류가 아니라 owner에게 depth-2 persona가 섞이는 실행 계약 결함이다.
+
+- `capability_mode`는 entry capability의 의미 모드이며 capability catalog가 허용값을
+  소유한다. 모든 current writer는 `--capability-mode`와 jobs/env
+  `capability_mode`를 명시하고 sealed route top-level 값과 exact 일치시킨다.
+- `worker_mode`는 adapter의 non-owner specialization 호환 필드다. route-bound
+  stage/review worker에서는 non-reserved `nodes[].unit`에서 파생하며 다른 값은
+  prompt/row/spawn 전에 거부한다. portable bootstrap의 실제 persona 입력은 unit이다.
+- depth-1 owner tuple은 `worker_type=owner`, `unit=_kernel/owner`,
+  `assigned_contract=capability`, `worker_mode=absent`다. owner와 `plan/*`, `dev/*`,
+  `qa/*` 등의 worker mode 조합, owner가 아닌 unit, capability-mode catalog 불일치,
+  route capability-mode/unit 불일치는 모두 fail-closed한다.
+- legacy `--mode`는 scalar면 capability mode, slash 값이면 worker mode로만
+  결정론적으로 해석한다. canonical field와 동시 입력은 ambiguous로 거부하고 새
+  writer는 legacy jobs `mode=`를 생성하지 않는다. 구 jobs row는 read-only로 보존한다.
+- `dispatch-node`와 `dispatch-chain`은 model role에서 mode를 추측하지 않는다. route의
+  `capability_mode`와 exact node `unit`만 wrapper에 전달한다. reserved kernel unit은
+  worker mode를 만들지 않는다.
+
+**acceptance**: ① owner `autopilot-code/dev + _kernel/owner`는 worker mode 없이 통과
+② 같은 owner + `plan/plan-author`는 세 adapter 모두 child row/prompt 0으로 거부
+③ plan depth-2는 capability mode `dev`와 worker mode/unit `plan/plan-author`를 별도
+보존 ④ capability catalog 및 route tuple mismatch 거부 ⑤ legacy scalar owner mode는
+capability mode로만 해석하고 slash owner mode는 거부 ⑥ generated prompt는 owner에게
+native stage mode path를 지시하지 않음 ⑦ jobs/env/Fleet 축 분리와 구 row tolerant read
+⑧ route/fallback/wrapper/projection/boundary 회귀 0.
+
+## 14. 의미↔규칙 경계 체크 (DESIGN_PRINCIPLES §0.7)
@@
 - **v27 경계 정련**: `supervised|poll-fallback` strict completion park와 ordinary interactive registry-open park의 후보 상태 집합, exact parent/latest-attempt 선택, bypass의 explicit opt-in은 결정론 fixture 대상이다. terminal row를 ordinary global park에서 제외해도 successor/join/wait/fallback/cleanup의 quiescence 판정은 약화하지 않으며, terminal-unverifiable을 dead로 재분류하거나 registry를 수동 수정하는 것은 금지한다.
+- **v28 축 정련**: capability-mode catalog membership, owner reserved unit/worker-mode 부재, non-owner unit↔worker-mode 일치, route tuple equality, legacy mode shape 분류는 결정론 validator 대상이다. capability mode의 의미 선택은 route owner가 하지만 worker persona 칸에 대체값을 넣어 validator를 우회할 수 없다.
*** Update File: pipeline_state.yaml
@@
-version: 27
+version: 28
@@
-  spec: done              # PRD v27 — SD-83 completion-delivery-scoped parent park; v25/v26 누락 snapshot을 transaction에서 복구
+  spec: done              # PRD v28 — SD-84 owner dispatch mode-axis separation
@@
 decisions_locked:
+  - 'SD-84(v28): capability_mode는 entry capability catalog/route 축, worker_mode는 non-owner unit의 호환 projection이다. owner는 _kernel/owner + assigned_contract=capability + worker_mode absent이며 stage mode 우회는 prompt/row/spawn 전에 거부한다. 새 writer는 legacy mode=를 쓰지 않는다'
*** Update File: pipeline_summary.md
@@
 # stage-dispatch — Spec Pipeline Summary
+
+## v28 update (2026-07-24) — owner mode-axis separation
+
+`capability_mode`와 depth-2 worker unit/persona를 분리한다. owner는
+`_kernel/owner`와 capability contract만 받고 worker mode를 받지 않는다. route-bound
+worker mode는 exact non-reserved unit에서 파생하며 model role 기반 mode 추측과
+legacy `mode=` 신규 기록을 폐기한다. owner+stage-mode, catalog mismatch, route/unit
+mismatch는 prompt·registry·spawn 전에 fail-closed한다.
+
*** End Patch
PATCH
grep -Fq '**v28 2026-07-24**' prd.md
grep -Fq 'SD-84(v28)' pipeline_state.yaml
grep -Fq '## v28 update' pipeline_summary.md
