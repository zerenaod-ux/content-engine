"""Bounded voice-only comparison; never changes the production speaker."""
import json,shutil,subprocess,wave
from pathlib import Path
import numpy as np
import imageio_ffmpeg
from studio_lib.cpu_voice import engine

TEXT="How can a tiny signal control a powerful machine? Here is the clever part. The coil pulls the arm down, the contacts touch, and the lamp lights up. Small movement, big result!"
VOICES={'Michael':'am_michael','Adam':'am_adam','Heart':'af_heart'}

def main():
 out=Path('voice-options');out.mkdir(exist_ok=True)
 model=engine(Path('.ce-cache/cpu-voice-models'));rows=[]
 for name,voice in VOICES.items():
  samples,sr=model.create(TEXT,voice=voice,speed=1.03,lang='en-us',sentence_pause=.20)
  samples=np.asarray(samples,dtype=np.float32).reshape(-1)
  if sr!=24000 or not sr<samples.size<sr*45 or not np.isfinite(samples).all() or abs(samples).max()<.001:raise ValueError('Invalid audition')
  samples*=min(1.,.95/abs(samples).max())
  raw=out/(name+'-raw.wav');target=out/(name+'.wav')
  with wave.open(str(raw),'wb') as w:
   w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((samples*32700).astype(np.int16).tobytes())
  subprocess.run([shutil.which('ffmpeg') or imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-y','-i',str(raw),'-af','loudnorm=I=-17:TP=-3:LRA=8','-ar','24000',str(target)],check=True)
  raw.unlink();rows.append({'label':name,'voice':voice,'duration':len(samples)/sr,'speed':1.03})
 (out/'report.json').write_text(json.dumps({'text':TEXT,'samples':rows,'production_changed':False,'music':False,'effects':False},indent=2))
if __name__=='__main__':main()
