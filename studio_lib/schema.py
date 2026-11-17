"""Strict bounded data-only scene format. No generated code is executed."""
import math
def number(x):return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)
def vector(v,n=3):return isinstance(v,list) and len(v)==n and all(number(x) for x in v)
FIELDS={'x','y','z','angle','scale','visible'}
def check(s):
    e=[]
    if not isinstance(s,dict):return ['scene must be an object']
    if not isinstance(s.get('title'),str) or not 4<=len(s['title'].split())<=12:e.append('title needs 4-12 words')
    if s.get('setting') not in ('ocean','studio','workshop','space'):e.append('setting must be ocean, studio, workshop or space')
    beats=s.get('beats',[]);objects=s.get('objects',[])
    if not isinstance(beats,list) or not 5<=len(beats)<=9:return e+['need 5-9 story beats']
    if not isinstance(objects,list) or not 3<=len(objects)<=80:return e+['need 3-80 persistent objects']
    ids=[o.get('id') for o in objects if isinstance(o,dict)]
    if len(ids)!=len(objects) or any(not isinstance(x,str) or not x for x in ids) or len(set(ids))!=len(ids):return e+['object ids must be unique strings']
    by={o['id']:o for o in objects};total=0
    for o in objects:
        oid=o['id'];parent=o.get('parent')
        if parent and parent not in ids:e.append(oid+': unknown parent')
        seen={oid};p=parent
        while p in by:
            if p in seen:e.append(oid+': cyclic parent hierarchy');break
            seen.add(p);p=by[p].get('parent')
        if not vector(o.get('position')) or max(abs(x) for x in o['position'])>20:e.append(oid+': position must be 3 finite world coordinates within +/-20')
        if o.get('axis','y') not in ('x','y','z'):e.append(oid+': rotation axis x/y/z only')
        meshes=o.get('meshes',[])
        if not isinstance(meshes,list) or not 1<=len(meshes)<=220:e.append(oid+': need 1-220 mesh components');continue
        total+=len(meshes)
        for m in meshes:
            if not isinstance(m,dict):e.append(oid+': mesh must be object');continue
            kind=m.get('type')
            if kind not in ('box','beam','cylinder','gear','face'):e.append(oid+': unknown mesh type');continue
            color=m.get('color')
            if not vector(color) or any(not 0<=c<=255 for c in color):e.append(oid+': RGB color 0-255 required')
            if kind=='box' and (not vector(m.get('at')) or not vector(m.get('size')) or min(m['size'])<=0):e.append(oid+': box needs at and positive size')
            if kind=='beam' and (not vector(m.get('a')) or not vector(m.get('b')) or m.get('a')==m.get('b') or not number(m.get('radius')) or not 0<m['radius']<=2):e.append(oid+': beam needs distinct a/b and radius')
            if kind in ('cylinder','gear') and (not vector(m.get('at')) or not number(m.get('radius')) or not 0<m['radius']<=8):e.append(oid+': wheel needs at and radius')
            if kind=='cylinder' and (not number(m.get('length')) or not 0<m['length']<=10):e.append(oid+': cylinder needs positive length')
            if kind=='gear' and (not isinstance(m.get('teeth'),int) or not 8<=m['teeth']<=48):e.append(oid+': gear teeth must be integer 8-48')
            if kind=='face' and (not isinstance(m.get('points'),list) or not 3<=len(m['points'])<=40 or not all(vector(p) for p in m['points'])):e.append(oid+': face needs 3-40 points')
        anim=o.get('motion',{})
        if not isinstance(anim,dict):e.append(oid+': motion must be object');continue
        for k,keys in anim.items():
            if k not in FIELDS:e.append(oid+': unsupported motion '+k);continue
            if not isinstance(keys,list) or not 2<=len(keys)<=30 or not all(vector(p,2) for p in keys):e.append(oid+': motion needs 2-30 [beat_position,value] keys');continue
            if any(not 0<=p[0]<=len(beats) for p in keys) or any(b[0]<=a[0] for a,b in zip(keys,keys[1:])):e.append(oid+': keys must increase within beat range')
            if k=='scale' and any(not .1<=p[1]<=4 for p in keys):e.append(oid+': scale outside .1..4')
            if k in ('x','y','z') and any(abs(p[1])>20 for p in keys):e.append(oid+': animated offset outside world')
    if total>220:e.append('maximum 220 mesh components')
    words=0
    for i,b in enumerate(beats):
        if not isinstance(b,dict):e.append('beat must be object');continue
        if not isinstance(b.get('say'),str) or not 6<=len(b['say'].split())<=25:e.append(f'beat {i}: say needs 6-25 words')
        else:words+=len(b['say'].split())
        if not isinstance(b.get('focus'),list) or not b['focus'] or any(x not in ids for x in b['focus']):e.append(f'beat {i}: focus must name existing objects')
        if not isinstance(b.get('demonstration'),str) or len(b['demonstration'])<12:e.append(f'beat {i}: explain visible demonstration')
        evidence=b.get('evidence',[])
        if not evidence or not isinstance(evidence,list) or any(x not in ids for x in evidence):e.append(f'beat {i}: evidence must name existing visible objects')
        if not number(b.get('seconds')) or not 3<=b['seconds']<=10:e.append(f'beat {i}: seconds must be 3-10')
    if not 95<=words<=165:e.append('narration must total 95-165 words')
    if all(isinstance(b,dict) and number(b.get('seconds')) for b in beats) and not 45<=sum(b['seconds'] for b in beats)<=65:e.append('total proposed seconds must be 45-65')
    if not any(o.get('motion') for o in objects):e.append('scene needs meaningful object motion')
    if not isinstance(s.get('principle'),str) or len(s['principle'].split())<8:e.append('state the causal principle')
    return e
