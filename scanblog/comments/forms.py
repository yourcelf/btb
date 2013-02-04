import datetime

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from comments.models import Comment, CommentRemoval
from correspondence.models import Letter
from correspondence.utils import LatexCompileError

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

class CommentRemovalForm(forms.ModelForm):
    comment = forms.ModelChoiceField(queryset=Comment.objects.all(),
            widget=forms.HiddenInput)

    class Meta:
        model = CommentRemoval
        exclude = ['date']

    def clean(self):
        super(CommentRemovalForm, self).clean()
        data = self.cleaned_data
        # Ensure that the comment is not changed by the form.
        data['comment'] = self.instance.comment
        # Trim white space for messages.
        data['web_message'] = data['web_message'].strip()
        if 'comment_author_message' in data:
            data['comment_author_message'] = data['comment_author_message'].strip()
        if 'post_author_message' in data:
            data['post_author_message'] = data['post_author_message'].strip()
            if data['post_author_message'] != "":
                # Verify that latex compiles properly by constructing a letter,
                # rendering it to a file, then deleting it.
                letter = Letter.objects.create(
                    type="comment_removal",
                    recipient=data['comment'].document.author,
                    org=data['comment'].document.author.organization_set.get(),
                    body=data['post_author_message'],
                    # Just need any user here to validate the Letter -- but we
                    # delete it right away anyway.
                    sender=data['comment'].document.author,
                    send_anonymously=True,
                    sent=datetime.datetime.now()
                )
                letter.comments.add(data['comment'])
                error = None
                try:
                    filename = letter.get_file()
                except LatexCompileError as e:
                    error = e
                finally:
                    letter.delete()
                if error:
                    self._errors["post_author_message"] = error.message
                    del data["post_author_message"]
        return data
