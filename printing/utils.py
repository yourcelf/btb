import re
import csv
import codecs
import argparse
import unicodedata
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
    res = subprocess.check_output(["pdfinfo", pdf])
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

def slugify(value):
    # Taken from django.utils.text
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    return re.sub('[-\s]+', '-', value)

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

