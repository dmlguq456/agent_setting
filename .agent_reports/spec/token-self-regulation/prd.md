# Token Self-Regulation — Spec (PRD)

> mode: **library + cli + runtime hook + isolated experiment** · 작성 2026-07-13 · v2
> 컴포넌트: `agent_setting`의 세션 단위 token/context 계측과 안전한 출력 자기조절. 루트 `spec/prd.md`(Unified Memory System)와 독립이며 이 폴더가 자체 SoT다.
> 입력: v1 snapshot(`_internal/versions/v1/prd.md`) + `.agent_reports/research/token-self-regulation/` + Phase 0–1 구현·검증 결과.

## 0. 한 줄

**Phase 2는 token-budget hook의 실제 호출·무주입·directive UTF-8 byte와 런타임 누적 counter 증가를 서로 다른 관측량으로 bounded XDG aggregate에 기록하고, Phase 3는 production hook을 그대로 둔 채 deterministic offline forecast와 격리된 control/static/dynamic paired experiment만 수행한다. 어떤 단계도 input pruning, RL, model effort, intensity, dispatch, QA 또는 필수 검증을 변경하지 않는다.**

Phase 0–1은 구현 완료 상태다. v2의 구현 범위는 Phase 2 회계·progressive disclosure와 Phase 3 실험 계약까지이며, 동적 정책의 production 채택은 실험 gate와 사용자의 명시적 채택 결정 뒤 별도 spec/code cycle로 남긴다.

## 1. 배경과 문제

v1은 active context와 session cumulative counters를 분리하고, `tight|critical` band 진입에서만 240 UTF-8 bytes 이하 directive를 한 번 주입했다. 다음 위험은 아직 닫히지 않았다.

1. hook invocation 자체와 0-byte 경로가 회계되지 않으면 재주입 tax의 denominator가 없다.
2. exact directive bytes, 모델 tokenization, 런타임 session counter는 서로 다른 관측량이다. 이를 하나의 “token savings” 또는 billing cost로 합치면 거짓 정밀도가 생긴다.
3. static threshold보다 나은 동적 정책인지 알려면 같은 workload를 control/static/dynamic으로 짝지어 비교해야 한다. production hook에서 먼저 실험하면 안전·품질 불변식을 검증하기 전에 사용자 세션을 바꾼다.

따라서 v2는 **계측 계약을 먼저 고정하고, dynamic policy는 offline forecast + isolated experiment로만 평가**한다.

## 2. Runtime currentness와 유지 경계

### 2.1 이미 구현된 Phase 0–1

- shared parser가 active context와 cumulative input/cache/output/reasoning/total counter를 분리한다.
- Codex는 exact session rollout만 읽고, missing/stale/malformed/ambiguous/decreasing counter는 `unknown|degraded`로 fail-open한다.
- `normal|unknown|native|same-band`는 token-budget directive contribution이 정확히 0 byte다.
- `tight|critical` 신규 진입만 canonical 1-line directive를 낸다.
- `$CODEX_HOME/config.toml`, credentials, transcripts, runtime session DB는 쓰지 않는다.

### 2.2 v2 production boundary

- Phase 2 accounting은 관측과 on-demand reporting만 추가한다. Phase 1 static policy의 threshold, directive 의미, transition-only 동작은 바꾸지 않는다.
- Phase 3 dynamic candidate는 production `UserPromptSubmit` hook에서 **항상 disabled**다.
- dynamic candidate는 offline trace replay와 명시적 isolated experiment runner에서만 실행한다.
- gate가 통과해도 evaluator의 최고 verdict는 `eligible_for_user_review`다. 자동 채택·자동 config 변경·production activation은 없다.

### 2.3 Codex/adapter 지원 경계

- Codex runtime cumulative counters는 관측 가능한 session denominator지만 invoice, API billing ledger 또는 directive 귀속 counter가 아니다.
- exact model tokenizer가 실제 emitted payload에 대해 runtime/model/version과 함께 제공되지 않으면 directive token count는 `unknown`이다.
- component PRD는 `spec/token-self-regulation/prd.md`가 SoT다. 현재 Codex flat spec-read preflight가 component path를 승인하지 못하면 actual read evidence를 남기고 unsupported gate로 보고하되, 다른 spec을 대신 읽어 승인으로 위장하지 않는다.

## 3. 범위

### 3.1 Phase 2 — 재주입 회계

#### 3.1.1 관측 단위

token-budget helper를 호출한 한 번의 `UserPromptSubmit` lifecycle을 `hook_invocation` 1회로 센다. 회계 대상은 hook 전체 additional context가 아니라 **token-budget component가 기여한 directive 부분만**이다.

| 결과 | 정의 |
|---|---|
| `zero_injection` | token-budget component의 최종 contribution이 정확히 빈 byte sequence. normal/unknown/native/same-band/degraded/timeout/error fail-open을 포함한다. |
| `emission` | token-budget component가 non-empty canonical directive를 contribution으로 반환했다. |

```text
hook_invocations = zero_injections + emissions
directive_utf8_bytes_total = Σ len(emitted_directive.encode("utf-8"))
zero_injection의 directive bytes = 0
```

`directive_utf8_bytes`는 transport JSON escaping, wrapper metadata, stdout newline을 제외하고 실제 hook context에 삽입되는 directive 문자열의 UTF-8 byte 길이다. aggregate에는 content 본문을 저장하지 않고 canonical directive id만 허용한다.

#### 3.1.2 bounded XDG aggregate

기본 위치:

```text
${XDG_STATE_HOME:-$HOME/.local/state}/agent-harness/token-budget/accounting/
  <sha256(session-id)[:32]>.json
```

session id 원문, prompt, response, transcript, directive 본문은 저장하지 않는다. 파일 하나는 고정 schema의 session aggregate이며 per-turn journal이 아니다.

```yaml
accounting_version: 1
adapter: codex|claude|opencode|portable
session_digest: <32 hex>
first_observed_at: <ISO-8601>
last_observed_at: <ISO-8601>
hook_invocations: <non-negative int>
zero_injections: <non-negative int>
emissions: <non-negative int>
zero_reason_counts:
  normal: <int>
  unknown: <int>
  native: <int>
  same_band: <int>
  degraded: <int>
  timeout_or_error: <int>
directive_utf8_bytes_total: <int>
directive_utf8_bytes_max: <int>
observed_session_token_samples: <int>
observed_session_total_tokens_first: <int|null>
observed_session_total_tokens_last: <int|null>
observed_session_token_delta_monotonic: <int>
counter_decrease_events: <int>
unavailable_token_samples: <int>
```

Bound:

- session file 하나는 8 KiB 이하, directory는 최근 256 session file·총 2 MiB 이하를 동시에 만족한다.
- update는 기존 transition state와 같은 atomic replace + bounded lock을 사용한다.
- bound 초과 시 가장 오래된 aggregate부터 prune하고, prune/write/lock 실패는 hook을 막지 않고 회계만 `degraded`로 둔다.
- aggregate pruning은 runtime session/transcript나 repo artifact를 지우지 않는다.

#### 3.1.3 monotonic observed session token delta

`session_total_tokens`는 runtime이 같은 exact session에 보고한 cumulative counter만 받는다.

```text
첫 valid sample: baseline만 저장, delta += 0
current >= last_trusted: delta += current - last_trusted; last_trusted = current
current < last_trusted: delta 변화 없음; last_trusted 유지; counter_decrease_events += 1
missing/unsupported: delta 변화 없음; unavailable_token_samples += 1
```

이 값은 hook invocation 사이에 runtime cumulative counter가 단조 증가한 **관측 차이**다. directive가 야기한 token 수, 절감량, invoice cost 또는 billing savings가 아니다. fork/subagent는 session digest가 달라 별도 aggregate를 가진다. parent/child 합산은 하지 않는다.

#### 3.1.4 exact bytes와 token counters 분리

- `directive_utf8_bytes_*`는 exact payload bytes다.
- `observed_session_*tokens*`는 runtime cumulative counters다.
- 둘을 bytes-per-token 상수, 문자 수, 언어 휴리스틱으로 변환하지 않는다.
- actual payload에 대한 exact tokenizer가 runtime/model/version 식별자와 함께 검증된 경우에만 optional `directive_exact_tokens`를 기록한다. 그렇지 않으면 필드를 생략하거나 `null`로 둔다.
- 어떤 production CLI/Fleet/report도 이 둘의 차이를 `savings`, `net savings`, `cost`, `billing`, `ROI`로 이름 붙이지 않는다.

### 3.2 Phase 2 — progressive disclosure

| Layer | 자동 주입 | 내용 |
|---|---:|---|
| L0 zero | 0 bytes | normal/unknown/native/same-band/degraded/failure. 회계 설명도 넣지 않는다. |
| L1 essential | transition에서만 | 기존 canonical tight/critical 1-line directive, 각각 240 UTF-8 bytes 이하. required work·intensity/dispatch·tools/tests·safety·input context 불변 의미만 유지한다. |
| L2 diagnostic | 자동 주입 없음 | `kv|json` 또는 accounting report 요청 시 aggregate counters와 degradation reason을 노출한다. |
| L3 experiment | 자동 주입 없음 | candidate manifest, paired results, bootstrap evidence, adoption decision은 experiment artifact에서만 읽는다. |

Phase 2 구현은 L1에 accounting schema, metric 설명, experiment 규칙 또는 긴 safety 목록을 추가하지 않는다. 중복 의미는 canonical directive/portable invariant를 참조하고 supplement는 on-demand 파일로만 둔다.

### 3.3 Phase 3 — deterministic offline forecast candidate

candidate id는 `offline-forecast-v1`이다. production hook과 분리된 pure function이며 입력 trace와 frozen manifest가 같으면 byte-identical decision sequence를 내야 한다.

허용 record는 content-free telemetry뿐이다.

- `context_used_pct`, `context_window_tokens`
- 직전 최대 3개의 non-decreasing context percentage increment
- monotonic observed session token delta sample
- current static band, turns since last candidate emission
- cumulative hook invocation/emission/directive byte counters

단, `offline-forecast-v1`의 **decision feature**는 `context_used_pct`, 최근 percentage increment, current static band, target-band episode latch뿐이다. window/token delta/accounting counters는 replay integrity와 report용이며 decision을 바꾸지 않는다. valid non-negative increment가 하나도 없으면 history insufficient다.

```text
step = median(last up to 3 non-negative context_used_pct increments)
forecast_pct = min(99, current_context_used_pct + step)
if sample history is insufficient or any required signal is unknown/degraded:
    decision = static-equivalent/no-early-emission
elif forecast crosses critical before observed critical and critical not emitted in this episode:
    decision = emit canonical critical directive in the isolated arm
elif forecast crosses tight before observed tight and tight not emitted in this episode:
    decision = emit canonical tight directive in the isolated arm
else:
    decision = zero
```

candidate는 새로운 directive 문구를 생성하지 않고 v1 canonical directive만 선택한다. target-band episode latch는 해당 threshold에 대한 첫 forecast crossing에서 닫히고, observed와 forecast가 모두 threshold 아래인 valid sample이 들어온 뒤에만 다시 열린다. 따라서 early emission 뒤 실제 band transition의 duplicate를 억제하고 band별 최대 emission 수를 static보다 늘리지 않는다. coefficient fitting, stochastic sampling, online update, reward learning, RL은 없다. threshold, episode rule, candidate code hash, fixture hash는 manifest에 고정한다.

offline replay는 **행동 forecast/screening**일 뿐 모델 출력 품질이나 token saving을 증명하지 않는다. 채택 증거는 isolated paired experiment에서만 만든다.

### 3.4 Phase 3 — paired control/static/dynamic experiment

세 arm은 production hook 밖의 isolated runner에서 같은 workload를 실행한다.

| Arm | 정책 |
|---|---|
| `control` | token-budget directive contribution 항상 0 byte |
| `static` | v1 70/85% transition-only policy |
| `dynamic` | frozen `offline-forecast-v1`; canonical directive만 사용 |

complete paired sample은 동일한 `workload_id`, prompt/artifact hash, exact model/runtime/config, reasoning effort, intensity, dispatch/depth, QA/required checks, rubric version을 가진 control/static/dynamic triplet이다. arm 순서는 workload별 counterbalanced하며 runtime seed가 있으면 동일 seed를 기록한다. 하나라도 missing/degraded counter, config mismatch, required output 누락이면 그 triplet은 invalid이고 sample count에 넣지 않는다.

Evaluator input/output의 단일 계약은 `experiment_contract.md`가 소유한다. evaluator는 계산만 하는 deterministic program이며 production hook이나 runtime config를 수정하지 않는다.

## 4. 결정과 불변식

### TSR-1 — TSR-7 (v1 유지)

1. active context와 cumulative session counters는 분리된 exact-session signal이다.
2. native budget는 validated explicit opt-in만 인정하며 runtime config는 read-only다.
3. token pressure는 intensity, routing, model role/effort, stage/depth/dispatch, verification rigor를 바꾸지 않는다.
4. safety/security/validation/error handling/accessibility와 required guard는 불가침이다.
5. transcript/source/research/plan/input context reduction은 off다.
6. production reinjection은 static transition-only다.
7. missing/stale/malformed/ambiguous/decreasing signal은 추정 없이 fail-open한다.

### TSR-8 — 회계는 관측이지 절감·비용 주장이 아니다

hook count, zero/emission count, exact directive bytes, monotonic runtime counter delta를 별도 필드로 보존한다. 인과 귀속, savings, billing cost를 파생하지 않는다.

### TSR-9 — exact tokenizer 없이는 token 수를 추정하지 않는다

bytes-to-token heuristic, 평균 chars/token, 다른 모델 tokenizer 대입은 금지한다. exact tokenizer provenance가 없으면 directive token count는 unknown이다.

### TSR-10 — 회계 state는 bounded·content-free·fail-open이다

회계는 XDG의 hashed-session aggregate만 사용하며 prompt/response/directive 본문을 저장하지 않는다. 회계 실패가 hook 또는 사용자 작업을 실패시키지 않는다.

### TSR-11 — progressive disclosure는 자동 prompt tax를 늘리지 않는다

L0/L1만 production hook에 존재한다. L2/L3는 요청·실험 artifact로만 열며 normal/unknown/native/same-band의 0-byte 계약을 보존한다.

### TSR-12 — dynamic policy는 실험 격리 상태다

dynamic candidate는 offline/isolated runner에서만 실행한다. production activation flag, 자동 rollout, runtime config mutation을 추가하지 않는다.

### TSR-13 — 정책 실험도 작업 계약을 바꾸지 않는다

control/static/dynamic의 input, model effort, intensity, dispatch/depth, QA, required tools/checks는 동일하다. input pruning, RL, online learning, safety/quality gate 완화는 모든 arm에서 금지한다.

### TSR-14 — evaluator는 채택하지 않는다

evaluator는 `insufficient|reject|eligible_for_user_review`만 반환한다. 최종 채택은 증거를 본 사용자의 명시적 `adopt` 결정과 후속 autopilot-spec/autopilot-code cycle을 요구한다.

## 5. Phase 3 채택 gate

모든 조건을 동시에 만족해야 `eligible_for_user_review`다.

1. **Minimum paired samples**: valid complete triplet `n >= 30`. 둘 이상의 workload stratum을 선언했다면 각 stratum `n >= 10`도 만족한다.
2. **Data integrity**: included triplet의 arm config/hash가 일치하고 runtime cumulative counters가 단조·available이다. exclusion reason과 count를 공개한다.
3. **Safety/required checks**: 세 arm 모두 required checks와 safety/security/data-loss/accessibility gate가 100% pass한다. 한 건의 hard failure도 허용하지 않는다.
4. **Quality tolerance**: 사전 고정된 `[0,1]` rubric에서 dynamic-control 및 dynamic-static paired quality difference의 95% bootstrap lower bound가 각각 `>= -0.02`이고 hard-regression sample이 0건이다.
5. **Paired bootstrap savings confidence**: sample별 runtime metric을 `Δsession_total_tokens_arm`으로 두고, `control - dynamic`과 `static - dynamic`의 one-sided 95% paired bootstrap lower bound가 각각 `> 0`이다. 이는 **observed session-token delta difference, non-billing**으로만 표기한다.
6. **Dynamic-vs-static comparison**: quality뿐 아니라 exact directive bytes, emissions, observed session-token delta를 static과 직접 보고한다. control 대비 개선만으로는 통과하지 않는다.
7. **Explicit user adoption decision**: gate report 뒤 사용자가 `adopt|reject|continue-experiment`를 명시한다. `adopt` 전 상태는 항상 `pending_user_decision`이다.

Bootstrap은 complete triplet/workload id를 paired unit로 10,000회 resample하고 manifest의 fixed seed `20260713`을 사용한다. evaluator version, input hash, 포함/제외 sample id, point estimate, confidence bound를 기록한다. exact comparable runtime counter가 없으면 savings confidence를 추정하지 않고 `insufficient`다.

## 6. Acceptance criteria

### Phase 2 회계

- [ ] 매 token-budget helper invocation이 정확히 한 번 집계되고 `invocations = zero + emissions`가 항상 성립한다.
- [ ] normal/unknown/native/same-band/degraded/failure contribution은 0 bytes이며 zero reason count가 고정 enum으로 집계된다.
- [ ] emitted directive의 UTF-8 bytes가 실제 삽입 문자열 기준으로 정확히 누적되고 240-byte cap 회귀가 없다.
- [ ] 첫 runtime total sample은 delta 0, non-decreasing sample만 monotonic delta에 더한다.
- [ ] decreasing/missing sample은 delta를 조작하지 않고 별도 degradation count로 남긴다.
- [ ] XDG aggregate는 8 KiB/file, 256 files, 2 MiB bounds와 atomic update/lock/fail-open을 검증한다.
- [ ] aggregate와 CLI에 raw session id, prompt, response, directive body가 없다.
- [ ] exact tokenizer provenance 없는 fixture에서 token estimate 필드는 absent/null이다.
- [ ] production 출력은 bytes/counter를 savings 또는 billing cost로 이름 붙이지 않는다.

### Progressive disclosure

- [ ] L0는 정확히 0 bytes이고 accounting/experiment 설명을 주입하지 않는다.
- [ ] L1은 기존 canonical 1-line directive와 불변 의미만 포함한다.
- [ ] L2/L3 정보는 명시적 CLI/report/artifact read에서만 노출된다.
- [ ] input pruning/summarization, RL, model effort/intensity/dispatch/QA 변경 경로가 없다.

### Phase 3 isolated experiment

- [ ] production UserPromptSubmit 경로에 dynamic candidate activation/config가 없다.
- [ ] 동일 trace+manifest에서 offline candidate decisions와 evaluator JSON이 byte-identical하다.
- [ ] control/static/dynamic triplet matching과 mismatch exclusion이 검증된다.
- [ ] minimum sample, 100% safety/required, quality tolerance, paired bootstrap 두 비교, dynamic-vs-static report가 machine-gated다.
- [ ] missing/degraded counter는 추정 없이 `insufficient`다.
- [ ] evaluator는 production write를 하지 않고 `eligible_for_user_review` 이상 verdict를 내지 않는다.
- [ ] 사용자 명시 채택 전 production static policy가 그대로 유지된다.

## 7. 구현 순서

1. Phase 2 accounting schema/pure reducer + bounded XDG atomic store와 focused fixtures.
2. hook lifecycle에 invocation outcome/bytes/runtime sample 회계를 fail-open side effect로 연결.
3. `kv|json` on-demand accounting surface와 progressive-disclosure regression tests.
4. `offline-forecast-v1` pure candidate + frozen manifest/replay fixtures.
5. isolated control/static/dynamic runner result schema와 deterministic evaluator.
6. minimum sample, safety/required, quality tolerance, paired bootstrap, static comparison gate tests.
7. focused tests → full Fleet → portable guards/adaptation boundary/doctor. production dynamic-disabled assertion을 final verify에 포함.

## 8. Non-goals

- production hook의 dynamic policy 활성화 또는 자동 rollout
- token/billing savings, 비용 효율, ROI 주장
- bytes-to-token 추정 또는 모델 tokenizer 대체
- transcript/input/artifact pruning·요약·삭제·auto compact 변경
- RL, reward model, online learning, adaptive coefficient update
- model 선택/reasoning effort/intensity/dispatch/depth/QA/reviewer budget 변경
- required tools/tests, safety/security/auth/permissions, validation, error/data-loss handling, accessibility, spec/plan/sandbox/git/hook/liveness guard 축소
- parent/child session counter 합산

## 9. Version history

- v2 (2026-07-13): Phase 2의 bounded XDG reinjection accounting과 progressive disclosure를 정의. exact directive UTF-8 bytes와 runtime cumulative counter delta를 분리하고 token/savings/billing 추정을 금지. Phase 3을 deterministic offline forecast + isolated paired control/static/dynamic evaluator로 제한하고 30 paired samples, safety/required, quality tolerance, paired bootstrap, static 비교, explicit user decision 채택 gate를 잠금.
- v1 (2026-07-13): Phase 0–1 채택. shared session telemetry + exact-session adapter, transition-only output policy와 intensity/safety/dispatch 불변식을 잠금.
