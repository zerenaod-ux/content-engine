"""Smooth detail framing tied to the already measured spoken action clock.

The component owns the physical focus position. No guessed objects or AI zoom
coordinates: use tested component shots, arrive before the measured action,
hold for explanation, and pull back to context for the payoff.
"""
import math
import numpy as np
from studio_lib.mesh import ease
VERSION='spoken-detail-camera-v1'

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
 return math.exp(math.log(z0)*(1-u)+math.log(z1)*u),a0*(1-u)+a1*u,r0*(1-u)+r1*u
