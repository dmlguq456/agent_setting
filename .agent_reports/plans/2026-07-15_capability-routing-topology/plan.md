# Capability routing topology — implementation plan

- Date: 2026-07-15
- Status: ready-for-spec-update
- Intensity: thorough
- Primary capability: `code-plan`
- Source worktree: `/home/Uihyeop/agent_setting-wt/capability-routing-topology`
- Base: `origin/main@68d90996`
- Spec significance: **SPEC-SIGNIFICANT** — `stage-dispatch`의 적용 범위, intensity 의미, main/worker 책임, adapter dispatch 계약을 바꾼다.

## 1. 결론

현재 계약은 “메인 세션은 오케스트레이터”와 `direct → quick → standard+` depth 모델을 이미 갖고 있다. 그러나 실행기는 사실상 `autopilot-code`의 고정 파이프에 최적화되어 있고, 나머지 entry capability는 prose 안에 서로 다른 stage 구조를 서술할 뿐 기계가 읽는 공통 토폴로지가 없다.

따라서 수정의 중심은 “모든 entry skill을 depth=2로 만든다”가 아니다. 아래 네 축을 분리하고, capability별 실행 토폴로지를 기계가 읽는 계약으로 승격하는 것이다.

1. `intensity`: 작업에 투입할 effort/assurance와 승격 수준
2. `topology`: inline, depth-1 one-shot, depth-1 conductor + depth-2 workers 중 어떤 형태로 실행할지
3. `worker_kind`: durable stage, bounded reviewer, map worker, resource runner 중 무엇인지
4. `transport`: headless, native subagent, detached OS process, 또는 검증된 fallback 중 무엇을 쓸지

사용자-facing 새 옵션은 추가하지 않는다. 사용자는 계속 capability와 intensity를 사용하고, topology/worker/transport는 capability registry와 route compiler가 파생한다.

## 2. 목표와 비목표

### 목표

- tracked/substantial 작업에서 메인 세션은 context owner, router, monitor, integrator 역할만 수행한다.
- 자잘하고 원자적인 작업은 `direct`로 메인 inline을 허용한다.
- 작은 tracked 작업은 `quick` depth-1 one-shot으로 메인 컨텍스트에서 분리한다.
- 명확한 규모·위험·자원·산출물 경계를 가진 `standard+` 작업은 capability별 토폴로지로 분사한다.
- depth=2는 “모든 phase”가 아니라 파일 기반 handoff가 완결되고 write ownership이 분리되는 durable worker에만 사용한다.
- route 판단, dispatch command, liveness, completion gate가 하나의 route record를 공유한다.
- 기존 진단의 smoke, detached lifecycle, report contract, global spawn cap을 같은 route/completion 체계에 연결한다.

### 비목표

- 모든 발화와 단일 파일 수정을 분사하지 않는다.
- 모든 entry capability를 `plan → execute → test → report` 네 칸에 억지로 맞추지 않는다.
- depth=3 이상을 열지 않는다.
- runtime-owned Codex config를 자동 수정하지 않는다.
- arbitrary shell execution 전체를 hook 하나로 완전히 통제한다고 주장하지 않는다.

## 3. 현재 상태 판정

### 이미 성립한 것

- `core/OPERATIONS.md §5.10`은 main을 context owner/router/orchestrator/integrator로 정의한다.
- intensity topology는 `direct=depth0`, `quick=depth1 one-shot`, `standard+=depth1 conductor → depth2 worker`로 선언되어 있다.
- `autopilot-code`는 `code-plan → code-execute → code-test → code-report`의 독립 sub-capability, write scope, role, jobs metadata, liveness가 가장 완성되어 있다.
- `autopilot-design`, `autopilot-draft`, `autopilot-lab`에는 standard+ stage-dispatch 문구가 이미 들어가 있다.
- `autopilot-spec`은 PRD authoring을 conductor-owned transaction으로 두고 scaffold만 선택적으로 depth=2로 보내는 의도적 비대칭 구조다.
- quick depth-1과 worker lifecycle 격리, distill/title 폭주 방지의 일부가 이미 구현돼 있다.

### 구조적 결손

- `capability-info`는 code에만 `pipeline_contract`, `stage_graph_contract`, `plan_policy`, `dispatch_contract`를 출력한다. 다른 entry capability는 대부분 `status=instruction-only`다.
- capability별 phase/stage/write scope/dependency가 prose에만 있어 main이 매번 해석한다.
- durable pipeline stage와 independent reviewer가 모두 “depth-2 worker”라는 이름 아래 섞여 있다.
- `utilities/dispatch-route.sh`는 model/harness 후보를 고를 뿐 capability topology를 만들지 않는다.
- dispatch wrapper는 긴 argv를 main이 직접 조립해야 하며 model 선택 오류가 worktree/artifact 검사 뒤에 드러난다.
- Codex headless preflight는 현재 primary checkout에서도 native skill discovery 실패로 막히고, linked worktree에서는 설치 projection의 symlink가 target worktree를 가리켜야 한다고 요구해 추가 실패한다.
- Codex 공식 hook 계약은 `PreToolUse`에서 conditional hard-deny 출력을 지원하지 않는다. 현재 local bridge의 `{"decision":"block"}`는 documented Codex deny contract가 아니므로 routing hard gate의 기반으로 사용할 수 없다.

### Runtime currentness evidence (2026-07-15)

- OpenAI Codex [Hooks documentation](https://learn.chatgpt.com/docs/hooks.md)은 `PreToolUse`가 `systemMessage`를 반환할 수 있다고 설명하지만 Claude식 `continue`, `stopReason`, `suppressOutput`은 지원하지 않으며 unsupported output field가 있으면 hook이 실패하고 tool call은 계속된다고 명시한다. 따라서 local `decision=block` 출력은 hard-deny 증거가 아니다.
- OpenAI Codex [Subagents documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents.md)은 native subagent의 `agents.max_threads`와 `agents.max_depth`를 runtime 설정으로 제공한다. 이는 harness가 등록하는 `codex exec` headless worker와 별도 표면이다.
- OpenAI Codex [Non-interactive mode documentation](https://learn.chatgpt.com/docs/non-interactive-mode.md)은 `codex exec`를 script/CI용 비대화형 실행 표면으로 정의한다. 본 계획의 registered headless transport는 이 표면을 사용한다.
- Local probe: `capability-info autopilot-code`만 pipeline/topology 필드를 노출했고, primary 및 linked worktree의 `headless --check`는 skill discovery/projection identity 문제로 실패했다. 구현 전 official docs 재확인과 local probe 재실행을 Phase 0 gate로 둔다.

## 4. 목표 실행 모델

### 4.1 메인 세션의 경계

메인 inline은 다음을 모두 만족하는 `direct`에만 허용한다.

- 결과가 하나의 원자적 outcome이다.
- 대상과 변경 범위가 이미 알려져 있다.
- spec/public API/shared contract 변경이 아니다.
- GPU, 장시간 process, bulk generation이 없다.
- 별도 산출물 handoff나 independent verification이 필요 없다.
- 한 번의 focused verification으로 종료할 수 있다.

하나라도 거짓이지만 durable stage 분할 기준에는 못 미치면 `quick` depth-1 one-shot으로 보낸다. 즉 애매한 작업은 inline이 아니라 quick 쪽으로 기운다.

다음 신호 중 하나라도 있으면 `standard+`로 승격한다.

- `resource_class ∈ {gpu, long-running, bulk-generation}`
- session과 분리된 process lifecycle이 필요함
- 서로 다른 write scope를 가진 durable output stage가 2개 이상
- metrics → figure/media → HTML/report처럼 3개 이상 산출물의 동기화가 필요함
- spec, public API, schema, shared contract를 변경함
- independent verifier/adversary가 completion condition임
- 작업 일부 실패 시 stage 단위 resume/retry가 필요함

파일 수나 시간 하나만으로 승격하지 않는다. 자동 관찰 가능한 신호와 capability별 의미 신호를 route record에 함께 남긴다.

### 4.2 depth와 worker kind

| Kind | Depth | 의미 | 기본 write 정책 |
|---|---:|---|---|
| `inline-direct` | 0 | 원자적 direct 작업 | main이 해당 원자 범위만 |
| `capability-owner` | 1 | quick one-shot 또는 standard+ conductor | quick은 scoped write, conductor는 통합·게이트만 |
| `pipeline-stage` | 2 | durable artifact/file handoff stage | registry에 선언된 class scope만 |
| `review-worker` | 2 | 독립 검토·반증·verification | read-only + verdict artifact |
| `map-worker` | 2 | 독립 source/file shard 분석 | shard output만, canonical merge 금지 |
| `resource-runner` | OS process | GPU/장기/bulk process | model depth와 별개, pid/log/run registry 소유 |

`pipeline-stage`와 `review-worker`를 metadata에서 반드시 구분한다. resource runner는 model session recursion이 아니므로 depth 숫자로 표현하지 않는다.

## 5. Capability별 권장 토폴로지

아래 표는 entry capability에 depth=2를 일괄 적용하지 않는 초기 registry 기준이다. 실제 구현 전에 `stage-dispatch` spec update에서 확정한다.

| Capability | Quick | Standard+ topology | Depth-2 기본 사용 |
|---|---|---|---|
| `autopilot-apply` | apply+focused compile one-shot | conductor → apply(single writer) → verify(read-only) → handback/human gate | 조건부 2-stage |
| `autopilot-code` | 기존 quick one-shot | plan → execute → test → report | 필수 staged |
| `autopilot-design` | 한 worker 안에서 필요한 phase만 | init/confirm은 conductor; refs → build(tokens+components) → visual review → handoff로 묶음 | 필수 staged, phase별 6분사 금지 |
| `autopilot-draft` | strategy+draft+focused review one-shot | material/strategy → draft production → review/refine → finalize; user pause는 conductor | 조건부 staged |
| `autopilot-lab setup` | spec+scaffold+smoke one-shot | setup contract는 conductor; scaffold worker → smoke verifier; full run은 detached resource runner | 조건부 stage + resource |
| `autopilot-lab eval` | 작은 checkpoint eval one-shot | eval/metrics → media/playback → report → independent verify → spec/note sync | 필수 staged |
| `autopilot-note` | 기본 경로 | source scan/analyze는 map workers 가능; canonical routing/apply/digest는 owner 단일 writer | reviewer/map만, 일반 stage pipeline 없음 |
| `autopilot-refine` | 기본 경로 | preview/snapshot/apply는 하나의 transactional owner; fact/style review만 read-only workers | reviewer만 기본 |
| `autopilot-research` | 작은 survey one-shot | search/retrieval maps → analysis/synthesis → report → claim verification | 필수 map+staged |
| `autopilot-ship` | 기본 경로 | release setup owner + read-only security/release review; 실제 deploy는 human external gate | reviewer만 기본 |
| `autopilot-spec` | 작은 update one-shot | PRD transaction은 depth-1 conductor 소유; research/review/scaffold만 선택적 depth-2 | 비대칭·선택적 |

핵심 보정은 두 가지다.

- design/draft처럼 phase가 많아도 모든 phase를 세션 하나씩 열지 않고 write ownership과 dependency를 기준으로 묶는다.
- spec/refine/note/ship처럼 transaction 또는 human gate 중심인 capability는 reviewer/map worker만 쓰고 가짜 four-stage pipeline을 만들지 않는다.

## 6. 기계가 읽는 topology source of truth

### 6.1 권장 구조

portable capability catalog와 분리된 실행 전용 registry `capabilities/topologies.json`을 둔다. 기존 `harness-manifest.json`은 identifier/dependency/role catalog를 유지하고, topology validator가 두 파일의 entry capability 집합이 정확히 일치하는지 검사한다. `manifest.json`에는 topology digest와 생성된 요약만 포함한다.

이 분리는 capability metadata와 execution graph의 역할을 나누며, 같은 필드를 두 곳에 중복하지 않는다.

경량화/parity 계약과의 결합 규칙:

- topology graph 본문을 각 adapter의 Skill frontmatter나 always-loaded bootstrap에 복제하지 않는다.
- generated Skill에는 기존 portable source pointer만 유지하고, topology는 `capability-info`/`preflight route`가 on demand로 읽는다.
- Claude, Codex, OpenCode는 sibling realization으로 각각 검증하며 한 adapter의 통과를 다른 adapter의 completion proxy로 쓰지 않는다.
- topology 추가 후 `context-footprint --strict`의 checked baseline과 5% 성장 한도를 통과해야 한다.

각 capability/mode recipe는 최소한 다음을 선언한다.

```json
{
  "capability": "autopilot-lab",
  "mode": "eval",
  "topology_class": "staged",
  "promotion_signals": ["gpu", "bulk-generation", "artifact-fanout"],
  "quick": {"owner_depth": 1, "max_depth": 1},
  "standard_plus": {
    "owner_depth": 1,
    "nodes": [
      {
        "id": "eval",
        "kind": "pipeline-stage",
        "depends_on": [],
        "role": "fast implementer",
        "inputs": ["checkpoint", "eval-spec"],
        "outputs": ["run.json", "metrics.jsonl"],
        "write_scope": ["eval/**", "run.json", "metrics.jsonl"],
        "resource_class": "gpu",
        "completion_gate": "smoke-bound-eval"
      }
    ]
  }
}
```

validator는 다음을 fail-closed로 검사한다.

- 모든 entry capability와 mode의 recipe 존재
- depth ≤ 2, quick depth-2 금지
- DAG cycle 없음
- pipeline stage의 input/output/write scope 선언
- 동시에 실행 가능한 node 간 write scope overlap 없음
- reviewer는 read-only, map worker는 canonical merge write 금지
- resource runner가 model depth를 사용하지 않음
- completion gate와 verifier command가 존재
- generated capability catalog/adapter projection의 topology digest 일치

### 6.2 route record

`utilities/capability-route.py`가 registry와 관찰 신호를 읽어 immutable route record를 만든다. main은 이 파일을 만든 뒤 dispatch한다.

필수 필드:

- capability, mode, intensity, topology class, owner depth
- promotion signals와 source(`observed|declared|capability-default`)
- worker node graph, role, write scope, resource class
- selected transport와 eligibility evidence
- model route trace
- inline enum과 근거 필드
- registry digest, source commit, route hash
- completion gates

inline enum은 자유 텍스트 대신 아래로 제한한다.

- `atomic-direct`
- `nonseparable-transaction`
- `runtime-unavailable`
- `dispatch-infra-self-modification`
- `user-restricted`

`atomic-direct`는 예외가 아니라 정상 route다. `standard+`에서 inline enum을 쓰면 metrics와 audit 대상이 된다.

## 7. Dispatch UX와 enforcement

### 7.1 한 명령 경로

main이 긴 argv를 조립하지 않도록 다음 고수준 경로를 만든다.

```text
preflight.sh route --capability <name> --mode <mode> --intensity <level> [signals...]
preflight.sh dispatch-route --route <route.json> --node <owner-or-stage>
```

`dispatch-route`가 low-level wrapper 인자를 생성하고 등록·launch한다. model role/profile/worker role/depth/parent/write scope는 registry에서 가져온다. exact model과 reasoning은 기존 model router가 current runtime eligibility를 확인해 materialize한다.

low-level `dispatch-headless.py`는 호환·테스트용으로 남기되, 일반 skill 문서에서는 고수준 경로만 사용한다.

`--quick`이라는 모호한 silent-inherit 옵션 대신 이름 있는 `quick-owner` preset을 route compiler 내부에 둔다. preset도 exact model resolution과 route trace를 기록한다.

### 7.2 validation 순서

1. CLI schema와 mutually-exclusive model/preset 인자
2. topology route hash와 node 존재
3. intensity/depth/parent/write scope
4. runtime/skill/plugin projection eligibility
5. worktree/artifact root
6. registry append와 process launch

현재처럼 필수 model 선택이 worktree 검사 뒤에 실패하지 않게 한다.

### 7.3 Codex runtime projection 선결 수정

현재 `headless --check <task-worktree>`는 installed `$CODEX_HOME` symlink가 task worktree를 직접 가리키는지 검사한다. 이는 main에 설치된 projection을 쓰는 정상 linked worktree도 실패시킨다.

두 경로로 분리한다.

- 일반 작업: installed projection source는 primary harness로 유지하고, target worktree와의 required contract/digest compatibility만 검사한다.
- harness self-modification: target worktree에서 ephemeral `CODEX_HOME` projection을 먼저 만들고 그 home을 검사·사용한다.

plugin-only skill discovery도 `skills_linked=0`을 정상으로 볼 수 있도록 installed plugin 상태를 실제로 probe해야 한다. projection exact-target check와 capability discoverability check를 분리한다.

### 7.4 hard gate의 현실적 경계

Codex 공식 hook surface는 `PreToolUse`의 conditional tool denial을 제공하지 않는다. 따라서 `decision=block` JSON에 routing enforcement를 맡기지 않는다.

hard gate는 repo-owned 실행 표면에서 구현한다.

- dispatch, lab run, detached run, report finalize 등 표준 wrapper가 valid route/completion marker 없이는 실행하지 않음
- generated skill은 raw long-running command 대신 wrapper만 안내
- conformance test가 raw bypass 명령을 projection에서 탐지
- runtime prefix rule은 무조건 금지 가능한 위험 command에만 사용하고 marker 조건부 routing에는 사용하지 않음

arbitrary shell 전체의 우회를 OS 수준에서 막는다고 주장하지 않는다. 지원 범위 밖 우회는 audit violation으로 남긴다.

## 8. 기존 진단 6건의 통합 수정 방향

### 8.1 인라인 편향

- `WORKFLOW §0.3`의 자유 서술을 route record로 대체한다.
- 자동 관찰 가능한 promotion signal은 route compiler가 직접 채운다.
- standard+ node를 raw inline 실행하려면 enum exception과 evidence가 필요하다.
- long/GPU/bulk wrapper는 valid route 없으면 시작하지 않는다.
- capability catalog에 topology 요약을 생성해 agent가 prose 여러 파일을 추적하지 않게 한다.

### 8.2 장기 작업과 세션 생명주기 분리

`utilities/launch-detached.sh`와 run registry를 만든다.

- `setsid + nohup` 기본 fallback, user-systemd가 검증된 환경에서는 adapter가 더 강한 backend를 선택 가능
- process group, PID, `/proc` start time, command hash, cwd, log, started_at, status 기록
- PID 재사용을 막기 위해 PID 단독이 아니라 start time까지 검증
- `run-status`, `run-tail`, `run-stop`을 제공하고 watcher는 session이 아니라 registry에 재부착
- model worker의 jobs.log와 OS resource runner registry를 분리하되 route id로 연결

### 8.3 전역 스폰 상한

이미 distill/title에 들어간 개별 cap을 공용 `model-worker-governor`로 승격한다.

- repo-owned headless/title/distill/loop spawn이 하나의 atomic lease pool을 사용
- total cap과 class cap, rolling start budget, kill switch, stale lease recovery 제공
- dispatch contract의 총 동시성 5를 실제 lease로 강제
- plugin/runtime copy는 canonical library에서 생성하고 hash parity를 검사; package 때문에 symlink가 불가능한 곳은 generated copy로 유지
- native Codex subagents는 공식 `agents.max_threads/max_depth` 경계가 별도이므로 recommended config fragment와 preflight disclosure로 관리하고, runtime-owned config를 자동 편집하지 않음

### 8.4 산출물 계약

report Markdown과 HTML을 서로 따로 조립하지 않고 하나의 `report_manifest.json`에서 생성한다.

verifier를 다음까지 확장한다.

- audio ↔ waveform ↔ spectrogram ↔ playback row 1:1
- summary statistics가 Markdown과 실제 사용자-facing HTML 양쪽에 존재
- 48 kHz/full-band/house panel parameters 일치
- media hash와 report link binding
- representative visual review evidence
- claim/range evidence와 figure semantic manifest 유지

`report.html`이 completion gate를 통과하지 않으면 REPORT.md가 완전해도 eval 완료로 보지 않는다.

### 8.5 mandatory smoke

- `autopilot-lab setup`의 smoke를 optional에서 default required로 바꾼다.
- smoke attestation은 config hash, code hash, checkpoint/input signature, command, exit status를 기록한다.
- full run/eval wrapper는 일치하는 passed smoke attestation 없이는 시작하지 않는다.
- config/code가 바뀌면 stale smoke를 거부한다.
- 1-batch가 불가능한 mode는 registry에 별도 최소 probe contract를 선언하며 자유로운 skip은 허용하지 않는다.

### 8.6 cwd와 spec-sync nudge

- route/dispatch/run wrapper는 absolute cwd와 canonical artifact root만 저장한다.
- guarded operation은 현재 cwd와 route cwd가 다르면 조용한 경고가 아니라 structured failure를 낸다.
- 일반 read-only shell에는 전역 경고를 주입하지 않는다.
- spec-sync nudge는 standalone 숫자를 identifier로 보지 않는다.
- `key=value`, prefix가 있는 requirement id, version/unit가 결합된 token만 비교하고 `«3»`, `«1»` 회귀 fixture를 추가한다.

## 9. 구현 phase

### Phase 0 — coordination과 spec update

1. 진행 중인 `pocock-parity-efficiency`가 merge될 때까지 projection/core/capability catalog 편집을 시작하지 않는다.
2. merge 후 이 worktree를 최신 main에 rebase하고 overlap census를 다시 기록한다.
3. `stage-dispatch` PRD를 v9로 update하거나 후속 component spec을 만들고 다음 결정을 고정한다: topology axes, capability matrix, route record, Codex hook limitation, runtime projection source/target 분리.
4. current official Codex hooks/subagents/non-interactive docs를 다시 확인하고 날짜와 지원/미지원 경계를 기록한다.

Gate: spec decision IDs와 acceptance criteria가 없으면 source implementation 금지.

### Phase 1 — topology registry와 validator

1. `capabilities/topologies.json` schema와 loader/validator를 구현한다.
2. 10개 entry capability와 mode recipe를 채운다.
3. capability catalog와 `capability-info`에 topology class, max depth, node ids, completion gates를 생성한다.
4. exact coverage, DAG, write overlap, quick-depth2, reviewer read-only 테스트를 추가한다.

Gate: adapter나 dispatch 동작을 바꾸기 전에 registry snapshot tests가 green이어야 한다.

### Phase 2 — route compiler와 Codex transport readiness

1. immutable route record compiler를 구현한다.
2. `preflight route`와 `dispatch-route` 고수준 명령을 추가한다.
3. low-level wrapper validation 순서를 앞당긴다.
4. linked worktree projection source/target 문제와 plugin-only skill discovery를 수정한다.
5. normal worktree와 harness self-modification ephemeral projection fixture를 각각 검증한다.

Pilot: 기존 `autopilot-code` 표준 파이프를 새 route record로 한 번 완주한다.

### Phase 3 — capability rollout

한 번에 전 capability를 바꾸지 않는다.

1. `autopilot-lab eval` — 사용자 사고와 가장 직접 관련된 pilot
2. `autopilot-design`, `autopilot-draft`, `autopilot-research` — 기존 staged prose를 registry로 이전
3. `autopilot-spec`, `autopilot-refine`, `autopilot-note`, `autopilot-ship` — transactional/reviewer/map topology 검증
4. `autopilot-apply`, `autopilot-lab setup` — mutation/smoke/human gate 연결

각 capability는 실제 one-shot 1회와 standard+ 1회를 통과한 뒤 다음 capability로 이동한다.

### Phase 4 — resource lifecycle, smoke, report completion

1. detached resource runner와 run registry
2. smoke hash attestation과 full-run gate
3. report manifest single source와 HTML/media verifier
4. lab completion gate 연결

이 phase는 model dispatch와 OS process lifecycle을 섞지 않는 것이 핵심이다.

### Phase 5 — global governor와 보조 마찰

1. distill/title/headless/loop 공용 governor
2. dispatch total cap=5 강제와 class caps
3. runtime config disclosure for native subagents
4. absolute cwd contract
5. spec-sync token parser 수정

### Phase 6 — enforcement rollout

1. report-only mode로 route mismatch를 계측
2. standard+ raw bypass와 missing completion marker를 warning으로 수집
3. false positive가 닫힌 wrapper 표면만 deny로 승격
4. adapter별 지원/미지원/감사-only 경계를 문서화

## 10. 예상 변경 표면과 동시 세션 충돌

### parity 세션과 겹치는 표면

- `core/CONVENTIONS.md`, `core/DESIGN_PRINCIPLES.md`
- `capabilities/README.md`
- `adapters/{claude,codex,opencode}` bootstrap
- Codex/OpenCode skill sync와 generated projections
- adaptation boundary와 skill conformance

이 파일들은 parity merge 후 rebase 전에는 수정하지 않는다. generated projection을 수동 편집하지 않는다.

### routing 구현의 주 소유 표면

- `capabilities/topologies.json` 또는 spec에서 확정한 동등 registry
- `tools/capability_topology.py`와 tests
- `utilities/capability-route.py`와 tests
- adapter preflight/dispatch wrapper
- `utilities/model-worker-governor.*`
- detached runner/run registry
- lab smoke/report verifier
- capability portable sources → generator → adapter projection

## 11. 검증 matrix

### Registry/route

- 모든 entry capability × mode × `direct|quick|standard+` snapshot
- direct all-predicate, ambiguous→quick, promotion-any→standard+ property tests
- quick depth-2 reject, depth-3 reject
- DAG cycle/write overlap/missing gate reject
- spec의 PRD transaction이 forced four-stage가 아님
- note/refine/ship이 mutating depth-2 pipeline을 강제하지 않음

### Runtime/dispatch

- primary projection + linked task worktree headless check
- harness self-modification ephemeral projection check
- plugin-only and native-symlink skill discovery modes
- missing model/preset이 filesystem work 전에 즉시 실패
- one route command이 jobs row, prompt, model trace를 동일 hash로 생성
- liveness/harvest가 route node를 보존

### Concurrency/lifecycle

- 50개 동시 launch 요청에서 active lease가 total cap을 넘지 않음
- class cap과 rolling budget 동시 적용
- kill switch에서 registry mutation/model spawn 0
- stale lease reclaim과 PID reuse 방지
- parent session 강제 종료 뒤 detached resource runner가 계속 살아 있고 재부착 가능

### Lab/report

- stale/missing smoke attestation이 full run 차단
- passed smoke와 동일 hash만 full run 허용
- HTML 통계 누락, media 1:1 불일치, house parameter 불일치 각각 fail
- Markdown과 HTML이 동일 report manifest에서 재생성됨

### Regression

- portable guards
- capability/manifest generator `--check`
- four-tree skill conformance와 portable capability exact coverage
- context-footprint checked baseline/strict budget
- Codex/OpenCode skill/plugin/command projection checks
- adaptation boundary
- Fleet dispatch tests
- doctor/runtime projection
- `git diff --check`

drill은 자동 실행하지 않는다. 구현 완료 후 E2E가 필요할 때 `preflight.sh loop-info drill`을 보고 사용자가 실행 범위를 정한다.

## 12. rollout과 rollback

- registry와 route compiler는 처음 report-only로 도입한다.
- 기존 low-level dispatch는 compatibility path로 한 release window 유지한다.
- capability 단위 feature flag로 rollout한다.
- route mismatch, fallback, inline exception, dispatch overhead를 계측한다.
- false positive가 발생하면 capability flag만 되돌리고 registry/trace는 보존한다.
- generated projection은 source+generator commit 단위로 되돌린다.

## 13. 완료 기준

다음이 모두 성립해야 “분사 체계를 잡았다”고 판단한다.

1. main이 substantial capability work의 실행 명령을 수동 조립하지 않는다.
2. 모든 entry capability의 토폴로지를 한 catalog에서 볼 수 있다.
3. not-all-depth2 비대칭이 validator로 보존된다.
4. quick은 one-shot, standard+는 capability recipe, direct만 atomic inline이다.
5. code 외 최소 lab/design/draft/research에서 실제 route-based 분사가 완주한다.
6. linked worktree에서 Codex headless preflight가 정상 작동한다.
7. long run은 session 종료와 독립이고 smoke hash에 묶인다.
8. report HTML/media contract가 completion을 fail-closed로 막는다.
9. repo-owned model spawn이 공용 governor 상한을 넘지 않는다.
10. adapter별 미지원 경계를 과장 없이 보고한다.
