# F-17 사이클 pipeline_summary — 라이브 세션 제목 refresher

**청사진**: `.agent_reports/spec/agent-fleet-dashboard/prd.md` §4.6 F-17 (within-spec, spec 편집 없음)
**브랜치/worktree**: `fleet-f17-title-refresher` @ `/home/Uihyeop/agent_setting-wt/fleet-f17-title-refresher`
**커밋**: `aa016cd`(impl) · `952fea2`(test verdict)
**VERDICT: 🟡 GREEN-with-notes**

## 변경 파일

| 파일 | 종류 | 요지 |
|---|---|---|
| `tools/fleet/titles.py` | 신규 | fleet-owned sidecar 헬퍼 — atomic write(`os.replace`)·tolerant read·fresh 판정(<24h)·stale sweep(>7d) |
| `tools/fleet/refresh_title.py` | 신규 | detached refresher — transcript tail delta → no-tools haiku(`--disallowedTools` 11도구) → `validate_title`(≤40자·printable·1줄) → sidecar write |
| `tools/fleet/collectors/claude.py` | 편집 | `enrich()` step 3 에 sidecar(<24h) 우선순위를 ai-title **앞**에 삽입(additive, `sess.slug` 불변) |
| `adapters/claude/statusline.sh` (`claude_setting/statusline.sh` 는 이 파일로의 symlink) | 편집 | `S_TRANSCRIPT` 추출 + tap 뒤 debounce(10min)+lock(`mkdir` atomic)+detached(`setsid … &`) 트리거 블록 |
| `tools/fleet/tests/test_f17_title_refresh.py` | 신규 | 31 테스트 — TitlesHelper·Priority·Validate·DeltaOffset·Trigger·Security |

## 검증 결과 (code-test, `dev_logs/test_verdict.md` 상세)

- **(a) 회귀**: 전체 `tools/fleet/tests/` 119 tests green (F-17 신규 31 + 기존 88).
- **(b) D-14 보안 3층 실측**: ① 셸-인젝션 monkeypatch → 무실행(sentinel 미생성), title 은 inert 40자-cap 문자열만 ② 실 argv 정적 캡처 — `--disallowedTools` 11도구 전부 + `FLEET_TITLE_REFRESH=1` env + `shell=False` ③ **라이브 인증 haiku**로 활성 인젝션 넣고 refresh 실행 → 인젝션 무시, 정상 제목 산출, `/tmp/F17_INJ` 미생성.
- **(c) 라이브 실증**: 수동 refresh 1회 실행(10.6s) → sidecar 생성 + `title='Refactor Auth Login Module'`(짧은 영어 제목) 반영, collector 우선순위 end-to-end 확인. degrade 경로(claude 부재/unauth)도 별도 확인.
- **(d) statusline 트리거**: 5종 실측(debounce no-spawn / stale+grown 1회 spawn / lock 중복차단 / detached 즉시반환 <2.0s / 재귀가드 env skip), `bash -n` 문법 OK.
- **(e) 불변식**: no-curses import 확인, `model.py`/`render.py` 미변경(신규 필드 0), transcript read-only(sidecar 는 별도 경로), `sess.slug` 불변 — F-14/F-15 회귀 0.

## NOTE (병합 비차단 follow-up)

`refresh_title.py:121` `run_worker` 가 `claude` 종료코드(`returncode`)를 검사하지 않고 stdout 을 그대로 반환 — **설치돼 있으나 인증 실패/quota 에러** 시 `"Not logged in…"` 같은 에러 배너가 `validate_title` 을 통과해 세션 제목으로 오염될 수 있음. plan §5 "실패=slug fallback" 불변식이 이 케이스에서 부분 위배(claude 부재/timeout/exception 은 정상 degrade). 위험도 LOW(inert display·40자 cap·24h self-heal·인증 복구 시 자동 덮어씀). **권장 수정**: `if r.returncode != 0: return ""` 1줄 추가.

## Artifact 경로

- plan: `.agent_reports/plans/2026-07-10_fleet-f17-title-refresher/plan.md`
- execute dev_log: `.agent_reports/plans/2026-07-10_fleet-f17-title-refresher/dev_logs/execute.md`
- test verdict: `.agent_reports/plans/2026-07-10_fleet-f17-title-refresher/dev_logs/test_verdict.md`
- 본 요약: `.agent_reports/plans/2026-07-10_fleet-f17-title-refresher/pipeline_summary.md`

## 후속 (오케스트레이터 몫 — 본 사이클서 수행 안 함)

merge · push · worktree 정리 · 라이브 statusline 반영(post-merge) · `run_worker` returncode 노트 반영 여부 판단.
