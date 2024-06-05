import datetime
import json
import subprocess

from dataclasses import dataclass
from typing import List

from .constants import DATETIME_FORMAT, DATETIME_FORMAT_DAY, GRAPHQL_QUERY_TEMPLATE
from .util import Pixel


@dataclass
class Contribution:
    date: datetime.datetime
    count: int

class GitHub:

    def get_user_contributions(self, user: str, start: datetime.datetime, end: datetime.datetime) -> List[Contribution]:

        # divide start and end into time ranges of max 365 days
        ranges = []

        while start < end:
            next = min(start + datetime.timedelta(days=365), end)
            ranges.append((start, next))
            start = next
        
        contributions = []

        for start_dt, end_dt in ranges:
            start = start_dt.strftime(DATETIME_FORMAT)
            end = end_dt.strftime(DATETIME_FORMAT)
            query = GRAPHQL_QUERY_TEMPLATE.format(user=user, start=start, end=end)
            response = subprocess.run(['gh', 'api', 'graphql', '-F', f'query={query}'], capture_output=True, text=True)
            parsed = json.loads(response.stdout)
            weeks = parsed['data']['user']['contributionsCollection']['contributionCalendar']['weeks']

            for week in weeks:
                for day in week['contributionDays']:
                    date = datetime.datetime.strptime(day['date'], DATETIME_FORMAT_DAY)
                    count = day['contributionCount']
                    contributions.append(Contribution(date, count))
        return contributions

    def make_commits(self, dummy_file: str, cells: List[Pixel], contribs: List[Contribution], end: datetime.datetime):

        max_contribs = max([c.count for c in contribs])
        commits = []



        pass

    