import os
import glob
import shutil
import tempfile
import subprocess
import datetime
from collections import defaultdict

from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from django.conf import settings

from scanning.models import Document
from scanning.utils import get_pdf_page_count
from correspondence import utils

def generate_file(letter):
    methods = {
        'letter': generic_letter,
        'consent_form': consent_form,
        'signup_complete': signup_complete_letter,
        'first_post': first_post_letter,
        'printout': printout,
        'comments': comments_letter,
        'waitlist': waitlist_postcard,
        'refused_original': refused_original,
        'returned_original': returned_original,
        'comment_removal': comment_removal,
    }
    if not letter.type:
        return None
    # Edge case: can't re-generate letters for people who have been made
    # inactive since the letter was created.
    if letter.type in ("first_post", "comments", "printout") and \
            (not letter.recipient.is_active or 
             not letter.recipient.profile.consent_form_received):
        return None
    # Edge case: Don't re-generate first posts if there's no first post
    # anymore.
    if letter.type == "first_post" and \
            not Document.objects.filter(author=letter.recipient,
                                        status="published").exists():
        return None
    # Edge case: Don't re-generate comments letters with no public comments.
    if letter.type == "comments" and not letter.comments.public().exists():
        return None

    tmp_file = methods[letter.type](letter)
    if not tmp_file:
        return None

    if os.path.getsize(tmp_file) == 0:
        raise Exception("Letter {0} ({1}) has errors -- filesize 0.".format(letter.id, letter.type))
    
    basename, ext = os.path.splitext(tmp_file)
    if letter.pk:
        destination = os.path.join(
                settings.MEDIA_ROOT,
                "letters",
                letter.created.strftime("%Y"),
                letter.created.strftime("%m"),
                "%s-%s-%s%s" % (
                    letter.recipient.pk if letter.recipient else "u" + str(id(letter)),
                    letter.type,
                    letter.pk, 
                    ext)
        )
        try:
            os.makedirs(os.path.dirname(destination))
        except OSError:
            pass
        shutil.move(tmp_file, destination)
        return os.path.relpath(destination, settings.MEDIA_ROOT)
    else:
        return tmp_file

def generic_letter(letter):
    if letter.is_postcard:
        return utils.render_postcard("correspondence/generic-postcard.txt", {
            'letter': letter,
            'address': letter.recipient.profile.full_address()
        })
    else:
        return utils.render_tex_to_pdf("correspondence/generic-letter.tex", {
            'letter': letter,
        })

def consent_form(letter):
    parts = []
    delete_after = []
    if letter.org.custom_intro_packet:
        parts.append(letter.org.custom_intro_packet.path)
    else:
        cover = utils.render_tex_to_pdf("correspondence/intro-packet-cover.tex", {
            'letter': letter
        })
        parts.append(cover)
        delete_after.append(cover)
        packet = utils.render_tex_to_pdf("correspondence/intro-packet-packet.tex", {
            'MEDIA_ROOT': settings.MEDIA_ROOT,
            'letter': letter
        })
        parts.append(packet)
        delete_after.append(packet)
    parts.append(os.path.join(settings.MEDIA_ROOT, "intro", "license.pdf"))

    combined = utils.combine_pdfs(*parts, add_blanks=True)
    for pdf in delete_after:
        os.remove(pdf)
    return combined

def signup_complete_letter(letter):
    return utils.render_tex_to_pdf("correspondence/created-packet-template.tex", {
        'letter': letter
    })

def first_post_letter(letter):
    pdfs = []
    pdfs.append(
        utils.render_tex_to_pdf("correspondence/first-post-template.tex", {
            'letter': letter
        })
    )
    # First post, if any.  First post uses a dynamic document rather than the
    # letter.document field, so that if a document is ever removed/unpublished,
    # we get the updated "first post" on printout.
    try:
        document = Document.objects.filter(status="published", type="post",
                author__pk=letter.recipient.pk).order_by('date_written')[0]
        pdfs.append(utils.url_to_pdf(document.get_absolute_url()))
    except IndexError:
        pass
    # Profile, if any
    if Document.objects.filter(status="published", type="profile",
            author__pk=letter.recipient.pk).order_by('-date_written').exists():
        pdfs.append(utils.url_to_pdf(letter.recipient.profile.get_absolute_url()))
    if not pdfs:
        return None

    combined_pdf = utils.combine_pdfs(*pdfs)
    for pdf in pdfs:
        os.remove(pdf)
    return combined_pdf

def printout(letter):
    return utils.url_to_pdf(letter.document.get_absolute_url())

def comments_letter(letter):
    pdfs = [
        # cover letter
        utils.render_tex_to_pdf("correspondence/comment-mailing.tex", {
            'letter': letter
        }),
        utils.url_to_pdf(
            reverse("correspondence.recent_comments_letter", args=[letter.pk])
        )
    ]
    combined_pdf = utils.combine_pdfs(*pdfs)
    for pdf in pdfs:
        os.remove(pdf)
    return combined_pdf

def waitlist_postcard(letter):
    return utils.render_postcard("correspondence/waitlist-postcard.txt", {
        'letter': letter,
        'address': letter.recipient.profile.full_address(),
    })

def returned_original(letter):
    return utils.render_tex_to_pdf("correspondence/returned-original.tex", {
        'letter': letter,
        'address': letter.recipient.profile.full_address(),
    })

def refused_original(letter):
    return utils.render_tex_to_pdf("correspondence/refused-original.tex", {
        'letter': letter,
        'address': letter.recipient.profile.full_address(),
    })

def comment_removal(letter):
    return utils.render_tex_to_pdf("correspondence/comment-removal.tex", {
            'letter': letter,
            'comment': letter.comments.get(),
            'message': letter.body,
        })

def generate_colation(mailing):
    """
    Generates a zip file containing all of the letters and envelopes for a
    particular mailing.  The output has the following structure:
    mailings-YYYY-MM-DD/ 
      letters/ (all letters, individually)
      envelopes/ (all envelopes)
      postcards/ (any other postcard type)
    
      all_letters.pdf -- all letters of all kinds (not postcards) combined for 
                         double-sided printing
      manifest.csv    -- CSV file with sheet counts and names.
      addresses.csv   -- CSV file with all addresses, one column per line,
                         front-padded
    """
    
    tmpdir = tempfile.mkdtemp(prefix="colation")
    outname = "mailings-%s_%s" % (
        datetime.datetime.now().strftime("%Y-%m-%d"),
        mailing.pk,
    )
    outdir = os.path.join(tmpdir, outname)
    os.makedirs(outdir) # also makes outdir

    envelopes = set()
    postcards = []
    letters = []
    manifest = defaultdict(int)
    for letter in mailing.letters.all():
        if not letter.get_file():
            continue
        address = letter.get_recipient_address()
        slug = slugify(address.split("\n")[0])
        if letter.is_postcard:
            postcards.append((slug, letter))
            continue
        letters.append((slug, letter))
        envelopes.add((slug, address, letter.org.mailing_address))
        count = get_pdf_page_count(letter.get_file())
        if count:
            manifest[(slug, address)] += count

    # Write manifest file
    if manifest:
        items = manifest.items()
        items.sort()
        rows = [(a.split("\n")[0].strip(), str((c + c%2)/2)) for (s, a),c in items]
        utils.write_csv(rows, os.path.join(outdir, "manifest.csv"))

    # Write envelopes
    if envelopes:
        envelope_dir = os.path.join(outdir, "envelopes")
        os.makedirs(envelope_dir)
        for slug, addr, from_address in envelopes:
            env_fh = utils.build_envelope(
                    from_address=from_address,
                    to_address=addr)
            path = os.path.join(envelope_dir, "%s-envelope.jpg" % slug)
            with open(path, 'w') as fh:
                fh.write(env_fh.getvalue())

        # Write addresses CSV
        sorted_addresses = [a for s, a, r in sorted(envelopes)]
        utils.write_address_csv(sorted_addresses,
                os.path.join(outdir, "addresses.csv"))

    # Write postcards
    if postcards:
        postcard_dir = os.path.join(outdir, "postcards")
        os.makedirs(postcard_dir)
        for slug, postcard in postcards:
            dest = os.path.join(postcard_dir,
                    "{0}-{1}{2}.jpg".format(
                        slug,
                        postcard.type,
                        postcard.pk
                    ))
            shutil.copy(postcard.get_file(), dest)

    # Copy and combine letters
    if letters:
        letter_dir = os.path.join(outdir, "letters")
        os.makedirs(letter_dir)
        for slug, letter in letters:
            dest = os.path.join(letter_dir,
                    "{0}-{1}{2}.pdf".format(slug, letter.type, letter.pk))
            shutil.copy(letter.get_file(), dest)
        sorted_pdfs = sorted(glob.glob(os.path.join(letter_dir, "*.pdf")))
        utils.combine_pdfs(*sorted_pdfs,
                add_blanks=True,
                filename=os.path.join(outdir, "all_letters.pdf")
        )
    
    # Zip
    tmp_zip_path = "{0}.zip".format(outdir)
    zipbase = os.path.basename(outdir)
    proc = subprocess.Popen(["/usr/bin/zip", "-r", zipbase, zipbase],
            cwd=tmpdir) # zip adds ".zip"
    proc.communicate()

    # Clean up 
    dest = os.path.join(settings.MEDIA_ROOT, "mailings",
            os.path.basename(outname) + ".zip")
    try:
        os.makedirs(os.path.dirname(dest))
    except OSError:
        pass
    shutil.move(tmp_zip_path, dest)
    proc = subprocess.Popen(["rm", "-r", tmpdir])
    return os.path.relpath(dest, settings.MEDIA_ROOT)
