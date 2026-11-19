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
 report={'available':False,'checked_at':checked,'handle':HANDLE,'source':'YouTube Analytics API','videos':[],'average_view_percentage':None,'note':'No verified retention data; Buffer views are separate.'}
 keys=('YT_CLIENT_ID','YT_CLIENT_SECRET','YT_REFRESH_TOKEN_HOWITTICKS')
 if not all(os.environ.get(k) for k in keys):
  report.update(state='connection_required',note='Connect How It Ticks YouTube with youtube.readonly and yt-analytics.readonly access; no other channel token is used.')
  return report
 try:
  access=request('https://oauth2.googleapis.com/token',data={'client_id':os.environ[keys[0]],'client_secret':os.environ[keys[1]],'refresh_token':os.environ[keys[2]],'grant_type':'refresh_token'})['access_token']
  base='https://www.googleapis.com/youtube/v3/channels?'
  target=request(base+urllib.parse.urlencode({'part':'id','forHandle':HANDLE}),access).get('items',[])
  mine=request(base+urllib.parse.urlencode({'part':'id','mine':'true'}),access).get('items',[])
  if len(target)!=1 or target[0]['id'] not in {x['id'] for x in mine}:raise ValueError('Authenticated channel does not match How It Ticks')
  channel=target[0]['id'];end=datetime.date.today()-datetime.timedelta(days=2);start=end-datetime.timedelta(days=90)
  params={'ids':'channel=='+channel,'startDate':str(start),'endDate':str(end),'metrics':'views,averageViewDuration,averageViewPercentage','dimensions':'video','maxResults':200,'sort':'-views'}
  videos=rows(request('https://youtubeanalytics.googleapis.com/v2/reports?'+urllib.parse.urlencode(params),access))
  eligible=[v for v in videos if v['views']>=100]
  report.update(available=True,state='available' if videos else 'awaiting_report',channel_id=channel,start_date=str(start),end_date=str(end),videos=videos,eligible_video_count=len(eligible),note='Source-reported delayed retention. Compare hooks only after enough views; this does not change narration facts or novelty.')
 except urllib.error.HTTPError as e:report.update(state='connection_or_service_error',note='YouTube analytics access failed with HTTP '+str(e.code)+'. Existing publishing status remains independent.')
 except (ValueError,KeyError):report.update(state='identity_or_report_error',note='Identity or retention report could not be verified. No foreign-channel statistics are accepted.')
 return report

def main():
 report=collect();old,sha=read_document(PATH,{})
 if old.get('available') and not report['available']:report['last_verified_report']=dict((k,v) for k,v in old.items() if k!='last_verified_report')
 write_document(PATH,report,sha,'Refresh identity-checked How It Ticks retention availability')
 print(json.dumps({k:report[k] for k in ('available','state','note')}),flush=True)
if __name__=='__main__':main()
