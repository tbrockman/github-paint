import datetime
import json
import math
import os
import shutil
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


def try_create_worktree(name: str, timeout: int = 60 * 5):
    start = datetime.datetime.now()

    while (datetime.datetime.now() - start).total_seconds() < timeout:
        result = subprocess.run(["git", "worktree", "add", name])

        if result.returncode == 0:
            return


def commit_date(tup: tuple[datetime.datetime, int]):
    date, count = tup
    # create a worktree
    name = f"day-{date.strftime(DATETIME_FORMAT_DAY)}"
    try_create_worktree(name)
    for i in range(count):
        # commit i-times in series (to avoid lock issues)
        commit(date, i, name)


def commit(date: datetime.datetime, i: int, cwd: str):
    seconds = math.ceil(date.timestamp())
    return subprocess.run(
        [
            "git",
            "commit",
            "--allow-empty",
            "-m",
            f" {i=}" + DUMMY_COMMIT_MESSAGE,
        ],
        cwd=cwd,
        env=dict(os.environ)
        | {"GIT_COMMITTER_DATE": str(seconds), "GIT_AUTHOR_DATE": str(seconds)},
    )


class GitHub:
    def __init__(self, token: str):
        os.environ["GH_TOKEN"] = token
        subprocess.run(
            [
                "git",
                "config",
                "--global",
                "--add",
                "safe.directory",
                "/github/workspace",
            ],
            check=True,
        )

    def get_user_contributions(
        self, user: str, start: datetime.datetime, end: datetime.datetime
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

    def count_dummy_repo_contributions(self, repo: str) -> defaultdict[str, int]:
        # clone the repo
        subprocess.run(["gh", "repo", "clone", repo])
        os.chdir(repo)
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
        self, cells: List[Pixel], repo: str, contribs: List[Contribution]
    ) -> List[Contribution]:
        # check if the dummy repo exists in github
        exists = (
            subprocess.run(["gh", "repo", "view", repo], capture_output=True)
        ).returncode == 0
        dummy_contribs: defaultdict[str, int] = defaultdict(int)

        if exists:
            dummy_contribs = self.count_dummy_repo_contributions(repo)

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
                0 if cell.color.value == 0 else cell.color.value - 1
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
        if not dryrun:
            # remove existing repo (if it exists)
            subprocess.run(["gh", "repo", "delete", repo, "--yes"])

        # create a new repo as a subdirectory

        if os.path.exists(repo):
            shutil.rmtree(repo)
        os.mkdir(repo)
        os.chdir(repo)
        subprocess.run(["git", "init", "-b", "main"])
        commit(deltas[0].date, 0, ".")

        # create dummy commits
        with Pool(parallelism, initializer) as pool:
            filtered = [d for d in deltas if d.count > 0]

            # create commits for each date (as a worktree)
            pool.map(
                commit_date,
                [(delta.date, delta.count) for delta in filtered],
            )

            # merge the worktrees
            for delta in filtered:
                subprocess.run(
                    [
                        "git",
                        "merge",
                        "--no-ff",
                        "--no-edit",
                        f"day-{delta.date.strftime(DATETIME_FORMAT_DAY)}",
                    ]
                )

            # for i, delta in enumerate(deltas[::-1]):
            #     if delta.count <= 0:
            #         print(
            #             f"Skipping {delta.date} (desired contributions={delta.count}) [{i+1}/{len(deltas)}]"
            #         )
            #         continue
            #     print(
            #         f"Committing {delta.count} times on {delta.date} [{i+1}/{len(deltas)}]"
            #     )
            #     pool.map(commit, [(delta.date, i) for i in range(delta.count)])

        if not dryrun:
            subprocess.run(
                ["gh", "repo", "create", repo, "--public", "--push", "--source", "."]
            )
        else:
            print("Dry run, not pushing to GitHub")
