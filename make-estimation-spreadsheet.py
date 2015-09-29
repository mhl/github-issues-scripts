#!/usr/bin/env python

from collections import namedtuple
import doctest
from optparse import OptionParser
import os
from os.path import dirname, join, realpath
import re
from xlwt import Workbook, Formula

from github import get_issues

# This script generates an Excel spreadsheet with one sheet per
# developer and a consensus sheet, designed to be uploaded to Google
# Spreadsheets for making estimates independently.

cwd = os.getcwd()
repo_directory = realpath(join(dirname(__file__)))

SheetInfo = namedtuple('SheetInfo', ['name', 'developer', 'sheet'])

Issue = namedtuple('Issue', ['url', 'number', 'title'])

# Algorithm from: http://stackoverflow.com/a/182924/223092
alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
def column_number_to_letters(column_number):
    dividend = column_number
    result = ''
    while dividend > 0:
        modulus = (dividend - 1) % len(alphabet)
        result = alphabet[modulus] + result
        dividend = (dividend - modulus) / len(alphabet)
    return result

def get_unestimated_open_issues(repo):

    results = []
    row_index = 1

    for number, title, body, issue in get_issues(repo):
        if ('pull_request' in issue) and issue['pull_request']['html_url']:
            continue
        difficulty_label_names = [i['name'] for i in issue['labels']
                                  if re.search(r'Difficulty ', i['name'])]
        if difficulty_label_names:
            continue
        row_index += 1
        results.append(Issue(issue['html_url'], number, title))

    return results

def main(repo, developers):

    basic_header = ['URL', 'Number', 'Title']

    workbook = Workbook()
    sheets = []

    for developer in developers:
        sheet_name = "{0} Estimates".format(developer)
        sheet = workbook.add_sheet(sheet_name)
        sheets.append(SheetInfo(sheet_name, developer, sheet))

    consensus_sheet_name = "Consensus"
    consensus_sheet_info = SheetInfo(
        consensus_sheet_name,
        None,
        workbook.add_sheet(consensus_sheet_name)
    )
    sheets.append(consensus_sheet_info)

    for sheet_info in sheets:
        sheet = sheet_info.sheet
        for column_index, column_header in enumerate(basic_header):
            sheet.write(0, column_index, column_header)
        if sheet_info.developer:
            sheet.write(0, len(basic_header), "{0} Estimate".format(sheet_info.developer))
            sheet.write(0, len(basic_header) + 1, "{0} Notes".format(sheet_info.developer))
        else:
            # If it's the consensus sheet, then add two columns for
            # each developer.
            column_index = len(basic_header)
            for developer in developers:
                sheet.write(0, column_index, "{0} Estimate".format(developer))
                sheet.write(0, column_index + 1, "{0} Notes".format(developer))
                column_index += 2
            sheet.write(0, column_index, "Consensus")

    for i, issue in enumerate(get_unestimated_open_issues(repo)):
        row_index = i + 1
        for sheet_info in sheets:
            for column_index in range(len(basic_header)):
                sheet_info.sheet.write(row_index, column_index, issue[column_index])
        # In the Consensus sheet add a reference to each of the
        # developer sheets' estimate and notes columns.
        for i, sheet_info in enumerate(s for s in sheets if s.developer):
            fmt = "'{sheet}'!{column}{row}"
            for original_column_index in (len(basic_header) + i for i in range(2)):
                formula_text = fmt.format(
                    sheet=sheet_info.name,
                    column=column_number_to_letters(original_column_index + 1),
                    row=row_index + 1)
                consensus_sheet_info.sheet.write(
                    row_index,
                    original_column_index + 2 * i,
                    Formula(formula_text))

    workbook.save('estimates.xls')

usage = """Usage: %prog [options] REPOSITORY DEVELOPER_A DEVELOPER_B ...

Repository should be username/repository from GitHub, e.g. mysociety/pombola"""
parser = OptionParser(usage=usage)
parser.add_option("-t", "--test",
                  action="store_true", dest="test", default=False,
                  help="Run doctests")

(options, args) = parser.parse_args()

if options.test:
    doctest.testmod()
else:
    if len(args) < 2:
        parser.print_help()
    else:
        repository = args[0]
        developers = args[1:]
        main(repository, developers)
