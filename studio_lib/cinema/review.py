"""Independent encoded-audio checks; no claim of a human listening review."""
import json,re,subprocess
from pathlib import Path

def normalized(text):
    text=text.lower().replace('’',"'").replace('‑','-')
    return re.findall(r"[a-z]+(?:'[a-z]+)?",text)

def word_error(reference,hypothesis):
    a=normalized(reference);b=normalized(hypothesis);row=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        nxt=[i]
        for j,y in enumerate(b,1):nxt.append(min(nxt[-1]+1,row[j]+1,row[j-1]+(x!=y)))
        row=nxt
    return row[-1]/max(1,len(a))

def review(plan,tl,out):
    from faster_whisper import WhisperModel
    out=Path(out);video=out/'video.mp4'
    p=subprocess.run(['ffmpeg','-hide_banner','-i',str(video),'-af','loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
    match=re.search(r'\{\s*"input_i"[\s\S]*?\}',p.stderr)
    if not match:raise ValueError('Encoded audio loudness measurement unavailable')
    loud=json.loads(match[0]);integrated=float(loud['input_i']);peak=float(loud['input_tp'])
    errors=[]
    if not -20<=integrated<=-12:errors.append('Integrated loudness outside review range')
    if peak>-.8:errors.append('Audio true peak too high')
    # Decode the final mixed MP4, not the original narration files.
    model=WhisperModel('tiny.en',device='cpu',compute_type='int8')
    segments,info=model.transcribe(str(video),beam_size=5,word_timestamps=True)
    segments=list(segments)
    spoken=' '.join(s.text for s in segments);expected=' '.join(b['say'] for b in tl['beats'])
    wer=word_error(expected,spoken)
    if wer>.25:errors.append('Independent transcription differs substantially from expected narration')
    (out/'audio-transcript.json').write_text(json.dumps([{'start':s.start,'end':s.end,'text':s.text,'words':[{'word':w.word,'start':w.start,'end':w.end} for w in s.words or []]} for s in segments],indent=2))
    report={'errors':errors,'integrated_lufs':integrated,'true_peak_dbfs':peak,'independent_asr_word_error_rate':wer,'expected_words':len(normalized(expected)),'speech_words_per_minute':len(normalized(expected))/tl['duration']*60,'method':'Encoded-audio decode, loudness measurement, independent tiny.en speech recognition; not human listening','human_listening_completed':False}
    (out/'audio-review.json').write_text(json.dumps(report,indent=2))
    if errors:raise ValueError('; '.join(errors))
