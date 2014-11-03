import os
import re
import sys
import glob
import argparse
import tempfile
import subprocess

from utils import UnicodeReader, slugify
import addresscleaner
from click2mail import Click2MailBatch

try:
    import conf
except ImportError:
    conf = None

parser = argparse.ArgumentParser(description="Create batch mailing with Click2Mail for the given downloaded mail batch")
parser.add_argument("directory", help="Path to downloaded mail batch")
parser.add_argument("-u", "--username", help="Click2Mail password",
        default=getattr(conf, "USERNAME", None))
parser.add_argument("-p", "--password", help="Click2Mail password",
        default=getattr(conf, "PASSWORD", None))
parser.add_argument("--staging", help="Run on staging server", action="store_true",
        default=getattr(conf, "STAGING", None))
parser.add_argument("--dry-run", help="Dry run. Don't actually hit Click2Mail",
        action="store_true",
        default=getattr(conf, "DRY_RUN", None))

def count_pages(pdf):
    res = subprocess.check_output(["pdfinfo", pdf])
    match = re.search("Pages:\s+(\d+)", res)
    return int(match.group(1))

def combine_pdfs(filenames):
    with tempfile.NamedTemporaryFile(suffix="combined.pdf", delete=False) as fh:
        name = fh.name

    res = subprocess.check_call(
            ["pdftk"] + filenames + ["cat", "output", name])
    return name 

def build(mailing_dir):
    jobs = {}
    page = 1
    all_letters = []
    with open(os.path.join(mailing_dir, "manifest.csv")) as fh:
        reader = UnicodeReader(fh)
        for name,sheets in reader:
            files = glob.glob(os.path.join(mailing_dir, "letters", slugify(name) + "*"))
            count = 0
            for filename in files:
                count += count_pages(filename)
            end = page + count
            jobs[name] = {
                "startingPage": page,
                "endingPage": end - 1
            }
            all_letters += files
            page = end

    filename = combine_pdfs(all_letters)

    with open(os.path.join(mailing_dir, "addresses.csv")) as fh:
        reader = UnicodeReader(fh)
        for row in reader:
            parts = [a for a in row if a]
            name = parts[0]
            address = addresscleaner.parse_address(u"\n".join(parts))
            jobs[name]["recipient"] = address
    vals = jobs.values()
    vals.sort(key=lambda j: j['startingPage'])
    return filename, vals 

def main():
    args = parser.parse_args()
    filename, jobs = build(args.directory)
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
