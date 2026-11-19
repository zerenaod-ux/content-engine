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
TRANSITIONS = {
    'bascule_bridge': {'stop', 'balance', 'pass', 'lower', 'resume'},
    'photovoltaic_cell': {'absorb', 'circuit', 'payoff'},
    'piston_pump': {'cutaway', 'suction', 'compression', 'payoff'},
    'wind_turbine': {'shaft', 'load', 'payoff'},
}

def tokens(text):
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower().replace('’', "'"))

def locations(haystack, needle):
    return [i for i in range(len(haystack)-len(needle)+1)
            if haystack[i:i+len(needle)] == needle] if needle else []

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
    return errors

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
        key=hashlib.sha256(json.dumps([VERSION,audio_hash,planned['say'],planned['motion_cue'],beat['start'],beat['end']],sort_keys=True).encode()).hexdigest()
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
            cue=tokens(planned['motion_cue']);matches=locations(flat,cue)
            if len(matches)!=1:
                raise ValueError(f"Measured audio did not uniquely contain action cue in beat {i}; hold before rendering")
            k=matches[0];spoken_start=beat['start']+.08+spans[k][0];spoken_end=beat['start']+.08+spans[k+len(cue)-1][1]
            if spoken_end<=spoken_start:raise ValueError('Action cue has no measured spoken interval')
            # Brief lead-in exposes the part before its name; preserve the full
            # action inside this beat and leave cameras on their original clock.
            start=max(beat['start'],spoken_start-.35)
            end=min(beat['end'],max(spoken_end+.25,start+1.2))
            if end-start<.35:raise ValueError('Speech cue leaves no safe action interval')
            row={'key':key,'beat':i,'action':planned['action'],'phrase':planned['motion_cue'],
                 'audio_sha256':audio_hash,'spoken_start':spoken_start,'spoken_end':spoken_end,
                 'motion_window':[start,end],'method':'Independent word timestamps from the saved voice track'}
        beat['motion_window']=row['motion_window'];rows.append(row)
        # Persist each accepted line so an interruption does not repeat alignment.
        report_path.write_text(json.dumps({'policy':VERSION,'cues':rows,'errors':[],
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
    if report.get('policy')!=VERSION or report.get('errors')!=[] or [r.get('beat') for r in rows]!=expected:
        raise ValueError('Complete measured spoken-action evidence missing')
    for row in rows:
        i=row['beat'];beat=timeline['beats'][i];planned=plan['beats'][i]
        if row['action']!=planned['action'] or row['phrase']!=planned['motion_cue'] or beat['say']!=planned['say']:
            raise ValueError('Spoken-action evidence belongs to different narration')
        window=row['motion_window']
        if beat.get('motion_window')!=window or not beat['start']<=window[0]<window[1]<=beat['end']:
            raise ValueError('Renderer timeline does not use its measured action window')
        if verify_audio and hashlib.sha256(Path(beat['voice']).read_bytes()).hexdigest()!=row['audio_sha256']:
            raise ValueError('Voice changed after action alignment')
    return report
