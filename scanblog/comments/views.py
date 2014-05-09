import json
import datetime

# Create your views here.
from django.contrib.auth.views import redirect_to_login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models.deletion import Collector
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from comments.models import Comment, CommentRemoval, RemovalReason, \
        CommentRemovalNotificationLog, Favorite
from correspondence.models import Letter
from comments.forms import CommentForm, CommentRemovalForm
from scanning.forms import FlagForm
from scanning.models import Document
from annotations.models import Note, handle_flag_spam
from annotations.tasks import send_flag_notification_email

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
    if not request.user.is_active:
        raise PermissionDenied
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
    """
    This is a function for users to delete their own comments.
    """
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
    if not request.user.is_active:
        raise PermissionDenied
    comment = get_object_or_404(Comment, pk=comment_id)
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
            comment=comment,
        )
        # Queue up an async process to send notification email in 2 minutes (we
        # delay to trap spam floods).
        if created:
             send_flag_notification_email.apply_async(
                     args=[ticket.pk], countdown=120)
        messages.info(request, _(u"A moderator will review that comment shortly. Thanks for helping us run a tight ship."))
        return redirect(comment.document.get_absolute_url())

        # redirect to confirmation.
    return render(request, "scanning/flag.html", {
            'form': form,
        })

@permission_required("comments.change_comment")
def spam_can_comment(request, comment_id):
    try:
        comment = Comment.objects.org_filter(request.user).get(
                pk=comment_id, comment_doc__isnull=True)
    except Comment.DoesNotExist:
        raise Http404
    # Only moderators can delete; and exclude bloggers, superusers, and
    # moderators from being deleted.
    can_del_user = request.user.has_perm("auth.delete_user") \
            and not comment.user.is_superuser \
            and not comment.user.groups.filter(name='moderators').exists() \
            and not comment.user.profile.managed

    if request.method == 'POST':
        redirect_url = comment.document.get_absolute_url()
        if can_del_user and request.POST.get("delete_user"):
            comment.user.delete()
            messages.success(request, "User and all user's content deleted.")
        else:
            comment.removed = True
            comment.save()
            messages.success(request, "Comment removed.")
        return redirect(redirect_url)

    also_deleted = None
    if can_del_user:
        # Get a list of things that will be deleted if the user is.
        collector = Collector(using='default')
        collector.collect([comment.user])
        also_deleted = []
        for model, instance in collector.instances_with_model():
            if instance != comment.user:
                also_deleted.append((instance._meta.object_name, instance))
    return render(request, "comments/spam_can_comment.html", {
        'comment': comment,
        'can_del_user': can_del_user,
        'also_deleted': also_deleted,
    })

@permission_required("comments.change_comment")
def remove_comment(request, comment_id):
    try:
        comment = Comment.objects.org_filter(request.user).get(
                pk=comment_id)
    except Comment.DoesNotExist:
        raise Http404

    try:
        removal = CommentRemoval.objects.get(comment=comment)
    except CommentRemoval.DoesNotExist:
        removal = CommentRemoval(comment=comment)

    # Have we sent the commenter a notice already?
    commenter_notified = CommentRemovalNotificationLog.objects.filter(
            comment=comment).exists()
    # Have we sent the blogger a notice already?
    blogger_notified = Letter.objects.filter(type="comment_removal",
            comments=comment).exists()

    form = CommentRemovalForm(request.POST or None, instance=removal)

    # Don't allow changing of comment message if they've already been notified.
    if commenter_notified:
        del form.fields['comment_author_message']
    # Don't allow changing of blogger's message if they've already been notified.
    if blogger_notified:
        del form.fields['post_author_message']

    if form.is_valid():
        comment.removed = True
        comment.save()
        removal = form.save()
        if removal.comment_author_message.strip() != u"" and comment.user.email:
            log, created = CommentRemovalNotificationLog.objects.get_or_create(
                    comment=comment)
            if created:
                subject = render_to_string("comments/removal-email-subject.txt", {
                    'removal': removal
                }).strip()
                body = render_to_string("comments/removal-email-body.txt", {
                    'notices_url': reverse("notification_notice_settings"),
                    'recipient': comment.user,
                    'removal': removal,
                    'message': removal.comment_author_message,
                })
                send_mail(
                   subject=subject,
                   message=body,
                   from_email=settings.DEFAULT_FROM_EMAIL,
                   recipient_list=[comment.user.email])

        return redirect(comment.get_absolute_url())
    reasons = {}
    for reason in RemovalReason.objects.org_filter(request.user):
        reasons[reason.pk] = {
            "default_web_message": reason.default_web_message,
            "default_comment_author_message": reason.default_comment_author_message,
            "default_post_author_message": reason.default_post_author_message,
        }
    return render(request, "comments/remove_comment.html", {
        'commenter_notified': commenter_notified,
        'blogger_notified': blogger_notified,
        'form': form,
        'removal': removal,
        'comment': comment,
        'reasons_json': json.dumps(reasons),
    })

@permission_required("comments.change_comment")
def unremove_comment(request, comment_id):
    try:
        comment = Comment.objects.org_filter(request.user).get(
                pk=comment_id, commentremoval__isnull=False)
    except Comment.DoesNotExist:
        raise Http404
    if request.method == "POST":
        try:
            comment.commentremoval.delete()
        except CommentRemoval.DoesNotExist:
            pass
        comment.removed = False
        comment.save()
        return redirect(comment.get_absolute_url())
    return render(request, "comments/unremove_comment.html", {
        'comment': comment,
        'removal': comment.commentremoval,
    })

@login_required
def mark_favorite(request):
    """
    AJAX method to mark a post as a favorite.
    """
    comment, document = _get_favorite_thing(request, request.POST)
    if not (comment or document):
        return HttpResponseBadRequest("Missing parameters")
    fav, created = Favorite.objects.get_or_create(
        user=request.user, document=document, comment=comment)
    return _favorite_count_response(request, comment or document, True)

def mark_favorite_after_login(request):
    if request.user.is_authenticated():
        fav_details = request.session.pop('favorite_after_login', None)
        if not fav_details:
            return redirect("/")
        else:
            comment, document = _get_favorite_thing(request, fav_details)
            fav, created = Favorite.objects.get_or_create(
                user=request.user, document=document, comment=comment)
            messages.info(request, "Favorite added.")
            return redirect(fav.get_absolute_url())
    else:
        if 'comment_id' in request.GET:
            dct = {'comment_id': request.GET['comment_id']}
        elif 'document_id' in request.GET:
            dct = {'document_id': request.GET['document_id']}
        else:
            raise Http404
        messages.info(request, "Please login in order to mark favorites.")
        request.session['favorite_after_login'] = dct
        return redirect_to_login(next=request.path)

@login_required
def unmark_favorite(request):
    comment, document = _get_favorite_thing(request, request.POST)
    thing = comment or document
    try:
        fav = thing.favorite_set.get(user=request.user)
        fav.delete()
    except Favorite.DoesNotExist:
        pass
    return _favorite_count_response(request, thing, False)

def _get_favorite_thing(request, dct):
    comment = None
    document = None
    if 'comment_id' in dct:
        try:
            comment = Comment.objects.public().get(pk=dct['comment_id'])
        except Comment.DoesNotExist:
            pass
    elif 'document_id' in dct:
        try:
            document = Document.objects.safe_for_user(request.user).get(pk=dct['document_id'])
        except Document.DoesNotExist:
            pass
    return comment, document


def _favorite_count_response(request, thing, has_favorited):
    return render(request, "comments/_favorites.html", {
        'thing': thing,
        'num_favorites': thing.favorite_set.count(),
        'has_favorited': has_favorited,
        'user': request.user,
    })

def list_favorites(request):
    if 'comment_id' in request.GET:
        thing = get_object_or_404(Comment, pk=request.GET.get('comment_id'))
    elif 'document_id' in request.GET:
        thing = get_object_or_404(Document, pk=request.GET.get('document_id'))
    else:
        raise Http404
    favorites = thing.favorite_set.select_related('user', 'user__profile').all()
    return render(request,"comments/_list_favorites.html", {
        'thing': thing,
        'favorites': list(favorites)
    })
