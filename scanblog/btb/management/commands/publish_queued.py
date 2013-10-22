import datetime
import logging

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from scanning.models import Document

__all__ = ('Command',)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    args = ''
    help = 'Publish ready-to-publish documents, if ready.'

    def handle(self, *args, **options):
        try:
            logger.info("Checking for ready-to-publish...")
            now = datetime.datetime.now()
            HOURS = settings.PUBLISHING_HOURS
            if now.hour < HOURS[0] or now.hour > HOURS[1]:
                logger.info("... not in publishing hours.")
                return
            count = Document.objects.ready().count()
            if count == 0:
                logger.info("... nothing to publish.")
                return
            oldest_ready = Document.objects.ready()[0]
            last_published = Document.objects.filter(
                status="published", type="post"
            ).order_by('-modified')[0]

            deadline = oldest_ready.created + datetime.timedelta(days=settings.MAX_READY_TO_PUBLISH_DAYS)
            diff = deadline - now
            diff_hours = diff.seconds / 60. / 60. + diff.days * 24
            remaining_hours = diff_hours * (HOURS[1] - HOURS[0]) / 24.
            interval = datetime.timedelta(seconds=(remaining_hours*60*60. / count))
            if deadline < now or now > (last_published.modified + interval):
                oldest_ready.status = "published"
                oldest_ready.date_written  = now
                oldest_ready.save()
                logger.info("... published %s. (%s queued)" % (oldest_ready.pk, count))
            else:
                logger.info("... waiting a little more (%s queued)" % count)
        except Exception:
            logger.exception("Problem publishing ready-to-publish documents.")
            raise

#
# The following is a test of the above algorithm.
#

# A mock document object which just tracks created, modified, and published.
class Doc(object):
    MAX_AGE = datetime.timedelta(days=6)
    PUBLISHING_HOURS = (7, 23) # min and max clock hours for publishing

    def __init__(self, created, published):
        self.created = datetime.datetime.strptime(created, "%Y-%m-%d %H:%M")
        self.modified = datetime.datetime.strptime(created, "%Y-%m-%d %H:%M")
        self.published = published

    def publish(self, date):
        self.published = True
        self.modified = date

# The publishing algorithm.
def publish_ready(now, docs):
    if now.hour < Doc.PUBLISHING_HOURS[0] or now.hour > Doc.PUBLISHING_HOURS[1]:
        return False

    # The equivalent of Document.objects.ready()
    ready = []
    last_published = None
    for doc in docs:
        if doc.created > now:
            continue
        if not doc.published:
            ready.append(doc)
        else:
            last_published = doc
    if len(ready) == 0:
        return False
    oldest_ready = ready[0]
    count = len(ready)

    # Determine if we should publish.
    deadline = oldest_ready.created + Doc.MAX_AGE
    remaining_hours = ((deadline - now).total_seconds() / 60. / 60.) * \
                      (Doc.PUBLISHING_HOURS[1] - Doc.PUBLISHING_HOURS[0]) / 24.
    interval = datetime.timedelta(seconds=(remaining_hours*60*60. / count))
    if deadline < now or now > (last_published.modified + interval):
        oldest_ready.publish(now)
    return interval

# Run the simulation -- starting time is the earliest document, ending time is
# when all have been published.
def sim(docs):
    now = docs[0].created
    remaining = len([doc for doc in docs if not doc.published])
    while True:
        for doc in docs:
            if not doc.published:
                break # for loop
        else:
            break # while loop
        now = now + datetime.timedelta(seconds=60*60)
        interval = publish_ready(now, docs)
        new_remaining = len([doc for doc in docs if not doc.published])
        published_one = "*" if new_remaining != remaining else " "
        remaining = new_remaining
        if published_one == "*":
            print now.strftime("%Y-%m-%d.%H:%M"), published_one, remaining, interval

if __name__ == "__main__":
    sim([
        Doc("2011-01-01 02:00", True),
        Doc("2011-01-01 02:00", False),
        Doc("2011-01-01 02:00", False),
        Doc("2011-01-01 02:00", False),
        Doc("2011-01-01 02:00", False),
        Doc("2011-01-01 02:00", False),
        Doc("2011-01-01 02:00", False),
        Doc("2011-01-01 02:00", False),
        Doc("2011-01-01 02:00", False),
        Doc("2011-01-01 02:00", False),
        Doc("2011-01-01 02:00", False),
        Doc("2011-01-01 02:00", False),
        Doc("2011-01-01 02:00", False),
        Doc("2011-01-01 02:00", False),
        Doc("2011-01-01 02:00", False),
        Doc("2011-01-01 02:00", False),
        #Doc("2011-01-05 08:00", False),
    ])

