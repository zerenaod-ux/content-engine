"""Read-only Buffer verification; never creates, schedules, edits or deletes posts."""
import datetime,json,sys,unicodedata,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import ce_publisher as publisher

def canonical(text):
    return re.sub(r'[^a-z0-9]+',' ',unicodedata.normalize('NFKD',text).lower()).strip()

def main():
    report={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'read_only':True,'complete':False,'platforms':{},'saved':[],'timezone':publisher.CFG.get('timezone','America/Chicago'),'posting_slots':publisher.CFG.get('slots',{})}
    if not publisher.TOKEN:raise ValueError('Publishing credential is not configured')
    account=publisher.api('{account{organizations{id}}}')
    if account.get('errors'):raise ValueError('Buffer account read was refused')
    orgs=((account.get('data') or {}).get('account') or {}).get('organizations') or []
    if not orgs:raise ValueError('No accessible publishing organization')
    posts=[];complete=True
    query='query($i:PostsInput!,$after:String){posts(first:100,after:$after,input:$i){edges{node{id text channelId status dueAt}} pageInfo{hasNextPage endCursor}}}'
    for org in orgs:
        cursor=None
        for page in range(5):
            response=publisher.api(query,{'i':{'organizationId':org['id'],'filter':{'channelIds':list(publisher.CHANNELS.values())}},'after':cursor})
            if response.get('errors'):raise ValueError('Buffer post-status read was refused')
            connection=(response.get('data') or {}).get('posts')
            if not isinstance(connection,dict):raise ValueError('Buffer returned no usable post-status data')
            posts.extend(x['node'] for x in connection.get('edges',[]))
            info=connection.get('pageInfo') or {}
            if not info.get('hasNextPage'):break
            cursor=info.get('endCursor')
        else:complete=False
    index=json.loads(Path('data/scenes/review/index.json').read_text())
    state=json.loads(Path('publish/state.json').read_text()).get('done',{})
    for platform,channel in publisher.CHANNELS.items():
        own=[p for p in posts if p.get('channelId')==channel]
        report['platforms'][platform]={'returned_posts':len(own),'statuses':{s:sum(p.get('status')==s for p in own) for s in sorted({str(p.get('status')) for p in own})}}
    for item in index.get('items',[]):
        if item.get('folder')!='saved':continue
        entry={'tag':item['tag'],'title':item.get('title'),'platforms':{}}
        for platform,channel in publisher.CHANNELS.items():
            tracked=state.get(item['tag']+'/'+platform,{})
            matches=[p for p in posts if p.get('channelId')==channel and (p.get('id')==tracked.get('remote') or canonical((p.get('text') or '').split('\n')[0])==canonical(item.get('title','')))]
            entry['platforms'][platform]=[{'status':p.get('status'),'due':p.get('dueAt')} for p in matches] or [{'status':'not_found_in_buffer','prior_owner_skip':str(tracked.get('remote','')).startswith('SKIPPED')}]
        report['saved'].append(entry)
    report['complete']=complete
    Path('publish-status-report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()

