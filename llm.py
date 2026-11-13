"""Free-LLM fallback router. Gemini's free quota is shared by every writer and often hits 429, so when Gemini fails callers use this.
Providers (all free tiers, OpenAI-compatible), tried in order when their key is present in the environment:
  GROQ_API_KEY (api.groq.com), CEREBRAS_API_KEY (api.cerebras.ai), OPENROUTER_API_KEY (openrouter.ai, ':free' models), MISTRAL_API_KEY (api.mistral.ai).
Model names change, so each provider is asked for its model list and the best known family is chosen. Returns text / parsed JSON, or raises ValueError."""
import json, os, re, urllib.request, urllib.error

PROVIDERS = [
    ('GROQ_API_KEY', 'https://api.groq.com/openai/v1', ('gpt-oss-120b', 'llama-3.3-70b', 'qwen3', 'llama', 'gpt-oss')),
    ('CEREBRAS_API_KEY', 'https://api.cerebras.ai/v1', ('gpt-oss-120b', 'llama-3.3-70b', 'qwen', 'llama')),
    ('OPENROUTER_API_KEY', 'https://openrouter.ai/api/v1', ('gpt-oss-120b', 'llama-3.3-70b', 'qwen', 'deepseek', 'gemma', 'llama', 'mistral')),
    ('MISTRAL_API_KEY', 'https://api.mistral.ai/v1', ('mistral-large', 'mistral-medium', 'mistral-small', 'mistral')),
]
_CACHE = {}


def _req(url, key, body=None):
    r = urllib.request.Request(url, json.dumps(body).encode() if body is not None else None, {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json', 'User-Agent': 'studio/1.0'})
    with urllib.request.urlopen(r, timeout=90) as x:
        return json.load(x)


def _models(env, base, prefs, key):
    if env in _CACHE:
        return _CACHE[env]
    ids = [m['id'] for m in _req(base + '/models', key).get('data', [])]
    if 'openrouter' in base:
        ids = [i for i in ids if i.endswith(':free')]
    ids = [i for i in ids if not re.search(r'embed|whisper|tts|guard|moderation|vision|image|audio|ocr|safeguard|prompt-guard', i)]
    out = []
    for p in prefs:
        out += [i for i in ids if p in i.lower() and i not in out]
    _CACHE[env] = out[:4]
    return _CACHE[env]


def available():
    return [e for e, _, _ in PROVIDERS if os.environ.get(e)]


def text(system, prompt, json_mode=True, temperature=0.8, max_tokens=6000):
    last = 'no free LLM key configured'
    for env, base, prefs in PROVIDERS:
        key = os.environ.get(env, '').strip()
        if not key:
            continue
        try:
            models = _models(env, base, prefs, key)
        except Exception as e:
            last = '%s model list: %s' % (env, str(e)[:80]); continue
        for model in models:
            msgs = ([{'role': 'system', 'content': system}] if system else []) + [{'role': 'user', 'content': prompt}]
            body = {'model': model, 'messages': msgs, 'temperature': temperature, 'max_tokens': max_tokens}
            if json_mode:
                body['response_format'] = {'type': 'json_object'}
            for attempt in (0, 1):
                try:
                    r = _req(base + '/chat/completions', key, body)
                    t = r['choices'][0]['message']['content']
                    if t and t.strip():
                        print('llm.py: answered by', env.split('_')[0], model, flush=True)
                        return t
                except urllib.error.HTTPError as e:
                    last = '%s %s HTTP %s' % (env.split('_')[0], model, e.code)
                    if e.code == 400 and json_mode and attempt == 0:
                        body.pop('response_format', None); continue   # model without JSON mode: ask plainly
                    break
                except Exception as e:
                    last = '%s %s %s' % (env.split('_')[0], model, str(e)[:60]); break
    raise ValueError('llm.py: ' + last)


def parse(t):
    t = t.strip()
    t = re.sub(r'^```(?:json)?|```$', '', t, flags=re.M).strip()
    try:
        return json.loads(t)
    except ValueError:
        m = re.search(r'\{.*\}', t, re.S)
        return json.loads(m.group(0))


def json_call(system, prompt, **kw):
    return parse(text(system, prompt, True, **kw))
