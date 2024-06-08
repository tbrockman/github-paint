from dataclasses import dataclass
from typing import List, Tuple

from .fonts import Font
from .util import Pixel, Color, Alignment


@dataclass
class Window:
    width: int
    height: int
    padding: Tuple[int, int, int, int] = (1, 1, 1, 1)  # top, right, bottom, left

    def print(self, pixels: List[Pixel]):
        table = [
            [Pixel(Color(1)) for _ in range(self.width)] for _ in range(self.height)
        ]

        for i, pixel in enumerate(pixels):
            x = i // self.height
            y = i % self.height
            table[y][x] = pixel

        for row in table:
            print("".join([str(pixel) for pixel in row]))

    # TODO: allow center and left-alignment within a window/interval, adjust repeat functionality accordingly
    def draw(
        self,
        text: str,
        font: Font,
        repeat=True,
        separator=" ",
        inverse=False,
        alignment=Alignment.RIGHT,
    ) -> List[Pixel]:
        """
        The draw function takes a text string, a font, and optional parameters to render the text in the window.

        NOTE: The text will be right-aligned by default, with the option to repeat the text across the window.

        Repeated text will be repeated as many times as possible, and then aligned to the desired anchor point. Any overflow is then truncated.
        """

        text_rv = (
            text[::-1] + separator[::-1]
        )  # Reverse the text, for a right-aligned layout
        blank_pixel = Pixel(Color(1) if not inverse else Color(4))
        rendered: List[Pixel] = [
            blank_pixel
            for _ in range(
                (self.width + self.padding[1] + self.padding[2])
                * (self.height + self.padding[0] + self.padding[3])
            )
        ]
        i = self.padding[3] * self.height  # Start with right padding

        while i < len(rendered):
            for c in text_rv:
                if c == " ":
                    i += font.letter_spacing * self.height * 2
                    continue

                glyph = font.get_glyph(c)

                # Render each column of the glyph, from right to left
                # With appropriate top and bottom padding
                for x in range(glyph.width - 1, -1, -1):
                    if i >= len(rendered):
                        break

                    # Add top padding
                    for _ in range(self.padding[0]):
                        i += 1

                    if i >= len(rendered):
                        break

                    # Add the column (from bottom to top, since as weekdays decrease, the y-axis increases)
                    for pixel in glyph.get_col(x)[::-1]:
                        rendered[i] = (
                            pixel
                            if not inverse
                            else Pixel(Color(4 - pixel.color.value + 1))
                        )  # + 1 since we can't use grey
                        i += 1

                    if i >= len(rendered):
                        break

                    # Add bottom padding
                    for _ in range(self.padding[1]):
                        i += 1

                if i >= len(rendered):
                    break

                # Add letter spacing
                for _ in range(font.letter_spacing * self.height):
                    i += 1

            if not repeat or i >= len(rendered):
                break

        # Force end padding
        for j in range(self.padding[3] * self.height):
            rendered[len(rendered) - j - 1] = blank_pixel

        return rendered
