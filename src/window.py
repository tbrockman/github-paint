from dataclasses import dataclass
from typing import Tuple

from .fonts import Font
from .util import Pixel, PixelBuffer, Color, HAlign, VAlign


@dataclass
class Window(PixelBuffer):
    padding: Tuple[int, int, int, int] = (1, 1, 1, 1)  # top, right, bottom, left

    def __repr__(self):
        return super().__repr__()

    def draw_text(
        self,
        text: str,
        font: Font,
        repeat: bool = True,
        separator: str = " ",
        inverse: bool = False,
        h_align: HAlign = HAlign.CENTER,
        v_align: VAlign = VAlign.CENTER,
    ):
        """
        The draw function takes a text string, a font, and optional parameters to render the text in the window.

        Repeated text will be repeated as many times as possible (given window size), and then positioned according to specified alignment and padding.
        """

        text_width, text_height = font.get_text_dims(text)
        sep_width, sep_height = font.get_text_dims(separator)

        while repeat and text_width < self.width:
            text += separator + text
            text_width += (
                font.letter_spacing + sep_width + font.letter_spacing + text_width
            )

        text_height = max(text_height, sep_height) if repeat else text_height
        text_buffer = PixelBuffer(
            width=text_width,
            height=text_height,
            empty_pixel=self.empty_pixel,
        )

        first_char = True
        i = 0

        while i < len(text_buffer.buf):
            for c in text:
                if not first_char:
                    for _ in range(font.letter_spacing * text_height):
                        text_buffer.buf[i] = self.empty_pixel
                        i += 1

                first_char = False

                glyph = font.get_glyph(c)
                remaining_height = (
                    text_height - glyph.height
                )  # guaranteed to be positive

                for x in range(glyph.width):
                    col = glyph.get_col(x)

                    for pixel in col:
                        text_buffer.buf[i] = (
                            pixel
                            if not inverse
                            else Pixel(Color(4 - pixel.color.value + 1))
                        )
                        i += 1

                    for _ in range(remaining_height):
                        text_buffer.buf[i] = self.empty_pixel
                        i += 1
        self.layout(text_buffer, h_align, v_align)

    def layout(
        self,
        buffer: PixelBuffer,
        h_align: HAlign,
        v_align: VAlign,
    ):
        delta_y = 0
        delta_x = 0

        match v_align:
            case VAlign.TOP:
                delta_y = self.padding[0]
            case VAlign.CENTER:
                delta_y = (
                    (self.height - buffer.height) // 2
                    + self.padding[0]
                    - self.padding[2]
                )
            case VAlign.BOTTOM:
                delta_y = self.height - buffer.height - self.padding[2]

        match h_align:
            case HAlign.LEFT:
                delta_x = self.padding[3]
            case HAlign.CENTER:
                delta_x = (
                    (self.width - buffer.width) // 2 + self.padding[3] - self.padding[1]
                )
            case HAlign.RIGHT:
                delta_x = self.width - buffer.width - self.padding[1]

        for j in range(buffer.width):
            for i in range(buffer.height):
                window_x = j + delta_x
                window_y = i + delta_y

                if 0 <= window_x < self.width and 0 <= window_y < self.height:
                    buffer_index = j * buffer.height + i
                    window_index = window_x * self.height + window_y
                    self.buf[window_index] = buffer.buf[buffer_index]
