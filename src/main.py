import datetime
import math
import os
import typer

from typing_extensions import Annotated

from dateutil.relativedelta import relativedelta, SU, SA

from .fonts.default import nitram_micro_mono_CP437
from .github import GitHub
from .window import Window

now = datetime.datetime.now(datetime.UTC).replace(
    hour=0, minute=0, second=0, microsecond=0
)
sunday_of_this_date_last_year = now - relativedelta(years=1, weekday=SU(-1))
next_saturday = now + relativedelta(weekday=SA(0))


def sunday_of_date(date: datetime.datetime) -> datetime.datetime:
    return date - relativedelta(weekday=SU(-1))


def next_saturday_of_date(date: datetime.datetime) -> datetime.datetime:
    return date + relativedelta(weekday=SA(0))


def main(
    user: Annotated[
        str,
        typer.Argument(
            help="GitHub user to generate the contribution banner for (e.g. 'tbrockman')"
        ),
    ],
    text: Annotated[
        str,
        typer.Argument(
            help="Text to display on the contribution graph (not guaranteed to fit)"
        ),
    ],
    start: datetime.datetime = sunday_of_this_date_last_year,
    end: datetime.datetime = next_saturday,
    separator: Annotated[
        str,
        typer.Option(
            help="An optional string to use to separate the text (if repeating)"
        ),
    ] = " ",
    inverse: Annotated[
        bool,
        typer.Option(
            help="Whether to use the inverse color scheme (empty text cells surrounded by filled)"
        ),
    ] = False,
    repeat: Annotated[
        bool,
        typer.Option(
            help="Whether to repeat the text across the entire width of the window (as much as possible)"
        ),
    ] = False,
):
    """
    Given a GitHub user, a string of text, we generate fake Git commits to display the desired text on the contribution graph within a given range.

    ---

    GitHub's contribution graph is a 53x7 grid (per year) where each cell represents a day (in UTC),
    with 5 shades of green indicating relatively (as a heatmap) how many contributions were made on each day.
    Based on one GitHub dev comment (https://github.com/orgs/community/discussions/23261#discussioncomment-3239758), the shade is determined by the distribution of commits in a given time-period, where each shade matches a given quartile:

    ---

    * Grey = 0 (we don't use this as we can't reliably remove user contributons from git history)\n
    * Lightest green = first quartile (25%)\n
    * Light green = median (50%)\n
    * Dark green = third quartile (75%)\n
    * Darkest green = last quartile\n

    ---

    By default (filtering to a specific time range will change this) the first cell is yesterday of last year, and the last cell is today of this year.
    """
    os.chdir("../test-repo-plz-ignore-1")
    generate_contrib_banner(user, text, start, end, separator, inverse, repeat)


def generate_contrib_banner(
    user: str,
    text: str,
    start: datetime.datetime,
    end: datetime.datetime,
    separator: str,
    inverse: bool,
    repeat: bool,
):
    height = 7
    start = sunday_of_date(start)
    end = next_saturday_of_date(end)
    weeks = math.ceil((end - start).days / 7)
    window = Window(width=weeks, height=height)
    cells = window.draw(
        text,
        nitram_micro_mono_CP437,
        repeat=repeat,
        separator=separator,
        inverse=inverse,
    )
    window.print(cells)
    git = GitHub()
    # importantly, contribs are in reverse order (most recent first)
    contribs = git.get_user_contributions(
        user,
        start,
        end,
    )
    deltas = git.calc_necessary_contrib_deltas(cells, contribs)
    git.make_necessary_commits(deltas)


if __name__ == "__main__":
    typer.run(main)
