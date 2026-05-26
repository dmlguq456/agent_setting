---
aspect: presentation
owner: 사용자
mode: init
updated: 2026-05-26
source: pptx 8 deck → PNG 301 slides (대표 슬라이드 샘플)
consensus: 3-instance (run A/B/C, 강한 일치)
note: Seed_FastTrack deck 은 PI 컨소시엄 양식 — 사용자 개인 reference 에서 분리
---

# 03. 발표 전략

> 발표 슬라이드 제작 전략·시각 디자인. 디자인팀(maker slide)·자료팀·편집팀이 슬라이드 비주얼·발표 흐름 작성 시 참조. 시각 fidelity 는 PNG 기반 추출 — deck 당 대표 슬라이드(title/목차/방법/결과/마무리) 샘플 관찰이며 전수 정독 아님.

## 1. 단일 마스터 템플릿 — Sogang IIPLab (3/3)

본인 deck 7종이 동일 골격 공유 (Seed_FastTrack 1종은 PI 컨소시엄 양식 → 제외):

- **4 슬라이드 타입**:
  - title/closing: 화면 중하단 **full-bleed 진홍(Sogang crimson) band + 흰 굵은 제목**(drop shadow). 종료는 "감사합니다".
  - content: 상단 **얇은 crimson running header**(`Dept. of Electronic Engineering, Sogang University / N` + 페이지번호) + 좌측 검정 제목.
  - section divider.
- **로고 고정 anchor**: 좌하단 IIP Lab + Sogang crest — content 슬라이드는 우하단, title 슬라이드는 우상단 배치.
- content 레이아웃: **좌 본문(bullet) / 우 절반 figure** 암묵 2-column.

## 2. 색·폰트 시스템 (3/3)

- **primary accent = Sogang 진홍(crimson, ≈ `#A6101A` 추정)** 단일. 순백 배경, gradient 없음.
- **강조 layering 일관**: bold(구조) → underline / colored underline → **빨강 텍스트**(핵심 insight 한 줄) → **노란 형광펜 band**(드묾). figure 의 역할색(encoder 초록/decoder 주황)과 underline 색 연동.
- 폰트: 영문 sans-serif / 국문 고딕 / **수식은 LaTeX Computer Modern serif math**(본문 sans 와 분리, 비중 높음).
- 블록 다이어그램은 [[01-paper-figure-style]]의 역할색 규약 재사용.

## 3. 발표 서사 — Motivation-first (3/3)

- 흐름: Title → Contents/목차(번호) → Introduction → 방법(**Motivation → Architecture** 2단) → Results → Conclusion → "감사합니다".
- **각 section 마다 motivation 먼저 깔고 architecture 제시** (motivation↔method 1:1 매핑) — why-driven.
- 긴 deck(survey성)은 분야 발전사 → 본인 work → 정리 깔때기.
- 심사용 deck 은 "Q1" **예상 질문 슬라이드** 습관.

## 4. 다이어그램 슬라이드化 (3/3)

- paper figure 통째 붙이기보다 **슬라이드 전용 재구성**. 좌 bullet / 우 diagram 2분할.
- signature figure(SepRe encoder/decoder 블록도)를 deck 간 재사용.
- backbone 진화를 **가로 나란히 비교**(제안 블록만 점선·색 강조), 단계별 reveal 빌드.
- 개념-실세계 photo 병치(과제 발표는 환경 사진).

## 5. 결과 제시 (3/3)

- **시그니처 시각화: `MACs(log) vs SI-SNRi` bubble scatter** — family 별 추세선, 본인 모델 우상단 Pareto frontier 강조.
- dense numeric 표(4분할, 제안 행 bold + 열별 best underline).
- spectrogram demo grid. (오디오 데모 슬라이드는 명확 미관찰 — 데모는 별도 mp4로 추정.)

## 6. 청중별 적응 (3/3) — 불변 vs 가변

**불변**: 마스터 템플릿 · crimson 색코딩 · 로고 · bullet 계층 · Motivation-first.
**가변**: 언어 · 길이 · 정보 밀도 · 톤.

| 청중 | 언어 | 특징 |
|---|---|---|
| 학회 (NeXt-TDNN/SepReformer) | 영어 | 압축·저밀도·1메시지·conference 로고/footnote |
| 심사 (박사학위청구) | bilingual 제목 | 최장(51장)·정식 목차·최고 밀도·Research 실적 선두·예상질문 |
| 세미나 (기업/Deep Learning) | 한영 혼용 | 교육적·survey·개념 비유·"직관" 칼럼·로드맵 |
| 과제 (기초연구/정부과제) | 한국어(전문어 영어 유지) | 고밀도·진척/데이터셋·과제 tag·환경 사진·행정 톤 |

## Open Questions

- crimson hex 는 PNG 시각 추정(`#A6101A`) — 원본 pptx eyedropper 로 확정 권장.
- 긴 제목이 crimson title band 에서 상하 잘리는 미세 결함이 여러 deck 반복(개선 여지).

## 사용자 수동 메모

(없음 — `/notes --scope user presentation` 로 추가)
