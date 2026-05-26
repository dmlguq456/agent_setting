---
aspect: writing
last_init: 2026-05-26
version: 2.5
---

# Paper / 한국어 보고서 작성 톤

> 본 카탈로그는 연구팀 / 편집팀 / 기획팀 / 메인 Claude 의 wording 자료 default. paper 본문·연구계획서·rebuttal·camera-ready 모두 같은 dictionary. 분석 source 일람은 `_internal/source_index.md`, 항목별 근거 prose 는 `_internal/aspect_writing_draft.md`.
>
> 분석 source paper 8 편 — TF-Restormer (ICML 2026) / TF-CorrNet (SPL 2025) / StackLess (Interspeech 2025) / NeXt-TDNN (ICASSP 2024) / SepReformer (NeurIPS 2024) / Statistical Beamformer (TASLP 2024) / IF-CorrNet DeepFilterEstimation (arXiv 2026) / SR-CorrNet AsymmetricEncoderDecoderTF (arXiv 2026). 한국어 자료 2 편 — 기초연구 음성향상 복원 v3 / 2 차년도 v6.

---

## 1. 문장 호흡 / 단락 구조

- **한 문장 = 두세 절 묶음 (25-35 words).** 한 절 + `where` / `while` / `by ...ing` / 분사구 한 묶음. 짧은 단정 + 길게 풀어쓴 보충이 같은 단락에 같이 등장.
  - anchor — TF-Restormer Abstract 첫 문장 27 words (`Speech restoration aims to recover ... where input and output sampling rates may differ.`), NeXt-TDNN Abstract `Inspired by recent ConvNet structures, we replace the SE-Res2Net block in ECAPA-TDNN with a novel 1D two-step multi-scale ConvNeXt block, which we call TS-ConvNeXt.` (분사구 + 본동사 + 관계절 한 묶음).
- **한 문장 = 한 claim.** 보충 자료는 새 문장으로 쪼갠다. 콜론·dash 안에 박지 않음. 콜론은 _수식 정의_ 직전 또는 _list_ 자리만.
- **Method 본문 호흡 더 짧고 단단.** Intro 25-30 words 묶음이 Method 자리 한 절 + 분사구로 압축. 수식 직전 한두 문장은 `Given ...` / `where ...` 끝맺음.
  - anchor — TF-Restormer §4.1 scaled log-spectral loss 자리 식 직전 한 문장이 desideratum numbered list 1-2 줄.
- **한국어 보고서 호흡 한 단계 김.** 한 호흡 안에 _필요성 + 대상 + 동작 + 결론_ 모두 묶음. _문법적으로 부적합한 길이라도 한 호흡_.
  - anchor — 연구계획서 v3 §1.1 `원거리에서 음성을 취득하는 경우에 대해서는 필연적으로 발생하는 음성의 왜곡 및 손실을 보정하고자 잡음 및 반향성분을 억제하고 음성 성분을 향상시켜야 할 뿐만 아니라 동시에 손실된 음원 성분을 예측하여 복원시키는 기술이 함께 고려될 필요가 있다.` (한 문장 안에 paper Abstract 의 _환경 + 한계 + 필요성_ 3 단 압축).
- **한국어 단락 연결사 6 종 — 따라서 / 또한 / 한편 / 그러나 / 결론적으로 / 더불어.** 단락 시작 자리 안에서 돌려 씀. 같은 연결사 두 단락 연속 회피.
- **누적 구조 `~ 뿐만 아니라 ~` 같은 단락 안에 두 번 이상.** 한국어 보고서 자리 추가절 누적 양식 빈번.

---

## 2. argumentation 구조

- **Intro 4-5 단 구조.** 도메인 광역 도입 (sub-task lineage) → 최근 paradigm 전환 (`This growing complexity has prompted a shift toward ...`) → 기존 한계 명시 (`however / despite / yet / commonly assume`) → 본 연구 motivation (`These observations motivate ...` / `Inspired by ...`) → contribution bullet 또는 prose.
  - anchor — TF-Restormer §1 `Speech enhancement ... has historically progressed through isolated sub-tasks ...` → `This growing complexity has prompted a shift toward general speech restoration ...` → `Beyond the choice of generative modeling paradigm, existing approaches commonly assume a fixed input–output sampling-rate setting.` → `These observations motivate extended SFI (xSFI) processing ...` → `In summary, our contributions are as follows:`.
  - anchor — NeXt-TDNN §1 lineage (i-vector → d-vector → x-vector → ECAPA-TDNN → ConvNeXt) → contribution 단정 `In this paper, we present a modernized backbone block for TDNN inspired by the recent ConvNeXt structure.`.
- **Gap 에 이름 부여 (self-referential label).** 한 단어 명사구 정의 후 paper 전체에서 같은 라벨로 anchor.
  - anchor — TF-Restormer `xSFI`, SepReformer `information bottleneck` + `ESSD`, SR-CorrNet `SepRe`, IF-CorrNet `inter-frame correlation`.
  - 정의 시점 — Abstract 끝 한 문장 또는 §1 마지막 단락 진입 `We formulate this gap as ...`.
- **Contribution bullet 양식 venue 별 분기.**
  - long-form (ICML / NeurIPS / TASLP) — 긴 한 문장 prose bullet (35-45 words, _what + why_ 한 묶음).
  - short paper (Interspeech / SPL / arXiv short) — bullet 없이 prose paragraph.
  - anchor — TF-Restormer §1 끝 자리 bullet 3 항이 각각 한 문장 prose; IF-CorrNet / TF-CorrNet / StackLess 자리 bullet 자체 없음.
- **Conclusion 짧음 — restate + key claim + future 3 단.** 한 단락 4-6 문장. `In this work, we (proposed / introduced / presented) X for ...` 진입.
  - anchor — TF-Restormer §6 `We presented TF-Restormer for speech restoration under the xSFI setting. ...`, IF-CorrNet §5 `In this work, we introduced IF-CorrNet, a deep filter estimation model for monaural speech dereverberation that explicitly leverages inter-frame correlations rather than raw complex STFT inputs.`, NeXt-TDNN §5 `In this paper, we proposed NeXt-TDNN, a TDNN backbone modernized through ConvNeXt-inspired design.`.
- **Limitations 자체 자리 venue 별 분기.**
  - Interspeech / NeurIPS — _Conclusion 안 분리된 두 번째 단락_ 으로 명시 (StackLess `However, this work has several limitations that should be addressed in future research.`, SepReformer `Limitations and future work.`).
  - ICML 8-page / SPL short — Conclusion 안 통합 또는 Appendix 이동 (TF-Restormer / TF-CorrNet / NeXt-TDNN / IF-CorrNet).
- **Limitations wording — frank 톤.** _focused on X + future studies will Y_ 또는 _study focuses on / consequently / further investigation is needed_ 3 단. 방어형 wording 회피.
  - anchor — StackLess `First, we focused on denoising tasks in non-reverberant conditions. Future studies will investigate the model's performance in reverberant environments to assess its robustness in real-world scenarios.`, SepReformer `Our study focuses on 2-speaker mixture situation [...]. Consequently, we believe that further investigation is needed to validate for more than 2-speaker mixture scenarios.`.

---

## 3. Citation 패턴

- **Pre-cite vs post-cite 혼용.**
  - pre-cite — 저자 이름이 claim 의 주체. 예: `Linformer (Wang et al., 2020) introduced linear projections of key-value ...`.
  - post-cite — 저자 이름이 근거 자리. 구절 끝 bracket. 한 문장 안 서술 anchor 뒤 괄호 묶음.
- **Venue 양식 그대로.**
  - ICML (TF-Restormer) — author-year `(Hu et al., 2020)`.
  - NeurIPS / TASLP / IEEE / arXiv (TF-CorrNet / NeXt-TDNN / SepReformer / Statistical Beamformer / IF-CorrNet / SR-CorrNet) — 숫자 bracket `[46, 47]` / `[3]`.
  - 저자 임의 변형 X (`[Wang20]` 같은 단축 X).
- **한 묶음 인용 — semicolon 구분 + 시간순.** `(Liu et al., 2022b; Serrà et al., 2022)`. 한 문장 안 두세 묶음까지 무리 없이 묶음.
- **sub-task 나열 자리 task 별 1-2 인용 매핑.**
  - anchor — TF-Restormer Intro 도입 sub-task 4 개 (denoising / dereverberation / declipping / BWE) 각각 paper 1-2 개 인용.
  - anchor — SR-CorrNet 도입 paradigm 3 단계 (TasNet / DPRNN / Sepformer) 각각 단일 인용.
- **자기 인용 — venue 별 분기.**
  - long-form (ICML / NeurIPS / TASLP) — third-person verbatim. TF-Restormer Related Work `Shin et al., 2025; Shin & Park, 2026`.
  - arXiv preprint / short paper — third-person 도 가능, `Our earlier work [31]` 강조 wording 도 등장. SR-CorrNet Intro `Our earlier work [31] proposed the Separation-Reconstruction (SepRe) strategy`. (Open Question — long-form 자리는 강조 회피).

---

## 4. 수학·notation

- **첨자 set 고정 — `t / f / F / T / C`.** 시간 = `t`, 주파수 = `f`, 채널 = `C`, frame 수 = `T`, bin 수 = `F`. TF-CorrNet / IF-CorrNet / TF-Restormer verbatim — 작성자의 고정 표기.
- **변수 표기.**
  - italic scalar — $f_E$, $f_D$, $T$, $F$.
  - bold uppercase matrix / tensor — $\mathbf{X}$, $\mathbf{Y}$, $\mathbf{Q}_{\text{ext}}$.
  - bold lowercase vector — $\mathbf{q}_f$, $\mathbf{x}_{tf}$.
  - anchor — SR-CorrNet `$\mathbf{x}_{tf} = [X_{tf1}, ..., X_{tfM}]^T \in \mathbb{C}^M$`, Statistical Beamformer `$\mathbf{x}_k(\tau) \in \mathbb{C}^M$`.
- **Greek loss weight — α / β / w 자리.** loss component weight $\alpha_c$, $w_{tf}$, $\beta$, transition point parameter. italic Greek.
  - anchor — TF-Restormer §4.1 `We use $\alpha_m = 0.6, \alpha_r = 0.2, \alpha_i = 0.2$`.
- **수식 도입 wording 3 어구 — `Given ...` / `Let ...` / `We define ...`.** 수식 직후 `where` 절로 변수 의미 풀이.
  - anchor — TF-Restormer `Given an input $x \in \mathbb{R}^{1 \times N_E}$ with sampling rate $f_E$ ...`, SR-CorrNet `Let the observation of K multi-speakers ...`, IF-CorrNet `We define an auxiliary loss ...`.
- **식 위 motivation + 식 + 식 아래 변수 명세 3 단.** 식 위 desideratum numbered list, 식 다음 paragraph 가 식 의미를 풀어 씀.
  - anchor — TF-Restormer §4.1 scaled log-spectral loss 자리 — 식 위 3 desideratum (monotonically decreasing gradient / unit-height gradient peak / $w_{tf}$ acting as transition-point parameter) numbered list, 식 아래 변수 명세 한 줄.
- **Feature tensor shape 본문 안 동시 등장.** shape + 모듈 분기 한 줄 묶음.
  - anchor — TF-Restormer §3.3 `feature with shape $\mathbb{R}^{T \times F \times C}$ where $F \in \{F_E, F_D\}$`.
- **식 번호 paper 전체 sequential.** `(1) / (2) / (3) / (4)`. `Eq. (3)` 직접 anchor 드뭄 — 식 다음 paragraph 가 식 의미를 풀어 씀.
- **Notation table 본문 X, Appendix 만.** 본문은 첫 등장 시 한 줄 변수 명세만.
- **Multi-line 식 거의 X, 한 줄 식이 default.** paper 4 편 전반 한 줄. multi-line 자리는 derivation 자리에 한정 (Statistical Beamformer Algorithm 1 자리만 예외).

---

## 5. 표·figure 인용

- **Figure inline 인용 동사 5-6 종 — `As shown in Figure N` / `Figure N illustrates / details / shows / depicts / describes / presents`.** 매 figure 마다 한 번씩 본문 inline 인용. 같은 동사 반복 회피.
  - anchor — TF-Restormer §3.2 `As shown in Figure 1, TF-Restormer realizes the xSFI setting through a conditional information-flow structure ...` + `Figure 2 details this realization at the module level.`, SepReformer §3.2 `The detailed architecture of the separator of the proposed SepReformer is illustrated in Figure 2`, SR-CorrNet §III `As illustrated in Fig. 3, SR-CorrNet implements the correlation-to-filter formulation`.
- **Caption 짧음 — 첫 문장 figure subject, 둘째 문장부터 세부.**
  - anchor — TF-Restormer Fig. 1 caption 2 문장 (`Overall architecture of TF-Restormer.` / `A query-based asymmetric encoder–decoder analyzes the native input bandwidth and reconstructs missing high-frequency bands using learnable extension queries.`).
  - Table caption 한 줄. TF-Restormer Table 1 `Results on UNIVERSE data for GSR`. caption 안 결과 wording 없음.
- **Table 인용 — `Table N reports / shows / compares` 짧은 단정.**
  - anchor — TF-CorrNet `In Table I, we compared our proposed TF-CorrNet to the TF-GridNet [15] ...`, NeXt-TDNN `In Table 2, we evaluated our proposed NeXt-TDNN and NeXt-TDNN-l for mobile and base models.`.
- **본문에 수치 verbatim dump 회피, 정성 wording 으로 anchor.** _highest / lowest / competitive / strong / more than two times faster_ 같은 비교 결론·추세로 anchor. 표를 가리키며 비교 결과만 풀어 씀.
  - anchor — NeXt-TDNN §4 `Compared to the conventional models, our models consistently achieved improved performances in both mobile and base model sizes. In particular, our NeXt-TDNN with $B=1$ achieved better result than ECAPA-TDNN with more than two times faster speed.` (수치 1.10% / 0.51 / 1.60 자리 본문에 안 박고 정성 wording).
  - anchor — TF-Restormer §5.2 `a trend confirmed in Table 2` 같이 별도 wording 으로 table 사이 일관성 강조.
- **Best anchor + footnote 보조.** best = bold, second-best = underline, dagger / 별표로 footnote.
  - anchor — TF-Restormer Table 1 footnote `†We utilized pretrained models ...` / `‡The results are reported in the original paper`.
- **Footnote 으로 implementation 세부 push.** paper 별 1-3 개. 본문 호흡 유지 자리 자체.
  - anchor — TF-Restormer §3.2 footnote `The 40 ms SFI-STFT window fixes the frequency resolution at ...`.
- **`see Appendix X` / `Refer to Appendix Y` anchor.** 세부 confiquration 자리는 Appendix push.
  - anchor — TF-Restormer §3.3 `Refer to Appendix C for detailed model configurations`.

---

## 6. Limitations / Future Work

(§2 _Limitations 자체 자리_ + _frank 톤_ 참조.)

- **한국어 enumeration — `첫째 / 둘째 / 셋째 / 마지막으로`.** 연구계획서 future direction 4-5 항을 enumeration 양식. 영어 paper contribution bullet 의 한국어 mirror.
  - anchor — 연구계획서 v6 §1.1 `그러나 여전히 해결해야 할 과제가 남아 있다. 첫째, 음성 생성 기반 복원 모델의 고도화이다. ...`.
- **Appendix 이동 패턴.** TF-Restormer ICML camera-ready 본문 page range 안 Limitations 단락 부재 → Appendix 이동. ICML 본문 8-page 제약. (Open Question — camera-ready 자리 본문 명시 vs Appendix push 사이 선택 기준).

---

## 7. 한국어 보고서 톤

- **평어 단정형 (`~다 / ~이다 / ~한다`).** 모든 본문 평어. `~ 필요가 있다 / ~ 필수적이다 / ~ 기대한다 / ~ 진행한다` 빈번. 존댓말 X.
- **도메인 영어 verbatim.** 모델·기법·지표 영어 그대로.
  - 모델 — Conformer / MetaFormer / DCCRN / MFNet / MTFAA-Net / Parrotron / VoiceFixer / wav2vec / HuBERT / wavLM / Vall-E / Diffwave / FastDiff / HiFi-GAN / U-Net / RNN / TCN / Transformer / LSTM / MP-SENet / AP-BWE / TF-Locoformer.
  - 지표·전처리 — MSE / Mean Square Error / STFT / Vocoder / Tacotron.
  - 영어 원어 + 한국어 약자 풀이 병기 — _자가지도 학습 (Self-supervised learning; SSL)_.
- **핵심 task wording 은 한국어 유지.** _음성 향상 / 음성 복원 / 음성 합성_, 영어 (Speech Enhancement / Restoration / Synthesis) 는 괄호 안.
- **판교체 회피.** `[[feedback_korean_readability_policy]]` ground truth. 일반 명사·동사·작업 흐름은 한국어 단정형, 도메인 약자만 영어.
- **v3 → v6 톤 변화.** 현 시점 ground truth = v6.
  - v3 = 수동·비인칭 + 당위 (`기술 개발을 수행한다 / 학습이 이루어진다 / 네트워크가 구성된다 / 가능할 것으로 기대한다 / 필수적이다`).
  - v6 = 능동 단정 작업 동사 (`개선한다 / 모색한다 / 구현하고 / 최적화한다`). 영문 paper 능동 We 톤이 한국어 보고서에 mirror.
  - v3 = 수식 driven, v6 = 선행 모델 narrative driven. v6 자리부터 선행 모델 third-person 인용 + restate + enumeration 으로 영문 paper 톤 mirror.
- **Figure 한국어 캡션 부기 (이중 자막).** 영어 원본 캡션 + 한국어 풀이. caption 자리 명사구·체언 종결.
  - anchor — `Figure 1: DCCRN network` + `DCCRN 기반 음성 향상 네트워크 구조`, `마스크 추정 기반 음성 향상 네트워크`, `입력 스펙트로그램 및 추정 마스크, 그리고 출력 스펙트로그램`.
- **번호 bullet — 한국어 번호 + 영어 학술 용어 병기.**
  - anchor — 연구계획서 §2.2 `1) 음성 향상 (Speech Enhancement) / 2) 음성 복원 (Speech Restoration) / 3) 음성 복원 및 향상 통합`.
- **목차 한자어 학술 용어.** _도전성·타당성·필요성·활용 방안·우수성·차별성_.
- **약자 처음 등장 — 한국어 풀이 + 영어 약자.**
  - anchor — `단구간 푸리에 변환 (STFT)` / `Reverberation Time to 60dB (RT60)` / `Low Pass Reverberation Filter (LPF)`.
- **Footnote citation 영어 그대로.** 한국어 자리라도 인용 자체는 영어 verbatim.
  - anchor — 연구계획서 footnote `F. Dang, H. Chen and P. Zhang, "DPT-FSNet: ..." ICASSP 2022 ...`.

---

## 8. Opening / Hook

- **Abstract 첫 문장 — 도메인 상태 동사 진입.** `X aims to ...` / `In general, ...` / `This paper presents ...` / `In this paper, we present ...` / `X has been used in Y task ...`. `We propose ...` / `We introduce ...` 직접 도입은 Abstract _마지막 한두 문장_ 자리.
  - anchor — TF-Restormer `Speech restoration aims to recover clean speech from degraded recordings affected by noise, reverberation, bandwidth reduction, or other distortions, where input and output sampling rates may differ.`.
  - anchor — SepReformer `In speech separation, time-domain approaches have successfully replaced the time-frequency domain with latent sequence feature from a learnable encoder.`.
  - anchor — SR-CorrNet `Speech separation in realistic acoustic environments remains challenging because overlapping speakers, background noise, and reverberation must be resolved simultaneously.`.
  - anchor — TF-CorrNet `In general, multi-channel source separation has utilized inter-microphone phase differences (IPDs) ...`.
  - anchor — StackLess `This paper presents an efficient speech enhancement (SE) approach that reuses a processing block repeatedly instead of conventional stacking.`.
  - anchor — Statistical Beamformer `In this paper, we present a statistical beamforming algorithm as a pre-processing step for robust automatic speech recognition (ASR).` (TASLP 양식 직접 도입).
- **Abstract 3-단 — claim → gap → contribution.** Abstract 길이 venue 별 분포 다르나 흐름 유지.
  - anchor — TF-Restormer `Speech restoration aims to ...` (claim) → `Existing approaches typically assume ...` (gap) → `We formulate this gap as the extended sampling-frequency-independent (xSFI) setting ...` (contribution).
  - Abstract 길이 — ICML (TF-Restormer) 6 문장 / NeurIPS (SepReformer) 11 문장 / arXiv (SR-CorrNet) 9 문장 / TASLP (Statistical Beamformer) 10 문장. 학회 분량 한계에 호흡 조절.
- **Hook 자체 X — 평이한 단정.** attention grabbing / 도발 회피. 도메인 그대로 + 다음 호흡에 gap. `While X has shown remarkable improvement, ...` / `However, the spatial information is fundamentally ...` 순차 진입.
- **Intro 첫 단락 — historical lineage 또는 well-known X problem.** 시점 부사절 + 분야 핵심 문제 + 진보 시점 인용.
  - anchor — TF-Restormer `Speech enhancement (Ephraim & Malah, 1984; Pascual et al., 2017) has historically progressed through isolated sub-tasks with dedicated models such as denoising (...), dereverberation (...), declipping (...), and bandwidth extension or super-resolution (...).`.
  - anchor — SepReformer `For the well-known cocktail party problem [14, 3], single channel speech separation [30] has been improved since the introduction of time-domain audio separation network (TasNet) [46, 47]`.
  - anchor — NeXt-TDNN `With the rise of deep neural networks, the conventional human-crafted embedding feature vector for speaker identity (i-vector) [1] was rapidly replaced with the DNN-based vector (d-vector) [2] in speaker verification.`.
  - anchor — SR-CorrNet `Speech separation is a fundamental task in speech and audio signal processing, serving as a key front-end for applications such as meeting transcription, hands-free communication, hearing aids, and distant automatic speech recognition (ASR).`.
- **한국어 opening — `본 연구는 X 을 Y 하기 위해 ... / 이를 위해 ...`.** 연구과제 명부터 목적까지 한 호흡.
  - anchor — 연구계획서 §0 `본 연구는 원거리 취득 음성에서 발생하는 왜곡 및 손실을 보정하고, 다양한 잡음 환경에서도 안정적으로 동작하는 음성 복원 기술을 개발하는 데 목적이 있다.`.
  - anchor — 제안서 요약 첫 문장 `음성과 같은 음원 신호를 원거리에서 취득하게 될 때, 취득 신호는 음원 성분 뿐만 아니라, 다양한 외부 배경 잡음, 간섭 잡음, 그리고 공간적 반향에 의해 왜곡된다.` (_~ 하게 될 때_ 조건절 + _~ 뿐만 아니라 ~_ 추가절 + _왜곡된다_ 결론).

---

## 9. 운영 wording (paper 안 일관성)

- **시그니처 키워드.** 영문 paper + 한국어 연구계획서 모두 등장.
  - `realistic acoustic environments` — SR-CorrNet / TF-Restormer / 연구계획서 (_원거리에서_).
  - distortion 4 갈래 — noise / reverberation / bandwidth / overlapping speaker. paper 별 조합 변형.
  - `sub-task → general / unified` motivation wording — TF-Restormer / SR-CorrNet.
- **`single unified` 단정 어휘.**
  - anchor — TF-Restormer `TF-Restormer as a single unified model attains balanced fidelity-perceptual quality without redundant resampling`.
  - anchor — SR-CorrNet `a single architecture to handle single-channel, multi-channel, noisy, and reverberant conditions within a common scheme`.
- **능동 We default, 수동은 학습 setup / dataset 자리만.**
  - 능동 We — contribution / 설계 / 결과 진술. `We propose ...` / `We introduce ...` / `We formulate ...` / `We additionally evaluate ...`. TF-Restormer §5 `To validate the effects of the proposed methods, we conduct an ablation study on scaled log-spectral loss, decoder design, and frequency projection module.`.
  - 수동 — 학습 / 평가 setup 보고. `were trained / were measured / was set to`. IF-CorrNet §3.2 `All models were trained on the simulated training set, and the best system was selected using SimData ...`.
- **Algorithm 박스 venue 별 — TASLP 만.** Statistical Beamformer Algorithm 1 = pseudo-code 박스 29 줄 (Initialize / for / Compute / Update / End 형식). TF-Restormer / SepReformer / SR-CorrNet 본문 algorithm 박스 없음.

---

## 사용자 수동 메모

> 본 절은 _사용자 영역_. `/notes --scope user writing` 가 append. analyze-user 는 _읽기만_ 하고 손대지 않음.

_(아직 비어 있음 — `/notes --scope user writing add ...` 로 첫 항목 추가)_
