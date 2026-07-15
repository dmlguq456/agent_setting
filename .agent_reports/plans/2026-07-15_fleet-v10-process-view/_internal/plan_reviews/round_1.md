# plan-review round 1 — fleet v10 처리-과정 시각화

- 대상: `plan/plan.md` + `checklist.md` (초판)
- 검토자: qa-team plan-review 모드 (독립, read-only)
- rigor: standard (독립 검토 1회 · correction 예산 1회)
- 판정: **PASS-with-fixes** → 본 라운드에서 전량 반영 완료 (correction 1/1 소진)

검토자는 인용 앵커 36개를 전수 대조하고, P1(route_hash 재계산)·P2(governor/run registry)·베이스라인 468을 **독립 재현**했다.

---

## 🔴 Blocking (2건 — 반영 완료)

### B1. `completion_gate=`는 gate **통과** 증거가 아니다 → §3.3 단일 판정 오염

- 반증: `completion_gate=`는 launch 시점 선언이다 (`adapters/claude/bin/dispatch-headless.py:389`). 실측 2건이 반증 — `fleet-v10-plan`은 `status=open`인데 `completion_gate=code-plan` 보유(끝나지 않은 노드가 "통과"), `fleet-v9-report`는 `status=done,note=dead-report-done`(죽은 노드가 "통과").
- 추가 근거: prd.md:284 — kill된 잡도 `done,note=fleet-kill`로 마감된다 → `status=="done"`조차 성공과 동치가 아니다.
- 파급: §3.3은 계획 스스로 "Step 2·3 공유 단일 판정, 복제 금지"로 지정한 소스다. 틀리면 breadcrumb·카드·`--json`이 같은 거짓을 말하고 prd.md:307(gate 통과 여부)·:292(추측 표시 금지)를 동시 위반한다 — F-28의 존재 이유("정책 따로 표시 따로" 제거)를 뒤집는다.
- **반영**: §3.3 판정표에서 gate 통과 판정 제거 → `✓` = `status=="done"` + `note` 검사(`fleet-kill`/`dead-*`는 `✕`). `completion_gate`는 **게이트 이름 표기 전용**, 통과 여부는 정직한 결손(`—`). Step 1에 gate-pass 증거 probe 추가(부재 시 P2 방식 이월). §3.4 `gate_passed` 키 삭제, §5.3 문구 정정.

### B2. `_FOLD_ROWS`가 `_TOGGLE_ROWS`에 하이재킹된다 — T3-9가 못 잡는다

- 반증: `render.py:2813-2816`의 toggle 판정은 **텍스트 substring 휴리스틱**(`"hidden" in segs[0][0] or "folded" in segs[0][0]`)이고 `else`로 배타적이다 → toggle로 잡히면 `_CLICK_ROWS`에 못 들어간다. 계획 §5.4의 "전 노드 done → 1행 접힘" 카드는 단일 세그먼트 행이고 `folded`/`hidden`은 기존 접힘 어휘다(`render.py:1975`). 그 단어가 라벨에 들어가면 rung 2가 클릭을 삼켜 카드가 영영 안 펼쳐진다 — `_handle_mouse` 도달 전 `_draw`에서 갈린다.
- I7이 `_FOLD_ROWS ∩ _CLICK_ROWS = ∅`만 주장 → **T3-9가 이 충돌을 통과시킨다**. "_draw 무수정 재사용" 단언 지점의 숨은 결합.
- **반영**: I7/T3-9를 `_FOLD_ROWS ∩ (_CLICK_ROWS ∪ _TOGGLE_ROWS) = ∅`으로 확장 + 접힘 카드 라벨에서 `folded`/`hidden` 어휘 금지를 §5.3/§5.4에 명문화.

## 🟡 개선 권고 (6건 — 전량 반영)

| # | 지적 | 반영 |
|---|---|---|
| Y1 | F-29 subagents는 `Session`에만 있고(`model.py:170`) 노드 실행 주체는 `DispatchJob`이다. render는 job↔session을 pid로 짝짓지 않는다(`parent_sid`/`parent_cwd`만 — `render.py:1788-1790`). 재사용되는 건 `_subagent_row()`뿐, **조인은 신규 작업**. 분기점 1528이 `is_child` 필터(:1545)보다 앞이라 실현은 가능. | §5.3에 pid 조인 명시 + checklist 항목 신설 |
| Y2 | `_SELECTABLE`(line idx) → `_draw` offset → `_CLICK_ROWS`(screen row) 2단 구조인데 계획이 **line-index 스태시(`_FOLDABLE`)를 빠뜨림** → `_draw`가 `_FOLD_ROWS`를 만들 소스가 없다. §5.6 "전량 `_build_lines` 직접 호출"도 T3-8/9/11에 대해 틀림(이들은 `_draw`가 채우는 맵을 본다 — 올바른 선례는 `test_f27_mouse.py:63-77` fake-scr `_draw` 하네스). | `_FOLDABLE` 추가 · §5.6 테스트 수단 정정 |
| Y3 | proc 잡 route env **실재**: `AGENT_ROUTE_FILE`/`AGENT_ROUTE_ID`/`AGENT_ROUTE_NODE`(`dispatch-headless.py:720-722`), 리더도 있음(`procscan.py:31 read_environ`). 계획이 쓴 `AGENT_DISPATCH_ROUTE_FILE`은 없는 이름. **`AGENT_ROUTE_HASH`는 미export** → proc 잡은 `expect_id`만 대조 가능. 간판 실측 케이스(`fleet-v10-plan`, pid 3555317)가 바로 proc 잡이라 degrade 방치 시 데모가 빈다. | §3.2 실명 확정 · §9 리스크 3 해소 |
| Y4 | §7 V2가 `FLEET_DEMO=1`을 명령에 넣지 않음 → 필수 디자인 critic이 빈 화면을 받을 수 있다 | V2 process 루프에 `FLEET_DEMO=1` 직접 삽입 |
| Y5 | `_scan_route_nodes(paths)`(재읽기) ↔ "파일 재open 금지"(rows 재사용) **모순**. `rows`는 `_scan_jobs_log` 지역변수(:820-821), `collect()`는 `paths`만 쥔다. `_jobs_log_fields`(:884)가 재읽기 선례. | 재읽기로 확정(선례 준수) + 모순 문구 제거 |
| Y6 | P1의 `BROKER_FIELDS` 근거가 사실과 다름 — 최상위가 아니라 `dispatch_evidence.tuples[]` 행 단위 정규화용(`capability-route.py:18,:66`)이고 두 record에 그 키 자체가 없다. 결론은 무관하게 옳음. | 문장 정정(없는 필드를 찾아 헤매지 않게) |

**앵커 드리프트(오도 아님)**: `_MOUSE_HINT_MIN_WIDTH` 2742(계획 2740) · `verify_route` 174-177(계획 175-177) · §3.5의 codex 픽스처 특징은 `nested_eligibility`가 아니라 `dispatch_evidence.tuples[].status` → 전부 정정.

## 🟢 확인됨 (독립 재현)

- **P1 재현 성공** — 두 record 모두 `hash_match=True, id_match=True, schema=1`. T1-4로 못박는 판단 옳음("계산식이 틀리면 전 record가 조용히 fallback → 기능은 죽고 테스트만 통과"라는 위험 인식이 정확).
- **P2 governor 정확** — `state.json` 실재(lease 2건, 하나가 본 plan 워커 pid 3555317), `DEFAULT_TOTAL_LIMIT=5`(:20), `len(leases)>=total`(:105), 죽은 lease 정리는 **write 시점에만**(:80-84) → §6a의 "read-only fleet은 죽은 lease를 스스로 걸러야 한다"는 **필수**. `AGENT_MODEL_GOVERNOR_ROOT` 워커 export 확인(:723).
- **P2 run registry 스킵 타당** — `--registry` default 없는 required(:18), `dispatch-node.py:12`는 러너 경로만 출력, live 0건. prd.md:311과 어긋나지 않으며 추측 경로 거부는 prd.md:292 준수.
- **§3.3 핵심 통찰 실재** — `dispatch.py:845-846`이 종단 행을 classification 전에 폐기 → `✓`를 영원히 못 그린다. "계획에서 가장 값진 발견".
- **분기 1곳 충분 · `_draw`/스크롤 무수정 재사용 유효** — `_build_lines` 호출자는 정확히 2곳(`render.py:2091`, `:2786`), `_clamp_offset`/`_OFFSET`/`_addline` 전부 line-index 기반. (B2·Y2 결합은 예외.)
- **`p` 키 충돌 없음**(`_handle_base_key` 2554-2577은 k/j/PPAGE/NPAGE/g/G/a/w만).
- **검증 명령 유효** — `COLUMNS=` 먹힘(`render_once`가 `shutil.get_terminal_size()` 사용 :2087) · V5 rsync는 `test_mirror_parity.py` docstring 공식 관용구와 일치 · 픽스처 json 미러 누락 경고 옳음 · **G3 grep 그대로 돎**(무매치 exit 1 = 통과) · V4 통과(단 `memory`는 조건부 키 → "기존 4키" 표현은 환경 의존 → §3.4 문구 완화).
- **베이스라인 재현** — `Ran 468 tests in 16.736s, OK`.
- **§5.5 `_WIDE` 지적 정확** — `✓●○✕`는 East Asian Ambiguous 폭이며 `_WIDE`(:2117)에 없다.
- **§0 안전 블록이 계획의 가장 강한 부분** — v8 위반 사례 정확 인용 + 픽스처-only 경계 표. `--view`(P3)를 `p`와 전역 하나로 묶어 결정 경로를 단일화한 것은 F-27 정신과 정합, spec 확장 아닌 구현 세부라는 판정에 동의.

---

## 반영 결과

B1·B2·Y1~Y6·앵커 드리프트 전량을 `plan/plan.md`/`checklist.md`에 반영했다. 재계획 불요(검토자 판단: "둘 다 §3.3 표와 §5.4/I7의 국소 수정"). correction 예산 1/1 소진 → 잔여 우려 없음(§9로 이월된 항목은 실측 후 판단 대상이며 blocking 아님).
