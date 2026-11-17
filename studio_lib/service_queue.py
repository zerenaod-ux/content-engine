"""Conflict-safe shared-service leases; rendering never holds a service lease."""
import contextlib,copy,datetime,json,os,time,urllib.request,urllib.error

class ServiceBusy(RuntimeError):pass

def transition(state,service,owner,priority,now,ttl=180):
 state=copy.deepcopy(state);leases=state.setdefault('leases',{});waiters=state.setdefault('waiters',[])
 prior=next((w for w in waiters if w['owner']==owner),None)
 state['waiters']=waiters=[w for w in waiters if now-w['seen']<600 and w['owner']!=owner]
 waiters.append({'owner':owner,'service':service,'priority':priority,'seen':now,'joined':prior.get('joined',prior['seen']) if prior else now})
 lease=leases.get(service)
 if lease and lease['until']<=now:leases.pop(service);lease=None
 first=min((w for w in waiters if w['service']==service),key=lambda w:(w['priority'],w.get('joined',w['seen']),w['owner']))
 acquired=not lease and first['owner']==owner
 if acquired:
  leases[service]={'owner':owner,'until':now+ttl}
  state['waiters']=[w for w in waiters if w['owner']!=owner]
 return state,acquired

def github(path,method='GET',body=None):
 req=urllib.request.Request('https://api.github.com/repos/'+os.environ.get('GITHUB_REPOSITORY','zerenaod-ux/content-engine')+'/'+path,method=method,data=json.dumps(body).encode() if body is not None else None,headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)

def read_document(path,default):
 import base64
 try:
  result=github('contents/'+path+'?ref=main');return json.loads(base64.b64decode(result['content'])),result['sha']
 except urllib.error.HTTPError as e:
  if e.code==404:return copy.deepcopy(default),None
  raise

def write_document(path,state,sha,message):
 import base64
 body={'message':message,'branch':'main','content':base64.b64encode((json.dumps(state,indent=2)+'\n').encode()).decode()}
 if sha:body['sha']=sha
 return github('contents/'+path,'PUT',body)

@contextlib.contextmanager
def lease(service):
 if os.environ.get('CE_SHARED_SERVICES')!='1':yield;return
 if not os.environ.get('GH_TOKEN'):raise ServiceBusy('Shared-service coordination is unavailable')
 path='data/operations/service-leases.json';owner=os.environ['GITHUB_RUN_ID']+'-'+os.environ.get('GITHUB_RUN_ATTEMPT','1')+'-'+service
 priority=0 if 'short' in os.environ.get('CE_JOB_KIND','') else 1;start=time.monotonic();held=False
 try:
  while time.monotonic()-start<180:
   state,sha=read_document(path,{'leases':{},'waiters':[]});new,acquired=transition(state,service,owner,priority,time.time())
   try:write_document(path,new,sha,'Coordinate shared '+service+' access')
   except urllib.error.HTTPError as e:
    if e.code in (409,422):time.sleep(1);continue
    raise
   if acquired:
    held=True;print('CE_STAGE='+('voice' if service=='voice' else 'planning'),flush=True);break
   print('CE_STAGE=queued',flush=True)
   print('Shared '+service+' capacity queued; saved work is retained',flush=True);time.sleep(10)
  if not held:raise ServiceBusy('Shared service is busy; resume from saved stages later')
  yield
 finally:
  for attempt in range(4):
   state,sha=read_document(path,{'leases':{},'waiters':[]})
   if state.get('leases',{}).get(service,{}).get('owner')==owner:state['leases'].pop(service)
   state['waiters']=[w for w in state.get('waiters',[]) if w['owner']!=owner]
   try:write_document(path,state,sha,'Release shared '+service+' access');break
   except urllib.error.HTTPError as e:
    if e.code not in (409,422):raise
    time.sleep(1)
