import json
import os
from os.path import join

import requests

with open(join(os.environ['HOME'], '.github-oauth-token-new.json')) as f:
    token = json.load(f)['token']

standard_headers = {'User-Agent': 'github-issues-printer/1.0',
                    'Authorization': 'bearer {0}'.format(token)}

def get_issues(repo, state='open'):
    page = 1
    while True:
        issues_url = 'https://api.github.com/repos/{0}/issues'.format(repo)
        r = requests.get(issues_url,
                         params={'per_page': '100',
                                 'page': str(page),
                                 'state': state},
                         headers=standard_headers)
        if r.status_code != 200:
            raise Exception, "HTTP status {0} on fetching {1}".format(
                r.status_code,
                issues_url)

        issues_json = r.json()
        for issue in issues_json:
            number = issue['number']
            title = issue['title']
            body = issue['body']
            yield number, title, body, issue

        page += 1
        if 'Link' not in r.headers:
            break
