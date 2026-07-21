# Design scaffolds

Reusable starting points for bezels, deck shells, tweak panels, and comparison
canvases. Each self-contained HTML file is copied into the design artifact
folder, filled with real content, and verified through the active runtime
adapter's visual harness. The portable rendering contract lives in
[`roles/units/design/_design-rules.md`](../roles/units/design/_design-rules.md).

| Scaffold | File | Purpose | Key behavior |
|---|---|---|---|
| `deck_stage` | `deck_stage/deck_stage.html` | Slide decks | Auto-scaled 1920×1080 fixed canvas with letterboxing; keyboard navigation (← → Space Home End); slide counter; print-to-PDF with one slide per page; speaker-note slots |
| `tweaks_panel` | `tweaks_panel/tweaks_panel.html` | Variant controls | Host protocol in which the panel only sets CSS variables; localStorage persistence; curated swatches instead of a free-form picker. **For a new version, add a tweak here instead of adding another file.** |
| `device_frames` | `device_frames/device_frames.html` | Device mockup bezels | `.ios-frame` for a phone notch, status bar, and home indicator; `.browser-frame` for desktop browser traffic lights and address bar. Pure CSS |
| `design_canvas` | `design_canvas/design_canvas.html` | Compare two or more options | Responsive grid with per-option labels for direction exploration |
| `image_slot` | `image_slot/image_slot.html` | Image placeholder | Drag-and-drop and click upload with localStorage persistence. **Use this to reserve space; do not fake an image with SVG.** |

## Workflow

1. `design-components` chooses the scaffold that fits the scope and request, then copies it into the design folder
   (for example, `slide` → `deck_stage.html` → `03_components/slides/slides.html`).
2. Replace the example blocks with real content; see the `HOW TO USE` comments.
3. Verify the render through the active adapter's browser-backed visual harness:
   render the file, capture a screenshot, collect console errors, inspect the
   image, and rerender after fixes. Follow the adapter bootstrap for its concrete
   command or tool surface; do not substitute a source-only check for a render.
4. When the requested handoff format is supported, the current shared converter
   is [`tools/design-mcp/convert.mjs`](../tools/design-mcp/convert.mjs). Treat it
   as an optional tool surface rather than a capability guaranteed by every
   adapter, and report the adapter fallback when it is unavailable.

## Rules

- Every scaffold has zero external build dependencies and opens directly in a browser, preserving standalone-artifact parity.
- Scale rules such as body text ≥ 24 px for decks and touch targets ≥ 44 px for mobile live in `roles/units/design/_design-rules.md`.
- All five scaffolds have passed render verification with zero console errors.
