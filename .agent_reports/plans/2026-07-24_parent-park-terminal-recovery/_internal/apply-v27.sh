#!/usr/bin/env bash
set -euo pipefail

spec_root=${AGENT_SPEC_ROOT:?AGENT_SPEC_ROOT is required}
test "${AGENT_SPEC_LOCK_HELD:-}" = 1
test "${AGENT_SPEC_NEXT_VERSION:-}" = 25
test "$spec_root" = /home/Uihyeop/agent_setting/.agent_reports/spec/stage-dispatch

v25="$spec_root/_internal/versions/v25"
v26="$spec_root/_internal/versions/v26"
mkdir -p "$v25" "$v26"

# v26 was committed without advancing the component pipeline metadata or creating
# its predecessor snapshot. Recover both immutable history points before v27.
git show 'f26ac412^:.agent_reports/spec/stage-dispatch/prd.md' > "$v25/prd.md"
git show 'f26ac412^:.agent_reports/spec/stage-dispatch/pipeline_state.yaml' > "$v25/pipeline_state.yaml"
git show 'f26ac412^:.agent_reports/spec/stage-dispatch/pipeline_summary.md' > "$v25/pipeline_summary.md"
cp "$spec_root/prd.md" "$v26/prd.md"
cp "$spec_root/pipeline_state.yaml" "$v26/pipeline_state.yaml"
cp "$spec_root/pipeline_summary.md" "$v26/pipeline_summary.md"

cd "$spec_root"
apply_patch <<'PATCH'
*** Begin Patch
*** Update File: prd.md
@@
 > · **v25 2026-07-24** (semantic completion과 execution quiescence 분리·strong replica concurrent batch/atomic admission·Fleet exact-attempt projection, SD-79~81)
 > · **v26 2026-07-24** (framing 앵커 — registry v4 다중 `replications` 앵커·autopilot-code `frame` 스테이지 신설·생성형 5 recipe framing standard 2-way·plan strong 2-way + plan-check 중재, SD-82; SD-76 단일 review 앵커 스키마 supersede, 원 의도(듀얼 모델 독립 방향 탐색) 복원)
+> · **v27 2026-07-24** (completion-delivery 범위별 parent park — interactive registry-open 보호와 supervised/poll successor-readiness 분리, terminal-unverifiable 전역 교착 복구, SD-83)
@@
-  direct fallback watcher, progress cache, parent-park/write phase guard가 공통 호출한다.
+  direct fallback watcher와 progress cache가 공통 호출한다. parent-park/write phase
+  guard의 classifier 사용 범위는 SD-83의 completion-delivery mode 경계를 따른다.
@@
 - 규칙 구간: v4 스키마 검증(앵커 kind 어휘·중복 앵커·하류 소비자·중재자·tier·
   glob 규칙·legacy 단일 키 거부)·다중 앵커 전개 결정론·replica 출력 경로 변환
   (`name.ext→name.replica.ext`, `<dir>/**→<dir>-replica/**`)·하류 inputs 확장·
   composed route 동일 확장·schema_version 3 read-only. 의미 판단 구간: framing
   앵커 선정(registry 선언 시 1회)·frame brief의 방향 판정 품질·plan 중재의
   승자/graft 판단·leg 배치의 harness/family 선택.
+
+## 13.17 v27 — completion-delivery 범위별 parent park (2026-07-24)
+
+### 13.17.1 SD-83 — interactive registry-open 보호와 strict completion park 분리
+
+**근거**: v25 구현 뒤 canonical registry의 terminal-unverifiable 행 46개가 일반
+Codex root와 worker의 모든 local tool을 `parent-parked`로 차단했다. 해당 행은 이미
+semantic terminal이라 새 `dispatch-wait`나 harvest로 상태를 바꿀 수 없고, exact host
+process 증거도 없어 quiescence를 증명할 수 없었다. 결과적으로 가드 자신을 수정하거나
+진단할 수 없는 전역 교착이 발생했다. 이 현상은 Codex native subagent의 spawn/wait
+지원과 무관하며, registered-headless completion delivery에 추가된 v24/v25 hook
+projection에서만 발생한다.
+
+- parent park는 하나의 readiness oracle가 아니다. `completion_delivery=supervised`와
+  명시적 `poll-fallback` owner는 exact child batch의 delivery phase를 집행하므로
+  `open|running`뿐 아니라 `done AND process_quiescence!=quiescent`도 계속 pending으로
+  취급한다. delivered phase의 exact harvest-only, undelivered sibling registration,
+  timeout의 typed draining/unverifiable 보존은 SD-78/79 그대로다.
+- 일반 interactive depth-0 parent의 all-local-tool hook은 **registry-open 보호**만
+  소유한다. exact direct child의 latest row가 `open|running`일 때만 park하고, terminal
+  row가 live/draining/unverifiable이어도 세션 전체를 park하지 않는다. terminal row의
+  process를 죽었다고 추론하거나 row를 자동 마감·삭제하는 것이 아니며 Fleet/liveness와
+  cleanup의 증거는 보존한다.
+- successor marker gate, runtime completion join, `dispatch-wait`, direct fallback watcher,
+  governor lease release, worktree cleanup은 계속 shared quiescence classifier를 사용해
+  fail-closed한다. 즉 interactive 도구 사용 가능성과 해당 attempt의 successor-ready/
+  cleanup-safe는 별개 상태다. 전자를 풀었다고 후자를 통과시키지 않는다.
+- native Codex subagent는 registered jobs row와 completion-delivery mode를 만들지 않으므로
+  이 변경의 후보 집합에 들어오지 않는다. native spawn/wait 지원 여부를 registered
+  headless parent-park 정책으로 제한하거나 반대로 추론하지 않는다.
+- recovery는 runtime-owned registry를 수동 mutation하지 않는다. operator가 명시적으로
+  켠 bounded bypass는 이 self-repair transaction 동안만 사용하고, 수정·회귀 검증 뒤
+  일반 hook 경로로 재검증한다.
+
+**acceptance**: ① ordinary interactive + open/running exact child는 park ② ordinary
+interactive + terminal live/draining 또는 terminal-unverifiable child는 unrelated local
+tool 허용 ③ explicit poll-fallback의 동일 terminal non-quiescent 두 상태는 계속 park
+④ supervised delivered/undelivered phase 규칙과 missing/invalid recovery fail-closed 유지
+⑤ terminal-quiescent는 모든 mode에서 park 후보 아님 ⑥ successor gate/join/wait/fallback
+readiness fixture 결과 무변 ⑦ native subagent-only 세션은 후보 0 ⑧ unrelated parent,
+stale older attempt, registry row mutation 0.
 ## 14. 의미↔규칙 경계 체크 (DESIGN_PRINCIPLES §0.7)
@@
 - **v25 정련**: semantic terminal과 exact-process quiescence의 AND gate, PID/start/namespace 판정, N-slot governor 원자 예약·claim·cancel, replica-group cardinality/동시 lifecycle, exact attempt Fleet join은 결정론 fixture 대상이다. 어떤 review 결과가 타당한지와 실패 leg를 SD-50의 어느 eligible harness로 내릴지는 owner 의미 판단이지만, strong plan을 임의 복제하거나 sibling을 묵시적으로 직렬화하는 것은 허용되지 않는다.
+- **v27 경계 정련**: `supervised|poll-fallback` strict completion park와 ordinary interactive registry-open park의 후보 상태 집합, exact parent/latest-attempt 선택, bypass의 explicit opt-in은 결정론 fixture 대상이다. terminal row를 ordinary global park에서 제외해도 successor/join/wait/fallback/cleanup의 quiescence 판정은 약화하지 않으며, terminal-unverifiable을 dead로 재분류하거나 registry를 수동 수정하는 것은 금지한다.
*** Update File: pipeline_state.yaml
@@
-version: 25
+version: 27
@@
   - 'plans/2026-07-24_dispatch-quiescence-contract/{plan/plan.md,_internal/metrics.md,_internal/spec-route.json}: shared quiescence + atomic replica admission/batch + Fleet exact-attempt projection; cap/sleep/marker-delay 금지'
+  - '사용자 결정 2026-07-24 (v26): 생성형 recipe의 framing은 standard 2-way, plan은 strong 2-way로 독립 방향 탐색하고 plan-check가 중재; registry v4 다중 replications와 frame stage로 배선(SD-82)'
+  - '운영 진단 2026-07-24 (v27): terminal-unverifiable current-contract row 46개가 ordinary Codex root/worker의 모든 local tool을 parent-parked로 차단. semantic terminal이라 wait/harvest로 해소 불가하고 host process 증거 부재로 quiescence도 입증 불가 — completion-delivery scope와 global park 후보 집합의 결합이 원인'
+  - '공식·로컬 surface 대조 2026-07-24 (v27): Codex native subagent spawn/wait와 registered-headless App Server completion supervisor는 별도 runtime surface. native 지원을 registered parent park로 제한하지 않으며 supervised/poll readiness만 strict 유지'
 phases:
-  spec: done              # PRD v25 — SD-79~81 successor-ready/replica batch/Fleet exact attempt; v24 snapshot = _internal/versions/v24/
+  spec: done              # PRD v27 — SD-83 completion-delivery-scoped parent park; v25/v26 누락 snapshot을 transaction에서 복구
   scaffolding: deferred   # lean — 코드 skeleton 은 autopilot-code 로 이월 (§11 module 구조만 확정, wrapper 재작성 불요)
   design: n/a             # 시각 UI 없음 (인프라 계약)
-  dev: in_progress        # dispatch-quiescence-contract 구현·회귀·live strong cross-harness drill 진행 중
+  dev: in_progress        # parent-park-terminal-recovery 구현·회귀·일반 hook smoke 진행 중
 last_updated: 2026-07-24
 decisions_locked:
+  - 'SD-83(v27): supervised와 explicit poll-fallback owner는 terminal non-quiescent를 strict pending으로 유지한다. ordinary interactive depth-0 all-tool hook은 exact latest direct child의 open/running만 park하며 terminal live/unverifiable은 전역 park 후보에서 제외한다. successor gate/join/wait/fallback/cleanup은 shared quiescence로 계속 fail-closed하고 registry mutation/dead inference/native-subagent 제한은 금지'
+  - 'SD-82(v26): registry v4 replications 배열로 review/map/pipeline-stage 다중 앵커를 전개. 생성형 5 recipe framing은 standard 2-way, autopilot-code frame stage 신설, plan은 strong 2-way+plan-check 중재. quick/direct와 처방적 recipe는 새 stage 비대상'
*** Update File: pipeline_summary.md
@@
-- **Status**: v25 implementation in progress — successor-ready quiescence·strong replica concurrent/atomic admission·Fleet exact-attempt projection(SD-79~81)
+- **Status**: v27 implementation in progress — completion-delivery-scoped parent park·terminal-unverifiable interactive recovery(SD-83)
@@
 ## v25 update (2026-07-24) — successor readiness + concurrent replica batch
@@
   같은 attempt의 `stage one-shot` 중복행만 제거한다. route-node stage done과 unrelated/
   native subagent row는 유지한다. 구현 후 deterministic race/cap/Fleet fixtures와 실제
   fixed-cap cross-harness strong drill로 closure한다.
+
+## v26 update (2026-07-24) — framing 앵커 + multi-replication topology
+
+- registry v4가 단일 review replication을 다중 `replications`로 일반화했다. 생성형
+  recipe의 framing은 standard부터 2-way, autopilot-code plan은 strong부터 2-way이며
+  plan-check가 두 leg를 중재한다. `frame` stage와 map/pipeline merge 계약을 SD-82에
+  고정했다.
+- f26ac412에서 PRD만 v26으로 전진하고 component pipeline metadata/snapshot이 빠진
+  drift를 v27 transaction이 보존적으로 복구했다: Git의 pre-v26 세 파일을 v25,
+  transaction 직전 세 파일을 v26 snapshot으로 저장했다.
+
+## v27 update (2026-07-24) — completion-delivery-scoped parent park
+
+- terminal-unverifiable current-contract row 46개가 ordinary Codex root와 worker의 모든
+  local tool을 전역 차단했다. 해당 행은 semantic terminal이라 wait/harvest로 바뀌지
+  않고 host process 증거도 없어, 기존 규칙 안에서는 자기수리조차 불가능했다.
+- SD-83은 supervised/poll-fallback의 strict terminal-nonquiescent park를 유지하되,
+  ordinary interactive all-tool hook은 exact latest child의 `open|running`만 park하도록
+  분리한다. terminal row는 삭제·마감·dead 추론하지 않는다.
+- successor gate, completion join, wait, fallback, governor/cleanup은 shared quiescence
+  classifier를 계속 사용한다. native subagent surface는 registered completion-delivery
+  후보가 아니므로 동작을 제한하지 않는다.
*** End Patch
PATCH

grep -Fq '**v27 2026-07-24**' prd.md
grep -Fq '## 13.17 v27' prd.md
grep -Fq 'version: 27' pipeline_state.yaml
grep -Fq 'SD-83(v27)' pipeline_state.yaml
grep -Fq '## v27 update' pipeline_summary.md
test -s "$v25/prd.md"
test -s "$v26/prd.md"
