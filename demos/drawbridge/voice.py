"""Cache individually measured voice lines; never change or expose credentials."""
import asyncio, hashlib, json, subprocess, time
from pathlib import Path
import edge_tts
ROOT = Path(__file__).resolve().parent
async def main():
    t0=time.monotonic(); story=json.loads((ROOT/'story.json').read_text()); out=ROOT/'output'; out.mkdir(exist_ok=True)
    cached=0; timeline=[]; t=0
    for b in story['beats']:
        key=hashlib.sha256(json.dumps([b['text'],story['voice']],sort_keys=True).encode()).hexdigest()[:16]
        f=out/(key+'.mp3')
        if f.exists() and f.stat().st_size>1000: cached+=1
        else:
            v=story['voice']
            for attempt in range(3):
                try:
                    await edge_tts.Communicate(b['text'],v['name'],rate=v['rate'],pitch=v['pitch']).save(str(f)); break
                except edge_tts.exceptions.NoAudioReceived:
                    if attempt==2: raise
                    await asyncio.sleep(2)
        dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(f)]))
        duration=max(b['minimum'],dur+0.55)
        timeline.append(dict(b,start=round(t,3),end=round(t+duration,3),voice=str(f),voice_duration=dur)); t+=duration
    result={'beats':timeline,'duration':t,'voice_seconds':time.monotonic()-t0,'cached_lines':cached,'generated_lines':len(timeline)-cached}
    (out/'timeline.json').write_text(json.dumps(result,indent=2)); print(json.dumps({k:v for k,v in result.items() if k!='beats'}))
if __name__=='__main__': asyncio.run(main())
