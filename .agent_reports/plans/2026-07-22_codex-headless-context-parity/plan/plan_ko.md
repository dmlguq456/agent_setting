---
status: complete
created: 2026-07-22
---

# Codex registered-headless handoff 및 부모 컨텍스트 위생

## 목표

Codex registered-headless 부모가 launch, wait/liveness, harvest 전 구간에서
정확한 attempt에 결합된 typed handoff를 받게 하되, 원시 worker 내용을 부모
컨텍스트로 복사하지 않는다. 기존 registry, Fleet, completion marker, fallback,
liveness, debugging 계약은 모두 유지한다.

## 현재 상태 분석

### 지배 계약

- SD-1은 dispatch-depth-1 owner가 stage 경로, verdict/status, gate 결정만
  보유하는 얇은 conductor여야 하며 stage 본문을 읽지 못하게 한다
  (`.agent_reports/spec/stage-dispatch/prd.md:123-128`).
- SD-2는 stage 간 전달을 파일로만 제한한다. prompt에는 artifact 경로와
  계약만 들어가며 이전 대화나 plan 본문 복사본은 들어가지 않는다
  (`prd.md:130-136`).
- Registered worker는 최소 typed kernel을 받고 정확히 3줄 envelope만
  반환한다 (`core/OPERATIONS.md:96-100`, `roles/worker-bootstrap.md:3-30`).
- 정확한 registry identity, 같은 turn 안의 bounded wait, liveness evidence,
  fallback, exact completion marker가 이미 canonical 계약이다
  (`core/OPERATIONS.md:166-177`).

### Claude comparator

- sibling wrapper는 모든 `claude -p` 출력을 attempt log로 redirect하고 launch
  receipt만 출력한다 (`adapters/claude/bin/dispatch-headless.py:410-429,
  1068-1118,1129-1189`).
- 로컬 fake-CLI의 success/failure/blocked 세 fixture 모두 raw marker와 3줄
  handoff를 parent receipt에서 배제하고 attempt log에만 남겼다. 전체 측정
  행렬과 명령은 `../baseline_comparison.md`에 있다.
- Claude는 CLI가 0으로 종료하면서 텍스트로 반환한 `FAIL`/`BLOCKED`를 receipt
  단계에서 type화하지 않는다. 이 누락을 복제하는 것이 아니라 transcript
  isolation과 동등한 안전 정보 클래스를 제공하는 것이 parity 목표다.

### Codex 경로와 실제 gap

- `utilities/codex_dispatch_terminal.py:16-115`는 정확한 `turn.completed` 앞의
  최종 3줄 handoff를 인식하고 sandbox-init/fail/blocked를 type화한다. 그러나
  terminal 부재와 malformed terminal을 구분하지 못하고 artifact 경로가
  `artifact_root` 안인지 검증하지 않는다.
- `adapters/codex/bin/dispatch-headless.py:554-604`는 이미
  `codex exec --json`을 attempt JSONL로 redirect한다. foreground launch는
  terminal을 parse하고 exact fail/blocked row만 닫은 뒤 (`:1431-1455`)
  receipt를 출력한다 (`:1466-1536`). 현재 raw 내용은 출력되지 않는다.
- `adapters/codex/bin/dispatch-liveness.py:324-369`는 failure note가 있는
  terminal만 인식한다. 유효한 `PASS`는 dead-PID 판정으로 넘어가 generic
  `EXITED`가 된다.
- `utilities/dispatch-wait.sh:78-88`이 쓰는
  `utilities/dispatch-liveness.sh:69-209`는 Codex JSONL을 mtime/debug 증거로는
  보지만 정확한 typed handoff는 추출하지 않는다. 따라서 wait만으로는 raw
  log 진단 없이 `PASS`/`FAIL`/`BLOCKED`를 구분할 수 없다.
- `adapters/codex/bin/dispatch-harvest.py:39-55,118-200`는 registry row와 exact
  completion/closure를 처리하지만 안전한 terminal envelope와 artifact
  readability를 내보내지 않는다.
- 기존 테스트는 parsing, sandbox-init closure, registry exactness, wait exit
  code를 검증하지만 launch/wait/liveness/harvest 전체의 parent-output
  non-leakage는 증명하지 않는다. 출발점은
  `utilities/codex_dispatch_terminal.test.py:10-62`,
  `utilities/dispatch_registry.test.py:44-72`,
  `utilities/dispatch_harvest.test.py:99-207`,
  `utilities/dispatch-wait.test.sh:31-80`이다.

## 변경 계획

### Phase 1: 단일 안전 exact-attempt terminal inspection API 정의

의존성 없음. 모든 parent-facing 연결보다 먼저 완료한다.

1.1. `utilities/codex_dispatch_terminal.py` 수정.

- 파일 첫 수정 직전에
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write utilities/codex_dispatch_terminal.py codex-headless`
  pre-edit guard를 실행한다.
- 현재 caller를 위해 `inspect_terminal_log(path) -> dict | None` compatibility
  wrapper를 유지한다.
- 마지막 exact `turn.completed`를 기준으로 `absent`, `valid`, `invalid`를
  구분하는 structured inspection API를 추가한다. invalid 결과는
  `missing-final-agent-message`, `malformed-handoff`,
  `artifact-outside-root` 같은 enum형 이유만 포함하고 거부된 raw 텍스트는
  포함하지 않는다.
- terminal 직전 마지막 agent message와 정확한 3줄 grammar만 허용한다.
  이전 agent message, command output, 선택된 terminal 뒤 event는 무시한다.
- 선택된 registry row의 4번째 column인 `worktree`를 root-resolution 입력으로
  고정한다. 기존 `utilities/artifact-root.sh <selected-worktree>` 계약과
  absolute `AGENT_ARTIFACT_ROOT` override를 통해 root를 resolve해 inspector에
  명시적으로 넘긴다. Registry column은 추가하지 않는다. 기존 pipe의
  `artifact_root` metadata는 cross-check에만 쓰며 mismatch, resolver failure,
  missing root는 고정 `artifact-root-unavailable` 또는
  `artifact-root-mismatch` state로 fail closed한다. linked worktree의 tracked
  `.agent_reports` shadow로 fallback하지 않는다.
- Non-`-` artifact는 해당 root 아래 strict resolve하고 missing path 및
  symlink/path escape를 거부한다. Typed readability와 validated path만 반환하며
  artifact 본문은 열거나 출력하지 않는다. `artifact: -` 허용 여부는 기존
  worker/completion-gate 계약에 남긴다.
- Shell wire를 다음 순서의 단일 ASCII v1 record로 고정한다:
  `codex-terminal-v1<TAB>state<TAB>source<TAB>verdict<TAB>artifact_state<TAB>blocker_reason<LF>`.
  값은 closed enum만 허용한다. `state=valid|absent|invalid|error`,
  `source=exact-turn-completed|runtime-error|none`,
  `verdict=PASS|FAIL|BLOCKED|-`, typed artifact state,
  `blocker_reason=none|worker-reported|contract-violation|-`이다. Path나
  worker-authored text는 wire에 넣지 않으므로 shell liveness는 path를
  decode하지 않는다. Exit 0/2/3/4는 valid/absent/invalid/inspection-error,
  64는 CLI misuse다. 0/2/3/4는 각각 정확히 한 record만 출력하고 raw stderr는
  금지한다. Malformed/multiple record는 caller가 `inspector-wire-invalid`로
  분류한다.
- `artifact_state` token은 정확히
  `unchecked|none|readable|missing|outside-root|unsafe-root`로 고정한다. 전체
  legal wire matrix는 다음과 같다.

  | exit | state | source | verdict | artifact_state | blocker_reason |
  |---:|---|---|---|---|---|
  | 0 | `valid` | `exact-turn-completed` | `PASS` | `none|readable` | `none` |
  | 0 | `valid` | `exact-turn-completed` | `FAIL|BLOCKED` | `none|readable` | `none|worker-reported` |
  | 2 | `absent` | `none` | `-` | `unchecked` | `-` |
  | 3 | `invalid` | `exact-turn-completed` | `-` | `unchecked|missing|outside-root` | `contract-violation` |
  | 4 | `error` | `runtime-error` | `-` | `unchecked|unsafe-root` | `contract-violation` |

  이 밖의 tuple은 모두 불법이며 exit 64는 record를 출력하지 않는다. Path와
  free text는 `codex-terminal-v1`에 절대 들어가지 않는다. Relative,
  filesystem-wide/over-broad, non-directory, missing, symlink-escaped, tracked
  worktree `.agent_reports` shadow, exact-attempt pipe metadata mismatch root는
  모두 하나의 고정 tuple
  `error/runtime-error/-/unsafe-root/contract-violation`과 exit 4로 귀결한다.
  `missing`이나 shadow fallback으로 낮추지 않는다. Valid root 아래 artifact
  missing은 `invalid/exact-turn-completed/-/missing/contract-violation`, artifact
  escape는 동일 형태의 `outside-root` tuple이다.
- 모든 worker-authored failure text에 하나의 parent-output policy를 적용한다.
  기본 receipt/liveness/wait/harvest는 고정 `blocker_reason`만 낸다. `PASS`는
  반드시 `blocker: none`이어야 하고 아니면 `pass-blocker-not-none` invalid다.
  Harvest가 failure detail을 명시적으로 요청한 경우에만
  `blocker_detail_excerpt` 및/또는 `failure_diagnostic_excerpt`를 출력할 수
  있다. Control을 먼저 escape한 뒤 각 필드를 UTF-8/code point/escape token을
  자르지 않는 가장 긴 512-byte 이하 prefix로 truncate하고 고정
  `*_truncated=0|1`을 붙인다. Diagnostic source는 exact attempt의 structured
  failed `command_execution`/runtime error뿐이며 `agent_message`는 금지한다.
  옵션이 있어도 모든 `PASS`는 두 detail field를 생략한다.
- Python receipt/harvest는 validated artifact reference를 padding 없는 RFC
  4648 URL-safe UTF-8 base64 `artifact_path_b64`로 노출할 수 있지만 decode나
  open은 하지 않는다. Liveness/wait는 path를 받지 않는다. 다음 stage는
  exact-attempt `valid` + `readable` 확인 뒤에만 decode하고 자기 guard 아래
  파일을 직접 연다.

1.2. `utilities/codex_dispatch_terminal.test.py` 확장.

- 파일 첫 수정 직전에
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write utilities/codex_dispatch_terminal.test.py codex-headless`
  pre-edit guard를 실행한다.
- raw command, 이전 agent message, final envelope sentinel이 서로 다른
  `PASS`/`FAIL`/`BLOCKED` fixture를 추가한다.
- `turn.completed` 부재, completed지만 envelope 부재, extra prose로 인한
  malformed, 이전 decoy envelope, completion 뒤 event, oversized tail,
  artifact 존재/containment, symlink escape를 검증한다.
- compatibility wrapper가 기존 failure note
  (`dead-worker-fail`, `dead-worker-blocked`, `dead-sandbox-init`)를 유지함을
  증명한다.
- linked-worktree canonical-root resolution, missing root, root metadata
  mismatch, space/control byte가 있는 fixture path, exact single-record wire,
  모든 wire exit code, malformed/multiple CLI record, mixed-harness bypass를
  검증한다.
- Frozen state/source/verdict/artifact-state/blocker/exit matrix의 모든 legal
  row와 대표 illegal cross-product를 검증한다. Relative, over-broad,
  non-directory, symlink-escaped, shadow, missing, metadata-mismatched root를
  각각 별도 fixture로 만들고 모두 동일한 `unsafe-root` tuple 및 path/free-text
  leakage 0개를 assert한다.
- Blocker/diagnostic detail이 default-off, failure-only, labeled,
  control-escaped, bounded임을 oversized single-line/multibyte-boundary case로
  증명한다. `PASS` + non-`none` blocker 및 모든 `PASS` detail emission 음성
  fixture를 추가하고 agent message가 diagnostic source가 아님을 증명한다.

완료 증거: parser unit suite PASS, valid fixture는 3개 handoff field와 typed
metadata만 노출, invalid fixture는 raw sentinel을 전혀 노출하지 않으며 exact
wire/root/failure-text boundary matrix가 PASS한다.

Phase 1 focused gate/rollback boundary: Phase 2 전
`PYTHONPATH=utilities python3 utilities/codex_dispatch_terminal.test.py`를
실행한다. Execution step log에 phase-owned file과 old/new block을 기록한다.
실패하면 중단하고 각 owned file의 exact write guard를 다시 실행한 뒤 기록된
old block을 `apply_patch`로 복원한다. reset/checkout과 pre-existing/unrelated
worktree 변경은 건드리지 않는다.

### Phase 2: 안전 결과를 parent-facing control surface에 투영

의존성: Phase 1 API와 테스트.

2.1. `adapters/codex/bin/dispatch-headless.py` 수정.

- 파일 첫 수정 직전에
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write adapters/codex/bin/dispatch-headless.py codex-headless`
  pre-edit guard를 실행한다.
- foreground dictionary probing을 structured inspection으로 교체하되
  compatibility용 `terminal_verdict`는 유지한다.
- Phase 1대로 exact selected worktree에서 canonical root를 resolve/cross-check
  한다. Receipt에 handoff state/source, verdict, artifact readability,
  `artifact_path_b64`, 고정 `blocker_reason`을 추가하며 blocker detail,
  diagnostic, transcript, artifact 본문은 출력하지 않는다.
- exact `FAIL`/`BLOCKED` row closure와 evidence를 유지한다. 유효한 `PASS`는
  observation일 뿐이며 row close, completion marker 작성, route advance를
  해서는 안 된다.
- detached 동작은 그대로 둔다. terminal 이전에 반환하므로 이후
  liveness/harvest가 inspection을 소유한다.

2.2. `adapters/codex/bin/dispatch-liveness.py` 수정.

- 파일 첫 수정 직전에
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write adapters/codex/bin/dispatch-liveness.py codex-headless`
  pre-edit guard를 실행한다.
- failure뿐 아니라 모든 verdict에 대해 PID/transcript fallback 전에 exact
  row의 `log_file`을 inspect한다.
- valid `PASS`는 `COMPLETED ... exact turn.completed PASS; harvest required`로
  표시하고 row가 open인 동안 exit 3을 유지한다. `FAIL`/`BLOCKED`는
  transcript excerpt 없이 typed terminal failure로 표시한다. terminal-invalid는
  거부된 내용을 출력하지 않고 typed `EXITED ... invalid-handoff`로 표시한다.
- exact-attempt binding, orphan precedence, limit/auth classification,
  heartbeat/PID evidence, current-row filtering, exit code는 모두 유지한다.

2.3. `utilities/dispatch-liveness.sh` 수정.

- 파일 첫 수정 직전에
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write utilities/dispatch-liveness.sh codex-headless`
  pre-edit guard를 실행한다.
- exact `log_file`이 있는 current Codex row에서 generic PID/mtime fallback보다
  먼저 selected row의 `worktree`와 함께 Phase 1 inspector를 호출한다. 정확히
  6개의 tab-separated v1 field만 parse하고 extra/missing record는
  `inspector-wire-invalid`로 거부한다. Enum만 소비하고 artifact path를
  decode하지 않는다.
- Python surface와 동일한 `COMPLETED`/typed-failure/invalid-handoff class와
  exit-3 동작을 적용한다. artifact 본문, blocker 텍스트, raw JSONL은 넣지
  않는다.
- Claude/OpenCode PID, transcript, limit, orphan, legacy-row 경로는 건드리지
  않으며 mixed-harness registry도 계속 동작해야 한다.

2.4. `utilities/dispatch-wait.sh` 수정.

- 파일 첫 수정 직전에
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write utilities/dispatch-wait.sh codex-headless`
  pre-edit guard를 실행한다.
- selection, 0/2/3 exit, interval/max bound, synchronous polling은 유지한다.
- exit-3 제목을 `SUSPECT/DEAD` 전용에서 `terminal/SUSPECT/DEAD`로 일반화해
  성공했지만 아직 harvest되지 않은 Codex child를 dead로 오표기하지 않는다.
- sanitized liveness output만 계속 전달한다.

2.5. `adapters/codex/bin/dispatch-harvest.py` 수정.

- 파일 첫 수정 직전에
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write adapters/codex/bin/dispatch-harvest.py codex-headless`
  pre-edit guard를 실행한다.
- exact row 선택 후 그 row의 `log_file`만 inspect하고 normalized handoff
  state/source/verdict, `artifact_path_b64`, 고정 `blocker_reason`, artifact
  readability를 출력한다. Selected row worktree로 root를 resolve하고 pipe
  metadata를 cross-check하며 본문은 읽거나 출력하지 않는다.
- Shared inspector 기반의 단일 명시적 failure-detail 옵션을 추가한다. Phase
  1의 bounded/labeled blocker/diagnostic field만 추가할 수 있다. `PASS` detail은
  거부하고 기본 enable하지 않는다.
- Fleet/debug compatibility를 위한 기존 `job_pipe`, exact selector,
  current attempt validation, profile-home cleanup, completion-marker replay를
  유지한다.
- closure semantics를 유지한다. routed `PASS`에는 계속 exact hash-bound
  `--completion`이 필요하며 parsed handoff가 breadth-close하거나 이를
  대체할 수 없다.

완료 증거: 동일 fixture가 foreground receipt, Codex liveness, shared wait,
harvest에서 일관된 typed verdict를 제공한다. success output에는 raw sentinel이
0개이고 요청된 failure field는 각각 labeled이며 512 UTF-8 byte 이하이다.

Lifecycle-valid fixture matrix: 실제 foreground wrapper는 stream isolation,
exact JSONL/artifact retention, receipt field, registry transition을 검증한다.
`PASS` row는 current/open 상태로 남아 Python liveness, shared liveness/wait,
read-only harvest에 직접 사용한다. `FAIL`/`BLOCKED` row는 wrapper 반환 시 이미
closed여야 한다. 기존 supported exact-attempt read-only harvest selector가
테스트로 증명된 경우에만 closure 후 읽고 normal current-row filtering은 절대
완화하지 않는다. Failure liveness/wait는 실제 wrapper-shaped
`FAIL`/`BLOCKED` JSONL과 byte-identical한 log를 가진 명시적 supplemental
controlled current/open row로 검증한다. 이 row는 supplemental로 label하고
closed/non-current attempt 선택 경로가 되지 않음을 증명한다.

Phase 2 focused gate/rollback boundary: parser suite와 함께
`python3 adapters/codex/bin/dispatch-headless.sd45.test.py`,
`python3 utilities/dispatch_registry.test.py`,
`python3 utilities/dispatch_harvest.test.py`,
`bash utilities/dispatch-liveness.test.sh`,
`bash utilities/dispatch-wait.test.sh`를 Phase 3 전에 실행한다. 실패하면
중단하고 exact guard를 다시 실행한 뒤 execution log의 old block과
`apply_patch`로 Phase 2 source 5개만 되돌린다. Phase 1 및 unrelated/pre-existing
변경은 보존한다.

### Phase 3: deterministic parity 및 회귀 테스트

의존성: Phase 1과 2. 이 phase의 테스트는 마지막 aggregate run을 제외하면
서로 독립적이다.

3.1. `utilities/dispatch_parent_context_conformance.test.py` 추가.

- 파일 생성 직전에
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write utilities/dispatch_parent_context_conformance.test.py codex-headless`
  pre-edit guard를 실행한다.
- fake `claude -p` success/fail/blocked fixture로 측정된 Claude baseline을
  고정한다. raw content와 handoff는 attempt log에 있고 parent receipt에는
  둘 다 없어야 한다.
- fake-Claude와 대칭인 fake `codex` executable을 만들고 실제
  `adapters/codex/bin/dispatch-headless.py --start` subprocess를
  `--launch-lifecycle foreground-scoped`로 `PASS`/`FAIL`/`BLOCKED` 각각
  실행한다. Real temporary Git worktree/artifact root/registry와 deterministic
  fake `codex exec --json` stdout/stderr를 사용한다. Renderer 호출로 대체하지
  않고 wrapper stdout/stderr, exact attempt JSONL, registry before/after를
  capture한다.
- Wrapper-produced open `PASS` row/log만 Codex Python liveness, shared shell
  liveness/wait, read-only harvest에 직접 전달한다. Wrapper-produced closed
  `FAIL`/`BLOCKED`는 selector가 current-row filtering을 바꾸지 않음을 증명한
  뒤 supported exact-attempt read-only harvest selector로만 읽는다. Python/
  shared liveness와 wait에는 실제 wrapper-shaped failure JSONL의 byte-identical
  복사본으로 supplemental controlled current/open row를 만들고 wrapper의
  closed failure attempt를 다시 열거나 breadth-select하지 않는다.
  Handcrafted parser/renderer fixture는 supplemental unit coverage로만 둔다.
- raw command, prior agent, final message, optional failure diagnostic,
  artifact-body-only content에 별도 sentinel을 쓴다. 모든 verdict에서
  command/prior-agent/final-message sentinel은 exact attempt log에 남지만 wrapper
  stdout/stderr와 모든 parent-facing output에는 없어야 한다. Artifact-body
  sentinel은 validated artifact에 남되 receipt/liveness/wait/harvest에는 없어야
  한다. Simulated next stage만 validated reference를 decode해 artifact를 직접
  연다.
- Optional blocker/diagnostic excerpt는 default absent, explicit failure
  option에서만 labeled/control-escaped/512 UTF-8 byte 이하임을 oversized,
  multibyte, control case로 증명한다. `PASS` detail은 불가하고 `PASS` +
  non-`none` blocker는 invalid임을 확인한다.
- attempt/route/log binding을 확인해 다른 worker의 더 최신 log가 선택된
  row를 만족시키지 못하게 한다. `PASS` exact row는 open이고 completion
  marker를 만들지 않으며 `FAIL`/`BLOCKED`는 기존 note로 exact attempt만
  닫는다. Unrelated/decoy row는 byte-for-byte 유지한다.
- Verdict별 before/after를 고정한다. Wrapper `PASS`는 liveness/wait/read-only
  harvest 전후 open이며 completion marker가 없다. Wrapper `FAIL`/`BLOCKED`는
  read-only harvest 전에 이미 exact-attempt closed이고 afterward에도
  byte-identical하다. Supplemental failure row는 liveness/wait 관찰 내내
  open이며 실제 closed row에 영향을 줄 수 없다.

3.2. `adapters/codex/bin/dispatch-headless.sd45.test.py` 확장.

- 파일 첫 수정 직전에
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write adapters/codex/bin/dispatch-headless.sd45.test.py codex-headless`
  pre-edit guard를 실행한다.
- valid pass/fail/blocked, invalid terminal, terminal 부재에 대한 receipt
  rendering case를 supplemental unit coverage로 추가한다. Wrapper-boundary
  isolation authority는 3.1에 있다.
- `PASS`가 row-close나 completion-marker code를 호출하지 않고 fail/blocked가
  기존 note로 exact attempt만 닫음을 assert한다.
- receipt stdout에 raw command/이전-agent sentinel이 없음을 assert한다.

3.3. `utilities/dispatch-wait.test.sh`와
`utilities/dispatch-liveness.test.sh` 확장.

- 각 파일의 첫 수정 직전에 다음 guard를 실행한다:
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write utilities/dispatch-wait.test.sh codex-headless`,
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write utilities/dispatch-liveness.test.sh codex-headless`.
- 한 parent 아래 exact Codex `PASS`, `FAIL`, `BLOCKED` JSONL row를 추가한다.
- exit 3, typed terminal 문구, raw sentinel 0개를 assert한다. 기존 no-row,
  alive, dead, parent filter, namespace, limit case는 유지한다.
- Exact v1 wire, malformed/multiple-record 거부, linked worktree, missing root,
  space/control-byte path, mixed-harness bypass case를 추가한다.

3.4. `utilities/dispatch_harvest.test.py` 확장.

- 파일 첫 수정 직전에
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write utilities/dispatch_harvest.test.py codex-headless`
  pre-edit guard를 실행한다.
- exact-row success/fail/blocked envelope 출력과 artifact-root 검증 case를
  추가한다.
- foreign/newer-log 음성 case, malformed envelope, default-off diagnostic,
  failure-only bounded blocker/diagnostic detail, oversized/multibyte/control,
  `PASS` + non-`none` blocker, success non-leakage를 추가한다.
- 기존 ambiguous selector, legacy read-only, idempotent close, exact
  completion-marker test는 그대로 재실행한다.

3.5. liveness seam에 한해 `utilities/dispatch_registry.test.py` 확장.

- 파일 첫 수정 직전에
  `/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh write utilities/dispatch_registry.test.py codex-headless`
  pre-edit guard를 실행한다.
- valid `PASS` terminal fixture가 open row를 generic `EXITED`가 아니라
  `COMPLETED`로 표시하고 completion harvest 전까지 open을 유지함을 증명한다.
- blocked sandbox-init exact-row closure fixture는 유지한다.
- Python liveness/registry seam에 이름이 고정된
  `test_codex_terminal_post_exit_orphan_reconcile` regression을 추가한다. Dead
  PID open Codex attempt 하나의 exact log에 valid terminal envelope와 distinct
  sibling row를 둔다. Post-exit orphan reconcile의 기존 precedence가 새
  terminal display보다 앞서고, exact target row와 기존 note만 canonical closed
  form으로 바뀌며, sibling은 byte-for-byte 유지되고, raw terminal sentinel은
  출력되지 않으며, 두 번째 reconcile은 no-op임을 증명한다. Concrete command는
  `python3 utilities/dispatch_registry.test.py`이고 broad close는 금지한다.

완료 증거: 아래 targeted/aggregate 명령이 모두 PASS한다. Conformance test는
자기 `TemporaryDirectory` 아래 capture tree를 만들고 cleanup 전에 negative
sentinel scan을 내부 실행해 checked capture count를 보고하며, exact
log/artifact의 positive retention도 검증한다. 외부 capture-path placeholder는
없다.

Phase 3 focused gate/rollback boundary: Phase 3-owned test를 모두 실행한 뒤
`python3 utilities/dispatch_parent_context_conformance.test.py`를 wrapper-boundary
gate로 실행한다. 실패하면 중단하고 exact write guard를 다시 실행한 뒤
execution log old block과 `apply_patch`로 Phase 3 test 6개만 복원한다. 새
conformance file은 이 phase가 생성한 경우에만 삭제한다. Pass한 Phase 1/2
구현과 unrelated 변경은 건드리지 않는다.

### Phase 4: 최종 검증 및 handoff evidence

의존성: 모든 구현 phase.

4.1. Verification의 정확한 targeted 명령을 실행하고 stdout, exit code,
test count를 source나 parent conversation이 아니라 cycle의 `test_logs/`
소유 경로에 기록한다. 각 phase의 focused gate 결과, owned-file 목록,
rollback boundary를 포함한다. Phase 4에서는 source edit를 허용하지 않는다.

4.2. `git diff --check`와 scoped diff를 검사한다. canonical PRD, core contract,
Claude wrapper, Fleet schema/collector, completion-marker format, fallback order,
native-subagent surface, runtime config, commit, merge, push, cleanup 변경이
없음을 확인한다.

4.3. `preflight.sh qa-policy thorough code`가 선택한 assurance를 수행한다.
선택된 독립 plan/code pass 하나, 최대 2 review round, 상한 2 deep + 2 fast
reviewer를 적용한다. 독립 worker를 쓸 수 없으면 필수 inline-review fallback을
정직하게 기록하고 independent delegation을 주장하지 않는다.

## 안전 불변조건

1. Raw worker output은 exact attempt log에 durable/debuggable하게 남지만 정상
   successful parent-facing output에는 복제되지 않는다.
2. 모든 terminal inspection은 registry `attempt_id`와 해당 row의 `log_file`에
   결합된다. current exact attempt에 cwd-wide/newest-log fallback을 사용하지
   않는다.
3. 선택된 `turn.completed` 직전의 exact final 3줄 envelope만 유효하다.
   Malformed terminal은 거부된 텍스트를 echo하지 않고 fail closed한다.
   `PASS`는 `blocker: none`인 경우에만 유효하다.
4. Parsed `PASS`는 성공 권한이 아니다. 기존 exact hash-bound completion
   marker만 routed success를 닫고 advance한다.
5. 기존 failure note와 fallback behavior는 유지한다. Parser 변경은 fallback
   hop을 reorder/add하거나 retry budget을 소비하지 않는다.
6. Registry schema, 6-field row, status vocabulary, exact attempt closure,
   Fleet-readable metadata, job-pipe debug data는 변하지 않는다.
7. Wait는 0/2/3 semantics를 가진 synchronous bounded polling으로 유지한다.
   Liveness PID, heartbeat, orphan, limit/auth, legacy fallback도 유지한다.
   이름이 고정된 post-exit orphan-reconcile regression은 precedence, exact
   row/note transition, idempotence, sibling 보존, terminal non-leakage를 고정한다.
8. Canonical root는 exact row worktree로 `utilities/artifact-root.sh`를 호출해
   resolve하며 새 registry column이나 linked-worktree shadow에서 추론하지
   않는다. Relative, over-broad, non-directory, escaped, shadow, missing,
   mismatched root는 모두 fixed `unsafe-root` tuple을 낸다. Non-`-` artifact
   경로는 strict containment 뒤에만 readable이고 parent surface는 artifact
   본문을 출력하지 않는다.
9. V1 shell wire는 path와 worker-authored text가 없는 6-field ASCII enum
   record 하나다. Failure blocker/diagnostic excerpt는 opt-in, failure-only,
   explicit label, control escape, field별 512 UTF-8 byte 상한을 적용하며 code
   point/escape를 자르지 않는다. Agent message는 diagnostic source가 아니며
   `PASS`는 detail을 전혀 노출하지 않는다.
10. Runtime-native subagent, Claude agent team, spec edit, unrelated refactor,
    commit, merge, push, cleanup, runtime config는 scope 밖이다.

## 위험

- 텍스트 `PASS`를 completion marker로 취급하면 SD-70을 우회한다. Liveness를
  exit 3으로 유지하고 exact completion harvest 전에는 row를 open으로 둔다.
- Shell/Python liveness가 drift할 수 있다. 같은 inspector CLI와 동일 verdict
  fixture를 두 surface 모두에 실행하고 6-field v1 grammar/exit code를 고정하며
  malformed/multiple record를 거부한다.
- Artifact resolve에는 symlink/TOCTOU 위험이 있다. Harvest 시 strict resolve로
  끝내지 않고 매 inspection에서 exact row worktree를 기준으로 resolve하고
  pipe metadata를 cross-check한다. Typed unreadable state를 내고 consuming
  stage가 자기 guard 아래에서 다시 열게 하며 cached content를 신뢰하지 않는다.
- Worker-authored blocker/diagnostic text는 크거나 민감할 수 있다. 기본값은
  fixed enum이며 detail은 explicit/bounded/labeled/success 불가로 제한한다.
  Oversized single-line, control, UTF-8 boundary를 검증한다.
- 큰/malformed JSONL은 ambiguity를 만들 수 있다. Bounded tail을 유지하고
  invalid UTF-8/JSON/envelope에서 fail closed하며 boundary를 테스트한다.
- Wait 문구 변경은 문자열 기반 테스트를 깰 수 있다. Exit code와 stable class
  token은 유지하고 human heading과 fixture만 갱신한다.
- 이 planning sandbox에서는 spec-read marker 경로가 read-only였다. Execute는
  source edit 전에 core/spec read marker와 파일별 write guard를 다시 성립시켜야
  하며 이 plan artifact를 guard evidence로 간주하면 안 된다.
- Phase-local rollback을 넓게 적용하면 기존 변경을 덮을 수 있다. 각 phase는
  focused gate에서 중단하고 execution log의 old block으로 해당 phase-owned
  file만 guarded `apply_patch` 복원한다. reset/checkout과 unrelated-file
  cleanup은 금지한다.

## 검증

`/home/Uihyeop/agent_setting-wt/codex-headless-context-parity`에서 assigned
source lineage를 기준으로 실행한다.

Guard 및 policy:

```sh
/home/Uihyeop/agent_setting/adapters/codex/bin/preflight.sh qa-policy thorough code
git status --short
git rev-parse HEAD
```

실행 가능한 파일별 write guard는 Phase 1-3 각 step 직전에 정확히 열거되어
있다. 각 파일 첫 수정 전에 실행해야 하며 이 최종 block은 대체 수단이 아니기
때문에 placeholder guard를 포함하지 않는다.

Targeted tests:

```sh
PYTHONPATH=utilities python3 utilities/codex_dispatch_terminal.test.py
python3 utilities/dispatch_parent_context_conformance.test.py
python3 adapters/codex/bin/dispatch-headless.sd45.test.py
python3 utilities/dispatch_registry.test.py
python3 utilities/dispatch_harvest.test.py
bash utilities/dispatch-wait.test.sh
bash utilities/dispatch-liveness.test.sh
python3 utilities/dispatch_progress.test.py
bash adapters/codex/bin/dispatch-headless.sd15.test.sh
```

Comparator regression(아래 override는 transient PID namespace 안에서 detached
launch를 의도적으로 시험하는 fixture에만 필요):

```sh
python3 adapters/claude/bin/dispatch-headless.sd45.test.py
AGENT_DISPATCH_ALLOW_NAMESPACED_SPAWN=1 bash adapters/claude/bin/dispatch-headless.sd15.test.sh
```

최종 scoped checks:

```sh
git diff --check
git diff -- adapters/codex/bin/dispatch-headless.py adapters/codex/bin/dispatch-liveness.py adapters/codex/bin/dispatch-harvest.py utilities/codex_dispatch_terminal.py utilities/dispatch-liveness.sh utilities/dispatch-wait.sh utilities/codex_dispatch_terminal.test.py utilities/dispatch_parent_context_conformance.test.py adapters/codex/bin/dispatch-headless.sd45.test.py utilities/dispatch_registry.test.py utilities/dispatch_harvest.test.py utilities/dispatch-wait.test.sh utilities/dispatch-liveness.test.sh
```

`utilities/dispatch_parent_context_conformance.test.py`가 deterministic capture
directory를 소유하고 negative sentinel scan을 내부에서 수행하므로 별도 shell
path는 필요 없다.

최종 기대 evidence:

- 모든 targeted 명령 exit 0.
- 모든 verdict의 wrapper stdout/stderr 및 receipt/liveness/wait/harvest capture에
  command/prior-agent/final-message/artifact-body sentinel이 0개다. Exact attempt
  log와 validated artifact에는 해당 sentinel이 실제로 남아 있다.
- Blocker/diagnostic detail은 explicit failure option에서만 required label로
  나타나고 ASCII/control/multibyte 경계에서 각 512 UTF-8 byte 이하다.
  `PASS`는 `blocker_reason=none`과 detail 0개이며 non-`none` blocker `PASS`는
  invalid다.
- V1 wire는 정확히 한 개의 6-field enum record이고 exit 0/2/3/4/64 동작이
  정의되며 열거된 legal tuple만 허용한다. Relative, over-broad,
  non-directory, escaped, shadow, missing, mismatched root는 모두 raw text 없이
  fixed `unsafe-root` tuple을 내고 artifact missing/outside-root는 각 distinct
  invalid tuple을 유지한다. Mixed-harness row는 Codex parser를 bypass한다.
- `PASS` liveness는 `COMPLETED`이지만 exact completion marker harvest 전까지
  routed row는 open 유지.
- Fail/blocked는 기존 exact failure note와 fallback behavior 유지.
- Lifecycle matrix는 real-wrapper `PASS`-open 및 `FAIL`/`BLOCKED`-closed
  transition을 증명한다. 동일 wrapper-shaped JSONL의 supplemental controlled
  open row가 current-row filtering을 완화하지 않고 failure liveness/wait를
  검증한다. 이름이 고정된 post-exit orphan regression은 precedence, exact
  row/note transition, idempotence, no breadth-close, raw terminal leakage 0개를
  증명한다.
- Scoped diff에 registry/Fleet/completion/fallback schema drift와 out-of-scope
  파일이 없음.

## 결정 지점

사용자에게 확인할 비가역 결정은 없다. 설계는 additive safe inspection view와
compatibility field를 사용하며 canonical registry, route, completion, artifact
계약을 변경하지 않는다.

## QA handoff

`qa-policy thorough code` 결과는
`assurance_scope=plan-check:selected-independent-pass:final-verify`, 선택 pass의
상한 2 deep + 2 fast reviewer, 최대 2 round다. Round 1과 round 2가 기록된
finding을 만들었다. Bounded owner assignment는 round-2 finding closure를 세 번째
독립 review가 아닌 correction으로 명시하고 English/Korean/checklist artifact
수정 뒤 구현을 승인했다. 동일 self-hosting runtime defect로 child dispatch가
불가능했기 때문에 implementation review와 final verify는 규정된 inline
fallback으로 수행했다. `_internal/metrics.md`에 이를 기록했고 independent
delegation은 주장하지 않는다.

## Review round 1 closure map

1. Bounded failure text: Phase 1.1은 fixed blocker enum, invalid
   `PASS`-with-detail, optional labeled 512-byte excerpt와 truncation 순서를
   정의한다. Phase 2.1/2.5는 receipt/harvest를 제한하며 Phase 1.2, 3.1, 3.4는
   oversized/multibyte/control/`PASS` 음성 case를 추가한다. 안전 불변조건 3/9와
   final evidence가 gate를 유지한다.
2. Artifact root/wire: Phase 1.1은 selected-row worktree +
   `artifact-root.sh`, pipe metadata cross-check, registry column 비변경, exact v1
   6-field grammar, enum/exit, caller decode rule을 고정한다. Phase 2.1-2.5가 이를
   연결하고 Phase 1.2/3.3/3.4가 linked worktree, missing/mismatched root, unsafe
   path, malformed wire, mixed harness를 검증한다.
3. Real Codex wrapper boundary: Phase 3.1은 모든 verdict에 대해 fake
   `codex exec --json`과 실제 foreground `dispatch-headless.py --start` entry를
   실행해 stdout/stderr/log/registry를 capture하고 log/artifact positive retention
   및 parent negative leakage를 증명한다. Phase 3.2는 supplemental이다.
4. Guard/rollback: Phase 1-3 모든 file에 exact pre-edit write command가 있고
   Verification placeholder는 제거됐다. 각 phase는 focused test gate와 해당
   phase-owned file만 대상으로 하는 guarded `apply_patch` rollback이 있다.

## 변경 이력

- 2026-07-22, review round 2 correction: 모든 artifact-state token과 legal
  wire/exit tuple을 고정하고 unsafe-root variant를 정규화했다. Real-wrapper
  transition evidence와 supplemental current/open failure liveness/wait
  evidence를 분리하고 named post-exit orphan-reconcile regression을 추가했으며
  negative capture scan을 deterministic conformance test 내부로 이동했다.

- 2026-07-22, review round 1: parent-visible worker-authored failure field를 모두
  bound하고 artifact-root authority와 inspector wire를 고정했다. Codex isolation
  proof를 real wrapper boundary로 옮기고 구체적 per-file guard, phase gate,
  rollback boundary, positive log/artifact retention assertion을 추가했다.
  Review가 baseline inconsistency를 발견하지 않아 `baseline_comparison.md`는
  변경하지 않았다.
