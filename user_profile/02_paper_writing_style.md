---
aspect: writing
owner: 사용자
mode: init
updated: 2026-05-26
source: paper PDF 8 (영문) + 국문 연구계획서 PDF 2 (기초연구 v3 / 2차년도 v6)
consensus: 3-instance (run A/B/C, 강한 일치)
note: 외부 hwp 계획서는 변환 실패로 제외
---

# 02. 학술 글쓰기 스타일

> paper(영문)·보고서(국문) 본문 톤. 연구팀·편집팀이 본문 wording 작성·다듬을 때 참조. 메모리 [[feedback-paper-body-rewrite-pattern]]·[[feedback-paragraph-cohesion-pre-check]] 와 정합.

## 1. Abstract 골격 — 4-move 고정 (3/3)

1. **task 정의/관행 진술** — 명사구 주어 단정형 ("Speech restoration aims to...", "[Task] remains challenging because...", "In [field], ...").
2. **기존 가정/한계** — "However" / "Although" 로 gap 명시.
3. **제안** — "We formulate/propose **[Model]**, a [명사구]" (모델명 italic) + 메커니즘 동사 나열.
4. **결과** — "Experimental results demonstrate..." 1문장. **수치는 abstract 에 거의 안 넣고 정성 서술로 마감**.

- conference paper 만 `Index Terms:` 명시.

## 2. 문장 구조 (3/3)

- 중-장문, **종속·관계절 다중 중첩**. 전치 부사절(By -ing / To do) + 주절.
- **현재분사 -ing 로 결과·부연 매달기** 강함 ("yielding... while keeping...", "enabling...").
- "X while Y" / "rather than Y" 로 제안과 기존을 **한 문장에 병치**.
- 1인칭 복수 **"we" 능동**이 기여 서술 주도. 수동태는 신호/데이터/메커니즘 서술에. 결과는 과거시제.
- contribution = "We..." bullet 리스트. 문단 끝 "Consequently/Therefore, we..." 로 회수.

## 3. 용어·약자 도입 (3/3)

- **"풀네임 (ACRONYM)" 첫 등장 정의** 엄격 ("short-time Fourier transform (STFT)").
- 자체 명명 개념·모듈명은 **italic 정의** (*xSFI*, *early split*, *SepRe*, *TS-ConvNeXt*).
- 모델명은 **의미 담은 합성 작명** (TF-Restormer / *-CorrNet family).

## 4. 강조·대비 transition (3/3)

- **대비 마커 고밀도**: Unlike / Instead / In contrast / Crucially / Notably / Rather than / More critically.
- "These observations motivate X" 로 gap→제안 연결.
- **hedging 비대칭** (시그니처): _남의 방법엔 hedge_ (typically/often/largely), _자기 기여·결과엔 단정_.

## 5. 수식·notation 서술 (3/3)

- 변수 도입 **즉시 `∈ ℝ^{...}` + "where ..." 정의절** + 물리적 의미 곁들임.
- **bold 대문자 = 텐서**, subscript E/D 로 encoder/decoder 구분, 시간-주파수 subscript `tf`.
- multi-task loss `L = Σ α_i L_i`.
- 서술 3단: 자연어 동기 → 식 → tuning parameter.
- "Let X be given as ... where ... respectively", "X denote Y".

## 6. 국문 보고서 톤 (3/3)

- **평어 단정 격식 문어**: ~한다 / ~이다 / ~필요하다 / ~기대한다. 당위·전망형 종결.
- **"국문풀이(영문; 약자)" 병기** — 영문 약자 규칙과 대칭 ("단시간 푸리에 변환(STFT)"). **모델명은 원어 유지**.
- 영문과 동일한 장문 다단 + gap-then-propose. "첫째/둘째/셋째" 번호 열거.
- 신호 물리 관점에서 문제 정의.

## 7. 영문 vs 국문 차이 vs 공통

| | 영문 | 국문 |
|---|---|---|
| 주어 | 1인칭 "we" 능동 | 무주어 객관 서술 |
| 강조 | italic 모델명 · contrastive transition | 부사 강조 · 당위 종결 |
| 종결 | 단정 + hedge 비대칭 | ~필요하다 / ~기대한다 |

- **공통 DNA**: 4-move 논리 골격 · gap-then-propose · 약자 규칙 · 장문 종속 · 의미 곁들인 수식 3단 · 신호 물리 framing — 언어 무관 동일.

## Open Questions

- 국문 톤은 기초연구 v3/v6 2편 기반 (외부 hwp·hwpx 보고서 변환 실패로 제외) — 국문 sample 보강 시 재검증.

## 사용자 수동 메모

(없음 — `/notes --scope user writing` 로 추가)
