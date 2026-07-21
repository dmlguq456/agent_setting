# pipeline_summary — adapter-model-config

- **status**: implemented + verified (worktree `adapter-model-config`, base `eda11cd4`, **not merged/committed**)
- **mode**: dev (harness infra, library/cli) · **intensity**: standard
- **spec-significance**: within-spec (SD-22/core ADAPTATION §3 delegate concrete model to adapter; no PRD amendment)

## 무엇을 했나

세 어댑터(codex/claude/opencode)의 concrete 모델 ID·effort 기술을 **어댑터별 단일 config
SoT**(`adapters/<adapter>/config/models.conf`)로 통합하고, 나머지 전 표면을 config-파생으로
리팩터. config 밖 concrete 모델 ID는 **fail-closed 가드**로 차단. codex의 `gpt-5.6-terra` 제거.

### 값 (확정 스킴)
| 티어 | codex | claude | opencode |
|---|---|---|---|
| deep | gpt-5.6-sol/high | fable/high (소진→opus 캐스케이드) | opencode-go/glm-5.2 |
| light | gpt-5.6-luna/med | sonnet/med | opencode-go/deepseek-v4-pro |
| mini | gpt-5.4-mini/low | haiku/low | opencode-go/deepseek-v4-flash |

- fast implementer = deep 모델 + medium effort. balanced orchestrator = light.
- 라이프사이클: turn-nudge=mini, curate=light. terra 완전 제거.
- opencode 모델 문자열은 로컬 opencode-go provider 레지스트리에서 **실측** 확인.

### 변경 표면 (19 modified + 5 new)
- **포터블**: core/ADAPTATION.md §3, roles/README Adapter Requirements 강화.
- **codex**: config/models.conf(신규), model-map.sh, role-map.sh, sync-native-agents.py(PROFILE_CONFIG 제거),
  agents/dev-team.toml(재생성), distill-worker.sh, README/ADAPTATION.
- **claude**: config/models.conf(신규), model-map.sh, mem-distill-worker.sh, deep agents frontmatter(opus→fable), ADAPTATION.
- **opencode**: config/models.conf(신규), role-map.sh.
- **가드**: tools/check-model-config.py(신규) + claude tools 심링크 + TOOL_DEFERRED + CI(checks.yml).
- **테스트**: stage_dispatch_capacity.test.py terra→현행 정합.

## 검증 (전부 그린)
- check-model-config.py: config 외 concrete ID 0.
- sync-native-agents --check: idempotent.
- capacity test: 8/8. fleet test_dispatch 76 / test_harness_model_merge 17.
- check-adaptation-boundary.sh: PASS. build-manifest --check: PASS.
- 세 어댑터 model-map/role-map 역할별 출력 스팟체크(terra 부재, deep=fable/sol/glm 등).

## 후속 반영 (사용자 승인 2026-07-21)
- claude qa-team/material-team frontmatter opus→sonnet(light). opus는 이제 어디서도 상시 티어가 아니고
  **capacity failover 캐스케이드에만** 존재.
- **capacity failover 실배선**: `CFG_TIER_DEEP_FAILOVER_CASCADE`를 SD-59가 소비하도록
  `utilities/stage-dispatch-fallback.py`에 `capacity_cascade_next` + `allowed_capacity_settings` 확장
  (failover 모델은 캐스케이드 선언으로 proved) + capacity_retry 자동 도출 배선. capacity 소진은
  모델 단위 전환(effort 강등 무의미)이라 캐스케이드도 모델 단위. **Fable 소진→opus→sonnet /
  SOL→LUNA / glm-5.2→deepseek-v4-pro** 자동. 단 **분사(headless) 경로 한정** — 네이티브
  서브에이전트는 Claude Code 런타임이 config-failover 미지원이라 자동 불가(구조적 한계).

## 남은 항목
- 네이티브 서브에이전트 frontmatter는 config-파생 아님(가드 exempt) + capacity failover 미적용
  (런타임 한계) — 완전 결정론/자동 failover 원하면 deep 작업을 분사 경로로 태우거나 별도 훅 후속.
- P2(범위 밖): dispatch-defaults.yaml capability×stage effort/model 선언(SD-66/68 개정) — 별도 spec 트랙.

## spec drift (deferred, autopilot-code는 타 스펙 미수정)
- 메모리 스펙 P-36: per-mode 모델 티어 메커니즘 보존, 값(curate deep→light) 변경. prose의 gpt-5.5/gpt-5.4-mini 언급 stale.

## 머지 안내
worktree에서 검증만 완료. 커밋/머지/push는 사용자 승인 후. `git -C <worktree> diff main` 으로 리뷰 가능.
