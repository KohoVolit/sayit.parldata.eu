import shutil
import subprocess

from django.core.management.base import BaseCommand
from django.conf import settings

from ._utils import get_subdomains
from sayit_parldata_eu.importers.import_parldata import ParldataImporter


class Command(BaseCommand):
    help = 'Refreshes cache of prerendered pages'

    def handle(self, *args, **options):
        if options.get('settings'):
            # refresh cache for the given subdomain
            shutil.rmtree(settings.CACHES['default']['LOCATION'], ignore_errors=True)
            importer = ParldataImporter(settings.COUNTRY_CODE, settings.PARLIAMENT_CODE, **options)
            importer.refresh_speakers_cache()
            importer.refresh_debates_cache()
        else:
            # refresh cache for all subdomains
            subdomains = get_subdomains()
            for sd in subdomains:
                subprocess.call(
                    '%s/bin/python %s/manage.py refresh_cache --settings subdomains.%s --verbosity %s' %
                    (settings.VIRTUALENV_DIR, settings.PROJECT_ROOT, sd, options['verbosity']), shell=True)
