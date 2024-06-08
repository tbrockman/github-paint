import datetime

from enum import Enum
from dataclasses import dataclass

from dateutil.relativedelta import relativedelta, SU, SA

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


class Alignment(Enum):
    LEFT = 0
    CENTER = 1
    RIGHT = 2


@dataclass
class Pixel:
    color: Color

    def __repr__(self):
        return "█" if self.color != Color.LIGHT_GREEN else " "
