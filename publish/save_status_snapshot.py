"""Save only the verified status file via GitHub's Contents API; no git fetch."""
import base64,datetime,json,os,time,urllib.request,urllib.error
PATH='contents/data/scenes/publishing-status.json'
def api(method,path,data=None):
    req=urllib.request.Request('https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']+'/'+path,
        data=json.dumps(data).encode() if data is not None else None,method=method,
        headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as response:return json.load(response)
def stamp(value):return datetime.datetime.fromisoformat(value.replace('Z','+00:00'))
def save(snapshot,request=api):
    checked=stamp(snapshot['checked_at'])
    if snapshot.get('read_only') is not True:raise ValueError('Expected a read-only verification report')
    content=base64.b64encode((json.dumps(snapshot,indent=2)+'\n').encode()).decode()
    for attempt in range(5):
        try:old=request('GET',PATH+'?ref=main')
        except urllib.error.HTTPError as e:
            if e.code!=404:raise
            old=None
        if old:
            prior=json.loads(base64.b64decode(old['content']))
            if stamp(prior['checked_at'])>=checked:return False
        payload={'message':'Refresh verified How It Ticks publishing status','branch':'main','content':content}
        if old:payload['sha']=old['sha']
        try:request('PUT',PATH,payload);return True
        except urllib.error.HTTPError as e:
            if e.code not in (409,422) or attempt==4:raise
            time.sleep(attempt+1)
    return False
if __name__=='__main__':
    from pathlib import Path
    result=save(json.loads(Path('publish-status-report.json').read_text()))
    print('Saved verified publishing status.' if result else 'A newer verified status is already saved.')
