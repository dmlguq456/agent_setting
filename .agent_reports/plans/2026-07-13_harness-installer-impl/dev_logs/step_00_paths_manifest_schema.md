# Step 0 — paths.py 신설 + manifest.py 스키마 문서화

## 0.1 `tools/install/paths.py` (신규 파일)

새로 만든 모듈. 내용 요약:

- `agent_home()` — `AGENT_HOME` env 우선, 없으면 `Path(__file__).resolve()` 에서 위로 올라가며
  `.git` 존재(디렉터리든 파일이든 — worktree 는 `.git` 이 파일)하는 첫 조상을 리포 루트로
  판정. 둘 다 실패하면 `RuntimeError`.
- `runtime_home(runtime, scope="global")` — `claude` → `~/.claude`, `codex` → `~/.codex`,
  `opencode` → scope`project`면 `$PWD/.opencode`, 아니면 `~/.config/opencode`. 알 수 없는
  runtime 은 `ValueError`. `Path.home()` 사용 — POSIX 에서 `$HOME` env 를 그대로 존중하므로
  테스트가 `os.environ["HOME"]` 을 임시 디렉터리로 바꿔치면 그대로 반영된다.
- `opencode_data_home()` — `~/.local/share/opencode` (runtime 소유, installer 는 절대 쓰지
  않음 — 참조·점검용으로만 존재).
- `harness_state_dir(runtime, scope)` — `runtime_home(...) / ".harness"`.
- `resolve_source(relpath)` — `agent_home() / relpath`.
- `source_exists(relpath)` — `resolve_source(relpath).exists()` — `Path.exists()` 는 symlink
  를 따라가므로 `claude_setting/core` 같은 심링크 디렉터리도 정상적으로 존재로 판정된다.

## 0.2 `tools/install/manifest.py` — 모듈 docstring만 확장 (로직 변경 없음)

기존 docstring 뒤에 plan.md Phase 0 Step 0.2 의 정확한 스키마를 이식:
- `manifest.json` 의 JSON shape (`schema/runtime/scope/version/timestamp/files`)
- `pristine/<relpath>` — 설치 시점 스냅샷, drift 미해결 시 덮어쓰기 금지 원칙 명시
- `local-patches/<relpath>` + `local-patches/backup-meta.json` shape
- cycle 1 스코프 한정 — copy-once 파일만 (Claude `settings.json`/`keybindings.json` +
  Windows 사본), symlink 제외, OpenCode `opencode.json` 은 merge-managed 로 별도 취급하며
  cycle 1 은 fragment 존재 여부만 기록
- SHA-256 hex 알고리즘 통일, `tools/build-manifest.py` 키 네이밍 컨벤션 참조

`record()`/`check_drift()`/`reapply()` 함수 바디는 그대로 유지 (`NotImplementedError`/`[]`) —
Phase 2 몫.

## Decision

- **agent_home() 의 git 루트 탐지**: `.git` 이 디렉터리(일반 clone)든 파일(worktree — 안에
  `gitdir: ...` 텍스트)이든 `.exists()` 로 동일하게 판정되므로 별도 분기 없이 하나의 조건으로
  양쪽을 다 지원. worktree 안에서 실행해도 그 worktree 루트를 정확히 찾는다(검증 완료).
- **AGENT_HOME env 우선순위**: 이 쉘 세션엔 이미 `AGENT_HOME=/home/Uihyeop/agent_setting` (메인
  리포)가 설정돼 있어, worktree 안에서 실행해도 `agent_home()` 은 env 값(메인 리포)을 반환한다.
  이는 사양대로의 동작(env 최우선)이며 버그 아님 — `env -u AGENT_HOME` 으로 확인한 결과 env
  없이는 정확히 이 worktree 루트를 반환함을 별도로 검증했다.
- **runtime_home opencode project scope**: `$PWD/.opencode` 로 구현 — `Path.cwd()` 는 호출 시점
  기준이라 caller 가 프로젝트 루트에서 호출한다는 전제(다른 installer 함수들과 동일 전제)를
  따른다. 별도 프로젝트 루트 탐지 로직은 추가하지 않음(scope 정의상 "현재 프로젝트" = cwd).

## 검증 결과

```
agent_home: /home/Uihyeop/agent_setting          # AGENT_HOME env 우선 적용 (이 쉘에 설정돼 있음)
runtime_home claude: /tmp/tmpnbv8iu12/.claude
runtime_home opencode global: /tmp/tmpnbv8iu12/.config/opencode
runtime_home opencode project: /home/Uihyeop/agent_setting-wt/harness-installer-impl/.opencode
source_exists claude_setting/core: True

# env -u AGENT_HOME 재검증:
agent_home (no env): /home/Uihyeop/agent_setting-wt/harness-installer-impl
```

실제 `~/.claude`/`~/.codex`/`~/.config/opencode` 는 건드리지 않음 — 전부 임시 `HOME`(subprocess
env, 세션 밖으로 유출 안 됨) 아래에서만 확인.
