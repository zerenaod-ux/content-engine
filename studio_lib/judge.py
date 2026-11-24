"""Quality judge that learns from the owner.

Pixel measures (faces, shades) are only a proxy for 'looks as good as the first two'. This module keeps that proxy honest:
  seeds    machines/meta/picture-seeds.json: fixture measures of machines the owner liked or rejected
  samples  every later video whose card carries a picture_check record AND has an owner verdict (review index folder saved/delete)
  fit()    picks the richness rule that best separates liked from rejected (grid search, ties go to the stricter rule) -> data/scenes/picture-taste.json
  agreement() how often the pixel verdict and the optional vision score agree with the owner; vision may block only after it has earned trust
Fail-open everywhere: a missing or broken file returns the built-in limits."""
import json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
TASTE='data/scenes/picture-taste.json'
REPORT='data/scenes/judge-report.json'
MIN_TRUST_SAMPLES=10;TRUST_AGREEMENT=.8

def _read(path,default):
 try:return json.loads((ROOT/path).read_text())
 except (OSError,ValueError):return default

def seed_samples():
 return [s for s in _read('machines/meta/picture-seeds.json',{}).get('samples',[]) if s.get('label') in ('good','bad')]

def live_samples():
 """Videos with recorded picture measures and an owner verdict."""
 verdict={i.get('tag'):i.get('folder') for i in _read('data/scenes/review/index.json',{}).get('items',[]) if isinstance(i,dict)}
 out=[]
 for r in _read('data/scenes/videos.json',[]):
  pc=r.get('picture_check') if isinstance(r,dict) else None
  v=verdict.get(r.get('tag')) if isinstance(r,dict) else None
  if isinstance(pc,dict) and v in ('saved','delete') and 'faces' in pc and 'colours' in pc:
   out.append({'machine':r.get('mechanism') or r.get('subject'),'label':'good' if v=='saved' else 'bad','faces':pc['faces'],'colours':pc['colours'],'pixel_pass':pc.get('pass'),'vision':pc.get('vision_score'),'tag':r.get('tag')})
 return out

def passes(s,rule):
 f,c,alt=rule['faces_min'],rule['colours_min'],rule.get('faces_alt')
 return (s['faces']>=f and s['colours']>=c) or (alt is not None and s['faces']>=alt)

def fit(samples):
 """Richness rule with the best accuracy; among equally good rules take the middle of that plateau, so a real video that measures a little
 differently from the fixture does not fall off the edge. Needs at least 3 liked and 3 rejected samples."""
 good=[s for s in samples if s['label']=='good'];bad=[s for s in samples if s['label']=='bad']
 if len(good)<3 or len(bad)<3:return None
 top=-1;plateau=[]
 for f in range(200,701,25):
  for c in range(40,301,10):
   for alt in [None]+list(range(500,2001,100)):
    rule={'faces_min':f,'colours_min':c,'faces_alt':alt}
    acc=sum(passes(s,rule) for s in good)+sum(not passes(s,rule) for s in bad)
    if acc>top:top=acc;plateau=[rule]
    elif acc==top:plateau.append(rule)
 fs=sorted(r['faces_min'] for r in plateau);cs=sorted(r['colours_min'] for r in plateau);alts=sorted(r['faces_alt'] for r in plateau if r['faces_alt'] is not None)
 rule={'faces_min':fs[len(fs)//2],'colours_min':cs[len(cs)//2],'faces_alt':alts[len(alts)//2] if len(alts)>len(plateau)/2 else None}
 if sum(passes(s,rule) for s in good)+sum(not passes(s,rule) for s in bad)!=top:rule=dict(plateau[len(plateau)//2])
 tp=sum(passes(s,rule) for s in good);tn=sum(not passes(s,rule) for s in bad)
 rule.update(samples=len(good)+len(bad),good_kept=f'{tp}/{len(good)}',bad_blocked=f'{tn}/{len(bad)}',accuracy=round((tp+tn)/(len(good)+len(bad)),3),equally_good_rules=len(plateau))
 return rule

def load_taste():
 """Limits the picture check should use; {} (built-in defaults) when nothing was fitted."""
 t=_read(TASTE,{})
 if not isinstance(t,dict) or not t.get('faces_min'):return {}
 lim={'faces_min':int(max(150,min(700,t['faces_min']))),'colours_min':int(max(30,min(300,t['colours_min'])))}
 if t.get('faces_alt'):lim['faces_alt']=int(t['faces_alt'])
 return lim

def agreement(samples):
 """Share of owner-judged videos where each judge agreed with the owner."""
 mine=[s for s in samples if s.get('pixel_pass') is not None]
 pix=statistics.mean([(s['pixel_pass'] is True)==(s['label']=='good') for s in mine]) if mine else None
 seen=[s for s in samples if isinstance(s.get('vision'),(int,float))]
 vis=statistics.mean([(s['vision']>=5)==(s['label']=='good') for s in seen]) if seen else None
 return {'pixel':None if pix is None else round(pix,3),'pixel_n':len(mine),'vision':None if vis is None else round(vis,3),'vision_n':len(seen)}

def vision_trusted(samples=None):
 """Vision may block a video only after it agreed with the owner on enough real videos."""
 a=agreement(live_samples() if samples is None else samples)
 return a['vision_n']>=MIN_TRUST_SAMPLES and a['vision'] is not None and a['vision']>=TRUST_AGREEMENT

def write(root=None):
 base=Path(root) if root else ROOT
 live=live_samples();allx=seed_samples()+live;rule=fit(allx);report={'policy':'judge-v1','seeds':len(seed_samples()),'live_samples':len(live),'agreement':agreement(live),'vision_blocks':vision_trusted(live),'rule':rule}
 (base/'data/scenes').mkdir(parents=True,exist_ok=True)
 if rule:(base/TASTE).write_text(json.dumps({k:v for k,v in rule.items()},indent=1)+'\n')
 (base/REPORT).write_text(json.dumps(report,indent=1)+'\n');return report

if __name__=='__main__':print(json.dumps(write(),indent=1))
