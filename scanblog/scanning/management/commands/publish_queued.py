from datetime import datetime, timedelta
from collections import defaultdict
import logging

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from scanning.models import Document

__all__ = ('Command',)
logger = logging.getLogger(__name__)

def calculate_pressure(ready, recent):
    pressure = defaultdict(int)
    def _add_pressure(i, remaining):
        for j in range(i, len(remaining)):
            pressure[remaining[j].author_id] += 1
    # Count historical pressure
    for i in range(len(recent)):
        _add_pressure(i, recent) # add the past..
        _add_pressure(0, ready)  # and add the future.
        pressure[recent[i].author_id] = 0
    _add_pressure(0, ready)
    return pressure

def next_by_pressure(ready, recent):
    """
    'Pressure' is a strategy for ordering ready-to-publish documents based on
    the number of posts each other has remaining.  The algorithm works like
    this: Associate each author with a quantity called "pressure", which is
    initialized to 0.  Each time you're ready to publish a post:

        1. Increase every author's pressure by an amount equal to the number of
        unpublished posts from that author.
        2. Publish from the author with the highest pressure. Then set that
        author's pressure to 0.

    Ties of pressure are broken by taking the first author of the tie who was
    not published immediately prior.

    This results in a decent, though not optimal ordering. It has the advantage
    of being conceptually simple, deterministic, and relatively computationally
    light.

    Rather than persist another value in the database for each author, we calculate
    current pressure based on the recent history of posts, regardless of how those
    posts were published.
    """
    pressure = calculate_pressure(ready, recent)
    max_pressure = None
    max_author = None
    for author_id, pressure in pressure.iteritems():
        # Get argmax, but solve ties by avoiding repeat of previous author
        if pressure > max_pressure or (
                pressure == max_pressure and recent and recent[-1].author_id == max_author):
            max_pressure = pressure
            max_author = author_id
    for doc in ready:
        if doc.author_id == max_author:
            return doc

def publish(doc, now=None):
    doc.date_written = now or datetime.now()
    doc.status = "published"
    doc.save()
    logger.info("... published Document {0}, {1}".format(doc.pk, doc.get_absolute_url()))

def calculate_interval(ready, now):
    oldest_date = ready[0].created
    deadline = oldest_date + timedelta(days=settings.MAX_READY_TO_PUBLISH_DAYS)
    if now >= deadline:
        return timedelta(seconds=0)
    diff = deadline - now
    diff_days = diff.days + diff.seconds / 60. / 60. / 24.
    hours_per_day = settings.PUBLISHING_HOURS[1] - settings.PUBLISHING_HOURS[0]
    remaining_hours = diff_days * hours_per_day
    interval = timedelta(seconds=(remaining_hours*60*60. / len(ready)))
    return interval

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
        return None
    # Quit early if there's nothing to publish.
    ready = list(Document.objects.ready().order_by('created'))
    if len(ready) == 0:
        logger.info("... nothing to publish.")
        return None

    interval = calculate_interval(ready, now)
    if not interval:
        logger.info("... Past Due!".format(ready[0].pk))
        doc = ready[0]
        publish(doc, now)
        return doc

    # Get the things published in the last week.
    recent = list(Document.objects.public().filter(
        type="post",
        date_written__gte=now - timedelta(days=settings.MAX_READY_TO_PUBLISH_DAYS)
    ).order_by('date_written'))

    if len(recent) == 0 or now > recent[-1].date_written + interval:
        logger.info("... calculating pressure")
        doc = next_by_pressure(ready, recent)
        publish(doc, now)
        return doc
    else:
        logger.info("... waiting a little longer before publishing ({0} queued).".format(
            len(ready)
        ))
        return None

class Command(BaseCommand):
    args = ''
    help = 'Publish ready-to-publish documents, if ready.'

    def handle(self, *args, **options):
        publish_ready(datetime.now())
