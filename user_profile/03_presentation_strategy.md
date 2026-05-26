---
aspect: presentation
last_init: 2026-05-26
version: 2.5
---

# 발표 자료 (Slide) 전략

자료팀 (presentation 자리) / 디자인팀 / 편집팀 default 참조. 사용자 발표 자료 다섯 자리 (박사 청구심사 / 학회 NeurIPS·ICASSP / 정부과제 정부과제·기초연구 중간발표·Seed FastTrack / 산업 세미나 기업 / 강의 Deep Learning Speech Processing) 100 장 이상 검토 결과. 각 절 불릿마다 _slide 자체 anchor_ (예: `박사학위_slide-21.png`, `NeXt-TDNN_slide-04 표지`) 를 같이 박아 ground-truth lookup 이 가능.

## 1. 슬라이드 layout

**마스터 — 공통 골격 + 자리별 변형**:
- 우상단 얇은 빨간 띠 + 흰 작은 글씨 `Dept. of Electronic Engineering, Sogang University / N` (학과명 + 슬라이드 번호) — 박사·학회·강의 본문 default (`박사학위_slide-08.png`, `SepReformer_slide-05`).
- 좌하단 IIPLab 로고 (분홍·자주 큐브 + 보라 4 줄 텍스트 `Intelligent / Information / Processing / Lab.`) — 모든 자리 본문 의무 (`박사학위_slide-12.png`).
- 산업 세미나만 좌하단 stamp 가 가로 한 줄 `INTELLIGENT INFORMATION PROCESSING LAB.` 회색 outline 폰트로 바뀜 — 자리 톤에 맞춘 stamp 변형 (`기업세미나_slide-03`).
- 우하단 특정대학 IHS 문장 + 한국어·영문 2 줄 stamp `특정대학 / Sogang University` (`박사학위_slide-08.png`).
- 본문 영역 좌측 정렬. 표지·단원 표지 슬라이드는 페이지 번호 라벨 생략 + 로고만 (`박사학위_slide-01.png` 표지).

**표지** — 진빨강 띠 (`#A0152A` 추정) + 흰 굵은 영문 sans-serif 타이틀 공통:
- 상단 1/3 비움 → 화면 폭 진빨강 띠 + 흰 굵은 영문 sans-serif (Open Sans 계열 bold) 타이틀 → 그 아래 저자명·이메일·소속·학회·날짜 (`박사학위_slide-01.png`).
- 학회 — 공저자 footnote (Equal contribution / Corresponding author / `*Presenter`) + 학회 공식 로고 (NeurIPS / ICASSP 2024 KOREA) 우하단 (`NeXt-TDNN_slide-01 표지`, `SepReformer_slide-01 표지`).
- 정부과제 — 한국어 위주. 상단 부제 (예: `2025 년도 차세대 유망 Seed 기술실용화 패스트트랙 단계평가 발표`) + 중앙 한국어 타이틀 + `특정대학 / ○○○ / 2025. 3. 12.` + 하단 4 기관 로고 (주관·공동·수요기업·IP-R&D) 가로 배치 (`SeedFastTrack_slide-01 표지`).
- 산업 세미나 — 한국어 minimal (`2026. 5. 13.` / `특정대학` / `박 형 민` 정자체 한 줄씩, `기업세미나_slide-01 표지`).
- 박사 — 영문 제목 + 한국어 부제 + 발표 날짜 + 저자 (`박사학위_slide-01.png`).

**본문** — H1 단원 anchor + 첫 글머리 부제 2 단계 navigation 의무:
- H1 = 같은 단원 슬라이드 머리에 반복 (`박사학위_slide-21.png` 및 `_slide-22.png` 모두 `Spatial Correlation for Multi-channel Speech`, `_slide-24.png` 및 `_slide-25.png` 및 `_slide-26.png` 모두 `Temporal Correlation for Reverberant Speech`).
- 첫 글머리 = 슬라이드 단위 부제 (`• Motivation` / `• Experiment: ...` / `• SR-CorrNet`) 큰 글씨로 박음.
- 글머리 계위 4 단계 (`•` 24-28 pt 검정 두꺼운 점 → `▪` 18-22 pt 검정 사각형 → `◦` 14-16 pt 속 빈 동그라미 → `•` 회색 작은 점). 한 슬라이드 안 글자 크기 3 단 이상 섞이지 않게 절제.
- 중앙 정렬은 Conclusion 또는 큰 수식 강조 자리만 (`SepReformer_slide-15 Conclusion`).

**단원 표지** — 화면 중앙 빨간 띠 + 흰 굵은 영문 section name:
- 박사 6 단원 모두 1 장씩 (`박사학위_slide-04 Introduction`, `_slide-13 Asymmetric Encoder-decoder for Speech Separation`, `_slide-20 Spatial Correlation`, `_slide-23 Temporal Correlation`, `_slide-27 Asymmetric TF Encoder-decoder with Correlation`, `_slide-37 Conclusion and Further Works`).
- 학회 8 분 talk 도 2 회 active (`NeXt-TDNN_slide-02 Introduction: How to Modernize TDNN?`, `_slide-07 Proposed NeXt-TDNN Architecture`, `_slide-19 Experiment`, `_slide-23 Conclusion`).
- 산업 세미나 active (`기업세미나_slide-09 Mask 기반 SE`, `_slide-18 Complex 및 Time-domain 기반 SE`).
- 정부과제 (정부과제 / 기초연구 중간발표 / Seed FastTrack) 약함 — 단계별 deliverable 표시로 대체 (`정부과제_slide-04` Gantt 자리, `기초연구_slide-03` 1·2·3 차년도 진행 자리).
- 박사 자리 단원 표지에는 띠 아래 근거 paper citation 1 줄 추가 (`박사학위_slide-23 Temporal Correlation` 띠 아래 `U.-H. Shin, J. Kim, ..., "Inter-frame correlation for deep filter estimation in speech dereverberation", ICASSP 2026 (submitted)`).

## 2. 서사 flow

**박사학위 청구심사** — 표지 → Research output (졸업 요건 충족 명시) → Contents → 단원 표지 → 본문 (Motivation → Method 수식+figure → Experiment 표) × 6 단원 → Conclusion (Progressive development) → Future Works → "감사합니다" → Reference list → Appendix 5 자리:
- 표지 `박사학위_slide-01.png` → Research output `_slide-02.png` → Contents `_slide-03.png` → 단원 표지 `_slide-04 Introduction`.
- 본문 자리 anchor = 본인 work 시기별 narrative. SepReformer (NeurIPS 2024, `_slide-13~17`) → TF-CorrNet (SPL 2025, `_slide-21~22`) → IF-CorrNet (ICASSP 2026 submitted, `_slide-24~26`) → SR-CorrNet (통합 framework, `_slide-27~36`) 의 progressive development 가 6 단원 흐름 묶음.
- Conclusion `_slide-38 Progressive development` → Future Works `_slide-39` → "감사합니다" `_slide-40` → Reference dense list `_slide-41~45` → Appendix 5 자리 `_slide-46~50`.

**학회 NeXt-TDNN (ICASSP 2024, 8 분 27 장)**:
- 표지 `NeXt-TDNN_slide-01` → 단원 표지 `_slide-02 Introduction: How to Modernize TDNN?` → 기존 연구 review 4 장 (TDNN `_slide-03` / ECAPA-TDNN `_slide-04` / Transformer `_slide-05` / ConvNeXt `_slide-06`) → 단원 표지 `_slide-07 Proposed NeXt-TDNN Architecture` → 본문 (Architecture + Rationale + Block 비교, `_slide-08~18`) → 단원 표지 `_slide-19 Experiment` → 결과 표 점진 reveal (`_slide-20~22`) → 단원 표지 `_slide-23 Conclusion` → 정리 → Future Works `_slide-25` → "Question & Answer" `_slide-27`.
- _기존 연구 review 4 장 + 본인 contribution 1 장_ 비율 — 청중을 도메인 흐름에 빠르게 안내한 뒤 본인 contribution 만 슬라이드 1 장에 압축.

**학회 SepReformer (NeurIPS 2024, 15 장)**:
- 표지 `SepReformer_slide-01` → demo (spectrogram 3 줄 + QR `_slide-02`) → Overview `_slide-03` → Motivation 1 `_slide-04` → Motivation 2 `_slide-05` → Architecture `_slide-06~08` → Effectiveness `_slide-09~11` → Visualization `_slide-12` → Overall Performance `_slide-13` → Performance vs Computations 산점도 `_slide-14` → Conclusion 3 줄 `_slide-15`.
- agenda 슬라이드 없음. 본문 영어 일관.

**정부과제** — 표지 → Table of Contents 4-7 자리 → 개요 (system architecture 도식) → 단계별 deliverable placeholder → 본문 → 단독 conclusion 약함:
- 정부과제 킥오프 — 사업 전체 plan 위주, system architecture 강조 (`정부과제_slide-02 TOC`, `_slide-03 system architecture`, `_slide-04 Gantt`).
- 기초연구과제 2 차년도 중간발표 — 1·2·3 차년도 진행 3 단 구조, 단원 표지 없음 (`기초연구_slide-03~12`).
- Seed FastTrack — 단계별 완수 deliverable 강조, IP-R&D 부각 (`SeedFastTrack_slide-01 표지 4 기관 로고`).

**산업 세미나 (기업)** — 표지 → 목차 6 장 → 로드맵 (2017~2026 timeline) → 문제 정의 (신호 모델 수식 + Task 표) → 시기별 연구 흐름 (URGENT Challenges 2024-2026) → 단원 표지 + 본문 chapter 3-4 장 → Conclusion (6 자리, TF-Restormer ICML 2026 강조) → "Q&A":
- 표지 `기업세미나_slide-01` → 목차 `_slide-02` → 로드맵 `_slide-03 timeline 2017~2026 패러다임 전환` → 문제 정의 `_slide-04 신호 모델 수식 + Task 표 6 행` → URGENT 시기별 흐름 `_slide-05~06 14 줄 dense` → 단원 표지 + 본문 chapter (`_slide-09 Mask`, `_slide-18 Complex+Time`, `_slide-25 TF dual-path`, `_slide-33 Restoration·Generative`) → Conclusion `_slide-44 6 자리 정리` → "Q&A" `_slide-45`.
- _목차 + 로드맵 + 문제 정의_ 3 장의 진입 ramp 가 산업 자리 특유. 학생·학회 자리에는 목차·로드맵 없음.

**강의 (Deep Learning Speech Processing)** — 표지 → demo (visualization 우선) → Overview → Motivation 1·2 → Architecture → Multi-loss → Ablation → Visualization → Overall Performance → Performance vs Computations 산점도:
- _결과 demo 가 motivation 보다 먼저_ 등장 — 청중이 결과부터 본 뒤 motivation 으로 들어가는 강의 호흡 (`강의_slide-02 demo spectrogram`).
- 최후 산점도로 본인 모델 위치 anchor — 청중이 슬라이드 한 장만 가져가도 본인 모델 위치 인지 가능.

## 3. 시각 결정

**색 팔레트**:
- 주 색 = 진빨강 (특정대학 색, `#A0152A` 추정) — 표지·단원 띠·헤더·강조 단어·박스 테두리. 가장 강한 시각 anchor (`NeXt-TDNN_slide-04 표지` 빨간 띠, `박사학위_slide-04` 단원 표지).
- 본문 default = 검정. 회색 = footnote / 부가 정보 / 날짜 / 산업 세미나 stamp outline 자리.
- 노란 형광 underline — 강의·학회 SepReformer 자리 본문 안 부분 키워드 강조 (`SepReformer_slide-04 Motivation 노란 underline`, `강의_slide-05 노란 underline`). 박사 자리는 노란 underline 자리에 빨강 어휘로 대체 — 두 자리의 강조 metaphor 분리.
- 빨강 진한 단어 / 굵은 어휘 = 정의·결론 핵심·본인 contribution (`박사학위_slide-28 ↳ SR-CorrNet for universal speech enhancement and separation` 빨간 굵게).
- architecture diagram block 색 코드 — Encoder 노랑 fill / Decoder 연두 fill / 부속 block 회색 또는 흰 / 화살표 검정. SR-CorrNet 같은 SepRe 계열은 Decoder orange 변형도 나타남 (`박사학위_slide-29 architecture`).
- module-level diagram — 회색·검정 outline + 흰 배경 (TF-model module 도식). 시그널 색과 emphasis 색 분리.
- 매체별 색 dictionary 다름 — paper figure (outline grayscale 위주), presentation (fill + 진빨강 anchor). [[project_user_paper_figure_style]] grayscale 룰과 발표 색 코드의 분리.

**폰트**:
- heading — 영문 sans-serif bold (Open Sans 계열 추정). 한국어 자리는 한국어 글꼴 (맑은 고딕 / Pretendard 추정).
- body — sans-serif.
- 수식 — serif Computer Modern Italic (LaTeX default). 본문 sans-serif 와 뚜렷한 시각 대비.
- footnote / citation — 작은 sans-serif 회색.

**figure 배치 — 다섯 패턴**:
- 2-column 정형 (좌 텍스트 60-65 % + 우 figure 35-40 %) — 본문 default. 좌측은 Motivation → Method 정의 → Key Insight → 수식 흐름, 우측은 직관 schematic (`박사학위_slide-21.png` 2-column).
- full-width architecture — figure 가 캔버스 60-70 % + 하단 1-3 글머리 caption (`박사학위_slide-29 SR-CorrNet 전체 도식`).
- 표 메인 슬라이드 — 부속 글머리 거의 X + 표 한두 개 가로 배치 + 데이터셋 caption 만 (`NeXt-TDNN_slide-21 Voxceleb1-O 표`).
- figure + 수식 결합 — 수식 dimensions 를 좌표 axis 로 그림 (`박사학위_slide-25 3D tensor + dimension 좌표축`).
- visualization (spectrogram / 산점도) — 강의·박사 자리 빈번. spectrogram 색맵 magma·inferno 계열 보라-노랑 (matplotlib `magma`, `SepReformer_slide-12 visualization`).

**모델 비교 산점도** — x축 MACs (G/s) log scale, y축 SI-SNRi (dB) 의 _Performance vs Computation_ frontier. ours = 진빨강·진주황 강조 + ✓ 체크, baseline = 톤 다운 (노랑·파랑·회색) (`SepReformer_slide-14 산점도`, `강의_slide-13 산점도`). [[project_user_paper_figure_style]] _ours 빨강_ 룰과 동일.

**표 layout**:
- 가로줄만 — 헤더 행과 본문 행 사이 가로줄 1 + 표 상하 가로줄 1. 세로줄 / 가운데 분리선 X.
- column 순서 `System | Params (M) | MACs (G/s) | Dataset 1 | Dataset 2 | ...` — params·MACs 가 metric 보다 앞, 도메인 metric (SI-SNRi 등) 은 데이터셋별로 나란히.
- ours 행 강조 — 진한 글씨 또는 옅은 노란 배경. baseline 은 default 흰 배경 (`NeXt-TDNN_slide-21 ours 진한 글씨`).
- 표 캡션 — 표 아래 `(a) On Encoder design`, `(b) Separator with SepRe method` sub-caption 으로 ablation 묶음 구분 (`박사학위_slide-19 ablation 묶음`).

**강조 metaphor**:
- 빨강 = 강조 / 도메인 / 결과 ours 행 / 표지 띠. 가장 강한 시각 anchor.
- 노란 형광 underline = 강의·학회 자리 본문 안 부분 키워드 marker.
- 빨강 진한 단어 = 정의·결론 핵심·본인 contribution.
- 체크 ✓ 표시 = 산점도 자리 ours 변형 식별.
- 음표 아이콘 + QR 코드 = spectrogram 자리 audio sample 청취 link (`SepReformer_slide-02 demo QR`).
- 빨간 점선 박스 / 빨간 박스 = figure 안 강조 영역 / 핵심 항목 강조.
- 본문 한 줄 _전체_ 색칠 X — 빨간 색·노란 underline·굵게는 _key 토큰_ 에만 박는 절제.

## 4. 청중별 변형 (학회 / 박사 / 정부과제 / 산업 세미나)

| 항목 | 박사 심사 | 학회 | 정부과제 | 산업 세미나 |
|---|---|---|---|---|
| 분량 | ~50 장 | 8-27 장 | 10-20 장 | ~45 장 |
| 시간 추정 | 40-60 분 | 8-20 분 | 30-40 분 | 60-90 분 |
| 본문 언어 | 영어 | 영어 일관 | 한국어 (도메인 영어) | 한국어 (도메인 영어) |
| 표지 부제 | 한국어 부제 | X (영문 단일) | 한국어 부제 | X (영문 단일) |
| agenda 슬라이드 | Contents 6 자리 | X | Table of Contents 4-7 자리 | 목차 6 자리 |
| Roadmap / timeline | X | X | X | 별도 1 슬라이드 |
| 단원 표지 | 6 자리 active | 짧은 자리도 2 회 active | 약함 (deliverable 로 대체) | active |
| 슬라이드당 메시지 수 | 1-2 + bullet 6-10 줄 | 1 + bullet 4-8 줄 | 4-6 (그림+사진+표+Gantt) | 2-3 (표 dense) |
| 실험 결과 강도 | 깊음 (table 5-7 개, dataset 4 자리) | 중간 (대표 표 2 자리) | 낮음 (도식+deliverable) | 낮음 (정리+spectrogram) |
| Future Works | 명시 1 슬라이드 | 명시 1 슬라이드 | X (단계별 plan 대체) | Conclusion 안 통합 |
| Appendix | Reference+Appendix 5 자리 | X | X | X |
| 마무리 슬라이드 | "감사합니다" | "Question & Answer" | X (직접 종료) | "Q&A" |
| citation 강도 | 단원 표지 paper + Reference dense | 표지 footnote, 본문 inline 적음 | 본문 inline 거의 X | figure 옆 caption (저자+연도+학회+CC) |

**핵심 — 자리별 변형 한 줄 정리**:
- 학회 — 영어 일관 / agenda 슬라이드 X / 단원 표지 active (짧은 자리도) / 실험 결과 표 중심 / 분량 압축 / Q&A 슬라이드 (`NeXt-TDNN_slide-27 Q&A`).
- 박사 — 종합 정리 / Reference + Appendix 5 자리 갖춤 / 시기별 progressive development / 6 단원 풀 / Research output 별도 슬라이드 (`박사학위_slide-02 졸업 요건 출판 list`).
- 정부과제 — 한국어 / 시스템 도식 중심 / deliverable 단계 표시 / Future Works 약함 / 한 슬라이드 정보 압축도 최고 (column 분할 + 박스).
- 산업 세미나 — 한국어 + timeline roadmap 1 슬라이드 추가 / 6 단원 / TF-Restormer 본인 work + lab paper 정리 강조 / 데모·spectrogram 위주.

## 5. 한국어 vs 영어

**자리별 언어 선택**:
- 박사·학회 — 본문 영어 일관. 박사 한국어는 자막·감사 슬라이드 자리만 (`박사학위_slide-40 감사합니다`). 본문 영어 = 영문 paper 자료 재활용 + 글로벌 일관성.
- 정부과제·산업 세미나 — 한국어 본문 + 도메인 용어 영어. 영어 약어 (`NKDaem`, `VoiceFixer`, `AIHub`, `DJI Mic 2`, `SNR`, `RIR`, `STFT`, `MIMO`, `SRP`, `Diarization`, `Mask`, `Complex TF`, `Restoration`, `Generative`, `BWE`, `URGENT`) 영어 그대로, 일반 표현 (_가공·확보·활용·방안·시기별·정리·도식_) 한국어 (`기업세미나_slide-04 신호 모델 수식 + 한국어 caption`).

**언어 정책** — 도메인 영어를 영어 그대로 두고 일반 명사·동사는 한국어로 풀어 쓰는 패턴. 같은 어휘를 한 자리에 두 가지 표기로 쓰지 않음. _판교체 회피_ 가 발표 자료에서 일관 — 사용자 평소 한국어 정책 ([[feedback_korean_readability_policy]]) 그대로의 패턴이 슬라이드 본문에도 박힘.

**약어 표기**:
- 첫 등장 시 풀어쓰기 (`Efficient Global Attention (EGA)`, `Convolutional Local Attention (CLA)`) → 이후 약어만 사용 (`NeXt-TDNN_slide-08 EGA 첫 등장 풀어쓰기 + 약어 정의`).
- architecture 도식 박스 안에는 약어 (`MHSA`, `LayerNorm`, `BN`, `BiLSTM`), 본문 bullet 풀어쓰기 (`NeXt-TDNN_slide-12 architecture 박스 약어 + bullet 풀어쓰기`).

## 6. 본문 텍스트 (bullet vs 박스 vs 도식)

**슬라이드당 텍스트 양**:
- 박사 — bullet 6-10 줄 (1 단 1-2 개, 2 단 3-5 개, 3 단 2-4 개). dense detailed (`박사학위_slide-21 bullet 9 줄`).
- 학회 — bullet 4-8 줄 (1 단 1 개, 2 단 2-4 개, 3 단 1-3 개). 약간 더 압축 (`SepReformer_slide-04 Motivation 1 bullet 6 줄`).
- 정부과제 — bullet 6-12 줄 + 시각 자산 4-6 개 (그림·사진·표·Gantt). 정보 압축 최고 (`정부과제_slide-04 Gantt + 사진 + 표 + bullet 6 자리`).
- 산업 세미나 — 표·dense 자료 (`기업세미나_slide-04 표 6 행`, `_slide-06 URGENT 14 줄 dense`).
- 표지·단원 표지 — 텍스트 거의 X (제목 한 줄만, `박사학위_slide-04 Introduction 한 줄`).

**분포**:
- bullet 압도적 — 박사·학회·강의 자리 4 단계 bullet 이 default. 사각형 textbox 거의 X.
- 수식 박스 — figure 안 자리 수식 (LaTeX), 회색 배경 + 검정 글씨 + italic serif (`박사학위_slide-25 dimension 좌표축 + 수식 박스`).
- architecture 도식 — block + 화살표. 박스 색 코드 (Encoder 노랑 / Decoder 연두·orange / 부속 회색 또는 흰, `박사학위_slide-29 SR-CorrNet 전체 도식`).
- 표 — 가로줄만 + ours 행 강조 + params·MACs metric 순.
- 그래프 — small-scale scatter (RTF / params 비교), spectrogram 다단, 산점도 (MACs vs SI-SNRi, `SepReformer_slide-14 산점도`).

**글머리 깊이 절제** — 최대 4 단계. 그 이상은 마지막 단계만 빨간 강조로 가독성 유지 (`박사학위_slide-28 ↳ SR-CorrNet for universal speech enhancement and separation` 빨간 굵은 강조처럼 _최후 결론_ 자리만 빨강).

**색 강조 규칙**:
- 빨강 = 단원 main 강조 / 결론 / 새 modal / 본인 contribution.
- 노란 highlight underline = 글머리 line 안 부분 키워드 marker (강의·학회 자리 빈번, 박사 자리는 적음).
- 검정 굵게 = 변수명·수식 element.
- 본문 한 줄 _전체_ 색칠 X — _key 토큰_ 에만 박는 절제 패턴.

**한 슬라이드 = 한 메시지 원칙** — 53 장 이상 검토 결과 거의 깨지지 않음. 슬라이드 한 장이 청중에게 30 초 ~ 1 분 분량의 호흡으로 박힘. 삭제·축약 의사결정 기준으로 작동:
- max message — 박사·학회·강의 1-2 + bullet 4-10 줄. 정부과제만 의식적 위반 4-6 message (`정부과제_slide-04` 한 슬라이드 5 message). 산업 세미나 표·spectrogram 자체 2-3 message.
- cut 규칙 — 글머리 4 단계 초과 → 통합·분리. bullet 10 줄 초과 → split (H1 반복). figure 2 + 표 1 동시 → split. 수식 5 줄 이상 → 본문 bullet 빼고 수식만 또는 Appendix.
- 자리별 자동 cut — 학회 motivation 깊이·proof Appendix·cut. 박사 Appendix 5 자리·Reference dense 로 분산. 산업 paper inline citation 자리 figure 옆 caption 으로 묶고 본문 cut. 정부과제 Future Works → 단계별 plan, Q&A 슬라이드 cut.

## 7. Conclusion / Take-home

**자체 Conclusion 슬라이드**:
- 박사 — 한 슬라이드 안 _Progressive development_ 4 자리 (SepReformer / TF-CorrNet / IF-CorrNet / SR-CorrNet) 본인 work 시기별 정리 (`박사학위_slide-38 Conclusion`). _SR-CorrNet: Integrated framework_ 강조 (TF-model + SepRe + 3d correlation + dynamic split). _Unified and advanced pre-processing_ 4 자리 항목 (single + multi-channel scenario / arbitrary speakers + joint task / SOTA performance / real-recorded robustness).
- 박사 Future Works — 자체 슬라이드 (`박사학위_slide-39 Future Works`). arbitrary mic array (single-channel 포함) / Target Speaker Extraction 3 자리 (speaker identity / text query / visual cue) / low-latency streaming + efficiency.
- 학회 NeXt-TDNN Conclusion — Modernizing TDNN + Efficiency & Effectiveness 두 자리 큰 bullet (`NeXt-TDNN_slide-24 Conclusion`). 수치 take-home 명시 (`with only 1/3 params and comps`).
- 학회 NeXt-TDNN Future Works — 자체 슬라이드 (Improvement of MSC + Investigation of MFA, `NeXt-TDNN_slide-25 Future Works`).
- 학회 SepReformer Conclusion — 굵은 3 줄 bullet 좌측 정렬 (`SepReformer_slide-15 Conclusion`).
- 산업 세미나 Conclusion — 6 자리 항목 한 슬라이드 정리 (`기업세미나_slide-44 Conclusion`): Mask 기반 / Complex TF + Time-domain / TF dual-path / Restoration · Generative / TF-Restormer ICML 2026 — 마지막 자리 빨간 글씨 강조 + dense bullet. TF-Restormer 자리 _Universal SE + GSR + TF-dual-path 정확성 + BWE fs 유연화_ 4 자리 + _Frequency cross-attention + extension query_ 핵심 contribution 명시.

**take-home 패턴**:
- 본인 work 시기별 list — 박사·산업 세미나 자리 본인 모델 4-5 자리 (SepReformer / TF-CorrNet / IF-CorrNet / SR-CorrNet / TF-Restormer) progressive development 가 narrative anchor (`박사학위_slide-38`, `기업세미나_slide-44`).
- 수치 take-home — 학회 자리 `1/3 params and comps` 같은 정량 수치 (`NeXt-TDNN_slide-24`). 박사 자리 _SOTA performance_ 같은 정성.
- 마지막 emphasis slide — 박사 "감사합니다" (한국어, `박사학위_slide-40`) / 학회 "Question & Answer" (영어, `NeXt-TDNN_slide-27`) / 산업 "Q&A" (한국어, `기업세미나_slide-45`) / 정부과제 자체 종료 슬라이드 X.

**brand 일관성**:
- 특정대학 진빨강 + 흰 글자 표지 = 시그니처. 어느 발표 자리든 한 장은 진빨강 띠 표지 (학회 slide 1, 박사 단원 표지 자리, `박사학위_slide-01`, `NeXt-TDNN_slide-01`).
- IIPLab 로고 좌하단 + 특정대학 로고 우하단 = 모든 본문 슬라이드.
- 헤더 우상단 슬라이드 번호 + Dept. 명 = 본문 default.
- 빨강 = 강조 / 노랑 형광 = underline 인용 = 강조 metaphor 통일.
- architecture 도식 좌→우 흐름 + encoder 노랑 / decoder 연두·orange / separator 회색 = 모듈 색 통일.
- 표 = 가로줄만 + params·MACs metric 보다 앞 + ours 행 진한 강조 = 표 layout 통일.

자리별로 정보 압축도와 청중 타겟만 다르고 시그니처 (색·로고·헤더·표·도식 layout) 는 일관. _학회 영어_ vs _정부과제 한국어_ vs _박사 영어_ 가 도메인 영어를 그대로 유지하면서 일반 어휘만 자리에 맞춰 갈아끼우는 방식.

**citation 형식**:
- 박사 — 단원 표지 푸터 paper (저자 + 제목 + 학회 + 연도, submitted 자리는 `(submitted)` 명시, `박사학위_slide-23 푸터 ICASSP 2026 submitted`) + Reference slide 자리 dense list (`박사학위_slide-41~45`).
- 학회 — 표지 footnote (공저자 + Equal contribution / Corresponding author, `SepReformer_slide-01 footnote`) + 본문 inline citation 약함.
- 정부과제 — 본문 inline reference 거의 X — 시스템 도식 위주.
- 산업 세미나 — figure / 표 옆 caption (저자 + 연도 + 학회 + 선택적 `CC=N` citation count) — `Wave-U-Net(Stoller 2018, ISMIR, CC=75)`, `Conv-TasNet(2019, 7-NSLP, CC=2509)` 같이 CC 까지 박는 것이 산업 자리 특유 (`기업세미나_slide-09 figure 옆 caption + CC`).

## 사용자 수동 메모

> 본 절은 _사용자 영역_. `/notes --scope user presentation add ...` 가 append. analyze-user 는 _읽기만_ 하고 손대지 않음.

_(아직 비어 있음 — `/notes --scope user presentation add ...` 로 첫 항목 추가)_
