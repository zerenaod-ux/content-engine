"""Replace only an undecided diagnostic card with its verified correction."""
import json,os,re,shutil,subprocess,time,urllib.error
from pathlib import Path
from studio_lib.service_queue import github,read_document,write_document
from studio_lib.quality_gate import require_seal

def guard(card,tag):
 labels={x['name'] for x in card.get('labels',[])}
 if card.get('state')!='open' or labels&{'ce-approve','ce-skip'}:raise ValueError('Preserve existing owner decision; correction cannot replace this card')
 if tag not in card.get('body',''):raise ValueError('Correction target does not match the existing review card')

def updated_rows(rows,tag,url,source):
 matches=[row for row in rows if row.get('tag')==tag]
 if len(matches)!=1:raise ValueError('Existing diagnostic index entry is missing or ambiguous')
 result=json.loads(json.dumps(rows));row=next(row for row in result if row.get('tag')==tag)
 if row.get('video')!=url:
  prior=row.setdefault('previous_versions',[])
  if row.get('video') and row['video'] not in prior:prior.append(row['video'])
  row['video']=url
 row['correction_source_run']=str(source);return result

def command(*args):return subprocess.check_output(args,text=True).strip()
def main():
 config=json.loads(Path('publish/daily-correction-delivery.json').read_text());source=str(config['source_run']);issue=int(config['issue']);tag=config['tag']
 if not re.fullmatch(r'ce-\d{8}-\d{4}',tag):raise ValueError('Invalid correction identity')
 run=github('actions/runs/'+source)
 if run.get('name')!='Verify corrected daily short media' or run.get('head_branch')!='main' or run.get('conclusion')!='success':raise ValueError('Untrusted correction source')
 card=github('issues/'+str(issue));guard(card,tag)
 work=Path('correction');command('gh','run','download',source,'--name','corrected-daily-media-'+source,'--dir',str(work))
 require_seal(work,'short')
 plan=json.loads((work/'plan.json').read_text());report=json.loads((work/'result.json').read_text())
 if report.get('manual_generated_plan_edits') is not False:raise ValueError('Missing automatic-generation provenance')
 repo=os.environ['GITHUB_REPOSITORY'];pages=Path('corrected-pages')
 command('git','clone','--depth','1','--branch','gh-pages','https://x-access-token:'+os.environ['GH_TOKEN']+'@github.com/'+repo+'.git',str(pages))
 (pages/'videos').mkdir(exist_ok=True);shutil.copyfile(work/'video.mp4',pages/'videos'/(tag+'.mp4'))
 command('git','-C',str(pages),'config','user.name','github-actions[bot]');command('git','-C',str(pages),'config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
 command('git','-C',str(pages),'add','videos/'+tag+'.mp4')
 if subprocess.run(['git','-C',str(pages),'diff','--cached','--quiet']).returncode:
  command('git','-C',str(pages),'commit','-m','Verified correction for '+tag)
  for attempt in range(4):
   push=subprocess.run(['git','-C',str(pages),'push'],capture_output=True,text=True)
   if push.returncode==0:break
   command('git','-C',str(pages),'pull','--rebase');time.sleep(2)
  else:raise RuntimeError('Corrected media could not be persisted')
 sha=command('git','-C',str(pages),'rev-parse','HEAD');url='https://cdn.jsdelivr.net/gh/'+repo+'@'+sha+'/videos/'+tag+'.mp4'
 for attempt in range(5):
  guard(github('issues/'+str(issue)),tag)
  rows,blob=read_document('data/scenes/videos.json',None)
  if not isinstance(rows,list):raise ValueError('Video index unavailable')
  try:write_document('data/scenes/videos.json',updated_rows(rows,tag,url,source),blob,'Update existing card media to verified correction');break
  except urllib.error.HTTPError as error:
   if error.code not in (409,422) or attempt==4:raise
   time.sleep(1)
 card=github('issues/'+str(issue));guard(card,tag)
 body=re.sub(r'(?m)^Watch: .*$', 'Watch: '+url,card['body']).split('\n### Inspection hold')[0]
 body+='\n\n### Verified correction for owner review\n\nSystem-rendered '+str(round(report['duration'],2))+'-second correction. Counterweight visibility, factual narration, encoded audio and full decode were checked. Automated speech review is not direct human listening. Earlier media is retained in index provenance; this update creates no new card, approval or publishing booking.\n'
 title=plan['title']+' 🚢'
 github('issues/'+str(issue),'PATCH',{'title':'How It Ticks: '+title,'body':body})
 current=github('issues/'+str(issue));guard(current,tag)
 if url not in current['body']:raise RuntimeError('Studio card read-back failed')
 print('Corrected media saved and existing undecided review card verified.')

if __name__=='__main__':main()
