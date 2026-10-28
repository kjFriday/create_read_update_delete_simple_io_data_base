# ==== Generic Company Inc. portfolio ====================================
# Project: create_read_update_delete_simple_io_data_base | File: test_sigil.py
# About: Tests for sigil: fixed vectors for a few neutral names, plus the grid's invariants.
# Copyright (c) 2026 kjFriday | SPDX-License-Identifier: AGPL-3.0-only
# You may change this file under the AGPL-3.0. The stamp at the end marks
# the version kjFriday wrote. Verify with the portfolio's stamp.py --check.
# Reused code, if any, is mapped in PROVENANCE.md.
# ========================================================================

# ==== Generic Company Inc. portfolio ===============================================
# Project: create_read_update_delete_simple_io_data_base | File: test_sigil.py
# About: Tests for sigil: fixed vectors for a few neutral names, plus the grid's invariants.
# Copyright (c) 2026 kjFriday | SPDX-License-Identifier: AGPL-3.0-only
# You may change this file under the AGPL-3.0. The stamp at the end marks
# the version kjFriday wrote. Verify with the portfolio's stamp.py --check.
# Reused code, if any, is mapped in PROVENANCE.md.
# ========================================================================

"""Tests for sigil: fixed vectors for a few neutral names, plus the grid's invariants."""

import unittest

from sigil import SIZE, grid, sigil, tint

VECTORS = {
    "Ada Reyes": (
        ["..#.#..", ".#####.", "##.#.##", "##...##", "#.#.#.#", "#.###.#", "#.###.#"],
        (175, 135, 255),
    ),
    "Generic Company Inc.": (
        ["..###..", "..#.#..", ".#.#.#.", "...#...", "##.#.##", "#######", "#.....#"],
        (95, 215, 175),
    ),
    "Python Toolkit": (
        ["..###..", ".#.#.#.", "#.....#", "##...##", ".#####.", "#..#..#", "...#..."],
        (0, 215, 255),
    ),
}


def pattern(g):
    return ["".join("#" if cell else "." for cell in row) for row in g]


class SigilTest(unittest.TestCase):
    def test_vectors(self):
        for name, (rows, rgb) in VECTORS.items():
            g, colour = sigil(name)
            self.assertEqual(pattern(g), rows, name)
            self.assertEqual(colour, rgb, name)

    def test_grid_is_square_and_mirrored(self):
        for name in ["Generic Company Inc.", "Ben Park", "Widget"]:
            g = grid(name)
            self.assertEqual(len(g), SIZE)
            for row in g:
                self.assertEqual(len(row), SIZE)
                self.assertEqual(row, row[::-1], name)

    def test_never_blank(self):
        for name in ["", "a", "zzz", "Generic Company Inc."]:
            self.assertTrue(any(any(row) for row in grid(name)), repr(name))

    def test_stable_and_name_specific(self):
        self.assertEqual(sigil("Generic Company Inc."), sigil("Generic Company Inc."))
        self.assertNotEqual(grid("Generic Company Inc."), grid("Generic Company inc."))

    def test_tint_is_an_rgb_tuple(self):
        for name in ["", "Ada Reyes", "Zoë"]:
            rgb = tint(name)
            self.assertEqual(len(rgb), 3)
            self.assertTrue(all(0 <= c <= 255 for c in rgb))


if __name__ == "__main__":
    unittest.main()

# ==== stamp v1 | author=kjFriday | hmac-sha256=2352de08f6f8f0fe80d401c8d77e1ebd613db577f9c3d7d54cfb9110e678be8f ====
