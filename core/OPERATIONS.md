# Operations — Git·Worktree·Dispatch·Push 운영 (canonical)

> CONVENTIONS.md 에서 분리(2026-06-23, 앞/뒤 2층 재편). git 운영(lock·preflight·worktree dispatch·`<agent-home>` repo push)은 산출물 컨벤션과 결이 달라 별도 파일로. **§ 번호·heading 보존** — SKILL.md·drill·hook 이 `OPERATIONS.md#59-…` 등 anchor 로 인용. git 운영 단일 출처.

## §5.8. Pipeline Lock — 공유 artifact root 다중 worktree 가드 (canonical)

**왜**: 여러 git worktree 가 _하나의 canonical artifact root_ (`.agent_reports`, legacy `.claude_reports`) 를 symlink 공유할 때(릴리즈 브랜치 클린 유지 위해 산출물은 gitignore), 두 worktree 가 동시에 `spec/` 공유 단일파일(`prd.md`·`pipeline_state.yaml`·`pipeline_summary.md`)을 쓰면 lost-update. `plans/<cycle>/` 는 사이클별 폴더라 경로 분리 → 비경합(lock 불필요).

- **lock 파일**: `<artifact-root>/.pipeline-lock` (공유 트리에 위치 → 모든 worktree 가시). transient — artifact root 자체가 gitignore 라 추적 안 됨.
- **보호 범위**: `spec/prd.md`·`spec/pipeline_state.yaml`·`spec/pipeline_summary.md` _쓰기_ 구간만. 읽기·plans 쓰기는 비-lock.
- **stale 무시(override)**: 기록 `at` 이 30 분 초과 OR 기록 worktree == 현재 worktree(재진입/잔존 락) → 통과.

**acquire** — 쓰기 진입 _직전_ (autopilot-spec 의 Step 3 / update mode, autopilot-code 의 pipeline_state·summary 쓰기 / spec-drift update):

```bash
REPORTS_DIR=.agent_reports; [ -d .claude_reports ] && [ ! -d .agent_reports ] && REPORTS_DIR=.claude_reports
LOCK="$REPORTS_DIR/.pipeline-lock"; NOW=$(date +%s); WT=$(pwd -P)
if [ -f "$LOCK" ]; then
  LAT=$(sed -n 's/^at=//p' "$LOCK"); LWT=$(sed -n 's/^worktree=//p' "$LOCK"); LBR=$(sed -n 's/^branch=//p' "$LOCK")
  if [ "$LWT" != "$WT" ] && [ $((NOW-${LAT:-0})) -lt 1800 ]; then
    echo "BLOCKED: '$LBR' ($LWT) 이 $((NOW-LAT))s 전부터 spec 편집 중 — 대기 또는 죽은 락이면 rm $LOCK"; exit 3
  fi   # same-worktree 또는 stale(>30m) → override 통과
fi
printf 'worktree=%s\nbranch=%s\nskill=%s\nat=%s\nat_iso=%s\npid=%s\n' \
  "$WT" "$(git branch --show-current 2>/dev/null)" "${SKILL:-autopilot}" "$NOW" "$(date -Iseconds)" "$$" > "$LOCK"
```

`exit 3`(BLOCKED) → 쓰기 _중단_ 하고 "다른 worktree 가 spec 편집 중" 사용자 보고 + 대기/override 판단 요청.

**release** — 파이프 정상 종료 _및_ 중단·에러 시 모두:

```bash
REPORTS_DIR=.agent_reports; [ -d .claude_reports ] && [ ! -d .agent_reports ] && REPORTS_DIR=.claude_reports
rm -f "$REPORTS_DIR/.pipeline-lock"
```

**detect-only** — "지금 spec 수정 중인가?" 단순 조회(메인 Claude 가 spec 손대기 전 확인):

```bash
REPORTS_DIR=.agent_reports; [ -d .claude_reports ] && [ ! -d .agent_reports ] && REPORTS_DIR=.claude_reports
[ -f "$REPORTS_DIR/.pipeline-lock" ] && cat "$REPORTS_DIR/.pipeline-lock" || echo "활성 편집 없음"
```

> 비-worktree(단일 체크아웃) 환경에선 lock 이 항상 same-worktree → 즉시 override, 무해. symlink 공유 worktree 에서만 실질 가드로 작동.

### §5.9. Git working-state preflight (worktree·merge 가드, canonical)

**왜**: §5.8 lock 은 artifact root _산출물_ 동시쓰기만 막는다. 정작 _실제 `.git` 워킹트리_ — merge/rebase 진행 중인지, dirty 한지, detached HEAD 인지, 같은 브랜치가 다른 worktree 에 잡혀 있는지 — 는 안 본다. 여러 worktree·브랜치로 작업하다 merge 가 끼면 이 자리를 놓쳐 (반쯤 머지된 트리 위에 commit / detached HEAD 에 commit 유실 / 다른 worktree 가 머지로 바꿔놓은 파일 위에 작업) 사고. 코드 손대는 skill(autopilot-code 가 canonical 소비자)은 **코드 편집 _전_ 1회 + 각 commit/write-back _직전_ 재확인**(= 주기적 체크) 한다.

```bash
# git-state preflight — 코드 편집 전 + 매 commit 직전. STOP 이면 편집·commit 멈추고 사용자 보고
GD=$(git rev-parse --git-dir 2>/dev/null) || { echo "OK non-git"; return 0 2>/dev/null||exit 0; }
op=; [ -f "$GD/MERGE_HEAD" ] && op=merge
{ [ -d "$GD/rebase-merge" ] || [ -d "$GD/rebase-apply" ]; } && op=rebase
[ -f "$GD/CHERRY_PICK_HEAD" ] && op=cherry-pick
br=$(git symbolic-ref --quiet --short HEAD 2>/dev/null || echo DETACHED)
head=$(git rev-parse --short HEAD 2>/dev/null)
ahead_behind=$(git rev-list --left-right --count @{u}...HEAD 2>/dev/null)  # "behind  ahead"
# 같은 브랜치를 잡고 있는 다른 worktree
elsewhere=$(git worktree list --porcelain 2>/dev/null | awk -v b="$br" '/^worktree /{w=$2} /^branch /{if($2=="refs/heads/"b && w!=ENVIRON["PWD"]) print w}')
# 브랜치 수명 — 현재 브랜치가 base(기본 브랜치)에 이미 다 반영됐나 (= 끝난 브랜치)
def=$(git symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@'); def=${def:-main}
git fetch -q origin "$def" 2>/dev/null
merged_in=$( [ "$br" != DETACHED ] && [ "$br" != "$def" ] && [ "$(git rev-list --count origin/$def..HEAD 2>/dev/null)" = 0 ] && echo yes )
if [ -n "$op" ];        then echo "STOP: $op 진행 중 — 해결(또는 --abort) 뒤 진행"; fi
if [ "$br" = DETACHED ];then echo "STOP: detached HEAD($head) — commit 유실 위험, 브랜치 체크아웃 먼저"; fi
[ -n "$elsewhere" ] && echo "WARN: 브랜치 '$br' 가 다른 worktree($elsewhere)에도 체크아웃됨"
[ "${ahead_behind%%	*}" -gt 0 ] 2>/dev/null && echo "WARN: upstream 이 ${ahead_behind%%	*} 커밋 앞섬(머지/리베이스 발생) — 통합 후 진행 권장"
[ -n "$merged_in" ] && echo "DONE-BRANCH: '$br' 가 origin/$def 에 ahead 0 (머지 완료/끝난 브랜치) — 새 작업은 base 최신에서 새 브랜치로: git switch -c <new-slug> origin/$def"
echo "state: branch=$br head=$head base=$def dirty=$(git status --porcelain 2>/dev/null|wc -l|tr -d ' ')"
```

- **STOP** (merge/rebase/cherry-pick 진행 중 · detached HEAD) → 편집·commit 멈추고 사용자 보고 + 처리 요청. 자동으로 `--abort`·강제 체크아웃 하지 않는다. **harness**: merge/rebase/cherry-pick 중 편집은 `hooks/git-state-guard.sh` 가 PreToolUse(Edit|Write) 에서 hard deny — ceremony 비경유 직접 편집 경로까지 커버 (drill g2 가 잡은 구멍, 2026-06-11). 탈출구 `$GITDIR/CLAUDE_MERGE_EDIT_OK` 는 _사용자가 충돌 해결을 명시 요청한 경우만_ — Claude 자가 판단 생성 금지 (artifact-guard untracked 와 동일 convention).
- **WARN** (다른 worktree 동일 브랜치 · upstream 앞섬 · 진입 시 세션 무관 dirty) → 한 줄 알림 후 진행 판단.
- **DONE-BRANCH (브랜치 수명)** — worktree 에서 판 브랜치가 base 에 머지되면 그 브랜치는 _끝난 것_. ahead 0 인데 그 위에 새 작업을 쌓으면 이미 머지된 죽은 브랜치에 commit 하는 꼴. **새 작업 cycle 진입 시 ahead 0 (+ base 아님 + 이번 작업용 브랜치가 아님) 이면 base 최신에서 새 브랜치를 판다** — `git fetch origin && git switch -c <slug> origin/$def` (worktree 안전 — base 를 체크아웃하지 않아 main worktree 와 충돌 없음). 이미 이번 작업용으로 갓 판 빈 브랜치면 그대로 사용. **직접 편집(비-ceremony)도 동일** — 죽은 브랜치 워킹트리에 미커밋 변경을 띄워두는 것 자체가 부유물 (drill g1, 2026-06-11: 죽은 브랜치 인지하고도 그 자리서 편집).
- **periodic 재확인**: 진입 시 `head` 를 기억 → 각 commit 직전 재실행해 `head` 가 바뀌었거나(아래서 머지·리베이스됨) 새 `MERGE_HEAD` 가 생겼으면 STOP. 비-worktree·비-git 자리에선 전부 `OK`/무해 통과.

### §5.10. 작업 격리·병렬 디스패치 (worktree 정책, canonical)

**왜**: 사용자가 요구사항을 연속으로 던질 때 main 세션이 한 건씩 직렬 처리하면 느리다. 실작업(편집·테스트·QA)은 worktree 로 격리해 background 병렬, 조정(triage·분사·보고)만 main 이 맡는다. 2026-07-06 토큰 절감 재설계: autopilot pipeline 을 main 이 통째로 직접 들고 가면 context 가 과하게 커지고, 반대로 monolithic skill 로 닫으면 cross-harness 관점을 내부에서 활용하기 어렵다. 따라서 depth 모델을 분리한다. **depth 0** = 사용자-facing main/orchestrator, **depth 1** = capability owner worker(예: `autopilot-code` 전체 파이프 책임), **depth 2** = `thorough|adversarial` owner 가 여는 bounded sub-worker(관점·검증·적대 리뷰). **depth 3+ 금지**.

**규모 분기** (요청 진입 시 main 이 판정):

| 규모 | 처리 |
|---|---|
| 자잘한 단발 (typo·1줄·quick 급 소규모) | main 워킹트리에서 바로 (현행) |
| 본작업 (qa standard 이상 · plan 추적 대상) | **worktree + 작업 브랜치** — base 최신에서 plan slug 브랜치 (§5.9 DONE-BRANCH 연계), mutation 커밋 누적 |
| 병렬 요청 (작업 진행 중 새 독립 요청) | 즉시 새 worktree 로 분사 (아래 규칙) — 앞 job 완료를 기다리지 않는다 |

**디스패치 규칙**:
1. **파일 겹침 triage**: 새 요청이 진행 중 job 과 같은 파일을 건드릴 것으로 추정되면 병렬 금지 — 그 job 뒤에 큐잉 (같은 브랜치에 이어서). 안 겹치면 병렬.
2. **실행** — worktree 생성 (`git worktree add <path> -b <slug> origin/<base>`, base 선정은 §5.9) 후 두 모드. **`<path>` 명명 규칙 (canonical, 2026-06-12 사용자 확정)**: 형제 디렉토리 `<repo>-wt/<slug>` 로 판다 (예: repo 가 `…/Foo` 면 worktree 는 `…/Foo-wt/<slug>`). Adapter UI/status surface 가 이 규칙을 신호로 삼을 수 있으므로 `<repo>_worktrees/` 같은 변형 금지, **`-wt/` 단일 표준**.
   - **경량 (팀 위임)**: 팀 에이전트를 `run_in_background` 분사, prompt 에 작업 루트 명시. 검증도 main 이 같은 경로로 QA 팀 spawn. 작은 단위·빠른 회전용.
   - **풀 ceremony (headless 분사)**: worktree 안에서 adapter-specific headless main 을 background 로 실행한다. Headless main 은 _완전한 메인_ 으로 동작해야 하며, 해당 runtime 이 제공하는 팀 분업·hook/preflight·plan 산출물 파이프를 정상 통과해야 한다. 주의: ① runtime별 tool/permission 사전 개방은 adapter가 소유(중간 질문 불가) ② 비용은 adapter realization 별로 명시 ③ **분사 depth 기본은 1** — depth 1 worker 는 capability owner 로서 전체 autopilot pipeline 을 책임지고 main 에는 synthesis 만 반환한다 ④ **depth 2 는 `thorough|adversarial` intensity 에서만** depth 1 owner 가 명시 subdispatch plan 을 세운 뒤 단일 역할 worker 로 열 수 있다; depth 2 worker 는 기본 read-only, 구현 worker 만 제한 write, 결과는 짧은 structured summary; **depth 3+ 금지** ⑤ **동시 분사 기본 상한 5대** (사용량 보호 — 초과는 사용자 명시 시만; 3→5 2026-06-22 사용자) ⑥ **분사 프롬프트의 capability 호출은 옵션 풀 명시** — capability, mode, qa, intensity, depth, parent 값을 명령행/프롬프트에 드러내 adapter UI·job registry 가 식별 가능하게 한다 ⑦ **dispatch model/effort 선택은 parent orchestrator 책임** — depth 0 main 또는 depth 1 owner 는 작업 난이도와 intensity/QA 수준을 보고 job 별 portable model role 또는 concrete runtime model/effort 를 명시한다. Adapter wrapper 는 선택된 값을 실행 옵션으로 반영하거나, 명시적 inherit 선택만 허용한다. Wrapper 가 임의 기본 모델을 고르거나 현재 interactive session model 을 암묵 상속하면 안 된다.
   - **job 레지스트리 (분사 시 의무)**: 분사 직전 `<agent-home>/.dispatch/jobs.log` 에 한 줄 append — `<ISO시각>\topen\t<repo>\t<worktree경로>\t<slug>\t<파이프>`. 6필드 형식은 하위호환을 위해 유지하고, `<파이프>` 안에 `capability=...`, `mode=...`, `qa=...`, `intensity=...`, `depth=1|2`, `parent=<parent-slug>`, `worker_role=...`, `owner=...`, `profile=...` 같은 key=value metadata 를 넣는다. 수확·정리 시 해당 줄의 `open` 을 `done` 으로. 세션이 죽어도 등록부가 남아 당직 7호가 고아 job (open 인데 24h+ 경과 또는 worktree 소멸·유휴) 을 감시한다.
   - **관제 안내 (분사 직후 한 줄, 2026-07-02)**: background 분사를 시작하면 사용자에게 `fleet`(크로스-하네스 관제 대시보드, `tools/fleet` — README §관제) 한 줄 안내 — 진행·stage·liveness 를 사용자가 라이브로 보는 표준 창구. jobs.log 등록·argv 옵션 명시(위 ⑤)가 fleet 의 식별 소스이므로 이 레지스트리 규율이 곧 관제 품질이다. 이미 fleet 을 띄워 둔 사용자에겐 반복 안내 불필요.
   - **stealth-death 가드 (분사 후 대기 자리 — 필수, §0.5 결정론)**: ⚠️ hung/crash 한 adapter-specific headless main 은 _exit 를 안 해 완료 알림이 영영 안 올 수 있다_ → 완료 알림만 믿고 무한 대기하면 silent 하게 시간을 날린다 (2026-06-16 5h 사고). **분사한 background 작업을 기다리는 자리에선 완료 알림에만 의존하지 말고 liveness 를 능동 점검한다**. 먼저 해당 adapter 의 headless contract 가 보고하는 liveness 명령을 쓴다: Codex 는 `adapters/codex/bin/preflight.sh liveness [jobs.log]`, OpenCode 는 `adapters/opencode/bin/preflight.sh liveness [jobs.log]`, Claude/shared projection 은 `bash <agent-home>/utilities/dispatch-liveness.sh`. 세 명령 모두 jobs.log 의 open job 별 session transcript/DB mtime 판정 — `ALIVE`(N분 내 갱신) / `SUSPECT`(N분+ 정지 = hang/death 의심) / `DEAD`(transcript 부재), exit 3 = 의심 1+ — 을 제공해야 한다. SUSPECT/DEAD 면 알림 기다리지 말고 transcript tail·dispatch 로그로 진단 → 수확 또는 재분사. 신호 = transcript/DB mtime (pgrep 경로매칭은 흔한 path 가 무관 프로세스에 걸려 false-alive). Workflow 등 harness-native 분사는 알림이 신뢰되지만, adapter-specific headless main 에는 본 가드 적용. "vigilant 하게 기억" 이 아니라 _adapter liveness wrapper 로_ 점검 (§0.5).
3. **merge = main/orchestrator 선별 책임** (2026-06-11 사용자 위임 — 수동 메모 (DB profile record `07_coding_convention`)가 source): 사용자 직접 리뷰 없이 main 이 선별 머지한다. **머지 시점 게이트** — (a) 사용자 머지 신호("합쳐"/"머지해") 또는 (b) 병렬 디스패치로 분사한 background job 수확 자리에서만. **자기 turn 의 본작업 브랜치를 같은 turn 에 self-merge 금지** — 브랜치 + 한 줄 보고로 turn 을 끝내고 main ref 는 불변 (§3 후속 단계 자동 진행에 merge-to-main 은 포함되지 않음). 머지 후에도 작업 브랜치는 같은 turn 에 삭제하지 않는다 (롤백 지점). **worktree 디렉토리는 별개** — 수확(머지+통합 빌드 검증) 완료된 worktree 는 다음 자연 휴지(다음 수확 자리·세션 마무리)에 디렉토리만 제거한다 (브랜치 ref 유지, `git worktree remove` 전 자체 dev 서버 등 고아 프로세스 종료 확인 — NFS lock 잔존 방지. 2026-06-12 worktree 9개 적체에서 사용자 지적). 절차 — `git diff main...<branch>` 로 _실내용_ 확인 → 이미 main 에 진전됐거나 회귀·중복이면 머지 안 함 → 충돌은 양쪽 의도를 해석해 해결 (한쪽 자동 채택·`--force` 금지) → _애매하거나 확정본을 되돌리는 자리면 멈추고 질문_ → 빌드 검증 후 커밋. "전부 합쳐" = 전량 머지가 아니라 선별 머지.
4. **공유 산출물**: artifact root 공유 단일파일 쓰기는 §5.8 lock 경유. `plans/<slug>/` 는 경로 분리라 비경합.
5. **컨텍스트**: job 조정 기록 누적으로 main 컨텍스트 압박 시 post-it handoff 제안 (글로벌 §2).

### §5.11. 지침 repo (`<agent-home>`) 커밋·push 정책

지침·규칙·hook/preflight·runtime status surfaces 등 `<agent-home>` 파일 수정은 **검증 직후 같은 turn 에 commit + push** — 사용자 별도 신호 불필요 (2026-06-12 사용자 ratify "규칙은 바로 그냥 push 하면 되겠네"). 작업 repo 의 push 는 별개 — deploy 게이트(사용자 신호) 유지.

---
