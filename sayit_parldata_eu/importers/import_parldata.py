from datetime import datetime
import locale
import logging
import os
import shutil
import requests
import urllib.parse

from django.core import management
from django.http import HttpRequest
from django.core.cache import cache
from django.utils.cache import get_cache_key
from django.conf import settings

from instances.models import Instance
from speeches.models import Section, Speech, Speaker

from . import vpapi

API_DATE_FORMAT = '%4Y-%m-%dT%H:%M:%S'
LOGS_DIR = '/var/log/sayit/import'
logger = logging.getLogger(__name__)

class ParldataImporter:
    def __init__(self, country_code, chamber_code, **options):
        self.api_url = 'http://api.parldata.eu'
        self.parliament = '%s/%s' %(country_code, chamber_code)
        self.subdomain = '%s.%s' %(chamber_code, country_code)
        self.initial_import = options.get('initial', False)
        self.verbosity = int(options.get('verbosity', 1))

        # set-up logging to a file
        logpath = os.path.join(LOGS_DIR, self.parliament)
        os.makedirs(logpath, exist_ok=True)
        logname = datetime.utcnow().strftime('%Y-%m-%d-%H%M%S') + '.log'
        logname = os.path.abspath(os.path.join(logpath, logname))
        handler = logging.FileHandler(logname, 'w', 'utf-8')
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        # set country specific info obtained from API
        resp = vpapi.get('')
        for country in resp['_links']['child']:
            if country['href'] == country_code:
                locale.setlocale(locale.LC_ALL, country['locale'])
                vpapi.timezone(country['timezone'])
                break
        vpapi.parliament(self.parliament)

        # in case of initial import delete all existing data
        if self.initial_import:
            self._vlog('Deleting all existing data')
            management.call_command('flush', verbosity=self.verbosity, interactive=False)
            shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
            shutil.rmtree(settings.CACHES['default'].get('LOCATION'), ignore_errors=True)

        self.instance, _created = Instance.objects.get_or_create(label='default')

    def _vlog(self, msg):
        if self.verbosity > 0:
            logger.info(msg)

    def _refresh_cache(self, path):
        host = self.subdomain + settings.ALLOWED_HOSTS[0]

        # delete cache key correspoding to a typical request
        request = HttpRequest()
        request.method = 'GET'
        request.path = path
        if settings.USE_I18N:
            request.LANGUAGE_CODE = settings.LANGUAGE_CODE
        request.META = {
            'HTTP_HOST': host,
            'HTTP_ACCEPT_ENCODING': 'gzip, deflate'
        }
        key = get_cache_key(request)
        cache.delete(key)

        # request the page to recreate the deleted cache key
        resp = requests.get(
            'http://%s%s' % (host, path),
            headers={'accept-encoding': 'gzip, deflate'}
        )

    def load_speakers(self):
        self._vlog('Importing speakers')

        # get datetime of the last import of speakers
        try:
            latest_speaker = Speaker.objects.order_by('-updated_at')[0]
            self.previous_speakers_import_at = latest_speaker.updated_at
        except IndexError:
            self.previous_speakers_import_at = datetime.min

        # update the people modified since the last import and create new ones
        updated_people = vpapi.getall(
            'people',
            where={'updated_at': {'$gt': self.previous_speakers_import_at.strftime(API_DATE_FORMAT)}}
        )
        count_c = 0
        count_u = 0
        for person in updated_people:
            defaults = {
                'name': person.get('name', '')[:128] or person['id'],
                'family_name': person.get('family_name') or '',
                'given_name': person.get('given_name') or '',
                'additional_name': person.get('additional_name') or '',
                'honorific_prefix': person.get('honorific_prefix') or '',
                'honorific_suffix': person.get('honorific_suffix') or '',
                'patronymic_name': person.get('patronymic_name') or '',
                'sort_name': person.get('sort_name') or '',
                'email': person.get('email'),
                'gender': person.get('gender') or '',
                'birth_date': person.get('birth_date') or '',
                'death_date': person.get('death_date') or '',
                'summary': person.get('summary') or '',
                'biography': person.get('biography') or '',
                'image': urllib.parse.quote(person.get('image', ''), safe=':/%'),
            }

            _record, created = _update_object(
                Speaker.objects, person,
                identifiers__identifier=person['id'],
                instance=self.instance,
                defaults=defaults
            )
            count_c += created
            count_u += not created

        self._vlog('Imported %i persons (%i created, %i updated)' % (count_c+count_u, count_c, count_u))

        self.refresh_speakers_cache()

    def _update_speech_sections(self, speech):
        """Creates or updates sections corresponding to the event where
        the speech occured and all its parent sections.
        Returns the event of the speech, the corresponding section,
        event title to use in speech objects and datetime of the event
        (or its parents)."""
        # create a list of all (parent-)events the speech belongs to
        events = []
        event_id = speech['event_id']
        while event_id:
            event = vpapi.get('events/%s' % event_id)
            events.append(event)
            event_id = event.get('parent_id')

        self._vlog('Importing speeches to section `%s`' % events[0].get('name'))

        section = None
        event_title = ''
        event_date = None

        # create/update section corresponding to the chamber
        org_id = events[0].get('organization_id')
        if org_id:
            org = vpapi.get('organizations/%s' % org_id)
            defaults = {
                'heading': org.get('name') or '',
                'start_date': org.get('founding_date'),
                'legislature': org.get('name') or '',
                'source_url': '%s/%s/organizations/%s' % (self.api_url, self.parliament, org['id']),
            }
            section, created = Section.objects.update_or_create(
                source_url=defaults['source_url'],
                instance=self.instance,
                defaults=defaults
            )
            if created:
                self._vlog('Created section `%s`' % org.get('name'))
            event_title = org.get('name', '')
            event_date = org.get('founding_date')

        # create/update all (parent-)sections the speech belongs to
        session = {}
        for event in reversed(events):
            if event.get('type') == 'session':
                session = event
            sd, st = _local_date_time(event.get('start_date'))
            defaults = {
                'heading': event.get('name') or '',
                'start_date': sd,
                'start_time': st,
                'legislature': org.get('name') or '',
                'session': session.get('name') or '',
                'parent': section,
                'source_url': '%s/%s/events/%s' % (self.api_url, self.parliament, event['id']),
            }
            section, created = Section.objects.update_or_create(
                source_url=defaults['source_url'],
                instance=self.instance,
                defaults=defaults
            )
            if created:
                self._vlog('Created section `%s`' % event.get('name'))
            event_title += (', ' if event_title else '') + event.get('name', '')
            event_date = event.get('start_date') or event_date

        return event, section, event_title, event_date

    def load_debates(self):
        self._vlog('Importing debates')

        # get datetime of the last import of speeches
        try:
            latest_speech = Speech.objects.order_by('-modified')[0]
            self.previous_debates_import_at = latest_speech.modified
        except IndexError:
            self.previous_debates_import_at = datetime.min

        # update the speeches modified since the last import and create new ones
        updated_speeches = vpapi.getall(
            'speeches',
            where={'updated_at': {'$gt': self.previous_debates_import_at.strftime(API_DATE_FORMAT)}},
            sort='event_id,date,position'
        )

        # prepare mapping from source_id to Speaker objects
        speakers = {s.identifiers.filter(scheme='api.parldata.eu')[0].identifier: s
            for s in Speaker.objects.select_related('identifiers')}

        speech_objects = []
        event = {}
        for speech in updated_speeches:
            if not speech.get('event_id'):
                continue
            if speech['event_id'] != event.get('id'):
                if self.initial_import:
                    Speech.objects.bulk_create(speech_objects)
                    speech_objects = []

                event, section, event_title, event_date = self._update_speech_sections(speech)

            # create/update the speech
            speaker = speakers.get(speech.get('creator_id'))
            start = speech.get('date') or event_date
            sd, st = _local_date_time(start)
            defaults = {
                'audio': speech.get('audio', ''),
                'text': speech.get('text', ''),
                'section': section,
                'event': event_title,
                'speaker': speaker,
                'type': speech.get('type', 'speech'),
                'start_date': sd,
                'start_time': st,
                'source_url': '%s/%s/speeches/%s' % (self.api_url, self.parliament, speech['id']),
            }
            if speech.get('attribution_text'):
                # FIXME: there are wrong attribution texts in some parliaments
                if not (self.parliament in ('al/kuvendi', 'kv/kuvendi', 'rs/skupstina') or
                        self.parliament == 'sk/nrsr' and len(speech['attribution_text']) > 80):
                    if speaker:
                        defaults['speaker_display'] = '%s, %s' % (speaker.name, speech['attribution_text'])
                    else:
                        defaults['speaker_display'] = speech['attribution_text']

            if self.initial_import:
                speech_object = Speech(instance=self.instance, **defaults)
                speech_objects.append(speech_object)
            else:
                speech_object, _created = Speech.objects.update_or_create(
                    source_url=defaults['source_url'],
                    instance=self.instance,
                    defaults=defaults
                )

        # create speeches of the last section when doing initial import
        if self.initial_import:
            Speech.objects.bulk_create(speech_objects)

        # show some statistcics
        modified_sections = Section.objects.filter(modified__gt=self.previous_debates_import_at).count()
        new_sections = Section.objects.filter(created__gt=self.previous_debates_import_at).count()

        modified_speeches = Speech.objects.filter(modified__gt=self.previous_debates_import_at).count()
        new_speeches = Speech.objects.filter(created__gt=self.previous_debates_import_at).count()

        self._vlog('Imported %i sections (%i created, %i updated) and %i speeches (%i created, %i updated)' % (
            modified_sections, new_sections, modified_sections-new_sections,
            modified_speeches, new_speeches, modified_speeches-new_speeches)
        )

        self.refresh_debates_cache(self.previous_debates_import_at)

    def refresh_speakers_cache(self):
        self._vlog('Refreshing speakers list cache')
        self._refresh_cache('/')
        self._refresh_cache('/speakers')
        self._vlog('Refreshed')

    def refresh_debates_cache(self, since_date=datetime.min):
        self._vlog('Refreshing sections cache')
        self._refresh_cache('/')
        self._refresh_cache('/speeches')
        sections = Section.objects.filter(modified__gte=since_date)
        for section in sections:
            self._vlog('Refreshing cache for section `%s`' % section.heading)
            self._refresh_cache(section.get_absolute_url())
        self._vlog('Refreshed cache for %s sections' % len(sections))

    def update_search_index(self):
        update_since = min(self.previous_speakers_import_at, self.previous_debates_import_at)
        self._vlog('Updating search index since %s' % update_since)
        management.call_command(
            'update_index', start_date=update_since.isoformat(), verbosity=self.verbosity, interactive=False)
        self._vlog('Updated')


def _local_date_time(dtstr):
    if not dtstr:
        return None, None
    dt = vpapi.utc_to_local(dtstr, to_string=False)
    return dt.date(), dt.time()


def _update_object(qs, data, defaults=None, **kwargs):
    # update or create the object itself
    record, created = qs.update_or_create(defaults=defaults, **kwargs)

    # update or create related objects for links and sources
    for l in ('sources', 'links'):
        for item in data.get(l, []):
            rel = getattr(record, l)
            rel.update_or_create(
                url=item['url'][:200],  # django-popolo limit is 200 chars
                defaults={'note': item.get('note', '')}
            )

    # in case of speakers update or create related objects for
    # identifiers, other_names and contact details,
    if qs.model == Speaker:
        record.identifiers.update_or_create(
            identifier=data['id'],
            scheme='api.parldata.eu',
        )
        for i in data.get('identifiers', []):
            record.identifiers.update_or_create(
                identifier=i['identifier'],
                scheme=i.get('scheme', ''),
            )
        for name in data.get('other_names', []):
            record.other_names.update_or_create(
                name=name['name'],
                defaults={'note': name.get('note', '')},
            )
        for cd in data.get('contact_details', []):
            subrec = record.contact_details.update_or_create(
                label = cd.get('label', ''),
                start_date = cd.get('start_date'),
                defaults={
                    'contact_type': cd['type'],
                    'value': cd['value'],
                    'note': cd.get('note', ''),
                    'end_date': cd.get('end_date'),
                }
            )
            for src in cd.get('sources', []):
                subrec.sources.update_or_create(
                    url=src['url'][:200],
                    defaults={'note': src.get('note', '')}
                )

    return record, created
