"""Preserve original quality below the CDN limit; bound only oversized transport copies."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
LIMIT=19_000_000

def probe(path):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def prepare(source,target,limit=LIMIT):
 source,target=Path(source),Path(target);media=probe(source)
 video=next(s for s in media['streams'] if s['codec_type']=='video');audio=next(s for s in media['streams'] if s['codec_type']=='audio')
 duration=float(media['format']['duration'])
 if video['codec_name']!='h264' or audio['codec_name']!='aac' or duration<=0:raise ValueError('Phone delivery requires verified H264/AAC media')
 target.parent.mkdir(parents=True,exist_ok=True);copied=source.stat().st_size<=limit
 if copied:shutil.copyfile(source,target)
 else:
  # Keep native dimensions and the original encoded narration; reserve container headroom.
  rate=int(limit*.90*8/duration)-max(160000,int(audio.get('bit_rate',160000)))
  if rate<600000:raise ValueError('CDN limit cannot preserve readable native media; delivery held')
  subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),'-c:v','libx264','-preset','medium','-b:v',str(rate),'-maxrate',str(int(rate*1.2)),'-bufsize',str(rate*2),'-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(target)],check=True)
 output=probe(target);track=next(s for s in output['streams'] if s['codec_type']=='video')
 if target.stat().st_size>limit or (track['width'],track['height'])!=(video['width'],video['height']) or abs(float(output['format']['duration'])-duration)>.1:raise ValueError('Phone media size, dimensions or timing failed; no review URL may be written')
 subprocess.run(['ffmpeg','-v','error','-i',str(target),'-f','null','-'],check=True)
 report={'policy':'preserve-native-phone-v1','original_bytes':source.stat().st_size,'delivered_bytes':target.stat().st_size,'width':track['width'],'height':track['height'],'duration':float(output['format']['duration']),'original_preserved':copied,'source_sha256':digest(source),'delivered_sha256':digest(target),'errors':[]}
 if copied and report['source_sha256']!=report['delivered_sha256']:raise ValueError('Original delivery bytes changed')
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('target');a=p.parse_args()
 report=prepare(a.source,a.target);Path('phone-delivery-quality.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
