#!/usr/bin/env python

import csv
import doctest
import json
from optparse import OptionParser
import os
from os.path import dirname, join, realpath
import requests

from github import standard_headers

cwd = os.getcwd()
repo_directory = realpath(join(dirname(__file__)))

def main(repo, csv_file):

    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            issue_number = row['Number']
            try:
                difficulty = int(row['Consensus'], 10)
            except ValueError:
                continue

            print "{0} => {1}".format(issue_number, difficulty)

            url_template = 'https://api.github.com/repos/{0}/issues/{1}/labels'
            url = url_template.format(repo, issue_number)
            labels = ["Difficulty " + str(difficulty)]
            print "url:", url
            print "labels:", labels
            r = requests.post(url,
                              headers=standard_headers,
                              data=json.dumps(labels))
            print r.content

usage = """Usage: %prog [options] REPOSITORY CSV-FILE

REPOSITORY should be username/repository from GitHub, e.g. mysociety/pombola

CSV-FILE should be have a "Consensus" column (with the estimated
complexity as an integer) and a "Number" column with the issue number.
"""
parser = OptionParser(usage=usage)
parser.add_option("-t", "--test",
                  action="store_true", dest="test", default=False,
                  help="Run doctests")

(options, args) = parser.parse_args()

if options.test:
    doctest.testmod()
else:
    if len(args) != 2:
        parser.print_help()
    else:
        main(args[0], args[1])
