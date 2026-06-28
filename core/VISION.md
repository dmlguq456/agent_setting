# VISION.md — 북극성 (먼 미래 목표)

> 1페이지 vision 메모. 정식 PRD 아님 — 방향 합의 후 `autopilot-spec` 으로 승격한다.
> 근거: artifact root 의 `research/hermes-agent/` (Hermes Agent 벤치마킹) + `07_security.md` (보안 체크리스트).
> 작성 2026-06-15.

## 한 줄

지금의 *세션-안 작업 파이프*(skills·agents·hooks·loops)를, **사용자가 설치만 하면 켜지는 자율 에이전트** — 처음엔 Claude Code **플러그인**, 더 나아가 **설치 프로그램** — 으로 졸업시킨다. 단, 우리의 거버넌스 불변식(_루프 출구는 제안까지, 결정은 사용자_)을 끝까지 깨지 않는다.

## 왜 (벤치마킹 동기)

Hermes Agent 벤치마킹 결론: 우리와 Hermes 는 self-improving agent 의 **상보적 절반**이다.

- **우리가 이미 가진 것 (지킬 것)**: 하드 순서 게이트·artifact-guard hook·적대 N-vote 검증·drill/study 메타루프·산출물 버전 거버넌스·7팀 분업. → *신뢰성·검증가능성*.
- **우리에게 없는 것 (배울 것)**: 자동 cross-session recall(최대 갭)·런타임 자기개선 초안·시간기반 lifecycle·persistent 실행·패키징. → *자동화·접근성·배포*.

북극성은 "Hermes 의 자동화 속도를 빌리되 우리 결정 게이트 *앞단*에 붙인다" — 즉 **자동 초안은 도입, 자동 적용은 거부**.

## 설계 원칙 (협상 불가)

1. **메커니즘은 자동, 결정은 사람.** 모든 자율 동작의 출구는 *제안/초안*. 적용·삭제·배포 같은 비가역은 사용자 게이트를 통과한다.
2. **거버넌스 우선.** 순서 게이트·소유스킬 수정·버전 트래킹·적대 검증은 자율성이 커질수록 *더* 강화한다(완화 아님).
3. **로컬·최소 의존.** 외부 서비스 직접 의존은 기본 거부(개념만 차용). 데이터는 로컬에 남긴다.
4. **메타-시험 유지.** 시스템이 자기 지침을 시험(drill)·외부 대조(study)하는 층은 플러그인/설치본에서도 1급 기능.

## 보안 전제 (먼저 못 박는다)

자율 에이전트 = 넓은 attack surface. OpenClaw 의 1차 검증된 CVE(1-click RCE 등)와, **Hermes 본인이 "in-process 방어는 그 무엇도 containment 가 아니다"라고 인정**한 사실을 출발점으로 삼는다.

- 플러그인/설치본은 `07_security.md` 의 **OWASP ASI01–10 + LLM Top10 체크리스트를 필수 입력**으로 한다.
- 핵심 위협: 임의 shell 실행·prompt injection·supply chain(skill/plugin)·credential 노출·게이트웨이 노출.
- 원칙: *containment(샌드박스/격리)* 없는 자율 실행은 배포하지 않는다. in-process 가드(approval·redaction·scan)는 보조일 뿐 격리의 대체가 아니다.

## Phased 로드맵 (먼 미래, 비확정 스케치)

| Phase | 목표 | 산출 형태 | 게이트 |
|---|---|---|---|
| **P0 — 현 세팅 강화** (진행 중) | Hermes 갭 이식(T1~T6): 자동 recall·자기개선 초안·lifecycle·multi-pass | `<agent-home>` 내부 (지침·loops·skills) | drill 회귀 통과 |
| **P1 — 패키징/플러그인화** | 흩어진 부품을 *설치 가능한 단위*로 — 표준 plugin 매니페스트·의존 선언·설정 스캐폴드 | Claude Code plugin (marketplace 배포 가능 형태) | 보안 체크리스트 + 재현 설치 검증 |
| **P2 — 설치 프로그램** | 비전문가도 설치만으로 전체 세팅을 부팅 — installer + 격리 실행 환경 + 안전 기본값 | 독립 설치본 | containment 검증 + 외부 보안 검토 |

## 비목표 (Non-goals)

- 모델 weight 자가학습(Atropos 류) — 우리는 모델 *소비자*다.
- 승인 없는 self-edit·자동 배포 — 불변식 정면 위반.
- persistent multi-channel gateway 를 *지금* 도입 — 현 쓰임(논문·실험·코드 파이프)과 불일치, P1 이후 재검토.
- 외부 메모리 backend(Honcho 등) 직접 통합 — 개념만 차용.

## 다음 단계

P0 이식이 안정되고 방향이 합의되면 → `/autopilot-spec` 으로 P1 플러그인 PRD 작성(본 vision + research + 07_security 가 입력). 그 전까지 본 문서가 north-star anchor.
