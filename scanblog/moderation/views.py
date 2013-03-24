import json
import re
from collections import defaultdict

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import permission_required, login_required
from django.core import paginator
from django.db.models import Count
from django.http import Http404
from djcelery.models import TaskMeta
from django.contrib.localflavor.us.us_states import STATES_NORMALIZED

from scanning.models import Document, Scan, DocumentPage, EditLock
from scanning import tasks as scanning_tasks
from profiles.models import Profile, Organization
from annotations.models import Tag
from django.contrib.auth.models import User
from correspondence.models import Letter
from comments.models import Comment
from btb.utils import dthandler

@permission_required("scanning.add_scan")
def home(request):
    """
    Single page app for scanning/moderation.
    """
    orgs = Organization.objects.org_filter(request.user)
    return render(request, "moderation/home.html", {
        'document_states': Document.STATES,
        'organizations_json': json.dumps(
            [o.to_dict() for o in orgs]
        )
    })

#TODO  better permission here
@permission_required("correspondence.manage_correspondence")
def manage_tasks(request):
    tasks = TaskMeta.objects.all().order_by('-date_done')
    status = request.GET.get("status", "")
    if status:
        tasks = tasks.filter(status=status)
    p = paginator.Paginator(tasks, 10)
    try:
        page = p.page(request.GET.get('page', 1))
    except (ValueError, paginator.EmptyPage):
        page = p.page(1)
    return render(request, "moderation/manage_tasks.html", { 
        'page': page,
        'status': status
    })

@login_required
def wait_for_processing(request, task_id):
    return render(request, 
            "moderation/wait_for_processing.html", 
            { 'task_id': task_id, })

def _date_aggregate(queryset, date_field, precision='week'):
    return queryset.extra(
            select={precision: """DATE_TRUNC('%s', %s)""" % (precision, date_field)}
        ).values(
            precision
        ).annotate(count=Count('pk')).order_by(precision)

#TODO: better permission here
@permission_required("correspondence.manage_correspondence")
def stats(request):
    just_profiles = set()
    just_posts = set()
    posts_and_profiles = set()
    with_profiles = set(Profile.objects.bloggers_with_profiles())
    with_posts = set(Profile.objects.bloggers_with_posts())
    for p in with_posts:
        if p not in with_profiles:
            just_posts.add(p)
        else:
            posts_and_profiles.add(p)
    for p in with_profiles:
        if p not in with_posts:
            just_profiles.add(p)
    enrolled = set(Profile.objects.enrolled())
    not_published = enrolled - with_profiles - with_posts

    waitlisted = Profile.objects.waitlisted().count() 
    waitlistable = Profile.objects.waitlistable().count()
    invited = Profile.objects.invited().count()

    stats = {
        'users': {
            'counts': {
                'name': 'All users',
                'size': Profile.objects.count(),
                'children': [
                    {
                        'name': 'Total active users',
                        'size': Profile.objects.active().count(),
                        'children': [
                            {
                                'name': 'Commenters',
                                'size': Profile.objects.commenters().count(),
                            },
                            {
                                'name': 'Bloggers',
                                'size': Profile.objects.bloggers().count(),
                                'children': [
                                    {
                                        'name': 'Not enrolled',
                                        'size': waitlisted + waitlistable + invited,
                                        'children': [
                                            {
                                                'name': 'Waitlisted',
                                                'size': Profile.objects.waitlisted().count()
                                            },
                                            {
                                                'name': 'Waitlistable',
                                                'size': Profile.objects.waitlistable().count(),
                                            },
                                            {
                                                'name': 'Invited',
                                                'size': Profile.objects.invited().count(),
                                            },
                                        ],
                                    },
                                    {
                                        'name': 'Enrolled',
                                        'size': Profile.objects.enrolled().count(),
                                        'children': [
                                            {
                                                'name': 'Just profiles',
                                                'size': len(just_profiles),
                                            },
                                            {
                                                'name': 'Just posts',
                                                'size': len(just_posts),
                                            },
                                            {
                                                'name': 'With both posts and profiles',
                                                'size': len(posts_and_profiles),
                                            },
                                            {
                                                'name': 'Nothing published',
                                                'size': len(not_published),
                                            },
                                        ],
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        'name': 'Total inactive users',
                        'size': Profile.objects.inactive().count(),
                        'children': [
                            {
                                'name': 'Commenters, inactive',
                                'size': Profile.objects.inactive_commenters().count(),
                            }, 
                            {
                                'name': 'Bloggers, inactive',
                                'size': Profile.objects.inactive_bloggers().count(),
                            }
                        ]
                    }
                ]
            },
            'time_series': {
                'waitlist': list(_date_aggregate(Profile.objects.bloggers(), 'date_joined')),
                'enrolled': list(_date_aggregate(Letter.objects.filter(type='signup_complete'), 'sent')),
                'commenters': list(_date_aggregate(Profile.objects.commenters(), 'date_joined')),
            },
        },
        'documents': {
            'time_series': {
                'posts': list(_date_aggregate(Document.objects.public().filter(type="post"), 'date_written')),
                'profiles': list(_date_aggregate(Document.objects.public().filter(type="profile"), 'date_written')),
                'requests': list(_date_aggregate(Document.objects.filter(type="request"), 'date_written')),
            },
            'post_impact': list(Profile.objects.enrolled().annotate(
                    count=Count('user__documents_authored')
                ).values('count', 'display_name')),
            'page_impact': list(Profile.objects.enrolled().annotate(
                    count=Count('user__documents_authored__documentpage')
                ).values('count', 'display_name')),
            'posts': {
                'total': Document.objects.filter(type="post").count(),
                'published': Document.objects.public().filter(type="post").count(),
                'ready_to_publish': Document.objects.ready().filter(type="post").count(),
            },
            'profiles': {
                'total': Document.objects.filter(type="profile").count(),
                'published': len(with_profiles),
                'ready_to_publish': Document.objects.ready().filter(type="profile").count(),
            },
        },
        'letters': {
            'time_series': {
                'letter': list(_date_aggregate(Letter.objects.sent().filter(type='letter'), 'sent')),
                'consent form': list(_date_aggregate(Letter.objects.sent().filter(type='consent_form'), 'sent')),
                'signup complete': list(_date_aggregate(Letter.objects.sent().filter(type='signup_complete'), 'sent')),
                'first post': list(_date_aggregate(Letter.objects.sent().filter(type='first_post'), 'sent')),
                #'printout': list(_date_aggregate(Letter.objects.sent().filter(type='printout'), 'sent')),
                'comments': list(_date_aggregate(Letter.objects.sent().filter(type='comments'), 'sent')),
                'waitlist': list(_date_aggregate(Letter.objects.sent().filter(type='waitlist'), 'sent')),
                'other': list(_date_aggregate(Letter.objects.sent().filter(type=''), 'sent')),
            },
            'impact': list(
                Profile.objects.active().annotate(
                    count=Count('user__received_letters')
                ).filter(count__gt=0).values('count', 'display_name')
            )
        },
        'comments': {
            'total': Comment.objects.public().count(),
            'time_series': {
                'comments posted': list(_date_aggregate(Comment.objects.public(), '"comments_comment"."created"')),
            },
            'by_user': list(User.objects.annotate(
                    count=Count('comment')
                ).filter(
                    count__gt=0
                ).values('count', 'username')),
            'impact': list(
                User.objects.annotate(count=Count('comment')).filter(count__gt=0).values('count', 'username'),
            )
        }

    }
    return render(request, "moderation/stats.html", {
        'stats': json.dumps(stats, default=dthandler)
    })

#XXX better permission needed here
@permission_required("correspondence.manage_correspondence")
def questions(request):
    q = request.GET.get('q', None)
    questions =  {
        'comment_gap': "How long after a post is published do comments keep coming in?",
        'writers_by_recency': "List of writers by how recently they posted.",
        'writers_by_volume': "List of writers by number of posts.",
        'letter_post_ratio': "Ratio of posts published to letters sent for each writer.",
        'comments_to_posts': "Ratio of comments received to posts published for each writer.",
        'states': "How many writers in which states?",
    }

    author_link = lambda p: "<a href='%s'>%s</a>" % (p.get_edit_url(), p)


    if not q:
        return render(request, "moderation/questions_index.html", {
            'questions': sorted(questions.items())
        })
    elif q == "comment_gap":
        counter = defaultdict(int)
        for comment in Comment.objects.public().filter(comment_doc__isnull=True):
            gap = (comment.created - comment.document.date_written).days
            counter[gap] += 1
        header_row = [
            "Days", "Count", "Total percentage so far"
        ]
        rows = []
        accum = 0
        total = sum(counter.values())
        for days, count in sorted(counter.items()):
            accum += count
            rows.append((days, count, "%2.2f" % (100. * accum / total)))
        return render(request, "moderation/question_answer.html", {
            'question': questions[q],
            'header_row': header_row,
            'rows': rows,
        })

    elif q == "writers_by_recency":
        date_profile = []
        for profile in Profile.objects.enrolled().select_related('user'):
            try:
                latest = profile.user.documents_authored.filter(status='published').order_by('-date_written')[0]
            except IndexError:
                continue
            date_profile.append((
                latest.date_written.strftime("%Y-%m-%d"),
                author_link(profile),
            ))
        date_profile.sort()
        date_profile.reverse()
        return render(request, "moderation/question_answer.html", {
            'question': questions[q],
            'header_row': ["", "Date", "Author"],
            'rows': [(i + 1, d, p) for i,(d,p) in enumerate(date_profile)]
        })
    elif q == "writers_by_volume":
        volume_profile = []
        for profile in Profile.objects.enrolled().select_related('user'):
            volume_profile.append((
                profile.user.documents_authored.filter(status='published').count(),
                author_link(profile),
            ))
        volume_profile.sort()
        volume_profile.reverse()
        total = sum(v for v,p in volume_profile)
        rows = [(v, "%2.2f" % (100. * v / total), p) for v,p in volume_profile]
        return render(request, "moderation/question_answer.html", {
            'question': questions[q],
            'header_row': [
                "Number of posts", 
                "Percentage of all posts",
                "Author",
            ],
            'rows': rows,
        })
    elif q == "letter_post_ratio":
        posts_vs_letters_profile = []
        for profile in Profile.objects.filter(blogger=True).select_related('user'):
            posts = profile.user.documents_authored.filter(status='published').count()
            letters = profile.user.received_letters.filter(sent__isnull=False).count()
            if letters == 0:
                ratio = 0
            else:
                ratio = float(posts) / letters
            posts_vs_letters_profile.append((
                ratio, posts, letters, profile
            ))
        posts_vs_letters_profile.sort()
        posts_vs_letters_profile.reverse()
        rows = [("%.4f" % r, p, l, author_link(a)) for r,p,l,a in posts_vs_letters_profile]
        return render(request, "moderation/question_answer.html", {
            'question': questions[q],
            'header_row': [
                "Ratio of posts to letters",
                "Total posts",
                "Total letters",
                "Author"
            ],
            'rows': rows,
        })
    elif q == "comments_to_posts":
        comments_to_posts = []
        for profile in Profile.objects.enrolled().select_related('user'):
            comments = Comment.objects.public().filter(
                    comment_doc__isnull=True,
                    document__author=profile.user).count()
            posts = profile.user.documents_authored.filter(status='published').count()
            if posts == 0:
                ratio = 0
            else:
                ratio = comments / float(posts)
            comments_to_posts.append((ratio, comments, posts, profile))
        rows = [
            ("%.4f" % r, c, p, author_link(a)) for r,c,p,a in reversed(sorted(comments_to_posts))
        ]
        return render(request, "moderation/question_answer.html", {
            'question': questions[q],
            'header_row': [
                "Ratio of comments to posts",
                "Total comments",
                "Total posts",
                "Author"
            ],
            'rows': rows,
        })
    elif q == "states":
        states = defaultdict(list)
        unknown_count = 0
        for profile in Profile.objects.enrolled():
            parts = re.split("[^a-zA-Z0-9\.]", profile.mailing_address)
            for word in parts[::-1]:
                if word.lower() in STATES_NORMALIZED:
                    state = STATES_NORMALIZED[word.lower()]
                    break
            else:
                unknown_count += 1
                state = "Unknown %s" % unknown_count
            states[state].append(profile)
        items = [(len(v), k, v) for k,v in states.items()]
        items.sort()
        items.reverse()
        rows = [
            (s, c, ",".join(author_link(p) for p in ps)) for c, s, ps in items
        ]
        return render(request, "moderation/question_answer.html", {
            'question': questions[q],
            'header_row': [
                'State', 'Count', 'Authors'
            ],
            'rows': rows,
        })


    raise Http404



@permission_required("scanning.add_scan")
def page_picker(request):
    pages = DocumentPage.objects.filter(
            document__status="published",
            document__author__is_active=True,
            document__author__profile__blogger=True,
            document__author__profile__consent_form_received=True)
        
    return render(request, "moderation/page_picker.html", {
        'pages': pages,
    })
 
@permission_required("scanning.tag_post")
def tagparty(request):
    return render(request, "moderation/tagparty.html", {
        'tags': Tag.objects.all().order_by('name'),
    })

@permission_required("scanning.tag_post")
def tagparty_next(request):
    try:
        doc = Document.objects.public().order_by('created').filter(
                type="post",
                tags__isnull=True,
                editlock__isnull=True,
        )[0]
    except IndexError:
        raise Http404

    lock = EditLock.objects.create(user=request.user, document=doc)
    scanning_tasks.expire_editlock.apply_async(args=[lock.id], countdown=60*5)

    return redirect(doc.get_absolute_url())

