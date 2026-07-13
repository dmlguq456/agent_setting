# Token Self-Regulation — Spec (PRD)

> mode: **library + cli + runtime hook** · 작성 2026-07-13 · v1
> 컴포넌트: `agent_setting`의 세션 단위 token/context 계측과 안전한 출력 자기조절. 루트 `spec/prd.md`(Unified Memory System)와 독립이며 이 폴더가 자체 SoT다.
> 입력: `.agent_reports/research/token-self-regulation/` (25 sources, 22 cards, thorough QA 완료) + 2026-07-13 Codex 공식 문서/current runtime 실측.

## 0. 한 줄

**런타임이 제공하는 세션 token/context 신호를 읽기 전용으로 정규화하고, 신호가 확실히 tight/critical band로 바뀔 때만 짧은 출력 규칙을 한 번 주입한다. 작업 intensity·필수 도구·검증·안전·보안·오류 처리·접근성·입력 컨텍스트는 줄이지 않는다.**

이번 구현 범위는 Phase 0–1이다. Phase 2(재주입 비용 회계·다이어트)와 Phase 3(동적 정책 실험)는 별도 사이클이다.

## 1. 배경과 문제

Ponytail 계열 규칙은 “덜 일하라”는 축을 넣지만, reasoning 모델에서는 규칙 재주입 자체가 token을 늘릴 수 있었고 조사 실험은 +26–39% 증가 사례를 확인했다. 반대로 입력 컨텍스트 축소는 순손실 위험이 크며, safety/validation을 budget 레버로 다루면 정확성 계약을 깨뜨린다.

따라서 이 기능은 다음을 동시에 만족해야 한다.

1. per-payload 비율이 아니라 **세션 denominator**를 관측한다.
2. `intensity`(작업 그래프/검증 rigor)와 `token pressure`(출력 표현)를 직교시킨다.
3. 정상·미확인·동일 band 상태의 prompt 주입은 0 byte다.
4. tight 상태에서도 조절 범위를 출력 간결성·명시되지 않은 부가 범위로 제한한다.
5. 런타임 네이티브 기능이 활성화된 경우 이를 복제하지 않는다.

## 2. Runtime currentness와 경계

### 2.1 Codex runtime support

2026-07-13 공식 Codex 문서 확인:

- built-in `/status`는 session configuration, token usage, remaining context를 표시하고 `/statusline`은 `context-used`, limits, token/session 항목을 네이티브 footer에 배치할 수 있다.
- config reference는 `model_context_window`, `model_auto_compact_token_limit`와 under-development `features.rollout_budget.{enabled,limit_tokens,reminder_interval_tokens,sampling_token_weight,prefill_token_weight}`를 노출한다.
- 공식 근거: <https://learn.chatgpt.com/docs/developer-commands#built-in-slash-commands>, <https://learn.chatgpt.com/docs/config-file/config-reference#configtoml>

로컬 실측:

- Codex CLI `0.144.1`.
- `rollout_budget`, `token_budget`, `runtime_metrics`는 under-development이며 현재 false.
- 공식 문서형 rollout-budget config probe는 미문서 필드를 요구한 뒤 그 필드도 schema mismatch로 거부해 현재 공개 config 경로가 실사용 불가하다.
- rollout `token_count` event에는 `info.last_token_usage`, `info.total_token_usage`, `info.model_context_window`가 있다.
- 네이티브 `/statusline`은 built-in 항목 구성 표면이고 arbitrary dynamic field는 지원하지 않는다.

### 2.2 Adapter projection

- `$CODEX_HOME/config.toml`은 runtime-owned다. 본 기능은 이를 쓰거나 자동 활성화하지 않는다.
- shared pure telemetry parser가 portable semantics를 소유하고 Fleet와 CLI가 이를 함께 쓴다.
- `utilities/token-budget.py`의 `kv`/`json`은 read-only 관측 표면이며, `hook`은 transition 판단을 위해 XDG state만 기록한다.
- Codex `preflight.sh token-budget`이 해당 utility를 노출한다.
- Codex `UserPromptSubmit` bridge는 utility의 transition output만 추가한다.
- `/status`, `/statusline`, Fleet collector, account rate-limit status를 대체하지 않는다.

### 2.3 Parity gap과 fallback

| Adapter | Phase 0 telemetry | Phase 1 automatic hook |
|---|---|---|
| Codex | `observed`: exact session rollout JSON | supported fallback; native는 validated opt-in만 |
| Claude | `observed`: native statusline tap/Fleet | 이번 cycle unsupported, 0-injection |
| OpenCode | `observed`: SQLite/Fleet | 이번 cycle unsupported, 0-injection |

- rollout/session signal이 없거나 stale/malformed이면 `unknown`으로 처리하고 **기존 정상 파이프로 fail-open**한다. 수치를 추정하거나 다른 세션 값을 빌리지 않는다.
- native rollout budget는 feature-list와 no-side-effect config probe를 모두 통과한 runtime에서 명시 opt-in 신호가 있을 때만 `native`로 인정한다. 현재 0.144.1은 해당 조건을 충족하지 않는다.

## 3. 범위

### 3.1 Phase 0 — 세션 계측·노출

정규화 출력:

| Signal | Codex source | 의미 |
|---|---|---|
| `active_context_tokens` | `last_token_usage.total_tokens` | 마지막 요청 시점의 현재 context occupancy 원천값 |
| `context_window` | `model_context_window` | runtime 보고 window |
| `context_used_pct` | Codex와 같은 12k reserve 제외식 | 현재 context pressure |
| session input/cache/output/reasoning/total | `total_token_usage.*` | 세션 누적 관측값; billing 비용으로 주장하지 않음 |
| `signal_age_seconds` | token-count event timestamp, legacy fallback은 rollout mtime | stale 판정 근거 |
| native budget state | 명시 opt-in/env | native 중복 방지용 상태 |

Codex context formula:

```text
effective_window = model_context_window - 12000
used = max(0, last_token_usage.total_tokens - 12000)
context_used_pct = round(100 * used / effective_window)
```

`Session.tokens`는 이미 adapter별 의미가 다르므로 정책 입력으로 재사용하지 않는다. 별도 explicit telemetry fields를 추가한다. Codex가 노출하지 않는 cache-read/create 분리는 `unknown`으로 둔다. raw counters는 항상 보존하며 향후 weighted score를 billing cost라고 부르지 않는다.

`context-footprint.py`는 bootstrap/skill/hook 정적 footprint audit이므로 런타임 세션 계측으로 확장하지 않는다. Phase 2 재주입 회계에서 그대로 재사용한다.

### 3.2 Phase 1 — 최소 if-then 정책

기본 threshold:

| State | 조건 | hook 동작 |
|---|---|---|
| `unknown` | 신뢰 가능한 신호 없음/stale | 0 byte, 정상 파이프 |
| `normal` | context used < 70% | 0 byte |
| `tight` | 70% ≤ context used < 85% | 이 band 진입 시 compact directive 1회 |
| `critical` | context used ≥ 85% | 이 band 진입 시 compact directive 1회 |
| `native` | validated native rollout budget active | 0 byte, native에 위임 |

threshold는 CLI/env로 검증 가능하게 override할 수 있지만 repository/runtime config를 쓰지 않는다. hook directive는 240 UTF-8 bytes 이하이며 다음 의미만 가진다.

- 사용자-facing 설명과 반복 요약을 간결하게 한다.
- 사용자가 요구하지 않은 부가 범위·선택적 탐색만 보류한다.
- 현재 요청을 완결하는 필수 구현·도구·테스트·보고는 그대로 한다.
- intensity, model/role routing, plan/review/test rigor를 낮추지 않는다.
- safety, security/auth/permissions, validation, error/data-loss handling, accessibility를 축소하지 않는다.
- spec/plan, sandbox/approval, git/write/hook/liveness guard를 우회하지 않는다.
- 기존 입력/산출물/컨텍스트를 삭제·요약·prune하지 않는다.

조사 roadmap의 “budget tight → 분사 억제”는 현행 standard+ stage/depth 계약과 충돌하므로 Phase 1 레버에서 명시적으로 제외한다.

## 4. 결정과 불변식

### TSR-1 — 세션 denominator와 경계

정책은 current context occupancy와 session cumulative counters를 함께 노출한다. per-payload token 비율을 세션 절감률로 부르지 않는다. cumulative counters가 없으면 해당 필드만 unknown이며 다른 세션에서 보간하지 않는다.

session-id별 raw cumulative 값은 독립적으로 보존한다. compaction/resume/retry는 같은 session id의 runtime 값으로 관측하고, fork/subagent는 별도 session으로 유지한다. parent/child 합산은 이 cycle의 정책 입력이 아니다. runtime counter가 감소하면 조작하지 않고 `degraded`로 표시한다.

### TSR-2 — native-first, no config mutation

Codex rollout budget가 validated opt-in으로 확인되면 harness policy는 관찰만 하고 주입하지 않는다. 기능을 켜기 위해 `$CODEX_HOME/config.toml`을 수정하지 않는다. under-development 기능을 stable portable contract로 주장하지 않는다.

### TSR-3 — intensity와 budget 직교

Budget state는 다음을 바꿀 수 없다.

- `direct|quick|standard|strong|thorough|adversarial` 선택
- depth/dispatch topology와 required stage
- model tier/reasoning effort/portable role
- plan-check, code review, test, adversary/security pass
- 현재 사용자 요청의 definition of done

### TSR-4 — safety rail 불가침

검증·안전·보안·권한·오류/데이터손실 처리·접근성·데이터 무결성과 모든 spec/plan/sandbox/git/hook/liveness guard는 어떤 pressure에서도 유지한다. utility와 hook directive에는 “optional만 축소, required unchanged” 의미가 machine-testable 문자열로 존재해야 한다.

### TSR-5 — input reduction off

Phase 1은 transcript, research, plan, source input을 prune/요약/삭제하지 않는다. auto compact 정책도 변경하지 않는다. 로그 출력이 길어도 stderr, exit status, 최초 실패 원인과 full log 경로를 숨기지 않는다.

### TSR-6 — transition-only reinjection

- `normal`, `unknown`, `native`, 동일 band 재관측: hook stdout contribution 0 byte.
- `tight`, `critical` 신규 진입: directive 1줄, 240 UTF-8 bytes 이하.
- session-id별 band state는 `${XDG_STATE_HOME:-$HOME/.local/state}/agent-harness/token-budget/` 아래에만 기록한다.
- directive에는 metrics 전체나 긴 규칙 목록을 넣지 않는다.
- Phase 2 전까지 savings 수치를 주장하지 않는다.

### TSR-7 — exact-session, tolerant parsing

Codex auto lookup은 exact session id suffix 하나만 허용한다. 0개/복수 candidate, invalid id, malformed JSON, missing keys, stale file은 unknown이다. transcript prompt/content를 출력하지 않는다.

## 5. CLI와 출력 계약

### 5.1 Portable utility

```text
utilities/token-budget.py \
  [--adapter portable|codex] [--session-id ID] \
  [--active-context-tokens N --context-window N] \
  [--session-input-tokens N ...] \
  [--format kv|json|hook]
```

- explicit signals가 있으면 runtime-independent fixture/adapter가 사용할 수 있다.
- Codex + session id면 rollout auto lookup을 시도한다.
- `kv`/`json`은 관측·debug 표면, `hook`은 band-transition directive 또는 빈 stdout이다.
- exit 0은 `unknown`을 포함한다. malformed CLI argument 같은 caller error만 non-zero다.

### 5.2 Codex preflight

```text
adapters/codex/bin/preflight.sh token-budget [cwd] [session-id] [kv|json|hook]
```

`cwd`는 기존 preflight 인터페이스 정합용이며 rollout 선택에는 사용하지 않는다. session id exact match만 쓴다.

### 5.3 Hook integration

`userprompt-lifecycle.py`는 mode/recall/briefing 뒤에 `token-budget ... hook` 결과를 parts에 추가하고, turn-nudge는 기존대로 side effect로 유지한다. budget lookup은 기본 1초의 독립 timeout을 가지며(환경변수로 0.05–5초 범위 조정), utility failure/timeout은 hook 전체 실패로 전파하지 않고 빈 budget context로 degrade한다.

## 6. Acceptance criteria

### 계측

- [x] synthetic Codex rollout에서 active context와 session cumulative counters를 분리해 정확히 파싱한다.
- [x] Codex 12k reserve 공식을 Fleet collector와 동일하게 계산한다.
- [x] Fleet `Session`이 active context와 cumulative input/cache/output/reasoning/total을 explicit fields로 보존한다.
- [x] Codex/Claude/OpenCode collector가 가능한 필드를 채우고 unavailable 필드는 `None`으로 둔다.
- [x] explicit portable signal이 동일한 policy state를 만든다.
- [x] unknown/missing/malformed/stale/ambiguous session은 값 추정 없이 unknown이다.
- [x] session-id 격리와 감소 counter의 degraded 판정이 검증된다.
- [x] JSON/KV는 prompt/content를 노출하지 않는다.

### 정책

- [x] 기본 69/70/84/85% boundary가 normal/tight/tight/critical이다.
- [x] normal/unknown/native와 동일 band hook output은 정확히 빈 문자열이다.
- [x] tight/critical 신규 진입은 각 1줄·240 bytes 이하다.
- [x] directive가 optional extras만 보류하고 required work/tools/tests/safety/input context 유지 의미를 담는다.
- [x] native active 명시 신호 시 fallback directive가 억제된다.

### 통합·비회귀

- [x] `preflight.sh token-budget` kv/json/hook 표면이 동작한다.
- [x] Codex UserPromptSubmit bridge가 tight/critical transition일 때만 budget context를 합성한다.
- [x] 기존 tracked anchor/recall/briefing/turn-nudge tests가 통과한다.
- [x] standard+ dispatch/depth와 required QA가 budget state에 영향받지 않는다는 문서/guard 검증이 있다.
- [x] Fleet canonical/Claude mirror parity, adapter boundary, portable guards, doctor에 신규 실패가 없다.
- [x] runtime-owned config와 transcript를 수정하지 않는다.

## 7. 구현 순서

1. shared pure telemetry parser + focused unit test: last/total/cache/missing/stale/threshold/session isolation.
2. Fleet `Session` explicit fields와 Codex/Claude/OpenCode collector mapping; Claude mirror 동기화.
3. `core/CONVENTIONS.md`와 `core/OPERATIONS.md`에 orthogonality/safety/dispatch invariant 추가.
4. `utilities/token-budget.py`와 Codex `preflight.sh token-budget` mapping.
5. Codex UserPromptSubmit hook의 transition-only context 연결.
6. Codex bootstrap/README/ADAPTATION 및 boundary checks 동기화.
7. focused → portable guards → adaptation boundary → doctor/runtime projection 검증.

## 8. Non-goals와 후속 phase

### 이번 범위 아님

- token 절감률/비용 효율 주장
- output 품질 자동 평가 또는 학습/RL
- transcript/input context 자동 압축·삭제
- 모델/effort/intensity/QA/dispatch 자동 하향
- Claude/OpenCode 자동 token hook 추측 구현
- native rollout budget 자동 활성화·config 편집
- parent/child session token 합산 또는 billing cost 계산

### Phase 2

- 실제 hook reinjection bytes/tokens와 turn 수 회계.
- tight workload의 net saving/quality 측정.
- transition cadence와 directive 다이어트 재평가.

### Phase 3

- 정적 threshold를 넘어선 동적 정책 실험.
- 별도 실험 artifact와 사용자 채택 결정 전에는 production 경로에 넣지 않는다.

## 9. Version history

- v1 (2026-07-13): Phase 0–1 채택. current Codex native rollout budget 경계를 반영해 `context-footprint.py` 확장안 대신 shared session telemetry + exact-session adapter를 선택. transition-only output policy와 intensity/safety/dispatch 불변식을 잠금. Phase 2–3 분리.
