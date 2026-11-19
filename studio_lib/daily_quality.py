"""The active daily component path uses encoded-audio and integrity gates too."""
import importlib.util,json,os,subprocess,sys
from pathlib import Path
from studio_lib.quality_gate import seal,require_seal
from studio_lib.cinema.review import review
from studio_lib.narration_timing import require_bound

def verify(plan,timeline,out,audit):
 out=Path(out);evidence=out/'narration-critique.json'
 require_bound(plan,timeline,out,verify_audio=True)
 if not evidence.exists() or json.loads(evidence.read_text()).get('errors')!=[]:
  if audit(plan,out):raise ValueError('Daily narration/action audit failed')
 (out/'plan.json').write_text(json.dumps(plan,indent=2))
 if importlib.util.find_spec('faster_whisper') is None:
  if os.environ.get('GITHUB_ACTIONS')!='true':raise ValueError('Independent daily audio review requires cloud dependencies')
  subprocess.run([sys.executable,'-m','pip','install','--quiet','faster-whisper'],check=True,timeout=180)
 review(plan,timeline,out)
 media=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(out/'video.mp4')]))
 track=next(s for s in media['streams'] if s['codec_type']=='video')
 seal(out,'short',{'duration':float(media['format']['duration']),'width':track['width'],'height':track['height']})
 return require_seal(out,'short')
