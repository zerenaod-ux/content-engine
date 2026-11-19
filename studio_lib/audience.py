"""Read-only, identity-checked YouTube retention. No borrowed channel statistics."""
import datetime,json,os,urllib.parse,urllib.request,urllib.error
from studio_lib.service_queue import read_document,write_document
HANDLE='@HowItTicks-p2v'
PATH='data/analytics/howitticks.json'

def request(url,token=None,data=None):
 headers={'Authorization':'Bearer '+token} if token else {}
 req=urllib.request.Request(url,data=urllib.parse.urlencode(data).encode() if data else None,headers=headers)
 with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)

def rows(report):
 headers=[x['name'] for x in report.get('columnHeaders',[])]
 required={'video','views','averageViewDuration','averageViewPercentage'}
 if not required.issubset(headers):raise ValueError('YouTube report omitted required retention measurements')
 result=[]
 for values in report.get('rows',[]):
  item=dict(zip(headers,values))
  if len(values)!=len(headers):raise ValueError('YouTube report has incomplete rows')
  result.append(item)
 return result

def collect():
 checked=datetime.datetime.now(datetime.timezone.utc).isoformat()
 report={'refresh_policy':'on_request','automatic_refresh':False,'available':False,'checked_at':checked,'handle':HANDLE,'source':'YouTube Analytics API','videos':[],'average_view_percentage':None,'note':'No verified retention data; Buffer views are separate.'}
 keys=('YT_CLIENT_ID','YT_CLIENT_SECRET','YT_REFRESH_TOKEN_HOWITTICKS')
 if os.environ.get('CE_RETENTION_REFRESH')!='requested' or not all(os.environ.get(k) for k in keys):
  snapshot={}
  if os.environ.get('GH_TOKEN'):
   try:snapshot,_=read_document(SNAPSHOT_PATH,{})
   except (urllib.error.URLError,OSError,ValueError):pass
  if guidance(snapshot):
   report.update(snapshot,state='available_snapshot',refresh_policy='on_request',automatic_refresh=False,note='Verified owner-connected vidIQ retention snapshot. Owner selected request-only refresh; no automatic analytics requests are made. Writing guidance expires after 48 hours.')
  else:report.update(state='snapshot_stale' if snapshot.get('channel_id')==CHANNEL_ID else 'connection_required',note='A fresh owner-requested report is needed. Request-only refresh is active; no other channel token is used.')
  return report
 try:
  access=request('https://oauth2.googleapis.com/token',data={'client_id':os.environ[keys[0]],'client_secret':os.environ[keys[1]],'refresh_token':os.environ[keys[2]],'grant_type':'refresh_token'})['access_token']
  base='https://www.googleapis.com/youtube/v3/channels?'
  target=request(base+urllib.parse.urlencode({'part':'id','forHandle':HANDLE}),access).get('items',[])
  mine=request(base+urllib.parse.urlencode({'part':'id','mine':'true'}),access).get('items',[])
  if len(target)!=1 or target[0]['id']!=CHANNEL_ID or target[0]['id'] not in {x['id'] for x in mine}:raise ValueError('Authenticated channel does not match How It Ticks')
  channel=target[0]['id'];end=datetime.date.today()-datetime.timedelta(days=2);start=end-datetime.timedelta(days=90)
  params={'ids':'channel=='+channel,'startDate':str(start),'endDate':str(end),'metrics':'views,averageViewDuration,averageViewPercentage','dimensions':'video','maxResults':200,'sort':'-views'}
  videos=rows(request('https://youtubeanalytics.googleapis.com/v2/reports?'+urllib.parse.urlencode(params),access))
  eligible=[v for v in videos if v['views']>=100]
  report.update(available=True,identity_verified=True,state='available' if videos else 'awaiting_report',channel_id=channel,start_date=str(start),end_date=str(end),videos=videos,eligible_video_count=len(eligible),note='Source-reported delayed retention. Compare hooks only after enough views; this does not change narration facts or novelty.')
 except urllib.error.HTTPError as e:report.update(state='connection_or_service_error',note='YouTube analytics access failed with HTTP '+str(e.code)+'. Existing publishing status remains independent.')
 except (ValueError,KeyError):report.update(state='identity_or_report_error',note='Identity or retention report could not be verified. No foreign-channel statistics are accepted.')
 return report

def main():
 report=collect();old,sha=read_document(PATH,{})
 if old.get('available') and not report['available']:report['last_verified_report']=dict((k,v) for k,v in old.items() if k!='last_verified_report')
 write_document(PATH,report,sha,'Refresh identity-checked How It Ticks retention availability')
 print(json.dumps({k:report[k] for k in ('available','state','note')}),flush=True)

CHANNEL_ID='UCXjX-Qu_SeFJN-oV4C2JjSQ'
SNAPSHOT_PATH='data/analytics/howitticks-vidiq.json'

def guidance(report,now=None):
 """Bounded factual evidence for hook/pacing decisions; never a topic/facts override."""
 import math,statistics
 now=now or datetime.datetime.now(datetime.timezone.utc)
 if not isinstance(report,dict) or report.get('identity_verified') is not True or report.get('available') is not True or report.get('channel_id')!=CHANNEL_ID or str(report.get('handle','')).lower()!=HANDLE.lower():return None
 try:
  checked=datetime.datetime.fromisoformat(report['checked_at']);age=(now-checked).total_seconds()
  if not 0<=age<=48*3600:return None
 except (ValueError,KeyError,TypeError):return None
 eligible=[]
 for v in report.get('videos',[]):
  values=[v.get(k) for k in ('views','averageViewDuration','averageViewPercentage')]
  if not all(type(x) in (int,float) and math.isfinite(x) for x in values):continue
  if values[0]>=100 and values[1]>0 and values[2]>0:eligible.append(v)
 if len(eligible)<2:return None
 curves=[];ids={v['video'] for v in eligible}
 for curve in report.get('retention_curves',[]):
  if curve.get('video') not in ids:continue
  points=curve.get('points',[])
  if not points or any(not isinstance(p,list) or len(p)!=2 or not all(type(x) in (int,float) and math.isfinite(x) for x in p) or not 0<=p[0]<=1 or p[1]<0 for p in points):continue
  curves.append({'video':curve['video'],'time_fraction_and_watch_ratio':[min(points,key=lambda p:abs(p[0]-q)) for q in (.1,.2,.3,.5,.9)],'note':'Watch ratio includes replay; this is not a unique-viewer percentage.'})
 return {'retention_curve_landmarks':curves,'source':report.get('source','YouTube Analytics API'),'channel_id':CHANNEL_ID,'checked_at':report['checked_at'],'report_end_date':report.get('end_date'),'qualified_videos':len(eligible),'median_average_view_percentage':statistics.median(v['averageViewPercentage'] for v in eligible),'median_average_view_seconds':statistics.median(v['averageViewDuration'] for v in eligible),'writing_instruction':'Keep the opening question and the first reveal concise; put explanatory detail into the later causal steps. These early channel measurements are evidence, not proof of a winning formula. Preserve all physical facts, supported actions, word/duration bounds, narrator identity and the no-repeat rule. Never quote analytics in narration.','limitations':'Small channel sample; source is delayed. Replay can produce ratios over 100%. Average watch time alone does not identify an exact drop-off.'}

def writing_context():
 """Analytics failures cannot stop the independent media pipeline."""
 if not os.environ.get('GH_TOKEN'):return None
 try:
  direct,_=read_document(PATH,{})
  result=guidance(direct)
  if result:return result
  snapshot,_=read_document(SNAPSHOT_PATH,{})
  return guidance(snapshot)
 except (urllib.error.URLError,OSError,ValueError,TypeError):return None

if __name__=='__main__':main()
