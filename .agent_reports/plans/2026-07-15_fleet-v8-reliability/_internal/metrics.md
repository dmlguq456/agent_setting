# metrics — 2026-07-15 fleet-v8-reliability (code-execute)

- **safety commit**: `8dd0c062a58fd61827cc9c3f1d7c7be63b8a7aa8` · 진입 시 worktree clean
- **커밋 없음** (지시대로 브랜치 dirty 유지 → code-test 스테이지 인계)

## 테스트

| 항목 | 값 |
|---|---|
| 기준선 | **247 tests OK** (13.7–14.4s) |
| 종료 | **414 tests OK** (16.4s) |
| 신규 | **+167** (회귀 0, 삭제 0) |
| 스위트별 | `test_f25_state_model` 33 · `test_f26_registry` 39 · `test_f22_name_cap` 13 · `test_f27_control` 82 |
| 기존 수정 | `test_f18_attribution` 단언 2건 (아키텍처 이동 — 약화 아님, phase_01 리뷰가 정당성 확인) |

## 변경 규모

- 추적 파일: **16 files changed, 2328 insertions(+), 188 deletions(-)** (canonical + mirror 양쪽)
- 신규(untracked) 파일: **2206 LOC** (canonical 기준 — `control.py` + 신규 테스트 4종)
- 신규 소스: `tools/fleet/control.py` (1개)
- 신규 테스트: 4파일 + `tests/fixtures/state_model/` 9픽스처
- mirror `adapters/claude/tools/fleet/` **매 Step 끝 rsync** — 최종 `test_mirror_parity` 통과

## acceptance 실측

| 항목 | 기대 | 실측 | 판정 |
|---|---|---|---|
| F-22 `_wide_name_width` | {60:28, 120:29, 168:40, 200:40} | **정확히 일치** (기준선 {60:28,120:29,168:**77**,200:**109**}) | ✅ |
| F-26 live (pid 1168514) | 이름 있는 `unused` 행 | `◌ agent-setting-17 unused 4h05m tracked` · tier 1 · `activity_ms=118.99` · `derived=false` | ✅ |
| F-26 동형 재현 (pid 2473021) | 동형 | `unused` · tier 1 · `activity_ms=143` · `proc_start_match=true` | ✅ (렌더 축은 스폰 맥락 아티팩트로 미표시 — step_04 로그 참조) |
| F-27 start-time 불일치 거부 | 거부 | `refused` + 프로세스 생존 + `reason=start_time_mismatch` 로그. **대조군**: 정확한 start-time → `ok`, rc=-15 | ✅ |
| F-27 자동 제어 횟수 | **0** | `--json`+`--once`×2 후 action log **미생성**(0 항목). 정적 grep: control importer 0줄 | ✅ |
| F-25 재배치 가드 | `.liveness =` 정확히 2곳 | **2곳** (`__init__.py:149`, `dispatch.py:1030` — 둘 다 위임) | ✅ |
| `--json` additive | 기존 필드 삭제/개명 0 | 전 행 `state_evidence` 보유 · `ev.state == liveness` · `derived ⇔ tier==3` 전행 성립 | ✅ |
| python 3.8 문법 | 통과 | `ast.parse` 전 파일 · 3.8.10 | ✅ |

## 행 길이 (기준선 대비 델타 — 절대치 0은 기준선부터 불가, step_03 로그 참조)

| width | 기준선 over | 종료 over | 델타 |
|---|---|---|---|
| 60 | 6 | 7 | +1 (pulse에 `◌ 1 unused` 어휘 추가 — legend/alert와 동일 계열, 기존 초과군) |
| 120 | 0 | 0 | **0** |
| 168 | 3 | 1 | **−2** (F-22 캡이 장문 dispatch 행 2건 해소) |

## 리뷰

| 리뷰 | 판정 |
|---|---|
| `phase_01_correctness.md` (F-25) | **PASS-with-minor** · CRITICAL 0 · 구 `classify()` 대비 **280조합 차분 퍼즈 divergence 0** → D1 실증. F4/F5/F6/F8 전량 반영 |
| `design_critic_step2.md` (F-26 렌더) | **PASS-with-minor** · CRITICAL 0 · **글리프 KEEP `◌`**(3폰트×4크기 실제 래스터 검증, `⊘` 렌더 증거로 기각) |
| `design_critic_step4.md` (F-27 UI) | **BLOCK → 해소.** CRITICAL 1 = 경고 프롬프트만 풋터 바 상실(시각 위계 역전, 실제 curses attribute 되읽기로 실측). `hdr_warn` 바 role 신설로 해소 |
| `phase_02_f26_f22_f27.md` (B–D) | **BLOCK → 해소.** CRITICAL 1 = `DispatchJob.proc_start` 부재로 잡 kill 전량 거부 + `close_registry_row` 죽은 코드. 필드 추가 + pid 4지점 동반 채움으로 해소. M1/M2/M3 전량 반영 |

## 실측으로 발견한 결함 (테스트가 아니라 **출력을 읽어서** 잡은 것)

1. **provenance 전 행 누출** — `enrich()` 1번 블록에서 해석해 title 가드가 항상 참. 60폭 렌더를 읽고 발견. (D5)
2. **`trackedmain` 분리자 소실** — name+suffix가 zone을 정확히 채우면 패딩 미발생. 잠복 버그를 F-22 캡이 일상화. (D7)
3. **168폭 이름 굶주림** — 캡+F-26 태그 충돌로 `agent-se…`. critic은 캡 이전(77셀) 기준이라 못 봄. (D6)
4. **프롬프트 키 잘림** — `confirm2` 117셀 → 60폭에서 "press Y to kill"이 잘려 **동의 방법을 감춘 채 동의를 요구**. 폭 실측으로 발견. (D10)

## 잔여 RED / 갭

- **없음(RED 0).** 414 tests OK. 리뷰 BLOCK 2건 전량 해소.
- **미수행 1건**: 계획 §6.6-6 라이브 TUI 수동 검증 — 헤드리스 워커에 대화형 TTY 부재. code-test/사용자 인계.
- **안전 경계 위반 1건 자진 신고**: step_04 로그 §안전 경계 위반 참조.
