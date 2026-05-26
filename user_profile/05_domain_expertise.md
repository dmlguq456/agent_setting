---
aspect: domain
last_init: 2026-05-26
version: 2.5
---

# 도메인 배경 / 용어

## 1. 주력 도메인 (SE / SS / SV / ASR / CSS / GSR)

사용자의 주 도메인은 _speech signal processing — TF (time-frequency) domain 처리_. paper 본문 backbone 이 일관되게 STFT 위 dual-path 모델 — _TF dual-path_ 가 사용자 시그니처 패러다임. TF DNN 과 classical statistical 두 갈래 bridging 연구자.

세부 갈래 (paper anchor + 가중치 순):

- **Speech enhancement / denoising (SE / DN)** — 매우 높음. _TF-Restormer_ (ICML 2026) / _Stack Less Repeat More_ (2025) / 다수.
- **Speech separation (SS)** — 매우 높음. _SepReformer_ (NeurIPS 2024) / _SR-CorrNet_ / SS 표준 benchmark 다수.
- **General speech restoration (GSR)** — 높음 (최근 떠오르는 축). _TF-Restormer_ 메인 framing — denoising + dereverberation + bandwidth extension + declipping 을 단일 unified 모델로 묶음.
- **Speech dereverberation (DR)** — 높음. _IF-CorrNet_ + WPE / D-MFMVDR / DCN 계열 prior 와 함께. REVERB Challenge.
- **Continuous speech separation (CSS)** — 높음. _TF-CorrNet_ (2025) 의 LibriCSS 평가, MIMO-BF-MISO 구조.
- **Multi-channel statistical beamforming** — 중간. _Statistical Beamformer_ (TASLP 2024). MVDR / MPDR / MLDR + SCM + SVE + ICA. CHiME-4 ASR robustness.
- **Bandwidth extension / super-resolution (BWE / SSR)** — 중간 (TF-Restormer 안 GSR sub-task 통합).
- **Speaker verification (SV)** — 중간. _NeXt-TDNN_ (2024) outlier — ConvNeXt modernization 기법이 backbone 일반론 자리에도 활용.
- **ASR robustness** — 중간. beamforming pre-processing 의 평가 자리.
- **Declipping** — 낮음. TF-Restormer related work sub-task 언급.

연구 흐름 — speaker verification (NeXt-TDNN 2024) → SS (SepReformer 2024) → multi-channel SS / CSS (TF-CorrNet 2025) → block efficiency (Stack Less 2025) → universal restoration (TF-Restormer 2026). 점진 _general / unified / restoration_ 방향 확장. 핵심 트리오 _SS · SE · restoration_ 세 축이 메인, _multi-channel beamforming / BSS 의 signal processing 전통_ 도 같이.

## 2. TF DNN 용어 (STFT / dual-path / TF block)

### 2.1 STFT 자리

- `STFT` / `iSTFT` — verbatim. complex 자리 `complex STFT`, `complex-spectrum-based`.
- `T-F` 와 `time-frequency (TF)` 혼용 — 본문 `TF`, equation·table column 자리 `T-F` 가능.
- `T-F bins` / `frequency bins` / `time frames` — 차원 명시.
- `frame duration` / `consistent STFT frame duration` — SFI / xSFI 핵심 정의 (40 ms window + 20 ms hop, sampling rate 무관 상수).
- `spectrogram` (magnitude 시각화) vs `complex spectrum` 구분.
- `log-Mel-filterbanks` / `mel features` — vocoder / SV 자리. NeXt-TDNN `80 log-Mel-filterbanks`.

### 2.2 dual-path / TF block

- `TF dual-path` / `time-frequency (TF) dual-path` — 사용자 시그니처. 거의 모든 본인 paper backbone.
- `dual-path model` / `dual-path strategy` — 반복 등장.
- `intra-chunk` / `inter-chunk` — DPRNN 계열.
- `TF block` / `TF-Encoder` / `TF-Decoder` — TF-Restormer naming.
- `band-split` / `band-partitioned cross-attention` — TF-Restormer 차별점.
- `time module` / `freq. module` / `frequency module` — module 단위. `Freq.` 축약 허용.
- `temporal mixing` / `frame-wise channel mixing` — SepReformer.

### 2.3 SFI / 새 키워드 — 사용자 신조어

- `SFI` = sampling-frequency-independent. TF-Restormer base, Paulus & Torcoli 2022 lineage.
- `xSFI` = extended SFI. **사용자 직접 신조어 (2026)**. ICML 2026 camera-ready 핵심 contribution. SFI 의 input-output rate 일치 가정을 풀어 decoupled rate 까지 확장.
- `SFI-STFT` / `SFI-iSTFT` / `SFI discriminator` — SFI 변형.
- `decoupled input-output rates` / `matched input-output rates` — input-output rate framework 의 dichotomy.

### 2.4 attention / transformer

- `MHSA` (multi-head self-attention) / `MHCA` (multi-head cross-attention) — TF-Restormer.
- `RoPE` (Su 2024) — rotary positional encoding. TF-Restormer.
- `positional embedding` / `relative positional encoding` — 방식 명시.
- `Conformer` / `Transformer` — block 명. capitalize.
- `global Transformer` / `local Transformer` — SepReformer / TF-CorrNet unit block.
- `EGA` (efficient global attention) / `CLA` (convolutional local attention) — SepReformer / TF-CorrNet 사용자 발명 약자.
- FFN variant — `FFN` / `EFN` / `ConvFFN` / `GCFN`. SepReformer GCFN (gated conv FFN), TF-Restormer ConvFFN, TF-CorrNet EFN.
- `Macaron-style ConvFFN` (Lu 2019) — 표준 backbone module, expansion factor 3, SwiGLU, Conv1D kernel.
- `GLU` / `SwiGLU` / `GELU` / `ReLU` — activation 표기.
- `F-projection` / `frequency linear projection` — Linformer (Wang 2020) / SpatialNet (Quan & Li 2024a) lineage. frequency bin static sequence 자리 inductive bias.

### 2.5 streaming / causality

- `streaming` / `causal` / `non-causal` — 모드 명시.
- `Mamba` (Gu & Dao 2024) — state-space alternative. TF-Restormer streaming variant 자리. constant-memory inference.
- `state-space` — Mamba 계열.
- `RTF` (real-time factor) — 실시간 자리 metric. signal processing RTF (relative transfer function) 동일 약자, 자리 맥락 구분.

### 2.6 sequence model

- `RNN` / `LSTM` / `BLSTM` / `TCN` — legacy. baseline 언급 자리만.
- `transformer` / `Conformer` — main.

## 3. Signal processing (beamformer / MVDR / WPE)

사용자가 _statistical signal processing_ 백그라운드 깊이 — _Statistical Beamformer_ (TASLP 2024) 가 증거. paper 안 수식 유도 + architectural design 동시.

### 3.1 beamforming

- `MVDR` (minimum-variance distortionless response).
- `MPDR` (minimum-power distortionless response) — MVDR 변형.
- `MLDR` (maximum-likelihood distortionless response) — Statistical Beamformer base. Gaussian / super-Gaussian / Laplacian source model.
- `mask-MVDR` / `mask-based MVDR` — neural mask + classical beamformer.
- `SCM` / `wSCM` — (weighted) spatial covariance matrix.
- `SVE` (steering vector estimation).
- `RTF` (relative transfer function) — direct-path / convolutive 두 갈래.
- `multi-tap filtering` — TF-CorrNet MIMO filter 자리. Deep filtering (Schroter 2022 lineage).

### 3.2 ICA / BSS

- `ICA` (independent component analysis).
- `IVA` (independent vector analysis).
- `BSE` / `BSS` (blind source extraction / separation).
- `CGMM` (complex Gaussian mixture model).
- `RLS` (recursive least squares) — online 자리.
- `TVV` (time-varying variance) — source model 분산 모수.

### 3.3 mask / filter / 상관

- `mask-based` — TF-CorrNet / Statistical Beamformer.
- `IPD` (inter-microphone phase difference) — multi-channel 자리.
- `PHAT` / `PHAT-β` / `SCOT-β` — generalized phase transform weighting, β=0.5 사용자 default.
- `correlation` / `spatial correlation` / `spatio-spectro-temporal correlation` — TF-CorrNet / SR-CorrNet 시그니처.
- `Correlation-to-filter paradigm` — IF-CorrNet / SR-CorrNet 시그니처. mask·spectrum 직접 추정 대신 correlation → filter 추정.
- `localization` — CSS 자리.

### 3.4 multi-channel signal model

- `multi-channel` / `multi-microphone` — 거의 동의어 혼용.
- `MIMO` / `MISO` / `MIMO-BF-MISO` — input/output count. TF-CorrNet.
- `direct signal` — target 자리 (mask-based).
- `room impulse response` / `RIR` — simulation 자리.
- `T60` — reverberation time. TF-CorrNet (T60 ∈ [0.2, 0.6] s), IF-CorrNet REVERB ([0.2, 0.8] s).

## 4. 약자 dictionary (핵심)

abstract 첫 사용 자리 expansion 양식 verbatim. paper 본문에서 등장 빈도 기준 ~45 행.

### 4.1 task / 도메인 약자

| 약자 | full form | 자리 |
|---|---|---|
| SE | speech enhancement | 모든 SE paper |
| SS | speech separation | 모든 SS paper |
| DN | denoising | TF-Restormer |
| DR | dereverberation | IF-CorrNet / REVERB |
| SV | speaker verification | NeXt-TDNN |
| ASR | automatic speech recognition | Statistical Beamformer / TF-CorrNet |
| CSS | continuous speech separation | TF-CorrNet |
| GSR | general speech restoration | TF-Restormer 메인 |
| BWE | bandwidth extension | TF-Restormer |
| SSR | speech super-resolution | TF-Restormer (BWE 신상 키워드) |

### 4.2 TF / transformer / streaming

| 약자 | full form | 자리 |
|---|---|---|
| STFT / iSTFT | (inverse) short-time Fourier transform | 모든 TF paper |
| TF | time-frequency | 모든 TF paper |
| DP | dual-path | SepReformer / TF-CorrNet |
| MHSA / MHCA | multi-head (self/cross)-attention | 모든 transformer paper |
| FFN / ConvFFN / GCFN / EFN | feed-forward variant | block 별 |
| EGA / CLA | efficient global attention / convolutional local attention | SepReformer / TF-CorrNet |
| LN / BN | layer / batch normalization | 모든 paper |
| GLU / SwiGLU / GELU / ReLU | activation | 모든 paper |
| RoPE | rotary positional encoding | TF-Restormer |
| SFI / xSFI | sampling-frequency-independent / extended SFI | TF-Restormer (xSFI 신조어) |
| MAE | masked autoencoder (He 2022) | TF-Restormer asymmetric encoder-decoder 영감 |
| SSL | self-supervised learning | TF-Restormer (perceptual loss 자리) |
| CED | convolutional encoder-decoder | Stack Less |

### 4.3 multi-channel / classical signal processing

| 약자 | full form | 자리 |
|---|---|---|
| MVDR / MPDR / MLDR | distortionless beamformer (variance / power / likelihood) | Statistical Beamformer |
| SCM / wSCM | (weighted) spatial covariance matrix | beamforming |
| SVE | steering vector estimation | beamforming |
| RTF | relative transfer function (또는 real-time factor — 자리 맥락) | multi-channel / efficiency |
| WPE | weighted prediction error | dereverberation classical |
| ICA / IVA | independent (component / vector) analysis | Statistical Beamformer |
| BSE / BSS | blind source extraction / separation | Statistical Beamformer |
| CGMM | complex Gaussian mixture model | Statistical Beamformer |
| RLS | recursive least squares | online 자리 |
| TVV | time-varying variance | source model 분산 모수 |
| RIR | room impulse response | multi-channel |
| T60 | reverberation time | multi-channel |
| MIMO / MISO | multi-input multi/single-output | TF-CorrNet |
| IPD | inter-microphone phase difference | multi-channel |
| PHAT-β / SCOT-β | (smoothed coherence transform) phase transform weighting | TF-CorrNet correlation |

### 4.4 metric — 도메인별 표준

| 약자 | full form | 자리 |
|---|---|---|
| SI-SDR / SI-SDRi | scale-invariant SDR (improvement) | SE / SS |
| SI-SNR / SI-SNRi | scale-invariant SNR (improvement) | SS — SepReformer main loss |
| SDR / SDRi | signal-to-distortion ratio (improvement) | TF-CorrNet / TF-Restormer |
| PESQ (WB / NB) | perceptual evaluation of speech quality | SE / SS |
| STOI | short-time objective intelligibility | SE / SS |
| DNSMOS / NISQA / UTMOS | non-intrusive perceptual MOS estimator | TF-Restormer perceptual quality |
| sBERT | SpeechBERTScore (Saeki 2024) | TF-Restormer |
| LSD | log-spectral distance | TF-Restormer / SR |
| MCD | mel-cepstral distortion | TF-Restormer |
| CSIG / CBAK / COVL / SSNR | composite SE metric | VoiceBank+DEMAND |
| CD / SRMR / LLR / SNRfw | dereverberation metric | REVERB (IF-CorrNet) |
| WER / CER | (character) word error rate | ASR / CSS |
| EER / minDCF | equal error rate / min detection cost | SV (NeXt-TDNN) |
| RTF | real-time factor | efficiency 자리 |
| MACs | multiply-accumulate (G/s) | 모든 paper 표 column |

### 4.5 training / module / 기타

| 약자 | full form | 자리 |
|---|---|---|
| FT | fine-tuning | (memory) |
| DM | dynamic mixing | SS 학습 옵션 |
| PIT | permutation invariant training | TF-CorrNet |
| ckpt | checkpoint (본문은 `checkpoint` full) | memory / spec |
| MFA / ASP | multi-layer feature aggregation / attentive statistics pooling | NeXt-TDNN |
| GRN | global response normalization | NeXt-TDNN |
| MSC | multi-scale convolution | NeXt-TDNN |
| ESSD | encoder-shared-split-decoder (early-split shared decoder) | SepReformer 신조어 |
| SepRe | separation-and-reconstruction | SepReformer 신조어 |
| TS-ConvNeXt | two-step ConvNeXt | NeXt-TDNN sub-block |

## 5. 모델명 / 작명 패턴

자유 텍스트 (paper / 발표 / 문서 / chat) 자리 hyphen 보존. Python identifier 자리 underscore (제약 강제).

### 5.1 user-coined model names

| 모델 | 패턴 | 비고 |
|---|---|---|
| `NeXt-TDNN` | `<Prefix>-<Backbone>` hyphenated | TDNN modernization (ConvNeXt 영감) |
| `SepReformer` | camelCase 결합 (Sep + Re + former) | _Separation + Reconstruction_ Transformer |
| `TF-CorrNet` | `TF-<Concept>Net` | _Correlation_ + Net |
| `TF-Restormer` | `TF-<Concept>er` | _Restoration_ + Transformer |
| `TS-ConvNeXt` | two-step ConvNeXt | NeXt-TDNN sub-block |
| `TS-ConvNeXt-l` | suffix `-l` for light | size variant |
| `SR-CorrNet` | `SR-<Concept>Net` | separation-and-reconstruction CorrNet |
| `IF-CorrNet` | `IF-<Concept>Net` | inter-frame prefix |

작명 규칙:

- **hyphen 적극** — `TF-Restormer` / `NeXt-TDNN` / `TS-ConvNeXt`. _공백 표기 X_ (`TF Restormer` 안 씀).
- **CamelCase / PascalCase + hyphen 혼용** — `SepReformer` 처럼 camel 단어가 hyphen 없이 한 단어 가능.
- 사용자 작품 prefix — `TF-` (time-frequency), `SR-` (separation-and-reconstruction), `IF-` (inter-frame), `TS-` (two-step), `NeXt-` (next-generation modernization).
- module / block 명도 hyphen — `Time self module` / `Freq. cross-self module` (TF-Restormer), `Global Transformer` / `Local Transformer` (SepReformer).

### 5.2 자리별 표기

| 자리 | 표기 |
|---|---|
| 자유 텍스트 | `TF-Restormer`, `NeXt-TDNN`, `TF-CorrNet`, `SR-CorrNet`, `IF-CorrNet`, `TS-ConvNeXt`, `SepReformer` |
| Python 폴더 / 클래스 | `TF_Restormer`, `SR_CorrNet_SS`, `TF_Encoder`, `TF_Decoder` |
| Python 패키지 | `tf_restormer`, `sr_corrnet` |
| 식별자 | `MS_STFT_Gen_SC_Loss`, `SSL_FM_Loss`, `HF_Loss`, `F_Linear`, `kv_shared`, `Ekv` |

자유 텍스트 hyphen ↔ Python underscore 병존 자체는 모순 X.

### 5.3 약자 결합 module 명

paper 안 도입하는 module 약자.

| 약자 | full form | paper |
|---|---|---|
| T-MHSA / F-MHSA / F-MHCA | time / freq MHSA, freq MHCA | TF-Restormer |
| T-ConvFFN / F-ConvFFN | time / freq ConvFFN | TF-Restormer |
| CS Transformer | cross-speaker Transformer | SepReformer |
| $\mathbf{Q}_{\text{ext}}$ | extension query (band-partitioned, learnable) | TF-Restormer |
| EGA | efficient global attention | SepReformer / TF-CorrNet |
| CLA | convolutional local attention | SepReformer / TF-CorrNet |
| GCFN | gated convolutional feed-forward network | SepReformer |
| ESSD | early-split shared decoder | SepReformer |
| MSC | multi-scale convolution | NeXt-TDNN |
| EFN | efficient feed-forward network | TF-CorrNet |
| TS-ConvNeXt | two-step ConvNeXt | NeXt-TDNN |
| ConvFFN | convolution feed-forward network | TF-Restormer |
| SepRe | separation-and-reconstruction | SepReformer |

작명 원칙 — _module 역할 + 처리 axis_ prefix (T- / F- / CS-). 자주 등장 약자만 본문 도입.

## 6. 외부 baseline / 인용 친숙도

| baseline | venue / 출처 | 자리 | 빈도 |
|---|---|---|---|
| **TF-GridNet** (Wang 2023) | TASLP 2023 | TF-CorrNet / TF-Restormer main comparison | 매우 자주 (TF dual-path SOTA) |
| **TF-Locoformer** (Saijo 2024) | WASPAA 2024 | TF-Restormer / Stack Less main GSR baseline | 자주 (universal SE SOTA) |
| **Conv-TasNet** (Luo & Mesgarani 2019) | TASLP 2019 | SepReformer / SS 일반 | 매우 자주 (time-domain SS origin) |
| **DPRNN** (Luo 2020) | ICASSP 2020 | SepReformer | 자주 (dual-path 패러다임 origin) |
| **Sepformer** (Subakan 2021) | ICASSP 2021 | SS 본문 | 자주 (transformer SS 원조) |
| **DPTNet** (Chen 2020) | Interspeech 2020 | SS 본문 | 가끔 |
| **BSRNN** (Luo & Yu 2023) | ICASSP 2023 | TF-Restormer dual-path 자리 (간접) / 음악 분리 | 가끔 |
| **MP-SENet** (Lu 2023) | Interspeech 2023 | Stack Less | 자주 (TF dual-path SE baseline) |
| **TasNet** (Luo & Mesgarani 2018) | ICASSP 2018 | SepReformer | 자주 |
| **SuDoRM-RF** (Tzinis 2020) | MLSP 2020 | SepReformer related work | 자주 |
| **QDPN** (Rixen 2022) | Interspeech 2022 | SepReformer related work | 자주 |
| **TDANet** (Li 2023) | ICLR 2023 | SepReformer related work | 가끔 |
| **A-FRCNN** (Hu 2021) | NeurIPS 2021 | SepReformer related work | 가끔 |
| **VoiceFixer** (Liu 2022b) | Interspeech 2022 | TF-Restormer GSR baseline | 자주 (Mel vocoder-based GSR) |
| **StoRM** (Lemercier 2023) | TASLP 2023 | TF-Restormer GSR baseline | 가끔 (diffusion STFT GSR) |
| **UNIVERSE / UNIVERSE++** (Serrà 2022 / Scheibler 2024) | NeurIPS 2022 / ICASSP 2024 | TF-Restormer GSR baseline | 자주 (diffusion GSR) |
| **FINALLY** (Babaev 2024) | NeurIPS 2024 | TF-Restormer latest comparison | 자주 (perceptual loss / Mel-vocoder baseline) |
| **ECAPA-TDNN** (Desplanques 2020) | Interspeech 2020 | NeXt-TDNN base | 매우 자주 (SV) |
| **ResNet** (He 2016) | CVPR 2016 | NeXt-TDNN baseline | 자주 |
| **ConvNeXt / ConvNeXt-V2** (Liu 2022 / Woo 2023) | CVPR 2022 / 2023 | NeXt-TDNN motivation | 자주 |
| **Conformer** (Gulati 2020) | Interspeech 2020 | TF-CorrNet baseline | 자주 (local + global attention) |
| **BLSTM** | classical | TF-CorrNet baseline | 가끔 |
| **WPE** (Nakatani 2010) | TASLP 2010 | dereverberation classical | classical |
| **Linformer** (Wang 2020) | arXiv 2020 | TF-Restormer freq module 영감 | 자주 |
| **SpatialNet** (Quan & Li 2024a) | TASLP 2024 | TF-Restormer freq module 영감 | 자주 |
| **MAE** (He 2022) | CVPR 2022 | TF-Restormer asymmetric encoder-decoder 영감 | 자주 |
| **Mamba** (Gu & Dao 2024) | COLM 2024 | TF-Restormer streaming variant | 자주 |
| **DeepFilterNet** (Schroter 2022) | ICASSP 2022 | multi-tap filtering lineage | 가끔 |
| **gpuRIR** (Diaz-Guerra 2021) | Multimedia Tools 2021 | RIR simulation | TF-CorrNet |
| **Ephraim & Malah** (1984) | TASSP 1984 | SE classical | TF-Restormer intro |
| **Pascual SEGAN** (2017) | Interspeech 2017 | GAN-based SE | TF-Restormer intro |
| **Paulus & Torcoli** (2022) | DAFx 2022 | SFI 원조 | TF-Restormer §1 |

핵심:

- **SS** — TF-GridNet · Sepformer · DPRNN · Conv-TasNet 사대장.
- **Restoration** — TF-Locoformer · VoiceFixer · UNIVERSE · FINALLY · StoRM.
- **SV** — ECAPA-TDNN · ResNet · ConvNeXt.
- **Dereverberation** — WPE classical 기준.

> Note: 외부 모델 연도 fingerprint (TF-GridNet 2023 / SpatialNet 2024a / sBERT Saeki 2024 / Mamba Gu & Dao 2024) 자리 본인 paper bib 후속 page (3+) cross-check 의무 (factcheck QA F6).

## 7. 사용 데이터셋

### 7.1 SE / restoration

| 데이터셋 | 자리 | 사용자 paper |
|---|---|---|
| **VCTK** / **VCTK-0.92** | clean speech | TF-Restormer SSR 학습 |
| **VoiceBank+DEMAND** (Valentini) | SE benchmark | Stack Less SE dedicated |
| **DNS Challenge 2020** (Reddy) | denoising noise source | Stack Less / TF-Restormer simulation |
| **UNIVERSE data** (Serrà 2022) | GSR eval (100 synthetic, f_E = f_D = 16 kHz) | TF-Restormer |
| **URGENT 2025** | real-world restoration | TF-Restormer |
| **DAPS** | restoration / BWE | TF-Restormer |
| **DEMAND** | noise corpus | SE benchmark |

### 7.2 SS

| 데이터셋 | 자리 | 사용자 paper |
|---|---|---|
| **WSJ0-2mix** / **WSJ0-{2,3,4,5}mix** | clean SS standard | SepReformer / SR-CorrNet |
| **Libri2Mix** | SS noisy variant | SepReformer |
| **WHAM!** / **WHAMR!** | noisy / reverb SS | SepReformer |
| **WSJ-CAM0** | REVERB 원본 발화 | IF-CorrNet |

### 7.3 CSS / dereverberation / ASR robustness

| 데이터셋 | 자리 | 사용자 paper |
|---|---|---|
| **LibriCSS** (overlap 0S/0L/10/20/30/40) | CSS eval | TF-CorrNet 10-hour 7-channel / Statistical Beamformer / SR-CorrNet |
| **CHiME-4** (dt05 / et05, sim / real) | ASR robustness | Statistical Beamformer |
| **REVERB Challenge** (SimData / RealData, FAR / NEAR) | dereverberation | IF-CorrNet |
| **Librispeech** | clean source / ASR | TF-CorrNet (training simulation) |
| **gpuRIR** | RIR generator | TF-CorrNet (T60 ∈ [0.2, 0.6] s) |

### 7.4 SV

| 데이터셋 | 자리 | 사용자 paper |
|---|---|---|
| **VoxCeleb1** (O / E / H — Hard 가장 어려움) | SV eval | NeXt-TDNN |
| **VoxCeleb2** | SV training | NeXt-TDNN |
| **MUSAN** / **RIR** | augmentation (Kaldi recipe) | NeXt-TDNN |

### 7.5 등장 안 함

- `WSJ0-3mix` (3 speaker variant) — 사용자 paper 안 직접 안 봤음.
- `LJSpeech` / `ESC-50` / `AudioSet` — TTS / non-speech audio 자리.

## 8. Notation 관례

paper 본문에서 일관:

- complex STFT — $\mathbf{X} \in \mathbb{R}^{F \times T \times 2}$ 또는 $\mathbb{C}^{F \times T}$. real / imaginary 두 채널 마지막 dim.
- encoder feature — $\mathbf{Z} \in \mathbb{R}^{F_E \times T \times C_E}$.
- decoder output STFT — $\mathbf{Y} \in \mathbb{R}^{F_D \times T \times 2}$.
- feature tensor — $\mathbb{R}^{T \times F \times C}$ 또는 $\mathbb{R}^{C \times T \times F}$. dual-path 자리 $T$, $F$ 두 축 명시.
- block / stage 수 — $B$ (block 수), $R$ (repeat), $B_E$ / $B_D$ (encoder / decoder block).
- channel dim — $C_E$ / $C_D$. xSFI _asymmetric_ 자리 $C_E > C_D$, $B_E > B_D$.
- frequency bin 수 — $F_E$ / $F_D$. frame 수 — $T$.
- sampling rate — $f_E$ / $f_D$ (encoder / decoder side). decoupled rate 시그니처.
- attention — $\mathbf{Q}, \mathbf{K}, \mathbf{V}$. extension query $\mathbf{Q}_{\text{ext}}$.
- multi-channel observation — $\mathbf{x}_{tf} \in \mathbb{C}^M$ at frame $t$, bin $f$.
- direct-path RTF — $\mathbf{h}_{k,f}$. convolutive RTF — $\mathbf{r}_{k,\tau f}$.
- multi-tap deep filter — $\mathbf{w}_{k,tf}$.
- clean source / output — $S_{k,tf}$, $Y_{k,tf}$ / 또는 $\mathbf{S}$, $\mathbf{Y}$.
- ground truth / predicted — $s$ / $\hat{s}$.
- loss — $\mathcal{L}$ calligraphic. component $\mathcal{L}_p$ / $\mathcal{L}_s$ / $\mathcal{L}_g$ / $\mathcal{L}_{\text{fm}}$ / $\mathcal{L}_{\text{hf}}$ subscript.
- weight — $\lambda$, $\lambda_g$ / $\lambda_p$ / $\lambda_s$ subscript.
- model parameter — $\theta$. model output $g_\theta(\cdot)$.
- coefficient — $\alpha$ / $\beta$. PHAT-$\beta$ exponent / super-Gaussian shape.
- TVV — $\lambda_k(\tau)$.
- 행렬 굵은 대문자 ($\mathbf{X}, \mathbf{V}, \mathbf{W}$), 벡터 굵은 소문자 ($\mathbf{x}, \mathbf{w}, \mathbf{h}$), scalar 일반체 ($T, F, C$).
- multi-head — $h$ index, $H$ head 수. speaker / source index — $j$ / $k$, source 수 $J$ / $K$.

## 9. 연구 framing 시그니처 (xSFI / GSR / asymmetric encoder-decoder)

### 9.1 시그니처 framing

paper 본문 framing 에서 반복 등장:

- **Asymmetric encoder-decoder** — encoder 입력 분석 capacity 집중, decoder 합성·복원 light (또는 역할 분리). TF-Restormer / SR-CorrNet / SepReformer 공통.
- **Correlation-to-filter** — mask·spectrum 직접 추정 대신 _correlation 입력 → filter 출력_. IF-CorrNet / SR-CorrNet 시그니처.
- **Dual-path (T / F) backbone** — TF domain 두 축 번갈아 처리. 모든 본인 paper backbone.
- **SFI / xSFI** — sampling rate 의존 제거. xSFI 사용자 신조어 (TF-Restormer ICML 2026), decoupled rate 확장. universal model 의 길.
- **TF dual-path Macaron-style ConvFFN + MHSA / MHCA + RoPE** — 본인 표준 transformer block.
- **Stage-wise / progressive reconstruction** — decoder stage 마다 점진 정제, 각 stage loss supervision. SepReformer / SR-CorrNet.
- **Decoupled / matched input-output rate** — TF-Restormer 신조어 framing. 기존 가정 한계 → 본인 framing 해소.
- **Conditional information-flow structure** — TF-Restormer 신조어. encoder input band 분석 → decoder query missing band 합성.
- **Early split vs late split** / **ESSD** — SepReformer 신조어. feature split timing design choice 정형화.
- **Progressive refinement** / **block reusing / block stacking** — Stack Less 핵심 framing. 동일 block 반복 점진 정제.
- **Spatial correlation** — TF-CorrNet 차별점. inter-microphone 차이가 spatial info source.
- **Projection-based spectral inductive bias** — TF-Restormer freq module (Linformer 영감).
- **Signal fidelity vs perceptual quality** — TF-Restormer metric framing. signal 충실도 + perceptual 품질 동시 달성. TF-Restormer Table 1 _signal fidelity_ (PESQ / SDR / LSD / MCD) + _perceptual quality_ (sBERT / UTMOS / DNSMOS) 두 column group 분리.

### 9.2 metric 묶음 — 도메인별 표준

`project_user_paper_figure_style.md` §6 + cross-aspect §4 일치.

| 도메인 | 표준 metric set |
|---|---|
| denoising / SE (VoiceBank+DEMAND dedicated) | PESQ-WB / PESQ-NB / STOI(%) / SI-SDR(dB) + CSIG / CBAK / COVL / SSNR |
| restoration (universal GSR) | _signal fidelity_ (PESQ↑ / SDR↑ / LSD↓ / MCD↓) + _perceptual quality_ (sBERT↑ / UTMOS↑ / DNSMOS↑) — 두 묶음 분리 |
| separation | SI-SNRi(dB) / SDRi(dB) 짝 |
| dereverberation | CD↓ / SRMR↑ / LLR↓ / SNRfw↑ / PESQ↑ |
| BWE / SR | LSD↓ / NISQA↑ |
| SV | EER(%) / minDCF |
| CSS | WER(%) on LibriCSS |
| ASR robustness | WER(%) on CHiME-4 |

_signal fidelity vs perceptual quality 두 그룹 분리_ 는 universal restoration 자리 사용자 시그니처 — 일반 SE paper 에서 흔치 않음.

### 9.3 표기 / 어조

paper 본문 일관 패턴.

- 약자 첫 등장 자리 full form 풀어 쓰기 — `signal-to-distortion ratio (SDR)` / `multi-head self-attention (MHSA)` / `time-frequency (TF) dual-path`. 이후 약자만.
- `T-F` 와 `TF` 두 형태 혼용 — 본문 `time-frequency (TF)` 또는 `TF`, equation / table column 자리 `T-F` 가능.
- `proposed <ModelName>` / `<ModelName> for <task>` — 자기 모델 지칭 패턴.
- `general speech restoration (GSR)` / `general speech enhancement` — task name 자리 _general_ prefix.
- `sub-task` (denoising / dereverberation / BWE / declipping) ↔ `universal model` dichotomy 명확.
- 외부 모델 hyphen 보존 (`Conv-TasNet` / `TF-GridNet` / `TF-Locoformer` — 원 paper 표기 따름).
- 표 column header 화살표 ↑ ↓ 명시 (`PESQ↑`, `LSD↓`, `MAC↓(G/s)`).
- ablation 표 row 순서 — (a) baseline → (b) prior → (c) ours 마지막.
- bold = best per column, underline = second-best.
- footnote dagger — † 외부 정보 / 특별 학습 옵션, ‡ dedicated variant, * auxiliary output.
- Figure 1 = overall architecture, Figure 2 = inner block / module 상세 — 거의 모든 본인 paper 공통.

### 9.4 self-referential label

`xSFI` / `SepRe` / `ESSD` — 본인 작품 안 자체 명명 라벨 일관 참조.

### 9.5 loss / training 어휘

- **Perceptual loss + scaled log-spectral loss (S-log)** — TF-Restormer (`s-log1p` 사용자 약자). Babaev 2024 perceptual 짝.
- **Adversarial training** (Mao 2017 lineage) — SFI-STFT discriminator.
- **Time-domain SI-SDR / SI-SNR loss** — separation 표준.
- **Multi-resolution L1 loss** — FFT {256, 512, 768, 1024} IF-CorrNet.
- **Multi-loss stage-wise supervision** — SepReformer / SR-CorrNet decoder stage loss.
- **Robust loss family** — `descending` (사용자 명시, `redescending` 안 씀).

### 9.6 venue 약자

사용자 본인 출판 venue 정식 약자 일관.

- **ICASSP** / **Interspeech** / **NeurIPS** / **ICML** / **ICLR** — 음성·AI top-tier.
- **TASLP** (IEEE Transactions on Audio, Speech, and Language Processing) — speech 저널 top.
- **SPL** (IEEE Signal Processing Letters) — letter 자리.
- **IEEE Access** — open-access 저널.
- **WASPAA** / **MLSP** / **DAFx** — workshop / specialized.

venue 표기 일관 (`ICASSP 2024`, `Interspeech 2025`).

### 9.7 도메인 깊이 신호

paper 본문에서 사용자가 직접 다루는 수준:

- STFT frame duration / hop / window 선택의 _음향학적 의미_ 직접 논의 — "40 ms window with 20 ms hop" / "integer sample counts at typical rates {8, 16, 22.05, 24, 32, 44.1, 48} kHz".
- MLDR super-Gaussian shape parameter $\beta$ 의 _통계 모델_ 측면 수식 유도 (Statistical Beamformer TASLP 2024 §II-D).
- RTF / convolutive transfer function / direct-path vs reverberation 의 _신호 모델_ 수식 (IF-CorrNet / SR-CorrNet).
- PHAT-$\beta$ / SCOT-$\beta$ normalization 수식 비교, $\beta$=0.5 채택 _경험적 근거_.
- ICA / IVA auxiliary function, distortionless / null constraints _Lagrangian formulation_.

→ _statistical signal processing_ (전통 음성 신호 처리) + _deep learning_ (transformer / mamba / dual-path) 두 갈래 모두 깊이. 어느 한쪽 단순 사용자 X.

### 9.8 사용자 배경

- _Sogang University_ 소속 (Department of Electronic Engineering / Department of Artificial Intelligence cross-affiliation). Hyung-Min Park 교수 supervision.
- _박사학위 청구심사_ 통과 단계 — paper 가속 단계.
- _multi-channel processing_ 도 익숙 (TF-CorrNet beamforming). single-channel SE 주 축, multi-channel 동시.
- _정부과제 / 정부과제_ + _industry seminar (기업)_ 양쪽 발표 자리 — 학계 + 산업 동시.

### 9.9 분야 위치 — 종합

사용자는 _TF-domain DNN 기반 speech enhancement / separation / restoration_ 메인 트랙 + _multi-channel beamforming / blind source separation 의 signal processing 전통_ 두 갈래의 _bridging 연구자_. TF dual-path 가 가장 강한 시그니처 키워드. 최근 (2025-2026) 흐름은 _universal / general restoration_ — SFI / xSFI / asymmetric encoder-decoder / query-based modeling.

용어 선호 한 줄 — _SFI / xSFI / TF dual-path / asymmetric encoder-decoder / band-partitioned cross-attention / extension query / scaled log-spectral loss_ 가 사용자 최근 시그니처.

## 사용자 수동 메모

> 본 절 사용자 영역. `/notes --scope user domain add ...` append. analyze-user 는 읽기만, 손대지 않음.

_(아직 비어 있음 — `/notes --scope user domain add ...` 로 첫 항목 추가)_
