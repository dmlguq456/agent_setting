# qa-intensity-unify — Spec (PRD)

> mode: **library** (하네스 계약 문서 — autopilot 파이프 옵션 축 개정) · 작성 2026-07-10 · v1
> 컴포넌트: `agent_setting` repo 의 **`--qa` 독립 축 폐지·intensity 완전 파생 일원화**. `spec/stage-dispatch/`(분사 토폴로지)·`spec/harness-layer-sync/` 와 독립 청사진 — 이 폴더가 자체 SoT.
> 입력(1순위 근거):
> - **사용자 결정 (2026-07-10 확정)**: "qa 가 따로 있어야 하나 싶네? 어차피 skill 자체의 intensity 자체가 있으니까 qa 는 그냥 자연스럽게 거기에 따라가는 게 맞지 싶어서.. 전체적으로 손봐주는 걸 다음 사이클로."
> - **선행 결정 계승** (DB `decision_74ca88` — 모순 아님, 진화): "검증 프로세스는 제거하지 않는다. intensity=pipeline shape/ceremony/dispatch depth, qa=verify rigor override 로만. 기본 verify 강도는 intensity 매핑." → 본 spec 은 그 잔존 명시-override 축까지 폐지. **검증 프로세스 유지 원칙 불변.**
> - **현행 실측** (2026-07-10 census): CONVENTIONS §1:48(--qa "compatibility and explicit assurance override" 잔존)·§1:71(명시 --qa 부재 시 intensity→qa 파생 이미 명문: direct→none/light·quick→quick·standard|strong→standard·thorough→thorough·adversarial→adversarial)·§1:75-76(external adversary = qa=adversarial 바인딩)·§1:105. 표면 분포: core 4·skills 46·adapters/claude/bin 2·codex 38·opencode 34·hooks 1·utilities 1·tools 6 파일(어댑터 다수 = projection 파생). wrapper `--qa` 필수 인자·jobs.log `qa=` 필드·fleet `check:<qa>` 라벨.
> 본 문서는 청사진(PRD). 구현은 autopilot-code (산출물 `plans/`). 지침 파일 자체는 본 spec 이 수정하지 않는다 — 방향만 확정.

## 0. 한 줄

**사용자-facing `--qa` 축을 폐지하고, 검증 rigor 를 intensity 파생 매핑(CONVENTIONS §1:71) 단일 경로로 일원화한다.** 검증 프로세스·스테이지는 하나도 제거하지 않는다 — "얼마나 깐깐하게"의 결정권만 intensity 한 축으로 접는다. 현행 계약이 이미 "파생이 기본, --qa 는 호환 override"까지 와 있으므로, 본 개정은 그 잔존 축을 접는 마무리 수순이다.

## 1. 배경 — 왜 접나

- **사용자 문제의식**: intensity 가 이미 파이프 shape 를 정하는데 qa 축이 따로 있어 이중 결정. 실사용에서 qa 는 사실상 intensity 를 따라간다(오늘 stage-dispatch Phase 2·3 사이클 전부 qa=intensity 등가로 지정).
- **이중 정의 실증**: `adversarial` 이 qa tier 와 intensity tier 양쪽에 존재 — 옵션 조합 공간에 의미 없는 조합(예: intensity=quick + qa=adversarial 은 §1:48 이 이미 금지)을 만들고, 호출·컨펌·wrapper·row 표기 전부에 축 하나를 더 끌고 다닌다.
- **선행 결정과의 관계**: 74ca88 은 "qa 는 shape 를 못 고른다, verify rigor 만"으로 이미 축을 반쯤 접었다. 본 spec 은 나머지 반(명시 override 표면)을 접는다. 유지되는 것 — 검증 프로세스 자체, intensity→rigor 파생 테이블(§1:71, SoT 로 승격).

## 2. 결정

### QA-1 — 축 폐지·완전 파생 (채택)
사용자-facing `--qa` 플래그 폐지. verify/plan-check/독립 리뷰 rigor 는 **CONVENTIONS §1:71 파생 매핑 테이블이 유일 경로**이자 단일 출처(SoT 승격). 검증 프로세스·스테이지 제거 없음(74ca88 계승) — quick 의 plan-check-lite/verify-lite, standard+ 의 code-test, thorough+ 의 다축 리뷰 전부 그대로, 선택권만 intensity 로 일원화.

### QA-2 — high-stakes 재매핑 + adversarial 이중 정의 해소 (채택)
- high-stakes 신호(_신중히/꼼꼼히/camera-ready/submission·PR open 직전_)의 자동 상향 = qa 상향 → **intensity 상향**(standard→strong/thorough/adversarial)으로 재매핑. adapter bootstrap §0(B) 문구 개정.
- qa tier 로서의 `adversarial` 제거 — **external adversary 요구(§1:75-76 검증 가능성 게이트 포함)는 intensity=adversarial 로 바인딩 이전**. 명시 intensity=adversarial 인데 외부 engine 불가면 loudly fail, 자동 상향분은 thorough 로 fallback + 보고 — 기존 의미론 그대로 축만 이동.
- `analyze-user` 의 "항상 adversarial 고정"도 intensity 표현으로 이전.

### QA-3 — 표면 정리 (채택, 하위호환 판단 포함)
| Surface | 개정 방향 |
|---|---|
| autopilot-*·sub-skill SKILL.md argument-hint·defaults | `--qa` 제거 + "rigor 는 intensity 파생(§1:71)" 한 줄. 어댑터 projection 은 sync 기제 일괄 |
| CONVENTIONS §1 | "compatibility and explicit assurance override" 절 폐지, 파생 테이블을 SoT 로 재서술. §1:105 external adversary role 은 intensity=adversarial 참조로 |
| WORKFLOW §1.1 | "choose intensity before --qa" → intensity 단일 축 서술 정합 |
| dispatch wrapper 3종 (claude dispatch-headless·codex/opencode preflight) | `--qa` 인자 optional/derived 강등 — 미지정 시 intensity 에서 파생. **jobs.log pipe `qa=` 필드는 유지**(fleet collector·기존 row 하위호환, 값=파생값 기록) |
| adapter bootstrap §0(B)·§0(C) 3종 | high-stakes → intensity 상향 문구·분사 옵션 예시 정리 (core-first) |
| drill fixture·docs 의 `--qa`/qa= 사용처 | 파생값으로 정합 (drill 러너 loops/** 자체는 타 세션 소유 — 케이스 파일만) |
| fleet `check:<qa>` 라벨 | **범위 외**(tools/fleet 타 세션 소유) — qa= 필드가 유지되므로 표시는 계속 동작, 라벨 의미 변화만 handoff 통지 |

### QA-OPEN-1 — 독립 rigor override 의 실존 반례 (미결)
shape 와 독립으로 rigor 만 올릴 실존 자리(후보: 문서 파이프의 fact-check rigor, autopilot-spec update quick + 무거운 검증 조합)가 구현 사이클 census 에서 확인되면 **그 자리 한정 내부 전용 파라미터**(표면 비노출, capability 정의 안 고정값)로 잔존. 반례가 없으면 완전 폐지. 추측으로 남기지 않고 census 로 판정.

## 3. 구현 phase (autopilot-code, 본 v1 입력 — 다음 사이클)

1. **core-first**: CONVENTIONS §1 재서술(파생 테이블 SoT 승격·adversarial 바인딩 이전) → WORKFLOW §1.1 → adapter bootstrap 3종 §0(B).
2. **skills 표면**: 전 SKILL.md argument-hint·defaults·본문 qa 참조 → intensity 파생 서술. sub-skills(code-*/draft-*/design-* 등) 동형.
3. **wrapper 3종**: `--qa` optional/derived (jobs.log `qa=` 필드 유지, 값=파생). 파생 로직은 wrapper 가 아니라 호출측 계약(§1:71 테이블) — wrapper 는 미지정 시 파생값 계산만.
4. **QA-OPEN-1 census** → 판정 + drill fixture 정합 + projection sync + 회귀(기존 스위트 + boundary check).
- 순서 제약: 현재 진행 중인 `sd15-adapter-parity` 사이클 수확 **후** 착수(양쪽 다 wrapper·adapter 문서를 만져 파일 겹침). 제외: `loops/**`·`tools/fleet/**`.

## 4. 의미↔규칙 경계 체크 (DESIGN_PRINCIPLES §0.7)

- **규칙 구간**: intensity→rigor 파생 테이블(결정론 매핑)·wrapper 파생 계산·jobs.log 필드 형식·adversarial 검증 가능성 게이트(외부 engine 실증 없으면 fail/fallback) — 전부 코드/테이블로 강제 가능.
- **의미 판단 구간**: (1) 발화에서 intensity 선택(기존과 동일 — 요청 shape 판단) (2) high-stakes 신호 감지(기존 qa 상향 판단과 동일 부담, 축만 이동) (3) QA-OPEN-1 반례 실존 판정(census 근거).
- **충돌**: 없음 — 축 폐지로 "의미 판단 두 번(shape + rigor)"이 한 번으로 줄어 §0.5 결정론-first 에 순방향. 검증 프로세스 유지(74ca88)와도 양립 — 제거되는 것은 프로세스가 아니라 옵션 표면.
