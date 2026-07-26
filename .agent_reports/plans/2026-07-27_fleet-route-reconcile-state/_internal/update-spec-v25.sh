#!/usr/bin/env bash
set -eu

spec_root=${AGENT_SPEC_ROOT:?}
next_version=${AGENT_SPEC_NEXT_VERSION:?}
if [ "$next_version" != "24" ]; then
  echo "expected v24 snapshot slot, got v${next_version}" >&2
  exit 65
fi

snapshot_dir="$spec_root/_internal/versions/v${next_version}"
mkdir -p "$snapshot_dir"
cp "$spec_root/prd.md" "$snapshot_dir/prd.md"

cd /home/Uihyeop/agent_setting
apply_patch <<'PATCH'
*** Begin Patch
*** Update File: .agent_reports/spec/agent-fleet-dashboard/prd.md
@@
 > · **v24 correction 2026-07-25** (live TUI repo 그룹 정렬 — 현재 activity tier를 매 tick 우선 적용하고, 빠른 위치 교환 방지는 같은 tier 안의 survivor anchor에만 적용)
+> · **v25 correction 2026-07-27** (route completion reconciliation — exact terminal 관측 뒤 completion marker를 기다리는 노드를 실패 `✕`와 분리해 `reconciling`/`…`로 표시, gate·progress는 계속 미완료)
@@
-  - **카드 구성**: L1 = `[capability·mode·intensity] <route_id 단축> — <n/m nodes> ⏳<경과>`; L2 = DAG 가로 흐름 `plan ✓12m › exec ● 8m (opus·high) › test ○ › report ○` — 노드별 상태 글리프(✓ 완료 / ● 활성+경과+모델 / ○ 미기동 / ✕ 실패)와 completion gate 통과 여부. `depends_on`이 병렬인 노드는 세로 분기(들여쓴 병렬 행)로.
+  - **카드 구성**: L1 = `[capability·mode·intensity] <route_id 단축> — <n/m nodes> ⏳<경과>`; L2 = DAG 가로 흐름 `plan ✓12m › exec ● 8m (opus·high) › test ○ › report ○` — 노드별 상태 글리프(✓ 완료 / ● 활성+경과+모델 / ○ 미기동 / `…` completion-marker 조정 대기 / ✕ 실패)와 completion gate 통과 여부. `depends_on`이 병렬인 노드는 세로 분기(들여쓴 병렬 행)로.
@@
 **acceptance**: owner current row는 `dev`만 표시하고 `plan/plan-author` 0회, plan
 depth-2 row는 `capability_mode=dev`, `worker_mode=unit=plan/plan-author`를 JSON에 별도
 보존하며 중복 knob 0회, legacy owner slash mode는 conflict로 분류, old scalar rows와
 public JSON consumer 회귀 0, mirror parity 통과.
+
+## 4.14 [v25 신설] route completion reconciliation projection — F-41
+
+- **F-41a (판정 경계)**: open attempt의 Fleet liveness가 `stale`이더라도
+  `state_evidence.attempt`가 단일 classifier의 exact
+  `shared-observer` 판정이고 그 `observed_liveness.state`가
+  `reconcile-needed`이면 route node는 `failed`가 아니라 `reconciling`이다. 단순
+  stale/dead, pid 종료, killed/cancelled, fail-note는 계속 `failed`다. 문자열 note나
+  top-level stage 이름만으로 이 상태를 합성하지 않는다.
+- **F-41b (완료·gate 독립)**: `reconciling`은 terminal output 관측과 completion marker
+  사이의 중간 상태다. `done` progress에 포함하지 않고 `gate_passed`를 만들지 않으며
+  successor도 열지 않는다. 유효 marker가 생기면 기존 marker 우선순위로 `done`이
+  되고, marker 없이 실제 실패 증거가 우세하면 `failed`다.
+- **F-41c (표시)**: breadcrumb와 stage detail은 yellow `…`, process L2는
+  `…gate`로 표시한다. `✕`·적색 failed alert·실패 자동 펼침은 실제 실패에만 쓴다.
+  public route JSON은 node `state=reconciling`을 그대로 노출하고 completion/gate
+  필드는 기존 의미를 유지한다.
+- **F-41d (병렬 집계)**: 병렬 그룹 상태 우선순위는
+  `failed > active > reconciling > done/pending fallback`이다. 한 leg가 조정 대기라는
+  이유만으로 그룹을 실패로 만들지 않되, 다른 leg의 실제 실패를 숨기지 않는다.
+
+**acceptance**: BC_ResNet_tf에서 관찰된 exact
+`terminal-observed/reconcile-needed` shape는 marker 전 `reconciling`+`…`+progress
+미증가, marker 후 `done`으로 전이한다. 동일 `stale`이라도 exact reconciliation
+증거가 없는 fixture는 `failed`+`✕`를 유지한다. group/process 및 wide/narrow/stack,
+parallel collapse, public JSON, canonical↔Claude mirror가 같은 상태를 보존한다.
@@
 ## 확정 결정 (v23 승격, 2026-07-24 — dispatch mode-axis projection)
@@
   중복 렌더하지 않고 JSON evidence로만 보존한다.
+
+## 확정 결정 (v25 승격, 2026-07-27 — route completion reconciliation)
+
+- **F-41 lock**: exact shared-observer `reconcile-needed`만 route node
+  `reconciling`으로 투영하고 yellow `…`/`…gate`로 표시한다. 이 상태는 완료·gate
+  통과·successor 개방을 주장하지 않으며 generic stale/dead 실패는 계속 `✕`다.

-## Next — current v16 implementation handoff (`autopilot-code`)
-
-1. `projection.py`와 additive model/JSON을 추가하고, exact route/registry evidence → ambiguity refusal → route-부재 단일 artifact stage 순서의 `WorkProjection` resolver를 구현한다.
-2. sealed arbitrary DAG의 opaque node/unit/gate/scope, parallel sibling, fan-in을 group/process/plain/JSON에 공통 투영한다.
-3. wide의 `harness | session (branch) | stages | time` 4칼럼, 각 경계 +1 cell, 빈 stage `-`와 narrow/stack의 동일 branch·stage placeholder 문법을 구현한다. interactive identity 아래에는 session 열에 맞춘 콜론 없는 `context <gauge> …[   NOW]` row를 둔다. dispatch는 context 없이 NOW만 같은 열에 두며 title/NOW만 단일 child association으로 공급한다. dim 퍼센트, 현행 TITLE 3~6단어·최대 40자 및 F-39의 3/4 concurrency·4 starts/60s·600/150s 계약은 유지한다.
-4. §4.12 acceptance matrix, canonical↔Claude mirror parity, public JSON compatibility를 hermetic fixture/fake clock으로 검증한다. default/custom live provider 호출과 실세션 spawn/signal은 금지한다.
-
-권장 진입: `/autopilot-code --mode dev --intensity strong "agent-fleet-dashboard PRD v16 F-36~F-39 구현 및 §4.12 검증"`. v6/v8/v9/v10 및 v2의 이전 구현 순서는 위 version history와 pipeline summary에 보존된 **완료·대체된 역사**이며 현재 실행 지시가 아니다.
+## Next — current v25 implementation handoff (`autopilot-code`)
+
+1. `route.py`가 exact shared-observer reconciliation evidence만 `reconciling`으로
+   분류하고 marker/generic-failure 우선순위를 보존한다.
+2. `render.py`의 breadcrumb, DAG detail, process L2, parallel collapse에 yellow
+   `…`/`…gate`를 적용한다.
+3. exact positive/negative fixture, marker 전이, 병렬 집계, JSON 및 mirror parity를
+   hermetic regression으로 고정한다. live registry 변이는 금지한다.
*** Update File: .agent_reports/spec/agent-fleet-dashboard/pipeline_state.yaml
@@
-  spec: done            # PRD v24: live repo ordering activity-tier correction
+  spec: done            # PRD v25: route completion reconciliation projection
@@
-  dev: done             # 6b1befe4 activity-tier group anchor + regression + mirror parity
-last_updated: 2026-07-25
-spec_version: v24
+  dev: pending          # F-41 route classification/render/tests implementation pending
+last_updated: 2026-07-27
+spec_version: v25
 decisions_locked:
+  - 'F-41(v25): exact shared-observer reconcile-needed는 route node reconciling/…로 표시하며 marker 전에는 done·gate·successor를 주장하지 않고 generic stale/dead는 계속 failed/✕다'
*** Update File: .agent_reports/spec/agent-fleet-dashboard/pipeline_summary.md
@@
 # agent-fleet-dashboard — Spec Pipeline Summary

+## 2026-07-27 · v25 route completion reconciliation
+
+BC_ResNet_tf의 frame depth-2 workers가 terminal output을 남긴 뒤 owner의 exact
+completion marker를 기다리는 짧은 구간에서 Fleet가 route node를 실패 `✕`로
+표시하는 오해를 바로잡는다.
+
+- exact shared-observer `reconcile-needed`만 새 route state `reconciling`으로 투영한다.
+- marker 전에는 progress·gate·successor를 움직이지 않고, generic stale/dead/killed는
+  계속 실제 실패로 유지한다.
+- group/process 표시는 yellow `…`(process L2 `…gate`)를 사용하며 병렬 그룹의 실제
+  실패가 있으면 실패가 계속 우선한다.
+- 구현은 `plans/2026-07-27_fleet-route-reconcile-state/`에서 진행하며 live registry를
+  변이하지 않는 hermetic fixture와 canonical/Claude mirror parity로 검증한다.
+
 ## 2026-07-25 · v24 live repo ordering correction
*** End Patch
PATCH

test -s "$snapshot_dir/prd.md"
