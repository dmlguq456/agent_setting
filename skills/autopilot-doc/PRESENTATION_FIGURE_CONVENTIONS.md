# Presentation Figure & Tone Conventions

> autopilot-doc presentation mode (특히 "cheatsheet variant" — 기존 PPT 본문 일부 보강) 에서 figure 생성 / draft 작성 시 강제 적용. SKILL.md의 presentation mode 섹션이 이 파일을 link.
>
> 본 conventions 는 2026-05-20 DSC 중간보고 cheatsheet 세션에서 사용자 명시적 지적·교정을 통해 확립된 룰. 발표 자료 품질에 직결되는 핵심 원칙이므로 우회 금지.

---

## 1. Figure 안 텍스트 최소화 (강제)

**원칙**: figure 는 "한 호흡에 패턴 파악" 이 목표. 텍스트로 설명할 사항은 draft 본문 bullet/표에 분리.

### 1.1 제거 / 금지

| 항목 | 금지 이유 |
|---|---|
| 긴 한국어 `suptitle` | figure caption (draft 본문) 으로 이전 — figure 안에 동일 정보 중복 X |
| 긴 한국어 subplot title (`전동시트 단독 신호 (target, clean)` 같은) | 짧은 영문 라벨로 대체 |
| `figure 내 수치 분석 box` (`out/target=1.02×, 파형 일치도=0.921` 등) | draft 본문 표로 분리 — figure 는 패턴 보이고, 수치는 본문에서 정량 비교 |
| informal/conversational 단어 (`촘촘`, `잘 보임`, `대박` 등) | administrative neutral 톤 위반 |

### 1.2 사용 (권장)

- **짧은 panel 라벨 박스** — subplot 좌상단에 `target` / `mix` / `output` / `4 ch` / `array1` / `#1` 같은 1-2 token 라벨을 `bbox=round` 박스로 배치. 색 패턴: spectrogram 패널은 흰 글씨 + 검정 배경 alpha 0.5 / RMS 패널은 검정 글씨 + 흰 배경 + gray edge
- **axis label 만 유지** — `freq [kHz]`, `time [s]`, `RMS`, `dB` 같은 단위 명시
- **colorbar label** — `dB` 만 (긴 설명 X)
- **legend** — 1-2 token (`target`, `mix`, `output`)

### 1.3 Caption 룰

draft markdown 안 figure caption 은 **1 줄** — figure 가 무엇을 보여주는지만. 수치 / 해석 / 결론은 본문 bullet 또는 표.

```markdown
![Figure C-1](path)

**Figure C-1**: array1, SNR −5 dB — target / mix / output spectrogram + 50 ms RMS
```

위 예시: 어떤 케이스 + 무엇 비교 명시. "출력이 정답을 잘 따라감" 같은 평가 / 수치는 본문에.

---

## 2. Spectrogram scale (강제)

### 2.1 Per-signal peak 정규화 + 공통 `−60 ~ 0 dB`

비교 대상 신호의 진폭이 크게 다를 때 (target 0.007 vs mix 0.014 vs noise 0.05 등) absolute dB scale 은 약한 신호가 색으로 안 보임.

```python
def spec_db_norm(s, nperseg=2048, noverlap=1024):
    f, t, Z = stft(s, fs=SR, nperseg=nperseg, noverlap=noverlap)
    mag = np.abs(Z)
    peak = mag.max() + 1e-9
    return f, t, 20*np.log10(mag/peak + 1e-9)

VMIN, VMAX = -60, 0  # 공통 scale (모든 panel)
```

→ 각 신호의 spectrum pattern 이 self-relative scale 로 보이고, panel 간 진폭 차이는 RMS overlay 에서 별도 확인.

### 2.2 colormap

- 기본: **`magma`** (dynamic range 좋음, 어두운 영역 가독성 ↑)
- 대안: `viridis` (밝은 영역 강조)
- 금지: `jet`, `hot` (perceptually non-uniform)

---

## 3. RMS profile (강제)

### 3.1 Window / hop

- **`50 ms window, 25 ms hop`** (75% overlap) — trajectory 가 매끄럽고 spike 위치도 잘 보임
- `1 s window` 는 trajectory 가 거침 (몇 분짜리 녹음 overview 에만 사용)
- `25 ms window` 는 너무 spiky — 패턴 산만

### 3.2 Plot 색상 / lw 컨벤션

| signal | color | lw | alpha | 의미 |
|---|---|---|---|---|
| mix (입력) | `gray` | 0.6 | 0.85 | 배경, 약화 |
| target (정답) | `tab:green` | 1.0 | 1.0 | reference |
| output (모델 출력) | `tab:red` | 0.9 | 1.0 | 검증 대상 |

→ target 이 가장 두꺼움 (reference 강조), output 은 그 위에 빨강 오버레이.

---

## 4. 청중 친화적 단위 변환 (강제)

**raw audio engineering 단위는 청중에게 안 와닿음**. 비전공자 의사결정자 포함 PPT 라면:

| Raw (지양) | 변환 (권장) |
|---|---|
| `RMS 260` (int16 raw) | `−42 dBFS` 또는 `전체 동적범위의 0.8%` |
| `RMS 150 ~ 240` | `−47 ~ −43 dBFS` 또는 `0.5 ~ 0.7%` |
| target vs noise RMS 비율 | `약 22 dB 차이 (≈ 12배)` |
| `0.0046` linear | `−47 dBFS` 또는 `약 0.5%` |

draft 본문에 raw 값 보존이 필요하면 괄호 안에 보조 표기:

```
모터 구간: 평균 RMS 약 −45 dBFS (전체 동적범위의 약 0.5%)
```

---

## 5. 기존 발표자료 (deck) 톤 분석 (강제)

**cheatsheet variant — 기존 PPT 본문 일부 보강** 시 pre-flight 단계에서 기존 deck 텍스트 추출 + 톤 파악.

### 5.1 PPT 텍스트 추출 (python-pptx)

```python
from pptx import Presentation
prs = Presentation(pptx_path)
for i, slide in enumerate(prs.slides, 1):
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                txt = ''.join(run.text for run in para.runs).strip()
                if txt: print(txt)
```

### 5.2 파악할 톤 요소

- **슬라이드 헤더 형식** (예: `진행 사항 – [세부 주제]`)
- **bullet 구조** (큰 주제 / `→` 결과 / 다음 단계)
- **결론 슬라이드 형식** (예: `진행 사항 요약` + `예정 사항` + `요청 사항`)
- **그림 종류** (spectrogram 비교, 시계열 overlay, 측정 setup 사진 등)
- **톤** (administrative neutral / pitch / 학술 reporting)

### 5.3 새 슬라이드는 기존 deck 마지막 슬라이드의 직접 후속

기존 deck Slide N 의 placeholder ("AI 기반 잡음제거 출력신호" 같은 미완성 항목) 가 본 cheatsheet 의 출발점. 새 슬라이드 첫 페이지 헤더는 그 placeholder 의 자연스러운 연결.

---

## 6. Asset 활용 (게으른 자료 금지)

**원칙**: 사용자가 준비한 모든 자료 (motor_sample / simul_sample / lab_sample / preprocessing viz·spec / manifest 등) 를 게으르게 한두 그림으로 끝내지 말고 풍부한 multipanel + 다양한 케이스로 다 활용.

### 6.1 권장 그림 수

- presentation cheatsheet 4 ~ 5 페이지 분량 → **그림 7 ~ 10 장** (페이지당 1 ~ 2 장)
- 각 페이지: 데이터 / 도식 / 결과 plot 분리

### 6.2 시뮬레이션 set 활용

- target / mix / output 3 신호 spectrogram + RMS overlay (multipanel)
- SNR sweep (3 ~ 5 점) 한 plot
- 모델 variant 비교 (4 ch vs 1 ch 같은) worst case plot
- 어레이 / 거리 / 측정 위치 variation 별도 plot

---

## 7. Path 컨벤션 (강제)

### 7.1 Markdown image embed 는 상대 경로

draft 위치 기준 상대 경로 — markdown viewer 가 일관 렌더링.

```markdown
draft 위치: .claude_reports/documents/{name}/draft/draft_ko.md
asset 위치: .claude_reports/assets/foo.png
embed:      ../../../assets/foo.png   (3단계 위)

data 위치: data/labels_v3/{date}/{base}.viz.png
embed:     ../../../../data/labels_v3/{date}/{base}.viz.png   (4단계 위)
```

### 7.2 Absolute path 금지

`/home/nas/...` 같은 absolute path 는 viewer / 환경에 따라 안 보임. markdown viewer 가 일관 인식하도록 상대 경로 강제.

---

## 8. 한국어 폰트 (matplotlib)

```python
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams['font.family'] = 'Noto Sans CJK JP'   # Pan-CJK 패밀리, 한글 글리프 포함
plt.rcParams['axes.unicode_minus'] = False
```

`Noto Sans CJK KR` 로 직접 호출 시 matplotlib 가 family 못 찾는 케이스 있음 — `JP` 가 등록명이지만 동일 ttc 안에 한글 글리프 있음.

---

## 9. Draft 작성 후 사용자 검토 거치기

1. plot 생성 → `SendUserFile` 로 즉시 전달
2. 사용자 검토 (모바일 앱에서 inline, 터미널에서는 파일 링크)
3. 수정 요청 받고 plot 재생성
4. 그 후 draft 본문 작성

→ draft 본문에 잘못된 그림 임베드되면 본문 수치 / 해석도 함께 재작성 비용 발생. plot 먼저 검토.

---

## 10. 본 conventions 의 적용 범위

- **autopilot-doc presentation mode** (모든 변형 — full deck / cheatsheet variant)
- **refine-doc** 으로 presentation artifact 수정 시 본 룰 검사 (figure 안 텍스트 / scale / 단위 변환 / 톤)
- **audit** 으로 presentation artifact 점검 시 본 룰 위반 식별
