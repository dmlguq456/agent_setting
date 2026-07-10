# 📋 계획 리뷰 결과 — round 2 (plan-review, focused re-verify)

**검토 대상**: `.agent_reports/plans/2026-07-02_dispatch-profiles/plan/plan.md`
**기준**: round 1 의 🔴 1건 + 🟡 5건 반영 여부. 실제 plan Read + 이식 원본(`dispatch-harvest.py`·`collectors/dispatch.py`)·codex hooks 레이아웃·`install-runtime-projection.sh` 를 실측 대조.

**Verdict: 🔴 0건 · 🟡 1건(신규) · 🟢 6건 원복 확인.** round 1 의 blocking 🔴(#1) 포함 6건 전부 정확히 반영됨 — 실행 가능. 단, #1 의 harness-aware 일반화 과정에서 **codex `hooks.json` 소스 경로 오타**(존재하지 않는 `codex-hooks/` 디렉터리)가 새로 유입 — round 1 🔴 와 동일 결함 계열(경로 오인 → silent skip → DP-2 침묵 위반)의 codex 브랜치 재발. v1 concrete 산출물(lab-runner=claude)은 안 타므로 non-blocking 이나, 첫 codex 프로필 전에 고쳐야 하며 지금 고치는 게 싸다.

---

## ✅ round 1 이슈별 반영 검증 (6/6 정확)

### #1 (🔴) L0 settings.json harness-aware 이중경로 — **완전 반영**
- **Current State 레이아웃 팩트 정정 ✅**: L32 "Layout facts" 가 *"`settings.json` does NOT exist at repo root — canonical is `adapters/claude/settings.json` … exists at runtime home root only as a projection … same runtime-first/repo-fallback divergence as skills/agents, not the both-roots availability of core/·hooks/"* 로 정확히 재서술. 실측(`adapters/claude/settings.json` 존재, repo root `settings.json` 부재)과 일치.
- **Step 1.1 harness-aware 재작성 ✅**: L60-64 — always(both)=`core/`+`hooks/`; **harness=claude** = `settings.json` 이중경로(`<HOME>/settings.json` → `<HOME>/adapters/claude/settings.json`); **harness=codex** = claude settings.json 링크 금지(spec §5 cross-harness leak guard 명시) + codex hook-registration 파일을 이중경로로. Rationale 줄에 "DP-2 는 각 harness 자기 hook-registration 메커니즘(claude=settings.json, codex=hooks.json)으로 충족, dual path 가 repo·home 양 컨텍스트 커버" 명시.
- **cross-harness 누출 금지 명시 ✅**: L63 "do **NOT** link claude `settings.json` into a codex home (spec §5 leakage-refusal guard)" + Step 3.1 L94 "Do **not** set `CLAUDE_CONFIG_DIR` here".
- **smoke assert 추가 ✅**: Verification L153 `test -e "$TMP/homes/smoke.lab-runner/settings.json"  # L0 hook-registration load-bearing element — false-green guard`.

### #2 (🟡) `_parse_pipe` 3 return → 4-tuple — **완전 반영**
- Step 5.2 L113 이 return 3곳을 **명시적 라인 지정**으로 요구: NEW(L62), **실패경로(L66 → `return None, None, None, None`)**, OLD(L70). 실측과 정확히 일치(L62 NEW / L66 `return None, None, None` / L70 OLD). 빈/malformed pipe 가 실제 L66 을 탄다는 도달경로(`_parse_pipe(pipe or "")` → 빈 문자열 regex 불일치)와 caller L351 4-way unpack `ValueError` crash 근거까지 서술. 정확.

### #3 (🟡) harvest open→done 전이만 rmtree — **완전 반영**
- Step 6.1 L125 이 "cleanup targets must be **only rows where an actual `open`→`done` transition happened**, not the whole `matched_jobs` snapshot" 로 명시. 실측 확인: `matched_jobs.append(fields.copy())`(L107, mutation 전 스냅샷) + 전이 브랜치 `if args.mark_done and fields[1] == "open":`(L108). plan 이 이 브랜치 안에서 별도 수집/rmtree 하도록 지시 — `--status all` 에서 running home 파손 위험 정확히 차단. `import shutil` 추가 요구(L125)도 실측(현재 미import)과 부합.

### #4 (🟡) liveness `name` iteration leak — **완전 반영**
- Step 4.1 L99-104 스니펫이 루프 본문 진입 시 `name=""` 리셋 후 case 분기, `[ -n "$name" ]` 로 경로 선택. profile= 부재 → 현행 `dir="$PROJ/$enc"`(후방호환) 유지. 직전 행 profile 누출 → false DEAD 근거 명시. 정확.

### #5 (🟡) 공유 registry·cleanup 소유 — **완전 반영**
- Step 2.1 L78 이 "deliberate difference" 표현을 폐기하고 **shared-registry ownership model** 로 재작성: claude+codex 가 AGENT_HOME=`~/.claude` 로 동일 `.dispatch/jobs.log` + 동일 `.dispatch/homes/` 공유 → codex harvest 가 claude profile home(lab-runner 등)까지 회수. "do **not** describe as deliberate difference" 명시.
- Step 6.1 L123 이 "harness-agnostic single cleanup owner … keys off `profile=` field, not the harness" 로 대응. DP-4 가 claude profile 에도 성립. 정확.

### #6 (🟡) gate 순서(--check 먼저) + Popen env 상속 — **완전 반영**
- Step 2.1 L79-83 / Step 3.1 L94: 순서 = ① `build-home --check`(non-zero → `return 3`, instance 미생성 → no leak) → ② `--instance`(생성) → ③ `append_job`(launch 전 등록) → ④ `Popen(env={**os.environ, "CLAUDE_CONFIG_DIR"/"CODEX_HOME": <instance>})`. "must inherit `os.environ` — a bare dict drops PATH and breaks the exec" 명시. round 1 이 지적한 역순(생성→검증) 완전 교정.

---

## 🟡 신규 발견 (fix 유입 regression)

### N1. Step 1.1 codex 브랜치 `hooks.json` 이중경로가 **존재하지 않는 `codex-hooks/` 디렉터리**를 가리킴 (round 1 🔴 결함의 codex 재발)
- **plan 문구 (L63)**: harness=codex 는 `hooks.json` 을 이중경로로 — *first `<HOME>/codex-hooks/hooks.json`, then `<HOME>/adapters/codex/codex-hooks/hooks.json`*.
- **실측 (틀림):**
  - `adapters/codex/` 아래에 `codex-hooks/` **없음**. 실제 concrete 파일은 **`adapters/codex/hooks/hooks.json`** (디렉터리명 `hooks`). → plan 의 repo-fallback `<HOME>/adapters/codex/codex-hooks/hooks.json` 은 **어디에도 없는 경로**.
  - `codex-hooks` 라는 이름은 별도 심링크 alias 트리 `codex_setting/codex-hooks → ../adapters/codex/hooks` 에만 존재(`check-adaptation-boundary.sh` L119). repo root·`~/.claude` root 어디에도 `codex-hooks/` 나 root-level `hooks.json` 은 없음.
  - codex runtime home 에서는 `install-runtime-projection.sh` L88 `link "$S/codex-hooks/hooks.json" "$CODEX_HOME/hooks.json"` — 즉 hooks.json 은 `<CODEX_HOME>/hooks.json`(root). plan 의 runtime-first `<HOME>/codex-hooks/hooks.json` 도 부정확(`<HOME>` 은 AGENT_HOME=`~/.claude`/repo 이지 CODEX_HOME 아님, 거기엔 codex-hooks 없음).
- **결과 (round 1 🔴 와 동일 계열):** build-home 이 이 두 경로를 그대로 코드화하면 codex profile home 에서 `link()` skip-on-missing 이 hooks.json 을 **조용히 건너뜀** → codex masked home 에 hook-registration 부재 → codex guard hook 전부 미등록 → DP-2 침묵 위반. #1 을 잡은 dual-path 메커니즘이 정작 codex 브랜치에서 없는 디렉터리를 가리켜 무력화됨.
- **왜 v1 non-blocking:** 유일한 profile 예시 lab-runner 는 `harness: claude` — smoke(L149-157)도 claude 경로만 실행. codex profile.yaml 이 v1 concrete 산출물에 없으므로 실행 게이트가 이 경로를 안 탐. 그러나 plan 은 prescriptive 문서라 구현자가 그대로 오경로를 코드화하고, smoke 가 claude 만 assert 하므로 round 1 이 경고한 것과 **동일한 false-green** 으로 못 잡음.
- **수정 제안:**
  1. codex repo-fallback 을 실경로 **`<HOME>/adapters/codex/hooks/hooks.json`** 로 정정(claude 가 `<HOME>/adapters/claude/settings.json` 쓰는 것과 대칭). build-home 은 소스로 AGENT_HOME(`<HOME>`)만 쓰므로 실제 발화되는 건 이 concrete fallback 이다.
  2. runtime-first 를 굳이 둘 거면 `<CODEX_HOME>/hooks.json`(root)로 — 단 build-home 이 CODEX_HOME 을 소스로 참조하지 않는 현 설계에선 concrete fallback 하나로 충분. 문구를 `codex-hooks/` → `hooks/` 로 정정하는 게 최소 수정.
  3. (선택) codex profile 예시가 v1 밖이라 smoke 로 못 잡으니, 정정 후 최소한 코멘트로 "codex hooks.json 소스=`adapters/codex/hooks/hooks.json`" 를 build-home 에 남길 것.

---

## 🟢 함께 확인된 견고한 부분

- **이식 원본 라인 대조 정확.** Step 5.2(L62/L66/L70)·Step 6.1(L107 스냅샷 / L108 `fields[1]=="open"` 전이)·`import shutil` 미존재 — 전부 실측과 일치. plan 이 소스를 추측이 아니라 실측 기반으로 씀.
- **#1 claude 브랜치 완결.** 레이아웃 팩트 정정 + dual path + smoke assert 3종 세트가 round 1 수정 제안과 1:1 대응. blocking 해소 확실.
- **Change History 정확.** L178-184 이 6건 fix 를 실제 반영 내용과 어긋남 없이 요약(과대 서술 없음).

## 🔎 minor watch-item (defect 아님)
- **#5 harvest homes-root 정합 의존성.** harvest `resolve_agent_home()` 는 AGENT_HOME env(+core/CORE.md) 없으면 `ROOT`(repo root) 반환(실측 L57-62). cleanup home 경로 `resolve_agent_home()/.dispatch/homes/` 와 jobs.log 경로가 **둘 다** `~/.claude` 로 수렴해야 성립 — plan 은 jobs.log 가시성만 "presumes shared ~/.claude registry" 로 커버. `harvest --jobs ~/.claude/…/jobs.log` 를 AGENT_HOME 미설정 repo 에서 돌리면 jobs.log=`~/.claude` 인데 homes root=`<repo>`(ROOT) → rmtree 가 없는 경로 겨냥 → cleanup 무발생(비파괴적 DP-4 miss). Step 6.1 에 "harvest 는 dispatch 와 **동일 AGENT_HOME(`~/.claude`)** 로 실행돼야 homes root 가 jobs.log 와 정렬" 한 줄 명시 권장. non-destructive 라 blocking 아님.

---

**결론:** round 1 6건 전부 정확·완전 반영(🔴 해소). 신규 🟡 1건(N1 codex `hooks.json` 경로 오타)은 v1 실행 non-blocking 이나 첫 codex profile 전 정정 필요 — 문구 `codex-hooks/` → `hooks/` 한 줄 수정이면 끝. minor watch-item 1건은 선택.
