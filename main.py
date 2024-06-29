import datetime
import math
import typer

from typing import List
from typing_extensions import Annotated

from src.fonts.default import nitram_micro_mono_CP437
from src.github import GitHub, Contribution
from src.window import Window
from src.util import (
    next_saturday_of_date,
    sunday_of_date,
    next_saturday,
    sunday_of_this_date_last_year,
    HAlign,
    VAlign,
    Color,
    Pixel,
)

app = typer.Typer()


def print_contribs(
    contribs: List[Contribution], start: datetime.datetime, end: datetime.datetime
):
    height = 7
    start = sunday_of_date(start)
    end = next_saturday_of_date(end)
    weeks = math.ceil((end - start).days / 7)
    window = Window(
        width=weeks,
        height=height,
        empty_pixel=Pixel(Color(0)),
        padding=(0, 0, 0, 0),
    )
    min_contrib = min(contribs, key=lambda c: c.count).count
    max_contrib = max(contribs, key=lambda c: c.count).count
    quarter = (max_contrib) // 4

    print(
        f"quarters (n * {quarter}): ",
        max_contrib - quarter,
        max_contrib - 2 * quarter,
        max_contrib - 3 * quarter,
        min_contrib,
    )

    # experimentally, this seems to be how the graph is colored
    for i, contrib in enumerate(reversed(contribs)):
        if contrib.count >= max_contrib - quarter:
            window.buf[i] = Pixel(Color(4))
        elif contrib.count >= max_contrib - 2 * quarter:
            window.buf[i] = Pixel(Color(3))
        elif contrib.count >= max_contrib - 3 * quarter:
            window.buf[i] = Pixel(Color(2))
        elif contrib.count >= min_contrib:
            window.buf[i] = Pixel(Color(1))
        else:
            window.buf[i] = Pixel(Color(0))
    print(window)


@app.command()
def simulate(
    user: Annotated[
        str,
        typer.Argument(
            help="GitHub user to simulate contribution banner for (e.g. 'tbrockman'). Used to retrieve existing contributions",
            envvar="INPUT_USER",
        ),
    ],
    token: Annotated[
        str,
        typer.Option(
            help="GitHub personal access token (used for creating/deleting repos, pushing commits, and getting user contribution history)",
            envvar="INPUT_TOKEN",
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
):
    git = GitHub(token)
    contribs = git.get_user_contributions(user, start, end)
    print_contribs(contribs, start, end)


@app.command()
def draw(
    text: Annotated[
        str,
        typer.Argument(
            help="Text to display on the contribution graph (not guaranteed to fit)",
            envvar="INPUT_TEXT",
        ),
    ],
    token: Annotated[
        str,
        typer.Option(
            help="GitHub personal access token (used for creating/deleting repos, pushing commits, and getting user contribution history)",
            envvar="INPUT_TOKEN",
        ),
    ],
    user: Annotated[
        str,
        typer.Option(
            help="GitHub user to generate the contribution banner for (e.g. 'tbrockman'). Used to retrieve existing contributions. Defaults to the GH user of the token.",
            envvar="INPUT_USER",
        ),
    ] = "",
    git_name: Annotated[
        str,
        typer.Option(
            help="Name for git user (defaults to name in GitHub profile of token user)",
            envvar="INPUT_GIT_NAME",
        ),
    ] = "",
    git_email: Annotated[
        str,
        typer.Option(
            help="Email for git user (defaults to email in GitHub profile of token user)",
            envvar="INPUT_GIT_EMAIL",
        ),
    ] = "",
    repo: Annotated[
        str,
        typer.Option(
            help="The name of the repo to create fake commits in (must be owned by the user). Also used as the name of the subdirectory to initialize the repo in",
            envvar="INPUT_REPO",
        ),
    ] = "github-painted",
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
    padding: Annotated[
        tuple[int, int, int, int],
        typer.Option(
            help="Padding to add to the window (top, right, bottom, left)",
            envvar="INPUT_PADDING",
        ),
    ] = (0, 0, 0, 0),
    h_align: Annotated[
        HAlign,
        typer.Option(
            help="The alignment of the text within the window",
            envvar="INPUT_HALIGN",
        ),
    ] = HAlign.CENTER,
    v_align: Annotated[
        VAlign,
        typer.Option(
            help="The alignment of the text within the window",
            envvar="INPUT_VALIGN",
        ),
    ] = VAlign.CENTER,
    # parallelism: Annotated[
    #     int,
    #     typer.Option(
    #         help="The number of parallel processes to use for generating the contribution banner",
    #         envvar="INPUT_PARALLELISM",
    #     ),
    # ] = (os.cpu_count() or 2) - 1,
    dry_run: Annotated[
        bool,
        typer.Option(
            help="Whether or not to actually push the commits to the remote repository (useful for testing)",
            envvar="INPUT_DRY_RUN",
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
    empty_pixel = Pixel(Color(1) if not inverse else Color(4))
    height = 7
    start = sunday_of_date(start)
    end = next_saturday_of_date(end)
    weeks = math.ceil((end - start).days / 7)
    window = Window(
        width=weeks,
        height=height,
        empty_pixel=empty_pixel,
        padding=padding,
    )
    git = GitHub(token)

    if not user or not git_name or not git_email:
        github_user = git.get_user()
        user = user or github_user["login"]
        git_name = git_name or github_user["name"]
        git_email = git_email or github_user["email"]

    # note: contribs are in reverse order (most recent first)
    contribs = git.get_user_contributions(
        user,
        start,
        end,
    )
    window.draw_text(
        text,
        nitram_micro_mono_CP437,
        repeat=repeat,
        separator=separator,
        inverse=inverse,
        h_align=h_align,
        v_align=v_align,
    )
    print(window)
    deltas = git.calc_necessary_contrib_deltas(window.buf[::-1], repo, contribs)
    print("Commit delta mask (darker=more commits, lighter=less):")
    print_contribs(deltas, start, end)

    if not dry_run:
        git.make_necessary_commits(repo, deltas, git_name, git_email)
    else:
        print("Dry run, not committing or pushing to GitHub.")


if __name__ == "__main__":
    app()
