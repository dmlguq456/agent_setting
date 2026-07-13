# Verification

- `bash hooks/portable-guards.test.sh` → `PASS=336 FAIL=0`
- `bash tools/check-adaptation-boundary.sh` → PASS (허용된 compat reference 59건 warning)
- `PYTHONPATH=tools python3 -m unittest discover -s tools/fleet/tests -v` → 180 tests PASS
- `bash utilities/dispatch-liveness.test.sh` → PASS
- `bash utilities/dispatch-wait.test.sh` → PASS
- `python3 tools/build-manifest.py --check` → PASS
- `bash tools/skill-conformance/scan.sh skills` → PASS
- changed shell syntax, Python compile, root/Claude mirror cmp, `git diff --check` → PASS
- Codex drill: `g_stage_dispatch` runner PASS; `a_lab_audio_html` runner PASS.
- g10: Codex가 slugger 구현과 실제 OpenCode depth-2 marker까지 완료. lineage assert false-fail을 교정한 뒤 동일 wrapper + 실제 OpenCode child postfix replay에서 세 assertion 모두 PASS.
- 교정 후 새 Codex headless rerun은 account usage limit으로 turn 시작 전 차단됨; runner가 이를 exit 70으로 분류하는 fake-runtime 회귀 검사 PASS.
- main runtime projection은 link/skill/agent/bootstrap/hook trust가 모두 정상이고, 사용자 병합형 `~/.codex/hooks.json`이 harness 원본과 exact-match가 아니라는 1건만 실패해 환경성 non-issue로 분류.
