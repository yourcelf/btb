import json

from django.http import HttpResponse, Http404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.shortcuts import render, get_object_or_404, redirect

from notification.models import Notice, NoticeType, NoticeSetting, NOTICE_MEDIA, get_notification_setting
from subscriptions.models import Subscription
from scanning.models import Document
from annotations.models import Tag
from profiles.models import Organization, Affiliation
from campaigns.models import Campaign

@login_required
def subscribe_to_org(request, org_id):
    org = get_object_or_404(Organization, pk=org_id, public=True)
    if request.method == "POST":
        sub, created = Subscription.objects.get_or_create(
                subscriber=request.user,
                organization=org,
        )
        return redirect("subscriptions.settings")
    return render(request, "subscriptions/subscribe_to.html", {
        'org': org,
    })

@login_required
def subscribe_to_campaign(request, slug):
    campaign = get_object_or_404(Campaign, slug=slug, public=True)
    if request.method == "POST":
        sub, created = Subscription.objects.get_or_create(
                subscriber=request.user,
                campaign=campaign,
        )
        return redirect("subscriptions.settings")
    return render(request, "subscriptions/subscribe_to.html", {
        'campaign': campaign,
    })

@login_required
def subscribe_to_affiliation(request, affiliation_id):
    affiliation = get_object_or_404(Affiliation, pk=affiliation_id, public=True)
    if request.method == "POST":
        sub, created = Subscription.objects.get_or_create(
                subscriber=request.user,
                affiliation=affiliation,
        )
        return redirect("subscriptions.settings")
    return render(request, "subscriptions/subscribe_to.html", {
        'affiliation': affiliation,
    })

@login_required
def subscribe_to_author(request, author_id):
    author = get_object_or_404(User, pk=author_id)
    if request.method == 'POST':
        sub, created = Subscription.objects.get_or_create(
            subscriber=request.user,
            author=author
        )
        return redirect("subscriptions.settings")
    return render(request, "subscriptions/subscribe_to.html", {
        'author': author,
    })

@login_required
def subscribe_to_document(request, document_id):
    document = get_object_or_404(Document, pk=document_id)
    if request.method == 'POST':
        sub, created = Subscription.objects.get_or_create(
                subscriber=request.user,
                document=document,
        )
        return redirect("subscriptions.settings")
    return render(request, "subscriptions/subscribe_to.html", {
        'document': document,
    })

@login_required
def subscribe_to_tag(request, tag_name):
    tag = get_object_or_404(Tag, name=tag_name.strip())
    if request.method == 'POST':
        sub, created = Subscription.objects.get_or_create(
                subscriber=request.user,
                tag=tag,
        )
        return redirect("subscriptions.settings")
    return render(request, "subscriptions/subscribe_to.html", {
        'tag': tag,
    })

@login_required
def notice_settings(request):
    """
    This is copied from notification.views.notice_settings in order to add
    code for managing subscriptions as well as notice settings.

    The notice settings view.
    
    Template: :template:`notification/notice_settings.html`
    
    Context:
        
        notice_types
            A list of all :model:`notification.NoticeType` objects.
        
        notice_settings
            A dictionary containing ``column_headers`` for each ``NOTICE_MEDIA``
            and ``rows`` containing a list of dictionaries: ``notice_type``, a
            :model:`notification.NoticeType` object and ``cells``, a list of
            tuples whose first value is suitable for use in forms and the second
            value is ``True`` or ``False`` depending on a ``request.POST``
            variable called ``form_label``, whose valid value is ``on``.
    """
    notice_types = NoticeType.objects.all()
    settings_table = []
    for notice_type in notice_types:
        settings_row = []
        for medium_id, medium_display in NOTICE_MEDIA:
            form_label = "%s_%s" % (notice_type.label, medium_id)
            setting = get_notification_setting(request.user, notice_type, medium_id)
            if request.method == "POST":
                if request.POST.get(form_label) == "on":
                    if not setting.send:
                        setting.send = True
                        setting.save()
                else:
                    if setting.send:
                        setting.send = False
                        setting.save()
            settings_row.append((form_label, setting.send))
        settings_table.append({"notice_type": notice_type, "cells": settings_row})
    notice_settings = {
        "column_headers": [medium_display for medium_id, medium_display in NOTICE_MEDIA],
        "rows": settings_table,
    }

    subscriptions = []
    for sub in Subscription.objects.filter(subscriber=request.user):
        label = 'sub_%s' % sub.pk
        if request.method == "POST" and not request.POST.get(label) == "on":
            sub.delete()
        else:
            subscriptions.append([label, sub])

    if request.method == "POST":
        messages.info(request, "Settings saved.")
        return redirect("subscriptions.settings")

    from_email = settings.DEFAULT_FROM_EMAIL

    return render(request, "notification/notice_settings.html", {
        "notice_types": notice_types,
        "notice_settings": notice_settings,
        "subscription_settings": subscriptions,
        "from_email": from_email,
    })

@login_required
def unsubscribe_all_from_email(request):
    # NOTE: This arrives from an automatic login from email.  So for security,
    # we log the users out automatically afterwards -- that way a wayward
    # forwarded email can only result in unsubscriptions, and not further
    # damage.  (The main worry would be a moderator forwarding an email
    # unknowingly).
    for nt in NoticeType.objects.all():
        ns, created = NoticeSetting.objects.get_or_create(
                user=request.user,
                notice_type=nt,
                medium="1", # email, see NOTICE_MEDIA
        )
        ns.send = False
        ns.save()
    logout(request) 
    messages.info(request, "All email subscriptions have been removed.  To manage your settings further, please log in.")
    return redirect("subscriptions.settings")

#
# Addenda to the django-notifications
#
@login_required
def ajax_set_notice_seen(request, notice_id):
    if request.method != 'POST':
        raise Http404
    notice = get_object_or_404(Notice, pk=notice_id)
    if notice.recipient != request.user:
        raise Http404
    notice.unseen = False
    notice.save()
    response = HttpResponse(json.dumps({'unseen': notice.unseen, 'id': notice.id}))
    response['Content-type'] = 'application/json'
    return response

@login_required
def ajax_delete_notice(request, notice_id):
    if request.method != 'POST':
        raise Http404
    notice = get_object_or_404(Notice, pk=notice_id)
    if notice.recipient != request.user:
        raise Http404
    notice.delete()
    return HttpResponse("success")

@login_required
def ajax_delete_all_notices(request):
    if request.method != 'POST':
        raise Http404
    Notice.objects.filter(recipient=request.user).delete()
    return HttpResponse("success")
