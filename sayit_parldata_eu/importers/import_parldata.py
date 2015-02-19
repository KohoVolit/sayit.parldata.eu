from datetime import datetime
import locale

from django.core import management

from instances.models import Instance
from speeches.models import Section, Speech, Speaker

from . import vpapi

import logging
logger = logging.getLogger(__name__)

class ParldataImporter:
    def __init__(self, country_code, chamber_code, **options):
        self.api_url = 'http://api.parldata.eu'
        self.parliament = '%s/%s' %(country_code, chamber_code)
        self.initial_import = options.get('initial', False)
        self.verbosity = int(options.get('verbosity', 0))

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

        self.instance, _created = Instance.objects.get_or_create(label='default')

    def _vlog(self, msg):
        if self.verbosity > 0:
#            logger.info(msg)
            print(msg)

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
            defaults = {
                'name': person['name'][:128],
                'family_name': person.get('family_name', ''),
                'given_name': person.get('given_name', ''),
                'additional_name': person.get('additional_name', ''),
                'honorific_prefix': person.get('honorific_prefix', ''),
                'honorific_suffix': person.get('honorific_suffix', ''),
                'patronymic_name': person.get('patronymic_name', ''),
                'sort_name': person.get('sort_name', ''),
                'email': person.get('email'),
                'gender': person.get('gender', ''),
                'birth_date': person.get('birth_date', ''),
                'death_date': person.get('death_date', ''),
                'summary': person.get('summary', ''),
                'biography': person.get('biography', ''),
                'image': person.get('image'),
            }
            _record, created = update_object(
                Speaker.objects, person,
                identifiers__identifier=person['id'],
                defaults=defaults,
                instance=self.instance
            )
            count_c += created
            count_u += not created

        self._vlog('Imported %i persons (%i created, %i updated)' % (count_c+count_u, count_c, count_u))

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
        chamber = {}
        session = {}
        sitting = {}
        speech_objects = []
        for speech in updated_speeches:
            if speech['position'] > 50: continue  # DEBUG

            if speech['event_id'] != sitting.get('id'):
                # in case of initial import bulk create speeches when a new sitting occurs
                if self.initial_import:
                    Speech.objects.bulk_create(speech_objects)
                    speech_objects = []

                sitting = vpapi.get('events/%s' % speech['event_id'])

                # create/update new section corresponding to the chamber
                if sitting['organization_id'] != chamber.get('id'):
                    chamber = vpapi.get('organizations/%s' % sitting['organization_id'])
                    self._vlog('Importing chamber `%s`' % chamber['name'])
                    defaults = {
                        'heading': chamber.get('name'),
                        'start_date': chamber.get('founding_date'),
                        'legislature': chamber.get('name', ''),
                        'source_url': '%s/%s/organizations/%s' % (self.api_url, self.parliament, chamber['id']),
                    }
                    chamber_object, created = Section.objects.update_or_create(
                        source_url=defaults['source_url'],
                        defaults=defaults,
                        instance=self.instance
                    )
                    sec_count_c += created
                    sec_count_u += not created

                # create/update new section corresponding to the session
                if sitting['parent_id'] != session.get('id'):
                    session = vpapi.get('events/%s' % sitting['parent_id'])
                    if int(session['identifier']) > 5: break  # DEBUG
                    self._vlog('Importing session `%s`' % session['name'])
                    sd, st = local_date_time(session.get('start_date'))
                    defaults = {
                        'heading': session.get('name'),
                        'start_date': sd,
                        'start_time': st,
                        'legislature': chamber.get('name', ''),
                        'session': session.get('name', ''),
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

                # create/update new section corresponding to the sitting
                self._vlog('Importing sitting `%s`' % sitting['name'])
                sd, st = local_date_time(sitting.get('start_date'))
                defaults = {
                    'heading': sitting.get('name'),
                    'start_date': sd,
                    'start_time': st,
                    'legislature': chamber.get('name', ''),
                    'session': session.get('name', ''),
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

            # create/update the speech
            speaker = speakers.get(speech.get('creator_id'))
            sd, st = local_date_time(speech.get('date'))
            defaults = {
                'audio': speech.get('audio', ''),
                'text': speech.get('text', ''),
                'section': sitting_object,
                'event': '%s, %s, %s' % (chamber['name'], session['name'], sitting['name']),
                'speaker': speaker,
                'type': speech.get('type', 'speech'),
                'start_date': sd,
                'start_time': st,
                'source_url': '%s/%s/speeches/%s' % (self.api_url, self.parliament, speech['id']),
            }
            if speaker and speech.get('attribution_text'):
                defaults['speaker_display'] = '%s, %s' % (speaker.name, speech['attribution_text'])
            elif speech.get('attribution_text'):
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


def local_date_time(dtstr):
    if not dtstr:
        return None, None
    dt = vpapi.utc_to_local(dtstr, to_string=False)
    return dt.date(), dt.time()


def update_object(qs, data, defaults=None, **kwargs):
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
