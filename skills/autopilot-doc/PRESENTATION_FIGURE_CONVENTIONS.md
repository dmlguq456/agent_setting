# Presentation Figure & Tone Conventions

> autopilot-doc presentation mode (특히 기존 deck 본문 일부 보강하는 cheatsheet variant) 에서 figure 생성 / draft 작성 시 적용. SKILL.md presentation 섹션이 본 파일을 link.
>
> 본 conventions 는 사용자 명시 교정으로 확립된 *domain-agnostic 원칙*. 특정 분야 (audio, image, vision 등) 의 구체 단위·플롯 종류·툴 이름 등은 의도적으로 제거 — 어떤 분야의 발표 자료든 적용 가능하도록.

---

## 1. Figure 안 텍스트 최소화

**원칙**: figure 는 패턴 보기, 수치·해석은 draft 본문 표로. figure 안에 글이 많으면 청중이 글 읽느라 그림을 못 봄.

- 긴 suptitle / subplot title 금지 → 짧은 token 라벨 박스로 panel 식별
- figure 안 수치 분석 박스 (ratio·correlation 등 비교 수치) 금지 → 본문 표로 분리
- caption 은 한 줄 — figure 가 무엇을 보여주는지만. 해석은 본문 bullet
- informal / conversational 단어 금지 — administrative neutral 톤

## 2. 비교 plot 의 공통 scale

여러 신호·이미지·분포를 같은 figure 에서 비교할 때 각 panel 을 자체 normalize 하면 절대 진폭 비교가 깨지고, absolute scale 만 쓰면 약한 신호가 안 보임. **비교군 전체의 공통 peak 를 기준 (0) 으로 정규화** 한 뒤 동일 scale 적용. dynamic range 는 데이터 분포에 맞춰 좁힘.

## 3. 시계열 plot 의 window / y-limit

dense 한 window + overlap 으로 trajectory 와 spike 양쪽 가시성 확보. 너무 큰 window 는 거칠고 너무 작은 window 는 산만하므로 데이터 길이에 비례한 적절한 값 선택.

y-axis 는 spike 에 끌려가지 않게 **percentile 기반 robust limit** (예: p95 ×1.15) 사용. raw max 사용 금지. 비교 패널 간 axis 통일.

## 4. 청중 친화적 단위 변환

raw engineering 단위 (도구가 내부에서 쓰는 수치) 는 비전공자에게 안 와닿음. 발표 자료에서는 **비율 / 로그스케일 / percentage / 익숙한 다른 단위** 로 변환해 표기. 두 값 비교 시 절대값 + 상대값 (배수 등) 함께 명시.

## 5. 기존 발표 deck 톤 미러

cheatsheet variant 는 기존 deck 의 직접 후속이므로, 신규 슬라이드의 헤더 양식 / bullet 구조 / 결론 형식이 기존 deck 과 일치해야 함. pre-flight 단계에서 기존 deck 의 텍스트 추출 → 톤 파악 → 새 슬라이드 첫 페이지가 기존 deck 마지막 placeholder 의 자연스러운 연결.

## 6. Asset 활용

사용자가 준비한 자료 (sample data, intermediate artifacts 등) 를 한두 그림으로 끝내지 말고 다양한 케이스 + multipanel 로 풍부하게 활용.

## 7. Path 컨벤션

markdown image / link embed 는 **draft 위치 기준 상대 경로**. absolute path 는 viewer / 환경에 따라 안 보임.

## 8. 보조 자료 (raw asset) 링크

figure 에 대응되는 **원본 raw asset** (audio / video / data 파일 등) 이 청중 검토에 필요하면 **페이지 단위로 zip 묶어 제공** + draft 본문에 `[label](path)` 형식 markdown link. 진폭 / 크기가 비교하기 어려운 경우 동일 scalar 정규화로 가독성 확보 (상대 비율 보존).

## 9. Draft 작성 순서

plot 먼저 생성 → 사용자에게 검토용 제출 → 수정 요청 반영 → 그 후 draft 본문 작성. 본문 먼저 쓰고 잘못된 plot 임베드하면 본문 수치 / 해석도 함께 다시 써야 해서 비용 큼.

## 10. 적용 범위

- autopilot-doc presentation mode (full deck / cheatsheet variant)
- refine-doc / audit 으로 presentation artifact 수정·점검 시 본 룰 검사
