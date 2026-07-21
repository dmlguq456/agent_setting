# dev_log 03 — claude 어댑터 config화 (resolver 완료·검증)

## adapters/claude/config/models.conf (신설)
- deep=fable/high, light=sonnet/medium, mini=haiku/low.
- deep failover cascade = "fable/max→…→opus/…→sonnet/…" (opus는 failover 전용, 상시 티어 아님).
- lifecycle: nudge=mini, curate=light.
- 역할→티어 그룹은 **claude 기존 그룹 보존** (codex와 다름: claude의 external adversary는 외부 엔진을
  호출하는 light wrapper라 deep 아님). deep=deep roles만, 나머지=light.

## model-map.sh (config source)
- opus→fable(deep), sonnet 유지(light). 그룹 case 보존. concrete alias 0.
- 검증: deep maker/reviewer→fable/high, fast impl/reviewer/orchestrator/external adversary→sonnet/medium.

## mem-distill-worker.sh (config source)
- fast-distiller→CFG_LIFECYCLE_NUDGE=mini→haiku (구 claude-sonnet-4-6).
- deep-curator→CFG_LIFECYCLE_CURATE=light→sonnet (구 claude-opus-4-8).
- 버전 박힌 concrete ID 제거. 문법 OK.

## 남은 결정 필요 (report에서 사용자에게)
1. claude agent frontmatter(`adapters/claude/agents/*.md`의 `model:`): deep 에이전트(plan/design/
   research/editorial-team)는 지금 opus → **fable로 갱신** 필요. 이 파일들은 codex tomls와 달리
   수기 Claude-native Agent 파일 → 가드가 frontmatter를 in-scope(config 일치 강제)로 볼지,
   runtime-native hint로 exempt할지 결정.
2. opencode 정확한 provider/model-id 문자열 (GLM 5.2/DeepSeek Pro/Flash) — opencode는 "provider/model-id"
   포맷. 정확 문자열은 추측 불가 → 사용자 제공 필요.
