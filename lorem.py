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
