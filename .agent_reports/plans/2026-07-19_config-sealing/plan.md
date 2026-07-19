---
slug: config-sealing
capability: autopilot-code
mode: dev/refactor
intensity: standard
stage: code-plan
status: planned
route_id: rt-d57cbb149952fd3d
route_hash: sha256:d57cbb149952fd3db6bc2f05da0890dd26e955fa6aad2c821c6784e63572938f
spec_significance: within-spec — spec/stage-dispatch/prd.md §13.9.2 SD-68
---

# SD-68 — dispatch-defaults config를 route record에 컴파일 시점 스냅샷으로 봉인

## 0. Spec 근거 라인 (지배 항목 정독 결과)

이 계획은 아래 spec 지배 항목을 정독한 뒤 그 계약을 코드 배선으로 옮긴 것이다.
근거 라인은 실측 인용이다.

- **§13.9.2 SD-68 (SoT, v17 2026-07-19 등재 — SD-66 2단계 유보 해제)**:
  "`capability-route.py compile`이 검증된 dispatch-defaults config를 로드해 ① 각 depth-2
  stage 노드에 `harness_affinity` 스탬프(config 어휘 그대로 `claude|codex|opencode|diverse`,
  미지정 칸·config 부재 = `unspecified`) ② record 상단 `dispatch_defaults_digest`(canonical
  config sha256, 부재 시 null)를 기록한다. `route_hash`가 두 필드를 봉인한다 — 컴파일
  시점 스냅샷이며, 사후 config 변경은 기존 route를 무효화하지 않는다(verify는 hash
  봉인만 검증, config 재로드 금지). `registry_digest`(topology registry pin)와는 의도적으로
  분리한다."
  - 우선순위 불변(SD-22): "explicit choice > hard eligibility(SD-48 tuple·usage limit) >
    record affinity(config 스냅샷) > heuristic/bias. soft default 유지 — conductor는 사유
    기록 후 이탈 가능, **차단 장치 신설 금지**."
  - 소비: "dispatch-node가 노드 `harness_affinity`를 registry row(`harness_affinity=`)에
    기록해 실제 `harness=`와의 이탈을 행 단위로 감사 가능하게 한다. … 1단계 selector
    배선(dispatch-route.sh)은 record 없는 depth-1·수동 경로의 소비자로 **불변 존속**.
    손상 config는 compile fail-loud, 부재는 전부 `unspecified`."
  - acceptance ①~⑤: ① compile 산출 route의 depth-2 노드 전부에 유효 어휘 `harness_affinity`
    존재 ② config 값 변경 → 신규 compile의 `route_hash` 변화 ③ 스탬프된 기존 route는
    config 사후 변경에도 verify 통과 ④ dispatch-node 경유 row에 `harness_affinity` 기록
    ⑤ explicit `--adapter`가 affinity와 달라도 launch 통과(soft) + 기존 스위트 회귀 0.

- **§13.8.1 SD-66 (v16, 1단계 — 봉인의 데이터 원천)**: 값 어휘 = `claude|codex|opencode|
  diverse|미지정`, "값은 하네스만 — concrete model/effort 금지". SD-22 3단계 stage affinity를
  사용자-선언 데이터로 외부화하며 "1단계 explicit choice와 2단계 hard eligibility는 이
  config에 항상 우선한다. soft default". 초기값(2026-07 스냅샷): autopilot-code
  `execute=codex`, `test·review=diverse`, `report=claude`, `plan=미지정`. **route hash 봉인
  경로(topology compile) 배선을 2단계로 유보** — SD-68이 그 2단계다.

- **§14 v17 규칙 구간 (의미↔규칙 경계, DESIGN_PRINCIPLES §0.7)**: "`harness_affinity` 어휘
  검증·`dispatch_defaults_digest` 봉인·registry row 기록은 **결정론 검사 대상**이다. …
  record affinity 이탈 사유의 타당성은 conductor 의미 구간으로 남는다." → 코드가 강제하는
  것은 어휘·봉인·row 기록뿐, 이탈 여부 판단은 코드 밖.
  §14 v16: "우선순위 적용 순서(explicit > eligibility > config affinity)는 결정론 검사 대상."

- **core/OPERATIONS.md §5.10 (SD-66 소비 규칙 현행 문장, line 129)**: "`profiles/dispatch-
  defaults.yaml` is the user-declared source for step 3 (stage affinity) of the SD-22 cascade:
  an explicit `--adapter`/`--family` choice and hard eligibility … always win over it, the
  orchestrator may still deviate … when it records a reason … cells the config leaves
  unspecified stay discretionary." → 이 문장에 **record affinity 소비 한 문장**을 현행화한다
  (SD-68 소비 계약, soft·차단 없음).

## 1. 설계 요지

SD-66 1단계는 selector(`dispatch-route.sh`)만 config를 소비한다(런타임 재로드). 2단계(SD-68)는
config를 **route record에 컴파일 시점 스냅샷으로 봉인**해서:
1. conductor가 record의 `harness_affinity`를 1차 후보(soft)로 읽고,
2. 실제 선택(`harness=`)과의 이탈이 registry row 단위로 감사 가능해지며,
3. 사후 config 변경이 이미 컴파일된 route를 무효화하지 못한다(불변식 = route_hash 봉인).

selector의 런타임 소비(1단계)와 record 봉인(2단계)은 **의도적으로 다른 소비자**다:
selector는 record 없는 depth-1·수동 경로용으로 불변 존속하고, 봉인 record는 standard+
depth-2 stage 노드용이다. 값 원천(`dispatch-defaults.yaml`)은 공유하지만 소비 시점이 다르다.

## 2. Canonicalization 방식 결정 + 사유 (spec가 plan 소관으로 위임한 결정)

**결정: `dispatch_defaults_digest` = 정규화 파싱 결과의 canonical JSON sha256.**
구체적으로 `dispatch-defaults.py`의 `load_and_validate()`가 반환한 검증된 config dict를
기존 `capability-route.py`의 `canonical()`(= `json.dumps(sort_keys=True, ensure_ascii=False,
separators=(",",":"))`) 로 직렬화한 바이트의 `sha256`, 접두사 `"sha256:"`. config 부재 시 `None`.

**원시 바이트가 아니라 정규화 파싱을 택한 사유:**
1. **봉인 대상은 "효과적 config"이지 파일 포맷이 아니다.** compile이 실제로 소비하는 것은
   `query_stage_affinity`가 읽는 파싱된 dict이다. 주석·공백·키 순서는 스탬프에 영향을
   주지 않으므로 digest도 거기 반응하면 안 된다. 원시 바이트 digest는 주석 한 줄(예:
   `dispatch-defaults.yaml`의 커밋된 scaffold capability 주석 해제) 편집만으로 `route_hash`가
   흔들려 **의미 변화 없는 봉인 파손(false churn)**을 낳는다. acceptance ②("config 값 변경
   → route_hash 변화")는 두 방식 모두 만족하지만, 정규화만이 값 무변경 시 hash 불변을
   보장한다.
2. **검증된 내용만 digest한다.** 정규화 경로는 `load_and_validate`를 통과한 dict만
   canonicalize하므로 손상 config는 digest 계산 이전에 fail-loud된다(§4.1). 원시 바이트는
   로더가 거부할 내용까지 해시할 수 있다.
3. **결정론.** `parse_yaml_subset`은 스칼라·인라인 리스트·2단계 매핑만 산출한다(순수
   dict/list/scalar/bool). `canonical()`은 `sort_keys=True`라 키 순서에 무관하게 결정론적이다.
   `Date.now`류 비결정 입력 없음.

**기각한 대안 — 원시 바이트(`config_path.read_bytes()`의 sha256):** 더 단순하고 "디스크에
있던 그대로"라는 감사 서사는 있으나, 위 (1) false churn과 (2) 미검증 바이트 해시 위험으로
기각. plan review에서 재검토 가능하도록 근거를 명시한다.

## 3. 파일별 변경 설계

> 소스 편집은 execute 스테이지 소관. 본 plan은 execute가 대화 없이 구현 가능하도록 완결
> 설계를 제공한다(§0.5 계약 완결성 의무). 편집은 worktree
> `/home/Uihyeop/agent_setting-wt/config-sealing` 에서만.

### 3.1 `utilities/dispatch-defaults.py` — 봉인용 어휘 헬퍼 1개 추가 (스키마·어휘 불변)

기존 `query_affinity`는 selector가 의존하며 미지정 칸에 `"neutral"`을 반환한다 — **건드리지
않는다**. SD-68 스탬프 어휘는 `claude|codex|opencode|diverse|unspecified`이므로 별도 헬퍼를 둔다.

```python
def query_stage_affinity(config, capability, stage):
    """SD-68 record-seal vocabulary: like query_affinity but a missing/unknown
    cell maps to 'unspecified' (the record-seal word), never 'neutral' (the
    selector word). Vocabulary ownership stays in this loader module."""
    value = query_affinity(config, capability, stage)
    return value if value in AFFINITY_VALUES else "unspecified"
```

- 스키마·어휘·기존 함수 전부 불변. selector 경로(`affinity` 서브커맨드 → `query_affinity`)
  영향 0. CLI 서브커맨드 추가 불요(compile이 Python API로 직접 호출).
- task "capability×stage 전체 맵이 필요하면 최소 함수 추가 허용" 조항의 최소 실현:
  compile은 노드별 stage 조회만 필요하므로 전체 맵 함수 대신 노드 단위 조회 헬퍼 1개.

### 3.2 `utilities/capability-route.py` — compile 봉인 (핵심)

**(a) 로더 모듈 import 추가** (상단, TOPO와 동형 — 하이픈 파일명이라 importlib 필수):
```python
DEFAULTS_SPEC = importlib.util.spec_from_file_location(
    "dispatch_defaults", ROOT/"utilities/dispatch-defaults.py")
DEFAULTS = importlib.util.module_from_spec(DEFAULTS_SPEC)
DEFAULTS_SPEC.loader.exec_module(DEFAULTS)
VALID_AFFINITY = DEFAULTS.AFFINITY_VALUES | {"unspecified"}  # 어휘 중복 정의 회피
```

**(b) 봉인 헬퍼** (모듈 함수):
```python
def _seal_dispatch_defaults(nodes, capability):
    """Return dispatch_defaults_digest and stamp each depth-2 node's
    harness_affinity, BEFORE route_hash is computed. Absent config -> all
    'unspecified' + digest None. Corrupt config -> fail-loud (reused loader
    validator), surfaced as ValueError so main() exits 64. registry_digest is
    a separate field and is never touched here."""
    config_path = DEFAULTS.default_config_path()  # honors DISPATCH_DEFAULTS_CONFIG
    if not os.path.exists(config_path):
        for node in nodes:
            if node.get("depth") == 2:
                node["harness_affinity"] = "unspecified"
        return None
    try:
        cfg = DEFAULTS.load_and_validate(config_path, DEFAULTS.default_topology_path())
    except DEFAULTS.DefaultsConfigError as exc:
        raise ValueError(f"corrupt dispatch-defaults config: {exc}")
    for node in nodes:
        if node.get("depth") == 2:
            node["harness_affinity"] = DEFAULTS.query_stage_affinity(cfg, capability, node["id"])
    return "sha256:" + hashlib.sha256(canonical(cfg)).hexdigest()
```

- **왜 `ValueError`로 감싸나:** `DefaultsConfigError`는 `ValueError` 비상속(실측 확인).
  `main()`의 `except (ValueError, TOPO.TopologyError)`가 exit 64로 마감하려면 `ValueError`
  계열이어야 한다. "기존 validator 재사용"(spec) = `load_and_validate` 그대로 호출하고
  그 예외를 fail-loud로 승격.
- **부재 판정:** `os.path.exists(config_path)`. env 오버라이드가 없는 경로를 가리키면 부재로
  간주 → 전부 `unspecified`, digest `None`.

**(c) `compile_route` 배선** — nodes 확정 직후(현행 line 203 dispatch_fallback 주입 이후),
`route_hash` 계산(현행 line 221) **이전**에 호출하고 payload에 필드 추가:
```python
# ... dispatch_fallback 주입 루프 끝난 직후 ...
dispatch_defaults_digest = _seal_dispatch_defaults(nodes, capability)
# payload dict 안에 registry_digest 근처(분리 명시)에 삽입:
#   "registry_digest": TOPO.registry_digest(registry),
#   "dispatch_defaults_digest": dispatch_defaults_digest,
```
- 스탬프가 `nodes`에 들어가고 digest가 payload에 들어간 뒤 기존 `route_hash(payload)`가
  자동으로 두 필드를 봉인한다(별도 hash 로직 불요 — 이미 `route_hash`는 route_hash/route_id
  외 전 필드를 해시).
- **가드 `depth==2`:** standard+ 만 depth-2 stage 노드를 가진다(실측 확인: plan/execute/test/
  report 전부 depth=2). direct/quick은 depth-1 단일 노드 → 스탬프 없음. digest는 모든
  intensity에서 기록(아래 결정).
- **direct/quick도 digest 기록 (uniform):** 봉인은 stage 노드에 국한되지만 digest는 "compile이
  본 config 스냅샷"의 감사 필드이므로 topology와 무관하게 균일 기록한다. selector가 이미
  config를 무조건 validate하는 선례(dispatch-route.sh line 38 "Validate unconditionally")와
  일관 — 손상 config는 direct compile도 fail-loud. 스키마 균일성 이득 > 미소한 부재-로드 비용.
- `registry_digest`와 **절대 병합 금지** — 별도 top-level 필드. config 변경이 topology pin을
  오염시키지 않음(§13.9.2 의도).

**(d) `verify_route` — config 재로드 금지, hash 봉인 + 어휘 유효성만** (현행 line 224~246 내
삽입, registry_digest 검증 직후):
```python
for node in route.get("nodes", []):
    if "harness_affinity" in node and node["harness_affinity"] not in VALID_AFFINITY:
        raise ValueError(f"invalid harness_affinity vocabulary: {node['harness_affinity']!r}")
digest = route.get("dispatch_defaults_digest")
if digest is not None and (not isinstance(digest, str) or not digest.startswith("sha256:")):
    raise ValueError("invalid dispatch_defaults_digest format")
```
- **config 재로드 없음.** `route_hash`(현행 line 225)가 이미 두 필드를 봉인 검증하므로
  사후 config 변경이 route를 무효화하지 못한다(acceptance ③).
- **하위호환:** `harness_affinity`/`dispatch_defaults_digest` 필드가 **없는** 구 route(현
  사이클 route.json 포함)는 위 두 검사가 모두 조건부(`in node` / `is not None`)라 그대로
  통과. 구 route 회귀 0.
- 어휘 검사는 손으로 편집 후 route_hash를 재계산한 위조 route에 대한 결정론 어휘 가드
  (§14 v17 "어휘 검증은 결정론 검사 대상").

### 3.3 `utilities/dispatch-node.py` — row 계측 (soft, 차단 없음)

record 노드에 `harness_affinity`가 있으면 wrapper argv에 passthrough 플래그로 전달해
registry row에 기록한다. **선택한 방식 = wrapper 인자 전달**(spec가 나열한 두 옵션 중 택일).

- **wrapper 인자 전달을 택한 사유:** `dispatch-node.py`는 `subprocess.run(argv)` 후
  returncode로 즉시 종료(현행 line 178)하며 attempt_id를 소유하지 않는다(wrapper가
  `new_attempt_id`로 생성). 따라서 시작 후 `annotate_attempt_row` 경로는 attempt_id 확보·
  race 문제로 부적합. wrapper가 row를 spawn 前 원자적으로 쓰므로(`claim_attempt_row`)
  passthrough 플래그가 결정론적이고 감사 durable하다. 기존 `--route-*` 메타데이터 전달과
  대칭.
- **`dispatch-node.py` 변경** (argv 조립부, depth-2 분기 근처 — 필드 유무만 보므로 depth
  무관하게 안전하나 실제로 depth-2 노드에만 필드 존재):
```python
affinity = node.get("harness_affinity")
if affinity:
    argv += ["--harness-affinity", affinity]
```
  필드 없는 구 route → 아무것도 추가 안 됨 → 현행 동작 불변.
- **wrapper 3종 passthrough** (`adapters/{claude,codex,opencode}/bin/dispatch-headless.py`):
  각 wrapper에 `--harness-affinity`(default None) 인자 추가 + pipe 메타데이터 루프의 키
  튜플에 `"harness_affinity"` 추가. 실측 확인 — 세 wrapper 모두 동형 루프 보유:
  - claude line 420, codex line 517, opencode line 483:
    `for key in ("route_file", "route_id", "route_hash", "route_node", "registry_digest", "write_scope", "completion_gate"):`
    → 튜플 끝에 `"harness_affinity"` 추가 + arg 선언. `args.harness_affinity`가 falsy면
    루프의 `if value:`가 걸러 구 경로 불변.
- **차단 장치 신설 금지 준수:** 이건 **순수 메타데이터 passthrough**이지 검증 게이트가
  아니다(OUT of scope "wrapper 3종 신규 검증 게이트"에 저촉 안 됨). explicit `--adapter`가
  affinity와 달라도 아무 비교·거부 없이 통과(acceptance ⑤ — soft). SD-22 우선순위
  explicit > … > record affinity 불변.
- **row 형식 영향:** 6개 탭 필드 불변, pipe에 kv 하나 추가일 뿐. 모든 파서가
  `dict(part.split("=",1) …)`라 추가 키에 무해. → 회귀 점검 항목(§5).

### 3.4 `core/OPERATIONS.md §5.10` — record affinity 소비 한 문장 현행화 (core-first)

line 129 SD-66 소비 문장(현행: selector용 "user-declared source for step 3") 뒤에 record 봉인
소비를 한 문장 추가:
> Once a route is compiled its stage nodes carry a sealed `harness_affinity` snapshot and the
> record top-level a `dispatch_defaults_digest`; a conductor consumes the node's
> `harness_affinity` as the step-3 candidate and records a reason when it deviates (soft, no
> gate), while `verify` only checks the hash seal and never reloads the config. This seals the
> config at compile time and is kept separate from `registry_digest`.

- soft·차단 없음 명문화. verify 재로드 금지·registry_digest 분리 명시.
- **커밋 순서: core 편집을 utilities 편집보다 먼저 커밋**(§4 참조).

## 4. 커밋 순서 (core-first — spec 명시 요구)

1. **커밋 1 (core-first):** `core/OPERATIONS.md §5.10` 소비 규칙 현행화만.
   - 근거: 지침(계약)이 구현보다 앞서 문서화되어야 소비 규칙이 코드 이전에 확정된다.
     conductor-prompt·spec가 명시적으로 "core 편집을 utilities 편집보다 먼저 커밋" 요구.
2. **커밋 2 (utilities + tests):** `dispatch-defaults.py` 헬퍼 → `capability-route.py`
   compile/verify → `dispatch-node.py` → wrapper 3종 → 테스트. 논리적 단일 변경이라
   한 커밋(또는 execute 판단으로 세분 가능하나 core 뒤 순서 불변).
3. 커밋 전 `adapters/**/__pycache__` 삭제(boundary guard). guard/테스트는 worktree 안에서만,
   primary checkout guard 금지.

## 5. 테스트 매핑 (acceptance ①~⑤ + 하위호환 + 회귀 0)

### 5.1 신규 — `utilities/capability_route.test.py` 확장
픽스처는 `DISPATCH_DEFAULTS_CONFIG` env로 temp config를 가리켜 결정론화(로더의
`default_config_path`가 env 존중 — 재구현 금지). 픽스처 config의 capability/stage 키는 실제
`topologies.json`(autopilot-code: plan/execute/test/report)에 대해 validate됨.

- **acceptance ① (depth-2 전 노드 유효 어휘 스탬프):** standard route 컴파일(promotion signal
  경로 = `test_promotion_standard`처럼 inline-fallback + signal, dispatch_evidence 불요).
  네 노드 전부 `harness_affinity in VALID_AFFINITY` 단언. 셸 config로 execute=codex,
  test=diverse, report=claude, plan=unspecified 단언.
- **acceptance ② (봉인 입증 — 값 변경 → route_hash 변화):** 픽스처 A(report:claude)와
  픽스처 B(report:codex)로 각각 compile → `route_hash` 상이 단언. 동일 config 재compile은
  `route_hash` 동일(주석/공백만 다른 두 파일도 동일 hash — 정규화 digest 입증) 단언.
- **acceptance ③ (스탬프 route는 config 사후 변경에도 verify 통과):** 픽스처 A로 compile한
  route 객체를 잡고, env를 픽스처 B로 바꾼 뒤 `verify_route(route)` 통과 단언(재로드 없음 =
  hash만 검증). 어휘·digest 검사 통과.
- **하위호환 (구 route verify):** `harness_affinity`/`dispatch_defaults_digest` 필드를 제거하고
  route_hash 재계산한 route가 verify 통과 단언(현 사이클 route.json 형태). + 잘못된 어휘
  스탬프(예: `"gpt"`)를 넣고 hash 재계산한 route는 verify 실패 단언(결정론 어휘 가드).
- **부재 경로:** env를 존재하지 않는 경로로 → compile 시 digest `None` + 전 depth-2 노드
  `unspecified` 단언.
- **손상 config fail-loud:** 깨진 YAML(예: 잘못된 affinity 값) 픽스처 → compile이
  `ValueError` 발생 단언(main exit 64 경로).

### 5.2 신규 — `utilities/dispatch_node.test.py` 확장
- **acceptance ④ (row에 harness_affinity 기록):** `MainMaterializationTest` 패턴(subprocess
  mock + argv 캡처)으로 `harness_affinity` 필드가 있는 depth-2 노드 route를 dispatch-node
  경유 → 캡처된 argv에 `--harness-affinity <값>` 포함 단언. 필드 없는 노드 →
  `--harness-affinity` 미포함 단언(구 route 불변).
- **acceptance ⑤ (explicit --adapter가 affinity와 달라도 launch 통과):** node
  `harness_affinity=codex`인데 `--adapter claude`로 dispatch-node → SystemExit(0)/argv 정상
  조립(차단·비교 없음) 단언. affinity와 adapter 불일치로 인한 어떤 오류도 없음.

### 5.3 회귀 0 (전량 통과 필수)
worktree 안에서 실행:
- `.py`: `utilities/capability_route.test.py`, `utilities/dispatch_node.test.py`,
  `utilities/dispatch_contract.test.py`, `utilities/worker_route_guard.test.py`
- sd45 3종(**python3**): `adapters/{claude,codex,opencode}/bin/dispatch-headless.sd45.test.py`
- sd15 3종(**bash 실행**): `adapters/{claude,codex,opencode}/bin/dispatch-headless.sd15.test.sh`
- `dispatch-route.test.sh`(**bash**): selector 1단계 의미 불변 회귀 — config 소비·우선순위
  순서 불변 확인(selector는 이번 변경에서 코드 편집 없음, 회귀 확인만).

특히 wrapper pipe에 kv 추가(§3.3)가 sd45/sd15·dispatch_contract 스위트의 row 형식/필드
파싱 단언을 깨지 않는지 확인 — 6-탭 필드 불변, kv dict 파서 무해가 전제. 만약 어떤 스위트가
pipe 전체 문자열을 exact-match 한다면 execute가 그 단언을 kv 추가에 맞춰 갱신(형식 계약
불변 범위 내).

## 6. 범위 밖 (건드리지 않음)
selector 캐스케이드 의미 변경(1단계 불변 존속), `profiles/dispatch-defaults.yaml` **값** 변경,
worker-route-guard, wrapper 3종의 **신규 검증 게이트**(passthrough는 게이트 아님), 권한
분류기, `spec/**` 편집.

## 7. 의미↔규칙 경계 (§14 준수 자기점검)
- 규칙(코드 강제): 어휘 검증·`route_hash` 봉인·`dispatch_defaults_digest` 결정론 계산·row
  기록·우선순위 순서. 전부 본 plan의 결정론 배선.
- 의미(코드 밖): 어느 하네스로 이탈할지, 이탈 사유의 타당성, 미지정 칸에서의 선택 — conductor
  판단. 코드는 **차단하지 않는다**(soft). SD-68 "차단 장치 신설 금지" 준수.
