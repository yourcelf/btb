import os
import sys
import glob
import json
import subprocess
from collections import defaultdict

from utils import UnicodeReader, slugify, count_pages, combine_pdfs, parser
import addresscleaner
from click2mail import Click2MailBatch

parser.add_argument("directory", help="Path to downloaded mail batch")
parser.add_argument("--skip-letters", action='store_true', default=False)
parser.add_argument("--skip-postcards", action='store_true', default=False)

def fix_lines(address):
    """
    Click2Mail screws up addresses with 3 lines.  If we have only one address
    line, put it in "address1".  If we have more, put the first in
    "organization", and subsequent ones in "addressN".
    """
    lines = [a for a in [
        address.get('organization', None),
        address.get('address1', None),
        address.get('address2', None),
        address.get('address3', None)] if a]
    if len(lines) == 1:
        address['organization'] = ''
        address['address1'] = lines[0]
        address['address2'] = ''
        address['address3'] = ''
    if len(lines) >= 2:
        address['organization'] = lines[0]
        address['address1'] = lines[1]
        address['address2'] = ''
        address['address3'] = ''
    if len(lines) >= 3:
        address['address2'] = lines[2]
        address['address3'] = ''
    if len(lines) >= 4:
        address['address3'] = lines[3]
    return address

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
            "recipients": [fix_lines(addresscleaner.parse_address(recipient))],
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
                fix_lines(addresscleaner.parse_address(letter['recipient'])) for letter in letters
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
    if args.directory.endswith(".zip"):
        directory = os.path.abspath(args.directory[0:-len(".zip")])
        if not os.path.exists(directory):
            subprocess.check_call([
                "unzip", args.directory, "-d", os.path.dirname(args.directory)
            ])
    else:
        directory = args.directory

    with open(os.path.join(directory, "manifest.json")) as fh:
        manifest = json.load(fh)

    if manifest["letters"] and not args.skip_letters:
        lfiles, ljobs, lpage = collate_letters(directory, manifest["letters"], 1)
        print "Found", len(ljobs), "letter jobs"
        if ljobs:
            run_batch(args, lfiles, ljobs)

    if manifest["postcards"] and not args.skip_postcards:
        pfiles, pjobs, ppage = collate_postcards(manifest["postcards"], 1)
        print "Found", len(pjobs), "postcard jobs"
        if pjobs:
            run_batch(args, pfiles, pjobs)

if __name__ == "__main__":
    main()
