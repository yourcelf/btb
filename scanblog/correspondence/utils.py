import os
import re
import csv
import shutil
import codecs
import tempfile
import cStringIO
import subprocess


from PIL import Image, ImageDraw, ImageFont
from pyPdf import PdfFileReader

from django.contrib.sites.models import Site
from django.conf import settings
from django.utils.safestring import mark_safe
from django.http import HttpResponse, Http404
from django.template import Context, loader

from correspondence.tex_conversions import latex_equivalents

WKHTMLTOPDF_CMD = getattr(settings, "WKHTMLTOPDF_CMD", "/usr/bin/wkhtmltopdf")

def mail_filter_or_404(user, model, **kwargs):
    try:
        return model.objects.mail_filter(user).get(**kwargs)
    except model.DoesNotExist:
        raise Http404

class LatexCompileError(Exception):
    pass

class HtmlToPdfError(Exception):
    pass

def render_tex_to_pdf(template, context):
    """
    Given a template that contains latex content, and context variables to hand
    to it, render a pdf.  Returns the name of a temporary file containing the
    pdf.
    """
    t = loader.get_template(template)
    tex_content = t.render(Context(context))
    pdf_name = compile_tex(tex_content)
    return pdf_name

    
def render_postcard(template, context):
    """
    Given a template for postcard content and context, render a postcard image.
    Returns the name of a temporary file containing the image.
    """
    t = loader.get_template(template)
    body = t.render(Context(context))
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as fh:
        filename = fh.name
    Postcard(address=context['address'], body=body).save(filename)
    return filename

def compile_tex(tex_content):
    """
    Returns the (temporary) filename of a pdf compiled from the given 
    tex content.
    """
    # un-unicode
    base = tempfile.mkdtemp(prefix="cpt")
    tex = os.path.join(base, "letter.tex")
    pdf = os.path.join(base, "letter.pdf")
    err = os.path.join(base, "error.txt")
    with codecs.open(tex, encoding='utf-8', mode='w') as fh:
        fh.write(tex_content)

    with codecs.open(tex, encoding='utf-8') as infile:
        with open(pdf, 'w') as outfile:
            with open(err, 'w') as errfile:
                proc = subprocess.Popen([
                        getattr(settings, 'RUBBER_PIPE_CMD', '/usr/bin/rubber-pipe'), 
                        "-fd", "-vvv", 
                    ], stderr=errfile, stdout=outfile, stdin=infile, 
                    cwd=base)
                proc.communicate()
    with open(err) as fh:
        error = fh.read()
        err_pos = error.find("There were errors.")

    if err_pos == -1:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as fh:
            moved_name = fh.name
        shutil.move(pdf, moved_name)
        exception = None
    else:
        exception = LatexCompileError(error[err_pos:])
    proc = subprocess.Popen(["rm", "-r", base])
    if exception:
        raise exception
    return moved_name

def tex_escape(string):
    # do matching quotes
    string = re.sub(r'(")([^"]*)(")', r"``\2''", string)
    # any straggling quotes
    string = re.sub(r'"', "''", string)
    lines = [line if line != "" else u"~" for line in string.split("\n")]
    string = u"\\\\\n".join(lines)
    # The rest
    return mark_safe("".join(latex_equivalents.get(ord(c), c) for c in string))

def combine_pdfs(*args, **kwargs):
    """
    PDFtk implementation.
    """
    add_blanks = kwargs.get('add_blanks', False)
    out_filename = kwargs.get('filename', False)

    tmpdir = tempfile.mkdtemp(prefix="combinepdfs")
    # Copy all files to the tmpdir, and add blank pages if needed.
    for i, filename in enumerate(args):
        shutil.copy(filename, os.path.join(tmpdir, "%06d.pdf" % i))
        if add_blanks:
            with open(filename) as fh:
                reader = PdfFileReader(fh)
                num_pages = reader.getNumPages()
                if num_pages % 2 == 1:
                    shutil.copy(os.path.join(settings.MEDIA_ROOT, 
                                             "blank.pdf"),
                                os.path.join(tmpdir, "%06da.pdf" % i))

    # Combine
    if not out_filename:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as fh:
            out_filename = fh.name

    cmd = [settings.PDFTK_CMD] + [os.path.join(tmpdir, f) for f in sorted(os.listdir(tmpdir))] + ["cat", "output", out_filename]
    retcode = subprocess.call(cmd)
    if retcode != 0:
        raise Exception("Combining pdfs failed: %s" % (" ".join(cmd)))
    shutil.rmtree(tmpdir)
    return out_filename

# PyPDF based implementation consumes too much memory for thin vhosts.
#def combine_pdfs(*args, **kwargs):
#    """ PyPDF implementation """
#    add_blanks = kwargs.get('add_blanks', False)
#    out_filename = kwargs.get('filename', False)
#    output = PdfFileWriter()
#    if add_blanks:
#        blank_page = PdfFileReader(open(os.path.join(settings.MEDIA_ROOT, "btb", "blank.pdf"))).getPage(0)
#    # handles must stay open until writer is done.
#    fhs = [open(filename) for filename in args]
#    for fh, filename in zip(fhs, args):
#        reader = PdfFileReader(fh)
#        count = reader.getNumPages()
#        for page in range(count):
#            output.addPage(reader.getPage(page))
#        if add_blanks and count % 2 == 1:
#            output.addPage(blank_page)
#
#    if out_filename:
#        with open(out_filename, 'w') as fh:
#            output.write(fh)
#    else:
#        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as fh:
#            out_filename = fh.name
#            output.write(fh)
#
#    for fh in fhs:
#        fh.close()
#
#    return out_filename

def url_to_pdf(url):
    """
    Returns the (tempoary) filename of a pdf representing a printout of
    the given URL.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as fh:
        pdf_name = fh.name
    if not url.startswith("http"):
        url = "http://%s%s" % (Site.objects.get_current().domain, url)

    proc = subprocess.Popen([WKHTMLTOPDF_CMD, 
        "--page-size", 'letter',
        "--print-media-type", 
        url, 
        pdf_name], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE)
    stdoutdata, stderrdata = proc.communicate()
    if stderrdata and "http error" in stderrdata:
        try:
            os.remove(pdf_name)
        except OSError:
            pass
        raise HtmlToPdfError(["; ".join((stderrdata.split("\n")[-2], url))])
    return pdf_name

def build_envelope(from_address, to_address):
    """
    Returns a file handle to a rendered envelope.
    """
    txtimg = Envelope(from_address=from_address, to_address=to_address)
    fh = cStringIO.StringIO()
    txtimg.save(fh, "jpeg")
    return fh

def write_address_csv(addresses, filename):
    split_addresses = []
    max_lines = 0
    for address in addresses:
        lines = [a.strip() for a in address.split("\n")]
        split_addresses.append(lines)
        max_lines = max(len(lines), max_lines)
    with open(filename, 'w') as fh:
        writer = UnicodeWriter(fh, encoding='utf-8', quoting=csv.QUOTE_ALL)
        for cols in split_addresses:
            cols = [""] * (max_lines - len(cols)) + cols
            writer.writerow(cols)

def write_csv(rows, filename):
    with open(filename, 'w') as fh:
        writer = UnicodeWriter(fh, encoding='utf-8', quoting=csv.QUOTE_ALL)
        for row in rows:
            writer.writerow(row)

class TextImage(object):
    density = 300
    def __init__(self, width, height, margin):
        self.margin = margin * self.density
        self.im = Image.new(
            'RGB', 
            (int(width * self.density), int(height * self.density)),
            (255, 255, 255)
        )

    def draw_wrapped_text(self, text, boundaries, rev_indent="", par_height=1,
            font_size=48,
            font_path=settings.TEXT_IMAGE_FONT):
        font = ImageFont.truetype(font_path, font_size)
        x, y = boundaries[0]
        mx, my = boundaries[1]
        width = mx - x

        ypos = y
        paragraphs = text.split("\n")
        draw = ImageDraw.Draw(self.im)
        for par in paragraphs:
            if not par.strip():
                ypos += font.getsize("M")[1] * par_height
                continue
            words = par.split()
            i = 0
            while True:
                if len(words) == 0:
                    break
                fsize = font.getsize(" ".join(words[:i + 1]))
                if fsize[0] > width or i >= len(words):
                    text = " ".join(words[:i])
                    draw.text((x, ypos), text, fill=(0, 0, 0), font=font)
                    ypos = ypos + fsize[1]
                    words = words[i:]
                    if rev_indent and len(words):
                        words[0] = rev_indent + words[0]
                    i = 0
                i += 1

    def save(self, filename, fmt=None):
        return self.im.save(filename, fmt)

    def to_response(self, attachment_name):
        response = HttpResponse(mimetype='application/jpeg')
        response['Content-Disposition'] = 'attachment; filename=%s' % attachment_name
        self.im.save(response, "jpeg")
        return response

class MailingLabelSheet(TextImage):
    """
    Produce a mailing label sheet with up to 30 given addresses.
    """
    label_height = 1.
    label_width = 2. + 5./8
    column_offsets = (
        (5./32, 0.5),
        (2. + 15/16., 0.5),
        (5. + 23/32., 0.5),
    )

    def __init__(self):
        super(MailingLabelSheet, self).__init__(8.5, 11, 0)

    def get_dims(self, row, col):
        x1 = self.column_offsets[col][0]
        y1 = self.column_offsets[col][1] + row * self.label_height 
        x2 = self.column_offsets[col][0] + self.label_width
        y2 = self.column_offsets[col][1] + (row + 1) * self.label_height
        x1 *= self.density
        y1 *= self.density
        x2 *= self.density
        y2 *= self.density
        return ((x1, y1), (x2, y2))

    def draw(self, addresses):
        #self.draw_bounds()
        for i,address in enumerate(addresses):
            col = int(i / 10)
            row = i % 10
            m = 0.125 * self.density
            dims = self.get_dims(row, col)
            dims = ((dims[0][0] + m, dims[0][1] + m), (dims[1][0] + m, dims[1][1] + m))
            if len(address.split("\n")) > 4:
                font_size = 40
            else:
                font_size = 46
            
            self.draw_wrapped_text(address, dims, font_size=font_size, par_height=0)

    def draw_bounds(self):
        for row in range(10):
            for col in range(3):
                ((x1, y1), (x2, y2)) = self.get_dims(row, col)
                print col, row, ((x1, y1, x2, y2))
                draw = ImageDraw.Draw(self.im)
                draw.line([(x1, y1), (x1, y2)], fill=(0,0,0), width=1)
                draw.line([(x1, y1), (x2, y1)], fill=(0,0,0), width=1)
                draw.line([(x2, y1), (x2, y2)], fill=(0,0,0), width=1)
                draw.line([(x1, y2), (x2, y2)], fill=(0,0,0), width=1)
        
class Envelope(TextImage):
    def __init__(self, width=9.5, height=4.125, margin=0.5, 
            from_address="", to_address="", **kwargs):
        super(Envelope, self).__init__(width, height, margin, **kwargs)
        if from_address:
            self.draw_from_address(from_address)
        if to_address:
            self.draw_to_address(to_address)

    def draw_from_address(self, address):
        w, h = self.im.size
        m = self.margin
        self.draw_wrapped_text(address, ((m, m), (w / 2, h / 2 - m)))

    def draw_to_address(self, address):
        w, h = self.im.size
        m = self.margin
        self.draw_wrapped_text(address, ((w / 3 + m, h / 2), (w - m, h - m)))

class Postcard(TextImage):
    def __init__(self, width=5.5, height=4.25, margin=0.25, center_margin=0.1, 
            address="", body="", draw_center_line=True, 
            body_font_size=42, address_font_size=46,
            **kwargs):
        super(Postcard, self).__init__(width, height, margin, **kwargs)
        self.center_margin = center_margin * self.density
        self.body_font_size = body_font_size
        self.address_font_size = address_font_size

        if draw_center_line:
            self.draw_center_line()
        if address:
            self.draw_address(address)
        if body:
            self.draw_body(body)

    def draw_center_line(self):
        s = self.im.size
        m = self.margin
        draw = ImageDraw.Draw(self.im)
        draw.line([(s[0] / 2, m), (s[0] / 2, s[1] - m)], fill=(0,0,0))

    def draw_address(self, address):
        s = self.im.size
        m = self.margin
        self.draw_wrapped_text(
                address, 
                ((s[0] / 2 + m, s[1] / 2), (s[0] - m, s[1] - m)),
                rev_indent="        ",
                par_height=0,
                font_size=self.address_font_size
        )

    def draw_body(self, text):
        s = self.im.size
        m = self.margin
        cm = self.center_margin
        self.draw_wrapped_text(
                text,
                ((m, m), (s[0] / 2 - cm, s[1] - m)),
                par_height=0.8,
                font_size=self.body_font_size
        )


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
