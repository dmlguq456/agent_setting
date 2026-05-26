---
aspect: analysis
owner: 사용자
mode: init
updated: 2026-05-26
source: 평가 코드 (TF_Restormer/SR_CorrNet metrics·engine·loss) + paper 실험/ablation 절 4편
consensus: 3-instance (run A/B/C, 강한 일치)
---

# 04. 실험·분석 방법론

> 실험 설계·평가·결과 해석 패턴. 자료팀(data-script)·연구팀·편집팀·기획팀이 분석 표현·검증 방법 참조. 메인 Claude 사용자 분석 응답 시 참조.

## 1. 평가 지표 set — task별 분리 (3/3)

- **2축 분류 보고**: "Signal fidelity"(PESQ/SDR/LSD/MCD/sBERT) vs "Perceptual quality"(UTMOS/DNSMOS/NISQA). 단순 나열 회피.
- **restoration/enhancement**: registry 19종 — intrusive(PESQ/STOI/SDR/LSD/MCD/composite 6) + nonintrusive(DNSMOS/NISQA 등 4) + neural(UTMOS/WVMOS 2) + semantic(SpeechBLEU/BERTScore/TokenDist 3) + asr(WER/CER 등 4). MOS 예측기 **3중(DNSMOS/UTMOS/NISQA) 교차 보고**.
- **separation**: SI-SNRi/SDRi 를 **PIT(permutation invariant)**로 감싸 평가.
- **SV**: EER(%)/minDCF/RTF. **CSS**: WER(%).
- metric 마다 적정 sample-rate 코드에서 강제 (PESQ/STOI wideband 16k, LSD/MCD/SDR fullband 48k, ASR 16k).

### 평가 코드 습관
- input/output/source **3-way 누적**(`_i` >> `` >> `_src`)으로 개선폭 실시간 표시.
- **95% CI 코드 레벨 내장**: running sum/sum² 1·2차 moment 누적 → `1.96·std/√n` (`cfd_95`).
- ASR 은 utterance 평균 아니라 **(err, ref_len) tuple 누적 → corpus-level rate** (token-가중 micro-average).
- 검증된 평가 코드를 프로젝트 간 이식 (PESQ `pesq_batch` wb n_processor=20 두 repo 동일).

## 2. Ablation 설계 (3/3)

- **한 표 = 한 설계 축**, one-factor-at-a-time (누적 아님). component swap/remove: `w/o X` / `w/ X` / `X instead of Y`.
- **size-matched control 강박** (시그니처): capacity 보상 변형(`w/ MHCA(small)`, R=5/6)으로 "성능 향상이 **파라미터 수가 아닌 구조** 때문"임을 confound 통제.
- 표마다 **Param.(M)·MAC(G/s) 비용 열 항상 병기** → trade-off 를 표 안에서 가시화.
- 곱집합 multi-condition grid 전수 sweep (SNR × overlap × rate-gap × clean/noisy).
- **다른 backbone 에 이식**해 일반성 검증. 표당 결론 1문장.

## 3. 데이터셋·split (3/3)

- task별 de-facto 표준 고정: separation = WSJ0-2mix/WHAM!/WHAMR!/Libri2Mix, CSS = LibriCSS, restoration = VCTK/URGENT/UNIVERSE, denoising = VoiceBank+DEMAND/DNS, dereverb = REVERB.
- 시뮬 절차(RIR/SNR/overlap) 명시, gpuRIR. noisy split 이 anechoic split 수 그대로 유지(WHAMR!=WSJ-2mix partition 정렬).
- **OOD transfer evidence**: VCTK 만 학습 → URGENT/DNS/REVERB **no re-training** 평가를 별도 라벨로 분리해 일반화 주장.

## 4. Baseline 비교 (3/3)

- **family별 grouping** + 수평선 분리 (time-domain / TF-domain / diffusion / vocoder).
- **공정성 각주**: `†`(dedicated/공식코드 재현) / `‡`(원논문 보고치). universal 모델도 dedicated 변형 동반 제공.
- **Input / Ground Truth anchor 행** 상단. Param/MACs/RTF 연산자원 항상 병기. DM augmentation 효과는 별도 표 격리.

## 5. 통계·검증 (3/3)

- PIT best-permutation, 화자수 추정 정확도 병기, speaker-count prior 유무 비교.
- multi-condition grid cross (SNR/overlap/rate-gap/clean·noisy).
- heteroscedasticity scatter plot 으로 loss 설계 정당화 (2026_ICML Fig.4: raw vs normalized error, CV 수치).

## 6. 결과 해석 서술 (3/3)

- **trade-off 명명 + _균형_ 을 핵심 주장**으로. 수치 verbatim 보다 경향 서술.
- dedicated 미달은 **정직히 인정** → generalization 프레임으로 전환.
- ablation 각 행을 **메커니즘에 인과 연결**. OOD 를 "transfer evidence"로 주장 강도 self-calibrate.
- 한계(subjective listening test 부재 등) 명시.

## 7. Loss 설계 방법론 (2/3)

- multi-term composite + 가중치 명시 (예 2026_ICML §4.1 α_m=0.6/α_r=0.2/α_i=0.2), multi-scale STFT, stage-specific early supervision.
- SI-SNR loss 는 `clamp(min=-30)` 로 안정화 (loss.py — eval metric 아닌 loss 단).
- 신규 loss 의 **3-속성 공리적 정당화** (paper 표기 "scaled log-spectral loss"; 내부 약칭 s-log1p).

## Open Questions

- separation engine metric 누적 코드 일부는 paper 본문으로 보강 (해당 source 파일 일부 미확인).

## 사용자 수동 메모

(없음 — `/notes --scope user analysis` 로 추가)
