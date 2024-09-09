# timespent (licensed under Apache 2.0)
## Not a standalone lib; requires a Github client to function
Python package for calculating time spent in Github
Output is saved as a CSV file named output.csv
Feel free to fork & modify output.

To run as CLI:
```bash
python3 -m timespent get_timespent \
 --access_token 'YOUR-TOKEN' \
 --github_url 'https://enterprise.etc.github.com' \
 --github_api_url 'https://enterprise.etc.github.com/api/v3' \
 --repo OrgName/repo \
 --contributors '[]'\
 --include_comments 'True' \
 --start_date_time '2024-02-06T00:00:00Z' \
 --end_date_time '2024-02-06T23:59:59Z'
```
