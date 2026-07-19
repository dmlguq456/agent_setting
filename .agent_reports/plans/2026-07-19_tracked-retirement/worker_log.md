# tracked/untracked 모드 퇴역 — 작업 로그

체크리스트 A→E 전체 실행 완료. 커밋: `452690ff` (`tracked-retirement` 브랜치).

## 요약

- 삭제: `utilities/{workflow-toggle,workflow-guard-hook}.sh`, `adapters/{claude,codex,opencode}/utilities/{workflow-toggle,workflow-guard-hook}.sh`, `adapters/claude/track-toggle.sh`, `adapters/claude/commands/track.md`, `claude_setting/track-toggle.sh` — settings.json 훅 등록 2건 함께 제거.
- `hooks/artifact-guard.sh`: `.untracked` 우회·생성순서 게이트(has_spec/has_research/block) 삭제. 존치: canonical-root 강제, `_internal` 예외, spec_touch route 검사. plugin-marketplace 미러 동기화.
- `hooks/worktree-path-guard.sh`: `.untracked` 우회 → `WORKTREE_GUARD_BYPASS=1` env 우회로 교체.
- `adapters/claude/statusline.sh`, `utilities/harness-status.sh`: 게이트 세그먼트/`workflow_state` 필드 제거(git_untracked 카운트는 유지).
- Codex/OpenCode `preflight.sh`: `start`/`mode`/`track` 서브커맨드 제거, `route` 시퀀스의 `mode` 호출 제거(회귀 발견·수정), `prompt-signal`에서 `workflow_state` 분기 제거. `userprompt-lifecycle.py`의 모드 배너 억제 로직(`CODEX_MODE_ANCHOR_ALWAYS` 등) 제거. OpenCode JS 플러그인(`agent-harness-guards.js`)의 `start`/`mode` 호출 제거.
- codex/opencode 스킬 54개 파일(및 codex plugin-marketplace 미러) — 생성기(`sync-native-skills.py`, `sync-native-plugin.py`) 원본을 고쳐 재생성.
- fleet: `_gate_info`/`_gate_word`/`_gate_tag`/`_project_gate` 및 세션행 게이트 태그·그룹 헤더 배지 삭제(healthy-silent, 대체 표식 없음). `Session.gate` 필드 제거, demo 픽스처 정리. `_WIDE`에서 미사용 📌 제거.
- 설치기(`projector.py`, `install-windows.sh`) 목록·`manifest.json`(재생성)·`tools/check-adaptation-boundary.sh`(수십 곳)·`.gitignore` 갱신.
- drill `g5`/`g5b`: assert를 canonical-root 강제 검증으로 개편(원래의 "생성순서 게이트" 검증은 게이트 자체가 퇴역했으므로 무의미해짐). `loops/drill/README.md` 갱신. **drill 미실행**.
- 문서 7종(core) + adapter README/ADAPTATION/AGENTS 6+ 파일 재표현: "tracked project" → "spec-backed project", 모드 서술 제거.
- `tools/context-footprint.py`: 회귀 발견 — `hook_samples()`가 삭제된 `preflight.sh mode`를 호출하고 있었음. 샘플 제거 + baseline JSON에서 `hook:codex-mode` 제거.
- 불변 확인: `capabilities/topologies.json`, `capability-route.py`, `*_route_guard.test.py` 등의 `tracked_gate_evidence` — 무변경. `.agent_reports/spec/**` — 무변경(쓰기 없음).

## 검증

- rsync `tools/fleet/` → `adapters/claude/tools/fleet/` 미러 동기화.
- fleet 전체 스위트: 662 passed.
- `hooks/portable-guards.test.sh`: 353 passed / 2 known pre-existing failures(코드 변경 전 HEAD에서도 동일하게 실패 확인 — `git stash` 대조로 검증; 코드 dispatch AGENT_HOME 관련, 이번 작업과 무관).
- `tools/check-adaptation-boundary.sh`: FAIL 0.
- `tools/adaptation-guard.test.sh`: PASS.
- `tools/install/profile-activation.test.sh`: PASS.
- 전수 grep(`workflow-toggle|workflow-guard-hook|track-toggle|📌tracked|⚡untracked|CODEX_MODE_ANCHOR|tracked mode|untracked mode|tracked project|preflight.sh (track|start)` 등): 0.
- `COLUMNS=168 python3 tools/fleet/fleet.py --once`(라이브+데모 둘 다): 정상 렌더, 게이트 워드 부재(유일한 "tracked" 매치는 branch 컬럼의 `tracked-retir`(브랜치명) 문자열).

```text
RESULT: pass
EVIDENCE: fleet 662 passed · portable-guards 353 passed/2 known-pre-existing(unrelated, stash-verified) · adaptation-boundary 0 FAIL · adaptation-guard PASS · profile-activation PASS · grep sweep 0 · fleet --once(live+demo) 정상, 게이트 워드 부재
FILES: 152
```
