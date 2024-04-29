import re
import csv
import codecs
import argparse
import tempfile
import subprocess
from PyPDF2 import PdfFileReader, PdfFileWriter

try:
    import conf
except ImportError:
    conf = None

parser = argparse.ArgumentParser(description="Create batch mailing with Click2Mail for the given downloaded mail batch")
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
    res = subprocess.check_output(["pdfinfo", pdf]).decode("utf-8")
    match = re.search("Pages:\s+(\d+)", res)
    return int(match.group(1))

def combine_pdfs(filenames):
    handles = [open(fn, 'rb') for fn in filenames]
    readers = [PdfFileReader(handle) for handle in handles]
    with tempfile.NamedTemporaryFile(suffix="combined.pdf", delete=False) as fh:
        writer = PdfFileWriter()
        for reader in readers:
            for page_num in range(reader.getNumPages()):
                writer.addPage(reader.getPage(page_num))
        writer.write(fh)
        name = fh.name
    for handle in handles:
        handle.close()

    #res = subprocess.check_call(["pdftk"] + filenames + ["cat", "output", name])
    return name 
