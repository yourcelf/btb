import os

import magic

from django import forms
from scanning.models import Scan
from profiles.models import Organization

def join_and(things):
    return ", ".join(things[0:-2] + [" and ".join(things[-2:])])

class ScanUploadForm(forms.Form):
    file = forms.FileField()

    def __init__(self, *args, **kwargs):
        self.valid_types = kwargs.pop('types', {
            "pdf": "application/pdf",
            "zip": "application/zip",
        })
        super(ScanUploadForm, self).__init__(*args, **kwargs)

    def clean_file(self):
        uf = self.cleaned_data['file']
        if not uf: 
            if self.fields['file'].required:
                raise forms.ValidationError("This field is required.")
            return
        mime = magic.Magic(mime=True)
        ft = mime.from_buffer(uf.read(65536))
        if ft not in self.valid_types.values():
            ext = os.path.splitext(uf.name)[1][1:]
            error = "Only %s files are supported." % \
                    join_and(self.valid_types.keys())
            if ext.lower() in self.valid_types.keys():
                error += "  Though the file you uploaded ends in '.%s', the contents are a %s file." % (ext, ft.split("/")[1])
            raise forms.ValidationError(error)

def get_org_upload_form(user):
    if user.is_superuser:
        qs = Organization.objects.all()
    else:
        qs = user.organizations_moderated.all()
    class OrgUploadForm(ScanUploadForm):
        organization = forms.ModelChoiceField(queryset=qs, empty_label=None)
    return OrgUploadForm

class TranscriptionForm(forms.Form):
    body = forms.CharField(widget=forms.Textarea(attrs={'rows': 40, 'cols': 40}))
    complete = forms.BooleanField(required=False, 
                                  help_text="Check if this transcription is complete.")

class LockForm(forms.Form):
    lock_transcription = forms.BooleanField(required=False)

class FlagForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea, help_text="What is up with this post?")
    urgent = forms.BooleanField(required=False, help_text="Please check if this is a serious problem that needs to be addressed immediately (we will do our best to act quickly).")
