# Paper figure / 표 시그니처 (Ui-Hyeop Shin)

> 본 사용자 paper 9 편 (2020-2026, ICML / NeurIPS / ICASSP / Interspeech / T-ASLP / SPL) 에서 추출한 figure / 표 형식의 _반복 패턴_. 분석팀이 본 사용자 paper figure / 표 자산 만들 때 default 로 따른다.

## 1. Architecture diagram

- 전부 **grayscale**. 색 안 씀.
- **wide / landscape** aspect.
- block box + arrow + tensor shape annotation.
- **Figure 1** = system overview, **Figure 2** = unit module 2-panel — 거의 고정 순서.
- 변종 비교는 4-5 panel side-by-side, (a)(b)(c)(d) sub-label.

## 2. Curve plot — 본 사용자의 실제 스타일

스크립트 ground truth: `plot_robust_loss_family.py` / `plot_slog_gradient_curves.py` (2026-05 ICML TF-Restormer cycle 산출).

- **폰트** — `Times New Roman → Nimbus Roman → Liberation Serif → DejaVu Serif` fallback chain, STIX math, 본문 10pt.
- **크기** — 6.4×2.8" landscape (single column) 또는 4.5×2.8" (2-panel side-by-side).
- **임베드** — `pdf.fonttype=42`, `ps.fonttype=42` (ICML / PMLR 검증 통과).
- **palette** (둘 중 자리에 맞는 것):
  - **cool + warm 분리** — baseline `#4C72B0` / `#55A868` / `#8172B2`, comparison `#DD8452` / `#B8860B` / `#7F4F24`, **ours `#C44E52` (빨강, 굵기 2.4)**.
  - **Sequential coral** — `cm.OrRd(np.linspace(0.85, 0.40, n))` ordered variant (decade-spaced w 등) — 어두운 색이 큰 값.
- **선 굵기** — baseline 1.4, ours 2.4 (강조).
- **선 스타일** — solid baseline, dashed `--` / dashdot `-.` / dotted `:` variant 별 차등.
- **legend** — 우상단 `framealpha=0.92, handlelength=2.4, borderpad=0.4`, 2 열 가능.
- **grid** — 옅음 `alpha=0.25, linewidth=0.5, which='both'`.
- **annotation** — 특정 점에 `ax.annotate(label, xy=(x,y), xytext=(x',y'))` 안에 직접. footnote 는 우측 하단 `ax.text(0.99, 0.02, ..., transform=ax.transAxes, fontsize=7.5, alpha=0.8)`.
- legend label 안 ours 는 _"(ours)"_ suffix.

## 3. Scatter — performance vs cost trade-off

- X = MACs (G/s), Y = 성능 metric (SI-SNRi / PESQ / EER).
- bubble size = parameter count (M).
- 정사각형 1:1.
- check mark / 원 마커로 학습 옵션 (DM 등) 표시.

## 4. Spectrogram

- **window 크기 (native sampling rate 별 고정)** — 8 kHz → 256, 16 kHz → 512, 48 kHz → 1024. 다른 rate 는 가까운 값 사용.
- **resample 금지** — 각 신호를 native rate 그대로 STFT.
- **색 축 (`vmin`, `vmax`) 그룹별 통일** — clean / noisy / restored 같은 비교 묶음 안 `imshow(..., vmin=GROUP_VMIN, vmax=GROUP_VMAX)` 고정. 강도 차이가 시각으로 정직히 비교됨.
- **비교 묶음 layout** — 4-panel side-by-side wide aspect (대략 4:1). panel (a) Input / (b)(c)(d) variant 또는 stage. caption 안 panel 식별, figure 안 직접 라벨 적게.
  - 참고 사례: P8 IF-CorrNet Figure 3, P6 Stack Less Figure 5.

## 5. 표 layout 표준

- **column 순서** — `System | Params (M) | MACs (G/s) | [Domain Time/TF] | <Dataset 1 metrics> | <Dataset 2 metrics> | ...`
- Params / MACs 는 _좌측_ (성능 metric 보다 먼저).
- column header 에 화살표 ↑↓ 명시 (`PESQ↑`, `LSD↓`).
- **row 순서** — input/baseline (Noisy / No Processing / Oracle) → prior methods (chronological) → ours (size 순 tiny / small / base / medium / large).
- **강조** — best per column = **bold**, second-best = _underline_.
- **footnote** — `†` 외부 정보 · `‡` dedicated variant · `*` auxiliary output (inference 불필요).
- **ablation 묶음** — Table N(a) / Table N(b) sub-table 분할.

## 6. 도메인별 metric set

| 도메인 | metric column 그룹 |
|---|---|
| Speech enhancement / denoising | PESQ-WB / PESQ-NB / STOI(%) / SI-SDR(dB) (+ 선택 CSIG / CBAK / COVL / SSNR) |
| **Universal speech restoration (시그니처)** | _signal fidelity_ (PESQ↑ / SDR↑ / LSD↓ / MCD↓) 와 _perceptual quality_ (sBERT↑ / UTMOS↑ / DNSMOS↑) — **두 group 분리** |
| Speech separation | SI-SNRi(dB) / SDRi(dB) — 둘 항상 같이 |
| Dereverberation | CD↓ / SRMR↑ / LLR↓ / SNRfw↑ / PESQ↑, SimData / RealData 분리 |
| Bandwidth extension / super-resolution | LSD↓ / NISQA↑ |
| Speaker verification | EER(%) / minDCF, VoxCeleb1-O/E/H 셋 셋트 |
| Continuous speech separation | WER(%) on LibriCSS, overlap 0S/0L/10/20/30/40 |
| ASR robustness | WER(%) on CHiME-4 dt/et/sim/real |

_signal fidelity + perceptual quality 두 group 분리_ 가 universal restoration 자리에서 본 사용자의 시그니처. 한 group 만 보고 결과를 평가하지 않음.

## 7. ours 강조 패턴

- curve / scatter — 빨강 `#C44E52`, legend "(ours)" suffix.
- 표 — bold per column, ours row 는 `\midrule` 로 prior methods 와 분리.

## 8. 참조 paper 일람 (시그니처 추출 source)

| # | 제목 | venue | 연도 |
|---|---|---|---|
| P1 | Auxiliary-Function-Based IVA with Generalized Inter-Clique Dependence | IEEE Access | 2020 |
| P2 | Statistical Beamformer with Non-stationarity and Sparsity (ICA-based) | T-ASLP | 2024 |
| P3 | NeXt-TDNN — Multi-Scale Temporal Convolution for Speaker Verification | ICASSP | 2024 |
| P4 | SepReformer — Asymmetric Encoder-Decoder for Speech Separation | NeurIPS | 2024 |
| P5 | TF-CorrNet — Spatial Correlation for Continuous Speech Separation | SPL | 2025 |
| P6 | Stack Less, Repeat More — Block Reusing for Progressive SE | Interspeech | 2025 |
| P7 | TF-Restormer — Query-Based Asymmetric Modeling for Speech Restoration | ICML | 2025 |
| P8 | IF-CorrNet — Deep Filter from Inter-Frame Correlations for Dereverberation | (submitted) | 2026 |
| P9 | SR-CorrNet — Asymmetric Encoder-Decoder via TF Correlation for Separation | T-ASLP (submitted) | 2026 |

**도메인 줄기** — time-frequency dual-path DNN (separation / SE / dereverberation / restoration), multi-channel + monaural 모두. _correlation 을 학습 대상으로 강조_ 한 CorrNet 패밀리 (P5/P8/P9), _asymmetric encoder-decoder_ 가 반복 등장 (P4/P7/P9), classical 신호처리 (P1 IVA / P2 ICA-based beamforming) 도 깊은 background.
