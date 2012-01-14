from django import forms

from registration.forms import RegistrationForm
from django.utils.translation import ugettext_lazy as _

class OptionalEmailForm(RegistrationForm):
    email = forms.EmailField(widget=forms.TextInput(attrs={'max_length': 75}),
                             required=False,
                             label=_("Email address"),
                             help_text=_("Email optional."))
#    contact = forms.BooleanField(required=False, label=_("May we contact you?"),
#            help_text=_("We reserve the right to cancel your account or " \
#                        "remove any comments that violate our guidelines.  " \
#                        "We value your contributions.  If you check this " \
#                        "box, we will contact you if there is ever a " \
#                        "ever a problem with your submission, so that you " \
#                        "can fix it and still get your point across.  " \
#                        "(We can only reach you if you also provide an email " \
#                        "address)."))


class UserModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, user):
        return u"%s (%s)" % (unicode(user.profile), user.username)

