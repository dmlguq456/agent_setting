# harness-layer-sync Phase 1b — 재귀 census 잔여 소탕 (하위 디렉토리 복사본)

> branch `layer-sync-phase1b` · 2026-07-10 · autopilot-code --mode dev --intensity standard
> 선행: Phase 1(`29f714f`, 머지됨) · Phase 2(`df6ff67`). 본 사이클은 Phase 1 census 가
> `adapters/claude/{hooks,tools,utilities}` **최상위만** 훑어 놓친 _하위 디렉토리 물리 복사본_ 을 소탕.

## 1. 재귀 전수 census (모든 깊이 · 비-symlink 실파일)

`find adapters/claude/{hooks,tools,utilities} -type f` → canonical 대조. fleet/**·loops/** 는 세션 겹침 deferred.

### 최상위 (Phase 1 예외 등재분 — 조치 없음)
| adapter path | class | 상태 |
|---|---|---|
| hooks/core-first-guard.sh | wrapper | 등재됨 ✓ |
| hooks/core-read-marker.sh | wrapper | 등재됨 ✓ |
| hooks/mem-distill-dispatch.sh | delta | 등재됨 ✓ |
| utilities/agent-worklog-state.sh | delta | 등재됨 ✓ |

### 하위 디렉토리 (census-gap — Phase 1b 처리 대상)
| adapter path | 대조 | 판정 | 처리 |
|---|---|---|---|
| tools/design-mcp/console-check.mjs | SAME | collapse | symlink |
| tools/design-mcp/convert.mjs | **DIFFER(2)** | **STALE** (canonical `33822d6` 06-29 14:46 "neutralize portable path" > adapter 06-29 14:21) | collapse (canonical=진실) |
| tools/design-mcp/.gitignore | SAME | collapse | symlink |
| tools/design-mcp/package.json | SAME | collapse | symlink |
| tools/design-mcp/package-lock.json | SAME | collapse | symlink |
| tools/design-mcp/README.md | SAME | collapse | symlink |
| tools/design-mcp/server.js | SAME | collapse | symlink |
| tools/design-mcp/smoke-test.mjs | SAME | collapse | symlink |
| tools/design-mcp/visual-check.mjs | SAME | collapse | symlink |
| tools/material/browser-fetch.mjs | SAME | collapse | symlink |
| tools/memory/apply-distill-actions.py | **DIFFER(11)** | **STALE** (canonical `1d31dd9` 07-05 **P-25 보안 fix 11줄 포함** > adapter `6886556` 06-29) | collapse (canonical=진실, fix 복원) |
| tools/memory/distill.test.sh | SAME | collapse | symlink |
| tools/memory/index-check.sh | SAME | collapse | symlink |
| tools/memory/inject.test.sh | SAME | collapse | symlink |
| tools/memory/mem_cluster_e_gamma.test.sh | SAME | collapse | symlink |
| tools/memory/mem_cluster_e.test.sh | SAME | collapse | symlink |
| tools/memory/mem.py | SAME (직전 수동 동기) | collapse | symlink |
| tools/memory/README.md | **DIFFER(4)** | **STALE** (canonical `a604fe8` 07-07 > adapter `18b35f4` 07-06) | collapse (canonical=진실) |
| tools/memory/recall.sh | SAME | collapse | symlink |
| tools/profile/build-home.py | SAME | collapse | symlink |
| tools/web-bundle/README.md | SAME | collapse | symlink |

**deferred (세션 겹침 — 처리 안 함)**: `adapters/claude/tools/fleet/**`(16 파일, 전부 concrete). `loops/**` 는 이 3개 층 밑에 없음(별도 top-level 층).

### 방향 판정 근거 (DIFFER 3건)
셋 다 canonical 이 더 최신·완전 → 전부 **STALE**(canonical=진실). 진짜 adapter-specific 0건 → 신규 예외 등재 불요.
특히 `apply-distill-actions.py` 는 canonical 에만 P-25 whitelist-bypass 보안 fix(id-mutation add-only 강제)가 있어 Claude 런타임 복사본이 그 fix 없이 실행 중이던 **실 divergence** — collapse 가 fix 를 런타임에 복원.

## 2. 처리 계약 (Phase 1 과 동일)

- SAME·STALE → canonical 로 symlink collapse. nested 파일 상대 target = `../../../../tools/<subdir>/<name>` (codex/opencode nested 컨벤션 동형).
- 하위 디렉토리 자체는 심링크를 담는 **실디렉토리로 유지**(codex/opencode 동형).
- 진짜 adapter-specific → 예외 등재 (본 사이클 해당 0건).

## 3. census-gap 구조 봉합 (가드 · HLS-5·7)

`tools/check-adaptation-boundary.sh`:
1. `assert_shared_adapter_class` 를 **nested rel 경로 지원**하도록 일반화(target 깊이 계산).
2. `check_claude_tool_projection` 의 nested `*/*` 분기 — 기존 "concrete 강제(symlink 금지)"(= census-gap 구조 진원)를 3-class 계약(`assert_shared_adapter_class`) 호출로 교체.
3. **신규 `check_claude_shared_layer_census`** — `adapters/claude/{hooks,tools,utilities}` 재귀 스캔: 예외 미등재 비-symlink 실파일 존재 시 **red**. 사람 vigilance 가 아니라 기계가 이 클래스를 잡음.
4. `CENSUS_DEFERRED="adapters/claude/tools/fleet"` — 동시 세션 소유 subtree 를 _명시_ 유예(silent omission 금지, ADAPTATION.md §6). 해당 세션 랜딩 시 제거.

음성테스트 `tools/adaptation-guard.test.sh` Case 7 추가 — nested 실파일 심으면 red(census) 확인 후 원복.

## 4. 검증
- `tools/check-adaptation-boundary.sh` green
- `tools/adaptation-guard.test.sh` 전건 PASS (신규 Case 7 포함)
- `bash -n` 전 스크립트 · `python3 -m py_compile`
- 무행동변화: SAME 18건 = symlink 후 byte 동일. mem CLI 스모크 `python3 tools/memory/mem.py stats` 정상.
- symlink 해석: `readlink -f` 물리 + `~/.claude/...` projection 체인 양쪽 canonical 도달.
