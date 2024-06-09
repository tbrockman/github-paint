from typing import List
from dataclasses import dataclass

from ..util import Pixel


@dataclass
class Glyph:
    pixels: List[Pixel]
    width: int
    height: int

    def get_col(self, x: int) -> List[Pixel]:
        return [self.pixels[y * self.width + x] for y in range(self.height)]


@dataclass
class Font:
    glyphs: List[Glyph]
    letter_spacing: int = 1

    def get_glyph(self, c: str) -> Glyph:
        return self.glyphs[ord(c)]

    def get_text_dims(self, text: str) -> tuple[int, int]:
        glyphs = [self.get_glyph(c) for c in text]
        width = (
            sum(glyph.width for glyph in glyphs) + (len(text) - 1) * self.letter_spacing
        )
        height = max(glyph.height for glyph in glyphs)
        return width, height
