import os
import sys
import glob
import json
from collections import defaultdict

from utils import UnicodeReader, slugify, count_pages, combine_pdfs, parser
import addresscleaner
from click2mail import Click2MailBatch

parser.add_argument("directory", help="Path to downloaded mail batch")

def collate_letters(mailing_dir, letters, page=1):
    # Sort by recipient.
    recipient_letters = defaultdict(list)
    for letter in letters:
        recipient_letters[(letter['recipient'], letter['sender'])].append(letter)

    # Assemble list of files and jobs.
    files = []
    jobs = {}
    for (recipient, sender), letters in recipient_letters.iteritems():
        count = 0
        for letter in letters:
            filename = os.path.join(mailing_dir, letter["file"])
            files.append(filename)
            count += count_pages(filename)
        end = page + count
        jobs[recipient] = {
            "startingPage": page,
            "endingPage": end - 1,
            "recipient": addresscleaner.parse_address(recipient),
            "sender": addresscleaner.parse_address(sender),
            "type": "letter"
        }
        page = end

    vals = jobs.values()
    vals.sort(key=lambda j: j['startingPage'])
    return files, vals, page

def collate_postcards(postcards, page=1):
    type_postcards = defaultdict(list)
    for letter in postcards:
        type_postcards[letter['type']].append(letter)

    files = []
    jobs = []
    for postcard_type, letters in type_postcards.iteritems():
        files.append(os.path.join(
            os.path.dirname(__file__),
            "postcards",
            "{}.pdf".format(postcard_type)
        ))
        for letter in letters:
            jobs.append({
                "startingPage": page + len(files) - 1,
                "endingPage": page + len(files) - 1,
                "recipient": addresscleaner.parse_address(letter['recipient']),
                "sender": addresscleaner.parse_address(letter['sender']),
                "type": "postcard",
            })
    return files, jobs, page + len(files)

def main():
    args = parser.parse_args()

    with open(os.path.join(args.directory, "manifest.json")) as fh:
        manifest = json.load(fh)

    files = [] # list of pdfs we will combine
    jobs = []  # list of jobs from within those pdfs
    page = 1 # starting page number

    if manifest["letters"]:
        lfiles, ljobs, lpage = collate_letters(args.directory, manifest["letters"], page)
        files += lfiles
        jobs += ljobs
        page = lpage

    if manifest["postcards"]:
        pfiles, pjobs, ppage = collate_postcards(manifest["postcards"], page)
        files += pfiles
        jobs += pjobs
        page = ppage

    filename = combine_pdfs(files)
    print "Building job with", filename
    batch = Click2MailBatch(
            username=args.username,
            password=args.password,
            filename=filename,
            jobs=jobs,
            staging=args.staging)
    if batch.run(args.dry_run):
        os.remove(filename)

if __name__ == "__main__":
    main()
