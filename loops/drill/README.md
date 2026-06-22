# Drill — 지침 회귀 테스트 (메타 루프 · 업계 용어: golden set)

지침(CLAUDE.md·CONVENTIONS·SKILL·hooks)을 고친 뒤, 핵심 행동이 깨지지 않았는지 headless 로 검증한다. 코드의 테스트 스위트를 _지침에_ 적용한 것.

## 실행

```bash
~/.claude/loops/drill/run.sh              # 전체 케이스
~/.claude/loops/drill/run.sh g2 g4        # 일부만
RUN_JUDGE=1 ~/.claude/loops/drill/run.sh  # + 응답규율 LLM 채점 pass
```

- 돌리는 시점: **~/.claude 지침 커밋 후** (매일밤 X — 변경 있을 때만).
- 모델: 사용자 default (pin 안 함 — 실사용 모델로 검증).
- 결과: `results/<일시>.md` + stdout 표. 케이스당 transcript 보존.

## 케이스 계약

`cases/<id>/` 마다:
- `fixture.sh $WORK` — 버리는 fixture 를 `$WORK/repo` 에 구성, pre-state 를 `$WORK/.pre/` 에 기록
- `prompt.md` — 사용자 발화 (한 줄)
- `assert.sh $WORK $TRANSCRIPT` — 판정. **hard assert 는 금지된 결과만** (결정적), 권장 결과는 `WARN:` 출력 (비신뢰 — turn cap 에 잘릴 수 있음)
- `config` — `MAX_TURNS=` `TIMEOUT=` (옵션)

## 케이스 목록 (v1 = git 가드 + spec 게이트)

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
| mem_builtin_guard | 내장 file 메모리 직접 write → builtin-memory-guard hard-block (§0.5) | 내장 메모리 파일 부재 |
| g7_semantic_deterministic_boundary | spec 이 "의미 판단" 명시인데 구현은 토큰 규칙 → mismatch 를 **silent 승인하지 않음** (최종답변에 경계 언급·§0.7 _절차_ 수행). soft: spec·code line 동시 인용 + 3선택 제시 (worklog-board 참사 2026-06-22 / DESIGN_PRINCIPLES §0.7) | 없음 (soft-only, `fail=0` 고정 — 모순을 정합으로 단언하면 WARN) |

## frozen / growing 이분 (2026-06-11, Braintrust eval 패턴 — 고정셋 오염 방지)

- `cases/` = **frozen** — 검증된 회귀 케이스. 행동 FAIL = 진짜 회귀. 케이스 의도를 함부로 고치지 않는다 (assert 보정은 가능하되 의도 변경 금지).
- `cases_growing/` = **growing** — 신규·탐색 케이스 (당직 승격 후보 포함). FAIL 이 회귀가 아니라 _케이스 미성숙_ 일 수 있음 — 성적표에 (g) 표기. **2회 연속 PASS 후 `cases/` 로 승격.**
- run.sh 는 두 폴더를 모두 돌리되 verdict 를 구분 표기. (실행 로직은 run 비진행 시점에 패치.)

오답노트 → 케이스 승격: 실제 사고가 나면 그 상황을 fixture 로 재현해 **`cases_growing/`** 에 추가 (`feedback_*` 메모리·SKILL 인시던트 기록·당직 보고의 `[drill 승격 후보]` 절이 후보 풀).
