"""Picture check: measure sampled frames before a video can reach the owner, and say how to redo a weak one.

Pixel measures only (no model, no network), so it can be trusted to run every time:
  fill      share of the stage area the machine covers (a tiny object in an empty frame fails)
  tones     how many different brightness steps the machine shows (flat boxes show few)
  richness  how many facets and distinct shades the machine is built from (generic kit builds are far below the hand-built ones)
  detail    share of machine pixels that sit on an edge (bevels, teeth, coils give many)
  motion    how much the machine pixels change from one sampled frame to the next inside a moving beat
An optional vision critique (a free vision model reading a contact sheet) is advisory: it is recorded and shown to the owner,
and can only make the gate stricter if it answers; if no vision service answers, the pixel gate alone decides."""
import json,math
import numpy as np
from PIL import Image

POLICY='picture-check-v1'
BAND=(300/1280,1100/1280)        # stage band of the 9:16 frame; title above, captions and progress bar below
SMALL=(270,480)
LIMITS={'fill_min':.08,'tones_min':7,'detail_min':.020,'motion_min':.004,'median_fill_min':.14,'faces_min':300,'colours_min':150}

def _small(img):return np.asarray(img.convert('RGB').resize(SMALL,Image.Resampling.BILINEAR),float)

def band_slice():
 h=SMALL[1];return slice(int(h*BAND[0]),int(h*BAND[1]))

def polygon_mask(faces):
 """Machine silhouette from the renderer's own projected faces (720x1280 units), cropped to the stage band."""
 from PIL import ImageDraw
 m=Image.new('L',SMALL,0);d=ImageDraw.Draw(m);k=SMALL[0]/720
 for _,poly,_ in faces:d.polygon([(x*k,y*k) for x,y in poly],fill=255)
 return (np.asarray(m)>0)[band_slice()]

def frame_metrics(img,faces):
 mask=polygon_mask(faces);a=_small(img)[band_slice()];count=int(mask.sum())
 out={'fill':round(count/mask.size,4),'tones':0,'detail':0.,'luma_mean':0.,'faces':len(faces),'colours':len({tuple(int(v) for v in c) for _,_,c in faces})}
 if count<30:return out
 luma=a@np.array([.299,.587,.114]);vals=luma[mask];out['luma_mean']=round(float(vals.mean()),1)
 hist,_=np.histogram(vals,bins=24,range=(0,255));out['tones']=int((hist>=.01*count).sum())
 gy,gx=np.gradient(luma);edge=(np.hypot(gx,gy)>14)&mask
 out['detail']=round(float(edge.sum()/count),4)
 return out

def motion_between(a,b,pa,pb):
 """Share of machine pixels (either look) whose colour changed between two looks."""
 ma=polygon_mask(pa)|polygon_mask(pb);xa=_small(a)[band_slice()];xb=_small(b)[band_slice()]
 changed=(np.abs(xa-xb).sum(axis=2)>30)&ma
 return float(changed.sum()/max(1,ma.sum()))

def sample_times(tl,per_beat=2):
 """Two looks inside every beat. A beat with a measured motion window is looked at early and late in that window, so a real movement is seen."""
 out=[]
 for i,b in enumerate(tl['beats']):
  w=b.get('motion_window')
  lo,hi=(float(w[0]),float(w[1])) if w and float(w[1])-float(w[0])>.3 else (b['start'],b['end'])
  fr=(.15,.85) if (lo,hi)!=(b['start'],b['end']) else (.35,.80)
  for k in range(per_beat):out.append((i,lo+(hi-lo)*fr[k]))
 return out

def evaluate(picture,tl,moving_beats=(),limits=None,sheet_path=None):
 """picture(t)->(PIL image, the scene's faces as (depth, polygon, colour) rows). Returns a report dict; report['errors'] is empty when the picture passes."""
 lim=dict(LIMITS);lim.update(limits or {})
 rows=[];frames=[];polys=[]  # polys holds each frame's renderer faces
 for i,t in sample_times(tl):
  im,pg=picture(t);m=frame_metrics(im,pg);m.update(beat=i,t=round(float(t),2));rows.append(m);frames.append(im);polys.append(pg)
 errors=[];info=[]
 body=[r for r in rows if 1<=r['beat']<=6]
 for r in body:
  tag=f"beat {r['beat']} at {r['t']}s"
  if r['fill']<lim['fill_min']:errors.append(f'{tag}: machine fills only {r["fill"]:.0%} of the stage; zoom in')
  if r['tones']<lim['tones_min']:errors.append(f'{tag}: flat shading ({r["tones"]} tones); parts look like plain boxes')
  if r['detail']<lim['detail_min']:errors.append(f'{tag}: too little visible detail ({r["detail"]:.1%} edges)')
 if body:
  faces=int(np.median([r['faces'] for r in body]));colours=int(np.median([r['colours'] for r in body]))
  if faces<lim['faces_min'] or colours<lim['colours_min']:errors.append(f'machine is built from too few facets/shades ({faces} faces, {colours} shades; needs {lim["faces_min"]}/{lim["colours_min"]}); use the rich parts library')
 fills=sorted(r['fill'] for r in body)
 if fills and fills[len(fills)//2]<lim['median_fill_min']:errors.append(f'machine is small in most shots (median fill {fills[len(fills)//2]:.0%}); frame it bigger')
 order=sample_times(tl)
 for i in moving_beats:
  idx=[k for k,(j,_) in enumerate(order) if j==i]
  if len(idx)==2:
   mv=motion_between(frames[idx[0]],frames[idx[1]],polys[idx[0]],polys[idx[1]])
   info.append({'beat':i,'motion':round(mv,5)})
   if mv<lim['motion_min']:errors.append(f'beat {i}: almost nothing moves between two looks ({mv:.2%} of the machine); the narrated action is not visible')
 report={'policy':POLICY,'limits':lim,'frames':rows,'motion':info,'errors':errors,'score':score(rows,errors)}
 if sheet_path:contact_sheet(frames,sheet_path)
 return report

def score(rows,errors):
 """0-10 for the owner's card: starts from how rich and well framed the frames are, minus a point per problem."""
 body=[r for r in rows if 1<=r['beat']<=6]
 if not body:return 0.
 fill=np.median([min(1.,r['fill']/.30) for r in body]);tones=np.median([min(1.,r['tones']/12) for r in body]);detail=np.median([min(1.,r['detail']/.06) for r in body])
 return round(max(0.,10*(.35*fill+.30*tones+.35*detail)-len(errors)*.5),1)

def contact_sheet(frames,path,columns=4):
 w,h=270,480;rows=math.ceil(len(frames)/columns);sheet=Image.new('RGB',(w*columns,h*rows))
 for k,im in enumerate(frames):sheet.paste(im.convert('RGB').resize((w,h)),((k%columns)*w,(k//columns)*h))
 sheet.save(path,quality=82);return path

def adjustments(report,current_zoom=1.0):
 """What a redo should change. Only framing (zoom) is automatic; anything else is flagged for the builder."""
 text=' '.join(report['errors']);zoom=current_zoom;notes=[]
 if 'zoom in' in text or 'frame it bigger' in text:zoom*=1.18;notes.append('zoom in 18%')
 if 'zoom out' in text:zoom/=1.15;notes.append('zoom out 13%')
 manual=[e for e in report['errors'] if 'flat shading' in e or 'too few facets' in e or 'too little visible detail' in e or 'almost nothing moves' in e]
 return {'zoom':round(max(.6,min(1.8,zoom)),3),'notes':notes,'needs_builder':bool(manual)}

def vision_prompt():
 return ('You are checking a vertical explainer video of a physical machine. The image is a contact sheet of frames. '
  'Reply JSON only: {"score":0-10,"problems":["..."]}. Penalise: parts that look like plain flat boxes, tiny objects in an empty frame, '
  'parts hidden behind other parts, text or labels that overlap the machine, moving parts that are not visibly different between frames.')

def vision_critique(sheet_path,ask):
 """ask(prompt,image_bytes)->dict. Advisory: any failure returns None and the pixel gate decides alone."""
 try:
  data=open(sheet_path,'rb').read();answer=ask(vision_prompt(),data)
  if isinstance(answer,dict) and isinstance(answer.get('score'),(int,float)) and isinstance(answer.get('problems'),list):
   return {'score':float(max(0,min(10,answer['score']))),'problems':[str(p)[:200] for p in answer['problems'][:6]]}
 except Exception:return None
 return None

def decide(report,vision=None,vision_floor=5.0):
 """Final verdict. Pixel errors always block. A vision score below the floor blocks only when a vision answer actually arrived."""
 errors=list(report['errors'])
 if vision and vision['score']<vision_floor:errors.append(f"vision check scored {vision['score']:.1f}/10: "+'; '.join(vision['problems'][:3]))
 return {'pass':not errors,'errors':errors,'score':report['score'],'vision':vision}

def write_report(report,verdict,path):
 slim={k:v for k,v in report.items() if k!='frames'};slim['frame_count']=len(report['frames'])
 open(path,'w').write(json.dumps({'report':slim,'verdict':verdict,'scope':'Pixel measures of sampled frames; not an approval of editorial quality'},indent=1))


def moving_beats_for(contract):
 """Beats where the contract expects a part (not just the cutaway cover) to move."""
 return sorted(i for i,m in contract['moves'].items() if any(ch!='cut' for ch in m))

def gemini_ask(prompt,image_bytes,model='gemini-flash-latest',timeout=40):
 """Optional free vision call (opt-in with CE_VISION_CHECK=true and GEMINI_API_KEY). Not exercised in tests against the live service."""
 import base64,os,urllib.request
 key=os.environ.get('GEMINI_API_KEY')
 if not key:return None
 body={'model':model,'response_format':{'type':'json_object'},'messages':[{'role':'user','content':[{'type':'text','text':prompt},{'type':'image_url','image_url':{'url':'data:image/jpeg;base64,'+base64.b64encode(image_bytes).decode()}}]}]}
 req=urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/openai/chat/completions',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=timeout) as r:text=json.loads(r.read())['choices'][0]['message']['content']
 return json.loads(text)

def run(picture,tl,plan,contract,out,ask=None,max_redo=2):
 """Gate used by the director before the long render. Redo = reframe (zoom) up to max_redo times; anything else stops the run with a plain reason.
 Returns the verdict dict; raises ValueError when the picture is not good enough to render."""
 import os
 from pathlib import Path
 out=Path(out);moving=moving_beats_for(contract);attempts=[]
 def view(zoom):return lambda t:picture(t,zoom)
 zoom=float(plan.get('picture_zoom',1.0));report=None
 for attempt in range(max_redo+1):
  report=evaluate(view(zoom),tl,moving,sheet_path=out/'picture-contact.jpg')
  attempts.append({'zoom':zoom,'errors':report['errors'],'score':report['score']})
  if not report['errors']:break
  adj=adjustments(report,zoom)
  if adj['needs_builder'] or adj['zoom']==zoom:break
  zoom=adj['zoom']
 plan['picture_zoom']=zoom
 vision=None
 if ask is None and os.environ.get('CE_VISION_CHECK')=='true':ask=gemini_ask
 if ask is not None:vision=vision_critique(out/'picture-contact.jpg',ask)
 verdict=decide(report,vision);verdict['attempts']=attempts;verdict['zoom']=zoom
 write_report(report,verdict,out/'picture-check.json')
 if not verdict['pass']:raise ValueError('Picture check failed; nothing was rendered: '+'; '.join(verdict['errors'][:4]))
 return verdict
