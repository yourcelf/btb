import os
import json
import shutil
import codecs
import zipfile
import datetime
import tempfile
import subprocess
from cStringIO import StringIO

from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, render, redirect
from django.template.defaultfilters import slugify
from django.http import HttpResponse, HttpResponseForbidden, Http404, HttpResponseBadRequest
from django.conf import settings
from django.db.models import Q, Count
from django.db import transaction

from comments.models import Comment, CommentRemoval
from correspondence.models import Letter, Mailing, StockResponse
from correspondence import utils, tasks
from profiles.models import Profile, Organization
from scanning.models import Scan, Document
from btb.utils import args_method_decorator, permission_required_or_deny, JSONView

class StockResponses(JSONView):
    @permission_required_or_deny("correspondence.manage_correspondence")
    def get(self, request):
        return self.json_response({
            'results': [s.to_dict() for s in StockResponse.objects.all()]
        })

class Letters(JSONView):
    """
    JSON CRUD for Letter models.
    """
    attr_whitelist = [
        'id', 'recipient_id', 'recipient', 'org_id', 
        'body', 'is_postcard', 'send_anonymously',
        'type', 'document_id', 'comments',
        'created', 'sent'
    ]
    def clean_params(self, request):
        """
        Parameters for put and post.
        """
        kw = json.loads(request.body)
        # TODO: Remove this at the client side.
        for key in ('order_date', 'org', 'document', 'recipient_address', 'sender'):
            kw.pop(key, None)
        self.whitelist_attrs(kw)
        kw['sender'] = request.user
        if kw.get('type', None) == 'waitlist':
            kw['is_postcard'] = True
        if 'recipient_id' in kw:
            kw['recipient'] = utils.mail_filter_or_404(
                    request.user, Profile, pk=kw.pop('recipient_id')
            ).user
        elif 'recipient' in kw:
            kw['recipient'] = utils.mail_filter_or_404(
                    request.user, Profile, pk=kw.pop('recipient')['id']
            ).user
        if 'recipient' not in kw:
            raise Http404
        if 'document_id' in kw:
            try:
                kw['document'] = Document.objects.org_filter(
                        request.user, pk=kw.pop('document_id')
                ).get()
            except Document.DoesNotExist:
                raise Http404
        if 'org_id' in kw:
            kw['org'] = utils.mail_filter_or_404(
                    request.user, Organization, pk=kw.pop('org_id')
            )
        else:
            raise Http404
        
        kw.pop('order_date', None) # added by CorrespondenceList
        for datefield in ('created', 'sent'):
            if datefield in kw:
                if kw[datefield] is None:
                    continue
                if kw[datefield] == True:
                    kw[datefield] = datetime.datetime.now()
                else:
                    kw[datefield] = kw[datefield].split(".")[0].replace('T', ' ')
                    kw[datefield] = datetime.datetime.strptime(kw[datefield], "%Y-%m-%d %H:%M:%S")
        return kw

    @permission_required_or_deny("correspondence.manage_correspondence")
    def get(self, request, letter_id=None):
        if letter_id:
            letter = utils.mail_filter_or_404(request.user, Letter, pk=letter_id)
            return self.json_response(letter.to_dict())

        letters = Letter.objects.mail_filter(request.user).filter(
                recipient__profile__lost_contact=False
             ).extra(
                select={
                    'date_order': 
                        'COALESCE("{0}"."sent", "{0}"."created")'.format(
                            Letter._meta.db_table
                        )

                },
                order_by=('-date_order',)
            ).distinct()
        if "sent" in request.GET:
            letters = letters.filter(sent__isnull=False)
        if "unsent" in request.GET:
            letters = letters.filter(sent__isnull=True)
        if "mailing_id" in request.GET:
            mid = request.GET.get("mailing_id")
            if mid == "null":
                letters = letters.filter(mailing__isnull=True)
            else:
                letters = letters.filter(mailing__pk=mid)
        if 'text' in request.GET:
            parts = [p.strip() for p in request.GET.get('text').split()]
            q = Q()
            for part in parts:
                q = q & (
                    Q(recipient__profile__display_name__icontains=part) | 
                    Q(recipient__profile__mailing_address__icontains=part) |
                    Q(body__icontains=part) |
                    Q(comments__comment__icontains=part)
                )
            letters = letters.filter(q)

        # Get counts by type first....
        counts = letters.values('type').annotate(
            count=Count('type')
        ).order_by()
        by_type = {
            'counts': dict((c['type'], c['count']) for c in counts)
        }
        # ... then filter by type, so the counts aren't affected by that.
        if 'types' in request.GET:
            types = request.GET.get('types').split(",")
            q = Q()
            for type_ in types:
                q = q | Q(type=type_)
            letters = letters.filter(q)

        return self.paginated_response(request, letters, 
                extra=by_type)

    @permission_required_or_deny("correspondence.manage_correspondence")
    def post(self, request, letter_id=None):
        kw = self.clean_params(request)
        comments = kw.pop('comments', [])
        letter = Letter(**kw)
        error = self.validate(letter)
        if error:
            return error
        else:
            letter.save()
            for comment in comments:
                letter.comments.add(Comment.objects.get(pk=comment['id']))
            return self.json_response(letter.to_dict())

    @permission_required_or_deny("correspondence.manage_correspondence")
    def put(self, request, letter_id=None):
        kw = self.clean_params(request)
        letter = utils.mail_filter_or_404(request.user, Letter, pk=kw['id'])
        comments = kw.pop('comments', [])
        for param, val in kw.iteritems():
            setattr(letter, param, val)
        error = self.validate(letter)
        if error:
            return error
        else:
            letter.save()
            letter.comments = [Comment.objects.mail_filter(request.user).get(pk=c['id']) for c in comments]
            return self.json_response(letter.to_dict())

    @permission_required_or_deny("correspondence.manage_correspondence")
    def delete(self, request, letter_id=None):
        letter = utils.mail_filter_or_404(request.user, Letter, pk=letter_id)
        letter.delete()
        return self.json_response(["success"])

    def validate(self, letter):
        if letter.type == "letter":
            try:
                letter.get_file()
            except utils.LatexCompileError as e:
                return HttpResponseBadRequest(e.message)
        return None

def date_to_str(date_or_str):
    try:
        return date_or_str.isoformat()
    except AttributeError:
        return date_or_str

class CorrespondenceList(JSONView):
    """
    This one combines scans and correspondence into a single response.  This is
    to facilitate a threaded view of the conversation with a particular user.
    """
    @permission_required_or_deny("correspondence.manage_correspondence")
    def get(self, request, user_id=None):
        scans = Scan.objects.mail_filter(request.user).order_by('-created')
        letters = Letter.objects.mail_filter(request.user)

        user_id = user_id or request.GET.get('user_id', None)
        try:
            incoming = bool(int(request.GET.get("incoming")))
        except ValueError:
            incoming = True
        try:
            outgoing = bool(int(request.GET.get("outgoing")))
        except ValueError:
            outgoing = True

        if not incoming and not outgoing:
            incoming = outgoing = True

        if user_id:
            if incoming:
                scans = scans.filter(author__id=user_id)
            else:
                scans = []
            if outgoing:
                letters = letters.filter(recipient__id=user_id)
            else:
                letters = []

        # Just grab all at once.  Number of letters/scans doesn't get so high
        # as to make it worth lazy fetching.
        all_correspondence = list(scans) + list(letters)
        all_correspondence.sort(
                key=lambda a: a.sent if hasattr(a, "sent") and a.sent else a.created,
                reverse=True)

        per_page = int(request.GET.get('per_page', 12))
        page_num = int(request.GET.get('page', 1))
        total_pages = int(len(all_correspondence) / per_page) + 1

        if per_page * (page_num - 1) > len(all_correspondence) or page_num < 1:
            page_num = 1

        sliced = all_correspondence[(page_num-1)*per_page : page_num*per_page]
        results = []
        for obj in sliced:
            as_dict = obj.to_dict()
            if isinstance(obj, Scan):
                as_dict['order_date'] = obj.created.isoformat()
                results.append({'scan': as_dict})
            else:
                as_dict['order_date'] = (obj.sent or obj.created).isoformat()
                results.append({'letter': as_dict})
        return self.json_response({
            'pagination': {
                'count': len(all_correspondence),
                'page': page_num,
                'pages': total_pages,
                'per_page': per_page,
            },
            'results': results
        })

class Mailings(JSONView):
    """
    JSON CRUD for Mailing models
    """
    def clean_params(self, request):
        kw = json.loads(request.body)
        if 'date_finished' in kw:
            if 'date_finished' in kw:
                if kw['date_finished'] == True:
                    kw['date_finished'] = datetime.datetime.now()
                elif kw['date_finished'] is not None:
                    kw['date_finished'] = kw['date_finished'].replace("T", " ")
        return kw

    @permission_required_or_deny("correspondence.manage_correspondence")
    def get(self, request, mailing_id=None):
        mailing_id = mailing_id or request.GET.get('mailing_id', None)
        if mailing_id is None:
            return self.get_list(request)
        mailing = utils.mail_filter_or_404(request.user, Mailing, pk=mailing_id)
        return self.json_response(mailing.to_dict())
    
    @permission_required_or_deny("correspondence.manage_correspondence")
    def get_list(self, request):
        mailings = Mailing.objects.mail_filter(request.user).extra(
                select={
                    "is_sent": "date_finished is NULL",
                    "order_date": '''COALESCE("{0}"."date_finished", "{0}"."created")'''.format(Mailing._meta.db_table),
                },
                order_by=['-is_sent', '-order_date']
        )
        if "finished" in request.GET:
            mailings = mailings.filter(date_finished__isnull=False)
        if "unfinished" in request.GET:
            mailings = mailings.filter(date_finished__isnull=True)
        if "editor_id" in request.GET:
            mailings = mailings.filter(editor__id=request.GET.get("editor"))
        return self.paginated_response(request, mailings, dict_method="light_dict")
    
    @permission_required_or_deny("correspondence.manage_correspondence")
    @args_method_decorator(transaction.atomic)
    def post(self, request, mailing_id=None):
        """
        Create a mailing, and autogenerated letters, reflecting the params given.
        """
        params = self.clean_params(request)
        if 'types' not in params:
            raise Http404

        mailing = Mailing.objects.create(editor=request.user)
        to_send = []
        types = set(params['types'])

        kw = {'auto_generated': True, 'sender': request.user}
        if "enqueued" in types:
            to_send += list(Letter.objects.unsent().mail_filter(request.user).filter(
                    recipient__profile__lost_contact=False,
                    mailing__isnull=True,
                    auto_generated=False
            ))
        if "waitlist" in types:
            to_send += list(Letter.objects.create(
                    recipient=p.user, type="waitlist", is_postcard=True, 
                    org=p.user.organization_set.get(), **kw 
                ) for p in Profile.objects.waitlistable().mail_filter(request.user).filter(
                    lost_contact=False
                ).distinct())
        if "consent_form" in types:
            cutoff = params.get("consent_cutoff", "") or datetime.datetime.now()
            to_send += list(Letter.objects.create(
                    recipient=p.user, type="consent_form",
                    org=p.user.organization_set.get(), **kw 
                ) for p in Profile.objects.invitable().mail_filter(request.user).filter(
                    user__date_joined__lte=cutoff,
                    lost_contact=False
                ).distinct())
        if "signup_complete" in types:
            to_send += list(Letter.objects.create(
                    recipient=p.user, type="signup_complete",
                    org=p.user.organization_set.get(), **kw 
                ) for p in Profile.objects.needs_signup_complete_letter().mail_filter(
                    request.user
                ).filter(lost_contact=False).distinct())
        if "first_post" in types:
            to_send += list(Letter.objects.create(
                    recipient=p.user, type="first_post",
                    org=p.user.organization_set.get(), **kw 
                ) for p in Profile.objects.needs_first_post_letter().mail_filter(request.user).filter(lost_contact=False).distinct())
        if "comments" in types:
            comments = list(Comment.objects.unmailed().mail_filter(request.user).filter(
                document__author__profile__lost_contact=False
            ).order_by(
                'document__author', 'document'
            ))
            author = None
            letter = None
            for c in comments:
                if c.document.author != author:
                    doc = c.document
                    author = c.document.author
                    letter = Letter.objects.create(recipient=c.document.author,
                            type="comments",
                            org=c.document.author.organization_set.get(),
                            **kw
                    )
                    to_send.append(letter)
                letter.comments.add(c)
        if "comment_removal" in types:
            removals = list(CommentRemoval.objects.needing_letters().mail_filter(request.user).filter(
                comment__document__author__profile__lost_contact=False
            ).order_by(
                'comment__document__author', 'comment__document'
            ))
            for removal in removals:
                letter = Letter.objects.create(
                    type="comment_removal",
                    recipient=removal.comment.document.author,
                    org=removal.comment.document.author.organization_set.get(),
                    body=removal.post_author_message,
                    send_anonymously=True,
                    **kw)
                letter.comments.add(removal.comment)
                to_send.append(letter)

        mailing.letters.add(*to_send)
        return self.json_response(mailing.light_dict())

    @permission_required_or_deny("correspondence.manage_correspondence")
    @args_method_decorator(transaction.atomic)
    def put(self, request, mailing_id=None):
        params = self.clean_params(request)
        mailing = get_object_or_404(Mailing, pk=mailing_id)
        if "date_finished" in params:
            mailing.date_finished = params['date_finished']
            mailing.save()
        return self.json_response(mailing.light_dict())
    
    @permission_required_or_deny("correspondence.manage_correspondence")
    @args_method_decorator(transaction.atomic)
    def delete(self, request, mailing_id=None):
        mailing = get_object_or_404(Mailing, pk=mailing_id)
        mailing.delete()
        return self.json_response("success")

def needed_letters(user, consent_form_cutoff=None):
    if consent_form_cutoff:
        consent_forms = Profile.objects.invitable().filter(
                user__date_joined__lte=consent_form_cutoff,
                lost_contact=False
            ).mail_filter(
                user
            ).distinct()
    else:
        consent_forms = Profile.objects.invitable().mail_filter(
                user
            ).distinct()
    return {
        "consent_form": consent_forms,
        "signup_complete": Profile.objects.needs_signup_complete_letter().mail_filter(
                user).filter(lost_contact=False).distinct(),
        "first_post": Profile.objects.needs_first_post_letter().mail_filter(
                user
            ).filter(lost_contact=False).distinct(),
        "comments": Profile.objects.needs_comments_letter().mail_filter(
                user
            ).filter(lost_contact=False).distinct(),
        "waitlist": Profile.objects.waitlistable().mail_filter(
                user
            ).filter(lost_contact=False).distinct(),
        "enqueued": Letter.objects.mail_filter(user).filter(
                sent__isnull=True,
                recipient__profile__lost_contact=False,
            ).exclude(mailing__isnull=False),
        "comment_removal": CommentRemoval.objects.needing_letters().filter(
                comment__document__author__profile__lost_contact=False
            ).distinct(),
    }

class NeededLetters(JSONView):
    @permission_required_or_deny("correspondence.manage_correspondence")
    def get(self, request):
        """
        Return a JSON struct representing counts of the as-yet-ungenerated
        automatic letters.  Excludes any letters that have been created, and are
        part of a mailing.
        """
        needed = needed_letters(
               request.user,
               request.GET.get('consent_form_cutoff', None)
           )
        counts = dict((k, v.count()) for k,v in needed.items())
        return self.json_response(counts)

@permission_required("correspondence.manage_correspondence")
@transaction.atomic
def clear_mailing_cache(request, mailing_id):
    mailing = utils.mail_filter_or_404(request.user, Mailing, pk=mailing_id)
    if mailing.file and os.path.exists(mailing.file.path):
        os.remove(mailing.file.path)
    mailing.file = ""
    mailing.save()
    for letter in mailing.letters.all():
        if letter.file and os.path.exists(letter.file.path):
            os.remove(letter.file.path)
        letter.file = ""
        letter.save()
    return HttpResponse("success")

@permission_required("correspondence.manage_correspondence")
def get_mailing_file(request, mailing_id):
    mailing = utils.mail_filter_or_404(request.user, Mailing, pk=mailing_id)
    if mailing.has_file():
        response = HttpResponse(content_type='application/zip')
        filename = mailing.get_file()

        # Compile special instructions
        special_instructions = []
        for letter in mailing.letters.all():
            if letter.recipient and letter.recipient.profile.special_mail_handling:
                special_instructions.append(letter.recipient.profile)
        if special_instructions:
            # Add/replace special instructions manifest.
            tmpdir = tempfile.mkdtemp()
            subdir = os.path.join(tmpdir, os.path.splitext(os.path.basename(filename))[0])
            os.makedirs(subdir)
            instructions_path = os.path.join(tmpdir, os.path.splitext(os.path.basename(filename))[0], 
                    "special_instructions.csv")
            rows = [["Name", "Address", "Special instructions"]]
            for profile in special_instructions:
                rows.append([
                    profile.display_name,
                    profile.mailing_address,
                    profile.special_mail_handling,
                ])
            utils.write_csv(rows, instructions_path)
            proc = subprocess.Popen(["zip", 
                os.path.splitext(filename)[0], 
                os.path.relpath(instructions_path, tmpdir),
            ], cwd=tmpdir)
            proc.communicate()
            shutil.rmtree(tmpdir)
        else:
            # No special instructions: remove them.
            proc = subprocess.Popen(["zip", "-d",
                filename,
                os.path.splitext(os.path.basename(filename))[0] + "/special_instructions.csv"
            ])
            proc.communicate()

        if settings.X_SENDFILE_ENABLED: # Apache
            response['X-Sendfile'] = filename
        elif settings.X_ACCEL_REDIRECT_ENABLED: # Nginx
            response['X-Accel-Redirect'] = "/private_media_serve/{}".format(
                    os.path.relpath(filename, settings.MEDIA_ROOT))
            del response['Content-Type']
        else:
            with open(mailing.get_file()) as fh:
                response.write(fh.read())
        response['Content-Disposition'] = 'attachment; filename={0}'.format(
            os.path.basename(mailing.get_file())
        )
        return response
    task_id = tasks.generate_collation_task.delay(mailing.pk, request.path)
    return redirect("moderation.wait_for_processing", task_id)

@permission_required('correspondence.manage_correspondence')
def print_envelope(request, user_id=None, reverse=None, address=None):
    if user_id:
        user = utils.mail_filter_or_404(request.user, Profile, pk=user_id).user
        to_address = user.profile.full_address()
    else:
        to_address = request.GET.get('address', address)
    if not to_address:
        raise Http404
    from_address = user.organization_set.get().mailing_address
    if reverse:
        from_address, to_address = to_address, from_address

    stringio = utils.build_envelope(to_address=to_address, from_address=from_address)
    response = HttpResponse(content_type='image/jpeg')
    response.write(stringio.getvalue())
    response['Content-Disposition'] = 'attachment; filename=%s-envelope.jpg' % \
            slugify(to_address.split('\n')[0])
    return response

@permission_required('correspondence.manage_correspondence')
def print_envelopes(request):
    if request.GET.get("ids"):
        try:
            ids = [int(i) for i in request.GET.get("ids").split(",")]
        except Exception:
            return HttpResponse("Error parsing ids parameter")
    else:
        return HttpResponse("Try adding 'ids' parameter")
    profiles = Profile.objects.select_related('user').in_bulk(ids)
    missing = []
    for pk in ids:
        if pk not in profiles:
            missing.append(pk)
    if missing:
        return HttpResponse("Can't find result for ids: %s" % missing)
    envelopes = []
    # NOTE: inefficient -- n+1 queries. Could be improved but not worth it for
    # the small expected query size.
    for pk, profile in profiles.iteritems():
        envelopes.append((utils.build_envelope(
            to_address=profile.full_address(),
            from_address=profile.user.organization_set.get().mailing_address
        ), "%s.jpg" % profile.get_blog_slug()))
    zipname = "envelopes-%s" % (datetime.datetime.now().strftime("%Y-%m-%d"))

    # Do it all in memory for fun and profit.
    zip_stringio = StringIO()
    zip_builder = zipfile.ZipFile(zip_stringio, "w")
    for jpeg, name in envelopes:
        zip_builder.writestr("%s/%s" % (zipname, name), jpeg.getvalue())
    zip_builder.close()
    response = HttpResponse(content_type='application/zip')
    response.write(zip_stringio.getvalue())
    response['Content-Disposition'] = 'attachment; filename=%s.zip' % zipname
    return response

@permission_required("correspondence.manage_correspondence")
def preview_letter(request):
    if request.method == "POST":
        letter = Letter.objects.create(
            type="letter",
            recipient=utils.mail_filter_or_404(request.user, Profile, pk=request.POST.get("recipient_id")).user,
            org=utils.mail_filter_or_404(request.user, Organization, pk=request.POST.get("org_id")),
            body=request.POST.get("body"),
            sender=request.user,
            send_anonymously=not request.POST.get("signed"),
            sent=datetime.datetime.now()
        )
        response = show_letter(request, letter.pk)
        letter.delete()
        return response
    return HttpResponseBadRequest("POST required")

@permission_required("correspondence.manage_correspondence")
def comment_removal_letter_preview_frame(request, comment_id):
    comment = utils.mail_filter_or_404(request.user, Comment, pk=comment_id)
    recipient = comment.document.author
    org = comment.document.author.organization_set.get()
    error = None
    if request.method == "POST":
        letter = Letter.objects.create(
            type="comment_removal",
            recipient=recipient,
            org=org,
            body=request.POST.get("body"),
            sender=request.user,
            send_anonymously=True,
            sent=datetime.datetime.now()
        )
        letter.comments.add(comment)
        response = None
        try:
            response = show_letter(request, letter.pk)
        except utils.LatexCompileError as e:
            error = e
        finally:
            letter.delete()
        if response:
            return response
    return render(request, "correspondence/comment_removal_letter_preview_frame.html", {
        'comment': comment,
        'recipient': recipient,
        'org': org,
        'error': error,
    })

        

@permission_required("correspondence.manage_correspondence")
def show_letter(request, letter_id=None):
    letter = utils.mail_filter_or_404(request.user, Letter, pk=letter_id)
    # Run this as an out-of-process task because WSGI borks on the subprocess
    # invocation for pdftk. http://stackoverflow.com/questions/7543452/
    filename = tasks.generate_letter_task.delay(letter_id=letter_id).get()
    basename, ext = os.path.splitext(filename)
    if ext == ".pdf":
        content_type = 'application/pdf'
    elif ext == ".jpg":
        content_type = 'image/jpeg'
    else:
        raise NotImplementedError("Unknown extention {0}".format(ext))

    response = HttpResponse(content_type=content_type)
    response['Content-Disposition'] = 'attachment; filename=%s-%s.%s' % (
            slugify(letter.recipient.profile.display_name), 
            letter.type,
            ext
    )
    with open(filename) as fh:
        response.write(fh.read())
    return response

# Allow local requests from wkhtmltopdf without authentication, but require
# permission otherwise
def recent_comments_letter(request, letter_id=None, pdf=None):
    if not (request.META['REMOTE_ADDR'] in settings.INTERNAL_IPS or 
            request.user.has_perm('correspondence.manage_correspondence')):
        return HttpResponseForbidden(request.META['REMOTE_ADDR'])

    # NB: we're trusting localhost with full access to comment letters here,
    # unfiltered.
    letter = get_object_or_404(
            Letter.objects.select_related('document', 'recipient'),
            pk=letter_id)
    if letter.type != "comments":
        raise Http404
    # ignore comments by the letter recipient.  This happens when writers reply
    # using a Reply ID to comments left on their letters.
    comments = list(letter.sorted_comments().exclude(user=letter.recipient))
    if len(comments) == 0:
        raise Http404

    # Hide moderator login stuff.
    orig_request_user = request.user
    request.user = AnonymousUser()
    response = render(request, "correspondence/show_commentmailing.html", {
        'letter': letter,
        'comments': comments,
    })
    request.user = orig_request_user
    return response

@permission_required("correspondence.manage_correspondence")
def mass_mailing_spreadsheet(request, who=None):
    """ 
    Return a spreadsheet with one line per address for all users of a given
    type.
    """
    if not who:
        orgs = Organization.objects.mail_filter(request.user)
        return render(request, "correspondence/mass_mailing_spreadsheet.html",
                {'orgs': orgs})

    if who == "bloggers":
        qs = Profile.objects.bloggers()
    elif who == "bloggers_with_published_content":
        qs = Profile.objects.bloggers_with_published_content()
    elif who == "enrolled":
        qs = Profile.objects.enrolled()
    elif who == "invitable":
        qs = Profile.objects.invitable()
    elif who == "invited":
        qs = Profile.objects.invited()
    elif who == "waitlistable":
        qs = Profile.objects.waitlistable()
    elif who == "waitlisted":
        qs = Profile.objects.waitlisted()
    elif who == "needs_signup_complete_letter":
        qs = Profile.objects.needs_signup_complete_letter()
    elif who == "needs_first_post_letter":
        qs = Profile.objects.needs_first_post_letter()
    elif who == "needs_comments_letter":
        qs = Profile.objects.needs_comments_letter()
    elif who == "lost_contact":
        qs = Profile.objects.filter(lost_contact=True)

    if who != "lost_contact":
        qs = qs.filter(lost_contact=False)

    qs = qs.mail_filter(request.user)

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as fh:
        fname = fh.name
    utils.write_address_csv([p.full_address() for p in qs], fname)

    response = HttpResponse(content_type='text/csv')
    with open(fname) as fh:
        response.write(fh.read())
    os.remove(fname)
    response['Content-Disposition'] = 'attachment; filename=%s-%s.csv' % (
        who, datetime.datetime.now().strftime("%Y-%m-%d")
    )
    return response

@permission_required("correspondence.manage_correspondence")
def mailing_label_sheet(request):
    if request.GET.get("ids"):
        try:
            ids = [int(i) for i in request.GET.get("ids").split(",")]
        except Exception:
            return HttpResponse("Error parsing ids parameter")
    else:
        return HttpResponse("Try adding 'ids' parameter")
    
    profiles = Profile.objects.in_bulk(ids)
    missing = []
    pages = []
    for i, id_ in enumerate(ids):
        if i % 30 == 0:
            page = []
            pages.append(page)
        if id_ in profiles:
            page.append(profiles[id_])
        else:
            missing.append(id_)
    if missing:
        return HttpResponse("Can't find result for ids: %s" % missing)

    pdf_files = []
    for page in pages:
        labels = utils.MailingLabelSheet()
        addresses = [p.full_address() for p in page]
        labels.draw(addresses)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as fh:
            jpg_name = fh.name
        labels.save(jpg_name)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as fh:
            pdf_name = fh.name
        proc = subprocess.Popen([
            settings.CONVERT_CMD,
            jpg_name,
            "-density", str(labels.density),
            pdf_name])
        proc.communicate()
        os.remove(jpg_name)
        pdf_files.append(pdf_name)
    combined = tasks.combine_pdfs_task.delay(pdf_files).get()
    for filename in pdf_files:
        os.remove(filename)
    response = HttpResponse(content_type='application/pdf')
    with open(combined, 'rb') as fh:
        response.write(fh.read())
    response['Content-Disposition'] = 'attachment; filename=labels.pdf'
    os.remove(combined)
    return response



