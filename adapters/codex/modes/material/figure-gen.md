# Codex Material Figure Gen Mode

This is a Codex-native realization guide generated from the portable mode
inventory. It is adapter-owned output, not a legacy runtime mode copy.

## Source Order

1. Read `roles/MODES.md`.
2. Read `roles/modes/material/figure-gen.md` for the portable mode contract.
3. Run `adapters/codex/bin/preflight.sh mode-info material/figure-gen`.
4. Obey the reported status, tool contract, runtime surface, and fallback before claiming support.

## Codex Runtime Mapping

- Status: `tool-contract`
- Realization: `portable-with-tool-contract`
- Tool Contract: `figure-gen`
- Tool Contract Check: `adapters/codex/bin/preflight.sh figure-gen --check <script.py>`
- Runtime Surface: `adapter-owned-figure-gen`
- Fallback: `satisfy-tool-contract-or-report-unavailable`
- Requirement: run the adapter-owned matplotlib figure script launcher for generated figure scripts, or report unavailable
- Note: Codex may use the persona only after satisfying or explicitly downgrading the named tool contract.

## Use

- Use Codex file, terminal, approval, sandbox, hook, and skill surfaces.
- Run `adapters/codex/bin/preflight.sh write <file> [session-id]` before edits.
- For `tool-contract` modes, run the named contract check before claiming the tool-backed result.
- If a required local provider or executable is unavailable, report the unavailable contract instead of silently downgrading.
- Treat `adapters/codex/modes/material/figure-gen.md` as the adapter-owned mode guide for this runtime.

## Projected Portable Mode Contract

The following contract is projected from `roles/modes/material/figure-gen.md` with non-Codex runtime
surfaces rewritten to Codex-native preflight/tool-contract wording.

# Mode: figure-gen

> The material-role router reads this file, then adopts the persona.

Invocation: `figure <name> <spec>` or an equivalent natural-language request.

Create reproducible matplotlib or seaborn figures for papers and presentations. One unit includes vector PDF, raster preview PNG, and the script that generated them.

## Outputs

- `<paper_dir>/figures/<name>.pdf`, with `pdf.fonttype=42`
- `<paper_dir>/figures/plot_<name>.py`, self-contained with minimal dependencies
- `<paper_dir>/figures/<name>_preview.png`, about 200 dpi by default

## Paper Defaults

- Serif fallback: Times New Roman → Nimbus Roman → Liberation Serif → DejaVu Serif; STIX for math.
- Choose dimensions for the placement: 6.4×2.8 in single-column landscape, 4.5×2.8 in each side-by-side panel, or 3.5×2.6 in vertical single-column use.
- Keep a coherent palette across figures in the same paper.
- Use subtle grids around alpha 0.25 and linewidth 0.5, including minor grids on logarithmic axes.
- Set both PDF and PostScript font type to 42.
- Presentation mode instead uses a larger 16:9-aware sans-serif treatment.

## Spectrogram Integrity

- Keep native sample rate and use fixed windows: 512 samples at 48 kHz, 400 at 16 kHz, and 256 at 8 kHz. Use the nearest of these for other rates rather than interpolating a novel window rule.
- Do not resample merely to make comparison panels uniform; sample rate is meaningful context.
- Within one comparison group, share `vmin` and `vmax` across every spectrogram so intensity is comparable. Separate figures may use different ranges.
- Use `mem profile 01_paper_figure_style` for panel and label preferences when that context is relevant; an explicit current-turn instruction overrides it.

## Script Convention

Collect colors, dimensions, and fonts as top-level constants. Comment domain equations. Increase preview DPI only when the requested review needs it. Automatic production creates individual PNGs and, when requested, one combined PPTX; do not create one PPTX wrapper per figure.

Return `<output path> -- <verdict>` plus a 3–5 line summary in the user's communication language and name the reproduction script.
