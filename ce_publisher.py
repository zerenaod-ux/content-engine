"""How It Ticks publisher. DRY-RUN unless PUBLISH_LIVE=1 (repo variable). Only videos the owner APPROVED (folder 'saved' in data/scenes/review/index.json) are posted.
Gives each approved video the next free slot per platform in Buffer (posting-slots.json), never double-posts (publish/state.json remembers every video handed to Buffer)."""
import json, os, sys, datetime, urllib.request, urllib.error
from pathlib import Path
from zoneinfo import ZoneInfo
B = Path(__file__).resolve().parent
CFG = json.loads((B / 'posting-slots.json').read_text())
CHANNELS = {'youtube': '6afa575fece6dfde5fdc5616', 'instagram': '6afa5728ece6dfde5fdc52a3', 'tiktok': '6afa56beece6dfde5fdc4be8'}   # Buffer channel ids (no secrets)
LIVE = os.environ.get('PUBLISH_LIVE') == '1'
TOKEN = os.environ.get('BUFFER_TOKEN', '').strip()
STATE = B / 'publish' / 'state.json'
MAX_CREATES = int(os.environ.get('PUBLISH_MAX', '6'))
TAGS = '#howitticks #explained #science #howthingswork'

def api(doc, variables=None):
    req = urllib.request.Request('https://api.buffer.com', json.dumps({'query': doc, 'variables': variables or {}}).encode(),
                                 {'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return json.load(e)

def load(p, d):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return d

def free_slots(platform, taken, now):
    tz = ZoneInfo(CFG.get('timezone', 'America/Chicago'))
    earliest = now.astimezone(tz) + datetime.timedelta(minutes=int(CFG.get('min_lead_minutes', 10)))
    out = []
    for off in range(0, 15):
        day = (now.astimezone(tz) + datetime.timedelta(days=off)).date()
        for t in CFG['slots'].get(platform, []):
            h, m = [int(x) for x in t.split(':')]
            s = datetime.datetime(day.year, day.month, day.day, h, m, tzinfo=tz)
            if s >= earliest:
                out.append(s.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z'))
    return [s for s in sorted(out) if s not in taken]

def video_url(tag):   # public, direct mp4 (Buffer must fetch it): jsDelivr copy on gh-pages (made at build time)
    return 'https://cdn.jsdelivr.net/gh/zerenaod-ux/content-engine@gh-pages/videos/%s.mp4' % tag

def main():
    if not CFG.get('enabled', True):
        print('posting disabled in posting-slots.json'); return
    idx = load(B / 'data/scenes/review/index.json', {'items': []})
    approved = [i for i in idx.get('items', []) if i.get('folder') == 'saved']
    state = load(STATE, {'done': {}})
    now = datetime.datetime.now(datetime.timezone.utc)
    held = {p: [] for p in CHANNELS}
    if TOKEN:
        orgs = ((api('{account{organizations{id}}}').get('data') or {}).get('account') or {}).get('organizations') or []
        org = orgs[0]['id'] if orgs else ''
        res = api('query($i:PostsInput!){posts(first:100,input:$i){edges{node{channelService dueAt status}}}}',
                  {'i': {'organizationId': org, 'filter': {'channelIds': list(CHANNELS.values()), 'status': ['scheduled', 'sending']}}})
        if res.get('errors') and not res.get('data'):
            print('Buffer read failed:', json.dumps(res)[:300]); sys.exit(1)
        for e in ((res.get('data') or {}).get('posts') or {}).get('edges', []):
            n = e['node']
            if n['channelService'] in held and n.get('dueAt'):
                held[n['channelService']].append(n['dueAt'][:19] + '.000Z')
    else:
        print('No BUFFER_TOKEN: planning without Buffer data.')
    cap = int(CFG.get('buffer_queue_limit', 6))
    plan = []
    for plat in CHANNELS:
        taken = set(held[plat]); room = max(0, cap - len(held[plat]))
        waiting = [i for i in approved if '%s/%s' % (i['tag'], plat) not in state['done']]
        for item in waiting[:room]:
            slots = free_slots(plat, taken, now)
            if not slots: break
            taken.add(slots[0]); plan.append((plat, item, slots[0]))
    print('%s: approved %d | Buffer holds %s | would schedule %d' % ('LIVE' if LIVE else 'DRY-RUN', len(approved), {k: len(v) for k, v in held.items()}, len(plan)))
    creates = 0
    for plat, item, due in plan:
        title = item.get('title') or ''
        print('  ', plat, due, title[:50])
        if not LIVE or creates >= MAX_CREATES: continue
        meta = {'youtube': {'title': title[:100], 'privacy': 'public', 'madeForKids': False, 'notifySubscribers': True, 'categoryId': '27'},
                'instagram': {'type': 'reel', 'shouldShareToFeed': True}, 'tiktok': {'title': title[:90]}}[plat]
        inp = {'channelId': CHANNELS[plat], 'text': title + '\n\n' + TAGS, 'schedulingType': 'automatic', 'mode': 'customScheduled', 'needsApproval': False,
               'saveToDraft': False, 'assets': [{'video': {'url': video_url(item['tag']), 'metadata': {'thumbnailOffset': 1000}}}], 'metadata': {plat: meta}, 'dueAt': due}
        r = api('mutation($input:CreatePostInput!){createPost(input:$input){... on PostActionSuccess{post{id status dueAt}} ... on MutationError{message}}}', {'input': inp})
        cp = ((r.get('data') or {}).get('createPost') or {}); creates += 1
        if cp.get('post'):
            state['done']['%s/%s' % (item['tag'], plat)] = {'remote': cp['post']['id'], 'due': due, 'at': now.isoformat(timespec='seconds')}
            STATE.parent.mkdir(exist_ok=True); STATE.write_text(json.dumps(state, indent=1)); print('    sent', cp['post']['id'])
        else:
            print('    NOT sent:', json.dumps(r)[:200])
            if 'limit' in json.dumps(r).lower() or 'allowance' in json.dumps(r).lower(): break

if __name__ == '__main__':
    main()
