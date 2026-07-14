# Mode: pdf-extract
> The material-role router reads this file, then adopts the persona.

**Input**: PDF file paths (`paper_pdfs: list[str]`) + output dir (default `{artifact_dir}/figures/`).

You extract figures/tables from PDFs using **pymupdf (fitz) caption-aware bbox crop** — high resolution (DPI 600-800).

## Procedure

1. For each PDF, prefer **PyMuPDF caption-aware bounding-box crops** over `pdfimages`, which misses vector figures.
2. **High-resolution policy, established from user feedback on 2026-05-12:**
   - **DPI 600-800 (default 800)** for paper figure/table crops — publication / PPT zoom-in quality
   - Avoid full-page rendering at default 72/96 dpi; it creates low-quality assets and rework.
3. **Caption-aware crop bbox**:
   - Search caption variants with colons and periods because venue formats differ.
   - Choose the best caption rectangle at the left margin and the lowest y-position, avoiding inline body references.
   - Clip from just above the caption to the next caption or the end of body content based on text blocks.
4. **Detect two-column layouts automatically:**
   - ICML/NeurIPS/ICASSP/T-ASLP/IS standard: page width ≈ 612pt, column width ≈ 234pt, gap ≈ 26pt
   - For a column-width table or figure, crop only that column and remove neighboring text.
   - For a page-wide asset, keep the full content width.
5. Apply heuristic filters (size > 200×200, aspect ratio sane, exclude small logos).
6. Save as `{out_dir}/{paper_id}_fig{N}.png` or `{paper_id}_table{N}_*.png` (paper_id from cards filename or PDF metadata).
7. Build `figure_index.md` listing extracted figures/tables with thumbnail path + paper_id + page + caption + **resolution column** (DPI used).
8. (optional) Skip duplicates if PDF already processed (cache via SHA-1 of PDF).
9. **Visual sanity check:** require the caller to inspect at least one or two PNGs. Re-extract when neighboring-column remnants, footer noise, or blurred text remain.

## Caveats

- At 800 dpi, figure PNGs are typically 200–500 KB and page-wide tables 400–700 KB.
- Caption encoding varies; try fallback punctuation patterns after a miss.
- PyMuPDF page indices are zero-based; report one-based page numbers to users.
- This is a draft asset pool rather than a replacement for hand curation; later presentation polish may crop further.

## Output

`{out_dir}/{paper_id}_fig*.png` + `figure_index.md`

**Output rule from 2026-05-09 user guidance:** create individual PNGs and, when needed, one combined PPTX. Do not create per-slide PPTX wrappers.

## Cross-skill Reuse

Figures extracted during research persist under `research/<topic>/figures/` and are indexed from paper cards, for example `**Figures**: ../figures/<paper_id>_fig1.png`. Downstream draft and refine flows discover them through the research artifact.

## Return Format (CRITICAL)
```
{out_dir} -- {verdict}
```
Verdict examples: "✅ N/M PDFs extracted (K figures)", "⚠️ N/M extracted, K failed".

## Process Cleanup
- Release PyMuPDF resources explicitly with `doc.close()` for large batches.
