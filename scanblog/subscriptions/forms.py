from django import forms

from subscriptions.models import MailingListInterest

class MailingListInterestForm(forms.ModelForm):
    class Meta:
        exclude = ['details']
        model = MailingListInterest
