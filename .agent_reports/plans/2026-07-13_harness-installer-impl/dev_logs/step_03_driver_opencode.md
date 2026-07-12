# Step log — Phase 3 Step 3.3 + Phase 4 Step 4.4: drivers/opencode.py

## 변경 파일
- `tools/install/drivers/opencode.py` — `install()`/`status()`/`checks()` 실 구현 (기존 `NotImplementedError`/`[]` scaffold 대체)

## Decision

**1. project-scope `opencode.json` 경로 단순화.**
`paths.runtime_home("opencode", scope)` 는 global→`~/.config/opencode`, project→`<cwd>/.opencode` 를 돌려준다. `INSTALL_LAYOUT.md` 의 project 예시는 실제로는 `opencode.json`을 프로젝트 **루트**(`<cwd>/opencode.json`, `.opencode/` 밖)에 두는 그림이지만, 이번 사이클은 두 scope 모두 `runtime_home(scope) / "opencode.json"` 으로 통일했다 (`_config_path()`). 즉 project scope 에서도 `<cwd>/.opencode/opencode.json` 을 본다 — `<cwd>/opencode.json`(루트) 이 아니다. plan.md 지시대로 "known simplification, not a blocker"로 문서화만 하고 넘어감. 다음 사이클에서 project-root 배치가 필요하면 `_config_path()` 하나만 고치면 되도록 함수로 격리해뒀다.

**2. conflict 판정 규칙 (exact rule).**
`_merge_config()`:
- `instructions` 키 부재 → `[our_path]` 로 신설(merged, changed=True).
- `instructions` 가 list 이고 우리 경로가 이미 있으면 no-op(unchanged). 없으면 append(다른 엔트리 보존, merged, changed=True).
- `instructions` 가 list 가 **아니면** → 즉시 conflict: `blocked=True`, `existing` 그대로 반환(수정 안 함), detail 텍스트 고정 문구 반환. `skills`/`skills.paths` 도 동일 규칙 — `skills` 키가 dict 아니거나 `skills.paths` 가 list 아니면 blocked.
- conflict 가 하나라도 나면 그 `merge` 항목만 `status:"blocked"` 로 기록하고 `install()` 전체의 `blocked=True` 를 세팅 — 그러나 **이미 처리된 symlink 액션은 롤백하지 않는다** (plan.md 의 BLOCKED = stop+report, undo 아님 지시 그대로).
- 검증: 사전에 `{'instructions': 'not-a-list'}` 로 seed 한 뒤 재설치 시 `blocked=True`, 파일은 덮어쓰지 않음(그 seed 값 그대로 남음) — 확인됨.

**3. drift-watch sentinel 탐지 방법 (Phase 4.4d).**
`_drift_watch_sentinel()`:
- 버전: `shutil.which("opencode")` → 있으면 `opencode --version` best-effort 캡처(실패해도 sentinel 자체는 안 죽음, "version unknown" 텍스트로 대체).
- plural 신호: `Path.home()/.config/opencode/{skills,commands,agents,plugins}` 4개 경로가 **실제 디렉터리로 존재**하는지 확인 (심링크가 아니라 진짜 dir인지까지는 구분 안 함 — `is_dir()` 은 심링크가 디렉터리를 가리켜도 True 이므로, 필요하면 향후 `is_symlink()` 배제 로직 추가 여지 있음).
- 항상 `ok=True`(정보성 sentinel, gate 아님) — `detail` 에 버전 + 발견/미발견 여부를 문장으로 기록.

**⚠️ 알려진 한계(caveat, 이번 사이클 미수정)**: 기존 `projector.py`의 opencode 고정 심링크 표(`_OPENCODE_FIXED_SYMLINKS`)가 plugin guard js 를 `"plugins/agent-harness-guards.js"` 라는 dest 경로로 심어서, 설치 자체가 `~/.config/opencode/plugins/` 라는 **실 디렉터리**(심링크 컨테이너)를 항상 만든다. 이 때문에 sentinel 의 4-후보 중 `plugins` 는 설치 직후 매번 "존재"로 잡혀 "plural 감지" 분기가 오탐(false positive)으로 뜬다 — 실측 검증 시 확인됨 (`opencode.drift-watch` 결과가 "plural dirs ... DETECTED" 로 나왔고, 원인은 `skills`/`commands`/`agents` 가 아니라 우리 자신이 만든 `plugins/` 컨테이너 디렉터리였다). Sentinel 은 informational-only(`ok=True` 고정)라 verify 를 fail 시키지는 않지만, `detail` 텍스트의 정확도는 떨어진다. 다음 사이클 후보 개선: (a) `plugins` 를 후보에서 빼거나 (b) 우리가 만든 `plugins/agent-harness-guards.js` 심링크 존재를 먼저 빼고 "그 외 파일이 있는 plugins/" 인지로 좁히기. plan.md 지시(Path.home()/.config/opencode/{skills,commands,agents,plugins} 그대로 확인)를 문자 그대로 따르되, 이 collision 은 caveat 로만 기록.

## 검증 결과 (throwaway mktemp HOME, 실제 `~/.config/opencode` 미접촉)

```
dry-run actions: 51                      # disk 미접촉 확인(tmp_home 빈 상태 assert 통과)
blocked: False
install status counts: {'created', 'merged'}
opencode.json exists: True
instructions: ['.../opencode_setting/AGENTS.md']
skills.paths: ['.../opencode_setting/opencode-skills']
second-run merge status: [{'action': 'merge', 'status': 'unchanged', 'detail': 'unchanged'}]  # 멱등성 확인
conflict blocked: True                   # non-list instructions seed 후 blocked 확인
conflict actions: [{'action': 'merge', 'status': 'blocked', 'detail': "... 'instructions' key exists with a non-list value — refusing to merge, manual resolution required"}]
status: {'channel': 'dev', 'version': '<repo-sha>', 'drift_count': 0, 'pointer_present': True, 'config_merged': False}
num checks: 57
```

- 전체 57개 check 모두 `ok: True` (symlink 51개 + sync-native 3개 + preflight 2개 + drift-watch 1개(sentinel, 로컬에 opencode 1.17.13 실치돼 있어 실행됨) + bootstrap-smoke 1개(`opencode debug config --pure` stdout 에 `opencode_setting/AGENTS.md` 확인됨)).
- `status()`의 `config_merged: False` 는 마지막 conflict 테스트 단계에서 `opencode.json`을 `{'instructions': 'not-a-list'}` 로 덮어썼기 때문(의도된 시퀀스 — 파일 자체는 안 건드렸지만 status 재조회 시점엔 이미 conflict 상태 파일).
- dry-run 이 디스크에 아무것도 안 만든다는 것은 `assert not os.listdir(tmp_home)` 로 확인.

## 블로킹 이슈
없음. 위 caveat(plugins 디렉터리 오탐)만 기록, verify 는 항상 통과(sentinel 이 정보성이라 gate 아님).
