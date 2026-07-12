# harness-installer — 구현 사이클 1 최종 보고

> plan: `plan/plan.md` (status: done) · checklist: `plan/checklist.md` · 브랜치 `harness-installer-impl` (미머지)

## 1. 한 줄 요약

`tools/install/` 를 스캐폴드 stub 에서 동작하는 installer 로 채웠다 — symlink projection·hash-manifest(drift/reapply)·3-런타임 driver·verify check 목록·`installer.py` cmd_* 배선·`mem import`+PATH launcher 까지 **Phase 0~6 전부 완료**, Phase 7 은 **Codex plugin 채널 wrap 만 in-cycle 완료**하고 **Claude plugin content generator + `install --plugin` wrapping 은 plan 자체 경계에 따라 다음 사이클로 명시 이월**했다. **verdict: 사이클 1 목표 달성(부분 범위 — Phase 7 Claude 축 의도적 미포함)**. code-test 는 51/51 PASS(functional E2E, real-home 결정론 가드 포함)로 사이클 1 산출물을 확인했다. 별도로, Phase 5 검증 도중 실제 `~/.claude/settings.json` 이 손상된 인시던트가 있었다(§5) — installer 코드 결함이 아니라 검증 스크립트의 env-scoping 실수였고, main orchestrator 가 이미 복구·검증 완료했다.

## 2. 목표 대비 결과

PRD §0.5 설계 원칙 5개 대비:

| 원칙 | 상태 | 비고 |
|---|---|---|
| 1. 2-채널 하이브리드 | **부분** | installer CLI(dev 경로)는 3-런타임 전부 완결. plugin 채널은 **Codex 만** in-cycle(§7.1 wrap) — Claude plugin 채널은 스캐폴드(marketplace skeleton)만 존재, content generator·`install --plugin` claude 경로는 미구현(deferred SKIP 반환). OpenCode 는 plugin 채널 자체가 PRD 상 부재 확인(설계상 installer 가 유일 경로) — 해당 없음. |
| 2. 결정론 우선 | **달성** | install/verify/drift/reapply 전부 코드 결정론, exit code 로 결과 보고. e2e 테스트가 exit code 계약(0/2/4 등)을 직접 검증. |
| 3. 파일-복제 회피 | **달성(installer CLI 경로 한정)** | driver 들은 기존 `sync-native-*`/`preflight.sh` 를 **호출**(재구현 아님) — dev_logs 상 각 driver 구현이 기존 adapter 스크립트를 wrapping. Claude plugin 내용물 생성기(원칙 3의 plugin 축)는 Phase 7 deferred 로 아직 미검증. |
| 4. 소유 경계(GSD 모델) | **달성** | manifest 는 installer 가 기록한 파일만 추적, uninstall 은 manifest 등재분만 제거(checklist 5.4, e2e `lifecycle.non_manifest_file_preserved` PASS). Phase 3+4 리뷰에서 발견된 HIGH(real 파일 데이터 유실 가능성)는 fix 완료·재검증됨(§3 참조).
| 5. idempotent | **달성** | e2e `lifecycle.idempotent_reinstall.exit0`+`no_blocked` PASS — 재설치가 안전. |

**요약**: installer CLI 경로(dev 머신 사용성)는 3-런타임 전부 완결. plugin 채널(소비자 경로)은 Codex 만 완결이고 Claude 는 계획대로 다음 사이클 대상.

## 3. Phase별 완료 현황

| Phase | 내용 | 상태 | 근거 |
|---|---|---|---|
| 0 | manifest 스키마 + layout 상수 (`paths.py`, `manifest.py` docstring) | ✅ done | checklist 0.1~0.2, `step_00_paths_manifest_schema.md` |
| 1 | `projector.py` — INSTALL_LAYOUT symlink 레시피 기계화 | ✅ done | checklist 1.1~1.2, `step_01_projector.md`, review `phase_01_02.md`(PASS) |
| 2 | `manifest.py` — hash-manifest/drift/reapply(`git merge-file`) | ✅ done | checklist 2.1~2.4, `step_02_manifest.md`, review fix `phase_01_02_fix.md`(atomic write 보강) |
| 3 | driver 3종(`claude`/`codex`/`opencode`) install/status/checks | ✅ done | checklist 3.1~3.3, `step_03_driver_*.md`, review `phase_03_04.md`(HIGH 1건 발견) → `phase_03_04_fix.md`(수정·재검증 완료) |
| 4 | `verifier.py` 실 check 목록(각 driver `checks()`) | ✅ done | checklist 4.1~4.4 |
| 5 | `installer.py` cmd_* 실배선(install/status/update/uninstall) | ✅ done | checklist 5.1~5.4, `step_05_installer.md` — **단, 이 스텝 검증 중 §5 인시던트 발생** |
| 6 | `mem import` + `~/.local/bin` launcher symlink | ✅ done | checklist 6.1~6.2, `step_06_bootstrap.md` |
| 7 | plugin 채널 wrap (P1, boundary) | ⚠️ **부분** | checklist 7.1: Codex plugin wrap ✅ done · Claude plugin content generator + `install --plugin` claude 경로 **[DEFERRED]**(plan.md 명시 경계, 다음 사이클) |

전체 39 스텝 중 완료 표시(checklist.md 기준) — Phase 0~6 전 스텝 `[x]`, Phase 7 은 7.1 `[x]` + 1건 `[DEFERRED]`(실패 아님, 계획된 범위 축소).

## 4. 테스트 결과 요약

`test_logs/e2e_lifecycle.md` (code-test, functional E2E 레벨):

- **PASS 51 / FAIL 0**
- 도달 레벨: syntax(py_compile) → import → smoke(install --dry-run) → **functional**(install/manifest/drift/reapply/verify/uninstall 전체 lifecycle, 3-런타임, plugin dry-run 포함)
- **real-home 결정론 가드 통과**: 실행 전/후 `~/.claude/settings.json`·`~/.codex/config.toml`·`~/.config/opencode/opencode.json` 해시가 mktemp HOME 전환 전 캡처 → trap 으로 종료 시 재확인, 변경 없음 확인.
- 특기: drift→reapply→user-edit-preserved 불변식, manifest-scoped uninstall(비manifest 파일 보존), CLI-absent SKIP(codex/opencode/claude bootstrap-smoke), PATH-collision guard(기존 `harness` 파일 보존) 모두 실측 통과.
- observational note(결함 아님): PRD 는 `python3 ≥ 3.10` 명시하나 실측 인터프리터는 3.8.10 — 전 스텝 clean 통과, 3.10+ 전용 문법 미검출. doc-vs-환경 괴리로 기록만.

## 5. 인시던트 — 실제 `~/.claude/settings.json` 손상 (Phase 5 검증 중)

Phase 5 dev-team 검증 과정에서, 별도 Bash 호출에 걸쳐 `HOME`/`AGENT_HOME`/`MEM_STORE` 를 export 유지하려다 **각 Bash 호출이 셸 상태를 리셋**하는 문제로 export 가 소실됐고, 그 결과 검증 스크립트의 drift-주입 라인(`echo '// user edit' >> "$HOME/.claude/settings.json"`)이 **의도한 mktemp 임시 HOME 이 아니라 실제 `$HOME`** 을 대상으로 실행됐다. 이로 인해 실제 `~/.claude/settings.json` 끝에 `\n// user edit\n` 이 그대로 append 되어 `json.load` 가 `Extra data: line 265 column 1` 로 실패하는 파손이 발생했다(`_internal/dev_reviews/INCIDENT_real_home_touched.md`).

**중요 — 원인 귀속**: 이는 **harness-installer 코드 자체의 결함이 아니다**. installer 소스(`tools/install/**`)에는 실제 런타임 홈을 건드리는 경로가 없으며, 이번 손상은 **검증 스크립트의 env-scoping 실수**(Bash 호출 간 export 미유지)로 발생한 것이다. main orchestrator 가 (1) 정확한 trailing-byte 진단(`data.endswith(b'\n// user edit\n')`) 후 (2) 기계적 truncation 복구 절차를 문서화하고 (3) 바이트 동일성 검증 방법을 제시했다 — 인시던트 문서 자체에 사용자가 직접 실행할 복구 커맨드가 포함되어 있다.

**재발 방지 — 이번 code-test 스테이지에서 실효적으로 검증됨**: 이번 e2e 테스트(§4)는 이 인시던트를 직접 반영해, env 유지가 필요한 모든 단계를 **단일 self-contained 스크립트**로 재구성하고(별도 Bash 호출 간 export 유실 문제 원천 차단), 임시 HOME 을 `mktemp` 로 **hard-code** 하고, **실행 시작/종료 시점 real-home 파일 sha256 비교를 trap 으로** 강제했다. 그 결과가 §4의 "real-home 결정론 가드 통과"이며, 이는 재발 방지 조치가 실제로 이 사이클에서 real home 무결성을 실행 전/후 동일하게 유지했음을 자체 검증한 것이다.

**남은 조치 — 해결·검증 완료 (conductor 갱신)**: `INCIDENT_real_home_touched.md` 문서 자체는 "Remediation NOT applied" 상태로 작성돼 있어 code-report 스테이지가 이를 그대로 인용해 복구 대기 중으로 서술했으나, 이 사이클 재개(§0 conductor 컨텍스트) 시점에는 **main orchestrator 가 이미 복구·검증을 완료**했다: (1) 정확한 trailing-byte(`\n// user edit\n`) truncation 으로 실제 `~/.claude/settings.json` 복구, (2) 바이트 동일성 검증. 이 conductor 가 직접 재확인: `python3 -c "import json; json.load(open('/home/Uihyeop/.claude/settings.json'))"` → **VALID JSON**, 그리고 백업 `~/.claude/settings.json.pre-incident-fix.bak` 존재(복구 전 스냅샷 보존). 이번 code-test 스테이지의 real-home 결정론 가드(§4)도 실행 전/후 해시 불변을 독립적으로 재확인해 이미-정상인 상태가 이번 사이클 동안 다시 훼손되지 않았음을 증명한다. `INCIDENT_*.md` 문서 본문은 역사적 기록으로 그대로 두되(당시 시점의 사실), 더 이상 실행 가능한 action item 은 아니다.

## 6. Deferred / Open 항목

- **plan.md 선언 deferred**: "Phase 7 (P1): Claude plugin content generator + Claude `install --plugin` CLI wrapping — explicitly deferred to a future cycle per the plan's own Phase 7 boundary (Codex plugin wrap landed in-cycle)."
- PRD 열린 결정 현재 상태:
  - **INST-OPEN-1** (plugin 탑재 hook 범위): 이번 사이클에서 파일별 목록 확정 **안 함** — Codex plugin wrap 은 기존 hook 배선을 그대로 wrap(신규 hook 목록 조정 없음), Claude plugin content generator 부재로 실질 결정 다음 사이클로 이월.
  - **INST-OPEN-3** (`INSTALL_LAYOUT.md` 사후 위상): 이번 사이클에서 **미착수** — CLI 가 Phase 0~6 으로 기능적 대체를 완료했으나 `INSTALL_LAYOUT.md` 자체의 "계약 서술 + `verify` 참조" 축소 편집은 진행되지 않았다. 다음 사이클(또는 별도 문서 동기화 작업) 대상.
  - **INST-OPEN-4** (OpenCode 배선 drift — 복수형 디렉토리·`skills.paths` 부재): plan.md 상 "선행 게이트(GSD 정독·OpenCode 실측) 통과" 로 기록되어 있고 Phase 3 opencode driver 가 non-destructive merge 로 구현됨 — 실측 결과가 driver 구현에 반영됐는지는 이 보고서 작성 시점 dev_logs 만으로 완전 확증되지 않아, 다음 사이클에서 opencode driver 구현이 실제 최신 opencode 배선과 일치하는지 별도 확인 권장.
- **인시던트**: 해결·검증 완료(§5 conductor 갱신 참조) — 잔여 action item 없음.

## 7. 커밋 목록 + 브랜치 상태

브랜치 `harness-installer-impl` (main 미머지, 이 사이클 전용):

```
a6fab8c chore: harness-installer-impl plan status -> done (P1 partially deferred)
06fcece feat: harness-installer Phase 7 (P1 in-cycle) — codex plugin channel wrap
7e9b090 feat: harness-installer Phase 5 — installer.py cmd_* wiring
5aaf51a feat: harness-installer Phase 3-4-6 — drivers, check lists, bootstrap
a1490a1 feat: harness-installer Phase 0-2 — paths, projector, manifest
24e2295 chore: Safety checkpoint before harness-installer-impl execution
```

(base `4de50f6` 이후 diffstat: 29 files changed, 3877 insertions(+), 84 deletions(-) — `tools/install/**` 6개 모듈 + `drivers/` 3개 + plan/checklist/dev_logs/dev_reviews 산출물.)

merge·push·worktree 정리는 미수행 — main orchestrator 몫.
