# plan-review round 1 — harness-installer 구현 사이클 1

- reviewer: 품질관리팀 (plan-review, standard tier)
- date: 2026-07-13
- plan: `.agent_reports/plans/2026-07-13_harness-installer-impl/plan/plan.md`
- scope: 구성 품질 (feasibility / missing steps / verification concreteness), non-adversarial 1 pass

## Verdict: PASS-WITH-FIXES

설계 골격은 탄탄하다. impl-inputs §A(GSD 정독) 채택이 충실하고, manifest 스키마·저장 위치·pristine 레이아웃·3-way 데이터플로우·결정론 verifier 가 hand-wave 없이 구체적이다. 스캐폴드 시그니처(`plan()`/`record()`/`check_drift()`/`reapply()`/`install()`/`checks()`/`status()`)와 stub 상태 서술도 실제 파일과 일치한다. P0 스코프 누락 없음, P1 경계 명시적. 다만 **두 건의 BLOCKING** 은 실행·검증 전에 반드시 고쳐야 한다 — 하나는 verification 블록 전체가 실행 불가한 launcher 호출 오류, 하나는 plan 의 핵심 전제(INST-STALE-1)가 파일시스템과 반대라 verification 기대출력이 뒤집혀 있는 문제다.

---

## BLOCKING

### B1. INST-STALE-1 전제가 사실과 반대 — `*_setting/` 는 존재한다 (plan §Current State line 26, 94, 102, 234; Verification lines 261-263, 270)

plan 은 "`{claude,codex,opencode}_setting/` projection directories **DO NOT EXIST in this worktree**" 를 핵심 전제로 깔고, 여기서 파생해 (a) projector 가 이 worktree 에서는 `skip: source absent` 만 낸다 (line 102, 262), (b) end-to-end 검증은 "materialized checkout 을 AGENT_HOME 으로 가리켜야만 가능" (line 234), (c) INST-STALE-1 을 HLS-interlock owner 에게 넘길 미결로 분류(line 234) 한다.

**실측 결과 세 디렉토리 모두 repo 루트에 존재하고 git-tracked 이며(commit `375edbc`, 이 plan 보다 한참 전), INSTALL_LAYOUT 이 서술한 projection-source 심링크를 정확히 담고 있다:**

```
claude_setting/  → CLAUDE.md README.md core commands skills agents agent-modes
                    hooks utilities tools scaffolds loops manifest.json
                    statusline.sh track-toggle.sh settings.json keybindings.json (모두 ../adapters|../core 로의 심링크)
codex_setting/   → AGENTS.md bin capabilities codex-agents codex-config ... roles
opencode_setting/→ AGENTS.md bin capabilities opencode-agents opencode-commands opencode-plugins opencode-skills ...
```

`AGENT_HOME=$REAL_REPO` 이면 `$AGENT_HOME/claude_setting/<p>` 는 정상 resolve 된다. 따라서:

- **Phase 1 dry-run 은 이 worktree 에서 `skip` 이 아니라 실제 symlink/copy_once plan 을 낸다.** line 102 의 "Done when … in this worktree (no `*_setting/`) it shows skip entries", Verification line 261-263 의 기대 출력("entries with action:skip, source absent")은 **정반대로 뒤집혀 있다** — code-test 가 이 기대치로 검증하면 정상 동작을 실패로 판정하거나 그 반대가 된다.
- **Phase 2 도 in-worktree 에서 실제로 manifest 를 기록한다.** line 270 의 "may SKIP on absent source" pessimism 은 근거가 없다 — copy_once source(`claude_setting/settings.json` → `../adapters/claude/settings.json`)를 cp 가 따라가 실바이트를 복사하므로 record 가 정상 성립한다.
- **INST-STALE-1 은 미결/HLS-interlock 안건이 아니다.** end-to-end 검증이 이 worktree 에서 그대로 가능하다는 사실은 plan 의 리스크 포스처를 완화하는 좋은 소식이지만, 지금처럼 "blocker"로 남겨두면 구현자가 존재하지 않는 장애를 우회하는 데 공수를 낭비한다.

**제안 수정**: (1) Current State §·Risks §Unresolved·Verification 의 "`*_setting/` 부재" 서술을 "존재·git-tracked, AGENT_HOME=repo 루트에서 정상 resolve" 로 정정. (2) Phase 1/2 의 "Done when" 기대출력을 `skip` 이 아니라 "실제 symlink/copy_once plan (또는 실 manifest)" 로 교체. (3) SKIP-on-absent 로직 자체는 방어적으로 유지하되(향후 부분 체크아웃 대비), "이 worktree 의 기대 결과"에서 default 를 실 plan 으로 바꾼다. (4) INST-STALE-1 을 미결에서 내리고 "resolved: sources present" 로 기록.

### B2. Verification launcher 호출이 실행 불가 — `python3 harness.sh` 는 SyntaxError (plan Verification line 248, 그리고 이에 의존하는 모든 Phase 블록)

Baseline setup 이 `alias harness="python3 $REAL_REPO/tools/install/harness.sh"` 로 되어 있는데, `harness.sh` 는 `#!/usr/bin/env sh` POSIX 스크립트다. 실측:

```
$ python3 tools/install/harness.sh --help
  File "tools/install/harness.sh", line 8
    SOURCE=$0
```

`python3` 는 sh 스크립트를 파싱하다 8번째 줄에서 SyntaxError 로 죽는다. 즉 **Phase 1~7 의 모든 `harness …` 검증 명령이 하나도 실행되지 않는다** — item 5(verification 이 functional level 까지 실행 가능한가)에서 치명적. 부수적으로, `alias` 는 non-interactive 셸 스크립트에서 기본적으로 확장되지 않으므로(code-test 가 블록을 스크립트로 실행하면 `shopt -s expand_aliases` 없이는 무효) alias 방식 자체도 취약하다.

**제안 수정**: baseline 을 다음 중 하나로 교체 — (a) `harness() { python3 "$REAL_REPO/tools/install/installer.py" "$@"; }` (installer.py 직접, 가장 확실), 또는 (b) `harness() { sh "$REAL_REPO/tools/install/harness.sh" "$@"; }` (launcher 경유). alias 대신 셸 함수를 써서 스크립트 실행 시에도 확장되게 한다.

---

## NON-BLOCKING

### N1. `cmd_update` 의 drift 게이팅과 Phase 2.3 검증 기대가 어긋남 (plan Step 2.3 line 126, Step 5.3 line 195; installer.py:132)

현재 스캐폴드 `cmd_update` 는 `drift = manifest.check_drift(runtimes) if args.reapply else []` — 즉 `--reapply` 없이는 drift 를 아예 계산하지 않는다. 그런데 Phase 2.3 "Done when"(line 126)과 Verification Phase 2(line 274)는 `--reapply` 없는 순수 `harness update --json` 이 `drift[]` 를 채우고 exit 4 를 내길 기대한다. plan Step 5.3(line 195)은 "keep check_drift" 라고만 하고 이 게이트 제거를 명시하지 않아, 그대로 두면 해당 검증 스텝이 조용히 빈 결과로 오탐 통과한다.

**제안 수정**: Step 5.3 에 "`cmd_update` 는 `--reapply` 여부와 무관하게 항상 `check_drift` 를 실행해 drift 를 report(exit 4)하고, `--reapply` 는 추가로 `reapply()` 를 호출한다 — installer.py:132 의 `if args.reapply` 게이트를 제거" 를 명시.

### N2. reapply 3-way 데이터플로우는 정확 — 확인 (plan Step 2.4 line 130)

`git merge-file -p --diff3 <ours=current-dest> <base=pristine> <theirs=new-canonical-source>` 는 `git merge-file OURS BASE THEIRS` 인자 순서와 정확히 일치하고, base=pristine(구 릴리스)·theirs=현 repo source 매핑도 impl-inputs §A trap #3407(pristine=구-릴리스 바이트) 과 정합. pristine-clobber 가드(line 227)도 반영됨. **문제 없음 — 이 축은 잘 설계됨.**

### N3. OpenCode opencode.json merge-manifest 미결 처리는 standard tier 에 적절 (plan line 236)

copy-only manifest 대상에서 merge-managed `opencode.json` 을 빼고 fragment-presence 만 기록, 전체 merge-aware manifest 는 차기 사이클로 미룬 뒤 spec owner 확인 안건으로 명시 — 스코프 판단으로 타당. 이 사이클에서 추가 작업 불필요.

### N4. Claude projection 목록은 INSTALL_LAYOUT 과 정확히 일치 — `bin` 제외도 의도적 (plan line 94)

plan line 94 의 claude 심링크 나열이 INSTALL_LAYOUT.md line 24 의 `for p in …` 목록과 완전히 일치한다(`bin` 을 넣지 않는 것도 INSTALL_LAYOUT 을 그대로 따른 것 — claude_setting 에 `bin` 심링크가 있어도 install 대상 아님). settings.json/keybindings.json 을 copy_once 로 분리한 것도 INSTALL_LAYOUT line 29-35 근거와 일치. **정확 — 지적 아님, 확인용.**

---

## 확인된 정합 사항 (칭찬)

- 스캐폴드 실상태 서술(installer.py cmd_* 라인 번호, projector `_PROJECTION_STUB`, manifest 의 `NotImplementedError` vs `check_drift` 의 `return []` 구분, driver `RUNTIME` 상수/`get_driver`)이 실제 파일과 한 줄도 어긋나지 않음 — feasibility 검증이 견고.
- 재사용 대상 경로 전수 실존 확인: codex `sync-native-{skills,agents,modes,plugin}.py`, opencode `sync-native-{skills,agents,commands}.py`, codex/opencode `preflight.sh`, `install-windows.sh`, `build-manifest.py`, `mem.py`(import 서브파서 line 3562 실존), `fleet.sh` 모두 존재. **Claude 에 sync-native/preflight 부재** 라는 plan 의 주장도 실측 일치(find 결과 0건) — fallback(pure symlink + copy_once, no generator) 처리 coherent.
- 안전 제약(실 runtime home 불가침, temp HOME + dry-run) 이 baseline block 과 Phase별 검증, 그리고 마지막 safety assertion(real home mtime 불변 확인)까지 일관되게 관철됨 — B2 launcher 만 고치면 실행 가능한 수준.
- Phase 의존 순서(0→2→5, 1→3→4, 6 병렬, 7 P1)와 signature-impact 분석(§Risks line 230)이 명확.

---

## Correction pass (standard tier — one pass, applied 2026-07-13)

Coordinator filesystem-verified both BLOCKING findings, then 기획팀 applied fixes in place:

- **B1 — RESOLVED.** `{claude,codex,opencode}_setting/` confirmed present & git-tracked (45 files; `claude_setting/CLAUDE.md`, `codex_setting/bin/preflight.sh` exist). Plan's Current State + Phase 1/2 expected outputs corrected to "sources present, full symlink plan, end-to-end verifiable in THIS worktree with AGENT_HOME=<repo root>". Stale INST-STALE-1 "absent" claim removed from Unresolved and replaced with an accurate **Claude native-runtime asymmetry** design note (Claude has no `preflight.sh`/`sync-native-*.py` — verifier check sets intentionally uneven per runtime; preserved correctly).
- **B2 — RESOLVED.** Verification baseline `alias harness="python3 .../harness.sh"` (would SyntaxError — harness.sh is POSIX sh) replaced with `harness() { sh "$REAL_REPO/tools/install/harness.sh" "$@"; }`. Per-phase command blocks now runnable.
- **N1 — RESOLVED.** Phase 5.3 now plans removal of the `if args.reapply` drift gate at `installer.py:132` so plain `update` always computes+reports drift (matches Phase 2.3 expectation).

**Final verdict: PASS.** No blocking issues remain. Deferred/flagged (not blockers): git-merge-file PATH availability (gated), opencode.json merge-manifest AMBIGUOUS, INST-OPEN-4 OPEN — all correctly recorded in Unresolved.
