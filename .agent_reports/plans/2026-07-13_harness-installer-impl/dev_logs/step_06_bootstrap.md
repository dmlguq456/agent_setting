# Step 6 — bootstrap.py (mem import + ~/.local/bin launcher symlinks)

## 산출물
- `tools/install/bootstrap.py` (신규) — `restore_memory()`, `install_launchers()`.
- `drivers/*.py`, `projector.py`, `manifest.py`, `installer.py` 는 건드리지 않음 (Phase 5 소관, 이번 phase 는 helper 함수만 구현·standalone 검증).

## Decision

**MEM_STORE 해석 우선순위**: `restore_memory(mem_store=...)` 파라미터 > `MEM_STORE` env > `paths.agent_home() / "memory"` 기본값. 이 순서는 plan.md Step 6.1 이 요구하는 "temp HOME 아래서는 `MEM_STORE` override 를 존중해 실제 memory repo 를 안 건드려야 한다"는 요건과, installer.py 가 나중에 wiring 할 때 명시 인자로 override 할 수 있게 하는 두 필요를 동시에 만족시키기 위함. `mem.py` 자신도 `STORE = Path(os.environ.get("MEM_STORE", AGENT_HOME / "memory"))` 로 동일한 env 를 읽으므로, `restore_memory` 가 subprocess 호출 시 `env={**os.environ, "MEM_STORE": str(mem_store)}` 를 넘겨 mem.py 내부 경로 계산과 우리 쪽 idempotency 체크(`mem_store/memory.db` 존재 여부)가 항상 같은 디렉터리를 가리키게 맞췄다.

**launcher collision-detection 규칙**: `target.exists() or target.is_symlink()` 로 먼저 "뭔가 있다"를 판정한 뒤(존재하지 않는 symlink 대상, 즉 broken symlink 도 `is_symlink()` 는 True 라 이 분기에 걸린다), `_is_our_symlink(target, source)` — `target.is_symlink() and target.resolve() == source.resolve()` — 로 "그게 우리 심볼릭 링크인가"를 판정한다. 우리 링크면 `unchanged`, 그 외(진짜 foreign 파일이든, 다른 곳을 가리키는 symlink 든, broken symlink 든) 전부 `skipped-collision` 으로 처리하고 **덮어쓰지 않는다** — INST-OPEN-2 가 요구하는 "우리가 만든 게 아니면 절대 clobber 하지 않는다"는 안전 원칙을 가장 보수적으로 만족시키기 위한 선택이다. plan.md 의 "stale symlink to something else that isn't a foreign real file 은 relink 가능" 이라는 문구도 검토했으나, symlink 대상이 다른 경우와 진짜 foreign 파일을 구분하는 추가 로직은 오탐 위험(예: 사용자가 자기 dotfiles 관리 도구로 다른 위치에 심볼릭 링크 걸어둔 경우)이 더 커서, "우리 심볼릭 링크가 아니면 전부 스킵"으로 단순화했다. 이렇게 해도 Done-when 요건(foreign harness → skip, 우리 symlink 재실행 → unchanged)은 정확히 만족된다.

**mem import subprocess 실패 시 미-raise**: `restore_memory` 는 install 파이프라인 안에서 "있으면 좋은" 부가 기능(memory 복원)이지 install 성패를 좌우하는 필수 스텝이 아니다. mem import 가 실패해도(예: dump.jsonl 이 스키마상 필수 컬럼 — `tier`/`scope`/`type` 등 NOT NULL — 을 갖추지 못한 손상된 덤프인 경우) `harness install` 전체가 죽어서는 안 되고, 사용자에게 "memory 복원은 실패했지만 나머지 설치는 정상"이라는 신호만 주면 된다. 그래서 `subprocess.run(...).returncode` 를 확인만 하고 `check=True`/raise 를 쓰지 않았으며, stderr 앞 300자를 `detail` 에 담아 진단 가능하게 했다.

## Verification

standalone 스크립트(과제 지정, temp dir 만 사용, 실제 `$HOME/.local/bin`·실제 memory repo 미접촉) 실행 결과:

```
restore_memory (fresh dump): {'action': 'failed', 'detail': 'mem import failed: exit=1 stderr=...IntegrityError: NOT NULL constraint failed: records.tier'}
memory.db created: True
restore_memory (idempotent re-run): {'action': 'skipped', 'detail': 'memory.db already present'}
restore_memory (no dump, no db): {'action': 'skipped', 'detail': 'no dump.jsonl to restore from, and no existing memory.db'}
dry-run launcher plan: [...status: planned x2...]  (.local 디렉터리 미생성 확인)
real launcher install: [...status: created x2...]
harness symlink: True
fleet symlink: True
idempotent re-run: [...status: unchanged x2...]
collision-guard result: [harness: skipped-collision, fleet: created]
ALL OK
```

모든 `assert` 통과 — idempotency(`r2`/`r6` 전부 unchanged), dry-run 무변경(`.local` 미생성), collision-guard(`skipped-collision`) 전부 확인됨.

**주석**: `r1`(최초 mem import)이 과제에 주어진 probe dump(`{"id":"t1","type":"note","body":"probe","tags":[],"links":[]}`)로는 `failed` 로 떨어졌다 — 이는 `bootstrap.py` 버그가 아니라 `mem.py` `import_dump()` 가 `RECORD_COLS` 의 NOT NULL 컬럼(`tier` 등)에 대한 기본값 채움을 `strength`/`last_accessed`/`injection_flag` 세 개만 해주고 `tier`/`scope`/`type`/`cwd_origin` 은 안 해주기 때문이다(라인 1790-1805 확인). 과제 스크립트도 `r1` 의 `action` 값을 assert 하지 않아 이 케이스로 인한 실패는 없다. 별도로 완전한 스키마(`tier`/`scope`/`type`/`created`/`updated`/`strength`/`last_accessed`/`injection_flag` 등 `RECORD_COLS` 전체)를 갖춘 dump 로 재검증한 결과 `{'action': 'imported', ...}` 로 happy-path 정상 동작을 확인했다:

```
{'action': 'imported', 'detail': 'mem import from /tmp/mem_full_test/dump.jsonl'}
```

## Blocking issues
없음. `tools/memory/mem.py` 는 읽기만 했고 수정하지 않음(Phase 6 scope 밖). `installer.py`/`drivers/*.py`/`projector.py`/`manifest.py` 미접촉.
