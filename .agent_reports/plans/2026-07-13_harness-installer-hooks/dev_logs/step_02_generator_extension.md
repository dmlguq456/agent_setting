# Phase 2 — `sync-native-plugin.py` 확장 구현 로그

## 변경 요약 (`adapters/claude/bin/sync-native-plugin.py`)

- 모듈 docstring: "skills + agents + hooks" → "skills + agents + hooks(5: 2 self-contained +
  3 spec-pipeline DATA-rebased) + hooks.json + utilities/agent-home.sh" 갱신.
- 상수:
  - `UTILITIES_SOURCE = ROOT / "utilities"`, `UTIL_BUNDLE = ["agent-home.sh"]` 추가.
  - `HOOK_ADOPT` 3종 추가(`spec-skill-gate.sh`·`spec-read-marker.sh`·`spec-sync-nudge.sh`) —
    총 5개, 순서 = git-state·artifact·spec-skill-gate·spec-read-marker·spec-sync-nudge.
  - 주석 "spec-pipeline trio deferred" → "adopted (cycle 3, ... env-prefix; see plan
    2026-07-13_harness-installer-hooks)" 갱신.
  - `_HOOK_EVENTS` 신설(5종 전부 event 매핑).
  - `_HOOK_MATCHERS`/`_HOOK_SHELLS` 에 spec 3종 추가(settings.json 실측: Skill/sh, Read/sh,
    Edit|Write|MultiEdit/bash).
  - `_HOOK_DATA_HOME = {spec-skill-gate.sh, spec-read-marker.sh, spec-sync-nudge.sh}` 신설
    (env-prefix 대상 판별 집합).
- `hooks_json()`: 기존 `PreToolUse` 하드코딩 리스트-컴프리헨션을 `HOOK_ADOPT` 순회 + `events`
  dict 누적 방식으로 교체. `_HOOK_DATA_HOME` 멤버 command 에
  `AGENT_HOME="${CLAUDE_PLUGIN_DATA}" ` prefix 를 얹고, 아닌 항목은 기존 문자열 그대로(회귀
  없음). docstring 을 다중이벤트+DATA 재기준 설명으로 갱신.
- `sync()`: 진입 가드에 `UTIL_BUNDLE` 각 파일 존재 확인 추가. hooks 복사 블록 뒤에 utilities
  rmtree→mkdir→copy2 블록 추가(exec bit 보존).
- `check()`: hooks 잉여-파일 탐지 블록 뒤에 utilities byte-compare + excess-file 탐지 블록
  추가(hooks 블록과 동일 패턴 미러).
- 3종 hook `.sh` 자체는 기존 `for name in HOOK_ADOPT: copy2`(`sync()`)와
  `for name in HOOK_ADOPT: read_bytes 비교`(`check()`)가 `HOOK_ADOPT` 리스트 확장만으로
  자동 커버 — 추가 코드 불요(plan 대로).

## 실행 결과

```
$ python3 -m py_compile adapters/claude/bin/sync-native-plugin.py
COMPILE_OK

$ python3 adapters/claude/bin/sync-native-plugin.py
generated Claude native plugin projection at adapters/claude/plugin-marketplace/plugins/agent-harness-claude

$ python3 adapters/claude/bin/sync-native-plugin.py --check
(no stderr) exit=0

$ md5sum 재실행 비교 (전체 plugin-marketplace 트리)
IDEMPOTENT_OK — 재실행 후 파일 md5 전부 동일
```

- 생성물: `hooks/` 에 5개 `.sh`(git-state-guard·artifact-guard·spec-skill-gate·
  spec-read-marker·spec-sync-nudge, 전부 exec bit 유지) + `hooks.json` + `utilities/`
  (`agent-home.sh`, exec bit 유지).
- `hooks.json` 구조(실측):
  - `PreToolUse`: git-state-guard(matcher `Edit|Write|MultiEdit|NotebookEdit`, prefix 없음) →
    artifact-guard(matcher `Edit|Write|MultiEdit`, prefix 없음) → spec-skill-gate(matcher
    `Skill`, `AGENT_HOME="${CLAUDE_PLUGIN_DATA}"` prefix).
  - `PostToolUse`: spec-read-marker(matcher `Read`, DATA prefix) → spec-sync-nudge(matcher
    `Edit|Write|MultiEdit`, DATA prefix).
  - 기존 2종(git-state·artifact) command 문자열은 사이클 2 와 byte-identical(prefix 없음) —
    회귀 0 확인.

## 불변식 검증

```
$ git diff -- hooks/
(empty — exit 0)
```

canonical `hooks/*.sh` 본체 **무수정** 확인. write 범위는
`adapters/claude/bin/sync-native-plugin.py`(생성기) + `adapters/claude/plugin-marketplace/`
(생성물)로 한정 — `git status --porcelain` 상 다른 트리 변경 없음.

## 부수 관찰 (범위 밖, 정보성)

`sync()` 는 `SKILLS`/`AGENTS` 전체를 매 실행 rmtree→copytree 하는 기존 사이클 2 설계이므로,
이번 실행이 `adapters/claude/skills/*/SKILL.md` 쪽의 **기존(cycle 3 이전부터 있던) 미동기화
drift**도 함께 반영했다(다수 SKILL.md 파일 diff). 이 drift 는 이번 스테이지가 만든 게 아니라
generator 의 full-resync 동작이 이번 실행에서 드러낸 것이며, hooks/spec 재기준과 무관 — 별도
sync-skills 사이클 소관. hooks/utilities 관련 변경만 이번 스테이지 book of record.
