# 도메인 배경·용어 선호 (Ui-Hyeop Shin)

> 사용자의 도메인 expertise 와 용어 선호. 연구팀 / 분석팀 / 편집팀이 paper·발표·코드 자료 다룰 때 default 참조.

## 주력 도메인

- **Time-frequency dual-path DNN** — speech separation / SE / dereverberation / restoration. 본인 시그니처.
- **Sampling-frequency-independent (SFI) 처리** — STFT 기반 임의 sample rate 모델링. xSFI (extended SFI) 가 본인 framework.
- **Multi-channel + monaural** — 둘 다 다룸.
- **Correlation-based learning** — CorrNet 패밀리 (TF-CorrNet / IF-CorrNet / SR-CorrNet).
- **Asymmetric encoder-decoder** — 반복 패턴 (SepReformer / TF-Restormer / SR-CorrNet).

## 보조 도메인

- **Classical 신호처리** — IVA / ICA-based beamforming / spatial constraint. 깊은 background.
- **Speaker verification** — NeXt-TDNN (1 편).

## 용어 선호

- `xSFI` — 본인이 도입한 약자. extended sampling-frequency-independent. main body 첫 등장 자리에서 풀이.
- `s-log1p` — proposed scaled log-spectral loss 의 본인 약자.
- `descending` — robust loss family 분류 용어. (`redescending` 안 씀 — 사용자 명시 결정.)
- `signal fidelity / perceptual quality` — 두 metric 그룹 분리 표현 시그니처.

## TODO (analyze-user 로 보강 예정)

- 자주 인용하는 paper / 저자 리스트
- 본인이 _intuitive_ 라 부르는 design choice 패턴
- 거부하는 도메인 표현 (예 _instantiation_ 같은 LLM-flavor)
