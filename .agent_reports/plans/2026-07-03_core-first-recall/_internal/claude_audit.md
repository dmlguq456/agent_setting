이제 필요한 부분을 다 확인했습니다. 발견 사항을 심각도 순으로 정리해서 보고합니다.

## 감사 결과 — core-first adapter guard + recall-first 메모리 변경

전체 diff, 신규 hook 코드(`hooks/core-first-guard.sh`, `hooks/core-read-marker.sh`), codex/opencode 프로젝션, `.gitignore`, drill 케이스, 테스트 스위트(273/273 PASS), `check-adaptation-boundary.sh`(OK)를 확인했습니다. **차단(blocking)급은 아니지만, 실질적으로 가드가 무력화되어 있는 상태**를 발견해 최상단에 올립니다.

### 🔴 1. [최상위] 라이브 `~/.claude/settings.json`에 신규 훅 2개가 미배선 — 가드가 실사용 세션에서 전혀 발동하지 않음
- **파일**: `adapters/claude/settings.json:52-60, 107-112` (repo, 수정됨) vs `~/.claude/settings.json` (live, 미수정 — mtime 15:01로 정체)
- 직접 확인: live `~/.claude/settings.json`의 `PreToolUse`에 `core-first-guard.sh`가 없고, `PostToolUse[Read]`에 `core-read-marker.sh`가 없습니다. repo 쪽만 갱신되고 실제 배포(복사/동기화)는 안 됐습니다.
- **이미 자가진단됨**: `loops/drill/results/2026-07-03_1835/a_core_first_adapter_edit.diagnosis.md`가 정확히 같은 결론을 담고 있습니다("행동은 PASS, 배포 드리프트로 hard FAIL"). 이 diff에 포함된 `loops/lib-runner.sh:39-41` 수정(`--settings` 명시 로드)은 **드릴 자체를 hermetic하게 만드는 fix B**만 적용한 것이고, diagnosis가 권고한 **fix A(실제 배포 — `cp adapters/claude/settings.json ~/.claude/settings.json`)는 아직 적용 안 됨**을 재확인했습니다.
- **영향**: 18:47 재실행 드릴은 PASS했지만, 이는 hermetic 테스트 환경에서만 그런 것이고 — 이 대화를 포함한 실제 Claude Code 세션은 지금도 core-first 가드 없이 `adapters/**`를 편집할 수 있는 상태입니다. 즉 이번 diff가 만든 안전장치는 **현재 프로덕션에 미적용**.
- **권고**: `cp adapters/claude/settings.json ~/.claude/settings.json` (또는 향후 재현되는 배포 파이프)로 즉시 동기화. `tools/build-manifest.py`가 manifest만 빌드하고 `~/.claude`로의 실제 배포 스텝이 파이프에 없다는 구조적 원인도 diagnosis가 이미 지적함.

### 🟠 2. `core-first-guard.sh` — 신규 하위 디렉터리 대상 fail-open (재현 확인)
- **파일**: `hooks/core-first-guard.sh:39` (`repo=$(git -C "$(dirname "$fp")" rev-parse --show-toplevel ...)`, 실패 시 `return 0`)
- 직접 재현: `adapters/claude/hooks/newdir/newfile.sh`처럼 **아직 존재하지 않는 하위 디렉터리**에 새 파일을 쓰는 경우, `dirname`이 존재하지 않는 경로가 되어 `git -C`가 실패 → `repo=""` → 게이트를 조용히 통과(exit 0, marker 불필요)합니다. 반면 기존 디렉터리 안의 신규 파일은 정상적으로 deny(exit 2)됩니다.
- **영향**: 이 가드가 막으려는 정확한 케이스(새 adapter 표면 신설)에서 오히려 뚫립니다. 신규 hook 파일, 신규 adapter 서브디렉터리 등을 만들 때 우회될 위험.
- **권고**: `dirname "$fp"`가 없으면 상위로 올라가며 존재하는 조상 디렉터리에서 `git -C`를 시도하거나, 실패 시 `return 2`(fail-closed)로 바꾸는 편이 안전.

### 🟡 3. `.core-grounding/`가 `.gitignore`에 없음 (`.spec-grounding/`와 비대칭)
- **파일**: `.gitignore:7`에 `.spec-grounding/`는 있지만 동형 디렉터리 `.core-grounding/`는 어디에도 없음.
- 실제로 `.core-grounding/`는 세션 ID·절대경로가 박힌 마커 파일들을 담고 있고(`git status`에 `??`로 잡힘), `git add -A`류를 실행하면 커밋될 위험이 있습니다.
- **권고**: `.gitignore`에 `.core-grounding/` 한 줄 추가.

### 🟡 4. mtime 기반 staleness 체크가 "읽고 나서 같은 파일을 바로 편집"하는 정상 플로우를 self-invalidate
- **파일**: `hooks/core-first-guard.sh:54-58`
- Read marker 기록 시각(`read_mtime`) 이후 해당 core 파일이 다시 쓰이면 stale 처리됩니다. 그런데 "core 파일을 Read → 같은 파일을 Edit(계약 추가) → adapter 파생 반영" 같은, 이 원칙이 정확히 요구하는 정상 워크플로우 자체가 그 read marker를 stale로 만듭니다(diff에 없는 다른 core 문서를 추가로 Read해야만 통과).
- 이미 diagnosis에 "**별도 확인 필요**"로 남겨져 있고 코드상 미해결 상태임을 확인. 오탐 deny 가능성이 있는 latent 이슈.
- **권고**: staleness 판정을 mtime 비교 대신 "이번 세션 내 Read 발생 여부"로 바꾸거나, 편집 직후 자기 marker를 갱신하는 식으로 보완.

### ⚪ 잔존 리스크 (blocking 아님, 참고용)
- **`session_id` "nosession" fallback** (`hooks/core-first-guard.sh:76`, `core-read-marker.sh:44`): 호출 측이 session_id를 못 넘기면 전역 `nosession` 버킷을 공유 → "이번 세션에 실제로 읽었는가"라는 취지가 옅어짐(TTL 없음). 정상 Claude/Codex/OpenCode 플로우에서는 session_id가 항상 전달되므로 실사용 위험은 낮음.
- **symlink 경로 vs git 정규화 경로 불일치**: `is_adapter_target(fp, repo)`가 호출자가 준 원본 `fp` 문자열과 `git rev-parse --show-toplevel`이 반환하는 정규화된 `repo` 경로를 단순 prefix 비교합니다. `fp`가 심볼릭 링크 경유 경로(예: 다른 프로젝션 경로)로 들어오면 매칭 실패 → fail-open 가능. 테스트 스위트에 symlink 경유 케이스가 없어 미검증. 현재 이 repo의 실제 작업 방식(항상 canonical 경로로 편집)에서는 발현 안 함.
- **codex 훅의 `/core/` 문자열 매칭이 넓음** (`adapters/codex/hooks/posttooluse-read-marker.py:111`): `.../core/foo.md` 형태면 어디든 매칭하지만, 실제 marker 기록은 `core-read-marker.sh`의 `"$repo"/core/*.md` 단일 레벨 체크로 다시 걸러지므로 실질적 우회는 없음(무해한 과매칭).

### 정합성 · 문서 교차검증
- Claude/Codex/OpenCode 세 어댑터의 `AGENTS.md`/`CLAUDE.md`/`ADAPTATION.md`/`README.md`/`manifest.json`/`build-manifest.py`/`check-adaptation-boundary.sh`는 서로 모순 없이 core-first 게이트를 일관되게 반영. `python3 tools/build-manifest.py --check` → up-to-date, `bash tools/check-adaptation-boundary.sh` → OK, `bash hooks/portable-guards.test.sh` → 273/273 PASS.
- `core/MEMORY.md`의 recall-first 갱신과 `adapters/claude/CLAUDE.md` 도메인 트리거 테이블 간 문구·범위 불일치 없음. 구 "매 턴 습관적 호출 X" 류 잔존 문구도 없음(grep 확인).

**요약**: 코드 로직 자체(가드/마커 스크립트, 3-adapter 프로젝션, 문서)는 서로 잘 맞고 테스트도 통과하지만, **가장 중요한 배포 단계(live `~/.claude/settings.json` 동기화)가 빠져 있어 이 세션을 포함한 실사용에서 core-first 가드가 지금 작동하지 않습니다.** 여기에 신규 디렉터리 fail-open(#2)과 `.gitignore` 누락(#3)은 즉시 고칠 만한 작은 수정입니다.
