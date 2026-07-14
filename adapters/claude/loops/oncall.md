# 야간 정찰 (read-only 점검 + 보고만)

당직 자체는 read-only 점검·보고 — 어떤 수정·커밋·푸시도 하지 않는다 (허용된 쓰기는 보고 파일 1개뿐). 발견의 *처리*는 아침 논의 데스크(D-26)가 받는다 — 되돌림가능+명백한 건 무인 처리+전수보고, 그외는 사용자 논의 (D-25, loops/README 공통 규약).

## 점검 항목

1. **git 상태**: `/home/nas/user/Uihyeop` 에서 depth 3 이내 `.git` 보유 repo 탐색 (백업·`node_modules`·`_layer2*` 제외). 각 repo 에서:
   - merge / rebase / cherry-pick 진행 중인지
   - dirty 파일 수
   - DONE-BRANCH: 현재 브랜치가 origin 기본 브랜치에 ahead 0 인데 기본 브랜치가 아님 (= 머지 완료된 끝난 브랜치에 머묾)
   - prunable worktree (`git worktree list --porcelain`)
2. **산출물 누적 minor**: 각 artifact root (`.agent_reports`, legacy `.claude_reports`) 의 `*/pipeline_summary.md` 에서 마지막 audit 이후 minor 기록 5건 이상 → `/audit` 권장 표시.
3. **실험 방치**: `experiments/_RUNLOG.md` 의 ⏳ 상태 entry 중 7일 이상 갱신 없음 → 목록.
4. **drill 회귀 미실행**: `<agent-home>` 의 최신 커밋 시각이 `<agent-home>/loops/drill/results/` 의 최신 run 디렉토리 시각보다 새로움 → "지침 변경 후 drill 미실행 — `run.sh --sample 2` 권장 (정기 회귀는 랜덤 2개로 가볍게; 가드·라우팅 등 _행동 규칙_ 을 대폭 바꾼 자리만 관련 케이스·전수)" 표시. (drill 을 직접 실행하지는 않는다 — 보고만.) **매번 전수는 과부하** — 지침 _텍스트_ (근거 문구·제목)만 바뀐 자리는 권장하되 행동 무관이면 skip 판단.
5. **정의·projection drift**: `<agent-home>`에서 `python3 tools/generate.py --check`, `tools/check-adaptation-boundary.sh`, `tools/skill-conformance/check.sh` 중 실패가 있으면 check 이름과 첫 actionable error를 표시. README prose는 자동 신선도 판정 대상이 아니라 human review 대상이다.
6. **note 루프 생존·성공**: `<agent-home>/loops/note.log` 의 마지막 `=== note run` 시각이 26시간 이상 과거 → "note 루프 고장 의심 (cron·인증·timeout)". **+ 마지막 run 의 종료 상태도 점검** — 그 run 블록의 `=== exit N ===` 가 N≠0 이거나 블록에 실패 마커(`401`·`invalid authentication`·`SyntaxError`·`=== FAILED after`·`=== ABORT:`)가 있으면 → "note 루프 마지막 실행 실패 (사유)" 를 **조치 필요** 로 보고. (시각이 최근이어도 실패했을 수 있으니 시각·성공 둘 다 본다.)
7. **연수 루프 생존·성공**: `<agent-home>/loops/study.log` 의 마지막 `=== study run` 시각이 8일 이상 과거 → "연수 루프 고장 의심" (주 1회 일요일 주기). **+ 마지막 run 의 종료 상태도 점검** — `=== exit N ===` 가 N≠0 이거나 실패 마커(`401`·`invalid authentication`·`SyntaxError`·`=== FAILED after`·`=== ABORT:`)가 있으면 → "연수 루프 마지막 실행 실패 (사유)" 를 **조치 필요** 로 보고. (2026-06-21 연수가 401 로 즉사했는데 시각만 보던 옛 점검이 못 잡은 사고 — 그 재발 방지.)
8. **디스패치 job 현황** (`<agent-home>/.dispatch/jobs.log` — OPERATIONS §5.10 등록부): `open` 항목 전부 보고에 나열 (현황 가시화). 그중 — (a) worktree 경로가 소멸했거나 24시간+ 경과 → **고아 의심**, (b) worktree 는 있는데 최근 24시간 커밋·artifact root 의 `plans/*/dev_logs` 변경 둘 다 없음 → **무진전 의심**. 둘 다 보고만 — 프로세스 kill·worktree 정리는 사용자 결정.
9. **메모리 승격 후보 (self-review nudge)** — Hermes periodic self-review 벤치마킹 이식(T4). 전날(`git log --since="36 hours ago"` 기준) `<agent-home>` 및 작업 repo 의 커밋 메시지·산출물 변경에서, _재사용 절차·사용자 선호·교정(correction)·컨벤션·교훈_ 으로 보이는데 아직 기록 안 된 것 → "메모리 승격 후보" 로 **가장 명확한 1~2개만** 목록. 판단 기준 = 메모리 승격 휴리스틱([MEMORY §7](../MEMORY.md) canonical): preferences·conventions·corrections·lessons = 승격 / trivial·재발견가능·git 이력에 이미 있는 것·ephemera = skip. 저장 자리: `mem add`/`mem note`(직접 store write) + 하네스 auto-memory(`runtime-home/projects/<cwd>/memory/` → SessionEnd `mem sync` 로 store **durable** mirror) + post-it(→ store **working** mirror). **저장하지 않는다 — 후보 제시만**(저장은 사용자 흐름 안 `/post-it` 또는 `mem add`). 노이즈 방지: 확실한 것 없으면 이 항목 통째로 생략(빈칸 > 잘못 채우기). 행동양식 변경 후보는 메모리 아니라 원칙 문서 자리이므로 제외. _※ 세션 중 자동 store write 는 미구현 — runtime 내장 memory→sync mirror + 수동 mem add/note 가 현 구현 경로._
10. **(폐기 — `mem lifecycle` 일임)** post-it 파일 regex 스캔은 제거됨 (제거된 `post-it.md` 파일 모델 잔재). store working tier staleness 는 SessionEnd `mem sync` → `mem lifecycle --apply` 가 `WORKING_TTL_DAYS`(현재 21d) 기준으로 자동 만료 처리하므로 야간 정찰 점검 대상 아님. (durable consolidate 후보 플래깅은 `mem lifecycle` report 모드가 담당 — oncall 재구현 X.)
11. **메모리 store 전수 진단 (D-39)**: `python3 <agent-home>/tools/memory/mem.py doctor` 실행 — read-only 9항목(integrity·FTS 정합·schema 불변식·working 비대·stale pending·durable soft-ceiling·graveyard 정합·dump 신선도·워커 건강) 결정론 체크. exit 0(clean) 은 무보고, exit 1(WARN)/2(FAIL) 이면 `[WARN]`/`[FAIL]` 항목을 그대로 보고에 옮긴다 — **조치는 하지 않는다**: 삭제·consolidate·merge·graduate 권한은 세션끝 opus 큐레이터(D-18) 소유 불변이라, doctor 발견은 아침 논의 안건·큐레이터 입력으로만 흐른다 (D-25 read-only 진단+보고 계약). (`tools/memory/index-check.sh`(legacy 파일 인덱스)와 별개 — doctor 는 store(DB) 대상.)
12. **runtime-watch 신선도 (2026-07-13 Codex rate-window currentness 사고)**: `<agent-home>/loops/runtime-watch.sh` syntax와 `/home/nas/user/Uihyeop/notes/runtime-watch/` 최신 보고 시각을 확인한다. 보고가 7일 이상 없거나 최근 runtime 정책 변경이 의심되면 `runtime-watch --run` 권장으로 보고한다. oncall 자체는 네트워크 probe·drill·headless·정책 edit 을 실행하지 않으며, 공식 primary source 해석과 정책 반영은 별도 autopilot-spec/code 사이클로 넘긴다.

## drill 승격 후보 태깅 (2026-06-11, P7 반자동화)

발견 중 _Claude 행동 규칙 위반의 재현 가능한 상황_ (merge 중 커밋 흔적·죽은 브랜치 위 작업 흔적·전제 없는 산출물 등)에는 항목 끝에 `[drill 승격 후보]` 태그. 보고 마지막에 후보만 모은 절을 둔다 — 사용자 "승격해줘" 발화 시 그 상황을 fixture 로 재현해 `loops/drill/cases_growing/` 에 케이스 골격(fixture.sh·prompt.md·assert.sh)을 생성하는 게 후속 절차.

## 보고

- `/home/nas/user/Uihyeop/notes/oncall/<오늘 날짜 YYYY-MM-DD>.md` 에 간결한 한국어 보고 작성 — 항목당 1~2줄, repo 경로·브랜치 명시, 권장 조치 한 줄.
- **발견 0 이어도 파일은 반드시 남긴다** — `# 야간 정찰 — <날짜>\n이상 없음 (점검 12항목 전부 통과)` 한 줄. 파일 자체가 heartbeat — 아침에 파일이 없으면 "이상 없음"이 아니라 **루프 고장**(cron·인증·timeout)을 뜻한다.
- 보고는 사실만 — 추정 수치·과장 금지 (빈칸 > 잘못 채우기).
