# §doc — Word / HWP / markdown prose

> autopilot-draft `--mode doc` 의 본문 구조 + 강제 룰. `common.md` (§Common) 의 룰도 모두 적용.

doc mode 는 본문 구조가 _사용자 template / venue format spec_ 이 결정한다. 본 파일은 _genre 별 기본 가이드_ 만 — 실제 산출은 task description 의 자연어 genre 의도 + `analysis_project/doc/{matching}/formats/` 의 사용자 template 우선.

## 공통

- audience-driven 톤 / 시제 — 한국 기관 · 위원회 · 산학협력단 → 한국어, international → 영문. 시제는 genre 따라 (보고 = 과거, 제안 = 미래, rebuttal-response = 시제 혼합).
- 절 구조는 사용자 template 따라 가변. template 없으면 generic fallback.
- 정량 metric 있으면 표.

## doc — 기술 보고서 / mid-report / post-mortem / quarterly

사용자 template (회사·기관·연구실) 우선. template 없을 때 generic fallback — Executive Summary / 배경 / 방법 / 결과·분석 / 토론 / 권고 / Appendix.

- _시간 흐름 자산_ 은 "snapshot YYYY-MM-DD 시점" 명시 (재학습 / 추가 보고 cycle 대비).
- _post-mortem_ — 시간순 사건 / root cause / fix / preventive measure 구조.

## doc — grant proposal / 사업 제안서

기관 template 우선 (NRF / NSF / Horizon / 산학협력단 등 — 기관별로 page limit · required section · evaluation criteria 가 다르므로 `analysis_project/doc/{matching}/formats/` 사전 등록 강하게 권장). template 없을 때 generic fallback — motivation / approach / preliminary results / timeline + milestone / budget / impact / risk.

## doc — rebuttal-response (OpenReview 응답)

venue rebuttal template 우선 (length limit · sub-type — meta-only / reviewer-dialogue / response-with-revision 등). template 없으면 사용자에게 prompt.

기본 가이드: reviewer 별 point-by-point 응답 (acknowledgment → core argument → evidence → conclusion). 모든 reviewer point 에 응답 필수 (누락 = critical error).

> _camera-ready 본문 통합_ 은 본 절이 아니라 `paper.md` 의 _Natural-integration rule_ 로. rebuttal 응답과 본문 통합은 다른 장르.

## doc — peer review 작성

venue review form **MANDATORY** — `analysis_project/doc/{matching}/formats/` 부재 시 pre-flight abort. venue 별 변형 (OpenReview / ACL ARR / IEEE conference / journal 등) 이 매년 바뀌므로 built-in preset 없음.

기본 가이드: score 는 paper 본문의 구체적 evidence 로 정당화 (section / figure / table cite). hostile 톤 회피, professional + constructive.
