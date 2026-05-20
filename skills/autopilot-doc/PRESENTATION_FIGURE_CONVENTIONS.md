# Presentation Figure & Tone Conventions

> autopilot-doc presentation mode (특히 기존 deck 본문 일부 보강하는 cheatsheet variant) 에서 figure 생성 / draft 작성 시 적용. SKILL.md presentation 섹션이 본 파일을 link.
>
> *Domain-agnostic 원칙*. 분야 specific 단위·플롯 종류·툴 이름은 의도적으로 제거.

---

## 0. 슬라이드 분량 제한 (강제)

PPT 슬라이드 한 장의 텍스트 분량은 엄격히 제한:

- bullet **최대 5 ~ 6 줄**
- 한 줄 **1-2 키워드** (대략 10 단어 이하, 풀 문장 지양)
- **그림 / 표가 슬라이드 면적의 ≥ 60 %** 차지
- 표는 행 ≤ 6, 열 ≤ 5 정도 — 그보다 크면 별도 슬라이드 분리

> note: 16:9 공간은 생각보다 작음. cheatsheet markdown 본문도 동일 기준 — 한 페이지의 bullet 수와 길이가 PPT 슬라이드 한 장 분량을 넘으면 안 됨. 긴 설명·수치 정당화·detail 은 **발표자 노트 / backup 슬라이드** 로 분리. draft 작성 시 매 페이지마다 "이게 슬라이드 한 장에 들어가는가" 자가 검사 필수.

## 1. Figure 안 텍스트 최소화

긴 suptitle / subplot title 금지. 짧은 token 라벨 박스만 사용. 수치·해석은 figure 가 아닌 draft 본문 표로.

> note: caption 은 한 줄 — figure 가 무엇을 보여주는지만. informal / conversational 단어 금지 (administrative neutral 톤).

## 2. 비교 plot 의 공통 scale

비교군 전체의 공통 peak 를 기준 (0) 으로 정규화 후 동일 scale 적용.

> note: 각 panel 자체 normalize 는 절대 진폭 비교가 깨지고, absolute scale 만 쓰면 약한 신호가 안 보임. dynamic range 는 데이터 분포에 맞춰 좁힘.

## 3. 시계열 plot 의 window / y-limit

dense window + overlap 으로 trajectory 와 spike 양쪽 가시성 확보. y-axis 는 percentile 기반 robust limit 사용 (raw max 금지).

> note: 너무 큰 window 는 거칠고 너무 작은 window 는 산만 — 데이터 길이에 비례한 값 선택. 비교 패널 간 axis 통일.

## 4. 청중 친화적 단위 변환

raw engineering 단위 (도구가 내부에서 쓰는 수치) → 청중에게 익숙한 단위 (비율 · 로그스케일 · percentage 등) 로 변환 표기.

> note: 두 값 비교 시 절대값 + 상대값 함께. 비전공자 의사결정자가 청중에 포함되면 특히.

## 5. 기존 deck 톤 미러

cheatsheet variant 의 헤더 양식 / bullet 구조 / 결론 형식은 기존 deck 과 일치.

> note: pre-flight 단계에서 기존 deck 텍스트 추출 → 톤 파악 → 새 슬라이드 첫 페이지가 기존 deck 마지막 placeholder 의 자연스러운 연결.

## 6. Asset 풍부 활용

사용자가 준비한 자료 (sample data, intermediate artifacts 등) 를 다양한 케이스 + multipanel 로 활용.

> note: 한두 그림으로 끝내면 발표 자료로서 약함 — 게으른 자료 X.

## 7. Path 컨벤션

markdown image / link embed 는 draft 위치 기준 상대 경로.

> note: absolute path 는 viewer / 환경에 따라 안 보임.

## 8. 보조 자료 (raw asset) 링크

figure 에 대응되는 원본 raw asset 은 페이지 단위 zip 묶어 제공 + draft 본문에 `[label](path)` 형식 link.

> note: 진폭 / 크기가 비교하기 어려운 경우 동일 scalar 정규화로 가독성 확보 (상대 비율 보존).

## 9. Plot 먼저, draft 나중

plot 생성 → 사용자 검토 제출 → 수정 반영 → 그 후 draft 본문 작성.

> note: 본문 먼저 쓰고 잘못된 plot 임베드하면 본문 수치 / 해석도 함께 다시 써야 해서 비용 큼.

## 10. 적용 범위

autopilot-doc presentation mode (full deck / cheatsheet variant) · refine-doc / audit 으로 presentation artifact 수정·점검 시 본 룰 검사.
