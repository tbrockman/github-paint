DUMMY_COMMIT_MESSAGE = (
    "created by github-paint 🎨 https://github.com/tbrockman/github-paint"
)
JOB_AD = "want to build something? 📬 iam@theo.lol 🏠 https://theo.lol 💼 https://linkedin.com/in/iamtheolol"
DATETIME_FORMAT_DAY = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
# ex contributon date: '2023-10-03T00:00:00.000+00:00'
CONTRIBUTION_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"
GRAPHQL_USER_CONTRIBUTION_QUERY_TEMPLATE = """
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
