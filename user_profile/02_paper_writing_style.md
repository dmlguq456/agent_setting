# Paper 작성 톤 (Ui-Hyeop Shin)

> paper 본문 작성 시 사용자의 톤·argumentation·인용 패턴. 연구팀 / 편집팀 / autopilot-draft paper 모드에서 default 로 참조.

## Argumentation 패턴

- _수치 verbatim 회피_ — 본문에 raw 수치 그대로 박지 않음. 비교 (`A is X% higher than B`) 또는 추세 (`shows monotonic improvement`) 로 서술.
- _Figure cascade_ — Figure 1 (overall) → Figure 2 (unit module) → ablation figure / table 순. 본문이 figure 흐름을 자연스럽게 안내.
- _opening 통합 다듬기_ — paragraph block 분리 안 함. opening + 본론 한 호흡으로.

## Section 구성

- Method 본문 — _design criteria → 구현 form → 직관 설명_ 3-step (예 ICML TF-Restormer s-log 절).
- Experiment 본문 — setup (dataset / metric / baseline 묶음) → main results → ablation 순.
- Conclusion — xSFI / 도메인 framing 명시 + future work 한두 줄 + closing 한 문장.

## Citation 관례

- 도메인 영어 약자 (xSFI / SFI-STFT / s-log1p 등) main body 첫 등장 자리에서 한 번 풀이 → 이후 약어만.
- abstract 와 main body 약자 도입은 _별개_ (abstract 에서 풀이 → main body 첫 등장 자리에서도 다시 풀이).

## Camera-ready / rebuttal 자리에서의 어조

- rebuttal 자료를 본문에 그대로 옮기지 않음 — 자연스럽게 문장으로 녹임 (paragraph block 회피).
- 표 형태 비교 자료는 별도 paragraph INSERT 회피 — 기존 paragraph 흐름 안 inline rewrite.

## TODO (analyze-user 로 보강 예정)

- 자주 쓰는 영어 표현·전이어
- introduction hook 패턴
- related work 톤
- discussion / future work 어조
