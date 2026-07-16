# Proposal-Gated Self-Improvement Governance — PRD

> mode: **library + cli** · 작성 2026-07-14 · v2 (on-call promotion bridge)
> 컴포넌트: agent harness의 loop evidence와 active source/plugin/runtime activation 사이의 승격 경계
> 구현은 `autopilot-code`; 이 문서는 의미·권한·상태 계약의 SoT다.

## 0. 한 줄

Loop는 실패에서 incident, fixture, candidate를 자동으로 만들 수 있지만 active
instruction, adapter, plugin, runtime config는 수정하지 않는다. 채택된 portable
invariant만 별도 spec/code/release cycle에서 source-first로 구현하며, 각 runtime
realization은 exact runtime/plugin fingerprint에 대해 다시 검증한다.

## 1. 문제와 목표

공식 Claude Code, Codex, OpenCode 업데이트와 local self-improvement가 같은
instruction, skill, hook, adapter projection 또는 runtime config를 수정하면 source
ownership과 activation 시점이 섞인다. Proposal 승인만 추가해도 이 충돌은 사라지지
않는다. 승인된 invariant와 version-bound runtime realization을 분리해야 한다.

목표:

1. 관찰·재현·제안은 자동화할 수 있다.
2. active setting이나 source 변경은 별도 승인된 spec/code/release cycle만 수행한다.
3. proposal freshness와 runtime realization compatibility를 별도 상태로 추적한다.
4. official update 후 과거 승인을 자동 승계하지 않는다.
5. evidence inbox는 runtime discovery, plugin cache, repo source 밖에 둔다.
6. on-call은 memory를 후보 신호로 읽고 live evidence로 교차검증한 뒤, 같은
   incident를 중복 proposal로 늘리지 않고 기존 record에 recurrence evidence를
   누적한다.

## 2. 소유권

| 영역 | 소유자 | Improvement loop 권한 |
|---|---|---|
| `core/`, `capabilities/`, `roles/` | portable source | candidate diff 제안만 |
| adapter source/generator | adapter source | candidate diff 제안만 |
| generated projection/plugin bundle | generator | read/check only; 직접 수정 금지 |
| installed plugin/cache/runtime binary | runtime/vendor | probe only |
| runtime-owned config | user/runtime | delta 제안만 |
| local proposal inbox | evidence loop | incident/evidence/state 기록 가능 |
| active release/activation ledger | installer/release cycle | read only |

한 runtime surface에는 active provider가 하나만 존재해야 한다. Plugin과 linked
projection은 서로 다른 surface를 제공할 때만 병존할 수 있다.

## 3. 이중 상태 모델

### 3.1 Portable proposal state

```text
observed -> reproduced -> proposed -> reviewed
reviewed -> adopted | superseded-by-native | rejected | deferred
deferred -> observed | reproduced
adopted -> superseded-by-native
```

- `observed`: incident와 base fingerprint가 존재한다.
- `reproduced`: 최소 fixture에서 baseline failure가 재현된다.
- `proposed`: 비활성 candidate, 영향, rollback evidence가 존재한다.
- `reviewed`: 최신 context와 human approval reference가 존재한다.
- terminal decision에는 human approval reference가 필요하다.

### 3.2 Runtime realization state

Proposal adoption은 미래 runtime 구현의 영구 승인이 아니다. Runtime별 realization은
별도 상태를 가진다.

```text
unverified -> active
active -> needs-revalidation
needs-revalidation -> active | incompatible | superseded-by-native | retired
```

Runtime/plugin/context fingerprint가 바뀌면 기존 `active` realization은 자동 승계되지
않고 `needs-revalidation` 대상이다.

## 4. Freshness contract

Proposal context는 canonical JSON으로 저장하고 전체 SHA-256을 base fingerprint로
사용한다. Context에는 최소 다음이 포함되어야 한다.

- repo/source revision과 dirty 여부
- portable core 또는 manifest fingerprint
- runtime 이름·버전
- upstream/plugin 이름·버전·content fingerprint
- official docs fingerprint 또는 evidence reference
- fixture fingerprint
- 현재 active provider/channel

`proposed -> reviewed`, terminal decision, realization `active` 전이는 현재 context가
stored base와 byte-equivalent canonical fingerprint일 때만 가능하다. Mismatch는
`stale` 판정이며 proposal을 `reproduced` 또는 `deferred`로 되돌려야 한다.
Recurrence ingest 자체는 base를 바꾸지 않는다. Pre-review proposal을 현재 context에
묶어 명시적으로 `reproduced` 전이할 때만 base를 갱신하며, 이후 review는 그
재현 context와 byte-equivalent해야 한다.

## 5. CLI 계약

구현 위치는 `tools/improvement/proposals.py`, local state 기본 위치는
`${XDG_STATE_HOME:-~/.local/state}/agent-harness/improvement`다.

필수 명령:

- `observe`: context와 incident summary로 proposal 생성
- `transition`: evidence를 복사해 portable state 전이
- `realization`: runtime realization 상태 기록
- `check`: 현재 context와 stored base의 freshness 비교; read-only
- `show`, `list`: read-only inspection

Automated collectors는 `observe --incident-key <key>`를 사용한다. `incident-key`는
acting agent가 현재 evidence를 해석해 선택하는 안정적인 one-line identity다.
결정론적 CLI는 의미 유사도를 판정하지 않고 exact key만 비교한다. 같은 key가 이미
존재하면 새 proposal을 만들지 않고 incident evidence와 incoming context fingerprint를
기존 record에 append한다. 기존 state와 human decision은 변경하지 않는다. 동일 key가
여러 record에 존재하면 자동 선택하지 않고 ambiguous error로 중단한다.
Named collector의 `reproduced` 전이는 현재 `--context`를 필수로 받고, 그
reproduction evidence와 함께 pre-review base를 갱신한다.

안전 계약:

- network, runtime CLI, package manager, Git mutation을 호출하지 않는다.
- repo, runtime home, plugin cache 내부를 store로 허용하지 않는다.
- evidence는 bounded opaque bytes로 복사하며 실행·해석하지 않는다.
- write는 lock + atomic replace를 사용한다.
- reviewed/terminal/active realization은 `--approval-ref`가 없으면 거부한다.
- CLI는 source, generated output, runtime config, activation state를 수정하는 명령을
  제공하지 않는다.

## 6. On-call promotion bridge

On-call은 최근 memory write event와 full record body를 incident discovery input으로
사용할 수 있다. Memory는 현재 사실이나 proposal evidence의 SoT가 아니며 다음 순서를
지킨다.

1. `mem log --json`에서 최근 memory mutation을 읽고, acting agent가 관련 record를
   선택한다. type, strength, keyword, 고정 threshold는 승격 규칙이 아니다.
2. 선택한 ID는 `mem show`로 전문을 읽는다.
3. 현재 source, test output, loop log, artifact 또는 runtime probe에서 memory claim을
   교차검증한다. live corroboration이 없으면 proposal로 승격하지 않는다.
4. 기존 proposal의 incident key와 의미를 확인한 뒤, agent가 stable incident key를
   정하고 `observe --incident-key`를 호출한다.
5. source/runtime을 수정하지 않는 bounded local fixture로 재현되면 현재 context를
   명시해 `reproduced`로 전이한다. 이 단계만 stale pre-review base를 갱신한다.
   candidate invariant·영향·rollback evidence까지 준비되면 `proposed`로 진행할 수
   있다. 재현 불가면 `observed`에 머문다.
6. morning report에는 proposal ID, 현재 state, live evidence, recurrence 여부와 다음
   human decision을 기록한다.

자동 범위는 `proposed`까지다. On-call은 network probe, headless runtime, drill,
source/generated projection, plugin, runtime config, Git mutation을 실행하지 않는다.
`reviewed`, terminal decision, realization activation은 기존 human approval gate를
그대로 따른다. reviewed/adopted/rejected 등 human-owned state의 같은 incident가 다시
발생해도 evidence만 append하고 state를 reopen하거나 덮어쓰지 않는다.

## 7. Reconciliation

공식 update가 감지되면:

1. official docs와 local runtime/plugin fingerprint를 다시 캡처한다.
2. 열린 proposal에 `check`를 실행한다.
3. stale proposal은 자동 적용하지 않는다.
4. native 기능이 fixture를 만족하면 `superseded-by-native`를 제안한다.
5. portable invariant가 유지되면 adapter만 승인된 cycle에서 수정·재생성한다.
6. semantic conflict는 자동 병합하지 않는다.
7. isolated runtime regression 후 기존 installer/release activation을 사용한다.

## 8. Non-goals

- self-edit 또는 automatic adoption
- prompt/session hook을 통한 매-turn 분류 또는 proposal 생성
- on-call이 memory를 자동 truth로 간주하거나 의미 판단을 keyword/threshold에 위임
- runtime/plugin auto-update 제어
- runtime-owned config merge
- candidate diff 적용, commit, push 또는 release
- LLM의 semantic review를 human approval로 간주

## 9. Acceptance criteria

1. 기본 inbox가 XDG state 아래 생성된다.
2. repo와 세 runtime home 아래 store가 거부된다.
3. illegal state transition이 거부된다.
4. approval-required transition이 approval reference 없이 거부된다.
5. context mismatch가 review/adoption/active realization을 차단한다.
6. evidence가 bounded state inbox로 복사되고 hash가 기록된다.
7. 테스트 전후 실제 runtime config/plugin tree가 byte-unchanged다.
8. 기존 generator, adapter boundary, installer/runtime activation 회귀가 통과한다.
9. exact incident key recurrence는 proposal을 늘리지 않고 evidence/history만 append한다.
10. 다른 key는 별도 proposal이며, ambiguous duplicate key는 fail closed한다.
11. on-call contract는 memory 전문과 live corroboration을 요구하고 자동 범위를
    `proposed`로 제한한다.
12. recurrence는 reviewed/terminal state를 자동 변경하거나 reopen하지 않는다.
13. stale recurrence는 ingest만으로 base를 바꾸지 않으며, current-context-bound
    reproduction 이후에만 freshness를 회복한다.

## 10. 후속 단계

v2는 on-call의 memory→proposal 승격을 연결한다. UI, scheduled runtime-watch 연결,
source diff 생성, activation automation은 각각 별도 proposal과 승인된 spec/code
cycle이 필요하다.
