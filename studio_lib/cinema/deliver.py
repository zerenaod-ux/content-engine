"""File a successful generated comparison in existing Studio review, never approve."""
import base64,datetime,hashlib,json,os,time,urllib.request,urllib.error
from pathlib import Path
REPO=os.environ['GITHUB_REPOSITORY'];TOKEN=os.environ['GH_TOKEN'];RUN=os.environ['SOURCE_RUN']
def api(method,path,data=None):
    req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path,data=json.dumps(data).encode() if data is not None else None,method=method,headers={'Authorization':'Bearer '+TOKEN,'Accept':'application/vnd.github+json','Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=120) as r:return json.load(r)
def get(path):
    try:return api('GET',path)
    except urllib.error.HTTPError as e:
        if e.code==404:return None
        raise
def put_file(path,content,branch,merge=None):
    # Re-read the latest SHA on each collision; never rebase unrelated history.
    for attempt in range(5):
        old=get('contents/'+path+'?ref='+branch);payload=content
        if merge is not None:
            prior=json.loads(base64.b64decode(old['content'])) if old else []
            payload=(json.dumps(merge(prior),indent=1,ensure_ascii=False)+'\n').encode()
        body={'message':'Studio comparison delivery '+RUN,'branch':branch,'content':base64.b64encode(payload).decode()}
        if old:body['sha']=old['sha']
        try:return api('PUT','contents/'+path,body)
        except urllib.error.HTTPError as e:
            if e.code not in (409,422) or attempt==4:raise
            time.sleep(2*(attempt+1))
def main():
    root=Path('incoming/cinema-output') if Path('incoming/cinema-output').exists() else Path('incoming')
    result=json.loads((root/'result.json').read_text());plan=json.loads((root/'plan.json').read_text())
    if result.get('manual_script_or_video_edits') is not False or result.get('owner_approved') is not False:raise ValueError('invalid automatic provenance')
    if plan.get('mechanism') not in ('wind_turbine','hand_generator','lever_balance','resistive_circuit','hydraulic_lift','thermal_contact','dna_pairing','water_transfer'):raise ValueError('unregistered cinematic subject')
    video=root/'video.mp4'
    if not video.is_file() or video.stat().st_size<100000:raise ValueError('finished video missing')
    run=api('GET','actions/runs/'+RUN)
    if run['conclusion']!='success' or run['head_branch']!='studio-cinematic-proof' or run['head_repository']['full_name']!=REPO:raise ValueError('source run is not the authorized successful comparison')
    stamp=run['created_at'].replace('-','').replace(':','');tag='ce-'+stamp[:8]+'-'+stamp[9:13]+'-cinema-'+RUN
    title=plan['title'].replace('\n',' ').strip()+({'hand_generator':' 💡','wind_turbine':' 💨','lever_balance':' ⚖️','resistive_circuit':' ⚡','hydraulic_lift':' 🏗️','thermal_contact':' 🌡️','dna_pairing':' 🧬','water_transfer':' 💧'}[plan['mechanism']])
    uploaded=put_file('videos/'+tag+'.mp4',video.read_bytes(),'gh-pages')
    sha=uploaded['commit']['sha']
    if video.stat().st_size>=19_000_000:raise ValueError('comparison exceeds mobile CDN size budget; retain artifact and fail delivery visibly')
    url='https://cdn.jsdelivr.net/gh/'+REPO+'@'+sha+'/videos/'+tag+'.mp4'
    # Release is archival; the card uses a direct Pages MP4 for mobile playback.
    release=get('releases/tags/'+tag)
    if not release:release=api('POST','releases',{'tag_name':tag,'target_commitish':run['head_sha'],'name':'How It Ticks comparison: '+title,'body':'Automatic cinematic comparison; owner review pending. Video: '+url+'\nSource run: '+run['html_url'],'prerelease':True})
    name=tag+'.mp4'
    if not any(x['name']==name for x in release.get('assets',[])):
        req=urllib.request.Request('https://uploads.github.com/repos/'+REPO+'/releases/'+str(release['id'])+'/assets?name='+name,data=video.read_bytes(),method='POST',headers={'Authorization':'Bearer '+TOKEN,'Content-Type':'video/mp4','Accept':'application/vnd.github+json'})
        with urllib.request.urlopen(req,timeout=120) as response:json.load(response)
    def merge(v):
        if not any(x.get('tag')==tag for x in v):v.append({'date':run['created_at'][:10],'tag':tag,'title':title,'video':url,'source':'automatic cinematic comparison','source_run':RUN,'owner_approved':False})
        return v
    put_file('data/scenes/videos.json',b'','main',merge)
    # Create the card only after the media and index save succeeded.
    labels=['scene-review','checks-warn','cinematic-test']
    for label in labels:
        if not get('labels/'+label):api('POST','labels',{'name':label,'color':'d29922'})
    marker='cinematic-source-run: '+RUN
    existing=api('GET','issues?state=all&labels=cinematic-test&per_page=100')
    issue=next((x for x in existing if marker in (x.get('body') or '')),None)
    if not issue:
        issue=api('POST','issues',{'title':'How It Ticks: '+title,'labels':labels,'body':'Automatically generated cinematic comparison. NOT approved or published.\n\nWatch: '+url+'\n\nApprove or Skip in Studio. Automatic approval is off.\n\nChecks: warn — visual, narration and sound review pending.\n\n'+marker+'\nSource: '+run['html_url']})
    print(json.dumps({'review_card':issue['html_url'],'video':url,'index_saved':True,'approved':False,'media_commit':sha}))
if __name__=='__main__':main()

