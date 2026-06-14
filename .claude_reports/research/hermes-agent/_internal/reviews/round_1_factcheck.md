# Round 1 — Fact-check (verbatim 카드 대조)

> 대상: `00_briefing` ~ `07_security`. Single source of truth = `cards/axis1~4`.
> 방식: 보고서 도메인 claim(모델명/버전/수치/CVE·CVSS/GHSA/날짜/메커니즘/스키마/repo URL) ↔ 카드 verbatim.
> 표기: 일치 ✅/❌, severity 🔴(날조·불일치) / 🟡(한정 누락) / — (정합·무문제).
> cost-aware: 가장 material 한 claim 위주. severity 없는 행은 "카드와 일치" 확인용.

## A. 지정 점검 항목 (사용자 명시 9종)

| 보고서 | 섹션 | Claim | 근거 카드 (file:line) | 일치 | severity |
|---|---|---|---|---|---|
| 01 / 00 | 01 §4 / 00 mermaid | "70+ registered tools / ~28 toolsets" | axis1:52, axis1:100 | ✅ | — |
| 00/01/06 | 표제·근거 | v0.16.0 "The Surface Release" (2026-06-06) | axis1:5, axis1:17 | ✅ | — |
| 02 / 00 | 02 §4 / 00 L20·C2 | Atropos = training-time RL environments framework (런타임 self-improvement 아님, trainer 미포함) | axis2:106, axis2:111, axis2:121-122 | ✅ | — |
| 03 / 00 | 03 §5 / 00 C3 | Honcho = Plastic Labs (`plastic-labs/honcho`) FastAPI server, optional provider | axis3:152-153 | ✅ | — |
| 03 / 01 | 03 §4 / 01 §6 | FTS5 이중 테이블 messages_fts(unicode61, external content) + messages_fts_trigram(trigram CJK) | axis3:88-89, axis3:97-103 | ✅ | — |
| 07 / 00 | 07 표·1-A / 00 C6 | CVE-2026-25253, CVSS 8.8 High, 1-click RCE gatewayUrl token exfil, patched 2026.1.29 | axis4:28-33, axis4:72 | ✅ | — |
| 07 | §1·ledger | GHSA-g8p2-7wf7-98mq / GHSA-m3mh-3mpg-37hw (8.6, CVE 없음) / GHSA-g27f-9qjv-22pm (3.1) | axis4:33,38,39,45 | ✅ | — |
| 00/04/07 | 인용구 | "Nothing inside the agent process constitutes containment …"("in-process 방어는 containment 아님") | axis4:104 (verbatim) | ✅ | — |
| 00/03/06 | 00 C7 / 03 §7 drift / 06 §5 | auto-memory "14 cwd / 58 파일" (live 관찰, digest "0개" 와 drift) | **카드 근거 없음** (cards 는 Hermes 외부조사 — 우리 세팅 수치 미수록) | ❌ | 🟡 |

> auto-memory 14cwd/58파일: cards 에 매칭 근거 없음이 **정상** — 이는 우리 세팅 live 관찰값이고 cards 는 Hermes 외부 벤치마킹 전용. 보고서가 "live 확인"·"digest 와 drift 명시"로 출처를 정직히 표기하고 있어 날조 아님. 단 fact-check 관점에선 카드-backed 가 아니므로 🟡 (검증은 live 코드 재확인에 의존 — 본 모드 범위 밖). **권고**: live `projects/*/memory/` 재집계로 수치 확정.

## B. 추가 material claim 대조

| 보고서 | 섹션 | Claim | 근거 카드 (file:line) | 일치 | severity |
|---|---|---|---|---|---|
| 01 | §2·§5 | AIAgent in `run_agent.py`, "synchronous orchestration engine", hub-and-spoke 4 entry | axis1:27,49 | ✅ | — |
| 01 | §2 | Provider Resolution "18+ provider" | axis1:51 (18+) | ✅ | — |
| 01/03 | 01 §3 / 03 §4 | ThreadPoolExecutor "최대 8 parallel workers" | axis1:73 (mirror, ❓공식 doc 미확인) | ✅ | 🟡 |
| 03/04 | 03 §4 / 04 §2a | "session_search ~20ms FTS5" | axis3:78 (~20ms) | ✅ | — |
| 03 | §1 표 | MEMORY.md 2,200 char(~800 tok) / USER.md 1,375 char(~500 tok) | axis3:16-17,34-35 | ✅ | — |
| 03 | §4 | state.db schema_version=11, WAL, busy 1s, retry 20–150ms max 15, checkpoint 50 write PASSIVE | axis3:84,120 | ✅ | — |
| 02/03 | curator | Curator inactivity: interval_hours 7d + min_idle_hours 2h; stale 30d / archive 90d | axis2:79,74 / axis3:65 | ✅ | — |
| 02 | §2.2 | LLM review = "background fork of AIAgent", max_iterations=8 | axis2:66 | ✅ | — |
| 02 | §4 | BFCL parallel 10%→46%(4.6x), simple 21%→51.75%(2.5x) | axis2:128 | ✅ | 🟡 |
| 02 | §3 | cron 60s tick, isolated fresh session, "cannot recursively create cron jobs" | axis2:93-94 | ✅ | — |
| 02/03 | 02 §1.5 / 03 §5 | Honcho 5 tool (honcho_profile/search/context/reasoning/conclude) | axis3:165-172 | ✅ | — |
| 03 | 부록 | external provider "9종", Holographic fact_store 9 actions(…contradict…) | axis3:218 | ✅ | — |
| 02 | §1.1 | skill SKILL.md+frontmatter, `~/.hermes/skills/`, agentskills.io 호환 | axis2:12,16 | ✅ | — |
| 02 | §1.3 | skill_manage actions create/patch/edit/delete/write_file/remove_file | axis2:31 | ✅ | — |
| 01/06 | 마케팅 | "140k stars in 3 months" = NVIDIA 2차 인용(Nous 1차 아님) | axis2:140 | ✅ | — |
| 00/04/06 | 마케팅 | "40% faster" = 1차 출처 없음 (SEO-only) | axis2:139 | ✅ | — |
| 07 | §1 | OpenClaw 개명 Warelay→CLAWDIS→Clawdbot→Moltbot→OpenClaw; npm pkg `clawdbot` | axis4:16 | ✅ | — |
| 07 | §1 | Peter Steinberger, 2026-02-14 OpenAI 합류; repo openclaw/openclaw, MIT, TS+Swift | axis4:14-15 | ✅ | — |
| 07 | §1 | HiddenLayer 발견(_exec unsandboxed, HEARTBEAT.md backdoor, plaintext .env, AMOS supply chain, Lethal Trifecta) | axis4:48-55 | ✅ | — |
| 07 | §1 | arXiv:2603.10387 defense rate Claude Opus 4.6 83% / DeepSeek V3.2 17%; sandbox escape 17%, priv-esc 8% | axis4:58-59 | ✅ | — |
| 07 | §2 | 7-layer defense-in-depth (allowlist/approval/container/MCP cred filter/context scan/cross-session iso/input sanit) | axis4:94-102 | ✅ | — |
| 07 | §2 | container backend 시 dangerous command check skip | axis4:109 | ✅ | — |
| 01/04 | 01 §3 / 04 §1 | 6 terminal backend: local/Docker/SSH/Singularity/Modal/Daytona | axis1:82 | ✅ | — |
| 01/00 | platforms | "20+ 채널" gateway (정확값 20~22 drift) | axis1:131-136 | ✅ | — |

## C. 🟡 한정 누락 정밀 (카드는 미검증/저신뢰인데 보고서 단정 여부)

| # | 항목 | 카드 confidence | 보고서 표기 | 판정 |
|---|---|---|---|---|
| 1 | ThreadPoolExecutor 8 worker | axis1:73·153 = mirror only, "❓공식 doc 미확인", medium | 01 §3 표에 "high (mirror; ❓공식 doc 직접 수치 미확인)" 병기, 본문 §1 요약은 "70+ 등록"만 언급(8 worker 단정 없음) | 🟡 경미 — 표에는 한정 보존, 본문 mermaid/요약엔 8worker 미등장이라 OK. **유지** |
| 2 | BFCL 4.6x/2.5x | axis2:128·130 = "Atropos 자체 보고, 독립 재현 ❓미검증", **Atropos 학습 모델 수치이지 Hermes 런타임 개선 아님** | 02 §4 가 "(confidence: high on 수치 보고; 독립 재현 ❓미검증) — 이는 Atropos 로 학습한 모델 수치이지…" 로 한정 보존 | 🟡 → 사실상 충족. 단 00/04 에는 이 수치 미인용(올바름). **유지** |
| 3 | per-turn background review 메커니즘 위치 | axis2:28 = "confidence medium, architecture 페이지 미수록 ❓" | 00 L76·02 §1.2 모두 "(high; review 메커니즘 위치는 medium)" / "(confidence: medium … ❓)" 병기 | ✅ 한정 보존 |
| 4 | nudge_interval 정확 턴 수 | axis3:66 = ❓미검증 | 03 §3 "(confidence: medium — 정확 턴 수치 ❓ 1차 미노출)" 병기 | ✅ 한정 보존 |
| 5 | bm25 ranking·이중테이블 결합 로직 | axis3:126·241 = low ❓ | 03 §4 "❓ bm25 ranking·이중 테이블 결합 로직은 doc 미노출(low)" 병기 | ✅ 한정 보존 |
| 6 | cron recursion 차단(Hermes 보안 측) | axis4:111 = "1차 미확인" | 07 §2·잔존표 "1차 미확인(§3 잔존표 ❓)" / "low ❓" 병기 | ✅ 한정 보존 |
| 7 | Honcho "theory of mind" 라벨 | axis3:242 = ToM 라벨 medium/약함 | 00 C5·06 §4 "ToM 라벨은 medium" 병기; 03 §5 는 "dialectic" 로만 기술(ToM 단정 회피) | ✅ 한정 보존 |
| 8 | "most used on OpenRouter" | axis2:141 = 2차 인용/1차 직접확인 실패 | 00 L19·06 §4 "NVIDIA 2차 인용 … OpenRouter 직접 확인 실패" 병기 | ✅ 한정 보존 |

## 종합 verdict

- **🔴 (날조·수치 불일치): 0건.** 점검한 ~35 material claim 전부 카드와 verbatim 일치 — 모델명/버전/CVE·CVSS/GHSA/날짜/스키마/메커니즘 이름에 fabrication·mismatch 없음.
- **🟡 (한정/근거): 1건 실질.**
  - auto-memory "14 cwd / 58 파일" = cards 미수록(Hermes 외부조사 카드 범위 밖, 우리 세팅 live 값). 보고서가 "live 확인·digest drift" 로 출처를 정직 표기해 날조 아니나, fact-check 상 카드-backed 아님 → 🟡. live `projects/*/memory/` 재집계 권고.
- **한정 보존 우수**: 카드가 ❓미검증/medium/low/SEO-only 로 표기한 8개 항목(8worker·BFCL·per-turn review 위치·nudge_interval·bm25·cron recursion·ToM·OpenRouter) 모두 보고서가 동일 한정을 병기 — 단정 누락 없음. 특히 마케팅 3종(40%·140k·most used)은 결론·이식 근거에서 정확히 배제됨.
- **카드 부재 고지**: 본 프로젝트는 `analysis_project/paper/` 부재(외부 기술 벤치마킹) — 정상. fact-check 는 cards + 보고서 verbatim 대조에 한정했고 web 재검증은 claim-verify(adversarial) 트랙 소관.
