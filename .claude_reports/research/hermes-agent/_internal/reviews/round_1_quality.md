# Round 1 — Research Deliverable 품질 검토 (hermes-agent)

> 검토자: 품질관리팀 (plan-review 페르소나, research deliverable 품질 축). Read-only.
> 검토일: 2026-06-15. 대상: `00_briefing`~`07_security` 8개 + `cards/` 4개.
> 검토 축: coverage / no-fabrication / progressive disclosure / actionable roadmap / 내부 일관성.
> severity: 🔴 치명(날조·요청축 누락·자기모순) / 🟡 개선.

---

## 종합 verdict

🔴 **0건**. 🟡 6건. 이 deliverable 는 *no-fabrication 규율이 이례적으로 강하다* — 모든 주요 contested claim 이 cards 에 verbatim 근거를 두고, 마케팅 주장(40%·140k·most used)은 일관되게 ❓로 격리되며, digest 와 live 의 drift("0개" vs 58파일)도 03/06 양쪽에서 정직하게 reconcile 했다. 발견은 전부 *보강·정밀화* 수준이지 *날조·누락·모순*이 아니다.

---

## 🔴 실행 전 반드시 수정할 문제

**발견된 치명 문제 없음 ✅**

- 요청 4축(아키텍처·loop·장기기억·보안) + 벤치마킹 갭 + 이식 roadmap 모두 다뤄짐 (01·02·03·07 + 04 + 05). 누락 축 없음.
- cards 에 없는데 보고서에 새로 생긴 주장은 발견 안 됨. "Hermes 앞섬/우리 앞섬" 판정은 모두 axis 카드 또는 live 우리설정 파일(claim-verify는 `agents/research-team.md`, drill/study는 `loops/README.md`+`loops/drill/run.sh` 실재 확인)에 근거.
- SEO-only 주장이 사실로 격상된 곳 없음 — 오히려 07 §3·06 §4 가 SEO narrative("전부 보완")를 명시 기각.
- 보고서 간 정면 모순 없음 — "0개" vs "58파일"은 *digest 의 오류를 live 로 정정*한 의도된 drift note 이지 자기모순 아님.

---

## 🟡 보완하면 좋은 점

### 🟡 1. 갭 판정 표가 cards 의 confidence 한정을 일부 흡수하지 못함 (per-turn review)
- **위치**: `02_loop_engineering.md` §5 표 (line 126), `04_benchmark_gap.md` §1 표 (line 17) + §2(b).
- **문제**: "per-turn self-review = **Hermes 앞섬**" 판정이 근거로 `axis2 §1.2` 를 가리키는데, 정작 그 카드 section 은 *"background review 가 매 turn 후 돈다"* 에 **confidence: medium** (skills 페이지 진술 기준·architecture 페이지에 코드 위치 미수록 ❓) 을 붙였다. 00_briefing 은 이 한정을 line 76 에서 *"(high; review 메커니즘 위치는 medium)"* 으로 정직하게 inherit 했는데, 04/02 의 판정 표는 confidence 칼럼 자체가 없어 medium 한정이 사라지고 flat "Hermes 앞섬"으로 단정된다.
- **왜 문제인가**: 이식 1순위 근거가 되는 비교축인데, 메커니즘의 *존재·위치*가 medium 인 채로 "앞섬"이 확정처럼 보이면 T2/T4 의 우선순위 정당화가 실제보다 단단해 보인다. (briefing 이 이미 옳게 했으므로 04 가 그 표기를 못 따라간 *일관성 누수*)
- **제안**: 04 §1 표에 confidence 칼럼 추가, 또는 per-turn 행에 한해 "(메커니즘 위치 medium)" 각주. 04 §2(a) FTS5 행은 이미 "(confidence: high)"를 본문에 달았으니 같은 패턴을 per-turn 행에도.

### 🟡 2. live 메모리 수치가 이미 stale (58 → 현재 72파일 / 14 → 15 cwd)
- **위치**: `00_briefing` C7·`03_memory_system` §7 drift note·`06_resources` §5 — 모두 "**14 cwd / 58 파일**".
- **문제**: 검토 시점 live 재확인 결과 `projects/*/memory/*.md` = **72파일 / 15 cwd**. 보고서 작성(06-14)~검토(06-15) 사이에도 증가. drift note 가 *0개→58* 은 정정했으나, 그 정정 수치 자체가 곧 stale 되는 *moving target* 이다.
- **왜 문제인가**: 날조는 아님(작성 시점엔 맞았을 것) — 단 "58"이라는 정밀 수치가 본문 3곳에 박혀 향후 인용 시 틀린 숫자로 굳을 위험.
- **제안**: 정밀 수치 대신 *"수십 파일 규모이나 cwd 마다 비대칭·인덱스 얇음"* 같은 **추세 표현**으로 격하하거나, 수치 옆에 "(2026-06-14 측정, 증가 중)" 측정일 명시. 결론(비대칭·얇음·자동 recall 부재)은 수치와 무관하게 유효하므로 결론은 안전.

### 🟡 3. "우리 앞섬" 8개 판정의 비대칭 검증 깊이
- **위치**: `04_benchmark_gap.md` §1·§3.
- **문제**: Hermes 측 claim 은 1차 doc·source 로 엄격 검증(06 ledger)했는데, *"우리 앞섬"* 측 판정(claim-verify·drill·study·순서게이트·버전트래킹)은 우리설정 파일을 근거로 들되 *Hermes 에 "없다"* 는 부재 증명을 대부분 단정형으로 적었다("Hermes 에는 메타-시험 층이 없다"). 부재 증명은 본질적으로 약한 주장(못 찾은 것일 수 있음)인데 confidence 한정이 없다.
- **왜 문제인가**: adversarial deliverable 의 self-consistency — 상대 주장엔 ❓를 후하게 붙였는데 자기 우위 주장엔 안 붙이면 *방향성 편향*으로 보일 수 있다. (실제로 grep 으로 claim-verify/drill/study 는 live 확인되어 "우리 보유"는 참. 약한 건 "Hermes 미보유" 쪽.)
- **제안**: "Hermes docs/source 에서 *확인된 범위 내* 대응 층 없음" 식으로 부재 주장의 범위를 한정. §3(a)의 "(확실)" 같은 단정 토큰은 *우리 보유* 에만 쓰고, *Hermes 부재* 에는 "1차 doc 범위 내 미발견".

### 🟡 4. roadmap 난이도/리스크는 충실하나 *검증 방법*이 비어 있음
- **위치**: `05_implementation.md` §1 표·§2.
- **문제**: 이식 후보 6개가 우리 실파일 위치(전부 live 확인됨 ✅)·난이도·리스크·불변식 준수를 잘 짚었다. 다만 plan-review 기준의 *"이식이 성공했는지 어떻게 검증하나"* (T1 recall helper 의 smoke test, T3 stale 플래깅의 false-positive 측정 등)가 없다. roadmap 이 "무엇을·어디에" 는 구체적이나 "됐는지 확인" 은 추상적.
- **왜 문제인가**: 우리 파이프 자체가 graduated test 를 강제하는데(autopilot-code), 이식 roadmap 이 그 검증 단계를 안 명시하면 다음 spec 입력으로 넘어갈 때 verification section 이 빈 채로 시작된다.
- **제안**: 각 후보에 1줄 "수용 기준"(예: T1 = "기존 메모리 키워드로 recall helper 가 정답 파일 top-3 반환", T3 = "stale 플래깅 false-positive < N"). T2 는 이미 drill golden 재실행이 있어 거의 됨.

### 🟡 5. 07 보안 체크리스트가 본 deliverable scope 를 살짝 넘어 PRD 를 선취
- **위치**: `07_security.md` §4 (자율 에이전트 보안 체크리스트, ASI01–10).
- **문제**: 매우 잘 작성된 체크리스트지만, 이는 *우리가 자율 에이전트를 만들 때*의 PRD 입력 — 현 deliverable("Hermes 벤치마킹")의 *조사 결과*가 아니라 *후속 설계 산출물의 초안*에 가깝다. 04 §2 각주가 "그 PRD 의 필수 입력"이라 연결은 해뒀으나, research scope(=markdown 분석 리포트) 경계에서 보면 prescriptive 영역으로 한 발 넘어감.
- **왜 문제인가**: scope creep 자체가 해로운 건 아니나(오히려 유용), autopilot-research scope 정의상 "분석 리포트만"이므로 이 체크리스트는 *연구 결론*이 아니라 *handoff 부록*으로 라벨링하는 게 정직. 지금은 본문 §4 로 섞여 있어 검증된 조사결과와 미래 권고가 같은 무게로 읽힌다.
- **제안**: §4 헤더에 "(handoff — autopilot-spec 입력용 권고, 본 조사의 검증 결론 아님)" 명시. 이미 §4 도입부에 "PRD용"이라 적었으나 한 단계 더 분리.

### 🟡 6. progressive disclosure — Level 2 가 다소 무겁다
- **위치**: `00_briefing.md` Level 0/1/2.
- **문제**: Level 0(한 줄)·Level 1(6개 핵심발견)은 계층화가 정확하고 훌륭하다. 단 Level 2("1페이지 개관")가 정정표 C1–C7 + mermaid + 8개 numbered finding + Top-5 표로 *1페이지를 초과*한다. progressive disclosure 의 약속(레벨이 올라갈수록 점진)에서 Level 2 가 사실상 04 의 요약본 무게라 "1페이지" 라벨과 어긋난다.
- **왜 문제인가**: 경미. 계층 자체는 맞고 내용도 정확. "1페이지" 자칭과 실제 분량의 불일치일 뿐.
- **제안**: Level 2 라벨을 "1페이지 개관" → "개관" 으로 풀거나, 정정표를 Level 1.5(필수 인지) 로 빼서 mermaid+finding 만 Level 2 에. 우선순위 낮음.

---

## 🟢 잘 작성된 부분

- **No-fabrication 규율이 모범적**: 모든 contested claim(Atropos·Honcho·47 tools·40% faster·140k·most used·"전부 보완")이 cards 에 1차 근거를 두고, 출처 부재/2차/SEO 를 ❓·❌·⚠️로 *granular* 격리. 06 ledger 와 07 §출처 ledger 가 source-quality 를 명시적으로 등급화. adversarial deliverable 의 정직성 기준을 충족.
- **drift 처리가 정직**: digest "0개" 오류를 live 확인으로 정정하고 03 §7·06 §5·00 C7 *세 곳에서 일관*되게 reconcile + CLAUDE.md §1(근거 우선) 정책까지 인용. drift 를 숨기지 않고 명시.
- **roadmap 의 우리설정 anchoring 이 실재**: 05 가 가리킨 9개 파일경로(loops·skills·hooks)가 검토 시 *전부 live 존재*. T2 의 "drill FAIL 자동초안 backlog" 도 `loops/README.md` line 46 + `drill/run.sh` line 57 에 실재 — 공허한 일반론이 아니라 실제 backlog 의 구체화.
- **불변식 준수 검사가 후보별로 명시**: 6개 이식 후보 전부 "루프 출구는 제안까지, 결정은 사용자" 불변식 준수를 칸으로 명시하고, §3 에서 위반 항목(skill 자동 적용·memory 무승인 write)을 *명시적으로 거부*. 거버넌스 의식이 roadmap 전체에 일관.
- **보안 적대 판정의 균형**: 07 이 "Hermes 가 더 안전하게 *설계*됨"(공정 인정)과 "완전 안전은 거짓"(SEO 기각)을 *제작자 본인 SECURITY.md 인용*으로 동시에 성립 — 한쪽으로 치우치지 않은 모범적 adversarial 결론.
