# © Mayanktaker Computers & Web Development | https://mayanktaker.com
# Palette loader for the MT Verdant icon and cursor generators.
# Colors live in palette/icons.json; artwork literals listed under "aliases" are remapped to the
# current token value so changing a token updates every icon that uses it.

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PALETTE_PATH = REPO_ROOT / "palette" / "icons.json"


def load() -> dict:
    # Read the palette document once per call so edits are picked up without a rebuild step.
    return json.loads(PALETTE_PATH.read_text())


_DOC = load()
COLORS: dict[str, str] = _DOC["colors"]
ALIASES: dict[str, str] = {
    literal.upper(): COLORS[token]
    for token, literals in _DOC["aliases"].items()
    for literal in literals
}


def hex_value(token: str) -> str:
    # Current hex value for one semantic token.
    return COLORS[token]


def rgb(token: str) -> tuple[int, int, int]:
    # Current token as an 8-bit RGB triple, for raster generators.
    value = COLORS[token].lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def rgba(token: str, alpha: int = 255) -> tuple[int, int, int, int]:
    # Current token as an 8-bit RGBA quadruple.
    return (*rgb(token), alpha)


def resolve(text: str) -> str:
    # Rewrite known artwork literals to their current token value (identity until a token changes).
    for literal, value in ALIASES.items():
        text = text.replace(literal, value)
        text = text.replace(literal.lower(), value)
    return text
