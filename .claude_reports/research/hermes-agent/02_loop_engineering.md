# 02 — Loop · Self-improvement 심층

> 근거: `cards/axis2_loop_selfimprove.md` (1차 = github.com/NousResearch + hermes-agent.nousresearch.com/docs + github.com/NousResearch/atropos). 이 보고서가 본 deliverable 의 무게중심.

---

## 0. 한눈 요약 — Hermes 의 self-improvement 는 *두 층*, weight 학습은 *별개*

Hermes 가 "self-improving" 인 이유는 **런타임에 에이전트가 자기 절차(skill)와 사실(memory)을 디스크에 누적·수정**하기 때문이다 (모델 weight 는 고정). 여기에 (a) 매 turn 후 background review (b) inactivity-triggered Curator (c) cron 스케줄 자동화 (d) 별도 self-evolution repo 의 GEPA 텍스트 진화가 얹힌다. **Atropos 는 이 런타임 loop 가 아니라 training-time RL environments framework — 모델 제작 단계의 별개 파이프라인**이다.

```
[런타임 self-improvement]                    [training-time, 별개]
  매 turn 후 review ──┐                        Hermes 가 쌓은
  skill_manage 자기편집 ─┼─► skill/memory 누적     trajectory(ShareGPT)
  Curator (inactivity) ─┘   (weight 고정)    ──► Atropos environments
                                              ──► 외부 trainer(Axolotl/Tinker)
                                              ──► 차세대 tool-calling 모델
```

---

## 1. Learning loop 메커니즘 (작업→포착→저장→로드→개선)

### 1.1 skill = procedural memory 의 저장 단위

**claim**: skill 은 폴더 단위, 폴더당 `SKILL.md`(markdown + YAML frontmatter) required, 부속 `references/`·`templates/`·`scripts/`·`assets/`. 위치 = `~/.hermes/skills/` ("primary directory and source of truth"), `category/skill-name/` 계층. (confidence: high — 공식 docs + repo 실파일 `skills/dogfood/SKILL.md` frontmatter verbatim 확인)
- frontmatter: `name`·`description`·`version`·`platforms`·`metadata.hermes.tags`·`metadata.hermes.related_skills`·`category`.
- **agentskills.io open standard 호환** — skill 포맷은 Hermes 독자 아님, 외부 표준 준수.

### 1.2 생성 트리거 (핵심 질문 — 무엇이 trigger 인가)

**claim**: 자율 skill 생성은 성공·실패·피드백 4 조건에서 작동. (confidence: high)

| # | 트리거 | 본질 |
|---|---|---|
| 1 | "After completing a complex task (5+ tool calls) successfully" | 작업 완료 + 복잡도 임계 |
| 2 | "When it hit errors or dead ends and found the working path" | 실패→복구 경로 발견 |
| 3 | "When the user corrected its approach" | 사용자 교정 |
| 4 | "When it discovered a non-trivial workflow" | 비자명 workflow 발견 |

**실행**: "background self-improvement review" 가 **매 turn 후** 돈다(configurable) — 이 review 가 비자명 workflow 를 판단해 자동 저장. (confidence: medium — skills 페이지 진술 기준, architecture 페이지엔 코드 레벨 위치 미수록 ❓)

### 1.3 누가 편집하나 — `skill_manage` self-edit

**claim**: LLM(에이전트) 자신이 `skill_manage` tool 로 직접 편집. 액션 = `create`(신규)·`patch`(token-efficient 타깃)·`edit`(대규모 재작성)·`delete`·`write_file`·`remove_file`. (confidence: high)

> 이것이 Hermes self-improvement 의 *심장*이자 우리와의 최대 메커니즘 차이 — **에이전트가 런타임에 자기 절차 문서를 고친다**. 우리에겐 이에 대응하는 자동 경로가 없다(drill→사용자 승인→수동 수정).

### 1.4 로드 — progressive disclosure (3-level)

**claim**: token 절약을 위한 3단계 점진 공개. (confidence: high)

| level | 호출 | 반환 |
|---|---|---|
| 0 | `skills_list()` | `[{name,description,category}]` (~3k tokens) |
| 1 | `skill_view(name)` | full content + metadata |
| 2 | `skill_view(name, path)` | 특정 reference 파일 |

invocation = slash command(`/skill-name`) 자동 노출. ❓ 어떤 skill 을 initial system prompt 에 자동 선택하는 selection 로직은 docs 미명시.

### 1.5 memory loop (skill 과 별개의 사실 축적)

§axis3 에서 상술 — 요지: `MEMORY.md`(~2,200 char) + `USER.md`(~1,375 char) frozen snapshot + FTS5 session archive. (confidence: high)

---

## 2. Curator — skill lifecycle 자동 정비

### 2.1 정체

**claim**: Curator = agent-created skill 에 대한 background maintenance pass(housekeeping). 기능 = usage metric(views/uses/patches) 추적 · lifecycle `active→stale→archived` 전이 · overlapping skill consolidation 제안 · 미사용 bundled skill archiving. (confidence: high)

### 2.2 품질 판단 — 점수 없는 정성 review

**claim**: Curator 는 **수치 grade 를 매기지 않음**. LLM review phase 가 `skill_view` 로 읽고 per-skill 로 keep / patch / consolidate / archive 를 *정성 판단*. 실행 = hybrid(deterministic auto-transition + LLM review). LLM review 는 "background fork of `AIAgent`" single aux-model pass, `max_iterations=8`. (confidence: high)

> **거버넌스 관점**: 품질 판단이 *LLM 정성 review 단독* — 적대 검증·교차 voter 없음. 우리 claim-verify(N-vote default-refute)와 대비되는 약점.

### 2.3 충돌·중복·deprecate

| 항목 | 처리 |
|---|---|
| 중복/충돌 | 같은 name 이 local·external 양쪽이면 local 우선. consolidation 은 full package(refs/templates/scripts/assets 동반) 단위 |
| bundled 업데이트 | `.bundled_manifest`(name→content hash) 추적, sync 시 unchanged 만 upstream 수용, **user-modified 는 "skipped forever"** (사용자 편집 보존). `hermes skills reset`/`--restore` |
| stale/archive (deterministic) | **30일 미사용 → stale, 90일 미사용 → `.archive/`**. 능동 자동삭제 없음(삭제는 수동 `skill_manage delete`) |

### 2.4 실행 트리거 — cron 아님

**claim**: Curator 는 cron daemon 이 아니라 **inactivity check** 로 트리거 — (1) 마지막 실행 후 ≥ `interval_hours`(default 7일) (2) agent idle ≥ `min_idle_hours`(default 2h) 동시 충족. 산출 = `~/.hermes/logs/curator/{run.json, REPORT.md}`. (confidence: high)

> 즉 skill 자기정비는 cron 으로 도는 게 아니다 — cron(§3)과 Curator 는 별개 시스템.

---

## 3. Cron — scheduled automation

**claim**: gateway daemon 내장 cron. 정의 = 자연어 / cron expr / relative delay / ISO timestamp. (confidence: high)
- **실행**: gateway 가 **60초 tick**, due job 을 **isolated fresh agent session** 에서 실행 → 결과를 target(Telegram 등) delivery.
- **runaway 방지**: "Cron-run sessions cannot recursively create more cron jobs" — cron 실행 내부에선 cron 관리 tool 비활성.
- **skill 연동**: job 에 0~N skill attach, fresh session 주입.

> **중요 구분**: cron 으로 도는 것은 *사용자 정의 prompt job* 뿐. self-improvement(per-turn review + Curator)는 cron 으로 돌지 않는다. (confidence: high)

---

## 4. Atropos — training-time RL (런타임 self-improvement 아님)

**claim**: Atropos = "environment microservice framework for async RL with LLMs" — LLM trajectory 를 environment 에서 수집·평가하는 RL **environments** framework. **trainer·inference engine 미포함** — weight 학습은 외부(Axolotl plugin·Tinker·example trainer). (confidence: high — atropos README raw)

### ★ 핵심 판정 (흐리지 않고 분리)

> **(a)** Hermes 런타임 self-improvement = skill/memory 축적, **weight 학습 아님**. 기반 모델 고정. (high)
> **(b)** Atropos = **training-time framework, 에이전트 운영 중 돌지 않음**. atropos README·Hermes docs·architecture 어디에도 Atropos 가 runtime 통합돼 inference 중 돈다는 언급 없음(atropos README 엔 Hermes 언급 자체 없음). Hermes trajectory 는 "ShareGPT-format ... for training data generation" = offline 학습 데이터 공급. (high)
> **정리**: Hermes 운영 trajectory 가 (별도 training 단계에) Atropos 거쳐 외부 trainer 로 *차세대 모델*을 학습시키는 데이터 공급원이 될 수 있는 관계. "Hermes 가 돌며 자기 weight 강화"는 **아님**.

**벤치마크 (Atropos 자체 보고)**: tool-calling environment 가 Berkeley Function Calling Benchmark 에서 parallel 10%→46%(4.6x), simple 21%→51.75%(2.5x). (confidence: high on 수치 보고; 독립 재현 ❓미검증) — *이는 Atropos 로 학습한 모델*의 수치이지 "Hermes 가 운영하며 실시간으로 좋아진다"는 근거 아님.

**보조**: 별도 repo `hermes-agent-self-evolution` = DSPy + GEPA(prompt/skill/code 진화 최적화, "mutating text ... via API calls, not GPU training") — 역시 weight 비학습·inference-time. → Hermes 생태계 self-improvement 는 (a) runtime skill/memory (b) GEPA 텍스트 진화 둘 다 weight 비학습. weight 학습은 오직 Atropos(+외부 trainer) training-time 경로뿐.

---

## 5. ★ 우리 loops/ (L1–L4) 와 1:1 대조

| Hermes 메커니즘 | 우리 대응물 | 누가 앞섰나 | 근거 |
|---|---|---|---|
| 매 turn 후 background self-improvement review | (직접 대응 없음) — 가장 가까운 건 post-it nudge(세션 wind-down 시 제안), QA 라운드(L2) | **Hermes 앞섬** (자동 per-turn) | axis2 §1.2 vs CLAUDE.md §2 post-it |
| `skill_manage` 런타임 self-edit (에이전트가 자기 절차 수정) | **drill(L4) → 사용자 승인 → 수동 지침 수정** | trade-off — Hermes=속도, 우리=거버넌스 | axis2 §1.3 vs loops/README L4 |
| Curator: inactivity check, active→stale(30d)→archived(90d) 자동 | post-it sweep (수동/세미자동, "확실한 것만" 자동 prune), 시간기반 lifecycle **없음** | **Hermes 앞섬** (시간기반 자동 lifecycle) | axis2 §2 vs CLAUDE.md post-it 정책 |
| Curator 품질 판단 = LLM 정성 review 단독(점수 없음) | **claim-verify(N-vote default-refute) · fact-check(verbatim)** 적대 검증층 | **우리 앞섬** (적대 검증 vs 정성 단독) | axis2 §2.2 vs agents 연구팀 mode |
| cron: 60s tick, isolated fresh session, 재귀 차단 | **oncall(cron 05:37) · note(cron 05:03) · study(일요일 06:17)** — 모두 세션 밖 cron+headless, idempotent | **동등** (우리도 fresh-session cron 보유) | axis2 §3 vs loops/README L3 |
| cron job 에 skill attach | autopilot-* 파이프 호출(루프는 직접 일 안 함, 파이프 호출) | 동등 (다른 형태) | loops/README "autopilot=동사, loop=부사" |
| (없음) 시스템이 *자기 지침을 시험* | **drill: fixture 가상상황 headless 시험·채점 = 행동 회귀테스트** | **우리 앞섬** (Hermes 에 메타-시험 층 없음) | loops/README L4 vs axis2 전반 |
| (없음) 외부 동향 × 자기 세팅 대조 | **study: agent engineering 신간·Claude Code 변경 조사 → 세팅 대조 → 개선 제안서** | **우리 앞섬** (Hermes 에 외부 대조 층 없음) | loops/README L4 vs axis2 전반 |
| Atropos (training-time RL, 별개) | (없음 — 우리는 모델 제작자 아님, 소비만) | N/A (쓰임 다름) | axis2 §4 |

**Takeaway**: Hermes 가 앞선 곳은 **"자동·런타임" 자기개선의 속도**(per-turn review·skill self-edit·시간기반 Curator), 우리가 앞선 곳은 **"검증·메타" 거버넌스의 신뢰성**(적대 N-vote·drill 행동 회귀·study 외부 대조). 둘은 같은 loop engineering 의 *서로 다른 박자* — Hermes 는 초·분 박자(L1/L2 자율)가 강하고, 우리는 주 박자(L4 메타)가 강하다. 이식의 정답은 우리의 L3/L4 루프에 Hermes 식 *자동 초안*을 붙이되 *결정 게이트는 사용자에 남기는* 것.
