import datetime
import json
import math
import os
import subprocess

from collections import defaultdict
from dataclasses import dataclass
from multiprocessing import Pool
from typing import List

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


def commit(date: datetime.datetime):
    seconds = math.ceil(date.timestamp())
    return subprocess.run(
        [
            "git",
            "commit",
            "--allow-empty",
            "--date",
            str(seconds),
            "-m",
            DUMMY_COMMIT_MESSAGE,
        ],
        capture_output=True,
    )


class GitHub:
    def get_user_contributions(
        self, user: str, start: datetime.datetime, end: datetime.datetime
    ) -> List[Contribution]:
        # divide start and end into time ranges of max 365 days (since the GitHub API only allows retrieving 1 year at a time)
        ranges = []

        while start < end:
            next = min(start + datetime.timedelta(days=365), end)
            ranges.append((start, next))
            start = next

        contributions = set()

        for start_dt, end_dt in ranges:
            start = start_dt.strftime(DATETIME_FORMAT)
            end = end_dt.strftime(DATETIME_FORMAT)
            query = GRAPHQL_QUERY_TEMPLATE.format(user=user, start=start, end=end)
            response = subprocess.run(
                ["gh", "api", "graphql", "-F", f"query={query}"],
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
        return list(sorted(contributions, key=lambda c: c.date))

    def __count_dummy_file_contributions_by_day(self) -> defaultdict[str, int]:
        result = subprocess.run(
            ["git", "log", "--pretty=format:%ct", f"--grep={DUMMY_COMMIT_MESSAGE}"],
            capture_output=True,
            text=True,
        )
        counts = defaultdict(int)

        print(f"stderr: {result.stderr} stdout: {result.stdout}")

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
        max_contribs = max([c.count for c in contribs])
        dummy_contribs = self.__count_dummy_file_contributions_by_day()
        deltas = []

        for i, cell in enumerate(cells):
            contrib = contribs[i]
            new_count = cell.color.value * max_contribs
            delta = (
                new_count  # add the number of contributions for our desired color quartile
                - contrib.count  # subtract the number of existing contributions on this day
                + dummy_contribs.get(
                    contrib.date.strftime(DATETIME_FORMAT_DAY), 0
                )  # add the number of existing dummy commits on this day
            )
            deltas.append(Contribution(contrib.date, delta))
        return deltas

    def make_necessary_commits(self, deltas: List[Contribution]):
        # remove our dummy file from the repo
        print("Removing dummy file from repo")
        result = subprocess.run(
            [
                "git",
                "filter-repo",
                "--force",
                "--prune-empty=always",
            ]
        )
        print(result, result.stderr, result.stdout)

        # re-add origin
        result = subprocess.run(
            [
                "git",
                "remote",
                "add",
                "origin",
                "https://github.com/tbrockman/github-paint",
            ]
        )

        with Pool(os.cpu_count() - 2) as pool:
            for delta in deltas:
                if delta.count <= 0:
                    continue
                pool.map(commit, [delta.date for _ in range(delta.count)])

        # TODO: allow configuring remote/branch
        # subprocess.run(["git", "push", "origin", "main"])
