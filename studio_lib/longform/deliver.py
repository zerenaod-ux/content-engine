"""Archive a qualifying original full video and open one Studio review card."""
import datetime,json,os,urllib.request
from pathlib import Path
from studio_lib.longform.contract import require_media
# Existing delivery's conflict-safe file writer and authenticated GitHub transport.
os.environ.setdefault('SOURCE_RUN',os.environ['GITHUB_RUN_ID'])
from studio_lib.cinema.deliver import api,get,put_file,REPO,RUN,TOKEN

def main():
 print('CE_STAGE=delivery',flush=True)
 root=Path('full-output');result=json.loads((root/'result.json').read_text());plan=json.loads((root/'accepted-plan.json').read_text())
 if result.get('format')!='original_full' or result.get('manual_script_or_video_edits') is not False or result.get('selected_by_system') is not True or result.get('reused_short_assets') is not False:raise ValueError('Original full-video provenance unavailable')
 require_media(result['duration'],result['width'],result['height'])
 video=root/'video.mp4'
 if not 100000<video.stat().st_size<90000000:raise ValueError('Original full-video delivery size outside supported range')
 run=api('GET','actions/runs/'+RUN)
 if run['head_branch']!='studio-cinematic-proof' or run['name']!='Original How It Ticks full video':raise ValueError('Untrusted full-video source')
 stamp=run['created_at'].replace('-','').replace(':','');tag='ce-long-'+stamp[:8]+'-'+stamp[9:13]
 title=plan['title'].strip()+' ⚙️'
 existing=get('releases/tags/'+tag)
 if not existing:existing=api('POST','releases',{'tag_name':tag,'target_commitish':run['head_sha'],'name':'How It Ticks original full video: '+title,'body':'Original system-selected single-topic native landscape video. Owner review required; not approved or published.','prerelease':True})
 name=tag+'.mp4'
 if not any(x['name']==name for x in existing.get('assets',[])):
  req=urllib.request.Request('https://uploads.github.com/repos/'+REPO+'/releases/'+str(existing['id'])+'/assets?name='+name,data=video.read_bytes(),method='POST',headers={'Authorization':'Bearer '+TOKEN,'Content-Type':'video/mp4','Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=180) as r:json.load(r)
 put_file('videos/'+name,video.read_bytes(),'gh-pages')
 url='https://zerenaod-ux.github.io/content-engine/videos/'+name
 def merge(rows):
  if not any(v.get('tag')==tag for v in rows):rows.append({'date':run['created_at'][:10],'tag':tag,'title':title,'topic':plan['topic'],'video':url,'kind':'long','format':'original_full','duration':result['duration'],'source_run':RUN,'owner_approved':False})
  return rows
 put_file('data/scenes/videos.json',b'','main',merge)
 marker='original-full-source-run: '+RUN
 for label in ('scene-review','checks-warn','long-video'):
  if not get('labels/'+label):api('POST','labels',{'name':label,'color':'1f6feb'})
 cards=api('GET','issues?state=all&labels=long-video&per_page=100')
 if not any(marker in (i.get('body') or '') for i in cards):
  api('POST','issues',{'title':'How It Ticks: '+title,'labels':['scene-review','checks-warn','long-video'],'body':'Original full video, one system-selected topic, native 16:9. NOT a compilation. No manual generated-script/video edits.\n\nWatch: '+url+'\n\nDuration: '+str(round(result['duration']))+' seconds.\n\nChecks: automated encoding/audio passed; owner scientific and visual review required. No claim of human listening.\n\nApprove or Skip in Studio. Nothing is auto-approved or published.\n\n'+marker})
 print('CE_STAGE=delivered',flush=True)
 print('Original full-video media and index saved; Studio review card available',flush=True)
if __name__=='__main__':main()
