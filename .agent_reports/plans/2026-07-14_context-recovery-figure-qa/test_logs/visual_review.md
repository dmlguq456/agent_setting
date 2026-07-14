# Representative PNG Visual Review

- PNG: `representative_spectrogram.png`
- SHA-256: `9bbaec1e1765672283f17f251dd3aef38f027470af1b77f22f3580b31c7172e0`
- Reviewed: 2026-07-14T16:22:04+09:00 with `view_image` at original detail
- Y axis: PASS — 0, 6, 12, 18, 24 kHz ticks are visible
- Tick/label readability: PASS after correction
- Colorbar: PASS — visible −80 to 0 dB scale and label
- Shared scale: PASS — both panels declare and visibly share −80 to 0 dB
- Labels: PASS — panel titles, time, frequency, and magnitude labels are readable

The first visual inspection exposed clipped horizontal frequency/colorbar
labels and a clipped title. The fallback renderer was corrected to rotate the
axis labels and shorten/center the title, then the regenerated PNG was opened
again. The recorded hash belongs to the corrected second image.

Local Codex `figure-gen --check` returned exit 69 because matplotlib is not
installed. The evidence image was therefore generated with the recorded
Pillow fallback renderer; this unavailable tool-contract result is not treated
as a matplotlib generation pass.
