"""Use the existing free router ledger, respecting cooldowns before repair calls."""
import json,os,time,urllib.error
from pathlib import Path
import llm
_UNAVAILABLE=set()
class ServiceUnavailable(ValueError):
    """No usable free service answered; retain valid work for a later run."""
def call(system,prompt,max_tokens=10000,temperature=.5):
    # GitHub Models produced empty responses in the first proof run; do not
    # burn repeated fallback attempts on it. Other channels' router is untouched.
    providers=[p for p in llm.PROVIDERS if p[0]!='GITHUB_MODELS_TOKEN' and os.environ.get(p[0])]
    if os.environ.get('GEMINI_API_KEY'):
        providers.insert(min(1,len(providers)),('GEMINI_API_KEY','https://generativelanguage.googleapis.com/v1beta/openai',('flash',)))
    last='no configured free provider'
    failures=[]
    for env,base,prefs in providers:
        key=os.environ[env].strip()
        rate_retries=0;json_mode=True;model=None
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
                models=[m for m in llm._models(env,base,prefs,key) if (base,m) not in _UNAVAILABLE]
                if not models:break
                model=models[0]
                model_name=model.removeprefix('models/') if env=='GEMINI_API_KEY' else model
                messages=[{'role':'system','content':system},{'role':'user','content':prompt}]
                body={'model':model_name,'messages':messages,'temperature':temperature,'max_tokens':max_tokens}
                if 'gpt-oss' in model_name:body['reasoning_effort']='low'
                if json_mode:body['response_format']={'type':'json_object'}
                r=llm._req(base+'/chat/completions',key,body)
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
                if e.code==404 and model:
                    _UNAVAILABLE.add((base,model));continue
                if e.code==400 and json_mode and any(s in last.lower() for s in ('response_format','json_object','validate json','failed to generate json')):
                    json_mode=False;max_tokens=max(1200,max_tokens);continue
                if e.code==429 and rate_retries==0:rate_retries+=1;continue
                break
            except Exception as e:last=type(e).__name__+': '+str(e)[:180];break
    raise ServiceUnavailable(' | '.join(failures[-3:]) if failures else last)
