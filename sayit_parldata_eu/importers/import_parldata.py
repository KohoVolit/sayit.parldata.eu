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

        # set country specific info obtained from VPAPI
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
            management.call_command('flush', verbosity=0, interactive=False)
            shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
            shutil.rmtree(settings.CACHES['default']['LOCATION'], ignore_errors=True)

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
            last_modified = latest_speaker.updated_at
        except IndexError:
            last_modified = datetime.min

        # update the people modified since the last import and create new ones
        updated_people = vpapi.getall(
            'people',
            where={'updated_at': {'$gt': last_modified.isoformat()}}
        )
        count_c = 0
        count_u = 0
        for person in updated_people:
            # FIXME: fix for currently flawed Kosovo and Albanian data
            if not person.get('name'): continue

            defaults = {
                'name': person['name'][:128],
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
                'image': urllib.parse.quote(person.get('image'), safe='/:'),
            }

            # FIXME: fix for currently flawed Serbian data
            if len(defaults['image']) >  200:
                defaults['image'] = None

            _record, created = _update_object(
                Speaker.objects, person,
                identifiers__identifier=person['id'],
                defaults=defaults,
                instance=self.instance
            )
            count_c += created
            count_u += not created

        self._vlog('Imported %i persons (%i created, %i updated)' % (count_c+count_u, count_c, count_u))

        self.refresh_speakers_cache()

    def load_debates(self):
        self._vlog('Importing debates')

        # get datetime of the last import of speeches
        try:
            latest_speech = Speech.objects.order_by('-modified')[0]
            last_modified = latest_speech.modified
        except IndexError:
            last_modified = datetime.min

        # update the speeches modified since the last import and create new ones
        updated_speeches = vpapi.getall(
            'speeches',
            where={'updated_at': {'$gt': last_modified.isoformat()}},
            sort='event_id,date,position'
        )

        # prepare mapping from source_id to Speaker objects
        speakers = {s.identifiers.filter(scheme='api.parldata.eu')[0].identifier: s
            for s in Speaker.objects.select_related('identifiers')}

        sec_count_c = 0
        sec_count_u = 0
        sp_count_c = 0
        sp_count_u = 0
        chamber, chamber_object = {}, None
        session, session_object = {}, None
        sitting, sitting_object = {}, None
        speech_objects = []
        updated_sections = []
        for speech in updated_speeches:
            if speech['event_id'] != sitting.get('id'):
                # in case of initial import bulk create speeches when a new sitting occurs
                if self.initial_import:
                    Speech.objects.bulk_create(speech_objects)
                    speech_objects = []

                sitting = vpapi.get('events/%s' % speech['event_id'])

                # create/update new section corresponding to the chamber
                if sitting['organization_id'] != chamber.get('id'):
                    chamber = vpapi.get('organizations/%s' % sitting['organization_id'])
                    self._vlog('Importing chamber `%s`' % chamber.get('name'))
                    defaults = {
                        'heading': chamber.get('name'),
                        'start_date': chamber.get('founding_date'),
                        'legislature': chamber.get('name') or '',
                        'source_url': '%s/%s/organizations/%s' % (self.api_url, self.parliament, chamber['id']),
                    }
                    chamber_object, created = Section.objects.update_or_create(
                        source_url=defaults['source_url'],
                        defaults=defaults,
                        instance=self.instance
                    )
                    sec_count_c += created
                    sec_count_u += not created
                    updated_sections.append(chamber_object)

                # create/update new section corresponding to eventual session
                if not sitting.get('parent_id'):
                    session = {}
                    session_object = chamber_object
                else:
                    if sitting['parent_id'] != session.get('id'):
                        session = vpapi.get('events/%s' % sitting['parent_id'])
                        self._vlog('Importing session `%s`' % session.get('name'))
                        sd, st = _local_date_time(session.get('start_date'))
                        defaults = {
                            'heading': session.get('name'),
                            'start_date': sd,
                            'start_time': st,
                            'legislature': chamber.get('name') or '',
                            'session': session.get('name') or '',
                            'parent': chamber_object,
                            'source_url': '%s/%s/events/%s' % (self.api_url, self.parliament, session['id']),
                        }
                        session_object, created = Section.objects.update_or_create(
                            source_url=defaults['source_url'],
                            defaults=defaults,
                            instance=self.instance
                        )
                        sec_count_c += created
                        sec_count_u += not created
                        updated_sections.append(session_object)

                # create/update new section corresponding to the sitting
                self._vlog('Importing sitting `%s`' % sitting.get('name'))
                sd, st = _local_date_time(sitting.get('start_date'))
                defaults = {
                    'heading': sitting.get('name'),
                    'start_date': sd,
                    'start_time': st,
                    'legislature': chamber.get('name') or '',
                    'session': session.get('name') or '',
                    'parent': session_object,
                    'source_url': '%s/%s/events/%s' % (self.api_url, self.parliament, sitting['id']),
                }
                sitting_object, created = Section.objects.update_or_create(
                    source_url=defaults['source_url'],
                    defaults=defaults,
                    instance=self.instance
                )
                sec_count_c += created
                sec_count_u += not created
                updated_sections.append(sitting_object)

            # create/update the speech
            speaker = speakers.get(speech.get('creator_id'))
            start = speech.get('date') or \
                sitting.get('start_date') or session.get('start_date') or chamber.get('founding_date')
            sd, st = _local_date_time(start)
            defaults = {
                'audio': speech.get('audio', ''),
                'text': speech.get('text', ''),
                'section': sitting_object,
                'event': '%s, %s, %s' % (chamber.get('name'), session.get('name'), sitting.get('name')),
                'speaker': speaker,
                'type': speech.get('type', 'speech'),
                'start_date': sd,
                'start_time': st,
                'source_url': '%s/%s/speeches/%s' % (self.api_url, self.parliament, speech['id']),
            }
            if speech.get('attribution_text'):
                # FIXME: there are false attribution texts in Slovak and Albanian data
                if len(speech['attribution_text']) < 100:
                    if speaker:
                        defaults['speaker_display'] = '%s, %s' % (speaker.name, speech['attribution_text'])
                    else:
                        defaults['speaker_display'] = speech['attribution_text']

            if self.initial_import:
                speech_object = Speech(instance=self.instance, **defaults)
                speech_objects.append(speech_object)
                created = True
            else:
                speech_object, created = Speech.objects.update_or_create(
                    source_url=defaults['source_url'],
                    defaults=defaults,
                    instance=self.instance
                )
            sp_count_c += created
            sp_count_u += not created

        # create speeches of the last sitting when doing initial import
        if self.initial_import:
            Speech.objects.bulk_create(speech_objects)

        self._vlog('Imported %i sections (%i created, %i updated) and %i speeches (%i created, %i updated)' % (
            sec_count_c+sec_count_u, sec_count_c, sec_count_u,
            sp_count_c+sp_count_u, sp_count_c, sp_count_u))

        self.refresh_debates_cache(updated_sections)

    def refresh_speakers_cache(self):
        self._vlog('Refreshing speakers list cache')
        self._refresh_cache('/')
        self._refresh_cache('/speakers')
        self._vlog('Refreshed')

    def refresh_debates_cache(self, sections=None):
        self._vlog('Refreshing sections cache')
        self._refresh_cache('/')
        self._refresh_cache('/speeches')
        if sections is None:
            sections = Section.objects.all()
        for section in sections:
            self._vlog('Refreshing cache for section `%s`' % section.heading)
            self._refresh_cache(section.get_absolute_url())
        self._vlog('Refreshed cache for %s sections' % len(sections))


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
                url=item['url'],
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
                    url=src['url'],
                    defaults={'note': src.get('note', '')}
                )

    return record, created
