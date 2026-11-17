from studio_lib.cinema.topic_memory import prompt_history
"""System-selected original single-topic long video, generated entirely on GitHub."""
import argparse,asyncio,base64,json,math,os,subprocess,time
from pathlib import Path
from studio_lib.providers import call
from studio_lib.topic_guard import duplicate,signature
from studio_lib.cinema.auto_topic import api,read
from studio_lib.cinema.build import voice,soundtrack
from studio_lib.cinema.review import review
from studio_lib.longform.contract import ACTIONS,SOURCES,FACTS,errors,require_media
from studio_lib.longform.render import frame,WIDTH,HEIGHT

def select(out):
 rows=[]
 for path in ('data/scenes/history.json','data/scenes/videos.json','data/scenes/topic-ledger.json'):
  data,_=read(path)
  if not isinstance(data,list):raise ValueError('Full topic history unavailable')
  rows+=data
 rejected=[]
 for i in range(4):
  candidate=call('Choose a genuinely new original full-video topic. Return JSON only.',
   'The system chooses the subject. Return {"topic":"specific How/Why question","mechanism":"rack_pinion or lead_screw"}. Use only these actual supported scopes, never claim an entire factory or vehicle. No reworded repeat. SCOPES: '+json.dumps(SOURCES)+' FULL HISTORY: '+json.dumps(prompt_history(rows))+' REJECTED: '+json.dumps(rejected),max_tokens=700,temperature=.5)
  (out/f'topic-selection-{i}.json').write_text(json.dumps(candidate,indent=2))
  topic=candidate.get('topic','');mechanism=candidate.get('mechanism')
  reason=duplicate(topic,rows)
  if mechanism not in SOURCES or reason:rejected.append(reason or 'Unsupported scope');continue
  own=str(os.environ['GITHUB_RUN_ID'])
  for attempt in range(4):
   ledger,sha=read('data/scenes/topic-ledger.json')
   if duplicate(topic,[r for r in ledger if str(r.get('owner'))!=own]):raise ValueError('New topic was concurrently reserved')
   ledger.append({'topic':topic,'topic_key':signature(topic),'owner':own,'mechanism':mechanism,'format':'original_full','state':'reserved'})
   try:
    api('contents/data/scenes/topic-ledger.json',{'message':'Reserve original full-video topic before generation','branch':'main','sha':sha,'content':base64.b64encode((json.dumps(ledger,indent=2)+'\n').encode()).decode()});break
   except __import__('urllib.error',fromlist=['HTTPError']).HTTPError as e:
    if e.code not in (409,422) or attempt==3:raise
    time.sleep(2)
  return candidate
 raise ValueError('No unique supported full-video topic selected')

def plan(out):
 saved=out/'accepted-plan.json'
 if saved.exists():
  result=json.loads(saved.read_text())
  if not errors(result):return result
 selected=select(out);rejected=[]
 for attempt in range(4):
  result=call('Write one original factual continuous explainer. Return JSON only.',
   'One subject only. Native long format, not assembled shorts. Return {"topic":exact topic,"mechanism":exact id,"title":"How/Why 4-8 words","hook":"2-7 simple words max 40 characters","beats":[{"action":"exact action","say":"30-44 spoken words","camera":"wide|engagement|output"}]}. Exactly sixteen actions in order: '+json.dumps(ACTIONS)+'. Total 480-650 words. First spoken beat ends with ?. Energetic natural delivery, short clauses, concrete cause and effect. No spoken camera directions, padding, horror framing, invented parts or numerical performance. Do not describe an unshown force sensor or invisible force as a literal object. Facts/source and visible action contract: '+json.dumps({'selected':selected,'source':SOURCES[selected['mechanism']],'actions':FACTS})+' PREVIOUS ERRORS: '+json.dumps(rejected),max_tokens=3600,temperature=.35)
  (out/f'raw-plan-{attempt}.json').write_text(json.dumps(result,indent=2));rejected=errors(result)
  if result.get('topic')!=selected['topic'] or result.get('mechanism')!=selected['mechanism']:rejected.append('Preserve selected topic and mechanism')
  if rejected:continue
  critique=call('Audit original narration against the exact shown mechanism. Return JSON only.',
   'Return {"errors":[specific unsupported claims or action mismatches]}. Reject unrelated topics, invented components, energy gain and production narration. CONTRACT: '+json.dumps(SOURCES[selected['mechanism']])+' ACTIONS: '+json.dumps(FACTS)+' PLAN: '+json.dumps(result),max_tokens=1800,temperature=.1)
  (out/f'critique-{attempt}.json').write_text(json.dumps(critique,indent=2))
  rejected=critique.get('errors')
  if not isinstance(rejected,list):raise ValueError('Factual review unavailable')
  if not rejected:saved.write_text(json.dumps(result,indent=2));return result
 raise ValueError('Original full script failed bounded validation: '+str(rejected))

def run(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);started=time.monotonic();p=plan(out)
 # Same voice delivery and measured word timing as shorts; full format has its own duration range.
 tl=asyncio.run(voice(p,out,duration_range=(120,300)));require_media(tl['duration'],WIDTH,HEIGHT)
 soundtrack(tl,out)
 for i,b in enumerate(tl['beats']):frame((b['start']+b['end'])/2,tl,p).save(out/f'check-{i:02}.png')
 fps=20
 proc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{WIDTH}x{HEIGHT}','-framerate',str(fps),'-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p',str(out/'silent.mp4')],stdin=subprocess.PIPE)
 try:
  for n in range(math.ceil(tl['duration']*fps)):
   proc.stdin.write(frame(n/fps,tl,p).tobytes())
   if n%200==0:print('Full-video native frames: '+str(n),flush=True)
 finally:proc.stdin.close()
 if proc.wait():raise RuntimeError('Landscape render failed')
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(out/'silent.mp4'),'-i',str(out/'mix.wav'),'-c:v','copy','-c:a','aac','-b:a','128k','-af','loudnorm=I=-16:TP=-1.5:LRA=9','-t',str(tl['duration']),'-movflags','+faststart',str(out/'video.mp4')],check=True)
 measured=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(out/'video.mp4')]))
 stream=next(s for s in measured['streams'] if s['codec_type']=='video');require_media(float(measured['format']['duration']),stream['width'],stream['height'])
 subprocess.run(['ffmpeg','-v','error','-i',str(out/'video.mp4'),'-f','null','-'],check=True);review(p,tl,out)
 result={'topic':p['topic'],'mechanism':p['mechanism'],'format':'original_full','duration':float(measured['format']['duration']),'width':stream['width'],'height':stream['height'],'manual_script_or_video_edits':False,'selected_by_system':True,'reused_short_assets':False,'owner_approved':False,'wall_seconds':time.monotonic()-started,'source':SOURCES[p['mechanism']]['source'],'quality_state':'technical_checks_passed_owner_visual_review_required'}
 (out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--out',required=True);run(a.parse_args().out)
