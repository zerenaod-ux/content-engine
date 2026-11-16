"""Use the existing free router ledger, respecting cooldowns before repair calls."""
import json,os,time,urllib.error
from pathlib import Path
import llm
def call(system,prompt,max_tokens=10000,temperature=.5):
    # GitHub Models produced empty responses in the first proof run; do not
    # burn repeated fallback attempts on it. Other channels' router is untouched.
    providers=[p for p in llm.PROVIDERS if p[0]!='GITHUB_MODELS_TOKEN' and os.environ.get(p[0])]
    last='no configured free provider'
    for env,base,prefs in providers:
        key=os.environ[env].strip()
        for turn in range(2):
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
                models=llm._models(env,base,prefs,key)
                if not models:break
                messages=[{'role':'system','content':system},{'role':'user','content':prompt}]
                body={'model':models[0],'messages':messages,'temperature':temperature,'max_tokens':max_tokens,'response_format':{'type':'json_object'}}
                r=llm._req(base+'/chat/completions',key,body)
                answer=r['choices'][0]['message'].get('content','')
                if not answer:raise ValueError('provider returned an empty answer')
                print('studio answered by',env.split('_')[0],models[0],flush=True)
                return llm.parse(answer)
            except llm.BudgetExceeded:raise
            except urllib.error.HTTPError as e:
                last=f'{env.split("_")[0]} HTTP {e.code}'
                if e.code==429 and turn==0:continue
                break
            except Exception as e:last=type(e).__name__+': '+str(e)[:180];break
    raise ValueError(last)
