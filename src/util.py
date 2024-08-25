import datetime
import errno
import os
import stat
import shutil

from enum import Enum
from dataclasses import dataclass, field
from typing import List

from dateutil.relativedelta import relativedelta, SU, SA  # type: ignore

now = datetime.datetime.now(datetime.UTC).replace(
    hour=0, minute=0, second=0, microsecond=0
)
next_saturday = now + relativedelta(weekday=SA(0))
prev_sunday_52_weeks_ago = next_saturday - datetime.timedelta(weeks=52, days=6)


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
        match self.color:
            case Color.DARKEST_GREEN:
                return "\033[38;5;16m█\033[0m"
            case Color.DARK_GREEN:
                return "\033[38;5;22m█\033[0m"
            case Color.GREEN:
                return "\033[38;5;34m█\033[0m"
            case Color.LIGHT_GREEN:
                return "\033[38;5;40m█\033[0m"
            case Color.GREY:
                return "\033[38;5;28m█\033[0m"


@dataclass
class PixelBuffer:
    width: int
    height: int
    empty_pixel: Pixel
    buf: List[Pixel] = field(init=False)

    def __post_init__(self):
        self.buf = [self.empty_pixel for _ in range(self.width * self.height)]

    def __repr__(self):
        table = [
            [self.empty_pixel for _ in range(self.width)] for _ in range(self.height)
        ]

        for i, pixel in enumerate(self.buf):
            x = i // self.height
            y = i % self.height
            table[y][x] = pixel
        return "\n".join(["".join([str(pixel) for pixel in row]) for row in table])


def handle_remove_readonly(func, path, exc):  # type: ignore
    excvalue = exc[1]  # type: ignore
    if func in (os.rmdir, os.remove, os.unlink) and excvalue.errno == errno.EACCES:  # type: ignore
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # type: ignore
        func(path)
    else:
        raise


def rmtree_readonly(path: str):
    shutil.rmtree(path, onerror=handle_remove_readonly)  # type: ignore
