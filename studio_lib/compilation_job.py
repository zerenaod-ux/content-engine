"""CI entry: build the long compilation from owner-approved shorts, archive it and open one review card.
Exits quietly (no failure email) when there are not enough approved shorts yet or one was made in the last 14 days."""
import datetime,json,os,sys
from pathlib import Path
from studio_lib import compilation,winners
from studio_lib.delivery_archive import release_or_record
from studio_lib.review_cards import find_by_marker
os.environ.setdefault('SOURCE_RUN',os.environ.get('GITHUB_RUN_ID','0'))
from studio_lib.cinema.deliver import api,get,put_file,REPO,RUN,TOKEN
import urllib.request

def _read(p,d):
 try:return json.loads(Path(p).read_text())
 except Exception:return d

def main():
 print('CE_STAGE=compilation',flush=True)
 videos=_read('data/scenes/videos.json',[]);idx=_read('data/scenes/review/index.json',{}).get('items',[])
 now=datetime.datetime.utcnow()
 for v in videos:
  if isinstance(v,dict) and v.get('format')=='compilation':
   try:age=(now-datetime.datetime.fromisoformat(str(v['date'])[:10])).days
   except Exception:continue
   if age<14:print('A compilation was made',age,'days ago; skipping');return
 try:w=winners.report().get('weights',{});rank=sorted(w,key=lambda m:-w[m])
 except Exception:rank=[]
 out=Path('long-output')/'video.mp4'
 try:plan=compilation.make(videos,idx,rank,Path('long-work'),out)
 except ValueError as e:
  print('Not ready:',e);Path('long-output').mkdir(exist_ok=True);Path('long-output/not-ready.txt').write_text(str(e));return
 run=api('GET','actions/runs/'+RUN);stamp=run['created_at'].replace('-','').replace(':','');tag='ce-long-'+stamp[:8]+'-'+stamp[9:13]
 title=plan['title']+' ⚙️';size=out.stat().st_size
 if not 100000<size<90000000:raise ValueError('Compilation size outside supported range: %d'%size)
 uploaded=put_file('videos/'+tag+'.mp4',out.read_bytes(),'gh-pages');sha=uploaded['commit']['sha']
 existing=get('releases/tags/'+tag)
 if not existing:existing=release_or_record(api,get,'releases/tags/'+tag,{'tag_name':tag,'target_commitish':run['head_sha'],'name':'How It Ticks compilation: '+title,'body':'Compilation of owner-approved shorts. Owner review required; not approved or published. Source run: '+run['html_url'],'prerelease':True},Path('long-output/archive-warning.json'))
 name=tag+'.mp4'
 if existing and not any(x['name']==name for x in existing.get('assets',[])):
  req=urllib.request.Request('https://uploads.github.com/repos/'+REPO+'/releases/'+str(existing['id'])+'/assets?name='+name,data=out.read_bytes(),method='POST',headers={'Authorization':'Bearer '+TOKEN,'Content-Type':'video/mp4','Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=300) as r:json.load(r)
 url='https://zerenaod-ux.github.io/content-engine/videos/'+name
 def merge(rows):
  if not any(v.get('tag')==tag for v in rows):rows.append({'date':run['created_at'][:10],'tag':tag,'title':title,'topic':'compilation','mechanism':'compilation','video':url,'kind':'long','format':'compilation','duration':plan['duration'],'chapters':[c['tag'] for c in plan['chapters']],'source_run':RUN,'media_commit':sha,'owner_approved':False})
  return rows
 put_file('data/scenes/videos.json',b'','main',merge)
 marker='compilation-source-run: '+RUN
 for label in ('scene-review','checks-warn','long-video'):
  if not get('labels/'+label):api('POST','labels',{'name':label,'color':'1f6feb'})
 if not find_by_marker(api,'long-video',marker):
  api('POST','issues',{'title':'How It Ticks: '+title,'labels':['scene-review','checks-warn','long-video'],'body':'Long compilation of %d shorts you already approved, 16:9, with chapter cards and voice lead-ins.\n\nWatch: %s\n\nDuration: %d seconds.\n\nChapters:\n%s\n\nApprove or Skip in Studio. Nothing is auto-approved or published.\n\n%s'%(len(plan['chapters']),url,round(plan['duration']),plan['description'],marker)})
 print('CE_STAGE=delivered',flush=True)
if __name__=='__main__':main()
