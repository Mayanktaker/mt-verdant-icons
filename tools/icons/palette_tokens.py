# © Mayanktaker Computers & Web Development | https://mayanktaker.com
# Palette loader for the MT Verdant icon and cursor generators.
# Colors live in palette/icons.json; the top-level "colors"/"aliases" block IS the dark variant
# and "variants.light" holds the light recolor table (flat literal -> hex plus token overrides).

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PALETTE_PATH = REPO_ROOT / "palette" / "icons.json"


def load() -> dict:
    # Read the palette document once per call so edits are picked up without a rebuild step.
    return json.loads(PALETTE_PATH.read_text())


class VariantPalette:
    # Colors and artwork literal remap bound to one variant.

    def __init__(self, colors: dict[str, str], remap: dict[str, str]):
        # Validate before use: literals are case-stable and no value feeds a later replacement.
        keys_lower = {key.lower() for key in remap}
        for literal, value in remap.items():
            if literal != literal.upper():
                raise ValueError(f"palette literal {literal} must be uppercase")
            if value.lower() in keys_lower and value.lower() != literal.lower():
                raise ValueError(f"palette remap {literal} -> {value} would chain into another literal")
        self.colors = colors
        self.remap = remap

    def hex_value(self, token: str) -> str:
        # Current hex value for one semantic token.
        return self.colors[token]

    def rgb(self, token: str) -> tuple[int, int, int]:
        # Current token as an 8-bit RGB triple, for raster generators.
        value = self.colors[token].lstrip("#")
        return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))

    def rgba(self, token: str, alpha: int = 255) -> tuple[int, int, int, int]:
        # Current token as an 8-bit RGBA quadruple.
        return (*self.rgb(token), alpha)

    def resolve(self, text: str) -> str:
        # Rewrite known artwork literals to this variant's values.
        for literal, value in self.remap.items():
            text = text.replace(literal, value)
            text = text.replace(literal.lower(), value)
        return text


def for_variant(name: str) -> VariantPalette:
    # Build the palette binding for one variant ("dark" or "light").
    doc = load()
    if name == "dark":
        colors = doc["colors"]
        remap = {
            literal.upper(): colors[token]
            for token, literals in doc["aliases"].items()
            for literal in literals
        }
    elif name == "light":
        section = doc["variants"]["light"]
        colors = section["colors"]
        remap = {literal.upper(): value for literal, value in section["aliases"].items()}
        # Token literals join the remap only where light actually recolors them, so neutral
        # tokens (shadow black, PDF badge white) and vendored upstream glyphs stay untouched.
        for token, literals in doc["aliases"].items():
            if colors[token].upper() != doc["colors"][token].upper():
                for literal in literals:
                    remap[literal.upper()] = colors[token]
    else:
        raise ValueError(f"unknown variant: {name}")
    return VariantPalette(colors, remap)


def pack_name(kind: str, variant: str = "dark") -> str:
    # Pack directory name for a pack kind ("icons"/"cursors") and variant.
    key = kind if variant == "dark" else f"{kind}_light"
    return load()["packs"][key]


_DARK = for_variant("dark")
COLORS: dict[str, str] = _DARK.colors
ALIASES: dict[str, str] = _DARK.remap


def hex_value(token: str) -> str:
    # Dark-variant token value (module-level back-compat).
    return _DARK.hex_value(token)


def rgb(token: str) -> tuple[int, int, int]:
    # Dark-variant token as an 8-bit RGB triple (module-level back-compat).
    return _DARK.rgb(token)


def rgba(token: str, alpha: int = 255) -> tuple[int, int, int, int]:
    # Dark-variant token as an 8-bit RGBA quadruple (module-level back-compat).
    return _DARK.rgba(token, alpha)


def resolve(text: str) -> str:
    # Dark-variant literal remap (module-level back-compat).
    return _DARK.resolve(text)
