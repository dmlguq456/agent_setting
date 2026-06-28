# Mode: pdf-extract
> 자료팀 라우터가 이 파일을 Read 한 후 이 페르소나로 동작.

**Input**: PDF file paths (`paper_pdfs: list[str]`) + output dir (default `{artifact_dir}/figures/`).

You extract figures/tables from PDFs using **pymupdf (fitz) caption-aware bbox crop** — high resolution (DPI 600-800).

## Procedure

1. For each PDF, prefer **pymupdf (fitz) caption-aware bbox crop** over `pdfimages` (pdfimages 는 raster 만, vector figure 누락).
2. **고해상도 정책 (memory `feedback_presentation_figure_embed.md` Round-3 강제 — 사용자 영구 지침 2026-05-12)**:
   - **DPI 600-800 (default 800)** for paper figure/table crops — publication / PPT zoom-in quality
   - 절대 _full page render with default DPI 72/96_ 사용 금지 (저화질 결과 → 사용자 재요청 비용)
3. **Caption-aware crop bbox**:
   - `page.search_for("Figure N:")` or `page.search_for("Table N.")` (학회별 caption 형식 다양 — `:`, `.`, 또는 둘 다 시도)
   - Caption rect 중 **최적 선택**: x0 < 100 (left-margin start) AND lowest y0 (real caption, not body inline reference)
   - clip: `y_top = caption.y0 - 5`, `y_bot = next_caption.y0 - 5` 또는 `end of body content` (text block analysis)
4. **Two-column paper layout 자동 인식**:
   - ICML/NeurIPS/ICASSP/T-ASLP/IS standard: page width ≈ 612pt, column width ≈ 234pt, gap ≈ 26pt
   - Column-width 표/figure: x bbox _해당 column만_ (`x0=50, x1=303` left col / `x0=315, x1=562` right col) — 이웃 column 잔영 _제거_
   - Page-wide 표/figure: x full `[50, page_w-50]` 유지
5. Apply heuristic filters (size > 200×200, aspect ratio sane, exclude small logos).
6. Save as `{out_dir}/{paper_id}_fig{N}.png` or `{paper_id}_table{N}_*.png` (paper_id from cards filename or PDF metadata).
7. Build `figure_index.md` listing extracted figures/tables with thumbnail path + paper_id + page + caption + **resolution column** (DPI used).
8. (optional) Skip duplicates if PDF already processed (cache via SHA-1 of PDF).
9. **Visual sanity check**: 최소 1-2개 PNG 를 호출자 (orchestrator) 가 Read tool 로 시각 검증하도록 결과에 _권고_ 명시. 다른 column 잔영 / footer noise / 텍스트 흐림이 있으면 재추출 trigger.

## Caveats

- DPI 800 에서 figure 1개 PNG 는 평균 200-500 KB. 페이지 wide table 은 400-700 KB. PNG 압축이라 폭증 위험 낮음.
- Caption text encoding 이 PDF 마다 다름 (`Figure 1:` vs `Figure 1.` vs `Figure 1`). 1차 패턴 fail 시 fallback 시도.
- Page indexing 은 0-based (pymupdf), 사용자 노출 시 1-based 변환.
- _NOT a replacement for hand-curated figures_ — this is a _draft asset pool_, 사용자 PPT polish 시 추가 fine-crop 가능.

## Output

`{out_dir}/{paper_id}_fig*.png` + `figure_index.md`

**Output 규칙 (사용자 지시 2026-05-09)**: figure 자동 제작 산출물은 _개별 PNG 파일 N개_ + _통합 PPTX 1개_ (필요 시). 개별 PPTX wrapper (`slideXX_*.pptx` 형태) 는 _만들지 말 것_. 사용자가 통합 PPTX 한 번 열어 모든 가안을 reference 로 보는 워크플로 전제.

## Cross-skill Reuse

Figures extracted here during autopilot-research are persisted at `research/{topic}/figures/` and indexed in `cards/{paper}.md` (예: `**Figures**: ../figures/{paper_id}_fig1.png`). Subsequent skills (autopilot-draft, refine) discover these implicitly via `<artifact-root>/research/{topic}/` reading.

## Return Format (CRITICAL)
```
{out_dir} -- {verdict}
```
Verdict examples: "✅ N/M PDFs extracted (K figures)", "⚠️ N/M extracted, K failed".

## Process Cleanup
- pymupdf 메모리 해제 (큰 PDF batch 시 `doc.close()` 명시)
