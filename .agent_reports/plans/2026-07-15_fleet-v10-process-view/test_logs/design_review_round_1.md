# 🎨 디자인 review — F-30 과정 뷰 (round 1)

**대상**: 실렌더 캡처 60/120/168열 × {group, process} (`/tmp/qa10/captures.txt` 재현 절차 하단)
**요약**: 신규 화면의 정보 위계·병렬 분기 표현·폭 사다리는 견고하다. 다만 **결손 카드가 화면을 지배**하고
(실측 live에서 카드 2장 중 1장이 "no route record"), L1 경과 표기가 자기 카드 안에서 일관되지 않는다.

> ⚠ **수행 주체 disclosure (계약 이탈 — conductor 판단 필요)**
> 태스크는 "디자인팀 critic 모드 **서브에이전트**를 띄워" 비평시킬 것을 필수로 지시했다. 수행 불가했다:
> ① 이 런타임에 native 서브에이전트(Task) 도구가 없다. ② 포터블 대체 경로인
> `stage-dispatch-fallback.py`는 `--route/--node`로 **immutable route record의 노드 1개**를 실행하는
> 도구인데, 본 사이클 record의 노드는 `plan/execute/test/report`뿐이라 ad-hoc critic 노드를 띄울 수 없다.
> → 아래 비평은 **qa 라우터가 critic 모드 규율(read-only·렌더 우선·6축·우선순위)로 직접 수행**했다.
> `_design_rules.md §검수는 분리한다`(만든 자가 검수하면 관대해진다)의 독립성 요건은 **부분 충족**이다
> (구현 주체는 execute이고 비평 주체는 별개 컨텍스트인 qa지만, 지정된 디자인팀 컨텍스트는 아니다).
> 렌더 런타임 한계: 터미널 TUI라 Design MCP·색 대비 수치 측정 비대상 — **텍스트 렌더 캡처가 상한**이며
> 색은 palette 키 수준으로만 판단했다.

---

## 축별 평가

### 시각 위계 — 🟢 양호 / 🟡 결손 카드 과다
카드 L1(태그+route_id+진행)→L2(DAG 흐름)→중첩 자식(`└▸🚀`/`└⚡`)의 3단 들여쓰기가 시선 흐름과 일치한다.
`⚠ failed node`를 L1 끝에 두어 접힌 상태에서도 실패를 놓치지 않게 한 것은 좋은 판단.
**다만** live 실측 화면은 카드 2장 중 1장이 `— no route record`다. 결손 카드가 정보 카드와 **동일한 시각 무게**
(같은 `▾`, 같은 들여쓰기, 같은 밝기)를 가져서, 화면의 절반이 "볼 것 없음"인데 그렇게 보이지 않는다.
→ 제안: degrade 카드는 dim 처리하고 정렬 순서상 record 카드 **뒤**로. (근본 해결은 verification.md §10.)

### 정렬·여백 — 🟢 양호
`  ▾ [tag] …` / `    node › node` / `     └▸🚀` 의 2·4·5칸 계단이 일정하고, 카드 간 빈 줄 1개로 호흡이 있다.
병렬 분기 `├`/`└` 트리 글리프가 fan-out 3개를 정확히 묶고, fan-in을 `› aggregate ○`로 다시 합류시키는
표현은 DAG를 텍스트로 옮긴 것 중 드물게 읽힌다. 60열에서도 트리 글리프를 지키고 모델 태그를 먼저 버리는
사다리가 계획대로 작동 — `_dw` 폭 계산 오정렬 0.

### 접근성 — 🟢 (TUI 범위)
상태가 **글리프(✓/●/○/✕) + 텍스트**로 이중 인코딩되어 색맹 사용자도 판독 가능 — 색 단독 의존이 아니다.
`p` 키 진입 + footer 표기로 키보드 경로가 살아 있고, 마우스는 보조다(F-27 문법 계승).
WCAG 수치 대비는 터미널 팔레트 소관이라 측정 비대상(위 disclosure).

### 반응형(폭 사다리) — 🟢 양호
60/120/168 전 폭에서 **카드 라인 오버플로 0**(east_asian_width 독립 재구현으로 교차검증).
60열에서 `[lab·eval·standard]`→`[lab·eval]`로 intensity를 먼저 버리고, `_drop_past_stages`로 과거 노드를
접어 활성 노드를 끝까지 살리는 SD-F2 계약이 실제로 지켜진다(`execute ● 8m › test ○ › report ○`).
신규 절단 로직·신규 폭 상수 없이 기존 idiom 재사용 — 계획 준수.
(60열 group 뷰 헤더 오버플로는 v9부터의 기존 동작으로, 본 사이클 신규 아님을 확인했다.)

### UX 흐름 — 🟡
빈 상태("활성 route 없음")·결손 상태(degrade 카드)·실패 상태(자동 펼침+적색)를 모두 다뤘고,
`_PROMPT` 떠 있을 때 카드 클릭을 삼키는 rung 1 불변이 살아 있어 오조작 위험이 낮다.
**🟡 이슈**: 접힘/펼침이 사용자에게 **되돌릴 수 있는 조작**임을 알려주는 affordance가 `▾`/`▸` 글리프 하나뿐이다.
footer에 fold 힌트가 없다(`p process`만 있다). 100열 이상에서 `_MOUSE_HINT_MIN_WIDTH` 선례대로 1세그 추가 여지.

### 톤 일관성 — 🟡 **L1 경과에 `⏳`가 없다**
prd.md:307은 L1을 `<n/m nodes> ⏳<경과>`로 규정한다. 실렌더:
```
▾ [code·dev·standard] rt-2f5c79f5 — 1/4 nodes  15m        ← ⏳ 없음, 공백 2칸 뒤 맨 숫자
   └▸🚀 demo-route-conductor-execute  claude code  Opus 4.8  (high)  ⏳8m   ← 같은 카드 안에서는 ⏳ 있음
```
전 캡처에서 `nodes` 행의 `⏳` 출현 **0회**, 자식 행은 9회. **같은 카드 안에서 같은 의미(경과)가 두 표기**를
쓴다 — `_design_rules` "시스템을 말로 먼저 선언한다 / 즉흥 발명 금지"에 걸리고, 맨 `15m`은 앞의 `1/4 nodes`에
붙어 읽혀 순간적으로 "노드 수의 일부"로 오독된다. spec 문자 그대로의 이탈이기도 하다.
→ 제안: L1도 `⏳15m`으로 통일(1글자 비용, 폭 사다리 영향 미미).

---

## 우선순위

**🔴 (없음)** — 렌더가 깨지거나 오정보를 그리는 지점은 없다.

**🟡 1. 마퀴 병렬 카드가 논리적으로 불가능한 DAG를 그린다 (demo 픽스처)**
```
▾ [lab·eval] rt-6f5423d0 — 0/6 nodes  9m ⚠ failed node
  setup ○                     ← 미기동인데
    ├ eval-asr ● 9m           ← 그 자식이 실행 중
    ├ eval-sep ✕ 3m           ← 그 자식이 실패
```
`setup ○`(미기동)의 dependents가 active/failed다 — 실제로 불가능한 파이프라인 상태이고, `0/6 nodes`도
"완료 0인데 3단계가 진행 중"으로 모순된다. 근인: `demo.py:_seed_route_evidence()`가 `_DEMO_CARD_RID`의
`plan`만 seed하고 **`_LAB_RID`의 `setup`은 seed하지 않는다**. 프로덕션 로직 결함은 아니지만, 이 카드는
F-30의 존재 이유(prd.md:307 병렬 분기)를 보여주는 **간판 화면**이고 `FLEET_DEMO=1` 사용자와 후속 critic이
보는 첫 인상이다. → `setup`에 done 증거 1건 seed(→ `setup ✓`, `1/6 nodes`)면 해소.

**🟡 2. L1 경과 `⏳` 누락** — 위 톤 일관성 참조. prd.md:307 문자 이탈 + 카드 내 표기 이원화.

**🟡 3. degrade 카드가 record 카드와 시각 무게가 같다** — 위 시각 위계 참조.
live 화면 절반이 결손인 현 상태(verification.md §10)에서 체감이 특히 크다.

**🟢 4. fold affordance 힌트 부재** — footer 여유 폭에서 1세그.

**🟢 5. 잘한 점(유지)** — 글리프+텍스트 이중 인코딩, `▸`/`▾` 사용(금지어 `folded`/`hidden` 회피로
`_TOGGLE_ROWS` 하이재킹 차단), fan-in `›` 재합류 표현, 60열 트리 글리프 보존 사다리.

---

## 재현
```bash
cd /home/Uihyeop/agent_setting-wt/fleet-v10-process-view
for w in 60 120 168; do
  COLUMNS=$w python3 tools/fleet/fleet.py --once
  COLUMNS=$w FLEET_DEMO=1 python3 tools/fleet/fleet.py --once --view process
done
```
> critic은 read-only다 — 위 수정은 방향 제안이며 반영 주체는 dev-team(execute/refine)이다.
