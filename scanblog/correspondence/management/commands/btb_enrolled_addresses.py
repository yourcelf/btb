import csv

from django.core.management.base import BaseCommand

from profiles.models import Profile
from correspondence.utils import UnicodeWriter

class Command(BaseCommand):
    args = 'destination filename'
    help = 'Print out a csv format address list of all enrolled writers.'

    def handle(self, *args, **kwargs):
        if len(args) != 1:
            raise Exception("Requires one argument, the name of the destination file.")
        dest = args[0]

        addresses = []
        max_length = 0
        for person in Profile.objects.enrolled().order_by('display_name'):
            address_parts = [a.strip() for a in person.full_address().split("\n")]
            addresses.append(address_parts)
            max_length = max(max_length, len(address_parts))

        with open(args[0], 'w') as fh:
            writer = UnicodeWriter(fh, quoting=csv.QUOTE_ALL)
            for addy in addresses:
                addy = [""] * (max_length - len(addy)) + addy
                writer.writerow(addy)
