import json
import os
from os.path import join

import requests

with open(join(os.environ['HOME'], '.github-oauth-token-new.json')) as f:
    token = json.load(f)['token']

standard_headers = {'User-Agent': 'github-issues-printer/1.0',
                    'Authorization': 'bearer {0}'.format(token)}
