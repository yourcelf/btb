import json
import datetime

from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404

from btb.utils import args_method_decorator, JSONView, date_to_string
from annotations.models import Note, ReplyCode
from scanning.models import Document, Scan
from profiles.models import Profile

class ReplyCodes(JSONView):
    @args_method_decorator(permission_required, "scanning.change_document")
    def get(self, request):
        if "code" in request.GET:
            codes = codes.filter(code=request.GET['code'])
        else:
            raise Http404
        if "document" in request.GET:
            dict_method = "doc_dict"
            codes = codes.org_filter(request.user)
        else:
            dict_method = "to_dict"
        return self.paginated_response(request, codes, dict_method=dict_method)

class Notes(JSONView):
    def clean_params(self, request):
        kw = json.loads(request.raw_post_data)

        #
        # Get the related object for which we are fetching notes.  Filter by
        # organization membership and type.
        #
        if kw.get('user_id', None):
            try:
                rel_obj = Profile.objects.org_filter(
                        request.user, pk=kw.pop('user_id')
                ).get().user
            except Profile.DoesNotExist:
                raise Http404
        elif kw.get('document_id', None):
            try:
                rel_obj = Document.objects.org_filter(
                        request.user, pk=kw.pop('document_id')
                ).get()
            except Document.DoesNotExist:
                raise Http404
        elif kw.get('scan_id', None):
            try:
                rel_obj = Scan.objects.org_filter(
                        request.user, pk=kw.pop('scan_id')
                ).get()
            except Scan.DoesNotExist:
                raise Http404
        else:
            rel_obj = None

        #
        # Handle remaining kwargs.
        #
        if 'creator_id' in kw:
            kw['creator'] = get_object_or_404(User, pk=kw.pop('creator_id'))
        else:
            kw['creator'] = request.user
        for date_field in ('created', 'modified', 'resolved'):
            if kw.get(date_field, None) is None:
                continue
            elif kw[date_field] == True:
                kw[date_field] = datetime.datetime.now()
            else:
                kw[date_field] = kw[date_field].replace('T', ' ')
        return kw, rel_obj
        
    @args_method_decorator(permission_required, "annotations.change_note")
    def get(self, request, note_id=None):
        """
        Filter notes to return.  If note_id is given, returns just the Note
        object as JSON.  Otherwise, a paginated response is given.

        Filter params:
            user_id=<id>:      notes attached to a particular user profile.
            document_id=<id>:  notes attached to a particular document.
            scan_id=<id>:      notes attached to a particular scan.
            unresolved:        notes with a null resolution.
            important:         notes with 'important == True'
        """
        note_id = note_id or request.GET.get('id')
        if note_id:
            try:
                note = Note.objects.org_filter(request.user, pk=note_id).get()
            except Note.DoesNotExist:
                raise PermissionDenied
            else:
                return self.json_response(note.to_dict())

        if 'user_id' in request.GET:
            user = get_object_or_404(User, pk=request.GET.get("user_id"))
            notes = user.notes.org_filter(request.user).by_resolution()
        elif 'document_id' in request.GET:
            document = get_object_or_404(Document, pk=request.GET.get("document_id"))
            notes = document.notes.org_filter(request.user).by_resolution()
        elif 'scan_id' in request.GET:
            scan = get_object_or_404(Scan, pk=request.GET.get("scan_id"))
            notes = scan.notes.org_filter(request.user).by_resolution()
        else:
            # All of the above.
            notes = Note.objects.org_filter(request.user).by_resolution()
        
        if 'unresolved' in request.GET:
            notes = notes.filter(resolved__isnull=True)
        if 'resolved' in request.GET:
            notes = notes.filter(resolved__isnull=False)
        if 'important' in request.GET:
            notes = notes.filter(important=True)
        if 'sort' in request.GET:
            notes = notes.order_by(*request.GET['sort'].split(","))
        return self.paginated_response(request, notes)

    @args_method_decorator(permission_required, "annotations.add_note")
    def post(self, request, note_id=None):
        # Clean params verifies org membership.
        kw, rel_obj = self.clean_params(request)
        if rel_obj:
            note = Note.objects.create(**kw)
            rel_obj.notes.add(note)
            return self.json_response(note.to_dict())
        raise Http404

    @args_method_decorator(permission_required, "annotations.change_note")
    def put(self, request, note_id=None):
        note = get_object_or_404(Note, pk=note_id)
        # Clean params verifies org membership.
        kw, rel_obj = self.clean_params(request)
        if rel_obj is None:
            raise Http404
        kwargs = {}
        for field in ("resolved", "important", "text"):
            setattr(note, field, kw[field])
        note.save()
        return self.json_response(note.to_dict())


    @args_method_decorator(permission_required, "annotations.delete_note")
    def delete(self, request, note_id=None):
        try:
            note = Note.objects.org_filter(request.user, pk=note_id).get()
        except Note.DoesNotExist:
            raise PermissionDenied
        note.delete()
        return self.json_response("success")
