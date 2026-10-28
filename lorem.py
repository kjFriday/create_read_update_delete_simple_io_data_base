# ==== Generic Company Inc. portfolio ====================================
# Project: create_read_update_delete_simple_io_data_base | File: lorem.py
# About: Deterministic lorem ipsum: placeholder words, sentences and paragraphs drawn from a...
# Copyright (c) 2026 kjFriday | SPDX-License-Identifier: AGPL-3.0-only
# You may change this file under the AGPL-3.0. The stamp at the end marks
# the version kjFriday wrote. Verify with the portfolio's stamp.py --check.
# Reused code, if any, is mapped in PROVENANCE.md.
# ========================================================================

# ==== Generic Company Inc. portfolio ===============================================
# Project: create_read_update_delete_simple_io_data_base | File: lorem.py
# About: Deterministic lorem ipsum: placeholder words, sentences and paragraphs drawn from a...
# Copyright (c) 2026 kjFriday | SPDX-License-Identifier: AGPL-3.0-only
# You may change this file under the AGPL-3.0. The stamp at the end marks
# the version kjFriday wrote. Verify with the portfolio's stamp.py --check.
# Reused code, if any, is mapped in PROVENANCE.md.
# ========================================================================

"""Deterministic lorem ipsum: placeholder words, sentences and paragraphs drawn from a seeded random.Random."""

WORDS = (
    "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore "
    "magna aliqua enim ad minim veniam quis nostrud exercitation ullamco laboris nisi aliquip ex ea commodo "
    "consequat duis aute irure in reprehenderit voluptate velit esse cillum fugiat nulla pariatur excepteur sint "
    "occaecat cupidatat non proident sunt culpa qui officia deserunt mollit anim id est laborum"
).split()


def words(rng, n):
    return " ".join(rng.choice(WORDS) for _ in range(max(n, 0)))


def sentence(rng, low=4, high=10):
    """One capitalised sentence of low..high words, ending in a full stop."""
    text = words(rng, rng.randint(low, high))
    return text[:1].upper() + text[1:] + "." if text else ""


def paragraph(rng, low=2, high=4, limit=None):
    """low..high sentences; cut back to whole words within `limit` characters when given."""
    text = " ".join(sentence(rng) for _ in range(rng.randint(low, high)))
    if limit is not None and len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0].rstrip(",") + "."
    return text

# ==== stamp v1 | author=kjFriday | hmac-sha256=43018d3a5da80fcda8adf49b21153bccdc00a394e50ba2bf2c3329dc399f4c16 ====
