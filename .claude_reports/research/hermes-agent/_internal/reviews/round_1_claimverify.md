# Round 1 — Claim Verify (adversarial, N-vote 외부 진위)

> mode: claim-verify (research-team). 적대적 외부 truth — NOT provenance(fact-check 분담), NOT quality.
> 각 material claim 당 3 skeptical voter(default-refute) → WebSearch 모순 탐색 → 다수결 kill / quorum abstain.
> 조사일 2026-06-15. 대상 = hermes-agent 보고서 8개(00~07)의 material claims.

## 결론 1줄

검증한 22 material claim 중 **🔴 kill 0건 / 🟡 abstain 4건 / ✅ survive 18건**. 우선 7개 priority claim 은 **전부 1차 소스로 외부 재확인 survive**. 단, 일부 claim 은 보고서가 _스스로_ "약함/2차/미확인"으로 이미 한정한 것(40% faster·140k stars·most-used)이라 본 검증은 그 한정의 정당성을 확인하는 방향으로 survive 처리 — 즉 "claim 자체가 틀렸다"가 아니라 "보고서의 약-신뢰 라벨이 정확하다"는 의미. **내부 metric 오류 2건 발견**(fact-check 분담이나 외부 검색 중 포착 → 아래 명시).

---

## Claim Verify 표

| # | Claim | Source(quality) | Vote (survive-refute) | Verdict | Confidence | 반증/확인 근거(URL) |
|---|---|---|---|---|---|---|
| P1 | "40% faster with self-created skills" — **1차 출처 부재** (보고서 주장 = 출처 없음) | SEO/2차만 (tokenmix·medium·nxcode·ofox·dev.to) | 3-0 survive (보고서의 "1차 부재" 한정이 정확) | ✅ | medium | 다수 블로그에 "40%" 출현하나 전부 SEO/aggregator. Nous README/docs/NVIDIA blog 직접 진술 미확인 → "1차 부재" 라벨 정당. [tokenmix](https://tokenmix.ai/blog/hermes-agent-review-self-improving-open-source-2026) |
| P2a | "140k GitHub stars in ~3 months" | NVIDIA blog(2차, GitHub 인용) | 2-1 survive | ✅ | low | NVIDIA blog·business20·byteiota 모두 "140k stars in under 3 months" 진술하나 시점 의존(95.6K~193k 변동). Nous 1차 측정 아님 → "2차 인용" 라벨 정당. [NVIDIA](https://blogs.nvidia.com/blog/rtx-ai-garage-hermes-agent-dgx-spark/) |
| P2b | "most used agent on OpenRouter" | NVIDIA blog(2차) | 2-1 survive | ✅ | low | NVIDIA blog 가 OpenRouter 인용(224B vs 186B tokens/day). OpenRouter rankings 1차 직접확인 실패는 보고서 자인. 약-신뢰 라벨 정당. [NVIDIA](https://blogs.nvidia.com/blog/rtx-ai-garage-hermes-agent-dgx-spark/) |
| P3a | OpenClaw **CVE-2026-25253** = 1-click RCE via gatewayUrl token exfil, CVSS 8.8 실재 | GHSA-g8p2 + Hacker News + SonicWall + SOCRadar + GitLab advisory(1차 다수) | 3-0 survive | ✅ | high | 강하게 실재. CWE-669, CVSS 8.8, gatewayUrl auto-WebSocket 무검증 — 카드와 정확 일치. [GHSA-g8p2](https://github.com/openclaw/openclaw/security/advisories/GHSA-g8p2-7wf7-98mq), [Hacker News](https://thehackernews.com/2026/02/openclaw-bug-enables-one-click-remote.html) |
| P3b | **GHSA-m3mh-3mpg-37hw** = .npmrc RCE 실재 | GitHub/GitLab advisory(1차) | 3-0 survive | ✅ | high | 실재. `--ignore-scripts` 하되 project-level `.npmrc` strip 안 함 → git executable hijack. fixed 2026.3.24 — 카드 일치. ⚠️ **단 CVSS 라벨 오류**: 카드 "8.6", advisory 실제 **3.1** (CWE-426). [GitLab](https://advisories.gitlab.com/pkg/npm/openclaw/GHSA-m3mh-3mpg-37hw/) |
| P3c | **GHSA-g27f-9qjv-22pm** = log poisoning indirect prompt injection 실재 | GitHub/GitLab advisory + Eye Research + eSecurityPlanet(1차+2차 다수) | 3-0 survive | ✅ | high | 실재. WebSocket Origin/User-Agent header 무sanitize 로깅 → LLM debug 시 injection. fixed 2026.2.13 — 카드 일치. [GitLab](https://advisories.gitlab.com/pkg/npm/openclaw/GHSA-g27f-9qjv-22pm/) |
| P4 | OpenClaw = **Peter Steinberger** 작, `github.com/openclaw/openclaw`, 개명 Clawdbot→Moltbot→OpenClaw | Wikipedia + winbuzzer + alternativeto(medium-high 다수) | 3-0 survive | ✅ | high | 확인. Steinberger(오스트리아), Anthropic 상표 압박으로 Moltbot 개명(2026-01-27), 3일 후 OpenClaw. npm 패키지명 `clawdbot` 잔존도 일치. ⚠️ 카드 "Warelay→CLAWDIS→Clawdbot"의 초기 단계 중 CLAWDIS 는 외부 미확인(Warel/Clawd 는 확인) — 핵심 attribution 엔 무영향. [Wikipedia](https://en.wikipedia.org/wiki/OpenClaw) |
| P5 | Hermes SECURITY.md: "in-process 방어는 그 무엇도 containment 아님" 실제 문구 | Hermes SECURITY.md raw(1차) | 3-0 survive | ✅ | high | **verbatim 확인**: "Nothing inside the agent process constitutes containment — not the approval gate, not output redaction, not any pattern scanner, not any tool allowlist." 카드 인용 정확. [SECURITY.md](https://github.com/NousResearch/hermes-agent/blob/main/SECURITY.md) |
| P6 | Atropos = training-time RL environments framework, 런타임 self-improvement 아님, trainer 미포함 | atropos README(1차) | 3-0 survive | ✅ | high | 확인. "trainer is not included"; Axolotl plugin·Tinker·example trainer 외부. Hermes runtime 통합 언급 없음 — 카드 핵심 판정 정확. [atropos](https://github.com/NousResearch/atropos) |
| P7 | Honcho = Plastic Labs 외부 FastAPI dialectic user modeling, optional provider | honcho repo + dev.to(1차+2차) | 3-0 survive | ✅ | high | 확인. FastAPI server(+Postgres+Redis), peer paradigm, dialectic background reasoning. `plastic-labs/honcho`. 외부 서비스 — 카드 "C3 정정"(내장 아님) 정확. [honcho](https://github.com/plastic-labs/honcho) |
| S1 | Atropos BFCL: parallel 10%→46%(4.6x), simple 21%→51.75%(2.5x) | atropos README + HF model card(1차, self-reported) | 3-0 survive | ✅ | medium | HF DeepHermes-ToolCalling-Specialist-Atropos 수치 일치. **단 self-reported·독립재현 미확인이며 _Atropos 학습 모델_ 수치이지 Hermes 런타임 개선 아님** — 카드의 이 한정이 핵심. [HF](https://huggingface.co/NousResearch/DeepHermes-ToolCalling-Specialist-Atropos) |
| S2 | OpenClaw ClawHub 악성 skill → AMOS(Atomic Stealer) supply chain | Trend Micro + Hacker News + SC Media(1차+2차 다수) | 3-0 survive | ✅ | high | 확인 — 실제로 카드보다 강함. "ClawHavoc" 캠페인, 341 악성 skill, AMOS/keylogger/backdoor. SKILL.md 안 악성 지시. [Trend Micro](https://www.trendmicro.com/en_us/research/26/b/openclaw-skills-used-to-distribute-atomic-macos-stealer.html) |
| S3 | OpenClaw HEARTBEAT.md persistent backdoor + .env plaintext secret + `_exec` no-approval/sandbox | HiddenLayer(1차 security firm) | 2-1 survive | ✅ | medium | HiddenLayer 분석 실재 확인. 개별 메커니즘 세부는 HiddenLayer 단독 의존(다른 firm 교차는 AMOS/CVE 쪽). 출처 등급-강도 부합. [HiddenLayer](https://www.hiddenlayer.com/research/exploring-the-security-risks-of-ai-assistants-like-openclaw) |
| S4 | "Lethal Trifecta 정식 충족" (HiddenLayer 라벨) | HiddenLayer(1차) | 2-1 survive | ✅ | medium | trifecta(private data + untrusted content + exfil) 프레임은 HiddenLayer/업계 통용. OpenClaw 4요소 동시성립 주장은 HiddenLayer 단독이나 구성요소(CVE·AMOS·.env)는 별도 1차 확인됨 → 합성 주장 survive. |
| S5 | Curator: inactivity check(7d interval+2h idle)로 active→stale(30d)→archived(90d) 결정론적 전이 | Hermes curator.md(1차 docs/repo) + KuCoin/Phemex(2차) | 3-0 survive | ✅ | high | 1차 doc 확인. "deterministic state machine, no model"; 30d stale/90d archive; 7d interval+2h idle; bundled/hub skill 미관여 — 카드 일치. [curator.md](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/curator.md) |
| S6 | hub-and-spoke: 단일 AIAgent core, 4 entry(CLI/Gateway/ACP/cron), provider-agnostic 18+ | Hermes repo+docs(1차) | 3-0 survive | ✅ | high | repo+docs 교차. v2026.5.16 태그 실재, "The Surface Release" framing 확인. 메커니즘 진술 = high. [repo](https://github.com/NousResearch/hermes-agent) |
| S7 | skill self-edit = `skill_manage`(create/patch/edit/delete), 매 turn 후 background review 트리거 | Hermes docs(1차) + 다수 2차 | 3-0 survive | ✅ | medium | 학습 loop·skill 자동생성·per-turn review 진술 다수 확인. 단 review 의 _코드레벨 위치_ 는 카드도 medium(architecture page 미수록) — 한정 유지. |
| S8 | FTS5 cross-session recall(`session_search`, unicode61+trigram, state.db schema v11) | hermes_state.py source(1차) | 3-0 survive | ✅ | high | source 직독 근거(카드). 외부 모순 없음. DDL·trigram CJK 진술 일관. [hermes_state.py](https://github.com/NousResearch/hermes-agent) |
| S9 | hermes-agent-self-evolution = DSPy+GEPA 텍스트 진화(weight 비학습, inference-time) | repo(1차) | 3-0 survive | ✅ | high | repo 실재 확인, "Evolutionary self-improvement ... DSPy + GEPA" — 카드 일치. weight 비학습 framing 정확. [repo](https://github.com/NousResearch/hermes-agent-self-evolution) |

---

## 🟡 abstain (미검증 — quorum/소스부족, 통과 X)

| # | Claim | 사유 | Verdict |
|---|---|---|---|
| A1 | "47 built-in tools" / 정확 tool 수 | 1차끼리 40/60/70 drift, 특정 tag `tools/registry.py` 직독 필요 — 외부 검색으로 단일값 확정 불가 (보고서도 ❓ 격리) | 🟡 |
| A2 | ThreadPoolExecutor "8 parallel workers" | mirror(2차) 단독, 공식 doc 직접 수치 미확인 (보고서 자인) | 🟡 |
| A3 | `nudge_interval` 정확 턴 수 | 1차 doc 미노출, 외부도 수치 미확인 (보고서 ❓) | 🟡 |
| A4 | DGX Spark/RTX **전용** optimization path (NIM 지원 넘어선 전용 최적화) | NVIDIA 협업·NIM 지원은 확인되나 "전용 path" 는 NVIDIA 마케팅 blog 의존 — primary 부재 (보고서 low) | 🟡 |

> abstain 4건 모두 보고서가 _이미_ ❓/미확인으로 격리한 항목 — 본 검증은 그 격리가 옳았음을 재확인. 결론·이식 판단에 쓰이지 않으므로 무해.

---

## 🔴 kill — 없음 (0건)

material claim 중 외부 1차 소스가 _반박_ 하는 것은 발견되지 않음. 보고서가 약-신뢰로 라벨한 claim(40%·stars·most-used)도 "틀렸다"가 아니라 "1차 부재/2차 인용"이라는 보고서의 한정 자체가 정확 → kill 아닌 survive(low/medium conf).

---

## ⚠️ 내부 metric 오류 (fact-check 분담이나 외부 검색 중 포착 — 정정 권고)

본 mode 는 외부 진위 담당이나, CVE 검색 중 **카드의 CVSS metric 2건 오기**를 발견. provenance/verbatim 은 round_1_factcheck.md 소관이나 외부 advisory 와 대조해 명시:

1. **GHSA-m3mh (.npmrc RCE)**: 카드/07_security `8.6 High` → advisory 실제 **CVSS 3.1** (CWE-426 Untrusted Search Path). **8.6 의 출처 불명** — advisory 직접값과 불일치.
2. **GHSA-g27f (log poisoning)**: 카드 `3.1 Low` → advisory 도 Low 계열이나, 카드가 m3mh=8.6/g27f=3.1 로 둔 배치가 의심됨(3.1 은 실제 m3mh 값). **두 advisory 의 CVSS 라벨이 서로 swap 됐을 가능성** — 07_security.md §1 취약점 표 CVSS 열 재확인 권고.

> 영향: CVE/GHSA 의 _실재·성격·핵심 판정_ 은 전부 survive(무영향). 잔존 위험은 _CVSS 숫자 라벨_ 정확도뿐 — 결론(OpenClaw 보안 다수 1차 검증·"전부 보완" 기각)은 불변. 단 camera-ready 면 정정 필요.

---

## inline 메모 권고 (호출자 반영용)

abstain/약-신뢰 항목은 보고서가 이미 confidence 라벨·❓ 격리로 반영 중 — 추가 inline 메모 불필요. 단 위 metric 오류 2건은 07_security.md §1 표에 정정 메모 권고:
- `<!-- memo: [VERIFY] GHSA-m3mh CVSS = 3.1 (CWE-426), not 8.6 — advisory 직접값 대조 (GHSA-m3mh-3mpg-37hw) -->`
- `<!-- memo: [VERIFY] GHSA-g27f/m3mh CVSS 라벨 swap 의심 — advisory 재확인 -->`

---

## 도메인 노트 (agent memory 후보)

- 이 도메인(NousResearch Hermes / OpenClaw 보안)은 **SEO/affiliate noise 가 극심** — "40% faster"·star 수·비교 narrative 가 블로그에 대량 복제되나 Nous 1차 부재. 보고서가 이를 정확히 격리한 것은 모범.
- OpenClaw CVE 군은 **1차 검증이 견고**(GHSA advisory + Hacker News/Trend Micro/SonicWall 등 다수 firm) — 보안 claim 은 강하게 survive.
- 반복 false-survive 위험 회피: CVSS _숫자_ 는 advisory 직접값 대조 필수(블로그가 자주 swap/round). 본 라운드 metric 오류 2건이 그 사례.
