# Round 1 — Quality Review (survey report)

- **Topic**: cross-platform-agent-frameworks
- **Reviewer role**: autopilot-research Step 4b quality reviewer (read-only)
- **Scope**: coverage · no-fabrication · progressive disclosure · actionable roadmap
- **Not in scope** (fact-checker's job): per-citation venue/year/metric verification (star counts, release dates, version strings)

**Verdict: PASS (강함) — 채택 권고안이 GSD 단일 prior art 에 의존한다는 점만 명시 유지하면 draft 진행 가능.**

---

## 1. Coverage — 요구 조사 대상 9종 전부 반영됨 ✓

task 가 지정한 대상과 보고서 반영을 대조:

| 요구 대상 | card | report 반영 |
|---|---|---|
| GSD | `gsd.md` | 01·03·04(a/d)·06 후보1·07 Tier1 — 최우선 후보로 심층 |
| spec-kit | `spec-kit.md` | 01·03·04(a)·06 후보2·07 Tier1 |
| BMAD-METHOD | `bmad-method.md` | 01·03·04(a/c)·05 |
| SuperClaude | `superclaude.md` | 01·03·04(b)·반면교사(drift 약함) |
| Superpowers | `superpowers.md` | 01·03·04(b)·lifecycle 재주입 |
| Agent OS | `agent-os.md` | 01·03·04(a)·profile inheritance |
| claude-flow | `claude-flow.md` | 01·03·04·05·#1834 반면교사 |
| Claude Code 공식 plugin | `claude-code-official-plugins.md` | 02 §1(host 규격)·03·04(a) version/SHA-pin |
| 멀티하네스 projection | `multi-harness-projection.md` | 02 §2(AGENTS.md)·04(d) ruler/rulesync 3층 처리 |

9개 카드 = 9개 대상 모두 landscape/comparison/deep-dive 에 등장하고, 각자 고유 역할(후보·반면교사·표준 target)로 배치됨. 누락 없음. 추가로 ruler/rulesync/AGENTS.md/agent_sync 까지 multi-harness 카드에서 포섭 — 요구 이상.

## 2. No-fabrication — 소급성 견고, caveat 보존 우수 ✓

report 주장을 card/analysis_summary 로 역추적한 결과 **날조·과장 삽입 없음**. 특히 잘한 점:

- **파생/마케팅 수치를 report 로 승격하지 않음**: GSD 카드가 "파생 plugin 문구, gsd-core 소스 미검증" 으로 격리한 `~92% token 감소`·`MCP-backed state` 가 report 어디에도 사실로 올라오지 않음. 04(b) 는 검증된 byte-budget(XL 90KB)만 인용.
- **unverified 꼬리표가 report 까지 일관 전파**: GSD 버전 drift(1.7.0-rc.4 vs changelog v1.4x), Agent OS email-gated install, claude-flow Codex parity 미검증, AGENTS.md governance 2차 출처(60,000+ repo "주장") 가 01·02·05·07 에서 caveat 로 그대로 유지됨.
- **수치 일치 spot-check 통과**: Superpowers "6+ harness"(카드 §1 은 7개 adapter 폴더 실측)·description ≤1024자·getting-started 150 words, claude-flow "12 worker/35 plugin/#1834", GSD "~61 skill/16 runtime" 모두 카드 근거와 일치.

**단 하나 주의(날조 아님, over-confidence 경계)**: 전 보고서의 중심 논거인 **GSD hash-manifest + `--reapply`** 는 gsd 카드 §2 에서 `docs/how-to/update-gsd.md` 기반 서술이고 `bin/install.js` line-level 은 카드 스스로 "재확인 필요"로 남긴 항목이다. report 는 이 메커니즘의 *존재*를 사실로 다루면서 "line 단위 미검증" 만 caveat 로 단다. 04(a) 의 reapply 흐름을 "의사 흐름(pseudo)"으로 라벨링한 건 정직한 처리지만, adopt 결정 전체가 이 단일 부분검증 prior art 에 걸려 있으므로 → §4 참조.

## 3. Progressive disclosure — 00_briefing 레벨 구성 양호 ✓

00_briefing 은 TL;DR → findings → visual → action 순으로 잘 계층화:
- **L0 한 줄 요약**: "prior art 는 GSD hash-manifest 하나뿐, 나머진 우회" — 핵심 결론을 먼저.
- **L1 Key Findings(5)**: 각 bullet 이 근거 링크(`analysis_summary §N`, `card §N`) 동반.
- **L2 mermaid 1-page overview**: 4카테고리 색상 강조(GSD 녹색=최우선, SuperClaude 적색=반면교사)로 시각 위계 명확.
- **L3 Top-3 Actionable Insights**: 각 insight 가 06 candidate·근거 카드로 drill-down 링크.

레벨 간 중복 최소, 각 레벨이 다음 레벨로 정확히 라우팅됨. 상호참조 링크(01/03/04/06)도 정합. 개선여지(경미): L1 finding 3 "파일-복사식 배포가 drift 를 낳는다"와 L3 insight 가 직접 연결 안 됨 — insight 에 "파일복제 회피"(05·06 §4 에 실재)를 4번째로 넣으면 finding↔action 대칭이 완성되나 필수는 아님.

## 4. Actionable roadmap — 06 매우 구체적, 실행가능 ✓

- **가중 selection matrix**: 4기준(drift robustness 0.40 등)을 repo 의 명시적 pain point 에 정렬 — 임의 가중 아님.
- **후보별 pros/cons/적합도** + 후보 간 관계(2는 1을 대체 못 하고 보완, 3은 소비-only 로 범위 한정) 명확.
- **pilot plan 이 실파일 지목**: `adapters/claude/settings.json` projection 1~2개 대상, 성공기준 3개(보존/충돌 report/소유경계), baseline(현 convention 대비 delta), 선행검증(GSD `bin/install.js`·`state-transition.cjs` 정독). 추상 권고가 아니라 바로 착수 가능한 수준.
- **risk table** 이 "GSD 실코드가 카드 서술과 다를 수 있음"을 명시적 리스크로 등재하고 pilot 전 정독으로 완화 — §2 에서 지적한 over-confidence 를 로드맵이 스스로 방어함.
- **next pipeline** 커맨드·경계 disclaimer 까지 완비.

**보완 제안(경미, blocking 아님)**: adopt 논거가 GSD 단일 후보에 집중돼 있으므로, "만약 pilot 에서 GSD 실코드가 서술과 다르면?"의 fallback 이 로드맵에 없다. 후보2(spec-kit registry)·보조(override-layer 승격)는 hash-manifest 감지 기능을 대체하지 못한다고 06 이 명시하므로, hash-manifest 이식이 실패할 경우의 대안(예: override-layer + explicit warning 만으로 축소 채택)을 risk 완화 열에 한 줄 추가하면 단일점 의존이 완화됨.

---

## 종합

4개 축 모두 통과. 특히 no-fabrication 의 caveat 전파 규율과 06 pilot 의 구체성이 강점. 유일하게 신경 쓸 점은 **전체 adopt thesis 가 부분검증 상태의 GSD hash-manifest 하나에 걸려 있다**는 구조적 집중이며, 이는 이미 report 가 (a) pseudo-flow 라벨 (b) risk 등재 (c) pilot 선행 정독으로 정직하게 다루고 있다. draft 단계 진행에 지장 없음. 위 §4 fallback 한 줄만 보완 권장.
