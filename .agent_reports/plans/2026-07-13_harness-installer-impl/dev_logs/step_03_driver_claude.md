# Step 3 — drivers/claude.py: install()/status()/checks() 실구현 (Phase 3.1 + Phase 4.2)

## 대상

`tools/install/drivers/claude.py` — `install()`/`status()` 의 `NotImplementedError` stub 과
`checks()` 의 빈 리스트 stub 을 실 로직으로 교체. Claude 는 native runtime — 생성기
(`sync-native-*.py`)도 `claude_setting/bin/preflight.sh` 도 존재하지 않으므로 재구현하지
않고, `projector.plan()` / `manifest.record()`·`check_drift()` / `verifier.check_symlink()`
등 이미 구현된 sibling 모듈만 호출한다.

## Old → New 요약

- Old: `install()`/`status()` 는 즉시 `NotImplementedError` raise, `checks()` 는 `[]`.
- New:
  - `install(scope, plugin, dry_run)` — `projector.plan(["claude"], scope=scope)["claude"]`
    를 순회하며 `symlink`/`copy_once`/`delegate`/`skip` 액션을 실 디스크 반영(또는 dry-run
    시 계획만 기록). `copy_once` 로 실제 복사된 파일들만 모아 `manifest.record()` 호출.
  - `checks(scope)` — projector plan 의 `symlink` 항목마다 `verifier.check_symlink()`,
    `copy_once` 항목마다 `verifier.check_file_exists()`, 그 위에
    `claude.build-manifest-check`(`tools/build-manifest.py --check`),
    `claude.compile-smoke`(`build-manifest.py`+`mem.py` compile), `claude.bootstrap-smoke`
    (CLI-gated) 4종 고정 check 를 덧붙인다.
  - `status(scope)` — `manifest._load_manifest(manifest._manifest_path("claude", scope))` +
    `manifest.check_drift(["claude"], scope=scope)` 조합으로 `{channel, version, file_count,
    drift_count}` 반환.

## 최종 함수 시그니처

```python
def install(scope="global", plugin=False, dry_run=False) -> dict   # {runtime, actions, blocked, manifest}
def checks(scope="global") -> list[Callable[[], dict]]              # verifier.run() 이 그대로 소비
def status(scope="global") -> dict                                  # {channel, version, file_count, drift_count}
```

## Decision (판단 콜)

1. **"real directory in the way" 방어 처리** — `symlink` dest 가 (symlink 가 아닌) 진짜
   디렉터리인 경우, `rm -rf` 로 밀어버리지 않고 `status="blocked"` + 사유를 남긴 뒤 해당
   entry 만 skip 하고 나머지 entry 는 계속 처리한다. Reason: 요청서에 명시된 대로 — 이
   케이스는 "매우 이상한 상태"이고, 실수로 사용자 데이터가 들어있는 디렉터리를 지울 위험이
   더 크다. 파일/symlink 인 경우(정상적으로 잘못 링크된 상태)는 `dest.unlink()` 로 안전하게
   제거 후 재생성 — 이건 install 재실행의 정상 경로.
2. **`copy_once` relpath = `dest.name`(파일명만)** — 요청서 지시대로 `Path(entry["dest"]).name`
   을 사용. `manifest.py` 의 `dest_abs = runtime_home / relpath` 컨벤션과 맞아떨어짐(Claude
   copy_once 대상인 `settings.json`/`keybindings.json` 이 runtime_home 바로 아래 있으므로
   파일명 = relpath). 하위 디렉터리로 옮겨질 여지가 있는 파일이 copy_once 대상에 추가되면
   이 가정이 깨지므로, 그런 변경이 생기면 projector 테이블 쪽에서 relpath 를 명시적으로
   내려주는 방식으로 바꿔야 함(현재 범위에는 없음 — 기록만 남김).
3. **`plugin=True` 처리 = 파일시스템 접촉 없는 사전 SKIP 배지 하나만 추가, symlink projection
   은 그대로 진행** — 요청서/Phase 7 boundary 그대로: plugin 채널(marketplace 콘텐츠 실물화)
   은 다음 사이클로 미뤄졌지만, 그건 `install --plugin` CLI wrapping 얘기고 기본 파일
   projection(symlink+copy_once) 자체를 막을 이유는 없다. `plugin` 플래그와 무관하게 동일한
   entries 루프가 돌고, `plugin=True` 일 때만 `{"action":"plugin","status":"skipped",...}`
   한 줄이 actions 리스트 맨 앞에 추가된다.
4. **bootstrap-smoke CLI-gate 방식** — `shutil.which("claude")` 로 CLI 존재만 먼저 판정하고,
   부재 시엔 subprocess 를 아예 실행하지 않은 채 `ok=True` + `SKIP(...)` detail 을 즉시
   반환(검증용 실행 환경에 `claude` CLI 가 실제로 설치돼 있어 이 분기는 "present" 경로로
   테스트됨 — 아래 검증 로그 참조). CLI 가 있어도 문서화된 headless bootstrap 계약이 없으므로
   `claude <subcommand>` 를 임의로 지어내 실행하지 않고 "present, no contract yet" 만 보고 —
   요청서에서 명시적으로 금지한 "unverified invocation 발명"을 피했다.
5. **`delegate`(Windows) 판정은 `os.name == "nt"` 만 체크, `dry_run` 이면 무조건 skip/planned**
   — POSIX(Linux/WSL 포함)에서는 절대 `install-windows.sh` 를 실행하지 않는다. `dry_run=True`
   상태에서 Windows 라도 subprocess 를 실행하지 않고 `status="planned"` 로만 기록(디스크
   미접촉 불변식 유지).
6. **`status()` 에서 manifest 모듈의 private 헬퍼(`_load_manifest`, `_manifest_path`) 직접
   재사용** — 요청서가 명시적으로 허용한 대로, sibling 모듈 안에서 JSON load 로직을
   중복 구현하지 않기 위해 그대로 호출. `manifest.check_drift()` 는 public API 그대로 사용.

## 검증 결과

`tempfile.mkdtemp()` 임시 `HOME` + `AGENT_HOME=<repo root>` 로만 실행 — 실제 `~/.claude`
미접촉.

```
dry-run actions: 18
(dry-run 중 임시 HOME 디렉터리 내용 없음 — assert 통과)

real install status counts: Counter({'created': 17, 'skipped': 1})
  # created 17 = symlink 15개 + copy_once 2개(settings.json, keybindings.json)
  # skipped 1  = delegate(install-windows.sh) — 비-Windows 라 스킵
symlink CLAUDE.md exists: True
settings.json is real file: True   (symlink 아님 — copy_once 정상)
manifest recorded: True

status: {'channel': 'dev',
         'version': 'a1490a1b3d20d5668efa7a059bd570ce704fd2f7',
         'file_count': 2, 'drift_count': 0}

num checks: 20
checks ok: 20 / 20
  claude.symlink.{CLAUDE.md,README.md,core,commands,skills,agents,agent-modes,
    hooks,utilities,tools,scaffolds,loops,manifest.json,statusline.sh,
    track-toggle.sh}  → 15개 모두 ok
  claude.file.settings.json / claude.file.keybindings.json → ok
  claude.build-manifest-check → ok (exit 0)
  claude.compile-smoke → ok
  claude.bootstrap-smoke → ok, detail="claude CLI present (no scripted
    bootstrap-smoke contract yet)"  # 이 실행 환경에 claude CLI 가 실제 존재 —
    absent 분기(SKIP)는 코드 경로만 확인(shutil.which 가 None 리턴 시 조기 return)

plugin=True dry_run 액션: [{'action': 'plugin', 'status': 'skipped',
  'detail': 'SKIP(claude): plugin channel — deferred to next cycle (Phase 7 boundary)'}]
```

실제 `$HOME`(재정의 전) 은 이 스크립트 실행 내내 접촉되지 않음 — `os.environ["HOME"]` 을
`import paths` 이전에(정확히는 `drivers.claude` import 이전에) 임시 디렉터리로 덮어썼고,
`paths.runtime_home()` 은 매 호출 시 `Path.home()` 을 재평가하므로 이 시점 이후의 모든
경로 계산이 temp HOME 기준으로만 이뤄짐.

## 참고 — import 경로

`projector.py`/`manifest.py` 관례를 그대로 따름 — `import paths`, `import projector`,
`import manifest`, `import verifier` 전부 절대 import(`sys.path.insert(0, "tools/install")`
전제, `drivers/__init__.py` 가 이미 `from . import claude` 로 패키지화하지만 모듈 내부에서는
sibling 을 상대 import 하지 않는 기존 컨벤션 유지).
