"""Regression coverage for Fleet's herdr-specific tint fallback."""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fleet import render  # noqa: E402


class HerdrTintTest(unittest.TestCase):
    def setUp(self):
        self._tint_ok = render._TINT_OK
        self._tint_pair = dict(render._TINT_PAIR)

    def tearDown(self):
        render._TINT_OK = self._tint_ok
        render._TINT_PAIR.clear()
        render._TINT_PAIR.update(self._tint_pair)

    def _init_colors(self, herdr):
        env = {"HERDR_ENV": "1"} if herdr else {}
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(render.curses, "COLORS", 256, create=True), \
                mock.patch.object(render.curses, "start_color"), \
                mock.patch.object(render.curses, "use_default_colors"), \
                mock.patch.object(render.curses, "init_pair") as init_pair, \
                mock.patch.object(
                    render.curses, "color_pair", side_effect=lambda pair: pair << 8
                ), \
                mock.patch.object(render.curses, "can_change_color", return_value=True), \
                mock.patch.object(render.curses, "init_color") as init_color:
            render._init_colors()
        return init_pair, init_color

    def test_herdr_uses_rail_fallback_without_fixed_tint_backgrounds(self):
        init_pair, init_color = self._init_colors(herdr=True)

        self.assertFalse(render._TINT_OK)
        self.assertEqual(render._TINT_PAIR, {})
        self.assertFalse(
            any(call.args[2] in set(render._TINT_LVL.values()) for call in init_pair.call_args_list)
        )
        init_color.assert_not_called()

    def test_plain_256_color_terminal_keeps_panel_tints(self):
        init_pair, init_color = self._init_colors(herdr=False)

        self.assertTrue(render._TINT_OK)
        self.assertEqual(
            len(render._TINT_PAIR),
            len(render._TINT_LVL) * 7,
        )
        self.assertTrue(
            any(call.args[2] in set(render._TINT_LVL.values()) for call in init_pair.call_args_list)
        )
        init_color.assert_any_call(17, 55, 60, 130)


if __name__ == "__main__":
    unittest.main()
