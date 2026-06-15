# Spec Pipeline Summary: memory-store

- **Date**: 2026-06-15
- **Mode**: library + cli
- **Status**: spec in_progress (PRD 초안, open 결정 대기)

## Process Log
| Step | Action | Result |
|---|---|---|
| 1 | 정보 수집 | 입력 5종 확인, 이주 대상 59파일/22dir |
| 2 | mode 확정 | library + cli (메모리 저장소 모듈) |
| 3 | PRD 작성 | prd.md — D1~D7 locked + D-open 1~3 |

## 핵심 결정 (locked)
- D1 markdown 원본(추적) + SQLite FTS5 색인(파생) + projection(파생)
- D2 저장 위치 ↔ 스코프 분리 (통합 저장소 + cwd_origin 태그)
- D3 자동 write (기억 한정, 사람 게이트 없음, 품질필터만) — 불변식 의식적 전환
- D4 59파일 이주 / D5 하네스 projection / D6 recall 진화 / D7 injection 가드

## Open (사용자 확인)
- D-open-1 삭제 정책 / D-open-2 projection 갱신 시점 / D-open-3 이주 후 기존 폴더

## Update Log

### v1 → v2 (2026-06-15, update mode — drift 정정, snapshot `_internal/versions/v1/`)
구현이 spec 보다 앞서 만든 drift 정정 (코드가 진실, spec 후행):
- **D5** "주입은 Claude Code 가 projects/ 에서, 우리가 못 바꿈" (outdated) → **자체 하네스**로 정정: SessionStart `mem inject --hook`(store→additionalContext 직접 주입) + SessionEnd `mem sync`(projects/ auto-memory→store mirror+색인). store 가 세션 주입의 source.
- **Architecture mermaid**: PROJ→CC projection 주입 흐름(old) → `SRC ==mem inject==> CC`(주입) + `projects/ ==mem sync==> SRC`(회수) + 하네스 write→projects/ 로 교체.
- **D-4** projection 갱신 → inject(세션시작)+sync(세션종료) hook 자동.
- **cli 표·[library] API**: `mem inject`·`mem sync` 행 추가, `mem project` 는 "보조(주입은 inject)" 주석.
- 근거(검증): `settings.json` SessionStart=`mem.py inject --hook`·SessionEnd=`mem.py sync` 확인, 이번 세션 상단 inject 블록 실측.
- 스코프 한정: D1~D4·D6·D7·통합모델·데이터모델 불변.

### v2 → v3 (2026-06-15, update mode — Hermes DB화 강화, snapshot `_internal/versions/v2/`)
사용자 방향 전환 (4턴 설계 동기화 후 lock): "sqlite 기반 DB화 + 메모리 git 이력 제거 + 별도 저장소". Hermes `state.db`(로컬 SQLite WAL) 정렬.
- **D1 반전 (SoT 전환)**: markdown 원본(추적) → **로컬 SQLite `memory.db`(WAL)가 SoT**. git 은 `dump.jsonl`(레코드당 1줄·id 정렬, deterministic 텍스트) mirror 만 추적, 바이너리 `.db`·`.index.db`·WAL 은 gitignore. 복원 = 덤프 replay. FTS5 색인은 파생물 아니라 DB 본체 내장으로 승격.
  - 근거(사용자 합의): 자주 갱신되는 DB 를 git 바이너리로 올리면 delta 안 먹고 bloat. 텍스트 덤프는 변경 줄만 diff + audit 가시성은 덤. 사람이 메모리를 routine 으로 읽을 필요는 없음(읽기=inject/recall).
- **D9 신규 (저장소 분리)**: `~/.claude/memory/` 를 전용 private repo(`claude-memory`)로. config repo(`claude_setting`)는 `git filter-repo --path memory/ --invert-paths` 로 전체 이력 제거 + force-push (git bundle 백업 선행), 이후 `memory/` gitignore. 중첩 ignore-repo (submodule 미사용).
- **통합 강화 (D-7)**: user_profile + post-it + **Claude 내장 auto-memory** 를 한 DB 로. tier/scope/type 컬럼으로 주입 행동 구분 유지 (Hermes MEMORY/USER/state 분리를 한 DB 컬럼으로 표현 → 더 통합적).
- **D3 정련**: user_profile raw=레코드 흡수, 구조화 aspect 문서는 DB→generated view (`mem export --profile`) — sub-agent 경로 Read 보존, 순수 DB 배선 대공사 회피.
- **API/CLI 추가**: `mem export`(dump/profile)·`mem import`(replay)·`mem migrate` 에 md-file source 추가. 데이터모델을 SQLite DDL + jsonl 덤프 스키마로 재기술.
- **non-goal 보강**: Turso/libSQL 원격 동기화 명시 비목표 (단일 사용자·외부 의존 0 근거).
- 스코프: D2(위치↔스코프 분리)·D4(자동write)·D5(lifecycle)·D6(inject/sync hook)·D8(보안)·통합모델 골격 불변.

### v3 → v4 (2026-06-15, update mode — profile 완전통합 + Hermes 잔여port + 결정론우선, snapshot `_internal/versions/v3/`)
v3 구현(DB화·이주·저장소분리) 완료 후, 사용자 지적("profile은 절반만 통합 — sub-agent는 여전히 md 원본을 권위로 읽음, 별론데")과 핵심 원칙("결정론·SW 가능한 건 코드로 → agent 생각 최소화") 반영.
- **§0.5 결정론-우선 (D-8, cross-cutting)**: SW 가능 요소는 hook/script/gate/DB로 대체, agent judgment는 fallback. DESIGN_PRINCIPLES 격상 예정.
- **Cluster A (D-9) profile 완전통합**: DB=profile SoT / `mem export --profile`을 sync·analyze-user에 wiring해 md를 generated view로(A2) / analyze-user DB-first(A3) / post-it·편집 DB 경유(A4). sub-agent 경로 Read는 보존(md=view, 파일명 결정론 도출).
- **Cluster B (D-10) Hermes 잔여port** (08_source_grounded 검증): B1 session_search 자율 turn-호출 강화 / B2 turn-counter 자기회고(UserPromptSubmit hook 결정론 카운터, nudge_interval=10 등가). 08 결론 = FTS5 cross-session 갭 닫힘, 남은 진짜 port 이 둘뿐.
- 유지: D1~D9 골격·데이터모델.

### v4 → v5 (2026-06-15, update mode — Option 2 파일 메커니즘 제거, snapshot `_internal/versions/v4/`)
사용자 결정: "그냥 sub-agent도 DB 읽게 하면 됨 + user_profile·post-it 별도 파일이 왜 있냐". v4의 Option 1(md를 generated view로 유지)을 **Option 2(파일 메커니즘 자체 제거)**로 전환.
- **Cluster A 재정의**: user_profile/·post-it.md **파일 제거**, DB가 유일 SoT·유일 읽기 소스. sub-agent는 `mem profile <aspect>`(신규)·`mem recall`로 DB 직접 읽기. analyze-user·/post-it는 DB authoring. projection wiring 불필요(파일 없음 → 동기 로직 소멸, §0.5 단순화). 매트릭스는 문서로 보존(소스=DB). register-postit·.postit-roots 폐기.
- 근거: Option 1의 유일 근거였던 'agent rewire 회피'를 사용자가 명시 waive("대공사 OK"). post-it은 세션 주입이 이미 mem inject(DB)라 파일이 이중 redundant.
- DESIGN_PRINCIPLES §0.5(결정론-우선) ✅ 이번에 격상 완료.

## Next
v5 구현 → autopilot-code --mode dev (본 v5 spec). 순서: Cluster A(파일 제거+DB 직접읽기: mem profile 추가→agent/CLAUDE 트리거 rewire→analyze-user/post-it DB authoring→파일 제거) → Cluster B(turn-counter→session_search) → hygiene(sync-skills/drill·stale draft·03↔08 cross-ref).
