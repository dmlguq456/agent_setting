# agent-fleet-dashboard — Spec (PRD)

> mode: **cli** (터미널 TUI 도구) · 작성 2026-07-01 · **v2 2026-07-10** (drift 흡수 + stage-dispatch 관제 parity + UI 가독성 개선) · **v3 2026-07-12** (minor 5건[F-14~F-19] 흡수 승격 — §4.7 분리 신설 + audit 🟡 3건 반영: §3 `--demo` 등재·§9 모듈 트리 현행화. 근거 = `_internal/audit/audit_2026-07-12T0910.md`) · **v4 2026-07-13** (F-20 dynamic Codex rate-window contract) · **v5 2026-07-13** (F-21 Codex native title + cross-harness fleet title provider. Claude-only refresher 계약 폐기) · **v6 2026-07-14** (F-22 responsive titles + F-23 recursive-storm containment) · **v7 2026-07-15** (F-24 portable worker attribution + unique Codex rollout ownership) · **v8 2026-07-15** (F-25~F-28 — 상태 판정 단일 모델·interactive 세션 레지스트리 1급·제한적 세션 제어[Non-goal 반전]·분사 정책 연동 계약. 근거 = 사용자 결정 4건: "fleet 직접 세션 제어"·"반쪽짜리 해소, 전향적 확장"·"버그가 아니라 판정 기준 자체가 불안정"·"분사 정책과 연동되는 가장 중요한 UI") · **v9 2026-07-15** (minor 6건 흡수 + audit 🟡 2건 해소[어휘 매핑 표·§10 다이어그램] + F-27 마우스 1급 재설계 + F-30 종착 비전 등재 "dispatch·서브에이전트 처리 과정 시각화". 근거 = `_internal/audit/audit_2026-07-15T1734.md` + 사용자 방향 2건) · **v10 2026-07-15** (F-28 구현 확정 + F-30 처리-과정 뷰 설계 확정 — 전제였던 stage-dispatch topology registry·route record·broker가 v11 구현으로 main 착륙[`f5f3949f`], 실측 record 스키마 기반) · **v11 2026-07-17** (두-평면 실험 폐기 후 채택분 등재 — F-29 스트립·비동기 판정 개정 + F-19 레포별 카드 행 + F-17 분사 세션 요약 전면 적용 + §4.10 F-32~F-34[분사 제목 입양·harness(model·effort) 통합·표시 문법 정리]. 근거 = 사용자 결정 연쇄 2026-07-16 "전부 다 버리고, 메모리 쪽과 서브 에이전트 쪽만 기존의 fleet에" 외 다수. 구현 선행·등재 후행 — 사용자 명시 이연의 사후 소급, 코드 실측 기준)
> · **v12 reliability minor 2026-07-20** (exact dispatch terminal evidence·namespace heartbeat expiry·Codex task lifecycle 우선·unmatched depth-2 canonical parity) · **v13 2026-07-21** (live TUI stable session/group order — refresh liveness·mtime 변화가 살아남은 행의 위치를 바꾸지 않음) · **v14 2026-07-22** (portable unit catalog·compositional route metadata·legacy worker_role 경계·runtime surface 구분) · **v15 2026-07-22** (F-19/F-35f — sync/migrate 신규 흡수의 `add`/literal `sync`·원천 논리 cwd·무변이 반복 0건·historical backfill 금지) · **v16 2026-07-22** (F-36~F-39 — interactive/dispatch 공통 work projection·composed DAG·ctx+NOW subordinate line·title worker 상향)
> 컴포넌트: `agent_setting` repo 의 **별도 내부 도구** — 기존 `spec/prd.md`(Unified Memory System)와 무관, 이 폴더(`spec/agent-fleet-dashboard/`)가 자체 청사진.
> 입력(1순위 근거): `research/agent-fleet-dashboard/00_prior_art.md`(build-vs-adopt·herdr·렌더스택) · `research/agent-fleet-dashboard/01_tap_mechanics.md`(하네스별 tap·discovery·liveness, file-cited)
> **v2 추가 입력**: `spec/stage-dispatch/prd.md`(SD-1~9 — 스테이지 단위 depth-2 headless 분사 계약, §9-13 fleet 표시 = Phase 2 잔여) · 현행 `tools/fleet/` 코드 전수 실측(2026-07-10 Explore, file:line-cited) · 사용자 관찰("워크플로우를 못 따라감 + UI 아쉬운 점 다수").
> 본 문서는 청사진(PRD). 구현은 autopilot-code (산출물 `plans/`). skeleton 은 lean 유지 위해 autopilot-code 로 이월(§9 module 구조만 확정).
> v1 원본 = `_internal/versions/v1/prd.md`. v1 이후 07-01~07-10 사이 커밋된 렌더 진화(§4 [v2 기준선] 참조)는 본 v2 가 소급 흡수 — 이 구간의 산출물 트레일은 `plans/2026-07-01_agent-fleet-dashboard/`·`plans/2026-07-01_fleet-render-v2/`·`plans/2026-07-03_fleet-cooling-groups/` + 직접 커밋(git log `tools/fleet`).

## 0. 한 줄

여러 하네스(Claude Code·Codex·opencode)의 **활성 세션 전부** + **프로젝트별 headless dispatch 잡**을, 어떤 하네스 TUI 에도 주입하지 않고 **외부에서 관찰**해 htop/nvtop 스타일 라이브 터미널 대시보드로 모아 보여준다. zero-dep python curses, tmux 세로 사이드 페인 배치.

## 0.5 설계 원칙 — 외부 관찰자 (zero-injection) ★ cross-cutting

**대시보드는 어떤 하네스의 TUI·transcript·프로세스에도 아무것도 주입하지 않는다.** 이미 디스크에 존재하는 신호(프로세스 테이블·transcript·statusline JSON·SQLite row·jobs.log)를 읽어 렌더한다. write 예외는 fleet이 _소유한_ local state뿐이다: Claude per-session statusline tap(§5)과 제목 sidecar(`$FLEET_TITLE_STATE_DIR` 또는 XDG state). 하네스 원본 transcript·DB에는 쓰지 않는다.

> **[v8 경계 개정] 관찰 + 사용자 개시 제어**: F-27이 "무제어" 절대 원칙을 "**자동 제어 0, 명시적 사용자 개시 제어만**"으로 좁힌다. fleet은 스스로 어떤 프로세스도 죽이거나 정리하지 않으며, 사용자의 명시적 키 입력 + 확인 게이트를 통과한 kill/정리 시그널만 보낸다. zero-injection(하네스 TUI·transcript·DB 무주입)은 그대로 불변 — 프로세스 시그널은 주입이 아니라 OS 표준 제어이고, 모든 제어 행위는 fleet 소유 action log에 남는다.

> **[v2 확장] "관찰" 의 범위**: 디스크·프로세스 외에 **하네스 계정 usage API 의 read-only 호출**(claude OAuth `/api/oauth/usage`, codex `wham/usage` — usage 헤더의 rate-limit 소스, `usage_api.py`·`codex.py` 실측)을 관찰로 인정한다. 쓰기·주입이 아니고 하네스 세션에 영향 0 — F-1 불변. opencode 는 usage API 부재 → 헤더에 "no usage api" 명시(결손 침묵 금지, F-3 동형).

- **왜**: codex·opencode 의 TUI/hook 은 우리가 못 건드림(그리고 건드리면 안 됨). 관찰자로만 두면 하네스 버전 업그레이드·재시작과 무관하게 동작하고, 대시보드 크래시가 세션에 영향 0.
- **적용**: 새 데이터가 필요하면 "이 하네스가 이미 어디에 남기나?"를 먼저 묻는다(§2 tap 매트릭스). 없으면 프로세스 스캔(universal 백본)으로 fallback. 새 emit 경로를 하네스에 심지 않는다.

## 1. 아키텍처 — 3계층, 2섹션

```
[발견 계층·universal 백본]  프로세스 스캔: comm ∈ {claude,codex,opencode} + /proc/<pid>/cwd + ps etime
        ↓  (모든 하네스의 모든 활성 세션을 무조건 열거 — 유일하게 100% 보장되는 tap)
[보강 계층·하네스별 passive enrichment]  세션당 상세를 디스크에서 read-only 로 부착
        · claude   → ~/.claude/.statusline/<session_id>.json (신규 per-session tap, §5) · fallback: ~/.claude/sessions/<pid>.json
        · codex    → 최신 rollout jsonl 의 마지막 token_count 이벤트 tail + config.toml (model/effort)
        · opencode → opencode.db `session` row (ro) — model/agent/tokens/cost
        · dispatch → statusline 잡스캔 로직(재사용) + .dispatch/jobs.log 병합
        ↓
[렌더 계층]  curses TUI — (A) fleet 그리드 + (B) dispatch 리스트, 1~2초 tick 라이브 갱신
```

- **백본이 세션 목록의 진실**: enrichment 가 실패/결손이어도 세션은 프로세스 스캔으로 항상 잡힌다. enrichment 는 "칸 채우기"일 뿐, 세션 존재 판정 아님.
- **pid ↔ session 매핑**: claude=`~/.claude/sessions/<pid>.json` 또는 statusline 파일의 session_id; codex=broker `--cwd`/leaf `/proc/cwd`; opencode=`/proc/cwd` == `session.directory`(argv 에 세션 id 없음).

## 2. Discovery & tap 매트릭스 (근거: 01_tap_mechanics.md)

| Need | Claude Code | Codex CLI | opencode |
|---|---|---|---|
| process comm | `claude` | `codex`(`app-server`/`exec`) | `opencode` |
| /proc/cwd + etime | ✅ | ✅ | ✅ |
| 세션 id | UUID | UUID | `ses_…`(+slug) |
| model / cwd | statusline JSON | rollout `session_meta.cwd` + config model | DB `session.model`/`directory` |
| token / context% | statusline `context_window.*` | rollout `token_count.info.*` | DB `tokens_*`(ctx% 유도) |
| **rate limit** | ✅ 5h/7d | ✅ duration-labeled windows | ❌ 없음 |
| **effort** | ✅ | ✅ config | ❌ 없음 |
| cost | ✅ | 토큰서 유도 | ✅ `session.cost` |
| liveness | transcript mtime + `sessions/<pid>.json` | rollout mtime | DB `MAX(time_updated)` |

**Takeaway**: 세션 _존재_ 는 프로세스 스캔으로 100% 균질. _상세_ 는 하네스별 비대칭 — opencode 는 rate-limit·effort 칸이 구조적으로 빈다(UI 가 결손 칸을 `—` 로 허용해야 함, §4). Codex telemetry 는 rollout jsonl 마지막 `token_count` 한 줄 tail 로 취득.

## 3. [cli] 명령·옵션·I/O

> **[minor edit · render v2 cycle, 2026-07-01]** 아래 옵션 표·키·런처 설명은 render v2 재구성 반영(cwd-group 레이아웃·스크롤·stale 토글). v1 원본은 `plans/2026-07-01_agent-fleet-dashboard/` 참조.

단일 진입 명령. 서브명령 없음(모니터 도구).

| 옵션 | 기본 | 의미 |
|---|---|---|
| `--interval <sec>` | `2` | 라이브 tick 주기(초). 백본 프로세스 스캔·enrichment 재수집 주기. |
| `--once` | off | 1회 스냅샷 렌더 후 종료(스크립트·디버그용, curses 미진입 시 plain 출력). |
| `--no-tmux` | off | tmux split 없이 현재 터미널에서 직접 실행(런처가 아니라 TUI 직접). |
| `--section <fleet\|dispatch\|both>` | `both` | **(v2 의미 변경)** 더 이상 화면 전체를 2섹션으로 쪼개지 않는다 — project(cwd) 그룹 _안에서_ 어떤 row-type 을 보여줄지 필터한다. `fleet`=그룹 안 세션 행만, `dispatch`=그룹 안 dispatch 행만, `both`=전체(기본). 필터 후 행이 0개가 된 그룹은 헤더째 생략(빈 그룹 미출력). |
| `--harness <list>` | all | 특정 하네스만(예: `claude,codex`). |
| `--json` | off | curses 대신 수집 결과를 JSON 으로 stdout(파이프·디버그·테스트). |
| `--all` | off | fleet 리스트에 stale/dead 세션도 표시. **기본은 숨김**(활성 working/idle 만; 헤더 카운트·`+N hidden` 요약은 유지). |
| `--demo` | off | **(v3 소급 등재 — audit 🟡-2)** demo fixture 를 라이브 데이터에 _병합_ 주입해 렌더 검증(대체 아님 — `2e23462`). env `FLEET_DEMO=1` 동등(런처·alias 경유 시). |

**(v2 신설) 라이브 조작 키**:

| 키 | 동작 |
|---|---|
| `↑`/`↓`, `j`/`k` | 1줄 스크롤 |
| `PgUp`/`PgDn` | 페이지 단위 스크롤 |
| `Home`/`g`, `End`/`G` | 맨 위 / 맨 아래로 이동(뷰포트는 항상 맨 아래까지 도달) |
| `a` | stale/dead 세션 + codex app-server companion 표시↔숨김 토글(`--all` 과 동일 효과, 라이브 재토글 가능) |
| `w` | **(v2 소급 흡수)** 레이아웃 cycle `auto → wide → narrow → stack` — auto 는 폭 컷오프(70/110열)가 결정, wide=1줄 grid·narrow=2줄 카드·stack=3줄 세로. 어느 모드든 harness 배지·slug·liveness 는 불락(정체성 anchor). footer 키 바에 현재 모드 표기(3-모드 전부 — §4.6 F-12). |
| 마우스 클릭(`+N hidden` 줄) | `a` 와 동일한 토글. `tmux set -g mouse on` 필요 |
| `q` | 종료 |
| `r` | 즉시 새로고침 |

- **마우스 트레이드오프(1줄 메모)**: 키보드 스크롤(`jk`/`PgUp,Dn`/`g,G`)이 기본(primary) 조작 경로다. tmux 마우스(`set -g mouse on`)를 켜면 `+N hidden` 클릭 토글이 되지만, 그 대가로 터미널 네이티브 클릭-선택·복사가 막힌다 — 그래서 마우스는 opt-in.
- **Input**: 없음(디스크·프로세스 관찰만). 환경변수 `AGENT_HOME`/`CLAUDE_HOME`(기본 `~/.claude`), `AGENT_DISPATCH_JOBS`(기본 `<AGENT_HOME>/.dispatch/jobs.log`) 존중.
- **Output**: curses full-screen(기본) / `--once`·`--json` 시 plain stdout.
- **Exit code**: `0` 정상 종료(q/Ctrl-C) · `1` 초기화 실패(터미널 아님·의존 누락) · `2` 인자 오류.
- **런처 (v2: normal-terminal 비율)**: 세로 사이드 페인 강제 배치는 폐기(retire). `fleet.sh` 기본 동작은 현재 터미널에서 `fleet.py` 를 **전체 크기(full-terminal)** 로 직접 실행. `--window` 옵션 시 tmux 안이면 새 tmux 창(역시 full-size)으로 열고, tmux 밖이면 direct 실행으로 degrade.

## 4. UI — project(cwd) 그룹 레이아웃 + 렌더 모델

> **[minor edit · render v2 cycle, 2026-07-01]** 아래는 v1 의 "(A) fleet 섹션 / (B) dispatch 섹션" 2섹션 분리 모델을 **project(cwd) 그룹** 모델로 대체한다. v1 원본 레이아웃은 `plans/2026-07-01_agent-fleet-dashboard/`(v1 빌드 사이클) 참조. §1 아키텍처 다이어그램의 "2섹션" 표기는 개념상 이 그룹 모델로 대체된 것으로 읽는다(다이어그램 자체는 미변경, §9-11 도 동일).

### [v2 기준선] 현행 화면 구성 (07-01~07-10 진화 소급 흡수 — 코드 실측)

v1 이후 커밋으로 진화한 현행 렌더 모델을 spec 기준선으로 승인한다 (render.py `_build_lines` 실측 순서):

1. **usage 헤더** — harness 별 1행 rate-limit 게이지: claude `5h/7d/<per-model>` (OAuth usage API + statusline tap), codex `duration-labeled windows` (wham API + rollout fallback, expiry-aware; `limit_window_seconds` 우선, legacy 에서만 primary=5h/secondary=7d), opencode = "no usage api" 명시행. 라벨은 dim(harness 로 오독 방지).
2. **fleet pulse 요약행** — `fleet <spinner> N working · M idle · [K detached] · ↳ J jobs (…)`. app-server companion 은 카운트 제외.
3. **alert strip** (조건부, healthy 면 0줄) — ctx ≥80% 세션 + stale/dead job, 최대 6개.
4. **프로젝트 그룹 카드** — 그룹 헤더(hot/cooling/cold 3단계 + `🚧 N` worktree 카운트; v11 minor #2 2026-07-19 — tracked/untracked 게이트 배지 퇴역: 하네스 전역 모드 폐기[커밋 `452690ff`, 사용자 결정 "굳이 의미가 있나"→"없애는 방향이 맞다"]에 따라 표시 계약에서 제거, 대체 표식 없음[healthy-silent]) → 세션 행 → dispatch 트리. 그룹핑 키 = 부모 repo 역매핑(`-wt`/`_worktrees` 2-pass) + `drill:<case>` 특수 그룹 + `loops` 그룹.
5. **folded 집계 1행** — live 세션 0 + 잡 0 그룹은 접어 `inactive +N folded <names>`.
6. **legend + footer 키 바** — 글리프 범례, 키 힌트, 스크롤 `↑N/↓N` 인디케이터.

레이아웃 3모드(`w` cycle, §3) · main-session bold · stale/companion dim·숨김 · 수동 blink(tmux A_BLINK strip 대응) · 256색 body tint(hot=midnight-blue/cooling=brown/cold=grey, 실패 시 `▍` rail fallback) 포함 전부 기준선. 이 기준선 위에서 v2 의 신규 계약은 §4.5(stage-dispatch 관제)·§4.6(UI 가독성)이다.

### project(cwd) 그룹 — 부모 repo 당 그룹 1개
세션과 그 프로젝트의 dispatch 잡을 **같은 그룹**에 묶는다. 그룹핑 키 = 부모 repo:
- worktree cwd (`<repo>-wt/<slug>`, `<repo>_worktrees/<slug>`) → 부모 repo 이름으로 역매핑.
- loops 잡(cwd 없음, key ∈ {oncall,note,study,drill}) → `loops` 그룹.
- 그 외 → cwd basename(`.broken*` 접미사는 제거).

각 그룹은 **세션 행 먼저, 그 다음 dispatch 행** 순서로 구성된다. 새 Fleet 실행과 stateless `--once`/`--json` 스냅샷의 초기 그룹 정렬은 활동도(working 포함 그룹 우선) → 최근성 → 이름순으로 결정적이다. 그러나 한 live TUI 실행 안에서는 최초 스냅샷 순서를 anchor로 보존한다: 계속 표시되는 그룹은 liveness·mtime 변화에도 서로의 상대 위치를 유지하고, 새 그룹만 survivor 뒤에 append한다. 사라진 그룹은 anchor에서 즉시 제거하며 Fleet 프로세스 재시작 시 anchor는 새로 시작한다.

> **[minor edit · cooling state, 2026-07-03]** 디렉토리(그룹) 헤더의 활동 상태를 **3단계**로 표시한다 — 코드 = `render.py` 그룹 헤더 (`_COOL_WINDOW_MIN`).
> - **활성(hot)**: 그룹 안에 `working` 세션/잡이 있음 → 이름 앞 녹색 `●`(blink) + green-bold 제목.
> - **대기(cooling)**: `working` 은 없지만 그룹 안 세션 transcript 의 최신 write 가 `_COOL_WINDOW_MIN`(기본 180분) 이내 → "방금 끝나 아직 온기" 중간 상태. 이름·인디케이터(채운 `●`)·`✓` 완료-경과 아이콘+경과시간(예 `✓ 1h32m`)을 **어두운 노랑**(dim yellow), body 틴트 = **살짝 어두운 갈색**(`_TINT_BODY_COOL`, 256-lvl 94 ≈ #875f00, `init_color` 가능 시 더 짙게). 온도 gradient = 활성 녹색 → cooling 노랑/갈색(잔열) → cold 회색. 세션은 idle 로 남아(48h live 창 안) 그룹이 접히지 않는다(R4). §7 의 dispatch-전용 `done` 을 _그룹 레벨_ 로 끌어올린 개념.
> - **비활성(cold)**: `working` 없음 + 최근 활동 없음(창 초과 또는 mtime 부재) → 이름 앞 **회색 고리 `○`**. shape-size gradient(채운 `●` 최근·활동적 > 고리 `○` 잠듦, design r2). dead(`✕` 적)·stale(`·`)와는 회색으로 구분.

### 세션 행 — harness 배지 + 1줄 패널
```
[Claude] <slug>  ✨<model> ·<effort>  🧠<ctx%>  5h<r>/7d<r>  ⏳<elapsed>  <liveness>
```
- **harness 배지(v2: 풀네임 로고, 단일 문자 C/X/O 폐기)**: `[Claude]`/`[Codex]`/`[opencode]` 텍스트를 하네스별 색상 + reverse-video 블록으로 표시. codex app-server companion 프로세스는 배지 옆에 `⚙app-server` 마커를 추가로 붙인다.
- **결손 칸 규칙(불변)**: 하네스가 안 주는 값(opencode 의 rate-limit·effort 등)은 `—` 로 표시(빈칸 아님 — "없음"을 명시).
- liveness: herdr 4-상태 어휘 재사용 — `idle`/`working`/`blocked`/`done`(+ `stale`/`dead`, §7). 색: working=녹, idle=dim, blocked=황, stale/dead=적.
- 정렬(그룹 내): 새 Fleet 실행과 stateless `--once`/`--json` 스냅샷은 working→idle→stale→dead→최근성의 기존 결정적 규칙을 사용한다. 한 live TUI 실행 안에서는 처음 보인 세션 순서를 anchor로 보존해, 계속 표시되는 행은 liveness·최근성 변화에도 상대 위치를 유지한다. 새로 보이는 세션은 survivor 뒤에 append하고 사라진 세션은 anchor에서 제거한다. 이 anchor는 live TUI run-local이며 필터/접기 뒤의 보이는 행에만 적용한다.

### dispatch 행 — 부모 세션 밑 `└▸` 자식 트리
> **[minor edit · nested-tree cycle, 2026-07-01]** v2 의 그룹당 dim `dispatch:` 서브 라벨 모델을 **세션→잡 단일 트리**로 대체한다. 각 dispatch 잡을 _그것을 분사한 부모 세션_ 아래 `└▸🚀` 자식 행으로 종속시키고, 별도 `dispatch:` 서브 라벨은 폐기. (v2 서브 라벨 원본은 `plans/2026-07-01_fleet-render-v2/` 참조.)

statusline 잡스캔 로직 재사용(**top-3 cap 제거** + `.dispatch/jobs.log` 병합). 세션 행 직후 그 세션의 자식 잡을 `└▸` 로 들여쓴다:
```
[Claude] <slug> 🛰️  ✨<model> …  <liveness>          ← 자식을 분사한 부모 세션 (command-center 🛰️)
  └▸🚀<pipe-key>▸<stage>  (<mode>·<qa>)  ⏳<elapsed>  <liveness>  <slug>
```
- **부모 링크 = 프로세스 env** (실측, `/proc/<pid>/environ`): `CLAUDE_CODE_SESSION_ID` = 그 잡을 분사한 부모 세션 id → 화면의 `Session.session_id` 와 매칭해 그 밑에 nest. `CLAUDE_CODE_CHILD_SESSION=1` = 헤드리스 자식 표식(argv `-p` 추측 대체). environ read 는 동일 user 만(충족) — 실패 시 graceful(orphan fallback). env가 없는 codex/opencode 분사는 registry `parent_cwd` → 화면 세션 cwd 매칭으로 nest한다(v9 흡수 — v8 minor #6: 세 어댑터 래퍼가 §5.10 pipe 계약의 `parent_cwd`를 부모 문맥 존재 시 기록하도록 정합 수정; 수정 전 기록 행은 잡 종료까지 orphan 유지).
- **아이콘(R5)**: 자식을 ≥1개 가진 부모 세션 앞에 command-center `🛰️`, 각 자식 잡 앞에 launch `🚀`. 자식 없는 일반 세션엔 붙이지 않음. double-width 정렬이 깨지면 render.py 의 `_ICON_PARENT`/`_ICON_CHILD` 한 곳에서 ASCII(`⌘`/`▸`)로 degrade.
- **orphan 규칙(R2)**: 부모 세션이 화면에 alive 인 동안만 nest. 부모가 죽거나(프로세스·화면 소멸) 화면 밖·env 없음이면 그 잡을 **프로젝트 레벨 orphan 으로 승격**(사라지지 않게) + `(orphan)` 마커. cron loops(oncall/note/study/drill) 는 애초에 부모 없음이 정상 → loops/프로젝트 레벨 flat(orphan 마커 없음). `--section dispatch`(세션 숨김) 에선 nest 앵커가 없어 전 잡이 flat 표시되며 이때 `(orphan)` 마커는 억제(의도적 off 이지 진짜 orphan 아님).
- **qa 실측 레이어드 fallback(R3)**: effective qa = argv `--qa` → jobs.log pipe 의 `qa=` 구조필드(신형 `capability=…,mode=…,qa=…` codex 형식) → 잡 산출물 `plans/*_<slug>/pipeline_state.yaml` 의 `qa_level` 실측 → CONVENTIONS §1.4 capability→default 맵 순. 명시값(argv)이 아닌 유도값(2~4)은 dim + `~` 접두(예 `~thorough`)로 구분 — argv 텍스트 오탐 방지 위해 `--qa` 파싱은 `[a-z]+` + valid-level 화이트리스트로 좁힌다. 이 fallback은 QA 표시만 다룬다. mode는 명시 구조필드를 우선하고, stage는 아래 `WorkProjection`의 단일 authority만 소비한다.
- stage = `WorkProjection.stage_label`. 기존 `live_stage()`는 `projection.py` 내부의 legacy artifact adapter로만 남으며, route tuple이 완전히 부재하고 exact plan-directory 후보가 하나일 때에만 호출되어 `stage_label` 하나만 제공한다. fuzzy/복수 후보 선택이나 route/node/progress/gate/completion 합성은 금지한다.
- 소스 = (a) 프로세스 스캔의 Claude autopilot/loops 잡 + (b) jobs.log 의 running/open 행(codex/opencode dispatch 는 여기서만 보임 — §6). dispatch 의 stale/dead 는 `--all` 무관 **항상 노출**(정리 신호).

### stale/companion 표시 비대칭 (v2 신설 — 세션 ≠ dispatch)
- **세션**: stale/dead 상태 또는 codex app-server companion 은 그룹별로 **기본 숨김**, 그룹 하단에 `+N stale/companion hidden` 요약 행(클릭·`a` 토글 가능). 표시로 전환 시 telemetry(모델/ctx%/rl/effort/cost)는 **dim(어둡게)** 처리 — last-observed 값이며 라이브 값이 아님을 시각적으로 구분. codex app-server 는 표시 전환 시 ctx%/rl 이 대시(`—`)로 남는다(companion 오귀속 문제 — §7 참조).
- **dispatch**: stale/dead 잡은 `--all` 여부와 무관하게 **항상 표시**(숨김 폴드 없음) — 잡 실패·중단 신호를 놓치지 않기 위함.
- **그룹 접기(R4, nested-tree cycle 2026-07-01)**: live 세션(비-stale/dead)이 0인 프로젝트 그룹은 **기본 접기** + `━━ 📁 <name>  (+N folded)` 요약 행(같은 `a`/클릭 토글로 펼침) — 세션 stale-hide 를 그룹 레벨로 미러. **caveat**: 노출 필요한 dispatch(active/stale/orphan 잡)가 그룹에 있으면 접지 않는다(dispatch 를 절대 숨기지 않기 — 접기 조건 = live 세션 0 AND 그룹 잡 0). 접힌 요약 행도 `_TOGGLE_ROWS` 등록으로 클릭 토글.

### 렌더 모델 (zero-dep curses)
- 단일 `curses` 루프, `--interval` 마다 재수집→재그림. `KEY_RESIZE` 처리(폭/높이 재계산, 스크롤 위치는 재클램프만 하고 리셋하지 않음). flicker 는 이 규모에서 무시(전체 지우고 다시 그림, 또는 `erase()`+`noutrefresh()`).
- **뷰포트 스크롤(v2 핵심 수정)**: 전체 라인이 화면 높이를 넘으면 v1 은 `+N more (resize)` 로 잘려 맨 아래에 도달할 수 없었다(핵심 버그). v2 는 offset 기반 뷰포트 렌더러로 교체 — 스크롤(§3 키 표)로 **항상 맨 아래까지 도달**. 푸터에 `↑{above}`/`↓{below}` 인디케이터 + 키 힌트 표시.
- 키: `q`=종료, `r`=즉시 새로고침, 스크롤/`a`/마우스는 §3 참조.
- 폭이 아주 좁으면(<~70열) cost/rl → effort → model 순으로 필드를 줄인다(배지·slug·liveness 는 정체성·상태 앵커라 항상 유지). 2열 그리드 승격은 MVP 밖(변경 없음).

## 4.5 [v14 개정] stage-dispatch 관제 parity — unit-aware 스테이지 row 계약 ★

> 근거: dispatch contract v3의 정식 축은 `assigned_contract`(portable capability/stage Skill), `unit`(portable unit catalog entry), `worker_type`(owner/stage/review/support bootstrap kind), `model_role`이다. `worker_role`은 구 jobs.log 판독만을 위한 legacy metadata이며 새 writer의 bootstrap·Skill·persona 정체성이 아니다.

- **SD-F1 (스테이지 row 사람 라벨)**: depth-2 row의 1차 단계명은 `assigned_contract`와 route `nodes[].id`에서 결정한다. `unit`은 같은 단계가 어떤 composable 실행 단위를 선택했는지 보여 주는 보조 라벨이며, `worker_type`과 `model_role`은 각각 bootstrap 종류와 모델 프로필로 분리한다. authoritative 필드가 없는 구 행에서만 `worker_role=code-plan/code-execute/code-test/code-report`를 legacy fallback으로 읽고 새 writer는 이를 생성하지 않는다.
- **SD-F2 (conductor 집계)**: depth-1 owner가 route record를 가지면 breadcrumb는 record의 DAG와 depth-2 `route_node`/`assigned_contract` 실측을 우선한다. route tuple이 완전히 부재한 legacy `owner=autopilot-code` 행에서만 `worker_role=code-*` 자식을 fallback으로 사용한다. 명시 tuple이 하나라도 있으나 record를 검증하지 못하면 fallback하지 않고 unknown/ambiguity로 남긴다. 완료 자식과 다음 미분사 사이의 갭은 route-부재 legacy 행에서만 산출물 유도값으로 표시한다.
- **SD-F3 (스테이지 자기 model/effort)**: dispatch wrapper가 pipe에 `model_role=/model=/effort=`를 기록하므로 스테이지 row는 자기 모델·effort를 1급 표시한다. pipe 값 부재 시 부모 상속은 fallback으로만 표시한다.
- **SD-F4 (pipe 파싱 tolerant + additive unit)**: pipe key=value 구분자의 canonical은 콤마지만 공백/콤마 혼용 구 행도 수용한다. `unit=`과 프로세스 env `AGENT_DISPATCH_UNIT`은 additive이며 부재는 정상이다. 미지 key는 무시하고 legacy row의 의미를 합성하지 않는다.
- **비대상(경계)**: conductor·스테이지의 제어는 여전히 monitor-only이고 depth-3+는 비지원이다. unit은 native subagent 종류나 runtime session persona로 역추론하지 않는다.

## 4.6 [v2 신설] UI 가독성 개선 — 정보 위계·스캔 가능성 (사용자 "아쉬운 점" 해소)

- **F-9 (dispatch 메타라벨 가독화)**: 현행 `(loop/drill-diagnosis·q/diagnosis_gro…/qa:~q)` 처럼 축약·중간잘림이 겹친 라벨을 재배분 — (a) role 은 SD-F1 단계명 매핑 우선, 매핑 밖 role 은 **중간잘림 대신 뒤에서 자름**(head 보존) (b) drill 케이스 하드코딩 축약 맵(`g6`/`g9` 등)은 **일반 규칙으로 대체**(`g\d+` 접두 추출 — 신규 케이스마다 코드 수정하는 구조 제거) (c) 라벨 성분 우선순위 명문화: 폭 부족 시 `qa → intensity → role` 순으로 드롭하되 mode 는 유지 (d) `~` 유도값 접두는 유지 + legend 에 1회 설명.
- **F-10 (alert 행 humanize)**: alert 의 job 이름도 dispatch 행과 같은 compact 이름 경로 재사용 — loop 잡의 `<case>-<ts>-<pid>` 꼬리(`…-20260710035842-294678`)는 strip. 같은 종류 alert 다수면 개수 집계(`⚠ 2 dead jobs: a·b`). 화면 폭 초과는 조용한 클립 대신 우선순위 절단(dead > stale > ctx).
- **F-11 (raw status 어휘 정리)**: registry-only 잡의 stage=`open`/`running` raw 노출과 loop 잡 `drill: running` 류를 사람 어휘로 — `open`=`queued`(미기동 대기), `running`=breadcrumb 미점등 트랙(기존 규칙 재사용). status 어휘 자체(jobs.log)는 불변 — 표시층만.
- **F-12 (footer·잡음 절제)**: (a) `+N malformed jobs.log rows skipped` 는 dim 강등 — 진단 상세는 `--json` 몫 (b) footer `w` 라벨이 stack 모드를 누락하는 표기 버그 수정(3-모드 전부) (c) legend 는 현재 화면에 실제 등장한 글리프만.
- **F-13 (dead/stale 행 결손 절제)**: dead/stale row 의 `— … — … —` 나열 대신 telemetry 셀은 생략하고 **마지막 관측 경과**(`last seen 2h`) 1값으로 대체 — "없음" 명시 원칙(F-3)은 live 행에만 적용, 죽은 행은 결손 나열이 정보가 아니다.
## 4.7 [v3 승격] 표시명·관제 표면 확장 — F-14~F-19

> v2 minor 5건(2026-07-10~11)의 승격 흡수. §4.6 이 "가독성 정제"(표시층 한정)였다면 본 절은 **신기능·신규 표면**이다 — 제목 소스 승격(F-14)·레이아웃 재설계(F-15/16)·fleet 소유 sidecar+LLM 워커(F-17)·collector 태깅(F-18)·신규 collector+패널(F-19). audit 🟡-1(섹션 의미 확장) 해소 분할.

- **F-14 (세션 표시명 = 하네스 세션 제목, 사용자 요청 2026-07-10 — 후속 사이클)**: 세션 row 이름을 합성 slug(`<cwd>-<sid8>`)에서 **하네스가 이미 남긴 세션 제목**으로 승격 — "ChatGPT 세션명처럼" 내용 요약이 관제에 보이게.
  - **소스 (실측 2026-07-10, Codex 재검 2026-07-13)**: claude = transcript jsonl 의 마지막 `{"type":"ai-title","aiTitle":…}` 라인 / opencode = DB `session.title` / codex = `$CODEX_HOME/state_<version>.sqlite` read-only `threads.title`(현재 활성 세션 포함) 우선 + `session_index.jsonl`의 최신 `thread_name` compatibility fallback. Codex 0.144.1에서 state DB 293행 중 286개 title, JSONL index 164개 이름을 확인했고 공식 `/rename` 표면과 정합한다. 전부 tolerant 파싱하며 부재·스키마 변경 시 fallback한다. Codex rollout `session_meta`에 제목이 없다는 과거 관찰만으로 Codex 전체 runtime에 제목 소스가 없다고 결론 내리지 않는다.
  - **표시 규칙**: 제목 있으면 name zone 에 제목(뒤에서 자름 — F-9 head 보존), 합성 slug 는 대체(식별 필요 시 dim 보조). headless 자식 세션(`-p`)엔 ai-title 이 없음 → 현행 slug 유지. 제목 부재·파싱 실패 = 현행 합성명 fallback (회귀 없음 원칙).
  - **비용**: liveness 가 이미 transcript mtime 을 보고 있으므로 같은 파일 tail 역스캔(수 KB)으로 마지막 ai-title 추출 — tick 당 부담 미미, 필요 시 mtime 키 캐시.
  - 하네스 자체 기능과의 경계: Claude Code 는 `/rename`·시작 시 auto-name 만 있고 _진행형_ 자동 재요약·프로그램적 갱신은 미지원(공식 문서 확인) — 그래서 이 자리는 fleet 표시층이 맡는 게 맞다 (zero-injection 관찰, §0.5).
- **F-15 (분사 row 레이아웃 재설계 — 탈가로화 + 옵션 1급 유지, 사용자 피드백 2026-07-10 저녁)**: F-14 출하 후 사용자 최대 불만 = "분사 세션 명이 다양한 옵션과 함께 가로로 쭉 늘어짐". 단 **옵션(capability·mode·qa·intensity·model/effort)은 사용자가 관찰하는 중요한 요소 — 숨기지 말고 더 잘 설계하라**가 명시 요구.
  - **방향**: 1차 라인은 정체성(단계 라벨·stage breadcrumb·상태·경과)로 다이어트하고, 옵션 메타는 **가로 나열 태그 대신 정렬된 자리**로 이동 — wide 레이아웃 = 고정 컬럼 정렬(세션 row 의 model/ctx 컬럼과 같은 원리), narrow = 2줄 카드의 L2 dim 옵션 라인 (세션 2줄 카드 기존 패턴 미러). F-9(c)의 "폭 부족 시 성분 드롭" 접근은 이 재배치로 대체.
  - **depth별 실행 정체성(v14, 2026-07-22)**: depth-1 options cell은 entry capability와 orchestration knobs를 표시한다(`code(dev/refactor·strong·owner)`). depth-2는 부모의 mode/entry를 반복하지 않고 **자신에게 배정된 `assigned_contract`와 `unit`**을 표시한다. contract는 portable Skill/단계 정체성, unit은 catalog가 선택한 composable 실행 단위이고 `worker_type`은 bootstrap 종류, `model_role`은 모델 프로필이다. route record의 `nodes[].unit`/`unit_choices`가 canonical이고 jobs.log `unit=`은 실행 실측이다. `worker_role`은 legacy metadata로만 보존하며 새 writer가 생성하거나 Fleet이 authoritative field보다 우선하지 않는다. QA level은 `--json` evidence에만 보존한다.
  - **workflow-first 정렬**: 관제의 1차 질문 = "어느 파이프가 어느 스테이지에 있고 어디가 막혔나". conductor row 의 파이프 진행(breadcrumb, SD-F2)이 1급이고, **done 스테이지 자식 row 는 기본 접어 breadcrumb 하이라이트로 흡수**(완료 잡 나열이 세로·가로 노이즈) — 활성(working/미기동)·실패(stale/dead/killed) 스테이지만 자식 row 로 남긴다.
  - **queued 오라벨 해소 (사용자 관찰: "queued 가 계속 뜨는데 작업 중인 건지?")**: 현행 `open`→queued 매핑은 registry-only row 전부에 적용돼, 실제 작업 중인데 proc 매칭이 안 된 row(proc-job 과 registry row 의 slug 불일치, cross-harness 등)도 queued 로 뜬다. 해소: registry-only row 에 **worktree transcript/rollout mtime 기반 liveness 유도**를 적용해 실작업 중이면 working 으로, queued 는 _진짜 미기동_(등록 후 transcript 무활동)만. proc-job ↔ registry row 의 slug 정합(dedup 키) 개선 포함.
  - 디자인팀 critic 을 plan 단계 텍스트 목업 비평에 필수 투입 (UI plan-review 계약) — 잡 다수일 때 세로 폭증·레이아웃별(wide/narrow/stack) 분기까지 비평 범위.
- **F-16 (세션 표시명: 짧은 영어 기준선, 사용자 요구 2026-07-10 저녁; 고정 폭은 F-22가 대체)**: F-14 의 title 표시가 문장형(한국어)으로 길어 20~24 display cols의 고정 tail-cut과 짧은 영어 sidecar를 도입했다. v6/F-22는 이 고정 폭만 대체하며, 영어·head 보존·native fallback 계약은 유지한다.
- **F-17 (라이브 제목 refresher — cross-harness fleet sidecar + no-tools 경량 LLM 워커, 사용자 승인 2026-07-10·공유 확장 2026-07-13)**: 하네스 원본 transcript에 쓰지 않고 **fleet 소유 neutral sidecar**로 진행형 재요약을 제공한다.
  - **sidecar**: `${FLEET_TITLE_STATE_DIR:-${XDG_STATE_HOME:-~/.local/state}/agent-fleet/titles}/<harness>/<sid>.json` — `{title, ts, source, offset}`. `<harness>/<sid>` namespace로 충돌을 막는다. 기존 `~/.claude/.fleet-titles/<sid>.json`은 Claude read-only migration fallback이다. 표시 우선순위 = **fresh sidecar(<24h) → runtime-native title(ai-title/threads.title/thread_name/session.title) → slug**.
  - **공용 워커**: `tools/fleet/refresh_title.py`가 Claude/Codex transcript delta를 공통 대화 텍스트로 정규화한다. 기본 provider는 기존 `claude -p --model haiku` + 도구 전면 차단이다. `FLEET_TITLE_COMMAND` argv template와 `FLEET_TITLE_MODEL`로 GPT 계열 등 별도 저비용 no-tools wrapper를 교체할 수 있다. shell은 사용하지 않으며 모델 출력은 영어 `TITLE:`과 대화 언어 `NOW:` 데이터로만 검증한다. **현행 TITLE 검증 계약은 3~6단어·최대 40자 하나뿐**이다. v9의 4~8단어·64자와 v6의 8~12단어·96자 계약은 역사적 기준이며 본 v16 계약이 명시적으로 대체한다.
  - **트리거**: Claude는 statusline debounce를 유지하되 neutral state/공용 워커를 쓴다. Codex는 live fleet loop가 collector가 찾은 rollout을 대상으로 같은 debounce(기본 10분)·`<harness>/<sid>` lock을 적용한다. `--json`, `--once`, demo/test 경로는 worker를 spawn하지 않는다.
  - **(v16 표시 개정; v11 minor #1의 생성 계약 유지) 제목+부제 통합 — 한 호출 두 출력**: provider 호출 하나가 `TITLE:`/`NOW:` 두 줄을 반환하고, 제목은 3~6단어·40자, NOW는 대화 언어 1문장·저장 120자를 유지한다. 사이드카의 `summary` additive·15분 신선 창·부제 실패 시 제목만 저장하는 정직 강등은 불변이다. **표시 위치는 F-37이 대체**한다: wide 전용 NOW 서브 행과 주 행 내 ctx gauge를 폐기하고, wide/narrow/stack 모두에서 정체성 카드 바로 아래 단 하나의 `ctx … · NOW` subordinate line을 사용한다. **분사 세션 디바운스 150s**(메인 600s)는 유지한다.
  - **(v16 개정) 분사 세션 전면 적용**: live fleet 스케줄러는 분사 자식 세션(`is_child`)도 메인 세션과 동일하게 요약 대상에 포함한다. 내부 워커 재귀 차단은 `is_child`가 아니라 mem_worker 태그(`FLEET_TITLE_REFRESH`/`MEM_DISTILL`) 몫이며, 메인·자식·기본·커스텀 provider는 F-39의 동일한 전역 slot/start pool을 공유한다. 스케줄러는 live TUI 루프에서만 돌고 `--json`/`--once`/demo/test에서는 provider를 시작하지 않는다.
  - **하네스 차이**: title provider와 sidecar 계약은 공용이고 native source만 다르다(Claude `ai-title`, Codex `threads.title` + legacy `thread_name`, OpenCode `session.title`). 하네스 종류나 native title의 존재는 scheduler 제외 조건이 아니다. Claude/Codex/OpenCode의 일반 registered conversational child는 모두 F-24의 동일 predicate와 150초 debounce를 적용하고, provider 실패·미호출 시 각 native title을 fallback으로 유지한다.
  - **비용·fallback**: provider 실패·미설치·quota 소진은 sidecar 미갱신으로 끝난다. Codex는 state DB/JSONL native title, Claude/OpenCode는 각 native title, 마지막으로 slug가 남으므로 제목이 사라지지 않는다.
- **F-18 (loop·drill·mem-워커 귀속 정밀화, 사용자 점검 요청 2026-07-11 "fleet에서 loop나 drill 관련한 부분 점검")**: 2026-07-11 drill 실발사 관찰로 확정된 표시 결함 2종.
  - **F-18a (drill runner 이중 표시 dedup)**: 같은 drill 실행이 두 row 로 뜬다 — (i) proc-scan loop job (key=`drill`, cwd=fixture) (ii) lib-runner 가 registry 에 쓴 row (slug=`drill-<harness>-<case>-<ts>-<pid>`, 매 실행 고유). slug 불일치로 기존 dedup(동일 slug skip)이 안 걸린다. 해소: **case 명 + cwd 상관**으로 매칭해 registry row 를 정본으로 1행 병합(proc 는 liveness 소스로 흡수) — F-15 의 proc↔registry 정합과 같은 계열, 매칭 키만 drill 명명으로 확장.
  - **F-18b (mem-워커 오귀속)**: 메모리 distiller/curator(`claude -p`, env `MEM_DISTILL=1`)와 F-17 refresher(`FLEET_TITLE_REFRESH=1`)가 부모 세션의 cwd·env 를 물려받아 (i) 부모 세션 밑 `↳` 자식 row 로 떠올랐다 수 분 내 사라지고(사용자 실관찰 "서브로 떴다가 지시하자마자 없어짐") (ii) cwd 가 drill fixture 면 `drill:<case>` 그룹으로 오귀속된다(실관찰: 큐레이터가 "drill running" 으로 표시). 해소: procscan 이 `/proc/<pid>/environ` 의 이 마커들을 읽어(동일 user, dispatch collector 의 AGENT_DISPATCH_* 선례) **mem-worker 세션으로 태깅** — 기본은 fleet pulse 카운트·그룹 row 에서 제외하고 legend 급 요약(`🧠N`)으로만, `a` 토글 시 dim row 노출(라벨 `mem`). drill/프로젝트 그룹 오귀속 차단이 1차 목적.
  - 불변식: collector/`--json` additive only(drill g9/g10 파이썬 임포트 표면)·registry 무write·기존 dedup·F-14~F-17 계약 유지.
- **F-19 (메모리 관측 패널 — mem 이벤트 요약행+상세, 사용자 확정 2026-07-11 "fleet에 memory 기능 추가")**: F-18b 가 mem-*워커*(프로세스)를 태깅한다면 F-19 는 그 *효과*(무엇이 기억·삭제됐나)를 보인다. 소스 = Unified Memory System PRD **v15 Cluster J** 의 write-events.jsonl(변이 이벤트 저널, D-37) + `memory/deleted-records.jsonl`(graveyard) tail — 둘 다 memory 시스템이 자기 목적으로 남기는 로그를 read-only 관찰(F-1 zero-injection 불변, 신규 emit 경로 아님).
  - **collector**: `collectors/memory.py` 신설 — 저널·graveyard tail 파싱(tolerant: 파일 부재·미구현·malformed 행 = 패널 생략/부분 표시, 회귀 없음). 기존 Session/DispatchJob 스키마 불변 — additive 신규 구조(`--json` 에 `memory` 키 추가).
  - **요약행**: pulse 근처 1행 — `🧠 mem  +N added(w·d) · M expired · K pruned · last distill <경과>` (오늘 로컬 자정 기준 집계, 이벤트 0 이고 alert 없으면 행 생략 — healthy 무음 원칙, alert strip 동형).
  - **상세**: `a` 토글 시 최근 이벤트 N줄(기본 8) dim row — 시각·action·tier/type·actor·body 스니펫 (F-18b dim row 계열, legend 글리프는 등장 시만 — F-12).
  - **alert 편입**: durable soft-ceiling 초과 · 활성 프로젝트 distill 무소식(저널 기준 임계 초과 = silent-death 신호) → 기존 alert strip 버킷 추가(우선순위 dead > stale > ctx > mem).
  - **의존·경계**: Cluster J D-37 저널이 add/reinforce 계열의 유일 소스 — 저널 미출하 구간엔 graveyard 만으로 삭제측 degrade 표시. 새 sync/migrate 흡수가 DB에 신규 레코드를 persist하면 기존 어휘 `action=add`·literal `actor=sync`로 정확히 1건 들어오며 collector·집계 로직은 바꾸지 않는다. 신규 레코드가 없는 반복 흡수는 이벤트 0건이고, 배포 전 레코드/source에 대한 historical backfill도 없다. 저널 포맷 변경 시 양 spec 동기 의무. 제어(prune 실행 등)는 여전히 Non-goal — 관찰만.
  - **(v11 신설) 레포별 카드 행 — 사용자 확정 2026-07-16 "mem는 레포별로" + "틴트 내부에 은은한 구분선"**: 그룹 카드 하단(bottom padding 앞)에 카드 틴트 위 in-band dim `─` 구분선 1행 + 그 레포의 오늘 mem 이벤트 최근순 최대 2행 — `🧠 HH:MM ± tier/type actor ⟵ <출처 세션 제목> "snippet"`, 전부 dim에 `+`=green/`−`=red만 착색. 귀속 키 = 저널 행의 `cwd`(board와 같은 `project_of` 그룹핑) 또는 `project` 필드; 필드 없는 구행은 정직 생략 — **이벤트 없는 레포는 구분선까지 전부 무음**(healthy-silent). 출처 세션 태그(`⟵`)는 저널 `sid`가 화면 세션으로 해석될 때만(오귀속 금지, F-26 계열). 일반 변이의 `cwd`는 메모리 PRD §5.12.1의 `MEM_CWD`/프로세스 fallback을 따르지만, sync/migrate 흡수의 `cwd`는 auto-memory의 decode 절대경로·post-it 레포 루트·decode 가능한 legacy 원천처럼 **원천의 논리 프로젝트 cwd**이며 실행 프로세스 cwd가 아니다. global/decode 불가 원천과 필드 없는 구행은 정직 생략한다. intel 존 집계 1행과 `a` 토글 상세(위 계약)는 불변. collector 반환에 `by_repo` additive.
- **F-20 (Codex dynamic rate-window contract, 2026-07-13 runtime-currentness incident)**: Codex usage windows are runtime data, not fixed names.
  - **Runtime support (official-source basis)**: OpenAI Codex public docs now frame Codex usage through ChatGPT plan-relative usage, credits, and token/credit consumption rather than a universal API-primary 5h window. Claude official support still documents Claude/Claude Code shared usage limits and reset waiting behavior. Normative fleet labels must come from official sources plus observed runtime schema, never from stale harness assumptions.
  - **Local projection**: Codex `wham/usage` and rollout `rate_limits` windows may carry `limit_window_seconds`. Fleet must parse that duration and render the label from the duration (`604800` -> `7d`, `18000` -> `5h`, etc.). The legacy mapping remains only when duration is absent: `primary`/`primary_window` -> `5h`, `secondary`/`secondary_window` -> `7d`.
  - **Parity gap**: Claude still exposes/usefully maps `5h`/`7d` buckets; Codex may expose one or more differently-sized windows, and `secondary_window` may be null. Fleet must not force Codex parity by naming primary as `5h`.
  - **Fallback**: Unknown positive durations render as their actual duration (`12345s`, `90m`, `2w`) rather than a false semantic label. Missing duration plus missing legacy slot renders the normal `—`/no usage row fallback. Expired reset timestamps still zero out stale rollout samples.
  - **Docs/examples**: user-facing examples must say `windows` or duration labels for Codex, not "Codex 5h/7d" as a guarantee. Claude examples may keep 5h/7d where the source remains Claude usage support.
- **F-21 (Codex title parity + shared provider, 2026-07-13 사용자 요구)**: F-14/F-17의 stale Codex `slug` 폴백을 폐기한다. Codex collector는 최신 versioned state DB의 `threads.title`을 read-only로 읽고 DB/WAL stamp cache를 적용하며, `session_index.jsonl` 최신 `thread_name`은 compatibility fallback으로 병합한다. fresh fleet sidecar가 native title을 이기며, live fleet만 shared refresher를 schedule한다. acceptance = 현재 활성 Codex native title 표시, JSONL fallback, sidecar precedence, Claude legacy fallback, 두 transcript parser, provider shell-free argv, live-only spawn, canonical/Claude mirror parity.
- **F-22 (세션 name zone 반응형 예산, v16 ctx 이동 반영)**:
  - **wide**: 터미널 폭에서 branch·harness(model·effort)·time과 패널 inset을 먼저 예약하고 세션 제목은 40 display-cols 고정 상한을 지킨다. ctx는 더 이상 주 행/name-zone 예약 요소가 아니며 F-37 subordinate line으로 이동한다. dispatch 이름의 F-15 24열 compact 상한과 공통 컬럼 정렬은 유지한다.
  - **narrow/stack**: 현재 터미널 폭과 L1 suffix(child-count·branch·상태 태그)를 기준으로 제목 예산을 계산한다. `_clip_w`의 display-cell/CJK 안전 tail-cut을 계속 사용하고, ctx는 identity card 밖 F-37 subordinate line에서 독립 예산을 갖는다.
  - **provider**: sidecar의 현행 `TITLE:`은 F-17의 단일 계약인 3~6단어·최대 40자를 저장한다. v9의 4~8단어·64자와 v6의 8~12단어·96자는 superseded 역사값이며 구현 입력이 아니다. 기존 sidecar는 호환하며 다음 debounce 갱신 때 자연스럽게 교체한다.
  - **[v8 minor 2026-07-15 — wide name zone 고정 상한 복원]**: F-22의 "터미널 slack을 세션 name column에 전부 준다" 계약은 **회귀로 판정**(사용자 피드백: "session 길이를 맞춤형으로 늘린 건 오히려 별로"). wide 레이아웃의 세션 제목 컬럼은 **고정 상한(기본 40 display cols, 상수 한곳에서 조정)**을 넘지 않으며, 남는 slack은 name column에 재배분하지 않는다. narrow/stack의 suffix-예약 예산 계산, display-cell/CJK 안전 tail-cut, dispatch compact 상한(F-15 24열)은 그대로 유지. F-22의 acceptance 중 "168열에서 예산이 24열보다 커진다"는 "40열 상한까지만 커진다"로 대체.
  - **acceptance**: 60/100/120/168열의 wide/narrow/stack 주 행과 subordinate line 모두 터미널 경계를 넘지 않고, branch/model/time 및 dispatch 정렬이 유지되며, ASCII/한글 제목·NOW는 display-cell 경계에서만 잘린다.
- **F-23 (제목 생성 재귀 폭풍 봉쇄, 2026-07-14 사고 후 사용자 요구)**:
  - **사고/원인**: 앞선 distill 큐레이터 폭풍이 남긴 수백 개 내부 세션이 live fleet 수집에 보였고, scheduler가 `mem_worker`/child를 제목 대상에서 제외하지 않아 각 transcript마다 `refresh_title.py → claude -p`를 시작했다. 제목 provider 자체도 세션으로 다시 수집되는 재귀 경로와 전역 상한 없는 백로그 drain이 결합해 title chain 216개, Claude 계열 프로세스 607개까지 증식했다. per-session lock/debounce는 서로 다른 sid 사이의 폭발을 막지 못한다.
  - **그래프 차단(v16)**: live scheduler는 `mem_worker`, `app_server`, dead/stale을 title 대상으로 삼지 않지만 일반 `is_child`는 F-17·F-39에 따라 대상이다. provider/worker의 `AGENT_SESSION_ROLE=worker`+`FLEET_TITLE_REFRESH=1`은 procscan에서 `mem_worker`로 식별되어 자기 요약 재귀를 끊는다. Claude statusline도 동일 env 재귀 가드와 중앙 worker 안전 계약을 사용한다.
  - **하드 상한(v16 단일 진실=F-39)**: fleet state root의 cross-process lease로 provider 동시 실행 기본 3·하드 최대 4(`FLEET_TITLE_CONCURRENCY`), rolling 60초 start budget 기본·하드 최대 4(`FLEET_TITLE_MAX_STARTS`)를 강제한다. 0은 비활성화이고 잘못된 값은 안전 기본값으로 복귀한다.
  - **kill switch/fail closed**: `FLEET_TITLE_DISABLE=1` 또는 `<title-state-root>/.refresh-disabled`가 있으면 statusline shell, scheduler, worker main, provider 직전 네 경계에서 새 호출을 거부한다. state guard 획득 실패·provider 부재·quota 소진도 sidecar 미갱신으로 끝나며 native title/slug fallback을 유지한다.
  - **복구**: SIGKILL로 남은 worker slot은 `2 × WORKER_TIMEOUT` 뒤, rolling-start lease는 60초 시간 창을 벗어나면 회수한다. lock/lease 갱신은 cross-process file lock 아래 수행하고 경합 시 fail closed한다.
  - **acceptance**: fake clock·격리 state root·stub provider만 사용한 hermetic test에서 200개 root/child backlog도 기본 동시 3, override 시 최대 4를 넘지 않고, 슬롯이 반환되어도 60초 동안 총 4개만 시작한다. mem-worker/app-server·kill switch는 0회, 정상 child는 자신의 150s debounce 후 대상, stale slot은 회수된다. live/default/custom provider는 테스트에서 절대 호출하지 않는다.
- **F-24 (portable worker 귀속 + Codex 세션 ID 단일 소유, 2026-07-15)**:
  - 모든 repo-owned background launcher의 `AGENT_SESSION_ROLE=worker`를 procscan/dispatch collector가 `is_child`의 강한 **귀속 증거**로 사용한다. 이 마커 자체는 title/NOW scheduler 제외 조건이 아니다. scheduler는 `mem_worker`(`FLEET_TITLE_REFRESH`/`MEM_DISTILL`), app-server, dead/stale, transcript가 없는 비대화식 loop/cron처럼 명시적으로 내부·비요약 대상으로 분류된 행만 제외한다. 일반 registered dispatch 자식은 대화 transcript가 있고 내부 제외 태그가 없으면 F-17/F-23/F-39에 따라 150초 debounce 대상이다.
  - Codex는 같은 cwd의 두 TUI 중 한 프로세스만 rollout fd를 소유할 수 있다. collector tick 시작 시 모든 `/proc/<pid>/fd` 기반 강한 rollout 소유권을 먼저 예약하고, fd가 없는 row의 cwd/start-time fallback은 예약된 sid를 절대 재사용하지 않는다. 따라서 한 sid/title이 두 PID에 동시에 찍히지 않는다. 식별 불충분 row는 `session_id/title=None`으로 정직하게 degrade하며 살아 있는 프로세스를 숨기지는 않는다.
  - acceptance: 같은 cwd의 fd-owner + fd-less TUI fixture에서 owner만 sid/title을 얻고 worker marker는 child 귀속만 증명한다. 대화 transcript가 있고 내부 제외 태그가 없는 일반 registered child는 150초 debounce 뒤 scheduler 대상이며, `mem_worker`/app-server/dead/stale 및 transcript 없는 비대화식 내부 loop/cron 행만 0회다. live `--json` snapshot에서도 동일 sid 중복이 없어야 한다.
- **적용 순서(정보 위계, v7 정정)**: §4.6(F-9~F-13)은 표시층(render.py) 한정 — collector 계약·모델 스키마 불변(SD-F4 만 collector). §4.7(F-14~F-24)은 각 항목에 명시된 표면까지 — F-17/F-21 neutral sidecar+shared trigger, F-18/F-24 procscan environ 태깅·Codex identity ownership, F-19 신규 collector(`collectors/memory.py`)·`--json` additive `memory` 키, F-20 Codex usage runtime-currentness, F-22 responsive render/provider, F-23 모든 title-provider ingress 안전 경계. 시각 결정이 substantial 해지면 autopilot-design 리드.
- **🧠 글리프 위계 (v3 명문화, audit 정보성 반영)**: 같은 글리프의 두 표면 — 그룹 헤더 `🧠 N` = F-18b mem-*워커 프로세스* 수 / pulse 인접 `🧠 mem …` 행 = F-19 메모리 *이벤트* 집계. 라벨 문맥(`N` vs `mem`)이 구분자 — 새 🧠 표면 추가 시 이 두 의미와 충돌 금지.

## 4.8 [v8 신설] 관제 신뢰성·세션 제어·분사 정책 연동 — F-25~F-28

> 계기(2026-07-15 사용자 결정 4건): ① herdr가 띄운 pid 1168514 유령 interactive 세션이 `title None`의 익명 idle 행으로만 표시돼 사용자가 어디서도 인지 불가 실측 ② "버그라기보다 동작의 판정 기준 자체가 계속 불안정한 느낌" ③ "fleet에서 직접 세션 제어 가능하게" ④ "에이전트 분사 정책과 연동되는 가장 중요한 UI — 제대로 검토 필요". §4.6이 표시층 가독성, §4.7이 표면 확장이었다면 본 절은 **판정의 신뢰성과 관제 폐루프**다.

- **F-25 (세션·잡 상태 판정의 단일 상태 모델)** ★ v8 핵심 — "기준 불안정" 해소.
  - **문제**: 상태 판정이 층층이 쌓인 사고별 휴리스틱에 분산돼 있다 — proc scan, transcript/rollout mtime 창(15min), slug 상관 dedup(F-18a), `open`→queued 매핑과 worktree mtime 유도(F-15), env 마커(F-18b/F-24), rollout fd 소유권(F-24). 각각은 정당하나 **우선순위·충돌 규칙이 코드 암묵**이라 같은 세션이 tick마다 다른 기준으로 분류될 수 있고, 사용자는 "왜 이 상태인가"를 검증할 수 없다.
  - **계약**: 단일 분류기(`model.py` 소유)가 모든 세션/잡의 상태를 결정한다. 입력 소스 우선순위를 규범으로 고정: **(1) 명시 registry 상태**(jobs.log status, `~/.claude/sessions` status) > **(2) 강한 프로세스 증거**(exact pid + `/proc` start-time, rollout fd 소유권, `AGENT_SESSION_ROLE` 등 env 마커) > **(3) mtime 휴리스틱**(최후, 유도값 표시 `~` 접두 유지). 하위 소스는 상위 소스와 모순될 때 절대 이기지 못한다.
  - **exact lifecycle 보강(v12)**: registered dispatch는 exact
    `attempt_id+route_id+route_node`의 terminal watchdog/log observation이 과거
    heartbeat·PID·cwd mtime보다 우선한다. canonical attempt identity가 있으면
    evidence가 stale/unknown이어도 cwd-wide transcript로 `working`을 합성하지 않는다.
    interactive Codex session은 검증된 최신 `task_started`/`task_complete`/
    `turn_aborted`를 mtime보다 먼저 사용하며 terminal lifecycle은 hysteresis 없이
    즉시 `idle`이다. 이는 registered dispatch와 in-session/native activity를 같은
    행으로 합치는 규칙이 아니라 두 표면의 독립적인 exact evidence 계약이다.
  - **어휘 정합 — 규범 매핑 표 [v9 삽입, audit 🟡 해소]**: 표시층은 아래 표를 임의 재해석하지 않는다. 구현 상수는 `model.py` 한곳(`SESSION_WORK_SEC=60s`, `SESSION_STALE_MIN=48h`, `JOB_STALE_MIN=15min`, `UNUSED_ACTIVITY_MS=2000ms`).

    **세션** (위 tier 우선순위 하에서):

    | 입력 증거 | tier | 상태 |
    |---|---|---|
    | pid 사망 · registry procStart ≠ `/proc` start-time (PID 재사용) | 2 | `dead` (즉시, hysteresis 없음) |
    | cwd symlink `(deleted)` (worktree 소멸) | 2 | `stale` |
    | registry `status=busy` | 1 | `working` |
    | registry `status=idle/shell` + transcript 부재 + `updatedAt-startedAt ≤ 2000ms` | 1 | `unused` — **stale 창 면제**(mtime이 스폰 시각 고정이므로; 살아있는 한 유지, v8 minor #4) |
    | registry `status=idle/shell` (사용 이력 있음) | 1 | `idle` |
    | Codex exact `task_started` | 2 | `working` |
    | Codex exact `task_complete/turn_aborted` | 2 | `idle` (즉시) |
    | transcript 침묵 > 48h (registry busy/idle이어도) | 3 | `stale` — **하위 tier가 상위를 이기는 유일한 규범 예외**(48h 침묵 세션을 working으로 보이는 것이 더 나쁨; v8 사이클 D1 명문화). unused는 면제 |
    | transcript 활동 < 60s | 3 | `working` |
    | 그 외 | 3 | `idle` |

    **잡** (jobs.log 원어휘 → 표시, OPERATIONS §5.10 status는 불변):

    | jobs.log | 표시 | 비고 |
    |---|---|---|
    | `open` (미기동) | `queued` | 진짜 미기동만 (F-15) |
    | `open` + worktree transcript/rollout 활동 | `working` | 유도값 — `~` 접두 (F-15) |
    | `running` | `working` | |
    | `done` | `done` | |
    | `killed` / `cancelled` | `killed` | cancelled는 어휘 통합, raw는 evidence에 보존 |
    | (liveness 유도) 15min 침묵 / pid 사망 | `stale` / `dead` | dispatch는 `--all` 무관 항상 노출 |
    | exact terminal watchdog/log | `done` / `dead` | heartbeat·PID·mtime보다 우선, 즉시 |

    **hysteresis**: 하향 전이(`working→stale`, `idle→stale`)는 tier-3 유도에만 300초 dwell 적용, 상향(활동 재개)과 `dead/killed/done`은 즉시. tier-1 명시 선언은 dwell로 지연되지 않는다.
  - **플래핑 방지 hysteresis**: 상태 하향 전이(working→idle, idle→stale)는 임계 시간 지속 시에만, 상향 전이(활동 재개)는 즉시. 임계값은 상수 한곳(`model.py`)에 모으고 tick 간 직전 상태를 참조해 경계 진동을 흡수한다.
  - **판정 근거 노출**: `--json`의 각 row에 `state_evidence`(판정 소스·근거 요약) 필드를 additive로 추가 — "왜 이 상태인가"를 기계·사람 모두 검증 가능하게. 관측된 불안정 사례는 픽스처로 고정해 회귀를 막는다.
  - **재배치**: F-15 queued 유도·F-18 상관 dedup·F-24 fd 소유권은 폐기가 아니라 이 분류기의 **입력 계층으로 재배치**된다 — 독립 패치 층으로 남기지 않는다.
- **F-26 (interactive 세션 레지스트리 1급 소스화 — 유령 세션 가시성)**:
  - `~/.claude/sessions/<pid>.json`(pid·session_id·name·status·startedAt·kind)을 fallback에서 **1급 enrichment 계약**으로 승격. Codex/OpenCode의 동형 레지스트리는 실측 후 tolerant 추가(부재 = 기존 경로, 회귀 없음).
  - **이름 fallback 사슬 확장**: fresh sidecar → runtime-native title → **세션 레지스트리 `name`**(예: `agent-setting-17`) → 합성 slug. 이름 없는 익명 행을 제거한다.
  - **`unused` 배지**: transcript 부재 + 시작 이후 무활동(레지스트리 `updatedAt`≈`startedAt`) 세션은 idle과 구분되는 `unused <경과>` 상태로 표시 — 프롬프트가 한 번도 제출되지 않은 유령 세션의 1급 신호(F-27 정리 후보의 기본 대상). **[v8 minor #4, 사용자 결정 2026-07-15]** unused는 stale 창(48h) **면제** — mtime이 스폰 시각에 고정되는 형태라 창 적용 시 F-26의 목적이 자동 무력화됨. 프로세스가 살아있는 한 계속 `unused`로 노출하고, 종료는 존재 축(tier 2 dead)이 담당한다. 면제는 unused 형태 한정 — 사용된 세션의 48h 침묵→stale 순서는 불변.
  - **provenance 태깅(best-effort)**: 부모 프로세스 계보로 출처를 추정해 dim 태그(`herdr`/`terminal`/`vscode`/`worker`)로 표시. 판별 실패 시 조용히 생략(오귀속보다 결손).
- **F-27 (제한적 세션 제어 — Non-goal 반전, 범위=kill+정리만, 사용자 확정 2026-07-15)**:
  - **반전 폭**: kill과 유령/stale 정리만. **attach·resume은 여전히 Non-goal**(herdr·tmux 영역). 자동 제어는 없다 — §0.5 v8 경계 개정 참조.
  - **조작 모델 [v9 개정 — 마우스 1급, 사용자 방향 2026-07-15 "그냥 마우스로 처리"]**: v8의 키보드 선택 모드(s/x 커서)를 사용자가 "별로"로 평가 → 마우스를 1차 경로로 재설계한다.
    - **마우스(1급)**: 행 클릭 = 해당 행 선택(하이라이트, 선택 모드 진입과 동일 상태) → 선택된 행 재클릭 = kill 요청 → 확인 프롬프트의 `[kill]`/`[cancel]` 클릭 타깃으로 확정/취소. 다른 행 클릭 = 선택 이동, 행 밖 클릭 = 해제. 기존 `+N hidden` 클릭 토글과 같은 `_TOGGLE_ROWS`/mouse mask 기제 재사용, tmux `set -g mouse on` opt-in 전제와 §3 트레이드오프(터미널 네이티브 클릭-복사 차단) 불변.
    - **키보드(폴백)**: v8의 `s`/`x` 진입 → `↑↓`/`jk` 이동 → `x` 요청 → `Esc` 해제 경로를 no-mouse 환경·접근성 폴백으로 유지. 확인 프롬프트는 y/n 키 병행.
    - kill 요청 시 대상 요약과 함께 확인 프롬프트. 기본 허용 대상 = `unused`/`stale`/`dead`/idle worker 세션과 registry 잡의 exact pid; `working`/`busy` 세션은 경고 + 이중 확인. (안전 계약·행위 기록·registry 마감은 아래 항 불변.)
  - **안전 계약**: 시그널 전 exact pid + `/proc` start-time 재검증(PID 재사용 방지, F-24·liveness 동형). SIGTERM 기본, 미종료 시 명시 재확인 후 SIGKILL 에스컬레이션. fleet 자신·현재 조작 중인 메인 세션은 대상 제외.
  - **행위 기록**: 모든 제어 행위는 fleet 소유 `action log`(XDG state jsonl, bounded rotation — 제목 sidecar·write-events 저널 동형)에 `ts/action/pid/sid/state/승인 방식`으로 append. 관제 도구가 자기 행위를 스스로 관측 대상으로 남긴다.
  - **registry 마감**: kill 성공한 registry 잡의 row는 `done,note=fleet-kill`로 마감한다 — F-18의 "registry 무write" 불변식에 대한 **명시적 단일 예외**(SD-15 `close_job_row` 동형 경로 재사용, 임의 write 아님).
- **F-28 (분사 정책 연동 관제 — 계약 선고정, 구현 후행, 사용자 확정 2026-07-15)**:
  - **방향**: stage-dispatch PRD v9의 immutable route record + `capabilities/topologies.json` topology registry가 착륙하면, Fleet의 capability/stage/depth/write-scope 표시는 pipe 문자열 휴리스틱이 아니라 **route record를 canonical 소스로 읽는다** — 분사 정책(라우팅 결정)과 관제 UI가 단일 SoT를 공유해 "정책 따로 표시 따로"의 기준 불일치를 구조적으로 제거한다.
  - **소비 계약(v16 evidence 경계가 종전 fallback을 대체)**: dispatch가 pipe/env에 명시 route tuple(`route_file`/`route_id`/`route_hash`/`route_node` 중 하나 이상)을 실으면 fleet은 read-only 파싱·검증한다. tuple이 하나라도 있는데 record가 없거나 파싱·hash·정체성 검증이 실패하면 `unknown`+stable ambiguity로 남기며 pipe/artifact 휴리스틱으로 덮지 않는다. **route tuple 전체가 부재한 legacy 행만** 종전 pipe/artifact fallback을 사용할 수 있다. fleet은 route record를 절대 쓰지 않는다.
  - **추가 관제 표면(소스 착륙 후 단계 적용)**: ① detached resource-runner run registry(장기 GPU/학습 잡) — 세션과 구분되는 resource-runner 행으로 표시, 재부착 상태 노출 ② model-worker-governor lease 현황 — pulse 인접 1행(`⚙ governor <active>/<cap>`, healthy 무음 원칙 적용 가능).
  - **의존·순서**: stage-dispatch v9 구현(topology registry → route compiler)이 선행한다(타 세션 진행 중). v8은 소비 계약만 고정하고, fleet 측 구현은 registry/route record 착륙 후의 별도 phase다. 저널/record 포맷 변경 시 양 spec 동기 의무(F-19 선례).
- **F-29 (native 서브 에이전트 호출 관측 — v8 minor #3, 사용자 확정 2026-07-15)**: 메인/분사 세션 외에 runtime-native 서브 에이전트(Claude Agent 도구, Codex `agents.max_threads`, OpenCode subagent)의 호출 현황을 표시한다.
  - **위상**: 서브 에이전트는 별도 OS 프로세스가 아니므로 proc 백본 비대상 — **enrichment 전용**. 세션 존재 판정에 절대 관여하지 않는다.
  - **소스(하네스별)**: OpenCode = DB `session.parent_id`+`agent` 컬럼(2026-07-15 실측 확인 — 가장 완전, 토큰·비용 포함) / Claude = 세션 transcript의 `isSidechain: true` 라인 + Agent tool_use↔tool_result 짝짓기로 타입·시작·종료 유도(제목/liveness가 이미 읽는 tail 재사용, mtime 키 캐시) / Codex = state DB threads 표면 probe 후 확정 — 확정 전에는 honest 결손(`—`), 추측 표시 금지.
  - **표시**: 세션 행 아래 `└⚡<agent-type> ⏳<경과>` 서브 행 — 분사 잡 `└▸🚀`와 글리프로 구분. 완료분은 기본 숨김, 활성만 표시 + 세션 행에 `⚡N` 카운트 배지, `a` 토글 시 최근 완료분 dim 노출. fleet pulse의 세션/잡 카운트에 혼입 금지(F-18 계열 — 별도 집계). **[v11 대체 — 아래 표시 개정이 현행]**
  - **표시 개정(v11, 사용자 확정 2026-07-16 — 두-평면 실험 채택분 이식)**: 서브에이전트당 1행 스택+`⚡N` 배지 계약을 **소유 행당 가로 스트립 1행**으로 대체 — `⚡<type> <●|✓>  <경과> · <type> …` (활성=normal·상시 표시, 완료=dim·`a` 토글 시만; ⚡는 첫 라벨 밀착, 경과는 2칸 분리 상시 dim — "번개랑 텍스트 사이 간격도 크고, 경과 시간도 띄워"). 인셋 = 순수 공백(커넥터 없음): 세션 소유 6칸, 분사 소유 행은 depth당 +2(8/10) — "들여쓰기 레벨을 충분히 안쪽으로", 스트립이 항상 자기 소유 행의 자식으로 읽히게. **분사 자식 세션의 서브에이전트도** 그 자식을 대표하는 dispatch 행 아래 같은 스트립으로 재부착(pid 조인 — "서브 세션에 서브 에이전트도"). `⚡N` 배지 폐기(스트립이 인라인 카운트를 이미 보임).
  - **수집 개정(v11 — 라이브 0건 결함 2종 수리)**: ① tool_use name 매칭 `"Task"` 단독 → `("Task","Agent")` — 현행 런타임은 `Agent`로 기록해 수정 전 라이브에서 항상 0건이었다(구 transcript 호환 유지). ② **비동기 발사 확인 ≠ 완료**: 배경 Agent 발사는 tool_use에 즉시 launch ack(`Async agent launched … agentId: <id>`)가 달리므로 단순 tool_use↔tool_result 페어링은 모든 비동기 에이전트를 발사 순간 완료로 오독(활성 ●가 절대 안 보임) — ack는 완료로 치지 않고 같은 id의 `<task-notification>` 정지 알림이 transcript에 나타나야 완료. id 미파싱 ack는 기존 페어링 폴백(영구 활성 방지).
  - **불변식**: zero-injection(read-only) 유지, `--json` additive(신규 `subagents` 키), 소스 부재·파싱 실패 = 서브 행 생략(회귀 없음).
  - **구현**: v8 사이클(`fleet-v8-reliability`) 수확 완료 → **v9 구현 사이클 스코프에 편입** → v11 표시·수집 개정은 `plans/2026-07-16_fleet-mem-subagent/` + main 직접 후속(2026-07-16 저녁 연쇄 피드백).
- **F-30 (종착 비전 — dispatch·서브에이전트 처리 과정 시각화, 사용자 방향 2026-07-15)**: "이후에 내가 진짜 원하는 건 dispatch 구조 및 서브에이전트 구조의 **처리 과정을 시각화**해서 보는 것." 행 나열이 아니라 오케스트레이션의 흐름 — conductor→stage 전이, 부모→서브에이전트 fan-out, 파이프라인 진행 — 을 과정으로 보이게 한다. 이 비전이 F-28(capability별 실제 topology DAG의 canonical 소비)·F-29(서브에이전트 관측)의 우선순위 근거다.

## 4.9 [v10 신설] 처리-과정 시각화 — F-28 구현 확정 + F-30 뷰 설계

> 현행 계약(v14, 2026-07-22): topology registry `capabilities/topologies.json`은 schema v3이며 portable unit catalog를 참조한다. immutable route record는 route schema v2·dispatch contract v3을 유지하고 top-level `unit_catalog_digest`, optional `composed`, `nodes[].unit`/`unit_choices`를 sealed hash에 포함한다. jobs.log pipe는 `route_file=/route_id=/route_hash=/unit=`로 링크하며, topology schema와 route schema를 같은 버전으로 오인하지 않는다.

- **F-28a (route record 소비 — v16 evidence 경계 개정)**: dispatch collector가 pipe/env의 `route_file`/`route_id`/`route_hash`/`route_node`를 read-only 로드하고 검증한다. **route tuple이 완전히 부재한 legacy 행**은 기존 pipe/artifact fallback을 사용할 수 있다. 반면 명시 route tuple이 하나라도 있는데 record 부재·파싱 실패·hash/정체성 불일치가 나면 `unknown`+기계 판독 가능 ambiguity로 남고 artifact 유도로 덮지 않는다. 검증된 record+정확 entity tuple만 topology/progress/node state/gate를 주장할 수 있고, record 없는 jobs.log/env exact evidence는 관측된 identity 필드만 보존한다. `--json route`는 `unit_catalog_digest`, `composed`, 각 node의 `unit`/`unit_choices`를 additive로 보존하며 구 record/row의 필드 부재는 정상이다.
- **F-28b (route-aware breadcrumb)**: conductor·stage 행의 stage breadcrumb을 고정 `_PIPE_STAGES` 하드코딩 대신 **record의 `nodes[].id` + `depends_on` DAG**에서 생성 — 임의 capability 파이프(lab eval, research 등)가 code 4단 강제 없이 자기 모양대로 표시된다. 노드 점등 = 해당 depth-2 자식 행 실측 우선(SD-F2 원칙 불변). 기존 breadcrumb은 route tuple이 완전히 부재한 legacy 잡에서만 유지하고, 명시 tuple이 하나라도 있으나 record가 부재·무효·불일치하면 unknown/ambiguity를 표시한다.
- **F-30 (처리-과정 뷰 — 전용 모드, 설계 확정)**:
  - **진입**: 전용 키 `p`(process) 토글 — 기존 `w` 레이아웃 cycle과 직교(그룹 뷰 ↔ 과정 뷰 전환). footer 키 바에 표기. 비대화식 투영 = `--view {group,process}` CLI 플래그 + `FLEET_VIEW` env — `p` 토글과 같은 전역 상태 하나를 공유하며 별도 코드 경로를 만들지 않는다(v10 구현이 3폭 캡처·디자인 비평 등 비대화식 검증용으로 추가, 2026-07-16 사용자 확정 minor).
  - **단위**: 카드 1장 = 활성 route 1개 (프로젝트 그룹 대신 파이프라인 중심 재그룹).
  - **카드 구성**: L1 = `[capability·mode·intensity] <route_id 단축> — <n/m nodes> ⏳<경과>`; L2 = DAG 가로 흐름 `plan ✓12m › exec ● 8m (opus·high) › test ○ › report ○` — 노드별 상태 글리프(✓ 완료 / ● 활성+경과+모델 / ○ 미기동 / ✕ 실패)와 completion gate 통과 여부. `depends_on`이 병렬인 노드는 세로 분기(들여쓴 병렬 행)로.
  - **gate 통과 증거 소스 (2026-07-16 확정, v10 minor #2 — 재개 조건 충족)**: v10 구현은 통과 증거 부재로 정직 결손(`—`) 처리했다(carryover §1). stage-dispatch v13(SD-56)이 canonical marker `.dispatch/<agent-home 기준>/completion/<route_id>/<node_id>.json`을 실사용으로 착륙시켜 재개 조건이 충족됐다. 판정 규칙: **marker 존재 + record의 route_id/route_hash 일치 = 통과**(별도 gate 표식, 상태 글리프와 독립 차원). marker 부재 = "무주장"(실패·미통과로 표시 금지, F-28 tolerant 원칙 불변). read-only, mtime 캐시, 이력 파일 중 최신만 authoritative.
  - **자식 연결**: 활성 노드 아래 그 노드를 실행 중인 세션 행(축약형)과 그 서브에이전트 `└⚡`(F-29 재사용)를 중첩 — "누가 지금 어느 단계를 어떤 모델로" 한눈에.
  - **마우스**: 노드/카드 클릭 = 접기·펼치기, 세션 축약행 클릭 = 선택(F-27 문법 재사용). 완료 route는 기본 1행 접힘, 실패 노드 포함 route는 자동 펼침 + 적색 강조.
  - **결손 원칙 불변**: route tuple이 완전히 부재한 legacy 잡만 과정 뷰에서 pipe 휴리스틱 요약 카드로 degrade한다(빈칸 아님). 명시 tuple이 하나라도 있으나 record를 검증하지 못하면 heuristic 카드로 대체하지 않고 unknown/ambiguity를 표시한다. `tracked_gate_evidence`는 `a` 토글 상세에서만 dim 노출한다.
- **F-28c (detached run·governor lease — 조건부)**: run registry·governor lease 소스는 이번 착륙 범위에 없을 수 있다 — 구현 사이클이 소스 실재를 probe하고, 부재 시 정직하게 스킵(스코프 이월 기록). 실재 시 pulse 인접 1행(`⚙ governor n/cap`)과 resource-runner 행을 v8 계약대로 표시.
- **F-31 (분사 세션 rolling 요약 관측 — v10 minor #4, 사용자 확정 2026-07-16)**: 실행 중 분사 세션마다 "지금 무엇을 하는 중"인지 1~2줄 rolling 요약을 유지해 세션 행 아래 dim 서브 행(및 과정 뷰 활성 노드 카드)에 노출한다 — F-30이 상태(글리프·DAG)를 보여준다면 F-31은 내용을 보완한다.
  - **소스**: 세션 transcript jsonl delta(F-29·제목 tail과 같은 read-only 관용구; codex/opencode는 각 adapter 로그·DB). `claude -p` stdout 로그는 메시지 경계에서만 갱신되므로 소스로 쓰지 않는다(실측 2026-07-16).
  - **구조(§0.5 결정론 분리)**: watcher 코드 = 관측 대상 발견(jobs.log attempt identity)–delta cursor(마지막 처리 uuid, distill 공유 marker 관용구)–케이던스(N초/K events, delta 없으면 무발화)–governor 등록(v18 storm containment: global slot·rolling budget·kill switch)–피드 append(JSONL: ts/slug/attempt_id/summary/cursor). 모델 = cheap-tier **no-tools** 요약 워커: delta 텍스트를 프롬프트 데이터로 주입(D-14 관용구 — 출력은 명령이 아니라 데이터), 1~2줄 요약 JSON만 stdout.
  - **불변식**: 요약은 표시 전용 — liveness·상태 분류에 절대 불개입(F-25·SD-58 단일 분류 소스 원칙), zero-injection(실행 세션 개입 없음), `--json` additive(`summaries` 키), summarizer 자신은 관측·재귀 대상 제외, 피드 부재·파싱 실패 = 서브 행 생략(F-28 tolerant). 비용 상한(케이던스·delta 크기 cap·요약 길이 cap)은 구현이 수치로 확정하고 실측 기록.
  - **구현**: 별도 autopilot-code 사이클(watcher 유틸 + render 소비). 완료 기준 = 실사이클 1개에서 이벤트→표시 지연과 토큰 비용 실측.
  - **(v11 참고)**: F-32의 분사 행 제목 입양이 "지금 무엇을 하는 중"의 거친 1급 표시(10분 디바운스 haiku 제목)를 이미 제공한다 — F-31 rolling 요약은 그 정밀·연속(케이던스 단위) 버전으로 여전히 별도 사이클.
  - **(v11 minor #1로 대체, 2026-07-19)**: 본 항목의 watcher·커서·피드·전용 케이던스 설계는 **구현하지 않는다** — 사용자 결정으로 F-17 제목 refresher의 한 호출 두 출력(제목 압축 + NOW 부제, §4.7 F-17 v11 minor #1)이 이 문제의식을 흡수했다. 잔여 격차(30초급 케이던스·다문장 실황)는 장수명 세션이 흔해져 실수요가 생길 때 재개 조건으로만 남긴다.

## 4.10 [v11 신설] 기존-보드 강화 — 두-평면 폐기 후 채택분 + 분사 요약 1급화 — F-32~F-34

> 배경(2026-07-16): F-30 방향의 "두-평면 문법" 가안(브랜치 `fleet-two-plane-demo`, 13라운드 반복)을 사용자가 폐기 — "결국 기존과 비교해서 뭐가 나아진건데 … 그냥 전부 다 버리고, 메모리 쪽과 서브 에이전트 쪽만 기존의 fleet에 붙이는 방향으로 가자". 채택분 2건(서브에이전트 가로 스트립·레포별 mem 카드 행)은 F-29/F-19 v11 개정으로 흡수, 나머지 확정 3건이 본 절. 가안 브랜치는 결정 기록으로 보존(머지 금지). 본 절 전체가 **구현 선행·등재 후행**(사용자 명시 이연) — 코드·테스트 실측 기준 소급 등재이며, 표시 좌표(인셋 6/8/10, prefix (depth+1)*2 등)의 단일 진실은 코드 상수다(spec은 의도·관계만 고정).

- **F-32 (분사 세션 요약·정체 1급화 — 제목 입양, 사용자 확정 2026-07-16 "지금은 메인 세션만 요약 에이전트가 붙는데 모든 분사 세션에 다 해당되게")**: 스케줄 절반은 F-17 v11 개정(분사 자식 포함) — 표시 절반이 본 항목. dispatch 행 이름 = **title→slug→key 체인**(세션 행의 title→name→slug와 동형): enrich가 이미 해석한 자식 세션의 fresh sidecar 제목을 그 자식을 대표하는 잡 행으로 입양한다. **v16부터 title만의 옛 `pid` 조인은 폐기하고 F-37b의 단일 association을 사용한다**: exact `(pid,proc_start)` → exact identity 부재 시 단 하나의 `(harness,realpath(cwd))` 후보이며 PID reuse·중복 PID·cross-harness·cwd 2+ 후보는 title/NOW/context 전체를 거부한다(F-26 — 오귀속이 부재보다 나쁘다). `DispatchJob.title` additive(None=기존 slug 정체성 그대로), 추가 IO 0(세션 enrich 결과 재사용), cross-harness. 이름 존 예산·클립은 유지하고 stage는 F-36 공통 projection만 사용한다.
- **F-33 (harness 필드 model·effort 통합; v16 ctx 게이지 확장 철회)**: WIDE 레이아웃의 별도 model 컬럼(`_MW`)을 폐지하고 harness 필드를 `claude code (Fable 5·xhigh)` 문법으로 표시하는 계약은 유지한다. harness/model/effort 색·플러시 `·`·`_HMW`·dead/stale bare harness·effort 평문 fallback·dispatch prefix 정렬도 불변이다. 다만 **"잔여 slack을 wide 주 행 ctx gauge가 흡수"하는 기존 계약은 사용자 승인 v16으로 폐기**한다. ctx는 wide 주 행·narrow/stack inline telemetry에서 제거하고 F-37의 모든 레이아웃 공통 subordinate line으로 이동하며, 이로써 생긴 주 행 폭은 F-36 공통 stage/progress zone이 사용한다.
- **F-34 (표시 문법 정리 — qa·`~` 표시 폐기 + 분사 ↳ 사다리, 사용자 연쇄 확정 2026-07-16)**: ① **qa 표시 폐기** — qa 축 폐기(CONVENTIONS §1.1)를 표시층에 반영: options 다이얼 = mode·intensity/role만, `qa:` 토큰과 rigor 색 사용처 제거(F-9(c) 드롭 우선순위는 intensity→role로 개정, F-15 R3의 qa 표시 계약 폐기). `--json`의 qa 데이터 필드는 불변(표시만 폐기). ② **`~` 파생값 마커 폐기** — "물결로 예측 표시하는 건 안 하면 안 되나": 상속 effort 등 유도값은 평문 표시, legend의 `~ derived/inherited value` 항목 제거(F-9(d) 폐기). ③ **분사 ↳ 사다리** — 모든 depth가 같은 ↳ 분사 화살표를 depth당 2칸씩 깊게(indent-only depth-2 표시 폐기, "depth=2 화살표는 없네"), 사다리 전체가 한 레벨 안에서 시작(prefix 폭 (depth+1)*2 — "분사 세션의 화살표를 좀 더 들여쓰자", depth-1 화살표가 부모 세션의 글리프 열이 아니라 텍스트 아래에 앉는다). 정렬은 harness 셀이 흡수(F-33 규칙).

## 4.11 [v14 신설] portable unit·compositional route 관측 — F-35

- **F-35a (축 분리)**: `assigned_contract`, `unit`, `worker_type`, `model_role`을 서로 대체 불가능한 축으로 보존한다. `worker_role`은 legacy-only이며 표시와 JSON에서 authoritative 축보다 우선하지 않는다.
- **F-35b (dispatch 전달)**: Claude/Codex/OpenCode wrapper는 선택된 unit을 jobs.log `unit=`과 `AGENT_DISPATCH_UNIT`에 additive로 전달한다. unit이 없는 owner/direct/legacy 행은 필드를 생략한다.
- **F-35c (Fleet 소비·표시)**: collector/model/route projection은 unit을 손실 없이 운반한다. group options와 process route node는 contract/단계 라벨을 1차로 유지하면서 unit을 compact 보조 라벨로 표시한다. route summary/JSON은 `unit_catalog_digest`, `composed`, node unit metadata를 보존한다.
- **F-35d (composed route)**: topology registry schema v3에서 unit catalog를 조합해 만든 route도 route schema v2·dispatch contract v3·sealed hash 검증을 그대로 따른다. Fleet은 catalog를 재컴파일하거나 digest를 추론하지 않고 record를 read-only projection한다.
- **F-35e (runtime surface 경계)**: Codex native subagent thread, stable `codex exec` non-interactive worker, Claude subagent/background session/agent-team teammate/non-interactive `-p`는 서로 다른 표면이다. Fleet의 `/proc`+jobs.log 백본과 passive enrichment는 이를 합성 identity로 섞지 않는다. `claude agents --json` agent-view 통합은 문서화된 잔여 확장으로 두며 이번 변경은 unit을 native agent type에서 추론하지 않는다.
- **F-35f (memory 호환)**: memory write-event journal의 `cwd`/action/path 계약은 unit migration과 독립이며 기존 collector가 그대로 소비한다. sync/migrate 흡수는 신규 레코드를 실제 persist한 때에만 `action=add`·literal `actor=sync`와 원천의 논리 프로젝트 `cwd`를 방출한다(global/decode 불가 원천은 `cwd` 생략). 신규 레코드가 없는 반복은 이벤트 0건이며 historical journal backfill은 하지 않는다. 현행 journal에 `cwd`가 없다는 오래된 주석만 정정한다.

## 4.12 [v16 신설] 공통 work projection·context subordinate line·title budget — F-36~F-39

> **목표**: interactive 메인 세션과 registered dispatch 잡을 서로 다른 stage 판정기로 그리지 않는다. 동일한 read-only evidence를 단 하나의 `WorkProjection`으로 정규화하고 group/process/plain/JSON 표면은 이 결과만 소비한다. 오귀속보다 부재가 낫고, context pressure는 intensity와 직교한다.

- **F-36a (공통 stage/progress projection)**: `Session`과 `DispatchJob`은 additive `work_projection`을 공유한다. 정규형은 `source`(`route-exact|registry-exact|artifact-inferred|none`), `route_id`, `route_hash`, `route_node`, `attempt_id`, `assigned_contract`, `unit`, `stage_label`, `node_state`(`active|done|failed|pending|unknown`), `active_nodes[]`, `progress{done,total}`, `ambiguity[]`를 운반한다. leaf는 정확히 한 `route_node`를, owner/conductor는 같은 route의 0개 이상 병렬 `active_nodes[]`를 표현한다. `projection.py`가 source-agnostic 단일 resolver를 소유하고 render/`--once`/`--json`은 `live_stage()`를 별도로 호출해 stage를 재판정하지 않는다.
- **F-36b (evidence 우선순위·모호성 거부)**:
  1. hash 검증된 immutable route record + 동일 entity의 명시 `route_id/route_node/attempt_id`;
  2. jobs.log 또는 process env의 명시 route/node evidence를 exact `(pid,proc_start)`로 결합;
  3. exact identity가 없고 단 하나의 후보만 남은 `(harness,realpath(cwd))` registered-row 결합;
  4. route evidence가 **완전히 없는** legacy 행의 artifact stage 유도.

  검증된 record+exact tuple만 topology·progress·node state·gate passage를 채운다. record 없는 jobs.log/env exact evidence는 관측된 identity를 `source=registry-exact`로 보존하지만 validated topology/progress/gate/node completion을 만들지 않는다. 명시 tuple이 record와 충돌·무효하거나 leaf에 서로 다른 route/node 후보가 2개 이상이면 `unknown`으로 남고 artifact로 덮지 않는다. stable ambiguity code는 최소 `route-record-mismatch`, `multiple-leaf-candidates`, `multiple-child-cwd-candidates`, `multiple-artifact-plan-dirs`를 사용한다. 단, 같은 검증 route의 병렬 active sibling은 모호성이 아니라 `active_nodes[]`로 모두 보존한다.
- **F-36c (임의 composed DAG)**: commit `e8938809`의 compose-on-demand route는 기존 route schema v2·dispatch contract v3·sealed hash를 그대로 사용하고 arbitrary `nodes[].id`, `unit`, `depends_on`, `completion_gate`, `write_scope`를 제공한다. Fleet은 node ID를 opaque label로, `depends_on`을 유일한 순서/분기 근거로 취급하여 record 순서의 topological level·parallel branch·fan-in·모든 active sibling을 그린다. `plan/exec/test/report`나 3단 고정 stage 하드코딩은 route tuple이 완전히 부재한 legacy fallback에서만 허용하고, Fleet은 catalog를 재조립하거나 node 이름에서 capability/stage를 추론하지 않는다.
- **F-36d (artifact fallback 경계)**: artifact 유도는 route tuple이 전혀 없고 exact plan-dir 후보가 하나일 때만 `source=artifact-inferred`로 `stage_label`만 채운다. `route_id`, `route_node`, progress, gate, node 완료를 절대 합성하지 않는다. 후보가 0개면 `source=none`, 2개 이상이면 `source=none`+`multiple-artifact-plan-dirs`로 남고, fuzzy "최선" 후보를 임의 선택하지 않는다.

- **F-37a (정확히 한 개의 context detail row)**: wide 주 행의 확장 ctx gauge, narrow/stack inline ctx telemetry, wide-only NOW 행을 이 계약이 대체한다. live session/dispatch 정체성 카드 직후·sub-agent strip 전에 depth inset을 맞춘 subordinate line 하나를 wide/narrow/stack 모두에 표시한다. 문법은 context가 fresh NOW **직전**에 오는 `ctx <NN%|—> [normal|tight|critical] [· <fresh NOW>]`이다. truth table:
  - live context+NOW → `ctx 63% normal · <NOW>`;
  - live context, NOW 부재 → `ctx 63% normal`(구분자 없음);
  - live context 부재, NOW 있음 → `ctx — · <NOW>`;
  - live 둘 다 부재 → `ctx —`;
  - stale/dead → cached context/NOW와 무관하게 detail row 전체 생략.

  렌더러는 ctx token을 먼저 예약하고 남은 폭에서 NOW만 display-cell/CJK 안전 tail-clip한다. NOW 부재는 row 부재가 아니라 context-only로 정직하게 표시한다.
- **F-37b (분사 자식 통합 association)**: title, NOW, context를 각기 다른 조인으로 가져오지 않고 하나의 child-session association이 세 값을 함께 공급한다. exact `(pid,proc_start)`를 우선하고, exact identity가 없을 때만 단 하나의 `(harness,realpath(cwd))` child 후보로 fallback한다. PID reuse, 중복 PID, cwd 후보 2개 이상, cross-harness 매칭은 세 값 전체를 거부하고 ambiguity를 남긴다. dispatch context는 해당 child runtime session의 normalized telemetry만 사용하며 부모 context 상속은 금지한다. `DispatchJob`/JSON의 child `context{used_pct,band,source}`는 additive이고 구 필드 의미를 바꾸지 않는다.

- **F-38 (context pressure ⊥ intensity)**: context band는 `unknown|normal|tight|critical`(`tight>=70`, `critical>=85`)의 관측·표시 신호다. band 변화는 title/NOW 표시 외의 route/node state, intensity, stage graph, dispatch depth, model role/effort, QA/reviewer budget, test/verification, retry, completion gate, safety·permission guard, definition of done을 변경하지 않는다. parent/child는 각자 denominator를 사용하고 missing/stale/malformed/source-sequence-regressed telemetry는 `unknown`으로 강등한다. 정상적 compaction으로 인한 수치 하락 자체는 무효 근거가 아니다.

- **F-39 (보수적 title/NOW worker 상향 — 현행 단일 진실)**: shared scheduler의 default concurrency는 `3`, hard max는 `4`; rolling start budget은 default/hard max 모두 `4 starts / 60s`; main debounce는 `600s`, child debounce는 `150s`다. main/child·default/custom provider는 같은 cross-process slot/start pool, per-session lock, stale-lease 회수, `FLEET_TITLE_DISABLE`+상태 파일 kill switch, fail-closed lock 계약을 공유한다. Fleet은 default Haiku provider의 도구 전면 차단과 `FLEET_TITLE_COMMAND` shell-free argv template/`FLEET_TITLE_MODEL` 교체 표면을 보장한다. 커스텀 wrapper의 no-tools 속성은 Fleet이 내부를 검증할 수 없으므로 wrapper 소유자가 강제한다. vendor를 hard-pin하지 않고 Haiku는 default일 뿐이다. `--json`/`--once`/demo/test는 provider process를 시작하지 않는다.

### v16 acceptance matrix

| 표면 | 필수 픽스처·언단 |
|---|---|
| wide/narrow/stack 및 overflow | `wide@168`, `wide@120`, `narrow@100`, `stack@60`에서 identity → `ctx … [· NOW]` → sub-agent strip 순서, CJK-safe clip, 행 폭 `<= terminal width`; NOW 부재, ctx 부재, 둘 다 부재, stale, dead 픽스처를 각각 고정한다. |
| child 정체성 | `(pid,proc_start)` exact 조인이 title/NOW/context를 함께 복사하고 부모/자식 서로 다른 ctx가 상속 금지를 증명한다. PID reuse·중복 PID·cwd 2후보·cross-harness는 세 값 전체를 보류한다. |
| projection parity | 같은 exact route/node evidence를 interactive `Session`과 registered `DispatchJob`으로 각각 입력해 normalized route/node/state/progress가 동일함을 증명하고, group/process/plain/JSON이 공통 projection만 소비함을 검사한다. |
| exact-over-artifact | exact `route_node=research`와 artifact `test` 충돌 시 exact가 이긴다. explicit tuple 무효+그럴듯한 plan-dir은 unknown/ambiguity이지 artifact fallback이 아니다. |
| artifact-only 경계 | plan-dir 정확히 1개는 `artifact-inferred`+`stage_label`만, 0개는 `none`, 2개 이상은 `none`+ambiguity. 모든 artifact 경로에서 route/node/progress/gate/completion은 부재한다. |
| composed DAG | sealed `survey -> {claim-a,claim-b} -> synth`와 기존 lab fork/fan-in 픽스처에서 arbitrary ID/unit/gate/scope, 병렬 active sibling, record-order level, progress를 보존하고 `_PIPE_STAGES`를 노출하지 않는다. |
| ambiguity refusal | 한 leaf의 서로 다른 route/node 2개, cwd 2후보, gate auto-derive 복수 후보를 모두 fail closed한다. 같은 validated route의 parallel sibling은 ambiguity가 아니라 모두 표시한다. |
| JSON additive | 기존 `sessions`, `jobs`, `summary`, `route`와 하위 필드 의미를 유지하고 `work_projection`·child `context`만 additive로 추가한다. old-key-only consumer도 통과한다. |
| context 직교성 | 69/70/85%에서 band/render만 변하고 route graph·node state·intensity·model/effort·QA·test·gate·guard는 byte-equivalent. 숫자 하락 자체는 허용하되 source-sequence regression은 unknown이다. |
| title quota hermetic | fake clock+격리 state root+200-session backlog에서 default concurrent 3, hard 4, rolling 60s starts 4를 증명하고 5번째 start를 거부하며 창 경과 후 재개한다. direct `run_worker()`도 lease를 우회하지 못한다. |
| no live provider | `subprocess.Popen`과 provider `subprocess.run`을 모두 fail-if-reached로 바꾸고 snapshot/demo/width/projection/storm 테스트를 실행해 default/custom/live provider 호출 0회를 증명한다. default tool denial·shell-free argv 테스트도 유지한다. |
| mirror parity | canonical Fleet↔Claude mirror 바이트/의미 parity와 public JSON smoke를 구현 완료 게이트에 포함한다. |

## 5. 능동 변경 — fleet-owned local state write

현재 `statusline.sh:10` 이 **모든 세션을 `~/.claude/.statusline-last.json` 한 파일에 덮어씀**(last-writer-wins) → 멀티세션 대시보드가 세션별 telemetry 를 못 얻음. 해결:

- statusLine 실행 시 stdin JSON 을 **세션별 파일**로도 dump: `~/.claude/.statusline/<session_id>.json`(디렉토리 신설). 기존 `.statusline-last.json` 단일 파일은 하위호환으로 유지.
- **stale 청소**: 대시보드 또는 statusline 이 오래된(예: mtime > 1일) 세션 파일 정리(디렉토리 폭증 방지). 또는 SessionEnd hook 이 해당 파일 삭제.
- 구현 위치 후보: (a) `statusline.sh` 에 `<session_id>.json` 추가 write 한 줄(가장 간단, 60s 주기라 최신성 충분), (b) SessionStart/UserPromptSubmit/Stop hook — 단 hook stdin 엔 telemetry 없음(§01_tap 1b), 그래서 **(a) statusline.sh 확장이 정답**. 결정: **(a)**.
- 하위호환·drift: statusline.sh 은 이 repo 소유 파일이라 변경이 곧 배포(심링크). 세션별 파일 추가는 기존 렌더 무영향.
- F-17/F-21 제목 sidecar도 fleet-owned local state다. Claude statusline과 live fleet scheduler는 같은 neutral title state/lock을 사용하며 하네스 transcript·DB를 수정하지 않는다.

## 6. 알려진 버그 동시 정리 (scope 포함)

`.dispatch/jobs.log` 실제 status 어휘 = `running`/`done`/`killed`/`cancelled`(`open` 0개)인데, `harness-status.sh:209`·`utilities/dispatch-liveness.sh:19` 는 `$2=="open"` 만 필터 → **현재 라이브 파일에 매칭 0**(Claude 수동 write 가 `open` 대신 `running` 을 씀).

- **대시보드 측**: live 판정에 `{open, running}` 둘 다 수용. malformed 행(field ≠ 6, `worktree`=`-`/`(main-tree)`) tolerant — skip 하되 카운트만.
- **동반 수정(권고, autopilot-code 가 판단)**: `harness-status.sh`·`dispatch-liveness.sh`·`dispatch-liveness.py`(codex/opencode) 의 `open` 필터를 `{open,running}` 으로 통일하거나, 쓰기 측(Claude 수동 append 규약)을 `open` 으로 통일. **canonical 은 `core/OPERATIONS.md:95`** — 어휘 단일화는 그 문서 갱신과 함께(대응 동기화). 대시보드 자체는 어느 쪽이든 tolerant 하게 읽어 회귀 안전.
- **[v2 추가] pipe 구분자 wild drift**: 2026-07-09 실측 — 콤마 canonical 인데 공백 구분 `key=value` 행이 레지스트리에 실존(현행 파서 오파싱). 표시층이 아니라 collector tolerance 로 흡수 = §4.5 SD-F4.

## 7. Liveness 모델 (재사용)

기존 3 스크립트 로직 재사용(15min stale 창):
- claude/codex = transcript(또는 rollout) mtime; opencode = DB `MAX(time_updated)`. `age ≤ 15min` → live, 초과 → `stale`, 없음 → `dead`.
- 추가 신호: pid `kill -0`(프로세스 생존), cwd symlink `(deleted)` 접미사 = orphan(worktree 지워짐), claude `sessions/<pid>.json.status`(idle/shell/busy).
- 4-상태(herdr) 매핑: `busy`/최근 write=working, `idle`=idle, (blocked 은 herdr 소켓 있을 때만 — 스코프 밖), stale/dead 는 별도.

## 8. herdr 계약 재사용 (채택 X)

`herdr`(github.com/ogulcancelik/herdr, Rust 멀티플렉서, ~9.1k★, AGPL 듀얼)은 **채택 안 함** — 터미널을 소유하는 멀티플렉서라 "zero-injection 관찰자" 목표와 상충하고 우리 dispatch(jobs.log)를 모름(00_prior_art.md).

- **재사용하는 것**: 4-상태 어휘(idle/working/blocked/done) — 세션 상태 표준으로. 이 repo 가 이미 가진 emitter(`hooks/herdr-agent-state.sh`)·liveness(`dispatch-liveness.*`).
- **옵션(스코프 밖, 후순위)**: `HERDR_ENV=1` 로 herdr 소켓이 떠 있으면 대시보드가 그 소켓의 push 상태를 _옵션 소스_ 로 구독(blocked 상태를 정확히 얻는 유일 경로). MVP 는 미포함.

## 9. Module 구조 (확정 — 코드 생성은 autopilot-code)

```
tools/fleet/
  fleet.py          # 진입 — 인자 파싱, curses 루프 or --once/--json/--demo
  collectors/
    __init__.py     # collect_all() → [Session...] (백본 프로세스 스캔 + 하네스별 enrich 디스패치)
    procscan.py     # comm ∈ {claude,codex,opencode} + /proc/cwd + etime + environ 마커 태깅(F-18b)
    claude.py       # ~/.claude/.statusline/<sid>.json + sessions/<pid>.json + ai-title/shared sidecar
    codex.py        # rollout token_count + config.toml + state DB title/JSONL fallback/shared sidecar
    opencode.py     # opencode.db session row (sqlite3 ro)
    dispatch.py     # statusline 잡스캔 로직 포팅(uncapped) + jobs.log 병합 + SD-F4 tolerant 파싱
    liveness.py     # 15min stale + kill -0 + (deleted) orphan → 4-state
    memory.py       # (v3/F-19) write-events 저널 + graveyard tail read-only 관찰
    usage_api.py    # (v2 F-1 확장) 하네스 계정 usage API read-only
  projection.py     # (v16/F-36) Session/DispatchJob evidence → 공통 WorkProjection 단일 resolver
  render.py         # WorkProjection 소비 curses 레이아웃(공통 stage zone + ctx/NOW detail + mem 패널)
  model.py          # Session/DispatchJob/WorkProjection dataclass + (v8/F-25) 단일 상태 분류기·state_evidence
  control.py        # (v8/F-27) verify_target/kill_target/close_registry_row + action log
  titles.py         # (v5/F-21) neutral <harness>/<sid> sidecar + Claude legacy fallback
  refresh_title.py  # (v5/F-21) cross-harness transcript parser + pluggable no-tools title provider/scheduler
  demo.py           # --demo/FLEET_DEMO fixture 병합 (§3)
  tests/            # unittest 스위트 (mirror-parity 가드 포함)
  fleet.sh          # 런처 (v2: full-terminal 기본, --window 시 tmux 새 창) → fleet.py
```
- 의존성: python3 표준 라이브러리만(`curses`,`sqlite3`,`json`,`os`,`subprocess`,`re`,`time`). 외부 pip 0.
- 설치: `~/.claude/tools/fleet/` 심링크(statusline.sh 선례). 실행 = `bash ~/.claude/tools/fleet/fleet.sh` 또는 alias.

## 10. Component diagram

```mermaid
flowchart TD
    subgraph SOURCES[디스크·프로세스 관찰 소스 · read-only]
      PS[ps / /proc/cwd/etime]
      CJ["~/.claude/.statusline/&lt;sid&gt;.json<br/>sessions/&lt;pid&gt;.json"]
      CX["~/.codex/sessions/**/rollout-*.jsonl<br/>state_*.sqlite(ro) · session_index.jsonl · config.toml"]
      OC["opencode.db (ro)"]
      JL["~/.claude/.dispatch/jobs.log"]
    end
    PS --> PROC[procscan.py]
    PROC --> COL[collectors.collect_all]
    CJ --> CL[claude.py] --> COL
    CX --> CXP[codex.py] --> COL
    OC --> OCP[opencode.py] --> COL
    PS --> DP[dispatch.py]
    JL --> DP --> COL
    COL --> LV[liveness.py] --> COL
    COL --> M[model.Session/DispatchJob]
    M --> WP["projection.py<br/>WorkProjection 단일 resolver"]
    WP --> R[render.py · group/process/plain]
    WP --> J["--json additive<br/>work_projection · child context"]
    R --> TUI[fleet TUI]
    SH[fleet.sh · tmux side pane] -.launch.-> TUI
    SL["statusline.sh (능동 변경 §5)"] -.writes.-> CJ
    COL -.live only schedule.-> TW["shared title provider<br/>Haiku default / custom command"]
    TW -.writes fleet state.-> TS["XDG agent-fleet/titles/&lt;harness&gt;/&lt;sid&gt;.json"]
    TS --> CL
    TS --> CXP
    TUI -.사용자 개시 kill · F-27.-> CTL["control.py — 유일한 signal/write 예외 (§0.5 v8 경계)"]
    CTL -.action log.-> AL["XDG agent-fleet/actions jsonl"]
    CTL -."done,note=fleet-kill row 마감".-> JL
```

## 11. MVP 경계

**MVP(이번 사이클)**: (A) fleet 세로 스택 + (B) dispatch uncapped 리스트 + 1~2초 tick 라이브 갱신 + §5 per-session tap + §6 jobs.log tolerant 읽기. 하네스 3종 collector + liveness 4-state. `--once`/`--json`(테스트용).

**후순위 (스코프 밖 — 명시)**:
- 시계열 sparkline(context%·usage 히스토리 — nvtop 그래프).
- herdr 소켓 구독(blocked 정확화, §8).
- 색·정렬·필터 커스터마이즈, 2열 그리드 승격.
- §6 동반 스크립트 수정(대시보드 tolerant 읽기로 회귀 없음 — 별도 결정).

## Non-goals

- 하네스 TUI·hook·프로세스에 주입(§0.5) — 오직 관찰. (v8: 사용자 개시 kill/정리 시그널은 주입이 아니라 제어 — §0.5 경계 개정 참조.)
- 세션 attach·resume — herdr/tmux 영역. (kill·유령/stale 정리는 v8 F-27로 도입 — 사용자 개시 + 확인 게이트 한정. 자동 제어(fleet 자체 판단 kill)는 계속 Non-goal.)
- 원격·웹 대시보드 — 로컬 터미널 only.
- 새 telemetry 파이프 신설 — 하네스가 이미 남긴 것만 읽음. (fleet 소유 action log는 telemetry 파이프가 아니라 자기 행위 기록 — 제목 sidecar 동렬.)

## 확정 결정 (locked, v1)

- **F-1 (외부 관찰자)**: zero-injection. write는 우리 소유 local state(statusline tap + neutral title sidecar)만 허용하고 하네스 원본 transcript/DB에는 쓰지 않는다. (§0.5·§5)
- **F-2 (3계층·2섹션)**: 프로세스 스캔 백본(세션 존재 진실) + 하네스별 passive enrichment(칸 채우기) + curses 렌더. fleet + dispatch 2섹션. (§1)
- **F-3 (하네스 비대칭 허용)**: opencode rate-limit·effort 결손 칸 `—`. Codex telemetry = rollout `token_count` tail. (§2,§4)
- **F-4 (per-session Claude tap)**: statusline.sh 이 `~/.claude/.statusline/<sid>.json` 도 write(단일 파일 덮어쓰기 해소). 구현=statusline.sh 확장. (§5)
- **F-5 (dispatch uncapped + jobs.log tolerant)**: statusline 잡스캔 재사용·top-3 cap 제거, jobs.log `{open,running}` 수용·malformed tolerant. jobs.log 어휘 버그 동반 정리 권고. (§6)
- **F-6 (재사용)**: herdr 4-상태 어휘 + 기존 liveness(15min stale). herdr 자체는 채택 X. (§7,§8)
- **F-7 (zero-dep curses)**: python 표준 라이브러리만. tmux 세로 사이드 페인 런처. (§9)
- **F-8 (MVP 경계)**: sparkline·herdr 소켓·커스터마이즈는 후순위 스코프 밖. (§11)

## 확정 결정 (v2 추가, 2026-07-10)

- **SD-F1~F4 (stage-dispatch 관제 parity)**: 스테이지 row 단계명 라벨 / conductor 집계 breadcrumb = 자식 실측 우선 / 스테이지 자기 model·effort 1급 / pipe 공백·콤마 tolerant. (§4.5, stage-dispatch SD-3·§9-13)
- **F-9~F-13 (UI 가독성)**: 메타라벨 축약 재배분(+drill 하드코딩 맵 → 일반 규칙) / alert humanize / raw status 어휘 표시층 정리 / footer·legend 잡음 절제 / dead·stale 결손 절제(`last seen`). (§4.6)
- **F-1 확장**: 관찰 = 디스크·프로세스 + 하네스 usage API read-only. (§0.5)
- **v2 기준선 승인**: usage 헤더·pulse 요약·alert strip·그룹 카드(3단계 온도·🚧·게이트 배지)·folded 집계·`w` 레이아웃 cycle·main-bold·tint 체계 — 07-01~07-10 진화 전체. (§4 [v2 기준선])

## 확정 결정 (v3 승격, 2026-07-12 — minor 5건 흡수 + audit 반영)

- **F-14~F-19 lock (§4.7)**: 세션 표시명=하네스 제목(+짧게·영어 F-16, sidecar refresher F-17) / 분사 row 레이아웃 재설계·done-stage breadcrumb 흡수·queued=진짜 미기동만(F-15) / mem-워커 environ 태깅·drill dedup(F-18) / 메모리 관측 패널 — memory PRD v15 Cluster J 저널 소비(F-19). 구현 전량 main 머지 확인 (audit forward 15/15 🟢).
- **§3 `--demo` 소급 등재** (audit 🟡-2) · **§9 모듈 트리 현행화** (audit 🟡-3) · **🧠 글리프 위계 명문화** (§4.7).
- minor log 리셋 — v3 스냅샷 baseline (audit `_internal/audit/audit_2026-07-12T0910.md`).

## 확정 결정 (v4 승격, 2026-07-13 — runtime-currentness F-20)

- **F-20 lock**: Codex rate windows are dynamically labeled from `limit_window_seconds` when present. The old `primary=5h`/`secondary=7d` mapping is compatibility fallback only. Incident recorded inline: local Codex `primary_window.limit_window_seconds=604800, used_percent=10, secondary_window=null` must render as a 7d window, not `5h 10% reset 6d22h`.

## 확정 결정 (v5 승격, 2026-07-13 — cross-harness title F-21)

- **F-21 lock**: Codex `threads.title`은 현재 native title 정본이며 `thread_name`은 compatibility fallback이다. title provider/sidecar는 Claude adapter 기능이 아니라 fleet 공용 계약이며, 기본 Haiku no-tools provider는 `FLEET_TITLE_COMMAND`로 다른 저비용 no-tools model wrapper와 교체 가능하다. fresh sidecar → native title → slug 순서와 live-only scheduling을 강제한다.

## 확정 결정 (v6 승격, 2026-07-14 — responsive title F-22 + storm containment F-23)

- **F-22 lock (역사적 v6 결정; 출력 길이는 v16에서 대체)**: 세션 제목의 24열 고정 상한을 폐기하고 터미널 가용폭 기반 예산을 쓰며 dispatch compact 상한과 display-cell 안전 클립을 보존한다는 레이아웃 결정은 유효하다. 당시의 최대 12단어·96자 provider 길이는 현행 입력이 아니며 v16 F-17의 3~6단어·최대 40자 단일 계약이 명시적으로 대체한다.
- **F-23 lock (v16 수치 개정)**: 내부 mem/title worker와 app-server/dead/stale를 graph cut하되 일반 child는 요약 대상으로 유지한다. 모든 진입점이 cross-process concurrency 기본 3/최대 4, rolling 60초 start budget 기본·최대 4, env/state kill switch, stale-lease 회수를 공유한다. 2026-07-14 재귀 title chain 사고는 200-session hermetic fixture로 고정하고 live provider를 검증에 호출하지 않는다.

## 확정 결정 (v7 승격, 2026-07-15 — worker attribution + Codex identity ownership)

- **F-24 lock**: `AGENT_SESSION_ROLE=worker`는 cross-harness child 귀속의 portable 강한 표식이다. Codex rollout fd 소유권을 tick prepass에서 먼저 예약해 same-cwd fallback이 이미 소유된 sid를 복제하지 못하게 한다. 불확실한 PID는 unknown으로 남기며 live row 자체는 보존한다.

## 확정 결정 (v8 승격, 2026-07-15 — 관제 신뢰성·세션 제어·분사 정책 연동, 사용자 확인 3건)

- **F-25 lock (상태 판정 단일 모델)**: 모든 세션/잡 상태는 `model.py` 소유 단일 분류기가 결정한다. 소스 우선순위 = 명시 registry > 강한 프로세스 증거(pid+start-time·fd 소유·env 마커) > mtime 휴리스틱. 하향 전이만 hysteresis, `--json`에 `state_evidence` additive 노출, 어휘 매핑 표 규범화. 기존 휴리스틱은 입력 계층으로 재배치. 접근 방식 "전면 재설계"는 사용자 확인(2026-07-15).
- **F-26 lock (세션 레지스트리 1급)**: `~/.claude/sessions`를 1급 enrichment로. 이름 사슬에 registry name 삽입, `unused` 상태 신설(무transcript+무활동), provenance dim 태그 best-effort.
- **F-27 lock (제한적 세션 제어)**: 범위 = kill+정리만(사용자 확인 — attach/resume 비대상 유지). 행 선택+확인 게이트, exact pid+start-time 재검증, SIGTERM→명시 SIGKILL, action log 기록, kill 성공 시 registry row `done,note=fleet-kill` 마감(무write 불변식의 명시 단일 예외). 자동 제어 0.
- **F-28 lock (분사 정책 연동)**: 타이밍 = "계약 선고정, 구현 후행"(사용자 확인). route record/topology registry 착륙 후 pipe 휴리스틱을 canonical record 소비로 대체한다. fallback은 route tuple이 완전히 부재한 legacy 행에만 허용하고, 명시 tuple의 record 부재·무효·불일치는 unknown/ambiguity로 남긴다. detached run registry·governor lease 관측은 소스 착륙 후 단계 적용.

## 확정 결정 (v9 승격, 2026-07-15 — minor 흡수 + audit 해소 + 마우스 재설계 + 종착 비전)

- **minor 6건 흡수**: v8 minor #1~#6(제목 4~8단어·64자 / name zone 40열 캡 / F-29 등재 / unused stale 면제 / kill 키 확정·§9 등재 / parent_cwd 래퍼 정합)을 본문으로 정리(취소선 제거), minor-log 리셋. 근거 = `_internal/audit/audit_2026-07-15T1734.md` (🟢 12 — 전 계약 코드 실재 확인).
- **F-25 규범 매핑 표 삽입** (audit 🟡-1 해소): 세션/잡 상태 표 + "48h 침묵이 registry 명시를 이기는 유일 예외"(v8 사이클 D1) 명문화. 구현 상수는 `model.py` 한곳.
- **§10 다이어그램 갱신** (audit 🟡-2 해소): `control.py` signal/write 예외 노드 + action log + registry row 마감 경로.
- **F-27 v9 (마우스 1급)**: 행 클릭 선택 → 재클릭 kill 요청 → `[kill]`/`[cancel]` 클릭 확정. 키보드 s/x 경로는 폴백 유지. 안전 계약(확인 게이트·start-time 재검증·working 이중 확인·action log·자동 제어 0) 불변. 근거 = 사용자 "그냥 마우스로 처리가 되는게 좋을것 같긴해"(2026-07-15).
- **F-30 (종착 비전)**: dispatch·서브에이전트 **처리 과정의 시각화**가 fleet의 목표 상태 — F-28/F-29 우선순위 근거로 등재, 전용 뷰 설계는 topology registry 착륙 후.

## 확정 결정 (v10 승격, 2026-07-15 — 처리-과정 시각화 설계 확정)

- **F-28a~c lock (v16 evidence 경계 개정)**: route record는 read-only로 소비하고 arbitrary DAG breadcrumb을 생성한다. 명시 route tuple이 없는 legacy 행만 artifact/pipe fallback을 허용하며, tuple-record 불일치·무효 record는 unknown/ambiguity로 남고 추론으로 숨기지 않는다. 자식 실측 우선과 detached run·governor 조건부 probe는 불변이다.
- **F-30 lock (과정 뷰)**: `p` 토글 전용 모드, 카드=route 1개, DAG 가로 흐름 + 병렬 세로 분기, 노드 상태 글리프(✓/●/○/✕), 활성 노드 아래 세션·서브에이전트 중첩, 마우스 접기/펼치기(F-27 문법), 완료 접힘·실패 자동 펼침이다. route tuple이 완전히 부재한 legacy 행만 degrade 카드를 사용하며 명시 tuple을 검증하지 못한 행은 unknown/ambiguity로 남긴다. 실측 스키마(schema_version 1) 기준 — 스키마 변경 시 stage-dispatch spec과 동기 의무(F-19 선례).

## 확정 결정 (v14 승격, 2026-07-22 — portable unit·compositional route)

- topology registry schema v3와 immutable route schema v2/dispatch contract v3은 별도 버전 축이다.
- unit은 portable catalog 실행 단위이고 Skill/contract, bootstrap worker type, model role, native agent type을 대체하지 않는다.
- `worker_role`은 legacy read-only metadata다. 새 writer는 생성하지 않고 Fleet은 authoritative fields 부재 때만 fallback한다.
- runtime-native surface는 공식 문서가 보장하는 경계까지만 주장한다. private transcript/state DB projection은 tolerant enrichment이고 정식 parity 근거가 아니다.

## 확정 결정 (v16 승격, 2026-07-22 — unified stage/context/title budget)

- **F-36 lock**: interactive `Session`과 registered `DispatchJob`은 동일 additive `WorkProjection`을 소비한다. 검증된 route/node evidence > exact registry/env identity > 단일 cwd 후보 > route-부재 artifact stage 순서며, 충돌/복수 후보는 임의 최신 route를 고르지 않고 unknown/ambiguity로 남긴다.
- **F-36 composed lock**: sealed route의 arbitrary `nodes[].id/unit/depends_on/completion_gate/write_scope`를 opaque DAG로 그린다. record에 대해 plan/exec/test/report 하드코딩을 사용하지 않고 parallel sibling/fan-in을 보존한다.
- **F-37 lock**: wide/narrow/stack의 primary identity row에서 ctx를 제거하고 subordinate line을 `ctx … [· NOW]` 문법으로 통일한다. NOW 부재에는 ctx-only, ctx 부재에는 `ctx —`, dead/stale에는 row 전체 생략. child의 title/NOW/context는 하나의 ambiguity-refusing association으로만 공급하고 parent ctx를 상속하지 않는다.
- **F-38 lock**: context pressure는 관측/표시만 바꾸며 intensity, graph/depth, model/effort, QA/test/retry/gate/guard/definition of done와 직교한다.
- **F-39 lock**: title/NOW worker는 default concurrency 3(max 4), rolling 4 starts/60s(max 4), main/child debounce 600/150s다. 공유 lease/kill switch/no-live-provider tests와 shell-free pluggable no-tools provider 경계를 유지하고 vendor를 hard-pin하지 않는다.

## Next — current v16 implementation handoff (`autopilot-code`)

1. `projection.py`와 additive model/JSON을 추가하고, exact route/registry evidence → ambiguity refusal → route-부재 단일 artifact stage 순서의 `WorkProjection` resolver를 구현한다.
2. sealed arbitrary DAG의 opaque node/unit/gate/scope, parallel sibling, fan-in을 group/process/plain/JSON에 공통 투영한다.
3. wide/narrow/stack identity 아래 하나의 `ctx … [· NOW]` row와 title/NOW/context 단일 child association을 구현하고, 현행 TITLE 3~6단어·최대 40자 및 F-39의 3/4 concurrency·4 starts/60s·600/150s 계약을 적용한다.
4. §4.12 acceptance matrix, canonical↔Claude mirror parity, public JSON compatibility를 hermetic fixture/fake clock으로 검증한다. default/custom live provider 호출과 실세션 spawn/signal은 금지한다.

권장 진입: `/autopilot-code --mode dev --intensity strong "agent-fleet-dashboard PRD v16 F-36~F-39 구현 및 §4.12 검증"`. v6/v8/v9/v10 및 v2의 이전 구현 순서는 위 version history와 pipeline summary에 보존된 **완료·대체된 역사**이며 현재 실행 지시가 아니다.
