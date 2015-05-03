import os
import re
import json
import random
import shutil
import string
import zipfile
import logging
import datetime
import tempfile
import subprocess
from PIL import Image, ImageDraw
import cStringIO as StringIO

from pyPdf import PdfFileWriter, PdfFileReader
from pyPdf.utils import PdfReadError

from django.contrib.auth.models import User
from django.conf import settings
from scanblog.celery import app
from sorl.thumbnail import get_thumbnail

from scanning.models import Scan, ScanPage, Document, DocumentPage, EditLock
from profiles.models import Organization

logger = logging.getLogger(__name__)

@app.task(name="scanning.tasks.update_document_images")
def update_document_images(document_id=None, process_pages=True, 
        process_highlight=True, document=None, status=None):
    """
    Apply transformations to the document pages and highlights.
    """
    doc = document or Document.objects.get(id=document_id)
    logger.debug("Update document images for {0}.".format(doc.pk))
    if not os.path.exists(doc.file_dir()):
        logger.debug("Creating directories: {0}".format(doc.file_dir()))
        os.makedirs(doc.file_dir())

    # Be sure to apply page transforms first, so highlight can work from them.
    if process_pages:
        _apply_page_transforms(doc)
    if process_highlight:
        _create_highlight(doc)

    if status is not None:
        logger.debug("Setting doc {0} status to {1}".format(doc.pk, status))
        doc.status = status
    doc.save()
    logger.debug("Update document images done.")
    return True

@app.task(name="scanning.tasks.process_zip")
def process_zip(filename, uploader_id, org_id, redirect=None):
    """
    Take a zip file, and process all PDFs that are in it as scans.
    """

    uploader = User.objects.get(pk=uploader_id)
    org = Organization.objects.get(pk=org_id)
    zipfh = zipfile.ZipFile(filename, 'r')
    tmpdir = tempfile.mkdtemp(prefix="zipscan")
    scans_to_process = []
    try:
        pdf_files = []
        for info in zipfh.infolist():
            # Watch out for mac zip archives, which contain a MACOS directory
            # with bogus PDFs that start with "._"
            if info.filename.lower().endswith(".pdf") and \
                    info.file_size > 1000 and \
                    not os.path.basename(info.filename).startswith("."):

                newname = os.path.join(
                        tmpdir, os.path.basename(info.filename)
                )

                with open(newname, 'wb') as fh:
                    zipextfile = zipfh.open(info.filename)
                    fh.write(zipextfile.read())
                    zipextfile.close()

                pdf_files.append(newname)

        for pdf_file in pdf_files:
            dest = move_scan_file(filename=pdf_file)
            scans_to_process.append(Scan.objects.create(
                uploader=uploader,
                org=org,
                pdf=os.path.relpath(dest, settings.MEDIA_ROOT),
                under_construction=True,
            ))

    finally:
        zipfh.close()
        os.remove(filename)
        shutil.rmtree(tmpdir)

    chain = split_scan.map([s.id for s in scans_to_process])
    chain()
    return redirect

@app.task(name="scanning.tasks.process_scan_to_profile")
def process_scan_to_profile(scan_id, redirect):
    """
    This scan processor is used by users who upload pdf's for their own
    profiles.
    """
    split = split_scan.subtask(scan_id=scan_id, redirect=redirect)
    split()
    scan = Scan.objects.get(pk=scan_id)
    doc = Document.objects.create(
        scan=scan, 
        editor=scan.author,
        author=scan.author,
        type="profile",
        status="published",
        under_construction=True,
    )
    for page in scan.scanpage_set.all():
        DocumentPage.objects.create(
            document=doc,
            scan_page=page,
            order=page.order,
        )
    up = update_document_images.subtask(document_id=doc.id)
    up()
    return redirect

@app.task(name="scanning.tasks.split_scan")
def split_scan(scan_id=None, redirect=None, scan=None):
    """
    Split a Scan into ScanPage's
    """
    # Mark under construction.
    scan = scan or Scan.objects.get(pk=scan_id)
    scan.under_construction = True
    scan.save()
    for doc in scan.document_set.all():
        doc.under_construction = True
        doc.save()

    # Check that the pdf works, and try to fix if not.
    try:
        with open(scan.pdf.path, 'rb') as fh:
            reader = PdfFileReader(fh)
            try:
                if 'Quartz' in reader.getDocumentInfo()['/Producer']:
                    # Assume that anything produced by Mac OS X Quartz needs to be
                    # fixed. It's buggy.
                    raise PdfReadError()
            except KeyError:
                pass
    except PdfReadError:
        logger.debug("Error reading pdf %s, try to fix." % scan.pdf.path)
        _fix_pdf(scan.pdf.path)

    name, ext = os.path.splitext(scan.pdf.name)
    directory, name_with_ext = os.path.split(scan.pdf.path)
    basename, ext = os.path.splitext(name_with_ext)
    page_basename = basename + "-page"

    # Burst pdf into single pages.
    pdf_pages = []
    burst_dir = tempfile.mkdtemp(suffix="pdfburst")
    #print "Bursting pages to " + burst_dir + "-%03d.pdf"

    # We used to use PyPDF to do this, but it consumes too much memory for
    # large PDFs.
    proc = subprocess.Popen([
        settings.NICE_CMD, settings.PDFTK_CMD, scan.pdf.path, "burst",
        "output", os.path.join(burst_dir, page_basename + "-%03d.pdf")
    ])
    proc.communicate()
    pages = sorted(os.listdir(burst_dir))
    for page in pages:
        #print "trying %s" % page
        match = re.match(page_basename + "-(\d\d\d)\.pdf", page)
        if match:
            page_dest = os.path.join(directory, "%s-%03d.pdf" % 
                    (page_basename, int(match.group(1)) - 1))
            #print "found %s" % page_dest
            shutil.move(os.path.join(burst_dir, page), page_dest)
            pdf_pages.append(page_dest)
    shutil.rmtree(burst_dir)

# NOTE: This simpler pyPdf strategy doesn't do so well on some pdfs.  pdftk
# burst is much more robust.
#    page_basename_with_dir = directory + "/" + page_basename
#    with open(scan.pdf.path, "rb") as in_fh:
#        reader = PdfFileReader(in_fh)
#        for i in range(0, reader.getNumPages()):
#            print "%s / %s" % (i, reader.getNumPages())
#            pdf_pages.append(page_basename_with_dir + "-%03d.pdf" % i)
#            with open(pdf_pages[-1], 'wb') as out_fh:
#                writer = PdfFileWriter()
#                writer.addPage(reader.getPage(i))
#                writer.write(out_fh)

    jpgs = []
    for page in pdf_pages:
        #print "Converting %s to jpg..." % page
        img = _pdfimages_page_to_jpg(page)
        jpgs.append(img)

    scanpages = []
    for i, filename in enumerate(jpgs):
        try:
            scanpage = ScanPage.objects.get(scan=scan, order=i)
        except ScanPage.DoesNotExist:
            scanpage = ScanPage(scan=scan, order=i)
        scanpage.image = os.path.relpath(filename, settings.MEDIA_ROOT)
        scanpage.save()
        scanpages.append(scanpage)
        # Pre-cache some thumbnails (performance optimization for moderation).
        get_thumbnail(scanpage.image.path, "900")
        get_thumbnail(scanpage.image.path, "100")
        get_thumbnail(scanpage.image.path, "15")
    scan.scanpages = scanpages

    # update document images, if any.
    chain = update_document_images.map([d.pk for d in scan.document_set.all()])
    chain()
    for doc in scan.document_set.all():
        doc.under_construction = False
        doc.save()
    scan.under_construction = False
    scan.save()
    return redirect

@app.task(name="scanning.tasks.merge_scans")
def merge_scans(scan_id=None, filename=None, redirect=None):
    scan = Scan.objects.get(pk=scan_id)
    concatenated = _concatenate_pdfs(scan.pdf.path, filename)
    dest = move_scan_file(filename=concatenated)
    scan.full_delete(filesonly=True)
    scan.pdf = os.path.relpath(dest, settings.MEDIA_ROOT)
    scan.under_construction = True
    scan.save()
    split_scan.subtask(scan_id=scan.id)()
    os.remove(filename)
    return redirect

@app.task(name="scanning.tasks.expire_editlock")
def expire_editlock(editlock_id=None):
    EditLock.objects.filter(pk=editlock_id).delete()
    return "success"

def _concatenate_pdfs(*pdfs):
    fhs = [open(name) for name in pdfs]
    readers = [PdfFileReader(fh) for fh in fhs]
    writer = PdfFileWriter()
    for reader in readers:
        for i in range(0, reader.getNumPages()):
            writer.addPage(reader.getPage(i))
    with tempfile.NamedTemporaryFile(
            delete=False, suffix=".pdf", prefix="concat") as fh:
        writer.write(fh)
        dest = fh.name
    for fh in fhs:
        fh.close()
    return dest

def _pdfimages_page_to_jpg(pdf_page):
    """
    Convert to jpg with pdfimages.  This is much faster than imagemagick for
    similar quality, but only works correctly if the pdf is a simple scan
    (single image per page) -- complex PDFs with multiple images will produce
    ugly and unexpected results.  For that reason, we try to isolate the
    output, and fall back to imagemagick if we get more images out than
    expected.
    """
    basename, ext = os.path.splitext(pdf_page)
    working_dir = tempfile.mkdtemp(suffix="-pdfimages-convert")
    ppm_prefix = os.path.join(working_dir, "img")
    txt_content = ppm_prefix + ".txt"

    # Verify that the pdf doesn't have text content first -- if so, we want
    # to use imagemagick instead.
    logger.debug("Extracting text for %s ..." % pdf_page)
    proc = subprocess.Popen([
        settings.NICE_CMD, settings.PDFTOTEXT_CMD, pdf_page, txt_content,
    ])
    proc.communicate()
    with open(txt_content) as fh:
        if fh.read().strip() != "":
            logger.debug("text not empty.  Switching to imagemagick.")
            # The PDF isn't empty of text!
            shutil.rmtree(working_dir)
            return _imagemagick_page_to_jpg(pdf_page)
    os.remove(txt_content)
    logger.debug("text empty.  Trying pdfimages.")

    # Run pdfimages.
    proc = subprocess.Popen([
        settings.NICE_CMD, settings.PDFIMAGES_CMD, pdf_page, ppm_prefix
    ])
    proc.communicate()

    # working_dir should now contain a ppm file.
    ppm_file = ppm_prefix + "-000.ppm"
    if not (len(os.listdir(working_dir)) == 1 and os.path.exists(ppm_file)):
        # This is not a simple PDF.  Use imagemagick instead.
        logger.debug("pdfimages didn't return expected number of images.  Trying imagemagick.")
        shutil.rmtree(working_dir)
        return _imagemagick_page_to_jpg(pdf_page)

    output = "%s.jpg" % basename
    # Convert to jpg.
    proc = subprocess.Popen([settings.NICE_CMD, settings.CONVERT_CMD, 
        #"-resize", "850x10000>",
        "-type", "TrueColor",
        ppm_file, output], stdout=subprocess.PIPE)
    proc.wait()
    os.remove(pdf_page)
    shutil.rmtree(working_dir)
    logger.debug("pdfimages success.")
    return output
    

def _fix_pdf(path):
    """
    Try to fix a pdf.  Raise an exception if it doesn't work.
    """
    logger.debug("Fixing pdf %s." % path)
    with tempfile.NamedTemporaryFile(delete=False, suffix="fixme.pdf") as fh:
        tmpname = fh.name
    # Just use pass it through pdftk, which fixes most common errors.
    proc = subprocess.Popen([settings.NICE_CMD, settings.PDFTK_CMD, 
        path, "cat", "output", tmpname], stdout=subprocess.PIPE)
    proc.communicate()
    # This will raise an exception if it didn't work.
    try:
        with open(tmpname, 'rb') as fh:
            PdfFileReader(fh)
    except Exception as e:
        logger.exception(e)
        logger.debug("Aborting.")
        raise
    # It worked.  Overwrite path with tmpname.
    shutil.move(tmpname, path)
    return path

def _imagemagick_page_to_jpg(pdf_page):
    """
    Convert to jpg (with imagemagick).  For optimum quality, we do this in
    two stages: first, convert using absurdly high dpi.  Second, downsample
    to a more appropriate size.  This makes it much slower, but the higher
    quality is worth it.
    """
    logger.debug("imagemagick convert %s" % pdf_page)

    # 1. High density go!
    output = "%s.jpg" % os.path.splitext(pdf_page)[0]
    proc = subprocess.Popen([settings.NICE_CMD, settings.CONVERT_CMD,
            '-density', '300x300',
            pdf_page, output], stdout=subprocess.PIPE)
    proc.communicate()
    os.remove(pdf_page)

    # 2. Dither down go!
    # Reduce size.  Modify in place.
    proc = subprocess.Popen([settings.NICE_CMD, settings.CONVERT_CMD, 
        "-resize", "850x10000>",
        "-type", "TrueColor",
        output, output])
    proc.wait()
    return output

def move_scan_file(uploaded_file=None, filename=None):
    """
    Create a random name for the uploaded file, and place it in a directory
    based on the current date.
    """
    abs_dir = os.path.abspath(
        os.path.join(settings.MEDIA_ROOT, settings.UPLOAD_TO,
            datetime.datetime.now().strftime("blogs/scans/%Y/%m/%d"))
    )
    dest = ""
    # Get a random name that doesn't exist yet.
    while True:
        name = ''.join(
                random.choice(string.hexdigits) for i in range(8)
        ) + ".pdf"
        dest = os.path.join(abs_dir, name)
        if not os.path.exists(dest):
            break
    if not os.path.exists(os.path.dirname(dest)):
        os.makedirs(os.path.dirname(dest))

    if filename:
        shutil.move(filename, dest)
    elif uploaded_file:
        with open(dest, 'wb+') as fh:
            for chunk in uploaded_file.chunks():
                fh.write(chunk)
    return dest

def _create_highlight(doc):
    """
    Create the highlight (teaser image) for the given doc, as specified by
    doc.highlight_transform
    """
    logger.debug("Create highlight for {0}".format(doc.pk))
    doc_basename = doc.get_basename()
    if doc.highlight and os.path.exists(doc.highlight.path):
        logger.debug("Removing existing highlight {0}".format(
            doc.highlight.path
        ))
        os.remove(doc.highlight.path)
    if doc.highlight_transform:
        logger.debug("Transform: `{0}`".format(doc.highlight_transform))
        try:
            tx = json.loads(doc.highlight_transform)
        except ValueError:
            logger.error("Invalid JSON for Document {} highlight_transform: {}".format(
                doc.pk, doc.highlight_transform))
            tx = None
            return
        if tx:
            try:
                documentpage = doc.documentpage_set.get(pk=tx['document_page_id'])
            except DocumentPage.DoesNotExist:
                logger.error("Bad highlight transform for Document {}: " \
                             "DocumentPage {} does not exist. {}".format(
                                 doc.pk,
                                 tx['document_page_id'],
                                 doc.highlight_transform))
                return
            img = Image.open(documentpage.image)
            img = img.crop([int(a) for a in tx['crop']])
            highlight_fname = "{0}-highlight.jpg".format(doc_basename)
            logger.debug("Save highlight: {0}".format(highlight_fname))
            img.save(highlight_fname)
            doc.highlight = os.path.relpath(highlight_fname, settings.MEDIA_ROOT)
            doc.save()
    logger.debug("Save highlight done.")
 
def _apply_page_transforms(doc):
    """
    Apply the transformations to every DocumentPage in a document, and rebuild
    the PDF.
    """
    logger.debug("Apply transforms start")
    if doc.pdf and os.path.exists(doc.pdf.path):
        os.remove(doc.pdf.path)
    doc_basename = doc.get_basename()
    #print "Page transformations for " + str(doc.pk)
    with open(doc.scan.pdf.path, 'rb') as scan_fh:
        reader = PdfFileReader(scan_fh)
        doc.pdf = "{0}.pdf".format(
                os.path.relpath(doc_basename, settings.MEDIA_ROOT)
        )
        page_fhs = []
        with open(doc.pdf.path, 'wb') as doc_fh:
            writer = PdfFileWriter()
            pages = list(doc.documentpage_set.all())
            for page in pages:
                if page.image and os.path.exists(page.image.path):
                    os.remove(page.image.path)
            for page in pages:
                #debug:
                #print "Page " + str(page.order) + ":"
                #print " " + page.transformations
                logger.debug("Transforming page {0}".format(page.pk))
                img = Image.open(page.scan_page.image.path)
                img_filename = "%s-page-%s.jpg" % (doc_basename, page.order)

                logger.debug("Transformations: `{0}`".format(page.transformations))
                if page.transformations or img.size[0] > 850:
                    tx = json.loads(page.transformations or "{}")
                    if 'rotate' in tx:
                        logger.debug("Rotating {0}".format(tx['rotate']))
                        # Rotate, but preserve width, and white background.
                        width, height = img.size
                        # Upscale for quality.
                        width *= 2
                        height *= 2 
                        img = img.resize((width, height), 
                                resample=Image.BICUBIC)
                        # Add alpha channel to not get black background from
                        # rotation
                        img = img.convert('RGBA')
                        # PIL rotates counter-clockwise.  We want clockwise.
                        img = img.rotate(-tx['rotate'], 
                                resample=Image.BICUBIC,
                                expand=True)
                        # Resize back to original width
                        resize = (
                            width/2,
                            int(img.size[1] * float(width) / img.size[0])/2
                        )
                        # ... but shrink further to 850 max width, if needed.
                        # Crop/highlight dimensions are based on max 850px
                        # width.
                        if resize[0] > 850:
                            resize = (
                                850,
                                int(resize[1] * (850. / resize[0]))
                            )
                        img = img.resize(resize, resample=Image.ANTIALIAS)
                        # Add a white background 
                        collage = Image.new('RGBA', resize, 
                                (255, 255, 255, 255))
                        collage.paste(img, (0,0), img)
                        img = collage.convert('RGB')
                    elif img.size[0] > 850:
                        logger.debug("Scale from {0} to 850".format(img.size))
                        # If we are'nt shrinking after rotating, shrink now.
                        img = img.resize(
                                (850, int(img.size[1] * 850. / img.size[0])),
                                resample=Image.ANTIALIAS
                        )

                    logger.debug("Checking for redactions.")
                    if tx and len(tx.get('redactions', [])) > 0:
                        logger.debug("Redacting")
                        draw = ImageDraw.Draw(img)
                        for r in tx['redactions']:
                            draw.rectangle([int(d) for d in r], fill="#000000")
                        del draw
                    if tx and len(tx.get('white_redactions', [])) > 0:
                        logger.debug("White redacting")
                        draw = ImageDraw.Draw(img)
                        for r in tx['white_redactions']:
                            draw.rectangle([int(d) for d in r], fill="#ffffff")
                        del draw

                    logger.debug("Checking for cropping.")
                    if 'crop' in tx and tx['crop'] is not None:
                        logger.debug("Cropping to {0}".format(tx['crop']))
                        img = img.crop([int(a) for a in tx['crop']])
                                
                    logger.debug("Storing page.")
                    # In-memory file to write pdf page to
                    page_fhs.append(StringIO.StringIO())
                    # Save page img as pdf.  We must hang on to file
                    # handles until the PdfFileWriter writes to disk.
                    img.save(page_fhs[-1], "pdf")
                    # Grab page from pdf, and add to writer.
                    page_reader = PdfFileReader(page_fhs[-1])
                    writer.addPage(page_reader.getPage(0))
                else:
                    # Just add the original PDF page if we aren't transforming.
                    writer.addPage(reader.getPage(page.scan_page.order))
                # Save transformed file (or copy of untransformed scan page
                # img)
                logger.debug("Saving image")
                img.save(img_filename)
                page.image = os.path.relpath(img_filename, settings.MEDIA_ROOT)
                page.save()

            logger.debug("Writing PDF")
            writer.write(doc_fh)
            for fh in page_fhs:
                fh.close()
    logger.debug("Apply transforms done")

