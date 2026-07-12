# Step 3 — drivers/codex.py: install()/status()/checks() 실구현 (Phase 3.2 + Phase 4.3)

## 대상

`tools/install/drivers/codex.py` — `install()`/`status()` 의 `NotImplementedError` stub 과
`checks()` 의 빈 리스트 stub 을 실 로직으로 교체. Codex 는 `sync-native-*.py` 생성기와
`preflight.sh` 를 가진 non-native runtime 이지만, projection 자체는 순수 symlink 뿐
(copy_once/merge 없음) — `projector.plan()` / `manifest.record()`·`check_drift()` /
`verifier.check_symlink()`·`check_cmd()` 등 이미 구현된 sibling 모듈만 호출한다.

## Old → New 요약

- Old: `install()`/`status()` 는 즉시 `NotImplementedError` raise, `checks()` 는 `[]`.
- New:
  - `install(scope, plugin, dry_run)` — `projector.plan(["codex"], scope=scope)["codex"]`
    (fixed symlinks + codex-skills/*·codex-agents/*.toml glob 이 이미 펼쳐진 상태) 를 순회하며
    `symlink`/`skip` 액션만 실 디스크 반영(또는 dry-run 시 계획만 기록). `plugin=True` 여도
    이 루프는 무조건 실행되고, 그 뒤에 `plugin` action 한 줄만 추가(SKIP 배지, Phase 7 자리).
    copy_once 파일이 없으므로 `manifest.record("codex", [], scope=scope)` 를 빈 files map 으로
    호출해 version/timestamp 만 스탬프.
  - `checks(scope)` — projector plan 의 `symlink` 항목마다 `verifier.check_symlink()`
    (`dest.parent.name` + `dest.name` 합성 id 로 basename 충돌 회피), 그 위에
    `codex.sync-native-{skills,agents,modes,plugin}` 4종 `check_cmd`,
    `codex.preflight.{capability-info,role}` 2종 `check_cmd`, `codex.bootstrap-smoke`
    (CLI-gated custom closure) 를 덧붙인다.
  - `status(scope)` — `manifest._load_manifest(manifest._manifest_path("codex", scope))` +
    `manifest.check_drift(["codex"], scope=scope)` 조합에 `pointer_present`(agent-harness
    symlink 존재)·`plugin_marketplace_source_present`(marketplace source dir 존재)·
    `plugin_registered=None`(Phase 7 TODO) 를 더해 반환.

## 최종 함수 시그니처

```python
def install(scope="global", plugin=False, dry_run=False) -> dict   # {runtime, actions, blocked, manifest}
def checks(scope="global") -> list[Callable[[], dict]]              # verifier.run() 이 그대로 소비
def status(scope="global") -> dict                                  # {channel, version, drift_count,
                                                                      #  pointer_present,
                                                                      #  plugin_marketplace_source_present,
                                                                      #  plugin_registered}
```

## Decision (판단 콜)

1. **"real file/dir in the way" 방어 처리(clobber 금지)** — `symlink` dest 가 (symlink 가 아닌)
   진짜 파일이든 디렉터리든 상관없이 밀어버리지 않고 `status="blocked"` + 사유를 남긴 뒤 해당
   entry 만 skip, 나머지 entry 는 계속 처리한다. Reason: codex 는 vanilla 설치에서 사용자가
   `~/.codex/AGENTS.md` 를 이미 real file 로 갖고 있는 첫 사용자 케이스가 실제로 있을 수 있음
   (요청서에 명시) — Claude driver 는 "real 디렉터리"만 방어했지만 codex 는 파일(AGENTS.md)도
   같은 위험군이라 `dest.exists() and not dest.is_symlink()` 로 파일/디렉터리 모두 커버.
   symlink 인 경우(정상적으로 잘못 링크된 상태, stale/wrong target 포함)는 `dest.unlink()` 로
   안전하게 제거 후 재생성 — install 재실행의 정상 경로.
2. **`already_linked` 판정은 `os.readlink()` 문자열 비교로, `.resolve()` 비교를 쓰지 않음** —
   요청서 지시대로 `Path(os.readlink(dest)) == source` 만 사용. Claude driver 는
   `dest.resolve() == source.resolve()` 를 우선 시도했지만, codex 는 source 자체가 아직 없는
   (glob 확장 전 등) 경우도 있을 수 있어 `.resolve()` 가 실패하거나 오탐할 여지가 있음 —
   readlink 직접 비교가 "source 존재 여부와 무관하게" resolve-safe.
3. **`plugin=True` 처리 = symlink projection 은 절대 스킵하지 않고, 그 뒤에 `plugin` action
   한 줄만 추가(INST-D-5)** — 요청서/scaffold docstring 에 명시된 대로: "plugin 이면 symlink
   생략"은 명시적 anti-pattern. custom agents `.toml`/prompts/config.toml fragment/AGENTS.md
   는 plugin 채널이 절대 못 싣는 표면이라, `plugin` 플래그 값과 무관하게 동일한 entries 루프가
   먼저 돌고 `plugin=True` 일 때만 `{"action":"plugin","status":"skipped",...}` 이 actions
   리스트 끝에 추가된다. 검증 스크립트에서 `plugin=True actions include symlinks: True` 로
   이 불변식을 명시적으로 확인.
4. **bootstrap-smoke CLI-gate + 실행 방식** — `shutil.which("codex")` 로 CLI 존재만 먼저
   판정하고, 부재 시엔 tempdir 도 안 만들고 즉시 `ok=True` + `SKIP(...)` 반환. CLI 존재 시엔
   Claude driver 와 달리 실제 실행 계약이 문서화돼 있어(`INSTALL_LAYOUT.md` Migration Order
   line ~343-344) `codex debug prompt-input 'bootstrap check'` 를 `CODEX_HOME=<tmp>` 로 실행하고
   stdout 에서 `"AGENTS.md — Codex Adapter Bootstrap"` 마커를 검색 — Claude 처럼 "present, no
   contract yet" 로 얼버무리지 않고 실 스모크를 돌린다(계약이 있으므로). tempdir 은
   `finally: shutil.rmtree(..., ignore_errors=True)` 로 항상 정리해 검증 실행이 흔적을 남기지
   않게 함.
5. **`checks()` symlink check id 충돌 회피 — `parent.name + name` 합성** — codex-skills/*
   와 codex-agents/*.toml 두 glob 모두 basename 이 겹칠 수 있어(예: 여러 서브디렉터리에 같은
   이름 파일) `f"codex.symlink.{dest_path.parent.name}.{dest_path.name}"` 로 상위 디렉터리명을
   접두. Claude driver 는 flat 한 고정 목록이라 basename 만으로 충분했지만 codex 는 glob
   fan-out 이 있어 이 방식이 필요.
6. **`status()` 에서 manifest 모듈의 private 헬퍼(`_load_manifest`, `_manifest_path`) 직접
   재사용** — Claude driver 와 동일한 관례. `manifest.check_drift()` 는 public API 그대로 사용.
7. **`plugin_registered=None` 을 추측으로 채우지 않음** — "codex 쪽에 실제 등록됐는지"는
   `codex plugin marketplace list` 호출이 필요한데 이는 Phase 7 wrapping 의 일부라 이번
   사이클에는 구현하지 않는다. `False` 로 단정하면 거짓 정보가 되므로 `None` + 주석으로
   "아직 모름"을 명시(요청서가 정확히 지시한 "honest placeholder, not a guess").

## 검증 결과

`tempfile.mkdtemp()` 임시 `HOME` + `AGENT_HOME=<repo root>` 로만 실행 — 실제 `~/.codex`
미접촉.

```
dry-run actions: 54
(dry-run 중 임시 HOME 디렉터리 내용 없음 — assert 통과)

real install status counts: {'created'}   # blocked 항목 없음(첫 실행, 충돌 없음)
blocked: False

agent-harness pointer is symlink: True
AGENTS.md is symlink: True
sample skill symlink exists: True

plugin=True actions include symlinks: True   # INST-D-5 불변식 확인
plugin=True plugin-marker action: [{'action': 'plugin', 'status': 'skipped',
  'detail': 'codex plugin marketplace/add wrapping — Phase 7 (not yet implemented
  in this dispatch), symlink projection still applied above (INST-D-5)'}]

status: {'channel': 'dev',
         'version': 'a1490a1b3d20d5668efa7a059bd570ce704fd2f7',
         'drift_count': 0, 'pointer_present': True,
         'plugin_marketplace_source_present': True,
         'plugin_registered': None}

num checks: 61   # symlink(54개 중 skip 없음 → 54) + sync-native 4 + preflight 2 + bootstrap 1
```

checks() 실행 결과 전수 확인(추가 실행, install 이미 적용된 상태):

```
codex.sync-native-skills   True  OK: python3 adapters/codex/bin/sync-native-skills.py --check
codex.sync-native-agents   True  OK: python3 adapters/codex/bin/sync-native-agents.py --check
codex.sync-native-modes    True  OK: python3 adapters/codex/bin/sync-native-modes.py --check
codex.sync-native-plugin   True  OK: python3 adapters/codex/bin/sync-native-plugin.py --check
codex.preflight.capability-info  True  OK: adapters/codex/bin/preflight.sh capability-info autopilot-code
codex.preflight.role             True  OK: adapters/codex/bin/preflight.sh role fast reviewer
codex.bootstrap-smoke      True  OK: AGENTS.md bootstrap marker found via codex debug prompt-input
```

전부 통과 — 이 샌드박스에 `codex` CLI 가 실제로 설치돼 있어 `codex.bootstrap-smoke` 도
SKIP 이 아닌 실 실행 경로(present)로 테스트됨. sync-native/preflight 스크립트도 이미
`adapters/codex/bin/` 아래 존재·실행 가능 상태라 환경 이슈·버그 모두 발견되지 않음.

blocked-detection 경로 별도 확인 — 임시 `~/.codex/AGENTS.md` 를 real file 로 미리 만들어
둔 뒤 install 실행:

```
blocked: True
[{'action': 'symlink', 'source': '.../codex_setting/AGENTS.md',
  'dest': '.../.codex/AGENTS.md', 'status': 'blocked',
  'detail': "dest is a real file/dir, refusing to overwrite: ... "
            "(e.g. a pre-existing vanilla codex AGENTS.md — surface, don't clobber)"}]
```

실제 `$HOME`(재정의 전) 은 이 스크립트 실행 내내 접촉되지 않음 — `os.environ["HOME"]` 을
`drivers.codex` import 이전에 임시 디렉터리로 덮어썼고, `paths.runtime_home()` 은 매 호출
시 `Path.home()` 을 재평가하므로 이 시점 이후의 모든 경로 계산이 temp HOME 기준으로만
이뤄짐.

## 참고 — import 경로

`projector.py`/`manifest.py`/`drivers/claude.py` 관례를 그대로 따름 — `import paths`,
`import projector`, `import manifest`, `import verifier` 전부 절대 import
(`sys.path.insert(0, "tools/install")` 전제, sibling 모듈은 상대 import 하지 않는 기존
컨벤션 유지).
