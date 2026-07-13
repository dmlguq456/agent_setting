# Token Self-Regulation — Phase 3 Experiment Contract

> status: **spec-only, production-disabled** · contract version: 1 · 2026-07-13
> parent: [prd.md](prd.md) v2. 이 파일은 isolated experiment의 input, pairing, evaluator, gate를 소유한다.

## 1. 목적과 경계

Phase 3은 `offline-forecast-v1`을 production hook에 넣기 전 다음 두 질문만 검증한다.

1. 같은 telemetry trace에서 candidate decision이 결정론적으로 재현되는가?
2. 같은 workload의 control/static/dynamic triplet에서 dynamic이 required quality/safety를 유지하면서 control과 static보다 낮은 observed session-token delta를 보이는가?

이 실험은 billing cost나 production savings를 측정하지 않는다. dynamic policy, input pruning, RL/online learning, model effort, intensity, dispatch/depth, QA 변경은 허용하지 않는다.

## 2. 고정 arm

| arm | directive policy | production 사용 |
|---|---|---:|
| `control` | token-budget contribution 0 bytes | 없음 |
| `static` | v1 `70% tight / 85% critical`, transition-only | 현재 production baseline을 isolated runner에서 복제 |
| `dynamic` | frozen `offline-forecast-v1`, v1 canonical directive만 선택 | 없음 |

세 arm의 prompt/artifact, exact model/runtime/config, reasoning effort, intensity, dispatch/depth, QA, required tools/checks, timeout/retry policy는 동일해야 한다. arm별 차이는 위 directive policy 하나뿐이다.

## 3. Offline candidate manifest

필수 manifest:

```yaml
contract_version: 1
candidate_id: offline-forecast-v1
candidate_code_sha256: <hex>
fixture_set_sha256: <hex>
tight_pct: 70
critical_pct: 85
history_window: 3
forecast_step: median_non_negative_context_pct_increment
unknown_behavior: static_equivalent_no_early_emission
directive_ids: [tight-v1, critical-v1]
bootstrap:
  resamples: 10000
  seed: 20260713
quality_tolerance: 0.02
minimum_complete_triplets: 30
production_enabled: false
```

manifest는 run 시작 전에 hash로 고정한다. run 도중 threshold, candidate code, directive, rubric, bootstrap seed를 바꾸면 새 experiment id가 필요하다.

## 4. 입력 record

### 4.1 Workload declaration

```yaml
experiment_id: <stable id>
workload_id: <stable id>
stratum: <declared category>
prompt_sha256: <hex>
artifact_bundle_sha256: <hex>
rubric_version: <id>
rubric_sha256: <hex>
required_checks: [<stable check id>]
safety_checks: [<stable check id>]
model_id: <exact runtime model id>
runtime_id: <harness + version>
runtime_config_sha256: <hex>
reasoning_effort: <value>
intensity: <value>
dispatch_depth: <value>
qa_contract: <value>
seed: <int|null>
arm_order: [control|static|dynamic, ...]
```

`prompt_sha256`는 pairing용이며 prompt 본문을 evaluator result에 복사하지 않는다. runtime seed가 없으면 `seed: null`을 기록하고 workload별 arm order를 counterbalance한다.

### 4.2 Arm result

```yaml
experiment_id: <id>
workload_id: <id>
arm: control|static|dynamic
manifest_sha256: <hex>
config_fingerprint: <all pairing fields hash>
status: complete|invalid|failed
exclusion_reason: <fixed enum|null>
session_counter_status: observed|degraded|unknown
session_total_tokens_start: <int|null>
session_total_tokens_end: <int|null>
session_token_delta: <int|null>
hook_invocations: <int>
zero_injections: <int>
emissions: <int>
directive_utf8_bytes_total: <int>
directive_exact_tokens: <int|null>
exact_tokenizer_provenance: <runtime/model/version|null>
required_checks_pass: <bool>
safety_checks_pass: <bool>
hard_regression: <bool>
quality_score: <float 0..1>
quality_evaluator_id: <deterministic-checker or blinded frozen reviewer id>
```

`session_token_delta = end - start`는 같은 exact session의 non-decreasing runtime counter일 때만 유효하다. bytes-to-token 추정은 금지한다. `quality_score`는 run 전 고정한 rubric의 deterministic checks 또는 arm label을 가린 frozen reviewer가 산출하며 세 arm에서 같은 evaluator/config를 쓴다. `hard_regression`은 rubric의 사전 선언 critical item 실패 또는 required user-visible output 누락이다. invalid/failed arm이 있는 workload는 complete triplet이 아니다.

고정 exclusion enum:

- `missing_arm`
- `pairing_fingerprint_mismatch`
- `counter_unknown_or_degraded`
- `counter_decreased`
- `required_output_missing`
- `runner_failure`
- `rubric_missing_or_changed`
- `manifest_changed`

## 5. Pairing과 계산

### 5.1 Complete triplet

한 paired sample은 같은 `experiment_id + workload_id`의 세 arm이 모두 `complete`이고 `config_fingerprint`, manifest, rubric이 일치하는 triplet이다. evaluator는 불완전 triplet을 보간·대체·재사용하지 않는다.

### 5.2 Paired metrics

sample `i`에서:

```text
quality_dynamic_vs_control_i = Qdynamic_i - Qcontrol_i
quality_dynamic_vs_static_i  = Qdynamic_i - Qstatic_i

observed_delta_control_vs_dynamic_i = Δtokens_control_i - Δtokens_dynamic_i
observed_delta_static_vs_dynamic_i  = Δtokens_static_i - Δtokens_dynamic_i
```

양의 observed delta difference는 candidate arm의 runtime session-token delta가 더 작았다는 뜻이다. metric label은 항상 `observed session-token delta difference (non-billing)`을 사용한다. directive bytes/emissions는 별도 exact descriptive metric이며 session-token difference에서 빼거나 token으로 변환하지 않는다.

### 5.3 Deterministic paired bootstrap

- resampling unit: complete `workload_id` triplet
- resamples: 10,000
- RNG seed: 20260713
- statistic: paired mean difference
- report: point estimate, one-sided 95% lower bound, included/excluded ids와 reason counts
- multi-run workload가 있으면 먼저 workload id 안에서 사전 고정 방식으로 하나의 summary를 만들고 workload id를 bootstrap한다.

동일 정렬 input JSON과 manifest에서 evaluator JSON은 byte-identical이어야 한다.

## 6. 채택 gate

평가 순서는 고정이며 앞 gate 실패 시 후속 수치를 채택 근거로 사용하지 않는다.

| gate | pass 조건 | fail verdict |
|---|---|---|
| G1 sample | complete triplet `n >= 30`; 복수 stratum이면 각 `n >= 10` | `insufficient` |
| G2 integrity | included triplet 100% fingerprint/manifest/counter valid | `insufficient` |
| G3 safety/required | 모든 arm의 required+safety check 100% pass, hard regression 0 | `reject` |
| G4 quality | dynamic-control, dynamic-static quality 95% LCB 각각 `>= -0.02` | `reject` |
| G5 control saving confidence | control-dynamic observed delta 95% LCB `> 0` | `reject` |
| G6 static comparison | static-dynamic observed delta 95% LCB `> 0`; exact bytes/emissions도 함께 보고 | `reject` |
| G7 user decision | gate report 후 명시 `adopt|reject|continue-experiment` | `pending_user_decision` |

G1–G6가 모두 pass하면 evaluator verdict는 `eligible_for_user_review`다. evaluator는 `adopted`를 출력할 수 없다.

## 7. Evaluator output

```yaml
contract_version: 1
experiment_id: <id>
manifest_sha256: <hex>
input_sha256: <hex>
verdict: insufficient|reject|eligible_for_user_review
complete_triplets: <int>
excluded_triplets: <int>
exclusion_reason_counts: {<enum>: <int>}
gates:
  G1_sample: pass|fail
  G2_integrity: pass|fail
  G3_safety_required: pass|fail
  G4_quality: pass|fail
  G5_control_confidence: pass|fail
  G6_static_comparison: pass|fail
metrics:
  quality_dynamic_vs_control: {mean: <float>, lower_95: <float>}
  quality_dynamic_vs_static: {mean: <float>, lower_95: <float>}
  observed_delta_control_vs_dynamic_nonbilling: {mean: <float>, lower_95: <float>}
  observed_delta_static_vs_dynamic_nonbilling: {mean: <float>, lower_95: <float>}
  directive_utf8_bytes_by_arm: {control: <int>, static: <int>, dynamic: <int>}
  emissions_by_arm: {control: <int>, static: <int>, dynamic: <int>}
adoption_decision: pending_user_decision
production_dynamic_enabled: false
```

## 8. 금지·중단 조건

- production hook/config에 dynamic candidate path가 발견되면 experiment를 중단하고 `reject`한다.
- input pruning/summarization, RL/reward/online fitting, model/effort/intensity/dispatch/depth/QA 차이가 있으면 해당 experiment id 전체를 invalid 처리한다.
- required/safety check를 arm별로 다르게 적용하거나 failure를 token metric으로 상쇄하지 않는다.
- exact tokenizer provenance가 없으면 `directive_exact_tokens: null`이다.
- counter가 missing/degraded/decreasing이면 savings confidence를 추정하지 않고 `insufficient`다.
- G1–G6 pass나 사용자 `adopt`만으로 production을 자동 수정하지 않는다. 채택 구현은 별도 v3 spec update와 autopilot-code 검증을 요구한다.
