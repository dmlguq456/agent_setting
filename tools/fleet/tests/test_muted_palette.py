"""Muted Fleet foreground and panel palette stays calm and semantic."""

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fleet import render  # noqa: E402


class MutedPaletteTest(unittest.TestCase):
    def test_256_color_palette_is_low_chroma(self):
        self.assertEqual(render._MUTED_256, {
            "soft": 253,
            "green": 151,
            "yellow": 187,
            "red": 181,
            "cyan": 152,
            "magenta": 182,
            "blue": 146,
            "vanilla": 230,
            "chrome": 252,
            "warning": 131,
        })
        with mock.patch.object(render.curses, "COLORS", 256, create=True):
            self.assertEqual(render._palette_fg("green", 2), 151)
            self.assertEqual(render._palette_fg("blue", 4), 146)

    def test_low_color_terminal_keeps_native_fallback(self):
        with mock.patch.object(render.curses, "COLORS", 8, create=True):
            self.assertEqual(render._palette_fg("green", 2), 2)
            self.assertEqual(render._palette_fg("soft", 7), 7)

    def test_panel_tints_keep_brightness_and_reduce_chroma(self):
        self.assertEqual(render._TINT_LVL, {
            "b": 235, "c": 238, "B": 236, "C": 236, "k": 235, "i": 235,
        })
        self.assertEqual(render._TINT_LVL["b"], render._TINT_LVL["i"])
        self.assertNotIn(60, render._TINT_LVL.values())
        self.assertNotIn(95, render._TINT_LVL.values())

    def test_semantic_hues_and_soft_focal_text_are_preserved(self):
        self.assertEqual(render._HUE_OF["g_work"][0], "g")
        self.assertEqual(render._HUE_OF["g_idle"][0], "y")
        self.assertEqual(render._HUE_OF["g_dead"][0], "r")
        badge_hues = [render._HUE_OF[key][0] for key in render._BADGE_KEY.values()]
        self.assertEqual(badge_hues, ["c", "m", "l"])
        self.assertEqual(render._HUE_OF["name_work"][0], "w")


if __name__ == "__main__":
    unittest.main()
