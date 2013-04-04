import json
import re
from collections import defaultdict
from difflib import SequenceMatcher
#from moderation.diff_match_patch import *

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import permission_required, login_required
from django.core import paginator
from django.db.models import Count
from django.http import Http404
from djcelery.models import TaskMeta
from django.contrib.localflavor.us.us_states import STATES_NORMALIZED

from scanning.models import Document, Scan, DocumentPage, EditLock, \
        TranscriptionRevision
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
        'transcribers': "Who does transcriptions? (SLOW)",
#        'transcribed': "What gets transcribed?",
        'inactive_commenters': "Inactive/shell commenter accounts, with no comments, transcriptions, subscriptions, or anything?",
        'disabled_commenters': "Disabled commenter accounts.",
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
        items = [(len(v), k, sorted(v, key=lambda p: p.user.date_joined)) for k,v in states.items()]
        items.sort()
        items.reverse()
        rows = [
            (s, c, ", ".join(author_link(p) for p in ps)) for c, s, ps in items
        ]
        return render(request, "moderation/question_answer.html", {
            'question': questions[q],
            'header_row': [
                'State', 'Count', 'Authors'
            ],
            'rows': rows,
        })
    elif q == "transcribers":
        import locale
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        transcribers = defaultdict(lambda: {
            'posts': set(),
            'additions': 0,
            'deletions': 0,
        })
        prev = None
        for rev in TranscriptionRevision.objects.select_related(
                    'transcription', 'editor'
                ).order_by('transcription__document', 'revision'):
            if prev and rev.transcription.document_id != prev.transcription.document_id:
                prev = None
            ed = transcribers[rev.editor.username]
            ed['posts'].add(rev.transcription.document_id)
            if not prev:
                ed['additions'] += len(rev.body)
            else:
                additions, deletions = _sequence_matcher_count_additions_deletions(
                    rev.body, prev.body
                )
                ed['additions'] += additions
                ed['deletions'] += deletions
            prev = rev
        rows = [(
                u, len(d['posts']), d['additions'], d['deletions']
            ) for (u,d) in transcribers.iteritems()]
        rows.sort(key=lambda r: r[1])
        rows.reverse()
        rows = [(
                i + 1,
                u,
                p,
                locale.format("%d", d, grouping=True),
                locale.format("%d", a, grouping=True),
            ) for i, (u, p, d, a) in enumerate(rows)]
        return render(request, "moderation/question_answer.html", {
            'question': questions[q],
            'header_row': ['',
                'Username',
                'Number of posts',
                'Total characters added',
                'Total characters removed',
            ],
            'rows': rows
        })
    elif q == "inactive_commenters":
        users = User.objects.select_related('profile').filter(
                profile__blogger=False,
                comment__isnull=True,
                transcriptionrevision__isnull=True,
                subscriptions__isnull=True,
                is_staff=False,
                is_active=True
        ).exclude(groups__name="moderator").order_by('date_joined')
        rows = [(
           author_link(u.profile),
           u.date_joined.strftime("%Y-%m-%d"),
           u.last_login.strftime("%Y-%m-%d"),
        ) for u in users]
        rows.sort(key=lambda u: u[-1])
        rows.reverse()
        rows = [(i + 1, a, b, c) for i, (a, b, c) in enumerate(rows)]
        return render(request, "moderation/question_answer.html", {
            'question': questions[q],
            'header_row': ['',
                'Username',
                'Date joined',
                'Last login',
            ],
            'rows': rows,
        })
    elif q == "disabled_commenters":
        users = User.objects.select_related('profile').filter(
                profile__blogger=False,
                is_active=False
        ).order_by('date_joined')

        rows = [(
            author_link(u.profile),
            u.date_joined.strftime("%Y-%m-%d"),
            u.last_login.strftime("%Y-%m-%d"),
            "<br />".join(
                n.text for n in u.notes.all()
            )
        ) for u in users]
        rows.sort(key=lambda u: u[-1])
        rows.reverse()
        rows = [(i + 1, a, b, c, d) for i, (a, b, c, d) in enumerate(rows)]
        return render(request, "moderation/question_answer.html", {
            'question': questions[q],
            'header_row': ['',
                'Username',
                'Date joined',
                'Last login',
                'Notes (if any)',
            ],
            'rows': rows
        })

#    elif q == "transcribed":
#        posts = defaultdict(lambda: {
#            'complete': False, 'dates': [], 'size': 0, 'author_pk': None,
#            'title': None, 'url': None,
#        })
#        post_authors = defaultdict(set)
#        cur = None
#        struct = None
#        for rev in TranscriptionRevision.objects.select_related(
#                    'transcription', 'transcription__document'
#                ).order_by('transcription__document', 'revision'):
#            if not cur or cur.transcription != rev.transcription:
#                struct = posts[rev.transcription.document.pk]
#                cur = rev
#            struct['complete'] = rev.transcription.complete
#            struct['dates'].append(rev.modified)
#            struct['size'] = len(rev.body)
#            struct['author_pk'] = rev.transcription.document.author.pk
#            post_authors[rev.transcription.document.author.pk].add(
#                rev.transcription.document.pk
#            )
#        rows = []
#        for pk, struct in posts.iteritems():


    raise Http404


# NOTE: Default performance of this is slower than default performance of
# sequence matcher; though it could be possible to tweak it to be more
# performant.
#def _dmp_count_additions_deletions(s1, s2):
#    additions = 0
#    deletions = 0
#    diffs = diff_match_patch().diff_main(s1, s2)
#    for (op, string) in diffs:
#        if op == diff_match_patch.DIFF_DELETE:
#            deletions += 1
#        elif op == diff_match_patch.DIFF_INSERT:
#            additions += 1
#    return additions, deletions

def _sequence_matcher_count_additions_deletions(s1, s2):
    additions = 0
    deletions = 0
    sm = SequenceMatcher(None, s1, s2)
    for opcode, a0, a1, b0, b1 in sm.get_opcodes():
        if opcode == 'insert':
            additions += b1 - b0
        elif opcode == 'delete':
            deletions += a1 - a0
        elif opcode == 'replace':
            additions += b1 - b0
            deletions += a1 - a0
    return additions, deletions

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

