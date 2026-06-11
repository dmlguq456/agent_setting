# 야간 정찰 (read-only 점검 + 보고만)

어떤 수정·커밋·푸시·정리도 하지 않는다. 허용된 쓰기는 보고 파일 1개뿐.

## 점검 항목

1. **git 상태**: `/home/nas/user/Uihyeop` 에서 depth 3 이내 `.git` 보유 repo 탐색 (백업·`node_modules`·`_layer2*` 제외). 각 repo 에서:
   - merge / rebase / cherry-pick 진행 중인지
   - dirty 파일 수
   - DONE-BRANCH: 현재 브랜치가 origin 기본 브랜치에 ahead 0 인데 기본 브랜치가 아님 (= 머지 완료된 끝난 브랜치에 머묾)
   - prunable worktree (`git worktree list --porcelain`)
2. **산출물 누적 minor**: 각 `.claude_reports/*/pipeline_summary.md` 에서 마지막 audit 이후 minor 기록 5건 이상 → `/audit` 권장 표시.
3. **실험 방치**: `experiments/_RUNLOG.md` 의 ⏳ 상태 entry 중 7일 이상 갱신 없음 → 목록.
4. **golden 회귀 미실행**: `~/.claude` 의 최신 커밋 시각이 `~/.claude/loops/golden/results/` 의 최신 run 디렉토리 시각보다 새로움 → "지침 변경 후 golden 미실행 — `~/.claude/loops/golden/run.sh` 권장" 표시. (golden 을 직접 실행하지는 않는다 — 보고만.)
5. **sync-skills drift**: `~/.claude/skills/*/SKILL.md`·`~/.claude/agents/*.md` 중 `~/.claude/skills/.sync_state.json` 보다 새로운 파일 존재 → "skill 정의 변경 후 README 미동기화 — `/sync-skills` 권장" 표시.
6. **note 루프 생존**: `~/.claude/loops/note.log` 의 마지막 `=== note run` 시각이 26시간 이상 과거 → "note 루프 고장 의심 (cron·인증·timeout)" 표시.
7. **연수 루프 생존**: `~/.claude/loops/study.log` 의 마지막 `=== study run` 시각이 8일 이상 과거 → "연수 루프 고장 의심" 표시 (주 1회 일요일 주기).
8. **디스패치 job 현황** (`~/.claude/.dispatch/jobs.log` — CONVENTIONS §5.10 등록부): `open` 항목 전부 보고에 나열 (현황 가시화). 그중 — (a) worktree 경로가 소멸했거나 24시간+ 경과 → **고아 의심**, (b) worktree 는 있는데 최근 24시간 커밋·`.claude_reports/plans/*/dev_logs` 변경 둘 다 없음 → **무진전 의심**. 둘 다 보고만 — 프로세스 kill·worktree 정리는 사용자 결정.

## 보고

- `/home/nas/user/Uihyeop/notes/duty/<오늘 날짜 YYYY-MM-DD>.md` 에 간결한 한국어 보고 작성 — 항목당 1~2줄, repo 경로·브랜치 명시, 권장 조치 한 줄.
- **발견 0 이어도 파일은 반드시 남긴다** — `# 야간 정찰 — <날짜>\n이상 없음 (점검 4항목 전부 통과)` 한 줄. 파일 자체가 heartbeat — 아침에 파일이 없으면 "이상 없음"이 아니라 **루프 고장**(cron·인증·timeout)을 뜻한다.
- 보고는 사실만 — 추정 수치·과장 금지 (빈칸 > 잘못 채우기).
