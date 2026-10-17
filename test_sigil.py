"""Tests for sigil: fixed vectors for a few neutral names, plus the grid's invariants."""

import unittest

from sigil import SIZE, grid, sigil, tint

VECTORS = {
    "Ada Reyes": (
        ["..#.#..", ".#####.", "##.#.##", "##...##", "#.#.#.#", "#.###.#", "#.###.#"],
        (175, 135, 255),
    ),
    "ACME Inc.": (
        ["#.###.#", "#.....#", "#..#..#", ".#.#.#.", "##...##", ".#.#.#.", ".#...#."],
        (175, 135, 255),
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
        for name in ["ACME Inc.", "Ben Park", "Widget"]:
            g = grid(name)
            self.assertEqual(len(g), SIZE)
            for row in g:
                self.assertEqual(len(row), SIZE)
                self.assertEqual(row, row[::-1], name)

    def test_never_blank(self):
        for name in ["", "a", "zzz", "ACME Inc."]:
            self.assertTrue(any(any(row) for row in grid(name)), repr(name))

    def test_stable_and_name_specific(self):
        self.assertEqual(sigil("ACME Inc."), sigil("ACME Inc."))
        self.assertNotEqual(grid("ACME Inc."), grid("ACME inc."))

    def test_tint_is_an_rgb_tuple(self):
        for name in ["", "Ada Reyes", "Zoë"]:
            rgb = tint(name)
            self.assertEqual(len(rgb), 3)
            self.assertTrue(all(0 <= c <= 255 for c in rgb))


if __name__ == "__main__":
    unittest.main()
