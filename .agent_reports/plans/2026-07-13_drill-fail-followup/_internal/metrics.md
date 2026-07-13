# Metrics

- separability: 부분별 수정은 분리 가능; root/adapters mirror와 통합 gate가 결합점이다.
- dispatch: 사용자 요청 범위의 후속 소사이클이며 별도 subagent를 사용하지 않는다.
- baseline: portable guards PASS=321 FAIL=8.
- final: portable guards PASS=336 FAIL=0; Fleet unit PASS=180; dispatch-liveness/wait PASS.
- drill: g_stage_dispatch PASS, a_lab_audio_html PASS, g10 Codex 행동 완료 후 lineage false-fail 교정 및 postfix replay PASS.
- environment: Codex usage reset은 2026-07-20 09:06로 보고되어 교정 후 새 headless turn은 시작되지 못함.
