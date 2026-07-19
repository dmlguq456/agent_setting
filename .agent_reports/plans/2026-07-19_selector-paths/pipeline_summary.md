# Pipeline Summary — selector-paths (autopilot-code dev/standard)

- route_id: `rt-0970ceb6cde95614` · route_hash: `sha256:0970ceb6…0dbb52`
- capability: autopilot-code · mode: dev/refactor · intensity: standard · qa: standard
- spec-significance: **within-spec** — governing `spec/stage-dispatch/prd.md` §13.8.1 SD-66 (1단계 소비자 배선, SD-23 read-only selector 유지)
- worktree: `/home/Uihyeop/agent_setting-wt/selector-paths` (branch `selector-paths`, base `main` @ `321792e5`)
- result commit: **`35d60fc1`** · worktree clean · **overall verdict: PASS**

## Outcome

`utilities/dispatch-route.sh`가 `$(dirname "$0")`로 내부 헬퍼를 해석해 심볼릭 링크
프로젝션(`adapters/{claude,codex,opencode}/utilities/`)을 따라가지 못하던 버그를 수정.
`readlink -f`(비존재 시 dirname 폴백)로 `$0` 실경로를 해석해 `self_dir`/`repo_root`를
선계산하고 4곳 헬퍼 경로(L28/L38/L103/L104)를 교체. POSIX/dash 클린, cascade·출력·종료코드
불변(SD-23 read-only 보존). `dispatch-defaults.py`는 자체 realpath 해석하므로 무변경.
`utilities/dispatch-route.test.sh`에 프로젝션 표면 회귀 테스트 추가.

## Stage ledger

| Stage | Harness | Model role | Verdict | Evidence |
|---|---|---|---|---|
| plan | claude (deviated) | deep maker | PASS | `plan.md`, `checklist.md` |
| execute | claude | fast implementer | PASS | `dev_logs/execute-claude.md` (commit 35d60fc1) |
| test | codex (diverse) | deep reviewer | PASS | `test_logs/test_report.md` |
| report | claude | fast writer | PASS | `final_report.md` |

모든 노드 completion marker: `.dispatch/completion/rt-0970ceb6cde95614/{plan,execute,test,report}.json`.

## Harness deviations (config affinity 이탈 사유 — SD-66 soft default)

- **plan: config=codex → claude 이탈.** 첫 codex plan attempt(`att-f06a8c68…`)가
  BLOCKED. 사유: codex workspace-write 샌드박스에서 preflight spec-read 마커가 primary
  `/home/Uihyeop/agent_setting/.spec-grounding`(read-only)에 기록 불가 → "required plan
  artifact writes denied". route fallback ordinal 1(same-harness-headless claude, supported)로
  재분사, claude(unsandboxed)는 primary `.spec-grounding` 기록 가능 → PASS(`att-ff9c2e89…`).
- **execute: config=codex → claude 이탈(사전 지시).** 2026-07-19 retry-lineage 실측 —
  codex workspace-write 샌드박스는 linked worktree git metadata가 read-only라 커밋
  불가(BLOCKED). claude로 실행해 정상 커밋.
- **test: codex 유지(diverse).** execute(claude)와 다른 하네스로 독립 검증(route
  promotion signal = independent-verifier). 예고된 codex 제약 실측: 종료 stage-heartbeat
  마커 영속화가 exit 65로 실패했으나 **검증 자체는 완주** — verdict를 `test_logs/test_report.md`로
  영속화했고 terminal heartbeat도 최종 기록되어 정상 harvest됨(salvage 불필요).
- **report: claude 유지(config).**

## Registry hygiene note (measured intervention)

첫 codex plan attempt는 BLOCKED로 종료했으나 namespace-local 워커가 terminal heartbeat/
completion marker 없이 죽어, guarded closer(harvest는 routed 행에 completion marker 요구,
reconcile은 namespace-local에 terminal heartbeat 요구)로 닫을 수 없는 사각지대에 빠졌다.
process(pid 152198) 소멸을 확인한 뒤 `jobs.log.lock` 하에서 해당 attempt 행만
`open→done`(note=`code-plan-blocked-codex-spec-grounding…`, verdict=BLOCKED)으로 수술적
플립 — `close_job_row` 의미 복제. 나머지 3개 성공 행은 completion marker → reconcile/harvest
정상 경로로 닫음. 종료 시점 parent=selector-paths open child 0.

## Verification (independent code-test, PASS)

- `sh -n`/`dash -n` 양 파일 clean · `sh utilities/dispatch-route.test.sh` → `dispatch-route: PASS`
- 3-어댑터 프로젝션(`--stage test … --maker-family gpt`): 3개 모두 `status=eligible` + `adapter=`(no `not found`); `--stage plan`(claude 프로젝션) → `adapter=codex`
- `bash tools/check-adaptation-boundary.sh` exit 0 (worktree)
- `dispatch_contract.test.py` 10 OK · `dispatch_node.test.py` 17 OK · sd15 ×3 PASS
- **sd45 ×3 실패(`test_route_consumer_and_*_refusal`, rc=73)는 사전 존재** — 독립 test가
  `git archive HEAD^`(부모 `321792e5`)로 격리 재현, 동일 실패명·어서션·rc·건수 일치 →
  회귀 아님, 범위 외.

## Out of scope / carry-forward

SD-68(route compile 봉인) 다음 사이클 · usage-check.sh/model-map.sh 내부 로직 ·
셀렉터 cascade 의미 · 권한 분류기 · spec/** · worker-route-guard · sd45 사전 실패(별도 후속).

## Handoff

Integration(main 머지·push·worktree cleanup)은 depth-0(main session) 소관 — 본 conductor는
수행하지 않음. 통합 대상: 커밋 `35d60fc1` on branch `selector-paths`.
