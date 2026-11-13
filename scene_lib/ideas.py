"""THE IDEA MAKER: thinks up a NEW topic every time, from the tiny to the huge, and never repeats one.
Strong rules: categories take turns; an idea is thrown out if its subject, its key words or its wording is close to anything already made
(data/scenes/history.json); unsafe subjects are thrown out; the best remaining idea (surprise + how well it can be shown) wins.
  python3 scene_lib/ideas.py pick topic.txt        python3 scene_lib/ideas.py record auto-scene.json"""
import datetime, json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
HIST = ROOT / 'data' / 'scenes' / 'history.json'
CATEGORIES = ['the human body', 'animals', 'insects and tiny creatures', 'space and planets', 'weather and the sky', 'earth, volcanoes and oceans', 'plants and farming', 'machines and engines',
              'everyday objects at home', 'food and the kitchen', 'buildings, bridges and cities', 'electricity and energy', 'vehicles and travel', 'atoms, germs and tiny things',
              'giant things and extremes', 'inventions that changed the world', 'sports and games', 'sound, light and colour']
BANNED = re.compile(r'\b(dose|dosage|medicines?|drugs?|pills?|cures?|treat(ment|ments|s|ing)?|diagnos\w*|surger\w*|vaccin\w*|weapons?|guns?|bombs?|explosives?|wars?|kill\w*|suicide|sex\w*|porn\w*|gambl\w*|casinos?|invest\w*|stock market|crypto\w*|bitcoin|loans?|elections?|politic\w*|religio\w*|gods?|abortion|alcohol|cigarettes?|vap(e|es|ing)|diets?|weight loss)\b', re.I)
STOP = set('a an the how why what does do is are of in on to from with and or for its it your you that this into up down out by at as be can make makes work works so than when where which who'.split())
def words(s): return {w[:-1] if len(w) > 4 and w.endswith('s') else w for w in re.findall(r'[a-z]+', str(s).lower()) if w not in STOP and len(w) > 2}
def jac(a, b): return len(a & b) / max(1, len(a | b))

def load():
    try: return json.loads(HIST.read_text())
    except Exception: return []

def too_close(idea, hist):
    """Why this idea repeats something already made, or '' if it is new."""
    subj = words(idea.get('subject', '')); kw = words(' '.join(idea.get('keywords', []))) | subj; tw = words(idea.get('topic', ''))
    for h in hist:
        hs = words(h.get('subject', '')); hk = words(' '.join(h.get('keywords', []))) | hs; ht = words(h.get('topic', '')) | words(h.get('title', ''))
        if subj and hs and (subj <= hs or hs <= subj): return 'same subject as "%s"' % h.get('topic')
        if jac(kw, hk) >= 0.34: return 'key words too close to "%s"' % h.get('topic')
        if jac(tw, ht) >= 0.5: return 'wording too close to "%s"' % h.get('topic')
    return ''

def next_categories(hist):
    recent = [h.get('category') for h in hist[-len(CATEGORIES):]]; n = len(hist)
    order = sorted(CATEGORIES, key=lambda c: (recent.count(c), (CATEGORIES.index(c) - n) % len(CATEGORIES)))
    return order

def pick(log=print):
    import llm
    hist = load(); made = '; '.join(h.get('topic', '') for h in hist[-60:]) or 'nothing yet'
    for cat in next_categories(hist)[:5]:
        prompt = f"""Think of 10 fresh ideas for a 33-second animated explainer video in the category: {cat}.
Each idea answers "How does X work?" or "Why does X happen?" about ONE concrete thing, from the tiny to the huge, that almost everyone has seen or used but few can explain.
It must be something you can SHOW happening step by step in one picture: things move, flow, fill, spin, grow, heat up, light up or change. No abstract ideas, no opinions.
Safe for all ages. NOT about: medicine or treatment, diets, weapons, war, politics, religion, money or investing, adult themes.
ALREADY MADE (do not repeat these or anything close to them): {made}
Return JSON: {{"ideas": [{{"topic": "how ... / why ... (6 to 14 words, plain)", "subject": "the one thing it is about, 1-3 words", "keywords": ["5 key words"], "wow": 1-10 (how surprising), "drawable": 1-10 (how clearly a simple animation can show it)}}]}}"""
        try: got = llm.json_call('You invent brilliant, surprising explainer video ideas. You answer with ONE JSON object.', prompt, temperature=1.0, max_tokens=1800).get('ideas', [])
        except Exception as e: log('ideas for "%s": no answer (%s)' % (cat, str(e)[:120])); continue
        ok = []
        for i in got if isinstance(got, list) else []:
            if not (isinstance(i, dict) and isinstance(i.get('topic'), str) and isinstance(i.get('subject'), str) and isinstance(i.get('keywords'), list)): continue
            t = re.sub(r'\s+', ' ', i['topic']).strip()
            if not 20 <= len(t) <= 110 or not re.match(r'(?i)(how|why)\b', t): continue
            if BANNED.search(t + ' ' + i['subject'] + ' ' + ' '.join(map(str, i['keywords']))): log('  thrown out (not allowed subject): ' + t); continue
            why = too_close(i, hist)
            if why: log('  thrown out (%s): %s' % (why, t)); continue
            i['topic'] = t; i['score'] = (i.get('wow') or 0) * 1.0 + (i.get('drawable') or 0) * 1.2; ok.append(i)
        if ok:
            best = max(ok, key=lambda i: i['score']); best['category'] = cat
            log('category: %s | %d new ideas | chosen: %s' % (cat, len(ok), best['topic'])); return best
        log('category "%s": no new idea survived the rules; trying the next category' % cat)
    raise SystemExit('REJECTED: no new idea passed the no-repeat rules')

def record(spec_path, idea_path='idea.json', failed=False):
    hist = load()
    try: spec = json.loads(Path(spec_path).read_text())
    except Exception: spec = {}
    try: idea = json.loads(Path(idea_path).read_text())
    except Exception: idea = {}
    hist.append({'date': datetime.date.today().isoformat(), 'topic': idea.get('topic') or spec.get('title', ''), 'title': spec.get('title', ''), 'subject': idea.get('subject', ''),
                 'keywords': idea.get('keywords', []), 'category': idea.get('category', ''), **({'failed': True} if failed else {})})
    HIST.parent.mkdir(parents=True, exist_ok=True); HIST.write_text(json.dumps(hist, indent=1, ensure_ascii=False) + '\n'); print('recorded; %d scenes in the history' % len(hist))

if __name__ == '__main__':
    if sys.argv[1] == 'pick':
        lines = []
        def log(m): print(m, flush=True); lines.append(m)
        try:
            idea = pick(log); Path(sys.argv[2]).write_text(idea['topic'] + '\n'); Path('idea.json').write_text(json.dumps(idea, ensure_ascii=False))
        finally: Path('idea-log.txt').write_text('\n'.join(lines) + '\n')
    elif sys.argv[1] == 'record': record(sys.argv[2], failed=len(sys.argv) > 3 and sys.argv[3] == 'failed')
