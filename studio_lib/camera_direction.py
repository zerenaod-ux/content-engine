"""Smooth detail framing tied to the already measured spoken action clock.

The component owns the physical focus position. No guessed objects or AI zoom
coordinates: use tested component shots, arrive before the measured action,
hold for explanation, and pull back to context for the payoff.
"""
import math,re
import numpy as np
from studio_lib.mesh import ease
VERSION='spoken-detail-camera-v2'

def pose(module,index,total):
 target,zoom,az=module.shot(index)
 # Context endpoints retain their tested whole-object framing.
 if 1 < index < total-1:zoom=min(3.3,zoom*1.25)
 return np.array(target,dtype=float),float(zoom),float(az)

def tracked_shot(t,beats,index,module):
 beat=beats[index];total=len(beats)
 a0,z0,r0=pose(module,max(0,index-1),total)
 a1,z1,r1=pose(module,index,total)
 if index==0:return z1,a1,r1
 start=float(beat['start']);end=float(beat['end'])
 # Finish before the first measured physical action, rather than continuing
 # to zoom while the mechanism has already performed it. Unaligned held
 # explanations use a bounded lead-in; their moving objects are unchanged.
 window=beat.get('motion_window')
 cue=float(window[0]) if window else start+.95
 arrival=min(end,start+1.2,max(start+.45,cue-.12))
 begin=max(start,arrival-.95)
 u=ease((t-begin)/max(.01,arrival-begin))
 zoom=math.exp(math.log(z0)*(1-u)+math.log(z1)*u);target=a0*(1-u)+a1*u;az=r0*(1-u)+r1*u
 return zoom,target,az

def clause_starts(beat):
 """Approximate start time of each spoken phrase from the text and measured voice length (no per-word AI guess)."""
 say=str(beat.get('say',''));parts=[p for p in re.split(r'(?<=[,;:.!?])\s+',say) if p.strip()]
 if not parts:return []
 begin=float(beat['start'])+.08;span=float(beat.get('voice_duration') or max(1.,float(beat['end'])-float(beat['start'])-.3))
 total=sum(len(p) for p in parts);acc=0;out=[]
 for p in parts:out.append(begin+span*acc/total);acc+=len(p)
 return out

def flourish(t,beat,index,total,zoom,target,az):
 """Cinematic life on top of the tested shot: slow push-in across the beat, a quick punch-in on every spoken phrase and a gentle sway.
 Context beats (first and last) stay on their tested whole-object framing."""
 if index==0 or index==total-1:return zoom,target,az
 start=float(beat['start']);end=float(beat['end']);u=max(0.,min(1.,(t-start)/max(.01,end-start)))
 punch=0.
 for c in clause_starts(beat)[1:]:
  x=(t-c)/.85
  if 0<=x<1:punch=max(punch,math.sin(math.pi*min(1,x*1.0))**1.5)
 env=math.sin(math.pi*u)**.5   # 0 at both beat edges: no jump between beats
 zoom=zoom*(1+.045*math.sin(math.pi*u)+.055*punch*env)
 az=az+.04*math.sin(t*.9)*env
 return zoom,target,az
