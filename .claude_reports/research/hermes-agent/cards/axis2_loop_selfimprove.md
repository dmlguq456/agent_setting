# 축 2: Loop engineering / Self-improvement 메커니즘 — Hermes Agent (Nous Research)

> 조사일 2026-06-14. 1차 소스 우선 (github.com/NousResearch, hermes-agent.nousresearch.com/docs).
> 각 발견 = claim → 근거 URL → confidence. 미검증은 "❓미검증" 명시.
> **주의**: 검색 노출되는 hermes-ai.net·hermes-agent.org·hermes-agent.ai·tokenmix.ai·ofox.ai·chatforest.com 등은 SEO/affiliate 저신뢰 도메인 — 단독 근거로 쓰지 않음. 공식 = `hermes-agent.nousresearch.com`.

---

## 1. Learning loop 실제 메커니즘 (작업 → 포착 → 저장 → 로드 → 개선)

### 1.1 Skill = "procedural memory" 의 저장 단위 (포맷·위치 확정)
- **claim**: Skill 은 폴더 단위로 저장되며 폴더당 `SKILL.md` (markdown + YAML frontmatter) 가 required, 부속으로 `references/`·`templates/`·`scripts/`·`assets/`. 저장 위치는 `~/.hermes/skills/` ("the primary directory and source of truth"), `category/skill-name/` 계층.
  - frontmatter 필드: `name`, `description`, `version`, `platforms`, `metadata.hermes.tags`, `metadata.hermes.related_skills`, `category`.
  - 근거: `hermes-agent.nousresearch.com/docs/user-guide/features/skills`, 실제 예시 `github.com/NousResearch/hermes-agent/tree/main/skills/dogfood/SKILL.md` (frontmatter verbatim 확인: `name: dogfood / description / version: 1.0.0 / platforms: [linux,macos,windows] / metadata.hermes.tags / related_skills`)
  - **confidence: high** (공식 docs + repo 실파일 교차 확인)
- **참고**: agentskills.io open standard 호환 (README). 즉 skill 포맷은 Hermes 독자 X, 외부 표준 준수.

### 1.2 Skill 생성 트리거 (무엇이 트리거인가 — 핵심 질문)
- **claim**: 자율 skill 생성은 다음 조건에서 작동 (성공·실패·피드백 모두 포함):
  1. "After completing a complex task (5+ tool calls) successfully" — **작업 완료 + 복잡도 임계(5+ tool calls)**
  2. "When it hit errors or dead ends and found the working path" — **실패→복구 경로 발견**
  3. "When the user corrected its approach" — **사용자 피드백/교정**
  4. "When it discovered a non-trivial workflow" — **비자명 workflow 발견**
  - 근거: `docs/user-guide/features/skills`
  - **confidence: high**
- **트리거 실행 메커니즘**: "background self-improvement review" 가 **매 turn 후** 돈다 (configurable). 이 review 가 비자명 workflow 를 판단해 자동 저장.
  - 근거: `docs/user-guide/features/skills`
  - **confidence: medium** (developer-guide/architecture 페이지에서는 이 review 가 별도로 명시되지 않음 — skills 페이지 진술 기준. ❓architecture 페이지 미수록으로 코드 레벨 위치는 확정 못함)

### 1.3 Skill 자기개선 — 누가 편집하나
- **claim**: LLM(에이전트) 자신이 `skill_manage` tool 로 직접 편집. 액션: `create`(신규)·`patch`(token-efficient 타깃 수정)·`edit`(대규모 구조 재작성)·`delete`·`write_file`·`remove_file`.
  - 근거: `docs/user-guide/features/skills`
  - **confidence: high**

### 1.4 다음 실행에 로드 — progressive disclosure (3-level)
- **claim**: context 로딩은 3단계 점진 공개로 token 절약:
  - Level 0 `skills_list()` → `[{name,description,category}]` (~3k tokens)
  - Level 1 `skill_view(name)` → full content + metadata
  - Level 2 `skill_view(name, path)` → 특정 reference 파일
  - 실제 필요할 때만 full content 로드. invocation 은 slash command (`/skill-name`) 로 자동 노출.
  - 근거: `docs/user-guide/features/skills`
  - **confidence: high**
  - ❓미검증: 주어진 대화에서 "어떤 skill 을 initial system prompt 에 자동 선택해 넣는가"의 selection 로직은 docs 에 명시 안 됨.

### 1.5 Memory loop (skill 과 별개의 사실 축적)
- **claim**: Skill(절차) 과 별개로 사실 memory 가 두 파일에 축적: `~/.hermes/memories/MEMORY.md` (에이전트 자기 노트, ~2,200 chars), `USER.md` (사용자 프로필, ~1,375 chars). 세션 시작 시 system prompt 에 **frozen snapshot** 으로 주입 (prefix caching 보존) — 세션 중 변경은 디스크엔 즉시, prompt 엔 다음 세션부터 반영.
  - 추가: FTS5 full-text search (SQLite `~/.hermes/state.db`) 로 과거 대화 무제한 검색 — "no LLM summarization, no truncation" (※ README 의 "FTS5 + LLM summarization" 표현과 docs 의 "no LLM summarization" 사이 표현 차이 존재; docs 가 더 구체적이라 docs 우선).
  - 근거: `docs/user-guide/features/memory`, README L18·L25
  - **confidence: high** (memory loop), **medium** (FTS5 LLM summarization 여부 — 소스 간 표현 불일치)
- "periodic nudges"·Honcho dialectic user modeling: README L18·L25 에 언급되나 memory docs 페이지엔 미상술. **confidence: low** (Honcho 통합은 README 광고 문구 수준, 코드/docs 상술 ❓미검증)

---

## 2. Skill 자동 생성·자기개선 — Curator (품질 판단·충돌·deprecate)

### 2.1 Curator 정체
- **claim**: Curator = "agent-created skill 에 대한 background maintenance pass" (housekeeping). 기능:
  - usage metric 추적 (views, uses, patches)
  - lifecycle 전이 관리: `active → stale → archived`
  - overlapping skill **consolidation** 제안 + drift 식별
  - 미사용 bundled built-in skill archiving (옵션)
  - 근거: `docs/user-guide/features/curator`
  - **confidence: high**

### 2.2 품질 판단 — 누가/어떻게
- **claim**: Curator 는 **수치 점수(grade)를 매기지 않음**. 대신 LLM review phase 가 skill 을 `skill_view` 로 읽고 per-skill 로 keep / patch(`skill_manage`) / consolidate / archive 를 **정성 판단**. 실행은 hybrid — deterministic auto-transition + LLM review. LLM review 는 "background fork of `AIAgent`" 를 single aux-model pass, `max_iterations=8` 로 spawn.
  - 근거: `docs/user-guide/features/curator`
  - **confidence: high**

### 2.3 Conflict / duplication / deprecate 처리
- **claim**:
  - **중복/충돌**: 같은 skill name 이 local·external 양쪽에 있으면 local 우선. Consolidation 은 skill 을 full package 로 취급 (references/templates/scripts/assets 동반 시 standalone 유지 or re-home+path rewrite or 통째 archive).
  - **bundled 업데이트 충돌**: `.bundled_manifest` (skill name → content hash) 추적. sync 시 unchanged 만 upstream 수용, **user-modified 는 "skipped forever" (사용자 편집 보존)**. `hermes skills reset <name>` 으로 manifest 클리어, `--restore` 로 bundled 재복사.
  - **deprecate/stale 임계 (deterministic)**: 30일 미사용 → `stale`, 90일 미사용 → `~/.hermes/skills/.archive/` 로 archive. 능동적 자동 삭제 시스템은 없음 (삭제는 `skill_manage delete` 수동).
  - 근거: `docs/user-guide/features/skills`, `docs/user-guide/features/curator`
  - **confidence: high**

### 2.4 Curator 실행 트리거 (cron 아님 — 주의)
- **claim**: Curator 는 **cron daemon 이 아니라 inactivity check 로 트리거**. 두 조건 동시 충족 시 실행: (1) 마지막 실행 후 ≥ `interval_hours` (default 7일) 경과 (2) agent idle ≥ `min_idle_hours` (default 2시간).
  - 근거: `docs/user-guide/features/curator`
  - **confidence: high**
  - → 즉 "skill 자기정비"는 cron 으로 도는 게 아님. cron(§3) 과 curator 는 별개 시스템.

---

## 3. Scheduled automation (cron / periodic / background loop)

- **claim**: built-in cron scheduler 가 gateway daemon 에 내장. 정의 형식 다중 지원:
  - 자연어 ("Every morning at 9am, check Hacker News...")
  - cron expression (`0 9 * * *`)
  - relative delay (`30m`, `every 2h`)
  - ISO timestamp (one-time)
- **실행 모델**: gateway daemon 이 **60초마다 tick**, due job 을 **isolated fresh agent session** 에서 실행. 흐름: `~/.hermes/cron/jobs.json` 로드 → due 체크 → fresh session 시작 → prompt 완료까지 실행 → 결과를 target(Telegram 등)에 delivery.
- **runaway 방지**: "Cron-run sessions cannot recursively create more cron jobs" — cron 실행 내부에선 cron 관리 tool 비활성.
- **skill 연동**: job 에 0~N개 skill attach (`skills` param), fresh session 에 주입.
  - 근거: `docs/user-guide/features/cron`, README L26
  - **confidence: high**
- **중요 구분**: cron 으로 도는 것은 **사용자 정의 prompt job** 뿐. cron docs 에 skill curation·consolidation·self-improvement 가 cron 으로 돈다는 언급 **없음**. self-improvement loop 와 cron 은 분리된 시스템 (self-improvement = per-turn review + inactivity-triggered curator).
  - **confidence: high**

---

## 4. Atropos RL 프레임워크 — weight 학습 vs skill/메모리 축적 (핵심 분리)

### 4.1 Atropos 정체 (1차 소스 확정)
- **claim**: Atropos = "an environment microservice framework for async RL with LLMs" — LLM trajectory 를 다양한 environment 에서 수집·평가하는 **RL environments framework**. environment(service) + trajectory API(trainer 가 batch pull) 로 구성.
  - 근거: `github.com/NousResearch/atropos` README (raw 확인)
  - **confidence: high**

### 4.2 Atropos 는 모델 weight 를 직접 학습하지 않는다
- **claim**: Atropos 는 **trainer 와 inference engine 을 "포함하지 않음(does not include)"**. weight 학습은 외부 trainer 가 담당 — Axolotl plugin, Tinker integration, 그리고 reference 용 example trainer. Atropos 자체는 rollout/trajectory 수집·평가 인프라(gym).
  - 근거: `atropos` README (raw): "does not include" trainer/inference; Axolotl·Tinker 통합 명시
  - **confidence: high**

### 4.3 ★ 핵심 판정 — runtime self-improvement vs Atropos training (흐리지 않고 분리)

> **(a) Hermes Agent 의 런타임 self-improvement 는 모델 weight 학습이 아니다.**
> 런타임 자기개선 = **skill/메모리 축적** (skill_manage 로 SKILL.md 작성/수정 + MEMORY.md/USER.md). 기반 모델 weight 는 고정 — 에이전트는 절차(skill)와 사실(memory)을 디스크에 누적할 뿐 retrain 하지 않는다.
> 근거: NVIDIA blog ("writes and refines its own skills... saves its learnings as a skill"), docs (skill_manage, curator), architecture (`AIAgent` 는 runtime orchestration). **confidence: high**
>
> **(b) Atropos 는 training-time 프레임워크다 — 에이전트 운영 중 돌지 않는다.**
> Atropos README·Hermes docs·architecture 어디에도 Atropos 가 Hermes runtime 에 통합돼 inference 중 돈다는 언급 **없음**. Atropos README 엔 Hermes 언급 자체가 없음. Hermes 가 만드는 trajectory 는 "ShareGPT-format trajectories... for training data generation" / "trajectory compression for training the next generation of tool-calling models" 즉 **offline/post-hoc 학습 데이터 생성** — Hermes runtime 과 별도 subsystem(`batch_runner.py`).
> 근거: `atropos` README, hermes `docs/developer-guide/architecture`, README L29. **confidence: high**
>
> **정리**: Hermes 가 운영 중 쌓은 trajectory 가 (별도 training-time 에) Atropos environment 를 거쳐 외부 trainer 로 *차세대 tool-calling 모델*을 학습시키는 **데이터 공급원**이 될 수 있는 관계. 하지만 "Hermes 가 돌면서 Atropos 로 자기 weight 를 강화한다"는 것은 **아님**. 두 self-improvement 는 층위가 다르다: runtime = skill/memory(무게중심), training-time = Atropos RL(별개 파이프라인, 모델 제작 단계).

### 4.4 tool-calling accuracy·long-range planning 주장의 근거
- **claim**: Atropos 의 tool-calling environment 가 Berkeley Function Calling Benchmark 에서 — parallel tasks 10%→46% (4.6x), simple tasks 21%→51.75% (2.5x) 개선 시연.
  - 근거: `atropos` README (raw 확인)
  - **confidence: high** (수치는 Atropos 자체 보고 — 독립 재현 ❓미검증)
- **주의**: 이 개선은 **Atropos 로 학습한 모델**의 벤치마크 수치 (training-time 산물)이지, "Hermes 에이전트가 운영하며 실시간으로 tool-calling 이 좋아진다"는 근거가 아님. long-range planning 강화에 대한 정량 근거는 1차 소스에서 **확인 못함 ❓미검증**.

---

## 마케팅 주장 — 1차 출처 추적

| 주장 | 1차 출처 URL (있으면) | 출처 신뢰도 | 검증 가능 여부 |
|---|---|---|---|
| "40% faster with self-created skills" (20+ skill 보유 시 유사 작업 ~40% 빠름, domain-specific·비전이) | **1차 출처 없음** — Nous 공식 README/docs·NVIDIA blog 어디에도 "40%" 없음. 출현처는 theagenticreview.substack 등 2차/SEO | 저신뢰 (출처 미확인) | ❓미검증 — Nous 공식 정량 근거 부재. claim-verify 대상. |
| "140k GitHub stars in 3 months" (2/25 launch → ~90일, 140,000+ stars, ~1,000 contributors) | NVIDIA blog `blogs.nvidia.com/blog/rtx-ai-garage-hermes-agent-dgx-spark/` ("crossed 140,000 GitHub stars in under three months"). 단 NVIDIA 는 GitHub 통계를 독립 출처로 인용한 것이지 1차 측정 아님. (※ README 의 star badge·각종 2차 글은 95.6K~193k 등 시점별 상이) | 중간 (NVIDIA 2차, GitHub 원천 인용) | 검증 가능 — GitHub star 수는 시점 명시하면 측정 가능. 단 "3개월" framing·정확 수치는 시점 의존. |
| "most used agent on OpenRouter" (5/10 OpenClaw 추월, 224B vs 186B tokens/day) | NVIDIA blog (동상, "most used agent in the world according to OpenRouter", OpenRouter 데이터 인용); techtimes 2차. **OpenRouter rankings 페이지 직접 확인 시 데이터 truncate 로 Hermes 확인 실패** | 중간 (NVIDIA 2차) / 1차(OpenRouter) 직접 확인 실패 | 부분 검증 가능 — OpenRouter rankings 가 1차이나 직접 fetch 에서 미확인. 시점 의존. claim-verify 가 OpenRouter 직접 확인 권장. |

> 종합: 마케팅 주장 3개 모두 **Nous Research 1차 직접 진술 아님**. "140k stars"·"most used"는 NVIDIA(신뢰할 2차)가 GitHub/OpenRouter 원천을 인용한 것, "40% faster"는 1차 출처 자체가 없고 SEO/2차 블로그에서만 출현 — 가장 약함.

---

## 출처 ledger

| # | URL | 유형 | 신뢰도 | 사용처 |
|---|---|---|---|---|
| 1 | github.com/NousResearch/hermes-agent (README raw) | 1차 (공식 repo) | high | §1.1, 1.5, §3, §4.3 (trajectory framing) |
| 2 | hermes-agent.nousresearch.com/docs/user-guide/features/skills | 1차 (공식 docs) | high | §1.1~1.4, §2.3 |
| 3 | hermes-agent.nousresearch.com/docs/user-guide/features/curator | 1차 (공식 docs) | high | §2.1~2.4 |
| 4 | hermes-agent.nousresearch.com/docs/user-guide/features/memory | 1차 (공식 docs) | high | §1.5 |
| 5 | hermes-agent.nousresearch.com/docs/user-guide/features/cron | 1차 (공식 docs) | high | §3 |
| 6 | hermes-agent.nousresearch.com/docs/developer-guide/architecture | 1차 (공식 docs) | high | §1.2(부분), §4.3(b) |
| 7 | github.com/NousResearch/hermes-agent/tree/main/skills/dogfood/SKILL.md | 1차 (실 skill 파일) | high | §1.1 (frontmatter 실증) |
| 8 | github.com/NousResearch/atropos (README raw) | 1차 (공식 repo) | high | §4.1~4.4 |
| 9 | github.com/NousResearch/hermes-agent-self-evolution | 1차 (공식 repo) | high | (보조) DSPy+GEPA 진화 = prompt/skill/code 최적화, weight X, inference-time |
| 10 | blogs.nvidia.com/blog/rtx-ai-garage-hermes-agent-dgx-spark/ | 2차 (신뢰) | medium-high | 마케팅 표 (140k stars, most used), §4.3(a) skill 축적 framing |
| 11 | openrouter.ai/rankings | 1차 | (확인 실패) | 마케팅 표 — 직접 fetch 시 데이터 truncate |
| 12 | theagenticreview.substack.com / techtimes / tokenmix / ofox / chatforest | 2차/SEO | low | "40% faster" 출현처 (단독 근거 불가) |

### 보조 발견 — hermes-agent-self-evolution (별도 repo)
- DSPy + GEPA(Genetic Evolution of Prompt Architectures)로 skill·tool description·system prompt·code 를 **진화 최적화** ("mutating text, evaluating results, selecting best variants" via API calls, **not GPU training**). prompt/skill/code 최적화이지 weight 학습 아님, inference/runtime 측. Phase 1(skill files) 구현, 2~4(tool desc/prompt/code) 계획. Atropos 언급 없음.
- → §4.3 판정 보강: Hermes 생태계의 self-improvement 는 (a) runtime skill/memory 축적 (b) self-evolution repo 의 텍스트 진화(GEPA) 둘 다 **weight 비학습**. weight 학습은 오직 Atropos(+외부 trainer)의 training-time 경로뿐.
