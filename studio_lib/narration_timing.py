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
ALIGNMENT_REVISION = 'phrase-through-sentence-v2'
TRANSITIONS = {
    'bascule_bridge': {'stop', 'balance', 'pass', 'lower', 'resume'},
    'photovoltaic_cell': {'absorb', 'circuit', 'payoff'},
    'piston_pump': {'cutaway', 'suction', 'compression', 'payoff'},
    'wind_turbine': {'shaft', 'load', 'payoff'},
}
ANCHORS = {
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
        if first==last:
            if first>0:first-=1
            elif last+1<len(words):last+=1
        if 2<=last-first+1<=10:beat['motion_cue']=say[words[first].start():words[last].end()]
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
            if end-start<.35:raise ValueError('Speech cue leaves no safe action interval')
            row={'key':key,'beat':i,'action':planned['action'],'phrase':planned['motion_cue'],
                 'audio_sha256':audio_hash,'spoken_start':spoken_start,'spoken_end':spoken_end,
                 'motion_window':[start,end],'method':'Independent word timestamps from the saved voice track'}
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
        if plan['mechanism']=='bascule_bridge' and planned['action']=='resume':
            gate=row.get('gate_window',[])
            if len(gate)!=2 or beat.get('gate_window')!=gate or not beat['start']<=gate[0]<gate[1]<window[0]:
                raise ValueError('Final barrier/car timing order is not verified')
        if verify_audio and hashlib.sha256(Path(beat['voice']).read_bytes()).hexdigest()!=row['audio_sha256']:
            raise ValueError('Voice changed after action alignment')
    return report
