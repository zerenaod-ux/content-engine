"""Free local Kokoro Heart narration. Never falls back to another voice."""
import json,subprocess
from pathlib import Path
BASE=Path(__file__).resolve().parent
WORK=BASE.parent.parent/'work'
RUNTIME=WORK/'kokoro-runtime/bin/python'
PIPELINE=None

QWEN_PYTHON_DEFAULT=Path.home()/'Dev/_ops/tts-lab/bin/python'
def style():
 try:return json.loads((BASE/'voice-style.json').read_text())
 except (OSError,ValueError):return {}
def engine():
 import os
 e=os.environ.get('CE_VOICE_ENGINE') or style().get('engine')
 return e if e in ('qwen','edge') else 'kokoro'
def qwen_run(jobs):
 """Expressive Qwen3-TTS narration in its own venv. No silent substitute voice: failure is reported."""
 py=Path(style().get('qwen_python') or QWEN_PYTHON_DEFAULT)
 if not py.is_file():raise RuntimeError('Expressive voice is selected but its tool is missing: '+str(py)+'. No substitute voice was used.')
 try:
  import os
  env={k:v for k,v in os.environ.items() if k not in ('HF_HOME','XDG_CACHE_HOME','HF_HUB_CACHE','TRANSFORMERS_CACHE')};env['HF_HUB_OFFLINE']='1'
  result=subprocess.run([str(py),str(BASE/'qwen_voice.py')],input=json.dumps({'jobs':jobs}),text=True,capture_output=True,timeout=3600,env=env)
 except subprocess.TimeoutExpired as e:raise RuntimeError('Expressive narration exceeded 60 minutes. No substitute voice was used.') from e
 if result.returncode or not all(Path(j['wav']).is_file() for j in jobs):raise RuntimeError('Expressive narration failed. No substitute voice was used. '+result.stderr[-500:])
def edge_run(jobs):
 """Natural American neural voice (Microsoft Jenny via the free edge-tts library). Writes 24 kHz wav and, when asked, exact word timings."""
 import asyncio,os,subprocess,tempfile,edge_tts
 voice=os.environ.get('CE_EDGE_VOICE','en-US-JennyNeural');rate=os.environ.get('CE_EDGE_RATE','+0%');pitch=os.environ.get('CE_EDGE_PITCH','+0Hz')
 async def one(text):
  try:com=edge_tts.Communicate(text,voice,rate=rate,pitch=pitch,boundary='WordBoundary')
  except TypeError:com=edge_tts.Communicate(text,voice,rate=rate,pitch=pitch)
  audio=bytearray();words=[]
  async for chunk in com.stream():
   if chunk['type']=='audio':audio+=chunk['data']
   elif chunk['type']=='WordBoundary':words.append({'text':chunk['text'],'start':chunk['offset']/1e7,'end':(chunk['offset']+chunk['duration'])/1e7})
  if not audio:raise RuntimeError('Edge voice returned no audio')
  return bytes(audio),words
 for job in jobs:
  last=None
  for attempt in range(4):
   try:audio,words=asyncio.run(one(job['text']));break
   except Exception as e:last=e;import time;time.sleep(2+attempt*3)
  else:raise RuntimeError('Natural voice (edge-tts) failed after retries: '+str(last)[:300]+'. No substitute voice was used.')
  with tempfile.NamedTemporaryFile(suffix='.mp3',delete=False) as f:f.write(audio);name=f.name
  try:
   r=subprocess.run(['ffmpeg','-v','error','-y','-i',name,'-ar','24000','-ac','1','-c:a','pcm_s16le',str(job['wav'])],capture_output=True,text=True)
   if r.returncode:raise RuntimeError('Could not decode narration: '+r.stderr[-300:])
  finally:os.unlink(name)
  if job.get('timing'):
   import wave
   with wave.open(str(job['wav'])) as w:duration=w.getnframes()/w.getframerate()
   Path(job['timing']).write_text(json.dumps({'tokens':words,'duration':duration}))
def available():
 if engine()=='edge':
  try:
   import edge_tts;return True
  except ImportError:return False
 import voice_frontend
 return RUNTIME.is_file() and (WORK/'kokoro-models').is_dir() and voice_frontend.available()
def segment(text,index,folder):
 output=Path(folder)/f'kokoro_{index:02d}.wav'
 if engine()=='edge':
  edge_run([{'text':text,'wav':str(output),'timing':None}])
  import wave
  with wave.open(str(output)) as audio:return str(output),audio.getnframes()/audio.getframerate()
 if engine()=='qwen':
  qwen_run([{'text':text,'wav':str(output),'timing':None}])
  import wave
  with wave.open(str(output)) as audio:return str(output),audio.getnframes()/audio.getframerate()
 result=subprocess.run([str(RUNTIME),str(Path(__file__).resolve()),str(output)],input=text,text=True,capture_output=True,timeout=900)
 if result.returncode or not output.exists():raise RuntimeError('Kokoro Heart narration failed. No substitute voice was used. '+result.stderr[-500:])
 import wave
 with wave.open(str(output)) as audio:duration=audio.getnframes()/audio.getframerate()
 if duration<=0:raise RuntimeError('Kokoro returned empty narration.')
 return str(output),duration

def segments(texts,folder):
 """Generate a complete Short's voice in one runtime so Kokoro loads once."""
 folder=Path(folder);outputs=[folder/f'kokoro_{index:02d}.wav' for index in range(len(texts))]
 if engine()=='edge':
  edge_run([{'text':t,'wav':str(o),'timing':None} for t,o in zip(texts,outputs)])
  import wave
  rendered=[]
  for output in outputs:
   with wave.open(str(output)) as audio:rendered.append((str(output),audio.getnframes()/audio.getframerate()))
  return rendered
 if engine()=='qwen':
  qwen_run([{'text':t,'wav':str(o),'timing':None} for t,o in zip(texts,outputs)])
  import wave
  rendered=[]
  for output in outputs:
   with wave.open(str(output)) as audio:rendered.append((str(output),audio.getnframes()/audio.getframerate()))
  return rendered
 try:
  result=subprocess.run([str(RUNTIME),str(Path(__file__).resolve()),'--batch',str(folder)],input=json.dumps(list(texts)),text=True,capture_output=True,timeout=900)
 except subprocess.TimeoutExpired as error:
  (folder/'failure.json').write_text(json.dumps({'temporary':True,'code':'local_voice_timeout','message':'Kokoro Heart batch narration exceeded 15 minutes.'},indent=2))
  raise RuntimeError('Kokoro Heart narration exceeded 15 minutes. A bounded retry is available; no substitute voice was used.') from error
 if result.returncode or not all(path.is_file() for path in outputs):
  raise RuntimeError('Kokoro Heart batch narration failed. No substitute voice was used. '+result.stderr[-500:])
 import wave
 rendered=[]
 for output in outputs:
  with wave.open(str(output)) as audio:duration=audio.getnframes()/audio.getframerate()
  if duration<=0:raise RuntimeError('Kokoro returned empty narration.')
  rendered.append((str(output),duration))
 return rendered
def style_enabled():
 try:return bool(json.loads((BASE/'voice-style.json').read_text()).get('enabled'))
 except (OSError,ValueError):return False
def deliver(pipeline,text):
 """Emotion-aware delivery when voice-style.json enables it; otherwise the original flat delivery."""
 import numpy as np
 if style_enabled():
  import voice_director;return voice_director.render(pipeline,text)
 parts=[a.numpy() if hasattr(a,'numpy') else a for _,_,a in pipeline(text,voice='af_heart',speed=0.95)]
 if not parts:raise RuntimeError('No narration generated')
 return np.concatenate(parts)

if __name__=='__main__':
 import os,sys
 os.environ['HF_HOME']=str(WORK/'kokoro-models');os.environ['XDG_CACHE_HOME']=str(WORK/'kokoro-cache')
 os.environ['HF_HUB_OFFLINE']='1'
 from kokoro import KPipeline
 import voice_frontend
 voice_frontend.configure()
 import numpy as np,soundfile as sf
 pipeline=KPipeline(lang_code='a',repo_id='hexgrad/Kokoro-82M',device='cpu')
 if len(sys.argv)>1 and sys.argv[1]=='--batch':
  folder=Path(sys.argv[2]);texts=json.loads(sys.stdin.read())
  for index,text in enumerate(texts):
   voice_frontend.check(pipeline,text)
   sf.write(folder/f'kokoro_{index:02d}.wav',deliver(pipeline,text),24000,subtype='PCM_16')
 else:
  text=sys.stdin.read();voice_frontend.check(pipeline,text)
  sf.write(sys.argv[1],deliver(pipeline,text),24000,subtype='PCM_16')
