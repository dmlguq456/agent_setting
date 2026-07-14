#!/usr/bin/env python3
"""Generate a deterministic full-band QA fixture with an independent metric band."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


METRIC_BAND_HZ = (20, 1000)
FIGURE_BAND_HZ = (0, 24000)
SAMPLE_RATE_HZ = 48000
VMIN_DB = -80
VMAX_DB = 0
COLORMAP = "magma"


def make_panel(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    frequencies = np.linspace(FIGURE_BAND_HZ[0], FIGURE_BAND_HZ[1], 256)[:, None]
    times = np.linspace(0, 1, 320)[None, :]
    harmonic = 28 * np.sin(2 * np.pi * times * 3 + frequencies / 3000)
    envelope = -60 + 28 * np.exp(-((frequencies - 6500) / 5000) ** 2)
    return np.clip(envelope + harmonic + rng.normal(0, 3, (256, 320)), VMIN_DB, VMAX_DB)


def main() -> None:
    panels = [make_panel(7), make_panel(11)]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharex=True, sharey=True)
    image = None
    for axis, data, title in zip(axes, panels, ("Reference", "Estimate")):
        image = axis.imshow(
            data,
            origin="lower",
            aspect="auto",
            extent=(0, 1, FIGURE_BAND_HZ[0], FIGURE_BAND_HZ[1]),
            vmin=VMIN_DB,
            vmax=VMAX_DB,
            cmap=COLORMAP,
        )
        axis.set_title(title)
        axis.set_xlabel("Time (s)")
        axis.set_ylim(*FIGURE_BAND_HZ)
        ticks = [0, 6000, 12000, 18000, 24000]
        axis.set_yticks(ticks, ["0", "6", "12", "18", "24"])
    axes[0].set_ylabel("Frequency (kHz)")
    colorbar = fig.colorbar(image, ax=axes, pad=0.02, fraction=0.035)
    colorbar.set_label("Magnitude (dB)")
    fig.suptitle("48 kHz full-band spectrogram — shared scale")
    fig.subplots_adjust(left=0.08, right=0.89, bottom=0.17, top=0.82, wspace=0.08)
    output = Path(__file__).with_name("representative_spectrogram.png")
    fig.savefig(output, dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
