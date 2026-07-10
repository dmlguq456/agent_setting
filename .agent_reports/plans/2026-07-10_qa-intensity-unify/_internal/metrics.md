# 계측 — qa-intensity-unify 사이클 (2026-07-10)

## 분사 방식 (dispatch topology)
depth-1 conductor **하이브리드**: 경계-결합(boundary-coupled) core·wrapper 편집은 inline, 분리 가능한(separable) 작업만 in-session Agent 워커로 분사.

| 단계 | 방식 | 근거 |
|---|---|---|
| census (QA-OPEN-1 포함) | `Explore` 1× 분사 (병렬, 독립 census) | 표면 매핑은 read-only·독립 — 분사 이득. conductor는 동시에 core 파악. |
| core-first 편집 (CONVENTIONS/WORKFLOW/DESIGN/ADAPTATION/bootstrap) | **inline** | 전 편집이 CONVENTIONS §1.1 재서술을 semantic anchor 로 공유 — 순차·비분리. ~50 boundary assertion 보존 필요 → 블라인드 file-handoff depth-2 는 무이득·고위험. |
| skills 표면 (52 파일: 20 SKILL + references) | `general-purpose` 3× **병렬** 분사 | 스킬 파일 간 독립(disjoint dir) = 진짜 separable. 공유 transformation contract 로 일관성 확보. |
| wrapper 3종 (claude/codex/opencode) | **inline** | boundary-asserted 문자열 보존 필요 — 정밀 편집, conductor 직접. |
| root skills/ 미러 | **inline** (rsync, 중앙 1회) | 워커 간 race 방지 — 워커는 adapters/claude/skills 만, 미러는 conductor 가 중앙에서. |
| 검증 (suites + boundary) | **inline** | |

**depth-2 headless `claude -p` 스테이지 세션 미사용 (의도적 판단)**: 본 작업은 boundary-guarded 문서 리팩터로 (1) core semantic anchor 가 전 편집을 순차 결합 (2) 스테이지 간 병렬 이득 없음 (3) blind file-handoff 이 ~50 assertion 위반 위험만 증가. 분리 가능한 부분(census·per-file skill 편집)은 in-session Agent 로 병렬화해 wall-clock 확보. "separable standard+ work 만 depth-2" 계약의 취지 준수.

## Wall-clock (근사)
| 단계 | 소요 | 병렬 |
|---|---|---|
| Explore census | ~198s | (core 파악과 겹침) |
| skills 워커 A (code/draft/research 계열) | ~528s | 3 동시 |
| skills 워커 B (spec/lab/note/ship/design/refine) | ~380s | 3 동시 |
| skills 워커 C (code-*/draft-*/analyze-user) | ~363s | 3 동시 |
| skills 병렬 벽시계 | ~528s (max) | — |
| core+wrapper inline 편집 | 워커 실행 중 겹쳐 진행 | — |
| 검증 (portable-guards ×2, boundary ×2, sd15 ×3, dispatch ×3) | 개별 ~90–120s | 일부 background |

## 프로필 사용
**없음.** harness-internal 계약 문서 작업 — 사용자-facing product 스타일 아님. `mem profile` 조회 불요(도메인 트리거 §7.6 매핑상 해당 자리 아님).

## Phase 2·3 표본 대비
- stage-dispatch Phase 2·3 는 depth-2 headless 스테이지 분사 표본. 본 사이클은 **문서 리팩터 = 스테이지 분사 부적합** 사례로, SD-OPEN-1(마이크로-스테이지 inline 임계값) 판단에 보강 데이터: boundary-coupled·비분리 작업은 스테이지 분사보다 conductor-inline + 분리 부분만 in-session 워커 병렬이 우월.
- 교훈: `git stash`로 baseline 측정 시 장시간 명령(portable-guards)과 체이닝하면 timeout 이 stash pop 을 삼켜 working tree 를 baseline 상태로 남길 수 있음 → baseline 비교는 별도 turn/짧은 명령으로. (본 사이클서 1회 발생·즉시 pop 복구.)
