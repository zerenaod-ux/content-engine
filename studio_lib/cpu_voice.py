"""Independent stock-voice fallback on GitHub CPU runners, never the laptop."""
import argparse,hashlib,importlib.util,json,os,subprocess,sys,time,urllib.request,wave
from pathlib import Path
import numpy as np
from studio_lib.cinema.speech import delivery

ASSET_BASE='https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/'
ASSETS={
 'kokoro-v1.0.int8.onnx':('ae315a79b623f244700e4afb9246c46a26066782e049ba174bf3ba433970ee9c',114119327),
 'voices-v1.0.bin':('bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d',28214398)}
from studio_lib.voice_policy import VOICE,VERSION

def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as source:
  for part in iter(lambda:source.read(1024*1024),b''):h.update(part)
 return h.hexdigest()

def asset(name,root):
 expected,size=ASSETS[name];path=Path(root)/name
 if path.exists() and path.stat().st_size==size and digest(path)==expected:return path
 path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix(path.suffix+'.part');start=time.monotonic()
 try:
  with urllib.request.urlopen(ASSET_BASE+name,timeout=45) as response,temp.open('wb') as output:
   total=0
   while True:
    part=response.read(1024*1024)
    if not part:break
    total+=len(part)
    if total>size or time.monotonic()-start>240:raise ValueError('CPU voice asset download exceeded its bound')
    output.write(part)
  if temp.stat().st_size!=size or digest(temp)!=expected:raise ValueError('CPU voice asset integrity failed')
  temp.replace(path);return path
 finally:temp.unlink(missing_ok=True)

def engine(root):
 if os.environ.get('GITHUB_ACTIONS')!='true':raise ValueError('CPU production voice must run on the cloud runner')
 if importlib.util.find_spec('kokoro_onnx') is None:
  subprocess.run([sys.executable,'-m','pip','install','--quiet','kokoro-onnx==0.6.1'],check=True,timeout=180)
 import onnxruntime as ort
 from kokoro_onnx import Kokoro
 model=asset('kokoro-v1.0.int8.onnx',root);voices=asset('voices-v1.0.bin',root)
 options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
 session=ort.InferenceSession(str(model),sess_options=options,providers=['CPUExecutionProvider'])
 return Kokoro.from_session(session,str(voices))

def render(spec,cache):
 if os.environ.get('GITHUB_ACTIONS')!='true':raise ValueError('CPU production voice must run on the cloud runner')
 cache=Path(cache);cache.mkdir(parents=True,exist_ok=True);model=None;lines=[];hits=0
 for i,b in enumerate(spec['beats']):
  profile=delivery(b.get('action','explain'),i,len(spec['beats']))
  scale=float(spec.get('delivery_speed_scale',1.0))
  if not .85<=scale<=1.15:raise ValueError('Narrator speed adjustment exceeds its natural delivery range')
  speed=max(.9,min(1.35,(1+float(profile['rate'].strip('%'))/100)*scale))
  key=hashlib.sha256(json.dumps([b['say'],VOICE,profile,speed,VERSION,'kokoro-onnx-0.6.1-int8'],sort_keys=True).encode()).hexdigest()
  path=cache/(key+'.wav');meta=cache/(key+'.json')
  reused=False
  if path.exists() and meta.exists():
   try:
    saved=json.loads(meta.read_text());reused=saved.get('sha256')==digest(path) and saved.get('voice')==VOICE and saved.get('voice_policy')==VERSION
   except (OSError,ValueError):reused=False
  if reused:hits+=1
  else:
   if model is None:model=engine(Path('.ce-cache/cpu-voice-models'))
   samples,sr=model.create(b['say'],voice=VOICE,speed=speed,lang='en-us',sentence_pause=profile['pause_after'])
   samples=np.asarray(samples,dtype=np.float32).reshape(-1)
   if sr!=24000 or not sr*.2<len(samples)<sr*90 or not np.isfinite(samples).all() or np.max(abs(samples))<.001:raise ValueError('CPU voice produced invalid audio')
   peak=float(np.max(abs(samples)))
   if peak>.98:samples=samples*(.98/peak)
   temporary=path.with_suffix('.part.wav')
   with wave.open(str(temporary),'wb') as output:
    output.setnchannels(1);output.setsampwidth(2);output.setframerate(sr);output.writeframes((samples*32700).astype(np.int16).tobytes())
   temporary.replace(path);meta.write_text(json.dumps({'sha256':digest(path),'provider':'kokoro-onnx','voice':VOICE,'voice_policy':VERSION,'speed':speed,'delivery':profile}))
  lines.append({'voice':str(path),'speaker':VOICE,'speed':speed,'delivery':profile})
 return {'provider':'kokoro-onnx-cpu','voice':VOICE,'voice_policy':VERSION,'lines':lines,'cached_lines':hits,'manual_audio_edits':False}

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--spec',required=True);parser.add_argument('--report',required=True);parser.add_argument('--cache',default='.ce-cache/cpu-voice-lines');args=parser.parse_args()
 result=render(json.loads(Path(args.spec).read_text()),args.cache);Path(args.report).write_text(json.dumps(result,indent=2))
