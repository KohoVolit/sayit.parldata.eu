import subprocess
from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings

from ._utils import get_subdomains
from sayit_parldata_eu.importers.import_parldata import ParldataImporter


class Command(BaseCommand):
    help = 'Imports new people and debates from api.parldata.eu'

    option_list = BaseCommand.option_list + (
        make_option('--initial', action='store_true',
            help='Initial import, delete old data and bulk create new.'),
    )

    def handle(self, *args, **options):
        if options.get('settings'):
            # load data for the given subdomain
            importer = ParldataImporter(settings.COUNTRY_CODE, settings.PARLIAMENT_CODE, **options)
            importer.load_speakers()
            importer.load_debates()
            importer.update_search_index()
        else:
            # load data for all subdomains
            subdomains = get_subdomains()
            for sd in subdomains:
                try:
                    subprocess.call(
                        '%s/bin/python %s/manage.py load_parldata --settings subdomains.%s --verbosity %s' %
                        (settings.VIRTUALENV_DIR, settings.PROJECT_ROOT, sd, options['verbosity']), shell=True)
                except KeyboardInterrupt:
                    raise
                except:
                    # output to console to provoke an e-mail from Cron
                    print('SayIt data import failed for parliament %s.' % sd)
