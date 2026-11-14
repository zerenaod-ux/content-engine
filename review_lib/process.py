"""Reconcile review labels, commit folder records, THEN close filed cards.
Retrying safely finishes a decision whose commit succeeded before card closing.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from review_lib.decisions import decision_for,video_for,file_decision,save


def api(path,method='GET',body=None):
    request=urllib.request.Request('https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']+path,
        data=json.dumps(body).encode() if body is not None else None,method=method,
        headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=30) as r:return json.load(r)


def main():
    for name,color in [('ce-approve','22863a'),('ce-skip','cb2431')]:
        try:api('/labels', 'POST',{'name':name,'color':color})
        except urllib.error.HTTPError as e:
            if e.code!=422:raise
    candidates={}
    for label in ('ce-approve','ce-skip'):
        page=1
        while True:
            rows=api(f'/issues?state=all&labels=scene-review,{label}&per_page=100&page={page}')
            for issue in rows:candidates[issue['number']]=issue
            if len(rows)<100:break
            page+=1
    root=Path('data/scenes/review');path=root/'index.json'
    index=json.loads(path.read_text()) if path.exists() else {'version':1,'items':[]}
    catalog=json.loads(Path('data/scenes/videos.json').read_text())
    completed=[];failures=[]
    for number in sorted(candidates):
        # Refresh labels so an older event never overrides the owner's newer choice.
        issue=api('/issues/'+str(number))
        try:
            folder=decision_for(issue)
            if not folder:continue
            video=video_for(issue,catalog)
            index,event=file_decision(index,issue,video,folder,os.environ['GITHUB_RUN_ID']+'-'+os.environ.get('GITHUB_RUN_ATTEMPT','1'))
            if event:save(root,index,event)
            completed.append(number)
        except ValueError as e:failures.append(f'Card {number}: {e}')
    if completed:
        subprocess.run(['git','add','data/scenes/review'],check=True)
        if subprocess.run(['git','diff','--cached','--quiet']).returncode:
            subprocess.run(['git','commit','-m','File Content Engine review decisions'],check=True)
            for attempt in range(3):
                subprocess.run(['git','pull','--rebase'],check=True)
                if subprocess.run(['git','push']).returncode==0:break
            else:raise RuntimeError('Folder records could not be saved; cards remain open.')
        # Durable folder records exist on the remote before cards leave Review.
        for number in completed:
            api('/issues/'+str(number),'PATCH',{'state':'closed'})
    for failure in failures:print(failure,file=sys.stderr)
    if failures:raise SystemExit(1)

if __name__=='__main__':main()
