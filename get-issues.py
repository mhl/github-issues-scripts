#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2014, 2015 Mark Longair
# This script is distributed under the terms of the GNU General Public License.
# See the COPYING file in this repository for the complete text of the license.

from distutils import spawn
import doctest
import errno
import hashlib
from optparse import OptionParser
import os
from os.path import dirname, exists, isdir, join, realpath, relpath, splitext
import re
import requests
import subprocess
import sys
import tempfile

from github import standard_headers, get_issues

if not spawn.find_executable('pandoc'):
    print >> sys.stderr, "pandoc couldn't be found on PATH"
    sys.exit(1)

# This is a script that downloads all the GitHub issues in a
# particular repository and generates a PDF for each one; the idea is
# to produce easily printable versions of all the issues for a
# repository.

# To get pandoc to produce PDFs, I also needed to install:
#
#  texlive-fonts-recommended
#  texlive-latex-base
#  texlive-latex-extra
#  texlive-latex-recommended
#  texlive-xetex

cwd = os.getcwd()
repo_directory = realpath(join(dirname(__file__)))
images_directory = relpath(join(repo_directory, 'images'), cwd)
pdfs_directory = relpath(join(repo_directory, 'pdfs'), cwd)

def mkdir_p(d):
    try:
        os.makedirs(d)
    except OSError, e:
        if e.errno == errno.EEXIST and isdir(d):
            pass
        else:
            raise

mkdir_p(images_directory)
mkdir_p(pdfs_directory)

def replace_image(match, download=True):
    """Rewrite an re match object that matched an image tag

    Download the image and return a version of the tag rewritten
    to refer to the local version.  The local version is named
    after the MD5sum of the URL.
    
    >>> m = re.search(r'\!\[(.*?)\]\((.*?)\)',
    ...               'an image coming up ![caption](http://blah/a/foo.png)')
    >>> replace_image(m, download=False)
    '![caption](github-print-issues/images/b62082dd8a02ea495f5e3c293eb6ee67.png)'
    """

    caption = match.group(1)
    url = match.group(2)
    hashed_url = hashlib.md5(url).hexdigest()
    extension = splitext(url)[1]
    if not extension:
        raise Exception, "No extension at the end of {0}".format(url)
    image_filename = join(images_directory, hashed_url) + extension
    if download:
        if not exists(image_filename):
            r = requests.get(url)
            with open(image_filename, 'w') as f:
                f.write(r.content)
    return "![{0}]({1})".format(caption, image_filename)

def replace_images(md):
    """Rewrite a Markdown string to replace any images with local versions

    'md' should be a GitHub Markdown string; the return value is a version
    of this where any references to images have been downloaded and replaced
    by a reference to a local copy.
    """

    return re.sub(r'\!\[(.*?)\]\((.*?)\)', replace_image, md)

def main(repo):

    for number, title, body, issue in get_issues(repo):

        pdf_filename = join(pdfs_directory,
                                    '{}.pdf'.format(number))
        if exists(pdf_filename):
            continue
        
        ntf = tempfile.NamedTemporaryFile(suffix='.md', delete=False)
        md_filename = ntf.name

        if 'pull_request' in issue and issue['pull_request']['html_url']:
            continue

        print "Doing issue", number, title

        with open(md_filename, 'w') as f:
            f.write(u"# {0} {1}\n\n".format(number, title).encode('utf-8'))
            f.write("### Reported by {0}\n\n".format(issue['user']['login']))
            # Increase the indent level of any Markdown heading
            body = re.sub(r'^(#+)', r'#\1', body or '')
            body = replace_images(body)
            body = body.encode('utf-8')
            f.write(body)
            f.write("\n\n")
            if issue['comments'] > 0:
                comments_request = requests.get(issue['comments_url'],
                                                headers=standard_headers)
                for comment in comments_request.json():
                    f.write("### Comment from {0}\n\n".format(comment['user']['login']))
                    comment_body = comment['body']
                    comment_body = re.sub(r'^(#+)', r'###\1', comment_body)
                    comment_body = replace_images(comment_body)
                    f.write(comment_body.encode('utf-8'))
                    f.write("\n\n")

        subprocess.check_call(['pandoc',
                               '--latex-engine=xelatex',
                               '-f',
                               'markdown_github',
                               md_filename,
                               '-o',
                               pdf_filename])

        os.remove(ntf.name)


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
