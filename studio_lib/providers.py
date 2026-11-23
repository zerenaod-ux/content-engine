"""Use the existing free router ledger, respecting cooldowns before repair calls."""
import json,os,time,urllib.error
from pathlib import Path
import llm
from studio_lib.service_queue import lease,cooling_down,remember_cooldown
_UNAVAILABLE=set()
class ServiceUnavailable(ValueError):
    """No usable free service answered; retain valid work for a later run."""
KEYLESS=[('KEYLESS_LLM7','https://api.llm7.io/v1',('gpt-oss','llama-3.3','qwen','deepseek','llama','mistral')),
         ('KEYLESS_OVH','https://oai.endpoints.kepler.ai.cloud.ovh.net/v1',('gpt-oss-120b','llama-3_3','qwen','llama','mistral'))]
KEYLESS_KEYS={'KEYLESS_LLM7':'unused','KEYLESS_OVH':''}

def _call_once(system,prompt,max_tokens=10000,temperature=.5,reasoning_effort="low"):
    # GitHub Models produced empty responses in the first proof run; do not
    # burn repeated fallback attempts on it. Other channels' router is untouched.
    providers=[p for p in llm.PROVIDERS if p[0]!='GITHUB_MODELS_TOKEN' and os.environ.get(p[0])]
    if os.environ.get('GEMINI_API_KEY'):
        providers.insert(min(1,len(providers)),('GEMINI_API_KEY','https://generativelanguage.googleapis.com/v1beta/openai',('flash',)))
    # Keyless free services (no account, limits per IP) are tried last, so a throttled key never stops a run.
    for env,base,prefs in KEYLESS:providers.append((env,base,prefs))
    last='no configured free provider'
    failures=[]
    for env,base,prefs in providers:
        import urllib.parse
        host=urllib.parse.urlparse(base).hostname
        if cooling_down(host):
            failures.append('Shared provider cooldown active');continue
        key=os.environ[env].strip() if os.environ.get(env) else KEYLESS_KEYS.get(env,'')
        rate_retries=0;json_mode=True;reasoning=True;model=None
        for turn in range(4):
            path=Path(os.environ.get('CE_METRICS_PATH','metrics.json'))
            try:ledger=json.loads(path.read_text())
            except (OSError,ValueError):ledger={}
            import urllib.parse
            limit=ledger.get('rate_limits',{}).get(urllib.parse.urlparse(base).hostname)
            if limit:
                reset=limit.get('retry_at')
                if reset is None:break
                wait=reset-time.time()
                if wait>60:break
                if wait>0:
                    print('free provider cooling down; preserving repair calls',flush=True)
                    time.sleep(wait+.5)
            try:
                if env=='GEMINI_API_KEY':models=[m for m in ('gemini-2.5-flash','gemini-flash-latest','gemini-2.0-flash','gemini-2.5-flash-lite') if (base,m) not in _UNAVAILABLE]   # fixed names: the listed 'models/...' name answered 404
                else:models=[m for m in llm._models(env,base,prefs,key) if (base,m) not in _UNAVAILABLE]
                if not models:
                    failures.append(env.split('_')[0]+' no usable model');print('studio provider has no usable model:',env.split('_')[0],flush=True);break
                model=models[0]
                model_name=model.removeprefix('models/') if env=='GEMINI_API_KEY' else model
                messages=[{'role':'system','content':system},{'role':'user','content':prompt}]
                body={'model':model_name,'messages':messages,'temperature':temperature,'max_tokens':max_tokens}
                if reasoning and 'gpt-oss' in model_name:body['reasoning_effort']=reasoning_effort
                if json_mode:body['response_format']={'type':'json_object'}
                with lease('ai'):
                    if cooling_down(host):raise llm.ProviderCoolingDown('Shared provider cooldown active')
                    try:r=llm._req(base+'/chat/completions',key,body)
                    except urllib.error.HTTPError as quota_error:
                        if quota_error.code==429:
                            import email.utils
                            raw=quota_error.headers.get('Retry-After') if quota_error.headers else None
                            try:retry_at=time.time()+max(0,float(raw))
                            except (ValueError,TypeError):
                                try:retry_at=email.utils.parsedate_to_datetime(raw).timestamp()
                                except (ValueError,TypeError,AttributeError):retry_at=time.time()+(65 if 'ovh' in host else 900)
                            retry_at=min(retry_at,time.time()+3600)  # never lock a service for more than an hour
                            remember_cooldown(host,retry_at)
                        raise
                answer=r['choices'][0]['message'].get('content','')
                if not answer:raise ValueError('provider returned an empty answer')
                print('studio answered by',env.split('_')[0],model_name,flush=True)
                return llm.parse(answer)
            except llm.BudgetExceeded:raise
            except urllib.error.HTTPError as e:
                last=f'{env.split("_")[0]} HTTP {e.code}'
                try:
                    payload=json.loads(e.read()).get('error',{})
                    message=payload.get('message','')
                    # Avoid echoing any credential even if a provider includes it.
                    for credential in [os.environ.get(p[0],'') for p in providers]:
                        if credential:message=message.replace(credential,'[private]')
                    if message:last+=' '+message[:350]
                except (ValueError,AttributeError):pass
                failures.append(last);print('studio provider refusal:',last,flush=True)
                if e.code in (402,403,404) and model:
                    _UNAVAILABLE.add((base,model));continue
                if e.code==400 and json_mode and any(s in last.lower() for s in ('response_format','json_object','validate json','failed to generate json','json mode')):
                    json_mode=False;max_tokens=max(1200,max_tokens);continue
                if e.code==400 and reasoning and 'reasoning' in last.lower():
                    reasoning=False;continue
                if e.code==429 and rate_retries==0:rate_retries+=1;continue
                break
            except Exception as e:
                last=type(e).__name__+': '+str(e)[:180];failures.append(env.split('_')[0]+' '+last);print('studio provider error:',env.split('_')[0],last,flush=True);break
    raise ServiceUnavailable(' | '.join(failures[-3:]) if failures else last)


def call(system,prompt,max_tokens=10000,temperature=.5,reasoning_effort="low"):
    """Free writers rate-limit by the minute: wait and ask again (up to 5 waits) before giving up."""
    for wait in range(6):
        try:return _call_once(system,prompt,max_tokens,temperature,reasoning_effort)
        except ServiceUnavailable:
            if wait==5:raise
            print('studio providers busy; waiting 25s',flush=True);time.sleep(25)
