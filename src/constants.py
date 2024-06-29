DUMMY_COMMIT_MESSAGE = "// github-paint dummy commit <want to build something together? 📬 iam@theo.lol 🏠 theo.lol 💼 in/iamtheolol>"
DATETIME_FORMAT_DAY = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
# ex contributon date: '2023-10-03T00:00:00.000+00:00'
CONTRIBUTION_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"
GRAPHQL_QUERY_TEMPLATE = """
{{
  user(login: "{user}") {{
    contributionsCollection(from: "{start}", to: "{end}") {{
      contributionCalendar {{
        totalContributions
        weeks {{
          contributionDays {{
            contributionCount
            date
          }}
          firstDay
        }}
      }}
    }}
  }}
}}
"""
