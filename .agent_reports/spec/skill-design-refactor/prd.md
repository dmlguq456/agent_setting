# Skill-Design Refactor — PRD v5

> 2026-07-16 · portable-first worker-bootstrap isolation amendment
> v1–v4의 완료 계약과 근거는 `_internal/versions/`에 보존한다. v5는 v4의
> entry-route confirmation과 main-context ownership을 worker 입력·출력 경계까지
> 확장한다.

## 0. Outcome

material work는 계속 `model proposal → user confirmation → capability-owned
execution`으로 라우팅한다. 승인 뒤 depth-0 main은 route/state/integration만
보유하고, worker는 공통 최소 kernel과 정확히 한 worker-type fragment 및
배정된 capability/stage contract만 소비한다. worker의 상세 근거는 파일에
남고 main으로 돌아오는 마지막 출력은 고정 3줄 handoff뿐이다.

## 1. Portable bootstrap contract

portable source는 `roles/worker-bootstrap.md`와
`roles/worker-types/{owner,stage,review,support}.md`다.

- **kernel:** worker identity, immutable assignment, write/artifact scope, safety,
  verification, file-only evidence, fixed handoff만 포함한다.
- **owner:** 선택된 entry capability와 stage graph, dispatch/wait/harvest,
  synthesis artifact만 소유한다.
- **stage:** 배정된 stage Skill·입출력·completion gate만 소유하고 topology를
  다시 고르거나 depth 3을 만들지 않는다.
- **review:** 기본 read-only이며 findings/evidence를 artifact에 남긴다.
- **support:** 하나의 bounded task만 수행하며 명시적 scope 없이는 mutation하지
  않는다.

worker bootstrap에서 제외하는 것은 main response policy, entry confirmation,
main memory lifecycle, briefing/title/UI/token context, 전체 capability catalog,
다른 stage의 상세 계약, integration/merge/push/cleanup, 사용자 설명이다.
안전·권한·write scope·route validation·verification은 줄이지 않는다.

## 2. Handoff envelope

worker의 마지막 출력은 정확히 다음 세 줄이다.

```text
artifact: <canonical path | ->
verdict: PASS | FAIL | BLOCKED
blocker: none | <one line>
```

`PASS`는 assigned completion gate 충족, `FAIL`은 시도/검토를 완료했지만 gate
미충족, `BLOCKED`는 권한·입력·runtime 상태 때문에 진행 불가를 뜻한다.
changed files, commands, logs, reasoning, warnings, unsupported-contract detail은
artifact에 기록한다. material registered work는 artifact가 필수이며 `-`는
durable output이 없는 atomic read-only support에만 허용한다.

## 3. Runtime realization and masking boundary

| Runtime | Harness-controlled projection | Runtime-owned residual input |
|---|---|---|
| Claude | masked profile은 kernel + one type + selected specialization만 조립한다 | 일반 custom subagent는 project/user `CLAUDE.md` hierarchy를 자동 상속하며 agent별 해제 설정이 없다 |
| Codex | headless prompt의 explicit full `adapters/codex/AGENTS.md` read를 제거하고 kernel + one type만 주입한다 | project `AGENTS.md` 자동 discovery를 custom agent layer가 제거한다는 공식 계약은 없다 |
| OpenCode | generated headless prompt를 같은 kernel/type/handoff로 감싼다 | project instruction auto-load의 물리 마스킹은 검증 전까지 fallback으로 표시한다 |

따라서 lifecycle suppression, harness-controlled prompt isolation, physical
runtime masking을 별도 상태로 보고한다. 자동 상속이 남는 runtime에
`fully masked`를 주장하지 않는다.

## 4. Conformance and measurement

1. 세 dispatcher는 custom prompt에도 kernel/type/handoff를 적용한다.
2. generated dispatch prompt는 full main adapter bootstrap을 explicit read하지
   않는다.
3. worker type은 explicit `--worker-type`을 우선하고 없으면 depth/role로
   결정론적으로 분류한다.
4. profile builder는 worker type을 필수 선언으로 검증하고 canonical kernel과
   one type fragment만 조립한다.
5. boundary test는 세 adapter의 동일 envelope, one-type projection, main-only
   wording 부재, runtime fallback 문서를 검사한다.
6. context-footprint는 kernel과 네 type 조합의 UTF-8 bytes를 baseline한다.
   보고는 정적 입력 변화이며 total token, billing, savings, ROI로 환산하지
   않는다.

## 5. Locked decisions

- **SD-26:** canonical worker input = one kernel + exactly one worker-type fragment
  + assigned capability/stage detail.
- **SD-27:** canonical return = artifact/verdict/blocker three-line envelope;
  verbose evidence is artifact-only.
- **SD-28:** worker output is machine-oriented handoff, not a user-facing report;
  main alone owns explanation and integration.
- **SD-29:** lifecycle suppression, prompt isolation, and physical masking are
  distinct support claims; runtime auto-inheritance is never hidden.
- **SD-30:** worker context reduction cannot remove safety, scope, route validation,
  verification, required input, or model/intensity/depth contracts.
- **SD-31:** static worker-bootstrap bytes are measured; aggregate token/cost savings
  remain unclaimed without paired production evidence under SD-16.

## 6. Completion

Complete only when core-first source, three sibling dispatchers, Claude masked
profiles, deterministic tests, clean-worktree boundary, generated projections,
and strict context-footprint all pass. An unverified runtime masking row leaves
that row `fallback`, not falsely `supported`; checked fallback is sufficient for
portable outcome GREEN when the residual input is documented and no duplicate
harness-controlled bootstrap is injected.
