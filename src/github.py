import datetime
import json
import math
import os
import subprocess

from collections import defaultdict
from dataclasses import dataclass
from multiprocessing import Pool
from typing import List, Set, Tuple
from signal import signal, SIGINT

from .constants import (
    DATETIME_FORMAT,
    DATETIME_FORMAT_DAY,
    DUMMY_COMMIT_MESSAGE,
    GRAPHQL_QUERY_TEMPLATE,
)
from .util import Pixel


@dataclass(frozen=True)
class Contribution:
    date: datetime.datetime
    count: int


def initializer():
    signal(SIGINT, lambda: None)  # type: ignore


def commit(date: datetime.datetime):
    seconds = math.ceil(date.timestamp())
    return subprocess.run(
        [
            "git",
            "commit",
            "--allow-empty",
            "-m",
            DUMMY_COMMIT_MESSAGE,
        ],
        capture_output=True,
        env=dict(os.environ)
        | {"GIT_COMMITTER_DATE": str(seconds), "GIT_AUTHOR_DATE": str(seconds)},
    )


class GitHub:
    def get_user_contributions(
        self, user: str, token: str, start: datetime.datetime, end: datetime.datetime
    ) -> List[Contribution]:
        # divide start and end into time ranges of max 365 days (since the GitHub API only allows retrieving 1 year at a time)
        ranges: List[Tuple[datetime.datetime, datetime.datetime]] = []

        while start < end:
            next = min(start + datetime.timedelta(days=365), end)
            ranges.append((start, next))
            start = next

        contributions: Set[Contribution] = set()

        for start_dt, end_dt in ranges:
            start_str = start_dt.strftime(DATETIME_FORMAT)
            end_str = end_dt.strftime(DATETIME_FORMAT)
            query = GRAPHQL_QUERY_TEMPLATE.format(
                user=user, start=start_str, end=end_str
            )
            response = subprocess.run(
                ["gh", "api", "graphql", "-F", f"query={query}"],
                env=dict(os.environ) | {"GH_TOKEN": token},
                capture_output=True,
                text=True,
            )
            parsed = json.loads(response.stdout)
            weeks = parsed["data"]["user"]["contributionsCollection"][
                "contributionCalendar"
            ]["weeks"]

            for week in weeks:
                for day in week["contributionDays"]:
                    date = datetime.datetime.strptime(day["date"], DATETIME_FORMAT_DAY)
                    count = day["contributionCount"]
                    contributions.add(Contribution(date, count))
        return list(sorted(contributions, key=lambda c: c.date, reverse=True))

    def __count_dummy_file_contributions_by_day(self) -> defaultdict[str, int]:
        result = subprocess.run(
            ["git", "log", "--pretty=format:%ct", f"--grep={DUMMY_COMMIT_MESSAGE}"],
            capture_output=True,
            text=True,
        )
        counts: defaultdict[str, int] = defaultdict(int)

        for line in result.stdout.split("\n"):
            if not line:
                continue

            timestamp = int(line.strip())
            date = datetime.datetime.fromtimestamp(timestamp).strftime(
                DATETIME_FORMAT_DAY
            )
            counts[date] += 1
        return counts

    def calc_necessary_contrib_deltas(
        self, cells: List[Pixel], contribs: List[Contribution]
    ) -> List[Contribution]:
        dummy_contribs = self.__count_dummy_file_contributions_by_day()
        # find the maximum number of contributions on a single day
        max_contribs = max(
            [
                c.count - dummy_contribs[c.date.strftime(DATETIME_FORMAT_DAY)]
                for c in contribs
            ]
        )
        deltas: List[Contribution] = []

        for i, cell in enumerate(cells):
            contrib = contribs[i]
            desired_count = (
                0 if cell.color.value == 1 else cell.color.value
            ) * max_contribs
            str_date = contrib.date.strftime(DATETIME_FORMAT_DAY)
            delta = (
                desired_count  # add the number of contributions for our desired color quartile
                - contrib.count  # subtract the number of existing contributions on this day
                + dummy_contribs[
                    str_date
                ]  # add the number of existing dummy commits on this day
            )
            deltas.append(Contribution(contrib.date, delta))
        return deltas

    def make_necessary_commits(
        self, repo: str, deltas: List[Contribution], parallelism: int, dryrun: bool
    ):
        # remove any existing empty commits
        subprocess.run(
            [
                "git",
                "filter-repo",
                "--force",
                "--prune-empty=always",
            ]
        )
        # re-add origin
        subprocess.run(
            [
                "git",
                "remote",
                "add",
                "origin",
                repo,
            ]
        )
        # checkout a new orphan branch
        subprocess.run(["git", "branch", "-D", "orphan"])
        subprocess.run(["git", "checkout", "--orphan", "orphan"])

        # create dummy commits
        with Pool(parallelism, initializer) as pool:
            # commit in reverse order
            for i, delta in enumerate(deltas[::-1]):
                if delta.count <= 0:
                    print(
                        f"Skipping {delta.date} (desired contributions={delta.count}) [{i+1}/{len(deltas)}]"
                    )
                    continue
                print(
                    f"Committing {delta.count} times on {delta.date} [{i+1}/{len(deltas)}]"
                )
                pool.map(commit, [delta.date for _ in range(delta.count)])

        # rebase main onto orphan
        subprocess.run(["git", "checkout", "main"])
        subprocess.run(["git", "rebase", "orphan", "--reapply-cherry-picks"])

        if not dryrun:
            # TODO: allow configuring remote/branch
            subprocess.run(["git", "push", "origin", "main", "--force"])
        else:
            print("Dry run, not pushing to remote")
