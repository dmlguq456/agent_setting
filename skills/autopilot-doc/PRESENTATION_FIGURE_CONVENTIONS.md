# Presentation Figure & Tone Conventions

> autopilot-doc presentation mode (특히 기존 PPT 본문 일부 보강하는 cheatsheet variant) 에서 figure 생성 / draft 작성 시 적용. SKILL.md presentation 섹션이 본 파일을 link.
>
> 본 conventions 는 2026-05-20 DSC 중간보고 cheatsheet 세션에서 사용자 명시 교정으로 확립.

---

## 1. Figure 안 텍스트 최소화

**원칙**: figure 는 패턴 보기, 수치·해석은 draft 본문 표로. figure 안에 글이 많으면 청중이 글 읽느라 그림을 못 봄.

- 긴 한국어 suptitle / subplot title 금지 → 짧은 token 라벨 박스 (`target` · `mix` · `output` · `4 ch` · `array1` 등)
- figure 안 수치 분석 박스 (`ratio=1.02× / corr=0.9` 같은) 금지 → 본문 표로 분리
- caption 은 한 줄 — figure 가 무엇을 보여주는지만. 해석은 본문 bullet
- informal/conversational 단어 (`촘촘`, `잘 보임` 등) 금지 — administrative neutral 톤

## 2. Spectrogram scale

여러 신호 비교 시 absolute dB scale 은 약한 신호가 안 보임. 비교군의 **공통 peak 를 0 dB 로 정규화** 한 뒤 동일 dB scale 사용. dynamic range 는 신호 특성에 맞춰 좁힘 (보통 −80 ~ 0 또는 −60 ~ 0). colormap 은 perceptually uniform 한 magma / viridis.

## 3. RMS profile

매끄러운 trajectory 와 spike 가시성 사이의 균형을 위해 짧은 window + overlap (대략 50 ms window / 25 ms hop) 사용. 1 s window 는 거칠어 전체 overview 에만, 25 ms window 는 너무 spiky.

y-axis 는 spike 에 끌려가지 않게 **p95 기준 robust limit** 으로 설정 (raw max 사용 금지). 비교 패널 간 axis 통일.

## 4. 청중 친화적 단위 변환

raw audio engineering 단위 (int16 RMS, linear amplitude) 는 비전공자에게 안 와닿음. 발표 자료에서는:

- linear RMS → **dBFS** 또는 **% of full-scale** 또는 **배수 (X×)** 로 변환
- 두 신호 비율 비교 시 dB 차이 + 배수 함께 표기 (예: "약 22 dB ≈ 12 배")

## 5. 기존 발표 deck 톤 미러

cheatsheet variant 는 기존 deck 의 직접 후속이므로, 신규 슬라이드의 헤더 / bullet 구조 / 결론 형식이 기존 deck 과 일치해야 함. pre-flight 단계에서 기존 PPT 텍스트 추출 (python-pptx 등) → 톤 파악 → 새 슬라이드 첫 페이지가 기존 deck 마지막 placeholder 의 자연스러운 연결.

## 6. Asset 활용

사용자가 준비한 자료 (sample wav, viz, manifest 등) 를 한두 그림으로 끝내지 말고 풍부한 multipanel + 다양한 케이스로 활용. 4~5 페이지 cheatsheet 면 그림 7~10 장이 일반적.

## 7. Path 컨벤션

markdown image embed 는 **draft 위치 기준 상대 경로**. absolute path 는 viewer / 환경에 따라 안 보임.

## 8. Audio sample link

발표 자료에 audio 신호 비교가 있으면 그림에 대응되는 wav 를 **페이지 단위로 zip 묶어 제공** + draft 본문에 `[label](path)` 형식 markdown link. 신호 진폭이 작아 청취 어려우면 동일 scalar 로 정규화 증폭 (상대 비율 보존). zip 은 일반적으로 페이지당 30~50 MB 정도.

## 9. Draft 작성 순서

plot 먼저 생성 → 사용자에게 검토용 제출 → 수정 요청 반영 → 그 후 본문 작성. 본문 먼저 쓰고 잘못된 plot 임베드하면 본문 수치 / 해석도 함께 다시 써야 해서 비용 큼.

## 10. 적용 범위

- autopilot-doc presentation mode (full deck / cheatsheet variant)
- refine-doc / audit 으로 presentation artifact 수정·점검 시 본 룰 검사
