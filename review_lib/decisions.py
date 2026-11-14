"""Content Engine review folders. Originals stay in their existing releases.
Only owner review labels move references between Saved and Delete holding folders.
No social-publishing or asset-deletion code lives here.
"""
import copy
import datetime
import json
from pathlib import Path
import re
import urllib.parse

LABELS={'ce-approve':'saved','ce-skip':'delete'}
TAG=re.compile(r'^ce-\d{8}-\d{4}(?:-\d+)?$')


def decision_for(issue):
    labels={x['name'] if isinstance(x,dict) else x for x in issue.get('labels',[])}
    if 'pull_request' in issue or 'scene-review' not in labels: return None
    choices=[LABELS[x] for x in LABELS if x in labels]
    if len(choices)>1: raise ValueError('Both decisions are present; choose Approve or Skip again.')
    return choices[0] if choices else None


def tag_from_url(url):
    u=urllib.parse.urlparse(url)
    if u.scheme!='https': return None
    if u.hostname=='github.com':
        match=re.fullmatch(r'/zerenaod-ux/(?:content-engine|shelfmade-dashboard)/releases/download/(ce-\d{8}-\d{4}(?:-\d+)?)/(ce-[\w-]+)\.mp4',u.path)
        if match and match[1]==match[2]: return match[1]
    if u.hostname in ('cdn.jsdelivr.net','fastly.jsdelivr.net'):
        match=re.fullmatch(r'/gh/zerenaod-ux/content-engine@gh-pages/videos/(ce-\d{8}-\d{4}(?:-\d+)?)\.mp4',u.path)
        if match:return match[1]
    return None


def video_for(issue,catalog):
    tags={t for url in re.findall(r'https://[^\s<>]+',issue.get('body','')) if (t:=tag_from_url(url.rstrip(').,')))}
    if len(tags)!=1: raise ValueError('The review card must identify exactly one Content Engine video.')
    tag=tags.pop()
    matches=[v for v in catalog if v.get('tag')==tag]
    if len(matches)!=1: raise ValueError('Video is not yet in the generated-video list; retry after generation finishes.')
    item=matches[0]
    if tag_from_url(item.get('video',''))!=tag: raise ValueError('Stored video reference is invalid.')
    return item


def file_decision(index,issue,video,folder,run_id,now=None):
    if folder not in ('saved','delete') or not TAG.fullmatch(video['tag']): raise ValueError('Invalid folder or video tag.')
    out=copy.deepcopy(index)
    out.setdefault('version',1);items=out.setdefault('items',[])
    old=next((x for x in items if x['tag']==video['tag']),None)
    if old and old['folder']==folder and old['issue_number']==issue['number']: return out,None
    stamp=now or datetime.datetime.now(datetime.timezone.utc).isoformat()
    event={'tag':video['tag'],'title':video.get('title') or issue['title'].removeprefix('Content Engine: '),
           'video':video['video'],'folder':folder,'issue_number':issue['number'],
           'issue_url':issue.get('html_url',''),'reviewed_at':stamp,'publishing_enabled':False,'ready_for_future_publish':folder=='saved'}
    history=copy.deepcopy(old.get('history',[])) if old else []
    if old: history.append({k:old[k] for k in ('folder','reviewed_at','record')})
    safe_run=re.sub(r'[^0-9-]','',str(run_id))
    if not safe_run: raise ValueError('A numeric run identifier is required.')
    path=f'{folder}/{video["tag"]}/{safe_run}.json'
    event['record']=path;event['history']=history
    out['items']=[x for x in items if x['tag']!=video['tag']]+[event]
    out['updated_at']=stamp
    return out,event


def save(root,index,event):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    if event:
        target=root/event['record'];target.parent.mkdir(parents=True,exist_ok=True)
        # Old decisions and all original assets are retained, including reclassification.
        if target.exists() and json.loads(target.read_text())!=event: raise ValueError('A previous decision record must not be overwritten.')
        target.write_text(json.dumps(event,indent=1,ensure_ascii=False)+'\n')
    (root/'index.json').write_text(json.dumps(index,indent=1,ensure_ascii=False)+'\n')
