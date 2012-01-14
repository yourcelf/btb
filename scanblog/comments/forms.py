from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

COMMENT_MAX_LENGTH = getattr(settings, 'COMMENT_MAX_LENGTH', 3000)

def autostrip(cls):
    fields = [(key, value) for key, value in cls.base_fields.iteritems() if isinstance(value, forms.CharField)]
    for field_name, field_object in fields:
        def get_clean_func(original_clean):
            return lambda value: original_clean(value and value.strip())
        clean_func = get_clean_func(getattr(field_object, 'clean'))
        setattr(field_object, 'clean', clean_func)
    return cls

@autostrip
class CommentForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea, label=_("Reply"),
            max_length=COMMENT_MAX_LENGTH)
    honey = forms.CharField(
            required=False, 
            widget=forms.TextInput(attrs={"class": "honey"}),
            label=_("If you enter anything in this field "\
                    "your comment will be treated as spam"),
    )

    def clean_honey(self):
        value = self.cleaned_data['honey']
        if value:
            raise forms.ValidationError(self.fields["honey"].label)
        return value
