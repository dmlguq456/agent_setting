---
aspect: figure
last_init: 2026-05-26
version: 2.5
---

# Paper / Figure 스타일

> 사용자 paper 8 편 (ICML / NeurIPS / ICASSP / Interspeech / T-ASLP / SPL) + figure_ppt 5 + ppt PNG 8 추출 패턴. 분석팀 / 연구팀 / 디자인팀 / 편집팀이 figure / 표 만들 때 default. process 메타 (consensus N/3, source A·B·C 매핑, quarantine 후보) 는 `_internal/aspect_figure_draft.md` 참조. open question 은 `_internal/open_questions.md` 참조.

## 1. Architecture diagram

### 1.1 Block 모양·outline·arrow

- 블록 모양 둥근 모서리 직사각형 (rounded rectangle) 통일. flat 2-D, 3-D shadow / gradient / bevel 전부 X (TF-Restormer Fig.1 / SepReformer.pptx slide-03 / NeXt-TDNN Fig.2 모두 동일 양식).
- Outline 두께 균일 (≈ 2 pt), hairline·굵은 line 같이 안 씀. 같은 paper 안 모든 block 동일 두께 (TF-Restormer Fig.1 본체·inset 같이 2 pt 균일).
- Arrow 검정 단색 1 pt + 단순 화살촉, 곡선 X. residual / skip 도 직선 + 우회 break (TF-Restormer Fig.1, IF-CorrNet Fig.2 모두 직선 routing).
- 분기·합류 자리 `⊕` (add) / `⊗` (concat·multiply) 원 기호. 글자 X (수학 기호 자체).
- White background 위에 outline 위주, fill 은 강조하려는 묶음만 옅은 tint (1.4 절 참조).

### 1.2 묶음·반복·layout

- 큰 묶음 (encoder 전체 / decoder 전체 / 반복 stack) dashed container 로 둘러쌈. 안쪽 fill 옅은 tint (1.4 절).
- 반복 횟수 `×B_E` / `×B_D` / `×R` 표기는 박스 _외부_ (좌측 또는 우측) italic LaTeX 자리. 박스 안 X.
- Layout 방향 좌→우 우세 (encoder 왼쪽, decoder 오른쪽, head 위쪽). data flow 가로 진행 default. SepReformer / TF-Restormer / NeXt-TDNN 모두 가로.
- 위-아래 layout 도 존재 — 입력 아래 (음성·STFT) → 출력 위 (mask·signal·head). IF-CorrNet Fig.2 / Statistical Beamformer Fig.1 자리 vertical.
- 보조 모듈 (attractor / split / filter / head) 아래쪽 column 또는 위쪽 head 자리 분리 배치.

### 1.3 역할별 outline 색 (paper figure dictionary)

본문 architecture figure 는 grayscale 우세, _강조하려는 묶음만_ 색 outline 으로 표시. PowerPoint slide 자리는 paper 자리보다 fill 더 옅게 (SepReformer.pptx).

| 역할 | 색 | hex 계열 | 자리 anchor |
|---|---|---|---|
| Encoder / analysis / 분리 측 | 녹색 outline | `#3F8C5C` 계열 | TF-Restormer Fig.1 encoder 묶음 / SepReformer Encoder |
| Decoder / reconstruction / synthesis 측 | 짙은 주황 outline | `#D27A4B` 계열 | TF-Restormer Fig.1 decoder 묶음 / SepReformer Reconstruction |
| Attention 변별점 (MHSA / MHCA) | 노란 (gold) outline | `#D4A52A` 계열 | TF-Restormer Fig.3 attention sub-block |
| 비교 figure / 변화점 / 신규 module | 빨간 **실선** outline + 빨간 글자 | `#C0392B` | TF-Restormer Fig.3 decoder-only MHCA |
| 출력 head / 부가 head (DOA·VAD·Loc·Filter) | 파랑 outline | `#3D6AA8` 계열 | NeXt-TDNN head / IF-CorrNet Filter 자리 |
| 일반 utility (Conv / Linear / LN / FFN) | 회색 fill·검은 글자 또는 회색 outline | `#7F7F7F` 계열 | 모든 paper 본문 architecture |

채도 낮게 잡음. 같은 의미 자리는 paper·figure_ppt 양쪽 일관 유지. 비교 figure 의 _신규 module 만_ 빨강 — paper figure 안 빨강은 변별점 자리 reserved.

### 1.4 Background tint

- Encoder 묶음 옅은 yellow-green tint, decoder 묶음 옅은 주황 tint (TF-Restormer Fig.1 좌·우 panel 색 대비).
- dashed container 안쪽 fill 자리 사용, 외곽선 색 = container outline 색 약화 버전.
- PowerPoint slide 자리는 paper 자리보다 fill 더 옅음 (SepReformer.pptx slide-03 대비 paper Fig.1).
- fill 없는 자리 default = white background + outline 만.

### 1.5 Inset / sub-block 펼침

- 큰 architecture 옆에 sub-module 내부를 zoom-in 펼치는 inset 박스 흔히 사용 (TF-Restormer Fig.1 의 Fig.3 inset / NeXt-TDNN Fig.2 inset).
- Inset 외곽선 _점선 박스_ 통일, 본 박스와 _얇은 회색 가이드 라인_ 또는 dashed arrow 로 연결.
- (a) / (b) / (c) sub-figure label 부여 — `(a) Time self module` / `(b) Freq. self module` / `(c) Freq. cross-self module` 같은 italic 부제, 그림 바로 아래 가운데 정렬.

### 1.6 텐서 shape annotation

- 박스 사이 화살표 옆 또는 박스 위·아래에 `\mathbb{R}^{F_E \times T \times C_E}` 형태 수학 모드 LaTeX shape 주석을 figure 본체 안 직접 박음.
- 변수 정의 (`F_E` / `T` / `C_E` / `B_E` / `B_D`) 는 caption 또는 본문에서 따로 정리, figure 본체에는 shape 자체만.
- shape 표기는 figure 안 본질 정보 — 캡션이 아니라 figure 본체 자리.

### 1.7 캡션 형식

- venue 규약 맞춤 — `Figure N.` (ICML / NeurIPS), `Figure N:` (ICASSP / Interspeech / SPL), `Fig. N:` (SPL 일부).
- 첫 문장 figure 내용 (어떤 architecture / 어떤 비교) 진술, 둘째 문장 핵심 메시지 한 줄 (왜 중요 / 어떤 발견).
- (a) / (b) / (c) sub-figure 있으면 캡션 본문 안에서 한 묶음으로 설명, 쉼표로 이어붙이는 NeurIPS-style 도 사용.
- 캡션 첫 단어 일부를 `\textbf{...}` 로 짧게 bold 처리하는 NeurIPS-style 도 사용.

### 1.8 데이터 흐름 시각화 (작은 색 막대 / 띠)

- architecture 외부에 데이터 텐서 자체를 작은 막대·띠로 그려 stack / split / 시간축 길이 변화 시각화.
- Encoder feature 녹색 stacked column, decoder padded query 주황 stacked column (TF-Restormer Fig.1 우측 ribbon).
- 범례에 화살표 종류 / query 방향 명시 — self 양방향 노랑, cross 단방향 빨강, mamba 점선 노랑.

## 2. Curve plot

### 2.1 폰트·축·grid (matplotlib ground truth)

- 폰트 serif (Times-style) 8-10 pt default. matplotlib fallback chain `Times New Roman → Nimbus Roman → Liberation Serif → DejaVu Serif`, STIX math, 본문 10 pt (`plot_robust_loss_family.py` / `plot_slog_gradient_curves.py` 자리 ground truth).
- PDF 임베드 `pdf.fonttype=42`, `ps.fonttype=42` 강제 (ICML / PMLR 검증, Type 3 금지 규약).
- Grid 옅은 회색 — `alpha=0.25, linewidth=0.5, which='both'`. 가로·세로 격자 또는 가로만, axis line 검정 얇은 선.
- y / x 축 범위 항상 명시 (자동 scale X), log-log 자주 사용 — TF-Restormer Fig.4 spectral error scatter 양축 log.
- tick mark 안쪽 또는 양쪽 방향.

### 2.2 Palette — cool + warm 두 갈래

두 사용 갈래만 default. 그 외 변형 시 명시 의도 필요.

| 갈래 | 사용 자리 | 색 |
|---|---|---|
| **cool + warm 분리** | baseline (cool) vs ours / variant (warm) 비교 | baseline `#4C72B0` / `#55A868` / `#8172B2`, comparison `#DD8452` / `#B8860B` / `#7F4F24`, **ours `#C44E52`** (빨강, 굵기 2.4) |
| **sequential coral** | ordered variant (parameter sweep / training step) | `cm.OrRd(np.linspace(0.85, 0.40, n))` — 어두운 색이 큰 값 |

- TF-Restormer Fig.4 — (a) raw error 파랑 vs (b) normalized error 빨강 점 색상 분리 (cool / warm 활용 사례).
- 3 series 이상 자리 yellow / orange / red / blue / green 계열로 명도 + 색상 같이 분리.
- ours 라인 thickness `linewidth=2.4`, baseline `1.4`, variant `1.6`. 스타일 — solid (baseline) / dashed / dashdot / dotted (variant) 차등.

### 2.3 Inset / annotation / reference line

- Inset 수치 박스 — `CV = 2.65` / `CV = 0.28` 같은 작은 숫자 박스 panel 안 우상단. `framealpha=0.85, boxstyle='round,pad=0.3'`.
- Reference line 회색 가로선 (`alpha=0.5, linestyle='--'`) + 라벨 (예: `transition line at unit gradient`).
- Annotation `ax.annotate(...)` 직접, footnote 우측 하단 `ax.text(0.99, 0.02, ..., fontsize=7.5, alpha=0.8)` 자리.
- Spectrogram thumbnail 을 line plot 안에 co-locate 하는 자리도 자주 (TF-Restormer Fig.4 (b) 자리).

### 2.4 Legend

- plot 안 inset (우상단 / 우하단), `framealpha=0.92, handlelength=2.4, borderpad=0.4` default.
- 2 열 (`ncol=2`) 가능, ours label `(ours)` suffix.
- 작은 폰트 (≈ 7.5-8 pt), 옅은 박스 또는 박스 없음.

### 2.5 크기·aspect

- single column 6.4 × 2.8" landscape default.
- 2-panel side-by-side 4.5 × 2.8" (per panel).
- Scatter trade-off — 1:1 aspect, X = MACs (G/s), Y = 성능 metric, bubble size = Params (M), 학습 옵션 표기는 check mark / 원 마커로 분리.

## 3. 표 layout

### 3.1 Column 순서 표준

좌→우 흐름:

```
Method/Model → Params (M) → MACs (G/s) → Domain (Time/TF) → <Dataset 1 metrics> → <Dataset 2 metrics> → ...
```

- Params / MACs 항상 _좌측_, dataset 별 metric 묶음은 우측.
- separation·verification 자리 `RTF` column 을 `MACs` 다음에 추가 (ICASSP2024 / IF-CorrNet Table 2).
- 큰 table 자리 column 위에 `Signal fidelity` / `Perceptual quality` heading multi-row header 로 묶음 (TF-Restormer Table 2 자리).
- Ablation 자리 fidelity 1 + perceptual 1 로 추림 (TF-Restormer Table 5).

### 3.2 화살표 (↑ / ↓) 표기

- 모든 metric 옆에 `↑` / `↓` 첨자 — `LSD↓` / `NISQA↑` / `SNR_fw↑` / `PESQ-WB↑`.
- 사용자 paper 표 전부 일관, 예외 X.

### 3.3 Best / second-best 표기

- Best = **bold** cell, 그룹 (mobile / base / Dedicated / Universal / ours) 안 best 만 bold. 그룹 사이 best 따로.
- Second-best = _underline_ — StackLess Table 1 자리 명시적. 다른 paper 자리는 underline 사용 X 또는 일관 안 됨.
- 색 강조 X (heatmap-style table 사용 X).

### 3.4 Footnote (`†` / `‡` / `*`) 표기

- `†` dedicated training / pretrained code 자리 — 예: `†We utilized pretrained models from implementation code from UNIVERSE++`.
- `‡` reported in original paper 자리 — 예: `‡The results are reported in the original paper`.
- `*` auxiliary output (inference 불필요) 자리.
- caption 안 footnote 정의 박음. baseline / proposed 비교 자리는 _공정성 표시_ 의무 — 세팅 불공정 부분 모두 caption footnote 로 명시.

### 3.5 Row 순서

- input / baseline (Noisy / No Processing / Oracle) → prior methods (chronological) → ours (size 순 tiny / small / base / medium / large).
- ours 묶음은 `\midrule` 로 prior methods 와 분리.
- 그룹 (Dedicated models / Universal restoration baselines / ours (off / off† / on)) 사이 horizontal rule.

### 3.6 Sub-table caption

- `(a)` / `(b)` / `(c)` / `(d)` 라벨로 dataset 별 묶음 — TF-Restormer Table 4 한정 자리. 다른 paper 자리는 sub-table caption 별도 X.

## 4. Spectrogram

### 4.1 Colormap (magma / inferno 계열)

- 색맵 magma / inferno 계열 (purple / violet hot) — TF-Restormer Fig.1 thumbnail ground truth.
- low magnitude 짙은 보라·검정, high magnitude 밝은 노랑·주황.
- viridis / jet / warm yellow → red → green 묘사 모두 부정확. 사용자 paper 자리 viridis 사용 X.
- 4-panel side-by-side 자리 (P8 IF-CorrNet Fig.3, P6 StackLess Fig.5) 도 같은 magma 계열 통일.

### 4.2 축·label

- y 축 `Frequency (kHz)` (0-8 kHz), x 축 `Time (s)` (0-5 s) 둘 다 명시.
- 축 label serif font (figure 본체 폰트와 통일).
- Colorbar thumbnail 자리 자주 생략. full-size 자리 dB scale 명시 또는 생략 둘 다 가능.

### 4.3 STFT window (native rate 별)

- 8 kHz → window 256, 16 kHz → window 512, 48 kHz → window 1024. native rate 별 고정.
- resample X (native rate 그대로 STFT). cross-rate 비교 자리에도 각 rate 의 native window 유지.
- 색 축 (`vmin`, `vmax`) 비교 묶음 안 _고정_ — `imshow(..., vmin=GROUP_VMIN, vmax=GROUP_VMAX)`. 강도 차이 시각으로 정직히 비교.

### 4.4 Multi-panel layout

- 가로 row 또는 2 × N grid.
- StackLess Fig.5 — `b ∈ {4, 8, 12, 16}` 위 row + `r ∈ {4, 8, 12, 16}` 아래 row (4 × 2 = 8 panel grid).
- IF-CorrNet Fig.3 — 입력 / 출력 / SF-Raw+MF-Filter / SF-Raw+SF-Mask 2 × 2 grid, 부분 zoom box (검정 사각 → 안 큰 zoom panel inset).
- Condition label (`b=4` / `r=8`) panel 위쪽 표기.

### 4.5 위치 — 두 갈래만

- (a) architecture diagram (Fig.1) 의 입·출력 thumbnail — 작은 크기, colorbar 생략 default.
- (b) 실험 결과 후반부 full-size 2 × N grid — 큰 크기, colorbar 자리 또는 생략.
- 독립 figure (예: dataset stats spectrogram) 자리 X. spectrogram 은 architecture 또는 실험 결과 두 갈래로만 등장.

## 5. 도메인별 metric set

도메인 인지 후 metric column 자동 셋팅.

### 5.1 GSR / Universal restoration (UNIVERSE-class, 시그니처)

- _Signal fidelity_ group — PESQ ↑ / SDR ↑ / LSD ↓ / MCD ↓ / sBERT ↑
- _Perceptual quality_ group — UTMOS ↑ / DNSMOS ↑ / NISQA ↑ (non-intrusive)
- Bandwidth set — 8→16 / 8→24 / 8→44.1 / 16→48 kHz column pair
- 보조 — Params (M), MACs (G/s)
- **두 group 분리 보고 의무**. 한 group 만 보고 평가 X — universal restoration 시그니처.

### 5.2 Speech enhancement / denoising (VoiceBank+DEMAND / DNS)

- DNS — PESQ-WB ↑ / PESQ-NB ↑ / STOI ↑ / SI-SDR ↑
- VoiceBank+DEMAND — PESQ-WB ↑ / STOI ↑ / SSNR ↑ / CSIG ↑ / CBAK ↑ / COVL ↑
- 보조 — Params (M), MACs (G/s)
- universal training 자리는 GSR metric 병행 보고.

### 5.3 Super-resolution / Bandwidth extension (VCTK-SSR)

- LSD ↓ / NISQA ↑
- Bandwidth pair column — 8→16 / 8→24 / 8→44.1 / 16→48 kHz 각각.

### 5.4 Single-channel separation (SepReformer / SR-CorrNet)

- SI-SNRi (dB) ↑ / SDRi (dB) ↑ 둘 같이 보고.
- Dataset — WSJ0-{2, 3, 4, 5}mix / WHAM! / WHAMR! / Libri2Mix.
- 보조 — Params (M), MACs (G/s), RTF.

### 5.5 Multi-channel / CSS (LibriCSS)

- Main — SDRi ↑ / PESQ ↑ / STOI ↑
- ASR-driven — WER (%) ↓ (utterance-wise / continuous × overlap 0S / 0L / 10 / 20 / 30 / 40)
- 보조 — Params (M), MACs (G/s)

### 5.6 Speaker verification (NeXt-TDNN)

- EER (%) ↓ / minDCF ↓
- Dataset — VoxCeleb1-O / E / H
- 보조 — Params (M), MACs (G/s), RTF.

### 5.7 Dereverberation (IF-CorrNet)

- CD ↓ / SRMR ↑ / LLR ↓ / SNR_fw ↑ / PESQ ↑
- Dataset — REVERB SimData / RealData × FAR / NEAR.

### 5.8 ASR / Beamforming (Statistical Beamformer)

- WER (%) ↓ 단독.
- Dataset — CHiME-4 (dt / et / sim / real) / LibriCSS.
- Batch / Online 분리 보고.

### 5.9 MOS-only on real recordings

- UTMOS ↑ / DNSMOS ↑ / NISQA ↑ (non-intrusive 만, reference 없는 자리).
- Dataset — VoxCeleb / URGENT 2025 blind / DNS 2020 real / REVERB Challenge real.

## 6. ours 강조

### 6.1 표 안

- ours 행 표 _마지막 묶음_ 자리, ours 변형 (size / on-off / configuration) 모두 같이 나열.
- metric value bold, baseline 위쪽 묶음.
- 그룹 사이 `\midrule` 로 분리 — Dedicated models / Universal restoration baselines / TF-Restormer (off / off† / on) 같은 묶음.
- 별표·박스 거의 X — bold + 마지막 자리 + 모델명 prefix (TF-Restormer / TF-CorrNet / B*R*-SC) 로 충분.

### 6.2 Architecture diagram 안

- ours 모듈 outline 짙은 주황, baseline 비교 자리 회색 outline.
- 강조 fill 옅은 주황, baseline fill 없음.
- 비교 figure 변별점 (decoder MHCA, 변형 module) 빨간 **실선** outline + 빨간 글자 (점선 X).
- paper figure 안 빨강은 신규 module / 변별점 자리에만 — 일반 ours 강조 자리 X (일반 ours 는 주황).

### 6.3 Curve / scatter

- ours warm `#C44E52` (굵기 2.4), baseline cool `#4C72B0` (굵기 1.4), variant `#DD8452` (굵기 1.6).
- Legend `(ours)` suffix 자리 명시.
- Scatter 자리 ours marker 큰 원 (`s=80`) + edge 강조, baseline 작은 원 (`s=40`).

### 6.4 Variant naming convention

- `Model (variant_flag)` 형식 — 괄호 안 짧은 키워드 또는 hyperparameter.
- 예시:
  - `TF-Restormer (off)` / `(off†)` / `(on)`
  - `TF-Restormer encoder-only` / `encoder-decoder w/o MHCA` / `(small)`
  - `w/o F-proj.` / `w/ F-proj. (sep.)` / `(sha.)`
  - `NeXt-TDNN-l (C=192, B=1)`
  - `TF-CorrNet (Conformer)`
- 같은 모델의 여러 변형은 표 행마다 괄호 안 부분만 다름.

### 6.5 Footnote dagger 활용

- `†` 로 구현·환경 차이 부연.
- 예 — `(off)` 와 `(off†)` 차이는 `†` = dedicated training (universal 안 / 밖 차이).
- `‡` = reported in original paper, `*` = auxiliary output (inference 불필요).

## 사용자 수동 메모

> 본 절은 _사용자 영역_. `/notes --scope user <aspect>` 가 append. analyze-user 는 _읽기만_ 하고 손대지 않음.

_(아직 비어 있음 — `/notes --scope user figure add ...` 로 첫 항목 추가)_
