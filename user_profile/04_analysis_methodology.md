---
aspect: analysis
last_init: 2026-05-26
version: 2.5
---

# 분석 / 실험 방법론

> 자료팀 / 연구팀 / 기획팀 / 개발팀 (코드 안 metric·검증) / 편집팀 / 메인 Claude default.
> verbatim quote·코드 스니펫·Open Question·source 일람 → `_internal/aspect_analysis_draft.md`.

## 1. 데이터 split / dynamic mixing

- task 별 _커뮤니티 표준 dataset_ 그대로 씀. 자주 갈아타지 않고, 새 task 자리만 새 dataset 추가 (TF-Restormer URGENT 2025 신규).
- 표준 묶음 정리 — GSR `UNIVERSE 합성 100 sample` (TF-Restormer §5.1), denoising `VoiceBank+DEMAND` (Valentini-Botinhao 2017, 824 utterance, SNR 2.5/7.5/12.5/17.5 dB test), SSR `VCTK-0.92` (Yamagishi 2019, 8→16 / 8→24 / 8→44.1 / 16→48 kHz), separation `WSJ0-2mix·WHAM!·WHAMR!·Libri2Mix`, CSS `LibriCSS` (10-hour 7-channel), dereverb `REVERB Challenge SimData+RealData`, ASR `CHiME-4`, OOD MOS `VoxCeleb·URGENT 2025·DNS Challenge 2020·REVERB Challenge`.
- segment / sampling rate 분리 명시 — separation 4 s + train 8 kHz (SepReformer §4.1), TF-CorrNet 2.4 s + batch 2 + 40k utterance/epoch (§IV-B), TF-Restormer 16 / 22.05 / 24 / 44.1 / 48 kHz 모두 integer sample 보장 위해 40 ms window + 20 ms hop 고정 (ms 단위 표기).
- evaluation rate ≠ train rate. varying length input 처리.
- simulation 자리 paper 별 분리 명시 — IF-CorrNet `T60 0.2-0.8 s / SNR 20 dB`, TF-CorrNet `T60 0.2-0.6 s`, StackLess `train SNR -5~15 dB / eval 0~25 dB`, VoiceBank+DEMAND `train SNR 0/5/10/15 dB`. 합치지 않음.
- 재현 가능 모듈 명시 의무 — RIR 도구 (gpuRIR Diaz-Guerra 2021) + noise corpus (DNS) + SNR / T60 range 숫자 명시. TF-Restormer 자리 추가 distortion (codec / downsampling) + fE = 8 또는 16 kHz random downsample. CSS 자리 average overlap ratio ≈ 50 %, diffuse + colored white noise 조합.
- dynamic mixing model size 별 차등 — SepReformer-L 만 DM, T/S/B/M 표준 set. SR_CorrNet `_dynamic_mixing` 자리 train 자리 random speaker 두 sample 골라 on-the-fly mix, same-speaker 회피 check + random gain ±3 dB.
- multi-rate train + multi-rate eval (TF-Restormer 자체 특징) — `_downsample_8k` (engine.py L134-140) 50 % 확률 16→8 kHz random downsample, `target_downsample` (L142-151) `fs_list_src` random choice. 한 model 로 multi-rate 처리, 논문 §4 _"various sampling rates"_.
- RandSpecAugment 자리 train phase 별 config 분리 — `engine.py` L57 `self.spec_aug = util_engine.RandSpecAugment(**self.config["engine"][self.train_phase]["RandSpecMasking"])`.

## 2. Baseline 비교

- **dedicated vs universal 두 묶음 병치** — denoising dedicated `DB-AIAT·MP-SENet·TF-Locoformer`, SSR dedicated `NVSR·Frepainter·AP-BWE·VoiceFixer`. universal `VoiceFixer·StoRM·UNIVERSE·UNIVERSE++·FINALLY·TF-Locoformer`. 본인 모델이 두 묶음 모두에서 경쟁력 있는지 보여주는 framing.
- **footnote 정직성 우선** — `†` 사전학습 모델 사용 또는 원 paper 보고치 (재현 X), `‡` dedicated task-specific retrain 결과, `*` dedicated 학습. _숫자 한 줄보다 footnote 정직성_ 우선. TF-Restormer caption verbatim — _"†We utilized pretrained models from implementation code from UNIVERSE++..."_ (Table 1) / _"†Dedicated models trained specifically for denoising"_ (Table 2) / _"†The models require fixed output sampling rates ... thus evaluated by upsampling the input"_ (Table 3) / _"‡Dedicated models trained specifically for super-resolution"_ (Table 3).
- **self-task-matched variant 두 자리** — `TF-Restormer (off)` universal training (다중 task / 다중 rate 한 model), `TF-Restormer (on)` task-matched fine-tune, `TF-Restormer (off†)` 추가 variant. _공정 비교_ + _potential ceiling_ 동시 제공.
- **size-matched control** — `w/ MHCA (small)` 행 자리 11.6 M (encoder-only) / 30.1 M / 10.9 M 두세 사이즈 나란히. parameter 차에서 오는 이득과 구조에서 오는 이득 분리. NeXt-TDNN Table 1 동일 — `Backbone × GRN × K × Params × EER` 자리 ablation cell 행 size 별 나란히.
- **model size sweep** — SepReformer T/S/B/M/L 한 표 안 backbone sweep. NeXt-TDNN Table 2 자리 mobile (≤ 2 M) vs base (≤ 7 M) horizontal section 으로 동일 column 공유.
- **OOD vs in-domain 분리 표** — TF-Restormer Table 4 VCTK-trained 을 URGENT 2025 / DNS 2020 / REVERB 자리로 옮겨 _transfer 자체_ 별도 표. self-quote (§5.3) — _"we report this as OOD transfer evidence rather than a controlled in-domain benchmark"_. 학습 자리만 잘하는 모델 vs 전이 잘되는 모델 분리.

## 3. Ablation 패턴

- **knock-out (single-axis 원칙)** — TF-Restormer Table 5 가 대표. encoder-only / w/o MHCA / w/ MHCA / w/ MHCA (small) 4 자리, 한 자리만 변경 다른 자리 default 고정. 수치 — 11.6 M / 151.3 G / LSD 2.12 / NISQA 4.21 (encoder-only), 30.8 / 252.4 / 1.04 / 4.33 (w/o MHCA), 30.1 / 240.8 / 0.89 / 4.53 (w/ MHCA), 10.9 / 89.2 / 1.36 / 4.38 (small).
- **knock-in** — SepReformer §5.2 SepRe 메커니즘을 Conv-TasNet / Sepformer 외부 separator 에 끼움. Conv-TasNet 15.3 → 19.5 (SepRe, 5.7 M), Sepformer 20.4 → 22.7 SI-SNRi (SepRe, 28.0 M). _한 architecture 만의 특수성_ 의심 차단, self-method _generalizability_ 증명.
- **hyperparameter sweep (dose-response)** — SepReformer Table 3(a) (BE,BD) depth sweep (1,4)/(2,3)/(3,2)/(4,1). TF-CorrNet Table III R=5/6 (spectral module repetition) + βf=0/1 (PHAT weighting). TF-Restormer Table 7 spectral loss 9 자리 + w_{tf} 10⁻¹·10⁻²·10⁻³ log scale + None / ℓ1 (mag.) / ℓ1 / ℓ2 / ℓ1 (complex) / log1p / s-log1p (adap. w_{tf}). StackLess Table 1 B × R 그리드 (B=1,4,8,12,16 × R=1,4,8,12,16) + B × R = 16 constant-product. IF-CorrNet Figure 2 #taps L=1/3/5/7/9.
- **input × output 2×2 grid** — TF-CorrNet Table IV: correlation Φ × filtering 최상 (SDRi 11.38 / PESQ 1.75), raw+filtering 차하 (9.05/1.46), Φ+mapping 폭락 (-7.64/1.14), raw+mapping 중간 (9.16/1.43). _다른 조합 자체가 왜 안 되는지_ 명시 — raw+filtering 자리 phase 정보 없음, Φ+mapping 자리 phase 부재로 mapping 자체 불가.
- **같은 ablation 여러 dataset 일관성** — TF-Restormer Table 6(a) SFI discriminator separate vs shared 자리 UNIVERSE / VoiceBank+DEMAND / VCTK-0.92 3 자리 검증. _한 dataset 자리 generalization_ 가능성 차단.
- **cell 라벨 자연어** — `w/o X` (변수 제거) / `w/ X` (변수 추가) / `X (small)` (size-matched) / `Shared (SFI)` vs `Separate` (구조 변형). _자연어 라벨이 metric 표 한 칸에 그대로_, 약어 X.
- **mechanism explanation 의무** — Table 다음 문단 _왜 그 방향_ 해석. _functional partitioning_ / _explicit separation_ / _cross-attention_ 메커니즘 단어. 표 단독 종료 X. TF-Restormer Table 5 해석 verbatim — _"Despite having far fewer MACs than encoder-only, this size-matched variant consistently outperforms the encoder-only model across all bandwidth settings, confirming that the gains arise from the explicit separation of analysis and reconstruction and the use of cross-attention rather than increased parameter count or computational cost."_

## 4. Metric set (도메인별 표)

cross-aspect single source of truth.

| task | metric |
|---|---|
| GSR / denoising (universal) | PESQ ↑ / SDR ↑ / LSD ↓ / MCD ↓ / sBERT ↑ + UTMOS ↑ / DNSMOS ↑ |
| denoising (dedicated VoiceBank+DEMAND) | PESQ-WB ↑ / PESQ-NB ↑ / STOI ↑ / SI-SDR ↑ + CSIG / CBAK / COVL / SSNR |
| SSR (VCTK-0.92) / OOD MOS | LSD ↓ / NISQA ↑ (rate 별) — OOD 는 UTMOS / DNSMOS / NISQA |
| separation (offline / online) | SI-SNRi / SDRi (offline) — + PESQ / STOI / WER (online ASR) |
| dereverb / ASR / SV | CD ↓ / SRMR ↑ / LLR ↓ / SNRfw ↑ / PESQ (intrusive SimData) + SRMR (RealData) — WER 4 자리 (dev/test × simu/real) — EER ↓ / minDCF ↓ + Params / MACs / RTF |

- denoising universal vs dedicated _두 묶음 병존_ — TF-Restormer §5.2 동시 보고.
- column header _Signal fidelity_ (PESQ / SDR / LSD / MCD / sBERT) vs _Perceptual quality_ (UTMOS / DNSMOS / NISQA) multi-column span. _수치 한 줄로 우열 X_, 두 묶음 동시 표시 + 본문 trade-off 해석.
- code 4 카테고리 분리 (`engine_eval.py` L189-258) — non-intrusive (wvmos / utmos / dnsmos / dnsmos_sig / dnsmos_bak / nisqa, z-normalized `in_wav_norm = self.normalize(in_wav_16k)`) / intrusive wideband 16 kHz (pesq / stoi, `in_wav_16k`) / intrusive fullband ≤ 48 kHz (lsd / sdr / mcd, `in_wav` fs_src) / downstream 16 kHz (bleu / bertscore / tokendist) / ASR err (wer_whisper / wer_w2v / cer_whisper).
- sBERT (SpeechBERTScore) — TF-Restormer 만 _semantic congruence_ 자리 추가, 2024+ 신규 metric, 다른 paper 자리 안 보임.
- ASR metric _per-utterance 평균 X, corpus-level micro-average_ — `Σerr / Σref_len` (ref_len weighted, `engine_eval.py` L249-258). `metrics[f'{key}_err'] += res_in[0]; metrics[f'{key}_ref'] += res_in[1]`.
- input / output / src 동시 평가 — `suffixes = ['', '_i', '_src']` (L289). `''` model output, `_i` model input (noisy/distorted), `_src` ground truth (reference upper bound). pbar `f"{in_value:.2f}>>{out_value:.2f}"` 로 improvement 실시간. Ground Truth 행 (PESQ 4.50 saturation, LSD/MCD 0.00, sBERT 1.00, DNSMOS 3.33) head-room reference.
- rate 자동 환산 — config `frame_length: int(stft.frame_length * fs/1000)` ms 단위 표기로 rate 별 자동 환산.

## 5. 통계 / variance / seed

- **95 % CI 코드** — `engine_eval.py` L311-314 `cfd_95(x, x_2, n) = 1.96 * std / sqrt(n)` (n=0 자리 0.0 fallback, `std = (x_2/n - (x/n)**2)**0.5`). 모든 metric 자리 x (sum) + x_2 (sum of squares) 누적, batch 끝 자리 `[95% CONFIDENCE SCORE]` log 출력 (L378).
- **paper Table mean only 패턴** — _코드 자리 통계 자체 있으나 paper Table 자리 mean only_. _statistic-aware code, statistic-light paper_. paper 자리 CI 자체 노출 안 함.
- **multiple seed 안 돌림** — SepReformer §4.2 self-quote verbatim _"Note that we did not train the models multiple times, as the deviations in the results are negligible below the significant digits."_ multiple seed 자체 안 돌림 + significant digit (소수점 한두 자리) 가정 + _disclosure_ 한 줄 명시. ICASSP / Interspeech 자리 표준.
- 본인 8 paper 자리 variance 자체 보고 X (묵시). _하나는 명시, 나머지는 묵시_ 정직.
- early-stopping patience — TF-CorrNet §IV-A _"validation loss did not decrease for two consecutive times"_ patience 2 단일 자리 (cross-paper 미확정, `_internal/` open question).
- significant digit — 소수점 한두 자리 자리 표 자체. 그 이하 noise floor 가정.

## 6. 시각화 (scatter / line / 표)

- **efficiency-quality scatter** — SepReformer Figure 5: x=MACs (G/s), y=SI-SNRi (dB), radius=Params (M), color/check=DM 사용. 4 정보 한 figure. _MACs ↓ + metric ↑_ trade-off 한 figure 자리 정리.
- **TensorBoard per-loss-term** — `engine.py` L443-467: `Loss_se/{train,valid}` / `Loss_time/{train,valid}` / `Loss_rep/{train,valid}` / `LearningRate`. adversarial 자리 추가 — `Loss_G_adv/{train,valid}` / `Loss_G_fm/{train,valid}` / `Loss_D/{train,valid}` / `Loss_pesq/{train,valid}`. composite loss 자리 단계별 시각화.
- **spectrogram + audio dump** — `engine.py` L365-380 noisy / enhanced / clean 세 자리 _spectrogram + audio_ 자리 TensorBoard log. validation 자리 random sample (index 10) 자리 epoch 자리 학습 진행 확인, eval 자리 5 sampling (`random_sample_idx=[10, 20, 30, 40, 50]`, `engine_eval.py` L84). IF-CorrNet Figure 3 RealData spectrogram 4 자리 (input / IF-Corr+MF-Filter / SF-Raw+MF-Filter / SF-Raw+SF-Mask) 정성 비교.
- **표 column grouping** — TF-Restormer Table 1 / 2 _Model_ column 5 카테고리 row grouping (Input / Ground Truth / dedicated / universal / proposed). 공정 비교 자리 시각 분리.
- **spectral error scatter** — TF-Restormer Figure 4 raw vs normalized error, _S_{m,t,f} (source magnitude) × |Y_{m,t,f} - S_{m,t,f}|_ scatter. CV inset — raw 2.65 vs normalized 0.28 (with w_{tf} = E_t[S_{m,t,f}]). scale factor w_{tf} 이론 가설 (heteroscedasticity) 정량 motivate. caption verbatim — _"Spectral error versus source magnitude $S_{m,tf}$ on VCTK-SSR (noisy-distorted, 16→48 kHz) testset from Table 3. ... Insets report the coefficient of variation (CV) of the plotted error: (a) raw error and (b) normalized error with $w_{tf} = E_t[S_{m,tf}]$."_
- **marker 결합** — bold=best / underline=second / `↑↓` direction / `†` footnote / `*` 추가. 4 mark 모두 caption 의 첫 두 줄 안 정의 의무.
- **본문 참조 어휘** — _"As shown in Table X"_ / _"In Table X"_ / _"As shown in Table X(a), TF-Restormer achieves ..."_ 첫 자리 표시 → 결과 해석 바로 이어붐. table → 해석 흐름 한 호흡.
- **hyperparameter sensitivity line plot** — IF-CorrNet Figure 2 #taps L=1/3/5/7/9 자리 PESQ + SRMR 자리 FAR vs NEAR 4 condition 자리 sensitivity trend. PESQ peak L=3, SRMR peak L=5 → trade-off 명시 → conservative L=3 채택.

## 7. Failure mode / qualitative

- **trade-off framing** — _failure 자체_ X, _trade-off_ 로. TF-Restormer §5.2 self-quote verbatim — _"While not surpassing dedicated denoising models in raw signal metrics, TF-Restormer achieves more consistent gains, showing strong generalization despite being designed for universal restoration."_ universal 자리 over-modifying clean inputs 자리 fundamental limit 인정.
- **자기 모델 약점 표 그대로 노출** — TF-Restormer (on) 행 SDR 12.11 < (off) 13.45 같은 _자기 모델 약점 자체_ 표에 그대로 두고 본문 해석. on/off trade-off 정직 보고.
- **head-room 어휘** — _"remains the principal direction for future work"_ / _"open whether ... better suit"_ / _"leaves open"_ 명시 (TF-Restormer §6, footnote 2). 자기 모델 한계와 _열린 질문_ 명시.
- **OOD 별도 section** — TF-Restormer §5.3 real-recorded + OOD 4 dataset (VoxCeleb / URGENT / DNS / REVERB) _paired reference 없음_ → non-intrusive MOS only. _"OOD transfer evidence rather than a controlled in-domain benchmark"_. _benchmark vs OOD transfer_ 두 자리 분리 보고.
- **타사 결과도 trade-off 어휘** — VoiceFixer _"improves MOS but sacrifices fidelity"_, FINALLY _"highest perceptual quality yet lacks signal fidelity"_. _한쪽만 본 모델_ 을 _trade-off 가 있는 모델_ 로 본다.
- **본인 모델 해석 어휘** — _balanced improvements_ / _consistent gains across diverse degradations_ / _stable performance comparable to dedicated models_ / _robust generalization_. 사용자가 _최고점 한 칸_ 보다 _전체 cell 균형_ 가치 매김.
- **mechanism explanation** — _"Because the SFI representation aligns TF structure across sampling rates, the unified discriminator receives more coherent supervision"_. correlation X, mechanism O.
- **conservative baseline 채택** — IF-CorrNet self-quote verbatim _"Overall, the results reveal a trade-off between dereverberation strength (SRMR) and speech distortion sensitivity (PESQ). Considering both metrics and stability across microphone distances, we adopt L = 3 as the baseline configuration."_ single best maximize X, stability + 두 metric balance 자리 conservative baseline justify.

## 8. Train·infer engine 자료

- **engine 3-파일 분리** — `engine.py` train (`_train` / `_validate` / `run`), `engine_infer.py` infer, `engine_eval.py` metric. eval 자리 train loss optional import (`engine_eval.py` L41-54 try/except) 자리 _eval-only config 자리 graceful fallback_.
- **BestModelTracker** — `engine.py` L99-101 `self.best_tracker = util_engine.BestModelTracker(mode="min"); self.best_tracker.restore(self.chkp_path)`. adversarial 자리 G + D 각각 별도, D 자리 single-metric L_D_adv tracking (comment L120).
- **multi-loss composite tracking (train phase 별)** — `engine.py` L420-427. pretrain `val_loss_gen = L_se·w_se + L_rep·w_ssl`. adversarial 5-term `+ L_pesq·w_pesq + L_G_adv·w_gan + L_G_fm·w_fm`. config `train_phase` 한 줄로 phase 전환, composite 자체 다름.
- **progress bar** — train pbar 7 loss (L_time / L_se / L_rep / L_pesq / L_G_adv / L_G_fm / L_D_adv) per-batch 평균 (L268-278). eval pbar (`engine_eval.py` L321-335) `{k: f"{dict_metric_mean[k+'_i']:.2f}>>{dict_metric_mean[k]:.2f}"}` 형태 input→output 자리 _improvement 자체_ 실시간 시각화.
- **`compute_metric` dispatch** — `engine_eval.py` L13 16 metric single API (`from tf_restormer.utils.metrics import compute_metric; val_out = compute_metric(key, in_wav_16k, src_wav_16k, 16000, device=self.device)`). wvmos / utmos / dnsmos / dnsmos_sig / dnsmos_bak / nisqa / pesq / stoi / lsd / sdr / mcd / bleu / bertscore / tokendist / wer_whisper / wer_w2v / cer_whisper.
- **per-key 6 suffix 누적** — `metrics = defaultdict(float)` 자리 `{key}` / `{key}_i` / `{key}_src` / `{key}_2` / `{key}_i_2` / `{key}_src_2` 6 키 한 metric 당 동시 누적. `_update_metrics` helper None-safe. _input / output / source / 분산_ 까지 utterance 누적.
- **unknown n_spks** — SR_CorrNet SS engine `test_unknown_n_spks` 자리 `len(estim_stft) != len(target_stft)` 자리 `zeros_tensor * 1.0e-8` padding 또는 truncate. _practical deployment_ 자리 ground truth known / unknown 시나리오 분기.
- **scheduler** — `if epoch == 1: self.warmup_scheduler.step()` (첫 에폭만 warmup) + 매 step `nn.utils.clip_grad_norm_(model.parameters(), clip_norm)` (gradient 2-norm clip). transformer 표준.
- **w_aux decay** — SR_CorrNet `engine.py` L187 `w_aux = 0.5 * (0.95)**(epoch-100) if epoch > 100 else 0.5`. 초반 강하게 보조하다 후반 약화. hard-coded magic number (0.5 / 0.95 / 100) config 외부화 X.
- **two-phase training fallback** — TF_Restormer `train_phase` / `train_phase_list` 자리 pretrain checkpoint 자리에서 adversarial fallback 복사 (`save_checkpoint_per_nth(... epoch.0000.pth ...)`). 직전 phase weight 시드, config 안 `train_phase` 한 줄 바꿔 phase 전환.
- **SR_CorrNet SE/CSS/SS 세 변형 공통 + 차이** — 공통 utility `setup_optimizer_and_scheduler` / `setup_logging` / `save_checkpoint_optimized`. 차이 — n_spks (단일 source / variable `is_var_spks max_n_spks` / variable `max_n_spks`), loss (MSE_complex + TimePlusMultiResTFL1Loss / MSE_complex PIT / PIT_SISNR_time + PIT_SISNR_mag + PIT_SISNRi), aux (VAD+LOC / VAD+LOC+presence+split_res / presence+split_res), valid metric (PESQ+STOI / loss only / SI-SNRi + SDR/SDRi optional), BSS SDR test (X / X / O `cal_SDRi`).
- **PIT prior_idx caching** — CSS `calculate_separation_loss_with_perm` 자리 perm_idx 반환 → aux loss `prior_idx=perm_idx` 강제 alignment, 재계산 X. main 과 같은 permutation 일관 학습. SS variant 도 동일 패턴 (main time / aux mag / metric SI-SNRi). PIT (Kolbæk 2017) 자리 모든 separation paper 자리 사용.
- **model size 측정** — Params (M) + MACs (G) + RTF 동시 보고. 도구 ptflops + thop + torchinfo 3 자리 (`util_engine.model_params_mac_summary`). 16,000 sample MAC (SepReformer / TF-CorrNet). TF-Restormer Table 1 MAC (G) 자리 UNIVERSE-SSR (fE = fD = 16 kHz). IF-CorrNet RTF (Nvidia RTX 5090) — TF-GridNet 0.081 / IF-CorrNet 0.025.

## 사용자 수동 메모

> 본 절은 _사용자 영역_. `/notes --scope user analysis` 가 append. analyze-user 는 _읽기만_ 하고 손대지 않음.

_(아직 비어 있음 — `/notes --scope user analysis add ...` 로 첫 항목 추가)_
