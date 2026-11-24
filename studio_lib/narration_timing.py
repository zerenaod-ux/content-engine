"""Bind discrete component actions to words measured from their saved speech.

Continuous motion stays continuous. This does not claim semantic pixel review.
"""
import hashlib
import importlib.util
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

VERSION = 'spoken-action-v1'
ALIGNMENT_REVISION = 'causal-component-actions-v4'
TRANSITIONS = {
    'pendulum_clock':{'cutaway','payoff'},
    'ratchet_wrench':{'cutaway','payoff'},
    'zipper':{'cutaway','guide','mesh','closed','reverse','payoff'},
    'stapler':{'cutaway','feed','press','clinch','return','payoff'},
    'optical_fiber':{'cutaway','enter','reflect','guide','payoff'},
    'electric_relay':{'cutaway','energize','attract','release','payoff'},
    'snap_thermostat':{'cutaway','heat','snap','cool','reset','payoff'},
    'clothespin':{'squeeze','insert','release'},
    'float_valve':{'cutaway','fill','throttle','draw','refill','payoff'},
    'combination_lock':{'cutaway','first','second','third','pull','payoff'},
    'camera_iris': {'cutaway','close','open','payoff'},
    'bascule_bridge': {'stop', 'balance', 'pass', 'lower', 'resume'},
    'photovoltaic_cell': {'absorb', 'circuit', 'payoff'},
    'piston_pump': {'cutaway', 'suction', 'compression', 'payoff'},
    'wind_turbine': {'shaft', 'load', 'payoff'},
}
ANCHORS = {
    'pendulum_clock':{'cutaway':r'cutaway','payoff':r'clock|pendulum|weight|hand'},
    'ratchet_wrench':{'cutaway':r'cutaway','payoff':r'wrench|ratchet|bolt|handle'},
    'zipper':{'cutaway':r'cutaway','guide':r'slider|guide','mesh':r'slider|teeth|heads','closed':r'slider|stop','reverse':r'slider|divider','payoff':r'zipper|slider|tapes'},
    'stapler':{'cutaway':r'cutaway','feed':r'magazine|spring|staple','press':r'handle|driver|input','clinch':r'driver|legs|anvil','return':r'handle|driver|return','payoff':r'stapler|handle|staple'},
    'optical_fiber':{'cutaway':r'cutaway','enter':r'light|pulse|core','reflect':r'light|pulse|boundary','guide':r'pulse|light|core','payoff':r'cable|fibre|fiber|receiver'},
    'electric_relay':{'cutaway':r'cutaway','energize':r'switch|current|coil','attract':r'armature|attraction|electromagnet','release':r'switch|current|spring','payoff':r'relay|coil|circuit|electromagnet'},
    'snap_thermostat':{'cutaway':r'cutaway','heat':r'heat|disc|warming|temperature','snap':r'disc|bimetal|snap','cool':r'heat|cool|temperature','reset':r'disc|snap|reset','payoff':r'thermostat|temperature|switch|circuit'},
    'clothespin':{'squeeze':r'handles|squeeze|input','insert':r'fabric|cloth|fold','release':r'input|release|spring|squeeze'},
    'float_valve':{'cutaway':r'cutaway','fill':r'water|float|ball|level','throttle':r'float|ball|washer|valve|stem|seat','draw':r'outlet|drain|draw.off|tap','refill':r'draw.off\s+valve\s+(?:shut\w*|clos\w*)|outlet\s+(?:shut\w*|clos\w*)|outlet|drain|water|refill|float','payoff':r'tank|float|level|inlet|water'},
    'combination_lock':{'cutaway':r'cutaway','first':r'first wheel|first dial','second':r'second wheel|second dial','third':r'third wheel|last wheel|third dial|last dial','pull':r'shackle|loop|pull','payoff':r'padlock|lock|shackle|gates|wheels|bar'},
    'camera_iris': {'cutaway':r'cutaway', 'close':r'(?:ring|blades|iris|opening|aperture)[^.!?;,]{0,30}?\b(?:turn\w*|pivot\w*|rotat\w*|clos\w*|narrow\w*|shrink\w*)', 'open':r'(?:ring|blades|iris|opening|aperture)[^.!?;,]{0,30}?\b(?:revers\w*|open\w*|widen\w*|pivot\w*|rotat\w*)', 'payoff':r'camera|aperture|opening|iris|cover|shell'},
    'bascule_bridge': {
        'stop': r'(?:barriers?|gates?)[^.!?;,]{0,28}?\b(?:clos\w*|lower\w*|shut\w*)',
        'balance': r'(?:road|span|bridge)[^.!?;,]{0,24}?\b(?:ris\w*|lift\w*|rais\w*)|counterweight[^.!?;,]{0,24}?\b(?:swing\w*|descend\w*|drop\w*)',
        'pass': r'(?:ship|vessel)[^.!?;,]{0,24}?\b(?:pass\w*|glid\w*|sail\w*|travel\w*)',
        'lower': r'(?:road|span|bridge)[^.!?;,]{0,24}?\b(?:lower\w*|descend\w*|drop\w*)|counterweight[^.!?;,]{0,24}?\b(?:ris\w*|swing\w*)',
        'resume': r'(?:car|traffic)[^.!?;,]{0,24}?\b(?:cross\w*|resum\w*|mov\w*)',
    },
    'photovoltaic_cell': {'absorb':r'cutaway|layers?|semiconductor|cell', 'circuit':r'(?:switch|circuit)[^.!?;,]{0,24}?\b(?:clos\w*|complet\w*)|clos\w*[^.!?;,]{0,24}?(?:switch|circuit)', 'payoff':r'panel|solar|light|energy'},
    'piston_pump': {'cutaway':r'cutaway|cylinder|piston|rod', 'suction':r'(?:piston|rod)[^.!?;,]{0,24}?\b(?:withdraw\w*|pull\w*|retract\w*|back\w*)', 'compression':r'(?:piston|rod)[^.!?;,]{0,24}?\b(?:advanc\w*|push\w*|compress\w*|forward\w*)', 'payoff':r'pump|water|input|valves?'},
    'wind_turbine': {'shaft':r'shaft|nacelle|bearing', 'load':r'(?:switch|circuit)[^.!?;,]{0,24}?\b(?:clos\w*|complet\w*)|clos\w*[^.!?;,]{0,24}?(?:switch|circuit)', 'payoff':r'turbine|wind|rotor'},
}


# A completion phrase bounds the physical action instead of stretching it across
# later explanation. Patterns reference only words already spoken by the model.
COMPLETIONS={
 'zipper':{'closed':r'slider (?:reach\w*|stop\w*)|chain (?:join\w*|clos\w*)'},
 'stapler':{'clinch':r'legs? (?:curl\w*|bend\w*|fold\w*)','press':r'legs? (?:pierc\w*|touch\w*)'},
 'optical_fiber':{'guide':r'(?:receiver|indicator) (?:activat\w*|light\w*)|(?:reach\w*|arriv\w*) (?:the )?(?:far end|receiver)'},
 'combination_lock':{'third':r'(?:bar|fence) (?:drop\w*|fall\w*|descend\w*|settle\w*)','pull':r'(?:shackle|leg) (?:lift\w*|ris\w*|open\w*)'},
 'electric_relay':{'attract':r'contacts? (?:touch\w*|clos\w*|meet\w*)|armature (?:lower\w*|pivot\w*)','release':r'contacts? (?:open\w*|separat\w*)|spring (?:return\w*|pull\w*)'},
 'snap_thermostat':{'snap':r'disc (?:snap\w*|flip\w*)|contacts? (?:open\w*|separat\w*)','reset':r'disc (?:snap\w*|return\w*)|contacts? (?:clos\w*|meet\w*)'},
 'clothespin':{'squeeze':r'jaws? (?:open\w*|separat\w*)','release':r'jaws? (?:clos\w*|grip\w*)'},
}

def completion_match(mechanism,action,words,spans,first_word):
 pattern=COMPLETIONS.get(mechanism,{}).get(action)
 if not pattern:return None
 text=' '.join(words);offsets=[];position=0
 for word in words:offsets.append((position,position+len(word)));position+=len(word)+1
 matches=[]
 for match in re.finditer(pattern,text):
  selected=[i for i,(a,b) in enumerate(offsets) if b>match.start() and a<match.end()]
  if selected and selected[0]>=first_word:matches.append(selected)
 if not matches:return None
 # Last physical-result phrase in a short clause, e.g. armature pivots then contacts close.
 selected=matches[-1]
 return {'phrase':' '.join(words[i] for i in selected),'start':spans[selected[0]][0],'end':spans[selected[-1]][1]}

def tokens(text):
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower().replace('’', "'"))

def locations(haystack, needle):
    return [i for i in range(len(haystack)-len(needle)+1)
            if haystack[i:i+len(needle)] == needle] if needle else []

def measured_matches(words,cue):
    exact=locations(words,cue)
    if exact:return [(i,i+len(cue)-1) for i in exact]
    # Speech recognizers can split a compound ('counter weight') differently.
    # Match identical letters only, with boundaries on complete heard words.
    joined=''.join(words);needle=''.join(cue);starts={};ends={};position=0
    for i,word in enumerate(words):
        starts[position]=i;position+=len(word);ends[position]=i
    matches=[];offset=0
    while needle:
        hit=joined.find(needle,offset)
        if hit<0:break
        if hit in starts and hit+len(needle) in ends:matches.append((starts[hit],ends[hit+len(needle)]))
        offset=hit+1
    return matches

def writing_rules():
    return ('For each transition action listed below, add motion_cue to that beat: '
            'an EXACT contiguous 2-10-word phrase copied from its own say, naming '
            'the action or the internal part being revealed. Choose a phrase that '
            'occurs once. The engine times that action to measured speech, not a '
            'guessed word rate. Preserve action order and every safety rule. '
            'Other beats keep their continuous motion or static identification. '
            'Transition actions by mechanism: '+json.dumps({k:sorted(v) for k,v in TRANSITIONS.items()}))

def cue_errors(plan):
    errors=[]
    for i,b in enumerate(plan.get('beats', [])):
        if b.get('action') not in TRANSITIONS.get(plan.get('mechanism'), set()):
            continue
        cue=b.get('motion_cue')
        if not isinstance(cue,str) or not 2<=len(tokens(cue))<=10:
            errors.append(f'beat {i}: motion_cue needs 2-10 exact spoken words')
        elif len(locations(tokens(b.get('say','')),tokens(cue))) != 1:
            errors.append(f'beat {i}: motion_cue must occur exactly once in its narration')
        elif plan.get('mechanism')=='ratchet_wrench' and re.search(r'\bpawl\b',cue,re.I):
            errors.append(f'beat {i}: motion_cue must not use the word pawl; speech recognition mishears it, use wrench, ratchet, bolt or handle')
        elif not re.search(ANCHORS[plan['mechanism']][b['action']],cue,re.I):
            errors.append(f'beat {i}: motion_cue must name this action or the internal part being revealed')
    return errors

def normalize_cues(plan):
    """Repair cue pointers only by selecting existing words, never narration.

    A model sometimes adds 'and' to a cue where the spoken text has a comma.
    Only function-word differences are allowed; all content words and negations
    must remain identical. Ambiguous anchors are left invalid for the gate.
    """
    result=json.loads(json.dumps(plan));ignored={'and','the','a','an'}
    core=lambda words:[w for w in words if w not in ignored]
    for beat in result.get('beats',[]):
        cue=beat.get('motion_cue');say=beat.get('say')
        if not isinstance(cue,str) or not isinstance(say,str):continue
        matches=list(re.finditer(r"[a-z]+(?:'[a-z]+)?",say.lower().replace('’',"'")))
        words=[m.group() for m in matches];needle=tokens(cue)
        if locations(words,needle):continue
        content=core(needle)
        if len(content)<2:continue
        candidates=[]
        for size in range(max(2,len(needle)-2),min(10,len(needle)+2)+1):
            for i in range(len(words)-size+1):
                if core(words[i:i+size])==content:
                    candidates.append((size,i,say[matches[i].start():matches[i+size-1].end()]))
        if candidates:
            shortest=min(c[0] for c in candidates);best=[c for c in candidates if c[0]==shortest]
            if len(best)==1:beat['motion_cue']=best[0][2]
    # Prefer the actual moving subject/action over a nearby static clause.
    # Select only existing model-written words; never supply spoken content.
    for beat in result.get('beats',[]):
        pattern=ANCHORS.get(result.get('mechanism'),{}).get(beat.get('action'))
        say=beat.get('say','')
        if not pattern or not isinstance(say,str):continue
        supplied=beat.get('motion_cue','')
        if isinstance(supplied,str) and len(locations(tokens(say),tokens(supplied)))==1 and 2<=len(tokens(supplied))<=3 and re.fullmatch(pattern,supplied.strip(),re.I):continue
        match=re.search(pattern,say,re.I)
        if not match:continue
        words=list(re.finditer(r"[a-z]+(?:'[a-z]+)?",say.lower().replace('’',"'")))
        selected=[i for i,w in enumerate(words) if w.end()>match.start() and w.start()<match.end()]
        if not selected:continue
        first,last=min(selected),max(selected)
        # Find a short unique window containing the actual subject/action.
        # Every candidate is copied verbatim; no spoken words are synthesized.
        chosen=None
        for size in range(max(2,last-first+1),11):
            starts=range(max(0,last-size+1),min(first,len(words)-size)+1)
            candidates=[]
            for start in starts:
                end=start+size-1;phrase=say[words[start].start():words[end].end()]
                if len(locations(tokens(say),tokens(phrase)))==1:candidates.append((abs(start-first),phrase))
            if candidates:chosen=min(candidates,key=lambda c:c[0])[1];break
        if chosen:beat['motion_cue']=chosen
    return result

def progress(t, beat):
    a,b=beat.get('motion_window', [beat['start'],beat['end']])
    return max(0.,min(1.,(t-a)/(b-a)))

def event_started(t, beat):
    return t >= beat.get('motion_window',[beat['start'],beat['end']])[0]

def span_progress(t, beats, first, last):
    a=beats[first].get('motion_window',[beats[first]['start'],beats[first]['end']])[0]
    b=beats[last]['end']
    return max(0.,min(1.,(t-a)/(b-a)))

def bind(plan, timeline, out, transcribe=None):
    """Only consume existing speech; never send a voice/model generation call."""
    errors=cue_errors(plan)
    if errors:raise ValueError('; '.join(errors))
    if len(plan['beats']) != len(timeline['beats']):raise ValueError('Speech/action beat count mismatch')
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    report_path=out/'spoken-action-timing.json'
    model=None
    def recognize(path):
        nonlocal model
        if transcribe is not None:return transcribe(path)
        if os.environ.get('GITHUB_ACTIONS')!='true':
            raise ValueError('Production speech alignment belongs on the cloud runner')
        if importlib.util.find_spec('faster_whisper') is None:
            subprocess.run([sys.executable,'-m','pip','install','--quiet','faster-whisper'],check=True,timeout=180)
        if model is None:
            from faster_whisper import WhisperModel
            model=WhisperModel('tiny.en',device='cpu',compute_type='int8')
        segments,_=model.transcribe(str(path),language='en',beam_size=5,word_timestamps=True)
        return [{'text':w.word,'start':w.start,'end':w.end} for s in segments for w in s.words or []]
    previous={}
    if report_path.exists():
        try:previous=json.loads(report_path.read_text())
        except (OSError,ValueError):pass
    cached={r.get('key'):r for r in previous.get('cues',[]) if previous.get('policy')==VERSION}
    rows=[]
    for i,(planned,beat) in enumerate(zip(plan['beats'],timeline['beats'])):
        if planned['action']!=beat['action'] or planned['say']!=beat['say']:
            raise ValueError('Saved speech does not match the accepted action/narration')
        if planned['action'] not in TRANSITIONS.get(plan['mechanism'],set()):continue
        voice=Path(beat['voice']);audio_hash=hashlib.sha256(voice.read_bytes()).hexdigest()
        key=hashlib.sha256(json.dumps([VERSION,ALIGNMENT_REVISION,audio_hash,planned['say'],planned['motion_cue'],beat['start'],beat['end']],sort_keys=True).encode()).hexdigest()
        if key in cached:
            row=cached[key]
        else:
            words=recognize(voice);flat=[];spans=[];last_end=-1.
            for word in words:
                a,b=float(word['start']),float(word['end'])
                if not all(math.isfinite(v) for v in (a,b)) or a<0 or b<a or a<last_end-.05:
                    raise ValueError('Measured speech word times are invalid')
                if b>float(beat['voice_duration'])+.25:raise ValueError('Word extends beyond its voice track')
                last_end=b
                for token in tokens(word['text']):flat.append(token);spans.append((a,b))
            (out/f'spoken-action-words-{i:02}.json').write_text(json.dumps({'audio_sha256':audio_hash,'expected':planned['say'],'phrase':planned['motion_cue'],'measured_words':words},indent=2))
            cue=tokens(planned['motion_cue']);matches=measured_matches(flat,cue)
            if len(matches)!=1:
                raise ValueError(f"Measured audio did not uniquely contain action cue in beat {i}; hold before rendering")
            first_word,last_word=matches[0];spoken_start=beat['start']+.08+spans[first_word][0];spoken_end=beat['start']+.08+spans[last_word][1]
            if spoken_end<=spoken_start:raise ValueError('Action cue has no measured spoken interval')
            # Brief lead-in exposes the part before its name; preserve the full
            # action inside this beat and leave cameras on their original clock.
            start=max(beat['start'],spoken_start-.35)
            end=min(beat['end'],beat['start']+.08+float(beat['voice_duration'])+.05)
            if plan.get('mechanism') in ('camera_iris','float_valve','combination_lock','electric_relay','snap_thermostat','zipper','stapler','optical_fiber','pendulum_clock','ratchet_wrench') and planned['action']=='cutaway':end=min(beat['end'],max(spoken_end+.1,start+.9))
            completion=completion_match(plan['mechanism'],planned['action'],flat,spans,first_word)
            if completion:end=min(end,max(start+.5,beat['start']+.08+completion['end']+.15))
            if end-start<.35:raise ValueError('Speech cue leaves no safe action interval')
            row={'key':key,'beat':i,'action':planned['action'],'phrase':planned['motion_cue'],
                 'audio_sha256':audio_hash,'spoken_start':spoken_start,'spoken_end':spoken_end,
                 'motion_window':[start,end],'method':'Independent word timestamps from the saved voice track'}
            if completion:row.update(completion_phrase=completion['phrase'],completion_spoken_start=beat['start']+.08+completion['start'],completion_spoken_end=beat['start']+.08+completion['end'],completion_policy='measured-result-v1')
            if plan['mechanism']=='bascule_bridge' and planned['action']=='resume':
                gate_match=[]
                for j,word in enumerate(flat):
                    if word in ('barrier','barriers','gate','gates'):
                        for k in range(j+1,min(len(flat),j+4)):
                            if re.match(r'ris|rais|lift|open',flat[k]):gate_match.append((j,k));break
                if len(gate_match)!=1:raise ValueError('Final barrier reopening needs its own measured cue')
                j,k=gate_match[0]
                gate_start=max(beat['start'],beat['start']+.08+spans[j][0]-.2)
                gate_end=min(beat['start']+.08+spans[k][1]+.15,start-.05)
                if gate_end-gate_start<.3:raise ValueError('Barrier must reopen before the car starts crossing')
                row['gate_window']=[gate_start,gate_end]
        beat['motion_window']=row['motion_window'];rows.append(row)
        if 'gate_window' in row:beat['gate_window']=row['gate_window']
        # Persist each accepted line so an interruption does not repeat alignment.
        report_path.write_text(json.dumps({'policy':VERSION,'alignment_revision':ALIGNMENT_REVISION,'cues':rows,'errors':[],
            'scope':'Discrete action timing; continuous motion and semantic pixel verification are separate'},indent=2))
    if not rows:   # recipe machines have no spoken-action transitions; the evidence file still states that explicitly
        report_path.write_text(json.dumps({'policy':VERSION,'alignment_revision':ALIGNMENT_REVISION,'cues':[],'errors':[],'scope':'No discrete transition actions for this mechanism; motion follows measured beat windows'},indent=2))
    timeline['motion_policy']=VERSION
    return timeline

def require_bound(plan,timeline,out,verify_audio=False):
    if plan.get('motion_policy')!=VERSION or timeline.get('motion_policy')!=VERSION:
        raise ValueError('Spoken-action timing policy missing')
    if cue_errors(plan):raise ValueError('Accepted narration has invalid action cues')
    report=json.loads((Path(out)/'spoken-action-timing.json').read_text())
    expected=[i for i,b in enumerate(plan['beats']) if b['action'] in TRANSITIONS.get(plan['mechanism'],set())]
    rows=report.get('cues',[])
    if report.get('policy')!=VERSION or report.get('alignment_revision')!=ALIGNMENT_REVISION or report.get('errors')!=[] or [r.get('beat') for r in rows]!=expected:
        raise ValueError('Complete measured spoken-action evidence missing')
    for row in rows:
        i=row['beat'];beat=timeline['beats'][i];planned=plan['beats'][i]
        if row['action']!=planned['action'] or row['phrase']!=planned['motion_cue'] or beat['say']!=planned['say']:
            raise ValueError('Spoken-action evidence belongs to different narration')
        window=row['motion_window']
        if beat.get('motion_window')!=window or not beat['start']<=window[0]<window[1]<=beat['end']:
            raise ValueError('Renderer timeline does not use its measured action window')
        if row.get('completion_policy')=='measured-result-v1':
            expected_end=min(beat['end'],beat['start']+.08+float(beat['voice_duration'])+.05,max(window[0]+.5,float(row['completion_spoken_end'])+.15))
            if abs(window[1]-expected_end)>1e-7:raise ValueError('Action completion does not match its measured result phrase')
        if plan['mechanism']=='bascule_bridge' and planned['action']=='resume':
            gate=row.get('gate_window',[])
            if len(gate)!=2 or beat.get('gate_window')!=gate or not beat['start']<=gate[0]<gate[1]<window[0]:
                raise ValueError('Final barrier/car timing order is not verified')
        if verify_audio and hashlib.sha256(Path(beat['voice']).read_bytes()).hexdigest()!=row['audio_sha256']:
            raise ValueError('Voice changed after action alignment')
    return report
