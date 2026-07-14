"""
Web-based figure extraction utility for autopilot-research Step 3.5 or direct callers.

Tier 1: ar5iv (https://ar5iv.labs.arxiv.org/html/{arxiv_id}), including vector-to-raster
Tier 2: arxiv-vanity fallback
Tier 3: arXiv PDF plus pdfimages fallback
All fail → record paper as "0 extracted" in figure_index.md

Usage:
  python3 extract_web_figures.py <cards_dir> <out_figures_dir> [--limit N] [--no-pdf]

Args:
  cards_dir: e.g., research/speech-enhancement-trends/cards
  out_figures_dir: e.g., research/speech-enhancement-trends/figures
  --limit N: process only first N papers (sample mode)
  --no-pdf: skip Tier 3 PDF fallback (web-only)
"""
from __future__ import annotations
import os
import re
import sys
import time
import json
import urllib.parse
from pathlib import Path
import requests
from bs4 import BeautifulSoup

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
HEADERS = {"User-Agent": UA}
TIMEOUT = 12  # seconds per fetch
RATE_LIMIT_S = 1.5  # between fetches
MIN_DIM = 200  # filter small icons
MIN_BYTES = 5_000  # filter tiny placeholders


def find_arxiv_id(card_text: str) -> str | None:
    """Extract an arXiv ID from a card body across supported link patterns."""
    patterns = [
        r"\*\*arXiv\*\*:\s*([0-9]{4}\.[0-9]{4,5})",
        r"\*\*arXiv ID\*\*:\s*([0-9]{4}\.[0-9]{4,5})",
        r"arXiv:\s*([0-9]{4}\.[0-9]{4,5})",
        r"arxiv\.org/abs/([0-9]{4}\.[0-9]{4,5})",
    ]
    for pat in patterns:
        m = re.search(pat, card_text)
        if m:
            return m.group(1)
    return None


def parse_cards(cards_dir: Path) -> list[dict]:
    """Parse cards/*.md into (paper_id, arxiv_id, title) records."""
    papers = []
    for f in sorted(cards_dir.glob("*.md")):
        if f.name.startswith("_"):
            continue
        text = f.read_text(encoding="utf-8")
        arxiv_id = find_arxiv_id(text)
        # Use the first H1 as the title.
        title_match = re.search(r"^# (.+)$", text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else f.stem
        papers.append({
            "paper_id": f.stem,
            "arxiv_id": arxiv_id,
            "title": title,
            "card_path": str(f),
        })
    return papers


def fetch_ar5iv(arxiv_id: str) -> str | None:
    """ar5iv HTML fetch."""
    url = f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code == 200 and "<figure" in r.text or "<img" in r.text:
            return r.text
    except Exception:
        pass
    return None


def parse_figures(html: str, base_url: str) -> list[str]:
    """Extract absolute figure image URLs from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    seen = set()

    # Strategy 1: <figure><img>
    for fig in soup.find_all("figure"):
        for img in fig.find_all("img"):
            src = img.get("src")
            if src and src not in seen:
                seen.add(src)
                urls.append(urllib.parse.urljoin(base_url, src))

    # Strategy 2: every remaining <img> after asset filtering.
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src or src in seen:
            continue
        # Skip common non-figure assets
        skip_patterns = ["logo", "badge", "icon", "favicon", "powered-by",
                          "math/", "/Math/", "tex_image"]
        if any(p in src.lower() for p in skip_patterns):
            continue
        seen.add(src)
        urls.append(urllib.parse.urljoin(base_url, src))

    return urls


def download_image(url: str, out_path: Path) -> tuple[bool, int]:
    """Download an image and apply the size filter. Return (success, bytes)."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True)
        if r.status_code != 200:
            return False, 0
        content = r.content
        if len(content) < MIN_BYTES:
            return False, len(content)
        out_path.write_bytes(content)
        return True, len(content)
    except Exception:
        return False, 0


def extract_pdf_fallback(arxiv_id: str, paper_id: str, out_dir: Path,
                         tmp_dir: Path) -> int:
    """Tier 3: arxiv PDF + pdfimages."""
    pdf_path = tmp_dir / f"{paper_id}.pdf"
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
    try:
        r = requests.get(pdf_url, headers=HEADERS, timeout=30)
        if r.status_code != 200:
            return 0
        pdf_path.write_bytes(r.content)
    except Exception:
        return 0

    out_prefix = out_dir / f"{paper_id}_fig"
    rc = os.system(f"pdfimages -png '{pdf_path}' '{out_prefix}' 2>/dev/null")
    pdf_path.unlink(missing_ok=True)
    if rc != 0:
        return 0

    # Filter: keep only N min-bytes, rename to {paper_id}_fig{N}.png
    extracted = sorted(out_dir.glob(f"{paper_id}_fig-*.png"))
    kept = []
    for i, src in enumerate(extracted):
        if src.stat().st_size < MIN_BYTES:
            src.unlink()
            continue
        new_name = out_dir / f"{paper_id}_fig{len(kept)+1}.png"
        src.rename(new_name)
        kept.append(new_name)
    return len(kept)


def extract_paper(paper: dict, out_dir: Path, tmp_dir: Path,
                  use_pdf: bool = True) -> dict:
    """Extract figures for one paper through the three-tier fallback."""
    arxiv_id = paper["arxiv_id"]
    paper_id = paper["paper_id"]
    if not arxiv_id:
        return {**paper, "tier_used": "none", "figures_count": 0,
                "figures": [], "reason": "no arxiv_id"}

    # Tier 1: ar5iv
    html = fetch_ar5iv(arxiv_id)
    base_url = f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}"
    if html:
        urls = parse_figures(html, base_url)
        figures = []
        for i, url in enumerate(urls):
            ext = Path(urllib.parse.urlparse(url).path).suffix.lower() or ".png"
            if ext not in {".png", ".jpg", ".jpeg", ".svg", ".gif"}:
                continue
            out_path = out_dir / f"{paper_id}_fig{len(figures)+1}.png"
            ok, _ = download_image(url, out_path)
            if ok:
                figures.append(str(out_path.name))
            time.sleep(0.3)  # per-image rate limit
        if figures:
            return {**paper, "tier_used": "ar5iv",
                    "figures_count": len(figures), "figures": figures}

    # Tier 3: PDF fallback. Skip the deprecated arxiv-vanity site.
    if use_pdf:
        n = extract_pdf_fallback(arxiv_id, paper_id, out_dir, tmp_dir)
        if n > 0:
            return {**paper, "tier_used": "pdf",
                    "figures_count": n,
                    "figures": [f"{paper_id}_fig{i+1}.png" for i in range(n)]}

    return {**paper, "tier_used": "none", "figures_count": 0,
            "figures": [], "reason": "all tiers failed"}


def write_index(records: list[dict], out_path: Path) -> None:
    """Write figure_index.md."""
    lines = ["# Figure Index", ""]
    lines.append(f"- Total papers processed: {len(records)}")
    n_with_fig = sum(1 for r in records if r["figures_count"] > 0)
    n_total_fig = sum(r["figures_count"] for r in records)
    lines.append(f"- Papers with figures: {n_with_fig} / {len(records)}")
    lines.append(f"- Total figures extracted: {n_total_fig}")
    lines.append("")
    lines.append("## Per-paper extraction record")
    lines.append("")
    lines.append("| Paper ID | arXiv | Tier | Figures |")
    lines.append("|---|---|---|---|")
    for r in sorted(records, key=lambda x: x["paper_id"]):
        figs_str = ", ".join(r["figures"]) if r["figures"] else "—"
        lines.append(f"| `{r['paper_id']}` | {r.get('arxiv_id') or '—'} | "
                     f"{r['tier_used']} | {r['figures_count']} ({figs_str[:80]}) |")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    if len(sys.argv) < 3:
        print("Usage: extract_web_figures.py <cards_dir> <out_figures_dir> "
              "[--limit N] [--no-pdf] [--paper-list <file>]")
        sys.exit(1)
    cards_dir = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    limit = None
    use_pdf = True
    paper_list_file = None
    args = sys.argv[3:]
    while args:
        a = args.pop(0)
        if a == "--limit":
            limit = int(args.pop(0))
        elif a == "--no-pdf":
            use_pdf = False
        elif a == "--paper-list":
            paper_list_file = args.pop(0)

    out_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = out_dir / "_tmp"
    tmp_dir.mkdir(exist_ok=True)

    all_papers = parse_cards(cards_dir)
    if paper_list_file:
        wanted = set(Path(paper_list_file).read_text().strip().splitlines())
        papers = [p for p in all_papers if p["paper_id"] in wanted]
        missing = wanted - {p["paper_id"] for p in papers}
        if missing:
            print(f"[warn] {len(missing)} paper_ids not found in cards: {sorted(missing)[:5]}...")
    else:
        papers = all_papers
    if limit:
        papers = papers[:limit]

    print(f"=== Processing {len(papers)} papers ===")
    records = []
    for i, p in enumerate(papers, 1):
        print(f"[{i}/{len(papers)}] {p['paper_id']} (arxiv: {p['arxiv_id']})", flush=True)
        rec = extract_paper(p, out_dir, tmp_dir, use_pdf=use_pdf)
        print(f"  → tier={rec['tier_used']}, figures={rec['figures_count']}", flush=True)
        records.append(rec)
        time.sleep(RATE_LIMIT_S)

    # Cleanup tmp
    try:
        tmp_dir.rmdir()
    except OSError:
        pass

    write_index(records, out_dir / "figure_index.md")
    print(f"=== Done. figure_index.md saved to {out_dir} ===")
    print(f"  Papers w/ figures: {sum(1 for r in records if r['figures_count'] > 0)}/{len(records)}")
    print(f"  Total figures: {sum(r['figures_count'] for r in records)}")


if __name__ == "__main__":
    main()
