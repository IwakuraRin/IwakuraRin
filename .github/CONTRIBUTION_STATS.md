# Contribution statistics

The workflow refreshes the existing card at minute 17 of every hour, on relevant
pushes to `main`, and via **Actions → Update contribution statistics → Run workflow**.
Scheduled runs can be delayed by GitHub, and image caching can delay display.

The GitHub GraphQL query requests commit contributions for the preceding 365 days
and the user's all-time authored pull request count. The built-in `GITHUB_TOKEN`
can read public activity across repositories; it does not grant access to the
user's other private repositories. GitHub's contribution attribution rules apply.
No personal access token or additional secret is required.

The workflow owns API access and Git commits. The Python command consumes the
GraphQL JSON response on standard input and owns only the three marked SVG text
elements. It validates all counts and markers before writing. Failures preserve
the previous card, and unchanged counts produce no commit. Bot commits do not
recursively trigger workflows with the built-in token.

Run checks with `python3 -m unittest discover -s tests -v`. There are no external
Python dependencies or module boundary tools in this repository.

GitHub can disable scheduled workflows in public repositories after 60 days of
inactivity. If disabled, re-enable the workflow from its Actions page.
