"""Sound for living-scene videos: energetic narrator (free edge-tts), generated sound effects that match the action, a light music bed, and the final mix.
Everything is generated here; no downloaded sounds, no paid tools."""
import json, os, shutil, subprocess, sys, wave
from pathlib import Path
import numpy as np

SR = 44100
ROOT = Path(__file__).resolve().parent.parent
VOICES = ['en-US-AndrewNeural', 'en-US-GuyNeural', 'en-US-ChristopherNeural', 'en-US-JennyNeural']   # most energetic first

def ensure_ffmpeg():
    ff = shutil.which('ffmpeg')
    if not ff:
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe(); b = Path('bin'); b.mkdir(exist_ok=True)
        if not (b / 'ffmpeg').exists(): os.symlink(ff, b / 'ffmpeg')
        os.environ['PATH'] = str(b.resolve()) + os.pathsep + os.environ['PATH']
    return 'ffmpeg'

_rs = np.random.RandomState(7)
def _t(dur): return np.arange(int(dur * SR)) / SR
def band(x, lo, hi):
    F = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); F[(f < lo) | (f > hi)] = 0; return np.fft.irfft(F, len(x))
def noise(dur, lo, hi):
    x = band(_rs.randn(max(8, int(dur * SR))), lo, hi); return x / (np.abs(x).max() + 1e-9)
def norm(x, peak=1.0): return x * (peak / (np.abs(x).max() + 1e-9))

# ---- sound effects (each returns a mono array, peak about 1) ----
def slice_(dur=0.5):
    t = _t(dur); return norm(noise(dur, 2500, 9000) * np.minimum(1, t * 40) * np.exp(-t * 5) + 0.5 * np.sin(2 * np.pi * (2400 - 1500 * t / dur) * t) * np.exp(-t * 9))
def whump(dur=0.5):
    t = _t(dur); return norm(np.sin(2 * np.pi * (120 * np.exp(-t * 10) + 42) * t) * np.exp(-t * 8) + 0.25 * noise(dur, 80, 500) * np.exp(-t * 14))
def tick(f=1500, dur=0.09):
    t = _t(dur); return norm(np.sin(2 * np.pi * f * t) * np.exp(-t * 60) + 0.6 * noise(dur, 2000, 8000) * np.exp(-t * 90))
def pop(dur=0.16):
    t = _t(dur); return norm(np.sin(2 * np.pi * (700 * np.exp(-t * 30) + 180) * t) * np.exp(-t * 28))
def zip_(dur=0.6, f0=280, f1=1500):
    t = _t(dur); f = f0 + (f1 - f0) * (t / dur) ** 1.4; ph = 2 * np.pi * np.cumsum(f) / SR
    return norm((np.sign(np.sin(ph)) * 0.5 + np.sin(ph)) * (0.55 + 0.45 * np.sign(np.sin(2 * np.pi * 46 * t))) * np.minimum(1, t * 30) * np.minimum(1, (dur - t) * 30) + 0.3 * noise(dur, 1500, 6000))
def thunk(dur=0.3):
    t = _t(dur); return norm(np.sin(2 * np.pi * (180 * np.exp(-t * 16) + 70) * t) * np.exp(-t * 16) + 0.4 * noise(dur, 300, 2500) * np.exp(-t * 40))
def click(dur=0.06):
    t = _t(dur); return norm(noise(dur, 1800, 7000) * np.exp(-t * 110) + 0.5 * np.sin(2 * np.pi * 2300 * t) * np.exp(-t * 90))
def snip(dur=0.22):
    t = _t(dur); a = noise(dur, 3000, 11000) * np.exp(-t * 55); b = np.roll(noise(dur, 2500, 9000) * np.exp(-t * 45), int(0.07 * SR)); b[:int(0.07 * SR)] = 0
    return norm(a + 0.9 * b + 0.4 * np.sin(2 * np.pi * 3100 * t) * np.exp(-t * 70))
def whoosh(dur=0.5):
    t = _t(dur); return norm(noise(dur, 400, 3500) * np.sin(np.pi * t / dur) ** 2)
def chime(f=880, dur=0.9):
    t = _t(dur); return norm((np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 2 * f * t) + 0.25 * np.sin(2 * np.pi * 3.01 * f * t)) * np.exp(-t * 5))
def sparkle(dur=4.0, base=660, rate=7.0):
    out = np.zeros(int(dur * SR)); scale = [1, 1.125, 1.25, 1.5, 1.667, 2, 2.25, 2.5]; k = 0; tt = 0.0
    while tt < dur - 0.4:
        c = chime(base * scale[(k * 3) % len(scale)], 0.4) * (0.35 + 0.65 * tt / dur); i = int(tt * SR); c = c[:len(out) - i]; out[i:i + len(c)] += c; k += 1; tt += 1 / rate
    return norm(out)
def splash(dur=0.5):
    t = _t(dur); return norm(noise(dur, 700, 7000) * np.minimum(1, t * 50) * np.exp(-t * 7))
def rumble(dur=1.0):
    t = _t(dur); return norm(noise(dur, 40, 180) * np.sin(np.pi * t / dur))

def hum(dur=2.0, f=92):
    t = _t(dur); x = sum(np.sin(2 * np.pi * f * k * t) / k for k in (1, 2, 3, 4, 6)) * (0.8 + 0.2 * np.sin(2 * np.pi * 23 * t))
    return norm(x * np.minimum(1, t * 4) * np.minimum(1, (dur - t) * 3))
def flow(dur=2.0):
    t = _t(dur); return norm(noise(dur, 500, 5200) * (0.75 + 0.25 * np.sin(2 * np.pi * 3.1 * t) * np.sin(2 * np.pi * 0.7 * t + 1)) * np.minimum(1, t * 5) * np.minimum(1, (dur - t) * 4))
def spray(dur=2.0):
    t = _t(dur); return norm(noise(dur, 2500, 10000) * (0.8 + 0.2 * np.sin(2 * np.pi * 9 * t)) * np.minimum(1, t * 6) * np.minimum(1, (dur - t) * 4))
def powerdown(dur=1.1):
    t = _t(dur); f = 420 * np.exp(-t * 3.2) + 40; return norm(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.4 * np.exp(-t * 1.5) + np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.5))

SFX = {'slice': slice_, 'whump': whump, 'tick': tick, 'pop': pop, 'zip': zip_, 'thunk': thunk, 'click': click, 'snip': snip, 'whoosh': whoosh, 'chime': chime, 'sparkle': sparkle,
       'splash': splash, 'rumble': rumble, 'hum': hum, 'flow': flow, 'spray': spray, 'powerdown': powerdown}

class Track:
    def __init__(self, T): self.T = T; self.buf = np.zeros(int(T * SR))
    def add(self, t, x, gain=1.0):
        i = int(max(0, t) * SR); x = x[:len(self.buf) - i]
        if len(x) > 0: self.buf[i:i + len(x)] += gain * x
        return self

def music(T, bpm=118, root=110.0, energy=1.0):
    """Light driving bed: kick on every beat, soft hat between, a 4-chord bass line and a pad. Generated, so no licence needed."""
    n = int(T * SR); t = np.arange(n) / SR; out = np.zeros(n); beat = 60.0 / bpm; prog = [1.0, 0.794, 1.189, 0.891]   # A, F, C, G (ratios)
    kt = _t(0.22); kick = np.sin(2 * np.pi * (110 * np.exp(-kt * 22) + 48) * kt) * np.exp(-kt * 13)
    ht = _t(0.05); hat = noise(0.05, 6000, 12000) * np.exp(-ht * 90)
    b = 0
    while b * beat < T:
        i = int(b * beat * SR); k = kick[:n - i]; out[i:i + len(k)] += 0.55 * k
        j = int((b + 0.5) * beat * SR)
        if j < n: h = hat[:n - j]; out[j:j + len(h)] += 0.16 * h
        f = root * prog[(b // 4) % 4]; d = min(beat * 0.92, T - b * beat); nt = _t(d)
        note = (np.sin(2 * np.pi * f * nt) + 0.35 * np.sin(2 * np.pi * 2 * f * nt)) * np.minimum(1, nt * 80) * np.exp(-nt * 3.2); note = note[:n - i]; out[i:i + len(note)] += 0.30 * note
        b += 1
    for c in range(int(T / (4 * beat)) + 1):
        i = int(c * 4 * beat * SR); d = min(4 * beat, T - c * 4 * beat)
        if d <= 0: break
        nt = _t(d); f = root * 2 * prog[c % 4]; pad = (np.sin(2 * np.pi * f * nt) + np.sin(2 * np.pi * f * 1.498 * nt) + np.sin(2 * np.pi * f * 1.26 * nt)) * np.sin(np.pi * nt / d) ** 0.6; pad = pad[:n - i]; out[i:i + len(pad)] += 0.07 * pad
    return norm(out) * energy

def speak(lines, rate='+16%', pitch='+2Hz'):
    """lines = [(start, end, text)]. Returns (voice track array for the whole video, log lines). Tries the most energetic voice first."""
    ensure_ffmpeg(); sys.path.insert(0, str(ROOT)); import local_voice
    T = max(b for a, b, _ in lines) + 0.5; n = int(T * SR); out = np.zeros(n); log = []
    os.environ['CE_EDGE_RATE'] = rate; os.environ['CE_EDGE_PITCH'] = pitch
    jobs = [{'text': tx, 'wav': 'v%d.wav' % i, 'timing': 't%d.json' % i} for i, (a, b, tx) in enumerate(lines)]
    used = None; last = None
    for v in ([os.environ['SCENE_VOICE']] if os.environ.get('SCENE_VOICE') else VOICES):
        os.environ['CE_EDGE_VOICE'] = v
        try: local_voice.edge_run(jobs); used = v; break
        except Exception as e: last = e
    if not used: raise RuntimeError('voice failed: %s' % last)
    log.append('voice: %s rate %s pitch %s' % (used, rate, pitch))
    for i, (a, b, tx) in enumerate(lines):
        dur = json.loads(Path('t%d.json' % i).read_text())['duration']; room = b - a - 0.1; src = 'v%d.wav' % i
        if dur > room:
            k = min(1.4, dur / room); subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-filter:a', 'atempo=%.3f' % k, 'f%d.wav' % i], check=True); src = 'f%d.wav' % i
        with wave.open(src) as w:
            sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
        m = int(len(x) * SR / sr); x = np.interp(np.arange(m) * sr / SR, np.arange(len(x)), x); i0 = int((a + 0.05) * SR); x = x[:n - i0]; out[i0:i0 + len(x)] += x
        log.append('line %d: %.2fs spoken, %.2fs room%s' % (i + 1, dur, room, ' (sped up)' if dur > room else ''))
    return norm(out, 0.95), log

def mix(T, voice, sfx, bed, sfx_gain=0.62, bed_gain=0.20):
    n = int(T * SR)
    def fit(x): x = x[:n]; return np.pad(x, (0, n - len(x)))
    voice, sfx, bed = fit(voice), fit(sfx), fit(bed)
    w = int(0.06 * SR); env = np.convolve(np.abs(voice), np.ones(w) / w, mode='same'); duck = 1 - 0.55 * np.clip(env * 7, 0, 1)   # music steps back while the narrator talks
    out = voice + sfx_gain * sfx * (1 - 0.25 * np.clip(env * 7, 0, 1)) + bed_gain * bed * duck
    t = np.arange(n) / SR; out *= np.minimum(1, np.minimum(t / 0.25, (T - t) / 0.5)); out = np.tanh(out * 1.5) / np.tanh(1.5)
    return norm(out, 0.97)

def write_wav(path, x):
    with wave.open(path, 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x, -1, 1) * 32700).astype(np.int16).tobytes())

def mux(frames, audio, out, fps=30):
    ensure_ffmpeg()
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(fps), '-i', frames, '-i', audio, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], check=True)
