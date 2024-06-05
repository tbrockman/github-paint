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