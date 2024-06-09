import datetime

from enum import Enum
from dataclasses import dataclass
from typing import List

from dateutil.relativedelta import relativedelta, SU, SA  # type: ignore

now = datetime.datetime.now(datetime.UTC).replace(
    hour=0, minute=0, second=0, microsecond=0
)
sunday_of_this_date_last_year = now - relativedelta(years=1, weekday=SU(-1))
next_saturday = now + relativedelta(weekday=SA(0))


def sunday_of_date(date: datetime.datetime) -> datetime.datetime:
    return date - relativedelta(weekday=SU(-1))


def next_saturday_of_date(date: datetime.datetime) -> datetime.datetime:
    return date + relativedelta(weekday=SA(0))


class Color(Enum):
    GREY = 0  # unused as we can't manually draw grey (no commit) pixels in GitHub contributions
    LIGHT_GREEN = 1
    GREEN = 2
    DARK_GREEN = 3
    DARKEST_GREEN = 4


class HAlign(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class VAlign(str, Enum):
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"


@dataclass
class Pixel:
    color: Color

    def __repr__(self):
        return "█" if self.color != Color.LIGHT_GREEN else " "


@dataclass
class PixelBuffer:
    buf: List[Pixel]
    width: int
    height: int

    def __repr__(self):
        table = [
            [Pixel(Color(1)) for _ in range(self.width)] for _ in range(self.height)
        ]

        for i, pixel in enumerate(self.buf):
            x = i // self.height
            y = i % self.height
            table[y][x] = pixel
        return "\n".join(["".join([str(pixel) for pixel in row]) for row in table])
