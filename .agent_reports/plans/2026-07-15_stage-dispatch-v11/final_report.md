# Stage-dispatch v11 final report

## 결과

v11 SD-48~50과 수확 관찰 O1을 구현해 main에 통합했다. 직접 nested
Codex spawn이 지원된다고 과장하지 않고, 측정된 동일 tuple은 hard
`unsupported`로 유지하면서 ancestor broker와 ordered fallback으로 depth-2
stage-dispatch를 복구한다.

- 구현 커밋: `298bc043`
- main merge: `7c293fd6`
- 검증: portable guards `359/359`, topology `8/8`, adaptation boundary와
  manifest check PASS, 세 어댑터 SD-15/SD-45 및 v11 fixture PASS.

## 핵심 변경

- route compiler가 parent harness/transport/sandbox, child harness, launch
  authority별 checked evidence를 요구하고 각 depth-2 node에 같은→교차
  harness→native→inline 순서를 고정한다.
- 세 wrapper가 inherited `AGENT_DISPATCH_JOBS`를 canonical registry로
  강제하고, spawn 전 stable attempt row를 기록하며 global write 불가와
  nested local override를 fail-closed한다.
- legacy cycle-local row는 attempt identity 기준으로 idempotent reconcile한다.
- Codex row에 PID/start tick을 기록하고 liveness의 PID 및 transcript fallback을
  harness-aware하게 만들어 O1 false-DEAD를 닫았다.

## 현재 depth=2 의미

- Codex headless/workspace-write conductor → Codex child 직접 spawn:
  `unsupported(network-operation-not-permitted)`.
- 동일 logical depth-2를 depth-0 ancestor broker가 launch: 현 runtime check
  `supported`.
- 따라서 depth=2 분사 자체는 route/fallback을 통해 안전하게 진행할 수
  있지만, conductor 내부의 같은-harness 재귀 `codex exec` 성공을 뜻하지 않는다.

## v12 후보 제안 — 구현하지 않음

- **O2 등재 권고**: worker는 커밋하지 않고 prepared commit message와 main
  harvest commit을 계약화하는 안을 우선 검토한다. sandbox 개방안은 위험
  검토가 필요하다.
- **O3 등재 권고**: 자기수정 cycle에 증거·사유 필수 orchestrator override를
  둘지, compile-time registry digest pin과 drift record를 둘지 autopilot-spec
  update에서 결정한다.

상세 검증은 `test_logs/final-verification.md`, 구현 내역은
`dev_logs/implementation.md`에 있다.
