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
            "recipients": [addresscleaner.parse_address(recipient)],
            "sender": addresscleaner.parse_address(sender),
            "type": "letter"
        }
        page = end

    vals = jobs.values()
    vals.sort(key=lambda j: j['startingPage'])
    return files, vals, page

def collate_postcards(postcards, page=1):
    # Collate postcards into a list per type and sender.
    type_sender_postcards = defaultdict(list)
    for letter in postcards:
        key = (letter['type'], letter['sender'])
        type_sender_postcards[key].append(letter)

    files = []
    jobs = []
    for (postcard_type, sender), letters in type_sender_postcards.iteritems():
        files.append(os.path.join(
            os.path.dirname(__file__),
            "postcards",
            "{}.pdf".format(postcard_type)
        ))
        jobs.append({
            "startingPage": page + len(files) - 1,
            "endingPage": page + len(files) - 1,
            "recipients": [
                addresscleaner.parse_address(letter['recipient']) for letter in letters
            ],
            "sender": addresscleaner.parse_address(sender),
            "type": "postcard",
        })
    return files, jobs, page + len(files)

def run_batch(args, files, jobs):
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

def main():
    args = parser.parse_args()

    with open(os.path.join(args.directory, "manifest.json")) as fh:
        manifest = json.load(fh)

    if manifest["letters"]:
        lfiles, ljobs, lpage = collate_letters(args.directory, manifest["letters"], 1)
        print "Found", len(ljobs), "letter jobs"
        if ljobs:
            run_batch(args, lfiles, ljobs)

    if manifest["postcards"]:
        pfiles, pjobs, ppage = collate_postcards(manifest["postcards"], 1)
        print "Found", len(pjobs), "postcard jobs"
        if pjobs:
            run_batch(args, pfiles, pjobs)

if __name__ == "__main__":
    main()
