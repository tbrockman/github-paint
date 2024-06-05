import datetime
import math
import os
import sys

from .constants import DATETIME_FORMAT_DAY
from .fonts import Font
from .fonts.default import nitram_micro_mono_CP437
from .github import GitHub
from .window import Window

def generate_contrib_banner(user: str, text: str, font: Font, start: datetime.datetime, end: datetime.datetime):
    """
    GitHub's contribution graph is a 53x7 grid (per year) where each cell represents a day (in UTC),
    with 5 shades of green indicating relatively (as a heatmap) how many contributions were made on each day.
    Based on one comment, the shade is determined by the distribution of commits in a given time-period, where each shade matches a given quartile.

    Grey = 0
    Lightest green = first quartile (25%)
    Light green = median (50%)
    Dark green = third quartile (75%)
    Darkest green = maximum

    By default (filtering to a specific time range will change this) the first cell is yesterday of last year, and the last cell is today of this year.

    Given a string of text, a font, a start time, and an end time, we generate fake Git commits to display the desired text on the contribution graph within the given range.
    """
    height = 7
    weeks = math.ceil((end - start).days / 7)
    window = Window(width=weeks, height=height, padding=(1, 1, 1, 1))
    cells = window.render_text(text, font, separator=chr(1), inverse=True)
    window.print(cells)

    git = GitHub()
    # contribs = git.get_user_contributions(user, start, end)
    # commits = git.make_commits(os.path.join(os.getcwd(), 'banner.md'), cells, contribs)
    # git.push_commits(commits)

if __name__ == '__main__':

    if len(sys.argv) < 4:
        print(f'Usage: main.py <user> <text> <start> [end (default: now)] (where start/end are {DATETIME_FORMAT_DAY})\nex: python main.py "Hello, World!" "2021-01-01" "2024-12-31"')
        sys.exit(1)

    start = datetime.datetime.strptime(sys.argv[3], DATETIME_FORMAT_DAY)
    end = datetime.now() if len(sys.argv) < 5 else datetime.datetime.strptime(sys.argv[4], DATETIME_FORMAT_DAY)
    generate_contrib_banner(sys.argv[1], sys.argv[2], nitram_micro_mono_CP437, start, end)