"""HOW IT TICKS AUTOPILOT. publish/ce-autopilot.json is the single switch (default OFF: the owner reviews every video by hand until she is happy).
python ce_autopilot.py on|off  -> flip the switch;  python ce_autopilot.py run (every 3 h) -> decide open review cards when ON.
Rules when ON: checks-ok + title rule ok -> approve (after hold_hours, at most `cap` per day); checks-warn waits for the owner; duplicate title -> skip;
unreviewed longer than skip_after_hours -> skip. A decision = label ce-approve / ce-skip, then the review-decisions workflow files it (Saved / Delete).
The publisher then posts only Saved videos, and only while posting is ON."""
import json, os, subprocess, datetime, re
from pathlib import Path
B = Path(__file__).resolve().parent
CFG = B / 'publish' / 'ce-autopilot.json'
REPO = os.environ.get('GITHUB_REPOSITORY', 'zerenaod-ux/content-engine')
DEF = {'on': False, 'cap': 1, 'hold_hours': 3, 'skip_after_hours': 72, 'day': '', 'count': 0, 'changed': '', 'last_run': '', 'log': []}
EMOJI = re.compile('[\U0001F300-\U0001FAFF☀-➿⭐⭕⌚-⏿]')

def sh(*a): return subprocess.run(a, capture_output=True, text=True)
def now(): return datetime.datetime.now(datetime.timezone.utc)
def load():
    try: c = json.loads(CFG.read_text())
    except (OSError, ValueError): c = {}
    d = dict(DEF); d.update(c); return d
def save(c): CFG.parent.mkdir(exist_ok=True); CFG.write_text(json.dumps(c, indent=1))
def title_ok(t):
    t = re.sub(r'\s+', ' ', str(t or '')).strip(); w = EMOJI.sub('', t).split()
    return bool(re.match(r'^(How|Why)\b', t)) and 4 <= len(w) <= 8 and len(EMOJI.findall(t)) == 1 and bool(EMOJI.search(t[-2:])) and '?' not in t and not re.search(r'#|https?:|@', t) and len(t) <= 70

def main():
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else 'run'
    c = load()
    if mode in ('on', 'off'):
        c['on'] = mode == 'on'; c['changed'] = now().isoformat(timespec='seconds'); save(c); print('how-it-ticks autopilot', mode); return
    c['last_run'] = now().isoformat(timespec='seconds')
    if not c['on']:
        save(c); print('autopilot off'); return
    today = now().astimezone(datetime.timezone(datetime.timedelta(hours=-6))).date().isoformat()
    if c['day'] != today: c['day'] = today; c['count'] = 0
    r = sh('gh', 'issue', 'list', '--repo', REPO, '--label', 'scene-review', '--state', 'open', '--limit', '100', '--json', 'number,title,labels,createdAt')
    try: issues = json.loads(r.stdout or '[]')
    except ValueError: issues = []
    issues.sort(key=lambda x: x['createdAt'])
    seen, acted = set(), False
    for i in issues:
        names = [l['name'] for l in i['labels']]
        if 'ce-approve' in names or 'ce-skip' in names: continue
        age = (now() - datetime.datetime.fromisoformat(i['createdAt'].replace('Z', '+00:00'))).total_seconds() / 3600
        title = re.sub(r'^(How It Ticks|Content Engine):\s*', '', i['title']).strip()
        dup = title.lower() in seen; seen.add(title.lower())
        act, why = None, ''
        if dup and age >= 1: act, why = 'ce-skip', 'duplicate title'
        elif age < c['hold_hours']: continue
        elif 'checks-ok' in names and title_ok(title):
            if c['count'] < c['cap']: act, why = 'ce-approve', 'checks ok'
            elif age >= c['skip_after_hours']: act, why = 'ce-skip', 'waited too long (daily cap)'
        if not act and age >= c['skip_after_hours']: act, why = 'ce-skip', 'unreviewed too long'   # warn cards wait for the owner until then
        if not act: continue
        ok = sh('gh', 'issue', 'edit', str(i['number']), '--repo', REPO, '--add-label', act).returncode == 0
        if ok and act == 'ce-approve': c['count'] += 1
        if ok:
            acted = True
            sh('gh', 'issue', 'comment', str(i['number']), '--repo', REPO, '--body', 'Autopilot: %s (%s).' % (act, why))
        c['log'] = ([{'t': c['last_run'], 'issue': i['number'], 'act': act, 'why': why, 'ok': ok}] + c['log'])[:40]
        print('autopilot', act, i['number'], why, 'ok' if ok else 'FAILED')
    save(c)
    if acted: sh('gh', 'workflow', 'run', 'review-decisions.yml', '--repo', REPO, '--ref', 'main')   # label events from the job token do not start workflows

if __name__ == '__main__':
    main()
