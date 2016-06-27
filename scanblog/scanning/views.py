import json
import datetime
import tempfile
import logging
logger = logging.getLogger("django.request")

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q, Prefetch
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.translation import ugettext as _
from django.http import Http404, HttpResponseBadRequest
from django.contrib.auth.views import logout
from celery.result import AsyncResult
from scanblog.celery import app

from btb.utils import args_method_decorator, permission_required_or_deny, JSONView

from scanning import utils, tasks
from scanning.models import *
from scanning.forms import LockForm, TranscriptionForm, ScanUploadForm, \
        FlagForm, get_org_upload_form
from annotations.models import Tag, Note, ReplyCode, handle_flag_spam
from annotations.tasks import send_flag_notification_email
from profiles.models import Organization, Profile, Affiliation
from comments.forms import CommentForm

def get_boolean(val):
    return bool(val == "true" or val == "1")

class Scans(JSONView):
    @permission_required_or_deny("scanning.change_scan")
    def get(self, request, obj_id=None):
        if obj_id:
            scans = Scan.objects.filter(pk=obj_id)
        else:
            scans = Scan.objects.all().order_by('-created')
            if request.GET.get("processing_complete"):
                scans = scans.filter(
                        processing_complete=
                            get_boolean(request.GET.get("processing_complete"))
                )
            if request.GET.get("managed"):
                try:
                    managed = bool(int(request.GET.get('managed')))
                except ValueError:
                    managed = False
                if managed:
                    scans = scans.filter(
                            Q(author__isnull=True) |
                            Q(author__profile__managed=True)
                    )
                else:
                    scans = scans.filter(author__profile__managed=False)
            if request.GET.get("editlock__isnull"):
                scans = scans.filter(
                        editlock__isnull=
                            get_boolean(request.GET.get("editlock__isnull"))
                )

        # A scan can be valid two ways: 1 -- the author is in the moderator's
        # orgs.  2 -- the scan's selected org is one of the author's orgs.
        # Hence the "extra_q".
        scans = scans.org_filter(request.user)
        return self.paginated_response(request, scans)

class ScanSplits(JSONView):
    """
    {
        "scan": scan
        "documents": [{
            "id": document id
            "type": type
            "title": title or ""
            "pages": [id,id,id,...]
        }]
    }
    """
    def clean_params(self, request):
        kw = json.loads(request.body)
        return kw

    @permission_required_or_deny("scanning.change_scan")
    def get(self, request, obj_id=None):
        try:
            scan = Scan.objects.org_filter(request.user, pk=obj_id).get()
        except Scan.DoesNotExist:
            raise PermissionDenied

        try:
            lock = EditLock.objects.get(scan__pk=scan.pk)
            if lock.user == request.user:
                lock.save()
        except EditLock.DoesNotExist:
            lock = EditLock.objects.create(user=request.user, scan=scan)
            tasks.expire_editlock.apply_async(args=[lock.id], countdown=60*5)

        split = {
            "scan": scan.to_dict(),
            "documents": [],
            "lock": lock.to_dict() if lock.user_id != request.user.id else None
        }

        # This will select a duplicate document for each scan page it contains.
        documents = Document.objects.order_by(
            'documentpage__scan_page__order'
        ).distinct().filter(scan__pk=scan.pk)

        # Since we got duplicates, filter them down here.
        visited = set()
        for doc in documents:
            if doc.id in visited:
                continue
            visited.add(doc.id)
            split['documents'].append({
                "id": doc.pk,
                "type": doc.type,
                "title": doc.title,
                "status": doc.status,
                "pages": list(doc.documentpage_set.order_by("order").values_list("scan_page__pk", flat=True))
            })
        return self.json_response(split)

    @permission_required_or_deny("scanning.change_scan", "scanning.add_document",
            "scanning.change_document", "scanning.delete_document")
    def post(self, request, obj_id=None):
        """
        Execute splits for a scan.  This could be updating an existing models,
        or creating new ones.
        """
        logger.debug("Starting split")
        with transaction.atomic():
            try:
                scan = Scan.objects.org_filter(request.user, pk=obj_id).get()
            except Scan.DoesNotExist:
                raise PermissionDenied
            params = self.clean_params(request)

            #
            # Save scan.
            #
            try:
                scan.author = Profile.objects.org_filter(request.user,
                    pk=params["scan"]["author"]["id"]
                ).get().user
                scan.processing_complete = params["scan"]["processing_complete"]
            except (KeyError, TypeError, Profile.DoesNotExist):
                # Processing complete is always False if there is no author; hence
                # two cases in the try block.
                scan.author = None
                scan.processing_complete = False
            scan.save()

            # Set pending scan.
            ps_code = (params['scan'].pop("pendingscan_code", None) or "").strip()
            try:
                has_ps = bool(scan.pendingscan)
            except PendingScan.DoesNotExist:
                has_ps = False
            if not ps_code and has_ps:
                # Remove the cached pendingscan reference. Ugh.  (simply setting
                # scan.pendingscan to None raises an error)
                ps = scan.pendingscan
                ps.scan = None
                ps.completed = None
                ps.save()
                scan = Scan.objects.get(pk=scan.pk)
            elif ps_code:
                try:
                    ps = PendingScan.objects.org_filter(
                            request.user, code=ps_code.strip()
                    ).get()
                except PendingScan.DoesNotExist:
                    pass
                else:
                    if ps.scan_id != scan.id:
                        ps.scan = scan
                        ps.completed = datetime.datetime.now()
                        ps.save()

            #
            # Split documents
            #

            docs = []
            for doc in params["documents"]:
                if ("pages" not in doc) or (len(doc["pages"]) == 0):
                    # Delete stale document.
                    if "id" in doc:
                        try:
                            Document.objects.org_filter(
                                request.user, pk=doc["id"]
                            ).get().full_delete()
                        except Document.DoesNotExist:
                            pass
                    continue
                if "id" in doc:
                    # Retrieve existing document.
                    try:
                        document = Document.objects.org_filter(
                                request.user, pk=doc["id"]
                        ).get()
                    except Document.DoesNotExist:
                        raise PermissionDenied

                else:
                    # Create new document.
                    if doc["type"] in ("request", "license"):
                        status = "unpublishable"
                    else:
                        status = "unknown"
                    document = Document.objects.create(
                            scan=scan,
                            editor=request.user,
                            author=scan.author,
                            type=doc["type"],
                            status=status,
                    )
                    # Create tickets
                    if doc["type"] == "request":
                        Note.objects.create(
                            text="Request from scan.",
                            document=document,
                            resolved=None,
                            creator=request.user,
                        )
                    elif doc["type"] == "license" and \
                            not document.author.profile.consent_form_received:
                        Note.objects.create(
                            text="Please check this license agreement, then update the user's license status accordingly.",
                            document=document,
                            resolved=None,
                            creator=request.user,
                        )

                # Apportion pages.
                pages = []
                # We need to transfer old page transforms to new document pages,
                # indexed by the scanpage_id, which persists.
                old_page_transformations = {}
                # ... and do the same for highlight_transform -- we need to change
                # the documentpage_id to the new documentpage_id.
                if document.highlight_transform:
                    old_highlight_transform = json.loads(document.highlight_transform)
                else:
                    old_highlight_transform = ""
                highlight_scan_page_id = None

                # Loop through current pages to get info to transfer to new pages,
                # and delete the old pages.
                for page in document.documentpage_set.all():
                    old_page_transformations[page.scan_page_id] = page.transformations

                    # Capture the old highlight transform's scan page ID.
                    if old_highlight_transform and \
                            page.pk == old_highlight_transform["document_page_id"]:
                        highlight_scan_page_id = page.scan_page_id

                    page.full_delete()

                # Clear the highlight transform so that it remains 'valid' even if
                # something goes wrong in identifying it with an old scan_page_id.
                document.highlight_transform = ""
                # Recreate the new pages, reusing the old transforms.
                for order,scanpage_id in enumerate(doc["pages"]):
                    documentpage = DocumentPage.objects.create(
                        document=document,
                        scan_page=ScanPage.objects.get(pk=scanpage_id),
                        order=order,
                        transformations=old_page_transformations.get(scanpage_id, "{}"),
                    )
                    # Reuse the old highlight transform, if it matches.
                    if scanpage_id == highlight_scan_page_id:
                        old_highlight_transform["document_page_id"] = documentpage.pk
                        document.highlight_transform = json.dumps(old_highlight_transform)
                document.save()
                document.documentpage_set = pages
                docs.append(document)
            scan.document_set = docs
        # Must do update_document_images outside transaction.atomic
        for document in docs:
            if document.status in ("published", "ready"):
                # Persist any changes to highlight_transform.
                tasks.update_document_images.delay(document.pk).get()
        #XXX Shouldn't be necessary but seems to be.
        scan.save()
        return self.get(request, obj_id=scan.pk)

class MissingHighlight(Exception):
    pass

class Documents(JSONView):
    def clean_params(self, request):
        kw = json.loads(request.body)
        return kw

    @permission_required_or_deny("scanning.change_document")
    def get(self, request, obj_id=None):
        docs = Document.objects.org_filter(request.user)
        g = request.GET.get
        if g("author__profile__managed", 0) == "1":
            docs = docs.filter(author__profile__managed=True)
        if g("author_id", None):
            docs = docs.filter(author__pk=g("author_id"))
        if g("type", None):
            docs = docs.filter(type=g("type"))
        if g("idlist", None):
            ids = [a for a in g("idlist").split(".") if a]
            if not ids:
                raise Http404
            docs = [b for a,b in sorted(docs.in_bulk(ids).items())]
        if g("status", None):
            docs = docs.filter(status=g("status"))
        #TODO: EditLock's for documents.
        return self.paginated_response(request, docs)

    @permission_required_or_deny("scanning.change_document")
    def put(self, request, obj_id=None):
        try:
            with transaction.atomic():
                try:
                    doc = Document.objects.org_filter(request.user, pk=obj_id).get()
                except Document.DoesNotExist:
                    raise PermissionDenied
                kw = self.clean_params(request)
                try:
                    doc.author = Profile.objects.org_filter(
                        request.user,
                        pk=kw['author']['id']
                    ).get().user
                except Profile.DoesNotExist:
                    raise PermissionDenied
                doc.editor = request.user
                doc.title = kw['title']
                if doc.type == "post":
                    try:
                        assert len(kw['highlight_transform']['crop']) > 0
                    except (AssertionError, KeyError):
                        raise MissingHighlight
                doc.highlight_transform = json.dumps(kw['highlight_transform'])

                if not kw['in_reply_to']:
                    doc.in_reply_to = None
                else:
                    reply_code = ReplyCode.objects.get(code__iexact=kw['in_reply_to'])
                    # Avoid recursion.
                    if reply_code.pk != doc.reply_code.pk:
                        doc.in_reply_to = reply_code
                    else:
                        doc.in_reply_to = None

                # Set affiliation, if any
                try:
                    doc.affiliation = Affiliation.objects.org_filter(request.user).get(
                            pk=kw['affiliation']['id'])
                except (TypeError, KeyError, Affiliation.DoesNotExist):
                    doc.affiliation = None

                doc.adult = kw['adult']
                # Ensure other processes won't try to serve this until we're done building.
                doc.date_written = kw['date_written']
                doc.status = "unknown"
                doc.save()

                # tags
                tags = []
                for name in kw['tags'].split(';'):
                    name = name.strip()
                    if name:
                        tag, created = Tag.objects.get_or_create(name=name.strip().lower())
                        tags.append(tag)
                doc.tags = tags

                # pages
                order_changed = []
                for page in kw['pages']:
                    docpage = doc.documentpage_set.get(pk=page['id'])
                    transformations = json.dumps(page['transformations'] or "")
                    if docpage.transformations != transformations:
                        docpage.transformations = transformations
                        docpage.save()
                    if page['order'] != docpage.order:
                        # Save a nonsensical order to avoid constraint clash, set
                        # correct order, but don't save until we're all done.
                        docpage.order = -docpage.order - 1
                        docpage.save()
                        docpage.order = page['order']
                        order_changed.append(docpage)

                for page in order_changed:
                    page.save()
        except MissingHighlight:
            return HttpResponseBadRequest("Missing highlight.")

	#XXX this additional save should not be needed, but seems to be. Issue
        # with transaction.atomic() ?
	doc.save()

        # Split images.
        result = tasks.update_document_images.delay(
                    document_id=doc.pk, status=kw['status']).get()

        logger.debug(u"post image update {}".format(doc.highlight_transform))

        # Update to get current status after task finishes.
        doc = Document.objects.get(pk=doc.pk)

        response = self.json_response(doc.to_dict())
        return response

#
# Pending scan CRUD
#

class PendingScans(JSONView):
    @permission_required_or_deny("scanning.change_pendingscan")
    def get(self, request, obj_id=None):
        if obj_id:
            pendingscans = PendingScan.objects.filter(pk=obj_id)
        elif "missing" in request.GET:
            pendingscans = PendingScan.objects.missing()
        elif "pending" in request.GET:
            pendingscans = PendingScan.objects.pending()
        elif "fulfilled" in request.GET:
            pendingscans = PendingScan.objects.fulfilled()
        else:
            pendingscans = PendingScan.objects.all()
        if "author_id" in request.GET:
            pendingscans = pendingscans.filter(author__pk=request.GET["author_id"])
        pendingscans = pendingscans.org_filter(request.user)
        return self.paginated_response(request, pendingscans)

    @permission_required_or_deny("scanning.add_pendingscan")
    def post(self, request, obj_id=None):
        params = json.loads(request.body)
        try:
            org = Organization.objects.org_filter(
                    request.user, pk=params["org_id"]
            ).get()
        except Organization.DoesNotExist:
            raise PermissionDenied
        try:
            author = Profile.objects.org_filter(
                    request.user, pk=params["author_id"]
            ).get().user
        except Profile.DoesNotExist:
            raise PermissionDenied

        pendingscan = PendingScan.objects.create(
            editor=self.request.user,
            author=author,
            org=org,
        )
        return self.json_response(pendingscan.to_dict())

    @permission_required_or_deny("scanning.change_pendingscan")
    def put(self, request, obj_id=None):
        try:
            ps = PendingScan.objects.org_filter(
                    request.user, pk=obj_id
            ).get()
        except PendingScan.DoesNotExist:
            raise PermissionDenied

        params = json.loads(request.body)
        if 'missing' in params:
            if params['missing'] == 1:
                ps.completed = datetime.datetime.now()
            else:
                ps.completed = None
            ps.save()
        return self.json_response(ps.to_dict())

    @permission_required_or_deny("scanning.delete_scan")
    def delete(self, request, obj_id=None):
        try:
            ps = PendingScan.objects.org_filter(
                    request.user, pk=obj_id
            ).get()
        except PendingScan.DoesNotExist:
            raise PermissionDenied
        ps.delete()
        return self.json_response(ps.to_dict())

class ScanCodes(JSONView):
    def get(self, request):
        if "term" not in request.GET:
            raise Http404

        pss = PendingScan.objects.org_filter(
                request.user,
                code__icontains=request.GET.get("term"),
                scan__isnull=True,
        )
        return self.json_response([ps.to_dict() for ps in pss])

@permission_required("scanning.add_scan")
def scan_add(request):
    """Displays a form for uploading a scan."""
    FormClass = get_org_upload_form(request.user)
    form = FormClass(request.POST or None, request.FILES or None, types={
        "pdf": "application/pdf",
        "zip": "application/zip",
    })
    if form.is_valid():
        if request.FILES['file'].name.lower().endswith(".zip"):
            with tempfile.NamedTemporaryFile(delete=False, suffix="scans.zip") as fh:
                for chunk in request.FILES['file'].chunks():
                    fh.write(chunk)
                fh.flush()
                task_id = tasks.process_zip.delay(filename=fh.name,
                        uploader_id=request.user.pk,
                        org_id=form.cleaned_data['organization'].pk,
                        redirect=reverse("moderation.home")
                )
        else:
            path = tasks.move_scan_file(uploaded_file=request.FILES['file'])
            scan = Scan.objects.create(
                uploader=request.user,
                pdf=os.path.relpath(path, settings.MEDIA_ROOT),
                under_construction=True,
                org=form.cleaned_data['organization'])
            task_id = tasks.split_scan.delay(scan_id=scan.pk,
                    redirect=reverse("moderation.edit_scan", args=[scan.pk]))
        return redirect('moderation.wait_for_processing', task_id)
    return render(request, "scanning/upload.html", {'form': form})

@permission_required("scanning.change_scan")
def scan_merge(request, scan_id):
    """ Merge an existing scan with a new file """
    try:
        scan = Scan.objects.org_filter(request.user, pk=scan_id).get()
    except Scan.DoesNotExist:
        raise Http404
    form = ScanUploadForm(request.POST or None, request.FILES or None, types={
        'pdf': 'application/pdf',
    })
    if form.is_valid():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as fh:
            for chunk in request.FILES['file'].chunks():
                fh.write(chunk)
            name = fh.name
        task_id = tasks.merge_scans.delay(
                scan_id=scan_id,
                filename=name,
                redirect=reverse("moderation.edit_scan", args=[scan.pk])
            )
        return redirect("moderation.wait_for_processing", task_id)
    return render(request, "scanning/merge.html", {'form': form})

@permission_required("scanning.change_scan")
def scan_replace(request, scan_id=None):
    try:
        scan = Scan.objects.org_filter(request.user, pk=scan_id).get()
    except Scan.DoesNotExist:
        raise PermissionDenied
    form = ScanUploadForm(request.POST or None, request.FILES or None, types={
        "pdf": "application/pdf",
    })
    if form.is_valid():
        filepath = tasks.move_scan_file(uploaded_file=request.FILES['file'])
        scan.full_delete(filesonly=True)
        scan.uploader = request.user
        scan.pdf = os.path.relpath(filepath, settings.MEDIA_ROOT)
        scan.save()

        task_id = tasks.split_scan.delay(
            scan_id=scan.pk,
            redirect=reverse("moderation.edit_scan", args=[scan.pk])
        )
        return redirect('moderation.wait_for_processing', task_id)
    return render(request, "scanning/replace.html", {'form': form})

@permission_required("scanning.delete_scan")
def scan_delete(request, scan_id=None):
    try:
        scan = Scan.objects.org_filter(request.user, pk=scan_id).get()
    except Scan.DoesNotExist:
        raise PermissionDenied
    if request.method != "POST":
        return render(request, "scanning/delete.html", {
            'scan': scan
        })
    scan.full_delete()
    messages.info(request, "Scan deleted.")
    return redirect(reverse("moderation.home") + "#/process")

@permission_required("scanning.delete_document")
def doc_delete(request, document_id=None):
    try:
        doc = Document.objects.org_filter(request.user, pk=document_id).get()
    except Document.DoesNotExist:
        raise PermissionDenied
    if request.method != 'POST':
        return redirect(reverse("moderation.edit_doc", document_id))
    doc.full_delete()
    messages.info(request, "Document deleted.")
    return redirect(reverse("moderation.home") + "#/process")


@permission_required('scanning.change_scan')
def scan_reimport(request, scan_id=None):
    try:
        scan = Scan.objects.org_filter(request.user, pk=scan_id).get()
    except Scan.DoesNotExist:
        raise PermissionDenied
    if request.method != "POST":
        return render(request, "scanning/reimport.html", {
            'scan': scan
        })
    task_id = tasks.process_scan.delay(
            scan_id=scan_id,
            redirect=reverse("moderation.home") + \
                    "#/process/scan/%s" % scan.id
    ).task_id
    return redirect("moderation.wait_for_processing", task_id)

@permission_required('scanning.change_scan')
def recent_scans(request):
    scans = Scan.objects.org_filter(
        request.user
    ).order_by('-created')[0:100]
    scan_ids = [s.id for s in scans]

    scan_pages = ScanPage.objects.filter(
        scan_id__in=scan_ids
    ).select_related(
        'scan', 'scan__author', 'scan__author__profile'
    ).order_by(
        '-scan__source_id',
        'scan',
        'order',
    ).prefetch_related(
        Prefetch('documentpage_set',
            queryset=DocumentPage.objects.select_related('document'))
    )

    items = []
    cur_scan = None
    cur_scan_count = 0
    cur_is_first = False
    for scan_page in scan_pages:
        if scan_page.scan != cur_scan:
            cur_scan = scan_page.scan
            cur_scan_count = 1
            cur_is_first = True
        else:
            cur_scan_count += 1
            cur_is_first = False
        if cur_scan_count > 15:
            items[-1]['has_more'] = True
            continue
        document_pages = scan_page.documentpage_set.all()
        documents = {}
        for doc_page in document_pages:
            documents[doc_page.document.id] = doc_page.document

        items.append({
            'first': cur_is_first,
            'scan': scan_page.scan,
            'page': scan_page,
            'documents': list(documents.values())
        })

    return render(request, "scanning/recent_scans.html", {
        'items': items
    })

#
# Transcriptions
#

@permission_required('scanning.change_transcription')
def transcribe_document(request, document_id):
    """Show and process the form for editing a transcription."""
    if not settings.TRANSCRIPTION_OPEN:
        raise Http404
    document = get_object_or_404(Document, pk=document_id)
    if not document.scan_id:
        raise Http404
    can_lock = request.user.has_perm('scanning.change_locked_transcription')

    try:
        transcription = document.transcription
    except Transcription.DoesNotExist:
        transcription = Transcription(document=document)
    if transcription.locked and not can_lock:
        raise PermissionDenied

    if can_lock:
        lockform = LockForm(request.POST or None)
    else:
        lockform = ''
    current = transcription.current()
    if current:
        initial = {'body': current.body, 'complete': transcription.complete}
    else:
        initial = None

    form = TranscriptionForm(request.POST or None, initial=initial)
    if form.is_valid():
        if lockform and lockform.is_valid():
            transcription.locked = lockform.cleaned_data['lock_transcription']
            transcription.save()

        # "sugar" is a honeypot for spam
        if form.has_changed() and not request.POST.get("sugar", None):
            # Don't add a revision for rapid changes.
            cutoff = datetime.datetime.now() - datetime.timedelta(seconds=120)
            transcription.complete = form.cleaned_data.get('complete', False)
            transcription.save()
            if (current and current.editor == request.user and
                    cutoff < current.modified):
                current.body = form.cleaned_data['body']
                current.save()
            else:
                if not current or current.body != form.cleaned_data['body']:
                    current = TranscriptionRevision.objects.create(
                        revision=current.revision + 1 if current else 0,
                        transcription=transcription,
                        body=form.cleaned_data['body'],
                        editor=request.user
                    )

        messages.success(request, _("Thanks for your attention to detail.  Transcription updated."))

        if document.type == "post":
            return redirect("scanning.after_transcribe_comment", document_id=document.pk)

        return redirect(document.get_absolute_url() + "#transcription")

    pages = document.documentpage_set.all()
    return render(request, "scanning/transcription_edit.html", {
        'lockform': lockform,
        'transcription': transcription,
        'document': document,
        'documentpages': pages,
        'documentpage_count': pages.count(),
        'form': form,
        'cancel_link': document.get_absolute_url(),
    })

@permission_required("scanning.change_transcription")
def after_transcribe_comment(request, document_id):
    """
    Prompt for a comment after a transcription is done.
    """
    document = get_object_or_404(Document, pk=document_id,
                                 type="post",
                                 scan__isnull=False,
                                 transcription__isnull=False)

    # Don't prompt for comment if they've already commented on this post.
    if document.comments.filter(user=request.user).exists() or \
            (not settings.COMMENTS_OPEN) or \
            document.author.profile.comments_disabled:
        return redirect(document.get_absolute_url() + "#transcription")

    if document.transcription.complete:
        prompt_text = "Thanks for writing! I finished the transcription for your post."
    else:
        prompt_text = "Thanks for writing! I worked on the transcription for your post."
    form = CommentForm(request.POST or None, initial={
        'comment': prompt_text
    })
    if form.is_valid():
        comment, created = Comment.objects.get_or_create(
            document=document,
            comment=form.cleaned_data['comment'],
            user=request.user,
        )
        if created:
            comment.document = document
        return redirect("%s#%s" % (request.path, comment.pk))

    return render(request, "scanning/after_transcribe_comment.html", {
        'document': document,
        'form': form,
    })

def revision_list(request, document_id):
    """
    Main revision display.
    """
    doc = get_object_or_404(Document, pk=document_id)
    if doc.status != "published":
        raise Http404
    try:
        revisions = list(doc.transcription.revisions.all())
    except Transcription.DoesNotExist:
        revisions = []
    return render(request, "scanning/revision_list.html", {
        'document' : doc,
        'revisions': revisions,
    })

def revision_compare(request, document_id):
    """
    AJAX comparison between two revisions
    """
    try:
        document = Document.objects.get(pk=document_id)
        earliest = TranscriptionRevision.objects.get(
                transcription__document=document,
                revision=int(request.GET['earliest']))
        latest = TranscriptionRevision.objects.get(
                transcription__document=document,
                revision=int(request.GET['latest']))
    except (KeyError, Document.DoesNotExist, TranscriptionRevision.DoesNotExist):
        raise
    return render(request, "scanning/_column_diff.html", {
        'document': document, 'earliest': earliest, 'latest': latest,
    })

@login_required
def flag_document(request, document_id):
    """
    Flag a post.
    """
    if not request.user.is_active:
        raise PermissionDenied
    doc = get_object_or_404(Document, pk=document_id)
    form = FlagForm(request.POST or None)
    if form.is_valid():
        if handle_flag_spam(request.user, form.cleaned_data['reason']):
            messages.info(request, _(u"Your account has been suspended due to behavior that looks like spam. If this is an error, please contact us using the contact link at the bottom of the page."))
            logout(request)
            return redirect("/")
        ticket, created = Note.objects.get_or_create(
            creator=request.user,
            text="FLAG from user. \n %s" % form.cleaned_data['reason'],
            resolved=None,
            important=form.cleaned_data['urgent'],
            document=doc,
        )
        # Queue up an async process to send notification email in 2 minutes (we
        # delay to trap spam floods).
        if created:
            send_flag_notification_email.apply_async(
                    args=[ticket.pk], countdown=120)
        messages.info(request, _(u"A moderator will review that post shortly. Thanks for helping us run a tight ship."))
        return redirect(doc.get_absolute_url())

        # redirect to confirmation.
    return render(request, "scanning/flag.html", {
            'form': form,
        })
