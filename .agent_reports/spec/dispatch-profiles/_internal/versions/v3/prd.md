# Dispatch Profiles — PRD v3

> 2026-07-24 · owner mode-axis amendment. v2 typed bootstrap과 v1 원 설계·실측·CLI
> 근거는 `_internal/versions/`에 보존한다.

## 0. Outcome

headless 분사마다 masked config home을 붙이는 v1의 부분 투영은 유지한다.
다만 “네 core 문서 전원 불변 로드”는 폐기한다. worker의 모델 입력은
`roles/worker-bootstrap.md` + 정확히 한
`roles/worker-types/{owner,stage,review,support}.md` + assigned contract + 선택된
specialization이다. main 오케스트레이션과 사용자 응답 계약은 worker에 넣지
않는다.

## 1. Typed instruction layers

| Layer | Content | Exposure |
|---|---|---|
| worker kernel | immutable assignment, safety/scope, file-only evidence, three-line handoff | every registered worker prompt |
| worker type | owner, stage, review, or support | exactly one, explicit declaration first |
| runtime attach | small harness template, settings/guards, credential/session isolation | selected profile only |
| specialization | `profiles/fragments/<name>.md`, selected Skills/agents | selected profile only |
| main orchestration | entry confirmation, memory lifecycle, routing/integration, merge/push/cleanup, user response | main only |

Safety/permission/git/artifact/route/liveness/verification guards remain
unpruned. Core files may stay symlink-accessible for deterministic checks but
the attach template does not request their blanket model read.

## 2. Declaration and build contract

Every `profiles/<name>.yaml` declares `worker_type` as one of
`owner|stage|review|support`. `model_role` XOR `model`, fragment existence, and
expose schema remain v1 invariants. `build-home.py --check` reassembles the
deterministic attach template plus selected fragments and reports the type.
The dispatch wrapper renders kernel/type around generated and caller-supplied
assignments; the profile home does not duplicate them. Registry/environment
metadata includes the resolved worker type.

## 3. Masking support boundary

Profile masking covers harness-controlled config-home projection and prompt
composition. Runtime-owned project/user instruction discovery is separate.
Claude ordinary custom subagents can inherit the `CLAUDE.md` hierarchy, Codex
may auto-discover project `AGENTS.md`, and OpenCode physical instruction masking
is unverified. These rows use a documented prompt-isolation fallback and must
not be called fully masked.

## 4. Handoff

Material registered workers write detailed evidence to the canonical artifact
root and end with exactly:

```text
artifact: <canonical path | ->
verdict: PASS | FAIL | BLOCKED
blocker: none | <one line>
```

## 5. Locked decisions

- **DP-13:** v1 L0 blanket core-read rule is superseded by the portable worker
  kernel plus exactly one type.
- **DP-14:** profile declares `worker_type`; dispatcher renders it and records it
  in the registry/environment.
- **DP-15:** attach template contains runtime attachment and residual-inheritance
  warning only; selected specialization remains profile-local.
- **DP-16:** lifecycle suppression, prompt isolation, config-home masking, and
  physical runtime instruction masking are distinct support claims.
- **DP-17:** detailed output is artifact-only; registered worker return uses the
  portable three-line envelope.
- **DP-18:** capability mode is an entry-contract field. Worker specialization is
  a separate non-owner field derived from the selected portable unit; it never
  selects the worker type or assigned contract.
- **DP-19:** an owner bootstrap is kernel + owner type + capability contract with
  reserved unit `_kernel/owner` and no worker specialization. A plan/dev/qa unit
  must never be loaded into an owner prompt.

## 5.1 v3 bootstrap tuple

The dispatcher validates the typed tuple before materializing a prompt or registry
row. `capability_mode` must belong to the assigned entry capability. `worker_mode`
is absent for owners and, for route-bound non-owners, equals the exact non-reserved
`unit`. Legacy `mode` is only a shape-classified compatibility input and cannot
override either canonical field. Registry and environment projections preserve the
two axes separately.

Negative fixtures cover owner+stage-mode, owner+non-owner-unit,
capability-mode catalog mismatch, route capability-mode mismatch, and
worker-mode/unit mismatch across all three adapters. Each failure produces no
prompt, row, or child process.

## 6. Completion

Complete when every profile passes builder checks, three dispatchers wrap custom
prompts, portable boundary/projection checks pass, and static kernel/type bytes
are baselined. Static bytes are not a total-token, billing, savings, or ROI
claim.
