from django import forms
from django.forms.util import ValidationError
from django.contrib.auth.models import User, Permission

from accounts.forms import UserModelChoiceField
from correspondence.models import Letter

perm = Permission.objects.get(content_type__model="letter", codename="manage_correspondence")
senders = (User.objects.filter(groups__permissions=perm) | User.objects.filter(is_superuser=True)).distinct()

class MailForm(forms.ModelForm):
    sender = UserModelChoiceField(queryset=senders, required=False)
    sender_title = forms.CharField(required=False, 
            help_text="Optional, unless sender is blank"
    )
    recipient = UserModelChoiceField(queryset=User.objects.exclude(profile__mailing_address=""), 
            label="Registered recipient",
            required=False, 
            help_text="Optional if name and address is provided below.")
    recipient_address = forms.CharField(
            widget=forms.Textarea(attrs={'rows': 6, 'cols': 20}), 
            required=False, 
            help_text="Optional if recipient is provided above.", 
            label="Name and address")
    body = forms.CharField(widget=forms.Textarea, help_text="Tex syntax.  Unescaped.  Required.")
    is_postcard = forms.BooleanField(required=False, help_text="Render as a postcard?")

    def clean_recipient_address(self):
        if not self.cleaned_data['recipient_address'] and not self.cleaned_data['recipient']:
            raise ValidationError("One of recipient or address is required.")
        elif self.cleaned_data['recipient_address'] and self.cleaned_data['recipient']:
            raise ValidationError("Please choose only one of 'recipient' or 'address'.")
        return self.cleaned_data['recipient_address']

    def clean_sender_title(self):
        name_parts = []
        if self.cleaned_data['sender']:
            name_parts.append(self.cleaned_data['sender'].profile.display_name)
        if self.cleaned_data['sender_title']:
            name_parts.append(self.cleaned_data['sender_title'])
        if not name_parts:
            raise ValidationError("One of sender or title is required.")

    class Meta:
        model = Letter
        exclude = ['type', 'comments', 'created', 'sent']

