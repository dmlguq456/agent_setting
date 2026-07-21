# dev_log 02 — codex 생성기·toml·distill config화 (완료·검증)

## sync-native-agents.py (생성기)
- `PROFILE_CONFIG` dict 제거 → `load_models_conf()` 파서 + `_CFG`.
- config에 프로필 섹션 추가: `CFG_PROFILE_<TEAM>=tier:effort:sandbox` (모델은 tier에서 파생).
- `codex_config(profile)`·`render_extra_agent`·memory-scout(model/reasoning/sandbox 키 제거) 정합.
- 검증: 생성기에 concrete `gpt-5.x` 0건.

## agents/*.toml 재생성
- dev-team: `gpt-5.6-terra` → **`gpt-5.6-sol`/medium** (fast implementer = deep 모델 + medium effort).
- 나머지 8개 tier 정합(deep→sol, light→luna). `--check` idempotent 통과.

## distill-worker.sh
- 모델 선택을 `. ../config/models.conf` + tier_model()로 config-파생.
- curate → CFG_LIFECYCLE_CURATE=light → gpt-5.6-luna (구 gpt-5.5 deep).
- increment/nudge → CFG_LIFECYCLE_NUDGE=mini → gpt-5.4-mini.
- concrete ID 담은 주석 2곳 정리. 문법 OK, concrete ID 0.

## spec-impact (deferred drift 기록)
- 메모리 스펙 P-36: per-mode 모델 티어 *메커니즘*·dispatch 계약 보존, 값(curate deep→light)만 변경.
  concrete 티어는 core/ADAPTATION §3(강화)대로 adapter-owned → within-spec. 스펙 prose의 gpt-5.5
  언급은 stale(autopilot-code는 타 스펙 직접 미수정). 사용자 결정(curate=light) 반영.
- ADAPTATION nudge: §3 편집 vs HLS 스펙의 §6 참조 → 무관.

## 코덱스 어댑터 = 코드 전 표면 config-파생 완료. 남음: 문서(가드 후 일괄), claude, opencode, 가드, 테스트.
