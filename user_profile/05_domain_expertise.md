---
aspect: domain
owner: 사용자
mode: init
updated: 2026-05-26
source: paper PDF 8 + 사용자 메모리
consensus: 3-instance (run A/B/C, 강한 일치)
---

# 05. 도메인 전문성

> 주력 분야·약자·계보. **모든 sub-agent 가 도메인 약자 인지에 참조** (figure caption / 슬라이드 / paper / plan / 변수명). 메인 Claude 가 사용자 발화 약자 해석 시 참조.

## 1. 주력 도메인 (3/3)

- **핵심: neural speech separation / enhancement / restoration**, **TF(time-frequency) domain dual-path** backbone. SS·SE·dereverberation 을 하나의 구조적 패러다임으로 통합하려는 방향.
- 비중: **Speech Separation 중심**(특히 회의록 CSS — LibriCSS) > SE/denoising > dereverberation > restoration(GSR/SSR).
- 보조/초기: statistical beamforming(TASLP, neural 이전 DSP 토대), speaker verification(NeXt-TDNN, ICASSP).
- 궤적: statistical beamforming/ICA → TF dual-path SS/CSS → asymmetric encoder-decoder 통합 restoration → rate-agnostic restoration.
- **약점 영역**: telephony/codec 앞단 DSP — 깊지 않음(메모리). 해당 약자는 풀이 1줄 동반 권장.

## 2. 저자 시그니처 기법 (3/3)

- **TF dual-path modeling** (time/freq 축 교대 처리)
- **asymmetric encoder-decoder** + early-split + lightweight synthesis
- **SepRe (Separation-Reconstruction)** — SepReformer 계열
- **correlation-to-filter** (spatial · inter-frame · spatio-spectro-temporal correlation, PHAT-β / SCOT-β)
- **deep filtering** (multi-frame multi-channel TF complex filter)
- **attractor-based dynamic split** (variable-speaker)
- **xSFI** (decoupled input-output sample rate / frequency extension query)
- **block reuse / progressive refinement**, **RoPE**, **Mamba/SSM streaming**, **s-log1p loss**
- self-citation chain 뚜렷: TF-CorrNet(SPL) → IF-CorrNet → SR-CorrNet → TF-Restormer(ICML), SepRe(NeurIPS) 교차 결합.

## 3. 약자 사전 (3/3 — 외부 표준 vs 사용자 고유 구분)

### Task / 평가
- **SS** Speech Separation · **SE** Speech Enhancement · **CSS** Continuous Speech Separation · **SV** Speaker Verification · **BWE** Bandwidth Extension · **SSR** Speech Super-Resolution/Restoration · **GSR** General Speech Restoration · **dereverb** dereverberation
- **SI-SDR/SI-SNR(i)** Scale-Invariant Signal-to-Distortion/Noise Ratio (improvement) · **PESQ** · **STOI/eSTOI** · **LSD** Log-Spectral Distance · **MCD** Mel-Cepstral Distortion · **SRMR** · **DNSMOS/UTMOS/NISQA/WVMOS** non-intrusive MOS 예측 · **sBERT** SpeechBERTScore · **WER/CER** · **EER/minDCF** (SV) · **RTF** Real-Time Factor
### 신호 처리
- **TF** Time-Frequency · **STFT/iSTFT** · **SFI** Sampling-Frequency-Independent · **IPD** Inter-channel Phase Difference · **PHAT** Phase Transform · **SCOT** smooth coherence transform · **wSCM** weighted Spatial Covariance Matrix · **ICA** · **RIR** Room Impulse Response · **SNR**
### 아키텍처/모듈
- **MHSA/MHCA** Multi-Head Self/Cross Attention · **RoPE** Rotary Positional Embedding · **SSM** State Space Model (Mamba) · **TDNN** · **GRN** Global Response Normalization · **ConvFFN/GLU/SwiGLU**
### Beamforming
- **MVDR/MPDR/MLDR** · **IVA**

### ⚠️ 중의성 주의
- **SR** — Separation-Reconstruction(SepRe) vs Super-Resolution vs Speech Restoration: 문맥 확인.
- **SE** — Speech Enhancement(task) vs Squeeze-and-Excitation(layer): 문맥 확인.
- 사용자 고유 명명(SepRe, late-split/early-split, xSFI, *-CorrNet family)은 **외부 표준 약자 아님** — 외부 독자용 글에선 풀이 동반.

## 4. 벤치마크·데이터셋 (3/3)

- SS: WSJ0-{2,3,4,5}mix, WHAM!/WHAMR!, Libri2Mix
- CSS: LibriCSS, AMI
- SE/denoising: DNS(2020), VoiceBank+DEMAND
- restoration/SR: VCTK, URGENT2025, UNIVERSE
- dereverb: REVERB · beamforming: CHiME-4 · SV: VoxCeleb1/2 · 기타: EARS, LibriSpeech

## 5. 연구 계보 (3/3)

- separation 계보: **TasNet → DPRNN → Sepformer → (본인) SepReformer → TF-GridNet / TF-Locoformer(TF dual-path) → CorrNet 독자 노선**. 주 baseline = TF-Locoformer · TF-GridNet.
- SV: ConvNeXt-V2 ← ECAPA ← Res2Net. beamforming: MVDR/MLDR + IVA.

## 6. 학회·저널 선호 (3/3)

- architecture/theory + ablation → **NeurIPS / ICML / ICLR**
- experimental/practical → **ICASSP / Interspeech**
- journal → **TASLP / SPL (IEEE Signal Processing Letters)**
- preprint → arXiv eess.AS
- **ICML 2026 TF-Restormer accept 확정** (현 camera-ready 대상).

## Open Questions

- TF-CorrNet 의 SPL 최종 게재는 미확정(arXiv 2509.16481, 2025-09 제출 단계) — venue 표기 "SPL" 은 잠정. 외부 인용 시 확인.
- 사용자 고유 약칭(s-log1p 등)은 paper 본문 풀이("scaled log-spectral loss")와 병기 권장.

## 사용자 수동 메모

(없음 — `/notes --scope user domain` 로 추가)
