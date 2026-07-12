# Step 2 — manifest.py: hash-manifest / drift / reapply 실구현

## 대상
`tools/install/manifest.py` — Phase 0 에서 이미 작성된 모듈 docstring(스키마 문서)은 그대로
두고, `record()` / `check_drift()` / `reapply()` 의 `NotImplementedError`/빈 리스트 stub 을
실 로직으로 교체. 전부 결정론적 코드 — LLM 머지 없음 (impl-inputs §A 채택안 그대로).

## Old → New 요약

- Old: `record(runtime, files)` / `reapply(runtimes)` 는 `NotImplementedError` 즉시 raise,
  `check_drift(runtimes)` 는 항상 `[]`.
- New: 4개 헬퍼(`_sha256`, `_manifest_path`, `_pristine_path`, `_backup_path`,
  `_safe_relpath`, `_load_manifest`/`_write_manifest`, `_git_head_or_unknown`,
  `_three_way_merge`) + 3개 공개 함수 실구현.

## 최종 함수 시그니처

```python
def record(runtime, files, scope="global", version=None) -> dict          # manifest dict 반환
def check_drift(runtimes, scope="global") -> list[dict]                   # drift 목록
def reapply(runtimes, scope="global", sources=None) -> dict               # 4-bucket 결과
```

`files` = `[{"relpath", "source_abs", "dest_abs"}, ...]` (projector `copy_once` 액션 유래,
Phase 3 driver 가 조립). `sources` = `{runtime: {relpath: source_abs}}` (Phase 3 driver 가
projector plan 의 copy_once 항목에서 현재 canonical source 경로를 뽑아 전달).

## Decision (판단 콜)

1. **`reapply()` 시그니처에 `sources` kwarg 추가** (plan.md 원안엔 없던 파라미터).
   Reason: 3-way merge 의 `theirs` 인자는 "현재 repo 의 canonical source 절대경로"인데,
   `manifest.py` 자체는 어느 relpath 가 어느 runtime 의 어느 source 트리(`claude_setting/`
   vs `codex_setting/` 등)에서 왔는지 모른다 (그 매핑은 projector 테이블의 소유). 이를
   `manifest.py` 안에 하드코딩하면 projector 테이블과 이중 관리가 생기고 drift 위험이 생김.
   대신 `record()` 와 대칭적으로 `sources` 를 호출자(Phase 3 driver) 가 주입하도록 해
   "copy_once 매핑의 단일 출처 = projector 테이블" 불변식을 유지했다. 특정 relpath 에 대한
   source 가 안 오면 병합을 시도하지 않고 `verify_failed` 버킷에 `"no canonical source
   provided"` 로 기록 — 크래시 대신 안전하게 skip.

2. **anti-clobber pristine-refresh 타이밍** — pristine 은 정확히 두 시점에만 쓰인다:
   (a) `record()` 호출 시 **그 경로에 pristine 이 전혀 없을 때만** (최초 설치) — drift 여부와
   무관하게 이미 있으면 절대 덮어쓰지 않음. (b) `reapply()` 안에서 **해당 파일이 성공적으로
   merge + 결정론적 verifier 통과까지 마친 직후에만** — 그 파일의 pristine 을 새 canonical
   bytes(`source_abs`)로 교체. `conflict`/`verify_failed`/`no-git-merge-file`/missing-source
   경로에서는 pristine 을 절대 건드리지 않는다. Reason: pristine 은 다음 3-way merge 의
   `base` — drift 가 미해결인 채로 최신 릴리스 사본으로 덮으면 base 가 사용자 수정 이전
   상태를 잃어버려 이후 merge 가 사용자 edit 을 diff 로 인식 못 하게 된다 (impl-inputs §A
   함정 #3407, docstring 에도 이미 명시돼 있던 규칙 — 구현에서 그대로 지켰다).

3. **`git merge-file` 부재 시 degrade path** — `subprocess.run(["git","merge-file",...])` 가
   `FileNotFoundError` 를 던지면(즉 `git` 이 PATH 에 없음) 함수 전체를 죽이지 않고, 이미
   1단계(pre-wipe backup)는 끝난 상태이므로 그대로 두고 `conflicts` 버킷에
   `{"status": "no-git-merge-file"}` 항목만 추가한 뒤 다음 파일로 넘어간다. Reason: plan.md
   Risks 절에 명시된 문서화된 degrade 경로 — 백업은 이미 안전하게 떠 있으니(사용자 데이터
   유실 없음) 자동 머지만 포기하고 사람이 나중에 `local-patches/` 에서 수동 처리하게 report.
   전체 `reapply()` 호출을 중단시키지 않음 — 다른 runtime/파일은 계속 처리.

4. **`_safe_relpath` 구현 방식** — 절대경로/`..` 세그먼트/NUL 은 직접 문자열·`Path.parts`
   검사로 거르고, 추가로 고정 sentinel base(`/__manifest_safe_base__`)에 대해
   `(base / relpath).resolve()` 후 `relative_to(base)` 로 최종 이탈 여부를 재검증한다
   (zip-slip 류 우회 방지 — symlink 트릭 등으로 앞의 문자열 검사를 통과해도 최종 resolve
   단계에서 걸리게). `record`/`check_drift`/`reapply` 세 함수 모두 manifest 유래 relpath 를
   쓰기 전에 반드시 이 함수를 통과시킨다.

5. **`check_drift` 의 "manifest 없음" vs "파일 없음" 구분** — plan.md 원문 표현("Missing
   dest = manifest file absent")을 문자 그대로 읽으면 헷갈리지만, 요청서 지시대로
   재해석했다: **runtime 전체의 manifest.json 이 없으면** 그 runtime 은 조용히 skip (아직
   설치 안 된 것 — drift 아님). **manifest 안에 등재된 개별 relpath 의 dest 파일이 디스크에
   없으면** `{"detail": "file missing"}` 으로 drift 목록에 넣는다. 두 케이스를 섞으면
   미설치 runtime 이 매번 거짓 drift 로 잡혀 `update` 가 항상 `EXIT_DRIFT` 를 뱉는 사고가
   난다.

6. **3-way merge 후 결정론적 verifier는 backup 전체 라인 대상** — plan.md 132행 지시를
   문자 그대로 구현(백업 파일의 모든 non-blank 라인이 병합 결과에 substring 으로 있어야
   통과). 검증 중 발견한 부작용: canonical 이 **사용자가 손대지 않은 기존 라인의 값 자체를
   바꾸는** 릴리스(예: `"a": 1` → `"a": 10`)는 라인 텍스트가 아예 달라지므로 이 verifier 가
   `verify_failed` 로 보수적으로 막는다 (merge 자체는 conflict 없이 깨끗해도). 이는 버그가
   아니라 설계된 보수적 동작으로 해석했다 — "애매하면 사용자 데이터 유실보다 report 후
   수동 처리" 원칙과 일치. 검증 스크립트는 이 특성에 맞춰 canonical 변경이 **새 키 추가**인
   케이스로 fixture 를 구성했다(§검증 결과 참조).

## 검증 결과

read-only, `tempfile.mkdtemp()` 임시 `HOME` 안에서만 실행 — 실제 `~/.claude` 등 손대지 않음.

**정상 3-way merge (canonical = 새 키 추가, user = 새 키 추가, 서로 겹치지 않는 라인)**
```
record() -> {"schema": 1, "runtime": "claude", "scope": "global",
             "version": "24e2295...", "timestamp": "...",
             "files": {"settings.json": "080d51f4...e59224"}}   # 64-hex sha256
pristine exists: True
drift before edit: []
drift after edit: [{'runtime': 'claude', 'path': 'settings.json', 'detail': 'hash mismatch'}]
reapply() -> {"reapplied": [{"runtime": "claude", "path": "settings.json"}],
              "conflicts": [], "verify_failed": [], "missing": []}
dest content after reapply:
{
  "new_feature": "on",
  "a": 1,
  "b": 2,
  "user_added": true
}
backup exists: True
backup-meta: {"from_version": "24e2295...", "pristine_hashes": {"settings.json": "080d51f4..."}}
pristine after reapply:
{
  "new_feature": "on",
  "a": 1,
  "b": 2
}
drift after reapply: []
ALL OK
```
→ 핵심 불변식 확인: reapply 이후 `dest` 에 **새 canonical 변경(`new_feature`)과 사용자
edit(`user_added`) 이 동시에** 남아 있음. `check_drift` 재실행 결과 `[]` — manifest hash 가
merge 결과와 동기화됨.

**충돌 케이스** (user 와 canonical 이 같은 라인을 서로 다른 값으로 수정):
```
conflict-case reapply -> {"reapplied": [], "conflicts": [{"runtime": "claude",
    "path": "settings.json", "status": "conflict"}], "verify_failed": [], "missing": []}
```
`dest` 는 grep 으로 확인 — 사용자의 `"a": 999` 값 그대로 유지(강제 머지 안 함, 파일 미변경).

**파일 소실 케이스** (drift 대상 파일 자체가 사라짐):
```
drift with missing file: [{'runtime': 'claude', 'path': 'settings.json', 'detail': 'file missing'}]
missing-file reapply -> {"reapplied": [], "conflicts": [], "verify_failed": [],
    "missing": [{"runtime": "claude", "path": "settings.json"}]}
```

세 시나리오 모두 `git merge-file` 이 설치돼 있는 환경에서 실행(로컬 git 존재) — `git` 부재
degrade path(`no-git-merge-file`)는 코드 리뷰로만 확인, 별도 격리 실행은 안 함(로컬 git
바이너리를 PATH 에서 빼는 건 이 세션 다른 작업에 영향 줄 수 있어 스킵).

## 참고 — import 경로

`projector.py` 관례(`import paths`, 절대 import, `sys.path.insert(0, "tools/install")` 로
실행)를 그대로 따랐다 — 처음에 `from . import paths` 로 썼다가 실행 시
`ImportError: attempted relative import with no known parent package` 나서 절대 import 로
수정.
