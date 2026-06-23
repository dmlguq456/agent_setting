# 00_briefing — worklog 디자인/실험 스튜디오를 위한 OSS 선행 조사

> **조사일** 2026-06-23 · **mode** technology(OSS 레포 조사로 적응) · **depth** medium·전수 후보 평가 · **QA** thorough(메타데이터 gh api 재실측 통과)
> **렌즈**: local-first · BYOK · 기존 하네스(PATH 의 claude/codex CLI + skills/memory) 재사용 · 디스크=상태(live-REPL 회피) · 앱 임베드(통째 채택 X) · 라이선스 MIT/Apache
> **기준선(중복 서술 금지)**: OD = nexu-io/open-design(web+daemon spawn·srcdoc iframe·agents.ts 어댑터) · OCD = opencoworkai/open-codesign(Electron + pi 내장·boolean parity 검증)
> **상세 카드**: [축1 브리지](axis1_bridge.md) · [축2 프리뷰](axis2_preview.md) · [축3 추적](axis3_tracking.md) · [축4 허브·검증](axis4_manifest_design.md)

---

## Level 0 (한 줄)

네 축 모두 **"통째 채택"이 아니라 "계약·스키마·단일 바이너리만 lift"** 로 수렴한다 — ACP(브리지)·Sandpack(프리뷰)·Trackio+uPlot(추적)·gray-matter+odiff(허브·검증)를 골격으로, OD/OCD 의 ad-hoc 레이어를 *표준·결정론* 으로 승격하면 된다.

## Level 1 (3–5줄)

- **축1 브리지**: 엔진을 새로 고르지 말고 **ACP(Agent Client Protocol)** 라는 JSON-RPC 표준을 계약으로 깔면, 내 PATH 의 claude/codex CLI 를 *교체 없이* swappable 백엔드로 붙일 수 있다(Codex·Gemini·Goose 가 이미 ACP 에이전트). 실행 데몬 레퍼런스는 goose, TS 차선은 continue.
- **축2 프리뷰**: **Sandpack**(별-origin bundler iframe + HMR, `bundlerURL` self-host 로 local-first 양립)이 검증된 골격. 스트리밍 부분 렌더는 vercel/chatbot `onStreamPart` 델타, 경량 HTML/JSX 경로는 renderify식 babel-standalone 으로 보완. 클라우드 sandbox(e2b·WebContainer·val.town)는 라이선스·local-first 로 전원 탈락.
- **축3 추적**: 통째 tracking 서버 5종(aim·ClearML·wandb·MLflow UI·omniboard) 전부 임베드/local-first 에서 탈락. 정답은 **조립** — **Trackio `sqlite_storage.py`**(단일 SQLite WAL+mtime polling = 데몬 없이 라이브 tail)로 `_RUNLOG`/jsonl 을 적재하고 **uPlot**(의존성 0)으로 Next.js 차트.
- **축4 허브·검증**: (a) **gray-matter + awesome-design-md DESIGN.md 규격** 으로 sync-skills frontmatter 를 정규화해 **anthropic 공식 plugin.json 규격** manifest 로 방출, (b) **odiff exit-code(0/21/22)** 를 디자인 verifier 의 결정론 게이트로 박는다(캡처는 이미 의존 중인 Playwright, 추가 종속 ~0).
- **메타 발견**: 후보 레포 다수가 *이전·동결*됨(프롬프트 메타데이터 stale) — pi `mariozechner/pi-mono → earendil-works/pi`, ACP `zed-industries → 전용 org`, goose `block → aaif-goose`, **cody 는 live private + 공개 snapshot archived(dead)**. 통념 정정 2건: vercel "artifacts"는 HTML iframe 이 아니라 Pyodide/ProseMirror, wandb 는 SDK 만 OSS·대시보드 클로즈드.

---

## 축별 1픽 추천표 (메인 산출)

| 축 | 🥇 1픽 | 보완·페어 | 한 줄 이유 | license | 적합도 |
|---|---|---|---|---|---|
| **축1 — 에이전트 백엔드 브리지** | **Zed ACP** (`agentclientprotocol/agent-client-protocol`, *프로토콜 레이어로*) | **goose**(`goosed` /reply SSE + 네이티브 ACP 실행 ref) · **continue**(`IMessenger`+`cn serve` TS 차선) | 엔진이 아니라 와이어 계약이라 내 claude/codex CLI 를 *안 바꾸고* swappable 백엔드로 — `session/request_permission` 정식 권한 + Rust/TS/Py SDK | Apache-2.0 | 상(전략) |
| **축2 — sandboxed 라이브 프리뷰** | **Sandpack** (`codesandbox/sandpack`, self-host `bundlerURL`) | **vercel/chatbot `onStreamPart`**(스트리밍 델타) · **renderify 패턴**(경량 babel-standalone) | 별-origin iframe + multi-file 번들 + `updateSandbox` HMR 을 검증된 라이브러리로, self-host 로 local-first 양립 | Apache-2.0 | 상 |
| **축3 — 실험 추적/대시보드** | **Trackio `sqlite_storage.py`**(데이터 계약) + **uPlot**(차트 엔진) | **MLflow file store**(append-only 텍스트 + nested lineage, 차점 계약) · **perspective**(대용량 백업) | 단일 SQLite WAL+mtime = 데몬 없이 라이브 tail 을 *이미 푼* 계약 + 의존성 0·48KB 차트 | MIT / MIT | 상(역할 2분할) |
| **축4 — manifest 허브 & 디자인 검증** | (a) **gray-matter + awesome-design-md DESIGN.md 규격** / (b) **odiff** exit-code 게이트 | (a) **frontend-design `plugin.json`** 공식 방출 규격 / (b) **Playwright `page.screenshot()`** 캡처원(이미 의존) | (a) frontmatter 2층 인제스트→공식 manifest 방출 / (b) `0/21/22` exit 가 곧 boolean 판정 — 추가 종속 ~0 | MIT / MIT | (a)상 (b)상 |

> **Takeaway**: 네 축의 1픽이 모두 *통째 앱*이 아니라 *계약(ACP·SQLite 스키마·frontmatter)·단일 바이너리(odiff)·경량 lib(uPlot·gray-matter)* 다 — 종속 무게를 최소로 둔 채 OD/OCD 가 손으로 짠 레이어를 표준/결정론으로 갈아끼우는 그림.

---

## 크로스-축 조립도 (네 목표 A·B·C·D 로의 매핑)

```
(A) 프롬프트 → 라이브 캔버스 디자인 스튜디오
    worklog UI ──prompt──▶ [축1 ACP client] ──session/prompt──▶ 내 claude/codex CLI (백엔드 무변경)
                              │  session/update (agent_message_chunk · tool_call · request_permission)
                              ▼  ws/SSE 중계
    worklog 캔버스 ◀──부분 렌더── [축2 Sandpack self-host iframe] ◀── onStreamPart 델타(생성 HTML/JSX)
                                   (경량 1장은 renderify식 babel-standalone + sandboxed iframe)

(B) autopilot-lab 실험 라이브 모니터
    experiments/_RUNLOG.md·jsonl ──적재──▶ [축3 Trackio SQLite 스키마(.db + WAL)]
                                              │  mtime polling (데몬 0)
                                              ▼
    worklog 대시보드 ◀── [축3 uPlot setData()] (run 비교·계보는 _RUNLOG parent 링크로 자체 구성; 대용량 시 perspective)

(C) ~/.claude 정의 → manifest 허브
    skills/agents/hooks/loops frontmatter ──[축4 gray-matter 인제스트]──▶ manifest.json
                                              (anthropic plugin.json/marketplace.json 규격 정렬)
    sync-skills 가 방출 ─────────────────────▶ worklog 가 카탈로그 렌더

(D) 디자인 taste/검증 결정론 게이트
    maker ─▶ Design MCP render ─▶ critic ─▶ verifier
                                              ├─ console-check.mjs (exit 2)        [기존]
                                              └─ [축4 odiff base.png cur.png] exit 0/21/22  [신규 boolean 게이트]
                                                 (캡처 = 이미 의존 중인 Playwright screenshot)
```

---

## OD/OCD 대비 *새로 얻는 것* (중복 제거, 델타만)

| 축 | OD/OCD 가 한 것 | 이번 조사로 새로 얻는 것 |
|---|---|---|
| 축1 | OD: 매 CLI 마다 ad-hoc `agents.ts` 어댑터 + 직접 권한/프리뷰 레이어 | **ACP 한 계약**으로 어댑터 제거(swappable backend) + `session/request_permission`·`fs/*`·`terminal/*` *표준* 권한 브로커링. 실행 데몬은 goose `goosed`(production Rust) / continue `cn serve` 로 베껴 적응 |
| 축2 | OD: srcdoc 정적 프리뷰 / OCD: Electron 렌더 | **별-origin 번들 iframe(Sandpack, srcdoc 보다 강한 격리)** + **토큰 스트리밍 → 점진 렌더(onStreamPart)** + **JSX 동적 평가(renderify)** — OCD 가 안 다룬 "생성 중 부분 렌더" |
| 축3 | (대응물 없음 — 둘 다 디자인 도구) | 실험 추적 면 자체가 신규. 단 *함정 회피*가 수확 — 통째 서버 5종 탈락시키고 **계약+엔진 조립**(Trackio 스키마 + uPlot)으로 데몬 0 라이브 tail |
| 축4 | OCD: boolean *parity*(구조 동등) 검증 | parity 를 **픽셀·레이아웃 비주얼 회귀로 확장**(odiff `21`=layout 붕괴 vs `22`=pixel 차 분리) + 정의→manifest 를 **anthropic 공식 plugin 규격에 정렬**(외부 카탈로그 호환) — OD/OCD 엔 없는 표준화 |

---

## 채택 리스크 요약 (1픽 기준)

- **ACP(축1)**: v1 stable + v2 draft 동시 진화 → 버전 추적 부담. 엔진이 아니라 *에이전트는 내가 호스팅/어댑트*(claude code 는 Zed SDK 어댑터 경유). ⭐3.5k 는 프로토콜이라 절대수 오해 소지(crate 누적 ~2.7M downloads·SDK 어제 publish 가 진짜 신호).
- **Sandpack(축2)**: push 2025-04 로 다소 정체 + 번들러 MB 급 무게 → 단순 HTML 1장엔 과함(그 경우 renderify 경량 경로). origin 분리 self-host 운영 부담.
- **Trackio+uPlot(축3)**: Trackio 신생(2025)·계보 UI 약함 → *스토리지 계약만* lift 하면 리스크 낮음(코어 <3000줄 통독 현실적). uPlot 은 다운샘플·비교 UI 직접 구현(부담 작음).
- **gray-matter+odiff(축4)**: 둘 다 안정 소형 MIT — 리스크 사실상 0. 단 plugin.json 규격은 진화 중이라 버전 고정 필요. awesome-design-md 92k 는 *큐레이션 리스트* 인기지 코드 의존이 아님(규격만 차용).

## 죽은/탈락 후보 (채택 금지 — 명시)

- **cody-public-snapshot**: archived=true(2025-08 동결), live 는 private → 보안 패치 0, ACP 가 흡수. **채택 금지.**
- **클라우드 sandbox 3종**(e2b 클라우드 의존·WebContainer 런타임 클로즈드+상용 유료·val.town 플랫폼 배포 종속): local-first·라이선스 렌즈 탈락.
- **통째 tracking 서버**(aim·ClearML·wandb 대시보드(클로즈드)·MLflow UI·omniboard(2023 정체)): 임베드 불가.
- **BackstopJS**: 20개월 무 push + 무거움, playwright+odiff 상위호환. **chromatic**: diff 가 클라우드 SaaS → 렌즈 위반.

---

## 다음 파이프라인

이 조사는 *field intelligence*(어떤 OSS 부품을 어떻게 lift 할지)다. 실제 빌드는 spec → code 로 인계:

- **권장 명령**: `/autopilot-spec --mode app "worklog 디자인/실험 스튜디오 — 축1 ACP 브리지 + 축2 Sandpack 프리뷰 + 축3 Trackio·uPlot 추적 + 축4 gray-matter manifest·odiff 검증 게이트"`
- spec 에서 확정할 비자명 결정: (1) ACP 어댑터를 worklog-board(Next.js) 안 route 로 둘지 별 daemon 으로 둘지 (2) Sandpack self-host bundler 운영 위치 (3) `_RUNLOG`→Trackio 스키마 매핑(특히 parent 링크→lineage) (4) odiff baseline 디스크 레이아웃.
- 코드 단계는 spec 확정 후 `/autopilot-code --mode dev` (spec/ 자동 인지).

> 경계: 본 보고서는 분석에서 도출된 high-level 부품 선정이다. 실제 spec·구현은 autopilot-spec / autopilot-code 로 인계된다.
