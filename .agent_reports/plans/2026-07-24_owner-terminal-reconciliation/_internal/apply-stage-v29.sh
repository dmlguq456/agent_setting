#!/usr/bin/env bash
set -euo pipefail

spec_root=${AGENT_SPEC_ROOT:?}
test "${AGENT_SPEC_LOCK_HELD:-}" = 1
test "${AGENT_SPEC_NEXT_VERSION:-}" = 28
snapshot="$spec_root/_internal/versions/v28"
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
 > · **v28 2026-07-24** (owner dispatch mode-axis 분리 — capability mode와 depth-2 worker unit/persona의 독립 필드·owner 모순 조합 fail-closed, SD-84)
+> · **v29 2026-07-24** (owner terminal reconciliation·canonical parent identity·공통 observed liveness·Claude deep=Opus/Fable main-only, SD-85~87)
@@
-## 14. 의미↔규칙 경계 체크 (DESIGN_PRINCIPLES §0.7)
+## 13.19 v29 — owner terminal reconciliation and dispatch model eligibility (2026-07-24)
+
+### 13.19.1 SD-85 — Claude Fable은 interactive depth-0 main-only, deep dispatch는 Opus
+
+- Claude adapter의 portable `deep *` 역할은 Opus로 실현한다. Fable은 사용자와 직접
+  대화하는 interactive depth-0 main session에서만 허용하며 registered headless
+  owner/stage, native subagent/agent-team worker, inherited dispatch model 및 capacity
+  fallback 후보에서는 자격 미달이다.
+- surface-aware eligibility는 default mapping뿐 아니라 explicit `model=fable`과
+  Fable main에서의 model inheritance도 launch 전에 거부한다. 거부된 Fable을 Opus로
+  조용히 바꾸지 않고 typed reason을 남기며, portable role 기반 재해석만 명시적으로
+  Opus를 선택한다.
+- Claude deep capacity cascade는 `opus -> sonnet`처럼 dispatch-eligible 모델만 가진다.
+  Fable usage/statusline/Fleet telemetry는 interactive main 관측을 위해 유지하되 그것이
+  headless eligibility 증거가 되지 않는다.
+
+### 13.19.2 SD-86 — supervisor exit의 exact terminal reconciliation
+
+- registered owner supervisor는 final runtime envelope와 process exit를 자신이 소유한
+  exact attempt id에 원자 reconcile한다. 성공, capacity, auth, protocol, missing-result,
+  signal/exit를 shared terminal classifier로 typed closure하고 `open` row를 남기지 않는다.
+- Claude 429/Fable-limit 같은 capacity envelope는 `done,note=dead-capacity`와
+  `failure_class=capacity` 증거를 보존한다. 이 terminal state가 SD-59 fallback state
+  machine의 입력이며, short early-death watch window가 끝난 뒤 발생해도 동일하다.
+- supervisor는 slug/cwd로 다른 retry를 breadth-close하지 않는다. marker/terminal race는
+  기존 exact terminal evidence 우선순위를 지키고, partial registry failure는 evidence를
+  보존한 typed nonzero와 exact reconcile 경로로 남긴다.
+
+### 13.19.3 SD-87 — canonical repository parent identity와 공통 observed liveness
+
+- parent lookup은 primary checkout과 linked worktree를 같은 canonical repository로
+  정규화하되 exact worktree, parent attempt id, PID/start 및 current status 조건은
+  약화하지 않는다. `--parent`는 slug, `--parent-attempt-id`는 exact attempt라는
+  별도 namespace를 prompt/CLI/test에서 강제한다.
+- Fleet, parent park, completion join, `dispatch-wait`, liveness와 fallback watcher는
+  같은 pure observed-liveness enum을 소비한다. `open + exact process gone + terminal
+  envelope`는 alive가 아니며 mutating supervisor/reconciler가 exact row를 닫는다.
+- Fleet는 read-only consumer로서 registry를 수정하지 않는다. 아직 reconcile되지 않은
+  stale-open은 숨기거나 alive로 합성하지 않고 `terminal-observed/reconcile-needed`로
+  표시한다. park/wait도 이를 무한 polling 대상으로 취급하지 않는다.
+
+**acceptance**: ① Claude supervisor 429 final이 exact row를 `dead-capacity`로 닫고
+fallback이 다음 eligible non-Fable 모델/harness로 한 번 전이 ② success/non-capacity/
+missing-result/signal terminal도 open 0 ③ deep role과 cascade에 Fable 0, explicit/inherited
+headless Fable launch 0, interactive telemetry 유지 ④ primary↔linked parent binding 성공,
+foreign repo·slug/attempt 혼용 거부 ⑤ PID-gone stale-open fixture에서 Fleet/park/wait/
+fallback observed state 일치, Fleet mutation 0 ⑥ Claude/Codex supervisor·wrapper·Fleet·
+liveness/adaptation 회귀 0.
+
+## 14. 의미↔규칙 경계 체크 (DESIGN_PRINCIPLES §0.7)
@@
 - **v28 축 정련**: capability-mode catalog membership, owner reserved unit/worker-mode 부재, non-owner unit↔worker-mode 일치, route tuple equality, legacy mode shape 분류는 결정론 validator 대상이다. capability mode의 의미 선택은 route owner가 하지만 worker persona 칸에 대체값을 넣어 validator를 우회할 수 없다.
+- **v29 terminal/model 정련**: execution-surface별 Fable 자격, deep role의 Opus 실현, supervisor final envelope→exact terminal closure, canonical repo identity, observed-liveness enum과 consumer별 mutation 권한은 결정론 fixture 대상이다. capacity 이후 어느 eligible harness/model을 택할지는 SD-22 의미 판단이지만 Fable을 분사 후보로 되살리거나 죽은 exact process를 alive로 합성할 수 없다.
*** Update File: pipeline_state.yaml
@@
-version: 28
+version: 29
@@
-  spec: done              # PRD v28 — SD-84 owner dispatch mode-axis separation
+  spec: done              # PRD v29 — SD-85~87 owner terminal/model/liveness contract
@@
 decisions_locked:
+  - 'SD-87(v29): primary/linked worktree는 canonical repository identity를 공유하되 exact worktree/attempt/PID 조건을 유지한다. Fleet/park/wait/fallback은 공통 observed-liveness를 소비하고 read-only Fleet는 stale-open을 숨기거나 mutation하지 않는다'
+  - 'SD-86(v29): supervisor final envelope/process exit는 exact owner attempt를 typed terminal로 reconcile한다. capacity는 dead-capacity/failure_class=capacity로 닫혀 SD-59 fallback을 기동하며 breadth-close는 금지한다'
+  - 'SD-85(v29): Claude deep 역할은 Opus. Fable은 interactive depth-0 main-only이며 registered/native/inherited dispatch 및 capacity cascade에서 금지한다. telemetry 표시는 유지한다'
*** Update File: pipeline_summary.md
@@
 # stage-dispatch — Spec Pipeline Summary
+
+## v29 update (2026-07-24) — owner terminal/model/liveness convergence
+
+종료된 supervised owner의 exact row를 final envelope와 process exit로 즉시 typed
+terminal reconcile하고, capacity closure가 기존 자동 fallback state machine을 실제로
+기동하게 한다. primary/linked worktree parent lookup은 canonical repository identity를
+공유하며 Fleet·park·wait·fallback은 하나의 observed-liveness enum을 소비한다. Claude
+`deep`은 Opus로 고정하고 Fable은 interactive depth-0 main session에서만 허용한다.
+
*** End Patch
PATCH
grep -Fq '**v29 2026-07-24**' prd.md
grep -Fq 'SD-85(v29)' pipeline_state.yaml
grep -Fq '## v29 update' pipeline_summary.md
