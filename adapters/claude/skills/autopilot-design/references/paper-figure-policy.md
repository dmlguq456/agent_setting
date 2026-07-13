# Paper architecture figure 는 _layout 가이드_ 까지만 (2026-05-28 정책)

논문용 architecture diagram (사용자 deck 양식의 그림) 은 **LLM 시각 craft 의 한계 영역** — 디자인팀은 본 그림을 생성하지 않는다. 다음 자리에서만 개입:
- **composition/layout 가이드 산출** — 블록 list(라벨·역할색·위치) · 흐름 · 위계 · 강조 자리. markdown sketch 또는 wireframe-grade SVG.
- **참조 자료 안내** — `<agent-home>/user_profile/assets/figure/svg/`(pptx 추출 개체) · `figure_ppt/*.pptx`(편집 가능 원본) · `mem profile 01_paper_figure_style` Part B 거시 감각.
- **사용자가 pptx 에서 직접 완성** — 슬라이드 도형 복제 후 라벨·색 교체.

본 정책은 **paper architecture figure 한정**. 다른 scope (ui · webapp · slide HTML · icon · mermaid/excalidraw diagram) 는 LLM 손그림으로 충분 → 시각 검증 루프로 완결.
