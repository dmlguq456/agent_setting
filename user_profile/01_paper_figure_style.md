---
aspect: figure
owner: 사용자
mode: init
updated: 2026-05-27
source: paper PDF 8 / figure_ppt 5 (PNG 54) / code architecture.png 2
consensus: 3-instance (run A/B/C) + reproduction-grade 정밀 관찰 보강
grade: macro-taste + object-library (원본 개체는 assets/figure/svg/ 복사가 기본; micro 재현 recipe 는 _internal/figure_reproduction_spec.md fallback)
changelog:
  - "2026-05-27: 재현 micro spec(구 Part B B1-B11)을 _internal 로 이관, Part B 를 거시 배치 감각+개체 라이브러리로 재구성 (LLM 재현 포기 → 원본 pptx 개체 복사). 265→121 줄."
---

# 01. Paper / Figure 제작 스타일

> Speech separation·enhancement·restoration 연구자의 figure/diagram 양식. architecture diagram + booktabs 표가 중심, line plot·scatter 는 절제적. **Part A** = 무엇을/왜(패턴 카탈로그), **Part B** = 거시 배치 감각 + 원본 개체 라이브러리(`assets/figure/svg/` 복사 source). 디자인팀·자료팀이 figure/표/슬라이드 비주얼 만들 때 1순위 참조 — _다시 그리지 말고 원본 개체를 복사_.

---

# Part A — 패턴 카탈로그 (무엇을 / 왜)

## A1. Architecture diagram — 역할 색 규약 (가장 강한 시그니처, 3/3)

NeurIPS SepRe → SPL TF-CorrNet → ICML TF-Restormer → 발표 deck 전부 일치하는 **역할→색** 매핑:
- 초록 = encoder / separation / analysis 경로 ("Time/Freq. self module")
- 주황 = decoder / reconstruction / synthesis 경로 ("Freq. cross-self module")
- 회색 = I/O·보조 연산 (STFT/iSTFT, Conv2D, Projection, Split, Filter, LN)
- 빨강 = novelty 강조 (빨강 점선 outline 또는 빨강 텍스트)
- 노랑/금색 = zoom-in 한 신규 sub-block (Q/K/V Linear, Freq. projection)

핵심 device (왜 그리나):
- **cross-attention 은 "key/value" 라벨 화살표**로 encoder→decoder 명시 — trademark (2026_ICML Fig.2, architecture.png).
- **텐서 shape glyph**: 모듈 아래 3D slab + 처리축 빨강 양방향 화살표로 "어느 축이 sequence·어느 축이 처리 대상"인지 못박음 (dual-path time/freq 모델 전용).
- **zoom-in callout**: 상위 block 을 점선으로 끌어내려 내부 분해, 확대 안에서도 색 규약 유지.
- 텐서 차원(`ℝ^{F×T×C}`)·반복(`×B_E`)을 figure 안에 직접 annotate, 본문 수식과 동일 bold 변수.

> 원본 개체는 **§B0** 라이브러리(`assets/figure/svg/`)에서 복사 / micro 재현 recipe(geometry·connector 수치)는 `_internal/figure_reproduction_spec.md` (fallback).

## A2. Booktabs 표 (정량 비교의 기본, 3/3)

- **세로 칸선 없음**, 가로줄만 (`\toprule`/`\midrule`/`cmidrule`/`\bottomrule`).
- **의미 그룹 다단 헤더**: "Signal fidelity"(PESQ/SDR/LSD/MCD/sBERT) vs "Perceptual quality"(UTMOS/DNSMOS) (2026_ICML Table 1·2).
- 열 순서: Method → 비용열(`Param.(M)`/`Size(M)`/`MACs(G/s)`/`MAC(G)`/RTF) → metric 열. 비용열을 성능과 **항상 같은 표에 동반**.
- **metric 헤더에 ↑/↓** 거의 항상 (PESQ↑, LSD↓, EER(%)↓).
- **Input / Ground Truth 기준 행을 최상단 별도 그룹** (GT 의 SDR 은 `∞`).
- **dagger `†`/`‡` 각주** (dedicated vs universal, pretrained code, 원논문 보고치).
- 행 그룹 좌측 **세로 회전 라벨** ("mobile"/"base") (NeXt-TDNN Table 2).
- ablation: 첫 열 자연어 case 명 ("encoder-only"/"w/o MHCA"/"w/ MHCA(small)"), **체크마크 √ 열**로 on/off.

ours 강조: **best 수치 = 열별 bold**, 제안 variant 는 **표 하단 그룹** 같은 prefix 묶음 (`TF-Restormer(off)/(off)†/(on)`). 채택 config·제안 행 회색 음영은 NeurIPS 계열만(SeparateReconstruct Table 4/5), TF-CorrNet/NeXt-TDNN 은 bold-only. 표 안 색 음영·화살표 절제 — bold+위치 1순위 (메모리 "rebuttal 표 drop" 정합 — [[feedback-paper-body-rewrite-pattern]]).

## A3. Curve plot (절제적, _consensus 2/3_ — run B·C 관찰)

- 위치: 분석용 figure·thesis·슬라이드 (paper 본문은 표 위주, loss curve 미관찰).
- **마커 달린 실선**(filled circle), 2×2 패널, 축/스케일 정렬. x="Stage index (b/r)" 또는 "Time frame index", y="PESQ-WB"/"SI-SDR"/"Cosine Similarity".
- **회색 점선 수평 기준선 + 라벨** ("Noisy"), 범례 패널 좌상단 박스.
- 색 4팔레트(주황/노랑/파랑/초록)로 변형 구분 (TF_Block_Reuse_slide-6: B16R1/B1R16/B8R1/B1R8).
- spectrogram + curve **같은 x축 수직 정렬** (SepReformer_slide-11: Spk1/Spk2 spectrogram + cosine similarity Z1~Z4 4색).

## A4. Scatter (희소, _consensus 2/3_ — run B·C 관찰)

- 2-패널 나란히, 밀도 산점도(점 수만 개), log-log, 단색 그라데이션(파랑=raw/문제 vs 빨강=normalized/개선) (2026_ICML Fig.4).
- **회색 대각 transition line + 텍스트 주석**, 패널 inset 박스에 핵심 수치("CV = 2.65" / "CV = 0.28").

## A5. Spectrogram 관례

- 용도 (3/3): architecture **입출력 anchor**(before/after) — 입력 band-limited → 출력 전대역(super-resolution). SFI-STFT / SFI-iSTFT 라벨 동반.
- colormap **2종 분업** (_consensus 2/3_): architecture anchor = **magma/viridis**(보라→주황→노랑); 정량 분석 figure = 관찰상 **jet**(파랑-초록-노랑-빨강) + dB 컬러바(−60~−120). _새 figure 는 perceptually-uniform(viridis/magma) 권장, jet 는 기존 자료 매칭 때만._
- 축: y="Freq. (kHz)"(0/2/4/6/8), x="Time (s)"/"Time frame index". anchor 썸네일은 축 생략 `T`/`F` 모서리만.
- 비교 패널 가로 나열 (degraded / mask grayscale 0~1 / restored 3단), b×r 격자.

## A6. 폰트 (개요 — 상세 Part B6)

- 블록 라벨·표 본문 = **sans-serif**. 수식·변수(`X`, `ℝ^{F×T×C}`, `×B_E`) = **LaTeX serif math (CM)**, bold 변수 + blackboard `ℝ`. 표 캡션 "Table N." 이탤릭. paper 는 라벨까지 serif 통일 가능.

## A7. 색 hex (pptx XML 추출 — **exact**, 추정 아님)

원본 figure pptx (`TF_Restormer_ICML.pptx` / `TF-CorrNet-v2.pptx`) 의 `srgbClr` 직접 추출값(두 deck 교차 확인). 이전 "≈" 추정값을 대체.

| 역할 | exact hex | 비고 |
|---|---|---|
| **novelty red** | **`#C00000`** | 두 deck 압도적 빈도 — 정의색 (PowerPoint 표준 dark red) |
| **decoder orange** | **`#ED7D31`** (밝은) / `#C55A11`·`#A9592D` (짙은) | ED7D31 = Office accent2 |
| **encoder green** | **`#548235`** / `#587048` (muted) / `#70AD47` (밝은) | 70AD47 = Office accent6 |
| **accent gold/yellow** (zoom) | **`#FFC000`** | Office accent4 |
| 보조/aux blue (speaker) | `#00B0F0` (light) / `#4472C4` (accent1) | |
| 보조 gray | `#A5A5A5` (accent3) | I/O·보조 stroke |
| 텍스트/fill | `#000000` / `#FFFFFF` | |

tint halo = 위 base 색의 ~15% 농도(PPT lumMod/lumOff). exact tint 는 **원본 도형 복제**로 그대로 가져오는 게 정확.

> **재현 원칙**: hex 는 이제 exact. 단 ① fill 흰색·stroke 가 carrier ② bold-only 표 강조 ③ red-dashed/red-text 신규 모듈 규칙은 그대로 우선.

---

# Part B — 거시 배치 감각 + 원본 개체 라이브러리

> **재현(다시 그리기) 포기 — 원본 개체 복사가 기본** (2026-05-27): figure 는 LLM 이 spec 보고 다시 그리지 않는다. `assets/figure/svg/<deck>_slide-N.svg` (pptx 추출, 100% fidelity) 에서 **실제 도형·텍스트 개체를 복사·재배치**한다. 같은 계열 새 figure 는 슬라이드 도형 `cp` 후 라벨·색만 교체가 최정밀. 본 Part 는 _그릴 때의 micro 수치_ 가 아니라 _개체를 어떻게 고르고 배치하나_ 의 거시 취향이다. micro 재현 recipe(geometry H-비율·box/marker/glyph 좌표·단계별 절차·primitives defs)는 pptx 없는 fallback 자리에서만 → **`_internal/figure_reproduction_spec.md`**.

## B0. 원본 개체 라이브러리 (복사 source)

- **`assets/figure/svg/`** — 5 deck 54 슬라이드를 `pdftocairo -svg` 로 추출한 벡터 개체 (도형·텍스트·색 그대로, 임베드 spectrogram 만 raster). 박스·화살표·glyph·라벨을 여기서 복사.
- canonical 앵커 — `ex1_TF_Restormer_architecture.svg`(top-level) · `svg/TF_Restormer_ICML_slide-1.svg`(unit module) 등.
- 편집 최정밀 원본 = `figure_ppt/*.pptx` (`/home/nas/user/Uihyeop/ref_user_profile/figure_ppt/`).
- raster anchor `exN_*.png` (육안 대조용).
- 신규 다이어그램(pptx 에 없는 워크플로우 등)은 `assets/figure/_primitives.svg` defs 복사 시작.

## B1. 거시 디자인 감각 (개체 선택·배치 원칙 — 신규 작업에 전이)

- **Composition** — top-level = 가로 banner 좌→우, 아래에 한 컨테이너를 점선으로 끌어내린 2단 분해도. unit-module 내부는 아래→위 (top-level 과 90° 직교 — 시그니처). 양끝 spectrogram anchor.
- **Density** — banner 는 빡빡하게(요소 gap 좁게), 분해도·glyph 띠는 숨통. 헐겁게 퍼지지 않게.
- **강조·절제** — 강조는 novelty 만(빨강 점선·빨강 텍스트, gold zoom). 나머지는 흰 fill+역할색 stroke 로 차분. 표는 색음영 자제, bold+위치로. 색 남발 X.
- **위계·시선** — focal point = novelty 모듈. 라벨 크기 위계(컨테이너 제목 > 모듈명 > 차원 첨자 > 범례).
- **색 의미** — encoder green / decoder orange / aux gray / novelty red / zoom gold (§A7 exact hex). fill 흰색, stroke 가 의미 carrier.
- **시그니처** (빠지면 "이 사람 figure" 아님) — ① cross-attention "key/value" 라벨 화살표 ② 텐서 glyph(slab 줄무늬=처리축 + 빨강 양방향 화살표) + 좌하단 axis 범례 ③ `ℝ^{...}` 차원 첨자(본문 수식과 동일 bold) ④ magma/viridis spectrogram anchor ⑤ `×B` 점선 stack 컨테이너.

## Open Questions

- 표 row 음영: NeurIPS 계열 회색 음영 vs TF-CorrNet/NeXt-TDNN bold-only — 매체/연도 차이 확정 못 함.
- 간격 비율·tint opacity 는 육안 근사 — exact 는 원본 pptx 복제. (hex 는 §A7 에서 exact 확보 완료.)

## 사용자 수동 메모

(없음 — `/notes --scope user figure` 로 추가)
