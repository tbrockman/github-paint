from dataclasses import dataclass
from typing import Tuple

from .fonts import Font
from .util import Pixel, PixelBuffer, Color, HAlign, VAlign


@dataclass
class Window:
    width: int
    height: int
    padding: Tuple[int, int, int, int] = (1, 1, 1, 1)  # top, right, bottom, left

    def draw(
        self,
        text: str,
        font: Font,
        repeat: bool = True,
        separator: str = " ",
        inverse: bool = False,
        h_align: HAlign = HAlign.CENTER,
        v_align: VAlign = VAlign.CENTER,
    ) -> PixelBuffer:
        """
        The draw function takes a text string, a font, and optional parameters to render the text in the window.

        Repeated text will be repeated as many times as possible (given window size), and then positioned according to specified alignment and padding.
        """
        blank_pixel = Pixel(Color(1) if not inverse else Color(4))

        text_width, text_height = font.get_text_dims(text)
        sep_width, sep_height = font.get_text_dims(separator)

        while repeat and text_width < self.width:
            text += separator + text
            text_width += (
                font.letter_spacing + sep_width + font.letter_spacing + text_width
            )

        text_height = max(text_height, sep_height) if repeat else text_height
        text_buffer = PixelBuffer(
            buf=[blank_pixel for _ in range(text_width * text_height)],
            width=text_width,
            height=text_height,
        )

        first_char = True
        i = 0

        while i < len(text_buffer.buf):
            for c in text:
                if not first_char:
                    for _ in range(font.letter_spacing * text_height):
                        text_buffer.buf[i] = blank_pixel
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
                        text_buffer.buf[i] = blank_pixel
                        i += 1
        window_buffer = PixelBuffer(
            buf=[blank_pixel for _ in range(self.width * self.height)],
            width=self.width,
            height=self.height,
        )
        return self.position_buffer_in_window(
            text_buffer, window_buffer, h_align, v_align
        )

    def position_buffer_in_window(
        self,
        buffer: PixelBuffer,
        window: PixelBuffer,
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
                    self.height - buffer.height + self.padding[0] - self.padding[2]
                ) // 2
            case VAlign.BOTTOM:
                delta_y = self.height - buffer.height - self.padding[2]

        match h_align:
            case HAlign.LEFT:
                delta_x = self.padding[3]
            case HAlign.CENTER:
                delta_x = (
                    self.width - buffer.width + self.padding[3] - self.padding[1]
                ) // 2
            case HAlign.RIGHT:
                delta_x = self.width - buffer.width - self.padding[1]

        for j in range(buffer.width):
            for i in range(buffer.height):
                window_x = j + delta_x
                window_y = i + delta_y

                if 0 <= window_x < window.width and 0 <= window_y < window.height:
                    buffer_index = j * buffer.height + i
                    window_index = window_x * window.height + window_y
                    window.buf[window_index] = buffer.buf[buffer_index]

        return window
