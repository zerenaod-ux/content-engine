"""Persist readable job stages and retry only known temporary failures."""
import argparse,datetime,json,os,subprocess,sys,time,urllib.error
from studio_lib.service_queue import read_document,write_document,github
LABELS={'selection':'Selecting a new topic','planning':'Writing and checking narration','voice':'Generating narration','render':'Rendering animation','audio':'Checking finished audio','delivery':'Sending to Studio','ready':'Rendered; Studio delivery pending','delivered':'In Studio; owner review required','queued':'Waiting for shared services'}

def classify_failure(text,attempt):
 lower=text.lower()
 transient=any(x in lower for x in ('noaudioreceived','serviceunavailable','servicebusy','cooldown active','timed out','timeout','http error 429','http 429','http error 503','connection reset'))
 permanent=any(x in lower for x in ('http 413','request too large','unsupported','script failed bounded validation','outside required duration','essential parts leave the frame'))
 retry=transient and not permanent and attempt<4
 return {'retryable':retry,'next_retry_at':time.time()+(2700 if '429' in lower else 900) if retry else None,'reason':'Temporary service or capacity failure' if transient and not permanent else 'Needs a code, content or configuration correction','state':'waiting_to_resume' if retry else 'needs_attention'}

def record(kind,stage,**extra):
 if not os.environ.get('GH_TOKEN'):return
 run=str(os.environ.get('CE_OPERATION_RUN',os.environ['GITHUB_RUN_ID']))
 if not run.isdigit():raise ValueError('Invalid production run reference')
 data={'run_id':run,'attempt':int(os.environ.get('CE_OPERATION_ATTEMPT',os.environ.get('GITHUB_RUN_ATTEMPT','1'))),'kind':kind,'stage':stage,'label':LABELS.get(stage,stage),'updated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_branch':os.environ.get('CE_OPERATION_BRANCH',os.environ.get('GITHUB_REF_NAME')),'owner_approved':False,**extra}
 for path,merge in [('data/operations/jobs/'+run+'.json',False),('data/operations/latest.json',True)]:
  for retry in range(5):
   old,sha=read_document(path,{})
   if merge:
    old.setdefault('jobs',{})[kind]=data;payload=old
   else:payload=data
   try:write_document(path,payload,sha,'Update '+kind+' production stage');break
   except urllib.error.HTTPError as e:
    if e.code not in (409,422) or retry==4:raise
    time.sleep(1)

def execute(kind,command,success_stage='ready'):
 record(kind,'selection',state='running');process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
 tail=[];last_stage=None
 for line in process.stdout:
  print(line,end='',flush=True);tail=(tail+[line])[-100:]
  if line.startswith('CE_STAGE='):
   last_stage=line.strip().split('=',1)[1];record(kind,last_stage,state='running')
 status=process.wait()
 if status:
  info=classify_failure(''.join(tail),int(os.environ.get('GITHUB_RUN_ATTEMPT','1')))
  if kind=='self-test' and os.environ.get('CE_RECOVERY_TEST')=='1' and info['retryable']:info['next_retry_at']=time.time()
  record(kind,'Stopped',**info)
 else:record(kind,'delivered' if last_stage=='delivered' else success_stage,state='awaiting_review' if last_stage=='delivered' else 'rendered' if success_stage=='ready' else 'running')
 return status

def watch():
 # One coordinator workflow is serialized; a successful rerun removes eligibility
 # by overwriting its record. Never repeats a successful publishing operation.
 try:files=github('contents/data/operations/jobs?ref=main')
 except urllib.error.HTTPError as e:
  if e.code==404:return
  raise
 for item in files:
  if item.get('type')!='file':continue
  record_data,_=read_document(item['path'],{})
  if not record_data.get('retryable') or (record_data.get('next_retry_at') or float('inf'))>time.time():continue
  run=github('actions/runs/'+str(record_data['run_id']))
  if run['status']!='completed' or run['conclusion']!='failure':continue
  if (run['head_branch'],run['name']) not in [('studio-cinematic-proof','Cinematic system comparison (not posted)'),('studio-cinematic-proof','Original How It Ticks full video'),('main','scene-factory'),('main','Recovery self-test')]:continue
  if int(run.get('run_attempt',1))>=4:continue
  github('actions/runs/'+str(run['id'])+'/rerun-failed-jobs','POST',{})
  print('Requested bounded recovery of '+record_data['kind']+' from its saved stages',flush=True)

def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
 run=sub.add_parser('run');run.add_argument('--kind',required=True);run.add_argument('--success-stage',default='ready');run.add_argument('command',nargs=argparse.REMAINDER)
 sub.add_parser('watch')
 stage=sub.add_parser('stage');stage.add_argument('--kind',required=True);stage.add_argument('--stage',required=True)
 a=p.parse_args()
 if a.action=='watch':watch();return
 if a.action=='stage':record(a.kind,a.stage,state='awaiting_review' if a.stage=='delivered' else 'running');return
 command=a.command[1:] if a.command and a.command[0]=='--' else a.command
 if not command:raise ValueError('Missing production command')
 raise SystemExit(execute(a.kind,command,a.success_stage))
if __name__=='__main__':main()
