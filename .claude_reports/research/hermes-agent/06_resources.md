# 06 — 1차 소스 · 검증 상태

> cards 3종의 출처 ledger 통합 + 검증 탈락/미확인 투명 기록. adversarial deliverable.

---

## 1. 1차 소스 (high 신뢰)

| 소스 | URL | 분류 | 무엇을 근거했나 |
|---|---|---|---|
| Hermes repo | github.com/NousResearch/hermes-agent | 1차 | repo·README·MIT·언어통계·v0.16.0·top-level 디렉토리·40+ tools |
| Hermes docs | hermes-agent.nousresearch.com/docs/ | 1차 | docs TOC·60+ tools·20+ platforms·learning loop |
| architecture doc | …/docs/developer-guide/architecture | 1차 | AIAgent·Prompt Builder·Provider Resolution·Tool Registry·70+ tools ~28 toolsets·20 adapter·auto-discovery·data flow |
| skills doc | …/docs/user-guide/features/skills | 1차 | skill 포맷·생성 트리거·skill_manage·progressive disclosure·stale 30d/90d |
| curator doc | …/docs/user-guide/features/curator | 1차 | Curator lifecycle·inactivity(7d+2h)·LLM 정성 review |
| memory doc | …/docs/user-guide/features/memory | 1차 | MEMORY/USER.md char limit·write_approval·frozen snapshot·중복거부 |
| memory-providers doc | …/docs/user-guide/features/memory-providers | 1차 | 9 provider·Holographic FTS5 |
| honcho doc | …/docs/user-guide/features/honcho | 1차 | dialectic·5 tool·built-in 비교표 |
| session-storage doc | …/docs/developer-guide/session-storage | 1차 | state.db DDL·FTS5 trigger·WAL·schema v11 |
| cron doc | …/docs/user-guide/features/cron | 1차 | 60s tick·fresh session·재귀차단 |
| `hermes_state.py` source | github.com/NousResearch/hermes-agent/blob/main/hermes_state.py | 1차 | trigram DDL·state_meta·schema_version |
| `skills/dogfood/SKILL.md` | github.com/NousResearch/hermes-agent/tree/main/skills/dogfood | 1차 | skill frontmatter verbatim 실증 |
| **Atropos repo** | github.com/NousResearch/atropos | 1차 | RL environments framework·trainer 미포함·BFCL 수치 |
| hermes-agent-self-evolution | github.com/NousResearch/hermes-agent-self-evolution | 1차 | DSPy+GEPA 텍스트 진화(weight X, inference-time) |
| **Honcho repo** | github.com/plastic-labs/honcho | 1차 | Honcho 정체·FastAPI·peer pair representation |

## 2. 2차 소스 (medium — 1차 보완·교차)

| 소스 | URL | 신뢰도 | 비고 |
|---|---|---|---|
| hermes-agent-docs mirror | github.com/mudrii/hermes-agent-docs | medium | ThreadPoolExecutor 8 worker·22 platforms·166 skills 교차 |
| NVIDIA blog | blogs.nvidia.com/blog/rtx-ai-garage-hermes-agent-dgx-spark/ | medium-high | 140k stars·most used·skill 축적 framing (단 GitHub/OpenRouter 인용, Nous 1차 아님) |
| Medium (Timi) | medium.com/@xpf6677/...-a84d2a9d5d01 | medium | 턴 카운터 nudge 메커니즘(1차 미노출 보완) |

## 3. 저신뢰 (단독 근거 미사용)

hermes-ai.net · hermes-agent.org · hermes-agent.ai · tokenmix.ai · ofox.ai · chatforest.com · theagenticreview.substack · techtimes — SEO/affiliate. 교차참고만.

---

## 4. ★ 검증 탈락 / 미확인 (refuted / unverified)

| 항목 | 상태 | 무엇을·왜 |
|---|---|---|
| **"40% faster with self-created skills"** | ❌ 가장 약함 (1차 출처 부재) | Nous README/docs·NVIDIA blog 어디에도 "40%" 없음. SEO/2차 블로그(theagenticreview 등)에서만 출현. claim-verify 대상. **결론·이식 근거로 쓰면 안 됨.** |
| **"140k GitHub stars in 3 months"** | ⚠️ 2차 인용 (Nous 1차 직접 진술 아님) | NVIDIA blog 가 GitHub 통계를 인용 — NVIDIA 의 1차 측정 아님. README badge·2차 글은 95.6K~193k 등 시점별 상이. star 수는 시점 명시하면 측정가능하나 "3개월" framing 은 시점 의존. |
| **"most used agent on OpenRouter"** | ⚠️ 2차 인용 / 1차 직접확인 실패 | NVIDIA blog(224B vs 186B tokens/day, OpenRouter 인용). OpenRouter rankings 페이지 직접 fetch 시 데이터 truncate 로 Hermes 확인 실패. claim-verify 가 OpenRouter 직접 확인 권장. |
| **"47 built-in tools"** | ⚠️ 버전 drift | 어느 tag 에도 정확 매칭 안 됨. 1차끼리 40/60/70 흔들림. 현재 best estimate = 70+(architecture doc). 확정하려면 특정 tag `tools/registry.py` 직독. |
| **Atropos = 런타임 self-improvement** | ❌ refuted | Atropos = training-time RL environments framework. runtime 통합·inference 중 작동 언급 어디에도 없음. (자세히 axis2 §4) |
| **Honcho = Hermes 내장** | ❌ 정정 | 외부 Plastic Labs FastAPI 서비스(optional provider). |
| **Honcho "theory of mind"** | ⚠️ 라벨 약함 | Hermes 는 "dialectic" 기술, Honcho README 의 ToM 명시 약함. |
| **DGX Spark / RTX 전용 path** | ❓ 미확인 | NVIDIA NIM 지원은 확인, 전용 최적화 1차 미확인(low). |
| **ThreadPoolExecutor 8-worker** | ❓ 미확인 | mirror 만, 공식 doc 직접 인용 미확보(medium). |
| **`nudge_interval` 정확 턴 수** | ❓ 미확인 | 1차 doc 미노출. |
| **`session_search` bm25 ranking·이중테이블 결합** | ❓ 미확인 | `hermes_state.py` 후반 cut off(low). |
| **BFCL 4.6x/2.5x 수치** | ⚠️ self-reported | Atropos 자체 보고, 독립 재현 미확인. 또한 *Atropos 학습 모델* 수치이지 Hermes 런타임 개선 아님. |

---

## 5. 우리 세팅 근거 (이 deliverable 대조 대상)

| 소스 | 경로 | 근거한 것 |
|---|---|---|
| 라우팅 코어 | `~/.claude/CLAUDE.md` §0 | spec-first 게이트·소유스킬 수정·artifact-guard |
| 루프 카탈로그 | `~/.claude/loops/README.md` | L1–L4·oncall/note/drill/study·불변식 |
| 메모리 (live) | `~/.claude/projects/<cwd>/memory/` | **메모리 dir 15개 / MEMORY.md 인덱스 14개 / 메모리 .md 파일 58개** (`.claude` config repo cwd 만 빈 레이어, 실작업 cwd 엔 채워짐 — per-cwd. §03 §7 명시) |
| user_profile | `~/.claude/user_profile/0X_*.md` | 6종 cross-project 성향 |
| hooks | `~/.claude/hooks/` | artifact-guard·git-state-guard·spec-skill-gate 등 |

**Takeaway**: Hermes 의 *설계·메커니즘* 진술은 1차 doc·source 로 high 신뢰지만, *마케팅 성능 주장*("40% faster"·"140k stars"·"most used")은 전부 Nous 1차 직접 진술이 아니거나 출처 부재 — 본 벤치마킹의 결론과 이식 판단은 *메커니즘 근거*에만 의존하고 성능 수치는 배제했다.
