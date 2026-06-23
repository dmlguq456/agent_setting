# Operations — Git·Worktree·Dispatch·Push 운영 (canonical)

> CONVENTIONS.md 에서 분리(2026-06-23, 앞/뒤 2층 재편). git 운영(lock·preflight·worktree dispatch·`~/.claude` push)은 산출물 컨벤션과 결이 달라 별도 파일로. **§ 번호·heading 보존** — SKILL.md·drill·hook 이 `OPERATIONS.md#59-…` 등 anchor 로 인용. git 운영 단일 출처.

## §5.8. Pipeline Lock — 공유 `.claude_reports` 다중 worktree 가드 (canonical)

**왜**: 여러 git worktree 가 _하나의 canonical `.claude_reports` 를 symlink 공유_ 할 때(릴리즈 브랜치 클린 유지 위해 산출물은 gitignore), 두 worktree 가 동시에 `spec/` 공유 단일파일(`prd.md`·`pipeline_state.yaml`·`pipeline_summary.md`)을 쓰면 lost-update. `plans/<cycle>/` 는 사이클별 폴더라 경로 분리 → 비경합(lock 불필요).

- **lock 파일**: `.claude_reports/.pipeline-lock` (공유 트리에 위치 → 모든 worktree 가시). transient — `.claude_reports/` 자체가 gitignore 라 추적 안 됨.
- **보호 범위**: `spec/prd.md`·`spec/pipeline_state.yaml`·`spec/pipeline_summary.md` _쓰기_ 구간만. 읽기·plans 쓰기는 비-lock.
- **stale 무시(override)**: 기록 `at` 이 30 분 초과 OR 기록 worktree == 현재 worktree(재진입/잔존 락) → 통과.

**acquire** — 쓰기 진입 _직전_ (autopilot-spec 의 Step 3 / update mode, autopilot-code 의 pipeline_state·summary 쓰기 / spec-drift update):

```bash
LOCK=.claude_reports/.pipeline-lock; NOW=$(date +%s); WT=$(pwd -P)
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
rm -f .claude_reports/.pipeline-lock
```

**detect-only** — "지금 spec 수정 중인가?" 단순 조회(메인 Claude 가 spec 손대기 전 확인):

```bash
[ -f .claude_reports/.pipeline-lock ] && cat .claude_reports/.pipeline-lock || echo "활성 편집 없음"
```

> 비-worktree(단일 체크아웃) 환경에선 lock 이 항상 same-worktree → 즉시 override, 무해. symlink 공유 worktree 에서만 실질 가드로 작동.

### §5.9. Git working-state preflight (worktree·merge 가드, canonical)

**왜**: §5.8 lock 은 `.claude_reports` _산출물_ 동시쓰기만 막는다. 정작 _실제 `.git` 워킹트리_ — merge/rebase 진행 중인지, dirty 한지, detached HEAD 인지, 같은 브랜치가 다른 worktree 에 잡혀 있는지 — 는 안 본다. 여러 worktree·브랜치로 작업하다 merge 가 끼면 이 자리를 놓쳐 (반쯤 머지된 트리 위에 commit / detached HEAD 에 commit 유실 / 다른 worktree 가 머지로 바꿔놓은 파일 위에 작업) 사고. 코드 손대는 skill(autopilot-code 가 canonical 소비자)은 **코드 편집 _전_ 1회 + 각 commit/write-back _직전_ 재확인**(= 주기적 체크) 한다.

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

**왜**: 사용자가 요구사항을 연속으로 던질 때 main 세션이 한 건씩 직렬 처리하면 느리다. 실작업(편집·테스트·QA)은 worktree 로 격리해 background 병렬, 조정(triage·분사·보고)만 main 이 맡는다. **확정 제약 (스모크 테스트 2026-06-11)**: 서브에이전트에는 Agent 툴이 노출되지 않는다 — **중첩 1단 한계**. 따라서 오케스트레이션은 항상 main 전담이고, 팀 에이전트는 prompt 에 명시된 worktree 경로에서만 일한다 (Skill·Bash·Edit 는 서브에이전트에서 정상).

**규모 분기** (요청 진입 시 main 이 판정):

| 규모 | 처리 |
|---|---|
| 자잘한 단발 (typo·1줄·quick 급 소규모) | main 워킹트리에서 바로 (현행) |
| 본작업 (qa standard 이상 · plan 추적 대상) | **worktree + 작업 브랜치** — base 최신에서 plan slug 브랜치 (§5.9 DONE-BRANCH 연계), mutation 커밋 누적 |
| 병렬 요청 (작업 진행 중 새 독립 요청) | 즉시 새 worktree 로 분사 (아래 규칙) — 앞 job 완료를 기다리지 않는다 |

**디스패치 규칙**:
1. **파일 겹침 triage**: 새 요청이 진행 중 job 과 같은 파일을 건드릴 것으로 추정되면 병렬 금지 — 그 job 뒤에 큐잉 (같은 브랜치에 이어서). 안 겹치면 병렬.
2. **실행** — worktree 생성 (`git worktree add <path> -b <slug> origin/<base>`, base 선정은 §5.9) 후 두 모드. **`<path>` 명명 규칙 (canonical, 2026-06-12 사용자 확정)**: 형제 디렉토리 `<repo>-wt/<slug>` 로 판다 (예: repo 가 `…/Foo` 면 worktree 는 `…/Foo-wt/<slug>`). statusline 의 `related()` job 필터가 이 `<repo>-wt/` 형식을 형제 worktree 로 인식해 `>_ running` 에 표시한다 — `_worktrees/` 등 다른 접미사는 인식 못 해 분사 job 이 statusline 에서 누락된다. 따라서 `<repo>_worktrees/` 같은 변형 금지, **`-wt/` 단일 표준**.
   - **경량 (팀 위임)**: 팀 에이전트를 `run_in_background` 분사, prompt 에 작업 루트 명시. 검증도 main 이 같은 경로로 QA 팀 spawn. 작은 단위·빠른 회전용.
   - **풀 ceremony (headless 분사)**: worktree 안에서 `claude -p "/autopilot-code --qa quick ..."` background — headless 는 _완전한 메인_ 이라 Agent 툴 보유 → 팀 분업·hook·plan 산출물까지 파이프 전부 정상 (Agent 툴의 중첩 1단 제한은 _툴 계층_ 한정, 프로세스 분사는 무관 — 2026-06-11 실증). 주의: ① `--allowedTools` 사전 개방 (중간 질문 불가) ② 비용 = 세팅 세금 ~40k/대 (drill g0 실측) ③ **분사는 main 전용, 깊이 1** — headless 가 또 headless 분사 금지 (폭주 방지) ④ **동시 분사 기본 상한 5대** (사용량 보호 — 초과는 사용자 명시 시만; 3→5 2026-06-22 사용자) ⑤ **분사 프롬프트의 skill 호출은 옵션 풀 명시** — `/autopilot-code --mode dev --qa quick` 식으로 `--mode`·`--qa` 를 명령행에 적는다. statusline 의 `>_ running` 표시가 ps 명령행 파싱이라 명시된 옵션만 보인다 (2026-06-11 — mode 미표시 자리에서 발견) ⑥ **headless 메인 model 은 `--model opus` 고정** — 미지정 시 메인 세션의 모델(fable 등 상위 tier)을 상속해 사용량을 태운다. 분사 메인은 orchestration 중심이라 opus 로 충분, 팀 agent 는 각자 frontmatter model 을 따른다 (2026-06-12 — fable 상속 실측 후 사용자 지시).
   - **job 레지스트리 (분사 시 의무)**: 분사 직전 `~/.claude/.dispatch/jobs.log` 에 한 줄 append — `<ISO시각>\topen\t<repo>\t<worktree경로>\t<slug>\t<파이프>`. 수확·정리 시 해당 줄의 `open` 을 `done` 으로. 세션이 죽어도 등록부가 남아 당직 7호가 고아 job (open 인데 24h+ 경과 또는 worktree 소멸·유휴) 을 감시한다.
   - **stealth-death 가드 (분사 후 대기 자리 — 필수, §0.5 결정론)**: ⚠️ hung/crash 한 headless `claude -p` 는 _exit 를 안 해 완료 알림이 영영 안 온다_ → 완료 알림만 믿고 무한 대기하면 silent 하게 시간을 날린다 (2026-06-16 5h 사고). **분사한 background 작업을 기다리는 자리에선 완료 알림에만 의존하지 말고 liveness 를 능동 점검한다**: `bash ~/.claude/utilities/dispatch-liveness.sh` (jobs.log 의 open job 별 세션 transcript mtime 판정 — `ALIVE`(N분 내 갱신) / `SUSPECT`(N분+ 정지 = hang/death 의심) / `DEAD`(transcript 부재), exit 3 = 의심 1+). SUSPECT/DEAD 면 알림 기다리지 말고 transcript tail·dispatch 로그로 진단 → 수확 또는 재분사. 신호 = transcript mtime (pgrep 경로매칭은 흔한 path 가 무관 프로세스에 걸려 false-alive). Workflow 등 harness-native 분사는 알림이 신뢰되지만, `claude -p` 헤드리스는 본 가드 적용. "vigilant 하게 기억" 이 아니라 _스크립트로_ 점검 (§0.5).
3. **merge = Claude 선별 책임** (2026-06-11 사용자 위임 — 수동 메모 (DB profile record `07_coding_convention`)가 source): 사용자 직접 리뷰 없이 main 이 선별 머지한다. **머지 시점 게이트** — (a) 사용자 머지 신호("합쳐"/"머지해") 또는 (b) 병렬 디스패치로 분사한 background job 수확 자리에서만. **자기 turn 의 본작업 브랜치를 같은 turn 에 self-merge 금지** — 브랜치 + 한 줄 보고로 turn 을 끝내고 main ref 는 불변 (§3 후속 단계 자동 진행에 merge-to-main 은 포함되지 않음). 머지 후에도 작업 브랜치는 같은 turn 에 삭제하지 않는다 (롤백 지점). **worktree 디렉토리는 별개** — 수확(머지+통합 빌드 검증) 완료된 worktree 는 다음 자연 휴지(다음 수확 자리·세션 마무리)에 디렉토리만 제거한다 (브랜치 ref 유지, `git worktree remove` 전 자체 dev 서버 등 고아 프로세스 종료 확인 — NFS lock 잔존 방지. 2026-06-12 worktree 9개 적체에서 사용자 지적). 절차 — `git diff main...<branch>` 로 _실내용_ 확인 → 이미 main 에 진전됐거나 회귀·중복이면 머지 안 함 → 충돌은 양쪽 의도를 해석해 해결 (한쪽 자동 채택·`--force` 금지) → _애매하거나 확정본을 되돌리는 자리면 멈추고 질문_ → 빌드 검증 후 커밋. "전부 합쳐" = 전량 머지가 아니라 선별 머지.
4. **공유 산출물**: `.claude_reports` 공유 단일파일 쓰기는 §5.8 lock 경유. `plans/<slug>/` 는 경로 분리라 비경합.
5. **컨텍스트**: job 조정 기록 누적으로 main 컨텍스트 압박 시 post-it handoff 제안 (글로벌 §2).

### §5.11. 지침 repo (`~/.claude`) 커밋·push 정책

지침·규칙·hook·statusline 등 `~/.claude` 파일 수정은 **검증 직후 같은 turn 에 commit + push** — 사용자 별도 신호 불필요 (2026-06-12 사용자 ratify "규칙은 바로 그냥 push 하면 되겠네"). 작업 repo 의 push 는 별개 — deploy 게이트(사용자 신호) 유지.

---

