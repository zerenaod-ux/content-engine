"""An isolated audio fixture, never a video/topic or publishing action."""
import json,subprocess,wave
from pathlib import Path
import numpy as np
from studio_lib.cpu_voice import render
from studio_lib.voice_policy import VOICE,VERSION
out=Path('narrator-check');out.mkdir(exist_ok=True)
spec={'beats':[
 {'action':'question','say':'What if a small movement could change everything? Let us follow it, one step at a time.'},
 {'action':'cutaway','say':'Here is the key connection. Watch how one part drives the next.'},
 {'action':'load','say':'Now the cause is clear: one change leads to the result.'},
 {'action':'payoff','say':'And that is the idea. Simple parts, working together.'}]}
report=render(spec,'.ce-cache/narrator-proof')
assert report['voice']==VOICE and all(line['speaker']==VOICE for line in report['lines'])
chunks=[]
for line in report['lines']:
 with wave.open(line['voice'],'rb') as w:
  assert w.getframerate()==24000 and w.getnchannels()==1
  chunks.append(np.frombuffer(w.readframes(w.getnframes()),np.int16))
 chunks.append(np.zeros(int(24000*line['delivery']['pause_after']),np.int16))
with wave.open(str(out/'raw.wav'),'wb') as w:
 w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(np.concatenate(chunks).tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',str(out/'raw.wav'),'-af','loudnorm=I=-17:TP=-3:LRA=8','-ar','24000',str(out/'narrator.wav')],check=True)
report.update(policy=VERSION,fixture_only=True,video_created=False,text=spec)
(out/'report.json').write_text(json.dumps(report,indent=2))
print('One fixed narrator produced all four delivery roles. No video created.')
