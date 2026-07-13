# plan-review r1 — skill-design-refactor PRD v1 (2026-07-13, 품질관리팀 plan-review, intensity=thorough)

대상: `spec/skill-design-refactor/prd.md` + `pipeline_state.yaml` (반영 전 v1 초안). 발견 반영 완료 — 반영 방식은 각 항목 뒤 `→`.

## 🟠 Major

- **M1. Plan Resolution "6개 물리 복제" 과대 카운트** — 실제는 code-execute/refine/report/test **4개**(code-plan 은 Pre-Check 사용, 블록 없음 — per-skill :144). authority 후보로 지목한 `autopilot-code/SKILL.md`에도 블록 없음(canonical 서술은 `autopilot-code/references/arguments-and-decisions.md:95`).
  → §3.1 표·SD-2 를 "4개(code-execute/refine/report/test, SKILL.md+README.md) pointer, authority=`autopilot-code/references/arguments-and-decisions.md`"로 정정. 완료 기준도 README.md 스캔 포함하도록 `grep -rln "keep in sync" skills/*/SKILL.md skills/*/README.md`로 확장.
- **M2. authority pointer target 미실존** — `autopilot-code/SKILL.md#plan-resolution` 앵커가 실제로 존재하지 않음.
  → pointer 예시를 `autopilot-code/references/arguments-and-decisions.md#plan-resolution`로 교체.

## 🟡 Minor

- **m1/m2. Language Rule·`<artifact-root>` 인용 라인 번호 부정확** — authority 판단 자체는 유효(공유 reference / CONVENTIONS §5). 근거 라인은 구현 사이클(`/autopilot-code --mode refactor`)에서 grep 재확인으로 자연 교정 — 이번 라운드는 반영 skip(저영향, 구현 착수 시 재확인 의무만 남김).
- **m3. `pipeline_state.yaml` D1 이 decisions_locked(SD-5)와 open_decisions 양쪽에 이중 서술** → open_decisions 의 D1 을 "게이트 trial-flip 결과에 따른 최종 범위"로 재정의해 SD-5(방향 잠정 확정)와 비모순화.
  → 반영 완료.
- **m4. Cluster 1 검증 게이트 절차의 순환성** — pre-flip 점검만으로는 disable-model-invocation 하 동작을 관측 불가.
  → §3.3 을 "희생 스킬 1개 trial-flip(draft-strategy=(a), code-test=(b)) → 관측 → 실패 시 revert" 절차로 명문화.
  → 반영 완료.
- **m5. grep 완료기준이 README projection 복제를 못 잡음** — M1 반영에 흡수(README.md 스캔 포함).
  → 반영 완료(M1 처리에 통합).

## 정확·양호 확인 (반영 불요)

- 고임팩트 수치(autopilot-design 315줄, 순수 sub-skill 13개, 시각검증 loop 3중, P6 line count)는 audit 원문과 전부 일치.
- Cluster 순서(2→3→1)·완료기준의 checkable 성격·Decision D1~D5 가 사용자 확정 입력(4축 적극 채택 + 원칙-하네스 충돌 유지)과 모순 없음.
- `dispatch-profiles` 선례와 포맷 동형(frontmatter·pipeline_state 필드·§의미↔규칙 경계 체크).

## 판정

M1·M2 반영 완료 → **블로커 없음, 커밋 가능**.
