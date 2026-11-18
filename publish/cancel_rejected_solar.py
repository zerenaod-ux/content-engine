"""Cancel only the explicitly rejected solar video's future Buffer bookings."""
import json, os, datetime, base64, urllib.request
from pathlib import Path
from ce_publisher import api, CHANNELS
TAG='ce-20261116-1727'
def main():
    index=json.loads(Path('data/scenes/review/index.json').read_text())
    item=next(x for x in index['items'] if x['tag']==TAG)
    if item['folder']!='delete' or item['issue_number']!=31: raise RuntimeError('Owner rejection is not recorded')
    state=json.loads(Path('publish/state.json').read_text())['done']
    targets={p:state[TAG+'/'+p]['remote'] for p in CHANNELS if TAG+'/'+p in state}
    orgs=api('{account{organizations{id}}}').get('data',{}).get('account',{}).get('organizations',[])
    if not orgs: raise RuntimeError('Cannot verify Buffer organization')
    def scheduled():
        r=api('query($i:PostsInput!){posts(first:100,input:$i){edges{node{id channelService status dueAt}}}}',{'i':{'organizationId':orgs[0]['id'],'filter':{'channelIds':list(CHANNELS.values()),'status':['scheduled','sending']}}})
        if r.get('errors'): raise RuntimeError('Cannot verify scheduled bookings')
        return {e['node']['id']:e['node'] for e in r['data']['posts']['edges']}
    before=scheduled(); results=[]
    for platform,remote in targets.items():
        post=before.get(remote)
        if not post: raise RuntimeError('Booking absent from scheduled read-back; inspect before deleting')
        if post['status']!='scheduled' or post['channelService']!=platform: raise RuntimeError('Booking is not safely cancellable')
        due=datetime.datetime.fromisoformat(post['dueAt'].replace('Z','+00:00'))
        if due<=datetime.datetime.now(datetime.timezone.utc): raise RuntimeError('Booking is already due')
        r=api('mutation($i:DeletePostInput!){deletePost(input:$i){... on DeletePostSuccess{id} ... on MutationError{message}}}',{'i':{'id':remote}})
        result=r.get('data',{}).get('deletePost',{})
        if result.get('id')!=remote: raise RuntimeError('Buffer did not confirm cancellation: '+str(result.get('message','unknown error')))
        results.append({'platform':platform,'cancelled':True,'remote':remote})
        print(platform+': future solar booking cancelled')
    after=scheduled()
    if any(remote in after for remote in targets.values()): raise RuntimeError('A rejected booking remains scheduled')
    report={'tag':TAG,'issue_number':31,'folder':'delete','cancelled':results,'verified_absent_from_schedule':True,'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    Path('solar-cancellation-report.json').write_text(json.dumps(report,indent=2))
    print('All rejected solar bookings removed; video retained in Delete')
if __name__=='__main__': main()
