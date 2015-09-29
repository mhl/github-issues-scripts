#!/usr/bin/env python

from collections import defaultdict
import csv
import datetime
import dateutil.parser
import doctest
from optparse import OptionParser
import os
from os.path import dirname, join, realpath
import re
import requests

from github import standard_headers, get_issues

# If you use milestones to group the issues that you hope to close
# over the course of the sprint, and 'Difficulty N' labels to indicate
# their relative complexity, this script will generate CSV files with
# the issues for each sprint.

cwd = os.getcwd()
repo_directory = realpath(join(dirname(__file__)))

def get_difficulty(issue):
    difficulty_label_names = [i['name'] for i in issue['labels']
                              if re.search(r'^Difficulty ', i['name'])]
    if len(difficulty_label_names) == 0:
        return None
    elif len(difficulty_label_names) == 1:
        label = difficulty_label_names[0]
        m = re.search(r'^Difficulty (\d+)', label)
        if not m:
            message = "Malformed Difficulty label: '{0}'".format(label)
            raise Exception, message
        return int(m.group(1), 10)
    else:
        raise Exception, "Found multiple Difficulty labels: '{0}'".format(
            difficulty_label_names)

def issues_sort_key(issue):
    state_number = 0 if issue['state'] == 'closed' else 1
    closed_at = issue['closed_at']
    return (state_number, closed_at)

def main(repo):

    milestone_due_dates = {}
    milestone_start_dates = {}

    for milestone_status in ('open', 'closed'):
        milestones_url = 'https://api.github.com/repos/{0}/milestones'.format(repo)
        r = requests.get(milestones_url,
                         params={'state': 'open'},
                         headers=standard_headers)
        if r.status_code != 200:
            raise Exception, "HTTP status {0} on fetching {1}".format(
                r.status_code,
                milestones_url)
        for milestone in r.json():
            title = milestone['title']
            if title.startswith('Sprint'):
                due_date = dateutil.parser.parse(milestone['due_on']) + \
                    datetime.timedelta(hours=4)
                start_date = due_date - datetime.timedelta(days=7)
                milestone_start_dates[title] = start_date
                milestone_due_dates[title] = due_date

    milestones = sorted(milestone_due_dates.keys())

    issues_in_milestone = defaultdict(list)
    issues_not_in_milestone = defaultdict(list)

    for number, title, body, issue in get_issues(repo, state='all'):

        if ('pull_request' in issue) and issue['pull_request']['html_url']:
            continue

        issue['difficulty'] = get_difficulty(issue)

        print "considering issue:", number

        date_closed = issue['closed_at']
        if date_closed is not None:
            date_closed = dateutil.parser.parse(date_closed)

        issue['closed_at'] = date_closed

        milestone = issue['milestone']
        if milestone is not None:
            milestone = milestone['title']

        if milestone in milestone_due_dates:
            issues_in_milestone[milestone].append(issue)
        elif date_closed:
            for possible_milestone in milestones:
                if date_closed > milestone_start_dates[possible_milestone] and \
                        date_closed <= milestone_due_dates[possible_milestone]:
                    issues_not_in_milestone[possible_milestone].append(issue)

    for milestone in milestones:

        filename = milestone + ".csv"

        print "writing:", filename

        with open(filename, "w") as fp:
            writer = csv.writer(fp)
            writer.writerow(['OfficiallyInMilestone', 'State', 'URL', 'Number', 'Difficulty', 'Title'])
            in_milestone = sorted(issues_in_milestone[milestone],
                                  key=issues_sort_key)
            not_in_milestone = sorted(issues_not_in_milestone[milestone],
                                      key=issues_sort_key)
            for issue in in_milestone:
                writer.writerow([True,
                                 issue['state'],
                                 issue['html_url'],
                                 issue['number'],
                                 issue['difficulty'],
                                 issue['title']])
            for issue in not_in_milestone:
                writer.writerow([False,
                                 issue['state'],
                                 issue['html_url'],
                                 issue['number'],
                                 issue['difficulty'],
                                 issue['title']])

usage = """Usage: %prog [options] REPOSITORY

Repository should be username/repository from GitHub, e.g. mysociety/pombola"""
parser = OptionParser(usage=usage)
parser.add_option("-t", "--test",
                  action="store_true", dest="test", default=False,
                  help="Run doctests")

(options, args) = parser.parse_args()

if options.test:
    doctest.testmod()
else:
    if len(args) != 1:
        parser.print_help()
    else:
        main(args[0])
