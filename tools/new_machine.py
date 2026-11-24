"""Start a new hand-built machine: writes studio_lib/<key>.py (a working rich-parts example) and machines/_drafts/<key>.json.
Edit the module so it draws your machine, replace every TODO in the spec, then move the spec to machines/<key>.json.
Nothing is registered until the spec is in machines/ and has no TODO left."""
import argparse,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
MODULE='''"""{title}: scaffold from tools/new_machine.py. Replace the drawing with this machine's real parts; keep state() honest, because the motion checks read it.
Beats 0-7 follow registry actions. Channels returned by state() are what machines/{key}.json measures (cut = cover lifting, turn = the driven part)."""
import functools
from studio_lib.mesh import ease
from studio_lib.narration_timing import progress
from studio_lib.solid_parts import background as gradient
from studio_lib import parts_rich as P
FLOOR=.30;GROUND=(34,47,59);DARK=True

def state(t,tl):
 b=tl['beats'];i=min(7,next((j for j,x in enumerate(b) if t<x['end']),7))
 cut=ease(progress(t,b[1]))*(1-ease(progress(t,b[7])))
 turn=3.1416*(ease(progress(t,b[2]))+ease(progress(t,b[4])))
 return dict(beat=i,cut=cut,turn=turn)
@functools.lru_cache(maxsize=1)
def background():return gradient((15,27,39),(41,60,74))

def draw(s,t,tl,hidden=()):
 p=state(t,tl)
 P.plate(s,(0,.9,2.5),(6.0,.3,5.0),(46,60,74))
 if 'gear' not in hidden:
  P.gear(s,(-1.0,0,2.7),1.25,16,p['turn'],.4,(186,198,206))
  P.gear(s,(1.05,0,1.75),.7,9,-p['turn']*16/9*0+(-p['turn']*16/9),.4,(222,176,84),tip=.14)
 if 'spring' not in hidden:P.spring(s,(.5,-.1,3.9),(2.5,-.1,3.9),7,.22,.04,(190,200,190))
 if 'door' not in hidden and p['cut']<.99:
  P.plate(s,(-.2,-.45+0,2.6+6.0*p['cut']),(5.0,.12,4.2),(94,110,122),tiles=(5,5))
 return p
SHOTS=[((0,0,2.6),1.3,.30),((0,0,2.6),1.5,.32),((-.6,0,2.6),2.4,.30),((-.2,0,2.4),2.0,.30),((.2,0,2.6),2.4,.30),((0,0,2.6),2.0,.30),((0,0,2.6),2.0,.30),((0,0,2.6),1.3,.30)]
def shot(i):return SHOTS[min(i,7)]
def elevation(t,tl):return 6.
'''
SPEC={
 "key":"{key}","module":"studio_lib.{key}","family":"{family}",
 "pattern":"\\b(TODO words people use for this object)\\b","detect":"TODO","block":"TODO details this machine does not show",
 "description":"TODO one line: what is shown and what is NOT shown","actions":["intro","cutaway","drive","hold1","repeat","hold2","limit","payoff"],
 "facts":{a:"TODO what this beat shows, in one or two plain sentences ending with what is not shown" for a in ["intro","cutaway","drive","hold1","repeat","hold2","limit","payoff"]},
 "source":"https://en.wikipedia.org/wiki/TODO",
 "contract":{"subjects":["TODO"]*8,"moves":{"1":{"cut":1},"2":{"turn":1},"4":{"turn":1},"7":{"cut":-1}},
  "holds":{"0":["cut","turn"],"1":["turn"],"2":["cut"],"3":["cut","turn"],"4":["cut"],"5":["cut","turn"],"6":["cut","turn"],"7":["turn"]},
  "visible":[[2,"gear"],[4,"spring"]]},
 "transitions":["cutaway","payoff"],"anchors":{"cutaway":"cutaway","payoff":"TODO"},
 "narration_rules":[],"cue_bans":[],"bounds":[],
 "label":{"from":1,"to":6,"text":"Cutaway · simplified model"}}
def main(argv=None):
 a=argparse.ArgumentParser();a.add_argument('key');a.add_argument('title');a.add_argument('--family');n=a.parse_args(argv)
 if not re.fullmatch(r'[a-z][a-z0-9_]{2,40}',n.key):sys.exit('key: lowercase letters, digits, underscore')
 mod=ROOT/'studio_lib'/(n.key+'.py');spec=ROOT/'machines'/'_drafts'/(n.key+'.json')
 if mod.exists() or spec.exists():sys.exit('already exists; pick another key')
 spec.parent.mkdir(parents=True,exist_ok=True)
 mod.write_text(MODULE.format(title=n.title,key=n.key))
 text=json.dumps(SPEC,indent=1).replace('{key}',n.key).replace('{family}',n.family or n.key)
 spec.write_text(text+'\n');print('wrote',mod,'and',spec)
if __name__=='__main__':main()
