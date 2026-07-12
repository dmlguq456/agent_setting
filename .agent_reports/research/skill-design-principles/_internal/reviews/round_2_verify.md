# Round 2 — Focused Verification (round-1 fix 반영 확인)

> reviewer: 품질관리팀 code-review(정적 검토) · date: 2026-07-13 · mode: fast, read-only
> scope: round-1 findings(🔴-1, 🟡-2~🟡-5) 의 수정 반영 + 새 왜곡·파일 간 불일치 여부.
> SoT: 00~07 보고서 + analysis_summary.md + cards(scottspence/glossary/startuphub) + _internal/pocock-verbatim-comparison.md + post-it/SKILL.md.
> verdict: **🔴 0** — 배포 산출물(00~07 보고서) 7건 전부 정확히 반영, 새 왜곡 없음. 잔여 🟡 3건은 모두 **upstream analysis_summary.md** 에만 남은 미동기화(보고서는 clean).

---

## 항목별 판정

### 1. `~50%` 귀속 (🔴-1) — 보고서 ✅ 완전 반영 / analysis_summary 미동기화(🟡)

**보고서(00·01·02·03·04·05·07): ✅ 반영.** round-1 이 cite 한 위치 전부 *"hook 워크어라운드 적용 후에도 남는 신뢰도"* 로 정정됨:
- 00: Level1 #1(line 76) "UserPromptSubmit hook 워크어라운드를 적용한 뒤에도 신뢰도가 ~50%", diagram(line 31) "hook 후에도 ~50%", 4축표(line 57) 동일.
- 01: line 28·111 "hook 워크어라운드를 적용한 뒤에도 ~50% … hook 만능론을 오히려 약화하는 근거".
- 02: line 48·52 "hook 후에도 ~50%".
- 03: line 12·39·44·52 "hook 워크어라운드 후에도 ~50%".
- 04: line 12·66·74 "hook 워크어라운드 뒤에도 ~50% 잔존".
- 05: line 43·65, 07: line 30.

bare auto-activation 신뢰도로의 오프레이밍 없음. "hook 이 신뢰도를 회복/해결" 강한 주장은 전부 제거되고 *"합당한 방향 … 신뢰도 이득은 측정 미검증"* hedge 로 대체됨. "우리 hook 이 더 낫다"류 미검증 단정도 *"성격이 다를 수 있으나 측정 미검증"* 으로 hedge. → 왜곡 해소 확인.

**🟡 잔여(analysis_summary §2(c), line 32)**: *"실전 auto-activation 신뢰도 ~50% → description wording 만으론 부족, hook 강제 보강 필요"* — 여기만 여전히 ~50% 를 bare 로 프레이밍하고 hook 을 remedy 로 제시. 🔴-1 이 cite 한 위치 목록엔 없었으나(01~05 보고서만 지목), 정정된 보고서와 **root-level 산출물끼리 drift**. 보고서를 진실로 삼으면 문제없으나 analysis_summary 도 root 배포물이라 동기화 권장.

### 2. post-it invocation 판정 (🟡-2) — ✅ 반영

06 §2 표(line 17) + Takeaway(line 20) + §5 요약(line 118) 모두 *"실사용상 user-driven 이나 frontmatter 에 disable-model-invocation flag 부재 → 원문 기준상 model-invoked default"* 로 대칭 정정. "user-invoked 명확" 단정 제거됨. post-it/SKILL.md 실물에 `disable-model-invocation` 부재 확인 — 정정 방향 정확. autopilot-research 와 동일 기준 적용(비대칭 해소).

### 3. failure-mode 종 수 (🟡-3) — 보고서 ✅ 반영 / analysis_summary 미동기화(🟡)

**02 §2: ✅.** intro(line 25) "canonical … 6종(premature completion/duplication/sediment/sprawl/no-op/negation) … variance bug 는 이 6종에 포함되지 않는 IH 축의 별도 failure", 표에 `canonical?` 열(✅ 6종 / ⚠️ 별도), Takeaway(line 37) "canonical 6종이고 variance bug 는 별도 집계 … Remio 5-test 는 negation 제외한 부분집합". 표·Takeaway 일치. 06 Takeaway(line 94)·요약(line 118)도 "6종 빠짐없이 커버, variance bug=Step 6" 로 정합.

**🟡 잔여(analysis_summary §7.2, line 75)**: *"no-op·sediment·duplication·sprawl 6종 진단?"* — 이름 **4개**만 나열하며 "6종" 라벨(round-1 🟡-3 가 cite 한 바로 그 위치). 미수정. (같은 파일 line 51/pocock-verbatim §5 의 "6종"은 count 만 언급이라 무해.)

### 4. 00 계보 (🟡-4) — ✅ 반영

00 Level1(line 11): *"StartupHub 의 Trigger/Structure/Steering/Pruning 을 국문화한 계보 … StartupHub 의 3번째 축 라벨 자체는 'Steering'이고, '유도/Guidance'는 그 라벨이 아니라 정의문(how the skill is guided to…)을 옮긴 것 — canonical 라벨은 Steering"*. "StartupHub 가 라벨을 Guidance 로 불렀다"는 오해 유발 표현 제거. 01 lineage diagram·verbatim §2 와 정합.

### 5. 04 Steering 정의 인용부호 (🟡-5) — 보고서 ✅ 반영 / analysis_summary 미동기화(🟡)

**04 ③(a)(line 24): ✅.** paraphrase 를 quote 로 감싼 형태 제거 — *"런타임 행동을 Predictability 로 형성하는 레버들 — GLOSSARY verbatim 은 'how the agent's runtime behaviour is shaped'"* 로, 서술은 평문 + GLOSSARY verbatim 만 인용부호. GLOSSARY 카드 line 13 원문과 일치.

**🟡 잔여(analysis_summary §4(a), line 46)**: *"the levers that shape the agent's runtime behaviour toward Predictability."* 를 여전히 인용부호로 감쌈(paraphrase-as-quote). round-1 🟡-5 가 명시 cite 한 위치인데 보고서만 고치고 analysis_summary 는 미수정.

("fog of war" 예시어는 round-1 fact-check 표 line 19 에서 code_search.md:31-33 대조 ✅ 확인됨 — 별도 문제 아님.)

### 6. "gerund" 오귀속 (🟡-3 fact-check) — ✅ 반영

02 §1 표(line 12) + Takeaway(line 21): *"3인칭 + 'Use when…' … Anthropic verbatim 은 'third person'·'Use when…'까지 지원(gerund 은 원문에 없음, 우리 컨벤션상 선호)"*. 00(line 77)·05·06(line 46·50)·07(line 16) 전부 "3인칭 'Use when…'" 로 통일, gerund 는 "우리 컨벤션 선호"로 명시 격리. Anthropic 오귀속 해소.

### 7. 06 로드맵 (커버리지) — ✅ 반영

- **Step 0(Predictability 정합)** 추가(line 28-33): root virtue 점검을 4축 레버 앞단에 배치 + Before/After.
- **Step 4 completion criterion / premature completion** 추가(line 67-72): checkable+exhaustive + post-completion steps 를 실제 context 경계 뒤로 + Before/After.
- Takeaway(line 94): 8-Step(0~7)이 02 failure-mode 6종을 빠짐없이 커버(매핑 명시: no-op/sediment/dup/sprawl=Step3, premature=Step4, negation=Step5, variance bug=Step6).
- **Next Pipeline 표 Takeaway** 추가(line 106): `/audit → /autopilot-spec → /autopilot-code --mode refactor` 단방향 순서 명시.

### 8. 새 오류·파일 간 불일치 — 보고서 clean, upstream 3건 drift

- **보고서 00~07 내부 일관**: `~50%` 표현("hook 워크어라운드 후에도 ~50%")·failure-mode "6종 + variance bug 별도"·"3인칭 'Use when…'" 전부 파일 간 일치. 새 왜곡·모순 없음.
- **upstream analysis_summary.md drift 3건**(위 1·3·5): §2(c) ~50% bare 프레이밍, §7.2 "4-names as 6종", §4(a) paraphrase-as-quote. 모두 정정된 보고서와 어긋남 — 보고서를 진실로 삼으면 무해하나, root-level 산출물 정합을 위해 동기화 권장.

---

## 종합

- **배포 산출물(00~07) 기준 🔴 0, 새 왜곡 0.** round-1 의 🔴-1 및 🟡-2~🟡-5 지적이 보고서에 정확·hedge 포함해 반영됨. 특히 🔴-1(수치 재배치 왜곡)은 프레이밍·강한주장·미검증단정 세 축 모두 해소.
- **잔여 🟡 3건은 전부 analysis_summary.md(upstream stage 산출물)에 국한** — 🟡-3·🟡-5 는 round-1 이 그 파일을 명시 cite 했으므로 partial-fix(보고서만 수정), 🟡-1(§2c)은 정정 보고서와의 신규 drift. 저비용 sync 로 정리 가능(1 파일 3줄).
- 칭찬: hedge 규율이 균일하다 — 5개 보고서에서 "합당한 방향 / 측정 미검증" 문구가 기계적으로 반복되지 않고 문맥마다 자연스럽게 배치됐고, 06 은 표본 대표성 hedge(line 22)·가공 예시 disclosure 까지 유지.
