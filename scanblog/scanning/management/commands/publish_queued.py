from datetime import datetime, timedelta
from collections import defaultdict
import logging

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from scanning.models import Document

__all__ = ('Command',)
logger = logging.getLogger(__name__)

def evaluate_order(order, recent, schedule):
    """
    Calculate a score for the given order in light of the given schedule, such
    that we attempt to maximize:
    1. Not publishing too late
    2. Not clumping together posts by the same author.
    """
    last_author_pos = {} # For calculating distances between posts by same author
    for i, doc in enumerate(recent):
        last_author_pos[doc.author_id] = i

    last_author_date = {} # For ensuring we don't reverse dates.

    score = 0
    for i, (doc, date) in enumerate(zip(order, schedule)):
        pos = len(recent) + i
        if date > doc.created + timedelta(days=settings.MAX_READY_TO_PUBLISH_DAYS):
            score -= 1000
        else:
            # Might want to scale this down more...
            score -= 1. / (date - doc.created).days
        if last_author_pos.get(doc.author_id, None) is not None:
            score -= 1. / (pos - last_author_pos[doc.author_id] + 1)
        if last_author_date.get(doc.author_id, None) is not None:
            if last_author_date[doc.author_id] > doc.created:
                score -= 1000 # No out of order pls!
        last_author_pos[doc.author_id] = pos
        last_author_date[doc.author_id] = doc.created
    return score

def next_by_pressure(ready, recent):
    pressure = defaultdict(int)
    def _add_pressure(i, remaining):
        for j in range(i, len(remaining)):
            pressure[remaining[j].author_id] += 1
    for i in range(len(recent)):
        _add_pressure(i, recent)
        _add_pressure(0, ready)
        pressure[recent[i].author_id] = 0

    max_count  = None # any int is greater than None
    max_author = None
    for author_id, count in pressure:
        if count > max_pressure_count:
            max_author = author_id
            max_count = count
    for doc in ready:
        if doc.author_id == max_author:
            return doc

def sort_ready(ready, recent, schedule):
    """
    Given a list of documents with their date_written and author, a list of
    recently published documents, and a schedule over which documents are to be
    published, determine the order in which they are to be published.
    """
    by_author = defaultdict(list)
    pressure = {}
    for doc in ready:
        by_author[doc.author_id].append(doc)
    author_items = by_author.items()
    author_items.sort(key=lambda item: len(item[1]), reverse=True)

    order = author_items[0][1]
    for author_id, docs in author_items[1:]:
        for doc in docs:
            best_pos = None
            best_pos_score = None
            for i in range(len(order) + 1):
                order.insert(i, doc)
                score = evaluate_order(order, recent, schedule)
                if score > best_pos_score:
                    best_pos = i
                    best_pos_score = score
                order.pop(i)
            order.insert(best_pos, doc)
    return order

def publish(doc, now=None):
    doc.date_written = now or datetime.now()
    doc.status = "published"
    doc.save()
    logger.info("... published Document {0}, {1}".format(doc.pk, doc.get_absolute_url()))

def build_schedule(count, interval, now=None):
    if now:
        # Clone now.
        cur = datetime(now.year, now.month, now.day, now.hour,
                       now.minute, now.second, now.microsecond, now.tzinfo)
    else:
        cur = datetime.now()
    schedule = []
    for i in range(count):
        schedule.append(cur)
        cur += interval
        while cur.hour < settings.PUBLISHING_HOURS[0] or \
                cur.hour > settings.PUBLISHING_HOURS[1]:
            cur += interval
    return schedule

def publish_ready(now=None):
    """
    Check for any ready-to-publish documents, and if they exist and there's
    been a sufficient interval since the last published, sort them and publish
    the most desired at the moment, taking into account the age of the document
    and how recently docs by that author had been published.

    Accepts optional 'now' as an argument to use rather than *real* now, to
    facilitate reliable testing outside publishing hours.
    """
    logger.info("Checking for ready-to-publish...")
    now = now or datetime.now()
    HOURS = settings.PUBLISHING_HOURS
    # Quit early if we're outside publishing hours.
    if now.hour < HOURS[0] or now.hour > HOURS[1]:
        logger.info("... not in publishing hours.")
        return
    ready = list(Document.objects.ready().order_by('created'))
    if len(ready) == 0:
        logger.info("... nothing to publish.")
        return
    recent = list(Document.objects.public().filter(
        type="post",
        date_written__gte=now - timedelta(days=settings.MAX_READY_TO_PUBLISH_DAYS)
    ).order_by('date_written'))
    oldest_date = ready[0].created
    deadline = oldest_date + timedelta(days=settings.MAX_READY_TO_PUBLISH_DAYS)
    if deadline <= now:
        logger.info("... Past Due!".format(ready[0].pk))
        publish(ready[0], now)
        return

    diff = deadline - now
    diff_hours = diff.seconds / 60. / 60. + diff.days * 24
    remaining_hours = diff_hours * (HOURS[1] - HOURS[0]) / 24.
    interval = timedelta(seconds=(remaining_hours*60*60. / len(ready)))
    if recent[-1].date_written + interval < now:
        logger.info("... building schedule")
        schedule = build_schedule(len(ready), interval, now)

        order = sort_ready(ready, recent, schedule)
        publish(order[0], now)
    else:
        logger.info("... waiting a little longer before publishing ({0} queued).".format(
            len(ready)
        ))

class Command(BaseCommand):
    args = ''
    help = 'Publish ready-to-publish documents, if ready.'

    def handle(self, *args, **options):
        publish_ready()
