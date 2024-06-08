import datetime
import math
import os
import typer

from typing_extensions import Annotated

from .fonts.default import nitram_micro_mono_CP437
from .github import GitHub
from .window import Window
from .util import (
    next_saturday_of_date,
    sunday_of_date,
    next_saturday,
    sunday_of_this_date_last_year,
    Alignment,
)


def main(
    user: Annotated[
        str,
        typer.Argument(
            help="GitHub user to generate the contribution banner for (e.g. 'tbrockman')",
            envvar="INPUT_USER",
        ),
    ],
    text: Annotated[
        str,
        typer.Argument(
            help="Text to display on the contribution graph (not guaranteed to fit)",
            envvar="INPUT_TEXT",
        ),
    ],
    repo: Annotated[
        str,
        typer.Argument(
            help="The remote repository to push the commits to (e.g. 'https://github.com/tbrockman/github-paint')",
            envvar="INPUT_REPO",
        ),
    ],
    start: Annotated[
        datetime.datetime,
        typer.Option(
            help="The start of the date range to generate the contribution banner for (will be rounded to the start of the previous Sunday)",
            envvar="INPUT_START",
        ),
    ] = sunday_of_this_date_last_year,
    end: Annotated[
        datetime.datetime,
        typer.Option(
            help="The end of the date range to generate the contribution banner for (will be rounded to the start of next Saturday)",
            envvar="INPUT_END",
        ),
    ] = next_saturday,
    separator: Annotated[
        str,
        typer.Option(
            help="An optional string to use to separate the text (if repeating)",
            envvar="INPUT_SEPARATOR",
        ),
    ] = " ",
    inverse: Annotated[
        bool,
        typer.Option(
            help="Whether to use the inverse color scheme (empty text cells surrounded by filled)",
            envvar="INPUT_INVERSE",
        ),
    ] = False,
    repeat: Annotated[
        bool,
        typer.Option(
            help="Whether to repeat the text across the entire width of the window (as much as possible)",
            envvar="INPUT_REPEAT",
        ),
    ] = False,
    alignment: Annotated[
        str,
        typer.Option(
            help="The alignment of the text within the window (LEFT, CENTER, RIGHT)",
            envvar="INPUT_ALIGNMENT",
        ),
    ] = Alignment.RIGHT,
    parallelism: Annotated[
        int,
        typer.Option(
            help="The number of parallel processes to use for generating the contribution banner",
            envvar="INPUT_PARALLELISM",
        ),
    ] = os.cpu_count() - 1,
    dryrun: Annotated[
        bool,
        typer.Option(
            help="Whether or not to actually push the commits to the remote repository (useful for testing)",
            envvar="INPUT_DRYRUN",
        ),
    ] = False,
):
    """
    Given a GitHub user, a string of text, we generate fake Git commits to display the desired text on the contribution graph within a given range.

    ---

    GitHub's contribution graph is a 53x7 grid (per year) where each cell represents a day (in UTC),
    with 5 shades of green indicating relatively (as a heatmap) how many contributions were made on each day. By default (filtering to a specific time range will change this) the first cell is the previous Sunday of this week last year, and the last visible cell is today.
    Based on one GitHub dev comment (https://github.com/orgs/community/discussions/23261#discussioncomment-3239758), the shade is determined by the distribution of commits in a given time-period, where each shade matches a given quartile.
    """
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
        alignment=alignment,
    )
    window.print(cells)
    git = GitHub()
    # note: contribs are in reverse order (most recent first)
    contribs = git.get_user_contributions(
        user,
        start,
        end,
    )
    deltas = git.calc_necessary_contrib_deltas(cells, contribs)
    git.make_necessary_commits(repo, deltas, parallelism, dryrun)


if __name__ == "__main__":
    typer.run(main)
