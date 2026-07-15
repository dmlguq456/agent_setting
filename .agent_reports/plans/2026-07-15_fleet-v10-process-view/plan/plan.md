# fleet v10 구현 플랜 — 처리-과정 시각화 (F-28a · F-28b · F-30 · F-28c)

> 계약: `spec/agent-fleet-dashboard/prd.md` **v10** — §4.9 신설(prd.md:298-311) · 확정 결정 v10(prd.md:478-481) · Next v10 구현 순서(prd.md:489). 배경 계약 = §4.8 F-28/F-29/F-30(prd.md:285-296).
> 워크트리: `/home/Uihyeop/agent_setting-wt/fleet-v10-process-view` (브랜치 `fleet-v10-process-view`)
> intensity: standard · qa: standard · spec_touch: **false** (spec 변경 금지)
> 베이스라인 (2026-07-15 본 plan 스테이지 실측): `python3 -m unittest discover -s tools/fleet/tests -t .` → **Ran 468 tests, OK** (17.1s, pytest 미사용)
> 대상: `tools/fleet/{route.py(신설), collectors/dispatch.py, render.py, model.py, fleet.py}` + 미러 `adapters/claude/tools/fleet/`

---

## ⛔ 0. 절대 안전 규칙 (모든 스텝에 선행 — 비협상)

**실제 `claude`/`codex`/`opencode` 세션을 스폰하거나 시그널하지 않는다. 본 사이클의 검증 입력은 픽스처뿐이다.**

근거: v8 사이클에서 execute 워커가 이 경계를 위반했다 — plan 문서가 "실세션을 새로 스폰해 재현 후 kill로 정리"를 안내했고 워커가 그대로 실세션 1개를 스폰·SIGTERM했다. 그 절차는 harvest 시 **철회**되었고 규범이 아니다: `plans/2026-07-15_fleet-v8-reliability/plan/plan.md:396-402`의 ⛔ 블록(자진 보고: 같은 사이클 `dev_logs/step_04_f27_control.md`, `final_report.md §4.5`). 올바른 재현은 **프로세스 생성 없는 픽스처 주입**이며, `tests/fixtures/state_model/*.json`이 그 선례다.

| 검증 대상 | 허용 수단 | 금지 |
|---|---|---|
| route record 소비 | `tests/fixtures/route/*.json` 실측 복사본 + 합성 픽스처를 `route.load()`/`collect(jobs_path=...)`에 주입 | 실 dispatch 실행, 실 record 경로 의존 |
| 노드 점등·과정 뷰 | 픽스처 `DispatchJob`/`Session` → `render._build_lines()` 직접 호출 | 라이브 파이프 스폰해서 눈으로 확인 |
| 마우스 | `render._handle_mouse(mx, my)` 직접 호출 (`test_f27_mouse.py` 선례) | 라이브 TUI 실클릭 |
| 3폭 렌더 | `COLUMNS=<w> ... --once` (읽기 전용, curses 미진입) | — |
| governor lease | 실 `state.json`을 **읽기만** + 픽스처 주입 | governor `state.json` write, lease acquire/release |

**route record는 read-only다.** `route.py`는 `open(..., "w")`/`write_text`/`os.replace`를 포함하지 않는다 — Step 5 검증에 정적 grep 게이트로 강제한다(§7 G3).

---

## 1. 조사 실측 — 태스크 전제 정정 4건 (execute 워커는 이것을 전제로 시작할 것)

본 plan 스테이지가 소스·실측 record·live state를 직접 확인해 얻은 결과. 태스크 기술과 다른 부분이 있으므로 먼저 읽을 것.

### P1 ★ `route_hash`는 **재계산 검증이 가능하다** (실증 완료 — 추측 아님)

태스크는 "hash 검증"만 지시했고 방식은 열어두었다. 실측 결과 계산식이 harness에 실재하고, 두 실측 record에 대해 **정확히 일치**함을 확인했다:

```python
# utilities/capability-route.py:21-26 (canonical + route_hash) — 그대로 재현 가능, stdlib만 사용
def canonical(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
def route_hash(payload):
    bare = {k: v for k, v in payload.items() if k not in ("route_hash", "route_id")}
    return "sha256:" + hashlib.sha256(canonical(bare)).hexdigest()
```

plan 스테이지 실측 (2026-07-15):

| record | stored | recomputed | 일치 |
|---|---|---|---|
| `fleet-v10-process-view.route.json` | `sha256:27f7bc9ff152ba13b…` | `sha256:27f7bc9ff152ba13b…` | **True** |
| `/tmp/agent-note-d1-route.json` | `sha256:1120bb39a13c41917…` | `sha256:1120bb39a13c41917…` | **True** |

해시 입력에서 제외되는 키는 **`route_hash`/`route_id` 둘뿐이다** — 위 재현이 그것을 증명한다. (`BROKER_FIELDS`(`capability-route.py:18`)는 최상위 필드가 아니라 `dispatch_evidence.tuples[]` **행 단위 정규화**에만 쓰이며(`:66`), 두 실측 record에 그 키 자체가 없다 — 없는 필드를 찾아 헤매지 말 것. plan-review Y6 정정.)

이것이 중요한 이유: 제외 규칙을 잘못 추측했다면 모든 record가 hash 불일치 → 조용한 fallback → **기능이 죽은 채 테스트만 통과**했을 것이다. 그래서 Step 1은 이 두 실측 픽스처에 대한 hash 일치를 테스트로 못박는다(§3.6 T1-4).

정규 검증 순서는 `utilities/capability-route.py:174-177 verify_route()`를 부분 차용한다:
1. `record["route_hash"] == route_hash(record)` (변조·절단 탐지)
2. `record["route_id"] == "rt-" + hash[7:23]` (id 파생 일관성)
3. pipe의 `route_hash=` / `route_id=` == record의 값 (`utilities/worker-route-guard.py:71` 선례 — pipe가 가리키는 record가 그 record인지)

**차용하지 않는 것**: `verify_route()`(capability-route.py:174-177)의 `registry_digest` 대조와 topology registry 로드. 이유 = fleet은 **크로스 프로젝트 전역 관제**이고 다른 체크아웃(`agent-note` 등)에서 컴파일된 record는 이 워크트리의 `capabilities/topologies.json`과 digest가 다를 수 있다 — 대조하면 정상 record를 무더기로 거부한다. 무결성 축(1·2·3)만 취하고 정책 축은 취하지 않는다. `spec_touch`/tracking 검증도 동일 이유로 비대상.

### P2 ★★ F-28c는 "부재 시 스킵"이 아니다 — **소스 분할 판정** (probe 완료)

태스크와 prd.md:311은 "소스가 이번 착륙 범위에 없을 수 있다 → 부재 시 정직하게 스킵"을 전제했다. plan 스테이지가 probe한 실측은 **둘의 운명이 다르다**:

| 소스 | 실재 | 발견 가능성 | 판정 |
|---|---|---|---|
| **model-worker-governor lease** | ✅ 코드 `utilities/model-worker-governor.py` + **live state 파일 실재** | ✅ 결정적 경로 | **구현한다** |
| **detached resource-runner run registry** | ✅ 코드 `utilities/resource-runner.py` | ❌ **경로 발견 불가** | **스킵 + 이월 기록** |

**governor (구현)** — live 실측:
```
/home/Uihyeop/agent_setting/.agent_reports/.runtime/model-worker-governor/state.json
{"leases": {"<token>": {"acquired_at": 1784126330.78, "class": "dispatch",
                        "pid": 3555317, "starttime": "8233143"}, …},
 "schema_version": 1, "starts": [1784126291.76, 1784126330.78]}
```
lease `pid 3555317`은 **본 plan 워커 자신**이다(`jobs.log`의 `fleet-v10-plan` 행 `pid=3555317`) — 즉 이 표면은 살아 있고 지금 관측 가능하다. 경로 해석 = `AGENT_MODEL_GOVERNOR_ROOT` → `$AGENT_ARTIFACT_ROOT/.runtime/model-worker-governor` (`utilities/model-worker-governor.py:24-33 default_root()`). cap = `DEFAULT_TOTAL_LIMIT = 5` (같은 파일:20), 초과 판정은 `len(leases) >= total` (:105-107).

**run registry (스킵)** — `utilities/resource-runner.py:18` 은 `--registry` 를 **required 인자**로 받고 기본 경로가 없다. `utilities/dispatch-node.py:12` 는 `kind=="resource-runner"` 노드에 대해 러너 스크립트 경로만 출력할 뿐 registry 위치를 정하지 않는다. `.agent_reports/.runtime/` 아래 실 파일 0건. 실측 record 어디에도 `resource-runner` kind 노드 없음. → **fleet이 발견할 canonical 경로가 존재하지 않는다.** 추측 경로를 뒤지는 것은 prd.md:292의 "추측 표시 금지"에 정면 위배다. 정직한 스킵 + 이월(§6 Step 4b).

### P3 `--once`에는 과정 뷰 진입 수단이 없다 → `--view` 추가가 필요하다

prd.md:305는 진입을 **`p` 키 토글**로 확정했다. 그런데 `p`는 curses 라이브 경로에만 존재하고(`render._handle_base_key` — render.py:2554), 검증 계약이 요구하는 **60/120/168열 `--once` 렌더 + 디자인 critic 비평**(태스크 "검증 계획에 반드시 포함")은 `--once`에서 과정 뷰를 그릴 수 없으면 **수행 자체가 불가능**하다. `render_once`(render.py:2082)는 키 입력을 받지 않는다.

→ `fleet.py`에 `--view {group,process}` (default `group`)를 **additive**로 추가한다. `p` 키와 `--view process`는 **같은 전역 `_PROCESS_VIEW` 하나**를 쓴다(결정 경로 단일화 — F-27의 "kill 결정 경로는 하나" 동형). `p` 토글이 규범 진입이라는 prd 계약은 불변이고, `--view`는 그것의 비대화식 투영이다. 기존 argparse 키 불변 → `--json`/기존 플래그 회귀 0.

### P4 checklist.md 위치 = 사이클 루트 (`plan/` 아님)

v9 실측: `plans/2026-07-15_fleet-v9-mouse-subagent/checklist.md` (루트), `plan/plan.md`(하위). route record의 execute 노드 `write_scope`가 루트 `checklist.md`를 포함한다(execute가 체크오프 주체). 본 스테이지 산출도 이 배치를 따른다.

---

## 2. 스텝 요약 · 의존 사슬

| Step | 내용 | 산출 | 선행 |
|---|---|---|---|
| **1** | F-28a — `route.py` 신설 + collector 소비 + `--json route` | `route.py`, `dispatch.py`, `model.py`, `fleet.py`, 픽스처 | — |
| **2** | F-28b — route-aware breadcrumb (DAG 생성, 자식 실측 점등) | `render.py` | 1 |
| **3** | F-30 — 과정 뷰 (`p`/`--view`, 카드, 병렬 분기, 마우스 접기, degrade) | `render.py`, `fleet.py` | 1, 2 |
| **4a** | F-28c — governor lease 1행 (**실재 → 구현**) | `collectors/governor.py`, `render.py` | — (1과 무관) |
| **4b** | F-28c — run registry **스킵 + 이월 기록** | `_internal/carryover.md` | — |
| **5** | 통합 검증 · 3폭 렌더 · 디자인 critic · 미러 동기 | `test_logs/`, 미러 | 1-4 |

**실제 의존**: Step 2·3은 Step 1의 `route.py` API에 의존한다(하드 의존). Step 4a는 완전 독립 — Step 1이 막히면 4a를 먼저 진행해도 된다. Step 3은 Step 2의 노드 상태 판정(§4.3 표)을 재사용한다(중복 구현 금지).

**execute는 단일 depth-2 워커** → 스텝 순서가 곧 계약이다. 각 스텝 종료 시 전체 테스트 회귀를 돌리고 dev_log를 남긴다.

---

## 3. Step 1 — F-28a route record 소비 (prd.md:302)

### 3.1 신설: `tools/fleet/route.py` (`model.py`의 형제 — zero-dep stdlib)

`dispatch.py`는 이미 1043행이다. route 파싱·캐시·DAG·요약을 거기 얹으면 collector가 두 가지 일을 하게 된다. `model.py`가 "스키마 + 분류기"를 소유하듯 `route.py`가 "route record 해석"을 소유한다. `render.py`와 `fleet.py`가 **둘 다** 이 지식을 필요로 하므로(collector 전용이 아님) collectors/ 아래가 아니라 패키지 루트에 둔다.

```python
# tools/fleet/route.py — read-only. write API 없음(§7 G3가 강제).
_CACHE = {}                       # {abspath: (mtime, size, record|None)}

def load(path, expect_hash=None, expect_id=None):
    """record dict | None. 어떤 실패도 raise하지 않는다 — None = 조용한 pipe 휴리스틱 fallback."""
    # 1. abspath, os.stat → (mtime, size). 캐시 히트(동일 mtime+size)면 즉시 반환 → tick당 재파싱 0.
    # 2. OSError(부재·/tmp 휘발·권한) → None 캐시(negative caching도 mtime 키를 못 얻으므로
    #    경로 키에 (None, None, None)으로 저장, 다음 tick에 stat 재시도 = 1회 stat 비용).
    # 3. json.JSONDecodeError / 비-dict → None
    # 4. schema_version != 1 → None (미래 스키마를 추측 해석하지 않음, prd.md:481 동기 의무)
    # 5. 무결성: record["route_hash"] == route_hash(record) 그리고
    #           record["route_id"] == "rt-" + hash 파생  (P1)
    # 6. pipe 대조: expect_hash/expect_id가 주어졌고 record 값과 다르면 → None
    # 7. nodes 형태 최소 검증: list이고 각 원소가 dict이며 "id"가 str → 아니면 None
def route_hash(record): ...        # capability-route.py:21-26 동형 (P1)
def node_order(record):            # depends_on DAG → 결정적 위상 정렬 + 병렬 그룹
    """[[node,…], …] — 레벨 리스트. 같은 레벨 = 병렬 분기(F-30 세로 분기의 근거)."""
def build_views(jobs, node_evidence): ...   # §3.3
def summary(view): ...                      # §3.4 --json
def clear_cache(): ...                      # 테스트 hermeticity (model.reset_state_tracker() 선례)
```

**`node_order` 계약** (Step 2·3이 공유하는 유일한 DAG 소스):
- Kahn 레벨 정렬. 같은 레벨 내 순서 = **record의 `nodes[]` 원순서**(사전순 아님) — 컴파일러가 쓴 순서가 사용자가 읽을 순서다. 결정적이어야 렌더가 tick마다 흔들리지 않는다.
- 사이클/미지 `depends_on` 참조 → 해당 노드를 **마지막 레벨에 원순서로 배치**하고 record 자체는 살린다(tolerant — 표시가 조금 이상해도 회귀 0이 낫다).
- 실측 두 record 모두 `plan→execute→test→report` 선형 = 레벨 4개 × 노드 1개. 병렬 분기는 합성 픽스처로만 검증 가능(§3.5).

### 3.2 `collectors/dispatch.py` 편집 표면 (최소)

| 위치 | 변경 |
|---|---|
| `_parse_pipe_meta` (dispatch.py:74) | **변경 없음** — 이미 `route_file=`/`route_id=`/`route_hash=`/`route_node=`를 tolerant하게 파싱한다(SD-F4 연속 토크나이저, `key=value` 무제한). 실측 jobs.log 행으로 확인. **여기를 건드릴 이유가 없다.** |
| `_scan_jobs_log` (dispatch.py:816) | `meta.get("route_file"/"route_id"/"route_hash"/"route_node")`를 `DispatchJob`에 부착(§3.2.1). |
| `_scan_processes` (dispatch.py:710) | proc 잡: env **`AGENT_ROUTE_FILE` / `AGENT_ROUTE_ID` / `AGENT_ROUTE_NODE`** 부착(§3.2.2 — 실명 확인됨). 리더는 기존 `procscan.read_environ`(procscan.py:31, dispatch.py:724가 이미 호출) 재사용. |
| `_scan_route_nodes(paths)` **신설** | §3.3 — 종단 행 포함 전량 스캔. `_jobs_log_fields`(dispatch.py:884) 선례대로 **파일을 다시 읽는다**(§3.2.3). |
| `collect()` (dispatch.py:975) | 말미에 `collect.last_route_nodes = _scan_route_nodes(paths)` 스태시. `collect.last_malformed`(dispatch.py:1039·1043) 선례와 동형. |

#### 3.2.2 ★ proc 잡 route env는 실재한다 — 실명 확정 (plan-review Y3)

초판은 env 이름을 `AGENT_DISPATCH_ROUTE_FILE`로 **추측**했다. 그런 이름은 없다. 실측 확인된 이름(`adapters/claude/bin/dispatch-headless.py:720-722`, codex·opencode 어댑터도 동일 export):

| env | 용도 |
|---|---|
| `AGENT_ROUTE_FILE` | record 경로 |
| `AGENT_ROUTE_ID` | `load(expect_id=…)` 대조 |
| `AGENT_ROUTE_NODE` | 이 잡이 실행 중인 노드 id |

**`AGENT_ROUTE_HASH`는 export되지 않는다** → proc 잡은 `expect_hash` 대조 **불가**, `expect_id`만 가능. `load()`는 두 인자를 독립적으로 받으므로(§3.1) 그대로 성립한다 — 무결성 축(hash 재계산)은 record 자체로 여전히 검증된다.

**이것이 중요한 이유**: 본 사이클의 간판 실측 케이스(`fleet-v10-plan`, pid 3555317)가 바로 **proc 잡**이다. 여기를 결손으로 두면 데모·critic 화면이 degrade 카드만 남는다. jobs.log backfill 경로(`_jobs_log_fields`, dispatch.py:884가 이미 proc 잡에 mode/profile을 채우는 선례)로도 보강 가능하다.

#### 3.2.3 `_scan_route_nodes`는 파일을 다시 읽는다 (모순 해소 — plan-review Y5)

초판은 §3.2에서 `_scan_route_nodes(paths)`(재읽기 함의)라 하고 §3.6/checklist에서는 "`rows` 재사용, 파일 재open 금지"라 했다 — **모순**이다. `rows`는 `_scan_jobs_log`의 지역 변수(dispatch.py:820-821)이고 `collect()`는 `paths`만 쥔다. 공유하려면 `_scan_jobs_log` 시그니처를 바꿔야 하는데, 그 함수는 F-15c dedup 계약의 중심이라 손대는 비용이 이득보다 크다.

**확정: 재읽기.** `_jobs_log_fields`(dispatch.py:884)가 이미 같은 파일을 두 번째로 읽는 **기존 선례**이고, jobs.log는 수백 행 규모의 로컬 파일이다(fleet은 이미 tick마다 `ps`를 spawn한다 — 그에 비하면 무시할 만하다). 최적화가 필요해지면 그때 `rows` 공유로 리팩터링한다.

#### 3.2.1 `model.DispatchJob` 신규 필드 (additive, 4개 전부 `Optional[str] = None`)

```python
route_file: Optional[str] = None    # pipe route_file= (레코드 경로 — /tmp 휘발 가능)
route_id:   Optional[str] = None    # pipe route_id=
route_hash: Optional[str] = None    # pipe route_hash=
route_node: Optional[str] = None    # pipe route_node= — 이 잡이 실행 중인 노드 id
```

**record 본문 자체는 `DispatchJob`에 넣지 않는다.** 이유: 실측 record는 300행이 넘고(`nodes[].dispatch_fallback[]`가 대부분), `asdict()`로 `--json`에 잡마다 통째로 실리면 스냅샷이 수십 배로 붓는다. 본문은 `route._CACHE`가 소유하고 잡은 `route_id`(가벼운 키)만 든다.

### 3.3 ★ 노드 상태의 근거 — "완료 노드는 잡 목록에 없다"

**설계상 가장 놓치기 쉬운 지점이다.** `_scan_jobs_log`(dispatch.py:843-846)는 최신 상태가 종단(`done`/`killed`/…)인 행을 **classification 전에 버린다**. 그래서 `collect()`가 돌려주는 `jobs`에는 **끝난 노드가 아예 없다**. 여기에만 의존하면 F-30 카드의 `✓ 완료`(prd.md:307)를 영원히 그릴 수 없다 — 방금 끝난 plan 노드가 `○ 미기동`으로 보인다.

→ `_scan_route_nodes(paths)` 신설: **종단 행을 버리지 않는** 별도 read pass. 같은 파일을 이미 읽고 있으므로 추가 I/O는 없다(같은 `rows`를 재사용하도록 구현할 것 — 파일 재open 금지).

```python
# {route_id: {node_id: {"status", "slug", "ts", "pid", "harness", "model", "effort"|"reasoning",
#                       "completion_gate", "note", "elapsed_min"}}}
# 규칙: (route_id, route_node) 키에 대해 last-occurrence-wins — _scan_jobs_log:830-842의
#       "slug 최신 행이 이긴다" 재조정과 동형(같은 노드의 재시도 행이 여러 개일 수 있다).
```

노드 상태 판정표 — **Step 2(breadcrumb)와 Step 3(카드)이 공유하는 단일 판정**. 두 곳에 복제 금지, `route.build_views()` 한 곳에서 계산한다.

| 글리프 | 상태 | 근거 (우선순위 순) |
|---|---|---|
| `●` active | 실행 중 | **live 잡 실측 우선(SD-F2 불변, prd.md:303)** — `jobs` 중 `route_node == node.id` 이고 `liveness == "working"`. 경과·모델·effort는 이 잡 행에서 온다. |
| `✕` failed | 실패 | live 잡 `liveness in ("stale","dead")`, 또는 registry 최신 행 `status in ("killed","cancelled")`, 또는 `status=="done"`인데 `note`가 실패 마감(`fleet-kill`/`dead-*`) |
| `✓` done | 정상 마감 | registry 최신 행 `status == "done"` **이고 위 `note` 실패 마감이 아님**. 경과 = 그 행 ts 기준. |
| `○` pending | 미기동 | 위 어디에도 해당 행이 없음 |

`●`가 `✓`를 이긴다(live 실측이 registry 기록을 이긴다 — F-25 tier 순서 동형: tier-2 proc > tier-1/3 기록). 한 노드에 live 잡과 done 행이 동시에 있으면 **재시도 중**이라는 뜻이고, 사용자가 봐야 하는 것은 지금 도는 쪽이다.

#### 3.3.1 ★★ `completion_gate=`는 gate **통과** 증거가 아니다 (plan-review B1 — 실측 반증)

초판은 `✓`의 근거를 "`completion_gate=` 필드 존재 = gate 통과"로 잡았다. **틀렸다.** `completion_gate=`는 **launch 시점 선언**이다(`adapters/claude/bin/dispatch-headless.py:389` — `args.completion_gate`를 그대로 pipe에 박는다). 실측 반증 2건:

- `fleet-v10-plan` — `status=open`인데 `completion_gate=code-plan` 보유 → **끝나지도 않은 노드가 "gate 통과"**로 판정된다.
- `fleet-v9-report` — `status=done,note=dead-report-done` + `completion_gate=code-report` → **죽은 노드가 "gate 통과"**로 판정된다.

더 나아가 **`status=="done"`조차 성공과 동치가 아니다**: prd.md:284는 fleet이 kill한 잡의 row를 `done,note=fleet-kill`로 마감한다고 규정한다. 그래서 위 표의 `✓`는 `note` 실패 마감을 배제한다.

**계약**:
- `completion_gate` 값은 **게이트 이름 표기 전용**이다(`a` 상세에서 dim). 통과 여부로 해석 금지.
- **gate 통과 여부는 현재 정직한 결손(`—`)이다.** prd.md:307이 요구하는 "completion gate 통과 여부"를 지금 있는 증거로는 말할 수 없다. 없는 근거로 ✓를 그리는 것은 prd.md:292 "추측 표시 금지" 위배이고, F-28의 존재 이유("정책 따로 표시 따로"의 제거)를 정면으로 뒤집는다.
- **Step 1이 먼저 probe한다**: jobs.log/artifact에 gate-pass의 실 증거(예: 게이트 훅이 남기는 별도 마커)가 실재하는가. 실재하면 표에 편입, 부재하면 **P2와 동일한 방식으로 이월 기록**(`_internal/carryover.md`)하고 결손으로 남긴다. **추측 매핑 금지.**

`build_views(jobs, node_evidence)` 는 **순수 함수** — 파일 I/O도 시계도 만지지 않는다(경과 계산용 `now`는 인자로 받는다). 그래야 픽스처만으로 전 분기를 테스트할 수 있다.

### 3.4 `--json` additive — `route` 키 (prd.md:302)

`fleet.py:_snapshot_json`(fleet.py:77)에 **최상위 `route` 키 1개** 추가. 기존 `sessions`/`jobs`/`summary` 키(+조건부 `memory`)와 그 값은 **불변**(`jobs[]` 원소에 §3.2.1의 4개 키가 느는 것은 additive — 기존 키 삭제·개명 0).

```json
"route": [
  {"route_id": "rt-27f7bc9ff152ba13",
   "route_hash": "sha256:27f7bc9f…",          // 전체 값 (id는 축약형이므로 원본 보존)
   "source": "record",                          // record | heuristic  ← degrade 구분
   "capability": "autopilot-code", "capability_mode": "dev",
   "execution_topology": "staged", "effective_intensity": "standard",
   "progress": {"done": 1, "total": 4},
   "nodes": [{"id": "plan", "depends_on": [], "level": 0, "state": "done",
              "gate": "code-plan", "note": null, "elapsed_min": 12,
              "model": "opus", "harness": "claude"}, …]}
]
```

- `gate_passed` 키는 **만들지 않는다**(§3.3.1 — 통과 증거가 없다). `gate`는 이름, `note`는 마감 사유 원문. `state`는 §3.3 표의 4값(`active`/`done`/`failed`/`pending`)만 쓴다.
- `route`는 **요약**이다(prd.md:302 "요약: capability/topology/nodes 진행/route_id"). `dispatch_fallback`/`tracked_gate_evidence`/`selection` 등 record 원문은 싣지 않는다.
- record 없는 잡의 route는 `source: "heuristic"`으로 실을 수 있으나, **route_id가 없으면 키를 만들지 않는다** — 빈 route_id로 묶은 유령 항목 금지. 즉 `route` 배열 원소는 최소한 route_id를 가진다.
- `mem`(fleet.py:90-92) 선례대로 **best-effort**: `route.py` 전체를 `try/except`로 감싸 어떤 실패도 `--json`을 깨뜨리지 못하게 한다.

### 3.5 픽스처 (`tools/fleet/tests/fixtures/route/`)

`/tmp`는 휘발한다 — **복사본이 정본**이다. (`agent-note-d1-route.json`은 plan 시점 아직 존재했으나 그 위치가 휘발성이라는 점 자체가 F-28a tolerant 계약의 실증 근거다.)

| 파일 | 출처 | 역할 |
|---|---|---|
| `real_claude_staged.json` | `/home/Uihyeop/agent_setting/.dispatch/logs/fleet-v10-process-view.route.json` **원문 그대로 복사** | rt-27f7bc9ff152ba13. hash 재계산 일치(T1-4)·선형 DAG·claude/opus |
| `real_codex_staged.json` | `/tmp/agent-note-d1-route.json` **원문 그대로 복사** | rt-1120bb39a13c4191. 휘발 위치 실증·codex/gpt-5.6·`dispatch_evidence.tuples[].status == "unsupported"` 후보 포함 |
| `synth_parallel_lab.json` | **신설 합성** | §3.5.1 |
| `synth_broken_hash.json` | real_claude에서 `capability` 1글자 변조(route_hash는 그대로) | hash 불일치 → `load()` None → 조용한 fallback |
| `synth_bad_schema.json` | `schema_version: 2` | 미래 스키마 거부 |
| `jobs_route.log` | 실측 `jobs.log` 행 4개를 그대로 발췌(탭 6필드 보존) | `route_file=`/`route_id=`/`route_hash=`/`route_node=` 실측 pipe 문자열. **done 행 포함**(§3.3 종단 행 근거) |

**`jobs_route.log`에 넣을 실측 행**(값은 원문 유지, 경로만 픽스처 tmpdir로 치환):
- `fleet-v10-plan` — `open`, `route_node=plan`, `pid=3555317`, `model=opus,effort=high`, route_file=**절대경로 실재**
- `fleet-v9-report` — `done`, `route_node=report`, `route_file=/tmp/fleet-v9-route.json`(**휘발 — 부재 fallback 실증**)
- `v93-reading-face-d1-test-r6` — `done`, `route_node=test`, codex, `route_file=/tmp/agent-note-d1-route.json`
- `v94-note-db-steward-research` — `open`, `route_node=research`, capability=**autopilot-spec**(code 4단이 아닌 파이프 실측)

#### 3.5.1 `synth_parallel_lab.json` — 병렬 분기 필수 (태스크 명시)

code 4단이 **아닌** 모양이어야 한다. `capabilities/topologies.json` 실재를 참고하되, 픽스처는 자립적으로 작성한다.

```
capability: autopilot-lab, capability_mode: eval, execution_topology: staged (schema_version 1)
nodes:
  setup     depends_on []                          level 0
  eval-asr  depends_on ["setup"]  ┐                level 1  ← 병렬 (depends_on 겹침)
  eval-sep  depends_on ["setup"]  ┤ 3-way fan-out  level 1
  eval-vad  depends_on ["setup"]  ┘                level 1
  aggregate depends_on ["eval-asr","eval-sep","eval-vad"]   level 2  ← fan-in
  report    depends_on ["aggregate"]               level 3
```
- 태스크 요구 "depends_on이 겹치는 노드 2개+"를 3개로 충족하고, **fan-in**(다중 depends_on)까지 덮는다 — fan-out만 있으면 `node_order`의 레벨 계산 오류를 놓친다.
- `route_hash`/`route_id`는 §3.1 `route_hash()`로 **생성해서 박아 넣는다**(손으로 쓴 가짜 해시 금지 — `load()`가 즉시 거부한다). 생성 절차를 `tests/fixtures/route/README.md`에 1줄 기록.
- `eval-sep` 노드는 **`✕` 실패**로 놓을 수 있게 registry 행 픽스처를 곁들인다(Step 3의 "실패 노드 포함 route 자동 펼침 + 적색" 검증 입력).

### 3.6 Step 1 검증

```bash
cd /home/Uihyeop/agent_setting-wt/fleet-v10-process-view
python3 -m unittest tools.fleet.tests.test_f28_route -v      # 신설
python3 -m unittest discover -s tools/fleet/tests -t .        # 468 + 신규, 회귀 0
```

신설 `tests/test_f28_route.py` (unittest only, `tempfile.TemporaryDirectory` + `mock` — `test_dispatch.py` 선례):

| id | 케이스 | 기대 |
|---|---|---|
| T1-1 | `load(real_claude_staged.json)` | dict, `route_id == "rt-27f7bc9ff152ba13"` |
| T1-2 | `load(real_codex_staged.json)` | dict, `route_id == "rt-1120bb39a13c4191"` |
| T1-3 | `load("<없는 경로>")` | `None`, **raise 없음** |
| T1-4 ★ | 두 실측 record: `route_hash(rec) == rec["route_hash"]` | True (P1 회귀 방지 — 계산식이 바뀌면 여기서 죽는다) |
| T1-5 | `load(synth_broken_hash.json)` | `None` |
| T1-6 | `load(synth_bad_schema.json)` | `None` |
| T1-7 | `load(real, expect_hash="sha256:deadbeef")` | `None` (pipe 대조 실패) |
| T1-8 | 캐시: 같은 경로 2회 `load` | `json.load` 호출 1회 (`mock.patch`로 카운트) |
| T1-9 | 캐시 무효화: `load` → 파일 mtime+내용 변경 → `load` | 새 record 반환 |
| T1-10 | `node_order(synth_parallel_lab)` | `[[setup],[eval-asr,eval-sep,eval-vad],[aggregate],[report]]` |
| T1-11 | `node_order` — 사이클 record | raise 없음, 전 노드 포함 |
| T1-12 | `collect(jobs_path=jobs_route.log)` | 잡에 `route_id`/`route_node` 부착, `/tmp` 부재 record 행도 잡은 **살아 있다** |
| T1-13 ★ | `collect.last_route_nodes[rt-…]["report"]["status"] == "done"` | 종단 행이 증거로 살아남음(§3.3) |
| T1-14 | `build_views`: live working 잡 + done 행 동시 | 노드 state `active`(`●`가 `✓`를 이긴다) |
| T1-15 | `build_views`: 실패 행 | state `failed` |
| T1-16 | `--json` additive | 기존 4키 그대로 + `route` 키 존재, `jobs[0]`의 기존 키 전부 보존 |
| T1-17 | route record 전무 | `route == []`, 기존 출력과 diff 없음 |

**acceptance**: 회귀 0 · `load()`가 어떤 입력에도 raise하지 않음 · record 없는 환경의 `--json`이 v9와 동일(`route` 키 및 jobs[]의 신규 4키 제외).

**리스크**: `_scan_route_nodes`가 jobs.log를 다시 열어 tick 비용 2배 → `_scan_jobs_log`가 이미 읽은 `rows`를 공유하도록 구현(파일 재open 금지). 검토 포인트로 dev_log에 명시할 것.

---

## 4. Step 2 — F-28b route-aware breadcrumb (prd.md:303)

### 4.1 문제 (실측)

`render.py:544 _PIPE_STAGES` 는 5개 capability의 3단 시퀀스를 **하드코딩**한다:
```python
_PIPE_STAGES = {"code": ["plan","exec","test"], "spec": ["spec","design","dev"],
                "research": ["search","analyze","report"], …}
```
실측 record의 code 파이프는 **4단**(`plan→execute→test→report`)이고, 실측 `jobs.log`에는 `capability=autopilot-spec, route_node=research`(=`v94-note-db-steward-research`)처럼 이 표에 **없는 노드**가 실재한다. 하드코딩 표는 실제 topology와 이미 어긋나 있다.

### 4.2 편집 표면

| 위치 | 변경 |
|---|---|
| `_stage_segs(key, stage, working, max_width)` (render.py:680) | `route_seq=None` 인자 **추가**(기본 None = 기존 동작 100% 보존). 주어지면 `seq = route_seq`, `_PIPE_STAGES.get(key)` 조회(render.py:694)를 건너뛴다. |
| `_dispatch_stage_segs(j, …)` (render.py:736) | depth-1 conductor 경로에서 `route.build_views()`의 노드 리스트 → `route_seq` 구성 후 전달. depth≥2 미세 상태 경로(render.py:741-749)는 **불변**(P0-1 계약). |
| `_conductor_stage_override(job)` (render.py:1916) | route 있는 잡: 자식 매칭을 `worker_role`→`_STAGE_ROLE` 표 대신 **`route_node` 우선**으로. `route_node`가 없으면 기존 `_STAGE_ROLE` 경로로 폴백. |
| `_PIPE_STAGES` (render.py:544) | **삭제하지 않는다** — record 없는 잡의 유일한 근거(prd.md:303 "record 없는 잡은 기존 breadcrumb 유지"). |

### 4.3 계약

- **자식 실측 우선(SD-F2 불변)**: 어떤 노드가 켜지는지는 record가 아니라 §3.3 판정표가 정한다. record는 **레일(어떤 노드가 어떤 순서로 있는가)**만 제공하고, **점등**은 실측이 한다. record가 `plan→execute→test→report`라 해도 도는 자식이 없으면 아무 노드도 `●`가 아니다.
- **폭**: `_STAGE_ZONE_MAX = 30`(render.py:657) 불변. 4단 이상 시퀀스는 `_drop_past_stages`(render.py:666)가 과거부터 접는다 — 이미 SD-F2 계약대로 활성 노드를 마지막까지 살린다. **새 폭 상수 만들지 말 것.**
- **라벨**: 노드 id를 그대로 쓴다(`execute`, `eval-asr`). `_PIPE_STAGES`의 `exec` 축약과 다르지만, record 노드 id는 **파이프의 진짜 이름**이고 임의 capability에서 축약표를 유지하는 것은 불가능하다. 폭 초과는 `_drop_past_stages`가 처리한다.
- record 있는데 `node_order`가 빈 리스트 → `route_seq=None`으로 전달(= 기존 경로).

### 4.4 Step 2 검증

`tests/test_f28_breadcrumb.py` 신설:

| id | 케이스 | 기대 |
|---|---|---|
| T2-1 | record 없는 code 잡 | breadcrumb == v9와 동일(`plan › exec › test`) — **회귀 0의 핵심** |
| T2-2 | real_claude record + execute 자식 working | `plan✓ › execute › test › report`, execute 점등 |
| T2-3 | synth_parallel_lab + `eval-sep` working | 노드 라벨이 `_PIPE_STAGES`에 없어도 정상 렌더 |
| T2-4 | record 있는데 자식 0 | 전 노드 unlit (SD-F2 — record가 점등하지 않는다) |
| T2-5 | 60열 4단+ | `_STAGE_ZONE_MAX` 초과 0, 활성 노드 생존 |
| T2-6 | autopilot-spec `route_node=research` | 실측 pipe 기반 렌더 성공 |

**acceptance**: T2-1이 v9 출력과 문자열 동일 · 3폭 zone 오버플로 0.

---

## 5. Step 3 — F-30 과정 뷰 (prd.md:304-310) ★ 본 사이클 핵심 · 신규 화면

### 5.1 진입 · 전역 상태

```python
_PROCESS_VIEW = False          # render.py 전역 (기존 _SHOW_ALL:1425 / _LAYOUT:61 과 동렬)
def set_process_view(v): ...   # set_show_all(render.py:1510) 선례
```
- `p` 키: `_handle_base_key`(render.py:2554)에 `elif ch in (ord("p"), ord("P")): set_process_view(not _PROCESS_VIEW)` 추가. **`w`(`_cycle_layout`, render.py:66)와 직교** — 과정 뷰 안에서도 `w`는 계속 레이아웃을 바꾼다(prd.md:305 "기존 w 레이아웃 cycle과 직교").
- `--view process`(P3): `fleet.py`가 `render.set_process_view(True)` 호출. `--once`/라이브 공통.
- footer(`_footer_segs`, render.py:2747) base 분기에 `p process`(또는 활성 시 `p group`) 세그 추가. `_MOUSE_HINT_MIN_WIDTH = 100`(render.py:2742) 선례대로 **60열에서는 생략**할 수 있다 — 60열 footer가 이미 빡빡하다. 폭 사다리는 실측 후 결정하고 dev_log에 근거를 남길 것.

### 5.2 분기 지점 (단 한 곳)

`_build_lines(...)`(render.py:1515)의 `_SELECTABLE` 리셋(render.py:1528) **직후**:
```python
if _PROCESS_VIEW:
    return _build_process_lines(sessions, jobs, malformed, memory, term_width, layout)
```
- `_build_lines`의 반환 계약(`[[(text, key), …] | None]`)을 그대로 지킨다 → `_draw`(render.py:2774)·`render_once`(render.py:2082)·`_addline`(render.py:2189)·스크롤·`_clamp_offset` 전부 **무수정 재사용**.
- `_SELECTABLE`은 과정 뷰에서도 세션/잡 축약행에 대해 채운다 → **F-27 kill 경로가 과정 뷰에서도 그대로 산다**(`_CLICK_ROWS`가 `_SELECTABLE` 기준 — v9 계약 §4.2.1).
- pulse 행(index 1)·malformed·memory 헤더는 **공통 헤더 헬퍼로 재사용**한다(그룹 뷰와 과정 뷰가 헤더를 두 벌 갖지 않게).

### 5.3 카드 구성 (prd.md:306-308)

**단위 = 활성 route 1개**(프로젝트 그룹이 아니라 파이프라인 중심 재그룹).

```
[code·dev·standard] rt-27f7bc9f — 1/4 nodes ⏳38m                    ← L1
  plan ✓12m › execute ● 8m (opus·high) › test ○ › report ○           ← L2 (가로 흐름)
    └▸🚀 fleet-v10-execute  claude  opus  ⏳8m                        ← 활성 노드 담당 행
       └⚡ explore ⏳2m                                                ← F-29 재사용
```

병렬 분기(prd.md:307 "depends_on이 병렬인 노드는 세로 분기(들여쓴 병렬 행)"):
```
[lab·eval·standard] rt-a1b2c3d4 — 1/6 nodes ⏳22m
  setup ✓5m ›
    ├ eval-asr ● 9m (sonnet·medium)
    ├ eval-sep ✕ 3m                     ← 실패 = 적색, route 자동 펼침
    └ eval-vad ○
  › aggregate ○ › report ○
```

- **L1**: `[capability·mode·intensity] <route_id 단축> — <n/m nodes> ⏳<경과>`.
  - capability는 `autopilot-` 접두 제거(`_strip_autopilot_prefix`, dispatch.py:68 재사용).
  - route_id 단축 = `rt-` + 앞 8자(예 `rt-27f7bc9f`). 전체 값은 `--json`에 있다(§3.4).
  - `n/m` = `done` 노드 수 / 전체 노드 수. 경과 = 그 route의 가장 이른 노드 행 ts 기준.
- **L2 글리프**(prd.md:307): `✓` 완료 / `●` 활성+경과+모델 / `○` 미기동 / `✕` 실패. 판정은 **§3.3 표 단일 소스**.
  - `●` 노드만 모델·effort를 단다(`(opus·high)`) — 전 노드에 달면 줄이 터진다.
  - **gate 통과 글리프를 만들지 않는다**(§3.3.1 — 증거 부재). `a` 상세에서 gate **이름**만 dim으로 표기한다.
  - ★ **접힘 카드 라벨에 `folded`/`hidden` 단어를 쓰지 않는다** — `_draw`(render.py:2813-2816)가 단일 세그먼트 행의 텍스트에 이 단어가 있으면 `a` 토글 행으로 **하이재킹**한다(§5.4 B2).
- **결손 degrade 카드**(prd.md:310 — 빈칸 아님):
  ```
  [code·dev] fleet-ui-v2 — no route record — plan › exec › test        ← 기존 _PIPE_STAGES 휴리스틱
  ```
  `source: "heuristic"`. record 부재/hash 불일치/`/tmp` 휘발 전부 이 카드로 떨어진다. **route_id가 없으므로 카드 키는 conductor slug**다.
- **`tracked_gate_evidence`는 `a` 토글에서만 dim**(prd.md:310). 기본 화면 노출 금지.

#### 5.3.1 ★ F-29 중첩은 "재사용"이 아니다 — pid 조인이 신규 작업이다 (plan-review Y1)

prd.md:308은 "활성 노드 아래 세션 행 + 그 서브에이전트 `└⚡`(F-29 재사용)"를 요구한다. 그런데:

- `subagents`는 **`Session`에만** 있다(model.py:170). 노드를 실행하는 주체는 **`DispatchJob`**이고 거기엔 그 필드가 없다.
- 서브에이전트 행 emit도 **세션 루프 안에만** 있다(render.py:1965-1969).
- render는 job↔session을 **pid로 짝짓지 않는다** — `parent_sid`/`parent_cwd`로만 묶는다(render.py:1788-1790).

**재사용되는 것은 `_subagent_row()`(render.py:1496)와 `_ICON_SUBAGENT` 뿐이고, 조인은 새로 짜야 한다.** 실현은 가능하다: 분기점(render.py:1528)이 `is_child` 필터(render.py:1545)보다 **앞**이므로 `_build_process_lines`는 자식 세션을 포함한 전체 `sessions`를 받는다.

계약: `{s.pid: s for s in sessions if s.pid}` 인덱스 → 활성 노드의 `job.pid`로 조회 → 매칭 세션의 `subagents`를 `_subagent_row()`로 emit. 매칭 실패·`subagents is None` → **⚡ 행 생략**(prd.md:294 결손 원칙 — 빈 행도 추측도 아님). T3-7이 이 조인을 공짜로 가정하지 않도록 checklist에 독립 항목으로 올린다.

### 5.4 접기 · 마우스 (prd.md:309 — F-27 문법 재사용)

```python
_ROUTE_FOLD = {}     # {card_key: bool}   — True = 접힘. 사용자 명시 조작만 기록.
_FOLDABLE   = []     # [{"line": idx, "card_key": …}]  — _build_process_lines가 채운다 (line index!)
_FOLD_ROWS  = {}     # {screen_row: card_key}  — _draw가 offset 적용해 tick마다 재구성
```

★ **2단 구조를 지킬 것**(plan-review Y2): 기존 마우스 맵은 `_SELECTABLE`(line index, `_build_lines`가 채움) → `_draw`가 스크롤 offset 적용 → `_CLICK_ROWS`(screen row)의 2단이다(render.py:2808-2820). `_FOLDABLE`(line index) 없이 `_FOLD_ROWS`만 선언하면 **`_draw`가 그것을 만들 소스가 없다**. `_CLICK_ROWS` 옆에 같은 idiom으로 붙인다.

기본 접힘 규칙(사용자 조작이 없을 때):
| route 상태 | 기본 |
|---|---|
| 실패 노드 포함 | **자동 펼침 + 적색 강조** (prd.md:309) |
| 전 노드 done | **1행 접힘** (prd.md:309) |
| 그 외(활성) | 펼침 |

`_ROUTE_FOLD`에 명시 항목이 있으면 그것이 이긴다(사용자 의사 > 기본). 카드가 사라지면 키도 제거(누수 방지 — `StateTracker.sweep()`, model.py:344 정신).

`_handle_mouse`(render.py:2592) 우선순위 — **기존 4단에 1단 삽입**:
1. `_PROMPT` → `_PROMPT_HITS`만 유효, 그 외 클릭 **삼킴**(불변)
2. `_TOGGLE_ROWS` → `a` 토글(불변)
3. **`_FOLD_ROWS` → 카드/노드 접기·펼치기 (신규)**
4. `_CLICK_ROWS` → 행 선택 / 재클릭 = kill 요청(불변)
5. 그 외 → `_exit_select()`(불변)

**★ 불변식 (plan-review B2로 확장)**: `_FOLD_ROWS ∩ (_CLICK_ROWS ∪ _TOGGLE_ROWS) = ∅`. 겹치면 클릭 1회가 두 뜻이 된다. **`_CLICK_ROWS`만 배제하는 것으로는 부족하다** — 진짜 위험은 `_TOGGLE_ROWS`다:

```python
# render.py:2813-2816 — toggle 행 판정은 텍스트 substring 휴리스틱이고 else로 배타적이다
if segs is not None and len(segs) == 1 and (
        "hidden" in segs[0][0] or "folded" in segs[0][0]):
    _TOGGLE_ROWS[row] = True
else:                     # ← toggle로 잡히면 _CLICK_ROWS/_FOLD_ROWS에 영영 못 들어간다
```

"전 노드 done → 1행 접힘" 카드는 **단일 세그먼트 행**이고, `folded`/`hidden`은 이 코드베이스의 기존 접힘 어휘다(render.py:1975 `+%d stale/companion hidden`). 그 단어가 라벨에 들어가는 순간 rung 2(`set_show_all`)가 클릭을 삼키고 카드는 **절대 펼쳐지지 않는다** — `_handle_mouse`에 도달하기도 전에 `_draw`에서 갈린다. "`_draw` 무수정 재사용"(§5.2)이 성립하는 범위의 유일한 예외이며, 초판 T3-9는 이 충돌을 **통과시켰다**. v9의 "toggle 행과 row map은 절대 겹치지 않는다"(render.py:2601-2602) 계약을 신규 맵으로 확장하는 것이다.

**안전 불변**: 과정 뷰는 **kill 경로를 새로 만들지 않는다**. 세션 축약행 클릭 = 선택뿐이고, 재클릭 → `_PROMPT` → `_handle_prompt_key`(render.py:2640, "control.kill_target에 도달하는 fleet의 유일한 경로")로 합류한다. `control.py`는 **한 줄도 건드리지 않는다**.

### 5.5 폭 (60/120/168)

`_STAGE_ZONE_MAX`가 아니라 카드 L2 전용 예산이 필요하다(카드는 들여쓰기가 다르다). 규칙:
- L2가 폭을 넘으면 `_drop_past_stages`(render.py:666) **재사용** — 과거 노드부터 접고 활성 노드를 마지막까지 살린다(SD-F2). 신규 절단 로직 금지.
- 60열: L1 `[code·dev·standard]` 태그가 이미 20열이다 → intensity를 먼저 떨어뜨리는 사다리(`_prompt_variants`, render.py:2397의 폭 사다리 idiom 재사용)를 쓴다. 구체 사다리는 **실측 후 결정**하고 dev_log에 3폭 캡처를 남길 것.
- 병렬 분기 들여쓰기는 60열에서 `├`/`└` 트리 글리프를 유지하되 모델 태그를 먼저 버린다.
- `_WIDE`(render.py:2117)에 새 글리프(`✕`, `●`, `○`, `✓`) 중 **전각인 것이 있는지 확인**하고 필요 시 등재 — 누락되면 폭 계산(`_dw`)이 어긋나 정렬이 깨진다. **놓치기 쉬운 지점.**

### 5.6 Step 3 검증

`tests/test_f30_process_view.py` 신설 — 전량 hermetic. **하네스가 두 가지다**(plan-review Y2 — 초판의 "전량 `_build_lines` 직접 호출"은 틀렸다):

| 대상 | 하네스 |
|---|---|
| 렌더 내용(T3-1~7, 12~14) | `render._build_lines(...)` 직접 호출 + `test_f29_subagents.py:195` 플래튼 idiom |
| **마우스·맵(T3-8~11)** | `_draw`가 채우는 맵(`_FOLD_ROWS`/`_CLICK_ROWS`/`_TOGGLE_ROWS`)을 보므로 **`test_f27_mouse.py:63-77`의 `FakeScreen` + `mock.patch.object(render.curses, "doupdate")` 하네스가 유일한 올바른 선례** — `_build_lines`만 부르면 이 맵들은 비어 있다 |

| id | 케이스 | 기대 |
|---|---|---|
| T3-1 | `_PROCESS_VIEW=False` | 기존 그룹 뷰와 **완전 동일**(v9 회귀 0) |
| T3-2 | real_claude record + 잡 | 카드 L1에 `rt-27f7bc9f`, `1/4 nodes` |
| T3-3 | synth_parallel_lab | `eval-asr/sep/vad`가 **같은 레벨의 들여쓴 병렬 행** |
| T3-4 | `eval-sep` 실패 | `✕` + 적색 키 + 해당 route **자동 펼침** |
| T3-5 | 전 노드 done | 기본 **1행 접힘** |
| T3-6 | record 없는 잡 | **degrade 카드**(빈 카드 아님) + `no route record` 문구 |
| T3-7 | 활성 노드 + F-29 subagents | `└⚡` 행 중첩(`_ICON_SUBAGENT` 재사용) |
| T3-8 | 카드 행 클릭 | `_ROUTE_FOLD` 토글, `_PROMPT` 미생성 |
| T3-9 ★ | `set(_FOLD_ROWS) & (set(_CLICK_ROWS) \| set(_TOGGLE_ROWS))` | **`== set()`** (§5.4 B2 — `_TOGGLE_ROWS` 포함이 핵심) |
| T3-9b ★ | 완료(접힘) 카드 행이 `_TOGGLE_ROWS`에 없다 | 접힘 카드 클릭 → `_SHOW_ALL` 불변, `_ROUTE_FOLD`만 토글 |
| T3-10 | 세션 축약행 클릭 → 재클릭 | `_PROMPT["stage"] == "confirm"` (F-27 문법 보존) |
| T3-11 | `_PROMPT` 떠 있을 때 카드 클릭 | **삼킴** — fold 안 됨(rung 1 불변) |
| T3-12 | `a` 토글 | `tracked_gate_evidence` dim 노출, 기본에선 부재 |
| T3-13 | 60/120/168 | 오버플로 0, 활성 노드 생존 |
| T3-14 | `--view process` + 잡 0 | 빈 화면 아님(정직한 "활성 route 없음") |

**acceptance**: T3-1·T3-9·T3-11이 통과 · 3폭 오버플로 0 · **디자인 critic 비평 완료**(§7 V3 — 신규 화면이므로 필수).

**리스크**: (a) 신규 화면 = 팔레트/글리프 어휘가 늘어난다 → 신규 색 키는 render.py 팔레트 표 **한 곳**에만 추가(`_STAGE_ZONE_MAX`, render.py:657의 "one constant, one place" 정신). (b) `_build_process_lines`가 커지면 `_build_lines`처럼 1000행 함수가 된다 → 카드 1장 = 헬퍼 1개(`_route_card(view, …)`)로 분리해 시작할 것.

---

## 6. Step 4 — F-28c (prd.md:311) — **분할 판정** (P2)

### 6a. governor lease — 실재 → 구현

`collectors/governor.py` 신설 (~40행, stdlib only):
```python
def collect():
    """{"active": n, "cap": m, "classes": {...}} | None. None = 소스 부재(정직한 결손)."""
    # 경로: $AGENT_MODEL_GOVERNOR_ROOT → $AGENT_ARTIFACT_ROOT/.runtime/model-worker-governor
    #       → dispatch._registry_home()/.agent_reports/.runtime/model-worker-governor
    #       (utilities/model-worker-governor.py:24-33 default_root() 동형. subprocess 금지 —
    #        artifact-root.sh를 tick마다 spawn하지 않는다.)
    # state.json read-only + mtime 캐시. cap = DEFAULT_TOTAL_LIMIT(=5, 같은 파일:20).
```

**★ read-only의 결과 — 죽은 lease를 직접 걸러야 한다**: governor는 **write 시점에** `process_starttime(pid) == lease["starttime"]`로 죽은 lease를 정리한다(`model-worker-governor.py:80-84`). fleet은 절대 write하지 않으므로, **state.json에는 이미 죽은 lease가 남아 있을 수 있다**. 그대로 세면 `⚙ governor 5/5`라고 거짓말한다. → fleet이 표시 전에 같은 판정을 **메모리에서** 적용한다: `procscan.read_proc_start(pid) == lease["starttime"]`인 lease만 센다(`procscan.read_proc_start`는 F-25/F-27이 이미 쓰는 PID 재사용 방지 동일 기제). **파일은 고치지 않는다.**

표시(prd.md:288·311): pulse 인접 **1행** `⚙ governor 2/5`. healthy 무음 원칙 적용 가능 → **cap의 절반 미만이면 숨긴다**(구체 임계는 실측 후 dev_log에 근거 기록). `--json`에 `governor` 키 additive. 소스 부재 → 행 생략(회귀 0).

**pulse 카운트 혼입 금지**(F-18 계열, prd.md:293 동형): governor lease는 세션/잡 카운트에 더하지 않는다. 별도 집계.

검증(`tests/test_f28c_governor.py`): 실 state.json 형태 픽스처(위 실측 shape) 주입 → `2/5`; 죽은 pid lease 포함 → 산 것만 카운트(★); 파일 부재 → `None` + 행 생략; 손상 json → `None`.

### 6b. run registry — 스킵 + 이월 기록

구현하지 않는다. 근거(P2): `--registry`가 caller-supplied required 인자이고 canonical 기본 경로가 없다(`utilities/resource-runner.py:18`), `dispatch-node.py:12`도 위치를 정하지 않으며, live 파일 0건, 실측 record에 `resource-runner` kind 노드 0건. **추측 경로 스캔은 prd.md:292의 "추측 표시 금지" 위배다.**

산출: `_internal/carryover.md` — 위 근거 + 재개 조건("resource-runner registry의 canonical 경로 규약이 stage-dispatch spec에 명시되면 F-28c 후반 재개") + prd.md:311 대비 실제 판정 차이(“부재”가 아니라 “발견 불가”). code-report가 이 파일을 사용자 보고에 올린다.

---

## 7. Step 5 — 통합 검증 · 미러 동기

```bash
cd /home/Uihyeop/agent_setting-wt/fleet-v10-process-view

# V1 전체 회귀 — 베이스라인 468 유지 + 신규
python3 -m unittest discover -s tools/fleet/tests -t .        # 기대: Ran 468+N, OK

# V2 3폭 렌더 — 그룹 뷰(회귀) + 과정 뷰(신규 화면). ★ Step 3 완료 후에만 --view가 존재한다.
# ★ FLEET_DEMO=1 필수(plan-review Y4): 이것 없이 라이브 route record가 없으면 과정 뷰는
#   "활성 route 없음"만 그리고 → V3 디자인 critic(태스크 명시 필수)이 빈 화면을 비평하게 된다.
for w in 60 120 168; do
  echo "=== group   $w ==="; COLUMNS=$w python3 tools/fleet/fleet.py --once
  echo "=== process $w ==="; COLUMNS=$w FLEET_DEMO=1 python3 tools/fleet/fleet.py --once --view process
done
# demo.py(107행)는 route도 subagents도 만들지 않는다 → Step 3에서 demo.py에 route를 실은 잡
# (record 있는 것 1 + degrade 1 + 병렬 route 1)과 subagents 1건을 additive로 추가한다.
# demo는 픽스처 모듈이므로(fleet.py:101-115에서 라이브에 병합) 안전하다.

# V3 ★ 디자인 critic (신규 화면 = 필수, 태스크 명시) — read-only
#   입력 = V2의 과정 뷰 3폭 캡처. 디자인팀 critic 모드, 6축 비평.
#   산출: _internal/design_reviews/round_1.md   ← code-test 스테이지가 수행/수확
#   ⚠ critic은 read-only다. 렌더를 고치는 것은 execute/refine이다.

# V4 --json additive 보증
python3 tools/fleet/fleet.py --json > /tmp/v10.json
python3 - <<'PY'
import json; d=json.load(open("/tmp/v10.json"))
assert {"sessions","jobs","summary"} <= set(d), "기존 최상위 키 소실"   # memory는 조건부 키
assert "route" in d, "route 키 부재"
print("keys:", sorted(d)); print("route:", len(d["route"]))
PY

# V5 미러 동기 (test_mirror_parity.py 가 byte-identical 강제)
rsync -a --delete --exclude='__pycache__' tools/fleet/ adapters/claude/tools/fleet/
python3 -m unittest tools.fleet.tests.test_mirror_parity -v

# G3 ★ read-only 게이트 — route record write 경로가 없음을 정적 증명
grep -nE "open\(.*['\"]w|write_text|os\.replace|\.write\(" tools/fleet/route.py tools/fleet/collectors/governor.py
#   기대: 출력 0줄. 1줄이라도 나오면 Step 1/4a 계약 위반 → 즉시 중단.
```

**미러 주의(v9 학습)**: 미러 대상은 `fleet.py`/`fleet.sh`만이 아니라 `tools/fleet/` **전 트리**다 — 신설 `route.py`·`collectors/governor.py`·`tests/test_f28_route.py`·`tests/fixtures/route/*.json` **전부** 미러에 byte-identical 복사본이 있어야 `test_mirror_parity`가 통과한다(`_tree()`는 `__pycache__`만 제외하고 raw bytes 비교). 픽스처 json을 빠뜨리기 쉽다.

---

## 8. 회귀 예산 · 불변식 (execute가 깨면 즉시 중단)

| # | 불변식 | 근거 |
|---|---|---|
| I1 | record 없는 환경에서 fleet 출력이 v9와 동일 | prd.md:302 "회귀 없음" |
| I2 | `route.load()`는 어떤 입력에도 raise하지 않는다 | prd.md:302 tolerant 필수 |
| I3 | route record에 write 0 (§7 G3 정적 증명) | prd.md:287 "fleet은 route record를 절대 쓰지 않는다" |
| I4 | 노드 점등은 자식 실측이 결정한다 — record는 레일만 | prd.md:303, SD-F2 |
| I5 | `--json` 기존 키 불변 | prd.md:294 additive |
| I6 | kill 도달 경로는 `_handle_prompt_key` 하나 | v9 §4.1 · control.py 불변 |
| I7 | `_FOLD_ROWS ∩ (_CLICK_ROWS ∪ _TOGGLE_ROWS) = ∅` | §5.4 (plan-review B2) |
| I11 | gate 통과를 `completion_gate=` 존재로 판정하지 않는다 | §3.3.1 · prd.md:292 |
| I8 | governor lease가 세션/잡 카운트에 혼입되지 않음 | prd.md:293 F-18 계열 |
| I9 | 실세션 스폰·signal 0 | §0 |
| I10 | spec 미변경 (`spec_touch=false`) | route record 선언 |

---

## 9. 미해결 · 리스크

1. **`--view` 플래그는 spec에 없다**(P3). prd.md:305는 `p` 키만 확정했다. `--view`는 검증 계약(3폭 `--once` + critic)을 수행 가능하게 하는 **비대화식 투영**이며 `p`와 같은 전역을 쓴다 — spec 확장이 아니라 구현 세부로 본다. code-report가 사용자에게 이 판단을 노출하고, 사용자가 반대하면 `FLEET_VIEW=process` 환경변수로 축소 가능(동일 진입점, CLI 표면 0).
2. **노드 라벨 폭**: 실측 노드 id(`execute`, `aggregate`, `eval-asr`)는 `_PIPE_STAGES`의 축약어(`exec`)보다 길다. 60열 병렬 카드에서 `_drop_past_stages`만으로 부족하면 노드 id 말단 절단이 필요할 수 있다 — Step 3 실측 후 판단, 새 상수는 한 곳에만.
3. ~~**proc 잡의 route**: env 실재 미확인~~ → **해소**(plan-review Y3). `AGENT_ROUTE_FILE`/`AGENT_ROUTE_ID`/`AGENT_ROUTE_NODE` 실재 확인(§3.2.2). 잔여 제약은 `AGENT_ROUTE_HASH` 미export 하나뿐이고, 무결성은 record 자체 재계산으로 담보되므로 설계에 영향 없다.
4. **governor 무음 임계**: "healthy 무음"의 구체 임계(prd.md:288 "적용 가능")는 실측 후 결정. 근거 없이 정하지 말고 dev_log에 관측을 남길 것.
5. **`/tmp` 휘발 실증의 시한성**: `agent-note-d1-route.json`은 plan 시점 존재했다. execute 시점에 사라져 있어도 **정상**이다 — 그래서 픽스처로 복사한다(§3.5). 원본 부재를 버그로 오인하지 말 것.
