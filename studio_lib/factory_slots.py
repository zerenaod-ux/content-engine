"""Reconcile three Chicago-time daily outputs; never approve or publish media."""
import argparse,datetime,json,os,re,time
from zoneinfo import ZoneInfo
from studio_lib.service_queue import github,read_document,write_document
from studio_lib.registry import REGISTRY
from studio_lib import novelty
TZ=ZoneInfo('America/Chicago')
SLOTS=((3,5),(11,5),(19,5))
STATE='data/operations/factory-control.json'

def decision(now,videos,available,active=False):
 now=now.astimezone(TZ);due=sum((now.hour,now.minute)>=(h,m) for h,m in SLOTS)
 today=[]
 for row in videos:
  match=re.fullmatch(r'ce-(\d{8})-(\d{4})',str(row.get('tag','')))
  if not match:continue
  stamped=datetime.datetime.strptime(''.join(match.groups()),'%Y%m%d%H%M').replace(tzinfo=datetime.timezone.utc).astimezone(TZ)
  if stamped.date()==now.date():today.append(row['tag'])
 ready=len(set(today));remaining=max(0,due-ready)
 reason='A generation run is already active' if active else 'No unused supported visuals remain' if remaining and not available else 'Daily output target already covered' if not remaining else 'A due generation slot needs a fresh video'
 return {'business_day':now.date().isoformat(),'timezone':'America/Chicago','slots':['03:05','11:05','19:05'],'due_slots':due,'ready_today':ready,'daily_target':3,'unused_visuals':len(available),'should_build':bool(remaining and available and not active),'reason':reason}

def snapshot(exclude_run=None):
 now=datetime.datetime.now(datetime.timezone.utc)
 videos,_=read_document('data/scenes/videos.json',None)
 if not isinstance(videos,list):raise ValueError('Daily output history unavailable; refusing to guess quota')
 runs=github('actions/runs?per_page=60')['workflow_runs']
 active=any(r.get('name')=='scene-factory' and str(r.get('id'))!=str(exclude_run) and r.get('status') in (('in_progress',) if exclude_run else ('queued','in_progress','waiting','requested','pending')) for r in runs)
 available=novelty.unused(REGISTRY,novelty.records())   # 2026-11-23 owner: kit-recipe fallback PAUSED (looked far weaker than hand-built machines); hold when none left
 return decision(now,videos,available,active)

def admit():
 scheduled=os.environ.get('GITHUB_EVENT_NAME')=='schedule' or os.environ.get('CE_AUTOMATIC_SLOT')=='true'
 result=snapshot(os.environ.get('GITHUB_RUN_ID')) if scheduled else {'should_build':True,'reason':'Explicitly requested system-generated sample or unfinished recovery'}
 output=os.environ.get('GITHUB_OUTPUT')
 if output:
  with open(output,'a') as f:f.write('should_build='+str(result['should_build']).lower()+'\n')
 if scheduled and not result['should_build']:
  from studio_lib.recovery import record
  record('daily-short','Waiting for fresh visuals' if not result['unused_visuals'] and result['due_slots']>result['ready_today'] else 'Daily target covered',state='held_for_novelty' if not result['unused_visuals'] and result['due_slots']>result['ready_today'] else 'idle',reason=result['reason'],retryable=False)
 print(json.dumps(result),flush=True)
 return result

def watch():
 policy,_=read_document('publish/factory-policy.json',{})
 if not isinstance(policy,dict) or policy.get('enabled') is not True:
  print('Daily catch-up is staged; regular scheduled generation is unchanged',flush=True);return {'enabled':False}
 result=snapshot();old,sha=read_document(STATE,{})
 if not isinstance(old,dict):raise ValueError('Factory reconciliation record is malformed')
 day=result['business_day'];attempts=int(old.get('dispatches',0)) if old.get('business_day')==day else 0
 pending=old.get('requested_at',0) if old.get('business_day')==day else 0
 if result['should_build'] and pending and time.time()-float(pending)<600:result.update(should_build=False,reason='A catch-up dispatch was just requested')
 if result['should_build'] and attempts>=6:result.update(should_build=False,reason='Daily bounded catch-up attempts exhausted; inspect the visible failures')
 # Wait for known temporary recovery instead of wasting another fresh subject.
 latest,_=read_document('data/operations/latest.json',{})
 job=latest.get('jobs',{}).get('daily-short',{}) if isinstance(latest,dict) else {}
 if result['should_build'] and job.get('state')=='waiting_to_resume' and job.get('retryable'):result.update(should_build=False,reason='The system is retaining an unfinished temporary-failure recovery')
 report=dict(result,dispatches=attempts,requested_at=pending,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
 if result['should_build']:
  report.update(dispatches=attempts+1,requested_at=time.time())
  write_document(STATE,report,sha,'Reserve one bounded missing daily factory dispatch')
  github('actions/workflows/content-engine.yml/dispatches','POST',{'ref':'main','inputs':{'topic':'auto','automatic_slot':'true'}})
  print('Requested one missing automatic generation slot; no approval or publishing action',flush=True)
 else:write_document(STATE,report,sha,'Record daily generation capacity and next required work')
 return report

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['admit','watch']);a=p.parse_args();admit() if a.action=='admit' else watch()
