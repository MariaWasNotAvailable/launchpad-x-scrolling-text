#!/usr/bin/env python3
"""Unit tests for launchpad_scroll.py"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import launchpad_scroll as ls


class TestClamp8Bit(unittest.TestCase):
    def test_min(self):
        self.assertEqual(ls.clamp_8bit(-1), 0)
        self.assertEqual(ls.clamp_8bit(-1000), 0)

    def test_max(self):
        self.assertEqual(ls.clamp_8bit(256), 255)
        self.assertEqual(ls.clamp_8bit(999), 255)

    def test_in_range(self):
        self.assertEqual(ls.clamp_8bit(0), 0)
        self.assertEqual(ls.clamp_8bit(127), 127)
        self.assertEqual(ls.clamp_8bit(255), 255)
        self.assertEqual(ls.clamp_8bit(42), 42)

    def test_float(self):
        self.assertEqual(ls.clamp_8bit(127.9), 127)


class TestClamp7Bit(unittest.TestCase):
    def test_min(self):
        self.assertEqual(ls.clamp_7bit(-1), 0)
        self.assertEqual(ls.clamp_7bit(-1000), 0)

    def test_max(self):
        self.assertEqual(ls.clamp_7bit(128), 127)
        self.assertEqual(ls.clamp_7bit(999), 127)

    def test_in_range(self):
        self.assertEqual(ls.clamp_7bit(0), 0)
        self.assertEqual(ls.clamp_7bit(127), 127)
        self.assertEqual(ls.clamp_7bit(42), 42)


class TestParseHex(unittest.TestCase):
    def test_valid_lowercase(self):
        self.assertEqual(ls.parse_hex("#00ff00"), (0, 255, 0))

    def test_valid_uppercase(self):
        self.assertEqual(ls.parse_hex("#FF00FF"), (255, 0, 255))

    def test_valid_mixed_case(self):
        self.assertEqual(ls.parse_hex("#AbCdEf"), (171, 205, 239))

    def test_valid_black_and_white(self):
        self.assertEqual(ls.parse_hex("#000000"), (0, 0, 0))
        self.assertEqual(ls.parse_hex("#FFFFFF"), (255, 255, 255))

    def test_invalid_too_short(self):
        with self.assertRaises(ValueError):
            ls.parse_hex("#fff")

    def test_invalid_too_long(self):
        with self.assertRaises(ValueError):
            ls.parse_hex("#00ff00ff")

    def test_invalid_non_hex(self):
        with self.assertRaises(ValueError):
            ls.parse_hex("#gggggg")

    def test_parse_single_color_requires_hash_for_hex(self):
        # parse_single_color routes non-hash strings to parse_named
        with self.assertRaises(ValueError):
            ls.parse_single_color("00ff00")


class TestParseNamed(unittest.TestCase):
    def test_green(self):
        self.assertEqual(ls.parse_named("green"), (0, 128, 0))

    def test_case_insensitive(self):
        self.assertEqual(ls.parse_named("GREEN"), (0, 128, 0))
        self.assertEqual(ls.parse_named("Green"), (0, 128, 0))

    def test_crimson(self):
        self.assertEqual(ls.parse_named("crimson"), (220, 20, 60))

    def test_unknown(self):
        with self.assertRaises(ValueError):
            ls.parse_named("notacolour")


class TestParseSingleColor(unittest.TestCase):
    def test_hex(self):
        self.assertEqual(ls.parse_single_color("#00ff00"), (0, 255, 0))

    def test_named(self):
        self.assertEqual(ls.parse_single_color("green"), (0, 128, 0))

    def test_whitespace_stripped(self):
        self.assertEqual(ls.parse_single_color("  #00ff00  "), (0, 255, 0))


class TestBuildMessage(unittest.TestCase):
    def test_default_colour(self):
        msg = ls.build_message("Hi", 6, ls.DEFAULT_COLOR, loop=0)
        self.assertEqual(msg[:6], ls.HEADER)
        # payload: [loop, speed] + colourspec + text bytes
        self.assertEqual(msg[6], 0)  # loop
        self.assertEqual(msg[7], 6)  # speed
        # colourspec: 01 R G B
        self.assertEqual(msg[8:12], [0x01, 0, 63, 0])  # 127//2 = 63
        self.assertEqual(msg[12:], [ord('H'), ord('i')])

    def test_custom_speed(self):
        msg = ls.build_message("A", 12, (255, 0, 0), loop=0)
        self.assertEqual(msg[7], 12)

    def test_loop(self):
        msg = ls.build_message("A", 6, (0, 127, 0), loop=1)
        self.assertEqual(msg[6], 1)

    def test_clamped_colour(self):
        # 255 // 2 = 127
        msg = ls.build_message("A", 6, (255, 255, 255), loop=0)
        self.assertEqual(msg[8:12], [0x01, 127, 127, 127])


if __name__ == "__main__":
    unittest.main()
