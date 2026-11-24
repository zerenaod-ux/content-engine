"""Long (8-10 minute) How It Ticks video made from the shorts the owner has already approved.

Only videos in the review index folder 'saved' are used, so nothing the owner has not accepted ever reaches a long video.
Each short becomes a numbered chapter on a 16:9 canvas (blurred fill behind the vertical picture) with a title card and a spoken lead-in
in the channel's own voice; an intro and an outro card frame the whole. The result is a normal review card for the owner to approve."""
import json,math,os,re,subprocess,urllib.request
from pathlib import Path
W,H,FPS=1920,1080,30
CARD=3.0;MIN_TOTAL,MAX_TOTAL=480.,600.
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
BACK='0x0f1b27'
CLIP_MIN,CLIP_MAX=20.,75.

def clean(text,limit=60):
 t=re.sub(r'[^\w\s\-\'?!.,]','',str(text)).strip();return (t[:limit]).rstrip()

def probe(path):
 return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(path)],text=True).strip())

def fetch_url(url,dest,limit=60_000_000):
 """Download one approved short (CI only). Refuses oversized or non-https sources."""
 if not str(url).startswith('https://'):raise ValueError('only https sources')
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'how-it-ticks-compilation'}),timeout=120) as r:
  data=r.read(limit+1)
 if len(data)>limit:raise ValueError('short is too large')
 Path(dest).write_bytes(data);return dest

def candidates(videos,index_items,rank=None):
 """Owner-approved shorts, best machines first, at most 2 per machine."""
 saved={i['tag'] for i in index_items if isinstance(i,dict) and i.get('folder')=='saved'}
 rows=[r for r in videos if isinstance(r,dict) and r.get('tag') in saved and r.get('video') and r.get('format') in (None,'short') and r.get('kind') in (None,'short') and not str(r.get('tag')).startswith('ce-long')]
 order={m:i for i,m in enumerate(rank or [])}
 def machine(r):return r.get('mechanism') or r.get('subject') or re.sub(r'\W+','_',str(r.get('title','')).lower())[:20]
 rows.sort(key=lambda r:(order.get(machine(r),len(order)),str(r.get('date')) ),reverse=False)
 seen={};out=[]
 for r in rows:
  m=machine(r)
  if seen.get(m,0)>=2:continue
  seen[m]=seen.get(m,0)+1;out.append(r)
 return out

def choose(rows,durations):
 """Walk the ranked list and keep videos until the total sits inside 8-10 minutes. durations: tag->seconds (None = unknown, skipped)."""
 pick=[];total=CARD*2   # intro + outro cards
 for r in rows:
  d=durations.get(r['tag'])
  if not d:continue
  add=d+CARD
  if total+add>MAX_TOTAL:continue
  pick.append(r);total+=add
  if total>=MIN_TOTAL:break
 if total<MIN_TOTAL:raise ValueError(f'Only {total:.0f}s of owner-approved shorts are available; a long video needs at least {MIN_TOTAL:.0f}s. Approve more shorts first.')
 return pick,total

def plan(pick,durations):
 t=CARD;chapters=[]
 for n,r in enumerate(pick,1):
  chapters.append({'n':n,'tag':r['tag'],'title':clean(re.sub(r'[^\x00-\x7f]+','',r.get('title','')).strip() or r.get('topic','')),'start':round(t,1),'duration':durations[r['tag']]})
  t+=CARD+durations[r['tag']]
 total=t+CARD
 title=f'How {len(chapters)} Everyday Machines Really Work'
 desc=title+'.\n\n'+'\n'.join(f'{int(c["start"]//60)}:{int(c["start"]%60):02d} {c["title"]}' for c in [{'start':0,'title':'Intro'}]+chapters)+'\n\nEvery chapter is a short we already published, explained with a simplified animated model.'
 return {'title':title,'description':desc,'chapters':chapters,'duration':round(total,1)}

def drawtext(lines,size_top=72):
 """ffmpeg drawtext chain for 1-3 centred lines; text is passed through a file-free, escaped form."""
 def esc(s):return str(s).replace('\\','\\\\').replace("'",'’').replace(':','\\:').replace('%','\\%').replace(',','\\,')
 parts=[]
 for k,(txt,size) in enumerate(lines):
  parts.append(f"drawtext=fontfile={FONT}:text='{esc(txt)}':fontcolor=white:fontsize={size}:x=(w-text_w)/2:y={H//2-90+k*110}")
 return ','.join(parts)

def run(cmd):
 subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)

ENC=['-c:v','libx264','-preset','veryfast','-crf','26','-pix_fmt','yuv420p','-r',str(FPS),'-c:a','aac','-b:a','128k','-ar','48000','-ac','2']

def card(path,lines,voice=None,seconds=CARD):
 """Title card; spoken line (if any) is padded to the card length."""
 vf=drawtext(lines)
 cmd=['ffmpeg','-v','error','-y','-f','lavfi','-i',f'color=c={BACK}:s={W}x{H}:d={seconds}:r={FPS}']
 if voice:cmd+=['-i',str(voice),'-af',f'apad,atrim=0:{seconds}','-map','0:v','-map','1:a']
 else:cmd+=['-f','lavfi','-i',f'anullsrc=r=48000:cl=stereo','-t',str(seconds),'-map','0:v','-map','1:a']
 run(cmd+['-vf',vf]+ENC+['-t',str(seconds),str(path)]);return path

def chapter_clip(path,src):
 fc=(f'[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=40:6,eq=brightness=-0.12[bg];'
     f'[0:v]scale=-2:{H}:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[v]')
 run(['ffmpeg','-v','error','-y','-i',str(src),'-filter_complex',fc,'-map','[v]','-map','0:a?','-af','aresample=48000,aformat=channel_layouts=stereo']+ENC+[str(path)]);return path

def speak_lines(lines,work,speaker=None):
 """Spoken lead-ins in the channel voice. Returns {index: wav path}; any failure returns {} so the cards are simply silent."""
 if speaker is not None:
  try:return speaker(lines,work)
  except Exception:return {}
 try:
  work=Path(work);spec={'title':'compilation','beats':[{'say':t,'seconds':2.5} for t in lines]};req=work/'comp-voice-request.json';rep=work/'comp-voice-report.json'
  req.write_text(json.dumps(spec))
  subprocess.run(['python3','-m','studio_lib.cpu_voice','--spec',str(req),'--report',str(rep)],check=True,timeout=600)
  data=json.loads(rep.read_text());return {i:l['voice'] for i,l in enumerate(data['lines']) if Path(l['voice']).is_file() and probe(l['voice'])<=CARD-.3}
 except Exception:return {}

def build(pick,durations,sources,work,out,speaker=None):
 """sources: tag->local file. Returns the plan dict; writes out (mp4) and chapters.txt next to it."""
 work=Path(work);work.mkdir(parents=True,exist_ok=True);p=plan(pick,durations)
 intro=f'How {len(pick)} everyday machines really work.'
 leads=[intro]+[f'Number {c["n"]}. {c["title"]}' for c in p['chapters']]+['That is how they tick. Thanks for watching.']
 voices=speak_lines(leads,work,speaker)
 parts=[card(work/'c000.mp4',[(p['title'],64),('How It Ticks',44)],voices.get(0))]
 for k,c in enumerate(p['chapters'],1):
  parts.append(card(work/f'c{k:03d}a.mp4',[(f'Chapter {c["n"]}',56),(c['title'][:44],56)],voices.get(k)))
  parts.append(chapter_clip(work/f'c{k:03d}b.mp4',sources[c['tag']]))
 parts.append(card(work/'c999.mp4',[('Thanks for watching',64),('More machines every week',44)],voices.get(len(leads)-1)))
 lst=work/'list.txt';lst.write_text(''.join(f"file '{x.resolve()}'\n" for x in parts))
 out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
 run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(lst),'-c','copy','-movflags','+faststart',str(out)])
 real=probe(out);p['duration']=round(real,1)
 (out.parent/'chapters.txt').write_text(p['description']+'\n');(out.parent/'compilation-plan.json').write_text(json.dumps(p,indent=1))
 return p

def make(videos,index_items,rank,work,out,fetch=fetch_url,speaker=None,probe_fn=probe):
 """Whole job: pick approved shorts, fetch them, check length, build."""
 work=Path(work);work.mkdir(parents=True,exist_ok=True)
 rows=candidates(videos,index_items,rank);sources={};durations={}
 total=CARD*2;pick=[]
 for r in rows:
  try:
   f=work/(r['tag']+'.mp4');fetch(r['video'],f);d=probe_fn(f)
  except Exception:continue
  if not CLIP_MIN<=d<=CLIP_MAX:continue
  durations[r['tag']]=d;sources[r['tag']]=f
  if total+d+CARD<=MAX_TOTAL:pick.append(r);total+=d+CARD
  if total>=MIN_TOTAL:break
 if total<MIN_TOTAL:raise ValueError(f'Only {total:.0f}s of owner-approved shorts could be fetched; a long video needs at least {MIN_TOTAL:.0f}s. Approve more shorts first.')
 return build(pick,durations,sources,work/'build',out,speaker)
