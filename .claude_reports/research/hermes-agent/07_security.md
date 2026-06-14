# 07 — 보안 (security): OpenClaw 취약점 이력 + Hermes 보안 모델 + "전부 보완" 적대 판정

> deliverable: adversarial security benchmarking. 조사일 2026-06-14.
> 근거 = `cards/axis4_security.md` (1차 소스 우선 — CVE/GHSA/researcher disclosure/repo SECURITY.md).
> 핵심 질문: "Hermes 가 OpenClaw 의 보안 문제를 *전부* 보완하고 완전히 안전하다" 는 강한 주장이 성립하는가? → **결론: 기각.**
> SEO/affiliate 단독 주장은 본 보고서에서도 ❓SEO-only/미검증 으로 격리한다.

---

## 1. OpenClaw — 실재 프로젝트 확정 + 보안 이력 (1차 검증)

**OpenClaw 는 실재하는 self-hosted autonomous AI agent 오픈소스 프로젝트다 (SEO 별칭 아님).**

- 제작자: Peter Steinberger (오스트리아, 2026-02-14 OpenAI 합류). repo `github.com/openclaw/openclaw` (MIT, TypeScript + Swift).
- 개명 이력 (취약점 추적 시 구명으로도 검색 필요): **Warelay → CLAWDIS → Clawdbot → Moltbot → OpenClaw**. npm 패키지명은 여전히 `clawdbot` (CVE advisory 가 이 이름으로 등록).
- 성격: messaging platform(WhatsApp/Telegram/Discord/Signal/iMessage)을 main UI 로 쓰는 self-hosted 24/7 personal agent. shell command·browser automation·email·file 조작. heartbeat scheduler 로 unprompted 자율 실행. 로컬 markdown memory. ClawHub third-party skill marketplace 보유.
- 폭발적 인기(GitHub star 24만+) → 공격자에게 매력적 타깃 → 보안 연구 집중.

> OpenClaw 는 Hermes Agent 와 **동일 카테고리**(self-hosted, messaging-gateway, 자율 tool-executing agent) — 두 프로젝트가 직접 경쟁 alternative 로 묶이며, SEO 글들이 "Hermes 가 OpenClaw 보안 문제를 고쳤다" 류 비교를 양산한다(§3).

### OpenClaw 검증된 취약점 표

| 주장된 취약점 | 1차 출처 | CVSS | 신뢰도 | 검증 |
|---|---|---|---|---|
| 1-Click RCE via gatewayUrl token exfiltration (CVE-2026-25253) — Control UI 가 query string `gatewayUrl` 을 무검증 신뢰·auto-connect, stored gateway token 을 WebSocket payload 로 전송. loopback-only 여도 victim 브라우저가 bridge. npm `clawdbot` ≤2026.1.28, patched 2026.1.29 | [GHSA-g8p2-7wf7-98mq](https://github.com/advisories/GHSA-g8p2-7wf7-98mq), [SOCRadar](https://socradar.io/blog/cve-2026-25253-rce-openclaw-auth-token/), [runZero](https://www.runzero.com/blog/openclaw/) | 8.8 High | high | ✅ |
| RCE via malicious .npmrc — `plugins/hooks install` 이 staging dir 에서 `npm install --ignore-scripts` 하되 project-level `.npmrc` 를 strip 안 함 → 악성 `.npmrc` 가 npm `git` executable path override → git dependency resolve 시 공격자 프로그램 실행. ≤2025.3.23, fixed ≥2026.3.24. **별도 CVE 없음** | [GHSA-m3mh-3mpg-37hw](https://github.com/openclaw/openclaw/security/advisories/GHSA-m3mh-3mpg-37hw) | 3.1 Low (CWE-426) | high | ✅ |
| Log poisoning / indirect prompt injection — attacker-controlled WebSocket header(`Origin`,`User-Agent`)가 sanitization 없이 로깅 → AI-assisted debugging 시 LLM context 로 들어가 injection 채널(~15KB). fixed 2026.2.13 | [GHSA-g27f-9qjv-22pm (Penligent 분석)](https://www.penligent.ai/hackinglabs/openclaw-log-poisoning-vulnerability-indirect-prompt-injection-via-websocket-headers-fixed-in-2026-2-13/) | 8.6 High | high | ✅ |
| `_exec` tool 이 **user approval 없이, sandbox 없이** 임의 명령 실행 | [HiddenLayer](https://www.hiddenlayer.com/research/exploring-the-security-risks-of-ai-assistants-like-openclaw) | — | high | ✅ |
| HEARTBEAT.md 에 악성 지시 append → system prompt 장악, 새 세션 넘어 **persistent backdoor** (memory poisoning) | [HiddenLayer](https://www.hiddenlayer.com/research/exploring-the-security-risks-of-ai-assistants-like-openclaw) | — | high | ✅ |
| 모든 API key/token 이 `~/.openclaw/.env` 에 **plaintext** → RCE 로 손쉬운 exfiltration | [HiddenLayer](https://www.hiddenlayer.com/research/exploring-the-security-risks-of-ai-assistants-like-openclaw) | — | high | ✅ |
| ClawHub 악성 skill 이 agent 에게 macOS stealer **AMOS(Atomic Stealer)** 다운·실행 지시 (supply chain) | [HiddenLayer](https://www.hiddenlayer.com/research/exploring-the-security-risks-of-ai-assistants-like-openclaw), [Wikipedia(Cisco)](https://en.wikipedia.org/wiki/OpenClaw) | — | high | ✅ |
| sandbox escape (defense rate 17%), privilege escalation (8%) — LLM backend 별 native defense 17~83% (66%p 편차) → 모델 선택이 1차 보안 결정 | [arXiv:2603.10387](https://arxiv.org/html/2603.10387v1) | — | high | ✅ |
| Cisco: third-party skill 이 user 인지 없이 data exfiltration / 중국 정부(2026-03) state agency·은행 사용 금지 | [Wikipedia](https://en.wikipedia.org/wiki/OpenClaw) | — | medium-high | ✅ |
| shared "main" session 으로 multi-user credential 누수 | [Giskard](https://www.giskard.ai/knowledge/openclaw-security-vulnerabilities-include-data-leakage-and-prompt-injection-risks) | — | medium | ⚠️ 2차, 1차 advisory 미확인 |
| "Moltbook breach / exposed dashboard", "247,000 stars" 정확 수치 | adversa.ai·vibecoding 등 | — | low | ❓ SEO-only — 단독 인용 금지 |

**"Lethal Trifecta" 정식 충족 (HiddenLayer):** OpenClaw 는 (1) _exec approval·sandbox 없음 + (2) HEARTBEAT.md persistent backdoor + (3) .env plaintext secret + (4) ClawHub 악성 skill AMOS stealer 가 동시에 성립 — private data 접근 + untrusted content 노출 + 외부 통신 능력의 세 요소를 모두 갖춘다.

**Takeaway**: OpenClaw 의 보안 문제는 SEO 과장이 아니라 **다수 1차 검증됨** (CVE 1 + GHSA 2 + security firm 2 + academic 1 + 국가 규제). "OpenClaw 는 보안이 엉망이었다" 는 큰 틀은 1차 소스로 성립한다. 단 정확 star 수·Moltbook breach 세부 같은 SEO dramatize 는 ❓로 격리.

---

## 2. Hermes 보안 모델 — repo SECURITY.md + docs 1차 근거

> 출처: [Hermes SECURITY.md](https://github.com/NousResearch/hermes-agent), [Hermes docs security](https://hermes-agent.nousresearch.com/docs/user-guide/security).

Hermes 의 보안 문서는 **이례적으로 정직**하다 — in-process 방어를 containment 라 부르지 않고, OS-level isolation 만 진짜 boundary 라고 명시한다.

**7-layer defense-in-depth:**
1. User authorization — allowlist + DM pairing code
2. Dangerous command approval — destructive op 에 HITL
3. Container isolation — Docker / Singularity / Modal / Daytona / NVIDIA OpenShell
4. MCP credential filtering — subprocess env var isolation (명시 선언분만 passthrough)
5. Context file scanning — prompt injection detection (메모리/컨텍스트 injection 스캔)
6. Cross-session isolation — 세션 간 데이터 격리 (OpenClaw shared-main-session 누수와 대비)
7. Input sanitization — working directory allowlist 검증

**SECURITY.md 핵심 정직 진술 (제작자 본인 명시):**
- "Nothing inside the agent process constitutes containment — not the approval gate, not output redaction, not any pattern scanner."
- "Authorization is required at every surface that crosses a trust boundary." (allowlist 미설정 시 agent work dispatch 거부)
- "Session identifiers are routing handles, not authorization boundaries."
- approval gate 는 "cooperative-mode mistakes, not adversarial output" 만 잡음 / output redaction 은 "a motivated output producer will defeat it" / Skills Guard 는 "a review aid" 일 뿐.

**중요한 self-인정 약점:** `docker`/`singularity`/`modal`/`daytona` backend 에서는 **dangerous command check 가 skip 됨** — container 자체가 security boundary 이기 때문. → container 가 약하거나 misconfigure 면 approval gate 도 꺼져 무방비.

**1차 미확인:** cron recursion 차단 메커니즘은 SECURITY.md·docs 에서 직접 확인 못 함(§3 잔존표 ❓).

**Takeaway**: Hermes 의 보안 *설계 자세*는 OpenClaw 의 알려진 실수(approval·sandbox 무 / plaintext secret / shared session / gateway 무검증)를 구조적으로 회피하도록 설계되어 있고, 무엇보다 **제작자 본인이 in-process 방어의 한계를 명시**한다는 점에서 보안 성숙도가 OpenClaw 보다 높다.

---

## 3. 적대 판정 — "Hermes 가 OpenClaw 보안을 전부 보완·완전 안전"

**판정: ❌ 기각.** 근거 둘:

**(a) Hermes 문서 어디에도 OpenClaw 언급·"보완" 주장이 없다.** SECURITY.md·docs·homepage 모두 OpenClaw·비교 벤치마킹 무언급. → "Hermes 가 OpenClaw 보안을 전부 보완했다" 는 **1차 근거가 0 인 주장**이며, 이 비교 프레임은 전적으로 SEO/affiliate 글(hermes-ai.net·hermes-agent.org·hermes-growth.dev·petronellatech 등)에서 생성된 것이지 Hermes 제작자(Nous Research)의 1차 주장이 아니다. → **❓ SEO-narrative, 1차 미검증.**

**(b) Hermes SECURITY.md 본인이 완전 안전을 *제작자가 부정*한다.** "in-process 방어(approval gate·redaction·scanner)는 그 무엇도 containment 가 아니다" 라고 명시하는 순간, "전부 보완(=완전 안전)" 주장은 *제작자 본인 문서와 정면 모순*된다. Hermes 의 입장은 "구조적 위험이 남는다" 이지 "완전 안전" 이 아니다.

**구조적으로 OpenClaw 와 *공유*하는 잔존 위협 (카테고리 동일):**
- **임의 shell/code 실행**: Hermes 도 LLM-emitted shell command 를 실행. container 안이긴 하나 container = 유일 경계 (in-process gate 는 adversarial 에 무력, container backend 시 approval 까지 skip).
- **prompt injection**: context file scanning 은 "review aid"·"detection" 수준. arXiv 결과처럼 모델 backend 에 따라 native defense 17~83% 요동 → 약한 모델 쓰면 동일하게 뚫림.
- **supply chain**: Skills Guard 는 강제 차단 아님 — 악성 skill 이 declared env 끌어 쓰면 통과.
- **messaging gateway 노출**: 멀티 채널 adapter 노출면이 넓고 operator 설정 의존.

**"self-host 라 안전하다" 의 허실:** self-host 는 cloud multi-tenant 노출은 줄이지만 (a) 임의 shell 실행 (b) indirect prompt injection (c) supply-chain skill (d) 로컬 secret (e) gateway 인증 — 어느 것도 self-host 자체로 해결 안 됨. OpenClaw 의 CVE 2건이 모두 self-host 환경에서 터진 것이 직접 반증. **self-host = attack surface 의 *위치* 이동이지 *제거*가 아니다.**

**공정한 차이 (Hermes 가 *설계상* 더 나은 점, 단 "전부"는 아님):** OpenClaw `_exec`(approval·sandbox 무) → Hermes approval gate + container 격리 기본 / OpenClaw `.env` plaintext → Hermes MCP credential filtering 으로 env 기본 stripping / OpenClaw shared-main-session 누수 → Hermes cross-session isolation / OpenClaw gateway 무검증(CVE-2026-25253) → Hermes every trust boundary authorization + allowlist 없으면 dispatch 거부.

> **최종 판정 (1줄): Hermes 의 보안 설계 자세는 OpenClaw 의 알려진 실수 다수를 구조적으로 회피하나, "전부 보완"·"완전 안전" 은 거짓이며 Hermes 본인 SECURITY.md 가 이를 부정한다 — 임의 shell·prompt injection·supply chain·gateway 노출의 잔존 위험은 카테고리상 OpenClaw 와 동일하게 크다.**

### Hermes 잔존 attack surface 표

| 위협 (OWASP ASI 매핑) | Hermes 완화책 (1차 확인) | 잔존 위험 | confidence |
|---|---|---|---|
| 임의 shell/code 실행 (ASI05) | approval gate + container backend(Docker/Modal/Daytona/OpenShell) | container 가 *유일* 경계; container 시 approval skip; misconfig 시 host 노출 | high |
| indirect prompt injection (ASI01/ASI06) | context file scanning (detection·review aid) | 약한 LLM backend 시 native defense 17%대; scanner 는 "motivated attacker 가 defeat"(본인 인정) | high |
| memory/context poisoning (ASI06) | context file scanning + cross-session isolation | persistent memory 채널 자체 존재 → poisoning 면역 아님 | medium |
| supply chain — 악성 skill/MCP (ASI04) | Skills Guard("review aid"), MCP credential filtering | guard 는 강제 차단 아님; 악성 skill 이 declared env 끌어 쓰면 통과 | high |
| secret/credential 노출 (LLM06) | env var 기본 stripping, 선언분만 passthrough | RCE 성립 시 declared secret·런타임 메모리 노출; 로컬 저장 secret 은 OS 권한 의존 | medium |
| messaging gateway 인증 (ASI03) | every boundary authorization, allowlist 미설정 시 dispatch 거부, DM pairing | 멀티채널 adapter(Telegram/Discord/Slack) 노출면 넓음; operator 설정 의존 | medium |
| privilege/over-agency (ASI02/ASI03) | allowlist, working dir 검증 | autonomous agent 본질상 broad tool 권한; arXiv priv-esc 방어 최약(8%) | medium |
| cron/heartbeat recursion (ASI08 cascading) | 1차 미확인 (docs/SECURITY.md 명시 없음) | 자율 스케줄러 재귀·자기증식 루프 차단 여부 불명 | low ❓ |
| sandbox escape (path traversal/symlink) | working dir allowlist (logical) | arXiv: logical sandbox 만으론 escape 방어 17%; OS-level 필요 | medium |

**Takeaway**: Hermes 는 OpenClaw 의 *구체적 실수*는 피했으나, self-host autonomous tool-executing agent 라는 **카테고리 자체의 잔존 attack surface** 는 그대로 안고 있다. 보안 비교의 정직한 결론은 "Hermes 가 더 안전하게 *설계*되었다" 이지 "Hermes 는 안전하다" 가 아니다.

---

## 4. 자율 에이전트 보안 체크리스트 (PRD용)

> **용도**: 우리가 추후 *"자율 에이전트 플러그인/설치 프로그램"* 을 PRD(autopilot-spec)로 설계할 때, 본 체크리스트가 보안 요구사항의 source 가 된다 — OWASP Top 10 for Agentic Applications 2026(ASI01–ASI10) + OWASP LLM Top 10 2025 + 위 OpenClaw/Hermes 사례 교훈에서 7개 그룹으로 도출.
> 출처: [OWASP Agentic 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/), [Promptfoo OWASP Agentic](https://www.promptfoo.dev/docs/red-team/owasp-agentic-ai/), [arXiv:2603.10387](https://arxiv.org/html/2603.10387v1).

**A. Tool/code 실행 (ASI02·ASI05 — OpenClaw `_exec`·.npmrc 교훈)**
- [ ] LLM-emitted shell/code 는 OS-level isolation(container/VM/microVM) 안에서만 실행 — in-process gate 를 containment 로 신뢰 금지.
- [ ] container backend 사용 시에도 default-deny + 위험 명령 approval 을 *완전히* 끄지 말 것 (Hermes "container 면 approval skip" 안티패턴 회피).
- [ ] 패키지/플러그인 설치 시 `--ignore-scripts` + project-level `.npmrc`/config stripping + lockfile 검증 (GHSA-m3mh 교훈).
- [ ] least-privilege: filesystem/network(L7 egress)/syscall 단위 declarative policy.

**B. Prompt injection / memory (ASI01·ASI06 — HEARTBEAT.md·log poisoning 교훈)**
- [ ] untrusted content(web/email/log/skill)는 별도 trust tier — context 주입 전 sanitize + length limit + control char 제거.
- [ ] persistent memory(markdown/RAG) write 는 검증·서명·diff 검토 (memory poisoning 차단).
- [ ] model backend 의 native tool-use safety alignment 를 *조달 기준*에 포함 (arXiv: 17~83% 편차 → 모델 선택이 1차 보안 결정).
- [ ] scanner/redaction 은 review aid 로만 카운트 — adversarial 보장 가정 금지.

**C. Identity·privilege·gateway (ASI03 — CVE-2026-25253 교훈)**
- [ ] 모든 trust boundary 에 authorization 강제; allowlist 미설정 시 작업 dispatch 거부(fail-closed).
- [ ] gateway URL/endpoint 등 외부 입력 query param 검증 + auto-connect 금지 + token 전송 전 사용자 확인 (CVE-2026-25253 직접 교훈).
- [ ] session id 를 authorization boundary 로 쓰지 말 것; multi-user/group 채널 강제 격리.
- [ ] messaging adapter 마다 caller allowlist + pairing/인증.

**D. Supply chain (ASI04 — ClawHub AMOS 교훈)**
- [ ] third-party skill/plugin/MCP server 는 서명·출처 검증·격리 실행; marketplace skill default-untrusted.
- [ ] 설치/업데이트 시 typosquatting·module shadowing·git alias poisoning 점검.

**E. Secrets (LLM06 — .env plaintext 교훈)**
- [ ] secret plaintext 디스크 저장 금지 — OS keychain/secret manager 사용.
- [ ] subprocess/tool 에 env var default-strip, 명시 선언분만 passthrough.

**F. Autonomy 안전망 (ASI08·ASI10)**
- [ ] cron/heartbeat 등 자율 스케줄러에 재귀·자기증식·무한루프 차단(rate limit·depth limit·budget cap).
- [ ] critical 행위는 default-deny + HITL; 위험도 분류(low auto / medium policy / high approval / critical deny).
- [ ] 감사 로깅(audit log) 전 행위 기록, repudiation 방지.
- [ ] rogue-agent 탐지: 행동 baseline 이탈 모니터링.

**G. 운영 권고 (arXiv defense framework)**
- [ ] defense-in-depth: allowlist → MITRE ATT&CK pattern match → semantic intent judge → sandbox guard 다층.
- [ ] agent 는 container/VM + mandatory access control 안에 배포.

**Takeaway**: 이 7개 그룹은 *자율 에이전트* 산출물을 우리가 직접 만들 때의 최소 보안 baseline 이다 — OpenClaw 의 실패가 "어떤 항목을 빠뜨리면 어떤 CVE 가 나는지" 의 실증 사례집 역할을 하고, Hermes 의 정직한 SECURITY.md 가 "각 방어를 어떻게 *과신하지 않게* 기술하는지" 의 모범 사례다.

---

## 출처 ledger

**1차 (CVE/GHSA/repo/researcher/academic):**
- [CVE-2026-25253 / GHSA-g8p2-7wf7-98mq — 1-click RCE gatewayUrl token exfil, CVSS 8.8](https://github.com/advisories/GHSA-g8p2-7wf7-98mq) — high
- [GHSA-m3mh-3mpg-37hw — .npmrc RCE, CVSS 3.1 (CWE-426)](https://github.com/openclaw/openclaw/security/advisories/GHSA-m3mh-3mpg-37hw) — high
- [GHSA-g27f-9qjv-22pm — log poisoning prompt injection, CVSS 8.6 (Penligent 분석 경유)](https://www.penligent.ai/hackinglabs/openclaw-log-poisoning-vulnerability-indirect-prompt-injection-via-websocket-headers-fixed-in-2026-2-13/) — high
- [HiddenLayer — OpenClaw security risks (`_exec`, HEARTBEAT backdoor, plaintext .env, AMOS supply chain, lethal trifecta)](https://www.hiddenlayer.com/research/exploring-the-security-risks-of-ai-assistants-like-openclaw) — high
- [arXiv:2603.10387 — OpenClaw 정량 보안 분석 + HITL defense framework](https://arxiv.org/html/2603.10387v1) — high
- [Hermes Agent repo (SECURITY.md)](https://github.com/NousResearch/hermes-agent) — high
- [Hermes Agent docs — security model](https://hermes-agent.nousresearch.com/docs/user-guide/security) — high
- [Wikipedia: OpenClaw — 정체·개명 이력·Cisco·중국 규제](https://en.wikipedia.org/wiki/OpenClaw) — medium-high
- [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) — high
- [Promptfoo — OWASP Agentic ASI01–ASI10 canonical names](https://www.promptfoo.dev/docs/red-team/owasp-agentic-ai/) — high

**2차 (신뢰할 만한 보안 분석):**
- [SOCRadar — CVE-2026-25253 분석](https://socradar.io/blog/cve-2026-25253-rce-openclaw-auth-token/) — medium
- [runZero — OpenClaw RCE](https://www.runzero.com/blog/openclaw/) — medium
- [Giskard — data leakage & prompt injection (shared-session 누수)](https://www.giskard.ai/knowledge/openclaw-security-vulnerabilities-include-data-leakage-and-prompt-injection-risks) — medium

**저신뢰 (❓ SEO/affiliate — 단독 근거 금지):**
- adversa.ai / vibecoding.app / mintmcp / skywork.ai / oneclaw.net / hermes-ai.net / hermes-agent.org / hermes-growth.dev 등 — "Moltbook breach", 정확 star 수, **"Hermes 가 OpenClaw 보안 전부 보완"** 류 비교 narrative 의 출처. 1차 교차 안 되는 주장은 전부 ❓격리.
