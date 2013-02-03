import json
import datetime

# Create your views here.
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.views import redirect_to_login
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseBadRequest
from django.conf import settings

from comments.models import Comment, Favorite
from comments.forms import CommentForm
from scanning.models import Document
from scanning.forms import FlagForm
from annotations.models import Note

def check_comment_editable(fn):
    def wrapped(request, comment_id): 
        try:
            comment = Comment.objects.with_mailed_annotation().filter(
                    pk=comment_id)[0]
        except IndexError:
            raise Http404

        # Can only edit comments that haven't been mailed.
        if comment.letter_sent:
            raise PermissionDenied
        if comment.user_id != request.user.id and \
                not request.user.has_perm("comments.change_comment"):
            messages.error(request, "You must be logged in as the owner of the comment to proceed.")
            return redirect_to_login(request.path)
        return fn(request, comment=comment)
    return wrapped

@check_comment_editable
def edit_comment(request, comment_id=None, comment=None):
    if settings.COMMENTS_OPEN == False:
        raise PermissionDenied("Comments are disabled currently.")

    form = CommentForm(request.POST or None, initial={
        'comment': comment.comment
    })
    if form.is_valid():
        comment.comment = form.cleaned_data['comment']
        comment.modified = datetime.datetime.now()
        comment.save()
        return redirect(comment.get_absolute_url())
    return render(request, "comments/edit_comment.html", {
        'comment': comment,
        'form': form,
    })

@check_comment_editable
def delete_comment(request, comment_id=None, comment=None):
    if request.method == "POST":
        url = comment.document.get_absolute_url()
        comment.delete()
        messages.success(request, "Comment has been deleted.")
        return redirect(url)
    return render(request, "comments/delete_comment.html", {
        'comment': comment
    })

@login_required
def flag_comment(request, comment_id):
    """
    Flag a comment. 
    """
    comment = get_object_or_404(Comment, pk=comment_id)
    form = FlagForm(request.POST or None)
    if form.is_valid():
        ticket, created = Note.objects.get_or_create(
            creator=request.user,
            text="FLAG from user. \n %s" % form.cleaned_data['reason'],
            resolved=None,
            important=form.cleaned_data['urgent'],
            comment=comment,
        )
        messages.info(request, _(u"A moderator will review that comment shortly. Thanks for helping us run a tight ship."))
        return redirect(comment.document.get_absolute_url())

        # redirect to confirmation.
    return render(request, "scanning/flag.html", {
            'form': form,
        })

@login_required
def mark_favorite(request):
    """
    AJAX method to mark a post as a favorite.
    """
    document = None
    comment = None
    if 'document_id' in request.POST:
        try:
            document = Document.objects.safe_for_user(request.user).get(
                    pk=request.POST.get('document_id'))
        except Document.DoesNotExist:
            raise Http404
    elif 'comment_id' in request.POST:
        try:
            comment = Comment.objects.public().get(
                    pk=request.POST.get('comment_id'))
        except Comment.DoesNotExist:
            raise Http404
    else:
        return HttpResponseBadRequest("Missing parameters")
    fav, created = Favorite.objects.get_or_create(
        user=request.user,
        document=document,
        comment=comment)
    return _favorite_count_response(request, comment or document, True)

@login_required
def unmark_favorite(request):
    if 'comment_id' in request.POST:
        thing = get_object_or_404(Comment, pk=request.POST.get(
            'comment_id'))
    elif 'document_id' in request.POST:
        thing = get_object_or_404(Document, pk=request.POST.get(
            'document_id'))
    else:
        raise Http404
    try:
        fav = thing.favorite_set.get(user=request.user)
        fav.delete()
    except Favorite.DoesNotExist:
        pass
    return _favorite_count_response(request, thing, False)

def _favorite_count_response(request, thing, has_favorited):
    return render(request, "comments/_favorites.html", {
        'thing': thing,
        'num_favorites': thing.favorite_set.count(),
        'has_favorited': has_favorited,
    })
