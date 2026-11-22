"""Record the next real unattended delivery; tests or manual samples never count."""
import datetime,json,math,time,urllib.error
from studio_lib.service_queue import github,read_document,write_document
PATH='data/operations/unattended-verification.json'

def verify_row(row,run):
 origin=row.get('generation_origin',{});proof=row.get('production_evidence',{});errors=[]
 if not isinstance(origin,dict) or not isinstance(proof,dict):return ['Production provenance missing']
 automatic=run.get('event')=='schedule' or (run.get('event')=='workflow_dispatch' and origin.get('automatic_slot') is True and run.get('actor',{}).get('login')=='github-actions[bot]')
 if not automatic:errors.append('This is not an automatically started scheduled/catch-up run')
 if origin.get('event')!=run.get('event') or str(origin.get('run_id'))!=str(run.get('id')):errors.append('Run provenance does not match GitHub')
 if run.get('name')!='scene-factory' or run.get('head_branch')!='main' or origin.get('source_ref')!='main':errors.append('Unexpected production workflow or branch')
 if run.get('status')!='completed' or run.get('conclusion')!='success':errors.append('The full workflow has not completed successfully')
 if origin.get('attempt')!=1 or run.get('run_attempt')!=1:errors.append('This proof was not a first-attempt unattended completion')
 if origin.get('event_sha')!=run.get('head_sha'):errors.append('Event source commit mismatch')
 if origin.get('manual_media_edits') is not False:errors.append('Manual-media-edit provenance missing')
 if proof.get('policy')!='unattended-proof-v1' or proof.get('errors')!=[] or proof.get('owner_approved') is not False:errors.append('Complete-output evidence is missing or failed')
 duration=proof.get('duration')
 if (proof.get('width'),proof.get('height'))!=(1080,1920) or type(duration) not in (int,float) or not math.isfinite(duration) or not 40<=duration<=70:errors.append('Verified media format is wrong')
 if proof.get('novelty_policy')!='original-idea-and-visuals-v1':errors.append('Permanent novelty evidence is missing')
 if proof.get('alignment_revision')!='causal-component-actions-v4' or proof.get('render_policy')!='native-studio-1080-v1':errors.append('The expected timing/visual implementation was not used')
 if proof.get('voice')!='am_fenrir' or proof.get('voice_policy')!='how-it-ticks-narrator-v2':errors.append('The fixed narrator policy is missing')
 if not isinstance(proof.get('media_sha256'),str) or len(proof['media_sha256'])!=64:errors.append('Verified media identity is missing')
 if not row.get('video') or not row.get('tag'):errors.append('Studio media/index delivery is missing')
 return errors

def expected_start(control,now=None):
 from zoneinfo import ZoneInfo
 zone=ZoneInfo('America/Chicago');local=(now or datetime.datetime.now(datetime.timezone.utc)).astimezone(zone)
 if control.get('business_day')!=local.date().isoformat():return None
 day=local.date()
 if control.get('ready_today',0)>=control.get('daily_target',3):day+=datetime.timedelta(days=1)
 for h,m in ((3,5),(11,5),(19,5)):
  candidate=datetime.datetime.combine(day,datetime.time(h,m),zone)
  if candidate>local:return candidate.isoformat()
 return datetime.datetime.combine(day+datetime.timedelta(days=1),datetime.time(3,5),zone).isoformat()

def observe():
 videos,_=read_document('data/scenes/videos.json',None)
 if not isinstance(videos,list):raise ValueError('Cannot verify unattended delivery without authoritative history')
 old,sha=read_document(PATH,{})
 report={'state':'awaiting_next_unattended_delivery','checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verified':False,'note':'Manual proof videos and skipped quota slots do not prove a newly generated unattended video.'}
 candidates=[r for r in videos if isinstance(r.get('generation_origin'),dict)]
 for row in reversed(candidates[-8:]):
  run_id=row['generation_origin'].get('run_id')
  if not str(run_id).isdigit():continue
  if old.get('verified') and str(old.get('run_id'))==str(run_id):
   report=dict(old,checked_at=report['checked_at']);break
  run=github('actions/runs/'+str(run_id));errors=verify_row(row,run)
  if errors:continue
  # Require the actual open or filed review card too, not an optimistic producer label.
  issues=[]
  for page in range(1,1001):
   batch=github('issues?state=all&per_page=100&page='+str(page));issues.extend(batch)
   if len(batch)<100:break
  else:raise ValueError('Review-card history was not exhausted; verification held')
  cards=[x for x in issues if row['video'] in str(x.get('body','')) and row['tag'] in str(x.get('body',''))]
  if len(cards)!=1:continue
  report.update(state='verified',verified=True,run_id=run_id,tag=row['tag'],title=row.get('title'),video=row['video'],studio_issue=cards[0]['number'],production_evidence=row['production_evidence'],note='One real automatically started run completed without a rerun and delivered this exact verified source to its Studio card. This does not prove every future run.')
  break
 if not report['verified']:
  control,_=read_document('data/operations/factory-control.json',{})
  report.update(next_eligible_slot=expected_start(control),daily_target=control.get('daily_target'),completed_today=control.get('ready_today'),quota_reason=control.get('reason'),schedule_note='An intended start window, not a completion promise; queued jobs and GitHub schedule delays are possible.')
 if old.get('verified') and not report['verified']:report['last_verified']=old.get('last_verified') or {k:v for k,v in old.items() if k!='last_verified'}
 for attempt in range(5):   # two runs can write this file at the same moment (HTTP 409): re-read the file version and try again
  try:write_document(PATH,report,sha,'Record real unattended production evidence without generating or publishing media');break
  except urllib.error.HTTPError as e:
   if e.code not in (409,422) or attempt==4:raise
   time.sleep(2+attempt*2);_,sha=read_document(PATH,{})
 print(json.dumps(report),flush=True);return report
if __name__=='__main__':observe()
