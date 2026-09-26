import json

with open('mslearn_dp600_50q.json', 'r', encoding='utf-8') as f:
    qs = json.load(f)

for q in qs:
    txt = q['text'].lower()
    if 'productkey' in txt or 'productcategory' in txt or 'apply buttons' in json.dumps(q):
        print('=== ' + q['id'] + ' ===')
        print('Type:', q.get('type'))
        print('Text:', q['text'][:70] + '...')
        for opt in q['options']:
            print('  [' + opt['id'] + ']', opt['text'])
