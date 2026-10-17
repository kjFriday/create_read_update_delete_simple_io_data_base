"""Identicons for employees and customers: a mirrored bit grid and a colour, both derived from a name.

The same name always gives the same mark. Nothing is stored or fetched.
"""

import hashlib

SIZE = 7  # cells per side; odd, so there is a true centre column
FILL = 44  # a cell is lit when its digest byte % 100 < FILL; over bytes 0-255 that lights about 51.6% of cells
NEUTRAL = (39, 79, 141, 209, 214, 105, 45, 168)  # xterm-256 colour indices
LEVELS = (0, 95, 135, 175, 215, 255)  # channel steps of the xterm 6x6x6 colour cube


def _sha256(text):
    return hashlib.sha256(text.encode("utf-8")).digest()


def grid(name):
    """SIZE x SIZE booleans, mirrored left to right; never entirely blank."""
    d = _sha256(name)
    half = (SIZE + 1) // 2
    g = [[False] * SIZE for _ in range(SIZE)]
    for y in range(SIZE):
        for x in range(half):
            g[y][x] = g[y][SIZE - 1 - x] = d[(y * half + x) % len(d)] % 100 < FILL
    if not any(any(row) for row in g):
        g[SIZE // 2][SIZE // 2] = True
    return g


def tint(name):
    """The name's colour as an (r, g, b) tuple, picked from NEUTRAL."""
    n = NEUTRAL[_sha256("tint:" + name)[0] % len(NEUTRAL)] - 16  # every NEUTRAL index is in the cube (16-231)
    return LEVELS[n // 36], LEVELS[n // 6 % 6], LEVELS[n % 6]


def sigil(name):
    return grid(name), tint(name)
