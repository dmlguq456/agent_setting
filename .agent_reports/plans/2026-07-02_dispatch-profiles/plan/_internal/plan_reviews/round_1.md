# 📋 계획 리뷰 결과 — round 1 (plan-review, deep)

**검토 대상**: `.agent_reports/plans/2026-07-02_dispatch-profiles/plan/plan.md`
**계획 요약**: dispatch-profiles v1(claude+codex) — codex 3파일 이식/확장 + `tools/profile/build-home.py` 생성기 신설 + fleet/liveness/harvest 를 profile 인지로 확장, `--profile` 생략 시 무파괴.
**검증 방식**: 경계 가드(`tools/check-adaptation-boundary.sh` L525-648·L2346-2478·L2985-2997), 이식 원본 4파일, fleet 3파일, `adapters/claude/settings.json`, repo 레이아웃을 실제 Read 하여 대조.

**Verdict: 🔴 1건 · 🟡 5건 · 🟢 praise 다수.** 전체 아키텍처(마커워크·이식 preservation·rmtree 안전성·검증 게이트)는 탄탄. blocking 은 L0 settings.json 경로 해석 1건 — 이것만 고치면 실행 가능.

---

## 🔴 실행 전 반드시 수정할 문제

### 1. L0 하드 포함 `settings.json` 의 소스 경로 해석이 repo 레이아웃과 어긋남 — guard hook 등록이 조용히 누락될 수 있음 (DP-2 위반 위험)

- **현재 코드 상태 (실측):**
  - repo 루트에 `settings.json` **없음**. Claude settings 의 canonical 위치는 `adapters/claude/settings.json` (build-manifest.py L223 이 여기를 읽음, projection allowlist L3002 이 `settings.json` 을 claude_setting 표면으로 투영).
  - 즉 `settings.json` 은 **runtime home(`~/.claude`) 루트에는 존재**(투영), **repo/worktree 루트에는 부재**.
  - `adapters/claude/settings.json` 의 hook command 는 전부 하드코드 절대경로 `bash "$HOME/.claude/hooks/artifact-guard.sh"` 형태 — hook 등록의 load-bearing 요소는 **instance 안 `settings.json` 존재 여부** 하나다(hooks/ 심링크가 아니라).
- **계획의 가정 (틀림):**
  - Current State L32: *"`core/`, `hooks/`, `settings.json` exist at repo/home root."* → `settings.json` 은 repo root 에 없으므로 **절반 오류**.
  - Step 1.1 L0 하드 포함을 `core/`·`hooks/`·`settings.json` 세 개를 **동일하게** 취급(암묵적으로 `$AGENT_HOME/settings.json`). 그런데 `core/`·`hooks/` 는 repo·home 양쪽 루트에 다 있지만 `settings.json` 만 예외다.
  - 계획은 skills/agents 에는 이미 "runtime-first / repo-fallback" 이중경로(`<HOME>/skills/<n>` → `<HOME>/adapters/claude/skills/<n>`, agents 는 root `agents/` 가 `check_removed_root_surfaces` 로 금지라 fallback 필수)를 **정확히** 적용했다. 같은 divergence 를 `settings.json` 에만 놓쳤다.
- **결과:**
  - repo/worktree 컨텍스트(=Verification smoke 가 `AGENT_HOME="$PWD"` 로 도는 바로 그 컨텍스트, 또는 AGENT_HOME 미설정 시 marker-walk 가 repo 루트로 귀결되는 경우)에서 `link()` 의 skip-on-missing 이 `settings.json` 을 **조용히 건너뜀** → masked home 에 settings.json 부재 → **guard hook(artifact-guard·git-state-guard·builtin-memory-guard) 전부 미등록** → L0 불변식(DP-2 "guard hooks 마스킹 불가") 침묵 위반.
  - smoke test(plan L136-147)가 `core/`·`CLAUDE.md`·`hooks/`·`skills/autopilot-lab` 만 assert 하고 **`settings.json` 을 확인하지 않아** false-green — 이 누락을 못 잡는다.
- **수정 제안:**
  1. build-home 의 L0 `settings.json` 소스를 skills/agents 와 동일한 이중경로로: `<HOME>/settings.json` 우선, 없으면 `<HOME>/adapters/claude/settings.json` fallback. (`core/`·`hooks/` 는 양쪽에 있으니 현행대로 OK.)
  2. smoke test 에 `test -e "$TMP/homes/smoke.lab-runner/settings.json"` 한 줄 추가 — L0 등록의 load-bearing 요소를 검증에 포함.
  3. (문서 정합) Current State L32 의 "settings.json exist at repo/home root" 를 실제(adapters/claude/settings.json)로 정정.

---

## 🟡 보완하면 좋은 점

### 2. `_parse_pipe` 는 return 지점이 3곳 — 4-tuple 확장 시 실패경로(L66) 누락하면 caller crash

- **현재 코드 상태:** `_parse_pipe` return 3곳 — L62 `return name, fields.get("mode"), fields.get("qa")` (NEW form), **L66 `return None, None, None` (parse 실패)**, L70 `return name, m.group(2), None` (OLD form). 빈/malformed pipe 는 실제로 L66 을 탄다(`_scan_jobs_log` 이 `_parse_pipe(pipe or "")` 호출, 빈 문자열은 `_PIPE` regex 불일치 → L66).
- **계획의 가정:** Step 5.2 는 *"Return tuple becomes (name, mode, qa, profile)"* 와 "OLD form → None" 만 언급. 세 return 을 모두 바꿔야 함이 명시적이지 않음.
- **위험:** L62/L70 만 고치고 L66 을 빠뜨리면, caller L351 의 4-way unpack(`pname, pmode, pqa, pprofile = _parse_pipe(...)`)이 **empty/malformed pipe 에서 `ValueError: not enough values to unpack`** 로 fleet 렌더 전체를 죽인다(도달 가능 경로).
- **수정 제안:** Step 5.2 에 "return 3곳(L62·L66·L70) 모두 4-tuple 로 — 특히 실패경로 `return None, None, None, None`" 를 명시.

### 3. harvest home cleanup 이 `matched_jobs`(mutation 전 스냅샷) 기준 — non-default selector 에서 running job home 삭제 위험

- **현재 코드 상태:** `dispatch-harvest.py` L107 `matched_jobs.append(fields.copy())` 는 mark-done **이전** 상태를 캡처(state="open"/"running" 등 원본). 실제 open→done 전이는 L108 `if args.mark_done and fields[1] == "open"` 에서만 일어남. `matches()` 는 `--status all` 일 때 running 행도 매칭.
- **계획의 가정:** Step 6.1 *"for each matched job actually marked done"* — 의도는 맞으나, 순진하게 `matched_jobs` 를 순회해 rmtree 하면 "actually marked done" 이 아닌 매칭도 포함된다.
- **위험:** `harvest --mark-done --status all --worktree X` 같은 호출에서 아직 **running 인 job 의 home 을 rmtree** → 진행 중 세션 파손. default(`--status open`)에선 매칭=마킹이라 안전하지만, selector 가 바뀌면 터진다.
- **수정 제안:** rmtree 를 `matched_jobs` 가 아니라 **실제 open→done 전이 브랜치**(`fields[1]=="open"` 안)에서 별도 리스트에 모은 대상에만 적용. 계획 문구를 "matched 가 아니라 실제 mark-done 전이된 행만" 으로 조인다.

### 4. liveness `while` 루프의 `name` 변수 iteration 간 leak

- **현재 코드 상태:** `utilities/dispatch-liveness.sh` L18-37 은 `while` 루프. 계획 스니펫(Step 4.1)은 `case "$pipe" in *profile=*) name=...;; esac` 로 **매칭될 때만** `name` 설정.
- **위험:** 이전 행이 `name` 을 세팅했고 현재 행에 `profile=` 이 없으면, `name` 이 **직전 값을 유지** → profile 없는 job 을 `homes/<slug>.<이전profile>/` 로 오탐 → 존재하지 않는 경로 → false DEAD. "profile= 부재 → 현행 경로(후방호환)" 라는 계획 의도(DP-7)가 깨진다.
- **수정 제안:** 루프 본문 진입 시 `name=""` 리셋 후 case 분기, `[ -n "$name" ]` 로 경로 선택. (계획 스니펫에 리셋 한 줄 추가.)

### 5. claude 프로필 instance home 의 cleanup 경로 부재 (DP-4 커버리지 갭)

- **현재 코드 상태:** home cleanup 훅은 **codex `dispatch-harvest.py` 에만** 추가됨(Step 6.1). `check_claude_bin_wrappers`(L1639-1653)는 claude bin 에 `mem-distill-worker.sh` 만 요구 — **claude 쪽 harvest 도구는 없고** 계획도 신설하지 않음.
- **계획의 가정:** Step 2.1 은 claude jobs.log 를 `~/.claude/.dispatch/jobs.log`, codex 는 repo-relative default 로 두고 이 차이를 *"deliberate"* 라 명시. 그런데 harness=claude 프로필(예: lab-runner)의 instance home 은 **누가 지우나?** codex harvest 가 지우려면 같은 jobs.log 를 읽어야 하는데, 계획이 두 registry 를 서로 다르다고 못박아 놓았다.
- **위험:** 두 registry 가 실제로 분리되면 codex harvest 가 claude 행을 못 봐서 **claude instance home 이 영구 누적**(gitignore 이지만 디스크 leak) → DP-4("harvest 시 제거") 불성립.
- **수정 제안:** (a) claude·codex 가 AGENT_HOME=`~/.claude` 로 **동일 jobs.log·동일 homes 루트를 공유**하고 codex harvest 가 harness 무관하게 profile= 행 전부를 청소한다는 모델을 명시(이 경우 Step 2.1 의 "deliberate difference" 표현이 오해 소지 → 정정), 또는 (b) claude instance cleanup 경로(별도 harvest 훅/오케스트레이터 회수)를 계획에 추가.

### 6. gate 순서 + `subprocess.Popen(env=...)` footgun (Phase 2/3)

- **gate 순서:** Step 2.1/3.1 은 ① `--instance`(생성) → ② `--check`(게이트) → 실패 시 return 3 순. instance 를 만들고 나서 검증하므로, 게이트 실패 시 **jobs.log 등록 전(append_job 이 게이트 뒤)** 이라 등록 안 된 instance 가 leak(harvest 가 jobs.log 기반이라 회수 불가). `--check`(선언/템플릿 검증) 를 **생성 전에** 돌리는 게 논리적(spec §4.2 도 check 를 게이트로 규정) — 재조립 검증이니 instance 없이 선행 가능.
- **Popen env:** Step 2.1 *"env carrying CLAUDE_CONFIG_DIR"* / Step 3.1 *"CODEX_HOME on the env"* — `env=` 에 **`{**os.environ, "CLAUDE_CONFIG_DIR": ...}`** 처럼 기존 환경을 상속해야 함. bare dict 를 넘기면 subprocess 가 PATH 등을 잃어 `claude`/`codex` 실행 자체가 깨진다. 계획에 "os.environ 복사 + 키 추가" 를 명시 권장.

---

## 🟢 잘 작성된 부분

- **marker-walk 설계가 정확히 검증됨.** `adapters/claude/core/CORE.md` 부재를 실측 확인 — 미러(`adapters/claude/tools/profile/`)에서 `parents` 를 walk 하면 adapters/claude 에서 멈추지 않고 repo 루트(core/CORE.md)까지 올라간다. root·mirror 양 depth 에서 byte-identical 로 동작 가능하다는 계획 핵심 전제가 성립. `check_claude_tool_projection`(L2456)은 byte-identity 를 강제하지 않고 concrete 존재만 보므로, byte-identity 는 계획이 자발적으로 건 정확한 correctness 제약.
- **codex assertion preservation 이 철저.** L599-628 의 ~30개 `grep -Fq` literal 을 Step 3.1 Risks 에 명시 열거했고, 편집 위치(parser/append_job/main)가 `dispatch_prompt()` prose 를 건드리지 않아 prompt literal 이 자연 보존된다. `check_runtime_projection(args.worktree, args.require_hook_trust)` 를 "그 블록 **뒤**" 로 잡은 것도 정확.
- **rmtree-on-symlink-farm 안전성 판단이 옳다.** `shutil.rmtree` 는 심링크를 따라가지 않고 unlink 하므로 core/·hooks/·skills/·`.credentials.json` 심링크 제거가 실제 원본을 건드리지 않는다 — 계획의 "removing it never deletes the real sources" 는 정확.
- **skills/agents 이중경로 해석이 정확.** root `agents/` 금지(`check_removed_root_surfaces` L2472)를 인지해 `adapters/claude/agents/` fallback 을 넣었고, expose 대상(autopilot-lab·analyze-project·post-it / dev-team·qa-team·material-team) 전부 실재 확인됨 — lab-runner 예시가 유효.
- **manifest 영향 재확인 정확.** `build-manifest.py` 는 `adapters/claude/skills|agents`·`loops/README.md`·`adapters/claude/settings.json` 만 스캔(L157/175/223/275) → `profiles/`·`tools/profile/`·신규 bin 은 manifest 무영향. `warn_concrete_runtime_terms`(L2988)가 `tools/` 를 스캔하지만 WARN 은 non-fatal 이고 계획이 concrete token 회피를 명시.
- **Verification section 이 구체적·실행가능.** 6개 게이트 + file-only smoke + ast 문법 체크 + non-profile 무파괴 dry-run — plan-review 기준의 "concrete executable test commands" 를 충족(finding #1 의 settings.json assert 한 줄만 보강하면 완전).
- **spec §9 파일 전수 커버 + scope 정합.** 모든 신설 파일이 계획에 있고, §8 하이브리드 라우팅·opencode 는 명시적으로 v1 범위 외로 정확히 defer.
