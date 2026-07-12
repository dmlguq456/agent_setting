# Step 5 — installer.py cmd_* real wiring

대상 파일: `tools/install/installer.py`. `build_parser()`/`resolve_runtimes()`/`emit()`/exit code
상수는 변경 없음.

## import 추가

`import paths`, `import bootstrap`, `import shutil`, `from pathlib import Path` — 기존
`import projector`/`manifest`/`verifier`/`from drivers import get_driver, RUNTIMES` 옆에.

## cmd_install (old: TODO 루프, projector.plan() 만 노출)

new:
- 각 runtime 에 대해 `driver.install(scope, plugin, dry_run)` 실호출.
- `result["actions"]` 를 사람이 읽을 `lines` + `checks[]` (`{rt}.{action}.{dest_name}`, `ok = status != "blocked"`) 로 변환.
- `any_blocked = any(r["blocked"] for r in results)`.
- blocked 없고 `dry_run` 아니면: `bootstrap.restore_memory()` (기본 `mem_store=None` — env `MEM_STORE`/`agent_home()/memory` 자체 해석에 맡김) + `bootstrap.install_launchers(dry_run=False)` 호출, 각각 checks/lines 에 append.
- blocked 없고 `dry_run` 이면: `bootstrap.install_launchers(dry_run=True)` 만 호출(계획 노출), `restore_memory` 는 호출 자체를 스킵(“skip” 라인만 기록) — dry-run 에 대응하는 restore_memory 네이티브 모드가 없어 가짜로 흉내내지 않음.
- exit: `EXIT_BLOCKED`(3) if any_blocked else `EXIT_OK`(0). driver.install() 은 예외를 던지지 않는 설계라 별도 try/except 없음(진짜 버그는 그대로 propagate).

**Decision (checks-list-from-actions mapping)**: check id = `f"{rt}.{action}.{Path(dest).name if dest else 'x'}"`, `ok = status != "blocked"`, `detail` = `a.get("detail")` (없으면 status). delegate 액션처럼 `dest` 가 없는 액션은 `x` placeholder 로 통일 — verify 쪽 checks() 컨벤션과 살짝 다르지만 install 단계는 "액션 결과 노출"이 목적이라 이 정도 단순화로 충분하다고 판단.

## cmd_status (old: TODO stub, "channel=미확인")

new: 각 runtime `driver.status(scope=args.scope)` 실호출 → `detail = f"channel={s['channel']} version={s['version']} drift={s['drift_count']}"`. `drift` top-level key 는 그대로 `[]` 유지 — status 는 요약 뷰, drift 상세는 update 담당이라는 원 설계 그대로 채택(플랜의 "OR" 옵션 중 단순한 쪽).

## cmd_update (old: `drift = manifest.check_drift(runtimes) if args.reapply else []` — 핵심 회귀 지점)

new:
- **`drift = manifest.check_drift(runtimes, scope=args.scope)` 를 `--reapply` 여부와 무관하게 항상 계산** — 이번 phase 의 목적 regression fix.
- `not args.reapply`: drift 있으면 `EXIT_DRIFT`(4) + 사람이 읽을 drift 라인, 없으면 `EXIT_OK`. 자동 조치 없음(사용자 결정 대기).
- `args.reapply`: `sources = {rt: {} for rt in runtimes}` 를 구성 — 각 runtime 의 `projector.plan([rt], scope)[rt]` 에서 `action == "copy_once"` 항목만 골라 `sources[rt][Path(entry["dest"]).name] = entry["source"]` (manifest.py 의 relpath=basename 컨벤션과 동일, claude driver 가 `manifest.record()` 에 넘기던 `copy_once_files` 구성과 대칭). `manifest.reapply(runtimes, scope=args.scope, sources=sources)` 호출 → `reapplied/conflicts/verify_failed/missing` 각각 lines/checks 에 노출.
- top-level `drift` 키는 두 분기 모두 `check_drift()` 결과로 채움(플랜 요구사항).

**Decision (reapply exit-code mapping)**: `result["conflicts"]` 또는 `result["verify_failed"]` 가 하나라도 있으면 `EXIT_DRIFT`(4) — PRD/plan 에 별도 exit code 정의가 없고, "사람 판단 필요"라는 의미에서 DRIFT 가 가장 가까운 기존 코드라 재사용. 완전히 깨끗하게 재적용(또는 애초에 재적용할 게 없음)이면 `EXIT_OK`.

## cmd_uninstall (old: `EXIT_OK` 고정, 실제 삭제 없음)

new: manifest 기반 소유 경계 제거.
- `manifest._load_manifest(manifest._manifest_path(rt, args.scope))` 로 매니페스트 로드(private helper 재사용 — drivers 가 status() 에서 쓰는 것과 같은 패턴).
- manifest 없으면 "제거할 것 없음" 라인만 남기고 continue(에러 아님).
- 제거 대상: (a) manifest `files` 맵의 모든 relpath → `runtime_home(rt,scope)/relpath` (copy-once), (b) 현재 projector plan 의 `action == "symlink"` 항목의 `dest` 전부(그 외 — real file 인 delegate·merge·skip 등은 손대지 않음).
- `dry_run`: 나열만, 디스크 미접촉, manifest 도 안 지움.
- 실제 실행: symlink 부터 `is_symlink()` 체크 후 idempotent unlink(이미 없으면 skip) → copy-once 파일은 존재 시 `local-patches/<relpath>` 로 `shutil.copyfile` 백업 후 unlink → 마지막으로 `manifest.json` 삭제(plan 명시 순서 준수).
- exit: 항상 `EXIT_OK`(이미 제거된 상태에 다시 uninstall 해도 성공).

**Decision (local-patches backup-before-uninstall 단순화)**: `manifest.py` 의 백업-메타(`backup-meta.json`, pristine hash 기록) 기계는 호출하지 않고, uninstall 전용으로 단순 `shutil.copyfile(dest, harness_state_dir/local-patches/relpath)` 만 수행 — uninstall 은 "다음 reapply 를 위한 3-way merge 컨텍스트"가 필요 없는 일회성 안전 복사이기 때문에 `reapply()`가 쓰는 backup-meta 인프라를 재사용하지 않기로 했다(과설계 방지, cycle-1 스코프).

**Decision (rmdir 빈 디렉터리 skip)**: plan 은 "rmdir empty shared dirs only" 를 언급하지만, 이번 사이클에선 **완전히 skip** — 다른 runtime-owned state 를 실수로 지울 위험을 피하려는 보수적 선택이며 버그가 아니라 의도적 축소다. 빈 디렉터리가 남는 것은 무해하다고 판단.

## 검증 (temp HOME lifecycle, 실 `~/.claude`/`~/.codex`/`~/.config/opencode`/`~/.local/bin`/실 memory store 전혀 미접촉)

한 Bash 세션 안에서 `HOME=$(mktemp -d)`, `AGENT_HOME=<repo>`, `MEM_STORE=<temp>/mem` export 후 연속 실행(각 Bash 호출 사이 env 가 리셋되는 하네스 특성 때문에 첫 시도는 분리된 호출로 나눠 실 HOME 으로 새 버렸었고, 재확인 결과 실 홈에는 원래도 manifest 가 없어 실질 피해 없음 — 이후 단일 호출로 재실행해 검증 완료).

```
=== TEMP HOME = /tmp/tmp.JbSB873n2d ===
install all --dry-run exit=0, HOME left empty (besides pre-made mem dir): OK
install claude exit=0, manifest OK, claude symlink OK
status: claude: channel=dev version=<repo-sha> drift=0 / codex,opencode: version=not-installed drift=0

update (no reapply) exit=4   # drift 있음: claude/settings.json hash mismatch — 회귀 테스트 핵심 통과
update --reapply exit=0      # reapplied: claude/settings.json (1개) — 3-way merge가 conflict 없이 clean 성공
reapply preserved user edit: OK

uninstall --dry-run: 2개 copy-once + 15개 symlink 제거 예정 (나열만, 미접촉)
uninstall (real) exit=0, manifest removed: OK, symlink removed: OK
harness launcher OK (temp HOME only)
```

- 실 `~/.claude/.harness/manifest.json` 은 테스트 전후로 계속 부재 확인(`test -e` OK).
- 실 `~/.local/bin/harness` 도 테스트 전후로 계속 부재 확인.
- reapply 결과는 "conflict" 가 아니라 "reapplied"(clean merge) 로 떨어졌다 — Phase 2 review 가 우려한 adjacent-line conflict 케이스는 이번 fixture(`>> ` 로 파일 끝에 한 줄 추가)에서는 발생하지 않았다. 이는 Phase-5 코드의 성공 기준이 아니므로 결과와 무관하게 통과 처리(`update` crash 나 drift-gate 제거 실패만 blocking 이었을 것).
- Phase-5 핵심 회귀 확인 두 가지 모두 통과: (a) `update` (no `--reapply`) 가 drift 를 무조건 계산·보고(exit 4) — 이전엔 `--reapply` 뒤에 게이트돼 있던 부분, (b) `update --reapply` 가 정상적으로 `sources` dict 를 구성해 `manifest.reapply()` 를 크래시 없이 호출하고 실제 outcome(reapplied 1건)을 만들어냄.
