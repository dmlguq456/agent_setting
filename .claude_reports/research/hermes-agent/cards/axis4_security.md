# 축 4: 보안 (security) — OpenClaw 취약점 이력 + Hermes 보안 모델·"전부 보완" 주장 적대 검증

> 담당 축: Hermes Agent vs OpenClaw 의 security 비교.
> 핵심 질문: "Hermes 가 OpenClaw 의 보안 문제를 *전부* 보완했다" 는 강한 주장을 1차 소스로 적대적 검증.
> 작성 자세: 1차 소스(CVE/GHSA/researcher disclosure/repo SECURITY.md) 우선. SEO/affiliate 단독 주장은 전부 ❓SEO-only 로 격리.
> 조사일: 2026-06-14.

---

## 0. OpenClaw 정체 — 확정 (high confidence)

**OpenClaw 는 실재하는 오픈소스 self-hosted autonomous AI agent 프로젝트다. SEO 별칭이 아니다.**

- 제작자: Peter Steinberger (오스트리아 개발자, 2026-02-14 OpenAI 합류). [Wikipedia](https://en.wikipedia.org/wiki/OpenClaw)
- repo: `github.com/openclaw/openclaw` (MIT License, TypeScript + Swift). [Wikipedia](https://en.wikipedia.org/wiki/OpenClaw)
- 개명 이력 (중요 — 취약점 추적 시 이전 이름으로도 검색해야 함): **Warelay (2025-11-24) → CLAWDIS (2025-12-03) → Clawdbot (2026-01-02) → Moltbot (2026-01-27) → OpenClaw (2026-01-30)**. npm 패키지명은 여전히 `clawdbot` (CVE advisory 가 이 이름으로 등록). [Wikipedia](https://en.wikipedia.org/wiki/OpenClaw)
- 성격: messaging platform(WhatsApp/Telegram/Discord/Signal/iMessage)을 main UI 로 쓰는 self-hosted 24/7 personal agent. shell command·browser automation·email·calendar·file 조작 수행. heartbeat scheduler 로 unprompted 자율 실행. 로컬 markdown 파일에 memory 저장. ClawHub 라는 third-party skill marketplace 보유. [Milvus blog](https://milvus.io/blog/openclaw-formerly-clawdbot-moltbot-explained-a-complete-guide-to-the-autonomous-ai-agent.md), [Wikipedia](https://en.wikipedia.org/wiki/OpenClaw)
- 규모: 3개월 내 GitHub star 24만+ (SEO 글의 "247,000" 수치는 미검증이나 폭발적 성장은 사실). → **공격자 입장에서 매력적 타깃 = 보안 연구가 집중됨.**

> 비교 alternative 거론 맥락: OpenClaw 는 Hermes Agent 와 동일 카테고리(self-hosted, messaging-gateway, 자율 tool-executing agent). 두 프로젝트는 직접 경쟁 alternative 로 묶이며, SEO 글들이 "Hermes 가 OpenClaw 보안 문제를 고쳤다" 류 비교를 양산함 (§4 참조).

---

## 1. OpenClaw 보안 취약점 이력 — 1차 소스 기반

OpenClaw 는 폭발적 인기 직후 **다수의 1차 보안 disclosure 가 실재**한다. SEO 주장이 아니라 CVE·GitHub Security Advisory·security firm 연구글로 뒷받침됨.

### 1-A. CVE-2026-25253 — 1-Click RCE via gatewayUrl token exfiltration (high, 검증됨)
- claim: 인증된 사용자가 악성 링크 클릭만으로 gateway auth token 이 공격자 서버로 유출 → operator-level gateway API 접근 → arbitrary config 변경 + gateway host 에서 code execution.
- 메커니즘 (1차 advisory 인용): Control UI 가 query string 의 `gatewayUrl` 을 검증 없이 신뢰하고 load 시 자동 연결, stored gateway token 을 WebSocket connect payload 로 전송. **loopback-only 로 제한해도 victim 브라우저가 connection 을 bridge 해 성립.**
- 영향 패키지: npm `clawdbot` ≤ 2026.1.28. patched: **2026.1.29** (UI 에서 new gateway URL 확인 강제).
- CVSS: 8.8 (High).
- 출처: [GitHub Advisory GHSA-g8p2-7wf7-98mq (CVE-2026-25253)](https://github.com/advisories/GHSA-g8p2-7wf7-98mq), [SOCRadar](https://socradar.io/blog/cve-2026-25253-rce-openclaw-auth-token/), [runZero](https://www.runzero.com/blog/openclaw/).

### 1-B. GHSA-m3mh-3mpg-37hw — RCE via malicious .npmrc (high, 검증됨)
- claim: plugin/hook 로컬 설치 시 arbitrary local code execution.
- 메커니즘 (1차 advisory 인용): `openclaw plugins install` / `openclaw hooks install` 이 staging dir 에서 `npm install --omit=dev --silent --ignore-scripts` 실행하되 project-level `.npmrc` 를 stripping 하지 않음. 악성 `.npmrc` 가 npm 의 `git` executable path 를 override → package.json 의 git dependency resolve 시 공격자 프로그램 실행.
- 영향: ≤ 2025.3.23, fixed ≥ 2026.3.24. CVSS 8.6 (High). **별도 CVE 없음 (GHSA only).**
- 출처: [GHSA-m3mh-3mpg-37hw](https://github.com/openclaw/openclaw/security/advisories/GHSA-m3mh-3mpg-37hw).

### 1-C. GHSA-g27f-9qjv-22pm — Log poisoning / indirect prompt injection via WebSocket headers (medium-low, 검증됨)
- claim: attacker-controlled WebSocket header(`Origin`, `User-Agent`)가 sanitization·length limit 없이 로깅 → AI-assisted debugging 시 그 log 가 LLM context 로 들어가 indirect prompt injection 채널이 됨 (~15KB 주입 가능).
- 영향: fixed **2026.2.13** (header sanitization + control char 제거 + length limit). CVSS 3.1 (Low) — 단 고권한 배포에선 운영상 유의미.
- 단, 연구자 본인이 "traditional RCE 처럼 동작하진 않았고 guardrail 이 sandbox 테스트에서 injection 탐지함" 으로 한정.
- 출처: [Penligent](https://www.penligent.ai/hackinglabs/openclaw-log-poisoning-vulnerability-indirect-prompt-injection-via-websocket-headers-fixed-in-2026-2-13/).

### 1-D. HiddenLayer 연구 — 구조적 위험 다발 (high, 검증됨, security firm 1차)
저자: Conor McCauley, Kasimir Schulz, Ryan Tracey, Jason Martin (HiddenLayer), 2026-02-03 공개. 발견:
- `_exec` tool 이 **user approval 없이, sandbox 없이** 임의 명령 실행.
- HEARTBEAT.md 파일에 악성 지시 append → system prompt 장악, 새 세션 넘어 **persistent backdoor**.
- 모든 API key/token 이 `~/.openclaw/.env` 에 **plaintext** 저장 → RCE 로 손쉽게 exfiltration.
- ClawHub 의 악성 skill 이 agent 에게 macOS stealer **AMOS(Atomic Stealer)** 다운·실행 지시 (supply chain).
- indirect prompt injection 으로 memory 변조(memory poisoning) → 전 세션 행동 변경.
- "Lethal Trifecta" 정식 충족: private data 접근 + untrusted content 노출 + 외부 통신 능력.
- 출처: [HiddenLayer Research](https://www.hiddenlayer.com/research/exploring-the-security-risks-of-ai-assistants-like-openclaw).

### 1-E. arXiv 2603.10387 — 정량 보안 분석 + defense framework (high, 검증됨, academic 1차)
- LLM backend 별 native defense rate: Claude Opus 4.6 83% / Qwen3 Max 68% / GPT-5.3 Codex 49% / DeepSeek V3.2 **17%** → **모델 선택 자체가 1차 보안 결정**, 66%p 편차.
- 카테고리별 최약점: **sandbox escape (defense 17%), privilege escalation (8%)** — logical sandboxing 만으로 불충분, OS-level isolation 필요 결론.
- HITL layered defense 제안: allowlist → pattern matching(MITRE ATT&CK 55+ rule) → semantic judge → sandbox guard.
- 출처: [arXiv:2603.10387](https://arxiv.org/html/2603.10387v1).

### 1-F. Cisco 발견 + 국가 차원 규제 (medium-high, 검증됨)
- Cisco: third-party skill 이 user 인지 없이 data exfiltration 수행 (HiddenLayer AMOS 건과 교차 일치).
- 중국 정부(2026-03): security risk 사유로 state agency·은행의 OpenClaw 사용 금지.
- 출처: [Wikipedia](https://en.wikipedia.org/wiki/OpenClaw).

### OpenClaw 취약점 — 출처 추적 표

| 주장된 취약점 | 1차 출처 (CVE/advisory URL) | 신뢰도 | 검증됨? |
|---|---|---|---|
| 1-Click RCE via gatewayUrl token exfil (CVE-2026-25253, CVSS 8.8) | [GHSA-g8p2-7wf7-98mq](https://github.com/advisories/GHSA-g8p2-7wf7-98mq) | high | ✅ |
| RCE via malicious .npmrc (CVSS 8.6, CVE 없음) | [GHSA-m3mh-3mpg-37hw](https://github.com/openclaw/openclaw/security/advisories/GHSA-m3mh-3mpg-37hw) | high | ✅ |
| Log poisoning indirect prompt injection (WebSocket headers, CVSS 3.1) | [GHSA-g27f-9qjv-22pm](https://www.penligent.ai/hackinglabs/openclaw-log-poisoning-vulnerability-indirect-prompt-injection-via-websocket-headers-fixed-in-2026-2-13/) | high | ✅ |
| `_exec` unsandboxed, no approval | [HiddenLayer](https://www.hiddenlayer.com/research/exploring-the-security-risks-of-ai-assistants-like-openclaw) | high | ✅ |
| HEARTBEAT.md persistent backdoor (memory poisoning) | [HiddenLayer](https://www.hiddenlayer.com/research/exploring-the-security-risks-of-ai-assistants-like-openclaw) | high | ✅ |
| plaintext secrets in `~/.openclaw/.env` | [HiddenLayer](https://www.hiddenlayer.com/research/exploring-the-security-risks-of-ai-assistants-like-openclaw) | high | ✅ |
| ClawHub 악성 skill → AMOS stealer (supply chain) | [HiddenLayer](https://www.hiddenlayer.com/research/exploring-the-security-risks-of-ai-assistants-like-openclaw), [Wikipedia(Cisco)](https://en.wikipedia.org/wiki/OpenClaw) | high | ✅ |
| sandbox escape (defense rate 17%), priv-esc (8%) | [arXiv:2603.10387](https://arxiv.org/html/2603.10387v1) | high | ✅ |
| shared "main" session 으로 multi-user credential 누수 | [Giskard](https://www.giskard.ai/knowledge/openclaw-security-vulnerabilities-include-data-leakage-and-prompt-injection-risks) | medium | ⚠️ (2차, 합리적이나 1차 advisory 미확인) |
| Moltbook breach / exposed dashboard | adversa.ai, vibecoding 등 SEO/blog | low | ❓ SEO-only — 1차 미확인, 단독 인용 금지 |
| "247,000 stars" 등 정확 수치 | SEO 글 다수 | low | ❓ 폭발적 성장은 사실, 정확 숫자 미검증 |

> 정직성 노트: **OpenClaw 의 취약점은 SEO 과장이 아니라 다수가 1차 검증됨**. 단 일부 SEO 글의 dramatize(예: 정확한 star 수, Moltbook breach 세부)는 ❓로 격리. "OpenClaw 는 보안이 엉망이었다" 는 큰 틀은 1차 소스로 *성립*한다.

---

## 2. Hermes 보안 모델 — 1차 소스(repo SECURITY.md + docs) 기반

> 출처: [Hermes SECURITY.md (repo)](https://github.com/NousResearch/hermes-agent), [Hermes docs security](https://hermes-agent.nousresearch.com/docs/user-guide/security).

Hermes 의 보안 문서는 **이례적으로 정직**하다 — in-process 방어를 containment 라 부르지 않고, OS-level isolation 만 진짜 boundary 라고 명시한다.

**7-layer defense-in-depth (docs):**
1. User authorization — allowlist + DM pairing code
2. Dangerous command approval — destructive op 에 HITL
3. Container isolation — Docker / Singularity / Modal / Daytona / NVIDIA OpenShell
4. MCP credential filtering — subprocess env var isolation (operator/skill 이 명시 선언한 변수만 passthrough)
5. Context file scanning — prompt injection detection (= 메모리/컨텍스트 injection 스캔)
6. Cross-session isolation — 세션 간 데이터 격리 (OpenClaw 의 shared-main-session 누수 1-X 와 대비)
7. Input sanitization — working directory allowlist 검증

**SECURITY.md 의 핵심 정직 진술 (그대로):**
- "Nothing inside the agent process constitutes containment — not the approval gate, not output redaction, not any pattern scanner."
- "Authorization is required at every surface that crosses a trust boundary." network adapter 는 operator allowlist 강제, allowlist 미설정 시 agent work dispatch 거부.
- "Session identifiers are routing handles, not authorization boundaries."
- approval gate 는 "cooperative-mode mistakes, not adversarial output" 만 잡음. output redaction 은 "a motivated output producer will defeat it". Skills Guard 는 "a review aid" 일 뿐.

**중요한 self-인정 약점 (docs):** "When running in `docker`/`singularity`/`modal`/`daytona` backends, **dangerous command checks are skipped** because the container itself is the security boundary." → container 가 곧 경계. container 격리가 약하거나 misconfigure 면 approval gate 도 꺼져 있어 무방비.

**확인 안 된 항목:** cron recursion 차단 메커니즘은 SECURITY.md·docs 에서 직접 확인 못 함 (조사 메모상 언급되나 1차 미확인 → §4 잔존표에서 ❓).

---

## 3. "전부 보완했다" 주장 — 적대 검증 (결론: 기각)

**핵심 발견: Hermes repo·docs 어디에도 OpenClaw 를 언급하거나 "OpenClaw 보안 문제를 고쳤다" 고 주장하지 않는다.** (SECURITY.md, docs, homepage 모두 OpenClaw·비교 벤치마킹 무언급.)

→ **"Hermes 가 OpenClaw 보안을 전부 보완했다" 는 1차 근거가 0 인 주장.** 이 비교 프레임은 전적으로 SEO/affiliate 글(hermes-ai.net·hermes-agent.org·hermes-growth.dev·petronellatech 등)에서 생성된 것으로, Hermes 제작자(Nous Research)의 1차 주장이 아니다. → **❓ SEO-narrative, 1차 미검증.**

더 강하게: Hermes 자신의 SECURITY.md 가 **"in-process 방어는 containment 가 아니다"** 라고 명시하는 순간, "전부 보완(=완전 안전)" 주장은 *제작자 본인 문서와 모순*된다. Hermes 는 "구조적 위험이 남는다" 는 입장이고, "전부 보완" 은 그 반대다.

**구조적으로 남는 위험 (OpenClaw 와 *공유*하는 위협 — 카테고리 동일):**
- 임의 shell/code 실행: Hermes 도 LLM-emitted shell command 를 실행. container 안이긴 하나 container = 유일 경계 (in-process gate 는 adversarial 에 무력, container 시 approval 까지 꺼짐).
- prompt injection: context file scanning 은 "review aid"·"detection" 수준. arXiv 결과처럼 모델 backend 에 따라 native defense 가 17~83% 로 요동 → Hermes 도 약한 모델 쓰면 동일하게 뚫림.
- 광범위 tool 권한 + messaging gateway 노출 = OpenClaw 의 "Lethal Trifecta" 를 Hermes 도 구조적으로 가짐 (private data + untrusted content + 외부 통신).

**"self-host 라 안전하다" 의 허실:** self-host 는 *cloud multi-tenant 노출*은 줄이지만 (a) 임의 shell 실행 (b) indirect prompt injection (c) supply-chain skill (d) 로컬 secret plaintext (e) messaging gateway 인증 — 어느 것도 self-host 자체로 해결 안 됨. OpenClaw 의 CVE 2건이 모두 self-host 환경에서 터진 게 직접 반증. **self-host = attack surface 의 *위치* 이동이지 *제거*가 아니다.**

**공정한 차이 (Hermes 가 *설계상* 더 나은 점, 단 "전부"는 아님):**
- OpenClaw `_exec` 는 approval·sandbox 무 → Hermes 는 approval gate + container 격리를 *기본 설계*에 포함. (단 container backend 시 approval skip 주의)
- OpenClaw secret plaintext `.env` → Hermes 는 MCP credential filtering 으로 env var 기본 stripping.
- OpenClaw shared-main-session 누수 → Hermes cross-session isolation.
- OpenClaw network gateway 무검증(CVE-2026-25253) → Hermes 는 every trust boundary 에 authorization 강제 + allowlist 없으면 dispatch 거부.

→ **판정: Hermes 의 보안 *설계 자세*는 OpenClaw 의 알려진 실수 다수를 구조적으로 회피하나, "전부 보완"·"완전 안전"은 거짓이며 Hermes 본인 문서가 이를 부정한다. 잔존 attack surface 는 카테고리상 OpenClaw 와 동일하게 크다.**

### Hermes 잔존 attack surface 표

| 위협 (OWASP ASI 매핑) | Hermes 완화책 (1차 확인) | 잔존 위험 | confidence |
|---|---|---|---|
| 임의 shell/code 실행 (ASI05) | approval gate + container backend(Docker/Modal/Daytona/OpenShell) | container 가 *유일* 경계; container 시 approval skip; misconfig 시 host 노출 | high |
| indirect prompt injection (ASI01/ASI06) | context file scanning (detection·review aid) | 약한 LLM backend 시 native defense 17%대; scanner 는 "motivated attacker 가 defeat" 가능(본인 인정) | high |
| memory/context poisoning (ASI06) | context file scanning + cross-session isolation | persistent memory 채널 자체는 존재 → poisoning 면역 아님 | medium |
| supply chain — 악성 skill/MCP (ASI04) | Skills Guard("review aid"), MCP credential filtering | guard 는 강제 차단 아님; 악성 skill 이 declared env 끌어 쓰면 통과 | high |
| secret/credential 노출 (LLM06) | env var 기본 stripping, operator/skill 선언분만 passthrough | RCE 성립 시 declared secret·런타임 메모리 노출; 로컬 저장 secret 보호는 OS 권한에 의존 | medium |
| messaging gateway 인증 (ASI03) | every trust boundary authorization, allowlist 미설정 시 dispatch 거부, DM pairing | 멀티 채널 adapter(Telegram/Discord/Slack) 노출면 넓음; operator 설정 의존 | medium |
| privilege/over-agency (ASI02/ASI03) | allowlist, working dir 검증 | autonomous agent 본질상 broad tool 권한; arXiv 기준 priv-esc 방어 카테고리는 일반적으로 최약(8%) | medium |
| cron/heartbeat recursion (ASI08 cascading) | 1차 미확인 (docs/SECURITY.md 에 명시 없음) | 자율 스케줄러의 재귀·자기증식 루프 차단 여부 불명 | low ❓ |
| sandbox escape (path traversal/symlink) | working dir allowlist (logical) | arXiv: logical sandbox 만으론 escape 방어 17%; OS-level 필요 | medium |

---

## 4. 자율 에이전트 보안 체크리스트 (PRD 용)

> "자율 에이전트 플러그인/설치 프로그램" 설계 시 보안 요구사항. OWASP Top 10 for Agentic Applications 2026(ASI01–ASI10) + OWASP LLM Top 10 2025 + 위 사례에서 도출.
> 출처: [OWASP Agentic 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/), [Promptfoo OWASP Agentic](https://www.promptfoo.dev/docs/red-team/owasp-agentic-ai/), [arXiv:2603.10387](https://arxiv.org/html/2603.10387v1).

**A. Tool/code 실행 (ASI02·ASI05, OpenClaw `_exec`·.npmrc 교훈)**
- [ ] LLM-emitted shell/code 는 OS-level isolation(container/VM/microVM) 안에서만 실행 — in-process gate 를 containment 로 신뢰 금지.
- [ ] container backend 사용 시에도 default-deny + 위험 명령 approval 을 *완전히* 끄지 말 것 (Hermes 의 "container 면 approval skip" 안티패턴 회피).
- [ ] 패키지/플러그인 설치 시 `--ignore-scripts` + project-level `.npmrc`/config stripping + lockfile 검증 (CVE GHSA-m3mh 교훈).
- [ ] least-privilege: filesystem/network(L7 egress)/syscall 단위 declarative policy.

**B. Prompt injection / memory (ASI01·ASI06, HEARTBEAT.md·log poisoning 교훈)**
- [ ] untrusted content(web/email/log/skill)는 별도 trust tier — context 주입 전 sanitize + length limit + control char 제거.
- [ ] persistent memory(markdown/RAG) write 는 검증·서명·diff 검토 (memory poisoning 차단).
- [ ] model backend 의 native tool-use safety alignment 를 *조달 기준*에 포함 (arXiv: 17~83% 편차 → 모델 선택이 1차 보안 결정).
- [ ] scanner/redaction 은 review aid 로만 카운트 — adversarial 보장 가정 금지.

**C. Identity·privilege·gateway (ASI03, CVE-2026-25253 교훈)**
- [ ] 모든 trust boundary 에 authorization 강제; allowlist 미설정 시 작업 dispatch 거부(fail-closed).
- [ ] gateway URL/endpoint 등 외부 입력 query param 검증 + auto-connect 금지 + token 전송 전 사용자 확인 (CVE-2026-25253 직접 교훈).
- [ ] session id 를 authorization boundary 로 쓰지 말 것; multi-user/group 채널은 강제 격리.
- [ ] messaging adapter 마다 caller allowlist + pairing/인증.

**D. Supply chain (ASI04, ClawHub AMOS 교훈)**
- [ ] third-party skill/plugin/MCP server 는 서명·출처 검증·격리 실행; marketplace skill default-untrusted.
- [ ] 설치/업데이트 시 typosquatting·module shadowing·git alias poisoning 점검.

**E. Secrets (LLM06, .env plaintext 교훈)**
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

---

## 출처 ledger

**1차 (CVE/GHSA/repo/researcher/academic):**
- [CVE-2026-25253 / GHSA-g8p2-7wf7-98mq — 1-click RCE gatewayUrl token exfil, CVSS 8.8](https://github.com/advisories/GHSA-g8p2-7wf7-98mq) — high
- [GHSA-m3mh-3mpg-37hw — .npmrc RCE, CVSS 8.6](https://github.com/openclaw/openclaw/security/advisories/GHSA-m3mh-3mpg-37hw) — high
- [GHSA-g27f-9qjv-22pm — log poisoning prompt injection, CVSS 3.1 (Penligent 분석 경유)](https://www.penligent.ai/hackinglabs/openclaw-log-poisoning-vulnerability-indirect-prompt-injection-via-websocket-headers-fixed-in-2026-2-13/) — high
- [HiddenLayer — OpenClaw security risks (`_exec`, HEARTBEAT backdoor, plaintext .env, AMOS supply chain, lethal trifecta)](https://www.hiddenlayer.com/research/exploring-the-security-risks-of-ai-assistants-like-openclaw) — high
- [arXiv:2603.10387 — OpenClaw 정량 보안 분석 + HITL defense framework](https://arxiv.org/html/2603.10387v1) — high
- [Hermes Agent repo (SECURITY.md)](https://github.com/NousResearch/hermes-agent) — high
- [Hermes Agent docs — security model](https://hermes-agent.nousresearch.com/docs/user-guide/security) — high
- [Wikipedia: OpenClaw — 정체·개명 이력·Cisco·중국 규제](https://en.wikipedia.org/wiki/OpenClaw) — medium-high (개명/제작자/Cisco/규제는 검증, star 수치 등은 미검증)
- [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) — high (체크리스트 기준)
- [Promptfoo — OWASP Agentic ASI01–ASI10 canonical names](https://www.promptfoo.dev/docs/red-team/owasp-agentic-ai/) — high

**2차 (신뢰할 만한 보안 분석):**
- [SOCRadar — CVE-2026-25253 분석](https://socradar.io/blog/cve-2026-25253-rce-openclaw-auth-token/) — medium
- [runZero — OpenClaw RCE](https://www.runzero.com/blog/openclaw/) — medium
- [Giskard — data leakage & prompt injection (shared-session 누수)](https://www.giskard.ai/knowledge/openclaw-security-vulnerabilities-include-data-leakage-and-prompt-injection-risks) — medium
- [Milvus blog — OpenClaw 정체 설명](https://milvus.io/blog/openclaw-formerly-clawdbot-moltbot-explained-a-complete-guide-to-the-autonomous-ai-agent.md) — medium

**저신뢰 (❓ SEO/affiliate — 단독 근거 금지):**
- adversa.ai / vibecoding.app / mintmcp / skywork.ai / oneclaw.net 등 — "Moltbook breach", 정확 star 수, "Hermes 가 OpenClaw 보안 전부 보완" 류 비교 narrative 의 출처. **1차 교차 안 되는 주장은 본 카드에서 전부 ❓격리.**

---

## 카드 자기 점검 (정직성)
- OpenClaw 취약점은 SEO 과장이 아니라 **다수 1차 검증됨** (CVE 1 + GHSA 2 + security firm 2 + academic 1).
- "Hermes 가 전부 보완" 은 **1차 근거 0** — Hermes 본인 문서가 OpenClaw 무언급 + "in-process 방어는 containment 아님" 으로 *완전 안전* 주장을 스스로 부정. SEO-narrative 로 격리.
- Hermes 의 보안 *설계 자세*는 OpenClaw 의 알려진 실수를 구조적으로 회피하나(approval+container+credential filtering+session isolation+boundary auth), 임의 shell·prompt injection·supply chain·gateway 노출의 잔존 위험은 카테고리상 OpenClaw 와 동일.
- 미확인 gap: Hermes cron recursion 차단(1차 미확인), Giskard shared-session 누수의 OpenClaw 1차 advisory, SEO 의 Moltbook breach 세부.
