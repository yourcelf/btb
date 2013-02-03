import os
import random
import string
import tempfile
import subprocess
from optparse import make_option
from collections import defaultdict

import yaml
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from django.core.management.base import BaseCommand
from django.conf import settings
from django.template.defaultfilters import slugify
from django.contrib.localflavor.us.us_states import US_STATES
from django.contrib.sites.models import Site

from scanning import tasks
from django.contrib.auth.models import User, Group
from profiles.models import Profile, Organization
from scanning.models import Scan, Document, DocumentPage
from comments.models import Comment
from correspondence.models import Letter

BACKGROUNDS = {
    'post': [
        os.path.join(settings.MEDIA_ROOT, "test", "backgrounds", "lorem0.jpg"),
        os.path.join(settings.MEDIA_ROOT, "test", "backgrounds", "lorem1.jpg"),
    ],
    'license': [
        os.path.join(settings.MEDIA_ROOT, "test", "backgrounds", "license0.jpg"),
        os.path.join(settings.MEDIA_ROOT, "test", "backgrounds", "license1.jpg"),
    ],
    'profile': [
        os.path.join(settings.MEDIA_ROOT, "test", "backgrounds", "profile0.jpg"),
        os.path.join(settings.MEDIA_ROOT, "test", "backgrounds", "profile1.jpg"),
    ],
    'photo': [
        os.path.join(settings.MEDIA_ROOT, "test", "backgrounds", "photo.jpg"),
    ],
}

def build_pdf(parts, profile):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as fh:
        name = fh.name
    c = canvas.Canvas(name)

    # Envelope
    c.setFont("Helvetica", 16)
    c.setStrokeColorRGB(1, 1, 1)
    c.setFillColorRGB(0.8, 0.8, 0.8)
    c.rect(0, 6*inch, 8.5*inch, 5*inch, fill=1)
    c.translate(0, 2 * inch)
    c.setFillColorRGB(0, 0, 0)
    # From address
    for i,line in enumerate([profile.display_name] + profile.mailing_address.split("\n")):
        c.drawString(0.5 * inch, (7.5 - i * 0.2) * inch, line)
    # To address
    to_address = profile.user.organization_set.get().mailing_address
    for i,line in enumerate(to_address.split("\n")):
        c.drawString(4 * inch, (6 - i * 0.2) * inch, line)
    c.showPage()

    # Contents
    part_counts = defaultdict(int)
    for part in parts:
        overlay_text = "%s %s" % (
            part['type'],
            str(Document.objects.filter(type=part['type']).count() + part_counts[part['type']])
        )
        part_counts[part['type']] += 1
        backgrounds = BACKGROUNDS.get(part['type'], None)
        for page in range(part['pages']):
            if backgrounds:
                c.drawImage(backgrounds[page % len(backgrounds)], 0, 0 * inch,
                    width=8.5 * inch, preserveAspectRatio=True
                )
            c.setFont("Helvetica", 100)
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.setFillColorRGB(0.8, 0.8, 0.8)
            c.drawString(inch, 10 * inch, overlay_text)
            c.setFont("Helvetica", 100)
            c.drawString(inch * 0.5, inch * 1, "page %s/%s" % (page + 1, part['pages']))
            c.showPage()
    c.save()
    # Flatten PDF text into images, by passing thru imagemagick.
    subprocess.Popen([settings.CONVERT_CMD, name, name]).communicate()
    return name

def load_test_data():
    data_file = os.path.join(settings.MEDIA_ROOT, "test", "test_data.yaml")
    uploader = User.objects.get(username='uploader')
    commenter = User.objects.create(username="commenter")
    with open(data_file) as fh:
        data = yaml.safe_load(fh)

    orgs = {}

    print "Setting site..."
    site = Site.objects.get_current()
    site.domain = data['site']['domain']
    site.name = data['site']['name']
    site.save()

    print "Adding admins..."
    for admin_data in data['admins']:
        user, created = User.objects.get_or_create(
                username=admin_data['username'],
                is_superuser=True,
                is_staff=True,
        )
        user.set_password(admin_data['password'])
        user.save()

    print "Adding orgs..."
    for org_data in data['orgs']:
        org, created = Organization.objects.get_or_create(
                name=org_data['name'],
                personal_contact=org_data['personal_contact'],
                slug=slugify(org_data['name']),
                public=org_data['public'],
                mailing_address=org_data['mailing_address'],
                about=org_data.get('about', ''),
                footer=org_data.get('footer', ''),
        )
        orgs[org_data['name']] = org
        for mod_data in org_data['moderators']:
            u, created = User.objects.get_or_create(
                    username=mod_data['username']
            )
            u.set_password(mod_data['password'])
            u.save()
            org.moderators.add(u)
            Group.objects.get(name='moderators').user_set.add(u)
    for org_data in data['orgs']:
        mail_handled_by = org_data.get('outgoing_mail_handled_by', None)
        if mail_handled_by:
            org = Organization.objects.get(name=org_data['name'])
            mailer = Organization.objects.get(name=mail_handled_by)
            org.outgoing_mail_handled_by = mailer
            org.save()

    print "Building pdfs and users..."
    for user_data in data['users']:
        user, created = User.objects.get_or_create(
                username=slugify(user_data['name'])
        )
        if user_data.get('managed', False):
            random_mailing_address = "\n".join([
                # Prisoner number
                "#%s" % "".join(random.choice(string.digits) for a in range(8)),
                # Street
                "%s Cherry Tree Lane" % "".join(
                    random.choice(string.digits) for a in range(3)),
                # City, state, zip
                "City Name, %s  %s" % (
                    random.choice(US_STATES)[0],
                    "".join(random.choice(string.digits) for a in range(5)),
                )
            ])
        else:
            random_mailing_address = ""

        user.profile.display_name = user_data['name']
        user.profile.mailing_address = random_mailing_address
        user.profile.blogger = user_data.get('blogger', False)
        user.profile.managed = user_data.get('managed', False)
        user.profile.consent_form_received = user_data.get('consent_form_received', False)
        user.profile.blog_name = user_data.get('blog_name', None) or ''
        user.profile.save()

        for org_name in user_data['orgs']:
            orgs[org_name].members.add(user)

        for corresp in user_data['correspondence']:
            direction, content = corresp.items()[0]
            if direction == "received":
                # Build Scan
                pdf = build_pdf(content['parts'], user.profile) 
                path = tasks.move_scan_file(filename=pdf)
                scan = Scan.objects.create(
                        uploader=uploader,
                        org=orgs[org_name],
                        author=user,
                        pdf=os.path.relpath(path, settings.MEDIA_ROOT),
                        under_construction=True,
                        processing_complete=True,
                        created=content['date'])
                # execute synchronously
                tasks.split_scan(scan_id=scan.pk)
                # Build Documents
                page_count = 1 # ignore envelope
                for part in content['parts']:
                    page_count += part["pages"]
                    if part["type"] == "ignore":
                        continue
                    document = Document.objects.create(
                            scan=scan,
                            editor=uploader,
                            author=user,
                            type=part["type"],
                            date_written=content["date"],
                            created=content["date"],
                            title=part.get("title", None) or "",
                    )
                    for i, page_index in enumerate(
                            range(page_count - part["pages"], page_count)):
                        scanpage = scan.scanpage_set.get(order=page_index)
                        DocumentPage.objects.create(
                                document=document,
                                scan_page=scanpage,
                                order=i)
                    # execute synchronously
                    if part["type"] in ("profile", "post"):
                        document.status = "published"
                    else:
                        document.status = "unpublishable"
                    document.highlight_transform = '{"document_page_id": %s, "crop": [44.5, 58.66667175292969, 582.5, 288.6666717529297]}' % document.documentpage_set.all()[0].pk
                    document.save()
                    tasks.update_document_images(document.pk)
                    for comment in part.get('comments', []):
                        Comment.objects.create(
                                user=commenter,
                                comment="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec a diam lectus. Sed sit amet ipsum mauris. Maecenas congue ligula ac quam viverra nec consectetur ante hendrerit. Donec et mollis dolor. Praesent et diam eget libero egestas mattis sit amet vitae augue. Nam tincidunt congue enim, ut porta lorem lacinia consectetur. Donec ut libero sed arcu vehicula ultricies a non tortor. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean ut gravida lorem. Ut turpis felis, pulvinar a semper sed, adipiscing id dolor. Pellentesque auctor nisi id magna consequat sagittis.",
                                document=document,
                                created=comment['date'],
                        )
        # Finish received scans before parsing letters, to ensure comments/etc
        # are there yet.
        for corresp in user_data['correspondence']:
            direction, content = corresp.items()[0]
            if direction == "sent":
                letter = Letter(type=content['type'], 
                        auto_generated=True, 
                        sender=uploader,
                        created=content['date'],
                        sent=content['date'],
                        recipient=user,
                        org=Organization.objects.get(name=user_data['orgs'][0]))
                if content['type'] == "comments":
                    letter.save()
                    comments = Comment.objects.unmailed().filter(
                            document__author=user,
                            created__lt=content['date']
                    )
                    for comment in comments:
                        letter.comments.add(comment)
                elif content['type'] == "letter":
                    letter.body = content['body']
                letter.save()

class Command(BaseCommand):
    args = ''
    help = 'Import mock users and pages for testing and dev.'
    option_list = BaseCommand.option_list + (
        make_option('--noinput',
            action='store_true',
            dest='noinput',
            default=False,
            help="Proceed with destructive operations without prompt.",
        ),
    )

    def handle(self, *args, **options):
        if not options['noinput']:
            print "Warning: this will delete all data."
            response = raw_input("Proceed, and delete everything? (y/n): ")
            if response.lower() != "y":
                print "Action cancelled."
                return
        Organization.objects.all().delete()
        for scan in Scan.objects.all():
            scan.full_delete()
        for user in User.objects.exclude(pk=1).exclude(pk=100):
            user.delete()
        for letter in Letter.objects.all():
            letter.delete()
        for comment in Comment.objects.all():
            comment.delete()
        load_test_data()
