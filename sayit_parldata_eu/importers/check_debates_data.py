# Check quality of debates data at api.parldata.eu for all available
# parliaments and write an audit report to a file.

import os
from collections import OrderedDict
import vpapi

OUTPUT_FILE = 'debates_data.txt'

# collect all parliaments in the API
parliaments = []
countries = vpapi.get('')
for c in countries['_links']['child']:
    c_parls = vpapi.get(c['href'])
    for p in c_parls['_links']['child']:
        parliaments.append('%s/%s' % (c['href'], p['href']))

print('Found %i parliaments' % len(parliaments))

# remove old file
if os.path.isfile(OUTPUT_FILE):
    os.remove(OUTPUT_FILE)

# audit all parliaments
for parl in parliaments:
    print('Checking %s...' % parl)
    vpapi.parliament(parl)
    r = OrderedDict()
    r['events'] = vpapi.get('events')
    r['sessions'] = vpapi.get('events', where={'type': 'session'})
    r['sittings'] = vpapi.get('events', where={'type': 'sitting'})
    r['sitting parts'] = vpapi.get('events', where={'type': 'sitting part'})
    r['unknown type events'] = vpapi.get('events', where={'type': {'$nin': [None, '', 'session','sitting','sitting part']}})
    r['events without type'] = vpapi.get('events', where={'$or': [{'type': {'$exists': False}}, {'type': {'$in': [None, '']}}]})
    r['events without start date'] = vpapi.get('events', where={'$or': [{'start_date': {'$exists': False}}, {'start_date': {'$in': [None, '']}}]})
    r['events without organization'] = vpapi.get('events', where={'$or': [{'organization_id': {'$exists': False}}, {'organization_id': {'$in': [None, '']}}]})
    r['events without name'] = vpapi.get('events', where={'$or': [{'name': {'$exists': False}}, {'name': {'$in': [None, '']}}]})
    r['events without parent'] = vpapi.get('events', where={'$or': [{'parent_id': {'$exists': False}}, {'parent_id': {'$in': [None, '']}}]})
    r['all speeches'] = vpapi.get('speeches')
    r['speeches'] = vpapi.get('speeches', where={'type': 'speech'})
    r['questions'] = vpapi.get('speeches', where={'type': 'question'})
    r['answers'] = vpapi.get('speeches', where={'type': 'answer'})
    r['scenes'] = vpapi.get('speeches', where={'type': 'scene'})
    r['narratives'] = vpapi.get('speeches', where={'type': 'narrative'})
    r['summaries'] = vpapi.get('speeches', where={'type': 'summary'})
    r['others'] = vpapi.get('speeches', where={'type': 'other'})
    r['unknown type speeches'] = vpapi.get('speeches', where={'type': {'$exists': True, '$nin': [None, '', 'speech','question','answer','scene','narrative','summary','other']}})
    r['speeches without type'] = vpapi.get('speeches', where={'$or': [{'type': {'$exists': False}}, {'type': {'$in': [None, '']}}]})
    r['speeches without date'] = vpapi.get('speeches', where={'$or': [{'date': {'$exists': False}}, {'date': {'$in': [None, '']}}]})
    r['speeches without text'] = vpapi.get('speeches', where={'$or': [{'text': {'$exists': False}}, {'text': {'$in': [None, '']}}]})
    r['speeches without event'] = vpapi.get('speeches', where={'$or': [{'event_id': {'$exists': False}}, {'event_id': {'$in': [None, '']}}]})

    # write result for a parliament
    with open(OUTPUT_FILE, 'a') as f:
        f.write('\n\n%s' % parl)
        for k, v in r.items():
            f.write('\n    %s: %i' % (k, v['_meta']['total']))
