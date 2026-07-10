---
name: stage-dispatch-phase2
slug: 2026-07-10_stage-dispatch-phase2
status: planned
mode: dev
intensity: strong
qa: standard
spec: .agent_reports/spec/stage-dispatch/prd.md
spec_scope: "§12 Phase 2 (v2) + §8.5 + §9 표면 8·8b·9b·9c·9d·10·11·14 (SD-10~14 · SD-OPEN-2)"
created: 2026-07-10
owner: autopilot-code
excluded_paths: ["loops/**", "tools/fleet/**"]
---

# Plan (국문 mirror) — stage-dispatch Phase 2 (배선 완성 + 확산 + drill 회귀)

> **청사진 SoT**: `.agent_reports/spec/stage-dispatch/prd.md` — §12 Phase 2, §8.5 (SD-10~14), §9 영향 표면 표, §13/§14 결정 목록. 본 plan 은 Phase 2 만 구현. Phase 1(§9 표면 1–7, 8-반쪽, 9, 10, 11 core 반전)은 이미 main 머지(5b7cf33)·pilot 검증 완료.
>
> **제외 — 절대 편집 금지(타 세션 소유)**: `loops/**`(drill 러너)·`tools/fleet/**`. drill 회귀 케이스는 `loops/` 에 쓰지 않고 **본 plan 디렉토리 아래 handoff 산출물**로 정의(Phase I).
>
> **core-first**: core 문서 편집(Phase B)이 모든 파생 adapter/skill/wrapper 편집보다 먼저. 각 step 의 앵커 인용은 참고용 — live 파일이 진실이므로 편집 전 재-Read 로 현행 문구 확인. Phase 1 이 이미 core 표면 대부분을 갱신했으므로 §9 표의 "현행 문구"는 여러 곳이 stale 하다. 각 step 은 현행이 이미 stage-dispatch 를 반영하는지 표시.

## 오리엔테이션 — Phase 1 이 이미 한 것 (재작업 금지)

2026-07-10 본 워크트리에서 재실측(core 문서 조사 pass):

- `core/OPERATIONS.md §5.10` line 94 = 얇은 conductor 스테이지 분사 narrative(③), 클래스별 depth-2 write 소유(④), `Σ(conductor+활성 스테이지) ≤ 5` 동시성(⑤), model role 명시(⑦) 이미 있음. line 98 = stealth-death liveness 가드.
- `core/CONVENTIONS.md §1` line 34(stage graph Dispatch policy)·line 46(Depth contract, depth-2 두 용법에 스테이지-워커 포함) 이미 반영.
- `core/WORKFLOW.md §1.1` line 57 = standard depth-1 owner 가 얇은 conductor 로 각 스테이지 분사, 이미 있음.
- `core/DESIGN_PRINCIPLES.md §8` line 226 = SD-1/SD-2 승격 이미 기록; line 254 변경 이력.
- `adapters/{claude,codex,opencode}` bootstrap §0(C)/AGENTS.md = conductor→스테이지 depth-2 언어 이미 있음(claude CLAUDE.md §0(C); codex AGENTS.md line 69; opencode AGENTS.md line 60).
- `skills/autopilot-code/references/context-and-guards.md` line 52 = "금지" → "기본 권장" 반전 완료.
- `dispatch-headless.py` = `--depth 2 --parent --worker-role --owner --profile` 이미 지원, depth≥3 차단, `code-*` role 에 depth-2 스테이지-워커 depth_note 주입(159–186행).

**빠진 것 (본 plan 의 실작업)** — "반쪽 배선"(§8.5.1) + SD-11/12/13/14 신규 메커니즘:
1. `dev-pipeline.md` Step 1~7 **본문**이 여전히 `invoke Skill: code-<stage>` 명령형(이중 신호); line 4 계약 블록의 `e.g.` 비한정 escape hatch(SD-10).
2. `SKILL.md` Stage Graph 표에 dispatch 모드 표기 없음(SD-10b).
3. SD-11 reminder hook 부재; SD-14b Stop 게이트 부재; `dispatch-wait.sh` 부재; wrapper depth-1 depth_note 에 one-shot 대기 계약 없음; registry 갭(SD-14b②) 미수정; conductor 가 자기 slug 를 모름.
4. 스테이지-워커 프로필 fragment 부재(SD-12).
5. SD-13 spec 선보장 문구 부재.
6. draft/research/spec/design/lab 확산 미완(WORKFLOW §5 행 + 각 파이프 스테이지 분사 계약).
7. stage-dispatch drill 케이스 정의 부재.

---

## Phase A — SD-14b① 전제: `-p` 모드 Stop hook 발화 실측 검증 (게이팅 probe, 소스 편집 없음)

> **왜 먼저**: SD-14b(conductor Stop 게이트)는 `claude -p` one-shot 세션이 실제로 turn 종료 시 `Stop` hook 을 발화해야만 성립. spec(§8.5.7, §12-0)이 이를 명시 전제로 못박음 — **발화 안 하면 Stop 게이트 보류**, SD-14 (a)depth_note + (c)dispatch-wait 만 출하. 본 phase 는 Phase E hook B 를 분기하는 verdict 를 낸다.

### Step A1 — `claude -p` 하 `Stop` 발화 probe
- **동작**(scratch, repo 무변경): `Stop` hook 이 sentinel 파일에 한 줄 append 하는 throwaway config home 을 만들고, trivial `claude -p` turn 을 그 home 으로 1회 실행.
  ```bash
  T=$(mktemp -d); mkdir -p "$T/home/hooks"
  cat > "$T/home/hooks/stop-probe.sh" <<'EOF'
  #!/bin/sh
  echo "STOP_FIRED $(date -u +%FT%TZ)" >> "$STOP_PROBE_OUT"
  exit 0
  EOF
  chmod +x "$T/home/hooks/stop-probe.sh"
  cat > "$T/home/settings.json" <<EOF
  { "hooks": { "Stop": [ { "matcher": "*", "hooks": [ { "type": "command", "command": "sh \"$T/home/hooks/stop-probe.sh\"", "timeout": 10 } ] } ] } }
  EOF
  STOP_PROBE_OUT="$T/fired.log" CLAUDE_CONFIG_DIR="$T/home" claude -p "say ok" >/dev/null 2>&1 || true
  cat "$T/fired.log" 2>/dev/null || echo "(Stop 미발화)"
  ```
  - env 이름 참고: wrapper 는 자식 세션에 `CLAUDE_CODE_CHILD_SESSION=1` + `AGENT_DISPATCH_DEPTH` 를 심음(dispatch-headless.py 384–386행). probe 는 이 env 불필요 — `-p` 모드에서 `Stop` 이 **발화하는가**만 판정.
- **기록**: 결과를 `_internal/dev_reviews/phaseA_stop_probe.md`(execute 단계)에 쓰고 `test_logs/`·`final_report.md` 에 노출.
- **분기(checklist Decision Points 기록)**:
  - **발화** → Phase E 가 hook B(conductor Stop 게이트) + settings 등록 + conformance 테스트 설치.
  - **미발화** → Phase E 는 hook B 등록 **전면 skip**; 대신 Stop hook 스크립트를 디스크에 두되(미등록) 헤더에 노트, `final_report.md` 에 "Stop 게이트 보류: `-p` Stop 미발화(probe <date>)" 기록. SD-14 는 (a)depth_note + (c)dispatch-wait 로 출하. **하드 분기 — 발화 안 하는 hook 을 등록하지 말 것.**

### Step A2 — 런타임 현행성 점검(bounded)
- 글로벌 Runtime-currentness gate 대로, Stop-hook 결정 확정 전 현행 Claude Code hook 문서에서 `-p`/headless 하 `Stop` 동작을 빠르게 확인(WebFetch/WebSearch, ≤2 쿼리). 공식 문서가 probe 와 모순되면 probe(실측)를 우선하되 불일치를 `final_report.md` 에 기록. 여기서 블록하지 않음 — probe 가 분기의 권위.

---

## Phase B — core 문서 증분 (core-first; 파생 파일보다 먼저 편집)

> 네 core 파일 모두 Phase-1 stage-dispatch 언어 보유. Phase 2 는 **SD-14 one-shot 대기 계약** + **SD-13 spec 선보장**(OPERATIONS), **확산 행 + lab 신규 행**(WORKFLOW §5), **capability-중립 확산 명시**(CONVENTIONS §1), **경량 SD-14 결정론 노트**(DESIGN_PRINCIPLES §8/§0.7)만 추가. 최소·additive — 잘 작동하는 기존 문장 재작성 금지.

### Step B1 — `core/OPERATIONS.md §5.10`: SD-14 one-shot 대기 계약 + SD-13 spec 선보장
- **파일**: `core/OPERATIONS.md`. §5.10 "풀 ceremony(headless 분사)" 불릿 **line 94**, stealth-death 가드 **line 98**(내용으로 재탐색 — 줄번호 drift 가능).
- **현행(line 98 head)**: `**stealth-death 가드 (분사 후 대기 자리 — 필수, §0.5 결정론)**: ⚠️ hung/crash 한 adapter-specific headless main 은 _exit 를 안 해 완료 알림이 영영 안 올 수 있다_ …` (ALIVE/SUSPECT/DEAD liveness 명령 계약 이어짐).
- **편집(SD-14, additive)**: stealth-death 문장 직후 **one-shot 대기 계약** 절 추가(stealth-death 와 구분되는 신규):
  > **one-shot 대기 계약(§8.5.7 SD-14)**: adapter headless main(conductor 포함)은 **one-shot 프로세스** — turn 종료 = 프로세스 종료. background 완료 알림은 그 프로세스가 살아 있을 때만 유효하므로, conductor 는 스테이지 분사 후 **Monitor·완료 알림 대기로 turn 을 끝내지 않는다**; 같은 turn 안 `utilities/dispatch-wait.sh`(dispatch-liveness 재사용) 반복 호출로 스테이지 종료를 폴링한 뒤 수확한다. 결정론 강제 3층 = (a) wrapper depth_note 주입 (b) conductor Stop hook 게이트(open 자식 row 시 차단, `-p` Stop 발화 검증 전제) (c) `dispatch-wait` 헬퍼.
- **편집(SD-13, additive)**: ③ conductor narrative(line 94)에 spec 선보장 절 1개:
  > **spec 전제 선보장(§8.5.4 SD-13)**: conductor 는 스테이지 분사 _전_ 대상 repo 의 spec 전제(artifact root 존재 + `spec/` 존재 또는 `/track` untracked)를 선확인한다 — 스테이지 세션은 풀 ceremony(artifact-guard 생성-순서 게이트 포함)를 받으므로, 전제 미충족을 스테이지 안 차단으로 발견하면 재분사 비용, conductor 게이트에서 잡으면 무료.
- **검증**: `grep -n "one-shot 대기 계약\|spec 전제 선보장" core/OPERATIONS.md` 둘 다; `grep -c "stealth-death"` 불변(기존 가드 중복 없음).

### Step B2 — `core/WORKFLOW.md §5`: 확산 행 + autopilot-lab 신규 행
- **파일**: `core/WORKFLOW.md` §5 표(헤더 line 105, 행 111–119).
- **현행**(autopilot-code 행 115 는 이미 스테이지 분사 반영; 확산 대상은 미반영):
  - `111 autopilot-research`, `113 autopilot-spec`, `114 autopilot-design`, `117 autopilot-draft`, `118 autopilot-refine`.
  - **autopilot-lab 행은 §5 에 없음.**
- **편집**: 111/113/114/117/118 각 행에 행 115 패턴을 본뜬 짧은 절 append:
  > `` `standard+` 에선 각 durable 스테이지가 **독립 headless 세션**(OPERATIONS §5.10 ③④)이고 위 팀은 그 스테이지 세션 _안_ 에서 실행 — depth-1 conductor 는 산출물 경로만 넘긴다. `direct/quick` 은 inline. ``
  - 파이프별 스테이지-워커 클래스 = 각 파이프의 §6-동형 표(Phase H). WORKFLOW 행 절은 generic 유지, 구체 스테이지→클래스 매핑은 각 파이프 reference 문서(Phase H)에 두어 이중 기재 회피.
- **신규 행(autopilot-lab)**: 118 뒤(또는 research/실험 entry 근처)에 신규 행:
  > `| **autopilot-lab** | (setup) 연구팀 plan-review + 개발팀 new-lib scaffold + 테스트팀 smoke / (eval) 테스트팀 functional + 자료팀 figure-gen + 연구팀 research-survey. `standard+` setup/eval 스테이지는 독립 headless 세션(OPERATIONS §5.10 ③④), 팀은 세션 _안_. `direct/quick`·단발 실험 run 은 inline |`
- **검증**: `grep -n "autopilot-lab" core/WORKFLOW.md` 신규 §5 행; 확산 각 행에 "독립 headless 세션" 포함.

### Step B3 — `core/CONVENTIONS.md §1`: capability-중립 확산 명시 (경량)
- **파일**: `core/CONVENTIONS.md §1`, Depth contract **line 46**(이미 `code-plan/execute/test/report` 스테이지-워커 열거).
- **현행(line 46)**: `(b) **pipeline stage-workers** — the conductor dispatches each sub-skill stage (e.g. code-plan/execute/test/report) as its own depth-2 headless session …`
- **편집(additive, 절 1개)**: 괄호를 일반화해 code 전용으로 읽히지 않게:
  > `… each sub-skill stage (code-* for autopilot-code; the homologous stage set for autopilot-draft/research/spec/design/lab — see each pipe's stage-worker table) as its own depth-2 headless session …`
- stage-graph Dispatch-policy 열(line 34)은 intensity-keyed·capability-중립 — **편집 불요**(이미 모든 `standard+` 파이프 적용). 확인 후 dev_logs 에 "변경 불요" 기록.
- **검증**: `grep -n "homologous stage set" core/CONVENTIONS.md`.

### Step B4 — `core/DESIGN_PRINCIPLES.md`: SD-14 결정론 노트 (경량)
- **파일**: `core/DESIGN_PRINCIPLES.md`. §8 line 226 이미 SD-1/SD-2 기록. §0.7(39–61행) 의미↔규칙 경계.
- **편집(§8, 기존 226 노트에 문장 1개 append)**:
  > 대기·수확도 이 결정론 흐름의 일부다(SD-14): conductor 의 스테이지 대기는 완료 알림 신뢰가 아니라 `dispatch-wait`(liveness 재사용) 폴링 + Stop hook 게이트로 결정론화되고, 죽은 스테이지 해석만 conductor 의미 판단으로 남는다.
- **편집(§0.7 coverage, 선택 — 자연스러울 때만)**: PRD §14 v2 추가를 절 1개로 미러 — SD-11 이 deny 아닌 reminder 로 시작(hook 이 intensity 를 결정론적으로 못 아는 구간 존중), SD-14b 피드백이 "대기 강제" 아닌 liveness 진단→행동 분기. §0.7 열거 목록에 자연스런 삽입점 있으면 추가, 없으면 skip(PRD §14 를 SoT 로 두고 억지 삽입 금지).
- **검증**: `grep -n "SD-14" core/DESIGN_PRINCIPLES.md`.

---

## Phase C — SD-14 wrapper 증분 + `dispatch-wait.sh` 헬퍼

> **먼저 재실측(§8.5.7 노트)**: 타 세션이 `AGENT_HOME` registry 갭을 이미 패치했을 수 있음. 편집 전 `dispatch-headless.py` `resolve_agent_home()`(269–273행)·`utilities/agent-home.sh` 재-Read, 갭이 남아있을 때만 수정. plan 시점 확인: `resolve_agent_home()` 가 `ROOT`(=`parents[3]`=worktree)로 폴백, `agent-home.sh` 는 `$HOME/agent_setting` 으로 폴백 → 불일치.

### Step C1 — SD-14b② registry 갭 수정 (`dispatch-headless.py`)
- **파일**: `adapters/claude/bin/dispatch-headless.py`, `resolve_agent_home()`(269–273행):
  ```python
  def resolve_agent_home() -> Path:
      env_home = os.environ.get("AGENT_HOME")
      if env_home and (Path(env_home) / "core" / "CORE.md").is_file():
          return Path(env_home)
      return ROOT
  ```
- **문제**: `AGENT_HOME` unset 시 wrapper 는 `ROOT/.dispatch`(worktree)에 jobs.log 를 쓰는데, `utilities/dispatch-liveness.sh`(+미래 Stop hook·`dispatch-wait.sh`)는 `agent-home.sh` → `$HOME/agent_setting/.dispatch` 로 registry 를 잡음 → 서로 다른 registry → Stop 게이트/liveness 가 wrapper 가 쓴 row 를 못 봄.
- **편집**: `AGENT_HOME` 체크 후 **`agent-home.sh` 와 동일 체인**(`CLAUDE_HOME` → `$HOME/agent_setting`(core/CORE.md 보유 시) → `$HOME/.claude`(core/CORE.md 보유 시))으로 폴백, 마지막에 `ROOT`:
  ```python
  def resolve_agent_home() -> Path:
      def _valid(p):
          return p and (Path(p) / "core" / "CORE.md").is_file()
      for cand in (os.environ.get("AGENT_HOME"),
                   os.environ.get("CLAUDE_HOME"),
                   str(Path.home() / "agent_setting"),
                   str(Path.home() / ".claude")):
          if _valid(cand):
              return Path(cand)
      return ROOT
  ```
  근거: `agent-home.sh` 선호 순서를 미러해 writer(wrapper)·readers(liveness/Stop/dispatch-wait)가 단일 registry 합의. `ROOT` 는 최후 폴백으로 남겨 설치 home 없는 격리 worktree 도 동작.
- **검증**: `AGENT_HOME= CLAUDE_HOME= python3 adapters/claude/bin/dispatch-headless.py --dry-run --worktree "$PWD" --slug t --capability code-plan --mode dev --qa standard --depth 1 --model-role "deep maker" | grep job_registry` 가 `"$(utilities/agent-home.sh)/.dispatch/jobs.log"` 와 동일. liveness 가 같은 파일 읽는지 교차확인.

### Step C2 — 자식 env 에 `AGENT_DISPATCH_SELF_SLUG` 주입 (Stop 게이트 필수)
- **파일**: `adapters/claude/bin/dispatch-headless.py`, `action == "start"` env 블록(383–393행).
- **문제**: 자식 세션은 `AGENT_DISPATCH_PARENT_SLUG`(부모)는 받지만 **자기 slug 는 안 받음**. conductor Stop 게이트는 "`parent=` 가 *내 자신* slug 인 open job" 을 찾아야 하는데 self slug 없이는 불가.
- **편집**: `env.update({...})` 에 `env["AGENT_DISPATCH_SELF_SLUG"] = args.slug` 추가.
- **검증**: dry-run 출력이 이미 `slug=` 표시; dev_logs 에 start env 가 `AGENT_DISPATCH_SELF_SLUG` 보유 한 줄 assert. (동작 테스트는 Phase I drill 로 이월.)

### Step C3 — depth-1 `depth_note` 에 SD-14 one-shot 대기 계약 추가
- **파일**: `adapters/claude/bin/dispatch-headless.py`, `dispatch_prompt()` depth-1 `else` 브랜치(178–186행). 현행 depth-1 note 끝에 one-shot 절 append(depth-1 만 — depth-2 스테이지-워커는 자식 대기 안 함):
  > ` You are a one-shot process: ending your turn ends the process, and background completion notifications never arrive after that. After dispatching a stage, do NOT end the turn on a Monitor/notification wait — poll within the same turn using utilities/dispatch-wait.sh (which reuses dispatch-liveness) until the stage row leaves 'open', then harvest its artifact verdict and dispatch the next stage. On SUSPECT/DEAD, diagnose and re-dispatch rather than waiting.`
- **검증**: `--register` 로 temp `--jobs`/`--log-dir` 에 등록 후 `grep "one-shot process" <log-dir>/t.claude.prompt.txt`(dry-run 은 command 만 출력하므로 prompt 파일로 assert).

### Step C4 — 신규 헬퍼 `utilities/dispatch-wait.sh`
- **파일(신규)**: `utilities/dispatch-wait.sh`(repo-root utilities; `dispatch-liveness.sh` 가 `utilities/`·`adapters/claude/utilities/` 양쪽에 있으니 동일 dual 배치 또는 symlink 로 기존 패턴 복제).
- **계약**(`dispatch-liveness.sh` 재사용, liveness 재구현 금지):
  - 사용: `dispatch-wait.sh [--parent <self-slug>] [--jobs <path>] [--interval <s>] [--max <s>]`.
  - registry 는 liveness 와 동일 방식(`AGENT_HOME` → `agent-home.sh`) → C1 과 정합.
  - 루프(bounded, 단일 Bash timeout 존중 `--max` ≤ 600s): 각 iteration
    1. jobs.log 의 `open` 중 `parent=<self-slug>` 카운트(`--parent` 시) — 0 이면 `exit 0`(자식 전부 done → 수확).
    2. 아니면 `dispatch-liveness.sh <jobs>`; exit 3(SUSPECT/DEAD)이면 문제 row 출력 후 `exit 3`(호출자 진단/재분사, 대기 지속 X).
    3. 아니면 `sleep <interval>`(기본 20s) 반복, `--max` 초과 시 `exit 2`(호출자 재호출 — 반복 호출형이라 conductor 의 다음 Bash 호출이 폴링 지속).
  - exit code: `0`=대상 자식 done(수확), `2`=아직 alive, 재폴링(재호출), `3`=SUSPECT/DEAD(진단). iteration 마다 한 줄 status.
  - POSIX sh, `set -uo pipefail`, liveness 처럼 `agent-home.sh` source; **background 프로세스·nohup 금지**(스테이지-워커 의무 — 동기 전용).
- **검증**: `sh utilities/dispatch-wait.sh --jobs /nonexistent --parent x` → exit 0 "(open 자식 없음)"; temp jobs.log 에 parent 매칭 `open` row + 신선 fake transcript → exit 2(alive); stale/부재 transcript → exit 3. `utilities/dispatch-wait.test.sh`(conformance — 결정론, drill 아님, `dispatch-liveness.test.sh` 미러) 소규모 신설.

---

## Phase D — SD-12 스테이지-워커 프로필 (fragment + 선언)

> 모델: `profiles/lab-runner.yaml` + `profiles/fragments/lab-runner.md`. 로더 = `tools/profile/build-home.py`: yaml 필수 `name/description/harness`, `model_role` **XOR** `model`, `fragments:` = 존재하는 repo-상대경로 list, `expose:` = `{skills,agents,triggers}` 만. bootstrap = `templates/bootstrap-<harness>.md` + fragments 순서 평문 concat.

### Step D1 — fragment 4개 `profiles/fragments/code-{plan,execute,test,report}.md`
- 각 = 최소 L2 role fragment, 헤딩 `## L2 — code-<stage> specialization`, 그 스테이지 계약만: (i) 자기 sub-skill role + 위임 in-session 팀(기획팀/개발팀/품질관리팀 test/품질관리팀 report), (ii) 입력 산출물 경로 + 출력 write 클래스(§6 / OPERATIONS §5.10 ④), (iii) file-only handoff + "입력은 파일에서, 앞 스테이지 대화 X", (iv) "재분사 금지(여기서 depth-1 금지); 내부 병렬 = in-session 팀". `fragments/lab-runner.md` 4소절(specialization/discipline/convention/stay-in-lane) 밀착 모델.
  - **code-plan**: `plans/<slug>/plan/{plan.md,plan_ko.md}` + `_internal/plan_reviews/` write; task + 기존 `plans/` read. 기획팀.
  - **code-execute**: 소스 + `plans/<slug>/{checklist.md,dev_logs/,_internal/dev_reviews/}` + plan frontmatter `status` write; `plan/plan.md` read. 개발팀. **소스 mutation 유일 스테이지.**
  - **code-test**: `plans/<slug>/{test_logs/,_internal/test_reviews/}`(소스 read-only) write; `plan.md` verification + `checklist.md` read. 품질관리팀 test.
  - **code-report**: `final_report.md` + `analysis_project/code/*` + `pipeline_summary.md`(§5.8 lock) write; plan/checklist/dev_logs/test_logs/_reviews read. 품질관리팀 fast writer.
- 각 ≤ ~30줄 — 요점은 full CLAUDE.md 대비 *최소* bootstrap(SD-12 토큰 절감).

### Step D2 — 선언 4개 `profiles/code-{plan,execute,test,report}.yaml`
- `lab-runner.yaml` 미러:
  - `name: code-<stage>`; `description:` 한 줄(main 라우팅 라벨).
  - `harness: claude`.
  - `model_role:` (CONVENTIONS §2.3 / SD-5): code-plan=`deep maker`, code-execute=`fast implementer`, code-test=`fast reviewer`(가변 — strong+ 에서 conductor 가 deep 상향 가능, 프로필 기본은 fast), code-report=`fast writer`. (concrete `model` 아닌 `model_role` — portable 경계.)
  - `fragments: [profiles/fragments/code-<stage>.md]`.
  - `expose:` 최소 — `skills: [code-<stage>, autopilot-code, post-it]`(+ code-report 는 analysis_project update 용 `analyze-project`), `agents:` 쓰는 팀 하나(`plan-team`/`dev-team`/`qa-team`), `triggers: []`.
- **model override 노트**: 프로필 `model_role` 은 *기본값*; conductor 의 분사 라인 `--model-role <role>` 이 여전히 지배(SD-5 명시 선택). fragment 에 "프로필 기본은 분사별 override 가능" 명시.

### Step D3 — `profiles/README.md` 카탈로그 등록 + 검증
- `profiles/README.md` 카탈로그 표에 4행(name + 한 줄 description) 추가 → main 이 이름으로 라우팅.
- **검증**: 각 스테이지 `python3 tools/profile/build-home.py code-<stage> --check` exit 0(선언/템플릿/fragment 존재 + 결정론 재조립). checker 가 내는 XOR/필드/경로 오류 수정.

### Step D4 — SD-12/SD-OPEN-1 계측 연결 (측정, 게이팅 아님)
- conductor 분사 라인(Phase F)이 `--profile code-<stage>` 전달 → jobs.log row 가 `profile=code-<stage>` 보유(wrapper 가 이미 append, 261–262행). *기록*엔 코드 변경 불요. 토큰/시간 비교는 Phase J 가 계측 로그 형식 정의; 여기선 full-bootstrap-vs-최소-프로필 비교가 가능하도록 프로필 배선만 보장.

---

## Phase E — Hooks: SD-11 reminder(soft) + SD-14b Stop 게이트(Phase A 게이팅)

> HOOKS.md 계약: hook **출력 shape** 은 **conformance** 층(`hooks/portable-guards.test.sh`), drill 아님; 에이전트 **행동** 만 drill(Phase I). 신규 hook 을 HOOKS.md Invariant Catalog 에 등록. 두 hook 모두 **에러 시 never-block**(fail-open), Stop 게이트의 의도된 결정론 차단만 예외.

### Step E1 — `hooks/stage-dispatch-reminder.sh` (SD-11, soft / non-deny)
- **파일(신규)**: `hooks/stage-dispatch-reminder.sh`. 패턴: `PreToolUse(Skill)` matcher, 단 `deny`(worktree-path-guard)가 아니라 **`additionalContext`(non-deny)** emit(spec-sync-nudge 식). `tool_input.skill` 파싱은 spec-skill-gate 식.
- **발화 조건(전부 성립, 아니면 clean `exit 0`)**:
  - env `CLAUDE_CODE_CHILD_SESSION=1` **and** `AGENT_DISPATCH_DEPTH=1`(conductor, main·depth-2 아님), **and**
  - `AGENT_DISPATCH_INTENSITY` ∈ {`standard`,`strong`,`thorough`,`adversarial`}(direct/quick 아님 — 그것들은 정당히 inline; deny 가 틀리고 reminder 가 맞는 이유 §8.5.2), **and**
  - `skill` ∈ {`code-plan`,`code-execute`,`code-test`,`code-report`}.
  - 재귀 가드: `[ "${MEM_DISTILL:-}" = "1" ]` → stdin drain, `exit 0`(메모리 hook 미러).
- **emit `additionalContext`**(reminder, 차단 아님):
  > `📌 stage-dispatch: 이 세션은 depth-1 conductor(intensity=<..>)입니다. code-<stage> 를 in-session Skill 로 직접 부르는 대신 dispatch-headless.py --depth 2 --parent $AGENT_DISPATCH_SELF_SLUG --worker-role code-<stage> 로 스테이지를 분사하고 dispatch-wait 로 수확하세요 (dev-pipeline Step 1~7). in-session Skill 은 direct/quick 또는 headless-불가 런타임 fallback 자리에서만.`
- **왜 soft(deny 금지)**: hook 은 이 자리가 정당한 headless-불가 런타임 fallback 인지 결정론적으로 못 앎 → deny 는 false-positive 위험. deny 상향은 drill/계측 후 이월(§8.5.2, §14-(4)).
- **등록**: `adapters/claude/settings.json` `PreToolUse` 배열, 신규 `{ "matcher": "Skill", "hooks": [ { "type":"command", "command":"sh \"$HOME/.claude/hooks/stage-dispatch-reminder.sh\"", "timeout":10 } ] }`(기존 `spec-skill-gate.sh` Skill matcher 와 공존).
- **CLI 모드**: conformance 테스트 위해 `--skill/--cwd/--session/--depth/--intensity` 지원.
- **conformance 테스트**(`hooks/portable-guards.test.sh`): (i) conductor+standard+code-plan → additionalContext emit; (ii) direct/quick → no-op; (iii) depth-2 스테이지 세션 → no-op; (iv) non-code skill → no-op; (v) main(자식 env 없음) → no-op.

### Step E2 — `hooks/conductor-stop-gate.sh` (SD-14b) — **Phase A verdict 조건부**
- **Phase A Step A1 이 `-p` 하 `Stop` 발화 확인했을 때만.** 미발화 시: 스크립트를 디스크에 생성(향후용), 헤더에 "UNREGISTERED: `-p` Stop 미발화(<date> probe) — final_report 참조" 노트, **settings.json 등록 안 함**; `final_report.md` 에 보류 기록. 이 step 의 등록 + conformance 발화 테스트 skip(CLI unit 테스트만 유지).
- **파일(신규)**: `hooks/conductor-stop-gate.sh`. `Stop` matcher.
- **발화 조건**: env `CLAUDE_CODE_CHILD_SESSION=1` + `AGENT_DISPATCH_DEPTH=1`(conductor) + `AGENT_DISPATCH_SELF_SLUG` 설정(C2). 아니면 clean `exit 0`. 재귀/루프 가드: Stop payload 의 `stop_hook_active` 존중 — 이미 active 면 `exit 0`(무한 차단 방지). 메모리-distill 가드 동일.
- **로직**:
  1. jobs.log 를 `agent-home.sh` 로 해석(C1/liveness 와 동일 registry).
  2. `parent=$AGENT_DISPATCH_SELF_SLUG` 인 `open` row 카운트. 0 이면 `exit 0`(conductor 종료 허용).
  3. ≥1 open 자식이면 `utilities/dispatch-liveness.sh <jobs>`:
     - **ALIVE**(exit 0, SUSPECT 없음) → **Stop 차단** + 행동 피드백: "열린 스테이지 자식 N개 실행 중 — turn 끝내지 말고 dispatch-wait 로 폴링 후 수확." (결정론 차단: Claude Stop hook 스키마의 block JSON emit — `{"decision":"block","reason":"..."}` 또는 현행 `hookSpecificOutput` 등가; 정확 스키마는 Phase A Step A2 에서 live 문서 확인.)
     - **SUSPECT/DEAD**(exit 3) → **대기 강제 X**(죽은 스테이지가 conductor 를 영구 hang 시키는 역전 방지): 차단 + **행동** 피드백 = "스테이지 자식 SUSPECT/DEAD — 대기 금지. transcript tail·dispatch 로그로 진단 → 수확/재분사 → jobs.log row 정리 후 종료." (§8.5.7, §14-(5): 피드백은 liveness→행동 분기, "대기하라" 아님.)
- **등록**(Phase A 발화 시만): `adapters/claude/settings.json` `Stop` 배열, 기존 `herdr-agent-state.sh idle` Stop hook 옆.
- **CLI 모드 + conformance 테스트**: `--self-slug/--jobs/--stop-active` 플래그; 케이스 — open 자식 없음→exit 0; open+alive→차단; open+dead→진단-차단; stop_hook_active→exit 0; non-conductor env→exit 0. (결정론 출력-shape assert → conformance, HOOKS.md 대로.)

### Step E3 — HOOKS.md Invariant Catalog + settings parity
- 두 hook 을 `core/HOOKS.md` Invariant Catalog 에 추가(name, event, invariant, fail-open 노트; Stop 게이트는 "`-p` Stop 발화 조건부" 표기).
- **parity 노트**: codex/opencode 는 자체 hook bridge. SD-11/SD-14b 는 Claude-first; codex/opencode `AGENTS.md` dispatch 절(Phase G)에 conductor one-shot 대기 계약이 그들의 `preflight.sh liveness` 로도 적용됨 한 줄 추가. 이번 phase 에 Claude hook 스크립트를 타 adapter 로 포팅하지 **않음**(범위 밖, follow-up 노트).

---

## Phase F — SD-10: `dev-pipeline.md` dispatch-first 재작성 + `SKILL.md` Stage Graph

> Phase 2 **최우선(priority 0)**. Phase C–E 메커니즘(dispatch-wait, 프로필, hook) 참조 — 그것들이 먼저 있어야 재작성 명령이 실행·검증 가능.

### Step F1 — `dev-pipeline.md` Step 1~7 dispatch-first 명령형 재작성
- **파일**: `skills/autopilot-code/references/dev-pipeline.md`.
- **비한정 escape hatch 제거**(line 4 계약 블록, 현행): `When still orchestrating in-session (e.g. `--intensity` downgraded, or a runtime without headless dispatch), invoke each stage via the Skill tool as written below …`
  - `e.g.` 개방 목록을 **닫힌 2조건 fallback** 으로 교체: `The in-session Skill path is a fallback used only when [a] intensity is direct/quick (micro-stages, no dispatch) or [b] the runtime has no headless dispatch (codex/opencode preflight reports unavailable). In all other standard+ cases, dispatch is mandatory, not optional.`
- **각 `standard+` 스테이지 step(1,3,4,5 + retry 6/7) 본문** 을 `invoke Skill: code-<stage>` → dispatch-first 로 재작성. Step 1 템플릿(3/4/5·retry 재실행/재테스트에 동형 적용):
  - **Step 1(code-plan)** 신규 본문:
    > `standard+` 는 code-plan 을 독립 depth-2 세션으로 분사(in-session 호출 X). 먼저 SD-13 spec 전제(artifact root + `spec/`, 또는 `/track`) 선확인. 다음:
    > ```
    > REPORTS_DIR=.agent_reports; [ -d .claude_reports ] && [ ! -d .agent_reports ] && REPORTS_DIR=.claude_reports
    > python3 <agent-home>/adapters/claude/bin/dispatch-headless.py --start \
    >   --worktree "$PWD" --slug <cycle-slug> \
    >   --capability code-plan --mode dev --qa <qa> --intensity <intensity> \
    >   --depth 2 --parent <cycle-slug> --worker-role code-plan --owner autopilot-code \
    >   --model-role "deep maker" --profile code-plan \
    >   --prompt-text "<sub-skill 계약 + 입력 산출물 절대경로 + 출력 계약 + slug>"
    > ```
    > 같은 turn 에서 폴링+수확(one-shot 대기 계약, SD-14):
    > ```
    > sh <agent-home>/utilities/dispatch-wait.sh --parent <cycle-slug>   # exit 0=done, 2=재호출, 3=진단
    > ```
    > exit 0 까지 dispatch-wait 반복, 그다음 plan frontmatter `status` + plan 경로만 읽어(verdict/status, plan 본문 X) Step 2 로. exit 3 이면 dispatch-liveness + transcript tail 진단 → 그 스테이지만 재분사(기존 산출물 재사용, SD-6). **분사 프롬프트는 입력 산출물 경로만 — plan 본문·앞 스테이지 대화 절대 X.**
  - **Step 3(code-execute)**: 동형, `--worker-role code-execute --model-role "fast implementer" --profile code-execute`; 입력 = `plan/plan.md` 경로; 수확 후 conductor 가 plan frontmatter `status` 읽음(Step 3/4 사이 Status Check 유지 — 이제 in-session 반환 아닌 파일 읽기).
  - **Step 4(code-test)**: `--worker-role code-test --model-role "fast reviewer" --profile code-test`; 입력 = `plan.md` verification + `checklist.md`; conductor 가 `test_logs/test_report.md` Level verdict 읽음.
  - **Step 5(code-report)**: `--worker-role code-report --model-role "fast writer" --profile code-report`.
  - **retry loop(6/7)**: memo 주입 + checklist 리셋 + code-refine/execute/test 재분사 유지하되 재실행/재테스트가 `invoke Skill` 이 아닌 **재분사** 명령(동일 템플릿). conductor 롤백(`git checkout <safety-commit>`)은 conductor 측 유지(`checklist.md` 에서 Safety commit 읽음 — 파일 read, 얇은 conductor 에 OK).
- **fallback 본문 유지**: 각 스테이지 step 아래 "[direct/quick] 또는 [headless-불가 런타임] fallback: invoke Skill: code-<stage>" 짧은 줄 유지 → 2조건 fallback 구체화.
- **plan-check(Step 2) inline 유지**(마이크로-스테이지, 한 줄 verdict, SD-6 경계) — 분사 스테이지 아닌 inline 마이크로-스테이지로 명시.
- **검증**: `grep -n "e.g." dev-pipeline.md` 가 escape-hatch 줄 미매칭; `grep -c "dispatch-headless.py" dev-pipeline.md` ≥ 4(durable 스테이지당 1); 각 스테이지 step 에 `dispatch-wait` 포함.

### Step F2 — `SKILL.md` Stage Graph 표: dispatch 모드 표기
- **파일**: `skills/autopilot-code/SKILL.md`, Stage Graph 표(45–51행).
- **편집**: `standard`/`strong`/`thorough` 행(`standard+` 밴드)에 즉독 dispatch 마커 추가 — 예: `standard` Graph 셀에 `(각 스테이지 = depth-2 headless 분사, file-only handoff)` append. 최소안: 표 아래 문장 1개 `**`standard+` dispatch**: 각 durable 스테이지(code-plan/execute/test/report)는 depth-2 headless 세션으로 분사된다 (dev-pipeline Step 1~7; direct/quick·plan-check 마이크로-스테이지는 inline).`
- **검증**: `grep -n "depth-2 headless" skills/autopilot-code/SKILL.md`.

---

## Phase G — adapter bootstrap parity 증분 (SD-14 one-shot + 확산 노트)

> 표면 §9-10/11. conductor→스테이지 depth-2 언어는 이미 있음(Phase 1). Phase 2 는 **SD-14 one-shot 대기** 절 + 확산이 모든 `standard+` 파이프에 적용됨 포인터만 추가.

### Step G1 — `adapters/claude/CLAUDE.md §0(C)`
- 이미 "conductor(depth-1)는 … 각 스테이지를 depth-2 headless 세션으로 분사" 서술. stealth-death 문장에 절 1개 append: `conductor 는 one-shot 프로세스이므로 스테이지 분사 후 알림 대기로 turn 을 끝내지 말고 dispatch-wait 로 같은 turn 폴링·수확한다 (SD-14).` **core-first 노트**: 이 bootstrap 은 파생 — 등가가 `core/OPERATIONS.md §5.10`(Step B1)에 먼저 있는지 확인; CLAUDE.md 절은 포인터, SoT 아님.
- **검증**: `grep -n "one-shot" adapters/claude/CLAUDE.md`.

### Step G2 — `adapters/codex/AGENTS.md`(line 69) + `adapters/opencode/AGENTS.md`(line 60)
- 둘 다 이미 "Depth-2 has two regular uses … pipeline stage-workers …" 보유. 문장 1개 append: `The depth-1 conductor is a one-shot process — after dispatching a stage it must not end the turn on a notification wait; it polls the registered stage with `preflight.sh liveness` in the same turn and harvests, re-dispatching on SUSPECT/DEAD (SD-14 parity).`
- 3-adapter parity: 동일 절 문구(각 adapter `preflight.sh` 경로만 조정).
- **검증**: `grep -n "one-shot process" adapters/codex/AGENTS.md adapters/opencode/AGENTS.md`.

---

## Phase H — 확산: draft/research/spec/design/lab 파이프에 stage-dispatch 계약

> WORKFLOW §5 행(Phase B2)이 라우팅 절반; 본 phase 는 운영 절반 — 각 파이프 reference 문서에 **§6-동형 스테이지-워커 표** + 짧은 stage-dispatch 계약 블록 추가(dev-pipeline.md line 4 가 autopilot-code 에 하는 것을 미러). 각 표: 스테이지 → in-session 팀(불변, 스테이지 세션 안 실행) → 입력 산출물 → 출력 산출물 → write 클래스.

> **범위 규율**: 확산 = 각 파이프 기존 파이프라인 문서에 **dispatch 계약 + 스테이지-워커 클래스 표** 추가. 각 파이프의 step 본문을 명령형 dispatch 로 재작성하지 **않음**(그건 SD-10 급 파이프별 대공사; Phase 2 확산 범위는 *계약 + 매핑*, 파이프별 본문 재작성은 follow-up 노트). spec 의 "확산 = 스테이지 분사 계약 적용 + §6 동형 표"(§12-1)에 정합, 5-파이프 full SD-10 아님.

### Step H1 — autopilot-draft
- **파일**: `skills/autopilot-draft/references/pipeline-steps.md`. top 계약 블록 + 표 추가. durable `standard+` 스테이지-워커: draft-strategy(Skill), Step 4.1 Draft Generation(연구팀), Step 5.5 polish(편집팀). durable 산출물 쓰는 material/analysis 스텝(Step 1 material analysis, Step 4.0 자료팀 figure 추출)은 후보 스테이지; 순수 오케스트레이터/regex 스텝(Step 4b detector)은 inline(마이크로-스테이지). 입출력은 research 표 대로(draft.md, strategy.md, figure_index.md).

### Step H2 — autopilot-research
- **파일**: `skills/autopilot-research/references/pipeline-search-analysis.md` + `report-generation.md`. 스테이지-워커: Step 2 search(연구팀), Step 3b skimming(연구팀 batch), Step 3e compile(연구팀), Step 4a report(연구팀), Step 4b QA(연구팀/codex-review-team). material(자료팀 browser-fetch/web-image)은 스테이지 안 하위 위임. depth-gated 스텝(2e/3c)은 조건부 스테이지로 표기.

### Step H3 — autopilot-spec
- **파일**: `skills/autopilot-spec/references/prd-authoring.md` + `scaffolding.md`. spec 스텝 대부분은 오케스트레이터-직접(PRD 작성) — 자연스런 dispatch 스테이지 **아님**(`spec/prd.md` 직접 write, conductor 자신의 판단 표면). 명확한 스테이지-워커 = **Phase 2 scaffold(개발팀 new-lib)** — 분리 가능·산출물 생산 스테이지. scaffold 를 주 dispatch 스테이지로 매핑, PRD 작성은 conductor-inline 로 표기. 이 비대칭 명시(모든 파이프가 4 대칭 스테이지 갖지 않음).

### Step H4 — autopilot-design
- **파일**: `skills/autopilot-design/SKILL.md`(`references/` 없음 — 파이프는 SKILL.md 본문). 스테이지가 이미 sub-skill(design-init/refs/tokens/components/review/handoff)로 깔끔히 매핑, 각각 이미 디자인팀 모드 위임. stage-dispatch 계약 추가: `standard+` design phase 는 depth-2 세션 분사; design phase 는 `[CONFIRM Gate]` 보유 — conductor 가 분사 phase 사이 게이트 verdict 쥠(파일: `design_state.yaml` phase status).

### Step H5 — autopilot-lab
- **파일**: `skills/autopilot-lab/references/setup-procedure.md` + `eval-procedure.md`. 스테이지-워커: setup S1 spec(연구팀 plan-review), S2 scaffold(개발팀 new-lib), eval E2(테스트팀), E3-2 plot(자료팀), E3-3 compare(연구팀). **lab 특수 nuance**: 실제 실험 *run* 은 흔히 장시간/async·사람 게이트(RUNLOG ⏳) — 이건 dispatch 스테이지 **아님**(실제 학습 대기); scaffold/eval/report 스테이지만 분사. 명시할 것. (`lab-runner.yaml` 프로필이 이미 있는 이유 — run 세그먼트는 자체 프로필; stage-dispatch 계약은 그와 합성.)

### Step H6 — §6-동형 표 일관성
- 각 파이프 추가 표는 OPERATIONS §5.10 ④ / spec §6 와 동일 컬럼: `스테이지 | in-session 팀 | 입력 산출물 | 출력 산출물 | write 클래스`. 두 스테이지가 lock 없이 같은 공유 파일 mutation 주장 없는지 교차확인(code-report `pipeline_summary.md` lock 예외 미러). **검증**: 5 파이프 문서 각각 "스테이지-워커" 표 + "file-only handoff" 절 보유; `grep -rl "stage-worker\|스테이지-워커" skills/autopilot-{draft,research,spec,design,lab}` 5개 전부.

---

## Phase I — drill 회귀 케이스 **정의** (handoff 산출물; loops/** 에 쓰지 않음)

> **하드 제약**: `loops/**` 타 세션 소유·편집 금지. 케이스를 **본 plan 디렉토리 아래 handoff 산출물**로 전달, loops-소유 세션이 `loops/drill/cases_growing/` 에 넣도록 정확한 4-파일 내용 완비.

### Step I1 — 케이스 정의 산출물 작성
- **디렉토리(신규, plan 아래)**: `.agent_reports/plans/2026-07-10_stage-dispatch-phase2/drill_case_stage_dispatch/`:
  - `README.md` — 설치 안내: "`loops/drill/cases_growing/g_stage_dispatch/` 에 복사; growing tier(2회 연속 PASS → `cases/` 승격); AXIS=git(jobs.log 검사); 비용 큼(headless 스테이지 분사) — g6 규율 미러."
  - `prompt.md` — fixture repo(**이미 `spec/` 보유** → SD-13 전제 성립)에서 `standard+` 다파일 dev 작업을 트리거하는 한 줄 발화, 스킬 문서만 주어진 상태(프롬프트에 dispatch 떠먹임 X) — §8.5.5 문서-효력 테스트.
  - `config` — `MAX_TURNS=120 TIMEOUT=2400 AXIS=git`(g6 보다 큼 — full 스테이지 파이프).
  - `fixture.sh` — `.agent_reports/spec/prd.md` + `pipeline_state.yaml` + 소스 몇 개 있는 throwaway repo 구성; `main` sha 를 `.pre/` 기록.
  - `assert.sh` — hard = **금지된 결과만**(drill 규율): main ref 불변(직접 main 커밋 X); jobs.log 에 depth-3 row 없음(`depth=3` 부재); non-execute 워커의 소스 write 없음. soft `WARN:`(turn-cap 관용) = `depth=2` 스테이지 row + `parent=<cycle-slug>` + `worker_role=code-plan|execute|test|report`; 스테이지 산출물 존재(`plan/plan.md`, `checklist.md`, `test_logs/`); `pipeline_summary.md` lock 미경합. **문서-효력 WARN**: `.dispatch/` 에 `dispatch-headless.py ... --depth 2 --worker-role code-*` 호출 흔적 ≥1 — 문서만으로 분사 발생.
- `fixture.sh`/`assert.sh` 는 `g6_worktree_dispatch` 모델(jobs.log grep 패턴 확립). `.pre/main_sha` 관용구 재사용.

### Step I2 — handoff 노트
- `final_report.md` 에 "drill handoff" 줄: 케이스는 plan 아래 정의, loops-소유 세션이 설치. `loops/` 무편집. (선택 `post-it` 로 그 세션용 handoff memo — Phase J.)

---

## Phase J — 계측 + SD-OPEN 관찰 (측정만; 임계 결정 없음)

### Step J1 — 계측 로그 형식(SD-OPEN-1 누적 + SD-12 토큰/시간)
- (`final_report.md` + 소규모 `plans/<slug>/instrumentation.md` 에) stage-dispatch run 당 기록 컬럼 정의: 스테이지, `profile=`(full-bootstrap vs `code-<stage>` 최소), model_role, wall-clock(jobs.log ts start→done), conductor 컨텍스트 크기 proxy. **마이크로-스테이지 inline 임계 확정 금지** — 누적만(SD-OPEN-1, §12-5). Phase-1 pilot 표본(plan 218s/execute 255s/test 46s/report 28s)을 연속성 위해 첫 행으로.

### Step J2 — SD-OPEN-2 curator 관찰
- 각 스테이지 세션이 SessionEnd mem curator(distiller) 기동하는지 기록. distiller 는 `MEM_DISTILL_ENABLE=1`(settings env) 게이트. 계측 = `instrumentation.md` 에 스테이지 세션당 "curator fired: yes/no" + 중복 `mem add` 발생 여부. **관찰만** — 개입 없음(§8.5.6, §13 SD-OPEN-2). 교차확인: reminder/Stop hook 이 이미 `MEM_DISTILL=1` 재귀 가드 → distiller 하위 세션 중 hook 발화 억제.

### Step J3 — cross-doc 동기화 + post-it handoff
- 편집 후 대응 산출물 동기화(변경의 일부, 별도 confirm X): `pipeline_summary.md` Decision Points; `post-it` handoff memo 로 (a) `loops/` 설치 대기 drill 케이스, (b) SD-14b Stop-게이트 분기 결과(등록/보류), (c) SD-11 deny 상향 이월 기록. 구현 선택이 청사진과 drift 했을 때만(spec-significance) spec 갱신 — 아니면 prd.md 무변경(본 plan 은 구현, 재-spec 아님).

---

## 검증 요약 (code-test 소비)

Level-graded (CONVENTIONS test taxonomy):
- **Syntax/lint**: `python3 -c "import ast; ast.parse(open('adapters/claude/bin/dispatch-headless.py').read())"`; 신규/편집 `.sh` 전부 `sh -n`(`dispatch-wait.sh`, `stage-dispatch-reminder.sh`, `conductor-stop-gate.sh`); `python3 -m json.tool adapters/claude/settings.json`.
- **Import/smoke**: `dispatch-headless.py --dry-run …`(C1 registry parity; C3 prompt one-shot 절 via --register temp); `build-home.py code-<stage> --check` × 4(D3).
- **Conformance**: `sh hooks/portable-guards.test.sh`(E1/E2 출력-shape 케이스 추가); `sh utilities/dispatch-wait.test.sh`(C4); `sh utilities/dispatch-liveness.test.sh`(불변, 회귀). repo-wide conformance 러너(`portable-guards.test.sh` + `tools/check-adaptation-boundary.sh`) 있으면 실행.
- **Functional**: dispatch-wait exit-code 매트릭스(0/2/3) temp jobs.log 대상; SD-11 reminder 가 conductor+standard+code-plan 에 additionalContext, direct/quick·depth-2·non-code·main 에 no-op.
- **문서-효력(drill 이월, Phase I)**: conductor 가 `dev-pipeline.md`/`SKILL.md` 만으로 스테이지 분사 — 에이전트 행동이라 결정론 테스트 아닌 drill 케이스.
- **grep assert**: 위 step별 grep(escape-hatch 제거; ≥4 스테이지 step 에 `dispatch-headless.py`; wrapper prompt·OPERATIONS·CLAUDE.md 에 `one-shot`; 5 파이프 + WORKFLOW §5 행(신규 lab 포함)에 확산 절).
- **무회귀 가드**: plan 이 `loops/**` 무편집 확인; `tools/fleet/**` write 없음 확인.

## Phase 순서·의존성 (code-execute용)

```
A (probe, E2 게이팅)
└─ B (core 문서, core-first)
   └─ C (wrapper+dispatch-wait)          ┐
   └─ D (프로필)                          ├─ 메커니즘; F 가 참조
   └─ E (hooks; E2 는 A 게이팅)          ┘
      └─ F (SD-10 dev-pipeline+SKILL, priority 0, C/D/E 참조)
         └─ G (adapter parity), H (확산), I (drill 산출물), J (계측)
```
- Phase 당 safe commit(checklist `Safety commit:` 헤더). 소스 mutation 은 Phase C(wrapper)·D(프로필-데이터)·E(hooks)·신규 `dispatch-wait.sh` + 나머지 문서 편집에 국한. 두 phase 가 같은 파일 mutation 안 함.
- Phase A 가 막히면(probe 불명확) 전 phase 진행; E2 등록만 보류 — 파이프는 완주(SD-14 a+c 는 무관하게 출하).

## 리스크 / conductor 노출 미결
- **SD-14b 스키마**: 정확한 Claude `Stop` hook block-JSON shape 을 E2 등록 전 live 문서 확인(Phase A Step A2) — plan 은 `{"decision":"block","reason":...}` 를 유력 shape 로 쓰되 검증 대상 표기.
- **확산 깊이**: Phase H 는 계약 + 매핑 표 전달, 파이프별 full 명령형 재작성 아님(§12-1 bounded 범위). 파이프별 SD-10 급 본문 재작성은 follow-up.
- **loops/** · **tools/fleet/**: 설계상 무편집; drill 케이스는 handoff 산출물만.
