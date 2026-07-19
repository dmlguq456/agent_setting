# dev log — code-execute (SD-68)

worktree: `/home/Uihyeop/agent_setting-wt/config-sealing`
route: rt-d57cbb149952fd3d

## Commits (core-first order)

1. `3fbbd1e3` — spec: SD-68 record affinity 소비 규칙 한 문장 현행화
   - `core/OPERATIONS.md` §5.10 line 129 문장 뒤에 record `harness_affinity`/
     `dispatch_defaults_digest` 소비 계약(soft·verify 재로드 금지·
     registry_digest 분리) 한 문장 추가.
2. `9130c437` — feat(dispatch): SD-68 dispatch-defaults config를 route record에
   컴파일 시점 스냅샷으로 봉인 (utilities + wrapper 3종 + tests)

## Files changed per commit 2

- `utilities/dispatch-defaults.py`: `query_stage_affinity(config, capability, stage)`
  추가. 기존 `query_affinity`/스키마/어휘/CLI 불변.
- `utilities/capability-route.py`:
  - 상단에 `DEFAULTS` importlib 모듈 로드 + `VALID_AFFINITY = DEFAULTS.AFFINITY_VALUES | {"unspecified"}`.
  - `_seal_dispatch_defaults(nodes, capability)` 헬퍼: config 로드 → depth-2 노드
    `harness_affinity` 스탬프 + `dispatch_defaults_digest` 반환. 부재 → 전부
    `unspecified` + digest `None`. 손상 → `DefaultsConfigError`를 `ValueError`로
    승격(fail-loud, main exit 64).
  - `compile_route`: dispatch_fallback 주입 직후·`route_hash` 계산 전에 호출,
    payload에 `dispatch_defaults_digest` 필드 추가(`registry_digest`와 분리).
  - `verify_route`: `harness_affinity`(필드 있을 때만) 어휘 검사 +
    `dispatch_defaults_digest` 포맷 검사만 추가. config 재로드 없음. 구 route
    (필드 부재) 하위호환 통과.
- `utilities/dispatch-node.py`: `node.get("harness_affinity")` 있으면 argv에
  `--harness-affinity <값>` 추가. 필드 없으면 불변.
- `adapters/{claude,codex,opencode}/bin/dispatch-headless.py`: `--harness-affinity`
  인자(default None) 추가 + pipe 메타데이터 키 튜플 끝에 `"harness_affinity"`
  추가(3개 파일 동형 위치: claude ~421, codex ~518, opencode ~484). falsy →
  필터링, 구 경로 불변. 신규 검증 게이트 없음(순수 passthrough).
- `utilities/capability_route.test.py`: acceptance ①(어휘 스탬프) ②(값 변경 →
  route_hash 변화, 주석만 변경 → hash 불변) ③(스탬프 route는 config 사후 변경에도
  verify 통과) + 구 route 하위호환 + 위조 어휘 verify 실패 + 부재 config(digest
  None/전부 unspecified) + 손상 config fail-loud(ValueError) 테스트 추가.
- `utilities/dispatch_node.test.py`: acceptance ④(argv에 `--harness-affinity`
  전달, 필드 없으면 미포함) ⑤(explicit `--adapter`≠affinity에도 launch 통과,
  soft·비교 없음) 테스트 추가.

## Self-test results (in worktree only)

- `utilities/capability_route.test.py` — 18 passed
- `utilities/dispatch_node.test.py` — 20 passed
- `utilities/dispatch_contract.test.py` — 10 passed (회귀)
- `utilities/worker_route_guard.test.py` — 13 passed (회귀)
- `adapters/codex/bin/dispatch-headless.sd45.test.py` — 9 passed
- `adapters/opencode/bin/dispatch-headless.sd45.test.py` — 9 passed
- `adapters/claude/bin/dispatch-headless.sd45.test.py` — 1 pre-existing failure
  (`test_route_consumer_and_missing_evidence_refusal`, exit 73), **confirmed
  identical on baseline via `git stash`** — unrelated to this change.
- `adapters/codex/bin/dispatch-headless.sd15.test.sh` — PASS (all rows)
- `adapters/opencode/bin/dispatch-headless.sd15.test.sh` — PASS (all rows)
- `adapters/claude/bin/dispatch-headless.sd15.test.sh` — 4 pre-existing failures
  (`model-worker-governor-denied`, env-specific governor cap), **confirmed
  identical on baseline via `git stash`** — unrelated to this change.
- `utilities/dispatch-route.test.sh` — PASS (selector 1단계 의미 불변 회귀 확인)

No pipe-string exact-match assertion needed updating — all suites use kv-dict
parsing, and the added `harness_affinity` key is transparent to them.

## Deviations

- Launch harness deviated from config affinity (`execute=codex`) to `claude`,
  per the conductor-prompt's recorded deviation note (Codex workspace-write
  sandbox has read-only linked-worktree git metadata, blocking commits).
