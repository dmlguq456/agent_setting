# 04 — 벤치마킹 갭 분석 (Hermes Agent ↔ 우리 세팅)

> 본 deliverable 의 결론 보고서. 3축(아키텍처·loop·memory) 종합 대조. 근거 = cards 3종 + 우리 세팅 실파일. confidence 는 cards 한정 유지.

---

## 1. 3축 종합 대조 표

| 축 | Hermes 설계 | 우리 설계 | 판정 | 근거 1줄 |
|---|---|---|---|---|
| **실행 모델** | persistent daemon(gateway long-running) + multi-channel | 세션 단위 + 세션 밖 cron(oncall/note/study) | Hermes 앞섬 (쓰임 다름) | axis1 §3 / loops |
| **entry 구조** | hub-and-spoke (1 core·4 entry) | 1 라우터(WORKFLOW)·N autopilot entry | 동등 | axis1 §2 |
| **LLM backend** | provider-agnostic 18+ | Claude Code (벤더 고정, 소비) | Hermes 앞섬 (유연성) | axis1 §2 |
| **tool 확장** | import-time auto-discovery + 3중 plugin | skills/ 자동 로드 + agents/ | 동등 | axis1 §4 |
| **multi-channel gateway** | 20+ 채널 push | 없음 (notes/ 파일 pull) | Hermes 앞섬 | axis1 §6 |
| **런타임 절차 자기개선** | `skill_manage` self-edit (에이전트가 직접) | drill→사용자 승인→수동 수정 | trade-off | axis2 §1.3 / loops L4 |
| **per-turn self-review** | 매 turn 후 background review | 없음(가장 가까운 건 post-it nudge) | Hermes 앞섬 (메커니즘 위치 medium) | axis2 §1.2 |
| **skill lifecycle** | Curator active→stale(30d)→archived(90d) 자동 | post-it sweep 세미자동, 시간기반 없음 | Hermes 앞섬 | axis2 §2 |
| **자기개선 품질 판단** | LLM 정성 review 단독 | claim-verify N-vote + fact-check 적대층 | **우리 앞섬** | axis2 §2.2 / agents |
| **메타-시험 (자기 지침 검증)** | 없음 | drill 행동 회귀테스트 | **우리 앞섬** | loops L4 |
| **외부 동향 대조** | 없음 | study (외부×세팅 → 제안) | **우리 앞섬** | loops L4 |
| **scheduled automation** | cron 60s tick, fresh session, 재귀차단 | oncall/note/study cron+headless, idempotent | 동등 | axis2 §3 / loops L3 |
| **memory 세션주입** | MEMORY/USER.md frozen snapshot | auto-memory 세션 시작 자동 주입 | 동등 | axis3 §1 |
| **cross-session recall** | FTS5 `session_search` 전 세션 자동 full-text | 세션주입+수동 recall, 인덱스 얇음 | **Hermes 앞섬 (큰 갭)** | axis3 §4 |
| **memory write 게이트** | write_approval + promote/skip 휴리스틱 | 가이드 서술, 코드 게이트 없음 | Hermes 앞섬 | axis3 §2 |
| **user modeling** | Honcho 자동 dialectic (외부) | user_profile 수동(analyze-user) | trade-off | axis3 §5 |
| **memory 용량 규율** | char limit + consolidation(error on full) | 자유 누적 | Hermes 앞섬 | axis3 §6 |
| **행동양식 관리** | memory 에 혼재 가능 | 원칙 문서 단일 출처 분리 | **우리 앞섬** | CLAUDE.md 정책 |
| **산출물 거버넌스** | 없음 | 하드 순서 게이트 + artifact-guard hook | **우리 앞섬** | CLAUDE.md §0 |
| **버전 트래킹** | skill version frontmatter | 산출물별 소유스킬 수정 + `_internal/versions/` | **우리 앞섬** | CLAUDE.md |
| **멀티에이전트 분업** | delegate/mixture_of_agents tool | 7팀(개발·기획·디자인·연구·자료·편집·품질) maker/verifier | 동등~우리 앞섬 | axis1 §3 / agents |
| **weight 학습 경로** | Atropos (training-time, 별개) | 없음 (소비자) | N/A | axis2 §4 |
| **보안 거버넌스** | 7-layer in-process defense(allowlist·approval·container·credential filtering·context scan·session isolation) — 단 제작자 본인이 "containment 아님" 명시 | hooks(git-state-guard·artifact-guard) + security-review agent(품질관리팀) + 적대 검증(N-vote) | **위협 모델이 다름** | axis4 §2-3 / 07_security |

**위협 모델 차이 (보안 행 판정):** Hermes 는 *다채널 자율 실행* 노출이 커 attack surface 가 넓고(임의 shell·gateway·supply chain·prompt injection 잔존), 우리는 *세션 내 도구* 모델이라 실행 노출은 작은 대신 *산출물 거버넌스*(생성 순서 hook·소유스킬 수정·버전 트래킹)가 강하다 — 같은 축의 비교가 아니라 다른 위협면을 방어한다. **단, 우리가 향후 *자율 에이전트 플러그인/설치 프로그램* 으로 확장하면 Hermes 급 attack surface 가 새로 생기므로 `07_security.md` 의 보안 체크리스트(OWASP ASI01–10 + LLM Top10)가 그 PRD 의 필수 입력이 된다.**

**Takeaway**: Hermes 가 앞선 12개는 거의 전부 *"자동·런타임·메모리 접근성"* 클러스터, 우리가 앞선 8개는 전부 *"거버넌스·검증·메타·관심사 분리"* 클러스터 — 두 시스템은 같은 agent engineering 의 **상보적 절반**이다. 갭이 큰 단일 항목은 **FTS5 cross-session recall** 하나.

---

## 2. Hermes 가 앞선 점 (우리가 배울 것)

### (a) FTS5 cross-session recall = *자동* 검색, 우리는 *주입+수동* + 얇은 인덱스
- Hermes: `session_search` 가 전 세션을 FTS5(unicode61 + trigram CJK)로 ~20ms 자동 full-text 검색. 에이전트가 "지난주 X 논의했나?"를 능동 recall. (confidence: high)
- 우리: auto-memory 는 세션 시작 frozen 주입 + 수동 recall 뿐. 과거 *세션 전문*을 검색하는 층 자체가 없다. 게다가 인덱스(MEMORY.md)가 cwd 마다 얇다(live: 메모리 dir 15개 / MEMORY.md 인덱스 14개 / 메모리 .md 파일 58개, cwd 마다 비대칭). 단 `.claude` 설정 repo cwd 자체(`projects/-home-Uihyeop--claude/memory/`)는 빈 레이어이고, 실제 작업 프로젝트 cwd 들엔 채워져 있다(per-cwd 라 config repo 만 비어 보였던 것). → **이식 1순위**(T1).

### (b) skill self-edit = *에이전트가 런타임에 자기 절차를 고침*, 우리는 out-of-band
- Hermes: `skill_manage`(create/patch/edit/delete)로 에이전트가 SKILL.md 를 직접 수정, 매 turn 후 review 가 트리거. (confidence: high)
- 우리: drill 이 행동 회귀를 *발견*하면 사용자 승인 후 *수동* 지침 수정. 안전하나 느리다. → 이식 시 우리 불변식("결정은 사용자") 유지하며 *제안 자동초안* 단계만 추가(T2).

### (c) Curator 자동 stale/archive lifecycle, 우리 sweep 은 수동/세미자동
- Hermes: inactivity check 로 30d→stale, 90d→archive 자동 전이. (confidence: high)
- 우리: post-it sweep 은 "확실한 것만" 자동 prune(애매하면 keep), 시간기반 lifecycle 없음. → 시간기반 stale 후보 *플래깅*(삭제는 보고)을 sweep 에 추가(T3).

### (d) persistent multi-channel gateway — 우리엔 없음
- Hermes: 20+ 채널을 long-running gateway 로. (confidence: high)
- 우리: 없음(notes/ 파일 pull 모델). → 쓰임 불일치(논문·실험·코드 파이프). 이식 우선순위 낮음, "왜 안 맞나" 명시로 충분.

---

## 3. 우리가 동등하거나 앞선 점

### (a) 하드 순서 게이트 + hook 강제 — Hermes 엔 산출물 거버넌스 없음
research/analyze → spec → plans 단방향 게이트를 `artifact-guard.sh` 가 *신규 생성 순서* 하드 강제. Hermes 에는 산출물 생성 순서·소유관계 개념이 없다. (확실)

### (b) 적대 검증층 — Hermes self-improvement 는 LLM 정성판단 단독
claim-verify(N-vote default-refute, WebSearch 모순 탐색, 다수결 kill) + fact-check(verbatim 대조) = *적대적* 검증. Hermes Curator/review 는 단일 LLM 정성 review 뿐 — 적대 voter·교차검증 없음. (axis2 §2.2)

### (c) L4 메타루프 — 시스템이 *자기 지침을 시험*하는 층
drill(fixture 가상상황 headless 시험·채점 = 행동 회귀테스트) + study(외부 동향 × 세팅 대조 → 제안). Hermes 에는 *메타-시험* 층이 없다 — self-improvement 는 자기 산출물을 고칠 뿐 *자기 규칙을 시험*하지 않는다. (loops L4)

### (d) 산출물 버전 트래킹 + 소유스킬 수정 규율
각 산출물은 그것을 만든 스킬로만 수정, `_internal/versions/v{N}/` 누적. 관심사·이력 분리. Hermes 의 skill version frontmatter 보다 강한 거버넌스. (CLAUDE.md)

### (e) 멀티에이전트 분업 (7팀)
maker/verifier·N-vote·fact-check 를 7개 전문팀으로 분업. Hermes 의 delegate/mixture_of_agents tool 은 동적 위임이나 *고정 역할·적대 검증 분업*은 우리가 더 구조화. (agents)

---

## 4. 철학 차이 (핵심 1단락)

Hermes 와 우리 세팅은 self-improving agent 의 **두 극단**을 대표한다. Hermes 는 *에이전트가 런타임에 자율적으로 자기를 고치는* 모델 — 매 turn review·`skill_manage` self-edit·Curator 자동 lifecycle 로 사람 개입 없이 빠르게 진화하지만, 품질 판단이 LLM 정성 review 단독이라 거버넌스가 약하고 자기 규칙을 시험하는 메타 층이 없다. 우리는 *루프가 발견·제안하고 결정은 사용자가 하는* 모델 — 하드 순서 게이트·적대 N-vote·drill 행동 회귀·소유스킬 버전관리로 안전하고 검증가능하지만, 모든 개선이 사람 승인을 거쳐 느리다. 이 trade-off 는 **속도 vs 신뢰성**으로 요약되며, 우리에게 옳은 이식 전략은 Hermes 의 *자동화 속도*를 빌리되 우리 불변식("루프 출구는 제안까지, 결정은 사용자")을 깨지 않는 것 — 즉 *자동 초안 생성*은 도입하되 *자동 적용*은 거부한다.

**Takeaway**: 배울 것은 메커니즘(FTS5 recall·자동 초안·시간기반 lifecycle), 지킬 것은 거버넌스(순서 게이트·적대검증·사용자 결정 게이트). 이식은 메커니즘만 떼어와 우리 결정 게이트 *앞단*에 붙인다.
