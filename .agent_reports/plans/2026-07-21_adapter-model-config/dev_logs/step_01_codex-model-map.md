# dev_log 01 — P0 core + codex model-map config-SoT

## P0 — 포터블 계약 강화 (완료)
- `core/ADAPTATION.md §3`: "concrete 모델명은 adapter 문서/생성 파일에 속함" → "단일 adapter config
  SoT(`adapters/<adapter>/config/models.conf`) + 전 표면 파생 + config-외 concrete ID는 fail-closed
  가드 위반 + effort 우선 튜닝" 으로 강화.
- `roles/README.md` Adapter Requirements: 동일 취지로 "단일 config SoT + 결정론 가드" 명문화.

## Codex — config SoT + model-map (완료·검증)
- 신설 `adapters/codex/config/models.conf` — codex concrete 모델/effort의 유일 선언처.
- `adapters/codex/bin/model-map.sh` 리팩터: config source(`. ../config/models.conf`), 역할→티어
  라우팅만 유지, concrete 리터럴 0. **terra 완전 제거.**

### 검증 (L1)
| role | 결과 | 기대 |
|---|---|---|
| deep maker | gpt-5.6-sol / high | deep |
| fast implementer | gpt-5.6-sol / **medium** | deep 모델 + medium effort ✓ (구 terra) |
| orchestrator | gpt-5.6-luna / medium | light ✓ (구 terra) |
| external adversary orchestrator | gpt-5.6-luna / medium | light |
| fast reviewer | gpt-5.6-luna / medium | light |
| external adversary | gpt-5.6-sol / high | deep |

- terra 잔존 grep: 0 (model-map·config).
- env override(CODEX_MODEL_SOL) 동작 확인.
- unknown role → exit 64 유지.

## 남은 작업 (checklist)
- codex: sync-native-agents PROFILE_CONFIG→config, tomls 재생성, distill-worker config화, docs 생성영역
- claude / opencode 대칭 구현
- 가드(check-model-config.sh) + 테스트 정합
