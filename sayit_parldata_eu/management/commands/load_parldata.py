from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from sayit_parldata_eu.importers.import_parldata import ParldataImporter


class Command(BaseCommand):
    help = 'Imports new people and debates from api.parldata.eu.'

    option_list = BaseCommand.option_list + (
        make_option('--initial', action='store_true',
            help='Initial import, delete old data and bulk create new.'),
    )

    def handle(self, *args, **options):
        _prefix, country, chamber = settings.MEDIA_ROOT.rsplit('/', 2)
        importer = ParldataImporter(country, chamber, **options)
        importer.load_speakers()
        importer.load_debates()
