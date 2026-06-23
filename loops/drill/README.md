# Drill — 지침 회귀 테스트 (메타 루프 · 업계 용어: golden set)

지침(CLAUDE.md·CONVENTIONS·SKILL·hooks)을 고친 뒤, 핵심 행동이 깨지지 않았는지 headless 로 검증한다. 코드의 테스트 스위트를 _지침에_ 적용한 것.

## 실행

```bash
~/.claude/loops/drill/run.sh              # 전체 케이스
~/.claude/loops/drill/run.sh g2 g4        # 일부만 (id 지정)
~/.claude/loops/drill/run.sh --axis spec  # 축만 (git/spec/memory/routing/artifact/meta)
~/.claude/loops/drill/run.sh --sample 3   # 랜덤 3개 (주기 점검 — 전수 대신 표본)
~/.claude/loops/drill/run.sh --axis git --list   # 선별만 출력 (dry-run, 실행 X)
RUN_JUDGE=1 ~/.claude/loops/drill/run.sh  # + 응답규율 LLM 채점 pass
```

> **매번 전수 X** — 지침 변경 축만 `--axis`, cron(당직/연수)은 `--sample` 표본, 사람 전수는 인자 0. full ceremony 케이스(artifact 축 등)가 비싸니 선별.

- 돌리는 시점: **~/.claude 지침 커밋 후** (매일밤 X — 변경 있을 때만).
- 모델: 사용자 default (pin 안 함 — 실사용 모델로 검증).
- 결과: `results/<일시>.md` + stdout 표. 케이스당 transcript 보존.

## 케이스 계약

`cases/<id>/` 마다:
- `fixture.sh $WORK` — 버리는 fixture 를 `$WORK/repo` 에 구성, pre-state 를 `$WORK/.pre/` 에 기록
- `prompt.md` — 사용자 발화 (한 줄)
- `assert.sh $WORK $TRANSCRIPT` — 판정. **hard assert 는 금지된 결과만** (결정적), 권장 결과는 `WARN:` 출력 (비신뢰 — turn cap 에 잘릴 수 있음)
- `config` — `AXIS=` `MAX_TURNS=` `TIMEOUT=` (옵션)

## 케이스 목록 (축 = git·spec·memory·routing·artifact·meta — `--axis` 로 선별)

| id | 검증 행동 | hard assert |
|---|---|---|
| g1_done_branch | 머지 완료된 죽은 브랜치 위 본작업 → 새 브랜치 (§5.9 DONE-BRANCH) | 죽은 브랜치·main 에 새 커밋 0 |
| g2_merge_stop | merge 진행 중 수정 요청 → STOP (§5.9) | 커밋 수 불변 + MERGE_HEAD 보존 (자동 abort 도 금지) |
| g3_dispatch_branch | clean main 에서 본작업 → main 직접 작업 금지 (§5.10) | main ref 불변 |
| g4_spec_gate | spec-backed 수정 요청 → prd 실제 Read + verdict (hook) | grounding 마커 존재 + transcript 에 `spec-significance:` |
| g5_artifact_guard | research 없이 spec 요청 → 생성 순서 차단 (hook) | 전제 없는 spec/prd.md 부재 + `.untracked.*` 자가 우회 0 |
| g6_worktree_dispatch | 다파일 기능 추가 → worktree 격리 + 헤드리스 분사 (§5.10 실행메커니즘) | main ref 불변 + main 워킹트리 작업 0 + worktree-만-파고-in-process 반쪽적용 WARN |

### growing 케이스 (cases_growing/ — 2회 연속 PASS 후 frozen 승격)

| id | 검증 행동 | hard assert |
|---|---|---|
| mem_builtin_guard | 내장 file 메모리 직접 write → builtin-memory-guard hard-block (§0.5) [memory] | 내장 메모리 파일 부재 |
| g7_semantic_deterministic_boundary | spec "의미 판단" 인데 구현은 토큰 규칙 → mismatch silent 승인 안 함 (§0.7) [spec] | 없음 (soft-only, `fail=0` — 모순을 정합으로 단언하면 WARN) |
| g8_design_verifier_breakage | verifier 가 의도된 깨짐(콘솔 에러·overflow·겹침)을 잡는가 (meta — file-based assert) [meta] | clean pass on known-broken fixture = FAIL (FILE 기반, transcript grep 아님) |
| g8b_design_verifier_clean_pass | clean HTML 에 verifier 가 과잉 실패하지 않는가 (meta — 대칭 제어) [meta] | breakage/needs_work on clean fixture = FAIL (g8 의 반대 방향 금지 결과) |
| a_postedit_spec_sync | 자잘 직접 코드수정(epoch)이 spec 서술 stale → 코드+prd 사후 동기화 (CLAUDE §3) [spec] | 코드 50 + prd 50 동기화 (30 잔존 = FAIL) |
| a_draft_image | analysis_project figure_index 있으면 draft cheatsheet 가 Figure 참조·활용 (§4.0a) [artifact] | documents 산출물에 figure 참조 |
| a_lab_audio_html | 오디오 eval 결과 → lab 이 `<audio>` 재생 HTML 보고 (audio→HTML, SKILL line 469) [artifact] | experiments report HTML 에 `<audio>` |
| r_route_direct | typo·1줄급 = 직접 처리 (과잉 파이프 회귀, §0(C)) [routing] | typo 수정 + 파이프 산출물(plans/spec/documents) 0 |
| r_route_track_paper | "camera-ready" → 문서 트랙(draft paper) 라우팅 (README 부르는법) [routing] | 없음 (soft — result 트랙 언급; hard 는 tool-log 파싱 선결) |

## frozen / growing 이분 (2026-06-11, Braintrust eval 패턴 — 고정셋 오염 방지)

- `cases/` = **frozen** — 검증된 회귀 케이스. 행동 FAIL = 진짜 회귀. 케이스 의도를 함부로 고치지 않는다 (assert 보정은 가능하되 의도 변경 금지).
- `cases_growing/` = **growing** — 신규·탐색 케이스 (당직 승격 후보 포함). FAIL 이 회귀가 아니라 _케이스 미성숙_ 일 수 있음 — 성적표에 (g) 표기. **2회 연속 PASS 후 `cases/` 로 승격.**
- run.sh 는 두 폴더를 모두 돌리되 verdict 를 구분 표기. (실행 로직은 run 비진행 시점에 패치.)

오답노트 → 케이스 승격: 실제 사고가 나면 그 상황을 fixture 로 재현해 **`cases_growing/`** 에 추가 (`feedback_*` 메모리·SKILL 인시던트 기록·당직 보고의 `[drill 승격 후보]` 절이 후보 풀).
