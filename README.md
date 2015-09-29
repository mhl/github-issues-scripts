# Useful scripts for managing GitHub issues

If GitHub issues play an important role in the way you manage
projects, then some of these scripts might be of use to you.

All of them rely on having a `~/.github-oauth-token.json` file
with your GitHub OAuth token, like:

```
{"token": "your github oauth access token here"}
```

You can generate such a token from
https://github.com/settings/tokens/new

## Remote collaborative estimation in a Google Spreadsheet

### make-estimation-spreadsheet.py

At work we do estimation of the difficulty of issues in a Google
Spreadsheet, where each developer has their own sheet within the
spreadsheet.  They put in a score (and optionally some notes)
beside each of the open unestimated issues without looking at
anyone else's sheet.  Then we get together on a video call and
all switch to the 'Consensus' sheet in the spreadsheet and
discuss any issues where we've made different estimates.

The procedure for doing this is to run a command like:

```
./make-estimation-spreadsheet.py mysociety/pombola mark duncan liz
```

The first parameter is the name of the GitHub repository and the
remaining parameters are names of the developers who'll be
taking part in the estimation exercise.

That command will generate a file called `estimates.xls`.

Unfortunately, just uploading this to Google Docs via
the obvious way doesn't seem to work; instead, you need to
create an empty Google Spreadsheet first, and then go to
"File > Import ...", select the 'Upload' tab, select the
`estimates.xls` file, and then select "Replace spreadsheet".

Then share that spreadsheet with your fellow developers, ideally
giving them the URL for their personal sheet within the
spreadsheet.

(Incidentally, the scoring system we use for estimation of
difficulty of issues is Mazz Mosley's,
[as described by Anna Shipman](http://www.annashipman.co.uk/jfdi/how-to-estimate.html)
which is based on how much you already know about how to do it
rather than estimating hours, say.)

### set-estimates.py

Once you've arrived at a consensus, you'll want to add those
estimates to the GitHub issues as labels of the form
`Difficulty 3`, `Difficulty 5`, etc. There's another script in
this repository to help with this, called `set-estimates.py`.

First, download just the 'Consensus' sheet of your estimation
spreadsheet in Google Docs as a CSV file. You can do that by
switching to that sheet and going to
"File > Download > Comma-separated values".

Then you can give the downloaded file as the second parameter to
the script - the first should be the name of the repository on
GitHub, e.g.

```
./set-estimates.py mysociety/pombola "Pombola estimation - Consensus.csv"
```

## Create a PDF file of every open issue in a respository

### make-sprint-milestone-spreadsheets.py

If you run this script against a repository, e.g. with:

```
./make-sprint-milestone-spreadsheets.py mysociety/yournextrepresentative
```

... it's make a `pdfs` subdirectory and generate one PDF in
there for each open issue in the repository. We found this
useful for
[printing out every open issue in a repository to triage them](http://longair.net/blog/2014/02/16/printing-out-github-issues-for-triage-or-estimation/).

Note that pandoc needs a lot of texlive to be installed for it
to generate PDFs - I needed to install the following:

```
sudo apt-get install \
    texlive-fonts-recommended \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-latex-recommended \
    texlive-xetex
```

Of course, some of these PDFs may be more than one page. To
print out just the first page of each, 4 to an A4 side, I did
this:

```
cd pdfs
for i in *.pdf; do pdftk $i cat 1-1 output ${i%.pdf}-first-page.pdf; done
pdftk *-first-page.pdf cat output all-first-pages.pdf
pdfnup --nup 2x2 --outfile all-first-pages-4up.pdf --no-landscape all-first-pages.pdf
```

(`pdftk` is in the Debian package of the same name, and `pdfnup`
is from `texlive-extra-utils`.)

If you use Mac OS, then apparently this may be helpful as help
on how to combine and print out the PDFs:
https://support.apple.com/en-gb/ht4075 (Thanks to Tom Steinberg
for that suggestion.)

## Spreadsheets for calculating sprint velocity / performance

When we first started estimating, I was interested in how the
points we estimated related to the amount of time in a sprint,
so it was helpful to generate CSV files with details of the
issues that were in each sprint (in the sense of being
associated with the milestone representing the sprint in GitHub
issues) and any other issues that were closed over the course of
the sprint.

This assumes that the following things are true:

* You use labels for difficulty points as above (i.e. of the
  form `Difficulty N`_)
* You have milestones that represent each sprint, with a title
  that begins with 'Sprint'
* Each milestone has a due date set in GitHub issues for the end
  of the sprint.

Then, supposing you have two weeks sprints, you can run:

```
./make-sprint-milestone-spreadsheets.py mysociety/pombola 14
```

That should generate one CSV file for each sprint milestone in
GitHub issues.

---

Mark Longair <mhl@pobox.com>
