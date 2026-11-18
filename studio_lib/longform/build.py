from studio_lib.cinema.topic_memory import prompt_history
"""System-selected original single-topic long video, generated entirely on GitHub."""
import argparse,asyncio,base64,json,math,os,subprocess,time
from pathlib import Path
from studio_lib.providers import call
from studio_lib.quality_gate import seal
from studio_lib.topic_guard import duplicate,signature
from studio_lib.cinema.auto_topic import api,read
from studio_lib.cinema.build import voice,soundtrack
from studio_lib.cinema.review import review
from studio_lib.longform.contract import ACTIONS,SOURCES,FACTS,mechanism_facts,errors,require_media
from studio_lib.longform.repair import repair_sections,repair_metadata,unsupported_comparison
from studio_lib.longform.render import frame,WIDTH,HEIGHT

def select(out):
 rows=[];created=[]
 for path in ('data/scenes/history.json','data/scenes/videos.json','data/scenes/topic-ledger.json'):
  data,_=read(path)
  if not isinstance(data,list):raise ValueError('Full topic history unavailable')
  rows+=data
  if path=='data/scenes/videos.json':created=data
 owned=[r for r in rows if str(r.get('owner'))==str(os.environ['GITHUB_RUN_ID']) and r.get('format')=='original_full']
 if owned:return {'topic':owned[-1]['topic'],'mechanism':owned[-1]['mechanism']}
 available={k:v for k,v in SOURCES.items() if not any(r.get('mechanism')==k for r in created)}
 if not available:raise ValueError('No uncovered full-format mechanism remains; do not repeat')
 rejected=[]
 for i in range(4):
  candidate=call('Choose a genuinely new original full-video topic. Return JSON only.',
   'The system chooses the subject. Return {"topic":"specific How/Why question","mechanism":"exact supported id"}. Use only these actual supported scopes, never claim an entire factory or vehicle. No reworded repeat. SCOPES: '+json.dumps(available)+' FULL HISTORY: '+json.dumps(prompt_history(rows))+' REJECTED: '+json.dumps(rejected),max_tokens=700,temperature=.5)
  (out/f'topic-selection-{i}.json').write_text(json.dumps(candidate,indent=2))
  topic=candidate.get('topic','');mechanism=candidate.get('mechanism')
  reason=duplicate(topic,rows)
  if mechanism in SOURCES and unsupported_comparison(topic,mechanism):reason='This topic requires geometry variants not shown by the fixed mechanism; choose a topic within the actual scope'
  if mechanism not in available or reason:rejected.append(reason or 'Unsupported scope');continue
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
  if not errors(result):
   evidence=out/'narration-critique.json'
   if evidence.exists() and json.loads(evidence.read_text()).get('errors')==[]:return result
   check=call('Audit saved narration against its exact rendered mechanism. Return JSON only.', 'Return {"errors":[specific unsupported claims]}. CONTRACT: '+json.dumps(SOURCES[result['mechanism']])+' ACTIONS: '+json.dumps(mechanism_facts(result['mechanism']))+' PLAN: '+json.dumps(result),max_tokens=1600,temperature=.1)
   evidence.write_text(json.dumps(check,indent=2))
   if check.get('errors')==[]:return result
 print('CE_STAGE=planning',flush=True)
 selected=select(out);rejected=[];result=None
 draft=out/'draft-plan.json'
 if draft.exists():
  prior=json.loads(draft.read_text())
  if prior.get('topic')==selected['topic'] and prior.get('mechanism')==selected['mechanism']:result=prior;rejected=errors(prior)
 for attempt in range(7):
  if result is not None and rejected and all('chapter needs' in e.lower() or 'narration must total' in e.lower() or 'title must' in e.lower() or 'hook needs' in e.lower() for e in rejected):
   result=repair_metadata(result,out,attempt)
   result=repair_sections(result,out,attempt)
  else:result=call('Write one original factual continuous explainer. Return JSON only.',
   'One subject only. Native long format, not assembled shorts. Return {"topic":exact topic,"mechanism":exact id,"title":"How/Why 4-8 words","hook":"2-7 simple words max 40 characters","beats":[{"action":"exact action","say":"30-44 spoken words","camera":"wide|engagement|output"}]}. Exactly sixteen actions in order: '+json.dumps(ACTIONS)+'. Total 480-650 words. First spoken beat ends with ?. Energetic natural delivery, short clauses, concrete cause and effect. No spoken camera directions, padding, horror framing, invented parts or numerical performance. Do not describe an unshown force sensor or invisible force as a literal object. Facts/source and visible action contract: '+json.dumps({'selected':selected,'source':SOURCES[selected['mechanism']],'actions':mechanism_facts(selected['mechanism'])})+' PREVIOUS ERRORS: '+json.dumps(rejected),max_tokens=3600,temperature=.35)
  (out/f'raw-plan-{attempt}.json').write_text(json.dumps(result,indent=2));draft.write_text(json.dumps(result,indent=2));rejected=errors(result)
  if result.get('topic')!=selected['topic'] or result.get('mechanism')!=selected['mechanism']:rejected.append('Preserve selected topic and mechanism')
  if rejected:continue
  critique=call('Audit original narration against the exact shown mechanism. Return JSON only.',
   'Return {"errors":[specific unsupported claims or action mismatches]}. Reject unrelated topics, invented components, energy gain and production narration. CONTRACT: '+json.dumps(SOURCES[selected['mechanism']])+' ACTIONS: '+json.dumps(mechanism_facts(selected['mechanism']))+' PLAN: '+json.dumps(result),max_tokens=1800,temperature=.1)
  (out/f'critique-{attempt}.json').write_text(json.dumps(critique,indent=2))
  rejected=critique.get('errors')
  if not isinstance(rejected,list):raise ValueError('Factual review unavailable')
  if not rejected:
   (out/'narration-critique.json').write_text(json.dumps(critique,indent=2));saved.write_text(json.dumps(result,indent=2));return result
 raise ValueError('Original full script failed bounded validation: '+str(rejected))

def run(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);started=time.monotonic();p=plan(out)
 # Same voice delivery and measured word timing as shorts; full format has its own duration range.
 print('CE_STAGE=voice',flush=True)
 tl=asyncio.run(voice(p,out,duration_range=(120,300)));require_media(tl['duration'],WIDTH,HEIGHT)
 soundtrack(tl,out)
 for i,b in enumerate(tl['beats']):frame((b['start']+b['end'])/2,tl,p).save(out/f'check-{i:02}.png')
 print('CE_STAGE=render',flush=True)
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
 subprocess.run(['ffmpeg','-v','error','-i',str(out/'video.mp4'),'-f','null','-'],check=True)
 print('CE_STAGE=audio',flush=True);review(p,tl,out)
 seal(out,'original_full',{'duration':float(measured['format']['duration']),'width':stream['width'],'height':stream['height']})
 result={'topic':p['topic'],'mechanism':p['mechanism'],'format':'original_full','duration':float(measured['format']['duration']),'width':stream['width'],'height':stream['height'],'manual_script_or_video_edits':False,'selected_by_system':True,'reused_short_assets':False,'owner_approved':False,'wall_seconds':time.monotonic()-started,'source':SOURCES[p['mechanism']]['source'],'quality_state':'technical_checks_passed_owner_visual_review_required'}
 (out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--out',required=True);run(a.parse_args().out)
