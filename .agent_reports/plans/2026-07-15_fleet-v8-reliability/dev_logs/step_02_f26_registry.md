# Step 2 — F-26 레지스트리 1급화 (dev log)

- **의존**: Step 1 완료(`unused`는 `classify_session()`이 만든다) ✅
- **종료 상태**: **332 tests OK** (기준선 247 + F-25 33 + F-26 39 + F-22 13) · 회귀 0

## 변경 파일

| 파일 | 변경 |
|---|---|
| `collectors/claude.py` | `read_registry(pid, home)` / `_apply_registry()` / `_ms_to_sec()` 신설 — registry를 1급 계약으로 승격. `sess.slug = name` 유지(무회귀) + `registry_name` 추가. `_has_transcript`·`_mtime_from_registry` 표식. **enrich 4) 블록에 provenance 해석**(제목 해석 **이후**) |
| `collectors/procscan.py` | `provenance(pid)` — ppid 계보 최대 6단계, 판별 실패 시 `None` |
| `render.py` | `_LIVE_GLYPH["unused"]="◌"` + `_GLYPH_KEY`/`_live_key`/`_HUE_OF`/`_COLOR`에 `g_unused`(글리프) · `g_unused_b`(배지) 2키. `_session_name()` 명시 사슬. `_unused_badge(s, compact)`. `_session_row`/`_session_row_2line` 배지·provenance + **강등 사다리**. pulse `◌ K unused`(K>0). legend(등장 시만) |
| `tests/test_f26_registry.py` | **신규** 39 tests |

## Decision

### D5 — provenance 해석 위치 (버그 수정: 실제 렌더를 읽고 발견)

초안은 `enrich()` **1번 블록**(registry 직후)에 provenance를 넣고 `if not sess.title` 로 가드했다. **그런데 그 시점엔 title이 아직 해석되지 않았다**(title은 3a/3b 블록에서 설정) → 가드가 **항상 참** → **모든 claude 세션에 provenance 태그가 붙었다.**

- **실측 발견**: 60폭 렌더에서 `● claude code  Fix bre… ▾2 tracked terminal  main` — 제목 있는 평범한 행까지 `terminal`이 붙어 이름 zone을 9셀씩 잡아먹었다. 테스트로는 안 잡혔고 **출력을 눈으로 읽어서** 잡혔다.
- **처분**: provenance 해석을 `enrich()` **맨 끝(4번 블록)**으로 이동. 의도(제목 없는 행에만)가 그제야 실현됨. 검증: 60폭 `grep -c terminal` = **0**(제목 있는 행 전부 미부착), 유령 행만 부착.

### D6 — 강등 사다리 (provenance → 배지 age → 이름)

F-22 40셀 캡(Step 3)이 얹히자 168폭에서 `agent-se…`로 **이름이 굶었다** — 캡 이전(77셀)엔 안 보이던 문제라 critic도 보지 못했다(critic은 Step 2 캡처 = 77셀 기준으로 평가).

- **규칙**: `avail`이 부족할 때 **provenance 먼저 드롭 → 배지 age 드롭 → 마지막에 이름 클립**.
- **근거**: F-26의 존재 이유가 **익명 행 제거**(prd.md:247)다. 이름이 가장 늦게 양보해야 한다. provenance는 계약 자체가 best-effort(prd.md:249)라 1순위 양보. age는 **모든 레이아웃이 time 셀로 이미 싣고 있어** 복구 가능한 절반(critic §2와 동일 논거).
- **결과 실측**: 60 = `agent-settin… unused tracked` / 120 = `agent-setting-17 unused 4h05m tracked terminal` / **168 = `agent-setting-17 unused 4h05m tracked`**(이름·배지 완전, provenance만 양보).

### D7 — `_NAME_GAP = 1` (잠복 버그 수정 — Step 3이 발현시킴)

`_session_row`의 패딩은 `if used < avail` 조건이라 **name+suffix가 zone을 정확히 채우면 패딩이 0** → gate 태그가 branch 컬럼에 **직접 붙는다**(`trackedmain`).

- **실측**: name(29) + `▾1`(3) + ` tracked`(8) = **정확히 40 = avail** → 패딩 미발생.
- **잠복성**: 기준선(zone=77)에서도 존재했으나 77을 정확히 채우는 장문 제목만 발현 → **드묾**. Step 3의 40 캡이 "채우는 것"을 **일상**으로 만들어 대부분 행에서 발현.
- **처분**: zone 안에 1셀을 분리자로 예약(`_NAME_GAP`). 168 렌더 `trackedmain` 충돌 **0건** 확인. F-22 acceptance 표는 불변({60:28,120:29,168:40,200:40}).

### D8 — 배지 색 분리 `g_unused_b` (critic ADVISORY §5 처분)

critic 지적대로 `untracked ∧ unused` 조합을 **실제로 렌더해 확인** → ` unused 3h45m`(g_unused) + ` untracked`(gate_u)가 **둘 다 dim yellow**라 하나의 덩어리로 읽혔다.

- **처분**: **배지에만** 별도 키 `g_unused_b`(plain yellow) 부여. **글리프는 `g_unused`(dim) 유지** — critic §1이 검증한 `●>○>◌` **잉크 무게 gradient**를 깨면 안 되므로 밝기를 올리지 않는다.
- critic의 제안(`g_unused` 전체를 비-dim으로)을 **부분 채택**한 셈 — 글리프까지 밝히면 gradient가 역행한다는 것이 critic 자신의 §1 논거다.

## 검증 결과 (계획 §4 검증 1–5)

| # | 항목 | 결과 |
|---|---|---|
| 1 | `test_f26_registry` | **Ran 39 tests — OK** |
| 2 | **F-26 live acceptance (pid 1168514)** | **OK — 아래 §live** |
| 3 | 3폭 실제 렌더 눈 리뷰 | **OK** — D5/D6/D7 3건이 여기서 발견됨(테스트는 통과 중이었다) |
| 4 | 디자인팀 critic | **PASS-with-minor · CRITICAL 0 · 글리프 KEEP `◌`** → `_internal/dev_reviews/design_critic_step2.md` |
| 5 | 전체 회귀 + mirror | **332 tests OK** · `test_mirror_parity` 통과 |

### live acceptance — 유령 세션 pid 1168514 (실측, 미조작)

전제 확인: `ps -p 1168514` → **살아있음**(`claude --teammate-mode tmux`, Wed Jul 15 11:39:47 2026 시작). **kill하지 않았다.**

```
$ COLUMNS=168 python3 tools/fleet/fleet.py --once | grep agent-setting-17
▍ ◌ claude code     agent-setting-17 unused 4h05m tracked   main   Fable 5 (xhigh)  ──────  —  4h05m
```
```json
"pid": 1168514, "liveness": "unused", "registry_name": "agent-setting-17",
"state_evidence": {"state":"unused","tier":1,"source":"claude-registry","derived":false,
  "rule":"idle refined to unused (no transcript, updatedAt≈startedAt)",
  "inputs":{"proc_start_match":true,"status":"idle","transcript":false,"activity_ms":118.99995803833008},
  "raw_status":"idle"}
```

- ✅ **익명 아님** — `agent-setting-17` (registry_name 사슬)
- ✅ **`unused <경과>` 배지** — `unused 4h05m`
- ✅ **idle과 구분되는 글리프** — `◌`(idle `●`, detached `○`, stale `·` 전부와 비충돌)
- ✅ pulse `◌ 1 unused` · legend `◌ unused`(등장 시만)
- ✅ tier 1 / `derived=false` / `activity_ms=119` — 계획 §1.2 실측과 1:1 일치

**PID 재사용 가드 실측**: registry `procStart:"3918896"` == `/proc/1168514/stat` field 22 `3918896` → `proc_start_match=true`. **이 대조가 없었으면(계획의 단일 `proc_start` 필드안) 가드가 무의미했다** — Step 1 D3 참조.

## critic 처분 요약

| critic 지적 | 처분 |
|---|---|
| **글리프 KEEP `◌`** (위임 결정) | **수용, 변경 없음.** critic이 3폰트×4크기 실제 래스터 렌더로 검증. `⊘`는 Liberation Mono에서 두부·DejaVu에서 최중량(gradient 역행)이라 기각 |
| MINOR §2 배지 age 중복(60폭 이름 굶주림) | **수용 — 단 예산 기반으로 일반화**(D6). critic은 "60폭 한정 축약" 권고했으나, 레이아웃 결합 대신 **이름이 굶을 때만** 축약하는 규칙으로 구현 → 120/168은 spec `unused <경과>` 그대로 유지(prd.md:248 준수), 60만 자동 축약. spec 두 요구(배지 shape vs 익명 행 금지)의 충돌을 폭이 아니라 **압박 조건**으로 해소 |
| ADVISORY §3 `terminal` 어휘 충돌 | **미조치 — 후속 obligation.** critic 판단 그대로: `terminal`은 **prd.md:249가 명시한 스펙 어휘**(`herdr`/`terminal`/`vscode`/`worker`)라 구현이 단독 변경할 사안이 아니다. spec 개정 선행 필요 → §후속 obligation |
| ADVISORY §4 `◌`/`○` 인접 미검증 | **수용 — 커버리지 추가.** `test_unused_and_detached_glyphs_are_distinguishable_side_by_side` 신설, detached+unused 동시 픽스처로 pulse/legend 강제 실증: `◌ 1 unused   ○ 1 detached` |
| ADVISORY §5 dim-yellow 중복 | **수용(부분).** D8 — 배지만 분리, 글리프는 dim 유지 |

## 후속 obligation (본 사이클 범위 밖)

1. **spec §9 모듈 트리에 `control.py` 등재** (계획 §6.1 — Step 4 착륙 후)
2. **spec §4.8 F-27 키 문구 sync** (`↑↓` 진입 → `s`/`x` 진입) — 사용자 확인 자리
3. **spec prd.md:249 provenance 어휘 `terminal` 재검토** (critic ADVISORY §3 — `tty`/`shell` 제안; 오독 해소 + 3–5셀 단축으로 이름 zone 압박 완화). **spec 개정 사안이므로 구현이 선행하지 않는다.**
