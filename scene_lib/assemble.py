"""Turns a scene spec + its rendered frames into the finished video: narrator, sound effects and music all come from the spec.
  python3 scene_lib/assemble.py scenes/<name>.json out.mp4      (run where the fr/ folder is)
Spec sound cues: "sfx": [[time, name, gain, optional argument], ...]   names: see scene_lib.audio.SFX"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scene_lib import audio as A

def main(spec_path, out):
    spec = json.loads(Path(spec_path).read_text()); T = float(spec['duration'])
    lines = [(s['start'], s['end'], s['say']) for s in spec['steps'] if s.get('say')]
    voice, log = A.speak(lines, rate=spec.get('voice_rate', '+16%'), pitch=spec.get('voice_pitch', '+2Hz'))
    fx = A.Track(T)
    for cue in spec.get('sfx', []):
        t, name, gain = cue[0], cue[1], (cue[2] if len(cue) > 2 else 0.8); f = A.SFX.get(name)
        if not f: raise SystemExit('unknown sound: %s' % name)
        fx.add(t, f(*cue[3:]) if len(cue) > 3 else f(), gain)
    m = spec.get('music', {}); bed = A.music(T, bpm=m.get('bpm', 118), root=m.get('root', 110.0))
    A.write_wav('audio.wav', A.mix(T, voice, fx.buf, bed)); A.mux('fr/%04d.jpg', 'audio.wav', out)
    Path('voice-log.txt').write_text('\n'.join(log) + '\n'); print('\n'.join(log)); print('DONE', out)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
