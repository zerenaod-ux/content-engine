"""Free-LLM fallback router. Gemini's free quota is shared by every writer and often hits 429, so when Gemini fails callers use this.
Providers (all free tiers, OpenAI-compatible), tried in order when their key is present in the environment:
  GROQ_API_KEY (api.groq.com), CEREBRAS_API_KEY (api.cerebras.ai), OPENROUTER_API_KEY (openrouter.ai, ':free' models), MISTRAL_API_KEY (api.mistral.ai).
Model names change, so each provider is asked for its model list and the best known family is chosen. Returns text / parsed JSON, or raises ValueError."""
import json, os, re, time, urllib.request, urllib.error, urllib.parse
import email.utils
from pathlib import Path

PROVIDERS = [
    ('GROQ_API_KEY', 'https://api.groq.com/openai/v1', ('gpt-oss-120b', 'llama-3.3-70b', 'qwen3', 'llama', 'gpt-oss')),
    ('CEREBRAS_API_KEY', 'https://api.cerebras.ai/v1', ('gpt-oss-120b', 'llama-3.3-70b', 'qwen', 'llama')),
    ('OPENROUTER_API_KEY', 'https://openrouter.ai/api/v1', ('gpt-oss-120b', 'llama-3.3-70b', 'qwen', 'deepseek', 'gemma', 'llama', 'mistral')),
    ('MISTRAL_API_KEY', 'https://api.mistral.ai/v1', ('mistral-large', 'mistral-medium', 'mistral-small', 'mistral')),
    # GITHUB_MODELS: free GitHub Models with the job's own token (no new key, permission models: read). Fixed model names.
    ('GITHUB_MODELS_TOKEN', 'https://models.github.ai/inference', ('openai/gpt-4.1-mini', 'meta/Llama-3.3-70B-Instruct', 'openai/gpt-4.1-nano')),
]
KEY_SHAPE = {'GROQ_API_KEY': 'gsk_', 'CEREBRAS_API_KEY': 'csk-', 'OPENROUTER_API_KEY': 'sk-or-'}


def key_check():
    """KEY_SHAPE: says (without showing any key) whether each saved key looks like that service's key, so a key saved under the wrong name is spotted."""
    for env, start in KEY_SHAPE.items():
        k = os.environ.get(env, '').strip()
        print('key check:', env, 'missing' if not k else ('looks right' if k.startswith(start) else 'DOES NOT look like a %s key (saved under the wrong name?)' % env.split('_')[0]), flush=True)
_CACHE = {}


class BudgetExceeded(ValueError):
    pass

class ProviderCoolingDown(ValueError):
    pass

_STARTED = time.monotonic()

def _req(url, key, body=None):
    # Shared on-disk ledger covers idea maker and writer subprocesses in one run.
    path = Path(os.environ.get('CE_METRICS_PATH', 'metrics.json'))
    try: metrics = json.loads(path.read_text())
    except (OSError, ValueError): metrics = {'requests': 0, 'seconds': 0, 'responses': 0, 'failures': 0, 'started_at': time.time(), 'usage': {}}
    if metrics['requests'] >= int(os.environ.get('CE_MAX_REQUESTS', '24')) or time.time() - metrics.setdefault('started_at', time.time()) >= float(os.environ.get('CE_MAX_SECONDS', '480')):
        raise BudgetExceeded('free request/time budget exhausted; accepted stages remain cached')
    host=urllib.parse.urlparse(url).hostname
    limit=metrics.get('rate_limits',{}).get(host)
    if limit and (limit.get('retry_at') is None or time.time()<limit['retry_at']):
        raise ProviderCoolingDown('provider rate-limited; remaining requests preserved')
    metrics['requests'] += 1
    path.write_text(json.dumps(metrics, indent=1))
    started = time.monotonic()
    try:
        r = urllib.request.Request(url, json.dumps(body).encode() if body is not None else None, {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json', 'User-Agent': 'studio/1.0'})
        with urllib.request.urlopen(r, timeout=max(1, min(90, float(os.environ.get('CE_MAX_SECONDS', '480')) - (time.time() - metrics['started_at'])))) as x:
            result = json.load(x)
        metrics['responses'] += 1
        usage = result.get('usage', {})
        for name in ('prompt_tokens', 'completion_tokens', 'total_tokens'):
            if isinstance(usage.get(name), int): metrics.setdefault('usage', {})[name] = metrics.get('usage', {}).get(name, 0) + usage[name]
        return result
    except urllib.error.HTTPError as e:
        metrics['failures'] += 1
        metrics.setdefault('http_statuses',{})[str(e.code)]=metrics.get('http_statuses',{}).get(str(e.code),0)+1
        if e.code==429:
            raw=e.headers.get('Retry-After') if e.headers else None
            retry_at=None
            if raw:
                try: retry_at=time.time()+max(0,float(raw))
                except ValueError:
                    try: retry_at=email.utils.parsedate_to_datetime(raw).timestamp()
                    except (ValueError,TypeError,OverflowError): pass
            metrics.setdefault('rate_limits',{})[host]={'retry_at':retry_at,'retry_after':raw}
        raise
    except Exception:
        metrics['failures'] += 1
        raise
    finally:
        metrics['seconds'] = round(metrics['seconds'] + time.monotonic() - started, 3)
        path.write_text(json.dumps(metrics, indent=1))


def _models(env, base, prefs, key):
    if env in _CACHE:
        return _CACHE[env]
    if 'models.github.ai' in base:
        return list(prefs)
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
        except BudgetExceeded: raise
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
                except BudgetExceeded: raise
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
