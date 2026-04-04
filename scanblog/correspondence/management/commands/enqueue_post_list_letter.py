from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from correspondence.models import Letter


class Command(BaseCommand):
    help = 'Enqueue a letter listing all published posts for a given author.'

    def add_arguments(self, parser):
        parser.add_argument('author_id', type=int)

    def handle(self, *args, **options):
        author_id = options['author_id']

        try:
            user = User.objects.get(pk=author_id)
        except User.DoesNotExist:
            self.stderr.write("User with id %s does not exist." % author_id)
            return

        org = user.organization_set.first()
        if org is None:
            self.stderr.write("User %s has no organization." % user.username)
            return

        sender = org.moderators.first()
        if sender is None:
            self.stderr.write("Organization '%s' has no moderators." % org.name)
            return

        letter = Letter.objects.create(
            type="post_list",
            recipient=user,
            sender=sender,
            org=org,
            auto_generated=True,
        )
        self.stdout.write("Created post_list letter %d for %s." % (letter.pk, user.profile.display_name))
