---
aspect: figure
owner: 사용자
mode: init
updated: 2026-05-26
source: paper PDF 8 / figure_ppt 5 (PNG 54) / code architecture.png 2
consensus: 3-instance (run A/B/C)
---

# 01. Paper / Figure 제작 스타일

> Speech separation·enhancement·restoration 연구자의 figure/diagram 양식. architecture diagram + booktabs 표가 중심이고 line plot·scatter 는 절제적. agent 가 figure/표/슬라이드 비주얼 만들 때 본 파일을 1순위 참조.

## 1. Architecture diagram (가장 강한 시그니처, 3/3)

- block: **rounded rectangle**, 흰 fill + **굵은 colored outline** (fill 아닌 stroke 가 semantic carrier). 상위 컨테이너는 모서리 radius 큼. subtle drop shadow.
- **역할 색 규약** (NeurIPS SepRe → SPL TF-CorrNet → ICML TF-Restormer → 발표 deck 전부 일치):
  - 초록 = encoder / separation / analysis 경로 ("Time/Freq. self module")
  - 주황 = decoder / reconstruction / synthesis 경로 ("Freq. cross-self module")
  - 회색 = I/O·보조 연산 (STFT/iSTFT, Conv2D, Projection, Split, Filter, LN) — 회색 outline + drop shadow
  - 빨강 = novelty 강조 (빨강 점선 outline 또는 빨강 텍스트)
  - 노랑/금색 = zoom-in 한 신규 sub-block (Q/K/V Linear, Freq. projection)
- 반복 stack: 경로색 **연한 tint 배경 + 회색 점선 컨테이너 + `×B_E`/`×B_D`/`×R` 첨자** (TF_Restormer_ICML_slide-3, TF-CorrNet-v2_slide-08).
- arrow: 가는 검정 직선 + 작은 채운 화살촉, **직각(orthogonal) 라우팅**. 점선 = 보조/조건 입력 ("Extension query", "key/value", "padding").
- 연산자 = 원 기호: `⊕` 잔차합, `⊗` masking/gating(옆에 "Swish" 라벨), `~⊕` positional embedding 합성.
- **cross-attention 은 "key/value" 라벨 화살표**로 encoder→decoder 명시 — trademark (2026_ICML Fig.2, architecture.png).
- zoom-in: 상위 block 을 **회색 점선 rounded rect** 로 감싸고 점선 leader 로 내부 분해. 확대 안에서도 색 규약 유지 (신규 연산만 색 outline) (2026_ICML Fig.3c, slide-5/6).
- subfigure: `(a)(b)(c)` 이탤릭 라벨 하단 중앙 + caption 재진술.

### 텐서 shape glyph (시그니처, 3/3)
- block 입출력에 **`ℝ^{F×T×C}` 수식 + bold 변수(X, Z, Y, D_{k,tf})** 항상 annotate. 도식 표기 = 본문 수식 표기 완전 일치.
- **작은 3D cuboid/slab 다발 pictogram**: 축 라벨 f(주파수)/t(시간)/k(화자) + **빨강 양방향 화살표(↕/↔)로 처리 축** 표시. encoder=초록 줄무늬 / decoder=주황 줄무늬. decoder 는 화자축 k 만큼 겹친 K장 stack.
- 좌하단 **범례 박스**: "sequence axis" / "processing axis" + 좌표축 아이콘 (SR_CorrNet architecture.png, TF-CorrNet-v2_slide-08, Doc_Thesis_slide-07). slide-2 는 색 점선 화살표 범례로 확장(노랑=self-attn query / 주황=cross-attn query / 노랑점선=mamba input streaming).
- 의도: dual-path(time vs freq) 모델에서 "어느 축이 sequence·어느 축이 처리 대상"인지 못박기.

## 2. Booktabs 표 (정량 비교의 기본, 3/3)

- **세로 칸선 없음**, 가로줄만 (`\toprule`/`\midrule`/`cmidrule`/`\bottomrule`).
- **의미 그룹 다단 헤더**: "Signal fidelity"(PESQ/SDR/LSD/MCD/sBERT) vs "Perceptual quality"(UTMOS/DNSMOS) 식. 단순 나열 회피 (2026_ICML Table 1·2).
- 열 순서: Method → 비용열(`Param.(M)`/`Size(M)`/`MACs(G/s)`/`MAC(G)`/RTF) → metric 열. 비용열을 성능과 **항상 같은 표에 동반**해 trade-off 논증.
- **metric 헤더에 ↑/↓ 방향 화살표** 거의 항상 (PESQ↑, LSD↓, EER(%)↓).
- **Input / Ground Truth 기준 행을 최상단 별도 그룹** (GT 의 SDR 은 `∞`).
- **dagger `†`/`‡` 각주**로 조건/출처 표기 (`†pretrained code`, `‡원논문 보고치`, dedicated vs universal).
- 행 그룹 좌측 **세로 회전 라벨** ("mobile"/"base") (NeXt-TDNN Table 2).
- ablation: 첫 열에 자연어 case 명 ("encoder-only", "w/o MHCA", "w/ MHCA(small)"), **체크마크 √ 열**로 on/off 토글.

### ours 강조 (3/3)
- **best 수치 = 열별 bold**. 제안 variant 는 **표 하단 그룹**으로 모으고 같은 prefix 묶음 (`TF-Restormer(off)/(off)†/(on)`).
- **채택 config 행 / 제안 모델 행 = 회색 row shading** (2024_NeurIPS SeparateReconstruct Table 4/5; TF-CorrNet/NeXt-TDNN 계열은 bold-only 로 음영 없이 — _(consensus: 음영은 NeurIPS 계열, bold+위치는 전반)_).
- 표 안 색 음영·화살표는 절제 — bold+위치 강조 1순위. (메모리의 "rebuttal 표 drop"·"수치 verbatim 제거"와 정합 — [[feedback-paper-body-rewrite-pattern]])

## 3. Curve plot (절제적, _consensus 2/3_ — run B·C 관찰, A 미발견)

- 등장 위치: **분석용 figure·thesis·슬라이드** (paper 본문은 표 위주). loss curve 류는 미관찰.
- 양식: **마커 달린 실선**(filled circle marker), 2×2 패널, 패널 간 축/스케일 정렬. x="Stage index (b/r)" 또는 "Time frame index", y="PESQ-WB"/"SI-SDR"/"Cosine Similarity".
- **회색 점선 수평 기준선 + 라벨** ("Noisy" baseline). 범례는 패널 좌상단 박스.
- 색 4팔레트(주황/노랑/파랑/초록)로 ablation 변형 구분 (TF_Block_Reuse_slide-6: B16R1/B1R16/B8R1/B1R8).
- spectrogram + curve 를 **같은 x축으로 수직 정렬** (SepReformer_slide-11: Spk1/Spk2 spectrogram 위 + cosine similarity Z1~Z4 4색 곡선 아래).

## 4. Scatter (희소, _consensus 2/3_ — run B·C 관찰)

- 2-패널 나란히, 밀도 산점도(점 수만 개), log-log, 단색 그라데이션(파랑=raw/문제 vs 빨강=normalized/개선) (2026_ICML Fig.4).
- **회색 대각 transition line + 텍스트 주석**, 패널 inset 박스에 핵심 수치("CV = 2.65" / "CV = 0.28").

## 5. Spectrogram 관례

- 용도 (3/3): architecture **입출력 anchor**(before/after) — 파이프라인 양끝 (입력 band-limited → 출력 전대역, super-resolution 시각화). SFI-STFT / SFI-iSTFT 라벨 동반.
- colormap **2종 분업** (_consensus 2/3_ — run B·C 관찰, run A 는 썸네일 colormap 미확정):
  - architecture anchor = **magma/viridis 계열**(보라→주황→노랑) (slide-2, TF_Block_Reuse_slide-3)
  - 정량 분석 figure = run 관찰상 **jet 계열**(파랑-초록-노랑-빨강) + dB 컬러바(−60~−120) (Doc_Thesis_slide-04). _descriptive — 새 figure 제작 시엔 perceptually-uniform(viridis/magma) 권장, jet 는 사용자 기존 자료 매칭이 필요할 때만._
- 축: y="Freq. (kHz)"(0/2/4/6/8), x="Time (s)" 또는 "Time frame index". anchor 썸네일은 축 생략, `T`/`F` 모서리 표기만.
- 비교 패널 가로 나열 (degraded / mask grayscale 0~1 / restored 3단), b×r spectrogram 격자(stack/repeat 효과).
- "Real/Imag." vs "Mag./Phase" 두 표현 구분 (위상은 noise 무늬).

## 6. 폰트

- block 라벨·표 본문: **sans-serif**(PPT diagram). 수식·변수(`X`, `ℝ^{F×T×C}`, `×B_E`): **LaTeX serif math (Computer Modern)** — bold 변수 + blackboard `ℝ` + 첨자 다용. 표 캡션 "Table N." 이탤릭.
- paper figure 와 slide figure 가 같은 폰트 룩 (CM serif 통일).

## 7. 색 hex (PNG 시각 추정 — vector source 미확보, "≈" 유지)

| 역할 | 추정 hex | 비고 |
|---|---|---|
| encoder green outline | ≈ `#4E7A3A`~`#5B8C3E` | tint 배경 ≈ `#E8F0DD` |
| decoder orange outline | ≈ `#D2691E`~`#E0701F` | tint 배경 ≈ `#FBE7DA` |
| 보조 gray outline | ≈ `#6E6E6E` | 채움 흰색/`#F2F2F2` |
| novelty red | ≈ `#C0392B`/`#E03030` | 점선·텍스트·처리축 화살표 |
| accent gold/yellow | ≈ `#D4A017`/`#E0A93B` | zoom sub-block |
| 화자 4색 팔레트 | 주황 `#C0581E` / 노랑 `#F2C14E` / 초록 `#3E7D44` / 파랑 `#2BA7DF` | TF-CorrNet-v2_slide-01 |

> **재현 원칙**: hex 추정에 의존 말고 ① 역할→색군 매핑 ② bold-only 표 강조 ③ red-dashed/red-text 신규 모듈 — 이 3규칙 우선. 정확 hex 는 원본 pptx eyedropper.

## 재현 체크리스트

1. rounded rect + drop shadow + 위/좌→우 직각 화살표.
2. encoder 초록 / decoder 주황 / 보조 회색 / 신규 빨강(점선·텍스트)·노랑(zoom).
3. 반복 stack = 점선 박스 + `×B_*` + 경로색 tint.
4. cross-attention = "key/value" 라벨 화살표.
5. block 마다 `ℝ^{...}` 첨자 + 본문 동일 bold 변수.
6. dual-path = sequence/processing axis 범례 + 3D slab pictogram + 빨강 처리축 화살표.
7. spectrogram anchor magma / 분석 figure jet+dB, 축 Freq.(kHz)/Time(s).
8. 표 = booktabs(세로선 X), metric ↑/↓, 의미그룹 다단 헤더, 비용열 동반, Input/GT 상단, proposed 행·best bold, dagger 각주.

## Open Questions

- 표 row 음영: NeurIPS 계열은 회색 음영 사용, TF-CorrNet/NeXt-TDNN 계열은 bold-only — 매체/연도 차이인지 확정 못 함.
- 모든 hex 는 PNG 육안 추정. source 에 명시 hex 없음.

## 사용자 수동 메모

(없음 — `/notes --scope user figure` 로 추가)
