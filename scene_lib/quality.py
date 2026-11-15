"""QUALITY_GATE (owner 2026-11-15: pictures were blurry, too dark, sometimes wrong (a real candle instead of a spark plug), and many shots did not move).
1. picture_ok: a free vision AI (Gemini, then OpenRouter free vision models) looks at every AI picture and confirms it really shows the named part.
2. motion_score: measures how much a clip really moves (optical flow); still-looking clips are rejected.
3. sharpness / brightness numbers for the report."""
import base64, json, os, urllib.request

UA = {'User-Agent': 'content-engine/1.0', 'Content-Type': 'application/json'}
ASK = ('You check pictures for an explainer video. The narration says: "%s". The picture should show: %s. '
       'Answer only JSON {"ok": true/false, "shows": "what the picture really shows in 3-8 words", "bright": true/false}. '
       'Be lenient: ok=true when the main subject is the named thing or a reasonable depiction of it, even if details differ from the description. '
       'ok=false ONLY when the main object is clearly a different thing (for example a candle instead of a spark plug), or the picture is unusable or full of text/letters. '
       'bright=false if the picture is mostly dark.')


def _post(url, body, headers, timeout=60):
    r = urllib.request.Request(url, json.dumps(body).encode(), {**UA, **headers})
    return json.loads(urllib.request.urlopen(r, timeout=timeout).read())


def _parse(t):
    t = t[t.find('{'): t.rfind('}') + 1]
    return json.loads(t)


_MODELS = {}


def _gemini_models(key):
    """ASK_FOR_MODELS: model names change, so ask Google which models this key can use (flash first)."""
    if not key: return []
    if 'g' not in _MODELS:
        try:
            j = json.loads(urllib.request.urlopen('https://generativelanguage.googleapis.com/v1beta/models?pageSize=200&key=' + key, timeout=30).read())
            ms = [m['name'].split('/')[-1] for m in j.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])
                  and 'flash' in m['name'] and not any(w in m['name'] for w in ('tts', 'image', 'audio', 'live', 'embed'))]
            _MODELS['g'] = sorted(ms, key=lambda n: ('lite' in n, 'preview' in n or 'exp' in n, n), reverse=False)[:4]
        except Exception: _MODELS['g'] = []
    return _MODELS['g']


def _openrouter_models(key):
    """free OpenRouter models that accept pictures, asked live."""
    if not key: return []
    if 'o' not in _MODELS:
        try:
            j = json.loads(urllib.request.urlopen(urllib.request.Request('https://openrouter.ai/api/v1/models', headers={'User-Agent': 'content-engine/1.0'}), timeout=30).read())
            _MODELS['o'] = [m['id'] for m in j.get('data', []) if m['id'].endswith(':free') and 'image' in (m.get('architecture') or {}).get('input_modalities', [])][:4]
        except Exception: _MODELS['o'] = []
    return _MODELS['o']


def picture_ok(path, say, label, log=print):
    """Returns (ok, note). ok=None when no vision AI answered (the picture is then kept)."""
    b64 = base64.b64encode(open(path, 'rb').read()).decode()
    q = ASK % (say, label)
    key = os.environ.get('GEMINI_API_KEY', '').strip()
    for model in _gemini_models(key):
        try:
            j = _post('https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s' % (model, key),
                      {'contents': [{'parts': [{'text': q}, {'inline_data': {'mime_type': 'image/jpeg', 'data': b64}}]}],
                       'generationConfig': {'temperature': 0}}, {})
            a = _parse(j['candidates'][0]['content']['parts'][0]['text'])
            return bool(a.get('ok')), a.get('shows', '') + ('' if a.get('bright', True) else ' (dark: will be brightened)')   # dark is fixed later by brightening
        except Exception as e: log('vision check %s: %s' % (model, str(e)[:90]))
    key = os.environ.get('OPENROUTER_API_KEY', '').strip()
    for model in _openrouter_models(key):
        try:
            j = _post('https://openrouter.ai/api/v1/chat/completions',
                      {'model': model, 'temperature': 0, 'messages': [{'role': 'user', 'content': [{'type': 'text', 'text': q},
                       {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + b64}}]}]}, {'Authorization': 'Bearer ' + key})
            a = _parse(j['choices'][0]['message']['content'])
            return bool(a.get('ok')) and a.get('bright', True) is not False, a.get('shows', '')
        except Exception as e: log('vision check %s: %s' % (model, str(e)[:90]))
    return None, 'no vision AI answered'


def motion_score(path):
    """Average optical-flow movement per frame (pixels at 270 px width). About < 0.6 looks like a still photo."""
    import cv2, numpy as np
    cap = cv2.VideoCapture(path); prev, tot, n, k = None, 0.0, 0, 0
    while True:
        ok, fr = cap.read()
        if not ok: break
        k += 1
        if k % 3: continue
        g = cv2.cvtColor(cv2.resize(fr, (270, int(270 * fr.shape[0] / fr.shape[1]))), cv2.COLOR_BGR2GRAY)
        if prev is not None:
            f = cv2.calcOpticalFlowFarneback(prev, g, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            tot += float(np.linalg.norm(f, axis=2).mean()); n += 1
        prev = g
    return tot / n if n else 0.0


def looks(path):
    """(brightness 0-255, sharpness) of the middle frame."""
    import cv2
    cap = cv2.VideoCapture(path); cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) // 2))
    ok, fr = cap.read()
    if not ok: fr = cv2.imread(path)
    g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
    return float(g.mean()), float(cv2.Laplacian(g, cv2.CV_64F).var())
